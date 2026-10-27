# -*- coding: utf-8 -*-
"""v615 · LA LISTA DE PENDIENTES DE LA OBRA (`core/tareas.py` + `core/tareas_ui.py`) — decisión
del usuario (28/10/2026): una lista sencilla en el proyecto donde el campo apunta tareas y las marca
como hechas. Y, preguntado: 1) UNA lista por obra, compartida; 2) marca/desmarca cualquiera de la
obra, borra solo quien la escribió (o la oficina); 3) la oficina también apunta; 4) nada más.

Lo que protege, SIN la hoja real (una hoja sustituida en memoria; el módulo y la pantalla, REALES):
  (a) apuntar: el texto limpio, sin vacíos ni larguísimos, sin repetir una PENDIENTE igual; con
      ID `TSK-####`, quién y cuándo; la caja nace vacía tras guardar y CONSERVA lo escrito si falla;
  (b) marcar / desmarcar: quién y cuándo; un doble toque no escribe dos veces;
  (c) borrar OCULTA (`Active=NO`, quién y cuándo); solo el autor o la oficina — y lo decide el
      módulo, no solo la pantalla;
  (d) la lista es de la OBRA: otra obra no la ve;
  (e) al borrar la obra se va su lista (como los partes, v516); la hoja va en el LOTE;
  (f) las dos pantallas: «To-do» en la obra del campo (detrás del parte) y en el detalle de la
      oficina (al final), cada una con su permiso.
"""
import ast
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

from core import hojas as H                                       # noqa: E402
from core import tareas as T                                      # noqa: E402

FAKE = r'''
class HojaFalsa:
    """La hoja `Tasks` en memoria, con la forma de gspread que usa `tareas`."""
    def __init__(self, cab):
        self.cab, self.filas, self.escrituras = list(cab), [], 0
    def get_all_records(self, **k):
        return [dict(zip(self.cab, f + [""] * (len(self.cab) - len(f)))) for f in self.filas]
    def append_row(self, fila, value_input_option=None):
        assert value_input_option == "RAW" and len(fila) == len(self.cab), fila
        self.filas.append([str(x) for x in fila]); self.escrituras += 1
    def batch_update(self, lote, value_input_option=None):
        assert value_input_option == "RAW"
        import re
        for d in lote:
            col, fila = re.match(r"([A-Z]+)(\d+)$", d["range"]).groups()
            c = 0
            for ch in col:
                c = c * 26 + ord(ch) - 64
            self.filas[int(fila) - 2][c - 1] = str(d["values"][0][0])
        self.escrituras += 1
    def delete_rows(self, n):
        del self.filas[n - 2]; self.escrituras += 1
'''
exec(FAKE)

