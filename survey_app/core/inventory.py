"""📦 Inventario — control de activos de la empresa vía QR (v263).

Cada activo tiene un registro (hoja `Activos`) y un QR que codifica un deep-link
a la app (`?activo=ACT-####`): al escanearlo se abre su ficha. Lleva ciclo de
vida (estado), ubicación/custodia, valor + depreciación (línea recta) y —en fases
siguientes— movimientos (entradas/salidas) y mantenimiento.

Hojas: `Activos` (registro) + `InvCategorias` (catálogo editable por grupo).
Multi-tenant, migran solas (`timeclock.get_sheet`). QR con `segno` (pure-python).
"""
import io
import logging
from datetime import date

import streamlit as st

from core import clock, timeclock

logger = logging.getLogger(__name__)

ACTIVOS_SHEET = "Activos"
ACTIVOS_HEADERS = [
    "ID", "Grupo", "Nombre", "Categoria", "Marca", "Modelo", "Serie",
    "FotoDriveID", "FechaCompra", "ValorCompra", "VidaUtilAnios",
    "Estado", "Condicion", "UbicacionTipo", "UbicacionRef", "AsignadoA",
    "FechaDevolucion", "ProximoMant", "Nota", "Activo", "CreadoPor", "Creado",
]
_ACOL = {h: i + 1 for i, h in enumerate(ACTIVOS_HEADERS)}

CAT_SHEET = "InvCategorias"
CAT_HEADERS = ["Grupo", "Nombre"]

ESTADOS = ["disponible", "en_uso", "mantenimiento", "dañado", "baja"]
CONDICIONES = ["bueno", "regular", "malo"]
UBIC_TIPOS = ["bodega", "proyecto", "usuario", "reparacion"]
CAT_DEFAULT = ["Herramienta", "Equipo", "Vehículo", "EPP", "Consumible", "Otro"]

_HEADERS = {ACTIVOS_SHEET: ACTIVOS_HEADERS, CAT_SHEET: CAT_HEADERS}


def is_configured() -> bool:
    return timeclock._secrets_present()


def app_url() -> str:
    """URL base de la app (secret APP_URL), para el deep-link del QR."""
    try:
        return str(st.secrets.get("APP_URL", "")).rstrip("/")
    except Exception:
        return ""


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _parse_date(v):
    try:
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return None


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws(title):
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(title, tuple(_HEADERS[title])), None
    except Exception as e:
        logger.warning("inventory: no se pudo abrir %s: %s", title, e)
        return None, f"No se pudo abrir la hoja {title}: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def _records(title):
    w, err = _ws(title)
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("inventory: lectura de %s falló: %s", title, e)
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


