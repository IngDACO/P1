# -*- coding: utf-8 -*-
"""v423 CADUCADO por v481: el bloque de costos cambió de función, no de comportamiento.

v423 protege que una LOCALIZACIÓN interna no vea «Costará al terminar», «Presupuesto» ni
el titular de obra — cosas que no le aplican. Ese código se extrajo de `render_expenses`
a `_costos_section` en v481 (para que el campo no lo vea), así que el guardián miraba una
función donde ya no está.

⚠️ No se relaja: se apunta a donde vive ahora **y se le añade lo que antes no podía
comprobar** — que ese bloque cuelgue de `ver_costos`, o sea que la protección de v423 y
la de v481 queden atadas: si alguien devuelve el bloque a `render_expenses` sin guarda,
salta aquí.
"""
import ast
import io

P = "verif_v423.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''_re = fn(PU, "render_expenses")
_esint_re = [n for n in ast.walk(_re) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "es_interno"]
chk("`render_expenses` distingue las internas", len(_esint_re) >= 1)
'''

NUEVO = '''# ⚠️ CADUCADO por v481 y REAPUNTADO: el bloque de costos se extrajo de
# `render_expenses` a `_costos_section` para que el CAMPO no lo vea. El código es el
# mismo y el comportamiento también; solo cambió de función.
_re = fn(PU, "_costos_section")
_esint_re = [n for n in ast.walk(_re) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "es_interno"]
chk("el bloque de costos distingue las internas", len(_esint_re) >= 1)
# ⚠️ Y lo que v423 no podía comprobar hasta ahora: que ese bloque sea justo el que el
# campo NO ve. Así la protección de v423 queda atada a la de v481 — si alguien devuelve
# el bloque a `render_expenses` sin guarda, salta aquí y no dentro de tres versiones.
_rx = fn(PU, "render_expenses")
_guardas = [ast.unparse(n.test) for n in ast.walk(_rx)
            if isinstance(n, ast.If) and "_costos_section" in ast.unparse(n)]
chk("...y ese bloque cuelga de `ver_costos` (v481)", _guardas == ["ver_costos"])
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v423.py: reapuntado a _costos_section + atado a ver_costos")
