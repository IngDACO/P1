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

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter, num as _num, parse_date as _parse_date

logger = logging.getLogger(__name__)

FACTURAS_SHEET = "Facturas"
FACTURAS_HEADERS = [
    "ID", "Grupo", "ClienteID", "ClienteNombre", "Numero", "Fecha", "Vencimiento",
    "LineasJSON", "Subtotal", "ImpuestoPct", "Impuesto", "Total",
    "Cobrado", "FechaCobro", "Estado", "Nota", "CreadoPor", "Creado",
    # v259: historial de cobros [{fecha, monto}] (Cobrado es el running total).
    "CobrosJSON",
]
_FCOL = {h: i + 1 for i, h in enumerate(FACTURAS_HEADERS)}



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


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(FACTURAS_SHEET, tuple(FACTURAS_HEADERS)), None
    except Exception as e:
        logger.warning("invoices: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {FACTURAS_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str):
    """Registros de FACTURAS_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(FACTURAS_SHEET, FACTURAS_HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(FACTURAS_SHEET))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _records_cached.clear()
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


def cobros_de(f: dict) -> list:
    """Historial de cobros [{fecha, monto}] de la factura."""
    try:
        return json.loads(f.get("CobrosJSON", "") or "[]")
    except Exception:
        return []


def estado_cobro(f: dict) -> str:
    """pendiente / parcial / cobrada / vencida / anulada (derivado de montos+fecha)."""
    if str(f.get("Estado", "")).lower() == "anulada":
        return "anulada"
    total, cob = _num(f.get("Total")), _num(f.get("Cobrado"))
    if total > 0 and cob >= total - 0.005:
        return "cobrada"
    # ⚠️ v345: VENCIDA gana a PARCIAL. Antes `parcial` se comprobaba primero, así que
    # **un abono de $1 sacaba a la factura de «vencida» para siempre**: el indicador
    # rojo del resumen y el `vencido` del P&L solo cuentan las `vencida`, y ese saldo
    # —que es el caso más común, el cliente que paga un anticipo y desaparece— no lo
    # veía nadie. Los tres sitios que suman lo vencido ya restan `Total − Cobrado`,
    # así que cuentan el saldo pendiente, no el total.
    venc = _parse_date(f.get("Vencimiento"))
    if venc and venc < clock.today():
        return "vencida"
    if cob > 0:
        return "parcial"
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


def pendiente_por_proyecto(grupo: str, incluir_archivados: bool = True) -> dict:
    """{ProyectoID: pendiente de facturar} de TODO el grupo, en una pasada (v397).

    Existe para poder mostrar el pendiente en la CARTERA sin llamar a
    `pendiente_de_facturar` una vez por fila — el patrón de `project_hours_bulk`
    (v145) y `gaps_by_group` (v107). Medido antes de ponerlo en la lista (regla
    v142): 16 obras cuestan ~32 ms y **0 llamadas nuevas a Sheets** en un rerun
    normal, porque todo sale de cachés ya vivas; en frío son 2 llamadas.

    ⚠️ Indexado por **ID**, no por nombre: dos obras pueden llamarse igual y un
    mapa por nombre colapsaría una de las dos en silencio (v306).
    ⚠️ Incluye ARCHIVADAS por defecto: archivar no es no-cobrar, y hoy 4 de las 9
    obras con pendiente lo están (v369).
    """
    # ⚠️ Import PEREZOSO: este módulo NO importa `projects` a nivel de módulo (lo
    # haría `projects` → `timeclock` → … y además nadie lo necesitaba hasta ahora).
    # Escribirlo como `P.list_projects` sin más habría sido un NameError (v342).
    from core import projects as _P
    out = {}
    for p in _P.list_projects(grupo=grupo, incluir_archivados=incluir_archivados):
        pid = str(p.get("ID", ""))
        try:
            v = pendiente_de_facturar(pid, grupo, p)
        except Exception as e:
            logger.warning("pendiente_por_proyecto %s: %s", pid, e)
            v = 0.0
        if v > 0:
            out[pid] = v
    return out


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
def _ids_frescos(col: str = "ID") -> list:
    """Los IDs LEÍDOS DE LA HOJA, saltándose la caché.

    ⚠️ v323: `_next_id` leía de `_records()`, que está cacheado **120 s** (TTL
    subido en v290). Si la caché no se invalidó —o se pobló entre la creación y
    la siguiente— el "siguiente" ID sale **repetido**, y en esta app *el ID es la
    identidad*: dos facturas con el mismo ID se pisan. Es ruta de ESCRITURA, así
    que lee fresco, igual que `toolruns._next_id` y `projects._find_row`.
    """
    w, err = _ws()
    if err or w is None:
        return []
    try:
        vals = w.get_all_values()
    except Exception as e:
        logger.warning("invoices: lectura fresca de IDs falló: %s", e)
        return []
    if not vals:
        return []
    try:
        i = vals[0].index(col)
    except ValueError:
        return []
    return [f[i] for f in vals[1:] if len(f) > i]


def _next_id() -> str:
    mx = 0
    for fid in _ids_frescos():
        fid = str(fid)
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
           clock.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps([])]
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
    prev = _num(f.get("Cobrado"))
    nuevo = min(_num(f.get("Total")), round(prev + _num(monto), 2))
    real = round(nuevo - prev, 2)                 # lo efectivamente sumado (respeta el tope)
    _fch = str(fecha or clock.today().isoformat())
    cobros = cobros_de(f)
    if real > 0:
        cobros.append({"fecha": _fch, "monto": real})
    try:
        w.batch_update([
            {"range": f"{_col_letter(_FCOL['Cobrado'])}{row}", "values": [[str(nuevo)]]},
            {"range": f"{_col_letter(_FCOL['FechaCobro'])}{row}", "values": [[_fch]]},
            {"range": f"{_col_letter(_FCOL['CobrosJSON'])}{row}",
             "values": [[json.dumps(cobros, ensure_ascii=False)]]},
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
