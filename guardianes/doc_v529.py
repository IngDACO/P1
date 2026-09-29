# -*- coding: utf-8 -*-
"""Documenta v529 — la caja del parte se vacía de verdad (en el navegador) al guardar."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"
SUITE = sys.argv[1] if len(sys.argv) > 1 else ""
BATERIA = sys.argv[2] if len(sys.argv) > 2 else ""

SECCION = """## LA CAJA DEL PARTE SE VACÍA DE VERDAD AL GUARDAR (v529)

Probando la v528 EN PRODUCCIÓN (sesión de campo, PRJ-0015): escribir un parte, confirmar lo
propuesto y deshacerlo funcionó —guardar el parte 2,3 s, confirmar 2,2 s—, pero **el texto
se quedaba en la caja** después de «Daily log saved.», con el parte ya en la lista. Invita a
guardarlo otra vez, o a retocarlo y crear un duplicado.

### ⚠️ Por qué ningún test lo veía
Desde v516 la caja se vaciaba con `st.session_state.pop(clave)` y `st.rerun()`. El SERVIDOR
quedaba en «» y AppTest —que lee el valor del servidor— lo daba por bueno. Pero Streamlit
solo le manda al NAVEGADOR el valor nuevo (`set_value` en el proto) cuando el código lo
**asigna**; borrar la clave no se lo manda, y el navegador conserva lo suyo. Es la familia
del desplegable de v527: lo que pinta el navegador no es lo que dice el servidor.

### El arreglo
El guardado confirmado enciende una marca, y la pasada siguiente asigna «» a la caja ANTES
de pintarla (asignar la clave de un widget ya pintado revienta). Si la hoja falla, no se
enciende nada y el texto se queda — también en la pasada siguiente.

`verif_v529` ejecuta la pantalla con AppTest y mira el **`set_value`**, el contrato con el
navegador, no solo el valor; y valida su sonda con el patrón viejo (da «vacía» en el
servidor y `set_value` False). `verif_v516` actualizado con la razón escrita (afirmaba el
`pop`, ahora el principio: solo se vacía si la hoja confirmó); `romper_v516`, su rotura
sobre el mecanismo nuevo.

### Anotado, sin tocar
Buscando el mismo patrón en toda la app aparecen otros sitios que sueltan con `pop` la clave
de un widget. `invoices_ui` y `location_ui` lo hacen porque las opciones cambian (para que el
widget no reviente, no para vaciar nada a la vista). `survey_ui` reinicia la solución activa
y los pisos del diagrama tras un cálculo nuevo: si las opciones salieran idénticas, podría
pasar lo mismo que aquí — pendiente de revisar con el usuario.

14 comprobaciones · __BATERIA__ · __SUITE__
"""

FILA = ("| v529 | **La caja del parte se vacía de verdad al guardar.** Probando la v528 EN "
        "PRODUCCIÓN (parte 2,3 s, confirmar 2,2 s): el parte se guardaba y **el texto seguía en "
        "la caja**, invitando a guardarlo otra vez. ⚠️ Desde v516 se vaciaba con `pop` de su "
        "clave: el servidor quedaba vacío —y AppTest lo daba por bueno— pero el navegador no se "
        "enteraba, porque Streamlit solo le manda el valor (`set_value`) cuando el código lo "
        "ASIGNA. Ahora el éxito enciende una marca y la pasada siguiente asigna «» antes de "
        "pintarla; si la hoja falla, el texto se queda. `verif_v529` mira el `set_value`, no "
        "solo el valor. 14 comprobaciones · __BATERIA__ · __SUITE__ |\n")

CAB = "| Ver | Cambio principal |\n|---|---|\n"
A_HIST = "## Versiones desplegadas (v528 = actual)"
A_CLA = "## \u00daltimas versiones desplegadas (v528 = actual)"
TRAS_CAB = "o el \u00edndice del final.\n\n---\n\n"


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def unica(s, a, etq, f):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica en %s: %d" % (etq, f, s.count(a)))


if not (SUITE and BATERIA):
    raise SystemExit('faltan los resultados: doc_v529.py "<suite>" "<bateria>"')
for _k, _v in (("__BATERIA__", BATERIA), ("__SUITE__", SUITE)):
    SECCION = SECCION.replace(_k, _v)
    FILA = FILA.replace(_k, _v)

h = io.open(HIST, encoding="utf-8").read()
unica(h, A_HIST, "cabecera", "HISTORIAL.md")
unica(h, CAB, "tabla", "HISTORIAL.md")
unica(h, TRAS_CAB, "separador", "HISTORIAL.md")
h = h.replace(TRAS_CAB, TRAS_CAB + SECCION + "\n", 1)
h = h.replace(A_HIST, "## Versiones desplegadas (v529 = actual)")
h = h.replace(CAB, CAB + FILA)
escribir(HIST, h)
print("HISTORIAL.md: seccion v529 + fila + cabecera")

c = io.open(CLAUDE, encoding="utf-8").read()
unica(c, A_CLA, "cabecera", "CLAUDE.md")
unica(c, CAB, "tabla", "CLAUDE.md")
c = c.replace(A_CLA, "## \u00daltimas versiones desplegadas (v529 = actual)")
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
print("CLAUDE.md: fila v529 · se cayo %s · nota %s -> %d · %d bytes"
      % (vieja.strip(), m.group(1), int(m.group(1)) + 1, len(c.encode("utf-8"))))
