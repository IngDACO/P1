# -*- coding: utf-8 -*-
"""v546: la trampa nº35 (un `st.expander` SIN clave se cierra solo cuando cambia lo de
encima). Un solo uso."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = "C:/Users/diego/P1/CLAUDE.md"
ANCLA = "**Y la regla de siempre, que volvió a aplicar:** antes de borrar el LECTOR"
TRAMPA = """35. ⚠️ **Un `st.expander` SIN clave se cierra solo cuando cambia lo que tiene encima.**
    Cada acción deja un aviso por `flash`, que se pinta una pasada y se va: al aparecer o
    irse, Streamlit crea de nuevo el desplegable de debajo y nace CERRADO. Con controles
    dentro, el usuario pone la hora y el botón desaparece (v546, el panel «Did you forget…»
    de Fichaje, 3 veces; y la lectura de la IA del Home). Comprobado en una mini-app 1.64:
    CON clave sigue abierto. → Un desplegable con controles dentro lleva `key=`.

"""
s = io.open(P, encoding="utf-8").read()
if s.count(ANCLA) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(ANCLA))
if "35. ⚠️ **Un `st.expander` SIN clave" in s:
    raise SystemExit("la trampa 35 ya estaba")
io.open(P, "w", encoding="utf-8", newline="").write(s.replace(ANCLA, TRAMPA + ANCLA))
print("CLAUDE.md: trampa 35 añadida")
