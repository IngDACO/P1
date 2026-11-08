# -*- coding: utf-8 -*-
"""v652 · LAS DOS INTERPRETACIONES DEL SURVEY (08/11/2026). Medido con los dos surveys reales de cliente1: Haiku daba
los desplazamientos en el sentido contrario al del cálculo, decía «todo resuelto» con el lado izquierdo fuera de límite en
los 8 pisos, razonaba al revés y describía mover una cabina instalada con gatos. Decisiones del usuario (A–E):
  A. los datos los pone la app (`hechos`); del cliente, desplazamientos y cortes los ESCRIBE la app; `revisar` comprueba
     cada mm, cada sentido y que no diga «resuelto» si queda algo; un intento más con los errores; si no, no se publica;
  B. el survey es ANTES de instalar: el RL/FB se aplica con la plantilla de plomadas (confirmado por el usuario);
  C. siempre la solución ACTIVA (al elegir otra se reescribe) y reintentar sin recalcular ni reenviar el correo;
  D. la oficina revisa y edita el texto del cliente antes del PDF;
  E. Sonnet 5.5, esfuerzo bajo, salida con esquema y respaldo.

Sin la API: el cliente de Anthropic y la llamada, sustituidos y apuntados.
"""
import json
import os
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import interpretation as I                              # noqa: E402

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


LIM = {"LIMIT_WR": 82.0, "LIMIT_WL": 82.0, "LIMIT_FR": 815.0, "LIMIT_FL": 815.0, "LIMIT_OR": 437.0, "LIMIT_OL": 437.0,
       "FB_MAX_BACK": 60.0}
ANA = {"MIN_WR": 73.5, "MAX_WR": 80.5, "WR_OFF_COUNT": 3, "MIN_WL": 69.5, "MAX_WL": 85.0, "WL_OFF_COUNT": 2,
       "MIN_FR": 807.0, "MAX_FR": 823.0, "FR_OFF_COUNT": 1, "MIN_FL": 810.0, "MAX_FL": 823.0, "FL_OFF_COUNT": 1,
       "MIN_OR": 429.5, "MAX_OR": 452.5, "OR_OFF_COUNT": 1, "MIN_OL": 432.5, "MAX_OL": 453.5, "OL_OFF_COUNT": 2,
       "MAX_OFF_RL": 12.5, "MAX_OFF_FB": 8.0}
MATRIZ = [{"WR": 90, "WL": 61, "FR": 820, "FL": 820, "OR": 450, "OL": 430},
          {"WR": 90, "WL": 85, "FR": 820, "FL": 820, "OR": 430, "OL": 441},
          {"WR": 90, "WL": 70, "FR": 820, "FL": 820, "OR": 430, "OL": 430}]
ANTES = [{"WR": 73.5, "WL": 69.5, "FR": 807, "FL": 830, "OR": 452.5, "OL": 440},
         {"WR": 80, "WL": 80, "FR": 820, "FL": 810, "OR": 430, "OL": 453.5},
         {"WR": 75, "WL": 85, "FR": 820, "FL": 830, "OR": 430, "OL": 430}]
PAR = {"NS": 3, "BS": 1998, "BSR": 1985, "BKS": 1772, "RAIL": 62, "SF1": 51, "SF2": 51, "BT": 900, "FRAME": 30,
       "TKSW": 965, "FS": 120, "TSW": 100, "WALL_LIMITING": False, "OFFSET_CABIN": 0, "OFFSET_SIDE": "R"}


def calc(rl=8.5, fb=8.0, off=None, matriz=None, extra=False, best=True):
    off = {"WR": 0, "FR": 0, "WL": 2, "FL": 0} if off is None else off
    b = {"rl": rl, "fb": fb, "fb_applied": fb, "total_off": sum(off.values()), "off_by_col": off,
         "matrix": matriz or MATRIZ, "fb_extra_applied": extra}
    return {"limits": dict(LIM), "analysis": dict(ANA), "optimizer_result": {"best": b if best else None},
            "bs_result": {"needed": True, "step": 3.5, "range_name": "ZB"}, "survey_adj": list(ANTES)}


