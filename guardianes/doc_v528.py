# -*- coding: utf-8 -*-
"""Documenta v528 — guardar más rápido: lote de lectura/escritura, heartbeat en segundo
plano y «Saving…»."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""
REAL = sys.argv[3] if len(sys.argv) > 3 else ""

SECCION = """## GUARDAR MÁS RÁPIDO: UNA LECTURA, UNA ESCRITURA Y EL HEARTBEAT EN SEGUNDO PLANO (v528)

Medido en PRODUCCIÓN (v527, sesión de campo, PRJ-0015) con una sonda en el navegador y,
en local, contando cada llamada HTTP a Google: guardar una etapa tardaba **~9,5 s**, 7-8 de
ellos en **~9 llamadas** de ~1 s cada una desde el Cloud (leer StageProgress, escribirla,
leer y escribir Activities, releerla para recalcular, leer y escribir Projects, el rastro
de cambios y el repintado). Y cada 50 s el heartbeat de la sesión única paraba un clic
**~1,9 s** leyendo `Login` entero. Decisión del usuario: las tres mejoras a la vez.

### 1 · Una lectura y una escritura
`StageProgress`, `Activities` y `Projects` viven en el MISMO libro. `hojas.frescas` las lee
FRESCAS en UNA llamada (`values_batch_get`) y `hojas.escribir` escribe todas en OTRA
(`values_batch_update`, RAW). Solo las filas NUEVAS van aparte, con `append_rows`, que es
lo único que hace sitio al final sin pisar a nadie. Crédito nuevo: **1 lectura + 1 append +
1 escritura** (+ el rastro de cambios); deshacer: 1 + 1. El avance de la obra se recalcula
con las actividades que se van a escribir, no releyéndolas.
- ⚠️ Las reglas de fechas reales de `Activities` siguen siendo UNA: salen a
  `projects._lote_avance`, que usan la rejilla vieja y el guardado por etapas.
- ⚠️ Se decide con la lectura FRESCA, no con la caché de la pantalla: con dos personas en
  la misma obra, la caché de 120 s hacía que la etapa se reescribiera con un % MENOR.
- ⚠️ Si la obra no está en `Projects`, no se escribe NADA (hasta v527 quedaban los
  créditos guardados y la obra sin recalcular, porque ese fallo no se miraba).
- El rastro de cambios **se mantiene** (no hubo un sí para quitarlo), ahora con el «antes»
  de la lectura fresca en vez del de la caché.

### 2 · El heartbeat en segundo plano
`auth.heartbeat_en_fondo` lo lanza en un hilo cada 50 s y la página no espera; app.py mira
en CADA pasada el veredicto del último que terminó (`heartbeat_resultado`, un dict, 0
llamadas) y expulsa solo con un `False` explícito. La regla no cambia: un token desplazado
sale; un fallo de Google, nunca. ⚠️ El hilo no toca Streamlit: la hoja se abre antes.

### 3 · «Saving…»
Un spinner alrededor de guardar una etapa, confirmar un parte, «Nothing to credit» y
guardar el parte: unos segundos con la pantalla quieta hacían creer que el clic no entró.

### Los guardianes
`fixture_guardado.py` (nuevo, no es un guardián): un libro de mentira que obliga a pasar
por el camino de producción —sus hojas revientan si se leen una a una— y **sustituye la
auditoría**, para que ninguna prueba escriba en el `AuditTrail` real. `verif_v514`, `v519`,
`v523` y `v525` simulaban `save_field_progress`, que el guardado ya no llama: pasan a
mirar lo que llega ESCRITO a `Activities` (más fuerte: antes bastaba con que se llamara).
`verif_v488` re-anclado en `heartbeat_resultado(`; `romper_v514` y `romper_v525`, cuatro
anclas sobre el código nuevo, con la razón al lado. `verif_v528`: el oráculo de
`hojas.frescas` son las propias funciones de gspread que usa `get_all_records`, y la
pantalla se EJECUTA con AppTest (marcar, guardar, repintar).

⚠️ La suite entera cazó dos fallos MÍOS en `hojas.frescas`, los dos de patrones ya vistos:
un mensaje de error en español que podía llegar a la pantalla dentro de «Error saving: …»
(`verif_v448`/`v449`) y `t` —la función de traducción— usada como variable de bucle
(`verif_v498`, el patrón de v439/v503). Arreglados, y re-corridas la batería y la suite.

Re-corridas sobre el código nuevo las baterías del código tocado: romper_v514 15/15,
v516 20/20, v519 13/13, v523 30/30, v524 19/19, v525 16/16.

__REAL__ · __BATERIA__ · __SUITE__
"""

FILA = ("| v528 | **Guardar más rápido.** Medido en producción: guardar una etapa tardaba "
        "~9,5 s en ~9 llamadas a Google, y el heartbeat paraba un clic ~1,9 s cada 50 s. "
        "Ahora `StageProgress`, `Activities` y `Projects` se leen FRESCAS en UNA llamada y se "
        "escriben en OTRA (las filas nuevas, con `append`): **1+1+1** en vez de ~9. ⚠️ Se "
        "decide con la lectura fresca, no con la caché (dos personas en la misma obra bajaban "
        "el %); si la obra no está, no se escribe nada; las reglas de fechas siguen siendo UNA "
        "(`_lote_avance`) y el rastro de cambios se mantiene. Heartbeat en un hilo: la página "
        "no espera y un fallo de Google no expulsa. «Saving…» en cada guardado del campo. "
        "`fixture_guardado` sustituye la auditoría (ninguna prueba escribe en el AuditTrail "
        "real). ⚠️ La suite cazó dos fallos míos (un error en español, `t` como variable). "
        "__REAL__ · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v527 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v527 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA and REAL):
    raise SystemExit('faltan los resultados: doc_v528.py "<suite>" "<bateria>" "<real>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE), ("__REAL__", REAL)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v528 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v528 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v528 = actual)")
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
print("CLAUDE.md: fila v528 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
