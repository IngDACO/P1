"""Órdenes de compra: el dinero COMPROMETIDO, que hasta ahora era invisible (v343).

## Por qué

`expenses` responde «cuánto llevas gastado»: una compra existe cuando hay un recibo.
Pero el material se **encarga** semanas antes de que llegue la factura, así que entre
el pedido y el recibo el proyecto aparece dentro de presupuesto mientras el dinero ya
está comprometido. El administrador se entera del sobrecosto cuando ya no puede hacer
nada — que es exactamente el problema que `cost_projection` resolvió para la mano de
obra en v144.

## Una sola definición de GASTO

⚠️ Una orden **no es** un gasto. Al recibirla se crea la fila en `Gastos`, así que el
costo real sigue teniendo UNA fuente (regla v310: había llegado a haber tres respuestas
a la misma pregunta). Aquí solo vive lo pendiente de recibir.

## El orden de las dos escrituras importa

Recibir = marcar la orden + crear el gasto. Si se creara el gasto primero y fallara el
marcado, la orden seguiría pendiente y al reintentar habría **dos gastos** por la misma
compra: el costo saldría inflado sin que nadie lo vea. Por eso se marca PRIMERO y se
crea el gasto después: si falla lo segundo, el costo queda corto pero la orden queda
marcada `recibida` **sin GastoID**, y eso `sin_gasto()` lo detecta y la UI lo enseña
con un botón para completarlo. Un hueco visible es mejor que un doble cargo invisible.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter
from core.num import num as _num
from core.num import parse_date as _parse_date

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "PurchaseOrders"
HEADERS = ["ID", "Grupo", "ProyectoID", "Proveedor", "Descripcion", "Categoria",
           "Valor", "Fecha", "FechaEsperada", "Estado", "GastoID", "RecibidaFecha",
           "Nota", "CreadoPor", "Creado"]

PENDIENTE, RECIBIDA, CANCELADA = "pendiente", "recibida", "cancelada"
ESTADOS = (PENDIENTE, RECIBIDA, CANCELADA)

_COL = {h: i + 1 for i, h in enumerate(HEADERS)}



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


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("orders: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: `registros(t, cabeceras)` cae a `get_sheet`, que CREA la
    hoja (regla v145). La crea la primera ESCRITURA, no una lectura."""
    from core import hojas                      # perezoso: evita el ciclo con timeclock
    return hojas.registros(SHEET) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(SHEET))
def _invalidate():
    from core import hojas                      # v339: hay que tirar también el LOTE
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception:
        pass


# ── Lecturas ─────────────────────────────────────────────────────
def list_for(pid, estado=None) -> list:
    out = [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]
    if estado:
        out = [r for r in out if str(r.get("Estado", "")) == estado]
    return sorted(out, key=lambda r: str(r.get("Fecha", "")), reverse=True)


def list_group(grupo, estado=None) -> list:
    out = [r for r in _records() if str(r.get("Grupo", "")) == str(grupo)]
    if estado:
        out = [r for r in out if str(r.get("Estado", "")) == estado]
    return sorted(out, key=lambda r: str(r.get("Fecha", "")), reverse=True)


def comprometido(pid) -> float:
    """Lo pedido y aún no recibido de un proyecto. Solo PENDIENTE cuenta:
    lo recibido ya vive en `Gastos` y lo cancelado no se debe."""
    return round(sum(_num(r.get("Valor")) for r in list_for(pid, PENDIENTE)), 2)


def comprometido_por_proyecto(grupo) -> dict:
    """{pid: comprometido} en UNA pasada — para las vistas de grupo, que si no
    llamarían a `comprometido()` una vez por proyecto."""
    out = {}
    for r in _records():
        if str(r.get("Grupo", "")) != str(grupo) or str(r.get("Estado", "")) != PENDIENTE:
            continue
        pid = str(r.get("ProyectoID", ""))
        out[pid] = round(out.get(pid, 0.0) + _num(r.get("Valor")), 2)
    return out


def atrasadas(grupo) -> list:
    """Pendientes cuya fecha esperada ya pasó: lo que hay que reclamar al proveedor.

    ⚠️ Una orden **sin** fecha esperada nunca sale atrasada — no se puede afirmar
    que llega tarde si nadie dijo cuándo llegaba.
    """
    hoy, out = clock.today(grupo), []
    for r in list_group(grupo, PENDIENTE):
        f = _parse_date(r.get("FechaEsperada"))
        if f and f < hoy:
            out.append({**r, "dias": (hoy - f).days})
    return sorted(out, key=lambda x: -x["dias"])


def sin_gasto(grupo) -> list:
    """Recibidas a las que les falta su fila en `Gastos` (ver la nota de arriba):
    su costo NO está contado en ningún sitio hasta que se complete."""
    return [r for r in list_group(grupo, RECIBIDA)
            if not str(r.get("GastoID", "")).strip()]


