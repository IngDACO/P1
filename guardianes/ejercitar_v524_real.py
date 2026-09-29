# -*- coding: utf-8 -*-
"""v524 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto.

⚠️ Lo que esto prueba y los tests de mesa NO: que en la hoja de verdad la columna nueva
(`Proposals`) nazca donde `marcar_revisado` la CALCULA — leído por un SEGUNDO camino
(gspread de solo lectura) —, que el registro vuelva IDÉNTICO por el lote de la app, y que
`acierto` saque de él lo mismo que se acreditó de verdad en StageProgress.
Datos de prueba («ZZ PRUEBA v524»), creados aquí y borrados pase lo que pase.
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


def respira(s=6):
    time.sleep(s)          # ⚠️ techo de 60 lecturas/min con UNA cuenta de servicio


import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402

from core import daily_log as DL                                  # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import parte_propuestas as PP                           # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v524"
CREADOS = []
NOTA = ("Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
        "Pendings:\ncube also needs to be installed")


def _ro():
    """El SEGUNDO camino, de SOLO LECTURA: los helpers de la app migran cabeceras."""
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def crudo(libro, hoja):
    try:
        return libro.worksheet(hoja).get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        return []


def foto():
    for h in ("Projects", "Activities", SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira(2)
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "Activities": len(H.registros("Activities") or []),
            "StageProgress": len(H.registros(SP.SHEET) or []),
            "DailyLogs": len(H.registros(DL.SHEET) or [])}


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


def pantalla(p, marcar):
    """Lo que anota la pantalla al pintar (`daily_log_ui._pintar`), sin Streamlit: aquí se
    prueba la HOJA, no la tarjeta (la tarjeta la ejecuta verif_v524 con AppTest)."""
    ofr = [["a", f["orden"], f["actividad"], f.get("termino", "")] for f in p["actividades"]
           if not f["hecha"]]
    ofr += [["e", o["orden"], o["actividad"], e["termino"]] for e in p["etapas"]
            for o in e["opciones"] if not o["hecha"]]
    ofr += [["q", o["orden"], o["actividad"], q["termino"]] for q in p["preguntas"]
            for o in q["opciones"] if not o["hecha"]]
    # Sin repetidos, como la pantalla: «Lights» sale en la lista de su etapa Y en la pregunta.
    return {"ofrecidas": ofr,
            "marcadas": list(dict.fromkeys((o, a) for _, o, a, _t in ofr if a in marcar)),
            "hechas": []}


RO = _ro()
_cab0 = (crudo(RO, DL.SHEET) or [[]])[0]
print("CABECERA DailyLogs ANTES · %d columnas" % len(_cab0))
ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))

try:
    sec("1. Una obra de prueba y un parte")
    _f = SC.filas_de_etapas("Installation", NS, (), None)
    _s = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_f)
    _ok, PID = P.create_project(
        GRUPO, MARCA, ns=NS, tipo="Installation", fecha_inicio="2026-10-01",
        fecha_fin_est=_s["fecha_fin"].strftime("%Y-%m-%d"), activities=_s["activities"],
        creado_por=YO, stage_plan=P.plan_nuevo("Installation", (), None))
    chk("obra creada", _ok, PID)
    if not _ok:
        raise SystemExit("sin obra no hay nada que ejercitar")
    CREADOS.append(PID)
    respira()
    P._invalidate()
    PRJ = P.get_project(PID) or {}
    _ok, LID = DL.crear(PID, GRUPO, NOTA, YO)
    chk("parte guardado", _ok, LID)
    respira()
    _v = crudo(RO, DL.SHEET)
    _cab = _v[0] if _v else []
    print("   CABECERA DailyLogs DESPUÉS · %d columnas" % len(_cab))
    chk("⚠️ en la hoja REAL `Proposals` nace AL FINAL, donde la calcula el módulo",
        _cab[:len(DL.HEADERS)] == DL.HEADERS, _cab)

    sec("2. Se «confirma» como lo haría la pantalla, y se guarda el registro")
    respira()
    PR = PP.propuestas(NOTA, SP.plan_de_obra(PRJ), SP.acreditado(PID))
    MARCAR = {"Install headers", "Lights"}
    X = pantalla(PR, MARCAR)
    chk("hay qué ofrecer (%d casillas) y qué marcar (%d)" % (len(X["ofrecidas"]),
                                                            len(X["marcadas"])),
        len(X["ofrecidas"]) >= 10 and len({a for _, a in X["marcadas"]}) == 2)
    respira()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, PP.creditos(X["marcadas"], LID), quien=YO,
                           origen=SP.PARTE)
    chk("se acredita lo marcado", _ok, _m)
    REG = PP.registro({PID: X}, app="v524-real")
    respira()
    _ok, _m = DL.marcar_revisado(LID, YO, propuestas=REG)
    chk("se revisa con su registro", _ok, _m)

    sec("3. ⚠️ Releído por los DOS caminos")
    respira()
    DL._invalidate()
    _p = [r for r in DL.partes(PID) if r.get("ID") == LID]
    chk("por el LOTE de la app: el registro vuelve IDÉNTICO",
        bool(_p) and _p[0].get("Proposals") == REG,
        (len(_p[0].get("Proposals", "")), len(REG)) if _p else None)
    respira()
    _v = crudo(RO, DL.SHEET)
    _fila = next((f for f in _v[1:] if f and f[0] == LID), [])
    _iP = DL.HEADERS.index("Proposals")
    chk("por el SEGUNDO camino: en su columna, idéntico",
        len(_fila) > _iP and _fila[_iP] == REG, len(_fila))
    chk("...y el TEXTO del parte intacto al lado",
        len(_fila) > 5 and _fila[DL.HEADERS.index("Text")] == NOTA)
    _ac = PP.acierto([_p[0].get("Proposals") if _p else ""])
    respira()
    SP._invalidate()
    _cr = {r.get("Activity") for r in SP.de_parte(PID, LID)}
    chk("`acierto` sobre lo guardado: lo marcado es lo que se ACREDITÓ de verdad",
        _cr == MARCAR and sum(_ac[t]["marcadas"] for t in "aeq") >= 2
        and _ac["a"]["marcadas"] == 1, (_cr, _ac))

    sec("4. Borrar la obra se lo lleva todo")
    _okd, _m = P.delete_project(PID)
    chk("se borra %s" % PID, _okd, _m)
    if _okd and PID in CREADOS:
        CREADOS.remove(PID)
    respira()
    for h in (SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira(3)
    chk("...ni parte ni crédito huérfano",
        not [r for r in (H.registros(SP.SHEET) or []) if str(r.get("ProjectID")) == PID]
        and not [r for r in (H.registros(DL.SHEET) or []) if str(r.get("ProjectID")) == PID])
finally:
    limpia()

respira(4)
DESPUES = foto()
print("")
print("DESPUES · %s" % " · ".join("%s %d" % kv for kv in DESPUES.items()))
chk("⚠️ la hoja quedó EXACTAMENTE como estaba (en filas)", DESPUES == ANTES,
    "antes=%s despues=%s" % (ANTES, DESPUES))

print("")
if fallos:
    print("FALLOS: %d de %d" % (len(fallos), n_ok + len(fallos)))
    sys.exit(1)
print("v524 HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
