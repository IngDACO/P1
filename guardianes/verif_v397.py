"""v397 · Facturar desde la cartera: columna, badge y botón.

Lo que hay que proteger:
  (a) que `sin_facturar` siga dando EXACTAMENTE lo mismo tras reimplementarla — si
      cambia, se mueve un indicador del resumen financiero (v317) sin que nadie lo pida;
  (b) UNA sola definición del pendiente y UNA sola de «ir a facturar» (v323);
  (c) el mapa por ID, no por nombre (v306), y con archivadas (v369);
  (d) el botón solo donde hay algo que pedir;
  (e) que se EJECUTE (importar no ejecuta, v378).
"""
import ast
import importlib
import io
import pathlib
import py_compile
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

import streamlit as st                                           # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}

from core import invoices as I                                   # noqa: E402
from core import finance as F                                    # noqa: E402
from core import projects as P                                   # noqa: E402

G = "cliente1"
ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) el mapa, sobre un caso CONSTRUIDO ==")
# ⚠️ v474: antes esto leia la demo y salia «SIN DATOS» desde que v456 la vacio — las
# afirmaciones de abajo llevaban versiones sin comprobarse. Ahora el caso se construye
# y la funcion que se ejercita sigue siendo la REAL: solo se sustituyen sus dos
# fuentes (`list_projects` y `pendiente_de_facturar`), que es lo que la demo aportaba.
_FIX = [
    {"ID": "PRJ-T-1", "Nombre": "Obra con pendiente", "Estado": "En progreso"},
    {"ID": "PRJ-T-2", "Nombre": "Obra ya facturada", "Estado": "En progreso"},
    {"ID": "PRJ-T-3", "Nombre": "Obra archivada", "Estado": "Archivado"},
]
_PEND = {"PRJ-T-1": 1200.0, "PRJ-T-2": 0.0, "PRJ-T-3": 340.5}
_lp_orig, _pf_orig = P.list_projects, I.pendiente_de_facturar
P.list_projects = lambda grupo=None, incluir_archivados=False, **k: (
    _FIX if incluir_archivados else [x for x in _FIX if x["Estado"] != "Archivado"])
I.pendiente_de_facturar = lambda pid, grupo="", p=None: _PEND.get(str(pid), 0.0)
try:
    _m = I.pendiente_por_proyecto(G)
    print(f"         {len(_m)} obras con pendiente · {sum(_m.values()):,.2f}")
    check("indexado por ID, no por nombre (v306)",
          sorted(_m), ["PRJ-T-1", "PRJ-T-3"])
    check("la que no debe nada NO entra", "PRJ-T-2" in _m, False)
    check("la ARCHIVADA con pendiente SI entra (v369)", _m.get("PRJ-T-3"), 340.5)
    check("y respeta incluir_archivados=False",
          sorted(I.pendiente_por_proyecto(G, incluir_archivados=False)), ["PRJ-T-1"])

    # ⚠️ La prueba, validada contra roturas: si no cazara ninguna, su verde no diria
    # nada (trampa nº12). Se comprueba que el caso construido DISTINGUE cada fallo.
    print("\n   ¿el caso construido CAZA una agregacion rota?")
    for _nom, _roto in (
            ("indexa por NOMBRE (v306)",
             lambda g=None, incluir_archivados=True, **k: {
                 x["Nombre"]: _PEND[x["ID"]] for x in _FIX if _PEND[x["ID"]] > 0}),
            ("cuela las que no deben nada",
             lambda g=None, incluir_archivados=True, **k: {
                 x["ID"]: _PEND[x["ID"]] for x in _FIX}),
            ("se deja fuera las ARCHIVADAS (v369)",
             lambda g=None, incluir_archivados=True, **k: {
                 x["ID"]: _PEND[x["ID"]] for x in _FIX
                 if _PEND[x["ID"]] > 0 and x["Estado"] != "Archivado"})):
        _r = _roto()
        _caza = not (sorted(_r) == ["PRJ-T-1", "PRJ-T-3"]
                     and "PRJ-T-2" not in _r and _r.get("PRJ-T-3") == 340.5)
        check("   caza: %s" % _nom, _caza, True)
finally:
    P.list_projects, I.pendiente_de_facturar = _lp_orig, _pf_orig

print("\n== 1b) y con la hoja REAL (informativo, no afirma si esta vacia) ==")
_m = I.pendiente_por_proyecto(G)
print(f"         {len(_m)} obras con pendiente · {sum(_m.values()):,.2f}")
if not _m:
    print("         (demo vacía: lo de arriba ya lo afirmo el caso construido)")
check("indexado por ID, no por nombre (v306)",
      all(k.startswith("PRJ-") for k in _m), True)
check("solo entra lo que tiene pendiente > 0",
      all(v > 0 for v in _m.values()), True)
