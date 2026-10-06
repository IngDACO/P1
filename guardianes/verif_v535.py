# -*- coding: utf-8 -*-
"""v535 · LO QUE QUEDABA PENDIENTE DE v534 («no dejes nada pendiente»).

1. ⚠️ CAMBIAR DE OBRA SIN SALIR DE LA HERRAMIENTA. El campo cambia de obra con el fichaje del
   menú lateral sin dejar Rieles; el admin, con el selector de obra. Hasta v535 no se
   olvidaba nada y `plan_ui.aplicar` solo rellena lo vacío: el LFKK de la obra X seguía
   bajo el nombre de la Y. Ahora manda el plano de Y y lo tecleado para X se olvida — salvo
   en el Survey, donde «Duplicate for the next lift» conserva A PROPÓSITO lo medido: ahí
   manda el plano de Y solo en lo que el plano trae.
2. ⚠️ LOS DATOS DE TRABAJO SON DE UNA CUENTA. Cerrar sesión solo quitaba `auth`: los
   resultados, lo tecleado y el historial del asistente se quedaban en la pestaña y otra
   cuenta que entrara en ella los veía. Ahora, si entra OTRA cuenta, la sesión empieza
   limpia; la MISMA que vuelve (tras salir o tras una expulsión) encuentra lo suyo.
3. Los dibujos miden lo que mide su contenido: con alto fijo, en pantalla estrecha quedaba
   un hueco en blanco debajo (medido en producción: 379 px de cronograma en 648).
4. El nº de paradas del plano no se aplicaba nunca al elegir obra: el 2 por defecto no es
   «vacío». Funcionaba por ACCIDENTE cuando Streamlit borraba el campo al salir (v534 dejó de
   borrarlo). `aplicar(..., neutros={"ns": 2})`.
5. Decisión documentada: pasar de «sin obra» a una obra AL VOLVER cuenta como cambio (como
   siempre). Guardar un cálculo no exige fichar, así que no se pierde nada por fichar.

Lo que protege, EJECUTANDO (la pantalla real de Rieles, la de verdad de `plan_ui` y la de
`estado_vivo`), con la sonda validada contra el fallo en cada caso (trampa nº12).
"""
import ast
import io
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

# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Cambiar de obra SIN salir: manda el plano de la nueva (la pantalla real de Rieles)")
GUION_R = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo, plan_ui, plan_store, plan_data, tool_save_ui, rail_cut_ui as R
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"lfkk": 1111.0, "lfgk": 911.0}, "PRJ-B": {"lfkk": 2222.0, "lfgk": 922.0}}
plan_ui.P.is_configured = lambda: True
_o = st.session_state.get("obra", "")
plan_ui._proyecto_fichado = lambda a: ({"ID": _o, "Name": _o} if _o else None)
plan_data.del_proyecto = lambda pid: dict(PLANOS.get(pid, {}))
plan_data.resumen = lambda d: "plano"
plan_store.selector = lambda *a, **k: None
R.render_guardar = lambda **k: None
R.tool_pdf = lambda *a, **k: b""
# ⚠️ Los guiones comparten proceso: lo que se sustituye se repone SIEMPRE (v534).
if not hasattr(estado_vivo, "_al_pintar_real"):
    estado_vivo._al_pintar_real = estado_vivo.al_pintar
estado_vivo.al_pintar = ((lambda h, o: False) if st.session_state.get("sin_olvido")
                         else estado_vivo._al_pintar_real)
estado_vivo.pasada()
if st.session_state.get("pg", "rieles") == "rieles":
    R.render_rail_cut_tab()
