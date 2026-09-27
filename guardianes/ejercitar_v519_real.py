# -*- coding: utf-8 -*-
"""v519 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto.

⚠️ Lo que esto prueba y los tests de mesa NO: que marcar una actividad INFORMATIVA en una
obra de verdad deje intacto lo que se lee DE LA HOJA — `Activities.Progress` y el avance
de la obra, que es lo que alimenta la curva S, el SPI y la reclamación. Con la hoja
sustituida, `verif_v519` demuestra que `acreditar` no llama al escritor; aquí se mira que
el número guardado siga siendo el mismo, releyéndolo.

⚠️ Y el 50/50: que una obra nueva selle 50, y que una que selló 14 lo conserve al
releerla — el reparto mueve el avance, y el avance es lo que se cobra.
"""
import json
import os
import sys
import time
from datetime import date

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dacox", "nombre": "dacox",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("\n%s" % x)


def respira(s=6):
    time.sleep(s)          # ⚠️ techo de 60 lecturas/min con UNA cuenta de servicio


from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402
from core import vocabulario as V                                 # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v519"
TRACCION = S.EXCLUYENTES["demolicion"]["opciones"][0]
CREADOS = []


def foto():
    """Con Activities y StageProgress: la lección de v518, donde la foto no contaba las
    filas que crear una obra escribe por debajo."""
    for h in ("Projects", "Activities", SP.SHEET, "DailyLogs"):
        H.invalidar(h)
    respira(2)
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "Activities": len(H.registros("Activities") or []),
            "StageProgress": len(H.registros(SP.SHEET) or []),
            "DailyLogs": len(H.registros("DailyLogs") or [])}


def obra(tipo, cond, pct=None):
    _f = SC.filas_de_etapas(tipo, NS, cond, pct)
    _s = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_f)
    _ok, pid = P.create_project(
        GRUPO, "%s %s" % (MARCA, tipo), ns=NS, tipo=tipo, fecha_inicio="2026-10-01",
        fecha_fin_est=_s["fecha_fin"].strftime("%Y-%m-%d"),
        activities=_s["activities"], creado_por=YO,
        stage_plan=P.plan_nuevo(tipo, cond, pct))
    if _ok:
        CREADOS.append(pid)
    return _ok, pid


def fila_actividad(pid, orden):
    P._invalidate()
    respira(3)
    return next((a for a in (P.list_activities(pid) or [])
                 if int(float(a.get("Order") or 0)) == orden), {})


def limpia():
    for pid in list(CREADOS):
        for intento in range(3):
            try:
                P.delete_project(pid)
                CREADOS.remove(pid)
                break
            except Exception as e:
                print("   (limpieza %s, intento %d: %s)" % (pid, intento + 1, e))
                time.sleep(8)


ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))

