# -*- coding: utf-8 -*-
"""Lectura FUERTE de las anclas de las baterías (v575). Módulo auxiliar: lo usa
`check_anclas_roturas.py`; la suite no lo corre por sí solo (no empieza por verif_/check_).

Hasta v574 el comprobador decía «viva» a una rotura si CUALQUIERA de sus cadenas aparecía en
el fichero que nombra. Tres huecos, los tres vistos en v569-v574:
  · el ancla muerta pasaba por viva si la cadena de REEMPLAZO sí estaba en el código
    (romper_v442: «P.ESTADOS_MANUAL,» estaba; su ancla, no);
  · solo se miraban listas llamadas ROTURAS/CONTROL (romper_v430 y v436 las llaman CASOS:
    nunca se revisaron, y tenían 9 muertas);
  · 52 «ilegibles» no se evaluaban (dos de ellas muertas: romper_v449 y v483).

Aquí el ANCLA se identifica por su POSICIÓN, la que le da la propia batería: los nombres
con que su bucle desempaqueta cada tupla (`for desc, rel, viejo, nuevo in ROTURAS`), la
función a la que la pasa entera (`prueba(*r)` → `def prueba(desc, fich, viejo, nuevo…)`),
o la lista de pares (`cambios`). Y se EVALÚA sin ejecutar la batería: solo sus
asignaciones PURAS de nivel de módulo (literales, `chr`, `.join`, `%`, rutas).
"""
import ast
from pathlib import Path

GUAR = Path(__file__).parent
APP = Path(r"C:\Users\diego\P1\survey_app")
ANCLA = {"viejo", "a", "old", "ancla"}
PARES = {"cambios", "pares"}
FICH = {"rel", "fich", "fichero", "mod"}
_OK_CALL = {"chr", "str", "len", "Path", "join", "normpath", "replace", "format", "abspath",
            "dirname", "with_name", "strip", "lstrip", "rstrip", "upper", "lower"}
_OK_MOD = {"os", "io", "sys", "re", "pathlib", "ast", "json"}


def _puro(nodo):
    for x in ast.walk(nodo):
        if isinstance(x, ast.Call):
            f = x.func
            nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if nm not in _OK_CALL:
                return False
        if isinstance(x, ast.Lambda):
            return False
    return True


def entorno(arbol, ruta):
    """Las asignaciones PURAS de nivel de módulo, ejecutadas en un espacio aislado."""
    # ⚠️ `__import__` hace falta para los imports de la lista blanca (sin él, NINGUNO se
    # ejecutaba y `Path`/`os` quedaban sin definir: romper_v437/v438 salían «ilegibles»)
    env = {"__file__": str(ruta), "__name__": "anclas",
           "__builtins__": {"chr": chr, "str": str, "len": len, "__import__": __import__}}
    for n in arbol.body:
        try:
            if isinstance(n, ast.Import) and all(a.name.split(".")[0] in _OK_MOD for a in n.names):
                exec(compile(ast.Module([n], []), "x", "exec"), env)
            elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in _OK_MOD:
                exec(compile(ast.Module([n], []), "x", "exec"), env)
            elif isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and _puro(n.value):
                exec(compile(ast.Module([n], []), "x", "exec"), env)
        except Exception:
            pass
    return env


def _nombres(t):
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, ast.Starred):
        return [getattr(t.value, "id", "?") + "*"]
    if isinstance(t, (ast.Tuple, ast.List)):
        out = []
        for e in t.elts:
            out += _nombres(e)
        return out
    return ["?"]


def _params(arbol, fn):
    d = next((x for x in ast.walk(arbol) if isinstance(x, ast.FunctionDef) and x.name == fn), None)
    return [a.arg for a in d.args.args] if d else None


def forma(arbol, nombre):
    """Los nombres que da la batería a cada posición de las tuplas de la lista `nombre`."""
    for n in ast.walk(arbol):
        if not isinstance(n, ast.For):
            continue
        it = n.iter
        nm = it.id if isinstance(it, ast.Name) else (
            it.args[0].id if isinstance(it, ast.Call) and it.args and isinstance(it.args[0], ast.Name) else (
                it.left.id if isinstance(it, ast.BinOp) and isinstance(it.left, ast.Name) else None))
        if nm != nombre:
            continue
        tg = n.target
        if isinstance(it, ast.Call) and getattr(it.func, "id", "") == "enumerate" and isinstance(tg, ast.Tuple):
            tg = tg.elts[1]
        if not isinstance(tg, ast.Name):
            return _nombres(tg)
        # `for r in ROTURAS:` y dentro `desc, rel, cambios = r[:3]` o `= r`
        for b in ast.walk(n):
            if isinstance(b, ast.Assign) and isinstance(b.targets[0], ast.Tuple) and (
                    (isinstance(b.value, ast.Subscript) and getattr(b.value.value, "id", "") == tg.id)
                    or (isinstance(b.value, ast.Name) and b.value.id == tg.id)):
                return _nombres(b.targets[0])
        # …o la tupla va ENTERA a una función: `prueba(*r)`
        for b in ast.walk(n):
            if isinstance(b, ast.Call) and any(isinstance(a, ast.Starred)
                                               and getattr(a.value, "id", "") == tg.id for a in b.args):
                p = _params(arbol, getattr(b.func, "id", ""))
                if p:
                    return p
    # sin bucle sobre la lista: la función que recibe las tuplas (con un parámetro de ancla)
    for d in ast.walk(arbol):
        if isinstance(d, ast.FunctionDef) and any(a.arg in ANCLA for a in d.args.args):
            return [a.arg for a in d.args.args]
    return None