# ⚠️ una a una contra la función de siempre: el mapa no puede inventarse cifras
_dif = []
for p in P.list_projects(G, incluir_archivados=True):
    pid = str(p.get("ID", ""))
    uno = I.pendiente_de_facturar(pid, G, p)
    mapa = _m.get(pid, 0.0)
    if abs(uno - mapa) > 0.005:
        _dif.append((pid, uno, mapa))
if _m:
    check("cada obra cuadra con `pendiente_de_facturar`", _dif, [])
# archivadas dentro (v369): archivar no es no-cobrar
_arch = {str(p.get("ID", "")) for p in P.list_projects(G, incluir_archivados=True)
         if str(p.get("Estado", "")) == "Archivado"}
# ⚠️ Esta afirmación exigía que la DEMO tuviera una obra archivada con pendiente, o
# sea que dependía de la forma de los datos de producción: el día que la demo tuvo una
# obra viva con pendiente y ninguna archivada, salió roja sin que nada estuviera mal.
# La regla YA está probada arriba con un caso CONSTRUIDO y validada contra roturas, así
# que aquí solo se comprueba si de verdad hay una archivada que comprobar.
if _m and _arch:
    check("las ARCHIVADAS con pendiente están en el mapa",
          bool(_arch & set(_m)), True)
elif _m:
    print("         (no hay obras archivadas ahora mismo: lo afirma el caso construido)")

print("\n== 2) ⚠️ `sin_facturar` no cambió de resultado ==")
# se reimplementó para delegar; si mueve una cifra, mueve el indicador del resumen
_ahora = sorted(F.sin_facturar(G))
# ⚠️ La columna es `Name`, no `Nombre`: **v468 renombró las columnas al inglés** y este
# guardián se quedó con el nombre viejo, así que comparaba contra cadenas VACÍAS. No
# saltó antes porque la demo no tenía ninguna obra con pendiente. Es la cuarta vez de
# esa clase (v475 encontró tres): algo migrado en el código y olvidado en lo que lo
# comprueba.
_esperado = sorted(
    (str(p.get("Name", "")), I.pendiente_de_facturar(str(p.get("ID", "")), G, p))
    for p in P.list_projects(G, incluir_archivados=True)
    if I.pendiente_de_facturar(str(p.get("ID", "")), G, p) > 0)
check("mismos nombres e importes que el cálculo directo", _ahora, _esperado)
check("...y sigue ordenado de mayor a menor",
      [v for _n, v in F.sin_facturar(G)] == sorted(
          [v for _n, v in F.sin_facturar(G)], reverse=True), True)

print("\n== 3) UNA sola definición (la lección de v323) ==")
_fin = io.open(BASE / "core" / "finance.py", encoding="utf-8").read()
check("`sin_facturar` delega en el mapa",
      "INV.pendiente_por_proyecto(grupo)" in _fin)
check("...y ya no repite el bucle",
      "INV.pendiente_de_facturar(str(p.get(\"ID\", \"\")), grupo, p)" in _fin, False)
_pui = io.open(BASE / "core" / "projects_ui.py", encoding="utf-8").read()
_arb = ast.parse(_pui)

def _funcs_con(pred):
    """Nombres de las funciones de projects_ui donde se cumple `pred(nodo)`."""
    out = set()
    for f in ast.walk(_arb):
        if isinstance(f, ast.FunctionDef) and any(pred(n) for n in ast.walk(f)):
            out.add(f.name)
    return out


# ⚠️ CADUCADO Y ACTUALIZADO en v402 (regla v385: se reescribe la afirmación, no se
# relaja, y la razón queda aquí). Antes esto fijaba el número de llamadas en 3. Ahora
# son más porque la LISTA también factura — ver abajo. Un número a mano vuelve a
# caducar al siguiente botón; lo que hay que proteger es el PRINCIPIO: que todo sitio
# con un botón «Facturar» delegue en la única función de navegación, en vez de
# rehacerse la preparación del cliente por su cuenta (la lección de v323).
_con_boton = _funcs_con(
    lambda n: isinstance(n, ast.Constant) and isinstance(n.value, str)
    and ("Facturar" in n.value or "Invoice" in n.value)
    and "material/receipt_long" in n.value)
