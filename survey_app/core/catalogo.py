"""Catálogo de productos y servicios: la base de las cotizaciones (v352).

## Para qué

Hasta ahora la app cubría **obra → costo → factura**. El dinero, sin embargo, empieza
antes: en la cotización. Este módulo es su materia prima — lo que la empresa vende, con
lo que le CUESTA. El margen no vive aquí: se pone línea a línea al cotizar, porque a un
cliente le cobras un 20% y a otro un 35% por lo mismo.

## Producto vs servicio: la diferencia es el costo

- **producto** → `CostoUnit × cantidad` (rieles, botoneras, cable).
- **servicio** → `HorasEst × TarifaHora × cantidad` (montaje, puesta en marcha).

⚠️ El servicio se mide en HORAS a propósito (decisión del usuario). Así la cotización
habla el mismo idioma que el fichaje y luego se puede contrastar lo cotizado con lo
ejecutado — *«cotizamos 120 h y llevamos 160»*—, que es lo que convierte esto en una
herramienta de gestión y no en una plantilla de Word.

## Una sola definición del costo

`costo_de()` es la ÚNICA fórmula. La cotización, el PDF y la comparación contra lo real
la llaman a ella. Cinco copias divergentes de un helper es exactamente lo que causó los
fallos de v323 (importes que se leían como $0 en silencio).

⚠️ Un artículo **se desactiva, no se borra** (regla v340): las cotizaciones viejas tienen
que seguir resolviendo su nombre. Y aun así cada línea de cotización guarda su propia
copia del precio, porque un documento cuenta lo que se pactó, no lo que hay hoy.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core import columnas
from core import valores
from core.num import col_letter as _col_letter
from core.num import num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "Catalogue"
HEADERS = ["ID", "Group", "Type", "Name", "Description", "Unit", "Category",
           "UnitCost", "EstHours", "HourlyRate", "Active", "Note", "CreatedBy", "Created"]

PRODUCTO, SERVICIO = "product", "service"
TIPOS = (PRODUCTO, SERVICIO)
UNIDADES = ("unit", "set", "m", "m²", "kg", "lump sum")
CAT_DEFAULT = ("Materials", "Equipment", "Installation", "Maintenance",
               "Transport", "Engineering", "Other")

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
        logger.warning("catalogo: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja — un lector que
    escribe (regla v145). La crea la primera alta."""
    from core import hojas
    return hojas.registros(SHEET) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(SHEET))
def _invalidate():
    from core import hojas                 # v339: hay que tirar también el LOTE
    hojas.invalidar()
    for fn in (_records_cached,):
        try:
            fn.clear()
        except Exception as e:             # v344: deja rastro, no lo tragues
            logger.warning("catalogo._invalidate: no se pudo limpiar %s: %s", fn, e)


# ── Lecturas ─────────────────────────────────────────────────────
def list_items(grupo, tipo=None, incluir_inactivos=False) -> list:
    out = [r for r in _records() if str(r.get("Group", "")) == str(grupo)]
    if not incluir_inactivos:
        out = [r for r in out if str(r.get("Active", "SI")).upper() != "NO"]
    if tipo:
        out = [r for r in out if str(r.get("Type", "")) == tipo]
    return sorted(out, key=lambda r: (str(r.get("Category", "")),
                                      str(r.get("Name", "")).casefold()))


def get_item(cid) -> dict:
    return next((r for r in _records() if str(r.get("ID", "")) == str(cid)), {})


def costo_de(item: dict, cantidad=1) -> float:
    """El costo de `cantidad` de este artículo. **La única fórmula** (ver el módulo).

    producto → CostoUnit × cantidad · servicio → HorasEst × TarifaHora × cantidad
    """
    c = _num(cantidad, 0.0)
    if str(item.get("Type", "")) == SERVICIO:
        return round(_num(item.get("EstHours")) * _num(item.get("HourlyRate")) * c, 2)
    return round(_num(item.get("UnitCost")) * c, 2)


def horas_de(item: dict, cantidad=1) -> float:
    """Horas que aporta esta línea (0 en un producto). Base del «cotizado vs real»."""
    if str(item.get("Type", "")) != SERVICIO:
        return 0.0
    return round(_num(item.get("EstHours")) * _num(cantidad, 0.0), 2)


def categorias(grupo) -> list:
    """Las de siempre + las que se hayan usado (como en inventario)."""
    extra = {str(r.get("Category", "")).strip() for r in list_items(grupo, incluir_inactivos=True)
             if str(r.get("Category", "")).strip()}
    return sorted(set(CAT_DEFAULT) | extra, key=str.lower)


