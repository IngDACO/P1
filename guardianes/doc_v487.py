# -*- coding: utf-8 -*-
"""Documenta v487 en CLAUDE.md (y la verificacion en produccion de v486)."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## ⚠️ Lo que v469 dejó escrito en español, y los desplegables que SOBRESCRIBÍAN (v487)

Salió de la pregunta del usuario *«¿ya quedó todo terminado?»*, **auditada contra el
código** en vez de contestada de memoria (la regla de v453). La respuesta era no.

### v486, verificado en producción con datos reales (antes de esta versión)
Tras el reinicio del proceso se vio el parte de horas con los días vacíos y las cifras
de control (0.09 / 0.04). Las otras tres tablas no tenían filas en la demo, así que se
sembraron en `cliente1` —2 artículos, 2 nóminas, 1 activo con 2 movimientos, todos
«ZZ PRUEBA v486»—, se miraron en pantalla (Hours del producto vacío junto a `6.50`,
Rate/h vacío junto a `$42.50`, Cost vacío junto a `$128`) y se **borraron** con doble
guarda (ID sembrado **y** marca en la fila). Foto antes/después en solo lectura:
**idéntica** en filas, IDs y cabeceras.
⚠️ Dos cosas de la prueba que NO eran fallos de la app, comprobadas antes de reportarlas:
«To pay» contaba la nómina marcada `paid` porque las nóminas guardan el estado en
**español** (`pagada`, a propósito desde v469) y la fila cruda la escribí yo en inglés;
y la categoría `Tools` salía como `Consumable` porque la canónica es `Tool` — pero eso
destapó lo de abajo.

### ⚠️ 1. Las KPIs de inventario marcaban 0 SIEMPRE desde v469
```python
c[1].metric(t("Available"), est.get("disponible", 0))
c[2].metric(t("In use"), est.get("en_uso", 0))
```
`resumen()` cuenta por el estado **ya canonizado** (`available`, `in use`), así que esas
dos claves no existían nunca. **Ejecutado**: con 2 disponibles y 1 en uso, las dos
tarjetas daban 0. ⚠️ **El guardián de v469 no podía verlo**: barre `ast.Compare` y aquí
el valor viejo es la **clave de una búsqueda**. Es v309/v349/v441 otra vez: *la red ve
solo la forma que se le enseñó*.

### ⚠️ 2. Y se seguía ESCRIBIENDO en español
Barrido en todas las formas (valor de dict, `x["Col"] = …`, defecto por `or`, fila
posicional de un `append_row`): **12 sitios**. Los que importan:
| Dónde | Efecto |
|---|---|
| `inventory.create_activo` · `mantenimiento` | `disponible`/`bueno`/`bodega`/`mantenimiento` en la hoja: se canoniza al leer, pero la hoja queda **mezclada** |
| `expenses` ×2 · `or "Otros"` | una compra sin categoría caía en «Otros» **al lado** de «Other»: la torta partía la misma categoría en **dos trozos, los dos rotulados «Other»** |
| `orders` · `or "Materiales"` | la categoría del gasto que nace al recibir una orden |
| `projects_ui` · `or "otro"` | pintaba **«otro»** en la lista de archivos |
| `auth_ui` · `or "campo"` | ver abajo: el peor |
Ahora con constantes con nombre (`INV.DISPONIBLE`, `expenses.SIN_CATEGORIA`…).

### ⚠️ 3. `L.index(v) if v in L else 0` SOBRESCRIBE EN SILENCIO
Delante de un desplegable que EDITA: si el valor guardado no está en la lista —una
categoría que se borró con `del_categoria`, un rol mal tecleado en la hoja, un color que
no es de la paleta— se muestra la **primera** opción y «Guardar» la escribe encima, sin
que nadie la eligiera. **12 sitios en 6 pantallas**: inventario ×4, catálogo ×2, tipo y
estado manual del proyecto (⚠️ el estado manual podía **des-archivar** una obra), estado
de una localización, rol y empresa de un usuario, y color de un trabajo.
⚠️ **El de Usuarios era el peor**: `_rcur = u.get("Role") or "campo"` — y `"campo"` es
español desde v469, así que **no está en `ROLES`**: un usuario sin rol salía con
**owner preseleccionado**, y un «Apply role» distraído lo convertía en propietario.

`ui_common.opciones_con_actual(opciones, actual)` es la definición única: el valor actual
se **antepone** y queda seleccionado, así que guardar sin tocar ese campo conserva lo que
había. Un vacío no se antepone (no hay dato que proteger). ⚠️ **No muta la lista**: son
constantes de módulo, y anteponerles un valor las cambiaría para toda la app hasta
reiniciar el proceso.
⚠️ En el color hacía falta además tocar el **guardado**: hacía `_colmap[_cn]`, y con un
color que no es un nombre de la paleta eso lanza `KeyError` y el formulario no guardaría.

### Tres fallos de método míos, los tres cazados por las propias redes
1. **El primer barrido de búsquedas dio 173 sitios y 171 eran sanos**: `usuario`,
   `proyecto`, `entrada`, `pendiente`… son valores viejos **y** claves internas de
   diccionarios que la propia app construye. El discriminador que sí funciona: la clave
   buscada **no la mete a mano nadie**, así que solo puede venir de los DATOS, que llegan
   canonizados. Validado contra el fallo construido **y** contra una clave interna sana.
2. **Los nombres de las 5 funciones exentas los supuse, y 4 no existían.** Lo cazó la
   comprobación de «exentos que siguen existiendo» del propio guardián — sin ella, una
   lista de exenciones mal escrita no exime nada y nadie se entera (v135 otra vez).
3. **Un `AttributeError` al ejecutar la pantalla parecía de la app** y era de mi
   `st.dataframe` sustituido, que devuelve `None`. Se comprobó re-ejecutando sin el
   sustituto antes de concluir nada.

### Verificación
`verif_v469` gana el bloque 10 (búsquedas y escrituras, con la red validada contra el
caso construido); `verif_v487` el patrón en todo el repo con **exentos por (fichero,
FUNCIÓN)** y razón escrita (idioma de sesión, días del tablero, posiciones de
cabecera); `check_v487_smoke` **ejecuta** las KPIs y las dos fichas con valores fuera de
la lista, con un CONTROL de que un valor de la lista no se duplica. Batería contra los
**tres a la vez**: 10/10 roturas + CONTROL, con el verde de base primero.
"""

