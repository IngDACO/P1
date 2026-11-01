# -*- coding: utf-8 -*-
"""v617 · LO VISTO VERIFICANDO v616 EN PRODUCCIÓN (28/10/2026, «Dale no dejes nada pendiente»):

  (1) ⚠️ un Enter en el importe GUARDÓ el recibo a medias (sin proveedor ni foto); el «Ir» del
      teclado del móvil hace lo mismo → BARRIDO: todo formulario de 2 campos o más, sin Enter
      (`enter_to_submit=False`); los de UN campo (la caja de «To-do», la fecha de pago de una
      nómina) lo conservan: ahí Enter es lo natural;
  (2) el importe de un recibo sin céntimos («$12» por 12.50) → con sus céntimos si los tiene;
  (3) mensajes de error en español sin traducir («Error leyendo: …», «Error creando grupo»,
      «… valores para … columnas») → en inglés y por `t()`.
Sin red ni hoja real.
"""
import ast
import glob
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

_W = {"text_input", "number_input", "text_area", "date_input", "time_input", "selectbox",
      "multiselect", "radio", "checkbox", "slider", "file_uploader", "color_picker", "toggle",
      "pills", "segmented_control", "data_editor"}


def formularios(src):
    """[(línea, nº de campos, enter_to_submit o None)] de cada `st.form` de una fuente."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.With):
            for it in n.items:
                c = it.context_expr
                if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "form":
                    _e = next((k.value for k in c.keywords if k.arg == "enter_to_submit"), None)
                    _ev = _e.value if isinstance(_e, ast.Constant) else (None if _e is None else "?")
                    nw = sum(1 for x in ast.walk(n) if isinstance(x, ast.Call)
                             and getattr(x.func, "attr", "") in _W)
                    out.append((c.lineno, nw, _ev))
    return out


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Enter no envía un formulario de varios campos (en TODA la app)")
# la sonda, validada con casos construidos (trampa 12)
_malo = formularios("import streamlit as st\nwith st.form('f'):\n    st.text_input('a')\n    st.number_input('b')\n")
_bueno = formularios("import streamlit as st\nwith st.form('f', enter_to_submit=False):\n    st.text_input('a')\n    st.number_input('b')\n")
_uno = formularios("import streamlit as st\nwith st.form('f'):\n    st.text_input('a')\n")
chk("la sonda VE un formulario de 2 campos que envía con Enter", _malo == [(2, 2, None)], _malo)
chk("...y reconoce el arreglado y el de un solo campo", _bueno == [(2, 2, False)] and _uno == [(2, 1, None)])
_mal, _todos = [], 0
for f in sorted(glob.glob(os.path.join(RAIZ, "core", "*.py"))) + [os.path.join(RAIZ, "app.py")]:
    for ln, nw, ev in formularios(open(f, encoding="utf-8").read()):
        _todos += 1
        if nw >= 2 and ev is not False:
            _mal.append("%s:%d (%d campos)" % (os.path.basename(f), ln, nw))
chk("⚠️ ningún formulario de 2 campos o más envía con Enter (%d formularios)" % _todos, not _mal, _mal)
chk("...el barrido vio los que debía (la app tiene ~30)", _todos >= 25, _todos)
_pu = open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
chk("el del recibo, en concreto (donde se vio)",
    'with st.form(f"{key_prefix}_add_{pid}{_sf}", clear_on_submit=False, enter_to_submit=False):' in _pu)
_td = formularios(open(os.path.join(RAIZ, "core", "tareas_ui.py"), encoding="utf-8").read())
chk("la caja de «To-do» (UN campo) conserva el Enter: es como se apunta una tarea", _td == [(_td[0][0], 1, None)]
    if _td else False, _td)

# AppTest: el formulario del recibo sale SIN Enter en el navegador (el proto que recibe)
APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import projects_ui as PU, expenses as E
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"items": [
    {"ID": "G-1", "Date": "2026-10-28", "Category": "Materials", "Amount": "12.5", "Supplier": "S1",
     "Description": "", "DriveID": "", "File": "", "CreatedBy": "campo000"},
    {"ID": "G-2", "Date": "2026-10-27", "Category": "Fuel", "Amount": "120", "Supplier": "S2",
     "Description": "", "DriveID": "", "File": "", "CreatedBy": "campo000"},
    {"ID": "G-3", "Date": "2026-10-26", "Category": "Fuel", "Amount": "1234.05", "Supplier": "S3",
     "Description": "", "DriveID": "", "File": "", "CreatedBy": "campo000"}]}
PU.render_expenses("PRJ-1", "cliente1", can_delete=False, key_prefix="fld", solo_de="campo000")
'''
at = AppTest.from_string(APP, default_timeout=60).run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])


def _forms(nodo, out):
    for ch in getattr(nodo, "children", {}).values() if isinstance(getattr(nodo, "children", None), dict) else []:
        p = getattr(ch, "proto", None)
        # (los nodos de AppTest no comparten «oneof»: se pregunta por el CAMPO `form`)
        if p is not None and "form" in getattr(getattr(p, "DESCRIPTOR", None), "fields_by_name", {}) \
                and p.HasField("form"):
            out.append(p.form)
        _forms(ch, out)
    return out


_fs = _forms(at.main, [])
chk("el formulario del recibo llega al navegador con `enter_to_submit` APAGADO",
    len(_fs) == 1 and _fs[0].enter_to_submit is False, [(f.form_id, f.enter_to_submit) for f in _fs])

# ═════════════════════════════════════════════════════════════════
sec("2. El importe, con sus céntimos")
_caps = " | ".join(c.value for c in at.caption)
chk("⚠️ 12.50 sale «\\$12.50» (salía «$12»)", r"Materials · \$12.50 · S1" in _caps, _caps[:300])
chk("...uno redondo, sin «.00» («\\$120»)", r"Fuel · \$120 · S2" in _caps)
chk("...y con miles y céntimos («\\$1,234.05»)", r"\$1,234.05 · S3" in _caps)

# ═════════════════════════════════════════════════════════════════
sec("3. Los mensajes de error, en inglés y traducibles")
_txt = {f: open(os.path.join(RAIZ, "core", f), encoding="utf-8").read()
        for f in ("ausencias.py", "auth.py", "credentials.py", "expenses.py", "correcciones.py")}
_viejos = [(f, s) for f, src in _txt.items() for s in ("Error leyendo", "Error creando grupo", "valores para")
           if s in src]
chk("⚠️ ni «Error leyendo» ni «Error creando grupo» ni «valores para … columnas»", not _viejos, _viejos)
chk("...sino `t(\"Error reading: {e}\", e=e)` en los cuatro módulos que leían",
    all('t("Error reading: {e}", e=e)' in _txt[f] for f in ("ausencias.py", "auth.py", "credentials.py", "expenses.py")))
chk("...y `t(\"Error creating the group: {e}\", e=e)`", 't("Error creating the group: {e}", e=e)' in _txt["auth.py"])

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
