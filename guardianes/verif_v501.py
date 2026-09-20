# -*- coding: utf-8 -*-
"""v501 · la LÍNEA BASE: el plan que se acordó, congelado.

Lo que protege:
  (a) que la ORIGINAL no se pierda nunca — es lo que sostiene el reclamo, y re-fijar no
      puede reescribir el pasado;
  (b) que un fallo de LECTURA no la borre: escribir «como si no hubiera» es peor que no
      escribir (v492);
  (c) que la comparación case las actividades por su ORDEN y no por posición, que en
      cuanto alguien reordena o borra una da basura en silencio;
  (d) la fila posicional contra su cabecera (v363);
  (e) y que el campo no fije líneas base.
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


from core import baseline as BL, projects as P                    # noqa: E402
from core.schedule import build_schedule                          # noqa: E402

INI = dt.date(2026, 9, 1)


def plan(durs, preds=None):
    return build_schedule(1, INI, {}, custom_rows=[
        {"nombre": "A%d" % (i + 1), "duracion": d, "peso": 10, "orden": i + 1,
         "pred": (preds[i] if preds else "")} for i, d in enumerate(durs)])


# ═════ 1 · congelar, comparar, re-fijar ══════════════════════════════════════
print("\n[1] el plan acordado se congela, y lo que se mueve se ve")
s1 = plan([4, 4, 4])
bl = BL.fijar({}, s1, "Bobo", "2026-09-17 09:00")
ck("al fijar se guarda la entrega, el total y las actividades",
   (bl["original"]["entrega"], bl["original"]["total"], len(bl["original"]["acts"])),
   ("2026-09-13", 12.0, 3))
ck("...y todavía no hay replanificaciones", bl["historial"], [])
ck("si el plan no cambia, no hay nada que reportar", BL.comparar(s1, bl)["actividades"], [])

s2 = plan([4, 8, 4])
c = BL.comparar(s2, bl)
ck("alargar una actividad mueve la entrega y se DICE", c["movio"], 4.0)
ck("...y se ve cuál cambió y cuánto se desplazó la siguiente",
   [(f["orden"], f["estado"], f["dur_base"], f["dur_hoy"], f["movio"]) for f in c["actividades"]],
   [(2, "cambiada", 4.0, 8.0, 0.0), (3, "cambiada", 4.0, 4.0, 4.0)])

# ⚠️ (a) la ORIGINAL no se toca al re-fijar
bl2 = BL.fijar(bl, s2, "Bobo", "2026-09-20 10:00")
ck("re-fijar CONSERVA la original", bl2["original"], bl["original"])
ck("...mueve la vigente", bl2["vigente"]["total"], 16.0)
ck("...y deja el rastro de cuánto movió la entrega",
   [(h["movio"], h["por"]) for h in bl2["historial"]], [(4.0, "Bobo")])
ck("tras re-fijar se SIGUE comparando contra la original", BL.comparar(s2, bl2)["movio"], 4.0)
ck("...y el contador de replanificaciones lo dice",
   BL.comparar(s2, bl2)["replanificaciones"], 1)

# ⚠️ (c) por ORDEN, no por posición
ck("una actividad NUEVA se marca como tal",
   [(f["orden"], f["estado"]) for f in BL.comparar(plan([4, 8, 4, 3]), bl)["actividades"]],
   [(2, "cambiada"), (3, "cambiada"), (4, "nueva")])
ck("...y una ELIMINADA también",
   [(f["orden"], f["estado"]) for f in BL.comparar(plan([4]), bl)["actividades"]],
   [(2, "eliminada"), (3, "eliminada")])
ck("sin línea base no se compara nada (la obra va como hasta v500)",
   BL.comparar(s1, {}), {"hay": False})

# ⚠️ Con órdenes 1,2,3 la posición y el orden COINCIDEN, así que casar por una o por otra
# da lo mismo y el caso no puede distinguirlas — el chequeo aprobaría igual con el fallo
# dentro. Aquí los órdenes son 1, 5 y 9 (una obra reordenada), que es cuando duele.
def _plan_ordenes(pares):
    return build_schedule(1, INI, {}, custom_rows=[
        {"nombre": "A%d" % o, "duracion": d, "peso": 10, "orden": o, "pred": "-" if i == 0 else str(prev)}
        for i, ((o, d), prev) in enumerate(zip(pares, [None] + [p[0] for p in pares[:-1]]))])


_sa = _plan_ordenes([(1, 4), (5, 4), (9, 4)])
_bla = BL.fijar({}, _sa, "Bobo", "2026-09-17 09:00")
_sb = _plan_ordenes([(1, 4), (5, 9), (9, 4)])        # cambia la del ORDEN 5
ck("con órdenes NO consecutivos, la que cambió se identifica por su ORDEN",
   [(f["orden"], f["dur_base"], f["dur_hoy"]) for f in BL.comparar(_sb, _bla)["actividades"]
    if f["estado"] == "cambiada"][:1], [(5, 4.0, 9.0)])

# ═════ 2 · la hoja: fila y cabecera casan (v363) ═════════════════════════════
print("\n[2] la columna nueva no descuadra la fila")
ck("«BaselineJSON» va AL FINAL", P.PROJECTS_HEADERS[-1], "BaselineJSON")
_tr = ast.parse(_fuente("core/projects.py"))
_cp = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef) and n.name == "create_project")
_fila = next((len(n.elts) for n in ast.walk(_cp)
              if isinstance(n, ast.List) and "ProjectID" not in ast.unparse(n)
              and len(n.elts) > 20), -1)
ck("la fila de create_project tiene tantos valores como columnas",
   _fila, len(P.PROJECTS_HEADERS))

# ═════ 3 · un fallo de LECTURA no borra la original ══════════════════════════
print("\n[3] si no se puede leer, NO se escribe")
_esc = []
_o_ws, _o_up, _o_sch = P._projects_ws, P.update_project, P.project_schedule
try:
    P.project_schedule = lambda pid: {"sched": plan([4, 4, 4])}
    P.update_project = lambda pid, f: (_esc.append(f), (True, "ok"))[1]

    def _revienta():
        raise RuntimeError("Sheets caído")
    P._projects_ws = _revienta
    _ok, _msg = P.fijar_baseline("PRJ-X", "Bobo")
    ck("con la hoja caída devuelve error...", _ok, False)
    ck("...y NO escribe nada (escribir borraría la original)", _esc, [])
finally:
    P._projects_ws, P.update_project, P.project_schedule = _o_ws, _o_up, _o_sch

# ⚠️ y una obra sin actividades no puede fijar una línea base vacía
_o_sch = P.project_schedule
try:
    P.project_schedule = lambda pid: {"sched": {"activities": []}}
    # ⚠️ No basta con que devuelva False: con la guarda rota TAMBIÉN devuelve False,
    # pero por otro motivo (ese pid no existe en la hoja). Se comprueba el MOTIVO.
    from core.i18n import t as _t
    _okc, _msgc = P.fijar_baseline("PRJ-X", "b")
    ck("una obra sin cronograma no fija línea base, y se dice por qué",
       (_okc, _msgc), (False, _t("This job has no schedule to freeze yet.")))
finally:
    P.project_schedule = _o_sch

# ═════ 4 · la pantalla ═══════════════════════════════════════════════════════
print("\n[4] dónde se fija y quién la ve")
_ui = _fuente("core/projects_ui.py")
_tu = ast.parse(_ui)


def _fn(nombre):
    f = next((n for n in ast.walk(_tu) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)
    return ast.unparse(f) if f else ""


ck("el botón está donde se acuerda el plan (el detalle de gestión)",
   "blset_" in _fn("_detalle_proyecto"), True)
ck("la comparación está donde se mira cómo va", "_BL.comparar" in _fn("_estado_section"), True)
ck("⚠️ el CAMPO no fija líneas base",
   ("blset_" in _fn("render_field_projects") or "_estado_section" in _fn("render_field_projects")),
   False)
# ⚠️ `_kpi_card` DEVUELVE el HTML: usarla como sentencia suelta lo tira y la tarjeta
# no se pinta, sin ningún error (v424).
_sueltas = [n for n in ast.walk(_tu) if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and getattr(n.value.func, "id", "") == "_kpi_card"]
ck("ninguna tarjeta KPI se tira sin pintar (v424)", _sueltas, [])

# ═════ 5 · sin ciclos ════════════════════════════════════════════════════════
print("\n[5] baseline es módulo HOJA")
_imp = [n for n in ast.walk(ast.parse(_fuente("core/baseline.py")))
        if isinstance(n, (ast.Import, ast.ImportFrom))]
_de_core = [ast.unparse(n) for n in _imp if "core" in ast.unparse(n)]
ck("no importa nada de core (no puede ciclar con projects)", _de_core, [])

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
