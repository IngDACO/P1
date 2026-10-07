# -*- coding: utf-8 -*-
"""v539 · LO REABIERTO ES DE LA OBRA DEL CÁLCULO.

⚠️ El fallo, introducido en v535 y encontrado ensayando las pantallas del admin con los
cálculos REALES de 88 walker (PRJ-0002): el admin usaba Belting con la obra A, iba a la
obra B → Files → «Reopen in the tool» (los valores se cargaban bien y el selector quedaba
en «no project») y elegía B en el selector —lo natural para volver a guardarlo—. La regla
de v535 («de X a Y sin salir, se olvida») tomaba la última obra de la herramienta, A, y
borraba lo medido sin aviso: HGPR 1547 → 0, 2 buffers → 1, plantilla 770 → 0. Con la
herramienta sin usar antes, nada se perdía (por eso no salía en los guardianes de v535).
«Rebuild the project in the Survey» tenía el mismo hueco: el plano pisaba lo reconstruido.

Ahora quien carga valores dice de qué obra son (`respetar(h, obra)`): elegir después ESA
obra no es un cambio; elegir otra sí (la regla de v535 sigue en pie).

Lo que protege, EJECUTANDO la pantalla real de Rieles y la del Survey con el selector del
admin, con la sonda validada contra el código de v538 (trampa nº12).
"""
import ast
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
from core import estado_vivo, plan_ui, plan_store, plan_data, tool_save_ui, projects as P
from core import rail_cut_ui as R, survey_ui as S
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm",
                            "grupo": "g"}
PROYS = [{"ID": i, "Name": "Obra " + i[-1], "Group": "g"} for i in ("PRJ-A", "PRJ-B", "PRJ-C")]
PLANOS = {"PRJ-A": {"lfkk": 1111.0, "lfgk": 911.0, "params": {"BS": 1326.0}, "ns": 3},
          "PRJ-B": {"lfkk": 2222.0, "lfgk": 922.0, "params": {"BS": 1500.0}, "ns": 5},
          "PRJ-C": {"lfkk": 3333.0, "lfgk": 933.0, "params": {"BS": 1700.0}, "ns": 7}}
# Un cálculo de Rieles guardado en la obra B, con el LFKK corregido a mano y el botón dentro.
CALC = {"ID": "CAL-B", "ProjectID": "PRJ-B", "Tool": "rieles",
        "DataJSON": json.dumps({"entradas": {"rc_lfkk": 2250.0, "rc_lfgk": 922.0,
                                             "rc_n2500": 4, "rc_calc1": True}})}
P.is_configured = lambda: True
P.list_projects = lambda grupo=None, **k: [dict(p) for p in PROYS]
P.head_installers_label = lambda *a, **k: "Ing"
plan_data.del_proyecto = lambda pid: json.loads(json.dumps(PLANOS.get(pid, {})))
plan_data.resumen = lambda d: "plano"
plan_store.selector = lambda *a, **k: None
R.render_guardar = lambda **k: None
R.tool_pdf = lambda *a, **k: b""


def _al_pintar_v538(herramienta, obra):
    """La de v538, copiada: la sonda tiene que VER el fallo con ella."""
    E = estado_vivo
    h, obra = str(herramienta), str(obra or "")
    n = int(st.session_state.get(E._PASADA, 0) or 0)
    antes = st.session_state.get(E._VISTA + h)
    ult_real = (antes[2] if antes and len(antes) > 2 else "") if antes else ""
    st.session_state[E._VISTA + h] = (n, obra, obra or ult_real)
    if st.session_state.pop(E._RESPETAR + h, False) or not antes:
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
estado_vivo.al_pintar = (_al_pintar_v538 if st.session_state.get("v538")
                         else estado_vivo._al_pintar_real)
S.init_state()
estado_vivo.pasada()
if st.session_state.pop("reabrir", None):
    # Files → «Reopen in the tool» (projects_ui), en una pasada de OTRA pantalla.
    tool_save_ui.pedir_reapertura(CALC, "rieles", "x")
    if st.session_state.get("sin_obra"):      # un reabrir pedido con el código de antes
        st.session_state[tool_save_ui._PENDIENTE].pop("obra", None)
    st.session_state.pop("_admin_nav_pending", None)
_rb = st.session_state.pop("reconstruir", None)
if _rb:
    # Lo que hace «Load this project into the Survey» (projects_ui), en otra pantalla:
    # BS corregido a mano (el plano de B dice 1500), BSR medido y 4 paradas.
    estado_vivo.respetar("sv", _rb)
    st.session_state["inp_BS"] = 1600.0
    st.session_state["inp_BSR"] = 1330.0
    st.session_state["ns"] = 4
pg = st.session_state.get("pg", "rieles")
if pg == "rieles":
    R.render_rail_cut_tab()
elif pg == "survey":
    S.render_survey_tab("administrator", "g")
