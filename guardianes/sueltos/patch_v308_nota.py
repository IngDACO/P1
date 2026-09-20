# -*- coding: utf-8 -*-
"""El comentario de v308 que ahora dice media verdad.

Sigue justificando por que las dos acciones van en DOS COLUMNAS, y eso no cambia. Pero
la frase «en movil se apilan solas, asi que no se pierde nada» se lee como si el movil
estuviera resuelto, y v480 midio que no: apilarse no cuesta ancho, cuesta ALTO, y ese
alto era lo que mandaba la accion de cada mañana por debajo del pliegue.

⚠️ No se borra ni se reescribe la razon de v308 —es correcta— sino que se le añade lo
que se midio despues. Un comentario que se queda a medias es peor que ninguno: el
siguiente que lo lea dara por bueno que el movil ya estaba mirado (v433/v434).
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\timeclock_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = """    # Antes iban apiladas y separadas por una línea, con los botones estirados a todo
    # el ancho. ⚠️ En móvil —donde el campo usa esto— Streamlit apila las columnas
    # solo, así que no se pierde nada; en PC se acaba el scroll y el botón de 1350 px.
"""

NUEVO = """    # Antes iban apiladas y separadas por una línea, con los botones estirados a todo
    # el ancho. ⚠️ En móvil —donde el campo usa esto— Streamlit apila las columnas
    # solo, así que no se pierde nada; en PC se acaba el scroll y el botón de 1350 px.
    # ⚠️ v480 MATIZA esa última frase, con medida: apilarse no cuesta ANCHO, pero sí
    # ALTO — y el alto era el problema. Con las tarjetas delante, este bloque empezaba
    # en y=618 de 812 en un teléfono, o sea que fichar (lo primero que hace el campo
    # cada mañana) quedaba bajo el pliegue. Por eso el resumen se movió DEBAJO. Las dos
    # columnas se quedan como están: esa parte de v308 sigue siendo cierta.
"""

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/timeclock_ui.py: el comentario de v308, matizado con lo medido")
