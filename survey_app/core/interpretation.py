"""
Las dos interpretaciones del survey: la INTERNA (7 apartados, informe técnico que se manda por correo a la oficina) y la
del CLIENTE (5 apartados, informe que se le entrega).

## Lo que había (medido el 08/11/2026 con los dos surveys reales de cliente1, PRJ-0026 y PRJ-0034)

Haiku 4.5 deducía él solo lo que la app ya sabía, y se equivocaba justo ahí: el informe interno daba el desplazamiento
lateral o el frontal en el sentido CONTRARIO al del cliente (y al del cálculo); el del cliente decía que se eliminaban
todos los conflictos con el lado izquierdo fuera de límite en los 8 pisos; razonaba al revés («a la izquierda para
recuperar holgura izquierda»); y describía mover una cabina instalada con gatos, cuando el survey se hace ANTES de
instalar. Las cifras que la app le daba hechas (límites, escalón del BSR, cortes por piso) sí cuadraban.

## Decisiones del usuario (08/11/2026)

- **A. Los datos los pone la app** (`hechos`): el sentido y los mm de cada desplazamiento, lo que queda fuera de límite
  por columna y piso, los cortes. Del cliente, «desplazamientos» y «cortes» los ESCRIBE la app (`texto_*`). El modelo
  redacta alrededor y `revisar` comprueba cada mm, cada sentido y que no diga «resuelto» si queda algo fuera: si falla,
  se le devuelve UNA vez con los errores; si vuelve a fallar, ese apartado no se publica y se dice.
- **B. El procedimiento**: el RL/FB se aplica al colocar la plantilla de plomadas desplazada (el plomado definitivo), y
  de ahí salen las guías (confirmado por el usuario).
- **C/D** (en `survey_ui`): siempre la solución ACTIVA, reintentar sin recalcular, y la oficina revisa el texto.
- **E. Sonnet 5.5**, esfuerzo bajo, salida con esquema y respaldo, como los demás agentes.

## ⚠️ Lo que no se toca

Las CLAVES de los dos esquemas son DATO: se guardan en `Proyectos.InterpJSON` y las leen `report.py` y `user_report.py`
(`ia.get("parametros")`…). Traducirlas o renombrarlas dejaría los informes en blanco sin ningún error (v437, v448).
"""
import json
import logging
import re

from core.i18n import d
from core.num import num as _num

try:
    import anthropic
except Exception:                 # que un fallo de la librería NO tumbe toda la app
    anthropic = None

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5-5"
ESFUERZO = "low"
MAX_TOKENS = 8000                 # razona y escribe del mismo presupuesto (trampa 50)
TIEMPO = 90.0
_BETA_RESPALDO = "server-side-fallback-2026-07-01"
NO_INCLUIDO = "[Not included: the assistant's text for this section did not match the calculation.]"

SYSTEM_PROMPT = """You are a senior engineer specialising in Schindler elevator installation.
You write the technical interpretation of a shaft survey for the company's own engineers. The survey is done BEFORE the
installation: the shaft is measured floor by floor so the rails can be set out where everything fits.

How the solution is applied on site: the plumb template and the plumb lines are set out displaced by the solution's
lateral shift and front-back shift (the report's final plumb setting); the rails and their brackets are then installed
to those plumb lines. Nothing is moved after installation. A landing door opening with more space than its maximum is
cut on that side.

Measurements per floor:
- WR/WL: side clearance between the car block (BKS + 2×RAIL) and the right/left wall. Out of limit when BELOW its minimum.
- FR/FL: distance from the front wall to the right/left rail centre. Out of limit when BELOW its minimum.
- OR/OL: space at the right/left of the landing door opening. Out of limit when ABOVE its maximum: in Case 2 that side of
  the opening is cut; in Case 1 (limiting wall) it counts against the solution.
- Shifting the block to the LEFT increases WR and reduces WL; towards the REAR increases FR and FL.
- BS = shaft width on the drawing, BSR = measured width; BT = landing door opening; FRAME = car door frame.

The FACTS block is computed by the app and is the only truth:
- Every number you write must be in FACTS, as it is written there.
- Say directions only as "to the LEFT", "to the RIGHT", "towards the REAR" or "towards the FRONT", exactly as FACTS gives
  them. Do not use the words forward, backward, leftward or rightward.
- If FACTS lists anything still out of limit, never say that everything is resolved, compliant or within limits: say
  what remains and on which floors.
- Do not invent floors, values, tolerances or equipment that are not in FACTS.

Writing rules:
- Always answer in clear, technical English
- At most 4-6 sentences per section; interpret what the numbers mean on site, do not copy the data back
"""

