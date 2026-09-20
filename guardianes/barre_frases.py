"""⚠️ El hueco de v349, aplicado al i18n.

El invariante de v441 mira el ARGUMENTO de la llamada de display. Una cadena que se
arma antes en una variable (`msg = f"..."; st.success(msg)`) pasa por delante sin que
salte nada — exactamente como el guardián del LaTeX de v309 no veía las variables.

Este barrido no mira el receptor ni el idioma: recoge TODA cadena literal del módulo
que NO esté ya dentro de `t(...)`/`d(...)` y que PAREZCA UNA FRASE (3+ palabras con
letras). Una clave de dict, un formato o un id no son frases; un texto de pantalla sí.
"""
import ast, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")


def frases(ruta: Path, minimo: int = 3):
    src = ruta.read_text(encoding="utf-8")
    tr = ast.parse(src)

    # 1) lo que ya está envuelto en t()/d() no cuenta
    envueltos = set()
    for c in ast.walk(tr):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in ("t", "d", "_d"):
            for a in c.args:
                for x in ast.walk(a):
                    envueltos.add(id(x))

    # 2) docstrings: son documentación, no pantalla
    docs = set()
    for n in ast.walk(tr):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))

    # 3) los mensajes de LOG no son pantalla (filtrar por RECEPTOR, lección v439)
    logs = set()
    for c in ast.walk(tr):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
           and isinstance(c.func.value, ast.Name) and c.func.value.id in ("logger", "log", "logging"):
            for a in ast.walk(c):
                logs.add(id(a))

    out = []
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Constant) and isinstance(x.value, str)):
            continue
        if id(x) in envueltos or id(x) in docs or id(x) in logs:
            continue
        s = x.value.strip()
        # ⚠️ Palabras separadas por ESPACIO: `sidebar_chat_input` no es una frase,
        # y contarlo como tal ahoga el barrido en 1.375 falsos positivos.
        pal = [w for w in re.split(r"\s+", s)
               if len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]", w)) >= 2]
        if len(pal) >= minimo:
            out.append((x.lineno, s))
    return out


if __name__ == "__main__":          # ⚠️ sin esto, importarlo corre su propio barrido
  UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
  tot = 0
  for m in UI + ["app"]:
      rel = "app.py" if m == "app" else f"core/{m}.py"
      f = sorted(set(frases(RAIZ / rel)))
      if f:
          print(f"\n=== {m}  ({len(f)}) ===")
          for ln, s in f:
              print(f"  {ln:5}  {s[:92]!r}")
          tot += len(f)
  print(f"\nTOTAL frases sin envolver: {tot}")
