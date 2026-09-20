"""Renombra la variable `t` de totales en `quotes_ui` → `_tot`.

⚠️ Yo mismo rompí este módulo: al traducir metí llamadas `t(...)` en tres funciones donde
`t` YA era una variable (el dict de totales) o un PARÁMETRO. Python marca el nombre local
en el ámbito ENTERO, así que:
  · `_nueva`  → UnboundLocalError en la primera etiqueta → «Nueva cotización» no abre
  · `_detalle`→ igual → el detalle de la cotización no abre
  · `_crear_proyecto` / `_totales_html` → `t` es el parámetro, así que `t("…")` sería
    llamar a un DICT → TypeError
Es el fallo de v437/v439 por tercera vez. La lección: correr el chequeo de ÁMBITO ANTES
de traducir un módulo, no después — después el daño ya está escrito en el fichero.
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(r"C:\Users\diego\P1\survey_app\core\quotes_ui.py")
s = P.read_text(encoding="utf-8")

REEMPLAZOS = [
    # asignaciones
    ("        t = Q.totales(lineas, imp)", "        _tot = Q.totales(lineas, imp)"),
    ("    t = Q.totales(lineas, _num(c.get(\"ImpuestoPct\")))",
     "    _tot = Q.totales(lineas, _num(c.get(\"ImpuestoPct\")))"),
    # firma y cuerpo de _totales_html
    ("def _totales_html(t: dict, imp_pct):", "def _totales_html(_tot: dict, imp_pct):"),
    ('T.dinero(t["subtotal"], 0), "antes de impuesto"',
     'T.dinero(_tot["subtotal"], 0), "antes de impuesto"'),
    ('T.dinero(t["impuesto"], 0), f"{_num(imp_pct):g}%"',
     'T.dinero(_tot["impuesto"], 0), f"{_num(imp_pct):g}%"'),
    ('T.dinero(t["total"], 0), "lo que se le cobra", T.AZUL',
     'T.dinero(_tot["total"], 0), "lo que se le cobra", T.AZUL'),
    ('T.dinero(t["ganancia"], 0),', 'T.dinero(_tot["ganancia"], 0),'),
    ('f"margen efectivo {t[\'margen_pct\']:.1f}%", T.VERDE',
     'f"margen efectivo {_tot[\'margen_pct\']:.1f}%", T.VERDE'),
    ('    if t["horas"]:', '    if _tot["horas"]:'),
    ("{t['horas']:g} horas** de ", "{_tot['horas']:g} service hours**. Once accepted "),
    ('"servicio. Al aceptarla podrás compararlas con las horas fichadas.")',
     '"you can compare them against the hours clocked.")'),
    # llamadas y firma de _crear_proyecto
    ("        _crear_proyecto(grupo, c, t)", "        _crear_proyecto(grupo, c, _tot)"),
    ("def _crear_proyecto(grupo, c, t):", "def _crear_proyecto(grupo, c, _tot):"),
    ('+ T.dinero(t["costo"], 0) + "** — es tu **costo** cotizado, no el precio "',
     '+ T.dinero(_tot["costo"], 0) + "** — es tu **costo** cotizado, no el precio "'),
    ('"al cliente (" + T.dinero(t["subtotal"], 0) + "). Así la alerta de "',
     '"al cliente (" + T.dinero(_tot["subtotal"], 0) + "). Así la alerta de "'),
    # el otro resto multilínea
    ('f":material/info: A record already existed for **{_nom}**; "\n'
     '                            f"la cotización se enlaza a esa.")',
     'f":material/info: A record already existed for **{_nom}**; "\n'
     '                            f"the quote is linked to that one.")'),
    ("        _totales_html(t, c.get(\"ImpuestoPct\"))",
     "        _totales_html(_tot, c.get(\"ImpuestoPct\"))"),
    ("        _totales_html(t, imp)", "        _totales_html(_tot, imp)"),
]

fallos = [o for o, n in REEMPLAZOS if s.count(o) != 1 and s.count(n) == 0]
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines())[:100])
    sys.exit(1)

for o, n in REEMPLAZOS:
    if s.count(o) == 1:
        s = s.replace(o, n, 1)
ast.parse(s)
P.write_text(s, encoding="utf-8")

# ⚠️ Comprobación de VERDAD: que no quede ni un `t` local en el módulo.
tr = ast.parse(s)


def mismo(fn):
    out = []
    for h in fn.body:
        pila = [h]
        while pila:
            nn = pila.pop()
            out.append(nn)
            for c in ast.iter_child_nodes(nn):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return out


mal = []
for fn in ast.walk(tr):
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    nod = mismo(fn)
    _st = [n.lineno for n in nod
           if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id == "t"]
    if "t" in {a.arg for a in fn.args.args}:
        _st.append(fn.lineno)
    if _st:
        mal.append(f"{fn.name}:{_st}")
print(f"  quotes_ui reescrito · {len(mal)} funciones con `t` local: {mal or 'ninguna'}")
sys.exit(0 if not mal else 1)