INTERPRETATION_SCHEMA = {
    # ⚠️ Las CLAVES no se tocan (ver el módulo). Solo cambian las descripciones.
    "parametros":          "Analysis of the shaft geometry: SF1/SF2 clearances, BS vs BSR, BKS and RAIL. Is the shaft generous or tight? Is there any relevant asymmetry?",
    "estado_inicial":      "State of the survey before shifting: which columns are out of limit, on which floors (from FACTS), and whether the problem is lateral, front-back or at the opening.",
    "desplazamientos":     "What the required shifts mean: how large they are against what each column needs, and what setting out the plumb lines that far means on site.",
    "solucion_optima":     "The solution found: the shifts exactly as FACTS gives them, why they help, what improves against the initial state, and exactly what is still out of limit and where (or that nothing is).",
    "evasion_pared":       "Only if FACTS says the extra push to clear the limiting wall was applied: why, how big the push is and what FRAME limits. Otherwise an empty string.",
    "bsr_vs_bs":           "The BSR vs BS result: is the shaft within tolerance; if an adjustment is needed, what the step and range mean for setting out.",
    "consideraciones":     "3-5 concrete points the installation team must check or bear in mind on site, from FACTS.",
}

USER_SYSTEM_PROMPT = """You are a senior COPEX engineer specialising in elevator installation.
You write three sections of a PROFESSIONAL report for the CLIENT and the installation technician on site: the summary,
the implementation steps and the final checks. The shifts and the cuts are already written by the app in the report.

RULES:
- Write in professional, clear, confident English (not academic, not ambiguous).
- Do NOT reveal internal formulas, algorithms or variable names.
- The survey is done BEFORE installation. The solution is applied by setting out the plumb template and the plumb lines
  displaced as the report's final plumb setting shows; the rails and brackets are installed to those lines; the landing
  door openings listed are cut. Never describe moving an installed car, releasing rail brackets or jacking anything.
- The FACTS block is the only truth: every number and every direction you write must be exactly as there. Say directions
  only as "to the LEFT", "to the RIGHT", "towards the REAR" or "towards the FRONT".
- If FACTS lists anything still out of limit, say so plainly in the summary, with where; never claim that everything fits
  or is resolved.
- Return ONLY the JSON object asked for.
"""

# ⚠️ Las CLAVES son DATO (ver el módulo): solo cambian las descripciones.
USER_SCHEMA = {
    "resumen":        "Executive summary (3-5 sentences) of the final positioning solution for the client: the shifts, the openings to cut, and anything that stays out of limit. It must be exact, so the client can rely on it.",
    "desplazamientos": "The shifts to set out, with values in mm and their direction (written by the app from the calculation).",
    "cortes":         "The landing door opening cuts, floor by floor, or that none is needed (written by the app from the calculation).",
    "implementacion": "Concrete, ordered steps to apply the solution on site: set out the plumb template and lines as the final plumb setting shows, install the rails to them, cut the openings listed.",
    "verificacion":   "What the technician must check after setting out and installing the rails (short checklist), using only values from FACTS.",
}
_DEL_MODELO_CLIENTE = ("resumen", "implementacion", "verificacion")
_COLS = ("WR", "WL", "FR", "FL", "OR", "OL")
_MAXIMO = ("OR", "OL")            # el resto son MÍNIMOS


def _esquema(claves) -> dict:
    return {"type": "object", "properties": {k: {"type": "string"} for k in claves},
            "required": list(claves), "additionalProperties": False}


