# -*- coding: utf-8 -*-
"""Documenta v540 — olvidar también en el navegador; las tablas de lo medido son de su obra."""
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

SECCION = """## OLVIDAR TAMBIÉN EN EL NAVEGADOR — Y LAS TABLAS DE LO MEDIDO SON DE SU OBRA (v540)

⚠️ Visto EN PRODUCCIÓN con la cuenta del admin, probando v539: en Belting, de 88 walker a otra
obra (sin plano) SIN salir de la herramienta, la pantalla seguía con HQ 14045, HGP 85 y HGPR
1785, y «Calculate» calculó con ellos bajo el nombre de la otra obra. La regla de v535 («de X
a Y sin salir, se olvida») BORRABA las entradas en el servidor; pero Streamlit 1.64 identifica
`number_input` y `radio` SOLO por su clave, y el navegador solo se entera de un valor cuando
el código lo ASIGNA (la trampa de v529, otra vez): se quedaba con el viejo y lo devolvía en el
clic siguiente. AppTest lee el SERVIDOR, así que los guardianes de v535 lo daban por bueno.
Solo funcionaba lo que el plano de la obra nueva ASIGNA.

→ `estado_vivo.olvidar` ASIGNA el valor por defecto de cada entrada (`DEFECTOS`, comprobado
contra el widget real pintando las cuatro herramientas; el HGPR por prefijo).

Y las tablas de lo medido —HKPR de cada buffer, BSR de cada ascensor, L de cada ascensor, la
matriz del caso 2— no se olvidaban NUNCA (ni al volver con otra obra): ahora son de su obra
(`TABLAS`). Ponerlas a ceros no basta: un `data_editor` con clave y filas fijas se identifica
por la clave y la FORMA de los datos «para conservar las ediciones» (código de Streamlit), así
que el navegador volvería a aplicar lo tecleado. Su clave lleva una generación
(`clave_tabla`) que sube al olvidar: tabla nueva para el navegador.

De paso: «Descargar belting.pdf» en Files salía en español (un literal concatenado, la forma
que las redes de i18n no ven — trampa nº30).

El guardián mira `proto.set_value` (lo que recibe el navegador), con la sonda validada contra
el `olvidar` de v539.

__PROD__ · 23 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v540 | **Olvidar también en el navegador; las tablas de lo medido son de su obra.** ⚠️ "
        "Visto en producción con el admin: de 88 walker a otra obra sin salir de Belting, la "
        "pantalla seguía con HQ/HGP/HGPR de 88 walker y «Calculate» los usó — v535 BORRABA en "
        "el servidor y el navegador (que solo se entera de lo ASIGNADO, trampa de v529) los "
        "devolvía. `olvidar` asigna el valor por defecto (`DEFECTOS`, comprobado contra el "
        "widget real); las tablas de lo medido (HKPR, BSR, L, matriz del caso 2), que no se "
        "olvidaban nunca, se vacían con una tabla editable NUEVA (`clave_tabla`). Y «Descargar» "
        "→ «Download». __PROD__ · __BATERIA__ · __SUITE__ |\n")

TRAMPA = """31. ⚠️ **Borrar el valor de un widget EN PANTALLA no le llega al navegador.** Streamlit
    1.64 identifica `number_input`/`radio` solo por su clave, y el navegador solo recibe un
    valor cuando el código lo ASIGNA (`proto.set_value`): con `del`/`pop` se queda con el
    viejo y lo devuelve en el clic siguiente. Mordió DOS veces —la caja del parte (v529) y el
    cambio de obra sin salir de la herramienta (v535, visto en v540 con el admin)— y las dos
    con AppTest en verde, porque AppTest lee el SERVIDOR. Un `data_editor` con clave y filas
    fijas, además, conserva sus ediciones mientras la forma de los datos no cambie: para
    vaciarlo hace falta OTRA clave. → Para «vaciar», ASIGNAR; y el guardián mira
    `proto.set_value`, no solo `.value`.

"""

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v539 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v539 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
A_TRAMPA = "**Y la regla de siempre, que volvió a aplicar:**"
N_VIEJA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v539).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v540).*"
E_VIEJA = "respetar(h, obra): lo cargado a propósito es de SU obra (v539); "
E_NUEVA = ("respetar(h, obra): lo cargado a propósito es de SU obra (v539); olvidar() ASIGNA "
           "el valor por defecto y vacía las tablas de lo medido con una tabla editable nueva "
           "(v540); ")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v540.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v540 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v540 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v540 = actual)")
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
print("CLAUDE.md: fila v540 + trampa nº31 · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v540")
