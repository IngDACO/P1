# -*- coding: utf-8 -*-
"""Cierra la sección v480: resultado de la suite y las 6 secciones medidas."""
import io

P = "C:\\Users\\diego\\P1\\CLAUDE.md"

ANCLA = """⚠️ Y un fallo **de la sonda, no del código**: `ast.walk` devolvía el `if prj:` de fuera
porque el texto del hijo está dentro del padre, y el guardián acusaba a un código
correcto. Se ató al `test`."""

EXTRA = """

Suite entera contra lo DESPLEGADO: **118 verde · 0 rojo · 0 roto** (1125 s).
⚠️ Se corrió **después** del último commit a propósito: la primera verde se había hecho
antes de anotar el comentario de v308, y un guardián que no ha visto el código que está
en producción no dice nada sobre producción.

### Las 6 secciones del campo, medidas en el móvil (no 3)
v478 dejó pendiente lo dinámico y v480 lo cierra: **Mis proyectos · Fichaje · Pre-Start**
con los números de arriba, y **Herramientas · Self-service · Biblioteca** comprobadas a
375 px — **0 desbordes, 0 elementos que se salgan del ancho, 0 objetivos táctiles por
debajo de 36 px**.
⚠️ Los «botones de 32×38» que aparecieron en el barrido **no eran un hallazgo**: son la
flecha del desplegable de Streamlit (el control entero mide 375×38 y se pulsa entero) y
el icono de ayuda de 16×16. Mirar qué eran deshizo la alarma, igual que con el margen.
⚠️ Y una lección de método: las tres primeras medidas de esas secciones salieron MAL
—las tres decían «Sign in»— porque al navegar rápido Streamlit pinta el acceso un
instante antes de restaurar la sesión de la cookie, y mi espera («que haya texto») se
conformaba con eso. La espera correcta es **que NO haya formulario de acceso** y que
aparezca una marca de la sección. Una medida tomada en el instante equivocado miente
igual que un selector que no casa."""

s = io.open(P, encoding="utf-8").read()
if s.count(ANCLA) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(ANCLA))
s = s.replace(ANCLA, ANCLA + EXTRA)

VF = "25 comprobaciones |\n"
NF = "25 comprobaciones · suite **118 verde** · las **6** secciones del campo medidas a 375 px |\n"
if s.count(VF) != 1:
    raise SystemExit("ancla fila no unica: %d" % s.count(VF))
s = s.replace(VF, NF)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("CLAUDE.md: suite 118 + las 6 secciones medidas")