# ═════════════════════════════════════════════════════════════════
# A. Los hechos: los calcula la app
# ═════════════════════════════════════════════════════════════════
def _sentido_lateral(rl) -> str:
    """⚠️ RL positivo = a la IZQUIERDA (el optimizador hace WR += rl, WL -= rl)."""
    return "left" if rl > 0.05 else "right" if rl < -0.05 else "none"


def _sentido_frontal(fb) -> str:
    """⚠️ FB positivo = hacia ATRÁS (FR += fb, FL += fb: se aleja de la pared frontal)."""
    return "rear" if fb > 0.05 else "front" if fb < -0.05 else "none"


def _txt_lateral(rl) -> str:
    s = _sentido_lateral(rl)
    return "no lateral shift" if s == "none" else "%.1f mm to the %s" % (abs(rl), s.upper())


def _txt_frontal(fb) -> str:
    s = _sentido_frontal(fb)
    return "no front-back shift" if s == "none" else "%.1f mm towards the %s" % (abs(fb), s.upper())


def _fuera(v, lim, col) -> bool:
    return v > lim + 1e-6 if col in _MAXIMO else v < lim - 1e-6


def _filas(m):
    if m is None:
        return []
    if hasattr(m, "to_dict"):
        return m.to_dict("records")
    return list(m)


def _pisos_fuera(filas, lim, col) -> list:
    return [i + 1 for i, r in enumerate(filas) if _fuera(_num(r.get(col)), lim, col)]


def _cortes(cortes) -> list:
    """`cortes_por_piso` en la forma que lee el modelo (y que escribe `texto_cortes`)."""
    out = []
    for c in cortes or []:
        x = {"floor": int(c.get("piso", 0))}
        if c.get("cortar_OR_mm"):
            x["cut_right_side_of_opening_mm"] = round(_num(c["cortar_OR_mm"]), 1)
        if c.get("cortar_OL_mm"):
            x["cut_left_side_of_opening_mm"] = round(_num(c["cortar_OL_mm"]), 1)
        out.append(x)
    return out


def solucion_de(calc_results) -> list:
    """`[rl, fb aplicado]` de la solución que se interpreta: con ella se sabe si el texto es de la ACTIVA (C)."""
    b = ((calc_results or {}).get("optimizer_result") or {}).get("best") or {}
    if not b:
        return []
    return [round(_num(b.get("rl")), 1), round(_num(b.get("fb_applied", b.get("fb"))), 1)]


