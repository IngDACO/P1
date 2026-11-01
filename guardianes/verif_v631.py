# -*- coding: utf-8 -*-
"""v631 · LO QUE DESTAPARON LAS PRUEBAS REALES DE v630 (02/11/2026, «Ok dale»).

  (1) ⚠️ El asistente admitía no saber qué es LFKK y aun así decía que era «el del primer riel»: la regla general
      no bastó. Además, parte de lo que se iba a marcar como «sin definir» SÍ lo dice la app en sus pantallas →
      bloque de siglas con lo que dice la app, comparado aquí con cada pantalla y con el motor;
      solo LFKK y LFGK quedan sin definición, y lo dice.
  (2) ⚠️ Decía que el atajo de Timeclock registra la baja: solo lleva a My absences.
  (3) ⚠️ «Switch project» a 64 px: el selector vivía en media columna de una columna.
  (4) ⚠️ El anexo de firmas: «Proyecto» en español y la fecha en ISO, pegado a un documento en inglés y DD/MM/YYYY.
Sin red: lo que afirma la guía se comprueba contra el código, no contra la propia guía (trampas 1 y 42).
"""
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core import chat_agent as CA, home_ui as H, prestart_pdf as PPDF, rail_cut as RC   # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


P = CA.SYSTEM_PROMPT
_ini = P.index("## SIGLAS DE LAS HERRAMIENTAS")
_fin = P.index("## CONFIDENCIALIDAD")
B = P[_ini:_fin]
B_L = re.sub(r"\s+", " ", B)

# ─────────────────────────────────────────────────────────────────────────────
sec("1. Lo que dice el bloque de cada sigla es lo que dice su pantalla")
for pantalla, rel, lineas in (
        ("RZ, RO = car rails · RF, RB = counterweight rails · in mm, measured on site.", "core/rail_cut_ui.py",
         ("- **RZ, RO:** rieles de cabina, en mm, medidos en obra", "- **RF, RB:** rieles de contrapeso, en mm, medidos en obra")),
        ("HKP (mm) — car sticker ↔ buffer serving the 1st level", "core/buffer_cut_ui.py",
         ("- **HKP:** car sticker ↔ buffer serving the 1st level",)),
        ("you enter the actual **HKPR** measured on each buffer", "core/buffer_cut_ui.py",
         ("- **HKPR:** esa misma distancia, la real, medida en obra en cada buffer",)),
        ("HQ — travel height (mm)", "core/belting_ui.py", ("- **HQ:** travel height",)),
        ("HGP — design striker↔buffer (mm)", "core/belting_ui.py", ("- **HGP:** striker ↔ buffer: el valor de diseño",)),
        ("HGPR — ACTUAL striker↔buffer distance on the counterweight, per lift (mm)", "core/belting_ui.py",
         ("- **HGPR:** esa misma distancia, la real, en el contrapeso y por elevador",)),
        ("how far to lower the car below the FFL of the top floor to install the belts", "core/belting_ui.py",
         ("- **DSTS:** cuánto bajar la cabina respecto al FFL del piso más alto para instalar los belts",))):
    _src = leer(rel)
    chk("la pantalla sigue diciendo «%s»" % pantalla[:58], pantalla in _src)
    for ln in lineas:
        chk("...y la guía: %s" % ln[:62], ln in B_L, ln)

# Las siglas que las herramientas leen del plano, sacadas de `plan_data`: una nueva sin explicar = rojo.
_pd = leer("core/plan_data.py")
_leidas = set(re.findall(r'\("([A-Z]{2,5})", _v\("', _pd))
chk("se leyeron las siglas del plano en plan_data", {"LFKK", "LFGK", "HKP", "HQ", "HGP"} <= _leidas, _leidas)
chk("⚠️ cada sigla que se lee del plano está en el bloque", all("**%s" % s in B for s in _leidas),
    [s for s in _leidas if "**%s" % s not in B])

# ─────────────────────────────────────────────────────────────────────────────
sec("2. LFKK y LFGK: lo que dice la guía es lo que hace el motor")
_a = RC.compute_case1(1000.0, 2000.0, 1, 0, [10.0])["elevadores"][0]
_b = RC.compute_case1(1500.0, 2000.0, 1, 0, [10.0])["elevadores"][0]
_c = RC.compute_case1(1000.0, 2500.0, 1, 0, [10.0])["elevadores"][0]
chk("Case 1: LFKK solo mueve el corte de cabina", _b["CutRC"] != _a["CutRC"] and _b["CutRCW"] == _a["CutRCW"], (_a, _b))
chk("Case 1: LFGK solo mueve el de contrapeso", _c["CutRCW"] != _a["CutRCW"] and _c["CutRC"] == _a["CutRC"], (_a, _c))
_filas = [{"RZ": 1.0, "RO": 2.0, "RF": 3.0, "RB": 4.0}]
_a = RC.compute_case2(1000.0, 2000.0, _filas, "encima")[0]
_b = RC.compute_case2(1500.0, 2000.0, _filas, "encima")[0]
_c = RC.compute_case2(1000.0, 2500.0, _filas, "encima")[0]
chk("Case 2: LFKK solo mueve RZ y RO (cabina)", all(_b[k] != _a[k] for k in ("CutRZ", "CutRO"))
    and all(_b[k] == _a[k] for k in ("CutRF", "CutRB")), (_a, _b))
