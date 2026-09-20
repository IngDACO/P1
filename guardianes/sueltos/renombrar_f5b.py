# -*- coding: utf-8 -*-
"""F5b, paso 0: renombrar las locales que TAPARÍAN el motor.

⚠️ Esto va ANTES de traducir, no después. Python marca el nombre local en el ÁMBITO
ENTERO de la función, así que un `t = totales(...)` al principio convierte cualquier
`t("…")` de más arriba o más abajo en un `TypeError`/`UnboundLocalError` que ni
`compileall` ni el import detectan — solo se ve ejecutando la pantalla (v437, v439,
v440: tres veces el mismo fallo, las tres por traducir primero y mirar después).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    # quotes.py — `t` es el dict de totales en 4 funciones
    ("core/quotes.py", "    t = totales(lineas, impuesto_pct)", "    _tot = totales(lineas, impuesto_pct)"),
    ("core/quotes.py", "    t = totales(lineas, imp)", "    _tot = totales(lineas, imp)"),
    ("core/quotes.py", '    t = totales(lineas, _num(c.get("ImpuestoPct")))',
     '    _tot = totales(lineas, _num(c.get("ImpuestoPct")))'),
    ("core/quotes.py", '    t = totales(lineas_de(c), _num(c.get("ImpuestoPct")))',
     '    _tot = totales(lineas_de(c), _num(c.get("ImpuestoPct")))'),
    # projects.py — `t` es el factor de interpolación
    ("core/projects.py",
     "                t = (dia - x0) / (x1 - x0) if x1 != x0 else 0\n"
     "                return y0 + (y1 - y0) * t",
     "                _f = (dia - x0) / (x1 - x0) if x1 != x0 else 0\n"
     "                return y0 + (y1 - y0) * _f"),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    n = src.count(viejo)
    if n != 1:
        print(f"  ⚠️ {rel}: {n} coincidencias de {viejo.strip()[:44]!r} — NO se toca")
        continue
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo.strip()[:52]}")
