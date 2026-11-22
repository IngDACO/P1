# -*- coding: utf-8 -*-
"""v698 · D1 del ciclo 6 (decisión del usuario, 23/11): «los días laborales de lunes a viernes cuentan siempre menos en
pausa; sábado y domingo no suman aunque estén en el tablero (si se trabaja, es para recuperar o adelantar). Suma en
progreso pero no en tiempo.» → `core/calendario.py` y el motor del plan con él. Y lo visto con la sesión de campo:
el aviso flotante con «reducir movimiento» desaparece de golpe a los 9 s, y sin la doble puntuación en el aviso de H12.

Nada sale a la red ni escribe: sustitutos y AppTest.
"""
import ast
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
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


from core.calendario import Calendario, pausas_de, laborable                 # noqa: E402
from core import schedule as S, projects as P, clock, theme                  # noqa: E402

D = date
# ═════════════════════════════════════════════════════════════════
print("1. El calendario: de lunes a viernes, fuera de pausa")
c = Calendario(D(2026, 11, 22), hoy=D(2026, 11, 23))           # C6: empieza en DOMINGO
chk("el día 0 es el lunes 23/11 (el domingo no cuenta)", c.fecha(0) == D(2026, 11, 23), c.fecha(0))
chk("el día 5 es el lunes 30/11 (el fin de semana no cuenta)", c.fecha(5) == D(2026, 11, 30), c.fecha(5))
chk("NS 8 (33 días de plan) termina el miércoles 06/01/2027 (era el 25/12)", c.fin(33) == D(2027, 1, 6), c.fin(33))
chk("el sábado 28/11 y el lunes 30/11 son el MISMO día del plan (el sábado suma avance, no tiempo)",
    c.dia(D(2026, 11, 28)) == c.dia(D(2026, 11, 30)) == 5, (c.dia(D(2026, 11, 28)), c.dia(D(2026, 11, 30))))
chk("antes del inicio, negativo (el viernes 20/11 → −1)", c.dia(D(2026, 11, 20)) == -1, c.dia(D(2026, 11, 20)))
chk("laborable: viernes sí, sábado no", laborable(D(2026, 11, 27)) and not laborable(D(2026, 11, 28)))
cp = Calendario(D(2026, 11, 2), pausas=[(D(2026, 11, 9), D(2026, 11, 16))], hoy=D(2026, 11, 23))
chk("una pausa del 9 al 13/11 no cuenta: el 23/11 es el día 10 (no el 15)", cp.dia(D(2026, 11, 23)) == 10, cp.dia(D(2026, 11, 23)))
chk("…y el día 5 del plan cae el 16/11, tras la pausa", cp.fecha(5) == D(2026, 11, 16), cp.fecha(5))
ca = Calendario(D(2026, 11, 2), pausas=[(D(2026, 11, 16), None)], hoy=D(2026, 11, 23))
chk("en pausa AHORA: el plan está parado (el 23/11 sigue siendo el día 10) y lo que falta cuenta desde mañana",
    ca.dia(D(2026, 11, 23)) == 10 and ca.fecha(10) == D(2026, 11, 24), (ca.dia(D(2026, 11, 23)), ca.fecha(10)))
_h = [{"Date": "2026-11-16 10:00", "cambios": {"Status": ["In progress", "On hold"]}},
      {"Date": "2026-11-09 10:00", "cambios": {"Status": ["On hold", "In progress"]}},
      {"Date": "2026-11-05 10:00", "cambios": {"Status": ["In progress", "On hold"]}},
      {"Date": "2026-11-04 10:00", "cambios": {"Progress": ["1", "2"]}}]
chk("pausas_de: del rastro (del más reciente al más antiguo) → una cerrada y una abierta",
    pausas_de(_h, "On hold", D(2026, 11, 23)) == [(D(2026, 11, 5), D(2026, 11, 9)), (D(2026, 11, 16), None)],
    pausas_de(_h, "On hold", D(2026, 11, 23)))
chk("…en pausa SIN rastro: desde hoy (no se inventa un pasado)", pausas_de([], "On hold", D(2026, 11, 23))
    == [(D(2026, 11, 23), None)])
chk("…y sin pausa, ninguna", pausas_de(_h[1:3], "In progress") == [(D(2026, 11, 5), D(2026, 11, 9))])

# ═════════════════════════════════════════════════════════════════
print("2. El motor del plan, en días que cuentan")
_rows = [{"nombre": "A", "duracion": 2, "peso": 50, "orden": 1}, {"nombre": "B", "duracion": 3, "peso": 50, "orden": 2}]
s = S.build_schedule(1, D(2026, 11, 22), {}, custom_rows=_rows)
chk("A: lunes 23 → martes 24; B: miércoles 25 → viernes 27 (el último día de trabajo)",
    [(a["fecha_inicio"], a["fecha_fin"]) for a in s["activities"]]
    == [(D(2026, 11, 23), D(2026, 11, 24)), (D(2026, 11, 25), D(2026, 11, 27))], s["activities"])
chk("el fin del plan es el viernes 27/11 y el cronograma lleva su calendario",
    s["fecha_fin"] == D(2026, 11, 27) and isinstance(s.get("cal"), Calendario), (s["fecha_fin"], s.get("cal")))