def hechos(calc_results: dict, all_params: dict) -> dict:
    """Todo lo que el modelo puede decir, calculado aquí. ⚠️ Es la ÚNICA verdad de los dos textos."""
    p, r = all_params or {}, calc_results or {}
    lim = r.get("limits") or {}
    ana = r.get("analysis") or {}
    best = (r.get("optimizer_result") or {}).get("best") or {}
    bs = r.get("bs_result") or {}
    caso2 = not bool(p.get("WALL_LIMITING"))
    limite = {c: round(_num(lim.get("LIMIT_%s" % c)), 1) for c in _COLS}
    antes = _filas(r.get("survey_adj"))
    f = {
        "case": ("Case 2: no limiting wall; a landing door opening over its maximum is cut on that side" if caso2
                 else "Case 1: a limiting wall that cannot be cut; openings over their maximum count against the solution"),
        "stops": int(_num(p.get("NS"))),
        "geometry_mm": {**{k: p.get(k) for k in ("BS", "BSR", "BKS", "RAIL", "SF1", "SF2", "BT", "FRAME", "TS", "TKSW", "FS", "TSW")
                           if p.get(k) is not None},
                        # lo que el modelo suele calcular por su cuenta: dado, para que no lo invente
                        "car_block_width": round(_num(p.get("BKS")) + 2 * _num(p.get("RAIL")), 1)},
        "configuration": {k: p.get(k) for k in ("OFFSET_CABIN", "OFFSET_SIDE", "OMEGA_SIDE", "WALL_STOP", "WALL_SIDE")
                          if p.get(k) not in (None, "")},
        # lo que cada columna PIDE desplazar (el análisis), distinto de lo que se desplaza (la solución)
        "shift_needed_mm": {"lateral": round(_num(ana.get("MAX_OFF_RL")), 1),
                            "front_back": round(_num(ana.get("MAX_OFF_FB")), 1)},
        "limits_mm": {**{c: {"limit": limite[c], "rule": "maximum" if c in _MAXIMO else "minimum"} for c in _COLS},
                      "max_rear_push": round(_num(lim.get("FB_MAX_BACK")), 1)},
        "before_shifting": {c: {"lowest": round(_num(ana.get("MIN_%s" % c)), 1),
                                "highest": round(_num(ana.get("MAX_%s" % c, ana.get("MIN_%s" % c))), 1),
                                "floors_out_of_limit": _pisos_fuera(antes, limite[c], c) if antes else None,
                                "how_many_out": int(_num(ana.get("%s_OFF_COUNT" % c)))} for c in _COLS},
    }
    if best:
        rl = round(_num(best.get("rl")), 1)
        fb = round(_num(best.get("fb_applied", best.get("fb"))), 1)
        filas = _filas(best.get("matrix"))
        por_col = best.get("off_by_col") or {}
        quedan = []
        for c in _COLS:
            # ⚠️ Lo que CUENTA la solución (off_by_col) manda; en el Caso 2 OR/OL no cuentan: se cortan (`cuts`)
            if int(_num(por_col.get(c))) <= 0:
                continue
            pisos = _pisos_fuera(filas, limite[c], c)
            vals = [_num(filas[i - 1].get(c)) for i in pisos]
            quedan.append({"column": c, "how_many_floors": int(_num(por_col.get(c))),
                           "floors": pisos if len(pisos) == int(_num(por_col.get(c))) else None,
                           "worst_mm": round((max(vals) if c in _MAXIMO else min(vals)), 1) if vals else None,
                           "limit_mm": limite[c], "rule": "maximum" if c in _MAXIMO else "minimum"})
        f["solution"] = {
            "lateral_shift": _txt_lateral(rl), "lateral_shift_mm": abs(rl), "lateral_direction": _sentido_lateral(rl),
            "front_back_shift": _txt_frontal(fb), "front_back_shift_mm": abs(fb), "front_back_direction": _sentido_frontal(fb),
            "extra_push_to_clear_limiting_wall": bool(best.get("fb_extra_applied")),
            "values_out_of_limit": int(_num(best.get("total_off"))),
            "still_out_of_limit": quedan,
            "everything_within_limits": not quedan,
        }
        if best.get("fb_extra_applied"):
            f["solution"]["front_back_shift_before_extra_push_mm"] = round(abs(_num(best.get("fb"))), 1)
    else:
        f["solution"] = None
    f["cuts"] = _cortes(cortes_por_piso(lim, best)) if best else []
    f["bsr_vs_bs"] = {"bsr_mm": p.get("BSR"), "bs_mm": p.get("BS"),
                      "difference_mm": round(_num(p.get("BS")) - _num(p.get("BSR")), 1),
                      "adjustment_needed": bool(bs.get("needed")), "step_mm": bs.get("step"), "range": bs.get("range_name")}
    return f


