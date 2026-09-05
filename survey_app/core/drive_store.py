"""
Almacenamiento de documentos de proyecto en Google Drive (OAuth de usuario, scope drive.file).

Secrets (Streamlit):
  [gdrive]
  client_id     = "..."
  client_secret = "..."
  refresh_token = "..."
  # opcional: root_folder_id = "..."  (carpeta raíz; si no, se crea 'COPEX Projects')

Usa google-auth + requests (sin dependencias nuevas). Estructura en Drive:
  <raíz> / <PRJ-id> / <archivos>
Los archivos quedan PRIVADOS en el Drive del dueño; las descargas pasan por la app
(la app trae los bytes con el token y los entrega con st.download_button).
"""
import json
import logging

import requests
import streamlit as st

logger = logging.getLogger(__name__)

SCOPES      = ["https://www.googleapis.com/auth/drive.file"]
ROOT_NAME   = "COPEX Projects"

# ── Carpetas en ingles, con respaldo al nombre viejo (v467) ───────────────────
# ⚠️ Las carpetas se buscan POR NOMBRE y se CREAN si no aparecen, asi que cambiar
# solo la constante dejaria los archivos ya subidos en la carpeta vieja: invisibles
# para la app y sin ningun error. Aqui se resuelve al reves — si aparece la vieja se
# le CAMBIA EL NOMBRE, que en Drive conserva el contenido (los ficheros cuelgan por
# id, no por nombre). Se auto-repara la primera vez que se toca cada carpeta.
LEGADO_CARPETAS = {
    "COPEX Projects": "COPEX Proyectos",
    "COPEX Assets":   "COPEX Activos",
    "COPEX Manuals":  "COPEX Manuales",
}
FOLDER_MIME = "application/vnd.google-apps.folder"
_API        = "https://www.googleapis.com/drive/v3/files"
_UPLOAD     = "https://www.googleapis.com/upload/drive/v3/files"
_TOKEN_URI  = "https://oauth2.googleapis.com/token"


def is_configured() -> bool:
    try:
        g = st.secrets.get("gdrive")
        return bool(g and g.get("client_id") and g.get("client_secret") and g.get("refresh_token"))
    except Exception:
        return False


@st.cache_data(ttl=120, show_spinner=False)
def is_available() -> bool:
    """True si Drive está configurado Y las credenciales OAuth funcionan.
    Fuerza un refresh del token (cacheado 120 s) para detectar credenciales
    inválidas (invalid_client / invalid_grant) sin reventar 3 subidas."""
    if not is_configured():
        return False
    try:
        _headers()      # refresca el token; lanza si las credenciales son inválidas
        return True
    except Exception as e:
        logger.warning("drive_store: credenciales OAuth no válidas: %s", e)
        return False


@st.cache_resource(show_spinner=False)
def _credentials():
    from google.oauth2.credentials import Credentials
    g = st.secrets["gdrive"]
    return Credentials(None, refresh_token=g["refresh_token"],
                       client_id=g["client_id"], client_secret=g["client_secret"],
                       token_uri=_TOKEN_URI, scopes=SCOPES)


def _headers():
    from google.auth.transport.requests import Request
    c = _credentials()
    if not c.valid:
        c.refresh(Request())
    return {"Authorization": f"Bearer {c.token}"}


# ── Carpetas ─────────────────────────────────────────────────────
def _find_folder(name, parent=None):
    q = f"name = '{name}' and mimeType = '{FOLDER_MIME}' and trashed = false"
    if parent:
        q += f" and '{parent}' in parents"
    r = requests.get(_API, headers=_headers(),
                     params={"q": q, "fields": "files(id,name)", "spaces": "drive"})
    r.raise_for_status()
    files = r.json().get("files", [])
    return files[0]["id"] if files else None


def _rename_folder(fid, nombre):
    """Renombra una carpeta. Conserva su contenido: los ficheros cuelgan por id."""
    r = requests.patch("%s/%s" % (_API, fid), headers=_headers(),
                       json={"name": nombre}, params={"fields": "id,name"})
    r.raise_for_status()
    return r.json().get("id")


