"""Rastro de cambios: quién tocó qué y cuándo (v342).

## Por qué

`CreadoPor` dice quién CREÓ una fila. No había nada que dijera quién la **cambió**.
En una app donde el **margen**, la **tarifa**, el **presupuesto** y el **avance**
deciden lo que se le cobra a un cliente y lo que se le paga a un trabajador,
*«¿quién puso este margen al 0%?»* es una pregunta que se va a hacer — y hasta ahora
no tenía respuesta.

## Alcance: lo que toca el DINERO, no las 70 escrituras

Registrar los 70 puntos de escritura sería una fila de auditoría por cada clic y una
hoja imposible de leer. Se registran los campos cuyo cambio mueve dinero o cambia el
estado del negocio (`CAMPOS_CLAVE`). Un cambio de nota o de teléfono no entra.

## Coste: 1 escritura por cambio, y solo si algo cambió de verdad

⚠️ `registrar()` compara antes/después y **no escribe nada si el valor es el mismo**.
Guardar un formulario sin tocar nada no ensucia el histórico ni gasta cuota. Y toda
una edición va en UNA fila (los campos en un JSON), no una fila por campo.

⚠️ **Nunca rompe la operación**: si la auditoría falla, el cambio ya se hizo y se
registra el fallo en el log. Perder la anotación es malo; perder el guardado del
usuario porque falló la anotación sería peor.
"""
import json
import logging

import streamlit as st

from core import clock, timeclock

logger = logging.getLogger(__name__)

SHEET = "Auditoria"
HEADERS = ["ID", "Grupo", "Fecha", "Usuario", "Entidad", "EntidadID",
           "Accion", "CambiosJSON"]

# Solo lo que mueve dinero o cambia el estado del negocio.
#
# ⚠️ CADA NOMBRE TIENE QUE SER UNA COLUMNA REAL. Un nombre que no existe en ninguna
# hoja no audita nada — y peor: hace que se anote un cambio que NUNCA se escribió,
# porque `update_project` descarta en silencio las claves que no conoce. Pasó en
# v343 con `MargenPct`, que no existe: **la columna del margen es `MargenMO`**, así
# que justo el campo para el que se construyó esta hoja («¿quién puso el margen a
# 0?») era el único que no se estaba vigilando. Lo cazó ejercitar la escritura
# contra la hoja real, no ningún test. `verif_v344.py` lo comprueba desde ahora.
CAMPOS_CLAVE = {
    # proyecto
    "MargenMO", "Presupuesto", "Avance", "Estado", "EstadoManual",
    "FechaInicio", "FechaFinEst", "Cliente", "ClienteID", "Nombre",
    "CampoAsignados", "AgrupacionID", "PesoEnAgrupacion",
    # persona
    "TarifaHora", "Rol", "Grupo", "Activo",
    # factura / nómina  (el cobro y el pago se siguen por `Estado` + `Cobrado`)
    "Total", "Cobrado", "ImpuestoPct", "Neto", "Base",
    # catálogo (v352): el precio de lo que vendes mueve dinero tanto como el margen.
    # ⚠️ Faltaban al principio y la prueba lo cazó: se cambió un costo de 185,50 a
    # 199,90 y el histórico quedó vacío. Es el mismo fallo que `MargenPct` en v344 —
    # el enganche estaba, el nombre del campo no. El guardián solo comprobaba una
    # dirección (que cada CAMPO_CLAVE exista); ahora también mira que los campos de
    # dinero del catálogo estén en la lista.
    "CostoUnit", "HorasEst", "TarifaHora",
    # ganancia del proyecto (v373). ⚠️ `GananciaHoraJSON` decide desde v360 lo que se
    # le cobra al cliente por cada hora y llevaba 13 versiones SIN auditar: el mismo
    # hueco que `MargenMO` en v344 y `CostoUnit` en v352, tercera vez. Si un campo
    # mueve dinero, entra aquí en el MISMO lote en que se crea.
    "GananciaHoraJSON", "GananciaFija",
}


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("auditoria: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records() -> list:
    """⚠️ SIN cabeceras a propósito.

    `hojas.registros(titulo, cabeceras)` cae a `get_sheet` cuando la hoja no está
    en el lote, y `get_sheet` **la CREA** — o sea, un "lector" que escribe (regla
    v145). La hoja la crea `registrar()`, que es la escritura. Mientras no se haya
    anotado nada, el historial está vacío y esa es la verdad.
    """
    from core import hojas
    return hojas.registros(SHEET) or []


def _invalidate():
    from core import hojas
    hojas.invalidar()
    try:
        _records.clear()
    except Exception:
        pass


def _usuario() -> str:
    try:
        return str(st.session_state.get("auth", {}).get("usuario", "") or "")
    except Exception:
        return ""


def diff(antes: dict, despues: dict) -> dict:
    """{campo: [antes, despues]} solo de los CAMPOS_CLAVE que de verdad cambiaron.

    Compara como TEXTO porque así es como viven en la hoja: `40` y `40.0` son el
    mismo valor para el usuario y no deben generar una entrada de histórico.
    """
    out = {}
    for k, nuevo in (despues or {}).items():
        if k not in CAMPOS_CLAVE:
            continue
        viejo = (antes or {}).get(k, "")
        a, b = str(viejo or "").strip(), str(nuevo or "").strip()
        try:                                     # 40 == 40.0 == "40"
            if a != "" and b != "" and abs(float(a) - float(b)) < 1e-9:
                continue
        except ValueError:
            pass
        if a != b:
            out[k] = [viejo, nuevo]
    return out


def registrar(entidad: str, entidad_id: str, cambios: dict,
              grupo: str = "", accion: str = "editar") -> bool:
    """Anota un cambio. Devuelve True si se escribió (False si no había nada)."""
    if not cambios:
        return False                             # nada cambió → no se ensucia el histórico
    w = _ws()
    if w is None:
        return False
    try:
        fila = [f"AUD-{int(clock.now().timestamp())}", str(grupo or ""),
                clock.now().strftime("%Y-%m-%d %H:%M:%S"), _usuario(),
                str(entidad), str(entidad_id), str(accion),
                json.dumps(cambios, ensure_ascii=False)[:4000]]
        w.append_row(fila, value_input_option="RAW")
        _invalidate()
        return True
    except Exception as e:
        # ⚠️ El cambio del usuario YA se hizo. No se re-lanza.
        logger.warning("auditoria: no se pudo anotar %s/%s: %s", entidad, entidad_id, e)
        return False


def historial(grupo: str = None, entidad: str = None, entidad_id: str = None,
              limite: int = 200) -> list:
    """Cambios, del más reciente al más antiguo, con los cambios ya parseados."""
    out = []
    for r in _records():
        if grupo and str(r.get("Grupo", "")) != str(grupo):
            continue
        if entidad and str(r.get("Entidad", "")) != str(entidad):
            continue
        if entidad_id and str(r.get("EntidadID", "")) != str(entidad_id):
            continue
        try:
            cam = json.loads(r.get("CambiosJSON", "") or "{}")
        except Exception:
            cam = {}
        out.append({**r, "cambios": cam})
    out.sort(key=lambda x: str(x.get("Fecha", "")), reverse=True)
    return out[:limite]
