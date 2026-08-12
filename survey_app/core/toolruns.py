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
from datetime import datetime

import streamlit as st

from core import timeclock
from core import clock

logger = logging.getLogger(__name__)

SHEET = "Calculos"
HEADERS = ["ID", "ProyectoID", "Grupo", "Herramienta", "Fecha", "Usuario",
           "Resumen", "DatosJSON", "Archivo", "DriveID"]

# Etiqueta visible por herramienta (la clave se guarda en la hoja)
HERRAMIENTAS = {
    "survey":   "Survey de elevador",
    "plomada":  "Líneas de plomada",
    "rieles":   "Corte de rieles",
    "buffers":  "Corte de buffers",
    "belting":  "Belting",
}


def is_configured() -> bool:
    return timeclock.is_configured()


def _ws():
    try:
        return timeclock.get_sheet(SHEET, HEADERS)
    except Exception as e:
        logger.warning("toolruns: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records() -> list:
    w = _ws()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("toolruns: lectura falló: %s", e)
        return []


def _invalidate():
    try:
        _records.clear()
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
    """Lee FRESCO a propósito: es ruta de escritura (regla de v108)."""
    w = _ws()
    if w is None:
        return "CAL-0001"
    try:
        n = len(w.get_all_values()) - 1      # menos la cabecera
    except Exception:
        n = 0
    return f"CAL-{max(0, n) + 1:04d}"


def registrar(pid: str, grupo: str, herramienta: str, resumen: str,
              datos: dict, usuario: str = "", pdf: bytes = None,
              filename: str = "") -> dict:
    """Guarda el cálculo contra el proyecto. Devuelve {ok, id, drive_id, error}."""
    res = {"ok": False, "id": "", "drive_id": "", "error": ""}
    if not pid:
        res["error"] = "Falta el proyecto."
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
        res["error"] = "No se pudo abrir la hoja de cálculos."
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
