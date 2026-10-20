"""v592 · TOOLS → PLUMB LINE, PROBADA (decisión del usuario: «Dale con todo»).

Visto en producción (20/10/2026, Bondi L1 con 3 ascensores BSR 1985 / 2010 / 1900):
  1. ⚠️ Resultados VIEJOS sin aviso (plantilla 350 en pantalla y RW de la de 300); guardar los
     mezclaba con las entradas nuevas → aviso y ni descargar ni guardar hasta recalcular.
  2. ⚠️ El destino de guardar (bloque COMPARTIDO de las 4 herramientas) sin elegir y con las
     9 obras → la de arriba, elegida, y solo instalaciones abiertas. Guardar dos veces
     duplicaba → «Saved» mientras el cálculo sea el mismo.
  3. ⚠️ Reabrir un cálculo perdía su obra («— no project —») → la trae al selector.
  4. ⚠️ «DOES NOT FIT» y a la vez «move the assembly 33.7 mm» → solo el aviso, con lo que falta.
  5. `:orange[:material/warning:]` literal en la tabla, lo guardado y el PDF → texto limpio y la
     fila en rojo; un decimal (6 vs 6.5, 83 vs 82.7); la comprobación delante del texto.
  6. El cajetín «… — Lift 1 · Lift 3» → «… · lift 3 of 3»; «L side» → «left».
  7. Cifras de la plantilla ACTIVAS; el aviso del plano FIJO; los del PDF por `flash`; «lift(s)»;
     el PDF con obra y fecha; la leyenda con el icono de los campos; Files con un toque.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, *rel.split("/")), encoding="utf-8").read()


G = r'''
import streamlit as st
import pandas as pd
import importlib
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import plan_ui, flash, incrustar, toolruns, projects as P
plan_ui = importlib.reload(plan_ui)
from core import tool_save_ui, plumb_ui
_LL = st.session_state.setdefault("_LL", [])
_SVG = st.session_state.setdefault("_SVG", [])
incrustar.script = lambda html, *a, **k: _LL.append(html)
incrustar.dibujo = lambda html, *a, **k: _SVG.append(html)
_PRJ = {"ID": "PRJ-1", "Name": "Lift A", "Type": "Installation", "Status": "In progress", "Group": "cliente1"}
_PLANO = st.session_state.get("_PLANO", {})
plan_ui.selector_proyecto = lambda key, ayuda="": ((_PRJ, _PLANO) if st.session_state.get("_OBRA", True) else (None, {}))
P.list_projects = lambda *a, **k: [
    _PRJ,
    {"ID": "PRJ-9", "Name": "Lift A", "Type": "Installation", "Status": "Cancelled", "Group": "cliente1"},
    {"ID": "PRJ-8", "Name": "Truck", "Type": "Delivery", "Status": "Planned", "Group": "cliente1"},
    {"ID": "PRJ-7", "Name": "Lift B", "Type": "Ripout + Installation", "Status": "Planned", "Group": "cliente1"}]
P.get_project = lambda pid: {"PRJ-1": _PRJ}.get(pid)
toolruns.is_configured = lambda: True
def _reg(**k):
    st.session_state.setdefault("_REG", []).append(k)
    return {"ok": True, "id": "CAL-9", "drive_id": "x"}
toolruns.registrar = _reg
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for k, v in {"plb_bks": 1772, "plb_rail": 62, "plb_tksw": 965, "plb_lt": 300, "plb_sf1": 51,
                 "plb_sf2": 51, "plb_bs": 1998, "plb_sg": 300, "plb_tg": 60}.items():
        st.session_state[k] = float(v)
    st.session_state["plb_n"] = 3
    st.session_state["plb_bsr_df"] = pd.DataFrame({"Elevador": ["Lift 1", "Lift 2", "Lift 3"],
                                                   "BSR (mm)": [1985.0, 2010.0, 1900.0]})
flash.mostrar()
plumb_ui.render_plumb_tab()
'''


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error",
                                              "success") for x in getattr(a, k, []))


print("1. El cálculo, la tabla y los avisos (AppTest, los 3 ascensores de producción)")
at = AppTest.from_string(G, default_timeout=300)
at.session_state["_PLANO"] = {"params": {"BKS": 1772}, "faltan": []}
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_cap = " | ".join(str(c.value) for c in at.caption)
chk("⚠️ el aviso del plano de la obra, FIJO (salía «8 value(s)…» una pasada)",
    "The drawing fields come from the project's drawing data" in _cap and "value(s)" not in _cap)
next(b for b in at.button if b.key == "plb_calc").click()
at.run()
chk("calcula sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.run()
chk("…y el aviso del plano sigue en la pasada siguiente",
    "The drawing fields come from the project's drawing data" in " | ".join(str(c.value) for c in at.caption))
_k = sorted(b.key for b in at.button if str(b.key or "").startswith("cpxkpi_plb_"))
chk("⚠️ las cinco cifras de la plantilla son BOTONES (eran HTML)",
    _k == ["cpxkpi_plb_d1", "cpxkpi_plb_d2", "cpxkpi_plb_dbp", "cpxkpi_plb_dbpw", "cpxkpi_plb_rw"], _k)
_df = [d.value for d in at.dataframe if "di+DBP+dd" in list(getattr(d.value, "columns", []))]
_cols = list(_df[0].columns) if _df else []
chk("⚠️ la comprobación DELANTE y el encaje al final (a 1024 px «di+DBP+dd» quedaba fuera)",
    _cols == ["Lift", "BSR (mm)", "di (left wall→plumb)", "dd (plumb→right wall)", "di+DBP+dd", "Fit"],
    _cols)
_fit = list(_df[0]["Fit"]) if _df else []
chk("⚠️ el encaje en texto LIMPIO y con un decimal (salía `:orange[…]` y «83 > 81»)",
    len(_fit) == 3 and _fit[2] == "DOES NOT FIT · Omega 82.7 > limit 81.0"
    and not any(":orange[" in x or ":material/" in x for x in _fit), _fit)
chk("…«move 6.5 mm towards the left» (la tabla decía 6, el aviso 6.5; y «L side»)",
    _fit[:1] == ["move 6.5 mm towards the left"] and _fit[1] == "centred · clearance 6.0 mm/side", _fit)
_ok1 = " ".join(str(x.value) for x in at.info)
chk("el aviso del ascensor 1 con palabras: «towards the left … the Omega is on the right»",
    "**move the assembly 6.5 mm towards the left**" in _ok1 and "Omega is on the right" in _ok1, _ok1)
at.selectbox(key="plb_sel_e").set_value(3)
at.run()
_err = " ".join(str(x.value) for x in at.error)
_inf = " ".join(str(x.value) for x in at.info)
chk("⚠️ el que NO cabe: solo el aviso, con cuánto falta (1.7 mm) y qué hacer",
    "DOES NOT FIT" in _err and "1.7 mm short" in _err and "Re-measure the BSR" in _err
    and "move the assembly" not in _inf, (_err[:200], _inf[:120]))
chk("…y se llama «Lift 3 of 3»", "Lift 3 of 3" in _err)
_svg = " ".join(at.session_state["_SVG"])
chk("⚠️ el cajetín dice «Lift A · lift 3 of 3» (decía «… Lift 1 · Lift 3»)",
    "Lift A · lift 3 of 3" in _svg and "Lift A · Lift 3" not in _svg)

print("\n2. Las cifras llevan al dibujo")
_LL0 = len(at.session_state["_LL"])
next(b for b in at.button if b.key == "cpxkpi_plb_d1").click()
at.run()
chk("tocar d1 baja al dibujo del ascensor (arriba del todo)",
    any(".st-key-cpx_plb_dibujo" in s and "block:'start'" in s for s in at.session_state["_LL"][_LL0:]))

print("\n3. ⚠️ Guardar: destino elegido, solo instalaciones abiertas, una vez")
_s = at.selectbox(key="prj_plb")
chk("⚠️ el destino viene con la obra de arriba (antes «— choose the project —»)",
    _s.value == "Lift A (PRJ-1)", _s.value)
chk("⚠️ …y solo ofrece instalaciones abiertas (fuera la cancelada homónima y la entrega)",
    list(_s.options) == ["— choose the project —", "Lift A (PRJ-1)", "Lift B (PRJ-7)"], list(_s.options))
next(b for b in at.button if b.key == "save_plb").click()
at.run()
_reg = at.session_state["_REG"] if "_REG" in at.session_state else []
chk("se guarda UNA vez, en PRJ-1", len(_reg) == 1 and _reg[0].get("pid") == "PRJ-1", len(_reg))
chk("…con el nombre de la obra y la fecha en el PDF (eran todos «plumb_setout.pdf»)",
    bool(_reg) and str(_reg[0].get("filename", "")).startswith("Plumb_setout_Lift_A_")
    and str(_reg[0].get("filename", "")).endswith(".pdf"), _reg[0].get("filename") if _reg else "")
chk("…y el resumen con su plural («3 lifts», no «lift(s)»)",
    bool(_reg) and str(_reg[0].get("resumen", "")).endswith("· 3 lifts"), _reg[0].get("resumen") if _reg else "")
chk("…sin `:orange[` en lo guardado",
    bool(_reg) and ":orange[" not in str(_reg[0].get("datos")))
_bs = next(b for b in at.button if b.key == "save_plb")
chk("⚠️ después: «Saved as CAL-9» a la vista y el botón «Saved», desactivado (un 2º toque duplicaba)",
    "Saved as **CAL-9**" in " ".join(str(x.value) for x in at.success)
    and _bs.disabled and "Saved" in str(_bs.label), (str(_bs.label), _bs.disabled))
at.selectbox(key="prj_plb").set_value("Lift B (PRJ-7)")
at.run()
chk("…a OTRA obra sí se puede guardar", not next(b for b in at.button if b.key == "save_plb").disabled)

print("\n4. ⚠️ Resultados viejos: aviso, y ni descargar ni guardar")
at.number_input(key="plb_lt").set_value(350.0)
at.run()
_w = " ".join(str(x.value) for x in at.warning)
chk("cambiar la plantilla tras calcular lo DICE", "You changed data since the last calculation" in _w, _w[:200])
chk("…y no ofrece descargar ni guardar (mezclaría entradas nuevas con resultados viejos)",
    not [b for b in at.button if b.key == "save_plb"] and not list(at.get("download_button"))
    and "Recalculate to download or save it" in _todo(at))
next(b for b in at.button if b.key == "plb_calc").click()
at.run()
chk("…y al recalcular vuelve todo", "You changed data" not in " ".join(str(x.value) for x in at.warning)
    and bool([b for b in at.button if b.key == "save_plb"]))

print("\n5. ⚠️ Reabrir un cálculo trae su obra al selector")
G2 = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
from core import tool_save_ui, projects as P
P.get_project = lambda pid: {"ID": "PRJ-1", "Name": "Lift A"} if pid == "PRJ-1" else None
st.session_state["_toolrestore"] = {"herramienta": "plomada", "valores": {"plb_lt": 300.0},
                                    "id": "CAL-3", "obra": "PRJ-1"}
st.session_state["_R"] = tool_save_ui.aplicar_restauracion("plomada")
'''
at2 = AppTest.from_string(G2, default_timeout=60).run()
chk("reabre CAL-3 con «Lift A (PRJ-1)» en el selector de la plomada (antes «— no project —»)",
    at2.session_state["_R"] == "CAL-3" and at2.session_state["pl_prj_plb"] == "Lift A (PRJ-1)"
    and at2.session_state["plb_lt"] == 300.0)

print("\n6. El resto (estático)")
_PL = fuente("core/plumb_ui.py")
_arb = ast.parse(_PL)
_fl = [ast.unparse(n.func) for n in ast.walk(_arb) if isinstance(n, ast.Call)
       and any(isinstance(x, ast.Constant) and isinstance(x.value, str) and "From the drawing" in x.value
               for x in ast.walk(n))]
chk("los avisos de leer un PDF, por `flash` (iban antes de un `st.rerun()`)",
    "flash.exito" in _fl and "st.success" not in _fl, _fl)
# (por las CADENAS del código: la 1ª vuelta casó «✏️» en MI comentario — trampa 2)
_cads = [n.value for n in ast.walk(_arb) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("la leyenda con el icono de los campos (decía «✏️ = by hand»)",
    any(":material/edit: = by hand" in c for c in _cads) and not any("✏️" in c for c in _cads))
_sin = []
for _f in ("plumb_ui", "rail_cut_ui", "buffer_cut_ui", "belting_ui"):
    for c in ast.walk(ast.parse(fuente("core/%s.py" % _f))):
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "render_guardar" \
                and not any(k.arg == "obra_id" for k in c.keywords):
            _sin.append(_f)
chk("⚠️ las CUATRO herramientas pasan su obra al bloque de guardar", not _sin, _sin)
_PU = fuente("core/projects_ui.py")
_tr = _PU.split('key=f"arch_tbl_{pid}_')[0][-600:]
chk("Files: un toque en la celda elige la fila (`single-cell`; con `single-row` solo la enmarcaba)",
    'selection_mode="single-cell"' in _tr and "selection_mode=\"single-row\"" not in _tr
    and "c[0] for c in (getattr(_s, \"cells\"" in _PU)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