chk("Case 2: LFGK solo mueve RF y RB (contrapeso)", all(_c[k] != _a[k] for k in ("CutRF", "CutRB"))
    and all(_c[k] == _a[k] for k in ("CutRZ", "CutRO")), (_a, _c))
chk("...que es lo que dice la guía",
    "Rails usa LFKK para los rieles de cabina y LFGK para los de contrapeso, en Case 1 y en Case 2." in B_L, B_L[:200])
chk("⚠️ dice que no tiene la definición", "**De estas dos NO tienes la definición:** no sabes qué miden ni qué significan sus letras" in B_L)
chk("...y a dónde mandar", "manda al plano o a la oficina" in B_L)
chk("⚠️ ninguna es la del primer riel ni la del último", "Ninguna es «la del primer riel» ni «la del último»" in B_L)
chk("el bloque manda parar: no añadir qué miden ni qué significan las letras",
    "responde con esto y para: no añadas qué miden, cómo se miden ni qué significan sus letras" in B_L)
chk("⚠️ ninguna línea DEFINE LFKK ni LFGK",
    all(not re.search(r"(LFKK|LFGK)\s*(=|:|es |significa)", ln) for ln in P.splitlines()),
    [ln for ln in P.splitlines() if "LFKK" in ln])
_rails = [ln for ln in P.splitlines() if ln.startswith("- **Rails:**")]
_fr = _rails[0].split(". ")[0] if _rails else ""       # la frase donde salen: los casos van en otra
chk("la línea de Rails no ata LFKK/LFGK a un riel", len(_rails) == 1 and "LFKK" in _fr
    and not re.search(r"primer|último|Case", _fr), _rails)
chk("⚠️ «qué representa cada parámetro» ya no invita a explicar lo que no tiene",
    "qué es TKSW, etc.), si está definido en esta guía" in P)
chk("el bloque va antes de la confidencialidad, junto a la regla",
    P.index("## LO QUE NO SABES") < _ini < _fin)

# ─────────────────────────────────────────────────────────────────────────────
sec("3. La baja: lo que hace el botón y lo que dice la guía")
_tc = leer("core/timeclock_ui.py")
_i = _tc.index('key="tc_baja"')
_bloque = _tc[_i:_tc.index("# ── Las DOS acciones", _i)]
chk("el botón lleva a Ausencias", 'navegar("autogestion", "🌴 Ausencias")' in _bloque, _bloque)
chk("⚠️ y no registra nada", not re.search(r"ausencias|solicitar|registrar|append_row|_ws\(", _bloque.replace("🌴 Ausencias", "")), _bloque)
_sub = dict(H._SUBSECCIONES_CAMPO["autogestion"][1])
chk("esa sub-pestaña es My absences", _sub.get("🌴 Ausencias", "").endswith("My absences"), _sub)
_au = leer("core/ausencias_ui.py")
chk("el botón que la registra existe", "Record the sick leave" in _au)
_G = re.sub(r"\s+", " ", P)
chk("⚠️ la guía dice que el atajo NO registra",
    "Ese botón NO registra la baja: solo lo lleva a **My absences**, y es allí donde se registra, con **Record the sick leave**." in _G)
chk("sin frases que digan lo contrario", "tap it and confirm" not in _G.lower())

# ─────────────────────────────────────────────────────────────────────────────
sec("4. «Switch project» en su propia fila (AppTest)")
from streamlit.testing.v1 import AppTest                          # noqa: E402

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import timeclock as TC, projects as P, roster as R, prestart as PS
from core import timeclock_ui as U
st.session_state["auth"] = {"rol": "field", "usuario": "camp", "nombre": "Camp", "grupo": "g"}
TC.is_configured = lambda: True
TC.open_sessions = lambda *a, **k: {
    TC.TIPO_GENERAL: {"proyecto": "", "proyecto_id": "", "clock_in": "2026-10-08 18:24:31"},
    TC.TIPO_PROYECTO: {"proyecto": "Obra A", "proyecto_id": "PRJ-A", "clock_in": "2026-10-08 18:25:01"}}
