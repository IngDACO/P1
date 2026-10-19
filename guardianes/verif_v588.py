"""v588 · TOOLS → HOME, PROBADA (decisión del usuario: «Dale con todo»).

  1. La tarjeta ENTERA es el botón (antes un «Open →» pequeño) — elementos activos.
  2. Por ANCHO (`T.por_fila`): tres por fila, dos bajo 700 px. Medido en producción a 846 px
     con el menú: tres de 136 px partían «Plumb line» y «Pre- / Start» y cada tarjeta medía
     distinto (228 · 225 · 183, los «Open →» a alturas distintas). Medido en una mini-app con
     el CSS nuevo: 2 × 215 px a 446, 2 × 164 en el móvil, 3 × 401 a 1300, la fila igualada.
  3. Llenar: cada tarjeta dice su último uso («Last used DD/MM/YYYY · obra») y la del
     Pre-Start, los de hoy.
  4. El Pre-Start con su rama: una herramienta nueva en el menú SIN rama salía como Pre-Start.

AppTest y el motor con las fuentes sustituidas: no se toca la hoja.
"""
import datetime as dt
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


print("1. El motor: el último uso por herramienta y los Pre-Start de hoy")
from core import toolruns as TR, prestart as PS, clock    # noqa: E402
_otr, _ops, _oc = TR._records, PS._records, clock.today
try:
    TR._records = lambda: [
        {"Tool": "plomada", "Group": "cliente1", "Date": "2026-10-12 09:00", "ProjectID": "PRJ-1"},
        {"Tool": "plomada", "Group": "cliente1", "Date": "2026-10-14 11:00", "ProjectID": "PRJ-2"},
        {"Tool": "plomada", "Group": "OTRO", "Date": "2026-10-18 11:00", "ProjectID": "PRJ-9"},
        {"Tool": "rieles", "Group": "Cliente1 ", "Date": "2026-09-01 08:00", "ProjectID": "PRJ-3"}]
    u = TR.ultimos_por_herramienta("cliente1")
    chk("el MÁS RECIENTE de cada herramienta del grupo (no el de otro grupo)",
        u["plomada"]["ProjectID"] == "PRJ-2" and u["rieles"]["ProjectID"] == "PRJ-3" and "survey" not in u, u)
    clock.today = lambda g=None: dt.date(2026, 10, 19)
    PS._records = lambda: [{"Group": "cliente1", "Date": "2026-10-19"}, {"Group": "cliente1", "Date": "2026-10-18"},
                           {"Group": "OTRO", "Date": "2026-10-19"}]
    chk("los Pre-Start de HOY del grupo", len(PS.de_hoy("cliente1")) == 1)
finally:
    TR._records, PS._records, clock.today = _otr, _ops, _oc

print("\n2. ⚠️ La portada (AppTest): tarjetas enteras, con su uso, y por ancho")
G = r'''
import datetime as dt
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": st.session_state.get("_ROL", "administrator"),
                                     "grupo": "cliente1"})
from core import home_ui as H, toolruns as TR, prestart as PS, projects as P
if st.session_state.get("_FALLA"):
    def _f(g):
        raise RuntimeError("hoja caída")
    TR.ultimos_por_herramienta = _f
else:
    TR.ultimos_por_herramienta = lambda g: {"plomada": {"Date": "2026-10-12 09:00", "ProjectID": "PRJ-1"}}
PS.de_hoy = lambda g: [{}]
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ Tower — Lift 1"}
st.session_state.setdefault("adm_herr_sub", st.session_state.get("_SUB", "🧰 Inicio"))
import core.prestart_ui as PSU
PSU.render_prestart_tab = lambda: st.write("PRESTART-PINTADO")
H._seccion_herramientas("cliente1")
'''


def _app(**ss):
    a = AppTest.from_string(G, default_timeout=90)
    for k, v in ss.items():
        a.session_state[k] = v
    return a.run()


def _bts(a):
    return {b.key: str(b.label) for b in a.button if str(b.key or "").startswith("cpxtool_")}


