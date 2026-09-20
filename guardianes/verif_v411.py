"""v411: franjas alternas + columna de HOY en el Panel.

Dos afirmaciones sobre el PRINCIPIO (regla v392), no sobre los colores ni los píxeles:

  (a) La zebra se pinta por CONTENEDOR-POR-FILA con su propia key, y no con un
      `nth-child` sobre el `stLayoutWrapper` que Streamlit intercala. Ese wrapper es
      reciente: una regla atada a él se rompe EN SILENCIO si mañana Streamlit mete otro
      nivel (v327), y una zebra que desaparece sola no da ningún error.

  (b) «Hoy» se resalta SOLO si cae en la semana que se está viendo. Si se marcara sin
      comprobarlo, al navegar a otra semana un día cualquiera aparecería como hoy —
      que es peor que no marcar nada, porque miente.

Además: la celda vacía tiene que ser TRANSPARENTE. Con fondo propio tapaba las dos
señales justo en las celdas vacías, que son la mayoría del tablero.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py")

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


src = F.read_text(encoding="utf-8")
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
f = next((n for n in ast.walk(arb)
          if isinstance(n, ast.FunctionDef) and n.name == "_tablero_editable"), None)
chk("existe `_tablero_editable`", f is not None)

# Todas las cadenas del cuerpo (ya sin comentarios): un comentario que mencionara
# `rosrow_` daría un OK falso (trampa nº2).
cad = [n.value for n in ast.walk(f)
       if isinstance(n, ast.Constant) and isinstance(n.value, str)]
todo = "".join(cad)

# ── (a) La zebra, por key de fila ───────────────────────────────────────────
chk("se crea un contenedor POR FILA con key `rosrow_`",
    any("rosrow_" in c for c in cad))
_crea_row = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "container"
                and any(kw.arg == "key" for kw in n.keywords)
                for n in ast.walk(f))
chk("...creado con `container(key=...)`", _crea_row)
chk("la zebra se pinta sobre esa key, no sobre el wrapper de Streamlit",
    ".st-key-rosrow_" in todo)
# ⚠️ Se busca el SELECTOR, no la palabra. La primera versión miraba
# `"stLayoutWrapper" not in todo` y daba FALLO con el código correcto: ese nombre
# aparece en un COMENTARIO CSS que va DENTRO de la cadena de estilos, y `tokenize` no
# lo quita porque para Python es parte de un string, no un comentario. Es la trampa nº2
# (grep ≠ uso) en su variante más escurridiza: comentario dentro de un literal.
_SEL_WRAPPER = ('data-testid="stLayoutWrapper"' in todo
                or "data-testid='stLayoutWrapper'" in todo)
chk("...y NO se estila el `stLayoutWrapper` de Streamlit (frágil, v327)",
    not _SEL_WRAPPER)

# ── (b) «Hoy», solo si cae en la semana ─────────────────────────────────────
# Debe existir una comparación entre la fecha de un día del tablero y `clock.today`.
_usa_today = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "today" for n in ast.walk(f))
_usa_fecha = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "fecha_de_dia" for n in ast.walk(f))
chk("se consulta el día de hoy (`clock.today`)", _usa_today)
chk("...y la fecha real de cada columna (`fecha_de_dia`)", _usa_fecha)

# El resaltado tiene que colgar de que hoy SE HAYA ENCONTRADO en la semana.
_guarda = False
for n in ast.walk(f):
    if isinstance(n, ast.If):
        prueba = ast.dump(n.test)
        if "_hoy_idx" in prueba:
            cuerpo = ast.dump(ast.Module(body=n.body, type_ignores=[]))
            if "nth-child" in "".join(
                    x.value for x in ast.walk(n) if isinstance(x, ast.Constant)
                    and isinstance(x.value, str)):
                _guarda = True
chk("el resaltado de hoy cuelga de haberlo encontrado en la semana visible", _guarda)
chk("se resalta la columna por `nth-child` (los hijos de una fila son todos stColumn)",
    "nth-child" in todo)
chk("...tanto en el cuerpo como en la cabecera",
    ".st-key-rosgrid" in todo and ".st-key-roshead" in todo)

# ── La celda vacía, transparente ────────────────────────────────────────────
chk("la celda vacía es TRANSPARENTE (si no, tapa zebra y hoy)",
    "background:transparent!important" in todo)
chk("...y ya no lleva su fondo propio", "background:#f8fafc!important" not in todo)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