FILA = ("| v487 | ⚠️ **Lo que v469 dejó escrito en español y los desplegables que "
        "SOBRESCRIBÍAN**, salido de auditar «¿ya quedó todo?» contra el código. **(1)** "
        "Las KPIs «Available»/«In use» de inventario marcaban **0 SIEMPRE**: buscaban "
        "`\"disponible\"`/`\"en_uso\"` y el estado llega canonizado — ejecutado, 2 "
        "disponibles daban 0; ⚠️ el guardián de v469 solo barría comparaciones y aquí el "
        "valor viejo era una **clave de búsqueda**. **(2)** 12 sitios seguían "
        "**escribiendo** en español (la torta partía «Other» en dos trozos, «otro» en "
        "pantalla). **(3)** `L.index(v) if v in L else 0` delante de un formulario que "
        "edita **sobrescribía en silencio** en 12 sitios de 6 pantallas —⚠️ podía "
        "des-archivar una obra, y en Usuarios el defecto `\"campo\"` (español) dejaba un "
        "usuario sin rol con **owner preseleccionado**—: `ui.opciones_con_actual` "
        "conserva el valor guardado. ⚠️ El primer barrido dio 173 búsquedas y **171 "
        "eran claves internas sanas** (el discriminador: nadie mete esa clave a mano); y "
        "**4 de mis 5 exentos tenían nombres inventados**, cazado por el propio "
        "guardián. + v486 **verificado en producción** sembrando y borrando datos "
        "(antes/después idéntico). 10/10 roturas contra 3 guardianes a la vez |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v486 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v487 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v487 + fila + cabecera")
