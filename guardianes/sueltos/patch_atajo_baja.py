# -*- coding: utf-8 -*-
"""La etiqueta de la seccion, y el atajo para avisar de una baja desde Fichaje."""
import ast
import io

# ── 1. la etiqueta: la palabra del usuario ───────────────────────────────────
P = "C:\\Users\\diego\\P1\\survey_app\\core\\home_ui.py"
s = io.open(P, encoding="utf-8").read()
V = '    ("autogestion",  ":material/account_circle: My things"),\n'
N = '    ("autogestion",  ":material/account_circle: Self-service"),\n'
if s.count(V) != 1:
    raise SystemExit("ancla etiqueta: %d" % s.count(V))
io.open(P, "w", encoding="utf-8", newline="").write(s.replace(V, N))
print("home_ui: la seccion se llama «Self-service» (autogestion)")

# ── 2. el atajo, en Fichaje ──────────────────────────────────────────────────
P = "C:\\Users\\diego\\P1\\survey_app\\core\\timeclock_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''        f'<span style="font-weight:700;color:{_col};font-size:16px;">{_est}</span>'
        f'<span style="color:#6b7280;font-size:12px;"> · {_det}</span></div>',
        unsafe_allow_html=True)
'''

NUEVO = '''        f'<span style="font-weight:700;color:{_col};font-size:16px;">{_est}</span>'
        f'<span style="color:#6b7280;font-size:12px;"> · {_det}</span></div>',
        unsafe_allow_html=True)

    # ── Atajo: «hoy no puedo ir» (v478) ──────────────────────────────────────
    # ⚠️ v478 metio las tres pantallas «mias» del campo bajo un nivel, y avisar de una
    # baja es la UNICA accion urgente de las tres: se usa la mañana que alguien se
    # levanta enfermo, en el movil. v430 la registra al instante justo por eso, asi que
    # el toque que perdio en el menu se devuelve AQUI, que es la pantalla que esa
    # persona abre esa misma mañana.
    # ⚠️ Solo si NO esta fichado: quien ya ficho no va a avisar de una baja, y el
    # boton solo seria ruido en la pantalla que mas se usa.
    if rol == "field" and not gen and not prj:
        if st.button(t(":material/sick: I cannot make it today — report sick leave"),
                     key="tc_baja", width="stretch"):
            from core.home_ui import navegar          # perezoso: evita el ciclo
            navegar("autogestion", "🌴 Ausencias")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla atajo: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("timeclock_ui: atajo a «avisar de una baja» cuando no esta fichado")
