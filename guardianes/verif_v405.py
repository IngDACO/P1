"""v405 · `use_container_width` solo puede quedar donde NO es de Streamlit.

El runtime lo dice al arrancar: «use_container_width will be removed after
2025-12-31». Hay fecha y ya pasó, así que puede desaparecer en cualquier versión.

⚠️ Lo que este guardián protege NO es «que no aparezca la palabra»: en `st_folium` ese
parámetro es del COMPONENTE y convertirlo rompe el mapa (es el arreglo de v307 que
llenó el hueco blanco de la Ruta del día). Lo que se exige es: ningún elemento de
STREAMLIT lo usa; los componentes de terceros pueden.
"""
import ast
import io
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
TERCEROS = {"st_folium", "st_canvas"}          # tienen su propio parámetro
ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def usos(src):
    """[(elemento, línea)] de cada `use_container_width=` REAL — por AST, no por texto.

    ⚠️ Un comentario de `route_ui` contiene el literal (el de v307, explicando por qué
    `st_folium` lo lleva). Contarlo como uso daría un rojo eterno — y al migrar por
    texto habría reescrito el comentario dejándolo mintiendo. grep ≠ uso.
    """
    out = []
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
        for kw in n.keywords:
            if kw.arg == "use_container_width":
                out.append((nom, kw.value.lineno))
    return out


print("== 1) la sonda SABE ver el caso roto ==")
check("detecta un uso en un elemento de Streamlit",
      usos('st.button("x", use_container_width=True)\n'), [("button", 1)])
check("un COMENTARIO con el literal no cuenta",
      usos('# use_container_width=True\nx = 1\n'), [])

print("\n== 2) el repo ==")
ficheros = sorted(BASE.glob("core/*.py")) + [BASE / "app.py"]
todos = []
for p in ficheros:
    for nom, ln in usos(io.open(p, encoding="utf-8").read()):
        todos.append((p.name, ln, nom))
malos = [t for t in todos if t[2] not in TERCEROS]
print(f"         {len(todos)} usos vivos · {len(malos)} en elementos de Streamlit")
check("ningún elemento de Streamlit lo usa ya", malos, [])
check("y los que quedan son de terceros (que sí lo necesitan)",
      sorted({t[2] for t in todos}), ["st_folium"])

print("\n== 3) se cambió por `width=`, y el elemento lo acepta ==")
import inspect                                                    # noqa: E402
import streamlit as st                                            # noqa: E402
_elems = set()
for p in ficheros:
    for n in ast.walk(ast.parse(io.open(p, encoding="utf-8").read())):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
        for kw in n.keywords:
            if kw.arg == "width" and getattr(kw.value, "value", None) == "stretch":
                _elems.add(nom)
check("hay `width=\"stretch\"` que revisar (si no, el test pasa en vacío)",
      len(_elems) > 0, True)
print(f"         elementos: {sorted(_elems)}")
_no = [e for e in _elems
       if getattr(st, e, None) is not None
       and "width" not in inspect.signature(getattr(st, e)).parameters]
check("todos los elementos aceptan `width`", _no, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
