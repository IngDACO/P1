"""v412: el tope de altura de la celda del Panel, y que no se pierda información.

Medido en producción a 1440 antes de tocar nada: las filas iban de **36 a 116 px** y una
sola celda con dos asignaciones y franja horaria estiraba SU fila al triple. El mayor
responsable no era la celda (53 px) sino **la nota (61 px)**, que ocupaba más que el
trabajo que anota.

Lo que se protege:
  (a) el label de la celda tiene tope de altura Y clamp — las dos cosas: el navegador
      BLOCKIFICA el `display:-webkit-box` (el `<p>` está en un contenedor flex), así que
      el clamp solo se sostiene por el `max-height`;
  (b) la nota va a UNA línea pero conserva el texto completo en el `title`: se acota lo
      que ocupa, no lo que se puede saber;
  (c) ⚠️ y el `title` va ESCAPADO también de comillas. `_esc` no las toca, y una comilla
      en la nota no solo rompería el atributo: permitiría inyectar otros.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


src = (RAIZ / "core" / "roster_ui.py").read_text(encoding="utf-8")
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
f = next((n for n in ast.walk(arb)
          if isinstance(n, ast.FunctionDef) and n.name == "_tablero_editable"), None)
chk("existe `_tablero_editable`", f is not None)
cad = [n.value for n in ast.walk(f)
       if isinstance(n, ast.Constant) and isinstance(n.value, str)]
todo = "".join(cad)

# ── (a) El tope del label ───────────────────────────────────────────────────
print("\n== a) el label de la celda no puede estirar la fila ==")
chk("clamp a 2 líneas", "-webkit-line-clamp: 2" in todo)
chk("...con `display:-webkit-box` (el clamp necesita las tres)",
    "-webkit-box" in todo)
chk("...y `box-orient` (la tercera)", "-webkit-box-orient" in todo)
chk("...y `overflow:hidden`", "overflow: hidden" in todo)
# ⚠️ Este es el que de verdad garantiza la altura: sin él, todo depende de que el
# navegador respete un clamp cuyo `display` él mismo blockifica.
chk("RESPALDO: `max-height` en el label (el clamp solo no basta)",
    "max-height: 29px" in todo)

# ── (b) La nota, acotada pero completa ──────────────────────────────────────
print("\n== b) la nota se acota sin perder el texto ==")
# ⚠️ ACTUALIZADO en v415 (regla v385: caducado, no relajado — razón al lado).
# v412 exigía literalmente `white-space:nowrap` + `text-overflow:ellipsis`, o sea UNA
# línea. Medido después en producción, esa línea **cortaba 2 de las 3 notas reales**, y a
# un aviso («⚠️ se pisa: dos obras a la vez») le faltaban 3 px de 135. v415 pasa a HASTA
# dos líneas. Lo que este guardián protege NO es el número de líneas: es que la nota
# **tenga un tope** y no pueda volver a estirar la fila sin control, que era el fallo de
# v412 (la nota medía 61 px, más que la propia celda).
chk("la nota está acotada a un nº de líneas", "-webkit-line-clamp:2" in todo)
chk("...con tope de altura de respaldo (el clamp se blockifica)",
    "max-height:29px" in todo)
chk("...y el texto COMPLETO sigue en el `title`", 'title="' in todo)
# La nota ya no puede ser un `st.caption`: eso era lo que medía 61 px.
_cap_nota = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "caption"
                and any(isinstance(a, ast.Name) and a.id == "nota" for a in n.args)
                for n in ast.walk(f))
chk("ya NO se pinta con `caption(nota)`", not _cap_nota)

# ── (c) El escape del atributo ──────────────────────────────────────────────
print("\n== c) el `title` no se puede romper (ni inyectar) ==")
from core.roster_ui import _esc                                   # noqa: E402


def _attr(nota):
    return _esc(nota).replace(chr(34), "&quot;")


casos = ['dice "vamos"', "O'Brien & Co", "<b>ojo</b>",
         '" onmouseover="alert(1)', "normal"]
malos = [c for c in casos if '"' in _attr(c) or "<" in _attr(c) or ">" in _attr(c)]
chk("la regla de escape es suficiente (probada sobre casos reales)", malos, [])
print(f"         probadas: {casos}")

# ⚠️ Lo anterior prueba MI regla, no la del código: reproduce el `.replace` en el propio
# test, así que seguía en verde con el escape BORRADO del código — un chequeo que pasa
# en vacío. Lo delató probar el guardián contra el código roto. Aquí se comprueba que la
# expresión del `title` REALMENTE lleva el reemplazo de la comilla.
_escapa_comillas = False
for n in ast.walk(f):
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "replace" and len(n.args) == 2):
        a0, a1 = n.args
        _es_chr34 = (isinstance(a0, ast.Call) and isinstance(a0.func, ast.Name)
                     and a0.func.id == "chr"
                     and isinstance(a0.args[0], ast.Constant) and a0.args[0].value == 34)
        _es_comilla = isinstance(a0, ast.Constant) and a0.value == '"'
        if (_es_chr34 or _es_comilla) and isinstance(a1, ast.Constant) \
                and a1.value == "&quot;":
            _escapa_comillas = True
chk("el CÓDIGO escapa la comilla antes de meterla en el `title`", _escapa_comillas)
chk("`_esc` sigue escapando `&`, `<` y `>`",
    _esc("a & b < c > d"), "a &amp; b &lt; c &gt; d")

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
