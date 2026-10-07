# -*- coding: utf-8 -*-
"""v541 · SIN OBRA NO SE OLVIDA NUNCA (una regla, no dos).

⚠️ El fallo, visto EN PRODUCCIÓN con la cuenta de campo (07/10/2026): en Rieles con PRUEBA
MOVIL, LFKK 1234 y 3 rieles de 2500 tecleados; «Close workday and project» en el menú lateral
→ todo a 0, sin haber cambiado de obra. Volver a fichar en la MISMA obra (tras comer) lo
habría perdido igual. Los botones del fichaje terminan en `st.rerun()`, que corta la pasada
ANTES de pintar la herramienta; en la siguiente, `al_pintar` creía que la herramienta
«volvía» de otra pantalla, y volver olvidaba también al pasar a «sin obra». Hasta v540 no se
notaba porque el borrado no llegaba al navegador (trampa nº31).

Ahora: lo tecleado es de la última obra REAL; se olvida al pintarse con OTRA obra real (la
primera tras usarla sin obra también: manda su plano, la decisión de v535); sin obra, nunca.
El Survey sigue con lo suyo (sin salir solo manda el plano; al volver con otra obra real,
olvida).

Lo que protege, EJECUTANDO la pantalla real de Rieles y la del Survey con botones que, como
los del fichaje, cambian la obra y cortan la pasada con `st.rerun()`; con la sonda validada
contra el `al_pintar` de v540 (trampa nº12).
"""
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from streamlit.testing.v1 import AppTest                          # noqa: E402

GUION = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo, plan_ui, plan_store, plan_data, rail_cut_ui as R, survey_ui as S
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"lfkk": 1111.0, "lfgk": 911.0, "params": {"BS": 1326.0}, "ns": 3},
          "PRJ-B": {"lfkk": 2222.0, "lfgk": 922.0, "params": {"BS": 1500.0}, "ns": 5}}
plan_ui.P.is_configured = lambda: True
plan_ui._proyecto_fichado = lambda a: ({"ID": st.session_state["obra"],
                                        "Name": st.session_state["obra"]}
                                       if st.session_state.get("obra") else None)
plan_data.del_proyecto = lambda pid: json.loads(json.dumps(PLANOS.get(pid, {})))
plan_data.resumen = lambda d: "plano"
plan_store.selector = lambda *a, **k: None
R.render_guardar = lambda **k: None
R.tool_pdf = lambda *a, **k: b""
S.projects_data.head_installers_label = lambda *a, **k: "Ing"


def _al_pintar_v540(herramienta, obra):
    """La de v540, copiada: la sonda tiene que VER el fallo con ella."""
    E = estado_vivo
    h, obra = str(herramienta), str(obra or "")
    n = int(st.session_state.get(E._PASADA, 0) or 0)
    antes = st.session_state.get(E._VISTA + h)
    ult_real = (antes[2] if antes and len(antes) > 2 else "") if antes else ""
    resp = st.session_state.pop(E._RESPETAR + h, False)
    if resp:
        ult_real = resp if isinstance(resp, str) else ""
    st.session_state[E._VISTA + h] = (n, obra, obra or ult_real)
    if resp or not antes:
        return False
    ult_pasada, ult_obra = antes[0], antes[1]
    if ult_pasada < n - 1 and ult_obra != obra:
        E.olvidar(h)
        return True
    if obra and ult_real and ult_real != obra:
        if h != "sv":
            E.olvidar(h)
        return True
    return False


# ⚠️ Los guiones comparten proceso: lo que se sustituye se repone SIEMPRE (v534).
if not hasattr(estado_vivo, "_al_pintar_real"):
    estado_vivo._al_pintar_real = estado_vivo.al_pintar
estado_vivo.al_pintar = (_al_pintar_v540 if st.session_state.get("v540")
                         else estado_vivo._al_pintar_real)
