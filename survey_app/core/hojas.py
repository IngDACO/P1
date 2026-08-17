"""Lector por LOTES del libro de Sheets (v339) — el techo de cuota.

## El problema, medido

La API de Sheets limita a **60 lecturas por minuto y por usuario**, y "usuario" aquí
es la **cuenta de servicio**: una sola para TODOS los grupos. O sea que el techo no
crece al añadir clientes, se reparte entre ellos.

Medido en producción antes de este módulo:
- arranque en frío: **12 llamadas** · 859 ms de media cada una
- estado sostenido: **~6 lecturas/min por usuario activo** (TTL 120 s)
- → **~10 usuarios activos en paralelo**, o **5 arranques por minuto**, antes del 429

De esas llamadas, **15 de 19 eran `values/{hoja}`: una por hoja**. La app lee 21 hojas
distintas con 30 lectores cacheados, y cada uno pedía la suya por separado.

## La palanca

`spreadsheets.values.batchGet` trae **muchos rangos en UNA sola petición**, y la cuota
cuenta peticiones. Pedir 10 hojas de golpe cuesta 1 lectura, no 10.

Este módulo hace exactamente eso: la primera hoja que alguien pida dispara **una**
llamada que se trae TODAS, y el resto salen de ahí.

## Lo que NO hace

⚠️ **Las rutas de ESCRITURA siguen leyendo frescas.** `_find_row`, `_next_id` y
`_ids_frescos` van directos al worksheet a propósito: usar una caché para decidir
dónde escribir o qué ID toca es como se corrompen los datos (v323). Este módulo es
solo para LECTURA de display.
"""
import logging

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

# Las hojas que la app lee para MOSTRAR. El orden no importa; la lista sí: pedir de
# más cuesta ancho de banda, no cuota (es 1 petición igual), pero pedir de menos
# obliga a una segunda llamada.
HOJAS_LECTURA = (
    # ⚠️ "Sheet1" es la del FICHAJE y es la más leída de todas (horas, costo de mano
    # de obra, conciliación, plan-vs-real). Se llama así porque es la hoja original
    # del libro; el nombre no se toca (renombrarla rompería `_cached_ws`).
    "Sheet1",
    "Proyectos", "Actividades", "Agrupaciones", "Documentos", "Alarmas",
    "Login", "Grupos", "Credenciales", "Gastos", "Clientes", "Facturas",
    "Nominas", "Activos", "InvCategorias", "MovimientosActivo",
    "Roster", "Trabajos", "PreStarts", "Calculos", "Rieles",
    "Auditoria", "Ordenes",
    "Catalogo",      # v352 — cotizaciones     # v342 — si no entra aquí, sería una llamada suelta
)


def _libro():
    """El objeto Spreadsheet, cacheado por proceso (ya lo hace `timeclock`)."""
    ws = timeclock._cached_ws()          # hoja1; de ahí colgamos el libro
    return ws.spreadsheet if ws is not None else None


def _existentes() -> set:
    """Títulos de las hojas que EXISTEN, en minúsculas.

    ⚠️ Sale del índice que `timeclock._libro()` ya construye y cachea (v290), así
    que **no cuesta ninguna llamada**. Hace falta porque `values_batch_get`
    rechaza la petición ENTERA si un solo rango no existe: pedir una hoja que
    todavía no se ha creado (p. ej. `MovimientosActivo` mientras no haya activos)
    tumbaba el lote completo y devolvía a leer hoja por hoja.
    """
    try:
        hojas, _cab = timeclock._libro()
        return set(hojas or {})
    except Exception as e:
        logger.warning("hojas: no se pudo leer el índice del libro: %s", e)
        return set()


@st.cache_data(ttl=120, show_spinner=False)
def _lote() -> dict:
    """UNA llamada `values:batchGet` con todas las hojas → {titulo: [[celdas]]}.

    ⚠️ Devuelve valores CRUDOS (como `get_all_values`), no registros: así este
    módulo no impone un formato y cada lector arma lo suyo con `registros()`.
    """
    lib = _libro()
    if lib is None:
        return {}
    try:
        hay = _existentes()
        pedir = [h for h in HOJAS_LECTURA if h.strip().lower() in hay]
        if not pedir:
            return {}
        # `values_batch_get` acepta A1 por hoja. Sin límite de columna: trae lo que haya.
        rangos = [f"'{h}'" for h in pedir]
        r = lib.values_batch_get(rangos)
        out = {}
        for tramo in (r.get("valueRanges") or []):
            # el rango vuelve como "'Hoja'!A1:Z99" → recuperamos el título
            rng = str(tramo.get("range", ""))
            titulo = rng.split("!")[0].strip("'")
            out[titulo] = tramo.get("values") or []
        return out
    except Exception as e:
        # Si el lote falla (una hoja que aún no existe, un hipo de la API), NO se
        # rompe nada: `registros()` cae al lector de siempre, hoja por hoja.
        logger.warning("hojas: el lote falló, se lee hoja por hoja: %s", e)
        return {}


def invalidar():
    try:
        _lote.clear()
    except Exception:
        pass


def registros(titulo: str, cabeceras=None):
    """Filas de una hoja como dicts, **idéntico a `get_all_records(numericise_ignore=['all'])`**.

    Es decir: la fila 1 es la cabecera, todo llega como TEXTO (nunca numerizado —
    conservar los ceros a la izquierda importa, regla de v42) y las filas cortas se
    rellenan con "" hasta la cabecera.

    Si la hoja no vino en el lote, cae al camino de siempre (una llamada suya).
    """
    datos = _lote().get(titulo)
    if datos is None:
        if cabeceras is None:
            return None                   # que el llamador use su propio lector
        try:
            w = timeclock.get_sheet(titulo, tuple(cabeceras))
            return w.get_all_records(numericise_ignore=["all"])
        except Exception as e:
            logger.warning("hojas: lectura suelta de %s falló: %s", titulo, e)
            return []
    if not datos:
        return []
    cab = [str(c) for c in datos[0]]
    n = len(cab)
    out = []
    for fila in datos[1:]:
        vals = [str(v) for v in fila[:n]] + [""] * max(0, n - len(fila))
        out.append(dict(zip(cab, vals)))
    return out
