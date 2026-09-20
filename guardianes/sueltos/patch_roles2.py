# -*- coding: utf-8 -*-
"""Los roles viejos que entran por un HELPER, no por un dict literal.

⚠️ El primer barrido solo miraba diccionarios y se dejo estos 12: `como("propietario")`
pasa el rol como ARGUMENTO. Y mi detector de helpers empezo dando **0** porque filtraba
con `'"auth"'` (comillas dobles) sobre `ast.unparse`, que las escribe SIMPLES — la
sonda fallando por el FORMATO, el error de v459 otra vez. Es la leccion de siempre: un
barrido ve solo la forma que se le enseño.
"""
import ast
import io
import pathlib

MAPA = {"propietario": "owner", "administrador": "administrator",
        "campo": "field", "conductor": "field"}
tot = 0

for p in sorted(pathlib.Path(".").glob("*.py")):
    if not p.name.startswith(("verif_", "check_")):
        continue
    src = p.read_text(encoding="utf-8")
    try:
        arb = ast.parse(src)
    except SyntaxError:
        continue
    setters = {f.name for f in ast.walk(arb)
               if isinstance(f, ast.FunctionDef) and "session_state" in ast.unparse(f)
               and "auth" in ast.unparse(f)}
    puntos = [(n.args[0].lineno, n.args[0].col_offset, n.args[0].value,
               MAPA[n.args[0].value])
              for n in ast.walk(arb)
              if isinstance(n, ast.Call) and getattr(n.func, "id", "") in setters
              and n.args and isinstance(n.args[0], ast.Constant)
              and n.args[0].value in MAPA]
    if not puntos:
        continue
    lineas = src.split("\n")
    for ln, col, viejo, nuevo in sorted(puntos, reverse=True):
        b = lineas[ln - 1].encode("utf-8")          # col_offset va en BYTES (v468)
        trozo = b[col:].decode("utf-8", "replace")
        if not (trozo.startswith('"%s"' % viejo) or trozo.startswith("'%s'" % viejo)):
            raise SystemExit("%s:%d literal fuera de sitio: %r" % (p.name, ln, trozo[:20]))
        q = trozo[0]
        lineas[ln - 1] = (b[:col].decode("utf-8", "replace")
                          + q + nuevo + q + trozo[len(viejo) + 2:])
    nueva = "\n".join(lineas)
    ast.parse(nueva)
    p.write_text(nueva, encoding="utf-8", newline="")
    tot += len(puntos)
    print("   %-26s %d llamada(s)" % (p.name, len(puntos)))

print("\n%d llamadas actualizadas" % tot)
