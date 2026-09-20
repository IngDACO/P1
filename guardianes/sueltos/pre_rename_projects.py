"""PRE-VUELO de `projects_ui`: renombra los `t` que taparían el motor de idioma.

Se hace ANTES de traducir (lección de v437/v439/quotes_ui: comprobarlo después es
comprobarlo con el daño ya escrito). Son renombrados de variables locales; no cambian
comportamiento.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")

R = [
    # `_tlabel(t)` — `t` es el TIPO de proyecto
    ('    def _tlabel(t):\n'
     '        return (f"Todos ({len(entries)})" if t == "Todos"\n'
     '                else f"{_TIPO_LABEL.get(t, t)} ({cuenta[t]})")',
     '    def _tlabel(_tp):\n'
     '        return (f"Todos ({len(entries)})" if _tp == "Todos"\n'
     '                else f"{_TIPO_LABEL.get(_tp, _tp)} ({cuenta[_tp]})")'),

    # `for t in req:` — `t` es cada TIPO de certificado exigido
    ('        for t in req:\n'
     '            fila[t] = _ico.get(comp["por_tipo"].get(t, "falta"), "—")',
     '        for _c in req:\n'
     '            fila[_c] = _ico.get(comp["por_tipo"].get(_c, "falta"), "—")'),

    # `t = data["totales"]`
    ('    t = data["totales"]\n', '    _tot = data["totales"]\n'),
    # ⚠️ y TODOS sus usos: renombrar la asignación y dejar los usos deja un NameError.
    ('+ _kpi_card("Costo cargado", T.dinero(t["costo"], 0))',
     '+ _kpi_card("Costo cargado", T.dinero(_tot["costo"], 0))'),
    ('+ _kpi_card("Ingreso estimado", T.dinero(t["ingreso"], 0))',
     '+ _kpi_card("Ingreso estimado", T.dinero(_tot["ingreso"], 0))'),
    ('+ _kpi_card("Ganancia estimada", T.dinero(t["ganancia"], 0),\n'
     '                            T.VERDE if t["ganancia"] > 0 else None)',
     '+ _kpi_card("Ganancia estimada", T.dinero(_tot["ganancia"], 0),\n'
     '                            T.VERDE if _tot["ganancia"] > 0 else None)'),
]

s = P.read_text(encoding="utf-8")
fallos = [o for o, n in R if s.count(o) != 1 and s.count(n) == 0]
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines())[:100])
    sys.exit(1)
for o, n in R:
    if s.count(o):
        s = s.replace(o, n, 1)
ast.parse(s)

# ⚠️ `t = data["totales"]` se usaba más abajo: hay que convertir TODOS sus usos o el
# renombrado deja un NameError. Se localizan por AST dentro de esa función.
tr = ast.parse(s)
pend = []
for fn in ast.walk(tr):
    if isinstance(fn, ast.FunctionDef) and fn.name == "render_group_profitability":
        pend = sorted({n.lineno for n in ast.walk(fn)
                       if isinstance(n, ast.Name) and n.id == "t"})
if pend:
    print(f"  ⚠️ quedan usos de `t` en render_group_profitability: {pend}")
    lin = s.splitlines(True)
    for ln in pend:
        print(f"      {ln}: {lin[ln - 1].rstrip()[:96]}")
    sys.exit(1)

P.write_text(s, encoding="utf-8")
print("  projects_ui: 3 renombrados, sin usos colgando")