sec("1. E · Sonnet 5.5, con esquema, por tipo, y nunca la clave de verdad bajo AppTest")
chk("Sonnet 5.5 y esfuerzo bajo", I.MODEL == "claude-sonnet-5-5" and I.ESFUERZO == "low")
_src = leer("core/interpretation.py")
chk("⚠️ la clave, la de `parte_agente` (bajo AppTest, vacía); ni rastro de `st.secrets` aquí",
    "AG.clave_api()" in _src and "st.secrets" not in _src)
chk("⚠️ bajo AppTest, sin clave (no gasta en cada suite: trampa 44)", I._clave() == "")
chk("ya no se lee por posición", "content[0]" not in _src)
LLAM, RESP = [], []


class _B:
    def __init__(self, tipo, texto=""):
        self.type, self.text = tipo, texto


class _Msgs:
    def create(self, **k):
        LLAM.append(k)
        return RESP.pop(0)


class _Cli:
    def __init__(self, **k):
        self.beta = types.SimpleNamespace(messages=_Msgs())


_anth = I.anthropic
I.anthropic = types.SimpleNamespace(Anthropic=_Cli)
RESP[:] = [types.SimpleNamespace(stop_reason="end_turn", content=[_B("thinking"), _B("text", '{"resumen": "R"}')])]
_d, _m = I._llamar("SIS", "MSG", ["resumen"], "k")
_k = LLAM[-1]
chk("⚠️ con el razonamiento DELANTE, se lee el bloque de texto (trampa 50)", _d == {"resumen": "R"} and _m == "", (_d, _m))
chk("salida con esquema: exactamente las claves pedidas", _k["output_config"]["format"]["type"] == "json_schema"
    and _k["output_config"]["format"]["schema"]["required"] == ["resumen"]
    and _k["output_config"]["format"]["schema"]["additionalProperties"] is False and _k["output_config"]["effort"] == "low", _k["output_config"])
chk("con el respaldo del servidor", _k["fallbacks"] == "default" and _k["betas"] == [I._BETA_RESPALDO] and _k["model"] == I.MODEL)
# ⚠️ con un JSON VÁLIDO dentro: sin texto, el rechazo daba `None` de todos modos y la prueba no veía nada (romper_v652)
RESP[:] = [types.SimpleNamespace(stop_reason="refusal", content=[_B("text", '{"resumen": "R"}')])]
chk("un rechazo no se da por bueno (aunque traiga algo que se lee)", I._llamar("S", "M", ["resumen"], "k")[0] is None)
RESP[:] = [types.SimpleNamespace(stop_reason="max_tokens", content=[_B("text", '{"resumen": "R"}')])]
chk("...ni uno cortado por el tope", I._llamar("S", "M", ["resumen"], "k")[0] is None)
RESP[:] = [types.SimpleNamespace(stop_reason="end_turn", content=[_B("text", "no es json")])]
chk("lo que no se entiende, tampoco", I._llamar("S", "M", ["resumen"], "k")[0] is None)
I.anthropic = _anth

sec("2. A · Los hechos los calcula la app")
f = I.hechos(calc(), PAR)
s = f["solution"]
chk("⚠️ RL positivo = a la IZQUIERDA; FB positivo = hacia ATRÁS", s["lateral_shift"] == "8.5 mm to the LEFT"
    and s["front_back_shift"] == "8.0 mm towards the REAR" and s["lateral_direction"] == "left"
    and s["front_back_direction"] == "rear", s)
_n = I.hechos(calc(rl=-3.0, fb=-2.0), PAR)["solution"]
chk("y negativo, a la DERECHA y hacia el FRENTE", _n["lateral_shift"] == "3.0 mm to the RIGHT"
    and _n["front_back_shift"] == "2.0 mm towards the FRONT", _n)
