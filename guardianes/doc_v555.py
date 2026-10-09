# -*- coding: utf-8 -*-
"""Documenta v555 — Absences (bandeja del admin), probada acción por acción + trampa 37."""
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

SECCION = """## ABSENCES (BANDEJA DEL ADMIN), PROBADA ACCIÓN POR ACCIÓN (v555)

Recorrido en producción (Planning → Absences, decisión del usuario: «Dale»), con tres
solicitudes de prueba (AUS-0001..0003). Funcionaban el saldo, el aviso de choque con su
obra, «Who could cover it» (con el control de certificados) y aprobar (hoja + tablero:
ROS-0013 con LEAVE). Arreglado:

- ⚠️ **La tarjeta FANTASMA.** Tras «Reject», la tarjeta seguía en pantalla —atenuada, con
  su nota y sus botones— con Pending ya en 0 y el histórico diciendo «rejected». Streamlit
  1.64 deja en el navegador un bloque CON CLAVE (contenedor o desplegable) que una pasada
  ya no pinta, cuando la acción que lo quita es LENTA (hoja + aviso, 3-5 s), corre DENTRO
  de la tarjeta y la que ocupa su sitio tiene otra forma. Reproducido en una mini-app
  1.64: el servidor tenía solo C y en pantalla había cuatro «A». El envoltorio con clave
  por contenido NO lo cura; quitar la clave sí, pero las claves hacen falta (trampa 35).
  → **ACCIÓN DIFERIDA**: el botón solo apunta (`_aus_accion`) y relanza; la acción se
  ejecuta al principio (`_accion_pendiente`), ANTES de pintar la lista. Probado en la
  mini-app con contenedores y desplegables con clave: ningún fantasma. Trampa 37.
- ⚠️ La baja por enfermedad nace aprobada y «el admin la confirma después», pero la
  bandeja solo enseñaba lo pendiente → sección «Sick leave recorded» (14 días y próximas).
- ⚠️ El admin no podía deshacer nada aprobado (el error decía «cancélala» y el botón solo
  existía en la pantalla del campo) → «Cancel» con confirmación en lo aprobado: libera el
  tablero y avisa a la persona.
- El aviso a la persona decía «Absence aprobada» / «has been rechazada» → inglés.
- Lo pendiente, de lo más próximo a lo más lejano; fechas dd/mm/aaaa (con
  `projects_ui._fmt_fecha`) y un solo día sin «→»; las 3 tarjetas activas (abren su
  lista); el saldo dice cómo queda TRAS la solicitud, y «se pasa del saldo» mira eso
  (antes miraba el de antes: una de 5 días con 3 libres no avisaba).
- Aislamiento: la acción busca la ausencia SOLO en el grupo (`_de_grupo`; `AU.get` es
  global — lo exigió `verif_v430`).
- La cifra ámbar de las tarjetas (aquí y en el Panel de v551) en `AMBAR_TXT` (v328).

Datos de prueba: AUS-0001 y AUS-0003 canceladas, AUS-0002 rechazada; ROS-0013 vacía.

__PROD__ · 42 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v555 | **Absences, probada acción por acción.** ⚠️ Tras «Reject» la tarjeta quedaba "
        "FANTASMA (Streamlit 1.64 + bloque con clave + acción lenta dentro) → acción DIFERIDA, "
        "trampa 37. ⚠️ La baja por enfermedad no llegaba al admin y nada aprobado se podía "
        "deshacer → sección de bajas y «Cancel» con confirmación. Aviso en inglés, urgente "
        "primero, dd/mm/aaaa, tarjetas activas, saldo tras la solicitud. "
        "__PROD__ · __BATERIA__ · __SUITE__ |" + chr(10))

T36_FIN = ("    `|`, espacios) y larga; y antes de «arreglar» un rojo intermitente, medir su tasa.\n")
T37 = ("\n37. ⚠️ **Un bloque CON CLAVE puede quedarse FANTASMA en el navegador.** Streamlit 1.64 deja\n"
       "    en pantalla un contenedor o desplegable con `key=` que la pasada ya no pinta cuando la\n"
       "    acción que lo quita es LENTA (escribir en la hoja + avisar) y corre DENTRO de él con un\n"
       "    `st.rerun()`, y lo que ocupa su sitio tiene otra forma (v555: «Reject» en Absences).\n"
       "    AppTest NO lo ve (lee el servidor). → ACCIÓN DIFERIDA: el botón solo apunta y relanza;\n"
       "    la acción se ejecuta arriba, antes de pintar la lista. Quitar la clave también lo\n"
       "    cura, pero la trampa 35 la exige. Revisarlo en cada lista de tarjetas con acciones.\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v554 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v554 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v554).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 09/10/2026 (v515-v555).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v555.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, T36_FIN, "trampa 36", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v555 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v555 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v555 = actual)")
c = c.replace(CAB, CAB + FILA)
c = c.replace(T36_FIN, T36_FIN + T37)
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
print("CLAUDE.md: fila v555 + trampa 37 · se cayo %s · %d bytes" % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v555")
