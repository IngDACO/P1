# -*- coding: utf-8 -*-
"""Documenta v542 — el Survey se limpia de verdad y no mezcla proyectos."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
NEG = "C:/Users/diego/P1/NEGOCIO.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
PROD = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## EL SURVEY SE LIMPIA DE VERDAD Y NO MEZCLA PROYECTOS (v542)

Al revisar la matriz del Survey (decisión pendiente «¿es de su obra?») salió primero un fallo:

**A. ⚠️ Lo que REEMPLAZA no limpiaba.** El `data_editor` de la matriz tenía clave fija y filas
fijas, y Streamlit 1.64 lo identifica por la clave y la FORMA de los datos «para que las
ediciones sobrevivan a cambios de valores» (comentario en su código): «Duplicate survey»,
«Clear everything and start over», «Load matrix (.xlsx)» y «Rebuild the project in the
Survey» ponían la matriz nueva en el servidor y las celdas tecleadas volvían encima. Y «Clear
everything» BORRABA los parámetros y la configuración con los campos en pantalla: el servidor
a cero, el navegador con lo viejo, que devolvía en el clic siguiente (trampa nº31).
→ La matriz lleva una clave con generación y quien la reemplaza llama a
`estado_vivo.tabla_nueva("sv")`; «empezar de cero» (`survey_ui._limpiar_survey`) ASIGNA los
valores de partida (los mismos de `init_state`, `_CFG_INICIAL`).

**B. Decisión del usuario: «no se deben mezclar informaciones de proyectos».**
- Al **guardar el survey en su proyecto**, el survey EMPIEZA DE CERO, el selector del admin
  vuelve a «sin proyecto» y el aviso con «Open project ➜» pasa arriba (sobrevive).
- De una **obra real a otra** (sin salir o volviendo), el survey EMPIEZA DE CERO y manda el
  plano de la nueva (`estado_vivo.cambio_de_obra`). Se acaba la excepción de v535 que dejaba
  lo medido a mano.
- **Duplicate for the next lift** se queda (decisión del usuario): lo duplicado lo ADOPTA la
  siguiente obra DISTINTA (`estado_vivo.adoptar_siguiente`) y su plano manda.
- **Sin obra → obra** (teclear antes de fichar) conserva: no viene de ningún proyecto.
- Cerrar la jornada y volver a la misma obra conserva (v541).
- El contador de pasadas ya no decide nada (trampa nº32).

⚠️ El guardián cazó que el aviso «empezó de cero» se perdía: con otro nº de paradas la
matriz se redimensiona con `st.rerun()`. Va por `flash`, como los avisos del guardado.

__PROD__ · 25 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v542 | **El Survey se limpia de verdad y no mezcla proyectos.** ⚠️ «Duplicate», «Clear "
        "everything», importar un Excel y «Rebuild» dejaban las celdas tecleadas ENCIMA de la "
        "matriz nueva (el `data_editor` con clave y filas fijas re-aplica las ediciones), y "
        "«Clear everything» borraba los campos sin que el navegador se enterara: matriz con "
        "clave por generación y «empezar de cero» que ASIGNA. Decisión del usuario: guardar el "
        "survey en su proyecto lo limpia, y de una obra a otra empieza de cero; «Duplicate» se "
        "queda (lo adopta la siguiente obra) y teclear antes de fichar se conserva. "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v541 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v541 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v541).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v542).*"
E_VIEJA = ("al_pintar(): se olvida solo al pintarse con OTRA obra real, sin obra nunca (v541); ")
E_NUEVA = ("al_pintar(): se olvida solo al pintarse con OTRA obra real, sin obra nunca (v541); "
           "tabla_nueva() al REEMPLAZAR una tabla editable, y el Survey empieza de cero de una "
           "obra a otra (cambio_de_obra) salvo lo duplicado (adoptar_siguiente) (v542); ")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v542.py "<suite>" "<bateria>" "<produccion>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__PROD__", PROD)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
unica(c, E_VIEJA, "estado_vivo", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v542 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v542 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v542 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(E_VIEJA, E_NUEVA)
lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar: %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]
c = "".join(lineas)
m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v542 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v542")
