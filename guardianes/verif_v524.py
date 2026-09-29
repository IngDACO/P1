# -*- coding: utf-8 -*-
"""v524 · GUARDAR LO QUE SE PROPUSO Y SE DEJÓ SIN MARCAR.

Hasta v523 solo quedaba lo ACEPTADO (StageProgress con origen «log»). Lo que la app ofreció
y el trabajador dejó sin marcar no estaba en ningún sitio, así que «de cada 10 cosas que
propone, confirman X» no se podía calcular — y es justo el número con el que el usuario
decidirá cuándo darle más autonomía. Lo que protege:
  (a) ⚠️ que lo guardado sea EXACTAMENTE lo que se pintó: cada casilla ofrecida, con su
      tipo y el término que la trajo, ni una más ni una menos;
  (b) ⚠️ que «Nothing to credit» se registre como NADA aceptado aunque hubiera casillas
      marcadas (no se acreditaron), y «Confirm» como lo que sí;
  (c) que va en la MISMA escritura que la revisión (ni una llamada más contra la cuota, y
      ningún parte revisado sin registro), en la columna nueva AL FINAL (v363);
  (d) que un registro gigante no reviente la celda (50.000 caracteres): se recorta, y el
      recorte queda dicho;
  (e) que `acierto` cuente por TIPO — una propuesta suelta rechazada es un error de la app;
      una opción de lista sin marcar, no — y aguante registros rotos o recortados.
Todo EJECUTANDO (v378), la pantalla con AppTest.
"""
import datetime as _dt
import json
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


from core import daily_log as DL                                  # noqa: E402
from core import parte_propuestas as PP                           # noqa: E402
from core import stages as S                                      # noqa: E402
from core.num import col_letter                                   # noqa: E402

PLAN = S.plan_de("Installation", ())
NOTA = ("Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
        "Pendings lifts to do:\ncube also needs to be installed")


def _tipos(p):
    """Lo que la pantalla ofrecería para UN destino, por tipo — derivado de la lógica."""
    return {"a": [(f["orden"], f["actividad"]) for f in p["actividades"] if not f["hecha"]],
            "e": [(o["orden"], o["actividad"]) for e in p["etapas"] for o in e["opciones"]
                  if not o["hecha"]],
            "q": [(o["orden"], o["actividad"]) for q in p["preguntas"] for o in q["opciones"]
                  if not o["hecha"]]}


class _Reloj:
    AHORA = _dt.datetime(2026, 9, 30, 8, 15, 42)

    def now(self, g=None):
        return self.AHORA

    def today(self, g=None):
        return self.AHORA.date()


# ═════════════════════════════════════════════════════════════════
sec("1. La columna nueva, al FINAL (v363)")
chk("`Proposals` va detrás de `Reviewed`/`ReviewedBy`, al final",
    DL.HEADERS[-3:] == ["Reviewed", "ReviewedBy", "Proposals"], DL.HEADERS[-3:])
chk("...y las de v516 siguen en su sitio",
    DL.HEADERS[:8] == ["ID", "Group", "ProjectID", "Date", "Author", "Text", "Source",
                       "Created"], DL.HEADERS[:8])


class _WSdl:
    def __init__(self, filas):
        self.filas = [list(f) for f in filas]
        self.lotes = []
        self.revienta = False

    def get_all_records(self, numericise_ignore=None):
        if self.revienta:
            raise RuntimeError("429 quota exceeded")
        return [dict(zip(DL.HEADERS, f + [""] * (len(DL.HEADERS) - len(f)))) for f in self.filas]

    def append_row(self, fila, value_input_option=None):
        self.filas.append(list(fila))

    def batch_update(self, datos, value_input_option=None):
        self.lotes.append(datos)


