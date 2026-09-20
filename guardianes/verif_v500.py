# -*- coding: utf-8 -*-
"""v500 · el fin previsto sale de la CADENA, no del ritmo (SPI).

Lo que protege:
  (a) las tres reglas del pronóstico — terminada / en curso / sin empezar —, que es donde
      está el dominio: lo que no se hizo el martes no se puede hacer el martes;
  (b) que haya UNA sola respuesta a «cuándo termina» (v361: dos definiciones del mismo
      número acaban discrepando en pantalla, y el día que lo hacen ya es tarde);
  (c) que los CUATRO consumidores —cartera, agrupaciones, radar y el detalle— lean la
      misma; si uno se queda con el SPI, dos pantallas dicen fechas distintas;
  (d) y que el PLAN (`calcular`) no se haya movido al compartir la resolución de
      dependencias.
Todo EJECUTANDO (importar no ejecuta, v378).
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import plan, projects as P                              # noqa: E402
from core.schedule import build_schedule, schedule_projection     # noqa: E402


def A(o, d, pred="", av=0, ir=None, fr=None):
    return {"orden": o, "duracion": d, "pred": pred, "avance": av,
            "ini_real": ir, "fin_real": fr}


def fin(acts, hoy):
    return plan.pronostico(acts, hoy)["total_dias"]


# ═════ 1 · las tres reglas del pronóstico ════════════════════════════════════
print("\n[1] cuándo termina de verdad: lo hecho, lo que queda y lo que ni empezó")
CAD = [A(1, 4), A(2, 4), A(3, 4)]
ck("sin avance y en el día 0, el pronóstico ES el plan", fin(CAD, 0), 12.0)
ck("⚠️ lo que no se hizo no se hace en el pasado: día 6 sin empezar = 6+12", fin(CAD, 6), 18.0)
ck("una en curso al 50% deja 2 d DESDE HOY, y la obra sigue en plazo",
   fin([A(1, 4, av=100, ir=0, fr=4), A(2, 4, av=50, ir=4), A(3, 4)], 6), 12.0)
ck("...y al 10%, la obra se va 1,6 d",
   round(fin([A(1, 4, av=100, ir=0, fr=4), A(2, 4, av=10, ir=4), A(3, 4)], 6), 1), 13.6)
ck("terminar ANTES adelanta la cadena entera",
   fin([A(1, 4, av=100, ir=0, fr=2), A(2, 4), A(3, 4)], 2), 10.0)
ck("una obra TERMINADA no se mueve aunque hoy sea mucho después",
   fin([A(1, 4, av=100, ir=0, fr=3), A(2, 4, av=100, ir=3, fr=7),
        A(3, 4, av=100, ir=7, fr=9)], 30), 9.0)
ck("sin actividades no revienta", fin([], 5), 0.0)

# ⚠️ EL caso que motiva la versión: manda la que nadie tocó, no el promedio.
_r = plan.pronostico([A(1, 4, av=100, ir=0, fr=4), A(2, 10, "-", av=0), A(3, 4, "1")], 6)
ck("manda la actividad que bloquea, y es ELLA la crítica",
   (_r["total_dias"], [o for o, v in _r["por_orden"].items() if v["critica"]]), (16.0, [2]))
# y el desfase sigue valiendo en el pronóstico, no solo en el plan
ck("el desfase también cuenta al pronosticar",
   fin([A(1, 4, av=100, ir=0, fr=4), A(2, 4), A(3, 4, "1+2")], 4), 10.0)

# ═════ 2 · UNA sola respuesta a «cuándo termina» (v361) ══════════════════════
print("\n[2] una sola definición del fin previsto")
_s = build_schedule(1, dt.date(2026, 9, 1), {}, custom_rows=[
    {"nombre": "A", "duracion": 5, "peso": 10, "orden": 1, "pred": ""},
    {"nombre": "B", "duracion": 5, "peso": 10, "orden": 2, "pred": ""}])
_p = schedule_projection(_s, [50, 0], 4)
ck("la proyección ya NO devuelve la fecha del SPI",
   ("fecha_proj" in _p or "proj_dias" in _p), False)
ck("...y sí la de la cadena", ("fecha_cadena" in _p and "dias_cadena" in _p), True)
ck("el SPI se CONSERVA (mide el ritmo, que es otra pregunta)", "spi" in _p, True)
_usos = []
for _f in sorted(os.listdir("core")) + ["../app.py"]:
    if not _f.endswith(".py"):
        continue
    _ruta = "core/" + _f if not _f.startswith("..") else "app.py"
    if "fecha_proj" in _fuente(_ruta) or "proj_dias" in _fuente(_ruta):
        _usos.append(_ruta)
ck("nadie en el repo lee ya la fecha del SPI", _usos, [])

# ⚠️ Y el GANTT la dibuja: `schedule_svg` la pintaba con la clave del SPI, así que al
# retirarla la proyección habría desaparecido del gráfico **sin dar ningún error** —
# lo cazó este barrido, no la lectura del código.
from core.schedule import real_scurve, schedule_svg               # noqa: E402
# ⚠️ La proyección solo se dibuja si hay curva REAL (así lo pide `schedule_svg`), así que
# se construye con la función de verdad en vez de inventarse la forma del dato (v135):
# sin ella el chequeo fallaría por su propia construcción y acusaría a un código sano.
_rc = real_scurve(_s, [50, 0], upto_day=4)
_sv = schedule_svg(_s, real_curve=_rc, proj=_p, today_day=4, animar=False)
ck("el Gantt sigue dibujando la proyección (la fecha de la cadena)",
   _p["fecha_cadena"].strftime("%d/%m") in _sv, True)
ck("...y sin <defs>/<marker>, que svglib tira del PDF (v39)",
   ("<marker" in _sv or "<defs" in _sv), False)

# ═════ 3 · los CUATRO consumidores leen la MISMA ═════════════════════════════
print("\n[3] cartera, agrupaciones, radar y detalle, con la misma fecha")
_tp, _tu = ast.parse(_fuente("core/projects.py")), ast.parse(_fuente("core/projects_ui.py"))


def _cuerpo(arbol, fn):
    """El CÓDIGO de la función, sin su docstring.

    ⚠️ Con el docstring dentro, un chequeo por presencia se aprueba solo: el mío decía
    «usa dias_cadena» y lo encontraba en la frase que yo mismo había escrito ahí, con el
    código leyendo la clave vieja (trampa nº2, la misma de v461 y v472).
    """
    f = next((n for n in ast.walk(arbol)
              if isinstance(n, ast.FunctionDef) and n.name == fn), None)
    if not f:
        return ""
    cuerpo = list(f.body)
    if (cuerpo and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)):
        cuerpo = cuerpo[1:]
    return "\n".join(ast.unparse(n) for n in cuerpo)


VIEJAS = ("dias_gap", "fecha_proj", "proj_dias")
for _arb, _fn, _nuevas in ((_tp, "_gaps_for", ("dias_cadena",)),
                           (_tp, "projections_by_group", ("fecha_cadena", "dias_cadena")),
                           (_tp, "grouping_projection", ("fecha_cadena",)),
                           (_tu, "_estado_section", ("fecha_cadena", "dias_cadena"))):
    _c = _cuerpo(_arb, _fn)
    # en las DOS direcciones: que lea la nueva Y que NO quede leyendo la del ritmo
    ck(f"{_fn} lee la fecha/retraso de la CADENA",
       all(k in _c for k in _nuevas), True)
    ck(f"...y ya no lee la del SPI", [k for k in VIEJAS if k in _c], [])

# ═════ 4 · una sola definición de las DEPENDENCIAS ═══════════════════════════
print("\n[4] el plan y el pronóstico resuelven las dependencias igual")
_tpl = ast.parse(_fuente("core/plan.py"))
for _fn in ("calcular", "pronostico"):
    _f = next(n for n in ast.walk(_tpl) if isinstance(n, ast.FunctionDef) and n.name == _fn)
    ck(f"{_fn} delega en _preparar", "_preparar(acts)" in ast.unparse(_f), True)
# ⚠️ y el PLAN no puede haberse movido con el refactor (si no, cambian TODAS las obras)
ck("el plan sigue dando lo de v499 (NS=6 y NS=12 con ripout)",
   [(build_schedule(n, dt.date(2026, 9, 1), {}, ripout=r)["total_dias"])
    for n, r in ((6, False), (6, True), (12, False), (12, True))], [29, 35, 41, 50])

# ═════ 5 · la mejora, EJECUTADA contra la obra real ══════════════════════════
print("\n[5] donde el SPI no decía nada, ahora hay fecha")
_s2 = build_schedule(1, dt.date(2026, 9, 1), {}, custom_rows=[
    {"nombre": "A", "duracion": 5, "peso": 10, "orden": 1, "pred": ""}])
_p2 = schedule_projection(_s2, [0], 6)      # avance 0 → el SPI era None (división por 0)
ck("con avance 0 el SPI no puede decir nada...", _p2["spi"], None)
ck("...y la cadena sí da fecha y retraso",
   (_p2["fecha_cadena"] is not None, _p2["dias_cadena"]), (True, 6.0))

_r3 = P.project_schedule("PRJ-0001")
if _r3 and _r3.get("proj"):
    _pr = _r3["proj"]
    ck("obra REAL: la cadena da fin previsto", _pr.get("fecha_cadena") is not None, True)
    ck("...y dice QUÉ actividades mandan", bool(_pr.get("criticas_cadena")), True)
else:
    print("  --   sin obra real que medir (no es un fallo, pero tampoco una garantía)")
    sys.exit(2)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