_z = I.hechos(calc(rl=0.0, fb=0.0), PAR)["solution"]
chk("cero, sin sentido", _z["lateral_direction"] == "none" and _z["lateral_shift"] == "no lateral shift"
    and _z["front_back_shift"] == "no front-back shift", _z)
_q = s["still_out_of_limit"]
chk("⚠️ lo que SIGUE fuera, con sus pisos y su peor valor", _q == [{"column": "WL", "how_many_floors": 2, "floors": [1, 3],
                                                                   "worst_mm": 61.0, "limit_mm": 82.0, "rule": "minimum"}]
    and s["everything_within_limits"] is False, _q)
chk("⚠️ en el Caso 2, OR/OL no «siguen fuera»: se cortan", f["cuts"] == [
    {"floor": 1, "cut_right_side_of_opening_mm": 13.0}, {"floor": 2, "cut_left_side_of_opening_mm": 4.0}], f["cuts"])
_c1 = I.hechos(calc(off={"WR": 0, "FR": 0, "OR": 1, "WL": 0, "FL": 0, "OL": 0}), {**PAR, "WALL_LIMITING": True})
chk("en el Caso 1 (pared), OR fuera cuenta, con su máximo", _c1["solution"]["still_out_of_limit"] == [
    {"column": "OR", "how_many_floors": 1, "floors": [1], "worst_mm": 450.0, "limit_mm": 437.0, "rule": "maximum"}]
    and "Case 1" in _c1["case"], _c1["solution"]["still_out_of_limit"])
_ok0 = I.hechos(calc(off={"WR": 0, "FR": 0, "WL": 0, "FL": 0}), PAR)["solution"]
chk("sin nada fuera, «everything within limits»", _ok0["everything_within_limits"] is True and _ok0["still_out_of_limit"] == [])
chk("antes de desplazar, los pisos fuera de cada columna (de la matriz ajustada)",
    f["before_shifting"]["WL"]["floors_out_of_limit"] == [1, 2] and f["before_shifting"]["OL"]["floors_out_of_limit"] == [1, 2],
    f["before_shifting"])
chk("lo que el análisis pide desplazar, el bloque de cabina y el BSR", f["shift_needed_mm"] == {"lateral": 12.5, "front_back": 8.0}
    and f["geometry_mm"]["car_block_width"] == 1896.0 and f["bsr_vs_bs"]["difference_mm"] == 13.0
    and f["bsr_vs_bs"]["step_mm"] == 3.5, (f["shift_needed_mm"], f["bsr_vs_bs"]))
chk("sin solución, se dice", I.hechos(calc(best=False), PAR)["solution"] is None)

sec("3. A · Del cliente, desplazamientos y cortes los ESCRIBE la app")
_td = I.texto_desplazamientos(f)
chk("⚠️ la plantilla de plomadas, con el sentido del cálculo (B)", "Set out the plumb template and the plumb lines" in _td
    and "• Lateral: 8.5 mm to the LEFT." in _td and "• Front-back: 8.0 mm towards the REAR." in _td, _td)
chk("⚠️ y lo que SIGUE fuera, dicho al cliente", "Still out of limit after these shifts: the left side clearance on floors "
    "1, 3 (worst 61.0 mm against a minimum of 82.0 mm)" in _td, _td)
chk("sin nada fuera, no lo dice", "Still out of limit" not in I.texto_desplazamientos(I.hechos(calc(off={"WL": 0}), PAR)))
_tc = I.texto_cortes(f)
chk("los cortes piso a piso, del cálculo", "• Floor 1: cut 13.0 mm on the right side of the opening." in _tc
    and "• Floor 2: cut 4.0 mm on the left side of the opening." in _tc, _tc)