at = _app()
b = _bts(at)
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ seis tarjetas-botón `cpxtool_*` (la tarjeta ENTERA, no un «Open →»)",
    sorted(b) == sorted("cpxtool_" + k for k in ("survey", "plomada", "rieles", "buffers", "belting", "prestart"))
    and not [x for x in at.button if str(x.key or "").startswith("hubherr_")], sorted(b))
chk("cada una: título · para qué sirve · su uso (tres bloques)",
    all(v.count("\n\n") == 2 for v in b.values()), list(b.values())[:1])
chk("⚠️ el último uso, con fecha DD/MM/YYYY y la obra",
    "Last used 12/10/2026 · ZZ Tower — Lift 1" in b.get("cpxtool_plomada", ""), b.get("cpxtool_plomada"))
chk("…sin uso, «Not used yet»", b.get("cpxtool_survey", "").endswith("Not used yet"))
chk("el Pre-Start dice los de hoy («1 done today»)", b.get("cpxtool_prestart", "").endswith("1 done today"))
_css = " ".join(str(m.value) for m in at.markdown)
chk("⚠️ por ancho: el bloque con clave y la regla de tres por fila / dos bajo 700 px",
    ".st-key-cpx_herr_hub" in _css and "@container (max-width:700px)" in _css)
at.button(key="cpxtool_rieles").click()
at.run()
chk("tocar la tarjeta lleva a su herramienta",
    "_admin_nav_pending" in at.session_state
    and tuple(at.session_state["_admin_nav_pending"]) == ("herramientas", "✂️ Rieles")
    or (at.session_state["adm_herr_sub"] == "✂️ Rieles" if "adm_herr_sub" in at.session_state else False))
at = _app(_FALLA=True)
chk("si el registro de cálculos falla, la portada sigue (sin pie de uso)",
    not at.exception and _bts(at).get("cpxtool_plomada", "").endswith("Not used yet"))
at = _app(_ROL="field")
chk("el campo ve CINCO (su Pre-Start va aparte)", "cpxtool_prestart" not in _bts(at) and len(_bts(at)) == 5,
    sorted(_bts(at)))

print("\n3. El Pre-Start con su rama")
at = _app(_SUB="🦺 Pre-Start")
chk("«Pre-Start» pinta el Pre-Start", any("PRESTART-PINTADO" in str(m.value) for m in at.markdown))
HU = io.open(os.path.join(RAIZ, "core", "home_ui.py"), encoding="utf-8").read()
_f = HU[HU.index("def _seccion_herramientas"):HU.index("# ── HOME")]
chk("⚠️ y lo desconocido lo DICE (antes el `else` era el Pre-Start)",
    'elif sub == "🦺 Pre-Start":' in _f and "This Tools section does not exist" in _f.split("else:")[-1])

print("\n4. El estilo de la tarjeta (estático)")
TH = io.open(os.path.join(RAIZ, "core", "theme.py"), encoding="utf-8").read()
chk("la tarjeta `cpxtool_*` con su borde y alto mínimo", '[class*="st-key-cpxtool_"] button {{' in TH
    and "min-height: 140px" in TH)
chk("⚠️ la fila se iguala (la cadena de la columna a `height:100%`)",
    '.st-key-cpx_herr_hub [data-testid="stColumn"] [data-testid="stButton"] {{ height: 100%; }}' in TH)
_tj = TH[TH.index("TARJETA DE HERRAMIENTA"):TH.index("TOGGLE SEGMENTADO")]
_r1 = _tj[_tj.index('button p:first-child {{'):].split("}}")[0]
_r3 = _tj[_tj.index('button p:nth-child(3) {{'):].split("}}")[0]
chk("el título no se parte (`nowrap`); el uso puede ir en dos líneas (sin `nowrap`)",
    "white-space: nowrap" in _r1 and "nowrap" not in _r3 and "line-height: 1.3" in _r3, (_r1, _r3))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
