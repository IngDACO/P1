# -*- coding: utf-8 -*-
"""v685 · LO VISTO CERRANDO LA OFICINA DEL CICLO 4 (16/11/2026): lo que el informe del ciclo dejaba «sin probar»,
probado en producción con la sesión de Bobo (PRJ-0045) y el correo interno ensayado en local con sus datos reales.

  1. Tras «Duplicate for the next lift» la matriz queda a ceros, el chip decía «Matrix: 12 levels» en verde y
     «Calculate» NO lo frenaba: ni `validate_inputs` ni `_do_calculo` miran la matriz, así que salía el correo interno
     y se pagaban las dos interpretaciones de un resultado sin una sola medida (lo mismo con un Survey nuevo).
  2. «Rewrite the interpretation» funcionaba (las 3 cajas del modelo nuevas, las 2 de la app iguales, sin recalcular ni
     correo) pero no decía nada al terminar y TIRABA sin avisar lo que la oficina hubiera cambiado en las cajas (nacen
     otras, `_clave_iu`).
  3. El correo interno: «Notificación de uso», «Paso… Zona», «Matriz SURVEY ingresada» y el pie en español; «OFF per
     column» era el dict de Python («{'WR': 12, 'FR': 0, …}»); el CSV adjunto con «Stop» 0–11 (la H5 del ciclo 4) y
     llamado «survey_matrix.csv»; el pie no nombraba el informe de gestión ni el CSV; RL/FB sin sentido.

Sin red: las interpretaciones, el PDF, el correo y la hoja, sustituidos y contados.
"""
import email
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd                                               # noqa: E402
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                          # noqa: E402

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


COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]

sec("1. La matriz sin medir: qué niveles y cómo se dice")
from core import calculations as C                               # noqa: E402
_llena = [{c: 100.0 + i for c in COLS} for i in range(6)]
chk("una matriz medida: ningún nivel sin medir", C.niveles_sin_medir(_llena, COLS) == [], C.niveles_sin_medir(_llena, COLS))
_ceros = [{c: 0.0 for c in COLS} for _ in range(12)]
chk("⚠️ la de «Duplicate» (todo a 0): los 12, numerados 1…12", C.niveles_sin_medir(_ceros, COLS) == list(range(1, 13)),
    C.niveles_sin_medir(_ceros, COLS))
_parc = [dict(f) for f in _llena]
_parc[2] = {c: 0.0 for c in COLS}
_parc[4] = {c: float("nan") for c in COLS}
chk("un nivel a 0 y otro vacío (NaN): el 3 y el 5", C.niveles_sin_medir(_parc, COLS) == [3, 5], C.niveles_sin_medir(_parc, COLS))
_uno0 = [dict(f) for f in _llena]
_uno0[1]["OR"] = 0.0
chk("un solo valor a 0 NO es un nivel sin medir", C.niveles_sin_medir(_uno0, COLS) == [], C.niveles_sin_medir(_uno0, COLS))
chk("los tramos: «1–3, 5, 7–8»", C._tramos([1, 2, 3, 5, 7, 8]) == "1–3, 5, 7–8", C._tramos([1, 2, 3, 5, 7, 8]))
chk("...y uno solo, «4»", C._tramos([4]) == "4", C._tramos([4]))
_a12 = C.aviso_matriz(pd.DataFrame(_ceros), COLS)
chk("⚠️ el aviso de los 12: «12 levels have no measurements yet (1–12)…»",
    len(_a12) == 1 and "12 levels have no measurements yet (1–12): enter them before calculating." in _a12[0], _a12)
_a1 = C.aviso_matriz(pd.DataFrame([_llena[0], {c: 0.0 for c in COLS}]), COLS)
chk("...y en singular: «Level 2 has no measurements yet…»",
    len(_a1) == 1 and _a1[0].startswith("Level 2 has no measurements yet (its six values are 0)"), _a1)
chk("una medida entera: ningún aviso", C.aviso_matriz(pd.DataFrame(_llena), COLS) == [])
# ⚠️ v685 · B: medido A MEDIAS (lo destapó romper_v685: dos niveles a 0 → 18.755 «soluciones» y el informe sin acabar)
chk("un OR (u OL) a 0 sí vale: la apertura enrasada", C.celdas_a_cero(_uno0, COLS) == [], C.celdas_a_cero(_uno0, COLS))
_med1 = [dict(f) for f in _llena]
_med1[3]["FR"] = 0.0
chk("⚠️ un FR a 0 en el nivel 4: medido a medias", C.celdas_a_cero(_med1, COLS) == [(4, ["FR"])], C.celdas_a_cero(_med1, COLS))
_am1 = C.aviso_matriz(pd.DataFrame(_med1), COLS)
chk("⚠️ ...y se dice: «Level 4: FR at 0 — enter it before calculating (WR, WL, FR and FL can't be 0).»",
    _am1 == ["Level 4: FR at 0 — enter it before calculating (WR, WL, FR and FL can't be 0)."], _am1)
