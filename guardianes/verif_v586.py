"""v586 · LOS PARTES QUE NO MOVÍAN LA CURVA (decisión del usuario: «Dale»).

El 15/10 el usuario escribió dos partes de prueba y la curva no se movió. Causa: las dos
obras eran anteriores a v512 y no tenían plan de etapas, y la tarjeta de propuestas se
CALLABA (`return`) — el parte se guardaba y no pasaba nada, sin una palabra. Y aun con
plan, la app entendía 1 de 4 líneas de un parte y 1 de 7 del otro.

  1. ⚠️ Una obra sin plan (o con un catálogo anterior) lo DICE arriba de los partes, en la
     pantalla del campo —con un botón a «Progress»— y en la del admin.
  2. ⚠️ Un parte sin nada que confirmar lo dice: ya acreditado, fuera del plan, pendiente,
     no es avance, o «no reconocí nada».
  3. El vocabulario entiende las entregas y la caja de herramientas («got delivery», «got
     toolbox», «set up toolbox», «delivery of tools») y «set up tools» / «set up for rip
     out» como etapa; lo que no ha pasado («got delayed», «pushed back») queda pendiente;
     y quitar la caja es recoger (la contrapartida va ANTES que la logística).
  4. Finance → Expenses sin obras dice por dónde seguir: un botón «New project».

Todo EJECUTANDO (v378): el buscador contra el catálogo real y las pantallas con AppTest.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from core import stages as S, vocabulario as V, parte_propuestas as PP   # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


INST = S.plan_de("Installation", ())
RI = S.plan_de("Ripout + Installation", ())


def acts(txt, plan):
    return sorted({c["actividad"] for c in V.buscar(txt, plan)["candidatos"]})


def etapas(txt, plan):
    return sorted({(e["pista"], e["numero"]) for e in V.buscar(txt, plan)["etapas"]})


print("1. ⚠️ Los partes del usuario del 15/10, contra el plan de su tipo (EJECUTADO)")
chk("«got delivery» → recibir la entrega", acts("got delivery", INST) == ["Receive lift delivery"],
    acts("got delivery", INST))
chk("«got toolbox» → recibir la caja (el alias: «got» es relleno)",
    acts("got toolbox", INST) == ["Receive toolbox"], acts("got toolbox", INST))
chk("«set toolbox» / «Set up toolbox» → recibir la caja",
    acts("set toolbox", INST) == ["Receive toolbox"] == acts("Set up toolbox", INST))
chk("«survey shaft» sigue → Survey", acts("survey shaft", INST) == ["Survey (verify vs. existing shaft)"])
chk("«Got delivery of tools» (desmontaje + instalación) → la entrega de la caja",
    "Toolbox/gear delivery for installer" in acts("Got delivery of tools", RI), acts("Got delivery of tools", RI))
chk("«Set tools up» → la etapa Set Up (las dos en desmontaje + instalación)",
    etapas("Set tools up", RI) == [("install", 1), ("ripout", 0)] and etapas("Set tools up", INST) == [("install", 1)],
    (etapas("Set tools up", RI), etapas("Set tools up", INST)))
chk("«Set up for rip out» → la R0 del desmontaje", etapas("Set up for rip out", RI) == [("ripout", 0)])
chk("«Installed tirak» sigue → Mount tirak", acts("Installed tirak", RI) == ["Mount tirak"])
chk("«started rip out» NO propone nada (no dice qué se hizo; casaría con «started ripping out»)",
    not acts("started rip out", RI) and not etapas("started rip out", RI))
chk("…ni «Set lift up» (sin respaldo: se pregunta al usuario)",
    not acts("Set lift up", RI) and not etapas("Set lift up", RI))

print("\n2. ⚠️ Lo que NO tiene que proponer")
_b = V.buscar("bandsaw locked in a colleague's toolbox on another job", INST)
chk("«…locked in a colleague's toolbox» (un bloqueo del documento) no propone nada",
    not _b["candidatos"] and not _b["etapas"], [c["actividad"] for c in _b["candidatos"]])
_t = V.buscar("toolbox talk", INST)
chk("«toolbox talk» sigue siendo la charla, no la caja",
    not _t["candidatos"] and any("Safety talk" in n.get("motivo", "") for n in _t["no_avance"]))
for _f in ("Delivery got pushed back", "First delivery got delayed so second delivery got pushed back",
           "Delivery postponed"):
    _r = V.buscar(_f, INST)
    chk("«%s» → pendiente, no acreditado" % _f, not _r["candidatos"] and _r["pendientes"],
        ([c["actividad"] for c in _r["candidatos"]], _r["pendientes"]))
# ⚠️ La 1ª vuelta esperaba «Pack up»: era la medida con «toolbox» a secas, que se quitó por el
# bloqueo del documento. Lo que importa es el principio: quitar la caja NUNCA es recibirla.
_rm = "Removed 3x Kits and 1 toolbox"
chk("«%s» nunca propone RECIBIR la caja" % _rm,
    not ({"Receive toolbox", "Toolbox/gear delivery for installer"} & set(acts(_rm, INST) + acts(_rm, RI))),
    (acts(_rm, INST), acts(_rm, RI)))
chk("…y quitarla tiene contrapartida: recoger (Pack up)",
    V.CONTRAPARTIDA.get("Receive toolbox") == ["Pack up"]
    and V.CONTRAPARTIDA.get("Toolbox/gear delivery for installer") == ["Pack up"])
chk("«Removed the inex kit» → quitar el kit (su sinónimo)",
    acts("Removed the inex kit", INST) == ["Remove Inex kit components"], acts("Removed the inex kit", INST))
# ⚠️ romper_v586 enseñó que la de arriba NO ejercita el orden: «remove inex» es sinónimo y
# llega directo. Estas llegan a la LOGÍSTICA por su propio término dentro de una frase de
# quitar, y solo la contrapartida (que ahora va antes) las convierte en recoger.
chk("⚠️ «Took down the set up toolbox» → recoger, no RECIBIR la caja (la contrapartida va antes)",
    acts("Took down the set up toolbox", INST) == ["Pack up"], acts("Took down the set up toolbox", INST))
chk("⚠️ «Dismantled the receive inex kit» → quitar el kit, no recibirlo",
    acts("Dismantled the receive inex kit", INST) == ["Remove Inex kit components"],
    acts("Dismantled the receive inex kit", INST))
chk("«picked up delivery» sigue proponiendo la entrega",
    acts("picked up delivery", INST) == ["Receive lift delivery"])

print("\n3. ⚠️ Un parte sin nada que confirmar: QUÉ dice (la lógica)")
_p = PP.propuestas("Waiting on the scaffold all day", INST, {})
chk("«Waiting on the scaffold» no tiene nada que confirmar", not _p["hay_algo"])

# ═════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                          # noqa: E402

APP = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import clock, daily_log as DL, daily_log_ui as DLU
from core import projects as P, stage_progress as SP, stages as S
from core import auth as _A
_A.list_users = lambda *a, **k: [{"User": "campo000", "Name": "Field Test"}]
ss = st.session_state
PLAN = S.plan_de("Installation", ())
HOY = "2026-10-15"
TXT = ss.get("_txt", "got delivery")
DL.partes = lambda pid, autor=None, dia=None: [
    {"ID": "LOG-9101", "ProjectID": pid, "Author": "campo000", "Date": HOY,
     "Created": HOY + " 20:17:00", "Text": TXT}]
DL.dias_cubiertos = lambda pid: 1
DL.crear = lambda *a, **k: (True, "LOG-X")
clock.today = lambda grupo=None: _dt.date(2026, 10, 15)
_modo = ss.get("_plan", "ok")
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ job", "Type": "Installation",
                             "Kind": "internal" if _modo == "interno" else ""}
P.es_interno = lambda prj: _modo == "interno"
SP.plan_de_obra = lambda prj: [] if _modo in ("sin", "interno") else PLAN
SP.version_desfasada = lambda prj: "2026-01-01" if _modo == "vieja" else ""
SP.acreditado = lambda pid: dict(ss.get("_hecho", {}))
def _ir():
    ss["_fui"] = ss.get("_fui", 0) + 1
if ss.get("_vista") == "admin":
    DLU.render_admin("PRJ-9101", "cliente1", key_prefix="adm")
else:
    DLU.render_campo("PRJ-9101", "cliente1", "campo000", key_prefix="fld",
                     ir_avance=None if ss.get("_sin_boton") else _ir)
'''


def _app(**estado):
    a = AppTest.from_string(APP, default_timeout=90)
    for k, v in estado.items():
        a.session_state[k] = v
    return a.run()


def _txt(a):
    return " | ".join([str(x.value) for x in list(a.caption) + list(a.markdown) + list(a.info)])


def _bt(a, key):
    return next((b for b in a.button if b.key == key), None)


print("\n4. ⚠️ Obra SIN plan: el campo y el admin lo leen arriba (AppTest)")
at = _app(_plan="sin")
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ el campo lee que la obra no tiene plan (antes, nada)", "has no stage plan" in _txt(at), _txt(at)[:300])
chk("…y que el avance se marca en «Progress»", "mark what advanced in «Progress»" in _txt(at))
chk("…sin tarjeta de propuestas (no hay contra qué acreditar)", _bt(at, "fld_pp_LOG-9101_ok") is None)
_b = _bt(at, "fld_dl_ir_av_PRJ-9101")
chk("hay botón «Go to Progress»", _b is not None and "Go to Progress" in str(_b.label))
if _b is not None:
    _b.click()
    at.run()
    chk("…y lleva (su `on_click` corre)", at.session_state["_fui"] == 1 if "_fui" in at.session_state else False)
at = _app(_plan="sin", _sin_boton=True)
chk("sin a dónde ir, no hay botón (no se ofrece uno que no hace nada)", _bt(at, "fld_dl_ir_av_PRJ-9101") is None)
at = _app(_plan="sin", _vista="admin")
chk("⚠️ el admin también lo lee", "has no stage plan" in _txt(at) and "crew" in _txt(at), _txt(at)[:300])
at = _app(_plan="vieja")
chk("plan de un catálogo ANTERIOR: lo dice, con su versión", "older catalogue (2026-01-01)" in _txt(at), _txt(at)[:300])
at = _app(_plan="interno")
chk("una localización interna (sin avance) no dice nada de planes", "stage plan" not in _txt(at))
at = _app(_plan="ok")
chk("con plan, ningún aviso de plan", "stage plan" not in _txt(at), _txt(at)[:300])
chk("…y el parte con algo propone (la tarjeta sigue)", _bt(at, "fld_pp_LOG-9101_ok") is not None)

print("\n5. ⚠️ Con plan y nada que confirmar: lo DICE (antes, nada debajo)")
for txt, debe, q in (
        ("Waiting on the scaffold all day", "did not recognise any activity", "nada reconocido"),
        ("got delivery", "already credited", "todo ya acreditado"),
        ("Pendings:\ncube also needs to be installed", "still to do is not credited", "solo pendiente"),
        ("Site induction", "does not carry progress", "inducción: no es avance")):
    at = _app(_plan="ok", _txt=txt, _hecho={(1, "Receive lift delivery"): 100.0})
    chk("«%s» → %s" % (txt.replace("\n", " "), q), debe in _txt(at) and _bt(at, "fld_pp_LOG-9101_ok") is None,
        _txt(at)[-300:])

print("\n6. Finance → Expenses sin obras: por dónde seguir (AppTest)")
APP_GE = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "adm", "rol": "administrator", "grupo": "G"})
from core import projects_ui as PU, expenses as E
E.is_configured = lambda: True
E.group_expenses = lambda g: {"proyectos": [], "compras_grupo": []}
PU.render_group_expenses("G")
'''
try:
    from core import projects_ui as _PU
    _fn = next(n for n in ("render_group_expenses", "render_gastos_grupo") if hasattr(_PU, n))
except StopIteration:
    _fn = None
chk("la pantalla de Expenses del grupo existe con un nombre conocido", _fn is not None)
if _fn:
    at = AppTest.from_string(APP_GE.replace("render_group_expenses", _fn), default_timeout=60).run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    chk("⚠️ dice que los costes van a una obra y que se cree una", "create one first" in _txt(at), _txt(at))
    _b = _bt(at, "ge_vacio_nueva")
    chk("botón «New project»", _b is not None and "New project" in str(_b.label))
    if _b is not None:
        _b.click()
        at.run()
        chk("…que lleva a Projects", tuple(at.session_state["_admin_nav_pending"]) == ("proyectos", "📊 Proyectos")
            if "_admin_nav_pending" in at.session_state else False)

print("\n7. `libro_foto`: el libro de SOLO LECTURA de los ensayos (desde que se borraron las obras)")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libro_foto                                                 # noqa: E402
from core import timeclock as _TC                                 # noqa: E402
_real = _TC._abrir
_L = libro_foto.Libro("ZZ-LIBRO", {"Sheet1": [["Name", "ProjectID"], ["Ana", "PRJ-1"]],
                                    "Bob's": [["ID", "Amount"], ["G-1", "12.5"], ["G-2"]]})
chk("lee como gspread: registros en texto con `numericise_ignore=['all']`",
    _L.worksheet("Bob's").get_all_records(numericise_ignore=["all"]) == [{"ID": "G-1", "Amount": "12.5"},
                                                                         {"ID": "G-2", "Amount": ""}])
chk("…y numéricos sin él", _L.worksheet("Bob's").get_all_records()[0]["Amount"] == 12.5)
from gspread.utils import absolute_range_name                     # noqa: E402
_vb = _L.values_batch_get([absolute_range_name("Bob's"), "'Sheet1'!1:1"])["valueRanges"]
chk("`values_batch_get` con el nombre absoluto (comillas dobladas) y con la cabecera sola",
    _vb[0]["values"][2] == ["G-2"] and _vb[1]["values"] == [["Name", "ProjectID"]]
    and _vb[0]["range"].startswith("'Bob''s'!"), _vb)
chk("`sheet1`, `row_values`, `col_values`, `cell`",
    _L.sheet1.title == "Sheet1" and _L.sheet1.row_values(1) == ["Name", "ProjectID"]
    and _L.sheet1.col_values(2) == ["ProjectID", "PRJ-1"] and _L.sheet1.cell(2, 1).value == "Ana")
try:
    _L.sheet1.append_row(["x"])
    _esc = True
except AttributeError:
    _esc = False
chk("⚠️ una ESCRITURA falla y queda APUNTADA (un `try` del ensayo no la esconde)",
    not _esc and _L.intentos == ["Sheet1.append_row"], _L.intentos)
chk("`hasattr` da False, no revienta", hasattr(_L.sheet1, "update_cell") is False)
import tempfile, json as _json                                    # noqa: E401,E402
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as _f:
    _json.dump({"libro": "ZZ-LIBRO", "hojas": {"Sheet1": [["Name"], ["Ana"]]}}, _f)
_li = libro_foto.instalar(_f.name)
chk("instalado: ese libro sale de la foto", _TC._abrir("ZZ-LIBRO") is _li)
libro_foto.quitar()
os.unlink(_f.name)
chk("…y `quitar` deja el `_abrir` real", _TC._abrir is _real)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
