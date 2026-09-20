# -*- coding: utf-8 -*-
"""Documenta v502 — el RESPONSABLE de cada actividad.

⚠️ CAMBIA respecto a `doc_v501.py`: el 20/09/2026 se partió `CLAUDE.md` (1,07 MB, ~300k
tokens, que ya no entraba en la ventana y mataba la sesión). Desde entonces:
  · la SECCION larga va a `HISTORIAL.md`;
  · en `CLAUDE.md` solo entra la FILA, y se borra la más vieja para que la lista no crezca;
  · el ancla `## Versiones desplegadas (vNNN = actual)` vive AHORA en HISTORIAL.md, y
    `CLAUDE.md` tiene `## Últimas versiones desplegadas (vNNN = actual)`.
Copiar el patrón de v501 tal cual escribiría en el sitio equivocado.
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SUITE = "**135 verde · 0 rojo · 0 roto** (923 s)"   # medido, no recordado
COMPROB = "25"                     # comprobaciones de verif_v502.py (medido, no recordado)
EJERCICIO = """La columna se creó sola en la hoja de `cliente1` (**10 → 11**, «Owner» al
final, sin descuadrar las cinco actividades que ya estaban). Puesto `admin1` como
responsable de la actividad 1, se releyó **de la hoja** y la app lo devolvió igual.
⚠️ Después, un guardado **PARCIAL** —solo el nombre, sin la clave `Owner`— cambió el
nombre y **dejó el responsable intacto**: ésa es la prueba que ningún test con datos
inventados puede dar, y es justo el patrón con el que guarda el campo (v162). Producción
devuelta a su estado: las cinco actividades idénticas a la foto inicial."""

SECCION = """## EL RESPONSABLE de cada actividad: que el retraso tenga dueño (v502)

Cuarto de los huecos que la auditoría de gestión de instalación dejó medidos. v499 puso
las dependencias, v500 el pronóstico desde la cadena y v501 la línea base: a estas alturas
la app sabe **qué** va tarde, **cuánto** y **por qué**. Lo que no sabía es **de quién es**.

Y sin eso no se puede dar el peldaño siguiente de la escalera —recomendar—: para proponer
a quién mover, primero hay que saber quién responde de qué.

### Cómo funciona
Una columna **Responsable** en la tabla editable de actividades (✏️ Datos), que se elige de
la gente asignada a la obra. En 📊 Estado, las actividades que van tarde —la **parada** (no
arrancó y ya tocaba) y la **arrastrada** (se pasó de su ventana)— salen con el nombre al
lado. En el resto no: ponerlo en todas las filas es ruido, y lo accionable es justo eso.

### ⚠️ Las tres cosas que fallarían en silencio
1. **Se guarda el LOGIN, se muestra el NOMBRE.** El login es la identidad y el nombre se
   repite (v306/v413/v459): en el grupo real hay dos `lksdfkldsf` y dos `fijiofgjei`.
   `auth.etiqueta_usuarios` pone el login detrás solo cuando hace falta, y el guardián
   comprueba que las etiquetas son ÚNICAS — si dos coincidieran, el mapa inverso guardaría
   el responsable equivocado sin que nadie lo viera.
2. **Un guardado PARCIAL no puede borrar responsables.** `Owner` entra en el bucle
   guardado (`if field in e`), así que una fila que no viaja en el `edits` no se toca. Es
   exactamente el fallo que v499 tuvo con las predecesoras —el plan entero reescrito sin
   ningún error— y el campo guarda justo con ese patrón (v162).
3. **Un responsable cuya persona ya no está asignada NO desaparece de la lista.** Las
   opciones son la gente asignada **más** los dueños ya guardados. Sin eso: sacas a alguien
   de la obra, su fila se pinta vacía, y el primer guardado de la tabla le borra el
   responsable a esa actividad sin que nadie lo haya pedido.

### Dónde vive
Columna `Owner` en `Actividades` (⚠️ **al final**, v363, y opcional: una actividad sin
responsable se comporta exactamente como hasta v501). Viaja a la pantalla como **lista
paralela** `owners` en `project_schedule`, igual que `avances` y `windows`: el motor de
plan (`schedule.py`/`plan.py`) es puro y no tiene por qué saber de personas — quién
responde de una actividad no mueve ni una fecha.

### Verificación
`verif_v502.py`, **{COMPROB} comprobaciones**, ejecutando donde se puede (importar no
ejecuta, v378; compilar no verifica nada, v439). Batería: **13 roturas, 13 cazadas +
CONTROL verde**, con el verde de base confirmado antes (v459) y el motivo de cada una a la
vista (v492). Suite completa: {SUITE}.

