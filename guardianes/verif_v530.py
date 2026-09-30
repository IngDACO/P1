# -*- coding: utf-8 -*-
"""v530 · ELEGIR OTRA SOLUCIÓN ACTIVA YA NO DEJA EL SURVEY EN UN BUCLE.

Desde el 19/07 (la «solución activa elegible»), elegir en el desplegable cualquier solución
que no fuera la recomendada dejaba la página en un bucle de pasadas SIN FIN: la lista se
ordenaba con la ACTIVA primero, así que al elegir otra se reordenaba y la POSICIÓN guardada
en el desplegable pasaba a señalar OTRA solución, que el código tomaba como elección nueva.
Medido con el survey real: más de 25 pasadas seguidas eligiendo la 2.ª o la 3.ª, con la
solución que usan diagramas, plomado e informe cambiando en cada una.

Y tras «Recalculate», la solución activa y los pisos se borraban con `pop`: el servidor
volvía a los de por defecto pero el navegador no se enteraba (el fallo de la caja del parte,
v529) — y en el siguiente clic DEVOLVÍA la selección vieja. Ahora cada cálculo lleva su
número y esos widgets, una clave nueva: nacen como widgets nuevos.

Lo que protege, EJECUTANDO `survey_ui.render_survey_tab` con AppTest (el caso de
`fixture_survey`, sin IA, sin correo y con las escrituras prohibidas):
  (a) ⚠️ elegir la 2.ª o la 3.ª cuesta UNA pasada más, no un bucle, y el desplegable se
      queda en la elegida;
  (b) ⚠️ lo que USAN diagramas, plomado e informe es la elegida (`optimizer_result.best`);
  (c) sigue estable en las pasadas siguientes, y se puede volver a la recomendada;
  (d) la estrella y el desplegado de «Solution N» van con la ACTIVA;
  (e) ⚠️ tras «Recalculate», la solución activa y los pisos son widgets NUEVOS (otra
      identidad) con la recomendada y los pisos por defecto, y lo que el navegador devuelva
      de los VIEJOS no cambia nada.
"""
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


from streamlit.testing.v1 import AppTest                          # noqa: E402

TOPE = 25
GUION = r'''
import sys
sys.path.insert(0, r"%s")
sys.path.insert(0, r"%s")
import pandas as pd
import streamlit as st
import fixture_survey as FX
from core import survey_ui as SU


def _prohibido(*a, **k):
    raise RuntimeError("ESCRITURA PROHIBIDA en esta prueba")


if not getattr(SU, "_prueba_v530", False):
    SU._prueba_v530 = True
    SU.generate_interpretation = lambda *a, **k: {"_ok": False}
    SU.generate_user_interpretation = lambda *a, **k: {"_ok": False}
    SU.send_usage_notification = lambda *a, **k: None
    SU.generate_report = lambda *a, **k: None
    SU.plan_ui.selector_proyecto = lambda *a, **k: (None, {})
    SU.toolruns.registrar = _prohibido
    SU.drive_store.upload = _prohibido

st.session_state.setdefault("auth", {"usuario": "dacox", "rol": "administrator",
                                     "grupo": "cliente1"})
st.session_state["pasadas"] = st.session_state.get("pasadas", 0) + 1
if st.session_state["pasadas"] > %d:
    st.markdown("CORTADO")
    st.stop()
SU.init_state()
if not st.session_state.get("_fx"):
    st.session_state["_fx"] = True
    for k, v in FX.PARAMS.items():
        if k in SU.PDF_PARAMS or k in SU.USER_ONLY:
            st.session_state["inp_%%s" %% k] = float(v)
    st.session_state["cfg_omega_side"] = FX.PARAMS["OMEGA_SIDE"]
    st.session_state["cfg_offset_side"] = FX.PARAMS["OFFSET_SIDE"]
    st.session_state["cfg_wall_yn"] = "N"
    st.session_state["ns"] = FX.PARAMS["NS"]
    st.session_state["survey_df"] = pd.DataFrame(
        [{c: r[c] for c in SU.SURVEY_COLS} for r in FX.MATRIZ])
SU.render_survey_tab("administrator", "cliente1")
''' % (RAIZ, AQUI, TOPE)


def _pasar(at, fn):
    """Hace la acción y devuelve cuántas pasadas costó."""
    at.session_state["pasadas"] = 0
    fn()
    return at.session_state["pasadas"]


def _sb(at):
    return next((s for s in at.selectbox if "Active solution" in str(s.label)), None)


def _ms(at):
    return next((m for m in at.multiselect if str(m.label) == "Floors"), None)


def _activa(at):
    b = at.session_state["calc_results"]["optimizer_result"]["best"]
    return "RL %+.1f · FB %+.1f" % (b["rl"], b.get("fb_applied", b["fb"]))


def _estrella(at):
    return [e.label for e in at.expander if ":material/star:" in str(e.label)
            and "Solution" in str(e.label)]


