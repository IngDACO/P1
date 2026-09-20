# -*- coding: utf-8 -*-
"""F5e, segunda parte: `chat_agent` — los mensajes de ERROR y el prompt del briefing.

ATENCION — decision de criterio, escrita a proposito: la BASE DE CONOCIMIENTO del
prompt (353 lineas de geometria del hueco, formulas, casos 1/2, diagnostico) se
QUEDA en espanol. Lo que decide el idioma de la respuesta es la regla de estilo, que
ya dice «responde SIEMPRE en ingles tecnico claro aunque esta guia este en espanol»;
el modelo lee espanol sin problema. Traducir 353 lineas de contenido tecnico denso
mete riesgo de error de traduccion en el conocimiento del asistente a cambio de cero
beneficio visible. Es una exclusion DELIBERADA, no un olvido.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\chat_agent.py")

C = [
    ('return "\u26a0\ufe0f La librer\u00eda anthropic no est\u00e1 disponible en el entorno."',
     'return "\u26a0\ufe0f The anthropic library is not available in this environment."'),
    ('return "\u26a0\ufe0f API key no configurada. Agrega ANTHROPIC_API_KEY en .streamlit/secrets.toml"',
     'return "\u26a0\ufe0f API key not configured. Add ANTHROPIC_API_KEY to .streamlit/secrets.toml"'),
    ('return "\u26a0\ufe0f API key inv\u00e1lida. Verifica ANTHROPIC_API_KEY en secrets.toml"',
     'return "\u26a0\ufe0f Invalid API key. Check ANTHROPIC_API_KEY in secrets.toml"'),
    ('return "\u26a0\ufe0f L\u00edmite de rate alcanzado. Intenta en unos segundos."',
     'return "\u26a0\ufe0f Rate limit reached. Try again in a few seconds."'),
    ('return f"\u26a0\ufe0f Error al contactar la API: {e}"',
     'return f"\u26a0\ufe0f Error contacting the API: {e}"'),
    ('return f"No se pudo armar el resumen: {e}"',
     'return f"Could not build the summary: {e}"'),
    ('lines = ["\n---\n## Datos del survey actual en sesi\u00f3n\n"]',
     'lines = ["\n---\n## Current survey data in session\n"]'),
    ('lines.append(f"- OFF por columna: {obc}")',
     'lines.append(f"- OFF per column: {obc}")'),
    ('lines.append("- BSR >= BS: no se requiere ajuste")',
     'lines.append("- BSR >= BS: no adjustment required")'),
    ('lines.append(f"- Paso requerido: {bs[\'step\']} mm  Rango: {bs.get(\'range_name\')}")',
     'lines.append(f"- Step required: {bs[\'step\']} mm  Range: {bs.get(\'range_name\')}")'),
    ('lines.append(f"- DIF BS = {bs.get(\'dif_original\')} mm (no encontrado en rangos)")',
     'lines.append(f"- DIF BS = {bs.get(\'dif_original\')} mm (not found in any range)")'),
    ('"Genera un RESUMEN EJECUTIVO muy breve (vi\u00f1etas, m\u00e1ximo ~8 l\u00edneas) de lo m\u00e1s relevante que el "\n'
     '        "administrador tiene PENDIENTE hoy en su grupo, priorizando lo urgente '
     '(vencidos, retrasos, alarmas, "\n'
     '        "near miss) y cerrando con 1-2 acciones sugeridas. Concreto y accionable. '
     'Usa SOLO los datos provistos; "\n'
     '        "no inventes. Si no hay pendientes, dilo en una l\u00ednea.")',
     '"Write a very short EXECUTIVE SUMMARY in English (bullets, at most ~8 lines) of '
     'what matters most "\n'
     '        "among what the administrator has PENDING in their group today, putting '
     'the urgent first "\n'
     '        "(overdue, delays, alarms, near misses) and closing with 1-2 suggested '
     'actions. Concrete and "\n'
     '        "actionable. Use ONLY the data provided; do not invent anything. If there '
     'is nothing pending, "\n'
     '        "say so in one line.")'),
    ('"content": "Datos del grupo hoy:\n\n" + facts + "\n\nDame el resumen de pendientes."',
     '"content": "Group data today:\n\n" + facts + "\n\nGive me the summary of pending items."'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in C:
    n = src.count(viejo)
    if n != 1:
        print(f"  AVISO {n} de {viejo.splitlines()[0][:58]!r}")
        continue
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo.splitlines()[0][:58]}")
F.write_text(src, encoding="utf-8")
