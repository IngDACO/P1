"""v598 · UN TOQUE EN LA CELDA ELIGE LA FILA EN TODA LA APP (decisión del usuario: «Si dale»).

Visto verificando v597 (21/10/2026, producción): en la cartera de Projects tocar el NOMBRE de una obra
solo enmarcaba la celda, y «Open →» salía únicamente marcando la casilla — con «Tap a row and choose
what to do with it» debajo. Es el fallo que v567 descubrió (`single-row` en Streamlit 1.64: la fila
solo se elige con su casilla) y que v567-v592 fueron curando tabla a tabla; quedaban CUATRO: la
cartera (`cart_tbl`), People (`gu_tbl_*`), Inventory (`inv_tbl`) y Library (`lib_tbl`).
→ `single-cell` + la fila de la celda tocada. Y un BARRIDO para que no quede ni vuelva ninguna.
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


def _ss(a, k, defecto=None):
    return a.session_state[k] if k in a.session_state else defecto


def _lee_celdas(nodo):
    return any(isinstance(n, ast.Constant) and n.value == "cells" for n in ast.walk(nodo)) or \
        any(isinstance(n, ast.Attribute) and n.attr == "cells" for n in ast.walk(nodo))


# Los AYUDANTES que leen la celda (`_tabla_abre_obra`…): una tabla que les pasa su selección la
# lee por ellos. ⚠️ La 1ª vuelta marcó 3 tablas de Expenses/Contacts como «no leen la celda» —
# trampa 2, buscar texto no es mirar el uso: se la pasan a `_tabla_abre_obra`, que sí la lee.
AYUDANTES = set()


def barrer(src, nombre="?"):
    """Cada `st.dataframe(..., on_select=…)` → (línea, modo, ¿su función lee `.cells`?)."""
    tr = ast.parse(src)
    out = []
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for c in ast.walk(fn):
            if not (isinstance(c, ast.Call) and ast.unparse(c.func).endswith("dataframe")):
                continue
            kw = {k.arg: k.value for k in c.keywords}
            if "on_select" not in kw:
                continue
            modo = ast.literal_eval(kw["selection_mode"]) if "selection_mode" in kw else "(sin modo)"
            _llama = {ast.unparse(n.func).split(".")[-1] for n in ast.walk(fn) if isinstance(n, ast.Call)}
            # ⚠️ v600 · …o el CALLBACK del propio `on_select` (`functools.partial(_tocar_informe, …)`,
            # los informes de Inventory): ese ayudante no se LLAMA aquí, se pasa — y lee la celda.
            _pasa = {n.id for n in ast.walk(kw["on_select"]) if isinstance(n, ast.Name)}
            lee = _lee_celdas(fn) or bool(_llama & AYUDANTES) or bool(_pasa & AYUDANTES)
            out.append((nombre, c.lineno, fn.name, modo, lee))
    # una tabla dentro de una función anidada sale dos veces (la de fuera y la de dentro)
    return sorted({(a, b, m, l) for a, b, _f, m, l in out})


print("0. El barrido: toda tabla que se toca es `single-cell` y lee la CELDA")
_fuentes = {}
for base, _d, fs in os.walk(RAIZ):
    if any(x in base for x in (".git", "__pycache__", ".streamlit", "manuals", "static")):
        continue
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(base, f)
            _fuentes[os.path.relpath(p, RAIZ)] = io.open(p, encoding="utf-8").read()
for _src in _fuentes.values():      # 1ª pasada: qué funciones leen la celda (sin pintar tabla)
    for fn in ast.walk(ast.parse(_src)):
        if isinstance(fn, ast.FunctionDef) and _lee_celdas(fn) and "dataframe" not in ast.unparse(fn):
            AYUDANTES.add(fn.name)
_todas = []
for _n, _src in _fuentes.items():
    _todas += barrer(_src, _n)
chk("(los ayudantes que leen la celda, encontrados: %s)" % sorted(AYUDANTES), "_tabla_abre_obra" in AYUDANTES)
_mal = [x for x in _todas if x[2] != "single-cell"]
_sin = [x for x in _todas if x[2] == "single-cell" and not x[3]]
chk("ninguna `single-row` (ni `multi-row`): un toque en la celda solo la enmarcaba", not _mal, _mal)
chk("…y todas leen la fila de la CELDA tocada (`selection.cells`; con solo `.rows` el toque no hace nada)",
    not _sin, _sin)
chk("…y el barrido mira algo (no corre en vacío: hay tablas que se tocan)", len(_todas) >= 10, len(_todas))
# trampa 12: la sonda SABE ver el fallo
_ko = barrer("def f():\n    ev = st.dataframe(df, on_select='rerun', selection_mode='single-row')\n"
             "    return list(ev.selection.rows)\n")
_ko2 = barrer("def f():\n    ev = st.dataframe(df, on_select='rerun', selection_mode='single-cell')\n"
              "    return list(ev.selection.rows)\n")
chk("la sonda VE una `single-row` y una `single-cell` que no lee celdas (casos conocidos-malos)",
    _ko and _ko[0][2] == "single-row" and _ko2 and _ko2[0][3] is False, (_ko, _ko2))
_cuatro = {(n.replace(os.sep, "/"), m) for n, _l, m, _r in _todas
           if n.replace(os.sep, "/") in ("core/projects_ui.py", "core/auth_ui.py", "core/inventory_ui.py",
                                          "core/library_ui.py")}
chk("las cuatro de v598 están en el barrido y son `single-cell`",
    {n for n, m in _cuatro if m == "single-cell"} >= {"core/projects_ui.py", "core/auth_ui.py",
                                                       "core/inventory_ui.py", "core/library_ui.py"}, _cuatro)

PRE = r'''
import streamlit as st
if "_PRE_HECHO" not in st.session_state:
    st.session_state["_PRE_HECHO"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
'''

print("\n1. ⚠️ La cartera de Projects: un toque en el NOMBRE enseña las acciones de ESA obra")
GC = PRE + r'''
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "G"})
from core import projects_ui as PU
_P = [{"ID": "PRJ-1", "Name": "Obra Uno", "Status": "In progress", "Progress": 10, "Client": "C1", "Type": "Installation"},
      {"ID": "PRJ-2", "Name": "Obra Dos", "Status": "In progress", "Progress": 20, "Client": "C2", "Type": "Installation"}]
PU._cartera_lista(_P, {}, {}, {}, {}, {}, "G", False)
'''
at = AppTest.from_string(GC, default_timeout=120)
at.session_state["_PRE"] = {"cart_tbl": {"selection": {"rows": [], "columns": [], "cells": [(1, "Project")]}}}
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = " | ".join(str(m.value) for m in at.markdown)
chk("la celda de la 2ª fila → la tira de «Obra Dos» con «Open →» (antes hacía falta la casilla)",
    "**Obra Dos**" in _md and any(b.key == "cartlist_open" for b in at.button), _md[-200:])
next(b for b in at.button if b.key == "cartlist_open").click()
at.run()
chk("…y «Open →» abre PRJ-2", _ss(at, "_admin_open_proj") == "PRJ-2", _ss(at, "_admin_open_proj"))
# (la 1ª vuelta probaba también «la casilla sigue valiendo»: en `single-cell` NO HAY casillas — una
# sonda sin sentido, retirada con su razón)

print("\n2. People: un toque en la celda abre la ficha de ESA persona")
GU = PRE + r'''
from core import auth, auth_ui as AUI, credentials as C, timeclock as T
from core import admin_digest
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
def _u(u, n):
    return {"User": u, "Name": n, "Role": "field", "Group": "G", "Email": u + "@cairn.com.au",
            "TelegramChatID": "1", "Active": "SI", "HourlyRate": "50"}
US = [_u("ana", "Ana"), _u("beto", "Beto"), _u("carl", "Carl")]
auth.list_users = lambda *a, **k: US
auth.get_user = lambda u: next((x for x in US if x["User"] == u), {})
auth.fecha_ingreso = lambda u: None
C.is_configured = lambda: False
T.open_sessions = lambda *a, **k: {}
admin_digest.group_digest = lambda g: {}
AUI._ficha_usuario = lambda u, g: st.session_state.__setitem__("_FICHA", u["User"])
AUI._grupo_usuarios("G")
'''
au = AppTest.from_string(GU, default_timeout=120)
au.run()
chk("sin excepción", not au.exception, [e.value for e in au.exception][:1])
_orden = [r["User"] for r in au.dataframe[0].value.to_dict("records")] if au.dataframe else []
_k = au.dataframe[0].key if au.dataframe else ""
au2 = AppTest.from_string(GU, default_timeout=120)
au2.session_state["_PRE"] = {_k: {"selection": {"rows": [], "columns": [], "cells": [(1, "Name")]}}}
au2.run()
chk("la celda de la 2ª fila abre la ficha de %s" % (_orden[1:2] or ["?"])[0],
    len(_orden) == 3 and _ss(au2, "_gu_open") == _orden[1] and _ss(au2, "_FICHA") == _orden[1],
    (_orden, _ss(au2, "_gu_open"), _ss(au2, "_FICHA")))

print("\n3. Inventory: un toque en la celda abre ESE activo")
GI = PRE + r'''
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "G"})
from core import inventory_ui as IU, inventory as INV
_A = [{"ID": "ACT-2", "Name": "Taladro", "Category": "tools", "Status": INV.DISPONIBLE, "Active": "SI"},
      {"ID": "ACT-1", "Name": "Andamio", "Category": "tools", "Status": INV.DISPONIBLE, "Active": "SI"}]
INV.is_configured = lambda: True
INV.resumen = lambda g: {"n": 2, "por_estado": {}, "valor_actual": 0, "valor_compra": 0, "mant_vencido": 0}
INV.list_activos = lambda g, incluir_baja=False: _A
INV.categorias = lambda g: ["tools"]
INV.valor_actual = lambda a: 100.0
IU._reportes = lambda g: None
IU._categorias_expander = lambda g: None
IU._detalle = lambda g, aid: st.session_state.__setitem__("_DET", aid)
IU.render_inventario("G")
'''
ai = AppTest.from_string(GI, default_timeout=120)
ai.session_state["_PRE"] = {"inv_tbl": {"selection": {"rows": [], "columns": [], "cells": [(1, "Nombre")]}}}
ai.run()
chk("sin excepción", not ai.exception, [e.value for e in ai.exception][:1])
chk("la celda de la 2ª fila (por nombre: Andamio, Taladro) abre ACT-2 «Taladro»",
    _ss(ai, "_inv_open") == "ACT-2" and _ss(ai, "_DET") == "ACT-2", (_ss(ai, "_inv_open"), _ss(ai, "_DET")))

print("\n4. Library: un toque en la celda abre ESE documento")
GL = PRE + r'''
from core import library_ui as LU, projects_ui as PU
# (v604 · `_tabla` recibe las páginas «n/m» y projects_ui, y su clave lleva GENERACIÓN)
LU._tabla([{"ID": "LIB-1", "Title": "Manual A", "Section": "S", "Type": "manual", "Date": "2026-10-01"},
           {"ID": "LIB-2", "Title": "Manual B", "Section": "S", "Type": "manual", "Date": "2026-10-02"}], {}, PU)
'''
al = AppTest.from_string(GL, default_timeout=120)
al.session_state["_PRE"] = {"lib_tbl_0": {"selection": {"rows": [], "columns": [], "cells": [(1, "Title")]}}}
al.run()
chk("sin excepción", not al.exception, [e.value for e in al.exception][:1])
chk("la celda de la 2ª fila abre LIB-2", _ss(al, "_lib_open") == "LIB-2", _ss(al, "_lib_open"))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