def carpeta_con_legado(name, parent=None):
    """Id de la carpeta `name`, renombrando la vieja si es la que existe.

    ⚠️ El orden importa: primero se busca el nombre NUEVO, y solo si no esta se
    mira el viejo. Al reves, una instalacion ya migrada volveria a tocar Drive en
    cada arranque.
    """
    fid = _find_folder(name, parent=parent)
    if fid:
        return fid
    viejo = LEGADO_CARPETAS.get(name)
    if viejo:
        fid = _find_folder(viejo, parent=parent)
        if fid:
            try:
                _rename_folder(fid, name)
                logger.info("drive: carpeta %r renombrada a %r", viejo, name)
            except Exception as e:
                # Si el renombrado falla se sigue usando la carpeta VIEJA: mejor el
                # nombre en español que perder de vista los archivos.
                logger.warning("drive: no se pudo renombrar %r: %s", viejo, e)
            return fid
    return _create_folder(name, parent=parent)


def _create_folder(name, parent=None):
    body = {"name": name, "mimeType": FOLDER_MIME}
    if parent:
        body["parents"] = [parent]
    r = requests.post(_API, headers=_headers(), json=body, params={"fields": "id"})
    r.raise_for_status()
    return r.json()["id"]


@st.cache_data(ttl=600, show_spinner=False)
def _root_id():
    try:
        rid = st.secrets["gdrive"].get("root_folder_id")
    except Exception:
        rid = None
    return rid or carpeta_con_legado(ROOT_NAME)


@st.cache_data(ttl=600, show_spinner=False)
def project_folder(pid: str) -> str:
    """Id de la carpeta del proyecto (la crea si no existe)."""
    root = _root_id()
    return _find_folder(pid, parent=root) or _create_folder(pid, parent=root)


@st.cache_data(ttl=600, show_spinner=False)
def folder(name: str) -> str:
    """Id de una subcarpeta con nombre `name` bajo la raíz (la crea si no existe).
    Útil para almacenes que no son de un proyecto (p. ej. 'COPEX Manuals')."""
    root = _root_id()
    return carpeta_con_legado(name, parent=root)


# ── Archivos ─────────────────────────────────────────────────────
def upload_to(folder_id: str, filename: str, data: bytes,
              mime: str = "application/octet-stream") -> str:
    """Sube bytes a una carpeta cualquiera. Devuelve el fileId de Drive."""
    b = "===COPEXDOC==="
    meta = {"name": filename, "parents": [folder_id]}
    head = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + json.dumps(meta)
            + f"\r\n--{b}\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8")
    tail = f"\r\n--{b}--".encode("utf-8")
    body = head + (data or b"") + tail
    r = requests.post(_UPLOAD,
                      headers={**_headers(), "Content-Type": f"multipart/related; boundary={b}"},
                      params={"uploadType": "multipart", "fields": "id"}, data=body)
    r.raise_for_status()
    return r.json()["id"]


def upload(pid: str, filename: str, data: bytes, mime: str = "application/octet-stream") -> str:
    """Sube bytes a la carpeta del proyecto. Devuelve el fileId de Drive."""
    folder = project_folder(pid)
    b = "===COPEXDOC==="
    meta = {"name": filename, "parents": [folder]}
    head = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + json.dumps(meta)
            + f"\r\n--{b}\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8")
    tail = f"\r\n--{b}--".encode("utf-8")
    body = head + (data or b"") + tail
    r = requests.post(_UPLOAD,
                      headers={**_headers(), "Content-Type": f"multipart/related; boundary={b}"},
                      params={"uploadType": "multipart", "fields": "id"}, data=body)
    r.raise_for_status()
    return r.json()["id"]


@st.cache_data(ttl=300, show_spinner=False)
def download(file_id: str) -> bytes:
    """Descarga los bytes de un archivo (cacheado para no re-descargar en cada rerun)."""
    r = requests.get(f"{_API}/{file_id}", headers=_headers(), params={"alt": "media"})
    r.raise_for_status()
    return r.content


def delete(file_id: str):
    try:
        requests.delete(f"{_API}/{file_id}", headers=_headers())
    except Exception as e:
        logger.warning("drive_store: no se pudo borrar %s: %s", file_id, e)