_od = {k: getattr(DL, k) for k in ("_ws", "_invalidate", "clock", "_next_id")}
try:
    h = _WSdl([["LOG-0001", "cliente1", "PRJ-1", "2026-09-30", "ana", "x", "manual",
                "2026-09-30 07:00:00", "", "", ""]])
    DL._ws = lambda: h
    DL._invalidate = lambda: None
    DL.clock = _Reloj()
    DL._next_id = lambda recs: "LOG-0002"
    _ok, _ = DL.crear("PRJ-1", "cliente1", "Installed header", "ana")
    chk("`crear` escribe la fila ENTERA, con el registro vacío",
        _ok and len(h.filas[-1]) == len(DL.HEADERS) and h.filas[-1][-1] == "",
        (len(h.filas[-1]), len(DL.HEADERS)))

    sec("2. El registro va en la MISMA escritura que la revisión")
    REG = PP.registro({"PRJ-1": {"ofrecidas": [["a", 7, "Install headers", "instal header"]],
                                 "marcadas": [(7, "Install headers")], "hechas": []}},
                      app="v524")
    _ok, _m = DL.marcar_revisado("LOG-0001", "ana", propuestas=REG)
    chk("revisa", _ok, _m)
    _l = h.lotes[-1] if h.lotes else []
    chk("UNA sola escritura (ni una llamada más contra la cuota)", len(h.lotes) == 1, len(h.lotes))
    _col = {h_: col_letter(DL.HEADERS.index(h_) + 1) for h_ in ("Reviewed", "ReviewedBy", "Proposals")}
    chk("...con fecha, autor y registro, cada uno en SU columna y en SU fila",
        [x["range"] for x in _l] == ["%s2" % _col["Reviewed"], "%s2" % _col["ReviewedBy"],
                                     "%s2" % _col["Proposals"]], [x["range"] for x in _l])
    chk("...y el registro tal cual", _l[-1]["values"] == [[REG]] if _l else False)
    _n = len(h.lotes)
    _ok, _m = DL.marcar_revisado("LOG-0002", "ana")
    chk("sin registro (llamada vieja) también revisa, con la celda vacía",
        _ok and len(h.lotes) == _n + 1 and h.lotes[-1][-1]["values"] == [[""]])
    h.revienta = True
    _n = len(h.lotes)
    _ok, _m = DL.marcar_revisado("LOG-0001", "ana", propuestas=REG)
    chk("si la hoja falla, no escribe nada", not _ok and len(h.lotes) == _n, _m)
finally:
    for k, v in _od.items():
        setattr(DL, k, v)

# ═════════════════════════════════════════════════════════════════
sec("3. `registro`, `leer_registro` y `acierto`")
_pd = {"P1": {"ofrecidas": [["a", 7, "Install headers", "instal header"],
                            ["e", 11, "Door locks", "shaft wiring"],
                            ["e", 11, "Lights", "shaft wiring"],
                            ["q", 11, "Lights", "lights"],
                            ["q", 1, "Hang temporary work lighting", "lights"]],
              "marcadas": [(7, "Install headers"), (11, "Lights")],
              "hechas": [(7, "Install sills")]}}
r = PP.leer_registro(PP.registro(_pd, {"L2": "lift"}, {"3": "P3", "L2": None}, app="v524"))
chk("se lee de vuelta", bool(r) and r.get("v") == PP.REGISTRO_V, r.get("v"))
chk("...con la versión del código que propuso", r.get("app") == "v524")
chk("...lo ofrecido con su TIPO y el TÉRMINO que lo trajo",
    r["destinos"]["P1"]["ofrecidas"][0] == ["a", 7, "Install headers", "instal header"])
chk("...lo marcado", r["destinos"]["P1"]["marcadas"] == [[7, "Install headers"], [11, "Lights"]])
chk("...lo que ya estaba hecho", r["destinos"]["P1"]["hechas"] == [[7, "Install sills"]])
chk("...y lo que contestó y eligió",
    r["dudosos"] == {"L2": "lift"} and r["ascensores"] == {"3": "P3", "L2": None})
rn = PP.leer_registro(PP.registro(_pd, app="v524", nada=True))
chk("⚠️ «Nothing to credit»: NADA aceptado aunque hubiera marcas (no se acreditaron)",
    rn["nada"] is True and rn["destinos"]["P1"]["marcadas"] == []
    and len(rn["destinos"]["P1"]["ofrecidas"]) == 5)
chk("`leer_registro` no revienta con basura",
    all(PP.leer_registro(x) == {} for x in ("", None, "no es json", "[1, 2]", 42)))

a = PP.acierto([PP.registro(_pd, app="v524"), PP.registro(_pd, app="v524", nada=True),
                "basura", None])
