# -*- coding: utf-8 -*-
"""Añade a la sección v480 lo que salió de los tres rojos de la suite."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

BLOQUE = """
### ⚠️ Los tres rojos de la suite, y el fallo de dinero que había detrás
Ninguno era una regresión de las cuatro mejoras, y **uno no era falsa alarma**:

- **`es_del_proyecto` con el nombre VACÍO devolvía `True`.** El respaldo por nombre
  comparaba `"" == ""`, así que una obra cuyo `Name` estuviera en blanco se quedaba con
  **todas las jornadas generales** —las que no llevan proyecto— y con sus horas. Eso
  entra en `project_hours` y en el **costo de mano de obra** por sus tres llamadas
  (`projects.py` ×2, `expenses.py`), o sea que era un error de dinero silencioso. Y el
  `Name` en blanco no es hipotético: **el cliente tiene acceso a su propio libro**.
  Ahora, sin nombre no hay respaldo posible.
- **`check_ceros.py` leía `Nombre`/`Grupo`**, en español: **v468 renombró esas
  columnas**, así que le llegaba el nombre vacío y —por lo anterior— acusaba a obras
  inocentes de tener fichajes sin contar. ⚠️ Se mantuvo verde doce versiones **solo
  porque el libro de la demo no tenía obras**: en cuanto hubo una obra y una jornada,
  mintió. Es exactamente el guardián que habría gritado en cuanto entrara un cliente
  real.
- **`verif_v455`** exigía ver **≥3 modelos de ingreso distintos** en cuanto hubiera UNA
  obra: su salvaguarda solo contemplaba el libro vacío, y con una obra la variedad es
  imposible por aritmética. Ahora pide que haya **con qué** comprobar.

### ⚠️ Y tres afirmaciones de v308 que caducaron — reancladas, no relajadas
Las tres protegían de verdad el fallo de v306 (que a la hoja fuera la **etiqueta** del
desplegable en vez del **nombre**), pero lo hacían por su FORMA: «0 `next(...)` en la
función», «3 `_nom_de.get`» y una **lista de keys escrita a mano**. El botón nuevo usa
`next(iter(idmap))` para el TEXTO y saca el nombre de `_nom_de` — cumple la regla y
rompía el proxy.
Ahora afirman lo que protegían, **y más fuerte**: que **TODA** llamada a
`fichar_proyecto` tome su nombre de `_nom_de`, sean una o diez; y que en la columna del
Proyecto solo haya keys suyas, **derivado** en vez de listado (v433/v434).
⚠️ Con **control**: la sonda se valida contra el fallo de v306 **reconstruido**, porque
un cero que no sabe reconocer el fallo que busca no vale nada (trampa nº12).
"""

s = io.open(P, encoding="utf-8").read()
ANCLA = "### Verificación\n`verif_v480.py`, **25 comprobaciones**."
if s.count(ANCLA) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(ANCLA))
s = s.replace(ANCLA, BLOQUE.strip() + "\n\n" + ANCLA)

# la fila del índice recoge el hallazgo de dinero
VF = "descartó una alarma propia (el campo **no** ve el margen) y queda **una pregunta "
NF = ("⚠️ **un fallo de dinero** salido de un rojo que parecía falsa alarma: "
      "`es_del_proyecto` con el nombre vacío se quedaba con **todas las jornadas "
      "generales** (entra en horas y costo de mano de obra). + se "
      "descartó una alarma propia (el campo **no** ve el margen) y queda **una pregunta ")
if s.count(VF) != 1:
    raise SystemExit("ancla fila no unica: %d" % s.count(VF))
s = s.replace(VF, NF)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: los tres rojos + el fallo de dinero")