# ═════════════════════════════════════════════════════════════════
sec("1. El módulo (la hoja sustituida)")
_w = HojaFalsa(T.HEADERS)                                          # noqa: F821
_o = (T._ws, T._records, T._invalidate, H.siguiente_id_libre)
T._ws = lambda: _w
T._records = lambda: _w.get_all_records()
T._invalidate = lambda: None
H.siguiente_id_libre = lambda pref, n, propia=None, ancho=4: "%s%04d" % (pref, n + 1)
try:
    ok1, id1 = T.crear("PRJ-1", "cliente1", "  Pick up   the keys ", "campo000")
    chk("apuntar: ID `TSK-0001`, el texto limpio, quién y cuándo",
        ok1 and id1 == "TSK-0001" and _w.filas[0][:5] == ["TSK-0001", "cliente1", "PRJ-1", "Pick up the keys", "campo000"]
        and len(_w.filas[0][5]) == 19, _w.filas)
    chk("...vacía, no", T.crear("PRJ-1", "cliente1", "   ", "campo000")[0] is False)
    chk("...larguísima, no (una tarea es una línea)", T.crear("PRJ-1", "cliente1", "x" * (T.MAX_TEXTO + 1), "c")[0] is False)
    _e0 = _w.escrituras
    okd, md = T.crear("PRJ-1", "cliente1", "pick UP the keys", "helper 1")
    chk("⚠️ una PENDIENTE igual no se repite (dos personas, o un doble toque)",
        okd is False and "already on the list" in md and _w.escrituras == _e0, md)
    chk("...pero en OTRA obra sí (la lista es de la obra)", T.crear("PRJ-2", "cliente1", "Pick up the keys", "c")[0])
    T.crear("PRJ-1", "cliente1", "Order the brackets", "helper 1")
    chk("las pendientes, la ÚLTIMA apuntada primero (justo bajo la caja)",
        [r["ID"] for r in T.pendientes("PRJ-1")] == ["TSK-0003", "TSK-0001"], [r["ID"] for r in T.pendientes("PRJ-1")])
    chk("...y otra obra no ve nada de esta", [r["ID"] for r in T.pendientes("PRJ-2")] == ["TSK-0002"])

    okm, _m = T.marcar("TSK-0001", "PRJ-1", True, "helper 1")
    _f = _w.filas[0]
    chk("marcar: hecha, QUIÉN y CUÁNDO", okm and _f[6:8] == ["YES", "helper 1"] and len(_f[8]) == 19, _f)
    _e1 = _w.escrituras
    chk("...un doble toque no escribe otra vez (y dice que sí)", T.marcar("TSK-0001", "PRJ-1", True, "x")[0]
        and _w.escrituras == _e1)
    chk("...y pasa a «hechas»", [r["ID"] for r in T.hechas("PRJ-1")] == ["TSK-0001"]
        and [r["ID"] for r in T.pendientes("PRJ-1")] == ["TSK-0003"])
    chk("con la de antes HECHA, apuntarla otra vez sí se puede (es otra vez trabajo)",
        T.crear("PRJ-1", "cliente1", "Pick up the keys", "campo000")[0])
    okq, _m = T.marcar("TSK-0001", "PRJ-1", False, "campo000")
    chk("desmarcar: vuelve a pendiente y se limpia quién/cuándo", okq and _w.filas[0][6:9] == ["", "", ""], _w.filas[0])
    chk("marcar una tarea de OTRA obra (el ID no casa con la obra): no", T.marcar("TSK-0002", "PRJ-1", True, "c")[0] is False)

    okb, mb = T.borrar("TSK-0003", "PRJ-1", "campo000", False)
    chk("⚠️ borrar la de OTRO siendo del campo: no (lo decide el módulo)",
        okb is False and "Only the person" in mb and _w.filas[2][9] == "", mb)
    okc, _m = T.borrar("TSK-0003", "PRJ-1", "helper 1", False)
    _f3 = _w.filas[2]
    chk("...la suya, sí: OCULTA (`Active=NO`) con quién y cuándo — la fila sigue",
        okc and _f3[9:11] == ["NO", "helper 1"] and len(_f3[11]) == 19 and len(_w.filas) == 4, _f3)
    chk("...y desaparece de la lista", "TSK-0003" not in [r["ID"] for r in T.de_obra("PRJ-1")])
    chk("la oficina borra cualquiera", T.borrar("TSK-0004", "PRJ-1", "Admin2", True)[0])
    chk("una borrada no se marca", T.marcar("TSK-0003", "PRJ-1", True, "x")[0] is False)
    chk("al borrar la OBRA se va su lista (y solo la suya)",
        T.borrar_de_obra("PRJ-1") == 3 and [f[2] for f in _w.filas] == ["PRJ-2"], [f[2] for f in _w.filas])
    T._ws = lambda: None
    chk("sin hoja: dice que no (y no revienta)", T.crear("PRJ-1", "g", "x", "u")[0] is False
        and T.marcar("TSK-1", "PRJ-1", True, "u")[0] is False and T.borrar_de_obra("PRJ-1") == 0)
finally:
    T._ws, T._records, T._invalidate, H.siguiente_id_libre = _o

