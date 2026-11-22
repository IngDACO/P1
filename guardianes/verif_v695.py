# -*- coding: utf-8 -*-
"""v695 · Ciclo 6 → mejoras 2/3, EL PARTE Y EL AGENTE (22/11), con las decisiones del usuario:
- D2 / H10 · las puertas por PLANTA: «levels 5 and 6» de 8 acredita la parte hecha (25 %) y guarda las plantas
  (`plantas`, `stages.por_plantas`, la columna `Levels`); con todas, entera;
- D3 / H13 · los avisos de `flash` FLOTAN (no empujan la página al irse);
- H14 · desmarcar a mano lo que vino de un parte corrige la memoria del agente (`agente_memoria.desaprender`);
- H12 · lo no enviado se dice antes de confirmar, y lo empezado también va al To-do;
- H16 · el To-do desde el parte, con mayúscula y la fecha del parte; H22 · la oficina ve que el parte espera;
- H17 · un parte anterior al inicio de la obra se dice; H11 · «(1 change)».

Nada sale a la red ni escribe: el libro de mentira de `fixture_guardado`, hojas FALSAS, sustitutos y AppTest.
"""
import ast
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


def _fuente(rel):
    return open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    return next((n for n in ast.walk(ast.parse(_fuente(rel)))
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


from streamlit.testing.v1 import AppTest                                   # noqa: E402
import fixture_guardado as FG                                              # noqa: E402
from core import plantas as PL, stages as S, stage_progress as SP          # noqa: E402
from core import projects as P, agente_memoria as MEM, daily_log_ui as DLU  # noqa: E402
from core import stage_progress_ui as SPU, theme                           # noqa: E402
from core.num import col_letter                                            # noqa: E402

# ⚠️ trampa 48: lo real, antes de que un guion de AppTest lo sustituya en este proceso
_DESAPRENDER = MEM.desaprender
_REALES = {"_resto_agente": DLU._resto_agente, "_prueba": DLU._prueba}

# ═════════════════════════════════════════════════════════════════
print("1. D2 · las plantas de un parte")
for s, esp in (("Installed the landing door panels on levels 5 and 6.", [5, 6]),
               ("Did the doors on levels 3 and 4.", [3, 4]), ("floors 2-5 done", [2, 3, 4, 5]),
               ("level 3 and level 4", [3, 4]), ("stops 1, 2 & 4", [1, 2, 4]), ("landing no. 6", [6]),
               ("levels 3 to 5 and 7", [3, 4, 5, 7]), ("all levels done", list(range(1, 9))),
               ("L2 headers", []), ("level 12", []), ("Installed the door panels", [])):
    chk(f"«{s}» → {esp}", PL.de_texto(s, 8) == esp, PL.de_texto(s, 8))
chk("sin NS, nada", PL.de_texto("levels 3 and 4", 0) == [] and PL.de_texto("levels 3", None) == [])
chk("leer/texto", PL.leer("3,4, 6") == {3, 4, 6} and PL.texto({6, 3, 4}) == "3, 4, 6")
chk("stages.por_plantas: Landing Doors sí, Prepping no",
    S.por_plantas(S.PISTA_INSTALL, 7) and not S.por_plantas(S.PISTA_INSTALL, 2) and not S.por_plantas(None, None))

# ═════════════════════════════════════════════════════════════════
print("2. D2 · el crédito a medias, con sus plantas (stage_progress + Levels)")


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-11-22 10:00" if "%H" in f else "2026-11-22"

    def now(self, g=None):
        return self._T()


PRJ = {"ID": "PRJ-T", "Group": "cliente1", "Type": "Installation", "Name": "t", "NS": "8",
       "StagePlanJSON": P.plan_nuevo("Installation", ()), "Progress": "0", "Status": "Planned", "ManualStatus": ""}
PLAN = SP.plan_de_obra(PRJ)
O7 = next(i for i, e in enumerate(PLAN, start=1) if S.por_plantas(e.get("pista"), e.get("numero")))
DP = "Install door panels"
chk("el plan de instalación tiene Landing Doors con «Install door panels»",
    any(a["nombre"] == DP for a in PLAN[O7 - 1]["actividades"]), O7)
chk("HEADERS termina en «Levels» (al final: migra sola)", SP.HEADERS[-1] == "Levels")
_rr = [_sustituir(SP, clock=_Reloj(), _records=lambda: [])]
m = FG.montar(SP, P, PRJ)
try:
    ok, msg = SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": O7, "actividad": DP, "pct": 25.0, "nota": "LOG-13",
                                                     "niveles": [6, 5]}], quien="campo000", origen=SP.PARTE)
    _n = m.nuevas_sp()
    chk("a medias: la fila nueva lleva Pct 25 y Levels «5,6» (y cuadra con la cabecera)",
        ok and _n and _n[-1]["Pct"] == "25.0" and _n[-1]["Levels"] == "5,6" and len(m.sp.nuevas[-1]) == len(SP.HEADERS),
        (msg, _n))
    m.libro.llamadas.clear()
    ok, msg = SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": O7, "actividad": DP, "pct": 50.0, "nota": "LOG-14",
                                                     "niveles": [3, 4, 5, 6]}], quien="campo000", origen=SP.PARTE)
    _l = [x for lote in m.lotes_sp() for x in lote]
    _col = col_letter(SP.HEADERS.index("Levels") + 1)
    chk("…otro parte con más plantas reescribe la MISMA fila: Levels «3,4,5,6»",
        ok and any(x["range"].startswith(_col) and x["values"][0][0] == "3,4,5,6" for x in _l), _l)
    m.libro.llamadas.clear()
    ok, msg = SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": O7, "actividad": DP, "pct": 100.0, "nota": "",
                                                     "niveles": [1, 2, 3, 4, 5, 6, 7, 8]}], quien="campo000")
    _l = [x for lote in m.lotes_sp() for x in lote]
    chk("…entera: Levels vacío (entera = todas)", ok and any(x["range"].startswith(_col) and x["values"][0][0] == ""
                                                         for x in _l), _l)
