"""
Agente experto en instalación de elevadores Schindler.
Usa la API de Anthropic (Claude) con contexto completo del survey actual.
"""
import anthropic
import streamlit as st

MODEL       = "claude-haiku-4-5"
MAX_TOKENS  = 1024
MAX_HISTORY = 20   # máximo de mensajes guardados en memoria (evita tokens infinitos)

SYSTEM_PROMPT = """Eres un experto técnico senior en instalación y puesta en marcha de elevadores, con especialización en sistemas Schindler (modelos 3100, 3300, 5300, 5500 y otros).

Tu rol es asistir a técnicos e ingenieros de campo durante la ejecución de surveys de instalación. Respondes preguntas técnicas sobre:

## Tu área de conocimiento

### Geometría del hueco (shaft)
- Parámetros del plano: BS (ancho total), TS (profundidad), SF1/SF2 (holguras laterales), BKS (ancho cabina sin rieles), TKSW (distancia frontal diseño), TSW (umbral)
- BT = apertura de la puerta de rellano (NO el ancho de la cabina)
- Ancho del bloque cabina = BKS + 2×RAIL (tratado como un solo bloque rígido)
- BS = SF1 + BKS + 2×RAIL + SF2 (balance del hueco)

### Survey de campo
- WR/WL: espacio entre el bloque cabina y las paredes derecha/izquierda — deben ser ≥ LIMIT
- FR/FL: distancia de la pared frontal al centro del riel — deben ser ≥ LIMIT
- OR/OL: espacio a cada lado en la apertura de la puerta de rellano — si OR/OL > LIMIT se requiere corte físico
- Las mediciones varían nivel a nivel por irregularidades del hueco

### Posicionamiento de rieles (RL y FB)
- RL (Rail Lateral): desplazamiento lateral del bloque cabina (+ = izquierda, − = derecha según convención)
- FB (Front/Back): desplazamiento frontal de la cabina (+ = hacia atrás)
- FB_MAX_BACK = FS − TSW: máximo desplazamiento físico hacia atrás sin tocar la pared trasera
- Objetivo: minimizar valores fuera de límite, luego minimizar |RL| + |FB|

### Pared limitante (Caso 1)
- Cuando hay una pared que no se puede cortar en un nivel específico
- La cabina puede evadir físicamente la pared desplazándose hacia atrás: FB extra = FS − TSW
- Una vez aplicado el FB extra, el RL hacia esa pared no puede superar FRAME (el marco de la puerta de cabina taparia la apertura)
- Si FS ≤ TSW no hay espacio para evadir → el paso es inválido

### Caso 2 (sin pared limitante)
- OR/OL no cuentan como violaciones de posicionamiento
- Si OR/OL > LIMIT se requiere corte físico de la jamba/pared
- Se muestran columnas CUT OR / CUT OL con el valor a cortar

### BSR vs BS
- BSR: ancho real medido en obra (puede diferir del plano BS)
- Si BSR < BS hay que ajustar el shaft en rangos ZB → OB → Extended (paso 0.5 mm)
- Si BSR ≥ BS no se requiere ajuste

### Componentes y tolerancias
- RAIL: cabeza del riel (guía de la cabina), típico 8–16 mm
- FRAME: marco de la puerta de cabina, típico 80–120 mm
- OFFSET_CABIN: corrección lateral adicional para centrar la cabina
- CTRL_IN_FRAME: si el controlador ocupa espacio en el marco → reduce LIMIT_OR/OL en 70 mm en el último nivel
- OMEGA_SIDE: lado donde va el perfil omega de la cabina (R o L)
- Tolerancias típicas Schindler: ±2 mm en rieles, ±5 mm en paredes de hueco

### Proceso de instalación general
- Plomada de rieles: referencia vertical para alineación
- Plantillas de perforación: fijación de brackets al hueco
- Nivelación de cabina en cada parada
- Ajuste de puertas de rellano (landing doors)
- Pruebas de carga y velocidad
- Certificación y habilitación

### Problemas comunes en surveys
- Huecos fuera de tolerancia: paredes inclinadas, esquinas no verticales
- Diferencias BSR vs BS: hueco más angosto o ancho de lo planeado
- Niveles con OR/OL excesivo: requieren corte o modificación de jamba
- Pared limitante en un nivel: restringe el posicionamiento del bloque
- Vibraciones y ruidos: desalineación de rieles, desgaste de guías

## Estilo de respuesta
- Responde siempre en español
- Sé técnico pero claro — el usuario puede ser ingeniero o técnico de campo
- Si hay datos del survey actual en el contexto, úsalos para respuestas específicas
- Cuando des valores numéricos, indica las unidades (mm, kg, m/s, etc.)
- Si la pregunta está fuera de tu área, indícalo claramente
- Sé conciso: respuestas directas sin relleno innecesario
"""