at = AppTest.from_string(GUION, default_timeout=180)
at.run()
chk("el survey pinta sin errores", not at.exception, [e.value for e in at.exception][:1])
_b = next((x for x in at.button if "Calculate and see the results" in str(x.proto.label)), None)
chk("...con su botón de calcular", _b is not None)
_n = _pasar(at, lambda: (_b.click(), at.run()))
chk("calcular: sin errores y en 2 pasadas (la del clic y el cambio de fase)",
    not at.exception and _n == 2, (_n, [e.value for e in at.exception][:1]))
sb = _sb(at)
OPC = list(sb.options) if sb else []
chk("hay varias soluciones que elegir (si no, lo de abajo no prueba nada)", len(OPC) >= 3, OPC)
RECO = OPC[0] if OPC else ""
chk("al abrir, la activa es la recomendada, la primera", sb is not None and sb.value == 0
    and _activa(at) in RECO, (sb.value if sb else None, _activa(at), RECO))

for _pos, _nombre in ((2, "3.ª"), (1, "2.ª")):
    sec("⚠️ Elegir la %s" % _nombre)
    _n = _pasar(at, lambda: _sb(at).set_value(_pos).run())
    chk("⚠️ cuesta UNA pasada más, no un bucle (%d pasadas; tope %d)" % (_n, TOPE),
        _n == 2 and not [m for m in at.markdown if m.value == "CORTADO"], _n)
    chk("sin errores", not at.exception, [e.value for e in at.exception][:1])
    chk("el desplegable se queda en la elegida", _sb(at) is not None and _sb(at).value == _pos,
        _sb(at).value if _sb(at) else None)
    chk("⚠️ lo que USAN diagramas, plomado e informe es la elegida (%s)" % OPC[_pos],
        _activa(at) in OPC[_pos], (_activa(at), OPC[_pos]))
    chk("la lista NO se reordena (la recomendada sigue primera)",
        list(_sb(at).options) == OPC, list(_sb(at).options))
    _e = _estrella(at)
    chk("la estrella va con la activa («Solution %d»)" % (_pos + 1),
        len(_e) == 1 and ("Solution %d " % (_pos + 1)) in _e[0], _e)
    _n = _pasar(at, lambda: at.run())
    chk("...y sigue estable en la pasada siguiente (1 pasada, misma activa)",
        _n == 1 and _activa(at) in OPC[_pos], (_n, _activa(at)))

sec("Volver a la recomendada")
_n = _pasar(at, lambda: _sb(at).set_value(0).run())
chk("se vuelve en una pasada más, y la activa es otra vez la recomendada",
    _n == 2 and _activa(at) in RECO, (_n, _activa(at)))

# ═════════════════════════════════════════════════════════════════
sec("⚠️ Recalcular: la solución activa y los pisos nacen NUEVOS, con lo de por defecto")
_sb(at).set_value(2).run()
at.radio(key="diag_modo").set_value("Elegir").run()
_ms(at).set_value([1, 2]).run()
K_SOL, K_PIS = _sb(at).key, _ms(at).key
ID_SOL = _sb(at).proto.id
chk("antes: la 3.ª elegida y los pisos 2 y 3",
    _activa(at) in OPC[2] and _ms(at).value == [1, 2], (_activa(at), _ms(at).value))
_r = next((x for x in at.button if "Recalculate with the current data" in str(x.proto.label)),
          None)
chk("hay botón de recalcular", _r is not None)
_pasar(at, lambda: (_r.click(), at.run()))
chk("recalcular: sin errores", not at.exception, [e.value for e in at.exception][:1])
chk("vuelve la recomendada (es lo que usan los diagramas)", _activa(at) in RECO, _activa(at))
chk("⚠️ el desplegable es un widget NUEVO (otra clave, otra identidad): el navegador no "
    "tiene nada guardado para él",
    _sb(at) is not None and _sb(at).key != K_SOL and _sb(at).proto.id != ID_SOL,
    (K_SOL, _sb(at).key if _sb(at) else None))
chk("...y enseña la recomendada", _sb(at) is not None and _sb(at).value == 0,
    _sb(at).value if _sb(at) else None)
# El navegador conserva lo de la clave VIEJA y lo manda en el siguiente clic: se simula.
at.session_state[K_SOL] = 2
at.run()
chk("⚠️ lo que el navegador devuelva de la clave VIEJA no cambia la activa",
    _activa(at) in RECO and _sb(at).value == 0, (_activa(at), _sb(at).value))
at.radio(key="diag_modo").set_value("Elegir").run()
chk("⚠️ los pisos también nacen NUEVOS, con los de por defecto (no los 2 y 3 de antes)",
    _ms(at) is not None and _ms(at).key != K_PIS and _ms(at).value != [1, 2],
    (K_PIS, _ms(at).key if _ms(at) else None, _ms(at).value if _ms(at) else None))
_avisos = [w.value for w in at.warning if "Session State" in str(w.value)]
chk("sin el aviso de «valor por defecto y Session State a la vez»", not _avisos, _avisos)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
