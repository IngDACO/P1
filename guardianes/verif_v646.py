# -*- coding: utf-8 -*-
"""v646 · EL AGENTE DEL PARTE CON MÁS AUTONOMÍA (03/11/2026). Decisiones del usuario:
  (a) lo que el agente leyó como HECHO, sin ningún aviso, viene MARCADO; el autor lo desmarca y nada se acredita sin
      Confirm. Las dudas y lo de la lista de palabras, sin marcar;
  (b) lo PENDIENTE del parte, «Add to To-do» con un toque;
  (c) guardado un parte desde el chat, el agente lo lee y deja una tarjeta para acreditar lo que tiene claro: solo con
      el Confirm de su autor, y lo demás del parte sigue esperándole en Daily log;
  (B) el parte que su autor no revisa en 2 días pasa a la OFICINA (lo pendiente, Home y el Management assistant), que
      lo puede confirmar en su nombre; queda apuntado quién. Nada se acredita solo.

Sin la API ni la hoja: el modelo, la hoja y lo que escribe, sustituidos y apuntados.
"""
import ast
import datetime as dt
import json
import os
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import admin_digest as AD, chat_agent as CA, chat_tools as CT, clock, daily_log as DL   # noqa: E402
from core import daily_log_ui as DLU, parte_agente as AG, parte_propuestas as PP, stages as S      # noqa: E402

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


def funcion(fuente, nombre):
    arbol = ast.parse(fuente)
    return next((ast.get_source_segment(fuente, n) for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), "")


HOY = dt.date(2026, 10, 26)

# ═════════════════════════════════════════════════════════════════
sec("1. Cuándo un parte pasa a la oficina, y quién lo puede revisar")
chk("a los 2 días (decisión del usuario)", DL.DIAS_OFICINA == 2)
_r = {"ID": "L", "Group": "cliente1", "Author": "campo000", "Text": "x", "Created": "2026-10-24 17:00:00", "Date": "2026-10-24"}
chk("2 días desde que se GUARDÓ", DL.dias_sin_revisar(_r, HOY) == 2 and DL.para_la_oficina(_r, HOY))
chk("con 1 día, todavía es solo de su autor", not DL.para_la_oficina(dict(_r, Created="2026-10-25 09:00:00"), HOY))
chk("⚠️ cuenta el día en que se guardó, no el que cuenta el parte", not DL.para_la_oficina(dict(_r, Created="2026-10-26 08:00:00", Date="2026-10-10"), HOY))
chk("revisado, nunca", not DL.para_la_oficina(dict(_r, Reviewed="2026-10-25 18:00:00"), HOY))
chk("sin texto, nunca", not DL.para_la_oficina(dict(_r, Text="  "), HOY))


class _Hoja:
    def __init__(self, filas):
        self.filas, self.escr = filas, []

    def get_all_records(self, **k):
        return [dict(f) for f in self.filas]

    def batch_update(self, u, **k):
        self.escr.append(u)


_ws0, _today0 = DL._ws, clock.today
clock.today = lambda *a: HOY
DL._invalidate = lambda: None
_filas = [dict(_r, ID="L-1"), dict(_r, ID="L-2", Created="2026-10-25 09:00:00"), dict(_r, ID="L-3", Group="otro"),
          dict(_r, ID="L-4", Reviewed="2026-10-25 18:00:00", ReviewedBy="campo000")]