finally:
    m.restaurar()

# ═════════════════════════════════════════════════════════════════
print("3. H14 · desmarcar a mano lo que vino de un parte corrige la memoria")
_LL = []
_rd = _sustituir(MEM, desaprender=lambda pares: _LL.append(list(pares)) or 1)
for _src, _orig, _pct, _esp, _txt in (("log", SP.MANUAL, 0, [("LOG-11", DP)], "desmarcado a mano: desaprende"),
                                       ("log", SP.PARTE, 0, None, "a 0 desde un parte (no a mano): nada"),
                                       ("manual", SP.MANUAL, 0, None, "lo que se marcó a mano: nada"),
                                       ("log", SP.MANUAL, 100, None, "re-marcado: nada")):
    _LL.clear()
    m = FG.montar(SP, P, PRJ, creditos=[{"StageOrder": str(O7), "Activity": DP, "Pct": "100", "Source": _src,
                                         "Note": "LOG-11" if _src == "log" else ""}])
    try:
        ok, msg = SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": O7, "actividad": DP, "pct": _pct}],
                               quien="campo000", origen=_orig)
    finally:
        m.restaurar()
    chk(_txt, ok and ((_LL == [_esp]) if _esp else (_LL == [])), (msg, _LL))
_rd()
for _x in _rr:
    _x()


class _Hoja:
    def __init__(self, cab, filas):
        self.cab, self.filas, self.escrito = list(cab), [dict(x) for x in filas], []

    def get_all_records(self, **k):
        return [dict(x) for x in self.filas]

    def batch_update(self, lote, **k):
        self.escrito += lote
        for it in lote:
            _c = "".join(ch for ch in it["range"] if ch.isalpha())
            _f = int("".join(ch for ch in it["range"] if ch.isdigit()))
            self.filas[_f - 2][next(h for i, h in enumerate(self.cab) if col_letter(i + 1) == _c)] = it["values"][0][0]


def _mem(mid, frase, act, log, c="1", x="0", kind="learned", activa=""):
    return {"ID": mid, "Phrase": frase, "Activity": act, "Kind": kind, "Confirmed": c, "Rejected": x, "Group": "cliente1",
            "CreatedBy": "campo000", "LogID": log, "Created": "", "Updated": "", "Active": activa}


