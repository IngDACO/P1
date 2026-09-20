"""v399 · Ninguna columna de dinero puede pintar sin separador de miles.

QUE PROTEGE (el PRINCIPIO, no el numero de hoy — leccion de la trampa nº16):
la app tiene UNA cara para el dinero. `theme.dinero` pone `$27,883` en KPIs, pies
y tarjetas; una `NumberColumn` con `format="$%.0f"` pintaba `$27883`, o sea la
misma cifra con dos caras en la misma pantalla. Cualquier columna de dinero nueva
que nazca sin la coma vuelve a abrir esa grieta.

⚠️ El chequeo va por AST y NO por texto: un `format="$%d"` escrito en un comentario
o en un docstring no es un uso (trampa nº2, `grep != uso`, que ya ha mordido 4 veces).

⚠️ Y NO se exige `%.0f`: `%d` TRUNCA y `%.0f` REDONDEA (3305.76 -> $3,305 vs
$3,306). Unificarlos moveria cifras en pantalla. Cada columna conserva su
semantica; lo unico obligatorio es el separador.
"""
import ast
import io
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

ok = True


def check(nombre, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {nombre}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def formatos_de_dinero(src):
    """[(linea, formato)] de cada `*Column(..., format="$...")` REAL del arbol."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
        if not fn.endswith("Column"):
            continue
        for kw in n.keywords:
            if kw.arg == "format" and isinstance(kw.value, ast.Constant) \
                    and isinstance(kw.value.value, str) and "$" in kw.value.value:
                out.append((n.lineno, kw.value.value))
    return out


print("== 1) la sonda SABE ver el caso roto ==")
# ⚠️ Sin esto, un chequeo que no encuentra nada parece aprobar (trampa nº1 y nº12).
_roto = 'st.column_config.NumberColumn("X", format="$%d")\n'
_sano = 'st.column_config.NumberColumn("X", format="$%,d")\n'
check("detecta el formato sin coma",
      [f for _l, f in formatos_de_dinero(_roto) if "," not in f], ["$%d"])
check("...y deja pasar el que la lleva",
      [f for _l, f in formatos_de_dinero(_sano) if "," not in f], [])
check("un formato en un COMENTARIO no cuenta como uso",
      formatos_de_dinero('# format="$%d"\nx = 1\n'), [])
check("...ni dentro de un docstring",
      formatos_de_dinero('"""ejemplo: format="$%d" """\nx = 1\n'), [])

print("\n== 2) el repo ENTERO ==")
_fuentes = sorted((BASE / "core").glob("*.py")) + [BASE / "app.py"]
_todos, _sin_coma = [], []
for p in _fuentes:
    for ln, f in formatos_de_dinero(io.open(p, encoding="utf-8").read()):
        _todos.append((p.name, ln, f))
        if "," not in f:
            _sin_coma.append(f"{p.name}:{ln} {f}")
check("hay columnas de dinero que revisar (si no, el test pasa en vacio)",
      len(_todos) > 0, True)
print(f"         {len(_todos)} columnas de dinero en "
      f"{len({n for n, _l, _f in _todos})} modulos")
check("TODAS llevan separador de miles", _sin_coma, [])
check("ninguna con la coma duplicada",
      [x for x in _todos if ",," in x[2]], [])

print("\n== 3) cada columna conserva SU semantica (no se unifico nada) ==")
_specs = sorted({f.replace("$", "").replace(",", "") for _n, _l, f in _todos})
check("solo los tres especificadores de siempre", _specs, ["%.0f", "%.2f", "%d"])
# el reparto se DERIVA del codigo, no se fija a mano
from collections import Counter                                      # noqa: E402
_rep = Counter(f for _n, _l, f in _todos)
print("         " + " · ".join(f"{k} x{v}" for k, v in sorted(_rep.items())))
check("sigue habiendo columnas que TRUNCAN (%d) y columnas que REDONDEAN (%.0f)",
      bool(_rep.get("$%,d")) and bool(_rep.get("$%,.0f")), True)

print("\n== 4) los porcentajes NO se tocaron ==")
# los margenes van < 500, un separador ahi seria ruido
_pct = [f for p in _fuentes
        for _l, f in formatos_de_dinero(io.open(p, encoding="utf-8").read())
        if f.endswith("%%")]
check("ningun formato de dinero acabo siendo un porcentaje", _pct, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
