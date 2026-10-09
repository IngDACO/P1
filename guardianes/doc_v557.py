# -*- coding: utf-8 -*-
"""Documenta v557 — Users (Planificación), probada acción por acción."""
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

SECCION = """## USERS (PLANIFICACIÓN), PROBADA ACCIÓN POR ACCIÓN (v557)

Recorrido en producción (Planning → Users, decisión del usuario: «Arregla todo»), sin
crear, cambiar ni borrar a nadie. Funcionaban la lista, la ficha y sus 5 pestañas, y el
alta sin correo se rechazaba. Arreglado:

- ⚠️ **Correos que no lo son.** Había guardados «driver 1», «…@hotmai.com» y
  «…@hotmai.commomo»: ni el alta ni la ficha validaban nada, y con ellos los avisos no
  llegan a nadie sin que la pantalla lo diga. `auth.revisar_email`: lo que no es un
  correo NO se guarda (también `set_contact`, el motor); una probable errata de un
  proveedor frecuente se pregunta («Did you mean …?», umbral 0,78 medido sobre los datos
  reales) y solo se guarda confirmándola. La tabla («invalid email» / «check email») y la
  ficha los señalan; el correo se mira ANTES de crear la cuenta.
- ⚠️ **El alta borraba todo al dar un error** (`clear_on_submit=True`: sin correo se iban
  también usuario, nombre y contraseña). Conserva lo escrito y se vacía solo al crear
  (formulario por generación). También el del propietario y el de añadir credencial.
- ⚠️ **Contraseñas de 1 carácter valían.** Mínimo 8 (`auth.MIN_PW`) en altas y cambios;
  las existentes no se tocan. El cambio pide repetirla y vacía los campos al guardar. En
  `add_user` el mínimo se mira DESPUÉS del rol y el grupo (los mensajes de antes siguen).
- La línea de salud, ACTIVA: cada problema (sin contacto, correo, credenciales,
  inactivos) filtra la tabla — con una clave por filtro, porque la selección es un número
  de fila y se cruzaría entre filtros.
- «ContactName» en bruto → «Contact» (aquí y en el panel del propietario); la tarifa con
  «$»; el selector de secciones de la ficha, segmentado; fechas de alta y de credenciales
  en DD/MM/YYYY.

Pendiente para cuando se recorran las pantallas del propietario: los formularios de
grupos y de rieles tienen el mismo `clear_on_submit=True`.

__PROD__ · 46 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v557 | **Users, probada acción por acción.** ⚠️ Correos que no lo son («driver 1», "
        "«hotmai.com») se guardaban → validación (motor y pantalla) y «Did you mean…?». ⚠️ El "
        "alta borraba todo al dar error → conserva lo escrito. ⚠️ Contraseñas de 1 carácter → "
        "mínimo 8, repetirla al cambiar. Salud que filtra la tabla, «Contact», «$», selector "
        "segmentado, DD/MM/YYYY. __PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v556 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v556 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v556).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 10/10/2026 (v515-v557).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v557.py "<suite>" "<bateria>" "<produccion>"')
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
h = h.replace(A_HIST, "## Versiones desplegadas (v557 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v557 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v557 = actual)")
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
print("CLAUDE.md: fila v557 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v557")
