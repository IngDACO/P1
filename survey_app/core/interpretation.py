"""
Generación de interpretación técnica de los resultados del survey.
Usa la API de Anthropic (Claude) para analizar todos los datos y retornar
texto interpretativo estructurado por sección, listo para incluir en el PDF.
"""
import json
import streamlit as st

from core.i18n import d

try:
    import anthropic
except Exception:                 # que un fallo de la librería NO tumbe toda la app
    anthropic = None

MODEL      = "claude-haiku-4-5"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """You are a senior engineer specialising in Schindler elevator installation.
Your task is to analyse the data of an installation survey and produce a technical
interpretation that is detailed, clear and useful for the installation team on site.

You will receive the full analysis data as JSON and must return ONLY a valid JSON object
with the keys given. Do not include any text outside the JSON.

Technical background:
- BS = total shaft width = SF1 + BKS + 2×RAIL + SF2
- BSR = actual width measured on site (may differ from BS)
- BKS + 2×RAIL = car block (treated as a single rigid block)
- WR/WL: side clearance between the car block and the walls (minimum = LIMIT_WR/WL)
- FR/FL: distance from the front wall to the rail centre, per level (minimum = LIMIT_FR/FL)
- OR/OL: clearance at the landing door opening (maximum = LIMIT_OR/OL; if exceeded → physical cut)
- RL: lateral displacement of the car block (positive = left, negative = right)
- FB: front-to-back displacement (positive = towards the rear)
- FB extra: additional push to clear a limiting wall when OR/OL exceed the limit
- FRAME: car door frame — RL towards the wall cannot exceed FRAME when there is avoidance
- Case 1 (WALL_LIMITING=True): there is a wall that cannot be cut; OR/OL count as OFF
- Case 2 (WALL_LIMITING=False): OR/OL are handled as a physical cut and do not count as OFF

Writing rules:
- Always answer in clear, technical English
- Be specific: use the numeric values from the JSON in your analysis
- State clearly what is critical, what is acceptable and what needs attention on site
- At most 4-6 sentences per section (concise but complete)
- Do not repeat the raw data; INTERPRET its physical meaning and its implications
"""

INTERPRETATION_SCHEMA = {
    # ⚠️ Las CLAVES no se tocan: se guardan en `Proyectos.InterpJSON` y las lee
    # `report.py` con `ia.get("parametros")`. Traducirlas dejaría las 7 secciones en
    # blanco en todos los informes, sin dar ningún error (la regla de v437).
    "parametros":          "Analysis of the shaft geometry: SF1/SF2 clearances, BS vs BSR, BKS and RAIL. Is the shaft generous or tight? Is there any relevant asymmetry?",
    "estado_inicial":      "State of the survey matrix before any adjustment. Which columns are out of limit? Which floors are the most problematic? Is the problem lateral, front-to-back or at the opening?",
    "desplazamientos":     "Interpretation of MAX_OFF_RL and MAX_OFF_FB. How large are the required displacements? What does moving the rails that much mean physically?",
    "solucion_optima":     "Explanation of the solution found: what the selected RL and FB mean, why that combination was chosen, what it improves against the initial state, how many breaches remain and in which columns.",
    "evasion_pared":       "Analysis of the limiting-wall avoidance (if it applies). Explain what happened: why the extra FB was applied, how big the actual push was, what it achieved, and what constraint FRAME imposes on RL. If it does not apply, return null.",
    "bsr_vs_bs":           "Interpretation of the BSR vs BS result. Is the shaft within tolerance? If an adjustment is required, what the step and range found mean for the work on site.",
    "consideraciones":     "A list of 3-5 concrete points the installation team must check or bear in mind on site, based on the results of the analysis."
}