chk("sin cortes, se dice", I.texto_cortes(I.hechos(calc(matriz=[{"WR": 90, "WL": 90, "FR": 820, "FL": 820, "OR": 400, "OL": 400}],
                                                         off={"WL": 0}), PAR)) == "No landing door opening needs to be cut.")
chk("sin solución, ni desplazamientos ni cortes inventados", "No positioning solution" in I.texto_desplazamientos({"solution": None})
    and "No cuts can be defined" in I.texto_cortes({"solution": None, "cuts": []}))

sec("4. A · `revisar`: lo que escribió Haiku en los surveys REALES, cazado")
# (frases copiadas de PRJ-0026 y PRJ-0034, con la solución de cada uno)
f26 = I.hechos(calc(rl=8.5, fb=8.0), PAR)
f34 = I.hechos(calc(rl=4.0, fb=13.0), PAR)
_r = I.revisar({"a": "A uniform forward push (FB) of 8.0 mm is applied to correct the front-to-back variation."}, f26)
chk("⚠️ «forward» con FB hacia atrás", "a" in _r and any("wrong direction" in x for x in _r["a"]), _r)
_r = I.revisar({"a": "With RL = 8.5 mm left and FB = 8.0 mm forward, all eight levels transition to compliant WL clearance."}, f26)
chk("⚠️ «all eight levels transition to compliant» con WL fuera", any("claims everything is resolved" in x for x in _r.get("a", [])), _r)
_r = I.revisar({"a": "These adjustments eliminate all side clearance and front wall conflicts across all 8 floors."}, f26)
chk("⚠️ «eliminate all…» al cliente", any("claims everything" in x for x in _r.get("a", [])), _r)
_r = I.revisar({"a": "Apply RL = +4.0 mm (shift right) and FB = 13.0 mm (push back)."}, f34)
chk("⚠️ «shift right» con el lateral a la IZQUIERDA", any("«shift right» is the wrong direction" in x for x in _r.get("a", [])), _r)
_r = I.revisar({"a": "A rightward shift (RL = 4.0 mm) and rearward push (FB = 13.0 mm) are required."}, f34)
chk("«rightward» también (y «rearward» NO: es el sentido bueno)", len(_r.get("a", [])) == 1 and "rightward" in _r["a"][0], _r)
_r = I.revisar({"a": "1. Release the guide rail bracket fasteners on both sides. 2. Shift it using adjustable jacks or shims."}, f26)
chk("⚠️ B · mover una cabina instalada (aflojar soportes, gatos)", len(_r.get("a", [])) == 2
    and all("describes moving an installed car" in x for x in _r["a"]), _r)
_r = I.revisar({"a": "The residual 7.5 mm spread may come from a local wall bulge."}, f26)
chk("una cifra que no está en los hechos", _r.get("a") == ["the number 7.5 is not in FACTS"], _r)
_bueno = ("Set out the plumb lines 8.5 mm to the LEFT and 8.0 mm towards the REAR. The left side clearance stays out of "
          "limit on floors 1 and 3 (61.0 mm against 82.0 mm). Measure the clearance to the left wall on each of the 3 "
          "floors, and cut 13.0 mm on the right side of the opening on floor 1. BKS + 2×RAIL = 1896 mm.")
chk("⚠️ lo correcto pasa limpio (sentidos, cifras, «to the left wall», 2×RAIL)", I.revisar({"a": _bueno}, f26) == {},
    I.revisar({"a": _bueno}, f26))
chk("⚠️ lo resuelto de UNA columna, o negado, NO es «todo resuelto» (visto en el examen)",
    I.revisar({"a": "The front-back shortfall is fully resolved, but WL stays out on floors 1 and 3. It does not fully "
                    "resolve the left side."}, f26) == {}, I.revisar({"a": "The front-back shortfall is fully resolved."}, f26))