_med2 = [dict(f) for f in _med1]
_med2[0]["WR"] = float("nan")
_med2[0]["WL"] = 0.0
_med2[5] = {c: 0.0 for c in COLS}
chk("varios: WR vacía y WL a 0 en el 1, FR en el 4; el 6 entero sin medir va aparte",
    C.celdas_a_cero(_med2, COLS) == [(1, ["WR", "WL"]), (4, ["FR"])], C.celdas_a_cero(_med2, COLS))
_am2 = C.aviso_matriz(pd.DataFrame(_med2), COLS)
chk("...dos avisos: el nivel sin medir y «Measurements at 0 (1: WR, WL · 4: FR)…»",
    len(_am2) == 2 and _am2[0].startswith("Level 6 has no measurements yet")
    and _am2[1] == "Measurements at 0 (1: WR, WL · 4: FR): enter them before calculating (WR, WL, FR and FL can't be 0).", _am2)
chk("validate_inputs sigue sin mirar la matriz (los avisos se SUMAN)",
    "def validate_inputs(p: dict) -> list:" in leer("core/calculations.py"))

sec("2. En el Survey: el chip, el aviso temprano y «Calculate» con la matriz sin medir (AppTest)")
_su = leer("core/survey_ui.py")
_dc = _su[_su.index("    def _do_calculo():"):]
chk("⚠️ en `_do_calculo`, ANTES de las interpretaciones y del correo",
    "issues = validate_inputs(all_params) + aviso_matriz(survey_original_input, SURVEY_COLS)" in _dc
    and _dc.index("aviso_matriz(") < _dc.index("generate_interpretation(") < _dc.index("send_usage_notification("))
chk("...y en el aviso temprano (el de antes de pulsar)",
    "_iss0 = validate_inputs(_ap0) + aviso_matriz(st.session_state.survey_df, SURVEY_COLS)" in _su)

G = r'''
import streamlit as st
import pandas as pd
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"})
from core import survey_ui as SU, flash, interpretation as I
E = st.session_state.setdefault("_E", {"admin": [], "user": [], "pdf": [], "correo": 0})
def _adm(calc, ap):
    E["admin"].append(I.solucion_de(calc))
    return {**{k: "ADMIN %s" % I.solucion_de(calc) for k in I.INTERPRETATION_SCHEMA}, "_ok": True, "_sol": I.solucion_de(calc)}
def _usr(calc, ap):
    E["user"].append(I.solucion_de(calc))
    return {**{k: "%s %s #%d" % (k, I.solucion_de(calc), len(E["user"])) for k in I.USER_SCHEMA}, "_ok": True,
            "_sol": I.solucion_de(calc)}
SU.generate_interpretation = _adm
SU.generate_user_interpretation = _usr
def _pdf(**k):
    E["pdf"].append(dict(k.get("interpretation_user") or {}))
    return b"%PDF-1.4 x"
SU.generate_user_report = _pdf
def _correo(*a, **k):
    E["correo"] += 1
    return True
SU.send_usage_notification = _correo
# ⚠️ El optimizador, contado; y con una matriz SIN MEDIR no se deja correr: con la matriz a ceros no termina en 5 min
# (lo destapó romper_v685: con «Calculate» sin mirar la matriz, el guardián se colgaba en vez de salir rojo). La regla
# de «sin medir» va aquí escrita aparte, para que una rotura de la de la app no vuelva a colgarlo.
from core.optimizer import optimize as _opt_real     # el REAL, de su módulo (trampa 48: SU.optimize ya es este sustituto)
def _opt(adj, lim, ap):
    E["opt"] = E.get("opt", 0) + 1
    _sd = st.session_state.survey_df.fillna(0)
    if (_sd == 0).all(axis=1).any() or (_sd[["WR", "WL", "FR", "FL"]] == 0).any(axis=1).any():
        return {"best": None, "all_solutions": []}
    return _opt_real(adj, lim, ap)
SU.optimize = _opt
SU.plan_ui.selector_proyecto = lambda key, ayuda="": (None, {})
SU.projects_data.list_projects = lambda *a, **k: []
SU.init_state()
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    P = {"BKS": 1600, "RAIL": 62, "TKSW": 965, "SF1": 51, "SF2": 51, "BS": 1998, "BSR": 1985,
         "BT": 900, "FRAME": 30, "TS": 1750, "TK": 1400, "TKA": 100, "TKS": 30, "TSW": 100,
         "FS": 120, "OFFSET_CABIN": 0, "SG": 300, "TG": 60, "LengthTemplate": 300,
         "BGS": 900, "BK": 1100, "BKF1": 450, "BKF2": 450}
    for k, v in P.items():
        st.session_state["inp_" + k] = float(v)
    st.session_state["ns"] = 6
    _df = pd.DataFrame({
        "WR": [95, 88, 76, 92, 85, 80], "FR": [830, 822, 810, 818, 826, 815],
        "OR": [280, 296, 310, 288, 302, 295], "WL": [90, 84, 98, 79, 88, 86],
        "FL": [828, 820, 812, 824, 819, 816], "OL": [285, 292, 300, 305, 290, 298]}).astype(float)
    _mz = st.session_state.get("_MZ", "llena")
    if _mz == "ceros":
        _df = _df * 0.0
    elif _mz == "parcial":
        _df.iloc[[2, 4]] = 0.0
    elif _mz == "media":
        _df.loc[3, "FR"] = 0.0
    st.session_state["survey_df"] = _df
flash.mostrar()
SU.render_survey_tab("administrator", "cliente1")
'''


