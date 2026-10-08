# -*- coding: utf-8 -*-
"""Documenta v544 — la pantalla Home del admin, probada acción por acción en producción."""
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

SECCION = """## EL HOME DEL ADMIN, PROBADO ACCIÓN POR ACCIÓN EN PRODUCCIÓN (v544)

Primera pantalla del recorrido «pantalla por pantalla» que guía el usuario (08/10/2026), con la
cuenta admin de cliente1. Funcionaban: los 9 indicadores del resumen y sus «Go to», las tarjetas
Active/Progress, lista de obras → resumen → «Back»/«See the full project», el enlace a Maps, la
agenda (abre la ficha de la persona), el pin del mapa, el buscador (obra, persona, sin
resultados, Clear), «←», el menú lateral, la lectura de la IA (cuadra con los datos) y «Send it
to me» (la app confirma «Summary sent.»), el fichaje del lateral con su modal y su banda del Pre-Start, y el chat (respuesta
correcta con los datos reales). Lo que no:

1. **Las tarjetas KPI no se leían.** Streamlit 1.64 pinta la etiqueta de un botón EN COLUMNAS en
   una sola línea (`nowrap` + elipsis, los `<p>` en línea, el texto entero a un `title`): se leía
   «AC…», «PR…», «HO…» sin el número, y a 1366 px «ACTIVE 3 all 3 b…». Las 7 tarjetas `cpxkpi_`
   de la app (también las 4 de Day route). → CSS en `theme.py` que devuelve el salto de bloque;
   medido en producción a 846 y 1366 px antes de escribirlo.
2. **El mismo pin del mapa no se podía volver a abrir** (pin → «Back to the list» → mismo pin =
   nada; uno distinto sí). `st_folium` devuelve el ÚLTIMO clic en cada pasada y el filtro de
   repetidos no se reiniciaba nunca. → La clave del mapa lleva generación, que sube al cerrar el
   resumen; y un mapa sin clic olvida el último pin (volver al Home desde otra pantalla).
3. **«Hours · 4 h» abría Horas en «Today»** («No time entries»): la tarjeta suma todo el
   histórico. → Abre en «All» (marca pendiente aplicada antes de crear el radio, regla v111).
4. **La campana decía «No alerts» con 4 urgentes en el resumen** de la misma pantalla. Decisión
   del usuario: que entren. → Al admin le entran retrasos, vencidos y alarmas (una línea por
   motivo: el número de la campana es el «N urgent» del resumen), de `group_digest` (cacheado,
   0 lecturas nuevas). Y cada alerta es un botón que lleva a donde se resuelve (obra, ficha de la
   persona, Inventario, «My credentials» para el campo). `_alertas` sigue dando los textos.
5. **Textos:** «6 paradas» y «alarma(s)» en la pantalla inglesa → «6 stops», «1 alarm»; «13
   pendings» → «13 pending»; «18.0 d» → «18 d»; fechas ISO → dd/mm/aaaa como en Proyectos;
   logins → nombres en «No contact details» y en la cuadrilla del resumen de obra.

**Visto y NO arreglado aquí (anotado):** el mapa de pantallas del prompt del asistente está en
español y desfasado (manda a «Planificación → Usuarios»; va con el glosario); «Refresh» de la
lectura de la IA no genera otra, solo borra; tres primeras acciones se perdieron una vez sin
causa encontrada (el primer «Generate», el primer «Not now» y la primera pregunta del chat; al
repetir, bien); el mensaje de salida del fichaje no sale si se cierra desde la pantalla del
Pre-Start (en el Home sí); «Todos» en español en Proyectos; «Behind → Go to Projects» abre el
filtro «All»; «See the full project» no pone `&p=` en la URL.

Datos de prueba: dos fichajes del admin en PRJ-0015 (0,01 h cada uno, cerrados; 0 abiertos), la
lectura de la IA enviada al correo del admin y dos preguntas al chat.

__PROD__ · 44 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v544 | **El Home del admin, probado acción por acción en producción.** Funcionaban "
        "indicadores, «Go to», lista → resumen, agenda, pin, buscador, «←», menú, IA, fichaje y "
        "chat. Arreglado: las tarjetas KPI en UNA línea («AC…» sin número: Streamlit 1.64 recorta "
        "los botones en columnas → CSS); el MISMO pin no se reabría (`st_folium` repite el último "
        "clic → clave con generación); «Hours» abría en «Today»; la campana muda con 4 urgentes "
        "(ahora entran, y cada alerta lleva a su sitio); «paradas», «alarma(s)», «pendings», "
        "«18.0 d», fechas ISO y logins. __PROD__ · __BATERIA__ · __SUITE__ |\n")

TRAMPAS = """33. ⚠️ **Streamlit 1.64 pinta en UNA línea la etiqueta de un botón que va EN COLUMNAS.**
    El contenedor del markdown lleva `white-space:nowrap` + elipsis y los `<p>` salen `inline`;
    el texto entero se va a un `title`. Un botón de varias líneas (`a\\n\\nb\\n\\nc`) se queda en
    «AC…». Fuera de columnas (los resultados del buscador) no pasa. Lo destapó el recorrido del
    Home (v544): las tarjetas KPI llevaban así desde la subida a 1.64 sin que nada fallara. Es
    el parámetro `wrap` de `st.button`/`st.popover` (1.64): `None` = «decide Streamlit» = en una
    columna, recortar. → Un botón de varias líneas en columnas necesita `wrap=True` o su CSS
    (las tarjetas `cpxkpi_` lo llevan en `theme.py`, medido en producción).

34. ⚠️ **`st_folium` devuelve el ÚLTIMO clic en CADA pasada, no solo en la del clic.** Por eso
    el Home filtra los repetidos — y un filtro que no se reinicia deja ese pin muerto para
    siempre (v544: pin → «Back» → mismo pin = nada). → Para «otra vez el mismo», la clave del
    componente lleva generación y el recuerdo se borra cuando el componente vuelve sin clic.

"""
A_TRAMPA = "**Y la regla de siempre, que volvió a aplicar:** antes de borrar el LECTOR"

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v543 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v543 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"
N_VIEJA = "*Última puesta al día del estado de hecho: 07/10/2026 (v515-v543).*"
N_NUEVA = "*Última puesta al día del estado de hecho: 08/10/2026 (v515-v544).*"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and PROD):
    raise SystemExit('faltan los resultados: doc_v544.py "<suite>" "<bateria>" "<produccion>"')
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
unica(c, A_TRAMPA, "trampas", "CLAUDE.md")
n = io.open(NEG, encoding="utf-8").read()
unica(n, N_VIEJA, "marcador", "NEGOCIO.md")

h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v544 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v544 + fila + cabecera")

c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v544 = actual)")
c = c.replace(A_TRAMPA, TRAMPAS + A_TRAMPA)
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
print("CLAUDE.md: fila v544 + trampas 33-34 · se cayo %s · %d bytes"
      % (vieja.strip(), len(c.encode("utf-8"))))

escribir(NEG, n.replace(N_VIEJA, N_NUEVA))
print("NEGOCIO.md: marcador a v544")
