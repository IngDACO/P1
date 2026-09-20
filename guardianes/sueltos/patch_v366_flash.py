"""v366 — los 71 mensajes que mueren en un `st.rerun()`.

⚠️ LA TRAMPA: el idioma más común del repo es

    (st.success if ok else st.error)(msg)
    if ok:
        st.rerun()

Solo la rama de ÉXITO muere (es la que hace rerun). La de ERROR se pinta y se queda,
porque ahí no hay rerun. Convertir las dos a `flash` **rompería los errores**: quedarían
encolados esperando un rerun que no llega, y aparecerían más tarde en otra pantalla.
→ Se convierte SOLO la rama que reruns: `(flash.exito if ok else st.error)(msg)`.

Regla aplicada:
  · `st.MSG(...)` suelto seguido de rerun  → `flash.<equiv>(...)`
  · `(st.A if C else st.B)(...)` con el rerun bajo `if C:` → se convierte solo la rama
    que corresponde a C (la `body` si el rerun cuelga de `if C`, la `orelse` si de `if not C`)
  · cualquier otra forma → NO se toca, se reporta para mirarla a mano
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
MAP = {"success": "exito", "warning": "aviso", "error": "error", "info": "info"}


def attrs_st(n):
    if isinstance(n, ast.Attribute) and getattr(n.value, "id", "") == "st":
        return [n]
    if isinstance(n, ast.IfExp):
        return attrs_st(n.body) + attrs_st(n.orelse)
    return []


def es_msg(s):
    if not isinstance(s, ast.Expr) or not isinstance(s.value, ast.Call):
        return None
    a = attrs_st(s.value.func)
    return s.value.func if a and all(x.attr in MAP for x in a) else None


def es_rerun(s):
    if not isinstance(s, ast.Expr) or not isinstance(s.value, ast.Call):
        return False
    f = s.value.func
    return isinstance(f, ast.Attribute) and getattr(f.value, "id", "") == "st" and f.attr == "rerun"


_WIDGETS = {"button", "form_submit_button", "checkbox", "toggle", "download_button"}


def _test_es_widget(test):
    """¿La condición del `if` es un WIDGET (`st.button(...)`)?

    ⚠️ Distinción CLAVE, aprendida rompiéndolo: un rerun dentro de `if st.button(...)`
    NO mata el mensaje de arriba, porque ese mensaje se pinta en CADA pasada — es una
    insignia de ESTADO, no la confirmación de una acción:

        st.success("Telegram vinculado.")      ← estado, se ve siempre
        if st.button("Desvincular"):
            st.rerun()                          ← solo al pulsar

    Convertirlo a `flash` lo empeora: desaparece el estado y el mensaje reaparece
    suelto en otra pantalla. Solo cuenta como «muere en el rerun» cuando la condición
    es un dato (`if ok:`), o sea el resultado de una acción que ya ocurrió.
    """
    for n in ast.walk(test) if test is not None else []:
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and getattr(f.value, "id", "") == "st" \
                    and f.attr in _WIDGETS:
                return True
    return False


def rerun_bajo(stmt):
    """(hay_rerun, test) del rerun que cuelga directamente de este if/try/for."""
    test = getattr(stmt, "test", None)
    if _test_es_widget(test):
        return False, (None, None)          # el mensaje de arriba es un estado
    for campo in ("body", "orelse", "finalbody"):
        for s in getattr(stmt, campo, None) or []:
            if es_rerun(s):
                return True, (test, campo)
    for h in getattr(stmt, "handlers", []) or []:
        for s in h.body:
            if es_rerun(s):
                return True, (None, "handler")
    return False, (None, None)


cambios, manuales = [], []

for f in sorted(CORE.glob("*_ui.py")):
    src = f.read_text(encoding="utf-8")
    arbol = ast.parse(src)
    objetivos = []                       # (nodo_attr_a_cambiar,)

    def revisar(cuerpo):
        pend = []
        for s in cuerpo:
            fn = es_msg(s)
            if fn is not None:
                pend.append((s, fn))
                continue
            hay, (test, _campo) = (True, (None, None)) if es_rerun(s) else rerun_bajo(s)
            if hay:
                for (stmt, fnode) in pend:
                    if isinstance(fnode, ast.Attribute):
                        objetivos.append(fnode)                 # caso simple
                    elif isinstance(fnode, ast.IfExp):
                        # ⚠️ solo la rama que hace rerun
                        if test is not None and ast.dump(test) == ast.dump(fnode.test):
                            rama = fnode.body if _campo == "body" else fnode.orelse
                            if isinstance(rama, ast.Attribute):
                                objetivos.append(rama)
                            else:
                                manuales.append(f"{f.name}:{stmt.lineno} rama no simple")
                        else:
                            manuales.append(f"{f.name}:{stmt.lineno} condición del rerun "
                                            f"no coincide con la del mensaje")
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

    if not objetivos:
        continue

    lineas = src.splitlines(keepends=True)
    base = [0]
    for ln in lineas:
        base.append(base[-1] + len(ln))
    # sin duplicados, de atrás hacia adelante
    vistos, unicos = set(), []
    for n in objetivos:
        k = (n.lineno, n.col_offset)
        if k not in vistos:
            vistos.add(k)
            unicos.append(n)
    unicos.sort(key=lambda n: (n.lineno, n.col_offset), reverse=True)

    for n in unicos:
        ini = base[n.lineno - 1] + n.col_offset
        fin = base[n.end_lineno - 1] + n.end_col_offset
        viejo = src[ini:fin]
        assert viejo == f"st.{n.attr}", f"{f.name}:{n.lineno} esperaba st.{n.attr}, hay {viejo!r}"
        src = src[:ini] + f"flash.{MAP[n.attr]}" + src[fin:]
        cambios.append(f"{f.name}:{n.lineno} st.{n.attr} → flash.{MAP[n.attr]}")

    if "from core import flash" not in src.split("def ")[0]:
        ancla = "import streamlit as st\n"
        assert ancla in src, f"{f.name}: sin import de streamlit"
        src = src.replace(ancla, ancla + "\nfrom core import flash\n", 1)
        cambios.append(f"{f.name}: + import flash (módulo)")

    f.write_text(src, encoding="utf-8")

print(f"== convertidos: {len([c for c in cambios if '→' in c])} ==")
for c in cambios:
    print("  ", c)
if manuales:
    print(f"\n== ⚠️ para mirar a mano ({len(manuales)}) ==")
    for m in manuales:
        print("  ", m)
