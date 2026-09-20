"""Guardianes v322 — limpieza + los archivados en las agrupaciones.

1) Nada muerto: las 8 funciones borradas no vuelven, 0 imports sin usar.
2) 0 nombres libres REALES (contando cierres a cualquier profundidad).
3) ⚠️ EL IMPORTANTE: consultar los MIEMBROS de una agrupación tiene que incluir
   los archivados. Hay DOS formas de escribir esa consulta y el guardián de la
   primera versión solo veía una:
     a) `list_projects(..., agrupacion_id=gid)`
     b) filtrar a mano: `[p for p in <lista> if p["AgrupacionID"] == aid]`
   La (b) se me escapó y dejó la tarjeta de agrupación contando distinto que
   `grouping_progress`. Se prueba contra el código ROTO, no solo contra el sano.
"""
import ast
import builtins
import importlib
import io
import pathlib
import py_compile
import sys
import tokenize

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(BASE))
OK = True


def _fuentes():
    for p in sorted(BASE.rglob("*.py")):
        if "scratchpad" not in str(p):
            yield p


# ── 1) nada muerto ────────────────────────────────────────────────
MUERTAS = ["_agrupaciones_html", "_placeholder", "asignacion_dia", "semana_str",
           "available", "costo_empleador", "hay_datos", "hay_plano"]
print("== 1) las 8 funciones muertas no vuelven, ni por referencia ==")
mal = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(a):
        nom = (n.name if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               else n.id if isinstance(n, ast.Name)
               else n.attr if isinstance(n, ast.Attribute) else None)
        if nom in MUERTAS:
            mal.append(f"{p.name}:{n.lineno} {nom}")
print(f"   {len(mal)} problema(s)")
OK &= not mal

print("\n== imports sin usar ==")
sobra = []
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    usados = set()
    for n in ast.walk(a):
        if isinstance(n, ast.Name):
            usados.add(n.id)
        elif isinstance(n, ast.Attribute):
            v = n
            while isinstance(v, ast.Attribute):
                v = v.value
            if isinstance(v, ast.Name):
                usados.add(v.id)
    for n in ast.walk(a):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                if al.name != "*" and (al.asname or al.name).split(".")[0] not in usados:
                    sobra.append(f"{p.name}:{n.lineno} {al.name}")
print(f"   {len(sobra)} sin usar")
OK &= not sobra