def app(mz="llena", calcular=True):
    at = AppTest.from_string(G, default_timeout=600)
    at.session_state["_E"] = {"admin": [], "user": [], "pdf": [], "correo": 0}
    at.session_state["_MZ"] = mz
    at.run()
    if calcular:
        next(b for b in at.button if b.key == "btn_calc_datos").click()
        at.run()
    return at


def chip(at):
    return next((str(m.value) for m in at.markdown if "Matrix: " in str(m.value) and "levels" in str(m.value)), "")


def avisos(at):
    return [str(w.value) for w in at.warning]


def errores(at):
    return [str(e.value) for e in at.error]


def cajas(at):
    return {x.key: x.value for x in at.text_area if str(x.key).startswith("sv_iu_")}


at = app("ceros", calcular=False)
chk("con la matriz a ceros: sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ el chip ya no dice «Matrix: 6 levels» en verde: «6 without measurements», en naranja",
    "Matrix: 6 levels, 6 without measurements" in chip(at) and ":orange[" in chip(at) and ":green[" not in chip(at), chip(at))
chk("el aviso temprano lo dice antes de pulsar",
    any("6 levels have no measurements yet (1–6)" in w for w in avisos(at)), avisos(at))
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ «Calculate» se para con el error", any("6 levels have no measurements yet (1–6): enter them before calculating." in e
                                              for e in errores(at)), errores(at))
chk("⚠️ ...sin correo interno ni interpretaciones (nada pagado)", E["correo"] == 0 and E["user"] == [] and E["admin"] == [], E)
chk("⚠️ ...y el optimizador ni arranca (con la matriz a ceros no terminaba en 5 min)", E.get("opt", 0) == 0, E.get("opt"))
chk("...y sin resultado", not at.session_state["calc_results"])

at = app("parcial", calcular=False)
chk("con dos niveles sin medir: «2 without measurements»", "Matrix: 6 levels, 2 without measurements" in chip(at), chip(at))
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ ...y «Calculate» dice cuáles: «(3, 5)»", any("2 levels have no measurements yet (3, 5)" in e for e in errores(at))
    and E["correo"] == 0 and E["user"] == [] and E.get("opt", 0) == 0, (errores(at), E))

at = app("media", calcular=False)
chk("⚠️ con UNA medida a 0 (FR del nivel 4): «1 incomplete»", "Matrix: 6 levels, 1 incomplete" in chip(at)
    and ":orange[" in chip(at), chip(at))
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ ...y «Calculate» se para con el nivel y la medida, sin optimizar, ni correo, ni interpretaciones",
    any("Level 4: FR at 0 — enter it before calculating" in e for e in errores(at))
    and E["correo"] == 0 and E["user"] == [] and E.get("opt", 0) == 0, (errores(at), E))

