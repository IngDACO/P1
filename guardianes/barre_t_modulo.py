# -*- coding: utf-8 -*-
"""¿Hay algún `t()` que se evalúe AL IMPORTAR el módulo?

Una llamada a `t()` a nivel de módulo (o en el valor por defecto de un parámetro) se
ejecuta **una sola vez, al importar**, cuando todavía no hay sesión ni idioma
elegido. La cadena queda CONGELADA en el idioma de ese instante:

  · con el diccionario español lleno, ese texto saldría en inglés y solo ése;
  · y si además se compara (`tok == auth.SESION_OCUPADA`), traducir un lado y no el
    otro rompe la comparación **sin dar ningún error** — en `auth` eso hacía
    desaparecer el botón de «cerrar la otra sesión».

⚠️ Dentro de una FUNCIÓN sí vale: se evalúa en cada llamada, con la sesión ya viva.
Lo que se prohíbe es el ámbito de módulo y los defaults de parámetro.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
# ⚠️ Solo `t`. `d()` devuelve **siempre el idioma base, pase lo que pase** (v436),
# así que congelarlo al importar no cambia nada — por eso `plumb.LINE_NAMES` puede
# construirse a nivel de módulo con `_d()` sin problema.
MOTOR = {"t", "_i18t"}
# ⚠️ `app.py` NO es un módulo importado: es el SCRIPT, y Streamlit lo re-ejecuta
# entero en cada rerun. Su «nivel de módulo» corre con la sesión viva, así que ahí
# no se congela nada. Incluirlo daba 8 falsos positivos.
EXCL = {"app.py"}


def congelados(ruta):
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    # (a) ámbito de MÓDULO: todo lo que cuelga de tr.body sin entrar en def/class
    pila = [(x, False) for x in tr.body]
    while pila:
        n, _ = pila.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue                      # su cuerpo se ejecuta al LLAMAR, no al importar
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in MOTOR:
            out.append((n.lineno, "nivel de módulo"))
        for c in ast.iter_child_nodes(n):
            pila.append((c, False))
    # (b) valores por DEFECTO de parámetros: también se evalúan al definir la función
    for n in ast.walk(tr):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs = list(n.args.defaults) + [x for x in n.args.kw_defaults if x]
            for d_ in defs:
                for x in ast.walk(d_):
                    if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) \
                       and x.func.id in MOTOR:
                        out.append((x.lineno, f"default de {n.name}()"))
    return out


if __name__ == "__main__":
    tot = 0
    for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
        if f.name in EXCL:
            continue
        for ln, donde in sorted(set(congelados(f))):
            print(f"  ⚠️ {f.name}:{ln}  {donde}")
            tot += 1
    print(f"\n{tot} llamadas al motor que se CONGELAN al importar")
