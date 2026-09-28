# -*- coding: utf-8 -*-
"""Documenta v520 — la biblioteca técnica se llena con la carpeta de obra del usuario."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## LA BIBLIOTECA SE LLENA: 750 FOTOS DE OBRA Y DOS SECCIONES NUEVAS (v520)

El usuario pasó su carpeta `D:\\CopeX\\Library` —750 fotos ordenadas en nueve carpetas
(CW & Compo, Cabin, Controller, Docs, Doors, False Cabin, Pit, Plumbing, Top & Elec)— para
la biblioteca que ven TODOS los clientes, con una regla: «ponlas en el lugar que
corresponde; si no sabes dónde, pregunta».

### Lo que decidió el usuario

| Pregunta | Decisión |
|---|---|
| Fotos de pantalla de manuales Schindler | **Entran** |
| 87 fotos de equipo de montaje (false car, tirak, Blocstop, eslingas, grúa) que no caben en ninguna sección | **Sección nueva `Installation equipment`** |
| 38 fotos de plomada (plantilla, hilos, cálculos TKSW/BKS) | **Sección nueva `Setting out`** |
| 10 fotos con caras de trabajadores, 4 planos de una obra concreta, 3 formularios rellenados | **Entra todo** (se le avisó de que las ve cualquier cliente) |
| Marca de las fotos de obra | **Todo Schindler salvo lo ajeno** (cuadro chino, false car y herramientas sin marca; puerta de rellano Sematic) |

### Cómo se clasificó
Mirando las 750, no por el nombre de la carpeta: 67 hojas de contacto numeradas (12 por
hoja) y ampliaciones de las dudosas. La carpeta del usuario era una PISTA, no la
respuesta: *Cabin* traía operadores de puerta, paracaídas, cable viajero y ~180 páginas de
manual; *Docs* traía páginas de panelería de cabina y la nota de las medidas del belting.
Cada foto lleva título en inglés (se guarda y se busca) y, si estaba ANOTADA a mano, las
notas transcritas: «3 shims behind the header of the cabin each side», «bolts coming with
the lift are too long, DO NOT use», el cálculo de la plantilla (1490 + 40 = 1530…). Eso es
lo que hace que el buscador las encuentre.

Antes de subir, `preparar_biblioteca.py` hizo COPIAS a 1600 px **sin metadatos** —70 fotos
llevaban el GPS de la obra— y marcó las casi repetidas (dHash) sin borrar nada.

### ⚠️ Las secciones solo se AÑADEN
La sección vive como TEXTO en cada fila de `Library`. Renombrar una deja sus piezas fuera
de todo filtro **sin dar ningún error**, así que las catorce de siempre están escritas A
MANO en `verif_v520` (derivarlas de `SECCIONES` haría que el guardián aceptara cualquier
cambio). El orden sí es libre: solo decide cómo sale el desplegable.

### La carga en lote (`guardianes/sueltos/importar_biblioteca.py`)
⚠️ **No llama a `add_item` 750 veces**: cada alta lee la hoja entera para el ID (fresco, a
propósito), y 750 lecturas contra 60/min son 13 minutos de 429. Lee una vez, asigna IDs en
memoria saltando los referenciados (v427) y escribe con `append_rows` en tandas de 100.
⚠️ Pero valida **lo mismo que el alta** y comprueba la **cabecera REAL** antes de escribir
filas posicionales (v363). ⚠️ **Idempotente**: la llave es `FileName` = «L####.jpg», y lo
ya subido a Drive queda en `_subida_estado.json` — si se corta entre Drive y la hoja, la
siguiente pasada no duplica archivos. ⚠️ Primero el archivo, después la ficha (v343).

⚠️ **El `secrets.toml` LOCAL no trae `[gdrive]`** —el del Cloud sí; trampa nº11 otra vez—
y la primera prueba murió ahí. Se le pasa `--gdrive <toml>` con la MISMA credencial OAuth
de la app, leída en memoria y sin copiarla a ningún sitio. Tiene que ser la misma: con el
alcance `drive.file`, un archivo subido con otro cliente sería **invisible para la app**.
La corrida fallida alcanzó a dar de alta la marca Schindler en el catálogo antes de caer
en Drive — era un alta que había que hacer igual, y el orden (catálogo antes que archivos)
no deja fichas a medias.

### Verificado
Contra la hoja real, por un SEGUNDO camino (gspread de solo lectura, no las funciones de la app): **750 filas, 750 IDs y 750 nombres unicos, 0 que no casen con la clasificacion**; 25 archivos al azar bajados de Drive **identicos byte a byte** (y la sonda distingue dos distintos: validada, trampa nº12), **0 con EXIF**. Volver a correr la carga: «por subir: 0». Drive: 747 subidas en 42 min sin un reintento.
26 comprobaciones · **12/12 roturas + control** · suite 149 verde + 2 rojos que NO eran de esta version: `check_anclas_roturas` (el control de mi bateria anclaba en «TIPOS = [», 9 caracteres, por debajo del minimo de 10 del chequeo — el mismo falso positivo que arrastra v472; ancla alargada y la deuda sigue en 15 exactos) y `verif_v455` (caducado por los DATOS: con 3 obras exigia 3 modelos de ganancia, y `cliente1` tiene hoy 3, las tres a costo, porque PRJ-0015 se quedo a proposito; ahora lo dice en vez de fallar). Re-corridos en verde → **151**.
"""

FILA = ("| v520 | **La biblioteca se llena: las 750 fotos de obra del usuario.** Clasificadas MIRÁNDOLAS "
        "(67 hojas de contacto), no por la carpeta: *Cabin* traía puertas, paracaídas y ~180 páginas de "
        "manual. Títulos en inglés y **las anotaciones a mano transcritas** en las notas, que es lo que "
        "encuentra el buscador. Decisiones del usuario: **dos secciones nuevas** (`Setting out`, "
        "`Installation equipment`), **entra todo** (avisado de caras y planos) y **Schindler salvo lo "
        "ajeno**. ⚠️ Las secciones **solo se añaden**: viven como texto en cada fila, renombrar una la "
        "saca de todo filtro sin error — las 14 de siempre, escritas a mano en el guardián. ⚠️ Carga en "
        "lote que valida como `add_item`, comprueba la cabecera real y es idempotente; ⚠️ el secrets "
        "LOCAL no trae `[gdrive]` (nº11) y tiene que ser la misma credencial: con `drive.file` otro "
        "cliente dejaría los archivos invisibles para la app. Copias **sin EXIF** (70 con GPS). "
        "Hoja real por segundo camino: **750/750, 0 discrepancias**, 25/25 archivos identicos en Drive, 0 EXIF. 26 comprobaciones · **12/12 + control** · suite 151 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v519 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v519 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


for _m in ("__REAL__", "__SUITE__", "__FILA__"):
    if _m in SECCION or _m in FILA:
        raise SystemExit("queda la marca %s sin rellenar" % _m)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v520 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v520 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v520 = actual)")
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
print("CLAUDE.md: fila v520 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