at = app("llena")
E = at.session_state["_E"]
chk("con la matriz medida: el chip en verde y calcula (correo, interpretaciones y optimizador, una vez)",
    chip(at) == "" and E["correo"] == 1 and len(E["user"]) == 1 and E.get("opt") == 1 and at.session_state["calc_results"],
    (chip(at), E))
# «Duplicate for the next lift», desde los datos (el camino visto en producción)
at.radio(key="survey_fase").set_value("📝 Survey data")
at.run()
chk("en los datos, con la matriz medida: el chip en verde", ":green[" in chip(at) and "without" not in chip(at), chip(at))
next(b for b in at.button if b.key == "btn_dup_survey").click()
at.run()
chk("«Duplicate survey» lo dice", any("Survey duplicated" in str(x.value) for x in list(at.info) + list(at.success)
                                       + list(at.markdown) + list(at.toast)), "")
chk("⚠️ tras duplicar: el chip dice «6 without measurements»", "Matrix: 6 levels, 6 without measurements" in chip(at), chip(at))
next(b for b in at.button if b.key == "btn_calc_datos").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ ...y «Calculate» se para: el correo, las interpretaciones y el optimizador siguen en 1",
    any("6 levels have no measurements yet (1–6)" in e for e in errores(at)) and E["correo"] == 1 and len(E["user"]) == 1
    and E.get("opt") == 1, (errores(at), E))

sec("3. «Rewrite the interpretation»: lo dice al terminar y, con cambios de la oficina, pregunta antes (AppTest)")
at = app("llena")
E = at.session_state["_E"]
_c0 = cajas(at)
chk("calculado: las cinco cajas", len(_c0) == 5, list(_c0))
next(b for b in at.button if b.key == "sv_reescribir_ia").click()
at.run()
E = at.session_state["_E"]
_c1 = cajas(at)
chk("⚠️ sin cambios: reescribe sin preguntar (las dos, una vez más; sin correo)",
    len(E["user"]) == 2 and len(E["admin"]) == 2 and E["correo"] == 1, E)
chk("...con cajas nuevas y el texto nuevo", set(_c1) != set(_c0) and any(v.endswith("#2") for v in _c1.values()), _c1)
chk("⚠️ y lo dice: «Interpretation rewritten for the active solution…»",
    any("Interpretation rewritten for the active solution" in str(s.value) for s in at.success), [s.value for s in at.success])
_kres = next(k for k in _c1 if k.startswith("sv_iu_resumen_"))
_kfin = next(k for k in _c1 if k.startswith("sv_iu_verificacion_"))
at.text_area(key=_kres).set_value("EDITED BY THE OFFICE")
at.text_area(key=_kfin).set_value(_c1[_kfin] + "\nOne more check.")
next(b for b in at.button if b.key == "sv_reescribir_ia").click()
at.run()
E = at.session_state["_E"]
_w = [w for w in avisos(at) if "Rewriting replaces what you changed in" in w]
chk("⚠️ con cambios: NO reescribe todavía", len(E["user"]) == 2, E["user"])
chk("⚠️ ...pregunta, con las cajas cambiadas: «Summary, Final checks»",
    len(_w) == 1 and "Summary, Final checks" in _w[0] and "Implementation" not in _w[0], avisos(at))
chk("...con «Yes, rewrite it» y «Keep my changes», y el botón de reescribir parado",
    {"sv_rw_si", "sv_rw_no"} <= {b.key for b in at.button}
    and next(b for b in at.button if b.key == "sv_reescribir_ia").disabled, "")
next(b for b in at.button if b.key == "sv_rw_no").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ «Keep my changes»: no reescribe y lo cambiado sigue", len(E["user"]) == 2 and cajas(at).get(_kres) == "EDITED BY THE OFFICE"
    and cajas(at).get(_kfin, "").endswith("One more check."), (E["user"], cajas(at).get(_kres)))
chk("...y la pregunta se va", not [w for w in avisos(at) if "Rewriting replaces" in w]
    and not next(b for b in at.button if b.key == "sv_reescribir_ia").disabled, avisos(at))
next(b for b in at.button if b.key == "sv_gen_informe_cliente").click()
at.run()
E = at.session_state["_E"]
chk("lo que dejó la oficina sigue yendo al PDF", E["pdf"] and E["pdf"][-1]["resumen"] == "EDITED BY THE OFFICE", E["pdf"][-1:])
next(b for b in at.button if b.key == "sv_reescribir_ia").click()
at.run()
next(b for b in at.button if b.key == "sv_rw_si").click()
at.run()
E = at.session_state["_E"]
_c3 = cajas(at)
chk("⚠️ «Yes, rewrite it»: reescribe (una vez), sin recalcular ni correo",
    len(E["user"]) == 3 and len(E["admin"]) == 3 and E["correo"] == 1, E)
