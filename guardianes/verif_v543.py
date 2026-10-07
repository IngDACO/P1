# -*- coding: utf-8 -*-
"""v543 · EL AVISO «EL SURVEY EMPEZÓ DE CERO» SALE EN EL MOMENTO.

⚠️ Visto en producción con la cuenta de campo probando v542: al fichar en otra obra, el
Survey empezaba de cero en el acto, pero el aviso salía UNA PASADA TARDE (en el clic
siguiente). Iba por `flash`, y la shell pinta la cola de `flash` ANTES de que el Survey
encole en esa misma pasada. Por eso se había ido a `flash`: con otro nº de paradas la matriz
se redimensiona con `st.rerun()`, que se lleva un `st.info` pintado antes.

Ahora: una marca en la sesión; el aviso se pinta junto al selector mientras dure, y la marca
se quita solo DESPUÉS del punto en que la matriz puede cortar la pasada. Cortada o no, el
aviso está en la pasada que se ve; y no se queda para la siguiente.

Lo que protege, EJECUTANDO la pantalla real del Survey con el fichaje del menú lateral
(botones que cortan la pasada con `st.rerun()`, como los de verdad).
"""
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

GUION = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo, plan_ui, plan_data, survey_ui as S
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"params": {"BS": 1326.0}, "ns": 3},
          "PRJ-B": {"params": {"BS": 1500.0}, "ns": 5},
          "PRJ-C": {"params": {"BS": 1700.0}, "ns": 3}}
plan_ui.P.is_configured = lambda: True
plan_ui._proyecto_fichado = lambda a: ({"ID": st.session_state["obra"],
                                        "Name": st.session_state["obra"]}
                                       if st.session_state.get("obra") else None)
plan_data.del_proyecto = lambda pid: json.loads(json.dumps(PLANOS.get(pid, {})))
plan_data.resumen = lambda d: "plano"
S.projects_data.head_installers_label = lambda *a, **k: "Ing"
S.init_state()
estado_vivo.pasada()
for etq, o in (("cerrar", ""), ("fichar B", "PRJ-B"), ("fichar C", "PRJ-C")):
    if st.button(etq, key="sb_" + etq):
        st.session_state["obra"] = o
        st.rerun()
S.render_survey_tab("field", "g")
''' % RAIZ

MSG = "started from zero"


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def aviso(at):
    return any(MSG in i.value for i in at.info)


def nuevo():
    at = AppTest.from_string(GUION, default_timeout=120)
    at.session_state["obra"] = "PRJ-A"
    corre(at)
    at.number_input(key="inp_BSR").set_value(1330.0)
    return corre(at)


def boton(at, etq):
    at.button(key="sb_" + etq).click()
    return corre(at)


sec("1. ⚠️ El aviso sale en la pasada en que el Survey empieza de cero")
at = nuevo()
chk("de partida, sin aviso", not aviso(at))
boton(at, "fichar B")
chk("⚠️ A → B (otro nº de paradas: la matriz corta la pasada para cambiar de tamaño): el "
    "Survey empezó de cero Y el aviso está EN ESTA pasada",
    at.number_input(key="inp_BSR").value == 0.0 and at.number_input(key="ns").value == 5
    and aviso(at), (at.number_input(key="inp_BSR").value, [i.value[:40] for i in at.info]))
chk("...no va por `flash` (llegaba una pasada tarde)",
    not any(MSG in str(x[1]) for x in (at.session_state["_flash_cola"]
                                       if "_flash_cola" in at.session_state else [])))
corre(at)
chk("...y en la pasada siguiente ya no está (no se queda colgado)", not aviso(at))

at = nuevo()
boton(at, "fichar C")
chk("A → C (el MISMO nº de paradas: la pasada no se corta): el aviso también, en esta pasada",
    at.number_input(key="inp_BSR").value == 0.0 and aviso(at),
    (at.number_input(key="inp_BSR").value, [i.value[:40] for i in at.info]))
corre(at)
chk("...y tampoco se queda", not aviso(at))

at = nuevo()
boton(at, "cerrar")
chk("cerrar la jornada (sin obra) no es un cambio: sin aviso y lo tecleado sigue",
    not aviso(at) and at.number_input(key="inp_BSR").value == 1330.0)

sec("2. En el código")
_s = _fuente("core/survey_ui.py")
_i_marca = _s.find("st.session_state[_AVISO_CERO] = True")
_i_pinta = _s.find("if st.session_state.get(_AVISO_CERO):")
_i_corte = _s.find("            st.session_state.survey_df = new_df\n            st.rerun()")
_i_quita = _s.find("st.session_state.pop(_AVISO_CERO, None)")
chk("se encontraron la marca, el aviso, el corte de la matriz y la retirada (no es un paso en "
    "vacío)", min(_i_marca, _i_pinta, _i_corte, _i_quita) > 0,
    (_i_marca, _i_pinta, _i_corte, _i_quita))
chk("⚠️ la marca se quita DESPUÉS del punto en que la matriz puede cortar la pasada",
    _i_marca < _i_pinta < _i_corte < _i_quita, (_i_marca, _i_pinta, _i_corte, _i_quita))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