# ⚠️ con el lateral a la DERECHA: a la izquierda, «to the left wall» coincidía con el sentido y la prueba no veía nada
chk("«to the left wall» es un sitio, no un sentido (con el lateral a la DERECHA)",
    I.revisar({"a": "Measure the clearance to the left wall on each of the 3 floors."}, I.hechos(calc(rl=-3.0), PAR)) == {},
    I.revisar({"a": "Measure the clearance to the left wall on each of the 3 floors."}, I.hechos(calc(rl=-3.0), PAR)))
chk("con todo dentro, «all floors are within limits» SÍ vale",
    I.revisar({"a": "All floors are within limits after the shift."}, I.hechos(calc(off={"WL": 0}), PAR)) == {})
chk("con un desplazamiento CERO, cualquier sentido de ese eje está mal",
    "a" in I.revisar({"a": "Move the plumb lines 2.0 mm to the LEFT."}, I.hechos(calc(rl=0.0), PAR)))

sec("5. A · Un intento más con los errores; si no, no se publica")
COLA, MSGS = [], []


def _llamar(sistema, mensaje, claves, api_key):
    MSGS.append((sistema, mensaje, list(claves)))
    x = COLA.pop(0)
    return (x, "") if isinstance(x, dict) else (None, x)


I._llamar = _llamar
I._clave = lambda: "k"
BUENO = {"parametros": "Shaft 1998 mm on the drawing, 1985 mm measured.", "estado_inicial": "WL is out on floors 1 and 2.",
         "desplazamientos": "The plumb lines go 8.5 mm to the LEFT.", "solucion_optima": "WL stays out on floors 1 and 3.",
         "evasion_pared": "A push.", "bsr_vs_bs": "13.0 mm short, step 3.5 mm.", "consideraciones": "Check WL on floors 1 and 3."}
MALO = dict(BUENO, solucion_optima="Everything is resolved: 8.0 mm forward.")
COLA[:] = [dict(MALO), dict(BUENO)]
MSGS.clear()
_a = I.generate_interpretation(calc(), PAR)
chk("⚠️ el primero, con errores → se le devuelve UNA vez, con ellos", len(MSGS) == 2 and "It has these problems" in MSGS[1][1]
    and "forward" in MSGS[1][1] and "Your previous answer" in MSGS[1][1], [m[1][-300:] for m in MSGS[1:]])
chk("...y el segundo, bueno, se publica", _a["solucion_optima"] == "WL stays out on floors 1 and 3." and _a["_ok"] is True
    and _a["_avisos"] == [], _a)
chk("⚠️ «evasion_pared» solo si se aplicó el empuje extra", _a["evasion_pared"] is None)
chk("y sabe de qué solución es (C)", _a["_sol"] == [8.5, 8.0])
COLA[:] = [dict(MALO), dict(MALO)]
_a = I.generate_interpretation(calc(), PAR)
chk("⚠️ si vuelve a fallar, ESE apartado no se publica (y los demás sí)", _a["solucion_optima"] == I.NO_INCLUIDO
    and _a["parametros"] == BUENO["parametros"] and _a["_avisos"] and "solucion_optima" in _a["_avisos"][0], _a)
COLA[:] = ["the AI service could not be reached"]
_a = I.generate_interpretation(calc(), PAR)
chk("sin respuesta, la interna falla como antes (el correo sale sin el informe)", _a["_ok"] is False and "could not be reached" in _a["_error"])
I._clave = lambda: ""
chk("sin clave, también", I.generate_interpretation(calc(), PAR)["_ok"] is False)

I._clave = lambda: "k"
UB = {"resumen": "Shift the plumb lines 8.5 mm to the LEFT; WL stays out on floors 1 and 3.",
      "implementacion": "1. Set out the plumb template.", "verificacion": "Check WL on floors 1 and 3."}
