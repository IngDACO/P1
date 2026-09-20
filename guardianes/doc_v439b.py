"""Corrige la documentación de v439: F2 NO estaba completa cuando lo dije.

El texto se escribió antes de que el smoke test destapara 47 etiquetas más en español.
Un registro que dice «hecho» sobre algo que no lo estaba es peor que no tenerlo.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = DOC.read_text(encoding="utf-8")

VIEJO = """Cierra F1 (todo lo que SALE de la empresa) y hace F2 entera. **235 reemplazos**: 13 en
`notify.py` / `alerts.py` (correos de asignación e inducción, alarmas de problema y de
cambio) y 222 en los cuatro módulos que usa el técnico en obra — `timeclock_ui`,
`prestart_ui`, `ausencias_ui`, `route_ui`."""

NUEVO = """Cierra F1 (todo lo que SALE de la empresa) y hace F2 entera. **269 reemplazos**: 13 en
`notify.py` / `alerts.py` (correos de asignación e inducción, alarmas de problema y de
cambio) y 256 en los cuatro módulos que usa el técnico en obra — `timeclock_ui`,
`prestart_ui`, `ausencias_ui`, `route_ui`."""

assert s.count(VIEJO) == 1, f"ancla 1: {s.count(VIEJO)}"
s = s.replace(VIEJO, NUEVO, 1)

# ── El hallazgo que faltaba, insertado antes de «Lo que NO se traduce» ──────────
ANCLA2 = "### Lo que NO se traduce\nLas **claves de dato**"
BLOQUE = """### ⚠️ DIJE QUE F2 ESTABA TERMINADA Y QUEDABAN 47 ETIQUETAS EN ESPAÑOL
Mi barrido usaba un **detector de español** (acentos + palabras funcionales) y dio «0
restantes». Es falso, y de la peor manera: «Fichar», «Firma», «Iniciales», «Pendientes»,
«Sitios», «Descargar PDF» o el propio título **«Mis ausencias»** no llevan acento ni
palabra funcional, así que pasaron por delante. Es el mismo agujero que dejó escapar
«Planificado» en v438 y «Registrados» en el guardián de esta misma versión — **tres veces
el mismo detector, tres veces el mismo tipo de palabra**.
Lo destapó el smoke test, que al EJECUTAR `render_mis_ausencias` imprimió lo que la
pantalla pinta: `'## :material/event_busy: Mis ausencias'`.
→ El barrido bueno no busca español: busca **posición**. Todo literal que llega a una
función de display y NO está envuelto en `t()`, revisado luego a mano para separar
etiqueta de dato. Con él salieron 47, y el guardián lo lleva ahora como chequeo con
tope MEDIDO (que el número suba significa que alguien metió una etiqueta suelta).

### ⚠️ Y «compilan e importan» no es una verificación
Los dos `UnboundLocalError` de arriba y las 47 etiquetas convivieron con un
`compileall` en verde y los cuatro módulos importando sin queja. Lo que encontró las
dos cosas fue **llamar a las funciones** (`check_v439_smoke.py`, que ejecuta
`_aviso_olvido` y `render_mis_ausencias` con las dependencias de Sheets sustituidas y
mira lo que pintan). Importar no ejecuta — la lección de v378, aplicada a mí mismo.

"""
assert s.count(ANCLA2) == 1, f"ancla 2: {s.count(ANCLA2)}"
s = s.replace(ANCLA2, BLOQUE + ANCLA2, 1)

# ── Los guardianes caducados ────────────────────────────────────────────────────
ANCLA3 = "### ⚠️ Y la corrección de escala que hay que decir en voz alta"
CADUCA = """### Cuatro guardianes CADUCADOS (actualizados, no relajados)
`verif_v307` (Ruta del día), `verif_v308` (Fichaje), `verif_v408` (Pre-Start) y
`verif_v430` (Ausencias) fijaban literales en ESPAÑOL de los módulos que F2 tradujo.
Se miró el código acusado antes de tocar nada (regla v385): las cuatro conductas siguen
intactas y lo único que cambió es el idioma, a propósito. La afirmación se reescribe
sobre el PRINCIPIO —que la tabla marque los tres estados de fichaje, que exista la
tarjeta de la semana, que el aviso de duplicado remita a firmar, que el saldo diga de
qué periodo habla y avise cuando lo estima— con la razón escrita al lado, y donde se
pudo se ancló a la parte estable (el EMOJI del estado, no la palabra).

"""
assert s.count(ANCLA3) == 1, f"ancla 3: {s.count(ANCLA3)}"
s = s.replace(ANCLA3, CADUCA + ANCLA3, 1)

# ── Fila de la tabla ────────────────────────────────────────────────────────────
VF = ("hechos: se reaplicaron y se verificaron GENERANDO los mensajes. Guardián probado ")
NF = ("hechos: se reaplicaron y se verificaron GENERANDO los mensajes. ⚠️ **Y dije que F2 "
      "estaba terminada con 47 etiquetas aún en español**: mi detector busca acentos y "
      "palabras funcionales, y «Fichar», «Firma», «Pendientes» o «Mis ausencias» no tienen "
      "ninguna de las dos (tercera vez del mismo agujero: v438, el guardián de v439 y "
      "esto). Lo destapó el smoke test al EJECUTAR la pantalla; el barrido pasa a ser por "
      "POSICIÓN (literal de display sin `t()`), no por idioma. Guardián probado ")
assert s.count(VF) == 1, f"ancla 4: {s.count(VF)}"
s = s.replace(VF, NF, 1)

DOC.write_text(s, encoding="utf-8")
print(f"OK — CLAUDE.md {len(s.splitlines())} líneas")