def _build_context_block(calc_results: dict | None, all_params: dict | None) -> str:
    """Construye un bloque de contexto con los datos actuales del survey."""
    if not calc_results and not all_params:
        return ""

    lines = ["\n---\n## Datos del survey actual en sesión\n"]

    # Parámetros clave
    if all_params:
        p = all_params
        lines.append("### Parámetros")
        for key in ["BS", "BSR", "BKS", "BT", "RAIL", "FRAME", "SF1", "SF2",
                    "TS", "TKSW", "TSW", "FS", "TK", "OFFSET_CABIN",
                    "OMEGA_SIDE", "WALL_LIMITING", "WALL_STOP", "WALL_SIDE",
                    "CTRL_IN_FRAME", "CTRL_SIDE", "NS"]:
            v = p.get(key)
            if v is not None and v != 0 and v != "":
                lines.append(f"- {key} = {v}")

    if calc_results:
        r = calc_results

        # Límites
        lim = r.get("limits", {})
        if lim:
            lines.append("\n### Límites calculados")
            for key in ["LIMIT_WR", "LIMIT_WL", "LIMIT_FR", "LIMIT_FL",
                        "LIMIT_OR", "LIMIT_OL", "BC_CALC", "FB_MAX_BACK",
                        "MAX_OFF_RL", "MAX_OFF_FB"]:
                v = lim.get(key)
                if v is not None:
                    lines.append(f"- {key} = {round(v, 2)}")

        # Análisis inicial
        ana = r.get("analysis", {})
        if ana:
            lines.append("\n### Estado inicial (survey ajustado)")
            for col in ["WR", "WL", "FR", "FL", "OR", "OL"]:
                off  = ana.get(f"{col}_OFF_COUNT", 0)
                dif  = round(ana.get(f"DIF_{col}", 0), 2)
                mn   = round(ana.get(f"MIN_{col}", 0), 2)
                lines.append(f"- {col}: OFF={off}  DIF={dif}  MIN={mn}")
            lines.append(f"- MAX_OFF_RL = {round(ana.get('MAX_OFF_RL', 0), 2)}")
            lines.append(f"- MAX_OFF_FB = {round(ana.get('MAX_OFF_FB', 0), 2)}")

        # Resultado optimizador
        opt = r.get("optimizer_result", {})
        best = opt.get("best")
        if best:
            lines.append("\n### Mejor solución encontrada")
            lines.append(f"- RL = {best['rl']} mm")
            lines.append(f"- FB = {best['fb']} mm  (aplicado: {best.get('fb_applied', best['fb'])} mm)")
            lines.append(f"- Total OFF = {best['total_off']}")
            lines.append(f"- FB extra aplicado: {best.get('fb_extra_applied', False)}")
            obc = best.get("off_by_col", {})
            if obc:
                lines.append(f"- OFF por columna: {obc}")

        # BSR vs BS
        bs = r.get("bs_result", {})
        if bs:
            lines.append("\n### BSR vs BS")
            if not bs.get("needed"):
                lines.append("- BSR >= BS: no se requiere ajuste")
            elif bs.get("step"):
                lines.append(f"- Paso requerido: {bs['step']} mm  Rango: {bs.get('range_name')}")
            else:
                lines.append(f"- DIF BS = {bs.get('dif_original')} mm (no encontrado en rangos)")

    lines.append("---")
    return "\n".join(lines)


def get_chat_response(
    user_message:  str,
    history:       list,
    calc_results:  dict | None,
    all_params:    dict | None,
) -> str:
    """
    Envía el mensaje del usuario a Claude y devuelve la respuesta.

    history: lista de dicts {"role": "user"|"assistant", "content": str}
    """
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ API key no configurada. Agrega ANTHROPIC_API_KEY en .streamlit/secrets.toml"

    client = anthropic.Anthropic(api_key=api_key)

    # Sistema con contexto del survey actual
    context_block = _build_context_block(calc_results, all_params)
    system = SYSTEM_PROMPT + context_block

    # Construir historial (limitar para no saturar tokens)
    trimmed = history[-(MAX_HISTORY):]
    messages = [{"role": m["role"], "content": m["content"]} for m in trimmed]
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model      = MODEL,
            max_tokens = MAX_TOKENS,
            system     = system,
            messages   = messages,
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "⚠️ API key inválida. Verifica ANTHROPIC_API_KEY en secrets.toml"
    except anthropic.RateLimitError:
        return "⚠️ Límite de rate alcanzado. Intenta en unos segundos."
    except Exception as e:
        return f"⚠️ Error al contactar la API: {e}"
