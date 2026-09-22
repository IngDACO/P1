# -*- coding: utf-8 -*-
"""v514 contra la HOJA REAL (método v344): acreditar actividades de verdad.

  foto → crear una obra con plan → acreditar tres actividades → leer de vuelta el
  crédito Y el avance de la etapa en `Activities` → comprobar la obra entera →
  desmarcar una → borrar la obra → segunda foto

⚠️ Lo que SÍ prueba y ningún test puede: que la hoja `StageProgress` se cree sola, que
el crédito se lea de vuelta a través del LOTE de `hojas` (el fallo de v461/v507, que se
escribe bien y se lee vacío para siempre sin un solo error), y que el avance recalculado
llegue de verdad a `Activities.Progress` — que es lo que leen la curva S, el SPI y la
reclamación que se cobra.

⚠️ Lo que NO prueba: la pantalla. Eso solo se ve ejecutándola; aquí se llama a
`acreditar` con lo mismo que le pasa la pantalla (nº30).
"""
import os
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}
import gspread                                                    # noqa: E402
from datetime import date                                         # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stage_progress as SP                             # noqa: E402

GRUPO = "cliente1"
MARCA = "PRUEBA v514"
NS = 8

fallos, creados = [], []


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def cerca(q, real, esp, tol=0.15):
    try:
        bien = abs(float(real) - float(esp)) <= tol
    except Exception:
        bien = False
    if bien:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def _libro(escribir=False):
    sc = ["https://www.googleapis.com/auth/spreadsheets"] if escribir else \
         ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    cr = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]),
                                               scopes=sc)
    gc = gspread.authorize(cr)
    lib = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])
    grp = lib.worksheet("Groups").get_all_values()
    sid = [f[grp[0].index("SheetID")] for f in grp[1:] if f and f[0] == GRUPO][0]
    return gc.open_by_key(sid)


def foto():
    """⚠️ Si no se puede leer se ABORTA: una foto vacía aprueba cualquier limpieza."""
    try:
        lb = _libro()
        hay = {w.title for w in lb.worksheets()}
        pr = lb.worksheet("Projects").get_all_values()
        sp = (lb.worksheet(SP.SHEET).get_all_values() if SP.SHEET in hay else [[]])
    except Exception as e:
        raise SystemExit("no se pudo leer: %r (la foto seria falsa)" % (e,))
    return ([f[0] for f in pr[1:] if f and f[0]],
            len([f for f in sp[1:] if f]) if len(sp) > 1 else 0,
            SP.SHEET in hay)


ids0, ncred0, existia = foto()
print("ANTES · %d obras · %s %s · %d creditos"
      % (len(ids0), SP.SHEET, "existe" if existia else "NO existe aun", ncred0))