def _src(rel, env):
    fic = env.get("FICHEROS")
    if isinstance(fic, dict) and rel in fic:
        rel = fic[rel]
    rel = str(rel)
    for c in (Path(rel), APP / rel, APP / "core" / rel, GUAR / rel):
        try:
            if c.is_file():
                return c.read_text(encoding="utf-8").replace("\r\n", "\n"), rel
        except OSError:
            pass
    return None, rel


def _posiciones(nombres, tup):
    """(índice del fichero, índice del ancla, índice de la lista de pares) en `tup`."""
    if nombres and nombres[-1].endswith("*"):
        nombres = nombres + [nombres[-1]] * len(tup)
    nombres = (nombres or [])[:len(tup)]
    i_f = next((i for i, n in enumerate(nombres) if n in FICH), None)
    i_a = next((i for i, n in enumerate(nombres) if n in ANCLA or n.endswith("*")), None)
    i_p = next((i for i, n in enumerate(nombres) if n in PARES), None)
    if i_f is None:
        i_f = next((i for i, v in enumerate(tup) if isinstance(v, str) and v.endswith(".py")), None)
    return i_f, i_a, i_p


def analiza(ruta, fuente=None):
    """{vivas, muertas[], ilegibles[], sin_forma[]} de UNA batería. `fuente` permite
    analizar un texto en memoria (para validar la sonda con un caso conocido-malo)."""
    ruta = Path(ruta)
    arbol = ast.parse(fuente if fuente is not None else ruta.read_text(encoding="utf-8"))
    env = entorno(arbol, ruta)
    out = {"vivas": 0, "muertas": [], "ilegibles": [], "sin_forma": []}
    listas = [n.targets[0].id for n in arbol.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.List)
              and n.targets[0].id not in ("FICHEROS", "GUARDIANES", "PRUEBAS")]
    principal = None
    for L in listas:
        f = forma(arbol, L)
        if f is None:
            continue
        principal = principal or f
        val = env.get(L)
        if val is None:
            out["ilegibles"].append("%s:%s (no se evalúa sin ejecutarla)" % (ruta.name, L))
            continue
        _tuplas(ruta, L, f, val, env, out)
    # CONTROL: una tupla suelta. Su forma NO siempre es la de la lista (romper_v499…v514
    # lo escriben `(fichero, viejo, nuevo)`): el ancla es lo que va DETRÁS del fichero.
    ctl = env.get("CONTROL")
    if isinstance(ctl, tuple):
        _i = next((i for i, v in enumerate(ctl) if isinstance(v, str) and v.endswith(".py")
                   and _src(v, env)[0] is not None), None)
        if _i is not None and _i + 1 < len(ctl):
            _sig = ctl[_i + 1]
            _f = (["?"] * _i + ["rel", "cambios"]) if isinstance(_sig, list) else (["?"] * _i + ["rel", "viejo"])
            _tuplas(ruta, "CONTROL", _f, [ctl], env, out)
        elif principal:
            _tuplas(ruta, "CONTROL", principal, [ctl], env, out)
    if principal is None:
        out["sin_forma"].append("%s (sin forma reconocible)" % ruta.name)
    return out


def _tuplas(ruta, L, f, val, env, out):
    for k, tup in enumerate(val):
        if not isinstance(tup, (tuple, list)):
            continue
        i_f, i_a, i_p = _posiciones(f, tup)
        if i_f is None or (i_a is None and i_p is None) or max(x for x in (i_f, i_a, i_p) if x is not None) >= len(tup):
            out["sin_forma"].append("%s:%s[%d] %s" % (ruta.name, L, k, f))
            continue
        if any(v is None for v in tup):
            continue                     # rotura desactivada a propósito (None literal)
        src, rel = _src(tup[i_f], env)
        if src is None:
            out["sin_forma"].append("%s:%s[%d] fichero %r" % (ruta.name, L, k, tup[i_f]))
            continue
        try:
            anclas = [tup[i_a]] if i_a is not None else [x[0] for x in tup[i_p]]
        except Exception:
            out["ilegibles"].append("%s:%s[%d] pares" % (ruta.name, L, k))
            continue
        for a in anclas:
            if not isinstance(a, str):
                out["ilegibles"].append("%s:%s[%d] ancla no es texto" % (ruta.name, L, k))
            elif src.count(a.replace("\r\n", "\n")) >= 1:
                out["vivas"] += 1
            else:
                out["muertas"].append("%s:%s[%d] %s <- %r" % (ruta.name, L, k, rel, a[:70]))


def todas():
    tot = {"vivas": 0, "muertas": [], "ilegibles": [], "sin_forma": [], "baterias": 0}
    for p in sorted(GUAR.glob("romper_*.py")):
        r = analiza(p)
        tot["baterias"] += 1
        tot["vivas"] += r["vivas"]
        for k in ("muertas", "ilegibles", "sin_forma"):
            tot[k] += r[k]
    return tot


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = todas()
    print("baterías %d · vivas %d" % (r["baterias"], r["vivas"]))
    for k in ("muertas", "ilegibles", "sin_forma"):
        print("\n%s: %d" % (k, len(r[k])))
        for x in r[k]:
            print("   ", x)
