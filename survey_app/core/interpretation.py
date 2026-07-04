"""
Generación de interpretación técnica de los resultados del survey.
Usa la API de Anthropic (Claude) para analizar todos los datos y retornar
texto interpretativo estructurado por sección, listo para incluir en el PDF.
"""
import json
import anthropic
import streamlit as st

MODEL      = "claude-haiku-4-5"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """Eres un ingeniero senior especialista en instalación de elevadores Schindler.
Tu tarea es analizar los datos de un survey de instalación y generar una interpretación técnica
detallada, clara y útil para el equipo de instalación en campo.

Recibirás los datos completos del análisis en formato JSON y debes retornar ÚNICAMENTE un objeto
JSON válido con las claves indicadas. No incluyas texto fuera del JSON.

Conocimiento técnico disponible:
- BS = ancho total del hueco = SF1 + BKS + 2×RAIL + SF2
- BSR = ancho real medido en obra (puede diferir de BS)
- BKS + 2×RAIL = bloque cabina (tratado como un solo bloque rígido)
- WR/WL: espacio lateral entre bloque cabina y paredes (mínimo = LIMIT_WR/WL)
- FR/FL: distancia pared frontal al centro del riel por nivel (mínimo = LIMIT_FR/FL)
- OR/OL: espacio en la apertura de la puerta de rellano (máximo = LIMIT_OR/OL, si excede → corte físico)
- RL: desplazamiento lateral del bloque cabina (positivo = izquierda, negativo = derecha)
- FB: desplazamiento frontal (positivo = hacia atrás)
- FB extra: push adicional para evadir pared limitante cuando OR/OL exceden el límite
- FRAME: marco de puerta de cabina — RL hacia la pared no puede superar FRAME cuando hay evasión
- Caso 1 (WALL_LIMITING=True): hay una pared que no se puede cortar; OR/OL cuentan como OFF
- Caso 2 (WALL_LIMITING=False): OR/OL se gestionan como corte físico, no cuentan como OFF

Reglas de redacción:
- Responde siempre en español técnico claro
- Sé específico: usa los valores numéricos del JSON en tu análisis
- Identifica claramente qué es crítico, qué es aceptable y qué requiere atención en campo
- Máximo 4-6 oraciones por sección (conciso pero completo)
- No repitas los datos crudos; INTERPRETA su significado físico y sus implicaciones
"""