# ═════════════════════════════════════════════════════════════════
sec("2. Lo que la rodea")
chk("⚠️ `Tasks` va en el LOTE (su lector va sin cabeceras: fuera, vacía para siempre)", T.SHEET in H.HOJAS_LECTURA)
chk("la hoja es del libro del CLIENTE (no global)", T.SHEET.lower() not in __import__("core.timeclock", fromlist=["x"]).SHEETS_GLOBALES)
_pj = open(os.path.join(RAIZ, "core", "projects.py"), encoding="utf-8").read()
_dp = next(n for n in ast.walk(ast.parse(_pj)) if isinstance(n, ast.FunctionDef) and n.name == "delete_project")
# ⚠️ La llamada del módulo de TAREAS (el alias con que se importa `core.tareas`), no «alguna
# `borrar_de_obra`»: la de los partes la satisfaría igual (el escape que tuvo verif_v516 en esta
# misma versión, trampa nº2).
_alias_ta = {(a.asname or a.name) for n in ast.walk(_dp) if isinstance(n, ast.ImportFrom)
             and n.module == "core" for a in n.names if a.name == "tareas"}
chk("borrar la obra se lleva su lista (`delete_project` → `tareas.borrar_de_obra`)",
    bool(_alias_ta) and any(isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "borrar_de_obra"
                            and getattr(c.func.value, "id", "") in _alias_ta for c in ast.walk(_dp)),
    _alias_ta)
_pu = open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_apu = ast.parse(_pu)
_listas = [[e.value for e in n.value.elts if isinstance(e, ast.Constant)] for n in ast.walk(_apu)
           if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "_opts" for x in n.targets)
           and isinstance(n.value, ast.List)]
_campo = next((l for l in _listas if "🏗 Avance" in l), [])
chk("el campo tiene «To-do» DETRÁS del parte", _campo[1:3] == ["📝 Parte", "✅ Tareas"], _campo)
chk("el detalle de la oficina, al final (las 4 de siempre, en su sitio)",
    '["📊 Estado", "✏️ Datos", "💰 Costos", "📎 Archivos", "✅ Tareas"]' in _pu)
_ramas = [ast.get_source_segment(_pu, n) or "" for n in ast.walk(_apu)
          if isinstance(n, ast.If) and ast.unparse(n.test) == "_sec == '✅ Tareas'"]
_cuerpos = [ast.unparse(n) for n in ast.walk(_apu)
            if isinstance(n, ast.If) and ast.unparse(n.test) == "_sec == '✅ Tareas'"]
chk("dos ramas la atienden: el campo SIN permiso de oficina, la oficina CON él",
    len(_cuerpos) == 2 and sum("gestor=False" in c.split("elif")[0] for c in _cuerpos) == 1
    and sum("gestor=True" in c.split("elif")[0] for c in _cuerpos) == 1, len(_cuerpos))

# ═════════════════════════════════════════════════════════════════
sec("3. La pantalla (AppTest, con el módulo REAL y la hoja sustituida)")
APP = FAKE + r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": ss.get("_u", "campo000"), "nombre": "X",
                                     "rol": ss.get("_rol", "field"), "grupo": "cliente1"})
from core import auth, flash, hojas, tareas as T, tareas_ui as TU
if "_hoja" not in ss:
    ss["_hoja"] = HojaFalsa(T.HEADERS)
T._ws = lambda: ss["_hoja"]
T._records = lambda: ss["_hoja"].get_all_records()
T._invalidate = lambda: None
T.is_configured = lambda: True
hojas.siguiente_id_libre = lambda pref, n, propia=None, ancho=4: "%s%04d" % (pref, n + 1)
auth.list_users = lambda grupo=None: [{"User": "campo000", "Name": "Carlos Campo"},
                                      {"User": "helper 1", "Name": "Helena Uno"},
                                      {"User": "Admin2", "Name": "Bobo"}]
flash.mostrar()
TU.render("PRJ-9001", "cliente1", ss["auth"]["usuario"], gestor=bool(ss.get("_gestor")),
          key_prefix=ss.get("_kp", "fld"))
