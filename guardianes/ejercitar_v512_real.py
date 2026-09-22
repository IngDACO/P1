# -*- coding: utf-8 -*-
"""v512 contra la HOJA REAL (método v344): el alta desde el catálogo de etapas.

  foto → crear una obra de CADA tipo → leer de vuelta sus actividades y su plan
  sellado → borrarlas → segunda foto

⚠️ Lo que este ejercicio SÍ prueba y ningún test puede: que la columna `StagePlanJSON`
se cree sola al final de una hoja que ya tiene filas, que las 14/18/4 actividades se
escriban y se lean de vuelta con sus pesos, y que una obra de tipo «Delivery» siga
naciendo con UNA sola — o sea que el cambio no se derramó a donde no debía.

⚠️ Lo que NO prueba: la pantalla. El alta la pinta Streamlit y eso solo se ve
ejecutándola; aquí se llama a `create_project` con lo mismo que le pasa la pantalla.
Decirlo importa: un ejercicio que aparenta probar más de lo que prueba es peor que uno
corto (nº30).
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
from google.oauth2.service_account import Credentials             # noqa: E402
from core import projects as P                                    # noqa: E402
from core import schedule as SC                                   # noqa: E402
from core import stages as S                                      # noqa: E402

GRUPO = "cliente1"
MARCA = "PRUEBA v512"
TRAC = "Rip out mechanical components - traction"
NS = 8

fallos, creados = [], []


def ck(q, real, esp):
    if real == esp:
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
    """⚠️ Si no se puede leer se ABORTA: una foto vacía aprueba cualquier cosa."""
    try:
        lb = _libro()
        pr = lb.worksheet("Projects").get_all_values()
        ac = lb.worksheet("Activities").get_all_values()
    except Exception as e:
        raise SystemExit("no se pudo leer: %r (la foto seria falsa)" % (e,))
    if not pr or not pr[0]:
        raise SystemExit("Projects no tiene cabecera: la foto no vale")
    return pr[0], [f[0] for f in pr[1:] if f and f[0]], len([f for f in ac[1:] if f])


cab0, ids0, nact0 = foto()
print("ANTES · Projects %d columnas · %d obras · Activities %d filas"
      % (len(cab0), len(ids0), nact0))
ck("«StagePlanJSON» se creo sola AL FINAL (v363)", cab0[-1] if "StagePlanJSON" in cab0
   else "(no esta)", "StagePlanJSON")

CASOS = [
    # (tipo, condicionales, etapas esperadas, pista de la primera etapa)
    ("Installation", (), 14, S.PISTA_INSTALL),
    ("Ripout + Installation", (TRAC,), 18, S.PISTA_RIPOUT),
    ("Ripout", (TRAC,), 4, S.PISTA_RIPOUT),
]

try:
    for tipo, cond, n_esp, pista1 in CASOS:
        print("\n── %s ──" % tipo)
        time.sleep(12)          # ⚠️ 60 lecturas/min: ver la lección de v511
        _filas = SC.filas_de_etapas(tipo, NS, cond)
        _sch = SC.build_schedule(NS, __import__("datetime").date(2026, 10, 1), {},
                                 custom_rows=_filas)
        ok_, pid = P.create_project(
            GRUPO, "%s %s" % (MARCA, tipo), ns=NS, tipo=tipo,
            fecha_inicio="2026-10-01",
            fecha_fin_est=_sch["fecha_fin"].strftime("%Y-%m-%d"),
            activities=_sch["activities"], creado_por="Bobo",
            stage_plan=P.plan_nuevo(tipo, cond))
        ck("se crea la obra", ok_, True)
        if not ok_:
            print("   -> %s" % pid)
            continue
        creados.append(pid)
        P._invalidate()
        _prj = P.get_project(pid) or {}
        _acts = P.list_activities(pid) or []
        print("   %s · %d actividades · fin %s"
              % (pid, len(_acts), _prj.get("EndDateEst", "?")))
        ck("...con %d etapas" % n_esp, len(_acts), n_esp)
        # ⚠️ Los NOMBRES, no solo el numero: 18 actividades equivocadas contarian igual.
        ck("...y son las del catalogo",
           [str(a.get("Name", "")) for a in _acts],
           [f["nombre"] for f in _filas])
        ck("la primera etapa es de la pista que toca",
           str(_acts[0].get("Name", "")) if _acts else "(sin actividades)",
           _filas[0]["nombre"])
        _pl = P.plan_etapas(_prj)
        ck("el plan quedo sellado en la obra", _pl.get("version"), S.VERSION)
        ck("...con su tipo", _pl.get("tipo"), tipo)
        ck("...y sus condicionales", _pl.get("condicionales"), sorted(cond))
        _pesos = round(sum(float(a.get("Weight") or 0) for a in _acts), 1)
        ck("los pesos suman 100 en la hoja", _pesos, 100.0)
        ck("la obra nace en 0%", float(_prj.get("Progress") or 0), 0.0)

    # ⚠️ Y que el cambio NO se derramo: un delivery sigue con UNA actividad.
    print("\n── Delivery (no debe cambiar) ──")
    time.sleep(12)
    ok_, pid = P.create_project(GRUPO, "%s Delivery" % MARCA, tipo="Delivery",
                                fecha_inicio="2026-10-01", fecha_fin_est="2026-10-03",
                                activities=[{"nombre": "Execution", "duracion": 3,
                                             "peso": 1}],
                                creado_por="Bobo", stage_plan="")
    ck("se crea", ok_, True)
    if ok_:
        creados.append(pid)
        P._invalidate()
        _acts = P.list_activities(pid) or []
        ck("⚠️ sigue naciendo con UNA sola actividad", len(_acts), 1)
        ck("...y SIN plan de etapas", P.plan_etapas(P.get_project(pid) or {}), {})

finally:
    print("\n── se borran las obras de prueba ──")
    for pid in creados:
        try:
            _ok, _m = P.delete_project(pid)
            print("   %s -> %s" % (pid, _m))
        except Exception as e:
            print("   *** no se pudo borrar %s: %r" % (pid, e))
            fallos.append("quedo basura: %s" % pid)
    P._invalidate()

time.sleep(10)
cab9, ids9, nact9 = foto()
print("\nDESPUES · %d obras · Activities %d filas" % (len(ids9), nact9))
ck("no quedo ninguna obra de prueba", ids9, ids0)
ck("...ni ninguna actividad suelta", nact9, nact0)

print("\n" + "=" * 70)
print("CATALOGO DE ETAPAS, HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
