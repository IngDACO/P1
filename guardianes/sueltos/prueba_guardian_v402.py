"""¿El guardian nuevo CAZA el fallo que dice vigilar?

Un guardian que solo aprueba el codigo sano no demuestra nada. Aqui se fabrica la
version ROTA (la accion vuelve a colgar de la seleccion, fuera de todo boton) y se
comprueba que la misma logica la marca.
"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\survey_app\core\projects_ui.py"
src = io.open(P, encoding="utf-8").read()

ANCLA = "        from core import theme as _Tb\n"
assert ANCLA in src, "el ancla no existe — el test no probaria nada (paso en vacio)"
roto = src.replace(
    ANCLA,
    '        st.session_state["_admin_open_proj"] = str(proys[_sr[0]].get("ID", ""))\n'
    + ANCLA, 1)


def evalua(texto, etiqueta):
    arb = ast.parse(texto)
    cl = next(n for n in ast.walk(arb)
              if isinstance(n, ast.FunctionDef) and n.name == "_cartera_lista")
    acc = [n for n in ast.walk(cl)
           if (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_ir_a_facturar")
           or (isinstance(n, ast.Constant) and n.value == "_admin_open_proj")]
    bajo = []
    for n in ast.walk(cl):
        if isinstance(n, ast.If) and "button" in (ast.get_source_segment(texto, n.test) or ""):
            bajo += [x for x in ast.walk(n) if x in acc]
    sueltas = [a for a in acc if a not in bajo]
    print(f"  {etiqueta:<6} acciones={len(acc)}  fuera de boton={len(sueltas)}  "
          f"-> {'pasa' if not sueltas else 'LO CAZA'}")
    return bool(sueltas)


print("prueba del guardian de v402:")
sano = evalua(src, "sano")
cazado = evalua(roto, "roto")
ok = (not sano) and cazado
print("\n" + ("TODO OK — aprueba el sano y caza el roto" if ok else "EL GUARDIAN NO SIRVE"))
sys.exit(0 if ok else 1)