chk("...cajas nuevas con el texto nuevo (lo cambiado se fue, como se avisó)",
    "EDITED BY THE OFFICE" not in _c3.values() and any(v.endswith("#3") for v in _c3.values()), _c3)
chk("...y lo dice", any("Interpretation rewritten" in str(s.value) for s in at.success))
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

sec("4. El correo interno: en inglés, legible, «Stop» 1…NS y los adjuntos con nombre")
from core import email_notify as EN                              # noqa: E402
_capt = {}


class _SMTP:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, *a):
        pass

    def sendmail(self, frm, to, data):
        _capt["msg"] = data


_smtp0, _sec0 = EN.smtplib.SMTP, EN._secrets
EN.smtplib.SMTP = _SMTP
EN._secrets = lambda: ("from@example.invalid", "x", "to@example.invalid")
try:
    _df = pd.DataFrame(_llena)[COLS]
    _best = {"rl": -25.0, "fb": 3.0, "fb_applied": 16.0, "total_off": 23,
             "off_by_col": {"WR": 12, "FR": 0, "OR": 11, "WL": 0, "FL": 0, "OL": 0}}
    _ana = {c + "_OFF_COUNT": 0 for c in COLS}
    _ok = EN.send_usage_notification(
        proyecto="C4 — Harbour Lifts — Lift 4 (tools)", ingeniero="hjg,ujgjg",
        all_params={"BS": 1854, "BSR": 1840, "NS": 6, "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R"},
        analysis=_ana, opt_result={"best": _best}, bs_result={"needed": True, "step": 3.5, "range_name": "ZB"},
        survey_df=_df, pdf_bytes=b"%PDF-1.4 x", pdf_name=None, admin_report=b"%PDF-1.4 y")
finally:
    EN.smtplib.SMTP, EN._secrets = _smtp0, _sec0
chk("se arma y «se envía» (al SMTP de mentira)", _ok is True and "msg" in _capt)
_m = email.message_from_bytes(_capt.get("msg", b""))
_html, _adj = "", {}
for _p in _m.walk():
    if _p.get_content_type() == "text/html":
        _html = _p.get_payload(decode=True).decode("utf-8")
    elif _p.get_filename():
        _adj[_p.get_filename()] = _p.get_payload(decode=True)
_txt = re.sub(r"<[^>]+>", " ", _html)
chk("⚠️ sin español: ni «Notificación», ni «Paso:», ni «Zona:», ni «Matriz», ni «ingresada», ni «generada»",
    not re.search(r"Notificaci|Paso:|Zona:|Matriz|ingresada|generada", _txt), re.findall(r"Notificaci\w*|Paso:|Zona:|Matriz\w*", _txt))
chk("...en inglés: «Usage notification», «Step: 3.5 mm — Zone: ZB», «SURVEY matrix entered (mm)»",
    "Usage notification" in _txt and "Step: 3.5 mm — Zone: ZB" in _txt and "SURVEY matrix entered (mm)" in _txt)
chk("⚠️ «OFF per column» legible: «WR 12 · OR 11» (era el dict de Python)",
    re.search(r"OFF per column\s*</td>\s*<td[^>]*>WR 12 · OR 11<", _html) is not None and "{'WR'" not in _html,
    re.findall(r"OFF per column.{0,120}", _html))
chk("⚠️ RL y FB con su sentido: «-25.0 mm (to the RIGHT)», «+16.0 mm (towards the REAR)»",
    "-25.0 mm (to the RIGHT)" in _txt and "+16.0 mm (towards the REAR)" in _txt)
chk("el pie nombra los tres adjuntos", "Attached: the management report (PDF), the drawing (PDF), the survey matrix (CSV)." in _txt)
_csv = next((n for n in _adj if n.endswith(".csv")), "")
chk("⚠️ el CSV con la obra y la hora (era «survey_matrix.csv»)",
    re.fullmatch(r"Survey_matrix_C4_Harbour_Lifts_Lift_4_tools_\d{4}-\d{2}-\d{2}_\d{4}\.csv", _csv) is not None, list(_adj))
