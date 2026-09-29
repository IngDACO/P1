# -*- coding: utf-8 -*-
"""v525 · LA FECHA DEL PARTE (1A) Y LAS LÍNEAS SIN ASCENSOR (2B) — decisiones del usuario.

(1A) Lo confirmado desde un parte se fechaba el día de CONFIRMAR: un parte del lunes
confirmado el jueves decía que la etapa empezó el jueves, y la curva S real lo dibujaba así.
Ahora cada crédito lleva el día del TRABAJO (`StageProgress.WorkDate`) y las fechas reales de
la etapa salen de TODOS sus créditos: el inicio, el primero; el fin, el último.
(2B) En una nota de varios ascensores, lo que no nombra ninguno iba a la obra del parte —
decidir por él. Ahora lleva su propio selector, sin nada elegido.

Lo que protege, EJECUTANDO la cadena real (`acreditar` → `save_field_progress`) con las dos
hojas sustituidas, y la tarjeta con AppTest:
  (a) ⚠️ un parte de ANTES fecha la etapa en su día — y adelanta un inicio posterior, pero
      nunca atrasa uno anterior;
  (b) ⚠️ el fin es el ÚLTIMO día de trabajo de la etapa, no el del crédito que la cierra;
  (c) el camino a mano sigue fechando HOY; una fecha ilegible o del futuro, también;
  (d) los créditos de antes de v525 (sin `WorkDate`) cuentan con su día de registro;
  (e) las líneas sin ascensor no van a ninguna obra hasta que él elija, y un trozo sin nada
      que enseñar no deja un «→ obra» vacío.
"""
import datetime as _dt
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


from core import parte_propuestas as PP                           # noqa: E402
from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402

PLAN = S.plan_de("Installation", ())
HOY = _dt.date(2026, 10, 2)


class _Reloj:
    """Un reloj que FORMATEA de verdad (la lección de v516)."""
    AHORA = _dt.datetime(2026, 10, 2, 9, 30, 0)

    def now(self, g=None):
        return self.AHORA

    def today(self, g=None):
        return self.AHORA.date()


# ═════════════════════════════════════════════════════════════════
sec("1. La columna nueva y el día de trabajo")
chk("`WorkDate` va AL FINAL de StageProgress (v363)",
    SP.HEADERS[-1] == "WorkDate" and SP.HEADERS[:10] == [
        "ID", "Group", "ProjectID", "StageOrder", "Activity", "Pct", "Note", "Source",
        "UpdatedBy", "Updated"], SP.HEADERS)
_oc = SP.clock
try:
    SP.clock = _Reloj()
    _casos = [(None, "2026-10-02"), ("", "2026-10-02"), ("2026-09-29", "2026-09-29"),
              (_dt.date(2026, 9, 28), "2026-09-28"),
              (_dt.datetime(2026, 9, 27, 18, 0), "2026-09-27"),
              ("2026/09/29", "2026-10-02"), ("ayer", "2026-10-02"),
              ("2026-10-20", "2026-10-02"), ("2026-13-45", "2026-10-02")]
    _mal = [(e, SP._fecha_trabajo(e, "cliente1"), s) for e, s in _casos
            if SP._fecha_trabajo(e, "cliente1") != s]
    chk("el día de trabajo: el del parte; ilegible o del FUTURO → hoy (%d casos)" % len(_casos),
        not _mal, _mal)
finally:
    SP.clock = _oc
chk("un crédito de ANTES de v525 cuenta con su día de registro",
    SP._fecha_de({"Updated": "2026-09-21 08:00"}) == "2026-09-21"
    and SP._fecha_de({"WorkDate": "2026-09-19", "Updated": "2026-09-21 08:00"}) == "2026-09-19"
    and SP._fecha_de({}) == "")

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ La cadena REAL: acreditar → save_field_progress, con las hojas sustituidas")