_h = _Hoja(MEM.HEADERS, [_mem("MEM-29", "did the doors on levels 3 and 4", DP, "LOG-11"),
                         _mem("MEM-30", "did the doors on levels 3 and 4", "Tune doors", "LOG-11", c="0", x="1"),
                         # una REGLA con 1 confirmación: sin la protección se le restaría (lo destapó romper_v695)
                         _mem("MEM-31", "installed door panels", DP, "LOG-11", kind="rule", c="1"),
                         _mem("MEM-32", "x", DP, "LOG-11", activa="NO"),
                         _mem("MEM-33", "hung the doors", DP, "LOG-99")])
_rr = [_sustituir(MEM, _ws=lambda: _h, _invalidate=lambda: None, _ahora=lambda: "2026-11-22 17:00")]
n = _DESAPRENDER([("LOG-11", DP)])
_f = {r["ID"]: r for r in _h.filas}
chk("desaprender: la lección de ESE parte y esa actividad pasa a 0 confirmada / 1 rechazada",
    n == 1 and _f["MEM-29"]["Confirmed"] == "0" and _f["MEM-29"]["Rejected"] == "1", (n, _f["MEM-29"]))
chk("…y no toca una regla, una olvidada, otra actividad ni otro parte",
    _f["MEM-31"]["Confirmed"] == "1" and _f["MEM-32"]["Confirmed"] == "1" and _f["MEM-30"]["Rejected"] == "1"
    and _f["MEM-33"]["Confirmed"] == "1", _f)
chk("sin nada que deshacer, nada", _DESAPRENDER([]) == 0)
for _x in _rr:
    _x()

# ═════════════════════════════════════════════════════════════════
print("4. D2 · la tarjeta del parte: las plantas en la casilla y el crédito a medias")
_p = {"actividades": [{"orden": O7, "etapa": "Landing Doors", "actividad": DP, "hecha": False, "fuente": "agente",
                       "termino": "Installed the landing door panels on levels 5 and 6.",
                       "pruebas": ["Installed the landing door panels on levels 5 and 6."]},
                      {"orden": 2, "etapa": "Prepping", "actividad": "Prep doors (panels/blades, frames)", "hecha": False,
                       "fuente": "agente", "termino": "prepped the doors on levels 1 and 2", "pruebas": []}],
      "etapas": [], "preguntas": [], "pendientes": [], "retiradas": [], "fuera": []}
_cred = [{"StageOrder": str(O7), "Activity": DP, "Pct": "25", "Levels": "3,4"}]
_pl = DLU._plantas_de(_p, PLAN, 8, _cred)
chk("_plantas_de: Install door panels, nuevas 5,6 y todas 3,4,5,6 (suma lo acreditado)",
    _pl == {(O7, DP): {"nuevas": [5, 6], "todas": [3, 4, 5, 6], "ns": 8}}, _pl)
chk("…una actividad que NO es por plantas (Prepping) no entra", (2, "Prep doors (panels/blades, frames)") not in _pl)
_p2 = dict(_p, actividades=[dict(_p["actividades"][0], termino="all levels done", pruebas=[])])
chk("…«all levels»: entera, como siempre", DLU._plantas_de(_p2, PLAN, 8, []) == {})
chk("…sin NS: nada", DLU._plantas_de(_p, PLAN, 0, []) == {})
chk("_etq_plantas: «levels 5, 6 → 4 of 8 levels (50%)»",
    DLU._etq_plantas(_pl[(O7, DP)]) == "levels 5, 6 → 4 of 8 levels (50%)", DLU._etq_plantas(_pl[(O7, DP)]))
_cr = DLU._a_medias([{"etapa": O7, "actividad": DP, "pct": 100.0, "nota": "LOG-13"},
                     {"etapa": 1, "actividad": "Receive toolbox", "pct": 100.0, "nota": "LOG-13"}], _pl)
chk("_a_medias: la de plantas al 50 % con sus plantas; la otra, entera",
    _cr[0]["pct"] == 50.0 and _cr[0]["niveles"] == [3, 4, 5, 6] and _cr[1]["pct"] == 100.0 and "niveles" not in _cr[1], _cr)
