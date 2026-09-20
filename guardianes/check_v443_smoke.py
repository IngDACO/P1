# -*- coding: utf-8 -*-
"""Smoke de v443: EJECUTAR lo que se tocó. Importar no ejecuta (v378).

Lo que se cambió son cabeceras de tabla que viajan al PDF de las herramientas y
llamadas `d()`/`t()` nuevas. `compileall` y el import las dan por buenas: el
`UnboundLocalError` de v437/v439 y el `NameError` de v423 solo aparecen al LLAMAR.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

ok = True


def chk(t_, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


# ── 1 · la matriz de resultado de rieles (usa `d()` a nivel de módulo) ──
from core import rail_cut_ui as RC                                 # noqa: E402
_vals = [{"CutRC": 10.0, "CutRCW": 12.0}, {"CutRC": -3.0, "CutRCW": 0.0}]
_m = RC._result_matrix(["CutRC", "CutRCW"], _vals, 2)
chk("rieles: `_result_matrix` se EJECUTA", _m is not None)
chk("...y sus columnas van en inglés", list(_m.columns) == ["Lift 1", "Lift 2"],
    str(list(_m.columns)))

# ── 2 · el PDF de la herramienta con las cabeceras nuevas ──
from core.tool_pdf import tool_pdf                                 # noqa: E402
from core.i18n import d                                            # noqa: E402
_filas = [{d("Lift"): 1, "L (mm)": 100.0, "RC (mm)": 200.0}]
_pdf = tool_pdf(d("Rail cutting — Case 1"),
                meta={d("Project"): "PRUEBA"},
                tablas=[(d("Cuts per lift"), _filas)],
                notas=["nota"])
chk("el PDF se GENERA con la cabecera nueva", _pdf[:4] == b"%PDF", str(_pdf[:8]))
_txt = _pdf.decode("latin-1", "replace")
chk("...y no lleva la cabecera vieja «Elevador»", "Elevador" not in _txt)

# ── 3 · belting: la tabla de resultados dentro de su render ──
import ast                                                         # noqa: E402
_bt = ast.parse((RAIZ / "core/belting_ui.py").read_text(encoding="utf-8"))
_fn = next(f for f in ast.walk(_bt)
           if isinstance(f, ast.FunctionDef) and f.name == "render_belting_tab")
# ⚠️ `d` no puede ser variable en esa función: taparía la del motor en TODO el
# ámbito y reventaría con UnboundLocalError (el fallo de v437, cuatro veces ya).
_locales = {x.id for x in ast.walk(_fn)
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
chk("belting: `d` no se usa como variable en render_belting_tab",
    "d" not in _locales, str(sorted(_locales & {"d", "t", "_d"})))

# ── 4 · las llamadas nuevas de invoices_ui / catalogo_ui resuelven ──
from core import invoices_ui, catalogo_ui                          # noqa: E402
chk("invoices_ui tiene `d` resuelto", callable(getattr(invoices_ui, "d", None)))
chk("catalogo_ui tiene `t` resuelto", callable(getattr(catalogo_ui, "t", None)))

# ── 5 · el desglose del propietario, en inglés y sin reventar ──
from core import home_ui as H, admin_digest                        # noqa: E402
admin_digest.owner_digest = lambda: [
    {"grupo": "cliente1", "activos": 2, "avance": 50, "retrasos": 2, "alarmas": 1,
     "vencidos": 1, "cred_venc": 1, "sobre_presupuesto": 1, "pendientes": True}]
st.session_state["auth"] = {"usuario": "dacox", "grupo": "", "rol": "owner",
                            "nombre": "dacox"}
_a = H._alertas("")
chk("el desglose del propietario se EJECUTA", bool(_a))
chk("...y ya no dice «alarmas»/«vencidos»/«credenciales»",
    _a and "alarms" in _a[0] and "overdue" in _a[0] and "credentials" in _a[0],
    str(_a[:1]))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