st.markdown("V=%%r" %% ((st.session_state.get("rc_lfkk"), st.session_state.get("rc_n2500")),))
''' % RAIZ


def _v(at):
    return next(m.value for m in at.markdown if m.value.startswith("V="))


def _obra(at, o):
    at.session_state["obra"] = o
    at.run()
    return _v(at)


at = AppTest.from_string(GUION_R, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.run()
at.number_input(key="rc_n2500").set_value(3).run()
chk("de partida: obra A, su LFKK (1111) y lo tecleado (3)", _v(at) == "V=(1111.0, 3)", _v(at))
chk("⚠️ el campo ficha en la obra B SIN salir de Rieles: manda el plano de B (2222) y lo "
    "tecleado para A se olvida", _obra(at, "PRJ-B") == "V=(2222.0, 0)", _v(at))
at.number_input(key="rc_n2500").set_value(5).run()
chk("...sale de la obra (sin obra) y sigue en Rieles: no se olvida nada",
    _obra(at, "") == "V=(2222.0, 5)", _v(at))
chk("⚠️ ...y de ahí entra en la A: también cuenta como cambio (B → ninguna → A)",
    _obra(at, "PRJ-A") == "V=(1111.0, 0)", _v(at))
at.number_input(key="rc_n2500").set_value(7).run()
_obra(at, "")
chk("A → ninguna → A NO es un cambio: lo tecleado se queda", _obra(at, "PRJ-A") == "V=(1111.0, 7)",
    _v(at))
chk("varias pasadas con la misma obra no olvidan nada", _obra(at, "PRJ-A") == "V=(1111.0, 7)",
    _v(at))

at = AppTest.from_string(GUION_R, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.session_state["sin_olvido"] = True
at.run()
chk("la sonda VE el fallo de v534: sin mirar la obra, al pasar a B sin salir se queda el "
    "LFKK de A (trampa nº12)", _obra(at, "PRJ-B") == "V=(1111.0, 0)", _v(at))

# ── La decisión documentada: «sin obra» → obra, AL VOLVER, cuenta como cambio ──
at = AppTest.from_string(GUION_R, default_timeout=90)
at.session_state["obra"] = ""
at.run()
at.number_input(key="rc_lfkk").set_value(1200.0).run()
at.session_state["pg"] = "otra"
at.run()
at.run()
at.session_state["obra"] = "PRJ-A"
at.session_state["pg"] = "rieles"
at.run()
chk("decisión v535: tecleado sin obra, se ficha en A y se vuelve → manda el plano de A "
    "(como siempre; guardar no exige fichar, así que no se pierde nada por fichar)",
    _v(at) == "V=(1111.0, 0)", _v(at))

# ═════════════════════════════════════════════════════════════════
sec("1b. ⚠️ El Survey conserva lo MEDIDO (Duplicate) y solo pisa lo que trae el plano")
GUION_S = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo, plan_ui, plan_data
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"params": {"BS": 1326.0}, "ns": 3}, "PRJ-B": {"params": {"BS": 1500.0}, "ns": 5}}
plan_ui.P.is_configured = lambda: True
_o = st.session_state.get("obra", "")
plan_ui._proyecto_fichado = lambda a: ({"ID": _o, "Name": _o} if _o else None)
plan_data.del_proyecto = lambda pid: dict(PLANOS.get(pid, {}))
plan_data.resumen = lambda d: "plano"
if not hasattr(estado_vivo, "_al_pintar_real"):
    estado_vivo._al_pintar_real = estado_vivo.al_pintar
estado_vivo.al_pintar = estado_vivo._al_pintar_real
if "ns" not in st.session_state:
    st.session_state["ns"] = 2
estado_vivo.pasada()
_prj, _plano = plan_ui.selector_proyecto("sv")
if st.session_state.get("sin_forzar"):
    st.session_state.pop(plan_ui._FORZAR, None)     # la sonda: `aplicar` sin el aviso
if _plano:
    plan_ui.aplicar(_plano, {"params.BS": "inp_BS", "ns": "ns"}, neutros={"ns": 2})
st.number_input("BS", key="inp_BS")
st.number_input("BSR", key="inp_BSR")
st.number_input("NS", min_value=2, max_value=50, step=1, key="ns")
st.markdown("V=%%r" %% ((st.session_state.get("inp_BS"), st.session_state.get("inp_BSR"),
                       st.session_state.get("ns")),))
''' % RAIZ
at = AppTest.from_string(GUION_S, default_timeout=60)
at.session_state["obra"] = "PRJ-A"
at.run()
at.number_input(key="inp_BSR").set_value(1330.0).run()
chk("de partida: obra A, BS de su plano (1326), NS del plano (3) y BSR medido (1330)",
    _v(at) == "V=(1326.0, 1330.0, 3)", _v(at))
