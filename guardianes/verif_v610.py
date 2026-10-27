# -*- coding: utf-8 -*-
"""v610 · LA MEMORIA DEL AGENTE DEL PARTE (`core/agente_memoria.py`) — decisión del usuario
(27/10/2026): «El agente de logs debe tener la capacidad de aprender, debe tener una memoria»;
GLOBAL y AUTOMÁTICA. Y el cero de la auditoría (visto en la migración de v609).

Lo que protege, SIN red, sin la API y sin la hoja real (todo sustituido):
  (a) qué se aprende: marcado = confirmado; propuesta suelta sin marcar = rechazada; opción de
      pregunta sin marcar = rechazada SOLO si se marcó otra de la misma; lo demás, nada;
  (b) qué recibe el agente: reglas primero, «es» y «no es» con umbral, en orden FIJO (caché), y
      el bloque DELANTE del plan con su marca; `PROMPT_V` subido;
  (c) ⚠️ la memoria es GLOBAL (libro maestro) y bajo AppTest no toca la hoja REAL;
  (d) al confirmar un parte que leyó el agente, se aprende; del vocabulario o con «Nothing to
      credit», no; si la memoria falla, el parte queda confirmado igual;
  (e) el panel: el admin ve lo de su grupo y las reglas del propietario, solo quita lo de su
      grupo; el propietario lo ve y quita todo; enseñar una regla;
  (f) ⚠️ `auditoria.diff` no anota «0.0 → 0» como un cambio.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field",
                            "grupo": "cliente1"}

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

from core import agente_memoria as MEM                            # noqa: E402
from core import auditoria                                        # noqa: E402
from core import parte_agente as AG                               # noqa: E402
from core import stages as S                                      # noqa: E402
from core import timeclock                                        # noqa: E402

PLAN = S.plan_de("Installation", ())

# ═════════════════════════════════════════════════════════════════
sec("1. Qué se aprende de una revisión")
chk("la frase se guarda normalizada", MEM.normaliza("  Isntalled   the MOTOR. ") == "isntalled the motor")
chk("...y recortada (frases cortas: nada de texto largo de un cliente)",
    len(MEM.normaliza("x" * 500)) == MEM.MAX_FRASE)
_dest = {"PRJ-1": {
    "ofrecidas": [["a", 13, "Wire all boxes", "finished headroom wiring"],
                  ["a", 13, "Install electrical boxes", "finished headroom wiring"],
                  ["q", 10, "Install car rails to top", "Installed rails"],
                  ["q", 9, "Install first 2 CW rails", "Installed rails"],
                  ["q", 10, "Install motor bedplate", "installed bedplate"],
                  ["q", 10, "Install single bedplate", "installed bedplate"],
                  ["e", 7, "Install frames", "doors"],
                  ["a", 9, "Install CW tank", ""]],
    "marcadas": [[13, "Wire all boxes"], [10, "Install car rails to top"], [7, "Install frames"]]},
    "PRJ-2": {"ofrecidas": [["a", 13, "Wire all boxes", "Finished headroom wiring."]],
              "marcadas": [[13, "Wire all boxes"]]}}
_o = {(f, a): (c, r) for f, a, c, r in MEM.observaciones(_dest)}
chk("propuesta suelta MARCADA → confirmada (y se suma entre destinos)",
    _o.get(("finished headroom wiring", "Wire all boxes")) == (2, 0), _o)
chk("propuesta suelta SIN marcar → rechazada", _o.get(("finished headroom wiring", "Install electrical boxes")) == (0, 1))
chk("opción de pregunta marcada → confirmada; la otra de la MISMA pregunta → rechazada",
    _o.get(("installed rails", "Install car rails to top")) == (1, 0)
    and _o.get(("installed rails", "Install first 2 CW rails")) == (0, 1))
chk("⚠️ una pregunta sin NINGUNA marcada no enseña nada (no dijo nada de ellas)",
    not any(k[0] == "installed bedplate" for k in _o))
chk("las listas de etapa («e») y lo que no trae frase, nada",
    not any(a in ("Install frames", "Install CW tank") for _f, a in _o))
chk("sin destinos, nada", MEM.observaciones({}) == [] and MEM.observaciones(None) == [])

# ═════════════════════════════════════════════════════════════════
sec("2. Qué recibe el agente")
_lec = [{"Phrase": "zz b", "Activity": "Install sills", "Kind": "learned", "Confirmed": 3, "Rejected": 1},
        {"Phrase": "zz a", "Activity": "Install frames", "Kind": "learned", "Confirmed": 1, "Rejected": 1},
        {"Phrase": "installed motor", "Activity": "Install motor (machine)", "Kind": "rule", "Confirmed": 0, "Rejected": 0},
        {"Phrase": "zz c", "Activity": "Spin motor", "Kind": "learned", "Confirmed": 0, "Rejected": 2},
        {"Phrase": "zz d", "Activity": "Install keepers", "Kind": "learned", "Confirmed": 0, "Rejected": 1}]
_f = MEM.firmes(_lec)
chk("las reglas de la oficina, PRIMERO", _f[0] == ("rule", "installed motor", "Install motor (machine)", 0), _f)
chk("«es»: confirmada más veces que rechazada", ("means", "zz b", "Install sills", 3) in _f)
chk("...un empate NO es una lección", not any(x[1] == "zz a" for x in _f))
chk("«no es»: dos rechazos y ninguna confirmación; uno solo, no",
    ("not", "zz c", "Spin motor", 2) in _f and not any(x[1] == "zz d" for x in _f))
_big = [{"Phrase": "p%03d" % i, "Activity": "Install sills", "Kind": "learned", "Confirmed": 1, "Rejected": 0}
        for i in range(400)]
chk("con tope (lo que cabe en el prompt)", len(MEM.firmes(_big)) == MEM.MAX_LECCIONES)
_orig_lec = MEM.lecciones
MEM.lecciones = lambda grupo=None: list(_lec)
_txt = MEM.para_el_agente()
MEM.lecciones = lambda grupo=None: list(reversed(_lec))
_txt2 = MEM.para_el_agente()
MEM.lecciones = lambda grupo=None: []
_vacio = MEM.para_el_agente()
MEM.lecciones = _orig_lec
chk("el bloque CREW MEMORY con sus tres formas",
    _txt.startswith("CREW MEMORY") and "- «installed motor» → Install motor (machine) (rule set by the office)" in _txt
    and "- «zz b» → Install sills (confirmed 3×)" in _txt and "- «zz c» is NOT Spin motor (rejected 2×)" in _txt, _txt)
chk("⚠️ el MISMO texto venga en el orden que venga (va en la caché del prompt)", _txt == _txt2)
chk("sin lecciones, nada", _vacio == "")
_m = AG._mensaje("a", "", PLAN, {}, None, None, "en", memoria=_txt)[0]["content"]
chk("⚠️ la memoria va PRIMERO en el mensaje y con su marca; el plan después, con la suya",
    _m[0]["text"] == _txt and _m[0].get("cache_control") == {"type": "ephemeral"}
    and _m[1]["text"].startswith("JOB PLAN") and _m[1].get("cache_control"))
_marcas = 1 + sum(1 for b in _m if b.get("cache_control"))
chk("...y caben las marcas de caché (≤ 4 con la del sistema)", _marcas <= 4, _marcas)
chk("sin memoria, el plan sigue siendo lo primero", AG._mensaje("a", "", PLAN, {}, None, None, "en")[0]["content"][0]
    ["text"].startswith("JOB PLAN"))
chk("las instrucciones hablan de la memoria y `PROMPT_V` subió (se releen los partes sin revisar)",
    "CREW MEMORY" in AG._INSTRUCCIONES and AG.PROMPT_V >= 2)
_cap = {}
_orig_llamar = AG._llamar


def _fake(api_key, texto, fecha, plan, mapa, previa, respuestas, idioma, memoria=""):
    _cap["memoria"] = memoria
    return {"fragments": []}, {"seg": 0.1, "modelo": "claude-sonnet-5-5",
                               "uso": {"in": 1, "out": 1, "cache_r": 0, "cache_w": 0}}


AG._llamar = _fake
_r, _mot = AG.leer("a", PLAN, api_key="sk-x", memoria=_txt)
AG._llamar = _orig_llamar
chk("`leer` le pasa la memoria a la llamada y apunta cuántas lecciones llevaba",
    _cap.get("memoria") == _txt and _r and _r.get("memoria") == 3, (_r or {}).get("memoria"))

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ Global, y la hoja real fuera de los guardianes")
chk("`AgentMemory` es una hoja GLOBAL (libro maestro)", "agentmemory" in timeclock.SHEETS_GLOBALES)
# ⚠️ Esta faltaba en la 1ª versión de v610 y la cazó romper_v430 (verif_v430, rojo de base): el
# lector va SIN cabeceras, así que fuera del lote `registros` da None y la memoria se escribiría
# sin volver a leerse nunca. La sonda de la pantalla sustituye `_records_cached` y no lo veía.
from core import hojas as _HJ  # noqa: E402
chk("⚠️ `AgentMemory` está en el LOTE (si no, se lee vacía PARA SIEMPRE: regla v461/v507/v514)",
    MEM.SHEET in _HJ.HOJAS_LECTURA, MEM.SHEET)
_at0 = AppTest.from_string(r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import agente_memoria as MEM
st.write("WS:%s" % (MEM._ws() is None))
# ⚠️ La lectura real devolvería [] igual mientras la hoja no exista: la sonda le da algo
# CONOCIDO y comprueba que no lo usa (trampa 12: una sonda negativa, validada).
MEM._records_cached = lambda: [{"Phrase": "real", "Activity": "Install sills"}]
st.write("REC:%s" % (MEM._records() == []))
''', default_timeout=60).run()
_v = [x.value for x in _at0.markdown]
chk("⚠️ bajo AppTest: ni escribe ni lee la hoja real", "WS:True" in _v and "REC:True" in _v, _v)


# ═════════════════════════════════════════════════════════════════
sec("4. Escribir la memoria (hoja sustituida)")


class _WS:
    def __init__(self, filas):
        self.filas = [dict(f) for f in filas]
        self.lotes, self.nuevas = [], []

    def get_all_records(self, **k):
        return [dict({h: "" for h in MEM.HEADERS}, **f) for f in self.filas]

    def batch_update(self, lote, value_input_option=None):
        assert value_input_option == "RAW"
        self.lotes.append(lote)

    def append_rows(self, filas, value_input_option=None):
        self.nuevas += filas

    def append_row(self, fila, value_input_option=None):
        self.nuevas.append(fila)


_ws = _WS([{"ID": "MEM-0007", "Phrase": "finished headroom wiring", "Activity": "Wire all boxes",
            "Kind": "learned", "Confirmed": "2", "Rejected": "0", "Group": "cliente1"},
           {"ID": "MEM-0008", "Phrase": "zz otra", "Activity": "Install sills", "Kind": "learned",
            "Confirmed": "1", "Rejected": "0", "Group": "otro"}])
_orig = {"_ws": MEM._ws, "_invalidate": MEM._invalidate}
MEM._ws = lambda: _ws
MEM._invalidate = lambda: None
try:
    okA, nA = MEM.aprender([("finished headroom wiring", "Wire all boxes", 1, 0),
                            ("installed rails", "Install car rails to top", 1, 0)], "cliente1", "campo000", "LOG-1")
    _rng = {d["range"]: d["values"][0][0] for l in _ws.lotes for d in l}
    from core.num import col_letter as _cl
    chk("una lección que ya existe: se SUMA (2 → 3), no se repite",
        okA and _rng.get("%s2" % _cl(MEM.HEADERS.index("Confirmed") + 1)) == "3", _rng)
    chk("una nueva: fila ENTERA, con el siguiente ID, el grupo, quién y de qué parte",
        len(_ws.nuevas) == 1 and len(_ws.nuevas[0]) == len(MEM.HEADERS) and _ws.nuevas[0][0] == "MEM-0009"
        and _ws.nuevas[0][1:7] == ["installed rails", "Install car rails to top", "learned", "1", "0", "cliente1"]
        and _ws.nuevas[0][7:9] == ["campo000", "LOG-1"], _ws.nuevas)
    _ws.nuevas = []
    okR, mR = MEM.poner_regla("  Installed MOTOR ", "Install motor (machine)", "", "owner")
    chk("una regla de la oficina: normalizada y como regla", okR and _ws.nuevas
        and _ws.nuevas[0][1:4] == ["installed motor", "Install motor (machine)", "rule"], (mR, _ws.nuevas))
    chk("sin frase o sin actividad, no", not MEM.poner_regla("", "Install sills", "", "x")[0]
        and not MEM.poner_regla("algo", "", "", "x")[0])
    _ws.lotes = []
    okO, nO = MEM.olvidar(["MEM-0007", "MEM-0008"], "cliente1", False)
    chk("⚠️ un admin solo olvida lo de SU grupo", okO and nO == 1, (okO, nO))
    _ws.lotes = []
    okP, nP = MEM.olvidar(["MEM-0007", "MEM-0008"], "cliente1", True)
    chk("...el propietario, todo (y olvidar es `Active=NO`: queda rastro)",
        okP and nP == 2 and all(d["values"] == [["NO"]] for d in _ws.lotes[0]), _ws.lotes)
finally:
    MEM._ws, MEM._invalidate = _orig["_ws"], _orig["_invalidate"]
MEM._ws = lambda: None
chk("sin hoja, aprender dice que no (y no revienta)", MEM.aprender([("a", "b", 1, 0)], "g", "u", "L")[0] is False)
MEM._ws = _orig["_ws"]
_rec = [{"ID": "1", "Phrase": "a", "Activity": "X", "Group": "cliente1"},
        {"ID": "2", "Phrase": "b", "Activity": "Y", "Group": "otro"},
        {"ID": "3", "Phrase": "c", "Activity": "Z", "Group": "", "Kind": "rule"},
        {"ID": "4", "Phrase": "d", "Activity": "W", "Group": "cliente1", "Active": "NO"}]
_or = MEM._records
MEM._records = lambda: _rec
chk("lo que ve un admin: su grupo y las reglas del propietario (sin lo olvidado)",
    [r["ID"] for r in MEM.lecciones("cliente1")] == ["1", "3"])
chk("...y el agente y el propietario, todo lo activo", [r["ID"] for r in MEM.lecciones(None)] == ["1", "2", "3"])
MEM._records = _or

# ═════════════════════════════════════════════════════════════════
sec("5. ⚠️ El cero de la auditoría")
chk("«0.0 → 0» NO es un cambio", auditoria.diff({"Progress": "0.0"}, {"Progress": 0.0}) == {})
chk("...«5.0 → 0» SÍ", auditoria.diff({"Progress": "5.0"}, {"Progress": 0.0}) == {"Progress": ["5.0", 0.0]})
chk("...y un `None` sigue siendo vacío", auditoria.diff({"Progress": None}, {"Progress": ""}) == {})

# ═════════════════════════════════════════════════════════════════
sec("6. La tarjeta y el panel (AppTest)")
APP = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": ss.get("_u", "campo000"), "nombre": "X",
                                     "rol": ss.get("_rol", "field"), "grupo": "cliente1"})
from core import agente_memoria as MEM, clock, daily_log as DL, daily_log_ui as DLU, flash
from core import parte_agente as AG, projects as P, stage_progress as SP, stages as S
PLAN = S.plan_de("Installation", ())
_T, _COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in _COD.items()}
for _k, _v in (("_rev", {}), ("_aprendido", []), ("_mem_llamadas", []), ("_olv", []), ("_reglas", [])):
    ss.setdefault(_k, _v)
INFO = {"seg": 0.01, "modelo": "claude-sonnet-5-5", "uso": {"in": 1, "out": 1, "cache_r": 0, "cache_w": 0}}
T1 = "Installed headers and installed frames"


def _llamar(api_key, texto, fecha, plan, mapa, previa, respuestas, idioma, memoria=""):
    ss["_mem_llamadas"].append(memoria)
    return {"fragments": [{"line": 1, "text": "Installed headers", "class": "done", "codes": [C["Install headers"]],
                           "question": "", "reason": "", "lift": ""},
                          {"line": 1, "text": "installed frames", "class": "done", "codes": [C["Install frames"]],
                           "question": "", "reason": "", "lift": ""}]}, INFO


AG._llamar = _llamar
AG.clave_api = lambda: ss.get("_clave", "sk-test")
MEM.para_el_agente = lambda: "CREW MEMORY — test\n- «zz» → Install sills (confirmed 2×)"
MEM.aprender = lambda obs, g, u, l: (ss["_aprendido"].append((obs, g, u, l)) or (not ss.get("_mem_falla"), len(obs)))
MEM.lecciones = lambda grupo=None: [r for r in [
    {"ID": "MEM-1", "Phrase": "propia", "Activity": "Install sills", "Kind": "learned", "Confirmed": 2, "Rejected": 0, "Group": "cliente1", "Updated": "2026-10-27 10:00"},
    {"ID": "MEM-2", "Phrase": "ajena", "Activity": "Install frames", "Kind": "learned", "Confirmed": 1, "Rejected": 0, "Group": "otro", "Updated": ""},
    {"ID": "MEM-3", "Phrase": "installed motor", "Activity": "Install motor (machine)", "Kind": "rule", "Confirmed": 0, "Rejected": 0, "Group": "", "Updated": ""}]
    if grupo is None or r["Group"] in (grupo, "")]
MEM.olvidar = lambda ids, g, dueno: (ss["_olv"].append((list(ids), g, dueno)) or (True, len(ids)))
MEM.poner_regla = lambda f, a, g, u: (ss["_reglas"].append((f, a, g, u)) or (True, "Rule saved."))
LOGS = [{"ID": "LOG-9301", "Date": "2026-10-27", "Author": "campo000", "Created": "2026-10-27 17:00:00", "Text": T1}]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001")
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = "2026-10-27 18:00:00", ss["_rev"][r["ID"]]
        out.append(_r)
    return out


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = lambda lid, quien, propuestas="": (ss["_rev"].update({lid: quien}) or (True, "ok"))
DL.guardar_lecturas = lambda d: (True, len(d))
clock.today = lambda grupo=None: _dt.date(2026, 10, 27)
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ", "Type": "Installation"}
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [{"ID": "PRJ-9001", "Name": "ZZ"}]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: {}
SP.acreditar = lambda *a, **k: (False, "falla") if ss.get("_acr_falla") else (True, "ok")
SP.de_parte = lambda pid, lid: []
flash.mostrar()
if ss.get("_admin"):
    DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
else:
    DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


at = AppTest.from_string(APP, default_timeout=90).run()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("la lectura recibe la memoria", at.session_state["_mem_llamadas"][:1] == [
    "CREW MEMORY — test\n- «zz» → Install sills (confirmed 2×)"], at.session_state["_mem_llamadas"])
_c = [c for c in at.checkbox if c.key.startswith("fld_pp_LOG-9301_PRJ-9001_a_")]
for c in _c:
    if c.key.endswith("Install headers"):
        c.check()
at.run()
_bt(at, "fld_pp_LOG-9301_ok").click()
at.run()
_ap = at.session_state["_aprendido"]
chk("⚠️ al confirmar, aprende: lo MARCADO confirmado y lo que quedó sin marcar, rechazado",
    len(_ap) == 1 and sorted(_ap[0][0]) == sorted([("installed headers", "Install headers", 1, 0),
                                                   ("installed frames", "Install frames", 0, 1)])
    and _ap[0][1:] == ("cliente1", "campo000", "LOG-9301"), _ap)
# «Nothing to credit» y el vocabulario no enseñan.
at2 = AppTest.from_string(APP, default_timeout=90).run()
_bt(at2, "fld_pp_LOG-9301_no").click()
at2.run()
chk("«Nothing to credit» no enseña nada", not at2.session_state["_aprendido"] and "LOG-9301" in at2.session_state["_rev"])
at3 = AppTest.from_string(APP, default_timeout=90)
at3.session_state["_clave"] = ""
at3.run()
_c3 = [c for c in at3.checkbox if c.key.startswith("fld_pp_LOG-9301_")]
if _c3:
    _c3[0].check()
    at3.run()
_b3 = _bt(at3, "fld_pp_LOG-9301_ok")
if _b3 is not None:
    _b3.click()
    at3.run()
chk("lo leído por el VOCABULARIO no enseña (sus términos no son frases)",
    _b3 is not None and "LOG-9301" in at3.session_state["_rev"] and not at3.session_state["_aprendido"])
at4 = AppTest.from_string(APP, default_timeout=90)
at4.session_state["_mem_falla"] = True
at4.run()
[c for c in at4.checkbox if c.key.endswith("Install headers")][0].check()
at4.run()
_bt(at4, "fld_pp_LOG-9301_ok").click()
at4.run()
chk("⚠️ si la memoria falla, el parte queda confirmado igual",
    "LOG-9301" in at4.session_state["_rev"] and not at4.exception
    and any("Credited 1 activities" in x for x in _todo(at4)), _todo(at4)[-3:])

# ── el panel ──
at5 = AppTest.from_string(APP, default_timeout=90)
at5.session_state["_admin"] = True
at5.session_state["_rol"] = "administrator"
at5.session_state["_u"] = "admin1"
at5.run()
_t5 = _todo(at5)
_exp = [e for e in list(at5.expander) + list(at5.status) if "What the assistant has learned" in str(e.label)]
chk("el admin ve el panel «What the assistant has learned»", bool(_exp), [str(e.label) for e in list(at5.expander) + list(at5.status)])
_df = at5.dataframe[0].value if at5.dataframe else None
_fr = list(_df.iloc[:, 0]) if _df is not None else []
chk("...con lo de SU grupo y las reglas del propietario, NO lo de otro grupo",
    sorted(_fr) == ["installed motor", "propia"], _fr)
_ms = next((m for m in at5.multiselect if m.key == "adm_mem_olv"), None)
chk("...y solo puede elegir para olvidar lo de su grupo", _ms is not None and list(_ms.options) == ["«propia» → Install sills"],
    _ms and list(_ms.options))
_bt(at5, "adm_mem_olvidar").click()
at5.run()
chk("«Forget» sin elegir nada: lo dice y no olvida", not at5.session_state["_olv"]
    and any("Choose what the assistant should forget first" in x for x in _todo(at5)))
next(m for m in at5.multiselect if m.key == "adm_mem_olv").select("MEM-1")
at5.run()
_bt(at5, "adm_mem_olvidar").click()
at5.run()
chk("olvidar: lo pide para SU grupo y como admin", at5.session_state["_olv"] == [(["MEM-1"], "cliente1", False)],
    at5.session_state["_olv"])
next(x for x in at5.text_input if x.key == "adm_mem_frase").set_value("installed lift motor")
next(x for x in at5.selectbox if x.key == "adm_mem_act").set_value("Install motor (machine)")
at5.run()
_bt(at5, "adm_mem_regla").click()
at5.run()
chk("enseñar una regla: con la frase, la actividad y SU grupo",
    at5.session_state["_reglas"] == [("installed lift motor", "Install motor (machine)", "cliente1", "admin1")],
    at5.session_state["_reglas"])
chk("...la lista de actividades es la del catálogo", "Install motor (machine)" in list(
    next(x for x in at5.selectbox if x.key == "adm_mem_act").options))
at6 = AppTest.from_string(APP, default_timeout=90)
at6.session_state["_admin"] = True
at6.session_state["_rol"] = "owner"
at6.session_state["_u"] = "duena"
at6.run()
_df6 = at6.dataframe[0].value if at6.dataframe else None
chk("el propietario lo ve TODO", _df6 is not None and sorted(_df6.iloc[:, 0]) == ["ajena", "installed motor", "propia"])
next(x for x in at6.text_input if x.key == "adm_mem_frase").set_value("x")
next(x for x in at6.selectbox if x.key == "adm_mem_act").set_value("Install sills")
at6.run()
_bt(at6, "adm_mem_regla").click()
at6.run()
chk("...y su regla es GLOBAL (sin grupo)", at6.session_state["_reglas"] == [("x", "Install sills", "", "duena")],
    at6.session_state["_reglas"])

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