def etiqueta_items(items: list) -> dict:
    """{ID: etiqueta}, con el ID detrás **solo si el nombre se repite**.

    Misma regla que `projects.etiqueta_proyectos` (v306) y `auth.etiqueta_usuarios`
    (v319): dos artículos homónimos en un desplegable son indistinguibles, y uno de
    los dos queda imposible de elegir.
    """
    veces = {}
    for it in items:
        n = str(it.get("Name", ""))
        veces[n] = veces.get(n, 0) + 1
    return {str(it.get("ID", "")):
            (f"{it.get('Name', '')} ({it.get('ID', '')})"
             if veces.get(str(it.get("Name", "")), 0) > 1 else str(it.get("Name", "")))
            for it in items}


def resumen(grupo) -> dict:
    items = list_items(grupo, incluir_inactivos=True)
    act = [i for i in items if str(i.get("Active", "SI")).upper() != "NO"]
    return {"n": len(act),
            "productos": sum(1 for i in act if str(i.get("Type", "")) == PRODUCTO),
            "servicios": sum(1 for i in act if str(i.get("Type", "")) == SERVICIO),
            "inactivos": len(items) - len(act)}


# ── Escrituras ───────────────────────────────────────────────────
def _next_id() -> str:
    """⚠️ FRESCO, nunca de la caché: un ID sacado de datos de hasta 120 s puede salir
    REPETIDO, y el ID es la identidad (v323)."""
    w = _ws()
    if w is None:
        return "CAT-00001"
    mx = 0
    try:
        for r in valores.canonizar(columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), SHEET):
            i = str(r.get("ID", ""))
            if i.startswith("CAT-"):
                try:
                    mx = max(mx, int(i.split("-")[1]))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("catalogo._next_id: %s", e)
    return f"CAT-{mx + 1:05d}"


def crear(grupo, nombre, tipo=PRODUCTO, costo_unit="", horas_est="", tarifa_hora="",
          unidad="unit", categoria="", descripcion="", nota="", creado_por="") -> tuple:
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    if not str(nombre).strip():
        return False, t("Give the item a name.")
    if tipo not in TIPOS:
        return False, f"{t('Invalid type')}: {tipo}."
    # ⚠️ Sin costo el artículo no sirve para cotizar: saldría en $0 y nadie lo notaría
    # hasta ver el total (el mismo fallo de las colillas de $0 que arreglamos en v346).
    if tipo == SERVICIO:
        if _num(horas_est) <= 0 or _num(tarifa_hora) <= 0:
            return False, t("A service needs estimated hours and an hourly rate greater than 0.")
    elif _num(costo_unit) <= 0:
        return False, t("The unit cost must be greater than 0.")
    cid = _next_id()
    try:
        w.append_row([cid, str(grupo), str(tipo), str(nombre).strip(), str(descripcion),
                      str(unidad), str(categoria), str(_num(costo_unit)),
                      str(_num(horas_est)), str(_num(tarifa_hora)), "SI", str(nota),
                      str(creado_por), clock.now(grupo).strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, cid


def _fila(w, cid):
    """(nº de fila, registro) leyendo FRESCO: decidir DÓNDE escribir con una caché es
    como se corrompen los datos (v323)."""
    try:
        recs = valores.canonizar(columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), SHEET)
    except Exception as e:
        logger.warning("catalogo._fila: %s", e)
        return None, None
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cid):
            return i + 2, r
    return None, None


def actualizar(cid, fields: dict) -> tuple:
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    row, antes = _fila(w, cid)
    if row is None:
        return False, t("Item not found.")
    # v344: solo lo que la hoja sabe escribir; lo demás se descarta y SE DICE.
    escritos = {k: v for k, v in fields.items() if k in _COL}
    ignorados = [k for k in fields if k not in _COL]
    if ignorados:
        logger.warning("catalogo.actualizar(%s): columnas desconocidas: %s", cid, ignorados)
    if fields and not escritos:
        return False, t("No recognised field") + ": " + ", ".join(ignorados)
    lote = [{"range": f"{_col_letter(_COL[k])}{row}", "values": [[str(v)]]}
            for k, v in escritos.items()]
    try:
        w.batch_update(lote, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating')}: {e}"
    _invalidate()
    # ⚠️ FUERA del try y DESPUÉS de invalidar: si falla la anotación, el cambio del
    # usuario ya se hizo y no se deshace por eso (v342/v344).
    try:
        from core import auditoria
        auditoria.registrar("catalogo", cid, auditoria.diff(antes or {}, escritos),
                            grupo=str((antes or {}).get("Group", "")))
    except Exception as e:
        # Deja RASTRO (regla v323): el precio de lo que vendes sin apunte y sin log
        # es justo el hueco que v352 vino a cerrar.
        logger.warning("catalogo: no se pudo auditar %s: %s", cid, e)
    return True, t("Item updated.")


def set_activo(cid, activo: bool) -> tuple:
    """Desactivar NO borra: las cotizaciones viejas deben seguir resolviendo su nombre
    (regla v340 — y siempre con vuelta)."""
    return actualizar(cid, {"Active": "SI" if activo else "NO"})