def _build_data_payload(calc_results: dict, all_params: dict) -> str:
    """Construye el payload JSON con todos los datos relevantes para el análisis."""
    p   = all_params
    r   = calc_results
    lim = r.get("limits", {})
    ana = r.get("analysis", {})
    opt = r.get("optimizer_result", {})
    bs  = r.get("bs_result", {})
    best = opt.get("best", {})

    # Determinar columnas fuera de límite en solución
    sol_off = {}
    if best:
        for col, cnt in best.get("off_by_col", {}).items():
            if cnt > 0:
                sol_off[col] = cnt

    payload = {
        "geometria": {
            "BS":   p.get("BS"),   "BSR":  p.get("BSR"),
            "BKS":  p.get("BKS"),  "RAIL": p.get("RAIL"),
            "SF1":  p.get("SF1"),  "SF2":  p.get("SF2"),
            "BT":   p.get("BT"),   "FRAME":p.get("FRAME"),
            "TS":   p.get("TS"),   "TKSW": p.get("TKSW"),
            "FS":   p.get("FS"),   "TSW":  p.get("TSW"),
            "OFFSET_CABIN": p.get("OFFSET_CABIN"),
            "OFFSET_SIDE":  p.get("OFFSET_SIDE"),
        },
        "configuracion": {
            "NS":            p.get("NS"),
            "OMEGA_SIDE":    p.get("OMEGA_SIDE"),
            "WALL_LIMITING": p.get("WALL_LIMITING"),
            "WALL_STOP":     p.get("WALL_STOP"),
            "WALL_SIDE":     p.get("WALL_SIDE"),
            "CTRL_IN_FRAME": p.get("CTRL_IN_FRAME"),
            "CTRL_SIDE":     p.get("CTRL_SIDE"),
        },
        "limites_calculados": {
            "LIMIT_WR": round(lim.get("LIMIT_WR", 0), 2),
            "LIMIT_WL": round(lim.get("LIMIT_WL", 0), 2),
            "LIMIT_FR": round(lim.get("LIMIT_FR", 0), 2),
            "LIMIT_FL": round(lim.get("LIMIT_FL", 0), 2),
            "LIMIT_OR": round(lim.get("LIMIT_OR", 0), 2),
            "LIMIT_OL": round(lim.get("LIMIT_OL", 0), 2),
            "BC_CALC":       round(lim.get("BC_CALC", 0), 2),
            "FB_MAX_BACK":   round(lim.get("FB_MAX_BACK", 0), 2),
        },
        "estado_inicial": {
            col: {
                "MIN":       round(ana.get(f"MIN_{col}", 0), 2),
                "MAX":       round(ana.get(f"MAX_{col}", 0), 2),
                "DIF":       round(ana.get(f"DIF_{col}", 0), 2),
                "OFF_COUNT": ana.get(f"{col}_OFF_COUNT", 0),
                "LIMIT":     round(lim.get(f"LIMIT_{col}", 0), 2),
            }
            for col in ["WR", "WL", "FR", "FL", "OR", "OL"]
        },
        "desplazamientos_requeridos": {
            "MAX_OFF_RL": round(ana.get("MAX_OFF_RL", 0), 2),
            "MAX_OFF_FB": round(ana.get("MAX_OFF_FB", 0), 2),
        },
        "solucion": {
            "RL":              best.get("rl"),
            "FB_nominal":      best.get("fb"),
            "FB_aplicado":     best.get("fb_applied"),
            "FB_extra_usado":  best.get("fb_extra_applied", False),
            "total_OFF":       best.get("total_off"),
            "OFF_por_columna": best.get("off_by_col", {}),
            "caso":            "Case 1 (limiting wall)" if p.get("WALL_LIMITING") else "Case 2 (no limiting wall)",
        } if best else None,
        "bsr_vs_bs": {
            "BSR":         p.get("BSR"),
            "BS":          p.get("BS"),
            "diferencia":  round((p.get("BS", 0) - p.get("BSR", 0)), 2),
            "ajuste_requerido": bs.get("needed", False),
            "paso":        bs.get("step"),
            "rango":       bs.get("range_name"),
            "dif_original": bs.get("dif_original"),
        },
        "instrucciones": (
            "Analyse this data and return ONLY a JSON object with these keys: "
            + ", ".join(f'"{k}"' for k in INTERPRETATION_SCHEMA.keys())
            + ". For 'evasion_pared' return null if WALL_LIMITING is False or if "
            "FB_extra_usado is False. Every value must be a text string in English."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_interpretation(calc_results: dict, all_params: dict) -> dict:
    """
    Llama a Claude para generar la interpretación técnica del survey.
    Retorna un dict con claves de INTERPRETATION_SCHEMA.
    En caso de error retorna un dict con mensajes de fallback.
    """
    if anthropic is None:
        return _fallback("the anthropic library is not available in this environment.")
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback(d("API key not configured."))

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        payload = _build_data_payload(calc_results, all_params)

        response = client.messages.create(
            model      = MODEL,
            max_tokens = MAX_TOKENS,
            system     = SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": payload}],
        )

        raw = response.content[0].text.strip()

        # Extraer JSON aunque venga con texto extra
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return _fallback("The API did not return valid JSON.")

        data = json.loads(raw[start:end])

        # Asegurar que todas las claves existen
        for key in INTERPRETATION_SCHEMA:
            if key not in data:
                data[key] = None

        data["_ok"]    = True
        data["_error"] = None
        return data

    except anthropic.AuthenticationError:
        return _fallback("Invalid API key.")
    except json.JSONDecodeError:
        return _fallback("Could not parse the API response.")
    except Exception as e:
        return _fallback(f"Error: {e}")


def _fallback(reason: str) -> dict:
    """Retorna interpretación vacía marcada como fallida."""
    msg = f"[Interpretation unavailable: {reason}]"
    d = {key: (None if key == "evasion_pared" else msg)
         for key in INTERPRETATION_SCHEMA}
    d["_ok"]    = False
    d["_error"] = reason
    return d


# ══════════════════════════════════════════════════════════════
# INTERPRETACIÓN PARA EL INFORME DEL USUARIO (cliente)
# ══════════════════════════════════════════════════════════════
# ⚠️ El informe del CLIENTE sale SIEMPRE en inglés, como el resto de documentos que
# salen de la empresa (regla de `i18n.d`): su idioma no puede depender de cómo tenga
# la pantalla quien lo genera. Si algún día se quiere en español, se añade un
# parámetro de idioma AQUÍ y se elige el prompt — nunca se ata al idioma de la UI.
USER_SYSTEM_PROMPT = """You are a senior COPEX engineer specialising in elevator installation.
You are writing a PROFESSIONAL report addressed to the CLIENT / the installation technician on site.

Your goal: explain the final elevator positioning solution clearly, directly and in an
actionable way, leaving no doubt about how to implement it in the field.

RULES:
- Write in professional, clear, confident English (not academic, not ambiguous).
- Do NOT reveal internal formulas, algorithms, internal variable names or how it was calculated.
- Speak in terms of ACTION: what shift to make, in which direction, how many millimetres and why.
- If cuts are required, state them precisely (where, how many mm, on which floor).
- Use a tone that conveys that this is the final, correct solution.
- Return ONLY a valid JSON object with the keys given, with no text outside the JSON.

Background knowledge (to interpret, NOT to expose formulas):
- RL = lateral shift of the car block (+ left, - right).
- FB = front shift (+ towards the rear).
- OR/OL = space in the landing door opening; exceeding the maximum requires a physical cut.
- WR/WL = side clearances; FR/FL = distance from the front wall to the rail.
"""

# ⚠️ Las CLAVES son DATO, no etiqueta: se guardan en `Proyectos.InterpJSON` y las lee
# `user_report` (`ia.get("resumen")`). Traducirlas dejaría las cinco secciones de texto
# EN BLANCO en todos los informes, sin ningún error. Solo se traduce la descripción.
USER_SCHEMA = {
    "resumen":        "Executive summary (3-5 sentences) of the final positioning solution, in plain language for the client. It must give confidence that this is the definitive solution.",
    "desplazamientos":"Precise instruction of the shifts to carry out: RL (lateral) and FB (front), with values in mm, a clear direction (left/right, forward/rear) and the reason for each. The technician must know exactly what to move.",
    "cortes":         "If cuts are required (floor, how many mm, which side of the opening), describe them precisely and why. If NO cut is required, say so clearly and with confidence.",
    "implementacion": "Concrete, ordered steps to implement the solution on site (short, actionable list).",
    "verificacion":   "What the technician must check after installation to confirm it is correct (short checklist).",
}


def cortes_por_piso(lim: dict, best: dict) -> list:
    """Los cortes que exige la solución: `[{piso, cortar_OR_mm, cortar_OL_mm}]`.

    ⚠️ Es la ÚNICA definición de «hay cortes», y existe por un motivo concreto: el
    veredicto del informe del cliente lo deducía **leyendo el texto que escribe la
    IA** (`"requiere cortes" in ia["cortes"]`). Eso ya era frágil —basta con que el
    modelo redacte distinto— y se rompía del todo al pasar el informe al inglés: la
    frase en español no casaría nunca y el veredicto diría «sin valores fuera de
    límite» en un hueco que sí necesita cortes. Un dato se saca de los datos.

    Criterio: OR/OL por ENCIMA de su límite (la convención de v16), por piso.
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
    p    = all_params
    r    = calc_results
    lim  = r.get("limits", {})
    opt  = r.get("optimizer_result", {})
    best = opt.get("best", {}) or {}

    cortes = cortes_por_piso(lim, best)

    payload = {
        "proyecto": {
            "nombre":    p.get("PROYECTO", ""),
            "ingeniero": p.get("INGENIERO", ""),
            "paradas":   p.get("NS"),
        },
        "solucion_final": {
            "RL_mm":           best.get("rl"),
            "FB_mm":           best.get("fb_applied", best.get("fb")),
            "evasion_pared":   best.get("fb_extra_applied", False),
            "valores_fuera":   best.get("total_off"),
            "pared_limitante": bool(p.get("WALL_LIMITING")),
            "wall_stop":       p.get("WALL_STOP"),
            "wall_side":       p.get("WALL_SIDE"),
        } if best else None,
        "cortes_necesarios": cortes if cortes else d("None"),
        "instrucciones": (
            "Write the client report. Return ONLY a JSON with these keys: "
            + ", ".join(f'"{k}"' for k in USER_SCHEMA.keys())
            + ". Each value must be a string of professional ENGLISH text."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_user_interpretation(calc_results: dict, all_params: dict) -> dict:
    """Interpretación orientada al cliente para el informe descargable."""
    if anthropic is None:
        return _user_fallback(d("the anthropic library is not available in this environment."))
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _user_fallback(d("API key not configured."))
    try:
        client  = anthropic.Anthropic(api_key=api_key)
        payload = _build_user_payload(calc_results, all_params)
        response = client.messages.create(
            model      = MODEL,
            max_tokens = MAX_TOKENS,
            system     = USER_SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": payload}],
        )
        raw   = response.content[0].text.strip()
        start = raw.find("{"); end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return _user_fallback(d("The API did not return valid JSON."))
        data = json.loads(raw[start:end])
        for key in USER_SCHEMA:
            data.setdefault(key, None)
        data["_ok"] = True; data["_error"] = None
        return data
    except anthropic.AuthenticationError:
        return _user_fallback("Invalid API key.")
    except json.JSONDecodeError:
        return _user_fallback("Could not parse the API response.")
    except Exception as e:
        return _user_fallback(f"Error: {e}")


def _user_fallback(reason: str) -> dict:
    msg = f"[Interpretation unavailable: {reason}]"
    d = {key: msg for key in USER_SCHEMA}
    d["_ok"] = False; d["_error"] = reason
    return d