chk("⚠️ el Survey pasa a la obra B sin salir: BS y NS vienen del plano de B (1500, 5) y el "
    "BSR medido a mano SE QUEDA («Duplicate for the next lift»)",
    _obra(at, "PRJ-B") == "V=(1500.0, 1330.0, 5)", _v(at))
chk("el nº de paradas sigue siendo un entero (el widget no cambia de tipo)",
    isinstance(at.number_input(key="ns").value, int), type(at.number_input(key="ns").value))
at = AppTest.from_string(GUION_S, default_timeout=60)
at.session_state["obra"] = "PRJ-A"
at.session_state["sin_forzar"] = True
at.run()
chk("la sonda VE el fallo: sin el aviso a `aplicar`, el BS de A (1326) se queda bajo B",
    _obra(at, "PRJ-B").startswith("V=(1326.0"), _v(at))

# ── El aviso de `selector_proyecto` a `aplicar` no se hereda ──
_tpl = ast.parse(_fuente("core/plan_ui.py"))
_fsel = next(n for n in _tpl.body if isinstance(n, ast.FunctionDef)
             and n.name == "selector_proyecto")
_fapl = next(n for n in _tpl.body if isinstance(n, ast.FunctionDef) and n.name == "aplicar")
chk("`selector_proyecto` escribe el aviso SIEMPRE (no solo cuando hay cambio): un aviso viejo "
    "no lo hereda otra herramienta",
    "st.session_state[_FORZAR] = bool(estado_vivo.al_pintar(key" in ast.unparse(_fsel))
_tsv = ast.unparse(ast.parse(_fuente("core/survey_ui.py")))
chk("el Survey cuenta el NS neutro (2) como vacío UNA vez por obra (si no, quien pusiera 2 a "
    "mano lo vería volver al del plano en cada pasada)",
    "_neutro_sv = {'ns': 2} if st.session_state.get('_sv_ns_obra') != _pid_sv else None" in _tsv
    and "plan_ui.aplicar(_plano_sv, _mapa_sv, neutros=_neutro_sv)" in _tsv
    and "st.session_state['_sv_ns_obra'] = _pid_sv" in _tsv)
chk("...y «Start a new survey» vuelve a dejar que el NS del plano mande",
    "'_sv_ns_obra'" in _tsv.split("_reset_survey")[1].split("_dup_survey")[0])
chk("...y `aplicar` lo CONSUME (pop) al empezar",
    "st.session_state.pop(_FORZAR, False)" in ast.unparse(_fapl.body[1]), ast.unparse(_fapl.body[1]))

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ Los datos de trabajo son de UNA cuenta")
GUION_C = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo
if not st.session_state.get("_sembrado"):
    st.session_state["_sembrado"] = True
    for k, v in {"calc_results": {"x": 1}, "chat_history": ["hola"], "inp_BS": 1326.0,
                 "rc_res": {"y": 2}, "survey_df": "matriz", "initialized": True,
                 "_lang": "es", "_cookie_mgr": "gestor", "copex_cookie_get": {"c": 1},
                 "_flash_cola": [("info", "hola")], "_remember_session": True,
                 "_no_cookie_restore": True, "_hb_last": 5.0}.items():
        st.session_state[k] = v
u = st.session_state.get("quien", "ana")
st.session_state["auth"] = {"usuario": u}
limpio = estado_vivo.de_la_cuenta(u)
st.markdown("L=%%r" %% (limpio,))
st.markdown("K=%%r" %% (sorted(k for k in st.session_state.keys()
                              if k not in ("quien", "_sembrado")),))
