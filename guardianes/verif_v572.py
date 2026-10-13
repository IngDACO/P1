# -*- coding: utf-8 -*-
"""v572 · LO VISTO VERIFICANDO v571: los pies de las cifras del cliente se cortaban.

Medido en producción (13/10/2026, 800 px con el menú): cada tarjeta del resumen del
cliente deja 87 px de pie (12 px, Source Sans) y el kit recorta con «…» lo que no cabe
—a propósito: así la fila mide igual—, de modo que «linked to this client» (97 px) salía
«linked to this c…», y lo mismo «across its proj…», «clocked on its j…», «charged to its j…».
Los pies nuevos miden 52-79 px con la fuente real. AppTest no tiene fuente: aquí se vigila
con una cota de CARACTERES derivada de esa medida (15 caracteres = 79 px el más ancho).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUAR = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


from streamlit.testing.v1 import AppTest                                    # noqa: E402

# El guion de verif_v571, sacado por AST (importarlo lo EJECUTARÍA)
_t = ast.parse(io.open(os.path.join(GUAR, "verif_v571.py"), encoding="utf-8").read())
CAB = next(n.value.value for n in _t.body if isinstance(n, ast.Assign)
           and getattr(n.targets[0], "id", "") == "CAB")
at = AppTest.from_string(CAB, default_timeout=90)
at.run()
chk("la ficha se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_pies = {b.key: b.label.split("\n\n")[2] for b in at.button
         if str(b.key).startswith("cpxkpi_cls_") and b.label.count("\n\n") == 2}
chk("las seis cifras llevan su pie", len(_pies) == 6, _pies)
_largos = {k: v for k, v in _pies.items() if len(v) > 15}
chk("⚠️ ningún pie pasa de 15 caracteres (los 87 px medidos: «linked to this client» se cortaba)",
    not _largos, _largos)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
