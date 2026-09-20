# -*- coding: utf-8 -*-
"""F5c, paso 0: renombrar las locales `t` que taparían el motor.

⚠️ ANTES de traducir. Y ⚠️ renombrar es DOS pasos —la asignación y todos sus usos—:
en v446 el renombrado de `quotes` dejó 16 usos colgando que habrían sido NameError.
Aquí se comprueba con el AST que después NO queda ningún `Name` llamado `t` que no
sea la función.

⚠️ `roster._h(t)` y `credentials.matrix`/`manuals` usan `t` como PARÁMETRO o variable
de un `for` (no de una comprensión), así que sí tapan.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

# (fichero, [(viejo, nuevo, n_esperadas)])
PLAN = {
    "core/payroll.py": [
        ('        t = str(c.get("tipo", "")).lower()\n'
         '        if t == "devengo":',
         '        _tp = str(c.get("tipo", "")).lower()\n'
         '        if _tp == "devengo":', 1),
    ],
    "core/finance.py": [
        ('            t = str(c.get("tipo", "")).lower()\n'
         '            if t == "devengo":',
         '            _tp = str(c.get("tipo", "")).lower()\n'
         '            if _tp == "devengo":', 1),
        ('        t = _num(rates.get(clave, 0))\n'
         '        cargado += h["proyecto"] * t',
         '        _tar = _num(rates.get(clave, 0))\n'
         '        cargado += h["proyecto"] * _tar', 1),
    ],
    "core/prestart.py": [
        ('    t = unicodedata.normalize("NFKD", str(s or ""))',
         '    _s = unicodedata.normalize("NFKD", str(s or ""))', 1),
    ],
    "core/inventory.py": [
        ('    t = str(a.get("UbicacionTipo", "") or "")',
         '    _tp = str(a.get("UbicacionTipo", "") or "")', 1),
    ],
}

for rel, cambios in PLAN.items():
    f = R / rel
    src = f.read_text(encoding="utf-8")
    for viejo, nuevo, n_esp in cambios:
        n = src.count(viejo)
        if n != n_esp:
            print(f"  ⚠️ {rel}: {n} de {viejo.splitlines()[0].strip()[:44]!r}")
            continue
        src = src.replace(viejo, nuevo, n_esp)
        print(f"  OK  {rel}: {viejo.splitlines()[0].strip()[:50]}")
    f.write_text(src, encoding="utf-8")

# ── los usos que quedan colgando, renombrados por ámbito ─────────────────────
RESTO = {
    "core/payroll.py": "_tp",
    "core/finance.py": None,       # se tratan aparte (dos nombres distintos)
    "core/prestart.py": "_s",
    "core/inventory.py": "_tp",
    "core/roster.py": "_v",        # parámetro de `_h`
    "core/credentials.py": "_tp",  # variable de un `for`
    "core/manuals.py": "_tok",     # variable de dos `for`
}
print("\n── usos de `t` que quedan por fichero (Name, cualquier ctx):")
for rel in RESTO:
    tr = ast.parse((R / rel).read_text(encoding="utf-8"))
    n = [x.lineno for x in ast.walk(tr) if isinstance(x, ast.Name) and x.id == "t"]
    a = [x.lineno for x in ast.walk(tr) if isinstance(x, ast.arg) and x.arg == "t"]
    print(f"   {rel:24} Name: {sorted(set(n))}  ·  arg: {sorted(set(a))}")
