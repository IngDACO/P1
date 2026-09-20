"""F1b (2/2) — la IA del informe del CLIENTE escribe en inglés.

⚠️ Las CLAVES de `USER_SCHEMA` (`resumen`, `desplazamientos`, `cortes`,
`implementacion`, `verificacion`) NO se tocan: se guardan en `Proyectos.InterpJSON`
y las lee `user_report.ia.get("resumen")`. Traducirlas dejaría en blanco las cinco
secciones de texto de todos los informes, sin ningún error. Solo cambia el PROMPT
y las descripciones, que es lo que el modelo lee.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"C:\Users\diego\P1\survey_app\core\interpretation.py")
s = p.read_text(encoding="utf-8")

PROMPT_VIEJO = '''USER_SYSTEM_PROMPT = """Eres un ingeniero senior de COPEX, especialista en instalación de elevadores.
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
"""'''

PROMPT_NUEVO = '''# ⚠️ El informe del CLIENTE sale SIEMPRE en inglés, como el resto de documentos que
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
"""'''

SCHEMA_VIEJO = '''USER_SCHEMA = {
    "resumen":        "Resumen ejecutivo (3-5 frases) de la solución final de posicionamiento, en lenguaje claro para el cliente. Debe dar confianza de que es la solución definitiva.",
    "desplazamientos":"Instrucción precisa de los desplazamientos a realizar: RL (lateral) y FB (frontal), con valores en mm, dirección clara (izquierda/derecha, adelante/atrás) y el motivo de cada uno. Que el técnico sepa exactamente qué mover.",
    "cortes":         "Si hay cortes necesarios (piso, cuántos mm, en qué lado de la apertura), descríbelos con precisión y por qué. Si NO se requiere ningún corte, dilo claramente y con seguridad.",
    "implementacion": "Pasos concretos y ordenados para implementar la solución en obra (lista breve, accionable).",
    "verificacion":   "Qué debe verificar el técnico tras la instalación para confirmar que quedó correcto (checklist breve).",
}'''

SCHEMA_NUEVO = '''# ⚠️ Las CLAVES son DATO, no etiqueta: se guardan en `Proyectos.InterpJSON` y las lee
# `user_report` (`ia.get("resumen")`). Traducirlas dejaría las cinco secciones de texto
# EN BLANCO en todos los informes, sin ningún error. Solo se traduce la descripción.
USER_SCHEMA = {
    "resumen":        "Executive summary (3-5 sentences) of the final positioning solution, in plain language for the client. It must give confidence that this is the definitive solution.",
    "desplazamientos":"Precise instruction of the shifts to carry out: RL (lateral) and FB (front), with values in mm, a clear direction (left/right, forward/rear) and the reason for each. The technician must know exactly what to move.",
    "cortes":         "If cuts are required (floor, how many mm, which side of the opening), describe them precisely and why. If NO cut is required, say so clearly and with confidence.",
    "implementacion": "Concrete, ordered steps to implement the solution on site (short, actionable list).",
    "verificacion":   "What the technician must check after installation to confirm it is correct (short checklist).",
}'''

R = [
    (PROMPT_VIEJO, PROMPT_NUEVO),
    (SCHEMA_VIEJO, SCHEMA_NUEVO),
    ('            "Redacta el informe para el cliente. Retorna SOLO un JSON con estas claves: "\n'
     '            + ", ".join(f\'"{k}"\' for k in USER_SCHEMA.keys())\n'
     '            + ". Cada valor es una cadena de texto en español profesional."',
     '            "Write the client report. Return ONLY a JSON with these keys: "\n'
     '            + ", ".join(f\'"{k}"\' for k in USER_SCHEMA.keys())\n'
     '            + ". Each value must be a string of professional ENGLISH text."'),
    # el fallback también lo lee el cliente
    ('return _user_fallback("librería anthropic no disponible en el entorno.")',
     'return _user_fallback(d("the anthropic library is not available in this environment."))'),
    ('return _user_fallback("API key no configurada.")',
     'return _user_fallback(d("API key not configured."))'),
    ('return _user_fallback("La API no retornó JSON válido.")',
     'return _user_fallback(d("The API did not return valid JSON."))'),
]

falt = [o for o, _ in R if s.count(o) != 1]
if falt:
    print(f"⚠️ {len(falt)} anclas NO casan exactamente una vez:")
    for x in falt:
        print("   ···", x[:110].replace("\n", " ⏎ "), f"  (veces={s.count(x)})")
    sys.exit(1)

for o, n in R:
    s = s.replace(o, n, 1)

anc = "import streamlit as st\n"
assert s.count(anc) == 1
s = s.replace(anc, "import streamlit as st\n\nfrom core.i18n import d\n", 1)

p.write_text(s, encoding="utf-8")
print(f"OK — {len(R)} reemplazos aplicados en interpretation.py")
