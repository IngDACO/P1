# -*- coding: utf-8 -*-
"""Documenta v509 — cotizar leyendo el plano."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## COTIZAR LEYENDO EL PLANO (v509)

Tercera oportunidad del estudio de mercado del 20/09/2026. Simpro y Sage tienen
*estimating*; lo que nadie puede hacer es **presupuestar una instalación a partir del PDF
del plano**, porque hay que extraerlo primero — y eso ya se hace para el survey desde
v137.

### Cómo funciona
En la pantalla de cotización nueva se sube el plano. Del PDF salen **NS** (paradas),
**modelo** y **código de riel**; un ítem del catálogo dice de cuál depende su cantidad:

| Regla | Cantidad | Para qué |
|---|---|---|
| `fixed` | 1 | movilización, puesta en marcha |
| `per_stop` | NS | puertas de rellano, botoneras |
| `per_stop_minus_1` | NS − 1 | lo que va ENTRE plantas |
| `manual` | — | no se propone: su cantidad no sale del plano |

Las líneas propuestas **se siembran en el editor**, editables antes de guardar: es un
punto de partida, no un precio.

### ⚠️ La decisión que más importa: qué pasa si el plano no lo dice
**La línea entra con cantidad CERO y marcada en rojo**, nunca omitida ni con un 1
inventado. Decisión del usuario, y por una razón concreta:

- **Omitirla** haría la cotización **más barata** sin que nadie lo note. Sub-cotizar en
  silencio se descubre al facturar, cuando ya se firmó.
- **Inventar un 1** es peor todavía: esconde el error dentro de un número que parece
  calculado.

Con cantidad 0 y el motivo al lado, alguien tiene que decidirla. Es el mismo criterio que
`orders.atrasadas` («sin fecha no se puede decir que llega tarde») y que el expediente de
v506 («un ítem de tercero no pasa por cálculo»).

⚠️ Y la regla por defecto es **`manual`**: un ítem sin regla NO se propone. Lo contrario
—suponer `fixed`— metería una unidad de todo en cada cotización.

### Dónde vive
`core/quote_from_plan.py` es **módulo HOJA**: `cantidad_de` no importa nada y devuelve
`(cantidad, motivo)`, así que se puede ejercitar de verdad. ⚠️ **No calcula ni un
importe**: el precio lo pone `quotes.linea_de`, que es quien sabe de costos y márgenes
(regla v361: UNA definición). Columna `QtyRule` al final del catálogo (v363), opcional.
Las marcas `_regla`/`_falta` viajan a la pantalla pero **no a la cotización guardada**:
una línea guardada es un precio pactado, no una nota de cómo se propuso.

La pantalla **AÑADE, no reemplaza** (decisión del usuario): pulsar dos veces duplica y
eso se ve; perder lo escrito a mano, no.

### ⚠️ Red nueva: nombres libres en TODO `core`
La familia `NameError` / `UnboundLocalError` mordió **dos veces el mismo día**: el
`_etq_us` de v502 (tumbó la pantalla de detalle en producción) y, en esta misma versión,
un `theme.dinero(...)` en un módulo que importa `theme as T`. Las dos son invisibles para
`compileall` y para el import: Python solo se queja al EJECUTAR esa línea, y una línea
dentro de un expander puede tardar semanas en ejecutarse. `verif_v311` ya hacía el
barrido, pero sobre UNA función.

`check_nombres_libres.py` lo hace sobre los 100 módulos. Costó **tres intentos**, y los
dos primeros denunciaban código sano:
1. **9 módulos** — no recorría comprensiones ANIDADAS (`[{k: v for k, v in x.items()}
   for x in xs]`: los objetivos los liga la interior).
2. **1 módulo** — `ast.walk` aplana la anidación, así que `survey_ui._highlight`, que
   cierra sobre los ARGUMENTOS de `make_highlighter`, se comprobaba contra el ámbito de
   su abuela.
3. Verde, y validada contra **once** casos: caza el inexistente y no denuncia a lambdas,
   morsa, comprensiones, `with … as`, `except … as`, cierres ni funciones de tercer nivel.

Los dos falsos positivos se encontraron **mirando el código acusado** (v385). «Arreglar»
`_highlight` habría roto código correcto.

### Verificación
`verif_v509.py`, **36 comprobaciones**. Batería: **12 roturas, 12 cazadas + CONTROL**
⚠️ (la más grave —omitir la línea sin dato— **reventaba** al guardián en vez de ser
denunciada: `_por(...)["campo"]` muere con TypeError justo cuando la rotura hace
desaparecer la línea. **Quinta vez en el día** con ese patrón; ahora hay un accesor que
avisa en vez de morir). Suite completa: **142 verde · 0 rojo · 0 roto**.

**Ejercitado contra la HOJA REAL** (método v344): la columna se creó sola (**14 → 15**,
al final), tres ítems guardados con regla se leyeron de vuelta CON ella, la propuesta
salió de los precios reales (puerta ×8 = 7.200) y ⚠️ con un plano sin paradas salieron
**las mismas dos líneas**, la puerta a **0 con motivo** y la movilización intacta.
Catálogo devuelto.

⚠️ **Lo que el ejercicio NO prueba**: la extracción del PDF. Eso ya lo cubren el survey y
sus guardianes desde v137, y no hay un plano real en el cliente de prueba; se le pasa un
plano ya extraído. Decirlo importa: un ejercicio que aparenta probar más de lo que prueba
es peor que uno corto (nº30).

⚠️ **Para que sirva hay que poner reglas**: ningún ítem del catálogo las trae, así que
hasta entonces la propuesta dirá «ningún ítem toma su cantidad del plano».
"""

FILA = ("| v509 | **Cotizar leyendo el plano.** Tercera oportunidad del estudio: nadie puede "
        "presupuestar una instalación desde el PDF porque hay que extraerlo primero, y eso ya se "
        "hace desde v137. Del plano salen NS, modelo y riel; un ítem del catálogo dice si su "
        "cantidad es fija, por parada o por parada−1. ⚠️ **Si el plano no lo dice, la línea entra "
        "con cantidad CERO y marcada** — nunca omitida (abarataría en silencio y se descubre al "
        "facturar) ni con un 1 inventado (esconde el error en un número que parece calculado); y la "
        "regla por defecto es **manual**, o sea NO proponer. El módulo **no calcula ningún "
        "importe**: se los pide a `quotes.linea_de` (v361). La pantalla AÑADE, no reemplaza. ⚠️ Red "
        "nueva `check_nombres_libres` sobre los 100 módulos —la familia `NameError` mordió DOS "
        "veces hoy—, que costó **tres intentos**: los dos primeros denunciaban código sano "
        "(comprensiones anidadas, y `ast.walk` aplanando la anidación). 36 comprobaciones · "
        "**12/12 roturas + control** · suite 142 verde |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v508 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v508 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v509 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v509 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v509 = actual)")
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
print("CLAUDE.md: fila v509 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