_con_llamada = _funcs_con(
    lambda n: isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_ir_a_facturar")
check("hay botones de facturar que revisar (si no, el test pasa en vacío)",
      len(_con_boton) > 0, True)
check("TODA función con botón «Facturar» delega en `_ir_a_facturar`",
      sorted(_con_boton - _con_llamada), [])
check("la preparación del cliente vive en UN solo sitio",
      _pui.count('st.session_state["_fac_prj_pending"] = str(pid)'), 1)

print("\n== 4) el botón solo donde hay algo que pedir ==")
_cc = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_cartera_clickeable")
_t = ast.get_source_segment(_pui, _cc) or ""
check("condicionado a pendiente > 0 y a rol de gestión",
      "if _pf > 0 and puede_facturar:" in _t)
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
check("...y sin pendiente sigue habiendo «Abrir»",
      'elif st.button("Abrir →"' in _t or 'elif st.button(t("Open →")' in _t)
_cl = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "_cartera_lista")
_tl = ast.get_source_segment(_pui, _cl) or ""
# ⚠️ CADUCADO Y ACTUALIZADO en v402. La afirmación vieja era «la lista NO factura», y era
# la decisión de v397; el usuario la cambió al ver que desde la tabla solo se podía MIRAR
# el dinero. Lo que sigue habiendo que proteger es lo de fondo: que el clic de fila no
# tenga dos significados — o sea que seleccionar NO dispare ninguna acción por sí solo.
# Si `_admin_open_proj` o `_ir_a_facturar` volvieran a colgar de la selección en vez de
# un botón, el botón de facturar no se vería nunca.
_acciones = [n for n in ast.walk(_cl)
             if (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_ir_a_facturar")
             or (isinstance(n, ast.Constant) and n.value == "_admin_open_proj")]
_bajo_boton = []
for _n in ast.walk(_cl):
    if isinstance(_n, ast.If) and "button" in (ast.get_source_segment(_pui, _n.test) or ""):
        _bajo_boton += [x for x in ast.walk(_n) if x in _acciones]
check("hay acciones que revisar en la lista", len(_acciones) > 0, True)
check("ninguna acción cuelga de la SELECCIÓN: todas van bajo un botón",
      [a for a in _acciones if a not in _bajo_boton], [])
# ⚠️ CADUCADO por v440 (i18n F3): la clave de la columna pasó a «Not invoiced».
# Lo que la regla protege es que el importe pendiente viaje como NÚMERO (para que la
# tabla se pueda ordenar por él), no cómo se llame la columna.
check("...pero sí la columna, como NÚMERO (ordenable)",
      ('"Not invoiced": round(' in _tl or '"Sin facturar": round(' in _tl)
      and "NumberColumn" in _tl)

print("\n== 5) EJECUTAR las vistas (importar no ejecuta, v378) ==")
from core import projects_ui as PU                               # noqa: E402
_proys = P.list_projects(G, incluir_archivados=True)
_esc = [("cartera con pendientes", _m),
        ("cartera SIN pendientes (mapa vacío)", {}),
        ("mapa con un pid que ya no existe", {"PRJ-9999": 100.0})]
for _nom, _pend in _esc:
    for _fnom, _fn, _args in (
            ("lista", PU._cartera_lista, (_proys, {}, {}, {}, {})),
            ("tarjetas", PU._cartera_clickeable, (_proys, {}, {}, {}, {}))):
        try:
            # v402: las dos vistas comparten firma — la lista tambien factura
            _fn(*_args, pendientes=_pend, grupo=G, puede_facturar=True)
            check(f"corre {_fnom}: {_nom}", True)
        except Exception as e:
            check(f"corre {_fnom}: {_nom}", f"{type(e).__name__}: {e}", True)
try:
    PU._ir_a_facturar("PRJ-0005", G)
    check("corre `_ir_a_facturar`", st.session_state.get("_fac_prj_pending"), "PRJ-0005")
    check("...y deja la navegación puesta",
          st.session_state.get("_admin_nav_pending"), ("finanzas", "🧾 Facturas"))
except Exception as e:
    check("corre `_ir_a_facturar`", f"{type(e).__name__}: {e}", True)

print("\n== 6) nombres libres, compila e importa ==")
import builtins                                                  # noqa: E402
_B = set(dir(builtins)) | {"__file__"}
_mod = set()
for n in _arb.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        _mod.add(n.name)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            _mod.add((x.asname or x.name).split(".")[0])
    elif isinstance(n, ast.Assign):
        for t in n.targets:
            for s in ast.walk(t):
                if isinstance(s, ast.Name):
                    _mod.add(s.id)
for _f in ("_ir_a_facturar", "_cartera_lista", "_cartera_clickeable",
           "_facturar_atajo", "_detalle_proyecto", "_panel_proyectos"):
    _node = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
                 and n.name == _f)
    asign, usados = set(_mod) | _B, []
    for n in ast.walk(_node):
        if isinstance(n, ast.arg):
            asign.add(n.arg)
        elif isinstance(n, ast.Name):
            (asign.add(n.id) if isinstance(n.ctx, ast.Store) else usados.append(n.id))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                asign.add((x.asname or x.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            asign.add(n.name)
        elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
            asign.add(getattr(n, "name", ""))
            for x in getattr(n.args, "args", []):
                asign.add(x.arg)
        elif isinstance(n, ast.comprehension):
            for s in ast.walk(n.target):
                if isinstance(s, ast.Name):
                    asign.add(s.id)
    check(f"{_f} sin nombres libres",
          sorted({u for u in usados if u not in asign}), [])

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

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