def texto_desplazamientos(f) -> str:
    """El apartado «desplazamientos» del cliente, ESCRITO por la app (A): ni un sentido ni un mm que no sea el cálculo."""
    s = (f or {}).get("solution")
    if not s:
        return "No positioning solution was found for this survey. Contact the engineering office before setting out."
    out = ["Set out the plumb template and the plumb lines with these shifts from the drawing position:",
           "• Lateral: %s." % s["lateral_shift"], "• Front-back: %s." % s["front_back_shift"]]
    if s.get("extra_push_to_clear_limiting_wall"):
        out.append("• The front-back shift includes the extra push needed to clear the limiting wall.")
    out.append("The rails and their brackets are then installed to those plumb lines; the final plumb setting in this "
               "report gives the exact positions.")
    for q in s.get("still_out_of_limit") or []:
        _lado = {"WR": "the right side clearance", "WL": "the left side clearance", "FR": "the front distance to the right rail",
                 "FL": "the front distance to the left rail", "OR": "the space at the right of the door opening",
                 "OL": "the space at the left of the door opening"}[q["column"]]
        _donde = ("floors " + ", ".join(str(x) for x in q["floors"])) if q.get("floors") else "%d floor(s)" % q["how_many_floors"]
        out.append("Still out of limit after these shifts: %s on %s (worst %.1f mm against a %s of %.1f mm). The "
                   "engineering office will confirm how this is treated before installation."
                   % (_lado, _donde, q["worst_mm"] if q["worst_mm"] is not None else 0.0, q["rule"], q["limit_mm"]))
    return "\n".join(out)


def texto_cortes(f) -> str:
    """El apartado «cortes» del cliente, ESCRITO por la app desde `cortes_por_piso` (A)."""
    cuts = (f or {}).get("cuts") or []
    if not (f or {}).get("solution"):
        return "No cuts can be defined without a positioning solution."
    if not cuts:
        return "No landing door opening needs to be cut."
    out = ["These landing door openings must be cut:"]
    for c in cuts:
        partes = []
        if c.get("cut_left_side_of_opening_mm"):
            partes.append("%.1f mm on the left side" % c["cut_left_side_of_opening_mm"])
        if c.get("cut_right_side_of_opening_mm"):
            partes.append("%.1f mm on the right side" % c["cut_right_side_of_opening_mm"])
        out.append("• Floor %d: cut %s of the opening." % (c["floor"], " and ".join(partes)))
    return "\n".join(out)


# ═════════════════════════════════════════════════════════════════
# A. Lo que se acepta del modelo
# ═════════════════════════════════════════════════════════════════
_NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w])")
# Solo las formas que las instrucciones le dejan para un sentido (y las que le prohíben): «to the LEFT», «towards the
# REAR», «forward»… Lo que va seguido de «wall»/«side» describe un sitio, no un desplazamiento.
_SENTIDO = re.compile(r"\b(?:to|towards?|toward)\s+the\s+(left|right|rear|back|front)\b(?!\s*(?:-\s*)?(?:wall|side|hand|jamb|of\b))"
                      r"|\b(leftwards?|rightwards?|forwards?|rearwards?|backwards?)\b"
                      r"|\b(?:shift\w*|mov\w*|displac\w*|push\w*)\s+(left|right|back|rear|front)\b", re.I)
# B · el survey se hace ANTES de instalar: nada de mover una cabina instalada (lo que escribía Haiku)
_PROCEDIMIENTO = re.compile(r"\bjack(?:s|ed|ing)?\b|\b(?:releas|loosen|unlock|unbolt)\w*\s+(?:\w+\s+){0,3}?"
                            r"(?:bracket|brackets|car block|car|fasteners?)\b", re.I)
_EJE = {"left": ("lat", "left"), "leftward": ("lat", "left"), "leftwards": ("lat", "left"),
        "right": ("lat", "right"), "rightward": ("lat", "right"), "rightwards": ("lat", "right"),
        "rear": ("fb", "rear"), "back": ("fb", "rear"), "rearward": ("fb", "rear"), "rearwards": ("fb", "rear"),
        "backward": ("fb", "rear"), "backwards": ("fb", "rear"),
        "front": ("fb", "front"), "forward": ("fb", "front"), "forwards": ("fb", "front")}
_TODO_RESUELTO = re.compile(
    r"\b(?:eliminat\w*|resolv\w*|remov\w*|clear\w*|fix\w*|correct\w*)\s+(?:all|every)\b"
    r"|\ball\s+(?:\w+\s+){0,5}?(?:within|compliant|compl(?:y|ies)|meet|meets|conform\w*)\b"
    r"|\bno\s+(?:remaining|residual|outstanding)\s+(?:conflict|breach|violation|issue|value|problem)"
    r"|\beverything\s+(?:fits|is\s+within|is\s+compliant|is\s+resolved)", re.I)
