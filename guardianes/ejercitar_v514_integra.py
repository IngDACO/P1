# -*- coding: utf-8 -*-
"""v512-v514 INTEGRADOS con todo lo demás, contra la HOJA REAL.

  catálogo → cotización → aceptar → obra CON PLAN DE ETAPAS
     → acreditar actividades reales
        → avance ponderado → reclamación → PDF
        → línea base (v501) → ruta crítica (v499/v500)
        → expediente de entrega (v506)

## Por qué existe

`ejercitar_v512_real` comprueba que la obra nazca con sus etapas y `ejercitar_v514_real`
que acreditar mueva el avance. Ninguno comprueba lo que de verdad importa: que el nuevo
modelo de avance **siga alimentando el dinero**. El avance es lo que se reclama
(v507/v510), así que cambiarle la raíz sin recorrer la cadena entera es exactamente el
hueco que v511 vino a cerrar.

⚠️ Lo que NO prueba: la pantalla. Eso solo se ve ejecutándola (nº30).
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
from core import catalogo as CAT                                  # noqa: E402
from core import claims as CL                                     # noqa: E402
from core import projects as P                                    # noqa: E402
from core import quotes as Q                                      # noqa: E402
from core import stage_progress as SP                             # noqa: E402

GRUPO = "cliente1"
MARCA = "PRUEBA v514i"
NS = 8

fallos, creados = [], {"cat": [], "cot": [], "prj": []}


def ck(q, real, esp):
    if real == esp:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def cerca(q, real, esp, tol=0.5):
    try:
        bien = abs(float(real) - float(esp)) <= tol
    except Exception:
        bien = False
    if bien:
        print("  ok   %s" % q)
    else:
        fallos.append(q)
        print("  *** FALLO  %s  -> %r != %r" % (q, real, esp))


def pausa(s=14):
    print("   (pausa %ds — techo de 60 lecturas/min, v511)" % s)
    time.sleep(s)


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
        out = {}
        for h in ("Projects", "Quotes", "Catalogue", "Claims", "StageProgress",
                  "Activities"):
            v = lb.worksheet(h).get_all_values() if h in hay else [[]]
            out[h] = len([f for f in v[1:] if f]) if len(v) > 1 else 0
        return out
    except Exception as e:
        raise SystemExit("no se pudo leer: %r (la foto seria falsa)" % (e,))


ANTES = foto()
print("ANTES · " + " · ".join("%s %d" % (k, v) for k, v in ANTES.items()))

try:
    # ── 1) catálogo y cotización ─────────────────────────────────────────────
    print("\n1) catalogo y cotizacion")
    for nombre, costo in (("mobilisation", 2000), ("landing doors", 900),
                          ("rails", 3400)):
        ok_, cid = CAT.crear(GRUPO, "%s %s" % (MARCA, nombre), CAT.PRODUCTO,
                             costo_unit=costo, descripcion=nombre, creado_por="Bobo")
        if ok_:
            creados["cat"].append(cid)
    CAT._invalidate()
    _items = [i for i in (CAT.list_items(GRUPO) or []) if MARCA in str(i.get("Name", ""))]
    ck("los 3 articulos estan", len(_items), 3)
    if len(_items) != 3:
        raise SystemExit("sin catalogo completo no se sigue (precondicion rota)")
    _lineas = [Q.linea_de(i, 1, margen_pct=20.0) for i in _items]
    _tot = Q.totales(_lineas, 10.0)
    okq, cot = Q.crear(GRUPO, "", "%s cliente" % MARCA, _lineas, impuesto_pct=10.0,
                       creado_por="Bobo")
    ck("la cotizacion se guarda", okq, True)
    if not okq:
        raise SystemExit(str(cot))
    creados["cot"].append(cot)

    # ── 2) aceptar: ⚠️ la obra tiene que nacer CON plan de etapas ────────────
    print("\n2) aceptar la cotizacion")
    pausa()
    oka, pid = Q.aceptar_y_crear_proyecto(cot, nombre="%s obra" % MARCA,
                                          tipo="Installation", ns=NS,
                                          creado_por="Bobo")
    ck("se crea la obra", oka, True)
    if not oka:
        raise SystemExit(str(pid))
    creados["prj"].append(pid)
    P._invalidate()
    _prj = P.get_project(pid) or {}
    _acts = P.list_activities(pid) or []
    ck("⚠️ nace con las 14 etapas del catalogo", len(_acts), 14)
    # ⚠️ ESTO es lo que une los dos caminos: una obra creada desde COTIZACION tiene que
    # poder acreditar actividades igual que una creada a mano. Si `aceptar` no sellara
    # el plan, la pantalla nueva no aparecería y nadie se enteraría hasta usarla.
    ck("⚠️ y con su plan de etapas sellado", bool(P.plan_etapas(_prj)), True)
    ck("...con la version del catalogo de hoy",
       P.plan_etapas(_prj).get("version"), __import__("core.stages",
                                                      fromlist=["VERSION"]).VERSION)
    _c, _cid_q = CL.contrato(pid)
    ck("el contrato sale de esta cotizacion", _cid_q, cot)
    cerca("...y vale el subtotal", _c, round(_tot["subtotal"], 2))

    # ── 3) acreditar actividades REALES ──────────────────────────────────────
    print("\n3) se acreditan actividades (no se teclea el avance)")
    pausa()
    _ok, _msg = SP.acreditar(
        pid, GRUPO, _prj,
        [{"etapa": 4, "actividad": "Install first 2 rings", "pct": 100},
         {"etapa": 4, "actividad": "Install first 2 car rails", "pct": 100},
         {"etapa": 4, "actividad": "Install yoke/base, level it", "pct": 100},
         {"etapa": 6, "actividad": "Install rings to top", "pct": 100},
         {"etapa": 6, "actividad": "Install car rails to top", "pct": 100}],
        quien="Bobo")
    print("   -> %s" % _msg)
    ck("se acreditan", _ok, True)
    pausa()
    SP._invalidate()
    P._invalidate()
    _det = {e["orden"]: e for e in SP.detalle(pid, P.get_project(pid) or {})}
    # ⚠️ 15,6 y no 15. La etapa 4 lleva el espejo como CONDICIONAL y esta obra no lo
    # tiene, así que sus actividades aplicables suman 96 de peso, no 100: 15/96 = 15,6.
    # Mi primera cifra esperada fue 15,0 — hecha a mano ignorando la renormalización que
    # yo mismo construí en v512. El código tenía razón y el test estaba mal; mirar el
    # código acusado antes de «arreglarlo» (v385) es lo que evitó parchear algo correcto.
    cerca("etapa 4 al 15,6% (5+5+5 sobre 96, sin el espejo)", _det[4]["pct"], 15.6)
    # La etapa 6 no tiene condicionales, así que sí suma 100 y sale redondo.
    cerca("etapa 6 al 40% (22+18 sobre 100)", _det[6]["pct"], 40.0)
    _prj = P.get_project(pid) or {}
    _av = float(_prj.get("Progress") or 0)
    # 11% de la obra × 15% + 13% × 40% = 1,65 + 5,2 = 6,85
    cerca("⚠️ el avance de la OBRA es el ponderado, no una media", _av, 6.85, tol=0.4)

    # ── 4) ⚠️ el dinero se mueve con ese avance ──────────────────────────────
    print("\n4) la reclamacion sobre el avance acreditado")
    pausa()
    CL._invalidate()
    _d = CL.calcular(pid, GRUPO, None, _prj)
    print("   valor %.2f · avance %.2f%% · bruto %.2f · neto %.2f"
          % (_d["valor"], _d["pct"], _d["bruto"], _d["neto"]))
    ck("hay contrato contra el que reclamar", _d["hay_contrato"], True)
    cerca("⚠️ la reclamacion usa el avance ponderado", _d["pct"], _av, tol=0.05)
    cerca("...y el bruto sale de ahi", _d["bruto"],
          round(_d["valor"] * _av / 100.0, 2), tol=1.0)
    ck("⚠️ y NO es cero: el modelo nuevo alimenta el dinero", _d["bruto"] > 0, True)
    okr, msgr = CL.crear_reclamacion(pid, GRUPO, None, "", "integra", "Bobo", _prj)
    ck("la reclamacion se emite", okr, True)
    print("   -> %s" % msgr)

    # ── 5) lo que ya existia sigue funcionando sobre 14 etapas ───────────────
    print("\n5) lo de antes, sobre el modelo nuevo")
    pausa()
    # ⚠️ Por `P.fijar_baseline`, que es lo que llama la pantalla. La primera versión
    # llamaba a `baseline.fijar(pid, quien)` y reventaba: esa función es PURA y toma
    # `(baseline_actual, cronograma, quien)`, no el id. El reventón era mío, no un fallo
    # del código — y un ejercicio que llama a una API que no existe no prueba nada.
    okb, msgb = P.fijar_baseline(pid, "Bobo")
    print("   linea base -> %s · %s" % (okb, str(msgb)[:60]))
    ck("la linea base se fija sobre las 14 etapas", okb, True)
    # ⚠️ `project_schedule` devuelve {sched, real, today_day, …}: las actividades van
    # DENTRO de `sched`. Mi primera versión leía `.get("activities")` en la raíz y daba
    # 0 — parecía que el cronograma no se reconstruía. Tercer error del mismo tipo en
    # este ejercicio: escribir contra el recuerdo de la API en vez de leerla (v499).
    _ps = P.project_schedule(pid) or {}
    _sch = (_ps.get("sched") or {})
    ck("el cronograma se reconstruye con 14 actividades",
       len(_sch.get("activities", [])), 14)
    ck("...y alguna es critica (la cadena de v499/v500 opera)",
       any(a.get("critica") for a in _sch.get("activities", [])), True)
    # ⚠️ Y la curva S REAL tiene que reflejar lo acreditado: si diera 0 con la obra al
    # 7%, el avance por actividad no estaria llegando al earned value.
    # ⚠️ `real` es una lista de PARES (dia, valor), no de numeros: `max()` sobre ella
    # devuelve una tupla. Cuarto error del mismo tipo en este ejercicio — suponer la
    # forma de un dato en vez de leerla. Se toma el valor de cada par.
    _real = list(_ps.get("real") or [])
    _valores = [v for _d, v in _real] if (_real and isinstance(_real[0], (tuple, list))
                                          and len(_real[0]) == 2) else _real
    ck("la curva S real refleja lo acreditado", max([0] + list(_valores)) > 0, True)
    try:
        from core import handover as HO
        from core import handover_ui as HOU
        _filas = HO.estado(HOU.contexto(pid, GRUPO, P.get_project(pid) or {}))
        ck("el expediente de entrega sigue dando 13 items", len(_filas), 13)
    except Exception as e:
        fallos.append("el expediente revento")
        print("  *** FALLO  el expediente revento -> %r" % (e,))

finally:
    # ── 6) borrar TODO lo de la prueba ───────────────────────────────────────
    print("\n6) limpieza")
    for pid_ in creados["prj"]:
        try:
            print("   obra %s -> %s" % (pid_, P.delete_project(pid_)[1]))
        except Exception as e:
            print("   *** obra %s: %r" % (pid_, e))
            fallos.append("quedo la obra %s" % pid_)

    def _borrar(hoja, pred, etq):
        try:
            lb = _libro(escribir=True)
            if hoja not in {w.title for w in lb.worksheets()}:
                return
            ws = lb.worksheet(hoja)
            v = ws.get_all_values()
            n = [i for i, f in enumerate(v[1:], start=2) if f and pred(f, v[0])]
            for i in sorted(n, reverse=True):
                ws.delete_rows(i)
            print("   %-14s %d fila(s) %s" % (hoja, len(n), etq))
        except Exception as e:
            print("   *** %s: %r" % (hoja, e))
            fallos.append("limpieza de %s" % hoja)

    def _col(f, cab, k):
        try:
            return f[cab.index(k)]
        except Exception:
            return ""

    _pids = set(creados["prj"])
    _borrar("Claims", lambda f, c: _col(f, c, "ProjectID") in _pids, "(reclamaciones)")
    _borrar("StageProgress", lambda f, c: _col(f, c, "ProjectID") in _pids, "(creditos)")
    _borrar("Quotes", lambda f, c: f[0] in set(creados["cot"]), "(cotizaciones)")
    _borrar("Catalogue", lambda f, c: f[0] in set(creados["cat"]), "(catalogo)")
    for m in (CAT, Q, P, CL, SP):
        try:
            m._invalidate()
        except Exception:
            pass

time.sleep(10)
DESPUES = foto()
print("\nDESPUES · " + " · ".join("%s %d" % (k, v) for k, v in DESPUES.items()))
ck("⚠️ la hoja quedo EXACTAMENTE como estaba", DESPUES, ANTES)

print("\n" + "=" * 70)
print("INTEGRACION v512-v514, HOJA REAL — " + ("TODO OK" if not fallos else "HAY FALLOS"))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
