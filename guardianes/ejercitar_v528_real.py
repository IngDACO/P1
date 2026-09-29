# -*- coding: utf-8 -*-
"""v528 contra la HOJA REAL (método v344): foto → ejercitar → verificar LEYENDO por un
SEGUNDO camino → restaurar → segunda foto.

⚠️ Lo que esto prueba y los tests de mesa NO:
  - que la API REAL devuelve las filas como las espera `hojas.frescas` (el registro `i` es
    la fila `i + 2`, con las vacías de en medio contando): se compara, en las tres hojas
    del guardado, contra `get_all_records` — si no cuadrara, se escribiría en otra fila;
  - cuántas llamadas hace DE VERDAD guardar una etapa (contadas en el cliente HTTP, cada
    intento): 1 lectura en lote + 1 escritura en lote (+ el append de la fila nueva y el
    del rastro de cambios), sin ninguna lectura hoja a hoja;
  - que lo que queda en `StageProgress`, `Activities` y `Projects` es lo esperado, leído
    con gspread de SOLO LECTURA (no por los helpers de la app, que migran cabeceras).
⚠️ NO toca `Login` ni la sesión única: el heartbeat se prueba en verif_v528, no aquí.
Datos de prueba («ZZ PRUEBA v528»), creados aquí y borrados pase lo que pase.
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

from core import auditoria                                        # noqa: E402
from core import clock                                            # noqa: E402
from core import columnas, valores                                # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import timeclock                                        # noqa: E402

GRUPO, YO, NS = "cliente1", "dacox", 6
MARCA = "ZZ PRUEBA v528"
CREADOS = []
LLAMADAS = []
_anotar = timeclock._anotar_llamada


def _cuenta(method, endpoint):
    LLAMADAS.append((str(method).upper(), str(endpoint)))
    return _anotar(method, endpoint)


timeclock._anotar_llamada = _cuenta


def _tipos(desde):
    """Las llamadas al libro del CLIENTE desde `desde`. ⚠️ Las del maestro (p. ej. `Groups`,
    que lee el reloj del grupo cuando su caché de 120 s caduca) se cuentan aparte: son de
    la sesión, no del guardado, y harían el recuento dependiente del momento."""
    out = {"lote-leer": 0, "lote-escribir": 0, "append": 0, "suelta-leer": 0, "otra": 0}
    _otras = [ep for m, ep in LLAMADAS[desde:] if SID not in ep]
    if _otras:
        print("   (llamadas a OTRO libro, no cuentan: %d)" % len(_otras))
    for m, ep in LLAMADAS[desde:]:
        if SID not in ep:
            continue
        if "values:batchGet" in ep:
            out["lote-leer"] += 1
        elif "values:batchUpdate" in ep:
            out["lote-escribir"] += 1
        elif ":append" in ep:
            out["append"] += 1
        elif m == "GET" and "/values/" in ep:
            out["suelta-leer"] += 1
        else:
            out["otra"] += 1
    return out


def _ro():
    c = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(c)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def ro_registros(libro, hoja):
    """Registros por el SEGUNDO camino (gspread de solo lectura), canonizados."""
    w = libro.worksheet(timeclock.titulo_real(hoja))
    return valores.canonizar(columnas.canonizar(
        w.get_all_records(numericise_ignore=["all"])), hoja)


def foto():
    for h in ("Projects", "Activities", SP.SHEET, auditoria.SHEET):
        H.invalidar(h)
    respira(2)
    return {"Projects": len(P.list_projects(GRUPO) or []),
            "Activities": len(H.registros("Activities") or []),
            "StageProgress": len(H.registros(SP.SHEET) or [])}


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
SID = timeclock.sheet_id_para("Projects", GRUPO)
chk("el libro del cliente no es el maestro (si no, el recuento no separa nada)",
    SID and SID != str(st.secrets["TIMECLOCK_SHEET_ID"]))
ANTES = foto()
print("ANTES · %s" % " · ".join("%s %d" % kv for kv in ANTES.items()))
HOY = clock.today(GRUPO).isoformat()

try:
    sec("1. ⚠️ La API real devuelve las filas como espera `hojas.frescas`")
    respira()
    _w = {SP.SHEET: SP._ws(), P.ACTIVITIES_SHEET: P._activities_ws()[0],
          P.PROJECTS_SHEET: P._projects_ws()[0]}
    _n0 = len(LLAMADAS)
    _lote = H.frescas(_w)
    chk("las tres hojas en UNA llamada", _tipos(_n0)["lote-leer"] == 1
        and sum(_tipos(_n0).values()) == 1, _tipos(_n0))
    respira()
    for _t, _ws in _w.items():
        _uno = valores.canonizar(columnas.canonizar(
            _ws.get_all_records(numericise_ignore=["all"])), _t)
        chk("⚠️ %s: %d registros, idénticos y en la misma fila que `get_all_records`"
            % (_t, len(_uno)), _lote.get(_t) == _uno,
            (len(_lote.get(_t) or []), len(_uno)))
        respira(2)

    sec("2. Una obra de prueba con plan sellado")
    respira()
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
    PLAN = SP.plan_de_obra(PRJ)
    O7 = next(i for i, e in enumerate(PLAN, start=1)
              if "Install headers" in [a["nombre"] for a in e["actividades"]])
    _esp = next(e for e in SP._sobre(PLAN, {(O7, "Install headers"): 100.0})
                if e["orden"] == O7)["pct"]
    respira()
    _aud0 = len([r for r in ro_registros(RO, auditoria.SHEET) if r.get("EntityID") == PID])

    sec("3. ⚠️ Guardar: cuántas llamadas, cuánto tarda y qué queda")
    respira()
    _n0 = len(LLAMADAS)
    _t0 = time.perf_counter()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": O7, "actividad": "Install headers",
                                             "pct": 100, "nota": ""}], quien=YO)
    _dt = time.perf_counter() - _t0
    _c = _tipos(_n0)
    print("   llamadas: %s · %.1f s" % (_c, _dt))
    chk("se acredita", _ok, _m)
    chk("⚠️ 1 lectura en lote y 1 escritura en lote", _c["lote-leer"] == 1
        and _c["lote-escribir"] == 1, _c)
    chk("⚠️ ...y NINGUNA lectura hoja a hoja (antes: 4)", _c["suelta-leer"] == 0, _c)
    chk("...más 2 append: la fila nueva y el rastro de cambios (antes ~9 llamadas en total)",
        _c["append"] == 2 and sum(_c.values()) == 4, _c)
    respira()
    _sp = [r for r in ro_registros(RO, SP.SHEET) if r.get("ProjectID") == PID]
    chk("segundo camino · StageProgress: una fila, al 100 y con el día de hoy",
        len(_sp) == 1 and float(_sp[0].get("Pct") or 0) == 100.0
        and _sp[0].get("WorkDate") == HOY, _sp)
    respira(3)
    _acts = [r for r in ro_registros(RO, "Activities") if r.get("ProjectID") == PID]
    _a7 = next((a for a in _acts if int(float(a.get("Order") or 0)) == O7), {})
    chk("segundo camino · Activities: la etapa en %.1f%% y empezada hoy" % _esp,
        abs(float(_a7.get("Progress") or -1) - _esp) < 1e-9
        and _a7.get("ActualStartDate") == HOY, _a7)
    respira(3)
    _p = next((r for r in ro_registros(RO, "Projects") if r.get("ID") == PID), {})
    _av = P.compute_avance(_acts)
    chk("⚠️ segundo camino · Projects: el avance es el de Activities (%.1f) y «In progress»"
        % _av, abs(float(_p.get("Progress") or -1) - _av) < 1e-9
        and _p.get("Status") == "In progress", (_p.get("Progress"), _p.get("Status")))

    sec("4. Deshacer: la MISMA fila, sin append de StageProgress")
    respira()
    _n0 = len(LLAMADAS)
    _t0 = time.perf_counter()
    _ok, _m = SP.acreditar(PID, GRUPO, PRJ, [{"etapa": O7, "actividad": "Install headers",
                                             "pct": 0, "nota": ""}], quien=YO)
    _dt = time.perf_counter() - _t0
    _c = _tipos(_n0)
    print("   llamadas: %s · %.1f s" % (_c, _dt))
    chk("se deshace", _ok, _m)
    chk("⚠️ 1 lectura + 1 escritura en lote, y solo el append del rastro",
        _c["lote-leer"] == 1 and _c["lote-escribir"] == 1 and _c["append"] == 1
        and _c["suelta-leer"] == 0, _c)
    respira()
    _sp = [r for r in ro_registros(RO, SP.SHEET) if r.get("ProjectID") == PID]
    chk("segundo camino · la MISMA fila, ahora a 0",
        len(_sp) == 1 and float(_sp[0].get("Pct") or -1) == 0.0, _sp)
    respira(3)
    _p = next((r for r in ro_registros(RO, "Projects") if r.get("ID") == PID), {})
    chk("segundo camino · la obra vuelve a 0 y «Planned»",
        float(_p.get("Progress") or -1) == 0.0 and _p.get("Status") == "Planned",
        (_p.get("Progress"), _p.get("Status")))
    respira(3)
    _aud = [r for r in ro_registros(RO, auditoria.SHEET) if r.get("EntityID") == PID]
    chk("el rastro de cambios anotó los DOS guardados (decisión: se mantiene)",
        len(_aud) - _aud0 == 2, (len(_aud), _aud0))

    sec("5. Borrar la obra se lo lleva todo")
    _okd, _m = P.delete_project(PID)
    chk("se borra %s" % PID, _okd, _m)
    if _okd and PID in CREADOS:
        CREADOS.remove(PID)
finally:
    limpia()
    timeclock._anotar_llamada = _anotar

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
print("v528 HOJA REAL — TODO OK (%d comprobaciones)" % n_ok)
