"""v365 — los 19 mensajes que morían en un `st.rerun()` pasan a `flash`.

⚠️ Se sustituye SOLO el nombre de la función (`st.success` → `flash.exito`) en su
posición exacta por AST. Los argumentos no se tocan: varios son multilínea o llevan
condicionales dentro, y reescribirlos por texto es como se rompió la indentación en
v120 y v148.

⚠️ Se procesa cada fichero de ATRÁS hacia adelante: al sustituir se mueven los offsets
de todo lo que viene después.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

MENSAJES = {"success": "exito", "warning": "aviso", "error": "error", "info": "info"}


def llamada(nodo, attrs):
    if not isinstance(nodo, ast.Expr) or not isinstance(nodo.value, ast.Call):
        return None
    f = nodo.value.func
    if isinstance(f, ast.Attribute) and getattr(f.value, "id", "") == "st" and f.attr in attrs:
        return f
    return None


def morideros(arbol):
    """[(nodo_func, attr)] de los mensajes que se pierden en un rerun."""
    out = []

    def revisar(cuerpo):
        pend = []
        for s in cuerpo:
            f = llamada(s, MENSAJES)
            if f is not None:
                pend.append(f)
                continue
            if llamada(s, {"rerun"}) is not None:
                out.extend(pend)
                pend = []
                continue
            if isinstance(s, (ast.Return, ast.Raise)):
                pend = []
        for s in cuerpo:
            for campo in ("body", "orelse", "finalbody"):
                sub = getattr(s, campo, None)
                if isinstance(sub, list) and sub:
                    revisar(sub)
            for h in getattr(s, "handlers", []) or []:
                revisar(h.body)

    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            revisar(n.body)
    return out


total = 0
for f in sorted(CORE.glob("*_ui.py")):
    src = f.read_text(encoding="utf-8")
    objetivos = morideros(ast.parse(src))
    if not objetivos:
        continue
    lineas = src.splitlines(keepends=True)
    # offset absoluto del inicio de cada línea
    base = [0]
    for ln in lineas:
        base.append(base[-1] + len(ln))

    # de atrás hacia adelante
    objetivos.sort(key=lambda n: (n.lineno, n.col_offset), reverse=True)
    hechos = []
    for nodo in objetivos:
        ini = base[nodo.lineno - 1] + nodo.col_offset
        fin = base[nodo.end_lineno - 1] + nodo.end_col_offset
        viejo = src[ini:fin]
        assert viejo == f"st.{nodo.attr}", f"{f.name}:{nodo.lineno} esperaba 'st.{nodo.attr}', hay {viejo!r}"
        nuevo = f"flash.{MENSAJES[nodo.attr]}"
        src = src[:ini] + nuevo + src[fin:]
        hechos.append(f"{nodo.lineno}: {viejo} → {nuevo}")

    # import a nivel de módulo (flash es HOJA: solo importa streamlit, sin ciclos)
    if "from core import flash" not in src and "import flash" not in src:
        ancla = "import streamlit as st\n"
        assert ancla in src, f"{f.name}: no encuentro el import de streamlit"
        src = src.replace(ancla, ancla + "\nfrom core import flash\n", 1)
        hechos.append("+ import flash")

    f.write_text(src, encoding="utf-8")
    total += len(objetivos)
    print(f"── {f.name}: {len(objetivos)} mensajes")
    for h in reversed(hechos):
        print(f"     {h}")

print(f"\nTOTAL convertidos: {total}")
