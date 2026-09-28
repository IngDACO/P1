# -*- coding: utf-8 -*-
"""v523 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO →
restaurar → segunda foto.

⚠️ Lo que esto prueba y los tests de mesa NO:
  · que en la hoja REAL `Reviewed`/`ReviewedBy` queden en las columnas que
    `marcar_revisado` CALCULA desde `HEADERS` — leído por un SEGUNDO camino (gspread de
    solo lectura), no por el módulo que escribe. Si la migración las pusiera en otro
    sitio, la revisión caería en la columna de al lado sin un solo error (v323);
  · que lo confirmado desde un parte llegue a StageProgress con origen «log» y el ID del
    parte, y mueva `Activities.Progress` de su etapa — releído de la hoja;
  · que al repartir una nota de dos ascensores cada crédito caiga en SU obra;
  · que otro usuario no pueda revisar el parte, y que borrar las obras se lleve partes y
    créditos (v514, v516).
Los datos son de prueba («ZZ PRUEBA v523»), se crean aquí y se borran pase lo que pase.
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
from core import vocabulario as V                                 # noqa: E402
from core.num import col_letter                                   # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v523"
CREADOS = []
# ⚠️ La línea pendiente es una que SIN la cabecera sí se propondría («installed sills»);
# con «lift 3 sills», que no casa con nada, la comprobación pasaría en vacío (trampa nº1).
NOTA = ("lift 3 installed headers\nlift 1 installed sills\nShaft wiring done\n"
        "Pendings:\nlift 3 installed sills")


def _ro():
    """El SEGUNDO camino: gspread con permiso de SOLO LECTURA. Los helpers de la app
    migran cabeceras, o sea que escriben — una lectura hecha con ellos ya no es neutral."""
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


def obra(nombre):
    _f = SC.filas_de_etapas("Installation", NS, (), None)
    _s = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_f)
    _ok, pid = P.create_project(
        GRUPO, "%s %s" % (MARCA, nombre), ns=NS, tipo="Installation",
        fecha_inicio="2026-10-01", fecha_fin_est=_s["fecha_fin"].strftime("%Y-%m-%d"),
        activities=_s["activities"], creado_por=YO,
        stage_plan=P.plan_nuevo("Installation", (), None))
    if _ok:
        CREADOS.append(pid)
    return _ok, pid


def progreso(pid, orden):
    P._invalidate()
    respira(3)
    _a = next((a for a in (P.list_activities(pid) or [])
               if int(float(a.get("Order") or 0)) == orden), {})
    return float(_a.get("Progress") or 0)


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


RO = _ro()
_cab0 = (crudo(RO, DL.SHEET) or [[]])[0]
print("CABECERA DailyLogs ANTES · %d columnas: %s" % (len(_cab0), _cab0))
ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))

try:
    sec("1. Dos obras de prueba (dos ascensores de la misma torre)")
    ok1, P1 = obra("Lift 1")
    respira()
    ok3, P3 = obra("Lift 3")
    chk("creadas", ok1 and ok3, (P1, P3))
    if not (ok1 and ok3):
        raise SystemExit("sin obras no hay nada que ejercitar")
    respira()
    P._invalidate()
    PRJ1, PRJ3 = P.get_project(P1) or {}, P.get_project(P3) or {}
    chk("...las dos con plan sellado", bool(SP.plan_de_obra(PRJ1)) and bool(SP.plan_de_obra(PRJ3)))

    sec("2. El parte, escrito y releído de la hoja")
    respira()
    _ok, LID = DL.crear(P1, GRUPO, NOTA, YO)
    chk("se guarda", _ok, LID)
    respira()
    DL._invalidate()
    _p = [r for r in DL.partes(P1) if r.get("ID") == LID]
    chk("se relee por el LOTE", len(_p) == 1, len(_p))
    chk("...con el texto entero, saltos de línea incluidos",
        bool(_p) and _p[0].get("Text") == NOTA, _p[0].get("Text") if _p else None)
    chk("...y SIN revisar", bool(_p) and not DL.revisado(_p[0]))
    respira()
    _v = crudo(RO, DL.SHEET)
    _cab = _v[0] if _v else []
    print("   CABECERA DailyLogs DESPUÉS · %d columnas" % len(_cab))
    chk("⚠️ en la hoja REAL, `Reviewed` y `ReviewedBy` están donde las calcula el módulo "
        "(%s y %s)" % (col_letter(DL.HEADERS.index("Reviewed") + 1),
                       col_letter(DL.HEADERS.index("ReviewedBy") + 1)),
        _cab[:len(DL.HEADERS)] == DL.HEADERS, _cab)

    sec("3. Lo que la app propone, repartido por ascensor como lo asignaría el usuario")
    _asc = V.ascensores(NOTA)
    chk("detecta los dos ascensores y propone separar",
        _asc["separar"] and sorted(_asc["ascensores"]) == ["1", "3"], _asc["ascensores"])
    TROZOS = PP.reparto(NOTA, {"": P1, "1": P1, "3": P3})
    chk("cada obra recibe su trozo, y lo pendiente sigue pendiente en el de lift 3",
        TROZOS.get(P3, "").splitlines() == ["lift 3 installed headers", "Pending:",
                                            "lift 3 installed sills"]
        and TROZOS.get(P1, "").splitlines() == ["lift 1 installed sills", "Shaft wiring done"],
        TROZOS)
    respira()
    PR3 = PP.propuestas(TROZOS.get(P3, ""), SP.plan_de_obra(PRJ3), SP.acreditado(P3))
    respira()
    PR1 = PP.propuestas(TROZOS.get(P1, ""), SP.plan_de_obra(PRJ1), SP.acreditado(P1))
    _a3 = [(f["orden"], f["actividad"]) for f in PR3["actividades"]]
    _a1 = [(f["orden"], f["actividad"]) for f in PR1["actividades"]]
    chk("lift 3: propone «Install headers» y NO los sills pendientes",
        [a for _, a in _a3] == ["Install headers"], _a3)
    chk("lift 1: propone «Install sills» y la lista de «shaft wiring»",
        [a for _, a in _a1] == ["Install sills"] and len(PR1["etapas"]) == 1,
        (_a1, [e["termino"] for e in PR1["etapas"]]))

    sec("4. ⚠️ Se acredita SOLO lo «marcado», cada cosa en su obra")
    M3 = _a3
    M1 = _a1 + [(o["orden"], o["actividad"]) for o in PR1["etapas"][0]["opciones"][:2]]
    O7 = M3[0][0] if M3 else 0
    ANTES_7 = progreso(P3, O7)
    respira()
    _ok3, _m3 = SP.acreditar(P3, GRUPO, PRJ3, PP.creditos(M3, LID), quien=YO, origen=SP.PARTE)
    chk("lift 3 acreditado", _ok3, _m3)
    respira()
    _ok1, _m1 = SP.acreditar(P1, GRUPO, PRJ1, PP.creditos(M1, LID), quien=YO, origen=SP.PARTE)
    chk("lift 1 acreditado", _ok1, _m1)
    respira()
    SP._invalidate()
    _d3 = SP.de_parte(P3, LID)
    respira(3)
    _d1 = SP.de_parte(P1, LID)
    chk("`de_parte` lo encuentra releyendo: 1 en lift 3",
        [r.get("Activity") for r in _d3] == ["Install headers"], [r.get("Activity") for r in _d3])
    chk("...y %d en lift 1" % len(M1), sorted(r.get("Activity") for r in _d1)
        == sorted(a for _, a in M1), [r.get("Activity") for r in _d1])
    DESPUES_7 = progreso(P3, O7)
    chk("`Activities.Progress` de la etapa sube en lift 3 (%.1f → %.1f)" % (ANTES_7, DESPUES_7),
        DESPUES_7 > ANTES_7, (ANTES_7, DESPUES_7))
    respira()
    _sp = crudo(RO, SP.SHEET)
    _h = _sp[0] if _sp else []
    _filas = [dict(zip(_h, f)) for f in _sp[1:] if len(f) > 2 and f[2] in (P1, P3)]
    chk("por el SEGUNDO camino: %d filas, todas con origen «log» y el ID del parte"
        % len(_filas), len(_filas) == len(M1) + len(M3)
        and {r.get("Source") for r in _filas} == {"log"}
        and {r.get("Note") for r in _filas} == {LID}, [(r.get("Source"), r.get("Note")) for r in _filas])
    chk("...y ninguna cruzada de obra",
        {r.get("Activity") for r in _filas if r.get("ProjectID") == P3} == {"Install headers"},
        [(r.get("ProjectID"), r.get("Activity")) for r in _filas])

    sec("5. La revisión del parte")
    respira()
    _ok, _m = DL.marcar_revisado(LID, "otro_usuario")
    chk("otro usuario NO puede revisarlo", not _ok, _m)
    respira()
    _ok, _m = DL.marcar_revisado(LID, YO)
    chk("su autor sí", _ok, _m)
    respira()
    DL._invalidate()
    _p = [r for r in DL.partes(P1) if r.get("ID") == LID]
    chk("releído por el LOTE: revisado, y por quién",
        bool(_p) and DL.revisado(_p[0]) and _p[0].get("ReviewedBy") == YO,
        (_p[0].get("Reviewed"), _p[0].get("ReviewedBy")) if _p else None)
    respira()
    _v = crudo(RO, DL.SHEET)
    _f = next((f for f in _v[1:] if f and f[0] == LID), [])
    _iR, _iB = DL.HEADERS.index("Reviewed"), DL.HEADERS.index("ReviewedBy")
    chk("⚠️ por el SEGUNDO camino: la fecha en `Reviewed` y el autor en `ReviewedBy`, "
        "y `Created` intacto",
        len(_f) > _iB and len(_f[_iR]) == 19 and _f[_iB] == YO
        and _f[DL.HEADERS.index("Created")] != _f[_iR], _f)

    sec("6. Borrar las obras se lleva el parte y los créditos")
    for pid in (P1, P3):
        _okd, _m = P.delete_project(pid)
        chk("se borra %s" % pid, _okd, _m)
        if _okd and pid in CREADOS:
            CREADOS.remove(pid)
        respira()
    for h in (SP.SHEET, DL.SHEET):
        H.invalidar(h)
    respira(3)
    _r1 = [r for r in (H.registros(SP.SHEET) or []) if str(r.get("ProjectID", "")) in (P1, P3)]
    _r2 = [r for r in (H.registros(DL.SHEET) or []) if str(r.get("ProjectID", "")) in (P1, P3)]
    chk("...ni un crédito huérfano", not _r1, len(_r1))
    chk("...ni un parte huérfano", not _r2, len(_r2))

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
print("v523 HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