'''


def _w_(lista, key):
    return next((x for x in lista if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


def _alta(at, texto, gen):
    _w_(at.text_input, "fld_td_new_PRJ-9001_%d" % gen).input(texto)
    _w_(at.button, "fld_td_add_PRJ-9001").click()
    at.run()


at = AppTest.from_string(APP, default_timeout=90).run()
chk("se pinta sin excepción, vacía, con su caja", not at.exception
    and _w_(at.text_input, "fld_td_new_PRJ-9001_0") is not None
    and any("Nothing on the list yet" in x for x in _todo(at)), [e.value for e in at.exception][:1])
_alta(at, "Pick up the *keys* $5", 0)
_h = at.session_state["_hoja"]
chk("apuntar desde la caja: una fila, del autor de la sesión, y «Task added.»",
    len(_h.filas) == 1 and _h.filas[0][3:5] == ["Pick up the *keys* $5", "campo000"]
    and any("Task added." in x for x in _todo(at)), (_h.filas, _todo(at)[-3:]))
chk("...la caja nace VACÍA (otra generación)", _w_(at.text_input, "fld_td_new_PRJ-9001_1") is not None
    and _w_(at.text_input, "fld_td_new_PRJ-9001_1").value == "")
_cb = _w_(at.checkbox, "fld_tdp_PRJ-9001_TSK-0001")
chk("⚠️ el texto de la persona, ESCAPADO (ni cursiva ni fórmula)",
    _cb is not None and _cb.label == r"Pick up the \*keys\* \$5", _cb and _cb.label)
chk("...con quién la apuntó, por su NOMBRE (no el login) y la fecha DD/MM/YYYY",
    any(x.startswith("Added by Carlos Campo · ") and x[-10:-8].isdigit() and x[-5] == "/" for x in _todo(at)), _todo(at))
_alta(at, "pick up the *KEYS*   $5", 1)
chk("⚠️ la misma, otra vez: no se repite, lo dice, y lo escrito SE QUEDA en la caja",
    len(at.session_state["_hoja"].filas) == 1 and any("already on the list" in x for x in _todo(at))
    and _w_(at.text_input, "fld_td_new_PRJ-9001_1").value == "pick up the *KEYS*   $5", _todo(at)[-3:])
_w_(at.text_input, "fld_td_new_PRJ-9001_1").input("Order the brackets")
_w_(at.button, "fld_td_add_PRJ-9001").click()
at.run()
chk("dos pendientes, la última apuntada primero",
    [c.key for c in at.checkbox if c.key.startswith("fld_tdp_")] == ["fld_tdp_PRJ-9001_TSK-0002", "fld_tdp_PRJ-9001_TSK-0001"],
    [c.key for c in at.checkbox])
_w_(at.checkbox, "fld_tdp_PRJ-9001_TSK-0001").check()
at.run()
_f = at.session_state["_hoja"].filas[0]
chk("marcarla: hecha por quien la marcó, y baja a «Done (1)»",
    _f[6:8] == ["YES", "campo000"] and _w_(at.checkbox, "fld_tdd_PRJ-9001_TSK-0001") is not None
    and _w_(at.checkbox, "fld_tdp_PRJ-9001_TSK-0001") is None
    and any("Done (1)" in str(e.label) for e in list(at.expander) + list(at.status)), _f)
_d = _w_(at.checkbox, "fld_tdd_PRJ-9001_TSK-0001")
chk("...tachada, marcada y con quién y cuándo (por su nombre)",
    _d.value is True and _d.label.startswith("~~") and _d.label.endswith("~~")
    and any(x.startswith("Done by Carlos Campo · ") for x in _todo(at)), (_d.label, _todo(at)))
chk("el recuento: «1 pending · 1 done»", any("1 pending · 1 done" in x for x in _todo(at)))
_d.uncheck()
at.run()
chk("desmarcarla: vuelve a pendientes", at.session_state["_hoja"].filas[0][6] == ""
    and _w_(at.checkbox, "fld_tdp_PRJ-9001_TSK-0001") is not None, at.session_state["_hoja"].filas[0])
# borrar: el campo, solo las suyas — la de otra persona ni se le ofrece
at.session_state["_hoja"].filas.append(["TSK-0003", "cliente1", "PRJ-9001", "Helena's task", "helper 1",
                                        "2026-10-28 09:00:00", "", "", "", "", "", ""])
at.run()
_sd = _w_(at.selectbox, "fld_td_del_PRJ-9001")
chk("⚠️ «Delete a task» le ofrece al campo SOLO las que escribió",
    _sd is not None and sorted(_sd.options) == ["Order the brackets", "Pick up the *keys* $5"], _sd and _sd.options)
_w_(at.button, "fld_td_delb_PRJ-9001").click()
at.run()
chk("«Delete» sin elegir: lo dice y no borra", any("Choose the task to delete first" in x for x in _todo(at))
    and all(f[9] == "" for f in at.session_state["_hoja"].filas))
_w_(at.selectbox, "fld_td_del_PRJ-9001").set_value("TSK-0002")
at.run()
_w_(at.button, "fld_td_delb_PRJ-9001").click()
at.run()
chk("borrar la suya: «Task deleted.», oculta (la fila sigue) y fuera de la lista",
    at.session_state["_hoja"].filas[1][9] == "NO" and any("Task deleted." in x for x in _todo(at))
    and _w_(at.checkbox, "fld_tdp_PRJ-9001_TSK-0002") is None, _todo(at)[-3:])
# la oficina: apunta y borra cualquiera
at2 = AppTest.from_string(APP, default_timeout=90)
at2.session_state["_u"], at2.session_state["_rol"] = "Admin2", "administrator"
at2.session_state["_gestor"], at2.session_state["_kp"] = True, "adm"
at2.session_state["_hoja"] = at.session_state["_hoja"]
at2.run()
_sd2 = _w_(at2.selectbox, "adm_td_del_PRJ-9001")
chk("la oficina ve la MISMA lista y puede borrar cualquiera (también la de Helena)",
    # (AppTest da las opciones YA formateadas: el texto, no el ID)
    _sd2 is not None and "Helena's task" in _sd2.options and _w_(at2.checkbox, "adm_tdp_PRJ-9001_TSK-0003") is not None,
    _sd2 and _sd2.options)
_w_(at2.text_input, "adm_td_new_PRJ-9001_0").input("Send the induction to the new helper")
_w_(at2.button, "adm_td_add_PRJ-9001").click()
at2.run()
chk("...y apunta (la tarea es de quien la escribió: la oficina)",
    at2.session_state["_hoja"].filas[-1][3:5] == ["Send the induction to the new helper", "Admin2"])
# una petición de OTRA obra (se cambió de obra con algo a medias) se tira, no se aplica a esta
at3 = AppTest.from_string(APP, default_timeout=90)
at3.session_state["_hoja"] = HojaFalsa(T.HEADERS)                    # noqa: F821
at3.session_state["_td_pet"] = {"accion": "alta", "pid": "PRJ-OTRA", "kp": "fld", "texto": "No es de aquí"}
at3.run()
chk("⚠️ una petición de OTRA obra no se aplica a la que se ve (y se tira)",
    at3.session_state["_hoja"].filas == [] and "_td_pet" not in at3.session_state, at3.session_state["_hoja"].filas)
_tu = ast.parse(open(os.path.join(RAIZ, "core", "tareas_ui.py"), encoding="utf-8").read())
_exps = [n for n in ast.walk(_tu) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "expander"]
chk("los desplegables con controles, CON clave (trampa 35: sin ella se cierran con cada aviso)",
    len(_exps) == 2 and all(any(k.arg == "key" for k in n.keywords) for n in _exps), len(_exps))
chk("ninguna excepción en todo el recorrido", not at.exception and not at2.exception,
    [e.value for e in list(at.exception) + list(at2.exception)][:1])

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