COLA[:] = [dict(UB)]
MSGS.clear()
_u = I.generate_user_interpretation(calc(), PAR)
chk("⚠️ al modelo solo se le piden los TRES suyos", MSGS[-1][2] == ["resumen", "implementacion", "verificacion"])
chk("⚠️ desplazamientos y cortes, los de la app", _u["desplazamientos"] == I.texto_desplazamientos(f)
    and _u["cortes"] == I.texto_cortes(f), _u)
chk("los suyos, si pasan la revisión", _u["resumen"] == UB["resumen"] and _u["_ok"] is True and _u["_sol"] == [8.5, 8.0])
COLA[:] = [dict(UB, resumen="Everything fits: 8.0 mm forward."), dict(UB, resumen="Everything fits: 8.0 mm forward.")]
_u = I.generate_user_interpretation(calc(), PAR)
chk("⚠️ un resumen que no casa: vacío y dicho, y lo demás sigue", _u["resumen"] is None and _u["implementacion"] == UB["implementacion"]
    and any("«resumen» was left out" in x for x in _u["_avisos"]), _u)
COLA[:] = ["the AI service could not be reached"]
_u = I.generate_user_interpretation(calc(), PAR)
chk("⚠️ sin respuesta, el informe del cliente NO se bloquea: lo de la app y el aviso", _u["_ok"] is True
    and _u["desplazamientos"] and _u["resumen"] is None and any("could not write its sections" in x for x in _u["_avisos"]), _u)
I._clave = lambda: ""
_u = I.generate_user_interpretation(calc(), PAR)
chk("sin clave, igual", _u["_ok"] is True and _u["cortes"] and _u["_avisos"])

sec("6. Lo que recibe el modelo")
_pu = I._build_user_payload(calc(), PAR)
chk("los HECHOS, con los cortes de `cortes_por_piso` (la definición del veredicto, v437)", "FACTS (computed by the app" in _pu
    and '"cut_right_side_of_opening_mm": 13.0' in _pu and "8.5 mm to the LEFT" in _pu)
chk("...y lo que ya escribió la app", "Set out the plumb template" in _pu and "These landing door openings must be cut" in _pu)
_pa = I._build_data_payload(calc(), PAR)
chk("la interna, los mismos hechos", "FACTS (computed by the app" in _pa and '"still_out_of_limit"' in _pa)
chk("⚠️ B · las instrucciones: plantilla de plomadas, nada de mover la cabina, sentidos en una forma",
    "Never describe moving an installed car" in I.USER_SYSTEM_PROMPT and "plumb template" in I.SYSTEM_PROMPT
    and 'Do not use the words forward, backward' in I.SYSTEM_PROMPT and "never say that everything is resolved" in I.SYSTEM_PROMPT)

sec("7. C/D · En el Survey: la solución ACTIVA, reescribir sin recalcular y la oficina revisa (AppTest)")
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
    E["user"].append((I.solucion_de(calc), "survey_adj" in calc))
    if E.get("falla"):
        return {"_ok": False, "_error": "boom"}
    return {**{k: "%s %s" % (k, I.solucion_de(calc)) for k in I.USER_SCHEMA}, "_ok": True, "_sol": I.solucion_de(calc),
            "_avisos": ["«resumen» was left out: test."]}
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
    st.session_state["survey_df"] = pd.DataFrame({
        "WR": [95, 88, 76, 92, 85, 80], "FR": [830, 822, 810, 818, 826, 815],
        "OR": [280, 296, 310, 288, 302, 295], "WL": [90, 84, 98, 79, 88, 86],
        "FL": [828, 820, 812, 824, 819, 816], "OL": [285, 292, 300, 305, 290, 298]}).astype(float)
