# -*- coding: utf-8 -*-
"""v608 · LO VISTO EN EL ENSAYO DE v607 + «TELL THE OFFICE» — decisiones del usuario (27/10/2026):
«dale con 3 y 4».

(3) Dos casillas seguidas que salen del MISMO trozo («Finished with rails cabin and cw» → rieles de
    cabina y de contrapeso) repetían la cita debajo de cada una → UNA vez, debajo de la última.
(4) Lo que el agente marca como PROBLEMA se veía y nadie se enteraba → «Tell the office»: el autor
    ve el texto, lo corrige y lo manda (`alerts.report_problem`: alarma + Telegram/correo).

Lo que protege, con el modelo y la alarma SUSTITUIDOS (⚠️ nada llega a personas reales):
  (a) cada problema, UNA vez por parte, con su botón; nada se manda sin pulsar «Send»;
  (b) lo que se manda es lo que el autor dejó en la caja (sus palabras + de qué parte salen);
  (c) ⚠️ lo enviado queda en la lectura: no se ofrece otra vez (ni tras una recarga, ni tras
      «Read it again», ni en otra sesión) y no se avisa dos veces;
  (d) una caja vacía no manda nada; «Cancel» cierra sin mandar; un fallo lo dice y el botón sigue;
  (e) la cita repetida, una sola vez — también en la tarjeta del vocabulario.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test",
                            "rol": "field", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import alerts                                           # noqa: E402
from core import parte_agente as AG                               # noqa: E402

_ORIG = {"clave_api": AG.clave_api, "_llamar": AG._llamar, "report_problem": alerts.report_problem}

APP = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import alerts, clock, daily_log as DL, daily_log_ui as DLU, flash, parte_agente as AG
from core import projects as P, stage_progress as SP, stages as S

PLAN = S.plan_de("Installation", ())
_T, _COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in _COD.items()}
HOY = "2026-10-27"
ss = st.session_state
for _k, _v in (("_rev", {}), ("_cred", []), ("_guard", {}), ("_alertas", [])):
    ss.setdefault(_k, _v)
if not hasattr(AG, "_llam8"):
    AG._llam8 = []
INFO = {"seg": 0.01, "modelo": "claude-sonnet-5-5", "uso": {"in": 1, "out": 1, "cache_r": 0, "cache_w": 0}}
T1 = "Finished with rails cabin and cw\nDropsaw was broken\nMissing bolts and clips"
T2 = "Waiting on the builder\nscaffold in the way"


def _fr(line, text, cl, names=(), q="", r=""):
    return {"line": line, "text": text, "class": cl, "codes": [C[n] for n in names],
            "question": q, "reason": r, "lift": ""}


def _llamar(api_key, texto, fecha, plan, mapa, previa, respuestas, idioma):
    AG._llam8.append(texto)
    if texto == T1:
        return {"fragments": [
            _fr(1, "Finished with rails cabin and cw", "done", ["Install car rails to top", "Install CW rails to top"]),
            _fr(2, "Dropsaw was broken", "problem", r="tool broken"),
            _fr(3, "Missing bolts and clips", "problem", r="missing material"),
            _fr(3, "zz", "unclear", q="What is zz?")]}, INFO
    if texto == T2:
        return {"fragments": [_fr(1, "Waiting on the builder", "not_progress", r="waiting"),
                              _fr(2, "scaffold in the way", "problem", r="blocked")]}, INFO
    return {"fragments": [_fr(1, texto, "done", ["Install headers", "Install frames"])]}, INFO


def _report(pid, grupo, mensaje, creado_por, project_name=""):
    ss["_alertas"].append({"pid": pid, "grupo": grupo, "mensaje": mensaje, "por": creado_por,
                           "obra": project_name})
    if ss.get("_falla_alerta"):
        return False, "quota"
    return True, "ALR-%04d" % (9000 + len(ss["_alertas"]))


AG._llamar = _llamar
AG.clave_api = lambda: ss.get("_clave", "sk-test")
alerts.report_problem = _report
LOGS = [
    {"ID": "LOG-9201", "Date": "2026-10-26", "Author": "campo000", "Created": HOY + " 17:50:00", "Text": T1},
    {"ID": "LOG-9202", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:40:00", "Text": T2},
    {"ID": "LOG-9203", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:30:00",
     "Text": "Installed headers and installed frames"},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001")
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = HOY + " 18:00:00", ss["_rev"][r["ID"]]
        if r["ID"] in ss.get("_hoja", {}):
            _r["Reading"] = ss["_hoja"][r["ID"]]
        out.append(_r)
    return out


def _guardar(d):
    ss["_guard"].update(d)
    return True, len(d)


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = lambda lid, quien, propuestas="": (ss["_rev"].update({lid: quien}) or (True, "ok"))
DL.crear = lambda *a, **k: (True, "LOG-X")
DL.guardar_lecturas = _guardar
clock.today = lambda grupo=None: _dt.date(2026, 10, 27)
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ Test tower · Lift 1", "Type": "Installation"}
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [{"ID": "PRJ-9001", "Name": "ZZ Test"}]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: {}
SP.acreditar = lambda *a, **k: (ss["_cred"].append(a) or (True, "ok"))
SP.de_parte = lambda pid, lid: []
flash.mostrar()
DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _ta(at, key):
    return next((x for x in at.text_area if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


# ═════════════════════════════════════════════════════════════════
sec("1. «Tell the office» (modelo y alarma sustituidos)")
AG._llam8 = []
at = AppTest.from_string(APP, default_timeout=90).run()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_t = _todo(at)
chk("los problemas del parte, bajo su título, UNA vez cada uno",
    sum("Something the office should know" in x for x in _t) == 2   # LOG-9201 y LOG-9202
    and sum(x.startswith("“Dropsaw was broken”") for x in _t) == 1
    and sum(x.startswith("“Missing bolts and clips”") for x in _t) == 1, [x for x in _t if "Dropsaw" in x])
chk("...con su motivo", any(x == "“Dropsaw was broken” — tool broken" for x in _t))
chk("un botón «Tell the office» por problema", _bt(at, "fld_pp_LOG-9201_pb0") is not None
    and _bt(at, "fld_pp_LOG-9201_pb1") is not None)
chk("también en un parte SIN nada que confirmar (sin tarjeta)", _bt(at, "fld_pp_LOG-9202_pb0") is not None)
chk("⚠️ nada se manda sin pulsar", not at.session_state["_alertas"])
_bt(at, "fld_pp_LOG-9201_pb0").click()
at.run()
_x = _ta(at, "fld_pp_LOG-9201_pb_txt0")
chk("al pulsar: la caja con SUS palabras y de qué parte salen (nada redactado por el modelo)",
    _x is not None and _x.value == "Dropsaw was broken\n\n(From the daily log of 26/10/2026, LOG-9201.)",
    _x and _x.value)
chk("...y «Send to the office» / «Cancel»", _bt(at, "fld_pp_LOG-9201_pb_env0") is not None
    and _bt(at, "fld_pp_LOG-9201_pb_no0") is not None)
_bt(at, "fld_pp_LOG-9201_pb_no0").click()
at.run()
chk("«Cancel» cierra sin mandar", _ta(at, "fld_pp_LOG-9201_pb_txt0") is None
    and not at.session_state["_alertas"] and _bt(at, "fld_pp_LOG-9201_pb0") is not None)
_bt(at, "fld_pp_LOG-9201_pb0").click()
at.run()
_ta(at, "fld_pp_LOG-9201_pb_txt0").set_value("   ")
_bt(at, "fld_pp_LOG-9201_pb_env0").click()
at.run()
chk("una caja VACÍA no manda nada y lo dice", not at.session_state["_alertas"]
    and any("Write what the office should know first" in x for x in _todo(at)))
_bt(at, "fld_pp_LOG-9201_pb0").click()
at.run()
_ta(at, "fld_pp_LOG-9201_pb_txt0").set_value("Dropsaw broken on L1 — need a new one tomorrow")
_bt(at, "fld_pp_LOG-9201_pb_env0").click()
at.run()
_al = at.session_state["_alertas"]
chk("⚠️ se manda UNA alarma, con lo que el autor dejó en la caja, a la obra del parte",
    len(_al) == 1 and _al[0] == {"pid": "PRJ-9001", "grupo": "cliente1",
                                 "mensaje": "Dropsaw broken on L1 — need a new one tomorrow",
                                 "por": "campo000", "obra": "ZZ Test tower · Lift 1"}, _al)
chk("...y lo dice, con el número de la alarma",
    any("Sent to the office (ALR-9001)" in x for x in _todo(at)))
_g = AG.de_json(at.session_state["_guard"].get("LOG-9201", ""))
chk("⚠️ lo enviado queda en la lectura guardada", _g.get("avisos") == [
    {"texto": "Dropsaw was broken", "alerta": "ALR-9001"}], _g.get("avisos"))
chk("el problema enviado ya NO ofrece el botón; el otro sí",
    _bt(at, "fld_pp_LOG-9201_pb0") is None and _bt(at, "fld_pp_LOG-9201_pb1") is not None
    and any(":material/check: Sent to the office (ALR-9001)." == x for x in _todo(at)))
at.run()
chk("una recarga no vuelve a mandar", len(at.session_state["_alertas"]) == 1)
at.session_state["_ag_avisar"] = {"lid": "LOG-9201", "texto": "Dropsaw was broken", "mensaje": "otra vez"}
at.run()
chk("⚠️ una petición REPETIDA de lo ya enviado (doble toque) no manda otra alarma",
    len(at.session_state["_alertas"]) == 1, len(at.session_state["_alertas"]))

# ── un fallo lo dice y el botón sigue ──
at.session_state["_falla_alerta"] = True
_bt(at, "fld_pp_LOG-9201_pb1").click()
at.run()
_bt(at, "fld_pp_LOG-9201_pb_env1").click()
at.run()
chk("si la alarma falla: lo dice, no lo da por enviado y el botón sigue",
    any("Could not send it (quota)" in x for x in _todo(at))
    and _bt(at, "fld_pp_LOG-9201_pb1") is not None
    and len(AG.de_json(at.session_state["_guard"]["LOG-9201"]).get("avisos") or []) == 1)
at.session_state["_falla_alerta"] = False

# ── «Read it again» conserva lo enviado ──
_x = next((x for x in at.text_input if x.key == "fld_pp_LOG-9201_ag1_0"), None)
if _x is not None:
    _x.set_value("zz is the pit ladder")
    at.run()
    _bt(at, "fld_pp_LOG-9201_ag_releer").click()
    at.run()
_g2 = AG.de_json(at.session_state["_guard"].get("LOG-9201", ""))
chk("⚠️ tras «Read it again», lo enviado SIGUE enviado (no se ofrece otra vez)",
    _g2.get("rondas") == 2 and _g2.get("avisos") == [{"texto": "Dropsaw was broken", "alerta": "ALR-9001"}]
    and _bt(at, "fld_pp_LOG-9201_pb0") is None, (_g2.get("rondas"), _g2.get("avisos")))

# ── otra sesión: lo enviado viene de la hoja ──
AG._llam8 = []
at2 = AppTest.from_string(APP, default_timeout=90)
at2.session_state["_hoja"] = {"LOG-9201": at.session_state["_guard"]["LOG-9201"]}
at2.run()
chk("⚠️ otra sesión: lo enviado viene de la HOJA y no se ofrece (ni se vuelve a leer el parte)",
    _bt(at2, "fld_pp_LOG-9201_pb0") is None and _bt(at2, "fld_pp_LOG-9201_pb1") is not None
    and not any(x.startswith("Finished") for x in AG._llam8), AG._llam8)

# ═════════════════════════════════════════════════════════════════
sec("2. La cita repetida, una sola vez")
_t = _todo(at2)
chk("dos casillas del MISMO trozo: la cita una vez",
    sum(x == "“Finished with rails cabin and cw”" for x in [c.value for c in at2.caption]) == 1,
    [c.value for c in at2.caption if "Finished" in c.value])
chk("...y las dos casillas siguen ahí", len([c for c in at2.checkbox if c.key.startswith("fld_pp_LOG-9201_PRJ-9001_a_")]) == 2)
# Sin agente (la tarjeta del vocabulario): «Installed sills and frames» da dos de la misma línea.
AG._llam8 = []
at3 = AppTest.from_string(APP, default_timeout=90)
at3.session_state["_clave"] = ""
at3.run()
_c3 = [c.value for c in at3.caption]
_k3 = [c.key for c in at3.checkbox if c.key.startswith("fld_pp_LOG-9203_")]
chk("también en la del vocabulario: dos casillas de una línea, una cita",
    len(_k3) == 2 and sum(x == "“Installed headers and installed frames”" for x in _c3) == 1,
    (_k3, [x for x in _c3 if "sills" in x]))
chk("sin agente no hay problemas ni botón (y nada se lee)", not AG._llam8
    and _bt(at3, "fld_pp_LOG-9201_pb0") is None)

AG.clave_api, AG._llamar, alerts.report_problem = _ORIG["clave_api"], _ORIG["_llamar"], _ORIG["report_problem"]

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