# ── Categorías (catálogo editable) ───────────────────────────────
def categorias(grupo: str) -> list:
    """Categorías del grupo: los defaults + las añadidas (dedup, ordenadas)."""
    extra = [str(r.get("Nombre", "")).strip() for r in _records(CAT_SHEET)
             if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")).strip()]
    return sorted(set(CAT_DEFAULT) | set(extra), key=str.lower)


def add_categoria(grupo: str, nombre: str) -> tuple:
    nombre = str(nombre or "").strip()
    if not nombre:
        return False, "Nombre vacío."
    if nombre in categorias(grupo):
        return False, "Esa categoría ya existe."
    w, err = _ws(CAT_SHEET)
    if err:
        return False, err
    w.append_row([grupo, nombre], value_input_option="RAW")
    _invalidate()
    return True, "Categoría añadida."


def del_categoria(grupo: str, nombre: str) -> tuple:
    w, err = _ws(CAT_SHEET)
    if err:
        return False, err
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")).strip() == str(nombre).strip():
            w.delete_rows(i + 2)
            _invalidate()
            return True, "Categoría eliminada."
    return False, "No se encontró (¿es una por defecto? esas no se quitan)."


# ── Activos ──────────────────────────────────────────────────────
def list_activos(grupo: str = None, incluir_baja: bool = False) -> list:
    out = []
    for r in _records(ACTIVOS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if not incluir_baja and str(r.get("Activo", "SI")).upper() in ("NO", "FALSE", "0"):
            continue
        out.append(r)
    return out


def get_activo(aid: str) -> dict:
    for r in _records(ACTIVOS_SHEET):
        if str(r.get("ID", "")) == str(aid):
            return r
    return {}


def _next_id() -> str:
    mx = 0
    for r in _records(ACTIVOS_SHEET):
        aid = str(r.get("ID", ""))
        if aid.startswith("ACT-"):
            try:
                mx = max(mx, int(aid.split("-")[1]))
            except Exception:
                pass
    return f"ACT-{mx + 1:04d}"


def create_activo(grupo, nombre, categoria="", marca="", modelo="", serie="",
                  foto_id="", fecha_compra="", valor_compra="", vida_util="",
                  condicion="bueno", ubicacion_tipo="bodega", ubicacion_ref="",
                  proximo_mant="", nota="", creado_por="") -> tuple:
    """Registra un activo (estado inicial 'disponible'). Devuelve (ok, id|error)."""
    w, err = _ws(ACTIVOS_SHEET)
    if err:
        return False, err
    if not str(nombre or "").strip():
        return False, "El nombre del activo es obligatorio."
    aid = _next_id()
    row = [aid, grupo, str(nombre).strip(), str(categoria or ""), str(marca or ""),
           str(modelo or ""), str(serie or ""), str(foto_id or ""),
           str(fecha_compra or ""), str(_num(valor_compra)), str(_num(vida_util)),
           "disponible", str(condicion or "bueno"), str(ubicacion_tipo or "bodega"),
           str(ubicacion_ref or ""), "", "", str(proximo_mant or ""),
           str(nota or ""), "SI", str(creado_por or ""),
           clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, aid


def update_activo(aid: str, fields: dict) -> tuple:
    w, err = _ws(ACTIVOS_SHEET)
    if err:
        return False, err
    row = None
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("ID", "")) == str(aid):
            row = i + 2
            break
    if row is None:
        return False, "Activo no encontrado."
    batch = [{"range": f"{_col_letter(_ACOL[k])}{row}", "values": [[str(v)]]}
             for k, v in fields.items() if k in _ACOL]
    if batch:
        try:
            w.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, str(e)
    _invalidate()
    return True, "Activo actualizado."


def dar_de_baja(aid: str, motivo: str = "") -> tuple:
    return update_activo(aid, {"Activo": "NO", "Estado": "baja",
                               "Nota": (motivo or "Dado de baja")})


# ── Valor / depreciación (línea recta) ───────────────────────────
def valor_actual(a: dict) -> float:
    """Valor depreciado (línea recta): compra × (1 − años/vida útil), ≥ 0."""
    vc = _num(a.get("ValorCompra"))
    vida = _num(a.get("VidaUtilAnios"))
    fc = _parse_date(a.get("FechaCompra"))
    if vc <= 0 or vida <= 0 or not fc:
        return round(vc, 2)
    anios = (clock.today() - fc).days / 365.25
    return round(max(0.0, vc * (1 - anios / vida)), 2)


def resumen(grupo: str) -> dict:
    acts = list_activos(grupo)
    hoy = clock.today()
    por_estado = {}
    v_compra = v_actual = 0.0
    mant_venc = 0
    for a in acts:
        por_estado[a.get("Estado", "")] = por_estado.get(a.get("Estado", ""), 0) + 1
        v_compra += _num(a.get("ValorCompra"))
        v_actual += valor_actual(a)
        pm = _parse_date(a.get("ProximoMant"))
        if pm and pm < hoy:
            mant_venc += 1
    return {"n": len(acts), "por_estado": por_estado,
            "valor_compra": round(v_compra, 2), "valor_actual": round(v_actual, 2),
            "mant_vencido": mant_venc}


# ── QR ───────────────────────────────────────────────────────────
def qr_data(aid: str) -> str:
    base = app_url()
    return f"{base}/?activo={aid}" if base else str(aid)


def qr_png(aid: str, scale: int = 6) -> bytes:
    """PNG del QR (deep-link a la app). `segno` es pure-python (sin pillow)."""
    import segno
    buf = io.BytesIO()
    segno.make(qr_data(aid), error="m").save(buf, kind="png", scale=scale, border=2)
    return buf.getvalue()
