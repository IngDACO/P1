"""v306: identidad por ID + tipo de proyecto + el ID a la vista.

El chequeo importante no es "compila": es que NINGUN sitio vuelva a indexar
proyectos por NOMBRE (el fallo que colapsa homonimos en silencio) y que el
cronograma solo se genere para instalacion.
"""
import ast
import importlib
import pathlib
import py_compile
import sys

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) la fila de create_project cuadra con la cabecera ==")
from core import projects as P

_src = (BASE / "core" / "projects.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next(n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
           and n.name == "create_project")
_row = next((n.value for n in ast.walk(_fn) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", "") == "row" for t in n.targets)), None)
check("se pudo LEER la fila", isinstance(_row, ast.List), True)
check("nº de valores == nº de columnas", len(_row.elts), len(P.PROJECTS_HEADERS))
check("'Tipo' esta en la cabecera", "Type" in P.PROJECTS_HEADERS)
# v384: la regla es «las columnas NUEVAS van al final», no «Tipo es la última»:
# v360 y v373 añadieron GananciaHoraJSON y GananciaFija después, y también al
# final. Se comprueba el ORDEN relativo, que es lo que hace segura la migración.
check("Tipo va DESPUES de las columnas previas a v306",
      P.PROJECTS_HEADERS.index("Type") > P.PROJECTS_HEADERS.index("LabourMargin"))
# ⚠️ CADUCADO EN v501, REANCLADO — no relajado. Exigia que las de ganancia fueran las
# DOS ULTIMAS y v501 anadio `BaselineJSON` detras, TAMBIEN al final. Es exactamente la
# leccion que ya esta escrita cuatro lineas mas arriba para `Tipo` y que no se aplico
# aqui: lo que hace segura la migracion es el ORDEN RELATIVO —que nada se cuele ANTES de
# las historicas, porque la fila es POSICIONAL (v363)—, no cual sea la ultima.
check("las de ganancia van DESPUES de las columnas previas a v360",
      min(P.PROJECTS_HEADERS.index("HourlyProfitJSON"),
          P.PROJECTS_HEADERS.index("FixedProfit")) > P.PROJECTS_HEADERS.index("Type"))
check("...y siguen juntas y en ese orden",
      P.PROJECTS_HEADERS.index("FixedProfit") - P.PROJECTS_HEADERS.index("HourlyProfitJSON"), 1)
# ⚠️ CADUCADO EN v470, REANCLADO — no relajado. Exigia la lista EXACTA de 4 tipos y
# se puso rojo al añadir «Ripout + Installation» A PROPOSITO: un guardian atado a la
# FORMA caduca cuando la forma cambia (trampa nº16). Lo que la regla de v306 protege no
# es «hay 4 tipos», es que **el tipo decida el cronograma**: antes de v306 un delivery
# nacia con 11 actividades falsas que ensuciaban avance, SPI y el radar. Eso se afirma
# ahora sobre el PRINCIPIO, y el numero se DERIVA del propio codigo.
check("los tipos de v306 siguen todos ahi",
      [t for t in ("Installation", "Delivery", "Ripout", "Other") if t not in P.TIPOS], [])
check("y el tipo sigue DECIDIENDO el cronograma (la razon de ser de v306)",
      [P.genera_cronograma(t) for t in ("Installation", "Delivery", "Ripout", "Other")],
      [True, False, False, False])

print("\n== 2) NADIE indexa proyectos por NOMBRE (el fallo de v147/v150) ==")
# Un dict/comprehension cuya CLAVE sea `...get("Nombre")` sobre proyectos.
_sosp = []
for p in sorted(BASE.rglob("*.py")):
    try:
        arbol = ast.parse(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(arbol):
        _clave = None
        if isinstance(n, ast.DictComp):
            _clave = n.key
        elif isinstance(n, ast.Dict):
            continue                      # dicts literales: no son mapas de proyectos
        if _clave is None:
            continue
        # ⚠️ Se mira SOLO la clave, y se exige que mencione el nombre y NO el ID: una
        # clave `f"{Nombre} ({ID})"` es UNICA y por tanto correcta. Sin este matiz el
        # chequeo marcaba 5 sitios sanos (plan_ui, prestart_ui, tool_save_ui y los dos
        # selectores del propietario) — un guardian que grita en falso se acaba ignorando.
        _txt = ast.dump(_clave)
        if "'Nombre'" not in _txt or "'ID'" in _txt:
            continue
        # ¿la fuente iterada son proyectos? (list_projects / proys / prjs)
        _fuente = ast.dump(n)
        if any(k in _fuente for k in ("list_projects", "'proys'", "'prjs'", "'proyectos'")):
            _sosp.append(f"{p.name}:{n.lineno}")
check("se recorrio el repo (no es un barrido vacio)",
      len(list(BASE.rglob('*.py'))) > 40, True)
check("0 mapas de proyectos indexados por nombre", _sosp, [])

print("\n== 3) la etiqueta desempata SOLO cuando hace falta ==")
_p1 = {"ID": "PRJ-0001", "Name": "Torre Norte"}
_p2 = {"ID": "PRJ-0002", "Name": "Torre Sur"}
_d1 = {"ID": "PRJ-0007", "Name": "prueba"}
_d2 = {"ID": "PRJ-0008", "Name": "prueba"}
_e = P.etiqueta_proyectos([_p1, _p2])
check("sin homonimos: solo el nombre", sorted(_e.values()), ["Torre Norte", "Torre Sur"])
_e2 = P.etiqueta_proyectos([_p1, _d1, _d2])
check("con homonimos: LOS DOS llevan su ID",
      sorted(_e2.values()), ["Torre Norte", "prueba (PRJ-0007)", "prueba (PRJ-0008)"])
check("...y ninguna etiqueta se pierde (9 proyectos -> 9 claves)",
      len(P.etiqueta_proyectos([{"ID": f"PRJ-{i:04d}", "Name": "igual"}
                                for i in range(9)])), 9)
check("sin nombre no rompe", P.etiqueta_proyectos([{"ID": "PRJ-1", "Name": ""}]),
      {"PRJ-1": "(no name)"})
# la inversa (etiqueta -> ID), que es como la usan facturas/fichaje, no debe colapsar
_inv = {v: k for k, v in _e2.items()}
check("la inversa etiqueta->ID conserva los 3", len(_inv), 3)

print("\n== 4) el cronograma depende del TIPO ==")
_pu = ast.parse((BASE / "core" / "projects_ui.py").read_text(encoding="utf-8"))
_nf = next(n for n in ast.walk(_pu) if isinstance(n, ast.FunctionDef)
           and n.name == "_nuevo_proyecto_form")
_bs = [n for n in ast.walk(_nf) if isinstance(n, ast.Call)
       and getattr(n.func, "id", "") == "build_schedule"]
check("build_schedule sigue existiendo en el form", len(_bs) >= 1, True)
# la llamada que genera las actividades tiene que estar DENTRO de un if sobre _es_inst
_dentro = 0
for n in ast.walk(_nf):
    if isinstance(n, ast.If) and "_es_inst" in ast.dump(n.test):
        for sub in ast.walk(n):
            if isinstance(sub, ast.Call) and getattr(sub.func, "id", "") == "build_schedule":
                _dentro += 1
check("la generacion del cronograma esta bajo `if _es_inst`", _dentro >= 1, True)
# y el tipo se pasa a create_project
_cp = next(n for n in ast.walk(_nf) if isinstance(n, ast.Call)
           and getattr(n.func, "attr", "") == "create_project")
check("create_project recibe `tipo`", "tipo" in [k.arg for k in _cp.keywords])

print("\n== 5) el ID a la vista ==")
_txt_pu = (BASE / "core" / "projects_ui.py").read_text(encoding="utf-8")
_fl = next(n for n in ast.walk(_pu) if isinstance(n, ast.FunctionDef)
           and n.name == "_cartera_lista")
_claves = [k.value for n in ast.walk(_fl) if isinstance(n, ast.Dict)
           for k in n.keys if isinstance(k, ast.Constant)]
check("la vista Lista tiene columna ID", "ID" in _claves)
check("...y columna Tipo", "Type" in _claves)
check("la busqueda de la cartera incluye el ID", '{_pid}").lower()' in _txt_pu)

print("\n== 6) compila e importa ==")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:80]))
check(f"{len(mods) - len(malos)}/{len(mods)} modulos + app.py", malos, [])

from core import inventory as INV
check("inventory.ubic_ref_label deja el texto viejo tal cual",
      INV.ubic_ref_label("Torre Norte"), "Torre Norte")
check("...y un ID inexistente no rompe", INV.ubic_ref_label("PRJ-9999"), "PRJ-9999")

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