_h = _Hoja(_filas)
DL._ws = lambda: _h
ok, msg = DL.marcar_revisado("L-1", "Admin2", "reg", oficina="cliente1")
chk("⚠️ la oficina de SU grupo, si ya espera a la oficina: sí, con su nombre", ok and _h.escr and _h.escr[-1][1]["values"] == [["Admin2"]], (msg, _h.escr[-1:]))
_h.escr.clear()
ok, msg = DL.marcar_revisado("L-2", "Admin2", "reg", oficina="cliente1")
chk("⚠️ con 1 día, no", not ok and _h.escr == [] and "Only the person" in msg, msg)
ok, msg = DL.marcar_revisado("L-3", "Admin2", "reg", oficina="cliente1")
chk("⚠️ de otra empresa, no", not ok and _h.escr == [], msg)
ok, msg = DL.marcar_revisado("L-1", "Admin2", "reg")
chk("⚠️ sin decir que es la oficina, como antes: solo su autor", not ok and _h.escr == [], msg)
ok, msg = DL.marcar_revisado("L-4", "campo000", "reg")
chk("⚠️ ya revisado: no se pisa quién ni lo acreditado", not ok and _h.escr == [] and "already reviewed" in msg, msg)
ok, msg = DL.marcar_revisado("L-2", "campo000", "reg")
chk("su autor, como siempre", ok and len(_h.escr) == 1)
chk("leído FRESCO: sigue sin revisar", DL.sin_revisar_aun("L-1") and not DL.sin_revisar_aun("L-4") and not DL.sin_revisar_aun("L-99"))
DL._ws = lambda: None
chk("sin poder leer, no se da por sin revisar", not DL.sin_revisar_aun("L-1"))
_rec0 = DL._records
DL._records = lambda: [dict(_r, ID="G1"), dict(_r, ID="G2", Group="otro"), dict(_r, ID="G3", Created="2026-10-20 08:00:00")]
chk("⚠️ los que esperan, solo de SU grupo, del más viejo al más nuevo", [x["ID"] for x in DL.esperan_a_la_oficina("cliente1")] == ["G3", "G1"],
    [x["ID"] for x in DL.esperan_a_la_oficina("cliente1")])
DL._records = _rec0
DL._ws, clock.today = _ws0, _today0

_s = PP.registro({"P": {"ofrecidas": [["a", 1, "X", "t"]], "marcadas": [(1, "X")], "hechas": [], "premarcadas": [(1, "X")]}},
                 en_nombre_de="campo000")
_R = json.loads(_s)
chk("el registro dice qué venía MARCADO (si no, el acierto sale inflado)", _R["destinos"]["P"]["premarcadas"] == [[1, "X"]], _R)
chk("y si lo confirmó la oficina, por quién", _R.get("en_nombre_de") == "campo000")
_R = json.loads(PP.registro({"P": {"ofrecidas": [], "marcadas": [], "hechas": []}}))
chk("sin premarcadas ni oficina, como antes", "premarcadas" not in _R["destinos"]["P"] and "en_nombre_de" not in _R, _R)