# ⚠️ Sin «fully resolved»: en el examen marcó frases CIERTAS sobre UNA columna («the front-back shortfall is fully
# resolved, but WL stays out») y negadas («does not fully resolve»), y el apartado se perdía. Solo lo GLOBAL.


def _numeros(x, out):
    if isinstance(x, bool) or x is None:
        return out
    if isinstance(x, (int, float)):
        out.add(round(abs(float(x)), 1))
    elif isinstance(x, dict):
        for v in x.values():
            _numeros(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _numeros(v, out)
    elif isinstance(x, str):
        for m in _NUM.finditer(x):
            out.add(round(float(m.group(1).replace(",", "") + (m.group(2) or "")), 1))
    return out


def revisar(textos: dict, f: dict) -> dict:
    """`{apartado: [problemas]}` de lo que escribió el modelo frente a los HECHOS. Vacío = se acepta.

    - Cada número tiene que estar en los hechos (o ser un entero pequeño: pisos, cuentas, pasos de una lista).
    - Cada sentido de desplazamiento, el del cálculo (y ninguno si ese desplazamiento es cero).
    - Si algo queda fuera de límite, nada de «todo resuelto».
    - Ni gatos ni soportes que se aflojan: el survey es ANTES de instalar (B)."""
    permitidos = _numeros(f, set())
    tope_entero = max(12, int(_num((f or {}).get("stops"))))
    s = (f or {}).get("solution") or {}
    esperado = {"lat": s.get("lateral_direction", "none"), "fb": s.get("front_back_direction", "none")}
    queda = (not s) or bool(s.get("still_out_of_limit"))
    out = {}
    for k, txt in (textos or {}).items():
        txt = str(txt or "")
        mal = []
        for m in _NUM.finditer(txt):
            v = float(m.group(1).replace(",", "") + (m.group(2) or ""))
            if any(abs(v - a) < 0.051 for a in permitidos) or (v == int(v) and v <= tope_entero):
                continue
            mal.append("the number %s is not in FACTS" % m.group(0))
        for m in _SENTIDO.finditer(txt):
            eje, sentido = _EJE[(m.group(1) or m.group(2) or m.group(3)).lower()]
            if sentido != esperado[eje]:
                mal.append("«%s» is the wrong direction: the %s shift is %s" % (
                    m.group(0), "lateral" if eje == "lat" else "front-back",
                    s.get("lateral_shift" if eje == "lat" else "front_back_shift", "not defined")))
        for m in _PROCEDIMIENTO.finditer(txt):
            mal.append("«%s» describes moving an installed car: the survey is done before installation and the shifts "
                       "are set out with the plumb template and lines" % m.group(0))
        if queda:
            for m in _TODO_RESUELTO.finditer(txt):
                mal.append("«%s» claims everything is resolved, but FACTS lists what is still out of limit" % m.group(0))
        if mal:
            out[k] = list(dict.fromkeys(mal))
    return out


# ═════════════════════════════════════════════════════════════════
# E. La llamada (Sonnet 5.5, salida con esquema)
# ═════════════════════════════════════════════════════════════════
def _clave() -> str:
    """⚠️ Bajo AppTest, NUNCA la clave de verdad (trampa 44): la de `parte_agente`."""
    from core import parte_agente as AG
    return AG.clave_api()


def _llamar(sistema, mensaje, claves, api_key) -> tuple:
    """`(dict, "")` o `(None, motivo)`. Nunca lanza."""
    if anthropic is None:
        return None, "the anthropic library is not available"
    try:
        cliente = anthropic.Anthropic(api_key=api_key, timeout=TIEMPO, max_retries=1)
        r = cliente.beta.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, betas=[_BETA_RESPALDO], fallbacks="default",
            system=sistema, messages=[{"role": "user", "content": mensaje}],
            output_config={"effort": ESFUERZO, "format": {"type": "json_schema", "schema": _esquema(claves)}})
    except Exception as e:
        logger.warning("interpretation._llamar: %r", e)
        return None, "the AI service could not be reached"
    if r.stop_reason in ("refusal", "max_tokens"):
        return None, "the AI stopped (%s)" % r.stop_reason
    # ⚠️ Por TIPO: con Sonnet 5.5 puede ir antes un bloque de razonamiento (trampa 50)
    txt = next((b.text for b in r.content if getattr(b, "type", "") == "text"), "")
    try:
        data = json.loads(txt)
    except (ValueError, TypeError):
        return None, "the AI answer could not be read"
    return (data, "") if isinstance(data, dict) else (None, "the AI answer could not be read")