try:
    sec("1. Una instalación de verdad, con plan sellado")
    ok_i, PI = obra("Installation", ())
    chk("creada", ok_i, PI)
    if not ok_i:
        raise SystemExit("sin obra no hay nada que ejercitar")
    respira()
    P._invalidate()
    PRJ = P.get_project(PI) or {}
    DET = {e["numero"]: e for e in SP.detalle(PI, PRJ)}
    E7 = DET[7]
    O7 = E7["orden"]
    chk("la etapa 7 trae sus DOS informativas, releídas de la obra",
        len(E7["informativas"]) == 2, [a["nombre"] for a in E7["informativas"]])

    sec("2. Se deja la etapa 7 A MEDIAS con actividades que SÍ pesan")
    # ⚠️ A medias y no vacía: con la etapa a 0, «sigue a 0» no demostraría nada.
    respira()
    _ok, _msg = SP.acreditar(PI, GRUPO, PRJ,
                             [{"etapa": O7, "actividad": a["nombre"], "pct": 100}
                              for a in E7["actividades"][:3]], quien=YO)
    chk("se acreditan tres que pesan", _ok, _msg)
    _f = fila_actividad(PI, O7)
    ANTES_7 = float(_f.get("Progress") or 0)
    P._invalidate()
    respira(3)
    ANTES_OBRA = float((P.get_project(PI) or {}).get("Progress") or 0)
    chk("la fila 7 de Activities queda a medias (%.1f%%)" % ANTES_7, 0 < ANTES_7 < 100,
        ANTES_7)
    chk("...y la obra sube algo (%.2f%%)" % ANTES_OBRA, ANTES_OBRA > 0, ANTES_OBRA)

    sec("3. ⚠️ Se marcan las informativas, y lo GUARDADO no se mueve")
    respira()
    _ok, _msg = SP.acreditar(PI, GRUPO, PRJ,
                             [{"etapa": O7, "actividad": a["nombre"], "pct": 100}
                              for a in E7["informativas"]], quien=YO)
    chk("se marcan las dos informativas", _ok, _msg)
    respira()
    SP._invalidate()
    _cr = {str(r.get("Activity", "")) for r in SP.creditos(PI)}
    chk("...y quedan registradas en StageProgress (el hecho se guarda)",
        {a["nombre"] for a in E7["informativas"]} <= _cr, sorted(_cr))
    _f = fila_actividad(PI, O7)
    DESPUES_7 = float(_f.get("Progress") or 0)
    chk("⚠️ la fila 7 de Activities sigue EXACTAMENTE igual (%.1f → %.1f)"
        % (ANTES_7, DESPUES_7), DESPUES_7 == ANTES_7, (ANTES_7, DESPUES_7))
    P._invalidate()
    respira(3)
    DESPUES_OBRA = float((P.get_project(PI) or {}).get("Progress") or 0)
    chk("⚠️ y el avance de la OBRA —lo que se reclama— tampoco (%.2f → %.2f)"
        % (ANTES_OBRA, DESPUES_OBRA), DESPUES_OBRA == ANTES_OBRA, (ANTES_OBRA, DESPUES_OBRA))
    _det2 = {e["numero"]: e for e in SP.detalle(PI, PRJ)}
    chk("...y en pantalla salen MARCADAS (no se pierden)",
        all(a["pct"] >= 100 for a in _det2[7]["informativas"]),
        [a["pct"] for a in _det2[7]["informativas"]])

    sec("4. El vocabulario sobre la obra real")
    _r = V.buscar("Chaser job on level 3", SP.plan_de_obra(PRJ))
    chk("«chaser job» propone su informativa, marcada como que NO cuenta",
        [(c["actividad"], c["cuenta"]) for c in _r["candidatos"]]
        == [("Cut/expand concrete door openings (chaser job)", False)],
        [(c["actividad"], c["cuenta"]) for c in _r["candidatos"]])
    _r = V.buscar("roping all day", SP.plan_de_obra(PRJ))
    chk("«roping» propone belting (decisión A del usuario)",
        [c["actividad"] for c in _r["candidatos"]] == ["Install belts (motor, CW, cabin)"],
        [c["actividad"] for c in _r["candidatos"]])

    sec("5. ⚠️ El 50/50 solo para obras NUEVAS")
    respira()
    ok_n, PN = obra("Ripout + Installation", (TRACCION,))
    chk("combinada NUEVA creada", ok_n, PN)
    respira()
    ok_v, PV = obra("Ripout + Installation", (TRACCION,), 14.0)
    chk("combinada «vieja» (sella 14, como las de antes de v519)", ok_v, PV)
    respira()
    P._invalidate()
    _pn, _pv = P.get_project(PN) or {}, P.get_project(PV) or {}

    def _rip(prj):
        return round(sum(e["peso"] for e in SP.plan_de_obra(prj)
                         if e["pista"] == S.PISTA_RIPOUT), 2)

    chk("la NUEVA selló 50 en la hoja",
        json.loads(_pn.get("StagePlanJSON") or "{}").get("pct_ripout") == 50.0,
        json.loads(_pn.get("StagePlanJSON") or "{}").get("pct_ripout"))
    chk("...y su desmontaje pesa el 50%% al releerla (%.1f)" % _rip(_pn), _rip(_pn) == 50.0)
    chk("⚠️ la que selló 14 SIGUE en 14 al releerla (%.1f)" % _rip(_pv), _rip(_pv) == 14.0)

    sec("6. Borrar se lleva también los créditos informativos")
    for pid in (PI, PN, PV):
        _okd, _m = P.delete_project(pid)
        chk("se borra %s" % pid, _okd, _m)
        if _okd and pid in CREADOS:
            CREADOS.remove(pid)
        respira()
    H.invalidar(SP.SHEET)
    respira(3)
    _restos = [r for r in (H.registros(SP.SHEET) or [])
               if str(r.get("ProjectID", "")) in (PI, PN, PV)]
    chk("...y no queda ni un crédito huérfano, informativo o no", not _restos, len(_restos))

finally:
    limpia()

respira(4)
DESPUES = foto()
print("")
print("DESPUES · %s" % " · ".join("%s %d" % kv for kv in DESPUES.items()))
chk("⚠️ la hoja quedó EXACTAMENTE como estaba", DESPUES == ANTES,
    "antes=%s despues=%s" % (ANTES, DESPUES))

print("")
if fallos:
    print("FALLOS: %d de %d" % (len(fallos), n_ok + len(fallos)))
    sys.exit(1)
print("v519 HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