# ── Escrituras ───────────────────────────────────────────────────
def _next_id() -> str:
    """⚠️ Lee FRESCO, nunca de la caché: un ID sacado de datos de hasta 120 s puede
    salir REPETIDO, y el ID es la identidad (v323)."""
    w = _ws()
    if w is None:
        return "ORD-00001"
    mx = 0
    try:
        for r in w.get_all_records(numericise_ignore=["all"]):
            i = str(r.get("ID", ""))
            if i.startswith("ORD-"):
                try:
                    mx = max(mx, int(i.split("-")[1]))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("orders._next_id: %s", e)
    return f"ORD-{mx + 1:05d}"


def crear(pid, grupo, proveedor, valor, descripcion="", categoria="Materiales",
          fecha_esperada="", nota="", creado_por="") -> tuple:
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    if _num(valor) <= 0:
        return False, t("The order value must be greater than 0.")
    if not str(proveedor).strip():
        return False, t("Enter the supplier.")
    oid = _next_id()
    try:
        w.append_row([oid, str(grupo), str(pid), str(proveedor).strip(),
                      str(descripcion), str(categoria), str(_num(valor)),
                      clock.now(grupo).strftime("%Y-%m-%d"), str(fecha_esperada or ""),
                      PENDIENTE, "", "", str(nota), str(creado_por),
                      clock.now(grupo).strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving the order')}: {e}"
    _invalidate()
    return True, f"{t('Order')} {oid} {t('recorded.')}"


def _fila(w, oid):
    """(nº de fila 1-based, registro) leyendo FRESCO: decidir DÓNDE escribir con
    una caché es como se corrompen los datos (v323)."""
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("orders._fila: %s", e)
        return None, None
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(oid):
            return i + 2, r
    return None, None


def _set(w, row, campos: dict) -> tuple:
    """Varias columnas de una fila en UNA sola llamada (patrón v80)."""
    lote = [{"range": f"{_col_letter(_COL[k])}{row}", "values": [[str(v)]]}
            for k, v in campos.items() if k in _COL]
    if not lote:
        return True, ""
    try:
        w.batch_update(lote, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating')}: {e}"
    return True, ""


def marcar_recibida(oid, valor_real=None, creado_por="") -> tuple:
    """Marca la orden y crea su gasto. En ESTE orden (ver la nota del módulo)."""
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    row, r = _fila(w, oid)
    if row is None:
        return False, t("Order not found.")
    if str(r.get("Estado", "")) == RECIBIDA and str(r.get("GastoID", "")).strip():
        return False, t("That order was already received.")
    valor = _num(valor_real) if valor_real not in (None, "") else _num(r.get("Valor"))
    if valor <= 0:
        return False, t("The received value must be greater than 0.")

    ok, err = _set(w, row, {"Estado": RECIBIDA,
                            "RecibidaFecha": clock.now(r.get("Grupo")).strftime("%Y-%m-%d")})
    if not ok:
        return False, err
    _invalidate()

    ok_g, msg_g = _crear_gasto(r, valor, creado_por)
    if not ok_g:
        # ⚠️ La orden queda marcada y SIN GastoID a propósito: `sin_gasto()` la
        # detecta y se puede completar. Duplicar el gasto sería peor.
        return False, (f"{t('Marked as received, but the expense was NOT recorded')} ({msg_g}). "
                       + t("Complete it from the orders list."))
    _set(w, row, {"GastoID": msg_g})
    _invalidate()
    return True, f"{t('Order received and charged to the project')} ({valor:,.2f})."


def _crear_gasto(r, valor, creado_por="") -> tuple:
    """(ok, id_del_gasto | mensaje de error)."""
    from core import expenses as E
    ok, msg = E.add(str(r.get("ProyectoID", "")), str(r.get("Grupo", "")), valor,
                    categoria=str(r.get("Categoria", "")) or "Materiales",
                    proveedor=str(r.get("Proveedor", "")),
                    descripcion=f"Orden {r.get('ID','')} · {r.get('Descripcion','')}".strip(" ·"),
                    creado_por=creado_por)
    if not ok:
        return False, msg
    # `E.add` no devuelve el ID, así que se recupera de la hoja recién escrita.
    try:
        ult = [x for x in E._records() if str(x.get("ID", "")).startswith("G-")]
        gid = max(ult, key=lambda x: str(x.get("ID", ""))).get("ID", "") if ult else ""
    except Exception:
        gid = ""
    return True, str(gid)


def completar_gasto(oid, creado_por="") -> tuple:
    """Crea el gasto de una orden que quedó `recibida` sin él."""
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    row, r = _fila(w, oid)
    if row is None:
        return False, t("Order not found.")
    if str(r.get("GastoID", "")).strip():
        return False, t("That order already has its expense recorded.")
    ok, msg = _crear_gasto(r, _num(r.get("Valor")), creado_por)
    if not ok:
        return False, msg
    _set(w, row, {"GastoID": msg})
    _invalidate()
    return True, t("Expense recorded.")


def cancelar(oid) -> tuple:
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    row, r = _fila(w, oid)
    if row is None:
        return False, t("Order not found.")
    if str(r.get("Estado", "")) == RECIBIDA:
        return False, t("Already received: it cannot be cancelled (delete its receipt if it was a mistake).")
    ok, err = _set(w, row, {"Estado": CANCELADA})
    if not ok:
        return False, err
    _invalidate()
    return True, t("Order cancelled.")