chk("`acierto` cuenta los partes (y salta lo ilegible)", a["partes"] == 2 and a["nada"] == 1,
    (a["partes"], a["nada"]))
chk("...y por TIPO: sueltas 1 de 2, listas 1 de 4, preguntas 1 de 4",
    a["a"] == {"ofrecidas": 2, "marcadas": 1} and a["e"] == {"ofrecidas": 4, "marcadas": 1}
    and a["q"] == {"ofrecidas": 4, "marcadas": 1}, (a["a"], a["e"], a["q"]))

# ⚠️ El tope: una celda aguanta 50.000 caracteres y por encima la escritura FALLA — el
# parte se quedaría sin revisar. Se fabrica un registro enorme a propósito.
# ⚠️ Dimensionado para caer en el PRIMER recorte: con términos no cabe (~65.000) y sin ellos
# sí (~33.000). La primera versión de esta prueba era tan grande que saltaba directo a
# «cuentas», y el recorte de términos no se ejercitaba nunca (trampa nº1).
_gordo = {"P%d" % i: {"ofrecidas": [["e", 11, "Actividad %d %s" % (j, "x" * 40), "t" * 60]
                                    for j in range(100)],
                      "marcadas": [(11, "Actividad 1 " + "x" * 40)], "hechas": []}
          for i in range(5)}
_sin = len(json.dumps({"x": _gordo}, ensure_ascii=False, separators=(",", ":")))
s1 = PP.registro(_gordo, app="v524")
r1 = PP.leer_registro(s1)
chk("control: sin recortar NO cabría (%d > 45000)" % _sin, _sin > 45000)
chk("un registro enorme cabe en la celda (%d ≤ 45000)" % len(s1),
    len(s1) <= 45000 and bool(r1), len(s1))
chk("...recortando solo los TÉRMINOS, y diciéndolo", r1.get("recortado") == "terminos"
    and all(len(o) == 3 for o in r1["destinos"]["P0"]["ofrecidas"]), r1.get("recortado"))
chk("...con lo ofrecido y lo marcado ENTEROS, que es lo que se mide",
    PP.acierto([s1])["e"] == {"ofrecidas": 500, "marcadas": 5}, PP.acierto([s1])["e"])
_colosal = {"P%d" % i: {"ofrecidas": [["e", 11, "A%d %s" % (j, "y" * 80), "t"] for j in range(200)],
                        "marcadas": [], "hechas": []} for i in range(20)}
s2 = PP.registro(_colosal, app="v524")
r2 = PP.leer_registro(s2)
chk("uno colosal se queda en CUENTAS, y cabe",
    len(s2) <= 45000 and r2.get("recortado") == "cuentas"
    and r2["destinos"]["P0"]["ofrecidas"] == 200, (len(s2), r2.get("recortado")))
chk("...y `acierto` lo salta sin romperse",
    PP.acierto([s2])["partes"] == 1 and PP.acierto([s2])["e"]["ofrecidas"] == 0)

# ═════════════════════════════════════════════════════════════════
sec("4. Las propuestas llevan el TÉRMINO que las trajo")
_p = PP.propuestas(NOTA, PLAN, {})
_t = {f["actividad"]: f.get("termino") for f in _p["actividades"]}
chk("«Install headers» lleva su término", bool(_t.get("Install headers")), _t)

# ═════════════════════════════════════════════════════════════════
sec("5. La tarjeta EJECUTADA (AppTest): lo guardado es lo que se pintó")
from streamlit.testing.v1 import AppTest                          # noqa: E402

APP = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import clock, daily_log as DL, daily_log_ui as DLU
from core import projects as P, stage_progress as SP, stages as S

PLAN = S.plan_de("Installation", ())
HOY = "2026-09-30"
PRJS = {"PRJ-9001": "ZZ Test tower · Lift 1", "PRJ-9003": "ZZ Test tower · Lift 3",
        "PRJ-9002": "ZZ Other job"}