flash.mostrar()
SU.render_survey_tab("administrator", "cliente1")
'''


def app(falla=False):
    at = AppTest.from_string(G, default_timeout=600)
    at.session_state["_E"] = {"admin": [], "user": [], "pdf": [], "correo": 0, "falla": falla}
    at.run()
    next(b for b in at.button if b.key == "btn_calc_datos").click()
    at.run()
    chk("calcula sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def cajas(at):
    return {x.key: x.value for x in at.text_area if str(x.key).startswith("sv_iu_")}


at = app()
E = at.session_state["_E"]
_s0 = E["user"][0][0]
chk("al calcular, una de cada, con la matriz ajustada", len(E["user"]) == 1 and len(E["admin"]) == 1 and E["user"][0][1] is True, E)
_c = cajas(at)
chk("⚠️ D · las cinco cajas, con el texto propuesto", sorted(_c) == sorted("sv_iu_%s_1_0" % k for k in I.USER_SCHEMA)
    and _c["sv_iu_resumen_1_0"] == "resumen %s" % _s0, _c)
chk("los avisos del asistente, a la vista", any("was left out" in str(w.value) for w in at.warning))
chk("⚠️ el desplegable con controles lleva clave (trampa 35)", any(x.key == "exp_sv_iu" for x in list(at.expander) + list(at.status)))
_sel = next(x for x in at.selectbox if str(x.key).startswith("sol_activa_"))
_sel.set_value(1)
at.run()
E = at.session_state["_E"]
_s1 = E["user"][-1][0]
chk("⚠️ C · elegir otra solución reescribe las DOS, para la activa", len(E["user"]) == 2 and len(E["admin"]) == 2
    and _s1 != _s0 and E["admin"][-1] == _s1, (E["user"], E["admin"]))
chk("...sin volver a mandar el correo interno", E["correo"] == 1, E["correo"])
_c = cajas(at)
chk("⚠️ y las cajas son OTRAS, con el texto nuevo (trampa 31)", "sv_iu_resumen_1_1" in _c and _c["sv_iu_resumen_1_1"] == "resumen %s" % _s1, _c)
at.text_area(key="sv_iu_resumen_1_1").set_value("EDITED BY THE OFFICE")
next(b for b in at.button if b.key == "sv_gen_informe_cliente").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ D · el PDF lleva lo que dejó la oficina", E["pdf"] and E["pdf"][-1]["resumen"] == "EDITED BY THE OFFICE"
    and E["pdf"][-1]["desplazamientos"] == "desplazamientos %s" % _s1, E["pdf"][-1:])
chk("y sin reescribir otra vez (nada cambió)", len(E["user"]) == 2, E["user"])
chk("se puede descargar", any("Download the client report" in str(b.label) for b in at.get("download_button")))
next(b for b in at.button if b.key == "sv_reescribir_ia").click()
at.run()
E = at.session_state["_E"]
chk("⚠️ C · «Rewrite the interpretation»: las dos de nuevo, sin recalcular ni correo", len(E["user"]) == 3 and len(E["admin"]) == 3
    and E["correo"] == 1 and "sv_iu_resumen_1_2" in cajas(at), (len(E["user"]), E["correo"], list(cajas(at))))
at = app(falla=True)
chk("⚠️ si falla, lo dice y deja reintentar sin recalcular", any("Rewrite the interpretation" in str(e.value) for e in at.error)
    and any(b.key == "sv_reescribir_ia" for b in at.button) and not cajas(at))

sec("8. Guardar en la obra: de la activa y lo revisado")
_su = leer("core/survey_ui.py")
_g = _su[_su.index('key="sv_save_prj"'):_su.index("Survey saved to **{x}**")]
chk("⚠️ si se eligió otra solución, se reescribe ANTES de guardar", "if _ia_vieja(r):" in _g and _g.index("_ia_vieja(r)") < _g.index("attach_survey"))
chk("⚠️ en la obra va el texto revisado del cliente", '"user":  _iu_final(r)' in _g)
chk("...y el PDF de Drive, también", "interpretation_user=_iu_final(r)" in _g and "if _iu_final(r).get(\"_ok\"):" in _g)

print("\n=== verif_v652: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for x in fallos:
    print("   -", x)
sys.exit(1 if fallos else 0)