_p = S.schedule_projection(s, [100, 0], 2)
chk("la proyección: el fin previsto en días que cuentan (viernes 27/11, a tiempo)",
    _p["fecha_cadena"] == D(2026, 11, 27) and _p["dias_cadena"] == 0.0, (_p["fecha_cadena"], _p["dias_cadena"]))
import re                                                                     # noqa: E402
_svg = S.schedule_svg(s, today_day=2)
# solo las etiquetas del EJE (el título del gráfico lleva la fecha de inicio, 22/11)
_eje = re.findall(r'font-size="7\.5" fill="#5b6472">(\d\d/\d\d)</text>', _svg)
chk("el eje del Gantt no enseña sábado ni domingo (empieza el lunes 23/11, sin 22/11 ni 28/11)",
    _eje and _eje[0] == "23/11" and "22/11" not in _eje and "28/11" not in _eje, _eje)

# ═════════════════════════════════════════════════════════════════
print("3. La obra: hoy, sus ventanas y sus pausas")
from core import auditoria                                                    # noqa: E402
_prj = {"ID": "PRJ-T", "StartDate": "2026-11-02", "Status": "In progress", "NS": "8"}
_acts = [{"Name": "A", "DurationDays": "5", "Weight": "50", "Order": "1", "Progress": "100",
          "ActualStartDate": "2026-11-02", "ActualEndDate": "2026-11-06"},
         {"Name": "B", "DurationDays": "10", "Weight": "50", "Order": "2", "Progress": "20",
          "ActualStartDate": "2026-11-16", "ActualEndDate": ""}]
_rr = [_sustituir(P, get_project=lambda pid: dict(_prj), list_activities=lambda pid: [dict(a) for a in _acts]),
       _sustituir(clock, today=lambda *a, **k: D(2026, 11, 23)),
       _sustituir(auditoria, is_configured=lambda: True,
                  historial=lambda grupo=None, entidad=None, entidad_id=None, limite=200: [
                      {"Date": "2026-11-13 09:00", "cambios": {"Status": ["On hold", "In progress"]}},
                      {"Date": "2026-11-09 09:00", "cambios": {"Status": ["In progress", "On hold"]}}])]
# lo destapó romper_v698: se mira QUÉ ventanas llegan a la curva real (no solo que el calendario sepa convertir)
_VEN = []
_real0 = S.real_scurve
_rv = _sustituir(S, real_scurve=lambda sched, av, upto_day=None, windows=None: (_VEN.append(windows),
                                                                              _real0(sched, av, upto_day, windows))[1])
ps = P.project_schedule("PRJ-T")
_rv()
chk("las fechas REALES de cada actividad, en días del plan: A 2/11→6/11 = (0, 4); B desde el 16/11 = (6, sin fin)",
    _VEN and _VEN[0] == [(0, 4), (6, None)], _VEN)
chk("hoy (lunes 23/11) es el día 11 del plan: 15 laborables desde el 2/11 menos 4 de pausa (9–12/11)",
    ps["today_day"] == 11, ps["today_day"])
# la pausa va del 9/11 al 13/11 EXCLUIDO (volvió el viernes 13): cuentan 2–6/11 (5) y el 13 (1)
chk("…y la ventana real de B empieza en su día del plan (16/11 → 6)", ps["sched"]["cal"].dia(D(2026, 11, 16)) == 6,
    ps["sched"]["cal"].dia(D(2026, 11, 16)))
chk("el fin del plan (15 días de trabajo) cae el 26/11, después de la pausa", ps["sched"]["fecha_fin"] == D(2026, 11, 26),
    ps["sched"]["fecha_fin"])
from core import projects_ui as PU                                            # noqa: E402
_d = PU._diagnostico(ps)
chk("el diagnóstico usa el calendario (sin hito: B ya empezó)", _d["proximo"] is None, _d["proximo"])
for _x in _rr:
    _x()
_gc = ast.unparse(_func("core/projects.py", "grouping_curve"))
chk("la curva de una agrupación pasa cada fecha por el calendario de CADA obra",
    "s['cal'].dia(d) if s.get('cal')" in _gc and "s['cal'].fin(s['plan'][-1][0])" in _gc)
_dg = ast.unparse(_func("core/projects_ui.py", "_diagnostico"))
chk("el hito sale del calendario", "sched['cal'].fecha(a['inicio']) if sched.get('cal')" in _dg)
_src = _fuente("core/projects_ui.py")
chk("los textos dicen que son días de TRABAJO («working day N of M», «working days, Monday to Friday»)",
    'f"working day {_hoy_real} of {_tot}"' in _src and "working days, Monday to Friday" in _src
    and "(in {_fl:.0f} working days)." in _src)

# ═════════════════════════════════════════════════════════════════
print("4. Lo visto con la sesión de campo")
_css = theme._CSS
_i = _css.find("@media (prefers-reduced-motion: reduce) {\n  .st-key-cpx_flash")
_b = _css[_i:_i + 260]
chk("con «reducir movimiento», el aviso desaparece DE GOLPE a los 9 s (steps, sin fundido; gana a la global)",
    _i > 0 and "animation: cpxFlashFuera 9s steps(1, end) forwards !important" in _b
    and "animation-duration: 9s !important" in _b, _b)
chk("el aviso de lo no enviado, sin el punto dentro de las comillas",
    "literal_md(str(x).rstrip(' .'))" in ast.unparse(_func("core/daily_log_ui.py", "_propuestas")))

print()
print("verif_v698: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v698: TODO OK")
sys.exit(1 if FALLOS else 0)