class _WSsp:
    def __init__(self, filas):
        self.filas = [dict(f) for f in filas]
        self.nuevas, self.lotes = [], []

    def get_all_records(self, numericise_ignore=None):
        return [{h: str(f.get(h, "")) for h in SP.HEADERS} for f in self.filas]

    def append_rows(self, filas, value_input_option=None):
        self.nuevas += [list(x) for x in filas]

    def batch_update(self, datos, value_input_option=None):
        self.lotes.append(datos)


class _WSact:
    def __init__(self, filas):
        self.filas = filas
        self.lotes = []

    def get_all_records(self, numericise_ignore=None):
        return [{h: str(f.get(h, "")) for h in P.ACTIVITIES_HEADERS} for f in self.filas]

    def batch_update(self, datos, value_input_option=None):
        self.lotes.append(datos)


def _o_de(nombre):
    return next(i for i, e in enumerate(PLAN, start=1)
                if nombre in [a["nombre"] for a in e["actividades"]])


O7 = _o_de("Install headers")
# La etapa con MENOS actividades con peso: la que se puede completar entera en una prueba.
OC = min(range(1, len(PLAN) + 1), key=lambda i: len(PLAN[i - 1]["actividades"]))
ACTS_C = [a["nombre"] for a in PLAN[OC - 1]["actividades"]]
_orig_sp = {k: getattr(SP, k) for k in ("_ws", "_records", "_invalidate", "plan_de_obra",
                                        "version_desfasada", "clock")}
_orig_p = {k: getattr(P, k) for k in ("_activities_ws", "_invalidate",
                                      "_recompute_project_avance", "clock")}
_llegan = []
_orig_sfp = P.save_field_progress


def escenario(previos, act, creditos, fecha):
    """Corre `acreditar` de verdad. `previos` = créditos ya en StageProgress; `act` = la
    fila de Activities de cada etapa ({orden: {ActualStartDate, ActualEndDate, Progress}}).
    Devuelve (ok, {orden: {columna: valor escrito}}, filas nuevas de StageProgress)."""
    wsp = _WSsp([dict(p, ProjectID="PRJ-T", Group="cliente1") for p in previos])
    wact = _WSact([dict({"ProjectID": "PRJ-T", "Order": str(o), "Progress": "0"}, **v)
                   for o, v in act.items()])
    SP._ws = lambda: wsp
    SP._records = lambda: wsp.get_all_records()
    SP._invalidate = lambda: None
    SP.plan_de_obra = lambda prj: PLAN
    SP.version_desfasada = lambda prj: ""
    SP.clock = _Reloj()
    P._activities_ws = lambda: (wact, None)
    P._invalidate = lambda: None
    P._recompute_project_avance = lambda pid: None
    P.clock = _Reloj()
    _llegan.clear()
    _ok, _m = SP.acreditar("PRJ-T", "cliente1", {"ID": "PRJ-T"}, creditos, quien="u",
                           origen=SP.PARTE if fecha else SP.MANUAL, fecha=fecha)
    escrito = {}
    col = {i + 1: h for i, h in enumerate(P.ACTIVITIES_HEADERS)}
    from core.num import col_letter
    letra = {col_letter(i): h for i, h in col.items()}
    fila_de = {i + 2: int(f["Order"]) for i, f in enumerate(wact.filas)}
    for lote in wact.lotes:
        for x in lote:
            _l = "".join(ch for ch in x["range"] if ch.isalpha())
            _n = int("".join(ch for ch in x["range"] if ch.isdigit()))
            escrito.setdefault(fila_de.get(_n), {})[letra.get(_l)] = x["values"][0][0]
    return _ok, escrito, [dict(zip(SP.HEADERS, f)) for f in wsp.nuevas], wsp.lotes


def _cred(o, a, **k):
    return dict({"StageOrder": str(o), "Activity": a, "Pct": "100", "Source": "manual"}, **k)