ss = st.session_state
ss.setdefault("_rev", {})
ss.setdefault("_reg", {})
ss.setdefault("_cred", [])
ss.setdefault("_hecho", {"PRJ-9001": {(7, "Install sills"): 100.0}})
ss.setdefault("_falla", False)
LOGS = [
    {"ID": "LOG-9010", "Author": "campo000", "Created": HOY + " 17:30:00",
     "Text": "Installed header\nShaft wiring done"},
    {"ID": "LOG-9003", "Author": "campo000", "Created": HOY + " 16:40:00",
     "Text": "lift 3 installed headers\nlift 1 installed sills\nL2 call button"},
    {"ID": "LOG-9002", "Author": "campo000", "Created": HOY + " 16:30:00",
     "Text": "Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
             "Pendings lifts to do:\ncube also needs to be installed"},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001", Date=HOY)
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = HOY + " 17:40:00", ss["_rev"][r["ID"]]
        out.append(_r)
    return out


def _acreditar(pid, grupo, prj, creditos, quien="", origen=SP.MANUAL):
    ss["_cred"].append({"pid": pid, "origen": origen, "creditos": [dict(c) for c in creditos]})
    if ss["_falla"]:
        return False, "boom"
    return True, "ok"


def _revisar(lid, quien, propuestas=""):
    ss["_rev"][lid] = quien
    ss["_reg"][lid] = propuestas
    return True, "Reviewed."


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = _revisar
DL.crear = lambda *a, **k: (True, "LOG-X")
clock.today = lambda grupo=None: _dt.date(2026, 9, 30)
P.get_project = lambda pid: {"ID": pid, "Name": PRJS.get(pid, pid), "Type": "Installation"}
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [
    {"ID": k, "Name": v} for k, v in PRJS.items()]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: dict(ss["_hecho"].get(pid, {}))
SP.acreditar = _acreditar
SP.de_parte = lambda pid, lid: []
DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _app(**estado):
    at = AppTest.from_string(APP, default_timeout=90)
    for k, v in estado.items():
        at.session_state[k] = v
    return at.run()


def _cb(at, pre):
    return [c for c in at.checkbox if (c.key or "").startswith(pre)]


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _pintadas(at, pre):
    """(tipo, orden, actividad) de cada casilla PINTADA, sacado de su key."""
    out = set()
    for c in _cb(at, pre):
        _r = c.key[len(pre):]
        _t, _resto = _r.split("_", 1)
        if _t == "q":
            _resto = _resto.split("_", 1)[1]          # fuera el término de la pregunta
        _o, _act = _resto.split("_", 1)
        out.add((_t, int(_o), _act))
    return out


at = _app()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
K2 = "fld_pp_LOG-9002_PRJ-9001_"
_pint = _pintadas(at, K2)
for _k in (K2 + "a_7_Install headers", K2 + "e_11_Lights", K2 + "q_lights_11_Lights"):
    _c = [c for c in at.checkbox if c.key == _k]
    if _c:
        _c[0].check()
    else:
        fallo("no aparece la casilla %s" % _k)
at.run()
_b = _bt(at, "fld_pp_LOG-9002_ok")
if _b is not None:
    _b.click()
    at.run()
R = PP.leer_registro(at.session_state["_reg"].get("LOG-9002", "")) \
    if "LOG-9002" in at.session_state["_reg"] else {}
chk("al confirmar, se guarda un registro", bool(R), at.session_state["_reg"])
_d = (R.get("destinos") or {}).get("PRJ-9001", {})
_of = {(o[0], int(o[1]), o[2]) for o in _d.get("ofrecidas", [])}
chk("⚠️ lo guardado es EXACTAMENTE lo que se pintó (%d casillas)" % len(_pint),
    len(_pint) >= 10 and _of == _pint, (len(_of), len(_pint), sorted(_of ^ _pint)[:3]))
_esp = _tipos(PP.propuestas(NOTA, PLAN, {}))
chk("...y por tipo, lo que saca la lógica (%d sueltas, %d de lista, %d de pregunta)"
    % tuple(len(_esp[t_]) for t_ in "aeq"),
    all(sum(1 for o in _d.get("ofrecidas", []) if o[0] == t_) == len(_esp[t_]) for t_ in "aeq"))
chk("...cada una con el término que la trajo",
    bool(_d.get("ofrecidas")) and all(len(o) == 4 and o[3] for o in _d["ofrecidas"]))
chk("lo marcado: las DOS actividades (la tercera marca era la misma)",
    sorted(tuple(x) for x in _d.get("marcadas", [])) == [(7, "Install headers"), (11, "Lights")],
    _d.get("marcadas"))
chk("no es «nada», y lleva la versión del código",
    R.get("nada") is False and bool(R.get("app")), (R.get("nada"), R.get("app")))
_ac = PP.acierto([R])
chk("`acierto` sobre ese parte: suelta 1/1, lista 1/8, pregunta 1/5",
    _ac["a"] == {"ofrecidas": 1, "marcadas": 1} and _ac["e"]["marcadas"] == 1
    and _ac["q"]["marcadas"] == 1, (_ac["a"], _ac["e"], _ac["q"]))

# ── «Nothing to credit» con algo marcado ──
_c = [c for c in at.checkbox if c.key == "fld_pp_LOG-9010_PRJ-9001_a_7_Install headers"]
if _c:
    _c[0].check()
    at.run()
_n0 = len(at.session_state["_cred"])
_b = _bt(at, "fld_pp_LOG-9010_no")
if _b is not None:
    _b.click()
    at.run()
RN = PP.leer_registro(at.session_state["_reg"].get("LOG-9010", "")) \
    if "LOG-9010" in at.session_state["_reg"] else {}
_dn = (RN.get("destinos") or {}).get("PRJ-9001", {})
chk("«Nothing to credit»: se guarda como NADA, sin marcadas aunque hubiera una",
    RN.get("nada") is True and _dn.get("marcadas") == [] and len(_dn.get("ofrecidas", [])) >= 2,
    (RN.get("nada"), _dn.get("marcadas")))
chk("...y no se acredita nada", len(at.session_state["_cred"]) == _n0)

# ── varios ascensores: lo contestado y lo elegido ──
_r = [r for r in at.radio if r.key == "fld_pp_LOG-9003_dud_L2"]
if _r:
    _r[0].set_value("lift")
    at.run()
_sel = {s.key: s for s in at.selectbox if (s.key or "").startswith("fld_pp_LOG-9003_dest_")}
if "fld_pp_LOG-9003_dest_3" in _sel and "fld_pp_LOG-9003_dest_1" in _sel:
    _sel["fld_pp_LOG-9003_dest_3"].set_value("PRJ-9003")
    _sel["fld_pp_LOG-9003_dest_1"].set_value("PRJ-9001")
    at.run()
_c = [c for c in at.checkbox if c.key == "fld_pp_LOG-9003_PRJ-9003_a_7_Install headers"]
if _c:
    _c[0].check()
    at.run()
_b = _bt(at, "fld_pp_LOG-9003_ok")
if _b is not None:
    _b.click()
    at.run()
RM = PP.leer_registro(at.session_state["_reg"].get("LOG-9003", "")) \
    if "LOG-9003" in at.session_state["_reg"] else {}
chk("varios ascensores: se guarda lo que contestó de «L2»", RM.get("dudosos") == {"L2": "lift"},
    RM.get("dudosos"))
chk("...y la obra elegida para cada uno (L2 sin elegir = null)",
    RM.get("ascensores") == {"3": "PRJ-9003", "1": "PRJ-9001", "L2": None}, RM.get("ascensores"))
_m3 = (RM.get("destinos") or {}).get("PRJ-9003", {})
_m1 = (RM.get("destinos") or {}).get("PRJ-9001", {})
chk("...lo de cada obra en SU destino",
    _m3.get("marcadas") == [[7, "Install headers"]] and _m1.get("marcadas") == [],
    (_m3.get("marcadas"), _m1.get("marcadas")))
chk("...y lo ya hecho en lift 1 como HECHO, no como ofrecido",
    _m1.get("hechas") == [[7, "Install sills"]]
    and not [o for o in _m1.get("ofrecidas", []) if o[2] == "Install sills"], _m1)

# ── si `acreditar` falla, no hay registro (el parte sigue sin revisar) ──
at2 = _app(_falla=True)
_c = [c for c in at2.checkbox if c.key == K2 + "a_7_Install headers"]
if _c:
    _c[0].check()
    at2.run()
_b = _bt(at2, "fld_pp_LOG-9002_ok")
if _b is not None:
    _b.click()
    at2.run()
chk("si `acreditar` falla: ni revisión ni registro",
    "LOG-9002" not in at2.session_state["_reg"] and len(at2.session_state["_cred"]) >= 1,
    dict(at2.session_state["_reg"]))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
