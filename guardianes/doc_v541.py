# -*- coding: utf-8 -*-
"""Documenta v541 — sin obra no se olvida nunca (una regla, no dos)."""
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

SECCION = """## SIN OBRA NO SE OLVIDA NUNCA — UNA REGLA, NO DOS (v541)

⚠️ Visto EN PRODUCCIÓN con la cuenta de campo (07/10/2026), cerrando el pendiente «el campo
cambia de obra con el fichaje del menú lateral»: en Rieles con PRUEBA MOVIL, LFKK 1234 y 3
rieles de 2500 tecleados; «Close workday and project» en el menú lateral → todo a 0, SIN haber
cambiado de obra (y volver a fichar en la misma obra, p. ej. tras comer, lo habría perdido
igual). Los botones del fichaje terminan en `st.rerun()`, que corta la pasada ANTES de pintar
la herramienta: en la siguiente, `al_pintar` creía que la herramienta «volvía» de otra
pantalla, y volver olvidaba también al pasar a «sin obra». Venía de v535; hasta v540 no se
notaba porque el borrado no llegaba al navegador.

→ Una regla: lo tecleado es de la última obra REAL; se olvida al pintarse con OTRA obra real
(también la primera tras usarla sin obra: manda su plano, la decisión de v535); **sin obra,
nunca**. Lo cargado sin obra conocida (`respetar` sin obra) lo adopta la primera obra real. El
Survey sigue igual que antes: sin salir solo manda el plano; al volver con otra obra real,
olvida (el contador de pasadas ya solo decide eso).

⚠️ El guardián destapó de paso un fallo latente desde v535: al volver al Survey con otra obra,
`olvidar` BORRABA el nº de paradas y el plano lo ponía como 5.0 (decimal): `aplicar` solo lo
deja entero si lo que había era entero. Ahora `ns` tiene su valor por defecto (el 2 de
`init_state`) y se ASIGNA.

Logs del Cloud (05:53-07:09 UTC): el Cloud reinició el contenedor a las 05:53 (por eso la
pestaña de campo apareció recargada y como admin: la cookie); las versiones fijadas se cumplen
(extra-streamlit-components 0.1.81, streamlit-folium 0.27.4, drawable-canvas 0.9.3, Streamlit
1.64.0; anthropic 1.11.0 dentro de `<2`); cero errores y cero trazas.

__PROD__ · 20 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v541 | **Sin obra no se olvida nunca (una regla, no dos).** ⚠️ Visto en producción con "
        "la cuenta de campo: cerrar la jornada desde el menú lateral DENTRO de Rieles borraba lo "
        "tecleado sin cambiar de obra — los botones del fichaje cortan la pasada con "
        "`st.rerun()` y la herramienta creía «volver». Ahora se olvida solo al pintarse con OTRA "
        "obra real; sin obra, nunca; el Survey, como antes. ⚠️ Y el nº de paradas volvía como "
        "5.0 al volver al Survey con otra obra (latente desde v535): `ns` con valor por defecto. "
        "Logs del Cloud limpios (reinicio a las 05:53). __PROD__ · __BATERIA__ · __SUITE__ |\n")

TRAMPA = """32. ⚠️ **Una pasada cortada por `st.rerun()` no es «haber salido» de la pantalla.**
    `estado_vivo` decidía si una herramienta «volvía» mirando si se pintó en la pasada
    anterior; los botones del fichaje del menú lateral terminan en `st.rerun()` ANTES de que
    se pinte la herramienta, así que cerrar la jornada desde Rieles contaba como salir y
    volver (v541). AppTest lo reproduce si el botón del guion hace `st.rerun()`; uno que solo
    cambie el estado no. → No deducir navegación del contador de pasadas.

"""

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v540 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v540 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
A_TRAMPA = "**Y la regla de siempre, que volvió a aplicar:**"
N_VIEJA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v540).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v541).*"
E_VIEJA = ("olvidar() ASIGNA el valor por defecto y vacía las tablas de lo medido con una tabla "
           "editable nueva (v540); ")
E_NUEVA = ("olvidar() ASIGNA el valor por defecto y vacía las tablas de lo medido con una tabla "
           "editable nueva (v540); al_pintar(): se olvida solo al pintarse con OTRA obra real, "
           "sin obra nunca (v541); ")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v541.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, A_TRAMPA, "trampas", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v541 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v541 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v541 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(E_VIEJA, E_NUEVA)
c = c.replace(A_TRAMPA, TRAMPA + A_TRAMPA)
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
print("CLAUDE.md: fila v541 + trampa nº32 · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v541")
