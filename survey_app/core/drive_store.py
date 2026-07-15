"""
Almacenamiento de documentos de proyecto en Google Drive (OAuth de usuario, scope drive.file).

Secrets (Streamlit):
  [gdrive]
  client_id     = "..."
  client_secret = "..."
  refresh_token = "..."
  # opcional: root_folder_id = "..."  (carpeta raíz; si no, se crea 'COPEX Proyectos')

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
ROOT_NAME   = "COPEX Proyectos"
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
    return rid or _find_folder(ROOT_NAME) or _create_folder(ROOT_NAME)


@st.cache_data(ttl=600, show_spinner=False)
def project_folder(pid: str) -> str:
    """Id de la carpeta del proyecto (la crea si no existe)."""
    root = _root_id()
    return _find_folder(pid, parent=root) or _create_folder(pid, parent=root)


@st.cache_data(ttl=600, show_spinner=False)
def folder(name: str) -> str:
    """Id de una subcarpeta con nombre `name` bajo la raíz (la crea si no existe).
    Útil para almacenes que no son de un proyecto (p. ej. 'COPEX Manuales')."""
    root = _root_id()
    return _find_folder(name, parent=root) or _create_folder(name, parent=root)


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
