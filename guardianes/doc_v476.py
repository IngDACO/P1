# -*- coding: utf-8 -*-
"""Documenta v476 en CLAUDE.md."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

SECCION = """## ⚠️ «Invalid role.»: no se podia crear un usuario de campo (v476)

Reportado por el usuario: al dar de alta a alguien de campo desde el panel del admin,
la app respondia **«Invalid role.»** y no creaba nada.

**v469** paso los roles a ingles —la constante `auth.ROLES`, el dato de la hoja y la
canonizacion al leer— y **se dejo dos literales en la interfaz**:

| Dónde | Qué pasaba |
|---|---|
| `auth_ui:1109` | el admin creando un usuario de campo pasaba `"campo"` → `add_user` valida contra `ROLES` y devolvia «Invalid role.». **Nadie de campo se podia dar de alta** |
| `auth_ui:275` | el **BOOTSTRAP** (primer propietario con la hoja `Login` vacia) pasaba `"propietario"`. Latente, pero PEOR: una instalacion desde CERO no habria podido crear su primer usuario — la app no arranca |

Es, otra vez, **un valor migrado en un sitio y olvidado en su gemelo**: la misma
familia que `auth._COL` (v433), la proyeccion de `list_users` (v434) y las tres
caducidades que destapo v475.

### Se acoto la CLASE antes de tocar, no el caso
Barrido de literales que canonizan a otra cosa: **101 candidatos → 8 reales → 2 rotos**.
Los otros 93 son claves internas de dicts (`.get("usuario")`, `.get("proyecto")`) y los
6 restantes son etiquetas internas cuyo productor y consumidor coinciden. ⚠️ Y eso
ultimo se COMPROBO, no se supuso: `Alerts.Origin` y `AssetMovements.To` **no estan en
la lista blanca** de `valores.COLUMNAS`, asi que nunca se canonizan al leer y los dos
lados siguen de acuerdo; `Login.Role` **si** esta, que es justo lo que hace que una
fila vieja de la hoja se siga leyendo bien.

### ⚠️ Por que no lo vio ningun guardian
`verif_v469` barre **`ast.Compare`** —las ramas muertas— y estos dos literales entran
como **ARGUMENTO**. Un guardian ve solo la forma que se le enseño (v309/v349/v441), y
esta forma no estaba cubierta. Chequeo nuevo y general en ese mismo fichero: ningun
literal pasado a `add_user`/`set_role` puede quedar fuera de `auth.ROLES` — **derivado
de la constante**, no de una lista a mano, y con la sonda validada contra un caso
conocido-malo antes de creerse su cero.

### ⚠️ Y el shadowing de v440, cometido DENTRO del guardian nuevo
Escribi `for _f in sorted(os.listdir("core"))` y **`_f` es la LISTA DE FALLOS** de ese
guardian: al terminar valia `"app.py"`, asi que el veredicto contaba
`len("app.py") = 6` fallos que no existian. Lo delato que **todas las comprobaciones
imprimieran «ok» y el contador dijera 6** — un descuadre entre lo que se ve y lo que se
cuenta. Es exactamente el fallo que este documento lleva versiones describiendo, hecho
al escribir la red que lo vigila.
"""

FILA = ("| v476 | ⚠️ **«Invalid role.»: no se podia crear un usuario de campo** (lo "
        "reporto el usuario). **v469** migro los roles a ingles y se dejo DOS literales "
        "en la interfaz: el alta de campo (`\"campo\"`) y —peor, aunque latente— el "
        "**BOOTSTRAP** del primer propietario (`\"propietario\"`), o sea que una "
        "instalacion desde cero no habria arrancado. Se acoto la CLASE antes de tocar "
        "(101 candidatos → 8 reales → 2 rotos; los demas son claves internas o etiquetas "
        "que **no se canonizan al leer**, comprobado contra `valores.COLUMNAS`). ⚠️ No lo "
        "vio ningun guardian porque `verif_v469` barre **comparaciones** y esto entra "
        "como **argumento**: chequeo nuevo derivado de `auth.ROLES` y validado contra un "
        "caso conocido-malo. ⚠️ Y escribiendolo cometi el **shadowing de v440 dentro del "
        "propio guardian** (`_f`, que es su lista de fallos, como variable de bucle → "
        "`len(\"app.py\")` = 6 fallos inexistentes); lo delato que todo saliera «ok» y el "
        "contador dijera 6. Suite **116 verde** |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v475 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v476 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: sección v476 + fila + cabecera")
