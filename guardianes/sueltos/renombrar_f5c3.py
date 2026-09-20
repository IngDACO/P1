# -*- coding: utf-8 -*-
"""F5c, paso 0c: los ultimos `t` de manuals.py."""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\manuals.py")

# La comprension de `idf` tiene su PROPIO ambito (no tapa nada), pero se renombra
# igual: dejar un `t` suelto en el modulo es una mina para el proximo que edite ahi.
CAMBIOS = [
    ('idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}',
     'idf = {_tok: math.log(1 + (n - c + 0.5) / (c + 0.5)) for _tok, c in df.items()}'),
    ('        for t in q:\n'
     '            f = tf.get(t, 0)\n'
     '            if not f:\n'
     '                continue\n'
     '            s += idx["idf"].get(t, 0.0) * (f * (k1 + 1)) / '
     '(f + k1 * (1 - b + b * dl / idx["avgdl"]))',
     '        for _tok in q:\n'
     '            f = tf.get(_tok, 0)\n'
     '            if not f:\n'
     '                continue\n'
     '            s += idx["idf"].get(_tok, 0.0) * (f * (k1 + 1)) / '
     '(f + k1 * (1 - b + b * dl / idx["avgdl"]))'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in CAMBIOS:
    n = src.count(viejo)
    assert n == 1, f"{n} de {viejo.splitlines()[0][:50]!r}"
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo.splitlines()[0].strip()[:56]}")
F.write_text(src, encoding="utf-8")

resto = sorted({x.lineno for x in ast.walk(ast.parse(src))
                if (isinstance(x, ast.Name) and x.id == "t")
                or (isinstance(x, ast.arg) and x.arg == "t")})
print(f"\nrestos de `t` en manuals.py: {resto or 'ninguno'}")
assert not resto