''' % RAIZ
at = AppTest.from_string(GUION_C, default_timeout=60)
at.run()
_k1 = next(m.value for m in at.markdown if m.value.startswith("K="))
chk("la primera cuenta de la sesión no borra nada (no había de quién)",
    "L=False" in [m.value for m in at.markdown] and "'calc_results'" in _k1, _k1)
at.run()
chk("la MISMA cuenta en otra pasada no borra nada",
    "L=False" in [m.value for m in at.markdown]
    and "'calc_results'" in next(m.value for m in at.markdown if m.value.startswith("K=")))
at.session_state["quien"] = "beto"
at.run()
_k3 = next(m.value for m in at.markdown if m.value.startswith("K="))
chk("⚠️ entra OTRA cuenta: se borran los resultados, el historial del asistente y lo tecleado",
    "L=True" in [m.value for m in at.markdown] and not any(
        "'%s'" % k in _k3 for k in ("calc_results", "chat_history", "inp_BS", "rc_res",
                                    "survey_df", "initialized")), _k3)
chk("...y se conservan la identidad, el idioma, el gestor de la cookie, sus componentes y "
    "los mensajes pendientes",
    all("'%s'" % k in _k3 for k in ("auth", "_lang", "_cookie_mgr", "copex_cookie_get",
                                    "_flash_cola", "_remember_session", "_no_cookie_restore",
                                    "_hb_last", "_ev_cuenta")), _k3)
at.session_state["quien"] = "ana"
at.run()
chk("vuelve la cuenta anterior: también es un cambio (lo de «beto» no es suyo)",
    "L=True" in [m.value for m in at.markdown])

# ── app.py: tras el login, antes de conservar nada, y vuelve a poner el estado base ──
_tapp = ast.parse(_fuente("app.py"))
_pos = {}
for _i, _n in enumerate(_tapp.body):
    _src = ast.unparse(_n)
    if isinstance(_n, ast.If) and "render_login()" in ast.unparse(_n.test):
        _pos["login"] = _i
    if isinstance(_n, ast.If) and "de_la_cuenta(" in ast.unparse(_n.test):
        _pos["cuenta"] = _i
        _pos["init"] = [ast.unparse(x) for x in _n.body]
    if isinstance(_n, ast.Expr) and _src.endswith("_estado_vivo.pasada()"):
        _pos["pasada"] = _i
chk("⚠️ app.py mira de quién son los datos en el CUERPO del script, tras el login y ANTES de "
    "conservar las entradas", "cuenta" in _pos
    and _pos.get("login", 9e9) < _pos["cuenta"] < _pos.get("pasada", -1), _pos)
chk("...y si borra, vuelve a poner el estado base (hay lecturas por atributo que revientan "
    "sin él)", _pos.get("init") == ["init_state()"], _pos.get("init"))

# ═════════════════════════════════════════════════════════════════
sec("3. Los dibujos miden lo que mide su contenido")
import streamlit as st                                             # noqa: E402

from core import incrustar                                         # noqa: E402

_cap = []
_oi = st.iframe
st.iframe = lambda h, height=None, **k: _cap.append(height)
try:
    incrustar.dibujo("<svg></svg>", 330)
    incrustar.dibujo("<svg></svg>", 800, scroll=True)
    incrustar.dibujo("<svg></svg>", 52, ajustar=False)
    incrustar.script("<script></script>")
finally:
    st.iframe = _oi
chk("⚠️ un dibujo mide su contenido; la planta con scroll, el cronómetro y el script, fijos",
    _cap == ["content", 800, 52, 1], _cap)
_fijos, _ajust = [], []
for _f in sorted(os.listdir(os.path.join(RAIZ, "core"))) + ["../app.py"]:
    if not _f.endswith(".py"):
        continue
    _t = ast.parse(_fuente(os.path.join("core", _f) if _f != "../app.py" else "app.py"))
    for _n in ast.walk(_t):
        if isinstance(_n, ast.Call) and ast.unparse(_n.func) == "incrustar.dibujo":
            _kw = {k.arg: ast.unparse(k.value) for k in _n.keywords}
            (_fijos if _kw.get("ajustar") == "False" or _kw.get("scroll") == "True"
             else _ajust).append((_f, _n.lineno))
chk("se leyeron los dibujos de la app (no es un paso en vacío)", len(_ajust) >= 15,
    len(_ajust))
chk("⚠️ solo van fijos los dos cronómetros y la planta por pisos con scroll",
    sorted(f for f, _l in _fijos) == ["survey_ui.py", "timeclock_ui.py", "timeclock_ui.py"],
    _fijos)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