try:
    P.save_field_progress = lambda pid, cambios: (_llegan.append([dict(c) for c in cambios])
                                                  or _orig_sfp(pid, cambios))
    # (a) primer crédito de la etapa, desde un parte del 29 confirmado el 2
    _ok, e, nuevas, _ = escenario([], {O7: {}}, [{"etapa": O7, "actividad": "Install headers",
                                                  "pct": 100, "nota": "LOG-1"}], "2026-09-29")
    chk("(a) parte del 29 confirmado el 2: la etapa EMPIEZA el 29, no el 2",
        _ok and e.get(O7, {}).get("ActualStartDate") == "2026-09-29", e)
    chk("...y el crédito guarda su día de trabajo",
        [x.get("WorkDate") for x in nuevas] == ["2026-09-29"], [x.get("WorkDate") for x in nuevas])
    # (b) la etapa ya tenía inicio el 1 (por un crédito del 1): el parte del 29 lo ADELANTA
    _ok, e, _, _ = escenario([_cred(O7, "Install sills", WorkDate="2026-10-01")],
                             {O7: {"ActualStartDate": "2026-10-01", "Progress": "10"}},
                             [{"etapa": O7, "actividad": "Install headers", "pct": 100,
                               "nota": "LOG-1"}], "2026-09-29")
    chk("(b) un parte ANTERIOR al inicio guardado lo adelanta (1 → 29)",
        _ok and e.get(O7, {}).get("ActualStartDate") == "2026-09-29", e)
    # (c) ...pero uno POSTERIOR no lo atrasa
    _ok, e, _, _ = escenario([_cred(O7, "Install sills", WorkDate="2026-09-20")],
                             {O7: {"ActualStartDate": "2026-09-20", "Progress": "10"}},
                             [{"etapa": O7, "actividad": "Install headers", "pct": 100,
                               "nota": "LOG-1"}], "2026-09-29")
    chk("(c) un parte POSTERIOR no atrasa el inicio (sigue el 20)",
        _ok and "ActualStartDate" not in e.get(O7, {}), e)
    # (d) completar la etapa: el fin es el día del trabajo que la cierra si es el último
    _prev = [_cred(OC, a, WorkDate="2026-09-25") for a in ACTS_C[:-1]]
    _ok, e, _, _ = escenario(_prev, {OC: {"ActualStartDate": "2026-09-25", "Progress": "80"}},
                             [{"etapa": OC, "actividad": ACTS_C[-1], "pct": 100,
                               "nota": "LOG-1"}], "2026-09-29")
    chk("(d) la etapa se completa con un parte del 29: TERMINA el 29, no el 2 (%d actividades)"
        % len(ACTS_C), _ok and e.get(OC, {}).get("ActualEndDate") == "2026-09-29", e)
    # (e) ...pero si otra de sus actividades se hizo DESPUÉS, el fin es ese día
    _prev = [_cred(OC, a, WorkDate="2026-09-25") for a in ACTS_C[:-2]] + \
            [_cred(OC, ACTS_C[-2], WorkDate="2026-10-01")]
    _ok, e, _, _ = escenario(_prev, {OC: {"ActualStartDate": "2026-09-25", "Progress": "80"}},
                             [{"etapa": OC, "actividad": ACTS_C[-1], "pct": 100,
                               "nota": "LOG-1"}], "2026-09-29")
    chk("(e) ⚠️ el fin es el ÚLTIMO día de trabajo de la etapa (el 1), no el del parte que la cierra",
        len(ACTS_C) >= 2 and _ok and e.get(OC, {}).get("ActualEndDate") == "2026-10-01", e)
    # (f) a mano, sin fecha: hoy, como siempre
    _ok, e, nuevas, _ = escenario([], {O7: {}}, [{"etapa": O7, "actividad": "Install headers",
                                                  "pct": 100, "nota": ""}], None)
    chk("(f) a mano, sin fecha: la etapa empieza HOY, como siempre",
        _ok and e.get(O7, {}).get("ActualStartDate") == "2026-10-02"
        and [x.get("WorkDate") for x in nuevas] == ["2026-10-02"], (e, nuevas))
    # (g) créditos de ANTES de v525 (sin WorkDate) cuentan con su día de registro
    _prev = [_cred(OC, a, Updated="2026-09-21 08:00") for a in ACTS_C[:-1]]
    _ok, e, _, _ = escenario(_prev, {OC: {"ActualStartDate": "2026-09-21", "Progress": "80"}},
                             [{"etapa": OC, "actividad": ACTS_C[-1], "pct": 100,
                               "nota": "LOG-1"}], "2026-09-29")
    chk("(g) con créditos viejos sin `WorkDate`: su día de registro cuenta (inicio 21, fin 29)",
        _ok and _llegan and _llegan[-1][0].get("inicio") == "2026-09-21"
        and e.get(OC, {}).get("ActualEndDate") == "2026-09-29", (_llegan[-1:], e))
    # (h) re-acreditar una fila existente escribe también su WorkDate
    _ok, e, _, lotes = escenario([_cred(O7, "Install headers", Pct="0", WorkDate="2026-09-10")],
                                 {O7: {}}, [{"etapa": O7, "actividad": "Install headers",
                                             "pct": 100, "nota": "LOG-2"}], "2026-09-29")
    _wd = [x["values"][0][0] for l in lotes for x in l
           if x["range"].startswith(SP._col_letter(SP._COL["WorkDate"]))]
    chk("(h) al re-acreditar una fila existente, su `WorkDate` se actualiza al del parte",
        _ok and _wd == ["2026-09-29"], _wd)
    # (i) una fecha del FUTURO no llega a la hoja
    _ok, e, nuevas, _ = escenario([], {O7: {}}, [{"etapa": O7, "actividad": "Install headers",
                                                  "pct": 100, "nota": ""}], "2026-10-20")
    chk("(i) una fecha del FUTURO se queda en hoy (ni en el crédito ni en la etapa)",
        _ok and [x.get("WorkDate") for x in nuevas] == ["2026-10-02"]
        and e.get(O7, {}).get("ActualStartDate") == "2026-10-02", (nuevas, e))
    # (j) reabrir: el fin se borra (igual que siempre), y lo desmarcado no fecha nada
    _prev = [_cred(OC, a, WorkDate="2026-09-25") for a in ACTS_C]
    _ok, e, _, _ = escenario(_prev, {OC: {"ActualStartDate": "2026-09-25",
                                          "ActualEndDate": "2026-09-29", "Progress": "100"}},
                             [{"etapa": OC, "actividad": ACTS_C[0], "pct": 0, "nota": ""}], None)
    chk("(j) reabrir la etapa borra su fin, como siempre",
        _ok and e.get(OC, {}).get("ActualEndDate") == "", e)
