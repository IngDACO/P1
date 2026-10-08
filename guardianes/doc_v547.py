# -*- coding: utf-8 -*-
"""Documenta v547 — barrido: todo desplegable con controles dentro lleva clave."""
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

SECCION = """## BARRIDO: TODO DESPLEGABLE CON CONTROLES DENTRO LLEVA CLAVE (v547)

Lo destapó Fichaje en v546 (trampa nº35): un `st.expander` SIN clave se cierra solo cuando
cambia lo que tiene encima, y cada acción deja encima un aviso por `flash` que aparece una
pasada y se va. Con controles dentro, el usuario pierde el botón a mitad de la tarea. Había
**65** así en la app (16 en usuarios/propietario, 16 en Proyectos, 6 en Inventario, 4 en el
Survey, el chat del lateral…). Decisión del usuario: barrido de una vez, con guardián.

- La clave sigue el esquema de las claves de los controles de dentro: con `key_prefix` o con
  el ID de la entidad (obra, activo, factura, nómina, cliente…), para que lo abierto en una no
  se arrastre a otra y para que dos copias no choquen.
- En bucles (parte diario, historial del Pre-Start, avance por etapas) lleva el elemento.
- Los 4 que se abren solos según los datos («Upload manual» sin manuales, «Add rail» sin
  rieles, las instrucciones de obra con enlaces, Xero con pendientes) llevan esa condición en
  la clave: con clave, Streamlit solo respeta `expanded` la primera vez.
- Prefijo `exp_`, comprobado contra los selectores CSS por subcadena (`[class*=st-key-…]`).
- ⚠️ El script del barrido se paró a mitad: `end_col_offset` del AST va en BYTES UTF-8 y una
  línea con «—» desplazaba la columna. Revisadas las 38 primeras a mano en el diff (bien) y
  corregido el cálculo para las 27 restantes; `pyflakes` sin nombres sin definir.

Guardián `verif_v547` (AST sobre el código real, con sondas validadas contra casos
construidos): todo desplegable con controles lleva clave; ninguna clave fija se repite; en
bucles usa la variable del bucle; si `expanded` depende de datos, la condición va en la clave;
ningún CSS atrapa `exp_`. Exentas por nombre (anteriores): `cpxresumen`, `cpx_lectura_ia`,
`tc_corregir`.

__PROD__ · 17 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v547 | **Barrido: todo desplegable con controles dentro lleva clave (trampa 35).** "
        "65 en la app se cerraban solos cuando el aviso de arriba aparecía o se iba. La clave "
        "sigue el esquema de sus controles (key_prefix / ID), en bucles lleva el elemento y, si "
        "se abría solo según los datos, la condición. Guardián AST de las 4 reglas + CSS. "
        "__PROD__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v546 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v546 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v546).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v547).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v547.py "<suite>" "<bateria>" "<produccion>"')
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
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v547 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v547 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v547 = actual)")
c = c.replace(CAB, CAB + FILA)
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
print("CLAUDE.md: fila v547 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v547")
