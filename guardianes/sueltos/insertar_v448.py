# -*- coding: utf-8 -*-
"""Inserta la sección y la fila de v448 en CLAUDE.md (por fichero, no por shell)."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
D = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
     r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\doc_v448.md")

FILA = (
    "| v448 | **F5 CERRADO: el informe ADMIN, los correos y los prompts de la IA** — "
    "la app ya no tiene un solo texto en español salvo lo que es DATO. El informe "
    "admin (101 cadenas) va con `_d()` aplicado **por AST y por posición**, ⚠️ "
    "refusando toda cadena que se use como ÍNDICE (`'Duración (d)'`, `'Línea'`: son "
    "contrato con `schedule_table`/`plumb_table`). ⚠️ **El barrido del FUENTE se dejó "
    "22 líneas** y las encontró **generar el PDF y leer su texto** — la trampa nº27 "
    "otra vez —, capturando además el log del módulo, porque el veredicto va dentro "
    "de un `try/except` que registra y sigue (el fallo real de v437). ⚠️ Y el prefijo "
    "`\"[Interpretación no disponible\"` se **produce** en `interpretation` y se "
    "**compara** en `report` y `user_report`: los cuatro a la vez, o el informe "
    "imprimiría el mensaje de error como si fuera la interpretación. ⚠️ **Decisión de "
    "criterio dicha en voz alta**: la base de conocimiento de `chat_agent` (353 "
    "líneas) se queda en español y solo se traduce la REGLA DE ESTILO, que ahora "
    "ordena responder en inglés — el modelo lee español, y traducir contenido técnico "
    "denso mete riesgo de error en el conocimiento del asistente a cambio de nada. "
    "Quedan tres exclusiones declaradas: los nombres de actividad (dato de la hoja "
    "`Actividades`), esa base de conocimiento, y las CLAVES de schemas y columnas. "
    "7 roturas probadas |\n"
)

doc = io.open(D, encoding="utf-8").read().rstrip()
s = io.open(P, encoding="utf-8").read()

ancla = "## i18n F5c:"
assert ancla in s, "ancla de sección NO casa"
s = s.replace(ancla, doc + "\n\n" + ancla, 1)

old = "## Versiones desplegadas (v447 = actual)"
assert old in s, "ancla de tabla NO casa"
s = s.replace(old, "## Versiones desplegadas (v448 = actual)", 1)

f447 = "| v447 | **F5c: los 14 módulos de backend"
assert f447 in s, "ancla de fila v447 NO casa"
s = s.replace(f447, FILA + f447, 1)

io.open(P, "w", encoding="utf-8", newline="").write(s)

fila = [ln for ln in s.splitlines() if ln.startswith("| v448 |")]
assert len(fila) == 1, f"esperaba 1 fila v448, hay {len(fila)}"
for simbolo in ("schedule_table", "chat_agent", "user_report", "Actividades"):
    assert simbolo in fila[0], f"la fila perdió {simbolo!r}"
sec = re.search(r"## i18n F5 CERRADO:.*?(?=\n## )", s, re.S)
assert sec, "la sección de v448 no está"
for simbolo in ("verif_v448.py", "InterpJSON", "schedule.PHASES", "pypdf"):
    assert simbolo in sec.group(0), f"la sección perdió {simbolo!r}"
print(f"CLAUDE.md: fila ({len(fila[0])} chars) y sección "
      f"({len(sec.group(0).splitlines())} líneas) OK")