st.markdown("V=" + json.dumps([st.session_state.get(k) for k in st.session_state.get("ver", [])]))
''' % RAIZ

NADA = "— no project (load the drawing by hand) —"


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def V(at):
    return json.loads(next(m.value for m in at.markdown if m.value.startswith("V="))[2:])


def elige(at, key, pid):
    at.selectbox(key="pl_prj_" + key).set_value(("Obra %s (%s)" % (pid[-1], pid)) if pid else NADA)
    return V(corre(at))


def pasa(at, **kv):
    for k, v in kv.items():
        at.session_state[k] = v
    return V(corre(at))


def rieles(previa="PRJ-A", **flags):
    """Rieles usada (o no) con otra obra; Files → reabrir el cálculo de B; vuelve a Rieles."""
    at = AppTest.from_string(GUION, default_timeout=120)
    at.session_state["ver"] = ["rc_lfkk", "rc_lfgk", "rc_n2500"]
    for k, v in flags.items():
        at.session_state[k] = v
    at.session_state["pg"] = "rieles" if previa else "otra"
    corre(at)
    if previa:
        elige(at, "rc", previa)
        at.number_input(key="rc_n2500").set_value(3)
        corre(at)
    pasa(at, pg="otra", reabrir=True)
    v = pasa(at, pg="rieles")
    return at, v


REAB = [2250.0, 922.0, 4]

# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Reabrir un cálculo de la obra B con Rieles usada antes en la A (selector del admin)")
at, v = rieles()
chk("se reabre con lo guardado (LFKK corregido a 2250, n2500 = 4) y lo avisa",
    v == REAB and any("CAL-B" in i.value for i in at.info), v)
chk("⚠️ elige SU obra (B) en el selector: lo reabierto SE QUEDA (v538: LFKK al plano y "
    "n2500 a 0)", elige(at, "rc", "PRJ-B") == REAB, V(at))
chk("...y elegir OTRA obra (C) sí es un cambio: manda su plano y lo de B se olvida (v535)",
    elige(at, "rc", "PRJ-C") == [3333.0, 933.0, 0], V(at))
at, v = rieles()
chk("⚠️ elegir C JUSTO después de reabrir (sin pasar por B) también es un cambio: lo "
    "reabierto es de B, no de «ninguna obra»",
    v == REAB and elige(at, "rc", "PRJ-C") == [3333.0, 933.0, 0], V(at))

at, v = rieles(previa="")
chk("control: con Rieles sin usar antes, elegir B tras reabrir también lo conserva",
    v == REAB and elige(at, "rc", "PRJ-B") == REAB, V(at))

at, v = rieles(sin_obra=True)
chk("un reabrir pedido ANTES del despliegue (sin la obra): elegir B no borra nada",
    v == REAB and elige(at, "rc", "PRJ-B") == REAB, V(at))

at, v = rieles(v538=True)
_v538 = elige(at, "rc", "PRJ-B")
chk("la sonda VE el fallo: con el `al_pintar` de v538, elegir B borra lo reabierto "
    "(trampa nº12)", v == REAB and _v538 != REAB, _v538)

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ «Rebuild the project in the Survey» con el Survey usado antes en otra obra")


def survey(**flags):
    at = AppTest.from_string(GUION, default_timeout=120)
    at.session_state["ver"] = ["inp_BS", "inp_BSR", "ns"]
    for k, v in flags.items():
        at.session_state[k] = v
    at.session_state["pg"] = "survey"
    corre(at)
    v0 = elige(at, "sv", "PRJ-A")
    pasa(at, pg="otra", reconstruir="PRJ-B")
    return at, v0, pasa(at, pg="survey")


at, v0, v = survey()
chk("de partida, el Survey con la obra A (BS 1326 y 3 paradas de su plano)",
    v0[0] == 1326.0 and v0[2] == 3, v0)
chk("se reconstruye la B (BS corregido 1600, BSR 1330, 4 paradas) y llega entero",
    v == [1600.0, 1330.0, 4], v)
chk("⚠️ elige B en el selector: el plano de B NO pisa lo reconstruido (v538: BS 1500 y 5 "
    "paradas)", elige(at, "sv", "PRJ-B") == [1600.0, 1330.0, 4], V(at))
chk("...elegir OTRA obra (C) sí manda su plano, y lo medido a mano se queda (Duplicate)",
    elige(at, "sv", "PRJ-C") == [1700.0, 1330.0, 7], V(at))
at, v0, v = survey()
chk("⚠️ elegir C JUSTO después de reconstruir B también manda el plano de C",
    v == [1600.0, 1330.0, 4] and elige(at, "sv", "PRJ-C") == [1700.0, 1330.0, 7], V(at))
at, v0, v = survey(v538=True)
_v538 = elige(at, "sv", "PRJ-B")
chk("la sonda VE el fallo: con el `al_pintar` de v538 el plano de B pisa lo reconstruido",
    v == [1600.0, 1330.0, 4] and _v538[0] == 1500.0, _v538)

# ═════════════════════════════════════════════════════════════════
sec("3. Quien carga valores dice de qué obra son")
_tsu = ast.parse(_fuente("core/tool_save_ui.py"))
_f = {n.name: ast.unparse(n) for n in _tsu.body if isinstance(n, ast.FunctionDef)}
chk("«reabrir» guarda la obra del cálculo (su ProjectID) junto a lo pendiente",
    "'obra': str(fila.get('ProjectID', '') or '')" in _f.get("pedir_reapertura", ""))
chk("...y al cargarlo se la pasa a `respetar`",
    "estado_vivo.respetar(_PREFIJO.get(herramienta, '').rstrip('_'), pend.get('obra', ''))"
    in _f.get("aplicar_restauracion", ""))
_pu = ast.parse(_fuente("core/projects_ui.py"))
_llam = [ast.unparse(n) for n in ast.walk(_pu) if isinstance(n, ast.Call)
         and ast.unparse(n.func) == "_ev.respetar"]
chk("«Rebuild the project in the Survey» dice que lo cargado es de ESE proyecto",
    _llam == ["_ev.respetar('sv', pid)"], _llam)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
