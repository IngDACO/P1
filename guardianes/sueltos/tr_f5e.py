# -*- coding: utf-8 -*-
"""F5e: los prompts de la IA (`interpretation`, `chat_agent`).

Van en idioma BASE, sin `t()`: el prompt decide en que idioma ESCRIBE el modelo, y
el informe admin que lo consume ya esta en ingles. Es la misma decision que v437
tomo con el prompt del informe del CLIENTE.

ATENCION: las CLAVES de `INTERPRETATION_SCHEMA` no se tocan (se guardan en
`InterpJSON`), ni las del payload (`FB_aplicado`, `total_OFF`...), que las lee el
propio prompt por nombre.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

C = [
    ("core/interpretation.py",
     '"Caso 1 (pared limitante)" if p.get("WALL_LIMITING") else "Caso 2 (sin pared limitante)"',
     '"Case 1 (limiting wall)" if p.get("WALL_LIMITING") else "Case 2 (no limiting wall)"'),
    ("core/interpretation.py",
     '"Analiza estos datos y retorna SOLO un JSON con estas claves: "',
     '"Analyse this data and return ONLY a JSON object with these keys: "'),
    ("core/interpretation.py",
     '". Para \'evasion_pared\' retorna null si WALL_LIMITING es False o si "\n'
     '            "FB_extra_usado es False. Cada valor debe ser una cadena de texto en espa\u00f1ol."',
     '". For \'evasion_pared\' return null if WALL_LIMITING is False or if "\n'
     '            "FB_extra_usado is False. Every value must be a text string in English."'),
    ("core/interpretation.py", '_fallback("librer\u00eda anthropic no disponible en el entorno.")',
     '_fallback("the anthropic library is not available in this environment.")'),
    ("core/interpretation.py", '_fallback("La API no retorn\u00f3 JSON v\u00e1lido.")',
     '_fallback("The API did not return valid JSON.")'),
]

for rel, viejo, nuevo in C:
    p = R / rel
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != 1:
        print(f"  AVISO {rel}: {n} de {viejo.splitlines()[0][:56]!r}")
        continue
    p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {viejo.splitlines()[0][:58]}")

# los que salen 2 veces (fallback admin + fallback cliente)
for viejo, nuevo, esp in (
        ('_fallback("API key inv\u00e1lida.")', '_fallback("Invalid API key.")', 1),
        ('_user_fallback("API key inv\u00e1lida.")', '_user_fallback("Invalid API key.")', 1),
        ('_fallback("Error al parsear respuesta de la API.")',
         '_fallback("Could not parse the API response.")', 1),
        ('_user_fallback("Error al parsear respuesta de la API.")',
         '_user_fallback("Could not parse the API response.")', 1)):
    p = R / "core/interpretation.py"
    s = p.read_text(encoding="utf-8")
    n = s.count(viejo)
    if n != esp:
        print(f"  AVISO interpretation: esperaba {esp} y hay {n} de {viejo[:46]!r}")
        continue
    p.write_text(s.replace(viejo, nuevo), encoding="utf-8")
    print(f"  OK  {n}x {viejo[:52]}")