finally:
    for k, v in _orig_sp.items():
        setattr(SP, k, v)
    for k, v in _orig_p.items():
        setattr(P, k, v)
    P.save_field_progress = _orig_sfp

# ═════════════════════════════════════════════════════════════════
sec("3. `lineas_de` con las líneas SIN ascensor")
chk("`lineas_de(texto, \"\")` da las líneas que no nombran ascensor",
    PP.lineas_de("lift 3 installed headers\nInstalled cable tray\nlift 1 installed sills", "")
    == ["Installed cable tray"],
    PP.lineas_de("lift 3 installed headers\nInstalled cable tray\nlift 1 installed sills", ""))

# ═════════════════════════════════════════════════════════════════
sec("4. La tarjeta EJECUTADA (AppTest): la fecha del parte y el selector nuevo")
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
LOGS = [
    {"ID": "LOG-9012", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:50:00",
     "Text": "Install day 12\nlift 3 installed headers\nlift 1 installed headers"},
    {"ID": "LOG-9011", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:40:00",
     "Text": "lift 3 installed headers\nlift 1 installed sills\nInstalled cable tray"},
    {"ID": "LOG-9002", "Date": "2026-09-28", "Author": "campo000",
     "Created": HOY + " 16:30:00",
     "Text": "Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
             "Pendings lifts to do:\ncube also needs to be installed"},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001")
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = HOY + " 18:00:00", ss["_rev"][r["ID"]]
        out.append(_r)
    return out


def _acreditar(pid, grupo, prj, creditos, quien="", origen=SP.MANUAL, fecha=None):
    ss["_cred"].append({"pid": pid, "origen": origen, "fecha": fecha,
                        "creditos": [dict(c) for c in creditos]})
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


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _sel(at, key):
    return next((s for s in at.selectbox if s.key == key), None)


at = AppTest.from_string(APP, default_timeout=90).run()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])