# ── 2) nombres libres, CON cierres a cualquier profundidad ────────
def _asignados(fn):
    out = set()
    ar = fn.args
    for x in ar.args + ar.kwonlyargs + getattr(ar, "posonlyargs", []):
        out.add(x.arg)
    for x in (ar.vararg, ar.kwarg):
        if x:
            out.add(x.arg)
    pila = list(fn.body)
    while pila:
        n = pila.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            continue                      # otro ámbito
        if isinstance(n, ast.Lambda):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                out.add((x.asname or x.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        pila.extend(ast.iter_child_nodes(n))
    return out


def _usados(fn):
    out, pila = [], list(fn.body)
    while pila:
        n = pila.pop()
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            out.append(n.id)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        pila.extend(ast.iter_child_nodes(n))
    return out


print("\n== 2) nombres libres reales (cierres incluidos) ==")
libres = 0
for p in _fuentes():
    a = ast.parse(p.read_text(encoding="utf-8"))
    mod = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    for n in a.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            mod.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                mod.add((x.asname or x.name).split(".")[0])
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in ([n.target] if isinstance(n, ast.AnnAssign) else n.targets):
                for s in ast.walk(t):
                    if isinstance(s, ast.Name):
                        mod.add(s.id)
        elif isinstance(n, ast.Try):
            for s in ast.walk(n):
                if isinstance(s, (ast.Import, ast.ImportFrom)):
                    for x in s.names:
                        mod.add((x.asname or x.name).split(".")[0])

    def visita(fn, alcance):
        global libres
        mio = alcance | _asignados(fn)
        falta = sorted({u for u in _usados(fn) if u not in mio})
        if falta:
            libres += len(falta)
            print(f"   {p.name}::{fn.name} → {falta}")
        for h in ast.iter_child_nodes(fn):        # ⚠️ HIJOS, no walk: el nieto
            for x in ast.walk(h):                 # necesita el ámbito del hijo
                if isinstance(x, ast.FunctionDef):
                    visita(x, mio)
                    break

    for f in [n for n in a.body if isinstance(n, ast.FunctionDef)]:
        visita(f, mod)
print(f"   {libres} nombre(s) libre(s)")
OK &= (libres == 0)


# ── 3) el guardián de los archivados en agrupaciones ──────────────
def miembros_sin_archivados(src, nombre="<x>"):
    """Consultas de MIEMBROS de una agrupación que excluyen los archivados."""
    a = ast.parse(src)
    malos = []
    for n in ast.walk(a):                                   # forma (a): el kwarg
        if isinstance(n, ast.Call):
            f = n.func
            nom = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if nom == "list_projects":
                kw = {k.arg for k in n.keywords}
                if "agrupacion_id" in kw and "incluir_archivados" not in kw:
                    malos.append(f"{nombre}:{n.lineno} kwarg")
    for n in ast.walk(a):                                   # forma (b): a mano
        if not isinstance(n, ast.Compare) or "AgrupacionID" not in ast.unparse(n):
            continue
        comp = next((c for c in ast.walk(a) if isinstance(c, ast.comprehension)
                     and any(n is x for x in c.ifs)), None)
        if comp is None:
            continue
        fuente = ast.unparse(comp.iter)
        if "list_projects" in fuente:
            if "incluir_archivados" not in fuente:
                malos.append(f"{nombre}:{n.lineno} inline")
        else:                                               # la lista es una variable
            for x in ast.walk(a):
                if isinstance(x, ast.Assign) and ast.unparse(x.targets[0]) == fuente:
                    v = ast.unparse(x.value)
                    if "list_projects" in v and "incluir_archivados" not in v:
                        malos.append(f"{nombre}:{x.lineno} via {fuente}")
    return malos


print("\n== 3) miembros de agrupación: SIEMPRE con archivados ==")
inc = []
for p in _fuentes():
    inc += miembros_sin_archivados(p.read_text(encoding="utf-8"), p.name)
print(f"   incumplen: {len(inc)} {inc}")
OK &= not inc

print("\n== 3b) …y el guardián CAZA el código roto (no solo aprueba el sano) ==")
ROTO = [
    ("kwarg",  "for p in list_projects(grupo=g, agrupacion_id=gid):\n    pass\n"),
    ("inline", "m=[p for p in P.list_projects(grupo=g) if str(p.get('AgrupacionID',''))==aid]\n"),
    ("var",    "proys_all = P.list_projects(grupo=g)\n"
               "m=[p for p in proys_all if str(p.get('AgrupacionID',''))==aid]\n"),
]
for etq, src in ROTO:
    caza = bool(miembros_sin_archivados(src, etq))
    print(f"   {etq:<7} → {'CAZADO' if caza else 'SE ESCAPA'}")
    OK &= caza
SANO = ("proys_all = P.list_projects(grupo=g, incluir_archivados=True)\n"
        "m=[p for p in proys_all if str(p.get('AgrupacionID',''))==aid]\n")
falso = miembros_sin_archivados(SANO, "sano")
print(f"   sano    → {'FALSO POSITIVO' if falso else 'no grita'}")
OK &= not falso


# ── 4) el editor de miembros no puede desagrupar un archivado ─────
print("\n== 4) guardar los miembros NO desagrupa a un archivado ==")
src = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
tiene_fix = "_falta" in src and "_miembros_editor(nom_ags, todos + _falta" in src
print(f"   el editor añade los miembros archivados que faltan: {tiene_fix}")
OK &= tiene_fix


# ── 5) compila e importa ──────────────────────────────────────────
print("\n== 5) compila e importa ==")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
fallos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        fallos.append((p.stem, repr(e)[:80]))
print(f"   {len(mods) - len(fallos)}/{len(mods)} módulos + app.py")
OK &= not fallos

print("\n" + ("TODO OK" if OK else "HAY FALLOS"))
sys.exit(0 if OK else 1)