try:
    # ── 1) una obra con plan ─────────────────────────────────────────────────
    print("\n1) obra de instalacion con plan de etapas")
    _filas = SC.filas_de_etapas("Installation", NS, ())
    _sch = SC.build_schedule(NS, date(2026, 10, 1), {}, custom_rows=_filas)
    ok_, pid = P.create_project(GRUPO, "%s obra" % MARCA, ns=NS, tipo="Installation",
                                fecha_inicio="2026-10-01",
                                fecha_fin_est=_sch["fecha_fin"].strftime("%Y-%m-%d"),
                                activities=_sch["activities"], creado_por="Bobo",
                                stage_plan=P.plan_nuevo("Installation", ()))
    ck("se crea", ok_, True)
    if not ok_:
        raise SystemExit("sin obra no hay nada que ejercitar: %s" % pid)
    creados.append(pid)
    P._invalidate()
    _prj = P.get_project(pid) or {}
    ck("nace en 0%", float(_prj.get("Progress") or 0), 0.0)

    # ── 2) acreditar de verdad ───────────────────────────────────────────────
    print("\n2) se acreditan tres actividades de la etapa 6")
    time.sleep(12)
    _ok, _msg = SP.acreditar(
        pid, GRUPO, _prj,
        [{"etapa": 6, "actividad": "Install motor bedplate", "pct": 100},
         {"etapa": 6, "actividad": "Install single bedplate", "pct": 100},
         {"etapa": 6, "actividad": "Seal machine room / shaft penetrations", "pct": 100}],
        quien="Bobo")
    print("   -> %s" % _msg)
    ck("se acreditan", _ok, True)

    # ⚠️ Leído de vuelta POR EL LOTE, que es como lo lee la app. Si la hoja no estuviera
    # en `HOJAS_LECTURA` esto daría 0 con las filas escritas — el fallo de v461/v507.
    print("\n3) leido de vuelta desde la hoja")
    time.sleep(12)
    SP._invalidate()
    _cr = SP.creditos(pid)
    ck("⚠️ los tres creditos se leen (el lote los ve)", len(_cr), 3)
    ck("...con su % al 100",
       sorted({str(r.get("Pct")) for r in _cr}), ["100.0"])
    _det = {e["orden"]: e for e in SP.detalle(pid, _prj)}
    # 17 + 13 + 12 = 42% de la etapa 6
    cerca("⚠️ la etapa 6 va al 42% (17+13+12)", _det[6]["pct"], 42.0)
    ck("...y las demas siguen a cero",
       {round(e["pct"], 1) for o, e in _det.items() if o != 6}, {0.0})

    # ── 4) el numero que lee todo lo demas ───────────────────────────────────
    print("\n4) el avance llego a Activities")
    time.sleep(12)
    P._invalidate()
    _acts = P.list_activities(pid) or []
    _a6 = next((a for a in _acts if int(float(a.get("Order") or 0)) == 6), {})
    cerca("⚠️ la fila 6 de Activities dice 42%", float(_a6.get("Progress") or 0), 42.0)
    ck("...y tiene fecha de inicio real puesta sola (v162)",
       bool(str(_a6.get("ActualStartDate", "")).strip()), True)
    _prj = P.get_project(pid) or {}
    # La etapa 6 pesa 13 de 100 → 42% de ella ≈ 5,5% de la obra.
    cerca("⚠️ y el avance de la OBRA subio en consecuencia",
          float(_prj.get("Progress") or 0), 5.5, tol=0.6)

    # ── 5) desmarcar ─────────────────────────────────────────────────────────
    print("\n5) se desmarca una")
    time.sleep(12)
    _ok2, _m2 = SP.borrar(pid, 6, "Install single bedplate", GRUPO, _prj, quien="Bobo")
    ck("se desmarca", _ok2, True)
    SP._invalidate()
    P._invalidate()
    _det2 = {e["orden"]: e for e in SP.detalle(pid, P.get_project(pid) or {})}
    cerca("⚠️ la etapa baja a 29% (42 − 13)", _det2[6]["pct"], 29.0)
    ck("⚠️ y la fila NO desaparece: queda el rastro a 0",
       len(SP.creditos(pid)), 3)

finally:
    print("\n6) se borra la obra de prueba")
    for pid_ in creados:
        try:
            print("   %s -> %s" % (pid_, P.delete_project(pid_)[1]))
        except Exception as e:
            print("   *** no se pudo borrar %s: %r" % (pid_, e))
            fallos.append("quedo basura: %s" % pid_)
    # ⚠️ v514: los créditos los borra `delete_project`, no este guion. La primera
    # versión los limpiaba a mano aquí — y ese apaño TAPABA el fallo: sin él, borrar una
    # obra dejaba filas huérfanas apuntando a algo que ya no existe. Se quitó a
    # propósito para que la foto final lo compruebe de verdad.
    try:
        ws = _libro().worksheet(SP.SHEET)
        _vivos = [f for f in ws.get_all_values()[1:]
                  if f and len(f) > 2 and f[2] in creados]
        ck("⚠️ delete_project se llevo los creditos", len(_vivos), 0)
    except Exception as e:
        print("   *** no se pudo comprobar: %r" % e)
    SP._invalidate()
    P._invalidate()

time.sleep(10)
ids9, ncred9, _ = foto()
print("\nDESPUES · %d obras · %d creditos" % (len(ids9), ncred9))
ck("la cartera quedo como estaba", ids9, ids0)
ck("...y no quedo ningun credito de prueba", ncred9, ncred0)

print("\n" + "=" * 70)
print("AVANCE POR ACTIVIDAD, HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