⚠️ **Dos fallos del guardián, cazados por la propia batería:**
- el chequeo de «el campo no edita responsables» miraba `render_field_projects`, que no
  contiene ninguna tabla: la editable del campo está en `_field_activities`. Era un **OK en
  vacío** (trampa nº1) — no había nada ahí que pudiera traer la columna;
- el de «pinta el dueño en las dos» contaba subcadenas y salía **3 donde esperaba 2**,
  porque `ast.unparse` incluye el `def _dueno(x):`. El chequeo fallaba por su propia
  construcción (el error de v500). Ahora cuenta las LLAMADAS por AST.
Y una rotura no fue cazada sino que hizo **reventar** al guardián (`_ps["owners"]` →
KeyError al quitar la clave): un guardián que muere no denuncia, y la batería lo contaba
como «no cuenta». Se lee con `.get(...) or []` para que DENUNCIE.

### Ejercitado contra la HOJA REAL (método v344)
{EJERCICIO}
"""

FILA = ("| v502 | **El responsable de cada actividad: que el retraso tenga dueño.** Cerrado el "
        "cuarto hueco de gestión de instalación: con v499-v501 la app ya sabía qué va tarde, cuánto "
        "y por qué, pero no **de quién es** — y sin eso no puede recomendar a quién mover. Columna "
        "Responsable en la tabla de actividades (se elige de la gente asignada a la obra) y el "
        "nombre al lado de lo que va tarde: la parada y la arrastrada, no todas las filas. ⚠️ Se "
        "guarda el **LOGIN** y se muestra el nombre (el nombre se repite, v306/v413), y el guardián "
        "exige que las etiquetas sean únicas o el mapa inverso guardaría a otro. ⚠️ Un guardado "
        "PARCIAL **no borra** responsables (el fallo de v499 con las predecesoras, y el campo guarda "
        "así, v162), y ⚠️ un dueño cuya persona ya no está asignada **sigue en la lista**: si no, su "
        "fila se pintaría vacía y el primer guardado lo borraría sin que nadie lo pidiera. "
        "{COMPROB} comprobaciones · **13/13 roturas + control** ⚠️ (la batería cazó DOS fallos "
        "míos en el propio guardián: uno que pasaba en vacío mirando la función equivocada, y otro "
        "que fallaba por su propia construcción contando el `def` como una llamada) |\n")


# ⚠️ `.replace` y no `.format`: los textos llevan tablas y llaves sueltas, y un `format`
# reventaria o se comeria caracteres. Ademas se COMPRUEBA que no quede ningun marcador
# sin sustituir — escribir «{SUITE}» en el historial seria peor que no documentar.
for _k, _v in (("{COMPROB}", COMPROB), ("{SUITE}", SUITE), ("{EJERCICIO}", EJERCICIO)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)
for _t in (SECCION, FILA):
    if "{" in _t and "}" in _t.split("{", 1)[1][:40]:
        raise SystemExit("queda un marcador sin sustituir: %s"
                         % _t[_t.index("{"):_t.index("{") + 40])
if "PENDIENTE" in SECCION or "PENDIENTE" in FILA:
    raise SystemExit("hay un valor PENDIENTE sin rellenar: no se documenta a medias")


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v501 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v501 = actual)"

# ── HISTORIAL.md: la seccion LARGA + la fila en el indice completo ──────────
h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
# ⚠️ `\n---\n\n` a secas aparece DOS veces (la cabecera y la juntura con el indice), asi
# que la seccion nueva podria acabar al final del fichero. El ancla lleva la linea de
# antes, que si es unica.
TRAS_CAB = "o el índice del final.\n\n---\n\n"
unica(h, TRAS_CAB, "separador de cabecera", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v502 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v502 + fila en el indice + cabecera")

# ── CLAUDE.md: SOLO la fila, y se cae la mas vieja (la lista no crece) ──────
c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v502 = actual)")
c = c.replace(CAB, CAB + FILA)

lineas = c.splitlines(True)
idx = [i for i, l in enumerate(lineas) if l.startswith("| v")]
if len(idx) != 16:
    raise SystemExit("esperaba 16 filas tras insertar (15 + la nueva): %d" % len(idx))
vieja = lineas[idx[-1]][:10]
del lineas[idx[-1]]                       # ⚠️ se borra la MAS VIEJA: la lista no crece
c = "".join(lineas)

# la nota de cierre cuenta una version mas en el historial
import re                                                          # noqa: E402
m = re.search(r"_\(y (\d+) versiones anteriores", c)
if not m:
    raise SystemExit("no encuentro la nota de cierre de CLAUDE.md")
c = c.replace(m.group(0), "_(y %d versiones anteriores" % (int(m.group(1)) + 1))
escribir(CLAUDE, c)
print("CLAUDE.md: fila v502 + cabecera · se cayo %s · nota %s -> %d"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1))
print("\nCLAUDE.md: %d bytes" % len(c.encode("utf-8")))