_cr = DLU._a_medias([{"etapa": O7, "actividad": DP, "pct": 100.0, "nota": "L"}],
                    {(O7, DP): {"nuevas": [7, 8], "todas": list(range(1, 9)), "ns": 8}})
chk("…con las 8, entera", _cr[0]["pct"] == 100.0, _cr)
_fp = ast.unparse(_func("core/daily_log_ui.py", "_propuestas"))
chk("Confirm acredita con `_a_medias` y la tarjeta pinta con `plantas`",
    "_a_medias(PP.creditos(ticks, lid), _plantas_d.get(d))" in _fp and "plantas=_plantas_d[d]" in _fp)
PIN = r'''
import streamlit as st
from core import daily_log_ui as D
D._prueba = lambda f, oficina=False: None
D._resto_agente = lambda p, todo=None, k="": None
st.session_state["_R"] = D._pintar(st.session_state["_P"], "k", plantas=st.session_state["_PL"])
'''
at = AppTest.from_string(PIN, default_timeout=60)
at.session_state["_P"], at.session_state["_PL"] = {**_p, "actividades": _p["actividades"][:1]}, _pl
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("la casilla dice «Install door panels  ·  levels 5, 6 → 4 of 8 levels (50%)» (y viene marcada)",
    any(str(c.label) == DP + "  ·  levels 5, 6 → 4 of 8 levels (50%)" and c.value for c in at.checkbox),
    [(c.label, c.value) for c in at.checkbox])
for _k, _v in _REALES.items():                     # trampa 48: el guion los dejó sustituidos en este proceso
    setattr(DLU, _k, _v)

# ═════════════════════════════════════════════════════════════════
print("5. Progress: la actividad a medias lo dice; «(1 change)»")
_c = {(O7, DP): {"StageOrder": str(O7), "Activity": DP, "Pct": "25", "Levels": "3,4", "UpdatedBy": "campo000",
                 "WorkDate": "2026-11-22", "Source": "log", "Note": "LOG-13"}}
chk("_parcial: «· levels 3, 4 done (25%)»", "levels 3, 4 done (25%)" in SPU._parcial(_c, O7, DP, 25), SPU._parcial(_c, O7, DP, 25))
chk("…entera o a 0, nada", SPU._parcial(_c, O7, DP, 100) == "" and SPU._parcial(_c, O7, DP, 0) == "")
_rn = _sustituir(SPU, _nombre=lambda u: "hjg,ujgjg")
_ay = SPU._ayuda(_c, O7, DP, 25)
chk("el «?» de la casilla a medias: quién, de qué parte y qué plantas",
    _ay and "Credited by hjg,ujgjg" in _ay and "LOG-13" in _ay and "levels 3, 4" in _ay, _ay)
_rn()
chk("«Save stage N (1 change)» en singular", "Save stage {n} (1 change)" in _fuente("core/stage_progress_ui.py"))

# ═════════════════════════════════════════════════════════════════
print("6. D3 · los avisos flotan")
_css = theme._CSS
_i = _css.find(".st-key-cpx_flash {")
_bloque = _css[_i:_css.find("}", _i)]
chk("`.st-key-cpx_flash`: position fixed, sin pointer-events y con su desvanecido",
    _i > 0 and "position: fixed !important" in _bloque and "pointer-events: none" in _bloque
    and "animation: cpxFlashFuera" in _bloque and "@keyframes cpxFlashFuera" in _css, _bloque)
chk("…y su envoltorio, fuera del flujo (no deja hueco al irse)",
    '[data-testid="stLayoutWrapper"]:has(> .st-key-cpx_flash)' in _css and "position: absolute !important" in
    _css[_css.find('[data-testid="stLayoutWrapper"]:has(> .st-key-cpx_flash)'):][:200])
from core import flash                                                    # noqa: E402
chk("…la clave es la del bloque de `flash`", flash.BLOQUE == "cpx_flash")

# ═════════════════════════════════════════════════════════════════
print("7. H12 · lo no enviado y lo empezado")
_reg = {"fragmentos": [{"clase": "problem", "texto": "The sparky did not turn up again."},
                       {"clase": "problem", "texto": "Platform sways"}, {"clase": "done", "texto": "x"}],
        "avisos": [{"texto": "Platform sways", "alerta": "ALR-1"}]}
