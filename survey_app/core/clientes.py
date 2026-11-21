"""Gestión de clientes (CRM básico) — hoja `Clientes`, multi-tenant por grupo.

Hasta ahora un cliente era solo el texto libre `Cliente` de cada proyecto: no
había dónde guardar persona de contacto, teléfono, email, dirección ni notas.
Este módulo añade la ENTIDAD cliente (con esa info) sin migrar nada: el enlace
cliente↔proyectos se resuelve **por nombre normalizado** (el `Cliente` del
proyecto). Más adelante se puede añadir un `ClienteID` al proyecto para robustez.

Sigue los mismos patrones que `projects.py`: handle de hoja cacheado vía
`timeclock.get_sheet` (crea/migra la cabecera una vez), lecturas cacheadas 30 s
con invalidación al escribir, y escrituras en batch.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core import columnas
from core.num import col_letter as _col_letter
from core.num import num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

CLIENTES_SHEET = "Clients"
CLIENTES_HEADERS = [
    "ID", "Group", "Name", "ContactName", "Phone", "Email",
    "Address", "Notes", "Active", "CreatedBy", "Created",
]
_CCOL = {h: i + 1 for i, h in enumerate(CLIENTES_HEADERS)}



def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""

def is_configured() -> bool:
    return timeclock._secrets_present()


def _norm(s) -> str:
    """Nombre normalizado para casar cliente↔proyecto (sin may/min ni espacios dobles)."""
    return " ".join(str(s or "").strip().lower().split())


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, t("Google Sheets is not configured.")
    try:
        return timeclock.get_sheet(CLIENTES_SHEET, tuple(CLIENTES_HEADERS)), None
    except Exception as e:
        logger.warning("clientes: no se pudo abrir la hoja: %s", e)
        return None, f"{t('Could not open sheet')} {CLIENTES_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str):
    """Registros de CLIENTES_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(CLIENTES_SHEET, CLIENTES_HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(CLIENTES_SHEET))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar(CLIENTES_SHEET)
    try:
        _records_cached.clear()
    except Exception:
        pass


# ── Lecturas de dominio ──────────────────────────────────────────
def list_clientes(grupo: str = None, incluir_inactivos: bool = False) -> list:
    """Fichas de cliente del grupo (las que tienen fila en la hoja)."""
    out = []
    for r in _records():
        if grupo is not None and str(r.get("Group", "")) != str(grupo):
            continue
        if not incluir_inactivos and str(r.get("Active", "SI")).upper() in ("NO", "FALSE", "0"):
            continue
        out.append(r)
    return out


def get_cliente(cid: str) -> dict:
    for r in _records():
        if str(r.get("ID", "")) == str(cid):
            return r
    return {}


# ── Escrituras ───────────────────────────────────────────────────
def _ids_frescos(col: str = "ID") -> list:
    """Los IDs LEÍDOS DE LA HOJA, saltándose la caché (ver `invoices._ids_frescos`).

    ⚠️ v323: `_next_id` leía de `_records()` (cacheado 120 s desde v290) y podía
    devolver un ID **ya usado**. El ID es la identidad: dos clientes con el mismo
    CLI-#### se pisan y los proyectos enlazados apuntan al equivocado.
    """
    w, err = _ws()
    if err or w is None:
        return []
    try:
        vals = w.get_all_values()
    except Exception as e:
        logger.warning("clientes: lectura fresca de IDs falló: %s", e)
        return []
    if not vals:
        return []
    try:
        i = vals[0].index(col)
    except ValueError:
        return []
    return [f[i] for f in vals[1:] if len(f) > i]


def _next_id() -> str:
    """CLI-#### incremental. Lee FRESCO (es escritura) y **salta los referenciados**.

    ⚠️ v427: un ID reciclado arrastra lo que colgaba del anterior. Aquí la ficha del
    cliente es la que enlazan proyectos, cotizaciones y facturas por `ClienteID`, así
    que reutilizar un CLI-#### le pegaría a un cliente nuevo la facturación de otro.
    """
    mx = 0
    for cid in _ids_frescos():
        cid = str(cid)
        if cid.startswith("CLI-"):
            try:
                mx = max(mx, int(cid.split("-")[1]))
            except Exception:
                pass
    try:
        from core import hojas
        return hojas.siguiente_id_libre("CLI-", mx, propia=CLIENTES_SHEET)
    except Exception as e:
        logger.warning("clientes: no se pudo comprobar IDs referenciados: %s", e)
        return f"CLI-{mx + 1:04d}"


def email_valido(email) -> bool:
    """v602 · Vacío vale (es opcional); si hay algo, que tenga forma de email (`a@b.c`).

    Se guardaba cualquier cosa («abc») y el contacto quedaba inservible sin que nadie lo viera.
    """
    import re
    e = str(email or "").strip()
    return not e or bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e))


def solo_digitos(s) -> str:
    """v602 · Los dígitos de un teléfono, para buscarlo con o sin espacios («02 9000 1003»)."""
    return "".join(ch for ch in str(s or "") if ch.isdigit())


