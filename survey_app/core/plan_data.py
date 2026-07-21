"""
Datos del plano, guardados en el proyecto.

Antes cada herramienta pedía su propio PDF y lo reparseaba: el técnico de campo
subía el mismo plano cinco veces y esperaba entre 30 y 70 s cada vez. Desde
v137 el plano se lee **una sola vez al crear el proyecto** y sus valores quedan
en la columna `PlanoJSON`; las herramientas los leen sin tocar el PDF.

⚠️ `PlanoJSON` (lo que DICE el plano) es distinto de `ParamsJSON` (el survey,
que además incluye lo medido en obra: BSR, FS, FRAME, RAIL, OFFSET_CABIN). No
se mezclan: con solo el plano no se puede recalcular un survey.
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Qué herramienta usa cada dato (para poder decir qué falta y a quién afecta)
USA = {
    "params":  "📐 Survey · 🔩 Plomadas",
    "ns":      "📐 Survey (paradas)",
    "rail":    "📐 Survey (RAIL del catálogo)",
    "hq":      "🎗 Belting",
    "hgp":     "🎗 Belting",
    "hkp":     "🛡 Corte de buffers",
    "lfkk":    "✂️ Corte de rieles",
    "lfgk":    "✂️ Corte de rieles",
}


def extraer_todo(pdf_file, progreso=None) -> dict:
    """Lee TODO lo que el plano puede dar, en una sola pasada de texto.

    `progreso(frac, texto)` es opcional (para la barra de la UI). Devuelve un
    dict con los valores + metadatos; nunca lanza.
    """
    from extractors.schindler import (extract_from_pdf, extract_number_of_stops,
                                      extract_car_guide_rail, extract_belting,
                                      extract_hkp, PARAMS)
    from core.rail_cut import extract_lf

    out = {"params": {}, "ns": None, "rail": None,
           "hq": None, "hgp": None, "hkp": None, "lfkk": None, "lfgk": None,
           "archivo": getattr(pdf_file, "name", ""), "leido": "", "faltan": []}

    pasos = [
        ("params",  "Parámetros del hueco",   lambda f: extract_from_pdf(f)),
        ("ns",      "Número de paradas",      lambda f: extract_number_of_stops(f)),
        ("rail",    "Código de riel",         lambda f: extract_car_guide_rail(f)),
        ("belting", "Datos de belting",       lambda f: extract_belting(f)),
        ("hkp",     "HKP (buffers)",          lambda f: extract_hkp(f)),
        ("lf",      "LFKK / LFGK (rieles)",   lambda f: extract_lf(f)),
    ]
    for i, (clave, etiqueta, fn) in enumerate(pasos):
        if progreso:
            try:
                progreso(i / len(pasos), etiqueta)
            except Exception:
                pass
        try:
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)
            r = fn(pdf_file)
        except Exception as e:
            logger.warning("plan_data %s: %s", clave, e)
            continue
        if clave == "params":
            out["params"] = {k: v for k, v in (r or {}).items() if v is not None}
        elif clave == "belting":
            out["hq"] = (r or {}).get("HQ")
            out["hgp"] = (r or {}).get("HGP")
        elif clave == "hkp":
            out["hkp"] = (r or {}).get("HKP")
        elif clave == "lf":
            out["lfkk"] = (r or {}).get("LFKK")
            out["lfgk"] = (r or {}).get("LFGK")
        else:
            out[clave] = r
    if progreso:
        try:
            progreso(1.0, "Listo")
        except Exception:
            pass

    # Qué NO se pudo leer. Un valor ausente que nadie mira se convierte en un
    # cero silencioso aguas abajo, así que se deja explícito.
    faltan = [p for p in PARAMS if p not in out["params"]]
    for k in ("ns", "rail", "hq", "hgp", "hkp", "lfkk", "lfgk"):
        if out.get(k) in (None, ""):
            faltan.append(k.upper())
    out["faltan"] = faltan
    out["leido"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    out["n_params"] = len(out["params"])
    out["n_total"] = len(PARAMS)
    return out


def guardar(pid: str, datos: dict) -> tuple:
    """Escribe los datos del plano en el proyecto."""
    from core import projects as P
    return P.update_project(pid, {"PlanoJSON": json.dumps(datos or {},
                                                          ensure_ascii=False,
                                                          default=str)})


def del_proyecto(pid: str) -> dict:
    """Datos del plano guardados en el proyecto ({} si no hay)."""
    from core import projects as P
    for r in P.list_projects():
        if str(r.get("ID", "")) == str(pid):
            try:
                return json.loads(r.get("PlanoJSON") or "{}")
            except Exception:
                return {}
    return {}


def hay_datos(pid: str) -> bool:
    d = del_proyecto(pid)
    return bool(d and (d.get("params") or d.get("ns") or d.get("hkp")))


def resumen(datos: dict) -> str:
    """Línea legible de qué se leyó del plano."""
    if not datos:
        return "Sin datos del plano."
    n, tot = datos.get("n_params", 0), datos.get("n_total", 0)
    partes = [f"{n}/{tot} parámetros"]
    for k, et in (("ns", "NS"), ("rail", "riel"), ("hkp", "HKP"),
                  ("hq", "HQ"), ("lfkk", "LFKK")):
        if datos.get(k) not in (None, ""):
            partes.append(f"{et}={datos[k]}")
    return " · ".join(partes)