chk("_sin_enviar: solo el problema que no se mandó", DLU._sin_enviar(_reg) == ["The sparky did not turn up again."],
    DLU._sin_enviar(_reg))
chk("…y la tarjeta lo dice antes de Confirm", "_no_env = _sin_enviar(reg) if reg and (not oficina) else []" in _fp
    and _fp.find("Not sent to the office yet") < _fp.find("Confirm the {n} ticked"))
EMP = r'''
import streamlit as st
from core import daily_log_ui as D, tareas
tareas.pendientes = lambda pid: list(st.session_state.get("_TP", []))
D._resto_agente({"empezadas": [{"texto": "Half way through the cabin walls."}]}, todo=("LOG-11", "PRJ-T"), k="k")
'''
at = AppTest.from_string(EMP, default_timeout=60).run()
chk("lo EMPEZADO ofrece «Add to To-do»", any(b.key == "k_tde0" for b in at.button), [b.key for b in at.button])

# ═════════════════════════════════════════════════════════════════
print("8. H16 · el To-do desde el parte")
chk("con mayúscula", DLU._tarea_de({"pruebas": ["we will re-gap the guide shoes tomorrow"]})
    == "We will re-gap the guide shoes tomorrow")
TD = r'''
import streamlit as st
from core import daily_log_ui as D, daily_log as DL, tareas
DL.partes = lambda pid: [{"ID": "LOG-10", "Date": "2026-11-22"}]
tareas.crear = lambda pid, g, texto, autor: (st.session_state.setdefault("_C", []).append(texto), (True, "TSK-1"))[1]
tareas.pendientes = lambda pid: list(st.session_state.get("_TP", []))
if "_H" not in st.session_state:
    st.session_state["_H"] = 1
    st.session_state["_dl_tarea"] = {"lid": "LOG-10", "pid": "PRJ-T", "texto": "We will re-gap the guide shoes tomorrow"}
    D._apuntar_tarea("G", "campo000", {"PRJ-T"})
D._boton_tarea({"pruebas": ["we will re-gap the guide shoes tomorrow"]}, ("LOG-10", "PRJ-T"), "kb")
'''
at = AppTest.from_string(TD, default_timeout=60).run()
chk("se guarda con la fecha del parte: «We will re-gap … tomorrow (from the log of 22/11/2026)»",
    at.session_state["_C"] == ["We will re-gap the guide shoes tomorrow (from the log of 22/11/2026)"],
    at.session_state["_C"] if "_C" in at.session_state else None)
at = AppTest.from_string(TD, default_timeout=60)
at.session_state["_H"] = 1
at.session_state["_TP"] = [{"Text": "We will re-gap the guide shoes tomorrow (from the log of 22/11/2026)"}]
at.run()
chk("…y, ya en la lista (con su fecha detrás), no se ofrece otra vez", not any(b.key == "kb" for b in at.button)
    and any("In the job's To-do" in str(c.value) for c in at.caption), [b.key for b in at.button])

# ═════════════════════════════════════════════════════════════════
print("9. H22 · la oficina ve que el parte espera; H17 · antes del inicio de la obra")
ER = r'''
import streamlit as st
from core import daily_log_ui as D
D._nombre = lambda u: "hjg,ujgjg"
D._estado_revision({"ID": "LOG-13", "Author": "campo000", "Text": "C6 TEST 4", "Created": "2026-11-22 17:06:36",
                    "Date": "2026-11-22", "Reviewed": ""}, "PRJ-T")
'''
at = AppTest.from_string(ER, default_timeout=60).run()
chk("«Not reviewed by hjg,ujgjg yet · the office can review it from 24/11/2026.»",
    any("Not reviewed by hjg,ujgjg yet · the office can review it from 24/11/2026." in str(c.value) for c in at.caption),
    [c.value for c in at.caption])
_rc = ast.unparse(_func("core/daily_log_ui.py", "render_campo"))
chk("H17: al guardar, si el día es anterior al inicio de la obra, se avisa",
    "if _ini and dia and (dia < _ini):" in _rc and "This job starts on {d} and the log is for {x}." in _rc)

print()
print("verif_v695: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v695: TODO OK")
sys.exit(1 if FALLOS else 0)