# ── (1A) la fecha del parte llega a `acreditar` ──
_c = [c for c in at.checkbox if c.key == "fld_pp_LOG-9002_PRJ-9001_a_7_Install headers"]
if _c:
    _c[0].check()
    at.run()
_b = _bt(at, "fld_pp_LOG-9002_ok")
if _b is not None:
    _b.click()
    at.run()
_cr = [x for x in at.session_state["_cred"] if x["pid"] == "PRJ-9001"]
chk("⚠️ al confirmar un parte del 28 (hoy es 30), `acreditar` recibe el 28",
    len(_cr) == 1 and _cr[0]["fecha"] == "2026-09-28", _cr)

# ── (2B) las líneas sin ascensor ──
_s = _sel(at, "fld_pp_LOG-9011_dest__sin")
chk("nota de varios ascensores con una línea sin ascensor que propone: selector PROPIO",
    _s is not None and _s.value is None, None if _s is None else _s.value)
chk("...junto a los de cada ascensor",
    _sel(at, "fld_pp_LOG-9011_dest_3") is not None and _sel(at, "fld_pp_LOG-9011_dest_1") is not None)
chk("...con la línea que respalda, a la vista",
    any("Installed cable tray" in c.value for c in at.caption))
_k11 = [c.key for c in at.checkbox if (c.key or "").startswith("fld_pp_LOG-9011_")]
chk("⚠️ sin elegir obra, «Install cable tray» no se propone en NINGUNA",
    not [k for k in _k11 if k.endswith("Install cable tray")], _k11)
if _s is not None:
    _s.set_value("PRJ-9003")
    at.run()
_k11 = [c.key for c in at.checkbox if (c.key or "").startswith("fld_pp_LOG-9011_")]
_ct = [k for k in _k11 if k.endswith("Install cable tray")]
chk("elegida Lift 3: se propone allí, y solo allí",
    len(_ct) == 1 and _ct[0].startswith("fld_pp_LOG-9011_PRJ-9003_"), _k11)
if _ct:
    [c for c in at.checkbox if c.key == _ct[0]][0].check()
    at.run()
    _b = _bt(at, "fld_pp_LOG-9011_ok")
    if _b is not None:
        _b.click()
        at.run()
_R = PP.leer_registro(at.session_state["_reg"].get("LOG-9011", "")) \
    if "LOG-9011" in at.session_state["_reg"] else {}
chk("el registro guarda a dónde fueron las líneas sin ascensor",
    (_R.get("ascensores") or {}).get("") == "PRJ-9003", _R.get("ascensores"))
chk("una nota SIN varios ascensores no pregunta por las líneas sin ascensor",
    _sel(at, "fld_pp_LOG-9002_dest__sin") is None)

# ── un trozo sin nada que enseñar no deja un «→ obra» vacío ──
chk("«Install day 12» (no propone nada): sin selector de líneas sin ascensor",
    _sel(at, "fld_pp_LOG-9012_dest__sin") is None)
_s3, _s1 = _sel(at, "fld_pp_LOG-9012_dest_3"), _sel(at, "fld_pp_LOG-9012_dest_1")
if _s3 is not None and _s1 is not None:
    _s3.set_value("PRJ-9003")
    _s1.set_value("PRJ-9002")
    at.run()
_md = [m.value.strip() for m in at.markdown]
_cab12 = [m for m in _md if m.startswith("**→ ")]
chk("ambos ascensores a OTRAS obras: el trozo de esta (solo «Install day 12») no se pinta",
    _s3 is not None and "**→ ZZ Test tower · Lift 3**" in _cab12 and "**→ ZZ Other job**" in _cab12
    and "**→ ZZ Test tower · Lift 1**" not in _cab12, _cab12)

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
