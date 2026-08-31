"""
Registro de cálculos de las herramientas, atado al proyecto.

Hasta v128 las cuatro herramientas de cálculo (Plomadas, Corte de rieles, Corte
de buffers, Belting) eran islas: calculabas, mirabas el resultado en pantalla y
ahí moría. Ni PDF, ni descarga, ni rastro en el proyecto. Al día siguiente o lo
tenías en un papel o lo recalculabas.

Ahora cada ejecución alimenta la base del proyecto:
  - fila en la hoja **`Calculos`** (qué herramienta, quién, cuándo, resumen y
    los datos completos en JSON para poder reabrirlo)
  - PDF archivado en Drive y registrado como documento del proyecto

Sigue el mismo patrón que `prestart.submit`: PDF → Drive + documento → hoja,
con el archivado en best-effort (si Drive no está, el registro igual se guarda).
Lecturas cacheadas + invalidación al escribir (regla de v69/v108).
"""
import json
import logging

import streamlit as st

from core import timeclock
from core import clock

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "Calculos"
HEADERS = ["ID", "ProyectoID", "Grupo", "Herramienta", "Fecha", "Usuario",
           "Resumen", "DatosJSON", "Archivo", "DriveID"]

# Etiqueta visible por herramienta (la clave se guarda en la hoja)
HERRAMIENTAS = {
    "survey":   "Lift survey",
    "plomada":  "Plumb lines",
    "rieles":   "Rail cutting",
    "buffers":  "Buffer cutting",
    "belting":  "Belting",
}



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
    return timeclock.is_configured()


def _ws():
    try:
        return timeclock.get_sheet(SHEET, HEADERS)
    except Exception as e:
        logger.warning("toolruns: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """Registros de SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(SHEET, HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(SHEET))
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


def entradas_de(fila) -> dict:
    """Entradas con las que se hizo un calculo guardado ({} si no las trae).

    ⚠️ Hasta v148 `DatosJSON` solo guardaba los RESULTADOS, asi que un calculo
    no se podia reabrir: faltaba justo lo que hacia falta. Desde v148 la columna
    es {"entradas": {...}, "resultados": {...}}. Las filas con el formato viejo
    devuelven {} y simplemente no ofrecen "reabrir".
    """
    try:
        d = json.loads(str(fila.get("DatosJSON", "")) or "{}")
    except Exception:
        return {}
    return d.get("entradas") or {} if isinstance(d, dict) else {}


def list_for(pid: str) -> list:
    """Historial de cálculos de un proyecto, del más reciente al más antiguo."""
    out = [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]
    return sorted(out, key=lambda r: str(r.get("Fecha", "")), reverse=True)


def _next_id() -> str:
    """Lee FRESCO a propósito: es ruta de escritura (regla de v108).

    ⚠️ v428 — antes contaba FILAS, no el máximo. Nada borra cálculos desde la app, así
    que hoy no colisionaba; pero borrar una fila del medio (a mano, o si algún día se
    añade un «eliminar cálculo») habría emitido un ID **ya existente** — el fallo que
    en `roster` sí estaba vivo. El mismo patrón frágil, arreglado igual: máximo real,
    y saltando los que otra hoja referencie (v427). Un cálculo se enlaza a su PDF por
    `DriveID` y a su proyecto, así que reutilizar el número mezclaría dos registros.
    """
    w = _ws()
    if w is None:
        return "CAL-0001"
    mx = 0
    try:
        for fila in w.get_all_values()[1:]:
            cid = str(fila[0] if fila else "")
            if cid.startswith("CAL-"):
                try:
                    mx = max(mx, int(cid.split("-")[1]))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("toolruns._next_id: %s", e)
        return "CAL-0001"
    try:
        from core import hojas
        return hojas.siguiente_id_libre("CAL-", mx, propia=SHEET)
    except Exception as e:
        logger.warning("toolruns: no se pudo comprobar IDs referenciados: %s", e)
        return f"CAL-{mx + 1:04d}"


def registrar(pid: str, grupo: str, herramienta: str, resumen: str,
              datos: dict, usuario: str = "", pdf: bytes = None,
              filename: str = "") -> dict:
    """Guarda el cálculo contra el proyecto. Devuelve {ok, id, drive_id, error}."""
    res = {"ok": False, "id": "", "drive_id": "", "error": ""}
    if not pid:
        res["error"] = t("The project is missing.")
        return res

    # 1) Archivar el PDF (best-effort: si Drive falla, el registro igual se guarda)
    drive_id = ""
    if pdf and filename:
        try:
            from core import drive_store, projects
            if drive_store.is_available():
                drive_id = drive_store.upload(pid, filename, pdf, "application/pdf")
                projects.add_document(pid, filename, "calculo", drive_id, usuario)
        except Exception as e:
            logger.warning("toolruns: archivado en Drive falló: %s", e)
    res["drive_id"] = drive_id

    # 2) Fila en la hoja
    w = _ws()
    if w is None:
        res["error"] = t("Could not open the calculations sheet.")
        return res
    try:
        cid = _next_id()
        w.append_row(
            [cid, str(pid), str(grupo), str(herramienta),
             clock.now().strftime("%Y-%m-%d %H:%M"), str(usuario),
             str(resumen)[:480], json.dumps(datos, ensure_ascii=False,
                                            default=str)[:4800],
             str(filename), drive_id],
            value_input_option="RAW")
        _invalidate()
        res["ok"] = True
        res["id"] = cid
    except Exception as e:
        res["error"] = str(e)
    return res