INTERPRETATION_SCHEMA = {
    "parametros":          "Análisis de la geometría del hueco: holguras SF1/SF2, relación BS vs BSR, BKS y RAIL. ¿El hueco es generoso o ajustado? ¿Hay asimetría relevante?",
    "estado_inicial":      "Análisis del estado de la matriz survey antes de cualquier ajuste. ¿Qué columnas están fuera de límite? ¿Cuáles son los pisos más problemáticos? ¿Es el problema lateral, frontal o de apertura?",
    "desplazamientos":     "Interpretación de MAX_OFF_RL y MAX_OFF_FB. ¿Qué tan grandes son los desplazamientos necesarios? ¿Qué implica físicamente mover los rieles esa cantidad?",
    "solucion_optima":     "Explicación de la solución encontrada: qué significa el RL y FB seleccionados, por qué se eligió esa combinación, qué mejoras aporta vs el estado inicial, cuántas violaciones quedan y en qué columnas.",
    "evasion_pared":       "Análisis de la evasión de pared limitante (si aplica). Explica qué ocurrió: por qué se aplicó el FB extra, cuánto fue el push real, qué se ganó con ello, y qué restricción impone el FRAME sobre el RL. Si no aplica, retorna null.",
    "bsr_vs_bs":           "Interpretación del resultado BSR vs BS. ¿El hueco está dentro de tolerancia? Si se requiere ajuste, qué implica el paso y rango encontrado para el trabajo en campo.",
    "consideraciones":     "Lista de 3-5 puntos concretos que el equipo de instalación debe verificar o tener en cuenta en campo, basados en los resultados del análisis."
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
            "caso":            "Caso 1 (pared limitante)" if p.get("WALL_LIMITING") else "Caso 2 (sin pared limitante)",
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
            "Analiza estos datos y retorna SOLO un JSON con estas claves: "
            + ", ".join(f'"{k}"' for k in INTERPRETATION_SCHEMA.keys())
            + ". Para 'evasion_pared' retorna null si WALL_LIMITING es False o si "
            "FB_extra_usado es False. Cada valor debe ser una cadena de texto en español."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_interpretation(calc_results: dict, all_params: dict) -> dict:
    """
    Llama a Claude para generar la interpretación técnica del survey.
    Retorna un dict con claves de INTERPRETATION_SCHEMA.
    En caso de error retorna un dict con mensajes de fallback.
    """
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback("API key no configurada.")

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
            return _fallback("La API no retornó JSON válido.")

        data = json.loads(raw[start:end])

        # Asegurar que todas las claves existen
        for key in INTERPRETATION_SCHEMA:
            if key not in data:
                data[key] = None

        data["_ok"]    = True
        data["_error"] = None
        return data

    except anthropic.AuthenticationError:
        return _fallback("API key inválida.")
    except json.JSONDecodeError:
        return _fallback("Error al parsear respuesta de la API.")
    except Exception as e:
        return _fallback(f"Error: {e}")


def _fallback(reason: str) -> dict:
    """Retorna interpretación vacía marcada como fallida."""
    msg = f"[Interpretación no disponible: {reason}]"
    d = {key: (None if key == "evasion_pared" else msg)
         for key in INTERPRETATION_SCHEMA}
    d["_ok"]    = False
    d["_error"] = reason
    return d


# ══════════════════════════════════════════════════════════════
# INTERPRETACIÓN PARA EL INFORME DEL USUARIO (cliente)
# ══════════════════════════════════════════════════════════════
USER_SYSTEM_PROMPT = """Eres un ingeniero senior de COPEX, especialista en instalación de elevadores.
Redactas un informe PROFESIONAL dirigido al CLIENTE / técnico de instalación en obra.

Tu objetivo: explicar la solución final de posicionamiento del elevador de forma clara, directa
y accionable, SIN dejar ninguna duda de cómo implementarla en campo.

REGLAS:
- Escribe en español profesional, claro y seguro (no académico, no ambiguo).
- NO reveles fórmulas internas, algoritmos, nombres de variables técnicas internas ni cómo se calculó.
- Habla en términos de ACCIÓN: qué desplazamiento hacer, en qué dirección, cuántos milímetros y por qué.
- Si hay cortes necesarios, indícalos con precisión (dónde, cuánto en mm, en qué piso).
- Usa un tono que transmita que la solución es la definitiva y correcta.
- Devuelve ÚNICAMENTE un objeto JSON válido con las claves indicadas, sin texto fuera del JSON.

Conocimiento (para interpretar, NO para exponer fórmulas):
- RL = desplazamiento lateral del bloque cabina (+ izquierda, − derecha).
- FB = desplazamiento frontal (+ hacia atrás).
- OR/OL = espacio en la apertura de la puerta de rellano; si exceden el máximo se requiere corte físico.
- WR/WL = holguras laterales; FR/FL = distancia de la pared frontal al riel.
"""

USER_SCHEMA = {
    "resumen":        "Resumen ejecutivo (3-5 frases) de la solución final de posicionamiento, en lenguaje claro para el cliente. Debe dar confianza de que es la solución definitiva.",
    "desplazamientos":"Instrucción precisa de los desplazamientos a realizar: RL (lateral) y FB (frontal), con valores en mm, dirección clara (izquierda/derecha, adelante/atrás) y el motivo de cada uno. Que el técnico sepa exactamente qué mover.",
    "cortes":         "Si hay cortes necesarios (piso, cuántos mm, en qué lado de la apertura), descríbelos con precisión y por qué. Si NO se requiere ningún corte, dilo claramente y con seguridad.",
    "implementacion": "Pasos concretos y ordenados para implementar la solución en obra (lista breve, accionable).",
    "verificacion":   "Qué debe verificar el técnico tras la instalación para confirmar que quedó correcto (checklist breve).",
}


def _build_user_payload(calc_results: dict, all_params: dict) -> str:
    p    = all_params
    r    = calc_results
    lim  = r.get("limits", {})
    opt  = r.get("optimizer_result", {})
    best = opt.get("best", {}) or {}

    # Cortes por piso (OR/OL que exceden su límite)
    lim_or = float(lim.get("LIMIT_OR", 0))
    lim_ol = float(lim.get("LIMIT_OL", 0))
    cortes = []
    for i, row in enumerate(best.get("matrix", []) or []):
        c_or = round(float(row.get("OR", 0)) - lim_or, 1)
        c_ol = round(float(row.get("OL", 0)) - lim_ol, 1)
        piso = {}
        if c_or > 0: piso["cortar_OR_mm"] = c_or
        if c_ol > 0: piso["cortar_OL_mm"] = c_ol
        if piso:
            piso["piso"] = i + 1
            cortes.append(piso)

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
        "cortes_necesarios": cortes if cortes else "Ninguno",
        "instrucciones": (
            "Redacta el informe para el cliente. Retorna SOLO un JSON con estas claves: "
            + ", ".join(f'"{k}"' for k in USER_SCHEMA.keys())
            + ". Cada valor es una cadena de texto en español profesional."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_user_interpretation(calc_results: dict, all_params: dict) -> dict:
    """Interpretación orientada al cliente para el informe descargable."""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _user_fallback("API key no configurada.")
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
            return _user_fallback("La API no retornó JSON válido.")
        data = json.loads(raw[start:end])
        for key in USER_SCHEMA:
            data.setdefault(key, None)
        data["_ok"] = True; data["_error"] = None
        return data
    except anthropic.AuthenticationError:
        return _user_fallback("API key inválida.")
    except json.JSONDecodeError:
        return _user_fallback("Error al parsear respuesta de la API.")
    except Exception as e:
        return _user_fallback(f"Error: {e}")


def _user_fallback(reason: str) -> dict:
    msg = f"[Interpretación no disponible: {reason}]"
    d = {key: msg for key in USER_SCHEMA}
    d["_ok"] = False; d["_error"] = reason
    return d