TELEFONO_MIN_DIGITOS = 6


def telefono_valido(tel) -> bool:
    """v690 · Vacío vale (es opcional); si hay algo, que sea un teléfono: dígitos, espacios, «+», «-», «(», «)» y «.»,
    con `TELEFONO_MIN_DIGITOS` dígitos al menos. Ciclo 5 (H1): «abc» se guardaba sin aviso y el enlace «call» no salía."""
    import re
    s = str(tel or "").strip()
    return not s or (bool(re.fullmatch(r"[0-9+\-() .]+", s)) and len(solo_digitos(s)) >= TELEFONO_MIN_DIGITOS)


def _aviso_telefono() -> str:
    return t("That phone number does not look right (digits, spaces, + and dashes only, at least {n} digits).",
             n=TELEFONO_MIN_DIGITOS)


def create_cliente(grupo, nombre, contacto="", telefono="", email="",
                   direccion="", notas="", creado_por="") -> tuple:
    """Crea una ficha de cliente. Devuelve (ok, id|error)."""
    w, err = _ws()
    if err:
        return False, err
    nombre = str(nombre or "").strip()
    if not nombre:
        return False, t("The client name is required.")
    if not email_valido(email):
        return False, t("That email does not look right (it should be like name@company.com).")
    if not telefono_valido(telefono):                       # v690 · H1
        return False, _aviso_telefono()
    for r in _records():
        if str(r.get("Group", "")) == str(grupo) and _norm(r.get("Name")) == _norm(nombre):
            return False, t("A client with that name already exists in this group.")
    cid = _next_id()
    row = [cid, grupo, nombre, str(contacto or ""), str(telefono or ""),
           str(email or ""), str(direccion or ""), str(notas or ""),
           "SI", str(creado_por or ""), clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, cid


def update_cliente(cid: str, fields: dict) -> tuple:
    """Actualiza columnas sueltas de la ficha (fields = {Header: valor}), 1 batch."""
    if "Email" in fields and not email_valido(fields.get("Email")):
        return False, t("That email does not look right (it should be like name@company.com).")
    if "Phone" in fields and not telefono_valido(fields.get("Phone")):       # v690 · H1
        return False, _aviso_telefono()
    if "Name" in fields and not " ".join(str(fields.get("Name") or "").split()):
        return False, t("The client name is required.")
    w, err = _ws()
    if err:
        return False, err
    row = None
    try:
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))   # fresco al escribir
    except Exception as e:
        return False, str(e)
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cid):
            row = i + 2  # +1 cabecera, +1 base-1
            break
    if row is None:
        return False, t("Client not found.")
    batch = [{"range": f"{_col_letter(_CCOL[k])}{row}", "values": [[str(v)]]}
             for k, v in fields.items() if k in _CCOL]
    if batch:
        try:
            w.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, str(e)
    _invalidate()
    return True, t("Client updated.")


def set_activo(cid: str, activo: bool) -> tuple:
    """Archivar / restaurar, con SU mensaje (v602: archivar volvía a la lista sin decir nada)."""
    ok, msg = update_cliente(cid, {"Active": "SI" if activo else "NO"})
    if not ok:
        return ok, msg
    return True, t("Client restored.") if activo else t("Client archived.")


def renombrar(cid, nuevo, grupo) -> tuple:
    """Cambia el NOMBRE de un cliente (v690, ciclo 5 H2: la ficha no dejaba corregirlo).

    El ID es la identidad (las obras, cotizaciones y facturas se enlazan por `ClientID`), pero varias guardan además
    el nombre en texto. Se actualiza lo que NO es un documento emitido: la ficha, el texto «Client» de sus obras (y, a
    una obra sin ID que casaba por el nombre viejo, se le pone el ID) y sus cotizaciones en BORRADOR. Lo ya emitido
    (cotizaciones enviadas, facturas) conserva el nombre con que salió: es lo que tiene el cliente en la mano.
    `(ok, mensaje)`."""
    nuevo = " ".join(str(nuevo or "").split())
    if not nuevo:
        return False, t("The client name is required.")
    f = get_cliente(cid)
    if not f or str(f.get("Group", "")) != str(grupo):
        return False, t("Client not found.")
    viejo = str(f.get("Name", "") or "")
    if viejo == nuevo:
        return True, t("Nothing changed.")
    for r in _records():
        if (str(r.get("Group", "")) == str(grupo) and str(r.get("ID", "")) != str(cid)
                and _norm(r.get("Name")) == _norm(nuevo)):
            return False, t("A client with that name already exists in this group.")
    ok, msg = update_cliente(cid, {"Name": nuevo})
    if not ok:
        return ok, msg
    n_obras = 0
    try:
        from core import projects as P
        for p in P.list_projects(grupo=grupo, incluir_archivados=True):
            if es_del_cliente(p, cid, _norm(viejo)) and (str(p.get("Client", "")) != nuevo
                                                         or str(p.get("ClientID", "")) != str(cid)):
                _ok_p, _ = P.update_project(str(p.get("ID", "")), {"Client": nuevo, "ClientID": cid})
                n_obras += 1 if _ok_p else 0
    except Exception as e:
        logger.warning("clientes.renombrar: las obras de %s no se actualizaron: %s", cid, e)
    n_borr = 0
    try:
        from core import quotes as Q
        n_borr = Q.renombrar_cliente_borradores(grupo, cid, nuevo)
    except Exception as e:
        logger.warning("clientes.renombrar: los borradores de %s no se actualizaron: %s", cid, e)
    return True, t("Client renamed: «{a}» → «{b}». Updated: {o} project(s) and {q} draft quote(s). Quotes already sent "
                   "and invoices keep the name they were issued with.", a=viejo, b=nuevo, o=n_obras, q=n_borr)