def _generar(sistema, mensaje, claves, f, api_key) -> tuple:
    """`(textos, motivo, problemas)`: una llamada, y UNA más con los errores si `revisar` encuentra alguno (A)."""
    data, mot = _llamar(sistema, mensaje, claves, api_key)
    if data is None:
        return None, mot, {}
    probs = revisar({k: data.get(k) for k in claves}, f)
    if probs:
        data2, _m2 = _llamar(sistema, mensaje + "\n\nYour previous answer:\n" + json.dumps(data, ensure_ascii=False)
                             + "\n\nIt has these problems. Write it again, fixing them:\n- "
                             + "\n- ".join("%s: %s" % (k, x) for k, v in probs.items() for x in v), claves, api_key)
        if data2 is not None:
            data, probs = data2, revisar({k: data2.get(k) for k in claves}, f)
    return data, "", probs


def _build_data_payload(calc_results: dict, all_params: dict) -> str:
    """El mensaje de la interpretación interna: los hechos y lo que hay que escribir."""
    f = hechos(calc_results, all_params)
    return ("FACTS (computed by the app; the only truth):\n" + json.dumps(f, ensure_ascii=False, indent=1)
            + "\n\nWrite each section in English:\n"
            + "\n".join("- %s: %s" % (k, v) for k, v in INTERPRETATION_SCHEMA.items()))


def generate_interpretation(calc_results: dict, all_params: dict) -> dict:
    """La interpretación INTERNA. Un apartado que no casa con el cálculo tras el segundo intento no se publica."""
    try:
        f = hechos(calc_results, all_params)
        k = _clave()
        if not k:
            return _fallback(d("API key not configured."))
        data, mot, probs = _generar(SYSTEM_PROMPT, _build_data_payload(calc_results, all_params),
                                    list(INTERPRETATION_SCHEMA), f, k)
        if data is None:
            return _fallback(mot)
        out = {}
        for key in INTERPRETATION_SCHEMA:
            v = str(data.get(key) or "").strip() or None
            if key == "evasion_pared" and not ((f.get("solution") or {}).get("extra_push_to_clear_limiting_wall")):
                v = None
            out[key] = NO_INCLUIDO if (v and key in probs) else v
        out.update(_ok=True, _error=None, _sol=solucion_de(calc_results), _modelo=MODEL,
                   _avisos=["%s: %s" % (k2, "; ".join(v2)) for k2, v2 in probs.items()])
        return out
    except Exception as e:
        logger.warning("interpretation.generate_interpretation: %r", e)
        return _fallback("Error: %s" % type(e).__name__)


def _fallback(reason: str) -> dict:
    """Retorna interpretación vacía marcada como fallida."""
    msg = f"[Interpretation unavailable: {reason}]"
    d_ = {key: (None if key == "evasion_pared" else msg)
          for key in INTERPRETATION_SCHEMA}
    d_["_ok"] = False
    d_["_error"] = reason
    return d_


