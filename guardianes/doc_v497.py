# -*- coding: utf-8 -*-
"""Documenta v497 en CLAUDE.md: el emparejado con Xero dice por qué y se aplica de una vez."""
import io

P = "C:/Users/diego/P1/CLAUDE.md"

SECCION = """## El emparejado con Xero dice POR QUÉ, y se aplica de una vez (v497)

El usuario preguntó cómo automatizar el emparejado de personas con empleados de Xero.
⚠️ **Al mirar el código, la mitad de lo que pedía YA estaba**: `propuesta` empareja sola
(por correo y, si no, por nombre, solo parejas únicas) y cada desplegable **viene
preseleccionado** con ella, así que basta con «Save matches». Decirlo y no construir un
botón que repite lo que ya hace la app es parte del trabajo (v146: dos mecanismos para lo
mismo envejecen mal). Lo que de verdad faltaba era otra cosa:

1. **Por qué alguien se queda sin pareja.** Un «— not in Xero —» mudo manda a buscar el
   problema a Xero, y **casi siempre lo que falta está en COPEX**: el correo de esa
   persona. `propuesta_detallada` devuelve, por cada uno, la pareja **y su motivo**:
   `sin_email` · `no_esta` · `email_repetido` · `nombre_repetido` · `mismo_empleado`.
   La pantalla los cuenta («2 by email · 1 by name») y lista los que no, con su motivo.
2. **Volver a aplicar las propuestas** («Fill in the N proposed matches»), que es lo único
   que el valor por defecto no puede hacer: recuperar las filas que alguien dejó a mano en
   «— not in Xero —».

### Las reglas que fallarían en silencio
- ⚠️ El relleno escribe **claves de widget**, así que va por BANDERA y ocurre en la pasada
  siguiente (regla v111): hacerlo al pulsar revienta.
- **No pisa** lo que el administrador eligió, y **no pone al mismo empleado en dos
  personas** — eso paga las horas de una a otra. La protección que manda sigue siendo la de
  v490: si dos filas acaban en el mismo empleado, se avisa y **Guardar queda deshabilitado**.
- `propuesta` **DELEGA** en `propuesta_detallada`: una sola definición de cómo se empareja
  (v323), y el guardián comprueba que no vuelva a tener lógica propia.
- ⚠️ **Con el correo repetido se intenta el NOMBRE**, y si ese es único la pareja vale: la
  regla es «solo parejas únicas», no «solo por correo». Costó una comprobación mal escrita
  darse cuenta de que el código tenía razón y la prueba no.

### Verificación
`verif_v497.py`, **24 comprobaciones**, con la pantalla EJECUTADA (Streamlit sustituido):
los cinco motivos, el recuento, el botón, el relleno en la pasada siguiente, que no pisa ni
duplica, y por AST que la bandera se lee ANTES del primer desplegable. Batería: **8/8
roturas + CONTROL**.
⚠️ **Una rotura se escapó y enseñó algo**: desactivé el relleno entero y el guardián siguió
verde, porque **el desplegable ya trae la propuesta por defecto** y mi caso lo medía así. El
único caso que el botón resuelve —y el único que lo demuestra— es una fila que alguien dejó
en «— not in Xero —». Es la lección de siempre: una comprobación que puede pasar por otro
camino no comprueba lo que dice.
"""

FILA = ("| v497 | **El emparejado con Xero dice POR QUÉ y se aplica de una vez** (a raíz de «¿cómo "
        "automatizamos el emparejado?»). ⚠️ Auditar antes de construir: la propuesta automática YA "
        "existía y el desplegable ya venía preseleccionado — lo que faltaba era el motivo de cada "
        "fila sin pareja (`sin_email` · `no_esta` · `email_repetido` · `nombre_repetido` · "
        "`mismo_empleado`; casi siempre lo que falta está en COPEX, no en Xero) y un botón para "
        "recuperar las propuestas en las filas dejadas en «not in Xero». Relleno por BANDERA (v111), "
        "sin pisar lo elegido ni duplicar empleado, y `propuesta` DELEGA en la detallada. 24 "
        "comprobaciones · **8/8 roturas + control** ⚠️ una se escapó porque el valor por defecto ya "
        "hacía pasar el caso |\n")

s = io.open(P, encoding="utf-8").read()
ANCLA = "## Versiones desplegadas (v496 = actual)"
CAB = "| Ver | Cambio principal |\n|---|---|\n"
for etq, a in (("cabecera", ANCLA), ("tabla", CAB)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))
s = s.replace(ANCLA, SECCION + "\n## Versiones desplegadas (v497 = actual)")
s = s.replace(CAB, CAB + FILA)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: seccion v497 + fila + cabecera")
