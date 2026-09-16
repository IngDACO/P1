# -*- coding: utf-8 -*-
"""La LÍNEA BASE de una obra: el plan que se acordó, congelado.

Hasta v500 el cronograma se recalculaba SIEMPRE desde las duraciones vigentes, así que
alargar una actividad de 4 a 8 días no dejaba rastro: el plan nuevo pasaba a ser «el
plan», la curva S comparaba contra un blanco móvil y **nadie podía ver que la obra se
había replanificado**. Es lo que en una instalación hace falta para defender por qué se
retrasó una entrega y quién lo causó.

Tres fechas distintas, que la app no debe confundir:
- **línea base** → lo que se ACORDÓ (aquí);
- **plan vigente** → lo que dicen hoy las duraciones y dependencias (`plan.calcular`);
- **pronóstico**  → cuándo va a terminar de verdad (`plan.pronostico`, v500).

⚠️ Decisiones del usuario: se fija **con un botón**, cuando el plan está pactado (no al
crear la obra, que nace de una plantilla y casi siempre se ajusta después), y al
re-fijarla **la ORIGINAL nunca se pierde**: se conserva con un contador de cuántas veces
se replanificó y cuánto se movió la entrega cada vez.

Funciones puras: sin Streamlit ni Sheets (v378, para poder ejercitarlo entero).
"""
import logging

logger = logging.getLogger(__name__)


def snapshot(sched: dict, quien: str = "", cuando: str = "") -> dict:
    """Foto del plan vigente: la entrega, el total y la ventana de cada actividad."""
    acts = []
    for a in (sched or {}).get("activities", []) or []:
        acts.append({"orden": int(a.get("orden", 0) or 0),
                     "nombre": str(a.get("nombre", "")),
                     "dur": float(a.get("duracion", 0) or 0),
                     "ini": float(a.get("inicio", 0) or 0)})
    fin = (sched or {}).get("fecha_fin")
    return {"fijada": str(cuando), "por": str(quien),
            "entrega": fin.isoformat() if hasattr(fin, "isoformat") else str(fin or ""),
            "total": float((sched or {}).get("total_dias", 0) or 0),
            "acts": acts}


def fijar(bl: dict, sched: dict, quien: str = "", cuando: str = "") -> dict:
    """El `BaselineJSON` nuevo tras pulsar «fijar»: la ORIGINAL se conserva siempre.

    ⚠️ Re-fijar NO es corregir el pasado: la original es la que sostiene el reclamo, así
    que solo se escribe la primera vez. Lo que cambia es la VIGENTE, y cada re-fijación
    deja una línea en el historial con cuánto movió la entrega — que es el dato con el
    que se discute, no el plan entero (por eso el historial no guarda las actividades:
    así no crece sin control dentro de una celda).
    """
    bl = dict(bl or {})
    nuevo = snapshot(sched, quien, cuando)
    if not bl.get("original"):
        bl["original"] = nuevo
        bl["vigente"] = nuevo
        bl["historial"] = []
        return bl

    previo = bl.get("vigente") or bl.get("original") or {}
    bl.setdefault("historial", [])
    bl["historial"].append({
        "fijada": nuevo.get("fijada", ""), "por": nuevo.get("por", ""),
        "entrega": nuevo.get("entrega", ""),
        "desde": previo.get("entrega", ""),
        "movio": round(float(nuevo.get("total", 0)) - float(previo.get("total", 0)), 1)})
    bl["vigente"] = nuevo
    return bl


def comparar(sched: dict, bl: dict) -> dict:
    """Qué se ha movido respecto a lo acordado.

    Devuelve `{hay, entrega_base, entrega_hoy, movio, replanificaciones, actividades}`.
    `actividades` trae solo las que CAMBIARON, más las nuevas y las eliminadas —
    ⚠️ comparar dos listas por posición daría basura en cuanto alguien reordene o borre
    una actividad, así que se casan por su número de ORDEN.
    """
    base = (bl or {}).get("original") or {}
    if not base:
        return {"hay": False}

    por_orden = {int(a.get("orden", 0)): a for a in base.get("acts", []) or []}
    hoy = {int(a.get("orden", 0) or 0): a for a in (sched or {}).get("activities", []) or []}

    filas = []
    for o, a in sorted(hoy.items()):
        b = por_orden.get(o)
        if b is None:
            filas.append({"orden": o, "nombre": a.get("nombre", ""), "estado": "nueva",
                          "dur_base": None, "dur_hoy": float(a.get("duracion", 0) or 0),
                          "movio": None})
            continue
        d_base, d_hoy = float(b.get("dur", 0)), float(a.get("duracion", 0) or 0)
        i_base, i_hoy = float(b.get("ini", 0)), float(a.get("inicio", 0) or 0)
        if abs(d_base - d_hoy) > 1e-6 or abs(i_base - i_hoy) > 1e-6:
            filas.append({"orden": o, "nombre": a.get("nombre", ""), "estado": "cambiada",
                          "dur_base": d_base, "dur_hoy": d_hoy,
                          "movio": round(i_hoy - i_base, 1)})
    for o, b in sorted(por_orden.items()):
        if o not in hoy:
            filas.append({"orden": o, "nombre": b.get("nombre", ""), "estado": "eliminada",
                          "dur_base": float(b.get("dur", 0)), "dur_hoy": None, "movio": None})

    total_hoy = float((sched or {}).get("total_dias", 0) or 0)
    fin = (sched or {}).get("fecha_fin")
    return {"hay": True,
            "entrega_base": base.get("entrega", ""),
            "entrega_hoy": fin.isoformat() if hasattr(fin, "isoformat") else str(fin or ""),
            "movio": round(total_hoy - float(base.get("total", 0)), 1),
            "fijada": base.get("fijada", ""), "por": base.get("por", ""),
            "replanificaciones": len((bl or {}).get("historial", []) or []),
            "historial": (bl or {}).get("historial", []) or [],
            "actividades": filas}