# ══════════════════════════════════════════════════════════
#  Mantenimiento: inventario y limpieza (v456)
# ══════════════════════════════════════════════════════════
# ⚠️ La salvaguarda de fondo es el SCOPE: `drive.file` solo deja ver y tocar lo que
# ESTA app creó. Aunque estas funciones recorran «todo», no pueden alcanzar ni un
# archivo personal del usuario — por eso se puede ofrecer un borrado masivo sin que
# sea temerario. NO cambiar el scope sin revisar esto.


def _hijos(folder_id: str) -> list:
    """[{id, name, mimeType, size}] de lo que cuelga de una carpeta."""
    out, token = [], None
    while True:
        params = {"q": f"'{folder_id}' in parents and trashed = false",
                  "fields": "nextPageToken, files(id,name,mimeType,size)",
                  "spaces": "drive", "pageSize": 200}
        if token:
            params["pageToken"] = token
        r = requests.get(_API, headers=_headers(), params=params)
        r.raise_for_status()
        d = r.json()
        out += d.get("files", [])
        token = d.get("nextPageToken")
        if not token:
            return out


def inventario() -> dict:
    """Qué hay HOY en el Drive de la app: carpetas de primer nivel y su contenido.

    {raiz, carpetas:[{id, nombre, archivos:[...], n, bytes}], total, bytes}
    """
    # ⚠️ La raíz ES «COPEX Projects» (ROOT_NAME), así que las carpetas `PRJ-####`
    # cuelgan DIRECTAMENTE de ella — no hay un nivel intermedio. Mi primera versión
    # asumió `raíz / COPEX Projects / PRJ-#### / archivos` y buscaba los proyectos un
    # nivel más abajo del que están: resultado, **0 huérfanos con 32 archivos delante**.
    # Y la prueba con Drive simulado no lo cazó porque el mock reproducía MI suposición
    # en vez de la estructura real — el OK en falso de v309.
    root = _root_id()
    carpetas = []
    for f in _hijos(root):
        if f.get("mimeType") == FOLDER_MIME:
            hijos = _hijos(f["id"])
            carpetas.append({
                "id": f["id"], "nombre": f.get("name", ""),
                "archivos": [h for h in hijos if h.get("mimeType") != FOLDER_MIME],
                "subcarpetas": [h for h in hijos if h.get("mimeType") == FOLDER_MIME]})
    # Se sigue bajando un nivel más: un almacén como «COPEX Recibos» puede tener
    # subcarpetas propias, y así el recuento no se deja archivos fuera.
    for c in carpetas:
        for sub in c["subcarpetas"]:
            sub["archivos"] = [h for h in _hijos(sub["id"])
                               if h.get("mimeType") != FOLDER_MIME]
    def _n(c):
        return len(c["archivos"]) + sum(len(s.get("archivos", [])) for s in c["subcarpetas"])
    for c in carpetas:
        c["n"] = _n(c)
    return {"raiz": root, "carpetas": carpetas,
            "total": sum(c["n"] for c in carpetas)}


def borrar(ids: list) -> tuple:
    """Borra archivos o carpetas por id. Devuelve (borrados, [errores]).

    ⚠️ Devuelve los errores en vez de tragárselos como `delete()`: en una limpieza
    masiva, «no se pudo borrar 3 de 31» es justo lo que hay que saber (v323).
    """
    ok, errores = 0, []
    for fid in ids:
        try:
            r = requests.delete(f"{_API}/{fid}", headers=_headers())
            if r.status_code in (200, 204):
                ok += 1
            else:
                errores.append(f"{fid}: HTTP {r.status_code}")
        except Exception as e:
            errores.append(f"{fid}: {e}")
    if ok:
        # las carpetas están cacheadas 10 min: sin esto, la app seguiría creyendo que
        # existen y escribiría en un id que ya no está.
        for fn in (_root_id, project_folder, folder):
            try:
                fn.clear()
            except Exception as e:
                logger.warning("drive_store: no se pudo limpiar la caché: %s", e)
    return ok, errores
