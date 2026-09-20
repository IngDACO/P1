# -*- coding: utf-8 -*-
"""El chequeo de «lee sin canonizar» pasa de TEXTO a ESTRUCTURA.

⚠️ Exigia que la palabra `canonizar` apareciera **en la misma linea** que
`get_all_records`. Eso falla en las dos direcciones:
  · FALSO POSITIVO — una llamada envuelta en dos lineas (que es lo normal cuando la
    linea se pasa de largo) sale denunciada estando bien. Es lo que acaba de pasar.
  · FALSO NEGATIVO — la palabra en un comentario al final de la linea lo aprueba,
    que es la trampa nº2 (*grep != uso*) de siempre.
La pregunta real es estructural: **¿el resultado de esa lectura pasa por
`canonizar`?** Eso se responde en el arbol, no contando subcadenas.
"""
import ast
import io

P = "verif_v468.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = ('sin = []\n'
         'for p in sorted(Path("core").glob("*.py")):\n'
         '    if p.name in ("hojas.py", "columnas.py"):\n'
         '        continue\n'
         '    t = p.read_text(encoding="utf-8")\n'
         '    if "get_all_records" in t:\n'
         '        for ln, linea in enumerate(t.split("\\n"), 1):\n'
         '            if "get_all_records" in linea and "canonizar" not in linea:\n'
         '                sin.append("%s:%s" % (p.name, ln))\n')

NUEVO = '''def _sin_canonizar(arbol):
    """Lecturas `get_all_records(...)` cuyo resultado NO pasa por `canonizar`.

    ⚠️ Estructural a proposito: mirar si la palabra `canonizar` esta en la misma
    linea daba un FALSO POSITIVO con la llamada partida en dos (lo normal cuando se
    pasa de ancho) y un FALSO NEGATIVO si la palabra aparecia en un comentario.
    """
    envueltas = set()
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
        if nom != "canonizar":
            continue
        for dentro in ast.walk(n):
            if (isinstance(dentro, ast.Call)
                    and getattr(dentro.func, "attr", "") == "get_all_records"):
                envueltas.add(id(dentro))
    return [n.lineno for n in ast.walk(arbol)
            if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "get_all_records"
            and id(n) not in envueltas]


# ⚠️ La sonda, validada contra los dos casos conocidos ANTES de creerse su cero
# (trampa nº12): si no viera la lectura cruda, su «0» no significaria nada.
_MALA = ast.parse("r = ws.get_all_records(numericise_ignore=['all'])")
_BUENA = ast.parse("r = columnas.canonizar(\\n    ws.get_all_records(numericise_ignore=['all']))")
if not (_sin_canonizar(_MALA) and not _sin_canonizar(_BUENA)):
    fallo("la sonda de canonizacion NO distingue: su cero no diria nada")
else:
    ok("la sonda ve la lectura cruda y no marca la envuelta (aunque vaya en 2 lineas)")

sin = []
for p in sorted(Path("core").glob("*.py")):
    if p.name in ("hojas.py", "columnas.py"):
        continue
    try:
        _a = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for _ln in _sin_canonizar(_a):
        sin.append("%s:%s" % (p.name, _ln))
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v468.py: el chequeo de canonizacion es estructural y se auto-valida")
