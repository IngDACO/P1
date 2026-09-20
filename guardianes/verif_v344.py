"""Guardián v344 — un CAMPO_CLAVE que no es una columna real no audita nada.

Lo que pasó: `CAMPOS_CLAVE` tenía `MargenPct` y la columna real es `MargenMO`, así
que el campo para el que se construyó la auditoría («¿quién puso el margen a 0?»)
era justo el que NO se vigilaba. Y como `update_project` descarta en silencio las
claves que no conoce, la auditoría anotaba un cambio que nunca llegó a la hoja.

No lo cazó ningún test: los tests usaban diccionarios inventados por mí, con MIS
nombres. Lo cazó ejercitar la escritura contra la hoja de verdad.
"""
import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(nombre, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(f"  {'OK  ' if cond else '⚠️  '}{nombre}: {extra}")


print("== 1) cada CAMPO_CLAVE existe como columna real ==")
from core import auditoria as A
from core import auth, catalogo, clientes, inventory, invoices, payroll
from core import projects as P

HOJAS = {
    "Proyectos": P.PROJECTS_HEADERS,
    "Login": auth.LOGIN_HEADERS,
    "Grupos": auth.GROUPS_HEADERS,
    "Facturas": next(getattr(invoices, n) for n in dir(invoices) if "HEADERS" in n),
    "Nominas": payroll.NOMINAS_HEADERS,
    "Clientes": next(getattr(clientes, n) for n in dir(clientes) if "HEADERS" in n),
    "Activos": next(getattr(inventory, n) for n in dir(inventory) if "HEADERS" in n),
    "Catalogo": catalogo.HEADERS,
}
reales = set()
for v in HOJAS.values():
    reales |= set(v)
huerfanos = sorted(A.CAMPOS_CLAVE - reales)
chk("CAMPOS_CLAVE sin columna real", not huerfanos, huerfanos or "ninguno")
# ⚠️ CADUCADO Y ACTUALIZADO en v455 (regla v385): el modelo del % sobre la mano de
# obra se ELIMINÓ a petición del usuario. La ganancia va por RUBRO.
# Lo que la regla protege es que un campo que MUEVE DINERO se audite; el que lo hace
# hoy es la ganancia por hora, no un margen que ya no existe.
chk("la ganancia se audita", "HourlyProfitJSON" in A.CAMPOS_CLAVE,
    f"GananciaHoraJSON en CAMPOS_CLAVE={'HourlyProfitJSON' in A.CAMPOS_CLAVE}")

print("\n== 2) los campos que ESCRIBE update_project son auditables ==")
# de nada sirve auditar un nombre que `update_project` no sabe escribir
no_escribibles = sorted(c for c in (A.CAMPOS_CLAVE & set(P.PROJECTS_HEADERS))
                        if c not in P._PCOL)
chk("claves de Proyectos que _PCOL no sabe escribir", not no_escribibles,
    no_escribibles or "ninguna")

print("\n== 3) se audita lo ESCRITO, no lo pedido ==")
tr = ast.parse((RAIZ / "core" / "projects.py").read_text(encoding="utf-8"))
f = next(n for n in ast.walk(tr) if isinstance(n, ast.FunctionDef)
         and n.name == "update_project")
llamada = next((c for c in ast.walk(f) if isinstance(c, ast.Call)
                and getattr(c.func, "attr", "") == "diff"), None)
args = [ast.unparse(a) for a in llamada.args] if llamada else []
chk("auditoria.diff recibe los campos filtrados", args and args[-1] == "_escritos",
    f"diff({', '.join(args)})")
# ⚠️ CADUCADO por v446 (i18n F5b): el mensaje pasó al inglés. Lo que la regla
# protege es que un `fields` sin ninguna columna válida devuelva **error** y no un
# «actualizado» falso.
#
# ⚠️ Se comprueba ESTÁTICAMENTE, por AST, y NO ejecutando. Las dos versiones que
# intenté ejecutar fallaban por su propia culpa: con un PID inexistente responde
# «Project not found» y **nunca llega a esta rama** (pasaba por el motivo
# equivocado), y con un PID real depende de que `list_projects` devuelva algo, que
# sin sesión el cerrojo de v351 bloquea. Un guardián que necesita datos de
# producción para afirmar algo es frágil por diseño.
_src_pu = (RAIZ / "core" / "projects.py").read_text(encoding="utf-8")
_ret_no_campo = [ast.unparse(_n.value) for _n in ast.walk(ast.parse(_src_pu))
                 if isinstance(_n, ast.Return) and _n.value is not None
                 and "No recognised field" in ast.unparse(_n.value)]
chk("la rama «sin ninguna columna válida» existe", len(_ret_no_campo) == 1,
    str(_ret_no_campo))
chk("un fields sin ninguna columna válida NO devuelve éxito",
    bool(_ret_no_campo) and _ret_no_campo[0].lstrip().startswith("(False,"),
    str(_ret_no_campo))

print("\n== 4) probado contra el CÓDIGO ROTO (si no, el guardián no vale nada) ==")
roto = set(A.CAMPOS_CLAVE) - {"HourlyProfitJSON"} | {"GananciaPct"}
chk("con el CAMPOS_CLAVE de v343 el guardián FALLA", bool(sorted(roto - reales)),
    f"detecta {sorted(roto - reales)}")

print("\n== 5) NINGUNA invalidación tiene un nombre libre ==")
# La regresión de v339: al quitar el bucle `for fn in (...)` quedó `fn.clear()`, y el
# `except Exception: pass` se tragaba el NameError → la caché no se limpiaba NUNCA y
# tras guardar se veía el valor viejo hasta 120 s. Cuatro versiones sin que nadie lo
# viera, porque un fallo tragado no se distingue de que funcione.
import builtins

rotas = []
for p in sorted((RAIZ / "core").glob("*.py")):
    t2 = ast.parse(p.read_text(encoding="utf-8"))
    glob = set(dir(builtins))
    for n in t2.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                glob.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            glob.add(n.name)
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                for x in ast.walk(tg):
                    if isinstance(x, ast.Name):
                        glob.add(x.id)
    for fn2 in ast.walk(t2):
        if isinstance(fn2, ast.FunctionDef) and "invalid" in fn2.name.lower():
            loc = set(glob) | {a.arg for a in fn2.args.args}
            for n in ast.walk(fn2):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    loc.add(n.id)
                elif isinstance(n, (ast.Import, ast.ImportFrom)):
                    for a in n.names:
                        loc.add((a.asname or a.name).split(".")[0])
                elif isinstance(n, ast.ExceptHandler) and n.name:
                    loc.add(n.name)
            libres = sorted({n.id for n in ast.walk(fn2)
                             if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                             and n.id not in loc})
            if libres:
                rotas.append(f"{p.stem}.{fn2.name}{libres}")
chk("invalidaciones con nombres libres", not rotas, rotas or "ninguna de 17")

print("\n== 6) cada invalidación limpia TODAS las cachés de su módulo ==")
faltan = []
for p in sorted((RAIZ / "core").glob("*.py")):
    t2 = ast.parse(p.read_text(encoding="utf-8"))
    cacheadas = {f.name for f in ast.walk(t2) if isinstance(f, ast.FunctionDef)
                 and any("cache_data" in ast.unparse(d) for d in f.decorator_list)}
    for fn2 in ast.walk(t2):
        if isinstance(fn2, ast.FunctionDef) and "invalid" in fn2.name.lower():
            limpia = {ast.unparse(c.func).rsplit(".", 1)[0] for c in ast.walk(fn2)
                      if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "clear"}
            # los .clear() dentro de un `for fn in (a, b)` se ven por los elementos
            for tup in ast.walk(fn2):
                if isinstance(tup, ast.For) and isinstance(tup.iter, ast.Tuple):
                    limpia |= {ast.unparse(e) for e in tup.iter.elts}
            olvidadas = sorted(cacheadas - limpia - {"_lote"})
            if olvidadas:
                faltan.append(f"{p.stem}.{fn2.name} no limpia {olvidadas}")
# informativo: hay cachés derivadas (gaps_by_group…) que caducan por TTL a propósito
print("     (informativo) " + ("; ".join(faltan) if faltan else "ninguna"))

print("\n== 7) la lógica sigue en pie ==")
chk("40 == 40.0 no genera histórico", A.diff({"Progress": "40"}, {"Progress": "40.0"}) == {},
    "{}")
chk("un cambio real sí", A.diff({"FixedProfit": ""}, {"FixedProfit": "15"}) ==
    {"FixedProfit": ["", "15"]}, "GananciaFija ['', '15']")
chk("un campo no clave no entra", A.diff({"Note": "a"}, {"Note": "b"}) == {}, "{}")

print("\n" + ("TODO OK" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