# ══════════════════════════════════════════════════════════════
# INTERPRETACIÓN PARA EL INFORME DEL USUARIO (cliente)
# ══════════════════════════════════════════════════════════════
# ⚠️ El informe del CLIENTE sale SIEMPRE en inglés, como el resto de documentos que
# salen de la empresa (regla de `i18n.d`): su idioma no puede depender de cómo tenga
# la pantalla quien lo genera.
def cortes_por_piso(lim: dict, best: dict) -> list:
    """Los cortes que exige la solución: `[{piso, cortar_OR_mm, cortar_OL_mm}]`.

    ⚠️ Es la ÚNICA definición de «hay cortes»: el veredicto del informe del cliente lo deducía leyendo el texto de la IA,
    y un dato se saca de los datos (v437). Criterio: OR/OL por ENCIMA de su límite (la convención de v16), por piso.
    """
    lim_or = float(lim.get("LIMIT_OR", 0) or 0)
    lim_ol = float(lim.get("LIMIT_OL", 0) or 0)
    out = []
    for i, row in enumerate((best or {}).get("matrix", []) or []):
        c_or = round(float(row.get("OR", 0) or 0) - lim_or, 1)
        c_ol = round(float(row.get("OL", 0) or 0) - lim_ol, 1)
        piso = {}
        if c_or > 0:
            piso["cortar_OR_mm"] = c_or
        if c_ol > 0:
            piso["cortar_OL_mm"] = c_ol
        if piso:
            piso["piso"] = i + 1
            out.append(piso)
    return out


def _build_user_payload(calc_results: dict, all_params: dict) -> str:
    """El mensaje del cliente: los hechos (los cortes, con la MISMA definición que el veredicto del informe, v437) y lo
    que escribe el modelo. ⚠️ El nombre de esa función, solo en el CÓDIGO de aquí: verif_v437 lo busca en esta función, y
    nombrado en el docstring lo seguía encontrando aunque se quitara la llamada (lo destapó romper_v437)."""
    r = calc_results or {}
    f = hechos(r, all_params)
    f["cuts"] = _cortes(cortes_por_piso(r.get("limits") or {}, (r.get("optimizer_result") or {}).get("best") or {}))
    return ("FACTS (computed by the app; the only truth):\n" + json.dumps(f, ensure_ascii=False, indent=1)
            + "\n\nThe report already says, written by the app:\n" + texto_desplazamientos(f) + "\n" + texto_cortes(f)
            + "\n\nWrite the client report sections. Each value must be a string of professional ENGLISH text:\n"
            + "\n".join("- %s: %s" % (k, USER_SCHEMA[k]) for k in _DEL_MODELO_CLIENTE))


def generate_user_interpretation(calc_results: dict, all_params: dict) -> dict:
    """La del CLIENTE. «desplazamientos» y «cortes» los escribe la app; los otros tres, el modelo. ⚠️ Sin el modelo (o
    con un apartado que no casa) el informe NO se bloquea: ese apartado queda vacío, se dice, y la oficina lo escribe (D)."""
    try:
        f = hechos(calc_results, all_params)
        out = {"resumen": None, "desplazamientos": texto_desplazamientos(f), "cortes": texto_cortes(f),
               "implementacion": None, "verificacion": None,
               "_ok": True, "_error": None, "_avisos": [], "_sol": solucion_de(calc_results), "_modelo": MODEL}
        k = _clave()
        if not k:
            out["_avisos"].append("The assistant is not available here (no API key): write the summary, the steps and "
                                  "the checks yourself.")
            return out
        data, mot, probs = _generar(USER_SYSTEM_PROMPT, _build_user_payload(calc_results, all_params),
                                    list(_DEL_MODELO_CLIENTE), f, k)
        if data is None:
            out["_avisos"].append("The assistant could not write its sections (%s). Press «Rewrite» or write them." % mot)
            return out
        for key in _DEL_MODELO_CLIENTE:
            if key in probs:
                out["_avisos"].append("«%s» was left out: %s." % (key, "; ".join(probs[key])))
            else:
                out[key] = str(data.get(key) or "").strip() or None
        return out
    except Exception as e:
        logger.warning("interpretation.generate_user_interpretation: %r", e)
        return _user_fallback("Error: %s" % type(e).__name__)


def _user_fallback(reason: str) -> dict:
    msg = f"[Interpretation unavailable: {reason}]"
    d_ = {key: msg for key in USER_SCHEMA}
    d_["_ok"] = False
    d_["_error"] = reason
    return d_
