# -*- coding: utf-8 -*-
"""Documenta v508 — el `$` que Streamlit leyó como LaTeX en el cobro de obra."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

SECCION = """## EL `$` QUE STREAMLIT LEYÓ COMO LaTeX EN EL COBRO DE OBRA (v508)

La v507 funcionaba, pero la línea que resume la reclamación salía rota en pantalla:

```
work done <code class="language-math">0.00 · already claimed </code>31,500.00 · **this claim 0.00**
```

Streamlit trata lo que hay entre dos `$` de una misma cadena como **LaTeX**. Con dos
importes en la frase, el texto de en medio acabó dentro de un bloque matemático y los
`**` salieron literales.

### ⚠️ El código ya lo había escrito, palabra por palabra
`theme.dinero` existe desde **v309** justo para esto, y su docstring describe el síntoma
exacto —*«los `$` desaparecen y los `**` salen literales»*— y avisa:

> *«cada vez que alguien escriba `f"${x:,.2f}"` a mano el fallo vuelve, y vuelve en las
> pantallas de dinero»*

`claims_ui` traía su propio formateador. Volvió. **Tercera vez en el día que el propio
repositorio avisaba antes** (la nota de v461 sobre las hojas del lote fue la otra).

### Por qué el guardián de v309 no lo cazó
Su red busca `$` **literales** en el fuente. Los de v507 entraban por PARÁMETRO en
tiempo de ejecución (`t("… {h} … {a} …")`), así que la cadena literal no tenía ni un
`$`. Es la **trampa nº30**: un invariante mide una FORMA, y su «0» solo vale para esa
forma.

### ⚠️ Y el primer intento de tapar el agujero fue peor que el agujero
Una red ancha —cualquier `$` pegado a un número en un `*_ui`— denunció **68 sitios que
funcionan**: con una sola cifra en la cadena el problema no existe, lo dice el propio
docstring. Una red que acusa código sano acaba relajándose, y entonces no protege nada
(la lección de v385 al revés).

Se estrechó a la **causa**: ningún `*_ui` puede DEFINIR su propio formateador de dinero
en vez de delegar en `theme.dinero`. Validada en las dos direcciones — ve el caso malo y
no denuncia al que delega.

### ⚠️ Y un rojo que era basura mía
La suite dio `verif_v370` en rojo. No era regresión: los datos de prueba con los que se
verificó la pantalla de v507 dejaron una cotización aceptada colgada de `PRJ-0001`, y ese
guardián comprueba justamente que una obra sin cotización no cambie de modelo de ingreso.
**El guardián tenía razón**; la lección es que los datos de una verificación manual se
limpian ANTES de correr la suite, porque 16 guardianes leen la hoja real.

### Verificación
`verif_v309` ampliado (red nueva + sus dos validaciones), `verif_v507` en **29
comprobaciones** (los chequeos de `anular` y `decidir_variacion` pasaron a EJECUTARSE).
Suite completa: **140 verde · 0 rojo** tras limpiar los datos de prueba.
"""

FILA = ("| v508 | ⚠️ **El `$` que Streamlit leyó como LaTeX.** La línea que resume la reclamación "
        "salía rota: dos importes en una cadena y el texto de en medio acaba dentro de un bloque "
        "matemático, con los `**` literales. `theme.dinero` existe desde v309 para esto y su "
        "docstring **predice el fallo palabra por palabra** («cada vez que alguien escriba "
        "`f\"${x:,.2f}\"` a mano el fallo vuelve»); `claims_ui` traía formateador propio. ⚠️ El "
        "guardián de v309 no lo vio porque busca `$` **literales** y los míos entraban por "
        "parámetro — trampa nº30: un invariante mide una FORMA. ⚠️ Y la primera red nueva fue peor "
        "que el agujero: denunciaba **68 sitios sanos**, así que se estrechó a la causa (ningún "
        "`*_ui` define su propio formateador). Además, un rojo de la suite que era **basura de mis "
        "datos de prueba** en la hoja real: el guardián tenía razón |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v507 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v507 = actual)"
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
h = h.replace(A_HIST, "## Versiones desplegadas (v508 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v508 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v508 = actual)")
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
print("CLAUDE.md: fila v508 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
