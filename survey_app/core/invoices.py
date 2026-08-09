"""Facturas a clientes (cuentas por cobrar) — Fase 2 del módulo financiero.

Hoja `Facturas`, multi-tenant. Una factura le cobra a un cliente por una o varias
líneas (mano de obra a tarifa de venta, materiales, ítems libres), con impuesto
(GST/IVA) editable. Se registra cuánto se ha **cobrado** → estado
pendiente/parcial/cobrada/vencida. Para **no cobrar dos veces**, se lleva lo
**facturado por proyecto** (suma de las líneas con `proyecto_id`), y lo pendiente
de facturar = ingreso estimado (finance) − ya facturado.

Patrón calcado de projects.py/clientes.py (hoja cacheada + invalidación + batch).
"""
import json
import logging
from datetime import date

import streamlit as st

from core import clock, timeclock

logger = logging.getLogger(__name__)

FACTURAS_SHEET = "Facturas"
FACTURAS_HEADERS = [
    "ID", "Grupo", "ClienteID", "ClienteNombre", "Numero", "Fecha", "Vencimiento",
    "LineasJSON", "Subtotal", "ImpuestoPct", "Impuesto", "Total",
    "Cobrado", "FechaCobro", "Estado", "Nota", "CreadoPor", "Creado",
]
_FCOL = {h: i + 1 for i, h in enumerate(FACTURAS_HEADERS)}


def is_configured() -> bool:
    return timeclock._secrets_present()


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
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(FACTURAS_SHEET, tuple(FACTURAS_HEADERS)), None
    except Exception as e:
        logger.warning("invoices: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {FACTURAS_SHEET}: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def _records():
    w, err = _ws()
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("invoices: lectura falló: %s", e)
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


# ── Lecturas de dominio ──────────────────────────────────────────
def list_facturas(grupo: str = None, cliente_id: str = None) -> list:
    out = []
    for r in _records():
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if cliente_id is not None and str(r.get("ClienteID", "")) != str(cliente_id):
            continue
        out.append(r)
    return out


def get_factura(fid: str) -> dict:
    for r in _records():
        if str(r.get("ID", "")) == str(fid):
            return r
    return {}


def lineas_de(f: dict) -> list:
    try:
        return json.loads(f.get("LineasJSON", "") or "[]")
    except Exception:
        return []


def estado_cobro(f: dict) -> str:
    """pendiente / parcial / cobrada / vencida / anulada (derivado de montos+fecha)."""
    if str(f.get("Estado", "")).lower() == "anulada":
        return "anulada"
    total, cob = _num(f.get("Total")), _num(f.get("Cobrado"))
    if total > 0 and cob >= total - 0.005:
        return "cobrada"
    if cob > 0:
        return "parcial"
    venc = _parse_date(f.get("Vencimiento"))
    if venc and venc < clock.today():
        return "vencida"
    return "pendiente"


def facturado_por_proyecto(grupo: str) -> dict:
    """{ProyectoID: importe facturado} sumando las líneas (no cuenta anuladas)."""
    out = {}
    for f in list_facturas(grupo):
        if str(f.get("Estado", "")).lower() == "anulada":
            continue
        for ln in lineas_de(f):
            pid = str(ln.get("proyecto_id", "")).strip()
            if pid:
                out[pid] = out.get(pid, 0.0) + _num(ln.get("importe"))
    return {k: round(v, 2) for k, v in out.items()}


def pendiente_de_facturar(pid: str, grupo: str, prj: dict = None) -> float:
    """Ingreso estimado del proyecto − lo ya facturado (para precargar una factura)."""
    from core import finance as F
    ingreso = F.project_revenue(pid, grupo, prj)["ingreso"]
    ya = facturado_por_proyecto(grupo).get(str(pid), 0.0)
    return round(max(0.0, ingreso - ya), 2)


def resumen_cliente(grupo: str, cliente_id: str) -> dict:
    """{facturado, cobrado, pendiente, vencido, n} de un cliente."""
    fac = cob = venc = 0.0
    n = 0
    for f in list_facturas(grupo, cliente_id):
        if str(f.get("Estado", "")).lower() == "anulada":
            continue
        n += 1
        fac += _num(f.get("Total"))
        cob += _num(f.get("Cobrado"))
        if estado_cobro(f) == "vencida":
            venc += _num(f.get("Total")) - _num(f.get("Cobrado"))
    return {"facturado": round(fac, 2), "cobrado": round(cob, 2),
            "pendiente": round(fac - cob, 2), "vencido": round(venc, 2), "n": n}


# ── Escrituras ───────────────────────────────────────────────────
def _next_id() -> str:
    mx = 0
    for r in _records():
        fid = str(r.get("ID", ""))
        if fid.startswith("FAC-"):
            try:
                mx = max(mx, int(fid.split("-")[1]))
            except Exception:
                pass
    return f"FAC-{mx + 1:04d}"


def _next_numero(grupo: str) -> int:
    mx = 0
    for r in _records():
        if str(r.get("Grupo", "")) == str(grupo):
            try:
                mx = max(mx, int(_num(r.get("Numero"))))
            except Exception:
                pass
    return mx + 1


def create_factura(grupo, cliente_id, cliente_nombre, lineas, impuesto_pct=0.0,
                   fecha="", vencimiento="", numero="", nota="", creado_por="") -> tuple:
    """Crea (emite) una factura. `lineas` = [{concepto, importe, proyecto_id}]. (ok, id|error)."""
    w, err = _ws()
    if err:
        return False, err
    lineas = [ln for ln in (lineas or []) if _num(ln.get("importe")) != 0 or str(ln.get("concepto", "")).strip()]
    if not lineas:
        return False, "La factura no tiene líneas."
    subtotal = round(sum(_num(ln.get("importe")) for ln in lineas), 2)
    impuesto = round(subtotal * _num(impuesto_pct) / 100.0, 2)
    total = round(subtotal + impuesto, 2)
    fid = _next_id()
    num = str(numero).strip() or f"{_next_numero(grupo):04d}"
    row = [fid, grupo, str(cliente_id or ""), str(cliente_nombre or ""), num,
           str(fecha or clock.today().isoformat()), str(vencimiento or ""),
           json.dumps(lineas, ensure_ascii=False, default=str),
           str(subtotal), str(_num(impuesto_pct)), str(impuesto), str(total),
           "0", "", "emitida", str(nota or ""), str(creado_por or ""),
           clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, fid


def _find_row(w, fid):
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("ID", "")) == str(fid):
            return i + 2
    return None


def registrar_cobro(fid: str, monto, fecha="") -> tuple:
    """Suma un cobro a la factura (running total, tope = Total)."""
    w, err = _ws()
    if err:
        return False, err
    f = get_factura(fid)
    if not f:
        return False, "Factura no encontrada."
    row = _find_row(w, fid)
    if row is None:
        return False, "Factura no encontrada."
    nuevo = min(_num(f.get("Total")), round(_num(f.get("Cobrado")) + _num(monto), 2))
    try:
        w.batch_update([
            {"range": f"{_col_letter(_FCOL['Cobrado'])}{row}", "values": [[str(nuevo)]]},
            {"range": f"{_col_letter(_FCOL['FechaCobro'])}{row}",
             "values": [[str(fecha or clock.today().isoformat())]]},
        ], value_input_option="RAW")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, "Cobro registrado."


def anular(fid: str) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    row = _find_row(w, fid)
    if row is None:
        return False, "Factura no encontrada."
    try:
        w.update_cell(row, _FCOL["Estado"], "anulada")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, "Factura anulada."