TC.resumen_hoy = lambda *a, **k: {"general": 0.0, "proyecto": 0.0, "sin_asignar": 0.0, "por_proyecto": {}}
TC.resumen_semana = lambda *a, **k: {"general": 0.0, "proyecto": 0.0, "dias": 0}
TC.mis_fichajes = lambda *a, **k: []
TC.olvidos = lambda s: {}
def _sw(nombre, grupo, nom, ubicacion="", usuario="", new_pid=""):
    st.session_state["_fk_switch"] = (nom, new_pid)
    return True, "Switched"
TC.switch_project = _sw
def _sal(*a, **k):
    st.session_state["_fk_salio"] = True
    return True, "Out"
TC.clock_out = _sal
P.list_projects_for_field = lambda *a, **k: [{"ID": "PRJ-A", "Name": "Obra A", "Group": "g"},
                                             {"ID": "PRJ-B", "Name": "Obra B", "Group": "g"}]
R.is_configured = lambda: False
PS.hecho_hoy = lambda pid, g="": True
U.render_timeclock_tab()
''' % RAIZ


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def camino(nodo, key, ruta=()):
    """Los bloques que envuelven al widget `key`: cuántas columnas dentro de columnas vive."""
    for h in getattr(nodo, "children", {}).values():
        if getattr(h, "key", None) == key:
            return ruta
        r = camino(h, key, ruta + (getattr(h, "type", ""),))
        if r is not None:
            return r
    return None


def n_col(ruta):
    return sum(1 for x in (ruta or ()) if "column" in str(x) and "columns" not in str(x))


at = corre(AppTest.from_string(GUION, default_timeout=120))
_rs, _rb, _rl = camino(at.main, "tc_switch"), camino(at.main, "tc_switch_btn"), camino(at.main, "tc_prj_out")
chk("se encontraron los tres", None not in (_rs, _rb, _rl), (_rs, _rb, _rl))
chk("⚠️ el selector vive en UNA columna, no en una columna dentro de otra", n_col(_rs) == 1, _rs)
chk("...y su botón", n_col(_rb) == 1, _rb)
chk("...y «Leave the project»", n_col(_rl) == 1, _rl)
chk("«Leave the project» va encima de «Switch project»",
    _tc.index('key="tc_prj_out"') < _tc.index('key="tc_switch"'))
_sel = at.selectbox(key="tc_switch")
_sel.select("Obra B")
corre(at)
at.button(key="tc_switch_btn").click()
corre(at)
chk("cambiar de obra sigue funcionando", at.session_state["_fk_switch"] == ("Obra B", "PRJ-B"))
at = corre(AppTest.from_string(GUION, default_timeout=120))
at.button(key="tc_prj_out").click()
corre(at)
chk("«Leave the project» sigue funcionando", at.session_state["_fk_salio"] is True)

# ─────────────────────────────────────────────────────────────────────────────
sec("5. El anexo de firmas (PDF de verdad)")
from pypdf import PdfReader                                       # noqa: E402


def texto(info):
    pdf = PPDF.generate_anexo_firmas_pdf(info)
    return " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages)


_base = {"marca": "cliente1", "ps_id": "PS-0003", "proyecto": "PRJ-0027", "location": "Bondi",
         "firmas": [{"name": "installer CI 1", "initial": "IC1", "sig": None, "hora": "07:07"}]}
_t = texto(dict(_base, fecha="2026-11-02"))
chk("⚠️ la fecha de la hoja (ISO) sale DD/MM/YYYY", "02/11/2026" in _t and "2026-11-02" not in _t, _t[:300])
chk("⚠️ «Project», en inglés", "Project" in _t and "Proyecto" not in _t, _t[:300])
chk("la obra y el sitio siguen", "PRJ-0027" in _t and "Bondi" in _t and "Location" in _t, _t[:300])
chk("la firma y la hora siguen", "installer CI 1" in _t and "07:07" in _t, _t[:300])
_t = texto(dict(_base, fecha=""))
chk("sin fecha no revienta: una raya", "—" in _t or "PS-0003" in _t, _t[:200])
_t = texto(dict(_base, fecha="no es <fecha>"))
chk("una fecha ilegible sale tal cual y escapada, sin romper el PDF", "no es <fecha>" in _t, _t[:200])
_src = leer("core/prestart_pdf.py")
chk("las dos etiquetas pasan por d() (texto de documento)", "d('Project')" in _src and "d('Location')" in _src)

print("\n=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
for x in fallos:
    print("  FALLO: %s" % x)
sys.exit(1 if fallos else 0)