S.init_state()
estado_vivo.pasada()
# El fichaje del menú lateral: cada botón cambia la obra y termina en st.rerun() ANTES de
# que se pinte la herramienta (lo que hacen «Close workday and project» y «Clock in»).
for etq, o in (("cerrar", ""), ("fichar A", "PRJ-A"), ("fichar B", "PRJ-B")):
    if st.button(etq, key="sb_" + etq):
        st.session_state["obra"] = o
        st.rerun()
if st.session_state.pop("cargar_sin_obra", False):     # un `respetar` sin obra (v539)
    estado_vivo.respetar("rc")
    st.session_state["rc_n2500"] = 4
pg = st.session_state.get("pg", "rieles")
if pg == "rieles":
    R.render_rail_cut_tab()
elif pg == "survey":
    S.render_survey_tab("field", "g")
st.markdown("V=" + json.dumps([st.session_state.get(k) for k in st.session_state.get("ver", [])]))
''' % RAIZ


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def V(at):
    return json.loads(next(m.value for m in at.markdown if m.value.startswith("V="))[2:])


def boton(at, etq):
    at.button(key="sb_" + etq).click()
    return V(corre(at))


def num(at, k, v):
    at.number_input(key=k).set_value(v)
    return V(corre(at))


def sv(at, k):
    return at.number_input(key=k).proto.set_value


def rieles(obra, **flags):
    at = AppTest.from_string(GUION, default_timeout=120)
    at.session_state["obra"] = obra
    at.session_state["ver"] = ["rc_lfkk", "rc_n2500"]
    for k, v in flags.items():
        at.session_state[k] = v
    corre(at)
    return at


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Cerrar la jornada desde el menú lateral, dentro de Rieles (la pasada se corta)")
at = rieles("PRJ-A")
num(at, "rc_lfkk", 1234.0)
v = num(at, "rc_n2500", 3)
chk("de partida: obra A, LFKK corregido a mano (1234) y 3 rieles de 2500", v == [1234.0, 3], v)
v = boton(at, "cerrar")
chk("⚠️ «Close workday» (sin obra): lo tecleado SE QUEDA — el fallo de producción",
    v == [1234.0, 3], v)
v = boton(at, "fichar A")
chk("⚠️ ...y volver a fichar en la MISMA obra lo conserva (tras comer)", v == [1234.0, 3], v)
boton(at, "cerrar")
v = boton(at, "fichar B")
chk("cerrar y fichar en OTRA obra (B): manda el plano de B y lo tecleado para A se olvida",
    v == [2222.0, 0], v)
chk("...y el navegador lo recibe (`set_value`, trampa nº31)",
    sv(at, "rc_lfkk") is True and sv(at, "rc_n2500") is True,
    (sv(at, "rc_lfkk"), sv(at, "rc_n2500")))

at = rieles("PRJ-A", v540=True)
num(at, "rc_n2500", 3)
v = boton(at, "cerrar")
chk("la sonda VE el fallo: con el `al_pintar` de v540, cerrar la jornada borra lo tecleado "
    "(trampa nº12)", v[1] == 0, v)

# ═════════════════════════════════════════════════════════════════
sec("2. Las otras transiciones")
at = rieles("")
v = num(at, "rc_lfkk", 777.0)
v = boton(at, "fichar A")
chk("sin obra → A: manda el plano de A y lo tecleado sin obra se olvida (decisión de v535), "
    "también en el navegador", v == [1111.0, 0] and sv(at, "rc_lfkk") is True, v)

at = rieles("PRJ-A")
num(at, "rc_n2500", 3)
at.session_state["pg"] = "otra"
corre(at)
boton(at, "cerrar")                                   # cierra la jornada estando FUERA
at.session_state["pg"] = "rieles"
v = V(corre(at))
chk("salir de Rieles con A, cerrar la jornada fuera y volver SIN obra: se conserva", v[1] == 3, v)
v = boton(at, "fichar B")
chk("...y en cuanto ficha en otra obra (B), se olvida", v == [2222.0, 0], v)

at = rieles("PRJ-A")
num(at, "rc_n2500", 3)
at.session_state["pg"] = "otra"
corre(at)
boton(at, "fichar B")
at.session_state["pg"] = "rieles"
v = V(corre(at))
chk("salir con A y volver con B: se olvida (como siempre)", v == [2222.0, 0], v)

at = rieles("")
at.session_state["cargar_sin_obra"] = True
v = V(corre(at))
chk("cargado a propósito sin obra conocida (`respetar` sin obra)", v[1] == 4, v)
v = boton(at, "fichar B")
chk("...lo ADOPTA la primera obra real: fichar en B no lo borra", v[1] == 4, v)

# ═════════════════════════════════════════════════════════════════
sec("3. El Survey, cerrando la jornada sin salir")
at = AppTest.from_string(GUION, default_timeout=120)
at.session_state["obra"] = "PRJ-A"
at.session_state["pg"] = "survey"
at.session_state["ver"] = ["inp_BS", "inp_BSR", "ns"]
v = V(corre(at))
chk("de partida: obra A, BS y NS de su plano", v[0] == 1326.0 and v[2] == 3, v)
v = num(at, "inp_BSR", 1330.0)
v = boton(at, "cerrar")
chk("⚠️ cerrar la jornada no borra el Survey (antes: BS, BSR y NS a cero)",
    v == [1326.0, 1330.0, 3], v)
v = boton(at, "fichar A")
chk("...y volver a fichar en la misma obra lo conserva", v == [1326.0, 1330.0, 3], v)
at = AppTest.from_string(GUION, default_timeout=120)
at.session_state["obra"] = "PRJ-A"
at.session_state["pg"] = "survey"
at.session_state["ver"] = ["inp_BS", "inp_BSR", "ns"]
corre(at)
num(at, "inp_BSR", 1330.0)
at.session_state["pg"] = "otra"
corre(at)
boton(at, "fichar B")
at.session_state["pg"] = "survey"
_ok = True
try:
    v = V(corre(at))
except SystemExit as e:
    _ok, v = False, str(e)
chk("salir del Survey con A y volver con B: se olvida lo de A y manda el plano de B (como "
    "antes de v541), sin excepción", _ok and v[0] == 1500.0 and v[1] == 0.0 and v[2] == 5, v)
chk("...y el nº de paradas sigue siendo un ENTERO (un 5.0 cambiaría el tipo del widget)",
    _ok and type(at.number_input(key="ns").value) is int,
    _ok and type(at.number_input(key="ns").value))
at = AppTest.from_string(GUION, default_timeout=120)
at.session_state["obra"] = "PRJ-A"
at.session_state["pg"] = "survey"
at.session_state["v540"] = True
at.session_state["ver"] = ["inp_BS", "inp_BSR", "ns"]
corre(at)
num(at, "inp_BSR", 1330.0)
v = boton(at, "cerrar")
chk("la sonda VE el fallo en el Survey: con el `al_pintar` de v540, cerrar la jornada lo "
    "borraba", v[1] in (0, 0.0, None), v)

# ═════════════════════════════════════════════════════════════════
sec("4. La regla, en el código")
import ast                                                         # noqa: E402

_f = next(n for n in ast.parse(_fuente("core/estado_vivo.py")).body
          if isinstance(n, ast.FunctionDef) and n.name == "al_pintar")
_src = ast.unparse(_f)
chk("`al_pintar` solo olvida con una obra REAL distinta de la última real",
    "if obra and ult_real != obra:" in _src and "ult_obra" not in _src, _src[-400:])
from core import estado_vivo as EV                                 # noqa: E402

_init = next(n for n in ast.parse(_fuente("core/survey_ui.py")).body
             if isinstance(n, ast.FunctionDef) and n.name == "init_state")
_ns0 = [n.value.value for n in ast.walk(_init) if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Subscript)
        and isinstance(n.targets[0].slice, ast.Constant) and n.targets[0].slice.value == "ns"
        and isinstance(n.value, ast.Constant)]
chk("el valor por defecto del nº de paradas es el MISMO entero con que nace en el Survey "
    "(`init_state`)", _ns0 == [EV.DEFECTOS.get("ns")] and type(EV.DEFECTOS.get("ns")) is int,
    (_ns0, EV.DEFECTOS.get("ns")))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
