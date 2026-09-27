# -*- coding: utf-8 -*-
"""v516 + v517 contra la HOJA REAL: parte escrito → releído → interpretado contra el plan
sellado de una obra de verdad (método v344: foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto).

⚠️ Lo que esto prueba y los tests de mesa NO: que las dos piezas encajen por el camino de
la app. El texto no llega del guion sino de la hoja —pasando por el lote, que es como lee
la app—, y el plan no se construye aquí sino que se relee del `StagePlanJSON` sellado en
la obra. Si alguna de las dos cosas tiene una forma distinta de la que supongo, todo lo
anterior da igual.

⚠️ Y una pregunta concreta que solo la hoja contesta: ¿la raya «—» de «door blades —
Lift 3» sobrevive al viaje por Sheets? La frontera de oración del vocabulario depende de
ella. Si volviera como otro carácter, una frase que corta dejaría de cortar.
"""
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


def respira(s=1.5):
    time.sleep(s)          # ⚠️ techo de 60 lecturas/min con UNA cuenta de servicio


from core import daily_log as DL                                  # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402
from core import vocabulario as V                                 # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v517"
TRACCION = S.EXCLUYENTES["demolicion"]["opciones"][0]
CREADOS = []


def foto():
    """⚠️ Con `Activities` y `StageProgress`, no solo lo que este ejercicio escribe a
    mano. La primera versión contaba Projects y DailyLogs y NO las 32 filas de
    actividades que crear dos obras escribe por debajo: si `delete_project` dejara de
    borrarlas, la foto habría salido idéntica y el ejercicio en verde. Lo vio la
    verificación por el segundo camino, no el ejercicio."""
    for h in ("Projects", "Activities", SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira()
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "Activities": len(H.registros("Activities") or []),
            "StageProgress": len(H.registros(SP.SHEET) or []),
            "DailyLogs": len(H.registros(DL.SHEET) or [])}


def obra(tipo, cond):
    _f = SC.filas_de_etapas(tipo, NS, cond)
    _s = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_f)
    _ok, pid = P.create_project(
        GRUPO, "%s %s" % (MARCA, tipo), ns=NS, tipo=tipo, fecha_inicio="2026-10-01",
        fecha_fin_est=_s["fecha_fin"].strftime("%Y-%m-%d"),
        activities=_s["activities"], creado_por=YO, stage_plan=P.plan_nuevo(tipo, cond))
    if _ok:
        CREADOS.append(pid)
    return _ok, pid


def relee(pid):
    """Los partes TAL COMO LOS LEE LA APP: por el lote, con la caché tirada."""
    H.invalidar(DL.SHEET)
    DL._records_cached.clear()
    respira()
    return DL.partes(pid)


def limpia():
    """⚠️ SIEMPRE, aunque algo reviente: dejar basura en la hoja del cliente es peor que
    un guardián que falla. Con reintento, porque un 429 la tumbaba (v511)."""
    for pid in list(CREADOS):
        for intento in range(3):
            try:
                P.delete_project(pid)
                CREADOS.remove(pid)
                break
            except Exception as e:
                print("   (limpieza %s, intento %d: %s)" % (pid, intento + 1, e))
                time.sleep(6)


ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))

# (frase, a qué obra) — frases CITADAS en docs/ de partes reales
PARTES_INST = [
    "Installed/levelled MBB",
    "Installed 2 door blades — Lift 3",
    "Cleaned 4 car rails",
    "cleaned the pit, rails arriving tomorrow",
    "Wired 3-phase outlet for orange box — machine room",
]
PARTES_COMB = [
    "Wired 3-phase outlet for orange box — machine room",
    "three cages built",
    "Installed/levelled MBB",
]

