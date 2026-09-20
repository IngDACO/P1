# -*- coding: utf-8 -*-
"""F5c, paso 0b: los USOS que el renombrado dejó colgando.

⚠️ Renombrar es DOS pasos y esta es la segunda vez que lo olvido en dos versiones.
En `payroll.neto` el uso colgante era `elif t == "deduccion"`, y eso no habría dado
un NameError inocuo: con `t` importado como la función de idioma, la comparación es
siempre **False** y **las deducciones dejarían de restarse del neto a pagar**. Un
fallo de dinero, silencioso, en la función que calcula lo que cobra cada persona.

Por eso al final se comprueba por AST que no queda NINGÚN `Name`/`arg` llamado `t`
en los ficheros tocados.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

PLAN = {
    "core/payroll.py": [('        elif t == "deduccion":', '        elif _tp == "deduccion":', 1)],
    "core/finance.py": [
        ('            elif t == "aporte":', '            elif _tp == "aporte":', 1),
        ('        interno += h.get("interno", 0.0) * t\n'
         '        _d = (h["proyecto"] - h["jornada"]) * t',
         '        interno += h.get("interno", 0.0) * _tar\n'
         '        _d = (h["proyecto"] - h["jornada"]) * _tar', 1),
        ('        if t <= 0 and (h["jornada"] > 0 or h["proyecto"] > 0):',
         '        if _tar <= 0 and (h["jornada"] > 0 or h["proyecto"] > 0):', 1),
    ],
    "core/prestart.py": [
        ('    t = "".join(c for c in t if not unicodedata.combining(c))\n'
         '    return " ".join(t.lower().split())',
         '    _s = "".join(c for c in _s if not unicodedata.combining(c))\n'
         '    return " ".join(_s.lower().split())', 1),
    ],
    "core/inventory.py": [
        ('    return f"{t}: {ref}" if ref else (t or "—")',
         '    return f"{_tp}: {ref}" if ref else (_tp or "—")', 1),
    ],
    "core/roster.py": [
        ('    def _h(t):\n'
         '        try:\n'
         '            hh, mm = t.split(":")\n'
         '            return f"{int(hh)}:{mm}"\n'
         '        except Exception:\n'
         '            return t',
         '    def _h(_v):\n'
         '        try:\n'
         '            hh, mm = _v.split(":")\n'
         '            return f"{int(hh)}:{mm}"\n'
         '        except Exception:\n'
         '            return _v', 1),
    ],
    "core/credentials.py": [
        ('        for t in tipos:\n'
         '            mias = [c for c in creds\n'
         '                    if str(c.get("Usuario", "")) == u.get("Usuario") '
         'and str(c.get("Tipo", "")) == t]\n'
         '            if not mias:\n'
         '                fila[t] = "—"\n'
         '            else:\n'
         '                sts = [status(c.get("Vencimiento")) for c in mias]\n'
         '                fila[t] = ("vencido" if "vencido" in sts',
         '        for _tp in tipos:\n'
         '            mias = [c for c in creds\n'
         '                    if str(c.get("Usuario", "")) == u.get("Usuario") '
         'and str(c.get("Tipo", "")) == _tp]\n'
         '            if not mias:\n'
         '                fila[_tp] = "—"\n'
         '            else:\n'
         '                sts = [status(c.get("Vencimiento")) for c in mias]\n'
         '                fila[_tp] = ("vencido" if "vencido" in sts', 1),
    ],
    "core/manuals.py": [
        ('        for t in d:\n'
         '            tf[t] = tf.get(t, 0) + 1\n'
         '        tf_list.append(tf)\n'
         '        for t in set(d):\n'
         '            df[t] = df.get(t, 0) + 1',
         '        for _tok in d:\n'
         '            tf[_tok] = tf.get(_tok, 0) + 1\n'
         '        tf_list.append(tf)\n'
         '        for _tok in set(d):\n'
         '            df[_tok] = df.get(_tok, 0) + 1', 1),
    ],
}

for rel, cambios in PLAN.items():
    f = R / rel
    src = f.read_text(encoding="utf-8")
    for viejo, nuevo, n_esp in cambios:
        n = src.count(viejo)
        if n != n_esp:
            print(f"  ⚠️ {rel}: {n} de {viejo.splitlines()[0].strip()[:48]!r}")
            continue
        src = src.replace(viejo, nuevo, n_esp)
        print(f"  OK  {rel}: {viejo.splitlines()[0].strip()[:52]}")
    f.write_text(src, encoding="utf-8")

print("\n── comprobación FINAL por AST: ¿queda algún `t` local?")
malo = 0
for rel in list(PLAN) + ["core/manuals.py"]:
    tr = ast.parse((R / rel).read_text(encoding="utf-8"))
    n = sorted({x.lineno for x in ast.walk(tr)
                if (isinstance(x, ast.Name) and x.id == "t")
                or (isinstance(x, ast.arg) and x.arg == "t")})
    if n:
        malo += 1
        print(f"   ⚠️ {rel}: quedan en {n}")
print("   ninguno" if not malo else f"   {malo} fichero(s) con restos")
