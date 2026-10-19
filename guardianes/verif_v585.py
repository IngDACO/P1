"""v585 · LO VISTO VERIFICANDO v584 (decisión del usuario: «ok dale»).

  ⚠️ «Tracking options» abría la lista de obras y «Lines» apuntaba a la tabla del parte, pero
  la vista NO bajaba hasta ellas: la marca de `_bajar_a` iba en un bloque VACÍO, DELANTE de lo
  que abren, así que la vista se paraba en ese bloque (medido en producción: la lista abierta
  a 459 px con 450 de vista; de la tabla, a 417, solo asomaba la cabecera). En Quotes, en
  Catalogue y en el resto, el bloque ENVUELVE lo que se quiere ver → igual aquí.

  El guardián barre TODA la app: cada `_bajar_a(clave, …)` va dentro de
  `with st.container(key=clave)` y ese bloque lleva algo más que la marca. Y, en AppTest, la
  lista y la tabla están DENTRO del bloque al que baja la vista (la sonda, validada con un
  bloque conocido-bueno: las cifras dentro de `cpx_cont_kpis`).

AppTest y el motor con sus fuentes sustituidas: ninguna hoja ni Xero se tocan.
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


# ═════════════════════════════════════════════════════════════════
print("1. ⚠️ Cada `_bajar_a` ENVUELVE lo que se quiere ver (barrido de TODA la app, AST)")


def _clave_container(w):
    """La `key=` constante de un `with st.container(...)`, o None."""
    for it in w.items:
        c = it.context_expr
        if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "container":
            for k in c.keywords:
                if k.arg == "key" and isinstance(k.value, ast.Constant):
                    return k.value.value
    return None


def _es_bajar(n):
    return (isinstance(n, ast.Call)
            and (getattr(n.func, "attr", None) == "_bajar_a" or getattr(n.func, "id", None) == "_bajar_a"))


def malos_bajar(src, nombre="?"):
    """[(sitio, motivo)] de las llamadas a `_bajar_a` que NO envuelven su objetivo, y cuántas
    llamadas se miraron. Regla: el `with` más cercano que la contiene es
    `st.container(key=<la misma clave>)` y su cuerpo lleva algo más que la marca y los
    `import` (vacío, la vista se para en él y lo que abre queda debajo: v584)."""
    arbol = ast.parse(src)
    padre = {}
    for p in ast.walk(arbol):
        for h in ast.iter_child_nodes(p):
            padre[h] = p
    malos, vistos = [], 0
    for n in ast.walk(arbol):
        if not _es_bajar(n):
            continue
        vistos += 1
        sitio = "%s:%d" % (nombre, n.lineno)
        clave = n.args[0].value if n.args and isinstance(n.args[0], ast.Constant) else None
        if clave is None:
            malos.append((sitio, "la clave no es un literal"))
            continue
        w = padre.get(n)
        while w is not None and not isinstance(w, (ast.With, ast.FunctionDef)):
            w = padre.get(w)
        if not isinstance(w, ast.With):
            malos.append((sitio, "no está dentro de ningún `with`"))
            continue
        if _clave_container(w) != clave:
            malos.append((sitio, "el bloque que la contiene no es `st.container(key=%r)`" % clave))
            continue
        resto = [s for s in w.body
                 if not isinstance(s, (ast.Import, ast.ImportFrom))
                 and not (isinstance(s, ast.Expr) and _es_bajar(s.value))]
        if not resto:
            malos.append((sitio, "⚠️ el bloque está VACÍO: no envuelve lo que se quiere ver"))
    return malos, vistos


# La sonda, validada ANTES con los dos casos conocidos (trampa 12)
_V584 = '''
def f():
    with st.container(key="cpx_cont_jobs"):
        _PU._bajar_a("cpx_cont_jobs", "_cont_bajar_jobs")
    with st.expander("Jobs", key="exp"):
        st.code("x")
'''
_BIEN = '''
def f():
    with st.container(key="cpx_cot_tabla"):
        from core import projects_ui as _PU
        _PU._bajar_a("cpx_cot_tabla", "_cot_bajar")
        st.dataframe(1)
'''
_m1, _n1 = malos_bajar(_V584, "v584")
_m2, _n2 = malos_bajar(_BIEN, "bien")
chk("la sonda VE el fallo de v584 (bloque vacío delante) y da por bueno el de Quotes",
    _n1 == 1 and len(_m1) == 1 and "VACÍO" in _m1[0][1] and _n2 == 1 and not _m2, (_m1, _m2))
_m3, _ = malos_bajar(_BIEN.replace('key="cpx_cot_tabla"', 'key="otra"'), "otra")
chk("…y una clave que no es la suya", len(_m3) == 1 and "no es" in _m3[0][1], _m3)

_malos, _vistos, _ficheros = [], 0, set()
for _dir, _, _fs in os.walk(RAIZ):
    if "__pycache__" in _dir or os.sep + "." in _dir:
        continue
    for _f in _fs:
        if _f.endswith(".py"):
            _rel = os.path.relpath(os.path.join(_dir, _f), RAIZ)
            _m, _n = malos_bajar(_src(_rel), _rel)
            _malos += _m
            _vistos += _n
            if _n:
                _ficheros.add(_rel)
# ⚠️ Paso en vacío (trampa 1): hoy son 11 en 5 ficheros; si el barrido no viera ninguna, «0 malos»
# no diría nada
chk("el barrido ve las llamadas de la app (11 hoy, en 5 ficheros)", _vistos >= 11 and len(_ficheros) >= 5,
    (_vistos, sorted(_ficheros)))
chk("⚠️ NINGUNA marca de bajar en un bloque vacío o ajeno (en v584, dos en Accounting)", not _malos, _malos)

_cu = ast.parse(_src(os.path.join("core", "contable_ui.py")))


def _with_de(arbol, clave):
    return next((w for w in ast.walk(arbol) if isinstance(w, ast.With) and _clave_container(w) == clave), None)


def _llamadas(nodo, attr):
    return [n for n in ast.walk(nodo) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == attr]


_wj = _with_de(_cu, "cpx_cont_jobs")
chk("el bloque `cpx_cont_jobs` envuelve el desplegable «Jobs that must exist first»",
    _wj is not None and any("exp_cont_jobs_" in ast.unparse(k.value)
                            for e in _llamadas(_wj, "expander") for k in e.keywords if k.arg == "key"))
_wp = _with_de(_cu, "cpx_cont_ptabla")
chk("el bloque `cpx_cont_ptabla` envuelve la tabla del parte", _wp is not None and _llamadas(_wp, "dataframe"))

# ═════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys, datetime as dt
sys.path.insert(0, r"%s")
import streamlit as st
from core import contable_ui as CU, contable, xero_ui
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
contable.csv_ventas = lambda g, p, d=None, h=None: {"csv": "a", "filas": 1, "documentos": 1,
    "avisos": [], "opciones": ["Job A"]}
contable.csv_compras = lambda g, p, d=None, h=None: {"csv": "b", "filas": 3, "documentos": 2,
    "avisos": [], "opciones": ["Job A"]}
contable.identidad = lambda g: {"abn": "1", "legal": "x", "plazo": 14}
contable.mapa = lambda g: {}
_D = [dt.date(2026, 10, 6), dt.date(2026, 10, 7)]
contable.csv_partes = lambda g, d, h: {"csv": "x", "filas": 1, "personas": 1, "total": 3.5,
    "avisos": [], "dias": _D}
contable.partes = lambda g, d, h: {"dias": _D, "filas": [{"nombre": "Ana", "payroll_id": "",
    "etiqueta": "Ordinary Hours", "horas": {_D[0]: 3.5}, "total": 3.5}], "avisos": []}
xero_ui.render_conexion = lambda g, d=None, h=None: None
xero_ui.render_partes_xero = lambda g: None
CU.render_contable("G")
''' % RAIZ


def _bloque(nodo, clave):
    """El bloque `st.container(key=clave)`: AppTest le pone el id «$$ID-<hash>-<clave>»."""
    if str(getattr(getattr(nodo, "proto", None), "id", "") or "").endswith("-" + clave):
        return nodo
    for h in (getattr(nodo, "children", None) or {}).values():
        b = _bloque(h, clave)
        if b is not None:
            return b
    return None


def _descend(nodo):
    yield nodo
    for h in (getattr(nodo, "children", None) or {}).values():
        yield from _descend(h)


def _tiene(nodo, cond):
    return nodo is not None and any(cond(d) for d in _descend(nodo))


def _es_lista(d):
    return type(d).__name__ in ("Expander", "Status") and "Jobs that must exist first" in str(d.label)


def _es_parte(d):
    return type(d).__name__ == "Dataframe" and "Employee" in list(d.value.columns)


def _es_marca(clave):
    return lambda d: str(getattr(getattr(d, "proto", None), "id", "") or "").endswith("-ir_" + clave)


print("\n2. En la pantalla (AppTest): lo que se abre está DENTRO del bloque al que baja la vista")
at = AppTest.from_string(CAB, default_timeout=90).run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kp = _bloque(at.main, "cpx_cont_kpis")
chk("la sonda ve un bloque conocido-bueno: las cifras dentro de `cpx_cont_kpis`",
    _tiene(_kp, lambda d: type(d).__name__ == "Button" and d.key == "cpxkpi_cont_seg"))
chk("…y no ve la tabla del parte dentro de él (no da todo por bueno)", not _tiene(_kp, _es_parte))
chk("sin pedirla, ninguna marca de bajar", not _tiene(at.main, _es_marca("cpx_cont_jobs"))
    and not _tiene(at.main, _es_marca("cpx_cont_ptabla")))

at.button(key="cpxkpi_cont_seg").click()
at.run()
_bj = _bloque(at.main, "cpx_cont_jobs")
chk("⚠️ «Tracking options»: la lista abierta está DENTRO del bloque al que baja (en v584, debajo)",
    _tiene(_bj, _es_lista) and any(d.proto.expanded for d in _descend(_bj) if _es_lista(d)),
    [type(d).__name__ for d in _descend(_bj)] if _bj is not None else None)
chk("…con la marca de bajar dentro del mismo bloque", _tiene(_bj, _es_marca("cpx_cont_jobs")))
at.run()
chk("…y baja UNA vez: en la pasada siguiente ya no hay marca (la lista sigue abierta)",
    not _tiene(at.main, _es_marca("cpx_cont_jobs"))
    and any(d.proto.expanded for d in _descend(at.main) if _es_lista(d)))

at = AppTest.from_string(CAB, default_timeout=90).run()
at.button(key="cpxkpi_contp_lin").click()
at.run()
_bp = _bloque(at.main, "cpx_cont_ptabla")
chk("⚠️ «Lines»: la tabla del parte está DENTRO del bloque al que baja (en v584, debajo)",
    _tiene(_bp, _es_parte), [type(d).__name__ for d in _descend(_bp)] if _bp is not None else None)
chk("…con la marca de bajar dentro del mismo bloque", _tiene(_bp, _es_marca("cpx_cont_ptabla")))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