_lin = [x for x in (_adj.get(_csv) or b"").decode("utf-8").splitlines() if x.strip()]
chk("⚠️ y «Stop» 1…6 (salía 0–5)", _lin[:1] == ["Stop,WR,FR,OR,WL,FL,OL"] and _lin[1].startswith("1,") and _lin[-1].startswith("6,")
    and len(_lin) == 7, _lin[:3])
chk("el plano sin nombre subido: «Drawing_<obra>.pdf» (era «drawing.pdf»)", "Drawing_C4_Harbour_Lifts_Lift_4_tools.pdf" in _adj, list(_adj))
chk("el informe de gestión, como estaba", "Admin_report_C4_Harbour_Lifts_Lift_4_tools.pdf" in _adj, list(_adj))
_en = leer("core/email_notify.py")
chk("lo tecleado sigue escapado (v603) y «Head installer/s» (v459)",
    "{_html.escape(proyecto or '(not specified)')}" in _en and "<strong>Head installer/s:</strong>" in _en)
chk("ningún correo personal en el código del correo (el repositorio es público)", "@gmail.com" not in _en)

sec("5. El informe de gestión: los diagramas en inglés y con WL/WR a la línea del riel (H11), y sin cabeceras en español")
from core import report as R                                     # noqa: E402
_lat = "\n".join(R._dg_lateral_limits(91, 40, 101, 40, 1600, 62, 0, "R"))
_lon = "\n".join(R._dg_bc_calc(1760, 1000, 1350, 60))
chk("⚠️ sin español en los dos diagramas (PARED, FONDO, HUECO, BLOQUE CABINA, puerta, Perfil, Seccion)",
    not re.search(r"PARED|FONDO|HUECO|BLOQUE|CABINA|puerta|Perfil|Seccion|transversal", _lat + _lon),
    re.findall(r"PARED\w*|FONDO|HUECO|BLOQUE|CABINA|puerta|Perfil|Seccion", _lat + _lon))
chk("...en inglés: «Cross-section (top view…)», «LEFT WALL … RIGHT WALL», «CAR BLOCK», «BT (door)», «CAR BLOCK = TL»",
    "Cross-section (top view, not to scale):" in _lat and "LEFT WALL" in _lat and "RIGHT WALL" in _lat
    and "CAR BLOCK (BKS + 2*RAIL)" in _lat and "BT (door)" in _lat
    and "Longitudinal profile (side view, not to scale):" in _lon and "CAR BLOCK = TL" in _lon)
_fl = [x for x in _lat.splitlines() if "WL" in x and "WR" in x and "<" in x]
chk("⚠️ H11 · WL y WR llegan a la LÍNEA del riel («@»), y entre las dos líneas, BKS + RAIL",
    len(_fl) == 1 and re.search(r"\|<-+ WL -+>@<-+ BKS \+ RAIL -+>@<-+ WR -+>\|", _fl[0]) is not None
    and "|<-RAIL-|" not in _lat and "WL and WR are measured to it" in _lat, _fl)
_cols = [i for i, ch in enumerate(_fl[0]) if ch == "@"] if _fl else []
_blq = [x for x in _lat.splitlines() if "+---" in x]
chk("...y el bloque (BKS + 2·RAIL) sobresale de las dos líneas de riel, a los dos lados",
    len(_cols) == 2 and _blq and _blq[0].index("+") < _cols[0] and _blq[0].rindex("+") > _cols[1], (_cols, _blq[:1]))
chk("las dos paredes, en la misma columna en todas las líneas del dibujo",
    len({x.rindex("|") for x in _lat.splitlines() if x.startswith("    |")}) == 1, "")
_rp = leer("core/report.py")
chk("⚠️ la tabla de la solución, con su cabecera en inglés (era «Columna | Límite (mm) | Fuera límite | Niveles»)",
    all(x in _rp for x in ('_d("Column"):', '_d("Limit (mm)"):', '_d("Out of limit"):', '_d("Levels"):'))
    and not re.search(r'"(Columna|Límite \(mm\)|Fuera límite|Niveles)"\s*:', _rp))
chk("los rangos del BSR vs BS, en inglés (era «Rango 1 — Zona ZB»)",
    '_d("Range 1 — Zone ZB")' in _rp and '_d("Range 2 — Zone OB")' in _rp and '"Rango 1' not in _rp and '"Rango 2' not in _rp)

print("\n%s: %d ok, %d FALLO" % ("verif_v685", n_ok, len(fallos)))
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