sec("2. La pantalla del parte (con clics)")
APP = r'''
import datetime as _dt
import sys
import time
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
_adm = bool(ss.get("_admin"))
st.session_state["auth"] = ({"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"} if _adm
                            else {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"})
from core import agente_memoria as MEM, auth, clock, daily_log as DL, daily_log_ui as DLU, flash, parte_agente as AG
from core import projects as P, stage_progress as SP, stages as S, tareas as TA

PLAN = S.plan_de("Installation", ())
_T, _COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in _COD.items()}
for _k, _v in (("_rev", {}), ("_reg", {}), ("_cred", []), ("_tareas", []), ("_creadas", []), ("_aprendido", []),
               ("_ya", []), ("_llam", [])):
    ss.setdefault(_k, _v)
INFO = {"seg": 0.05, "modelo": "claude-sonnet-5-5", "uso": {"in": 100, "out": 50, "cache_r": 0, "cache_w": 0}}
TA_ = "Installed sills\nIssues:\nfinished the frames\nPending: fix the door clip"
TB = "Installed headers"
TE = "Induction day"
TF = "Pending: order the rails"


def _fr(line, text, cl, names=(), q="", r=""):
    return {"line": line, "text": text, "class": cl, "codes": [C[n] for n in names], "question": q, "reason": r, "lift": ""}


# ⚠️ En el módulo, no en la sesión: desde el 2º parte se leen en hilos, y ahí no hay sesión (como verif_v607)
if not hasattr(AG, "_llam_v646"):
    AG._llam_v646 = []


def _llamar(api_key, texto, fecha, plan, mapa, previa, respuestas, idioma, memoria=""):
    AG._llam_v646.append(texto)
    if texto == TA_:
        return {"fragments": [_fr(1, "Installed sills", "done", ["Install sills"]),
                              _fr(2, "Issues:", "not_progress", r="Heading"),
                              _fr(3, "finished the frames", "done", ["Install frames"]),
                              _fr(4, "Pending: fix the door clip", "pending")]}, INFO
    if texto == TB:
        return {"fragments": [_fr(1, "Installed headers", "done", ["Install headers"])]}, INFO
    if texto == TE:
        return {"fragments": [_fr(1, "Induction day", "not_progress", r="Induction")]}, INFO
    if texto == TF:
        return {"fragments": [_fr(1, "Pending: order the rails", "pending")]}, INFO
    return {"fragments": []}, INFO


AG._llamar = _llamar
AG.clave_api = lambda: ss.get("_clave", "sk-test")
LOGS = [
    {"ID": "LOG-A", "Date": "2026-10-26", "Author": "campo000", "Created": "2026-10-26 17:00:00", "Text": TA_},
    {"ID": "LOG-B", "Date": "2026-10-23", "Author": "campo000", "Created": "2026-10-23 17:00:00", "Text": TB},
    {"ID": "LOG-C", "Date": "2026-10-25", "Author": "helper", "Created": "2026-10-25 17:00:00", "Text": TB},
    {"ID": "LOG-D", "Date": "2026-10-22", "Author": "campo000", "Created": "2026-10-22 17:00:00", "Text": TB,
     "Reviewed": "2026-10-25 09:00:00", "ReviewedBy": "Admin2"},
    {"ID": "LOG-E", "Date": "2026-10-20", "Author": "campo000", "Created": "2026-10-20 17:00:00", "Text": TE},
    {"ID": "LOG-F", "Date": "2026-10-26", "Author": "campo000", "Created": "2026-10-26 16:00:00", "Text": TF},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001", Group="cliente1")
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = "2026-10-26 18:00:00", ss["_rev"][r["ID"]][0]
        out.append(_r)
    return out


def _acreditar(pid, grupo, prj, creditos, quien="", origen=SP.MANUAL, fecha=None):
    ss["_cred"].append({"pid": pid, "quien": quien, "origen": origen, "fecha": fecha,
                        "act": sorted(c["actividad"] for c in creditos)})
    return True, "ok"


def _revisar(lid, quien, propuestas="", oficina=""):
    ss["_rev"][lid] = (quien, oficina)
    ss["_reg"][lid] = propuestas
    return True, "Reviewed."


def _crear(pid, grupo, texto, autor):
    ss["_creadas"].append((pid, grupo, texto, autor))
    ss["_tareas"].append({"ID": "TSK-77", "Text": texto})
    return True, "TSK-77"


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = _revisar
DL.guardar_lecturas = lambda d: (True, len(d))
DL.sin_revisar_aun = lambda lid: lid not in ss["_rev"] and lid not in ss["_ya"]
clock.today = lambda grupo=None: _dt.date(2026, 10, 26)
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ Test tower", "Type": "Installation"}
P.list_projects = lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False: [{"ID": "PRJ-9001", "Name": "ZZ Test"}]
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [{"ID": "PRJ-9001", "Name": "ZZ Test"}]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: {}
SP.acreditar = _acreditar
SP.de_parte = lambda pid, lid: []
TA.pendientes = lambda pid: list(ss["_tareas"])
TA.crear = _crear
MEM.aprender = lambda obs, grupo, autor, lid: (ss["_aprendido"].append((autor, lid)) or (True, 1))
MEM.para_el_agente = lambda: ""
MEM.lecciones = lambda grupo=None: []
MEM.olvidadas = lambda grupo=None: []
auth.list_users = lambda g=None: [{"User": "campo000", "Name": "Field Test"}, {"User": "Admin2", "Name": "Bobo"},
                                  {"User": "helper", "Name": "Helper One"}]
flash.mostrar()
if _adm:
    DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
else:
    DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _cb(at, pref):
    return {c.key: c for c in at.checkbox if (c.key or "").startswith(pref)}


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


at = AppTest.from_string(APP, default_timeout=90).run()
chk("la pantalla del campo se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_a = _cb(at, "fld_pp_LOG-A_PRJ-9001_a_")
_v = {k.rsplit("_", 1)[1]: c.value for k, c in _a.items()}
chk("⚠️ lo hecho sin aviso, MARCADO de antes", _v.get("Install sills") is True, _v)
chk("⚠️ lo que el parte pone bajo «Issues», SIN marcar", _v.get("Install frames") is False, _v)
chk("y se dice que viene marcado", any("The assistant ticked what it is sure of" in x for x in _todo(at)))
_b = _bt(at, "fld_pp_LOG-A_PRJ-9001_td0")
chk("lo pendiente, con «Add to To-do»", _b is not None and "Add to To-do" in _b.label, [b.key for b in at.button if "_td" in (b.key or "")])
_b.click().run()
chk("⚠️ a la lista de ESA obra, con sus palabras (sin «Pending:») y con quien lo pulsó",
    at.session_state["_creadas"] == [("PRJ-9001", "cliente1", "fix the door clip", "campo000")], at.session_state["_creadas"])
chk("y luego dice que ya está, en vez del botón", _bt(at, "fld_pp_LOG-A_PRJ-9001_td0") is None
    and any("In the job's To-do" in x for x in _todo(at)))
_bf = _bt(at, "fld_pp_LOG-F_tdn0")
chk("un parte sin nada que acreditar, solo con un pendiente: también «Add to To-do»", _bf is not None
    and any("order the rails" in x for x in _todo(at)), [b.key for b in at.button if "LOG-F" in (b.key or "")])
_bt(at, "fld_pp_LOG-A_ok").click().run()
_cr = at.session_state["_cred"]
chk("⚠️ Confirm sin tocar nada: se acredita lo marcado de antes, y nada más", _cr and _cr[-1]["act"] == ["Install sills"]
    and _cr[-1]["quien"] == "campo000", _cr)
_R = PP.leer_registro(at.session_state["_reg"].get("LOG-A", ""))
chk("el registro lo distingue: venía marcada", any([a for _o, a in d.get("premarcadas") or []] == ["Install sills"]
                                                   for d in (_R.get("destinos") or {}).values()), _R)
chk("su autor revisa, y la memoria aprende de él", at.session_state["_rev"]["LOG-A"] == ("campo000", "")
    and ("campo000", "LOG-A") in at.session_state["_aprendido"], (at.session_state["_rev"], at.session_state["_aprendido"]))
at = AppTest.from_string(APP, default_timeout=90)
at.session_state["_dl_tarea"] = {"lid": "LOG-A", "pid": "PRJ-OTRA", "texto": "x"}
at.run()
chk("⚠️ «Add to To-do» no apunta en una obra que no es de quien lo pulsa", at.session_state["_creadas"] == [], at.session_state["_creadas"])
at = AppTest.from_string(APP, default_timeout=90)
at.session_state["_clave"] = ""
at.run()
_a = _cb(at, "fld_pp_LOG-A_PRJ-9001_a_")
chk("⚠️ lo de la lista de palabras (sin el agente), SIN marcar", _a and not any(c.value for c in _a.values()), {k: c.value for k, c in _a.items()})

AG._llam_v646 = []
at = AppTest.from_string(APP, default_timeout=90)
at.session_state["_admin"] = True
at.run()
chk("la de la oficina se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ la oficina lee lo que ya le espera, y nada más", sorted(AG._llam_v646) == sorted(["Installed headers", "Induction day"]),
    AG._llam_v646)
_b2 = _cb(at, "adm_pp_LOG-B_PRJ-9001_a_")
chk("⚠️ el de hace 3 días: su tarjeta, para confirmarlo por su autor, con lo claro marcado",
    [c.value for c in _b2.values()] == [True], {k: c.value for k, c in _b2.items()})
chk("dice de quién es y cuánto lleva", any("Field Test's log, 3 days without review" in x for x in _todo(at))
    and any("on their behalf" in x for x in _todo(at)), [x for x in _todo(at) if "log" in x][:4])
chk("⚠️ el de ayer, el de hoy y el de otro, sin tarjeta", not _cb(at, "adm_pp_LOG-C") and not _cb(at, "adm_pp_LOG-A")
    and _bt(at, "adm_pp_LOG-C_ok") is None and _bt(at, "adm_pp_LOG-A_ok") is None)
chk("⚠️ sin «Tell the office» ni «Read it again»: son del autor", _bt(at, "adm_pp_LOG-B_ag_releer") is None
    and not [b for b in at.button if (b.key or "").startswith("adm_pp_LOG-B_pb")])
chk("⚠️ el revisado por la oficina dice que fue por su autor", any("reviewed by Bobo (on behalf of Field Test)" in x for x in _todo(at)),
    [x for x in _todo(at) if "reviewed by" in x])
_bt(at, "adm_pp_LOG-B_ok").click().run()
_cr = at.session_state["_cred"]
chk("⚠️ Confirm de la oficina: acredita lo marcado, con SU nombre", _cr and _cr[-1]["act"] == ["Install headers"] and _cr[-1]["quien"] == "Admin2"
    and _cr[-1]["fecha"] == "2026-10-23", _cr)
chk("⚠️ se revisa como oficina de su grupo, y el registro dice por quién", at.session_state["_rev"]["LOG-B"] == ("Admin2", "cliente1")
    and PP.leer_registro(at.session_state["_reg"]["LOG-B"]).get("en_nombre_de") == "campo000", at.session_state["_rev"])
chk("⚠️ y la memoria NO aprende de la oficina", not at.session_state["_aprendido"], at.session_state["_aprendido"])
_e = _bt(at, "adm_pp_LOG-E_no")
chk("uno sin nada que acreditar: la oficina lo cierra con «Nothing to credit»", _e is not None)
_e.click().run()
chk("...como oficina, y por su autor", at.session_state["_rev"].get("LOG-E") == ("Admin2", "cliente1")
    and PP.leer_registro(at.session_state["_reg"]["LOG-E"]).get("nada") is True
    and PP.leer_registro(at.session_state["_reg"]["LOG-E"]).get("en_nombre_de") == "campo000", at.session_state["_rev"])
at = AppTest.from_string(APP, default_timeout=90)
at.session_state["_admin"] = True
at.session_state["_ya"] = ["LOG-B"]          # su autor lo revisó hace un momento, y la página aún no lo sabe
at.run()
_bt(at, "adm_pp_LOG-B_ok").click().run()
chk("⚠️ si su autor lo revisó hace un momento, la oficina no acredita nada, y lo dice", not at.session_state["_cred"]
    and any("already reviewed" in x for x in _todo(at)), (at.session_state["_cred"], [x for x in _todo(at) if "review" in x]))

sec("3. La oficina lo ve: lo pendiente, Home y el Management assistant")
_p0, _e0 = DLU._plan_de, DL.esperan_a_la_oficina
DL.esperan_a_la_oficina = lambda g: [{"ID": "L1", "ProjectID": "PRJ-1"}, {"ID": "L2", "ProjectID": "PRJ-SIN"}, {"ID": "L3", "ProjectID": "PRJ-1"}]
DLU._plan_de = lambda pid: ["plan"] if pid == "PRJ-1" else []
chk("⚠️ solo los de obras con plan: en las demás no hay nada que acreditar", [r["ID"] for r in DLU.partes_para_la_oficina("g")] == ["L1", "L3"])
DLU._plan_de, DL.esperan_a_la_oficina = _p0, _e0
chk("en lo pendiente de la oficina", "partes_por_revisar" in AD._PENDING_KEYS and "partes_para_la_oficina" in funcion(leer("core/admin_digest.py"), "group_digest"))
_d = {k: [] for k in AD._PENDING_KEYS}
_d.update({"grupo": "g", "n_activos": 1, "n_total": 1, "avance_prom": 0, "horas": 0,
           "partes_por_revisar": [{"id": "PRJ-1", "nombre": "Bondi", "log": "L1", "autor": "Field Test", "desde": "2026-10-23", "dias": 3}]})
AD.nombres_usuarios = lambda: {}
chk("y en el resumen que lee la IA", "Bondi · Field Test (3 d)" in AD.digest_text(_d), AD.digest_text(_d))
_ri = funcion(leer("core/projects_ui.py"), "_resumen_del_dia")
chk("⚠️ Home: el décimo indicador, que lleva a esas obras", '("partes", ":material/rate_review:", "Logs to review"' in _ri
    and '"partes": d.get("partes_por_revisar", [])' in _ri)
from core import admin_digest as _AD2, alerts as _AL, ausencias as _AU, correcciones as _CO, falsecar as _FC, projects as _P   # noqa: E402
_AU.pendientes = lambda g: []
_AU.excesos_por_decidir = lambda g: []
_CO.pendientes = lambda g: []
_CO.list_group = lambda g, estado=None, usuario=None: []
_FC.dias_sin_registro = lambda g, **k: []
_AL._alarmas_visibles = lambda: []
_AD2.nombres_usuarios = lambda: {"campo000": "Field Test"}
_P.list_projects = lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False: [{"ID": "PRJ-1", "Name": "Bondi"}]
DLU.partes_para_la_oficina = lambda g: [{"ID": "LOG-7", "ProjectID": "PRJ-1", "Author": "campo000", "Date": "2026-10-23", "Created": "2026-10-23 17:00:00"}]
clock.today = lambda *a: HOY
x = CT._bandejas({}, {"usuario": "Admin2", "grupo": "cliente1", "rol": "administrator"})["daily_logs_waiting_review"]
chk("⚠️ el Management assistant los ve, con el autor por su nombre y cuánto esperan", x["count"] == 1 and x["after_days"] == 2
    and x["latest"][0] == {"log_id": "LOG-7", "job": "Bondi", "project_id": "PRJ-1", "author": "Field Test", "date": "23/10/2026", "days_waiting": 3}, x)
_ot = CA._PERSONA["office_tools"].replace('"\n        "', "")
chk("y sabe dónde se confirman, y que él no", "pasa a la oficina" in _ot and "**Status**, abajo del todo" in _ot and "Tú no lo confirmas" in _ot)

sec("4. Desde el chat: guardar el parte y acreditar lo que tiene claro (con Confirm)")
PLAN = S.plan_de("Installation", ())
_T, _COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in _COD.items()}
ESC = []


def _reg(texto, frs):
    frag, _i, _a = AG.validar({"fragments": frs}, PLAN, texto)
    return {"v": AG.LECTURA_V, "clave": AG.clave(texto, PLAN), "modelo": "claude-sonnet-5-5", "prompt": AG.PROMPT_V,
            "fragmentos": frag, "respuestas": [], "rondas": 1}


def _f(line, text, cl, names=()):
    return {"line": line, "text": text, "class": cl, "codes": [C[n] for n in names], "question": "", "reason": "", "lift": ""}


T_OK = "Installed sills"
T_MAS = "Installed sills\nPending: fix the door clip"
T_AV = "Installed sills\nIssues:\nfinished the frames"
LECT = {T_OK: _reg(T_OK, [_f(1, "Installed sills", "done", ["Install sills"])]),
        T_MAS: _reg(T_MAS, [_f(1, "Installed sills", "done", ["Install sills"]), _f(2, "Pending: fix the door clip", "pending")]),
        T_AV: _reg(T_AV, [_f(1, "Installed sills", "done", ["Install sills"]), _f(2, "Issues:", "not_progress"),
                         _f(3, "finished the frames", "done", ["Install frames"])])}
_leidas = []
OBRA = {"ID": "PRJ-1", "Name": "Bondi", "Group": "cliente1"}
_logs = {}
DL.crear = lambda pid, g, txt, u, dia=None: (ESC.append(("DL.crear", txt)) or _logs.__setitem__("LOG-N", {"ID": "LOG-N", "Author": u, "Text": txt, "Date": "2026-10-26"}) or (True, "LOG-N"))
DL.partes = lambda pid, autor=None, dia=None: list(_logs.values())
_rev = []
DL.sin_revisar_aun = lambda lid: lid not in _rev
DL.marcar_revisado = lambda lid, quien, propuestas="", oficina="": (ESC.append(("revisado", lid, quien)) or _rev.append(lid) or (True, "ok"))
DLU._plan_de = lambda pid: PLAN
DLU._apuntar = lambda lecturas, fallos: _leidas.append(dict(lecturas))
DLU._lectura = lambda r, plan: LECT.get(str(r.get("Text")), {})
DLU._memoria = lambda: ""
DLU._aprender = lambda reg, por, g, u, lid: ESC.append(("aprende", lid, u))
DLU._version_app = lambda: "v646"
AG.clave_api = lambda: "sk-test"
AG.disponible = lambda k=None: True
AG.leer = lambda texto, plan, fecha="", mapa=None, previa=None, respuestas=None, idioma="en", api_key=None, memoria="": (
    ESC.append(("AG.leer", texto)) or (LECT.get(texto), "" if texto in LECT else "error"))
from core import stage_progress as _SP                                # noqa: E402
_SP.acreditado = lambda pid: {}
_SP.acreditar = lambda pid, g, prj, creditos, quien="", origen="", fecha=None: (
    ESC.append(("acreditar", pid, sorted(c["actividad"] for c in creditos), quien, origen, fecha)) or (True, "ok"))
_P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [OBRA]


def cctx(**k):
    return {"usuario": "campo000", "nombre": "Field Test", "grupo": "cliente1", "rol": "field", "acciones": [], **k}


def _carta_parte(txt):
    return {"tipo": "parte", "datos": {"project_id": "PRJ-1", "text": txt, "date": "2026-10-26"}}


ESC.clear()
_c = cctx()
ok, msg = CT.confirmar(_carta_parte(T_OK), _c)
chk("guarda el parte, y el agente lo lee una vez (y la lectura queda guardada)", ok and [e[0] for e in ESC] == ["DL.crear", "AG.leer"]
    and _leidas and "LOG-N" in _leidas[-1], (ESC, _leidas))
chk("⚠️ deja la tarjeta para acreditar lo que tiene claro, sin acreditar nada todavía", len(_c["acciones"]) == 1
    and _c["acciones"][0]["tipo"] == "credito" and _c["acciones"][0]["datos"]["creditos"] == [[_COD[C["Install sills"]][0], "Install sills"]]
    and not [e for e in ESC if e[0] == "acreditar"], _c["acciones"])
chk("y se lo dice", "confirm the card below to credit 1 activities" in msg, msg)
_carta = _c["acciones"][0]
ESC.clear()
ok, msg = CT.confirmar(_carta, cctx())
chk("⚠️ Confirm: acredita con la fecha del parte, como autor y desde el parte", ok and ESC[0] == ("acreditar", "PRJ-1", ["Install sills"], "campo000", "log", "2026-10-26"), ESC)
chk("⚠️ sin nada más que mirar: el parte queda revisado y la memoria aprende", ("revisado", "LOG-N", "campo000") in ESC and ("aprende", "LOG-N", "campo000") in ESC, ESC)
ESC.clear()
ok, msg = CT.confirmar(_carta, cctx())
chk("⚠️ dos veces no: ya está revisado", not ok and not [e for e in ESC if e[0] == "acreditar"] and "already reviewed" in msg, msg)
_logs.clear()
_rev.clear()
ESC.clear()
_c = cctx()
ok, msg = CT.confirmar(_carta_parte(T_MAS), _c)
_carta = _c["acciones"][0]
chk("con algo pendiente, la tarjeta lo avisa", "The rest of the log waits for you in **Daily log**." in _carta["detalle"], _carta["detalle"])
ESC.clear()
ok, msg = CT.confirmar(_carta, cctx())
chk("⚠️ acredita lo claro, y el parte SIGUE sin revisar: lo demás lo mira su autor", ok and [e[0] for e in ESC] == ["acreditar"]
    and "waits for you in **Daily log**" in msg, (ESC, msg))
_t = dict(_carta, datos=dict(_carta["datos"], creditos=[[1, "Install headers"]]))
ESC.clear()
ok, msg = CT.confirmar(_t, cctx())
chk("⚠️ una tarjeta tocada no acredita lo que el parte no dice con seguridad", not ok and not ESC, (msg, ESC))
ok, msg = CT.confirmar(_carta, cctx(usuario="otro"))
chk("⚠️ el parte de otro, no", not ok and not ESC, msg)
ok, msg = CT.confirmar(_carta, {"usuario": "Admin2", "grupo": "cliente1", "rol": "administrator"})
chk("⚠️ ni la oficina por esta tarjeta", not ok and not ESC and "not recognised" in msg, msg)
_logs.clear()
ESC.clear()
_c = cctx()
ok, msg = CT.confirmar(_carta_parte(T_AV), _c)
chk("⚠️ lo que el parte pone bajo «Issues» no entra en la tarjeta (en Daily log va sin marcar)",
    [a for _o, a in _c["acciones"][0]["datos"]["creditos"]] == ["Install sills"] and "waits for you" in _c["acciones"][0]["detalle"],
    _c["acciones"])
_logs.clear()
ESC.clear()
_c = cctx()
ok, msg = CT.confirmar(_carta_parte("Lift 1 installed sills\nLift 2 installed headers"), _c)
chk("⚠️ con dos ascensores no se ofrece: a qué obra va cada trozo lo elige su autor", ok and not _c["acciones"]
    and not [e for e in ESC if e[0] == "AG.leer"] and "more than one lift" in msg, (msg, ESC))
_logs.clear()
ESC.clear()
_c = cctx()
ok, msg = CT.confirmar(_carta_parte("ilegible para el agente"), _c)
chk("si el agente no puede, el parte queda guardado como antes", ok and not _c["acciones"]
    and msg == "Daily log saved. Open it in **Daily log** to confirm what it proposes.", msg)
_s = leer("core/chat_ui.py")
chk("⚠️ la tarjeta nueva entra en la MISMA lista (la de la sesión)", 'CT.confirmar(a, {**_contexto(), "acciones": lista})' in funcion(_s, "atender"))
_fp = CA._PERSONA["field_tools"].replace('"\n        "', "")
chk("el Field assistant sabe que esa tarjeta la pone la app, y que solo acredita con Confirm", "esa tarjeta la pone la APP, no tú" in _fp
    and "solo acredita si la persona pulsa **Confirm**" in _fp and "NO puedes fichar" in _fp)
_hd = next(h for h in CT.definiciones("field", "x") if h["name"] == "prepare_daily_log")["description"]
chk("y la herramienta del parte lo dice", "may offer a second card to credit" in _hd)

sec("5. ⚠️ Nada se acredita solo")
_src = leer("core/chat_tools.py")
_quien = {f.name for f in ast.walk(ast.parse(_src)) if isinstance(f, ast.FunctionDef)
          and any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "acreditar" for n in ast.walk(f))}
chk("en el chat, solo la tarjeta que confirma su autor", _quien == {"_confirmar_credito"}, _quien)
_dl = leer("core/daily_log_ui.py")
_qd = {f.name for f in ast.walk(ast.parse(_dl)) if isinstance(f, ast.FunctionDef)
       and any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "acreditar" for n in ast.walk(f))}
chk("en la pantalla, solo el Confirm de la tarjeta (autor u oficina)", _qd == {"_propuestas"}, _qd)
chk("y ninguna lectura acredita: el agente solo propone", ".acreditar(" not in leer("core/parte_agente.py"))

print("\n=== verif_v646: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
