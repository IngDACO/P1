"""Aplica un diccionario F5 — las FRASES que el invariante de posición no ve.

    python aplicar_f5.py dic_f5a core/auth_ui.py core/home_ui.py ...

Diferencia con `aplicar.py`: aquel se mueve sobre `piezas()`, que solo recoge lo que es
ARGUMENTO de una función de display. Este se mueve sobre `barre_frases.frases()`, o sea
TODA cadena del módulo que no esté ya envuelta — que es donde viven los trozos de
f-string y las cadenas armadas en una variable (el hueco de v349).

⚠️ Aquí se traduce **EN SITIO, sin envolver en `t()`**: la mitad de estas cadenas no son
un argumento entero (son un trozo de f-string) y envolverlas exigiría reestructurar la
llamada. Es el mismo criterio que F2/F3/F4 ya aplicaron a los trozos de f-string.

Se conservan las dos trampas que costaron una tanda en v440:
  1. `col_offset`/`end_col_offset` son offsets en BYTES UTF-8, no en caracteres.
  2. Si el trozo lleva comillas o no se decide **PARSEÁNDOLO**, no mirando su primer
     carácter (eso ya falló dos veces).
Y no se escribe un fichero que no compile.
"""
import ast
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(r"C:\Users\diego\P1\survey_app")
TRAD = importlib.import_module(sys.argv[1]).TRAD
SECO = "--seco" in sys.argv
RELS = [a for a in sys.argv[2:] if not a.startswith("--")]


def nodos(ruta: Path):
    """Las mismas cadenas que ve `barre_frases`, pero con su POSICIÓN."""
    src = ruta.read_text(encoding="utf-8")
    tr = ast.parse(src)

    envueltos, docs, logs = set(), set(), set()
    for c in ast.walk(tr):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
           and c.func.id in ("t", "d", "_d"):
            for a in c.args:
                for x in ast.walk(a):
                    envueltos.add(id(x))
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
           and isinstance(c.func.value, ast.Name) \
           and c.func.value.id in ("logger", "log", "logging"):
            for a in ast.walk(c):
                logs.add(id(a))
    for n in ast.walk(tr):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))

    out = []
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Constant) and isinstance(x.value, str)):
            continue
        if id(x) in envueltos or id(x) in docs or id(x) in logs:
            continue
        # ⚠️ El barrido reporta el texto con `.strip()`, así que la clave del diccionario
        # NO casa con `x.value` cuando la cadena lleva espacios alrededor — y en un trozo
        # de f-string ese espacio ES la separación entre palabras. Se casa por el texto
        # pelado y se DEVUELVE el espaciado original al sustituir.
        pel = x.value.strip()
        if pel not in TRAD:
            continue
        i = x.value.find(pel)
        out.append({"txt": pel, "full": x.value,
                    "pre": x.value[:i], "post": x.value[i + len(pel):],
                    "lin": x.lineno, "elin": x.end_lineno,
                    "col": x.col_offset, "ecol": x.end_col_offset})
    # de atrás hacia delante: sustituir por posición invalida las posteriores
    out.sort(key=lambda p: (p["lin"], p["col"]), reverse=True)
    return out


def _esc(s, dentro_f):
    s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
    if dentro_f:
        s = s.replace("{", "{{").replace("}", "}}")
    return s


tot_ok, rotos, a_mano = 0, [], []
for rel in RELS:
    p = RAIZ / rel
    src = p.read_text(encoding="utf-8")
    lin = src.splitlines(True)
    ok = 0
    for pz in nodos(p):
        eng = pz["pre"] + TRAD[pz["txt"]] + pz["post"]
        i0, i1 = pz["lin"] - 1, pz["elin"] - 1
        bl0, bl1 = lin[i0].encode("utf-8"), lin[i1].encode("utf-8")
        b0, b1 = bl0[:pz["col"]], bl1[pz["ecol"]:]
        bruto = (bl0[pz["col"]:] if i0 != i1 else bl0[pz["col"]:pz["ecol"]]).decode("utf-8")
        if i0 != i1:
            bruto = bruto + "".join(lin[i0 + 1:i1]) + bl1[:pz["ecol"]].decode("utf-8")
        try:
            nodo = ast.parse("(" + bruto + ")", mode="eval").body
            con_comillas = (isinstance(nodo, ast.JoinedStr)
                            or (isinstance(nodo, ast.Constant)
                                and nodo.value == pz["full"]))   # ⚠️ el COMPLETO, no el pelado
        except SyntaxError:
            con_comillas = False

        if con_comillas:
            q = '"' if '"' not in eng else "'"
            if q == "'" and "'" in eng:
                a_mano.append(f"{rel}:{pz['lin']} {pz['txt'][:50]!r} (comillas de los dos tipos)")
                continue
            nuevo = f"{q}{_esc(eng, False)}{q}"
        else:
            # ⚠️ Un trozo de f-string PARTIDO entre líneas se deja A MANO, igual que en
            # `aplicar.py`: sus comillas de cierre y apertura viven en las líneas
            # intermedias, así que colapsar el rango a una sola línea deja la f-string
            # sin cerrar — es lo que rompió payroll_ui y survey_ui en el primer intento.
            if i0 != i1:
                a_mano.append(f"{rel}:{pz['lin']} {pz['txt'][:50]!r} (f-string en varias líneas)")
                continue
            if '"' in eng or "'" in eng:
                a_mano.append(f"{rel}:{pz['lin']} {pz['txt'][:50]!r} (comilla dentro de f-string)")
                continue
            nuevo = _esc(eng, True)
        lin[i0:i1 + 1] = [b0.decode("utf-8") + nuevo + b1.decode("utf-8")]
        ok += 1

    nueva = "".join(lin)
    try:
        ast.parse(nueva)
    except SyntaxError as e:
        rotos.append(f"{rel}: {e}")
        continue                            # NO se escribe un fichero roto
    if ok and not SECO:
        p.write_text(nueva, encoding="utf-8")
    print(f"  {rel:32} {ok:3} hechas")
    tot_ok += ok

print(f"\n{tot_ok} aplicadas")
if a_mano:
    print(f"{len(a_mano)} A MANO (el aplicador se niega, no adivina):")
    for x in a_mano:
        print("   ", x)
if rotos:
    print("⚠️ NO ESCRITOS (no compilan):")
    for x in rotos:
        print("   ", x)
    sys.exit(1)
