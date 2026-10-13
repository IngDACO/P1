# -*- coding: utf-8 -*-
"""v576 · LO VISTO VERIFICANDO v575: las cifras se apilaban UNA POR FILA en estrecho.

Medido en producción (13/10/2026, panel a 640 px): las cuatro cifras de la lista de Contacts
salían una por fila, 607 px de ancho cada una (400 px de alto entre las cuatro): a ≤640 px
Streamlit apila las columnas. Invoices y Gastos las dejaban 2 por fila con una regla
`@container` (medida en v568/v569); las tres tiras nuevas de v571-v575 no la llevaban: la
LISTA de Contacts, el RESUMEN de la ficha del cliente y las cifras de Payroll.
→ `theme.dos_por_fila(clave)`, la regla en un solo sitio, y las tres la llevan.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUAR = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


from core import theme                                                     # noqa: E402

_css = theme.dos_por_fila("cpx_x_kpis")
chk("el helper: contenedor medido y 2 por fila bajo 700 px",
    ".st-key-cpx_x_kpis{container-type:inline-size}" in _css and "@container (max-width:700px)" in _css
    and "calc(50% - 0.5rem)" in _css and _css.startswith("<style>") and _css.endswith("</style>"), _css[:120])

from streamlit.testing.v1 import AppTest                                    # noqa: E402


def _cab(fichero):
    t = ast.parse(io.open(os.path.join(GUAR, fichero), encoding="utf-8").read())
    return next(n.value.value for n in t.body if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "CAB")


def _tiene(at, clave):
    return any((".st-key-%s{container-type:inline-size}" % clave) in m.value for m in at.markdown)


C571 = _cab("verif_v571.py")
at = AppTest.from_string(C571, default_timeout=90)
at.session_state["_LISTA"] = True
at.run()
chk("⚠️ la LISTA de Contacts lleva la regla (y sus cuatro cifras, dentro de ese contenedor)",
    not at.exception and _tiene(at, "cpx_clis_kpis"), [e.value for e in at.exception][:1])
at = AppTest.from_string(C571, default_timeout=90)
at.run()
chk("⚠️ el RESUMEN de la ficha del cliente, también", not at.exception and _tiene(at, "cpx_cls_kpis"),
    [e.value for e in at.exception][:1])
at = AppTest.from_string(_cab("verif_v574.py"), default_timeout=90)
at.run()
chk("⚠️ y las cifras de Payroll", not at.exception and _tiene(at, "cpx_nom_kpis"),
    [e.value for e in at.exception][:1])

# Las tres tiras tienen que estar DENTRO del contenedor que la regla mide: por el código,
# los botones `cpxkpi_*` cuelgan de `st.container(key=…)` (con `with` o como `_box.columns`).
_arb = {m: ast.parse(io.open(os.path.join(RAIZ, "core", m), encoding="utf-8").read())
        for m in ("clientes_ui.py", "payroll_ui.py")}
_claves = {ast.unparse(k.value) for t in _arb.values() for n in ast.walk(t) if isinstance(n, ast.Call)
           and ast.unparse(n.func).endswith("container") for k in n.keywords if k.arg == "key"}
chk("los tres contenedores existen con su clave",
    {"'cpx_clis_kpis'", "'cpx_cls_kpis'", "'cpx_nom_kpis'"} <= _claves, _claves)
# ⚠️ En el resumen del cliente las columnas salen del contenedor como `_box.columns(2)`: con
# `st.columns(2)` caerían FUERA del recuadro que la regla mide y no haría nada.
_cc = next(n for n in ast.walk(_arb["clientes_ui.py"]) if isinstance(n, ast.FunctionDef)
           and n.name == "_cifras_cliente")
_cols = [ast.unparse(n.func) for n in ast.walk(_cc) if isinstance(n, ast.Call)
         and ast.unparse(n.func).endswith(".columns")]
chk("…y sus columnas salen DEL contenedor (`_box.columns`, no `st.columns`)",
    _cols and all(c == "_box.columns" for c in _cols), _cols)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