def abierto(grupo, cid, proys=None) -> list:
    """Lo que un cliente tiene ABIERTO, en frases (v690, ciclo 5 H18): obras sin terminar, cotizaciones esperando
    respuesta (la versión vigente de cada trato) y lo que queda por cobrar. Para avisar antes de archivarlo."""
    out = []
    try:
        if proys is None:
            from core import projects as P
            _f = get_cliente(cid)
            proys = [p for p in P.list_projects(grupo=grupo) if es_del_cliente(p, cid, _norm(_f.get("Name")))]
        _vivas = [p for p in proys if str(p.get("Status", "")) not in ("Completed", "Cancelled", "Archived")]
        if _vivas:
            out.append(t("{n} job(s) not finished", n=len(_vivas)))
    except Exception as e:
        logger.warning("clientes.abierto obras %s: %s", cid, e)
    try:
        from core import quotes as Q
        _qs = Q.list_cotizaciones(grupo, cliente_id=cid)
        _esp = [x for x in Q.vistas(_qs).values() if x in (Q.ENVIADA, Q.VENCIDA)]
        if _esp:
            out.append(t("{n} quote(s) awaiting a reply", n=len(_esp)))
    except Exception as e:
        logger.warning("clientes.abierto cotizaciones %s: %s", cid, e)
    try:
        from core import invoices as INV
        _pend = sum(_num(f.get("Total")) - _num(f.get("Collected")) for f in INV.list_facturas(grupo, cid)
                    if str(f.get("Status", "")).lower() != "anulada")
        if _pend > 0.005:
            out.append(t("${x} still to collect", x=f"{_pend:,.2f}"))
    except Exception as e:
        logger.warning("clientes.abierto facturas %s: %s", cid, e)
    return out


def ficha_de(grupo, clave) -> dict:
    """v602 · La ficha que abre la lista: por su ID (CLI-…) o, para lo que llega por NOMBRE
    (Invoices, una obra), por el nombre normalizado — en las dos, ARCHIVADAS incluidas.

    ⚠️ La ficha buscaba solo entre las ACTIVAS y por nombre: una archivada salía «no record
    yet», sin «Restore», y «Save record» respondía «already exists» (visto en producción: un
    cliente archivado no se podía recuperar). El ID es la identidad; el nombre, el respaldo
    (dentro de un grupo no se repite: `create_cliente` lo impide, archivadas incluidas).
    """
    clave = str(clave or "").strip()
    fichas = list_clientes(grupo, incluir_inactivos=True)
    for f in fichas:
        if str(f.get("ID", "")) == clave:
            return f
    for f in fichas:
        if _norm(f.get("Name")) == _norm(clave):
            return f
    return {}


# ── Enlace cliente↔proyecto (ID-primero, nombre-de-respaldo) ─────
def es_del_cliente(proyecto: dict, cid: str, nombre_norm: str) -> bool:
    """¿El proyecto pertenece a este cliente?

    Regla única (como `timeclock.es_del_proyecto`, v145): si el proyecto tiene
    `ClienteID`, manda ese; si no, cae al `Cliente` (texto) normalizado. Así un
    proyecto vinculado por ID sigue casando aunque le renombren el texto, y los
    proyectos viejos (sin ID) siguen casando por nombre.
    """
    pid_cli = str(proyecto.get("ClientID", "")).strip()
    if pid_cli:
        return bool(cid) and pid_cli == str(cid)
    return _norm(proyecto.get("Client")) == nombre_norm


def client_key(proyecto: dict, fichas_by_id: dict):
    """(clave_normalizada, display) del cliente de un proyecto.

    Si el `ClienteID` resuelve a una ficha, se agrupa bajo el NOMBRE de la ficha
    (aunque el texto `Cliente` difiera); si no, bajo el texto `Cliente`.
    """
    pid_cli = str(proyecto.get("ClientID", "")).strip()
    f = fichas_by_id.get(pid_cli) if pid_cli else None
    nom = (f.get("Name") if f else str(proyecto.get("Client", "")).strip())
    return _norm(nom), nom