try:
    sec("1. Dos obras de verdad, cada una con su plan SELLADO")
    ok_i, PI = obra("Installation", ())
    chk("instalación creada", ok_i, PI)
    respira()
    ok_c, PC = obra("Ripout + Installation", (TRACCION,))
    chk("combinada (desmontaje de tracción + instalación) creada", ok_c, PC)
    if not (ok_i and ok_c):
        raise SystemExit("sin obras no hay nada que ejercitar")
    respira()

    P._invalidate()
    respira()
    PRJ_I, PRJ_C = P.get_project(PI) or {}, P.get_project(PC) or {}
    PLAN_I, PLAN_C = SP.plan_de_obra(PRJ_I), SP.plan_de_obra(PRJ_C)
    # ⚠️ Antes de nada, que el plan SE LEA de la obra: sin él, `buscar` no filtra y todo
    # lo de abajo pasaría en verde sin proteger nada (trampa nº1).
    chk("el plan sellado de la instalación se relee de la hoja (%d etapas)" % len(PLAN_I),
        len(PLAN_I) == 14, len(PLAN_I))
    chk("...y el de la combinada (%d etapas)" % len(PLAN_C), len(PLAN_C) == 18, len(PLAN_C))
    ACT_I = {a["nombre"] for e in PLAN_I for a in e["actividades"]}
    ACT_C = {a["nombre"] for e in PLAN_C for a in e["actividades"]}

    sec("2. Los partes se ESCRIBEN en la hoja (v516)")
    for t in PARTES_INST:
        _ok, lid = DL.crear(PI, GRUPO, t, YO)
        chk("parte en la instalación: «%s»" % t[:44], _ok, lid)
        respira()
    for t in PARTES_COMB:
        _ok, lid = DL.crear(PC, GRUPO, t, YO)
        chk("parte en la combinada: «%s»" % t[:44], _ok, lid)
        respira()

    sec("3. ⚠️ Se RELEEN como los lee la app, y el texto vuelve intacto")
    LI, LC = relee(PI), relee(PC)
    chk("la instalación trae sus %d partes" % len(PARTES_INST),
        len(LI) == len(PARTES_INST), len(LI))
    chk("la combinada trae sus %d" % len(PARTES_COMB), len(LC) == len(PARTES_COMB), len(LC))
    _vueltos = {str(r.get("Text", "")) for r in LI}
    chk("cada texto vuelve BYTE A BYTE como se escribió",
        _vueltos == set(PARTES_INST), sorted(set(PARTES_INST) - _vueltos))
    # ⚠️ La raya: la frontera de oración depende de ella.
    chk("...incluida la raya «—» de «door blades — Lift 3»",
        any("—" in t for t in _vueltos), [t for t in _vueltos if "blades" in t])

    def props(txt, plan):
        r = V.buscar(txt, plan)
        return {c["actividad"] for c in r["candidatos"]}, r

    sec("4. El vocabulario sobre el texto RELEÍDO y el plan RELEÍDO")
    POR_TXT_I = {str(r.get("Text", "")): r for r in LI}
    POR_TXT_C = {str(r.get("Text", "")): r for r in LC}

    _p, _ = props(POR_TXT_I["Installed/levelled MBB"]["Text"], PLAN_I)
    chk("«Installed/levelled MBB» → Install motor bedplate", "Install motor bedplate" in _p, _p)
    _p, _ = props(POR_TXT_I["Installed 2 door blades — Lift 3"]["Text"], PLAN_I)
    chk("«2 door blades — Lift 3» → Install door panels (la raya corta «Lift 3»)",
        "Install door panels" in _p, _p)
    _p, _ = props(POR_TXT_I["Cleaned 4 car rails"]["Text"], PLAN_I)
    chk("«Cleaned 4 car rails» → Clean rails", "Clean rails" in _p, _p)
    _p, _ = props(POR_TXT_I["cleaned the pit, rails arriving tomorrow"]["Text"], PLAN_I)
    chk("⚠️ «cleaned the pit, rails arriving» NO acredita Clean rails (la coma corta)",
        "Clean rails" not in _p, _p)

    sec("5. ⚠️ La barandilla, con el plan de VERDAD")
    _t = "Wired 3-phase outlet for orange box — machine room"
    _pi, _ri = props(POR_TXT_I[_t]["Text"], PLAN_I)
    _pc, _rc = props(POR_TXT_C[_t]["Text"], PLAN_C)
    chk("el mismo parte en la INSTALACIÓN no propone nada", not _pi, _pi)
    chk("...y lo aparta como «fuera del plan», no lo tira",
        bool(_ri["fuera_del_plan"]), len(_ri["fuera_del_plan"]))
    chk("...y en la COMBINADA sí lo propone (el desmontaje está en su plan)",
        "Fully kill lift electrically / route mains power to tirak" in _pc, _pc)
    _p, _ = props(POR_TXT_C["three cages built"]["Text"], PLAN_C)
    chk("«three cages built» en la combinada → Hoardings & protection",
        "Hoardings & protection" in _p, _p)
    # ⚠️ El invariante entero, no ejemplos: NINGUNA propuesta de ningún parte sale del
    # plan de su obra.
    _fuera_i = [(t, a) for t in POR_TXT_I for a in props(t, PLAN_I)[0] if a not in ACT_I]
    _fuera_c = [(t, a) for t in POR_TXT_C for a in props(t, PLAN_C)[0] if a not in ACT_C]
    chk("NINGUNA propuesta de ningún parte se sale del plan de su obra",
        not _fuera_i and not _fuera_c, _fuera_i + _fuera_c)

    sec("6. ⚠️ Borrar las obras se lleva sus partes (sin limpiarlos a mano)")
    # ⚠️ No se borran los partes antes: el ejercicio de v514 tapaba el fallo de los
    # huérfanos haciéndolo él mismo, y entonces no verificaba nada — arreglaba.
    for pid in (PI, PC):
        _okd, _m = P.delete_project(pid)
        chk("se borra %s" % pid, _okd, _m)
        if _okd and pid in CREADOS:
            CREADOS.remove(pid)
        respira(3)
    H.invalidar(DL.SHEET)
    respira()
    _restos = [r for r in (H.registros(DL.SHEET) or [])
               if str(r.get("ProjectID", "")) in (PI, PC)]
    chk("...y NO queda ni un parte huérfano", not _restos, len(_restos))

finally:
    limpia()

respira(3)
DESPUES = foto()
print("")
print("DESPUES · %s" % " · ".join("%s %d" % kv for kv in DESPUES.items()))
chk("⚠️ la hoja quedó EXACTAMENTE como estaba", DESPUES == ANTES,
    "antes=%s despues=%s" % (ANTES, DESPUES))

print("")
if fallos:
    print("FALLOS: %d de %d" % (len(fallos), n_ok + len(fallos)))
    sys.exit(1)
print("PARTE + VOCABULARIO, HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
