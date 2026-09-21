# -*- coding: utf-8 -*-
"""Documenta v511 — la cadena del dinero de punta a punta, y lo que destapó."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## LA CADENA DEL DINERO, DE PUNTA A PUNTA (v511)

v506, v507-v508, v509 y v510 se verificaron **cada una por su lado**, y las cuatro en
verde. Lo que nunca se había hecho es recorrer la cadena entera con datos reales:

    catálogo → cotización → aceptar → OBRA → avance → reclamación → PDF
                                        ├→ variación → mueve el contrato
                                        ├→ 100% → liberación de retención → PDF
                                        ├→ cotizar leyendo el plano (v509)
                                        └→ expediente de entrega (v506)

No se podía: **el catálogo del cliente de prueba estaba vacío**, así que no había
contrato contra el que reclamar, ni precios que proponer, ni expediente que cruzar. Cada
eslabón verde no dice nada del eslabón siguiente.

`ejercitar_e2e_dinero.py` monta la cadena de verdad y la recorre: **44 comprobaciones**.
Contrato 29.725 → avance real 52,6% → reclamación neta **14.853,58** → variación aprobada
llevando el contrato a **37.125** → obra al 100% → retención **1.856,25** → liberación
parcial de **928,12** → los dos PDF generados desde filas de Sheets. Y el expediente
denunciando, sin que nadie se lo pidiera: *«every activity is closed, but there is no
plumb verification on record»*.

⚠️ **Verificado también EN PRODUCCIÓN por el usuario**, que es lo único que cubre el
hueco de v502: la sección se pinta con sus cuatro indicadores, los tres documentos, el
botón de descarga y el bloque de retención. Ninguna red local ve eso.

### ⚠️ El fallo que encontró la cadena y que ningún test podía encontrar
Al agotar la cuota —el techo de **60 lecturas/min** de la cuenta de servicio—, emitir una
reclamación contestaba:

> «Google Sheets is not configured.»

**Es falso.** Los secrets estaban perfectos: era un 429 pasajero. Ese mensaje manda a
revisar una configuración que está bien, por algo que se va solo en un minuto; y en una
reclamación es peor todavía, porque el usuario puede concluir que la obra no tiene
contrato. Apareció **dos veces, en dos módulos distintos** (`claims` y, una corrida
después, `catalogo`), que es lo que lo delató como patrón y no como descuido.

La causa es estructural: **`_ws()` devuelve `None` por dos motivos que no son el mismo**
—faltan los secrets, o la hoja no se pudo abrir ahora— y el llamante no puede
distinguirlos, así que siempre culpa a la configuración. Hay **41 sitios en 20 módulos**
con ese literal.

Arreglado en `timeclock.motivo_sin_hoja()`, **una sola definición** (regla v361):
`timeclock` es quien sabe si hay secrets, así que es quien puede decir por qué no hay
hoja. `claims`, `catalogo` y `quotes` delegan ahí. ⚠️ **`projects` ya lo hacía bien**
—dice «Could not open sheet X: …»— y no se tocó: es el modelo, no el problema.

⚠️ Los **16 módulos restantes** siguen con el mensaje ambiguo. Se deja dicho en vez de
arreglado a medias: es una versión propia, y decidirlo es del usuario.

### ⚠️ Tres errores MÍOS que la cadena sacó a la luz
1. **Acusé a código sano.** La comprobación del presupuesto preguntaba por `Presupuesto`
   y la migración a inglés lo renombró a **`Budget`**: daba 0.0 y parecía un fallo del
   producto. Mirar el código acusado antes de «arreglarlo» (v385) evitó parchear algo que
   funcionaba. Ahora la clave se **deriva de la cabecera real**, así que no puede
   desfasarse otra vez.
2. **Seguí con la precondición rota.** Una corrida creó 3 de 5 artículos (429) y continuó,
   escupiendo cuatro rojos más —«hay 5 líneas», «propone las 3 reglas», «la puerta va NS
   veces»— que no eran fallos distintos: eran el MISMO repetido aguas abajo. Ahora el
   guion **aborta**: el ruido tapa la señal.
3. **La limpieza se rendía ante un 429**, dejando basura en la hoja de un cliente — y la
   corrida siguiente la confundió con duplicados propios (ocho artículos donde debía
   haber cinco). Ahora **reintenta**, y si aun así no puede, el guion para antes de crear
   nada encima. El borrado es lo último que puede fallar en silencio.

### ⚠️ Y la lección de método
**La cuota es un actor del sistema, no una molestia del entorno.** Cada 429 se disfrazó
de otra cosa: una obra «al 0%», una reclamación «sin configurar», un catálogo con ocho
artículos. Ninguno era un fallo del producto — pero **uno destapó uno real**. Si no se
aprieta hasta romper la cuota, ese mensaje seguiría ahí esperando al primer cliente con
varios usuarios a la vez. Es la razón de ejercitar contra lo real y no contra un mock.

### Verificación
`verif_v510.py` pasa de **56 a 63 comprobaciones** (las 7 nuevas sobre el mensaje, por
AST: se mira el cuerpo de `if w is None:`, no un grep — el literal aparece
legítimamente donde SÍ se comprobó que faltan los secrets). Batería: **14 roturas, 14
cazadas + CONTROL**, con dos nuevas. ⚠️ Una de ellas comprueba que el arreglo **hace
algo**: dejar los dos mensajes idénticos tenía que ponerse rojo, y se pone.

Hoja devuelta a la línea base y comprobado **releyendo**: catálogo 0, cotizaciones 0,
reclamaciones 0, y las 2 obras y 17 actividades del usuario intactas.
"""

FILA = ("| v511 | **La cadena del dinero, de punta a punta.** v506, v507-v508, v509 y v510 estaban "
        "verdes cada una por su lado, pero la cadena entera nunca se había recorrido con datos "
        "reales: el catálogo del cliente de prueba estaba vacío, así que no había contrato contra el "
        "que reclamar. 44 comprobaciones desde el catálogo hasta el PDF, **y verificada en "
        "PRODUCCIÓN por el usuario** — el hueco de v502, que ninguna red local ve. ⚠️ **Destapó un "
        "fallo que ningún test podía encontrar**: al agotar la cuota (60 lecturas/min), emitir una "
        "reclamación decía «Google Sheets is not configured» —falso, y en una reclamación el usuario "
        "puede concluir que la obra no tiene contrato—. Apareció en DOS módulos, que es lo que lo "
        "delató como patrón: `_ws()` devuelve None por dos motivos distintos y el llamante siempre "
        "culpa a la configuración (**41 sitios en 20 módulos**). Arreglado en `timeclock."
        "motivo_sin_hoja()`, UNA definición (v361); `projects` ya lo hacía bien y no se tocó. ⚠️ Y "
        "tres errores MÍOS: acusar a código sano por un nombre de columna que la migración a inglés "
        "renombró, seguir con la precondición rota encadenando rojos que eran el mismo fallo, y una "
        "limpieza que se rendía ante un 429 dejando basura. 63 comprobaciones · **14/14 + control** |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v510 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v510 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v511 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v511 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v511 = actual)")
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
print("CLAUDE.md: fila v511 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
