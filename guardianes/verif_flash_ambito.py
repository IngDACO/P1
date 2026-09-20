"""¿Cada uso de `flash.X` tiene el módulo importado EN SU ÁMBITO?

⚠️ La lección de v342, repetida hoy: un import LOCAL dentro de otra función hace creer
que el módulo está disponible. Comprobar la PRESENCIA del texto da un OK falso; hay que
comprobar el ÁMBITO — módulo, o la propia función (o alguna que la contenga).
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

fallos, ok_usos = [], 0


def importa_flash(cuerpo):
    """¿Este bloque de sentencias importa `flash` directamente?"""
    for n in cuerpo:
        if isinstance(n, ast.ImportFrom) and n.module == "core":
            if any(a.name == "flash" for a in n.names):
                return True
        if isinstance(n, ast.Import):
            if any(a.name in ("flash", "core.flash") for a in n.names):
                return True
        # ⚠️ Se desciende a if/try del PROPIO bloque, pero NUNCA dentro de un `def`:
        #    un import local de otra función no está en este ámbito. Descender ahí es
        #    justo el error de v342 — y lo cometí otra vez en la primera versión de
        #    este chequeo, que por eso dio «✓ todos bien» con 5 NameError delante.
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for campo in ("body", "orelse", "finalbody"):
            sub = getattr(n, campo, None)
            if isinstance(sub, list) and sub and importa_flash(sub):
                return True
        for h in getattr(n, "handlers", []) or []:
            if importa_flash(h.body):
                return True
    return False


for f in sorted(CORE.glob("*.py")):
    if f.name == "flash.py":
        continue
    arbol = ast.parse(f.read_text(encoding="utf-8"))
    nivel_modulo = importa_flash(arbol.body)

    # mapa: función → ¿importa flash?  y quién la contiene
    padre = {}
    for n in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(n):
            padre[hijo] = n

    for n in ast.walk(arbol):
        if not (isinstance(n, ast.Attribute) and getattr(n.value, "id", "") == "flash"):
            continue
        # ¿en qué función vive este uso?
        cur, disponible = n, nivel_modulo
        cadena = []
        while cur in padre and not disponible:
            cur = padre[cur]
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cadena.append(cur.name)
                if importa_flash(cur.body):
                    disponible = True
        if disponible:
            ok_usos += 1
        else:
            fallos.append(f"{f.name}:{n.lineno}  flash.{n.attr} en {cadena or ['<módulo>']} "
                          f"→ ⚠️ NameError: nadie importa flash en su ámbito")

print(f"== usos de flash con el módulo disponible: {ok_usos} ==")
if fallos:
    print(f"\n== ‼️ USOS SIN IMPORT ({len(fallos)}) ==")
    for x in fallos:
        print("  ", x)
    sys.exit(1)
print("   ✓ todos los usos tienen `flash` en su ámbito")
