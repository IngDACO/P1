# -*- coding: utf-8 -*-
"""v480 · El recorrido diario del campo en un movil.

Cuatro cambios, todos salidos de MEDIR con sesion de campo a 375x812:
  (1) Fichaje: las acciones ANTES del resumen — las 4 tarjetas ocupaban 230 px
      enseñando 0.00 h y empujaban «Workday» a y=618 y «Project» a y=759 de 812.
  (2) Una sola obra asignada: se abre sola donde se CONSULTA (Mis proyectos,
      Pre-Start) y es un boton EXPLICITO donde se ACTUA (fichar) — v138.
  (3) El plan de la semana y la ruta, DESPUES de la tarea: plegados empujaban la
      tabla de avance a y=676.
  (4) La columna del medio de la barra deja de estar vacia para el campo.

Lo que hay que proteger, que no es «que el codigo este»:
  · que no se haya PERDIDO informacion (priorizar != encoger, v408);
  · que la preseleccion no se cuele donde v138 pide accion explicita;
  · que el contexto siga saliendo en las salidas tempranas — moverlo al final sin
    eso lo habria hecho desaparecer justo para quien no tiene obra;
  · que el chip de la barra se EJECUTE (importar no ejecuta, v378) y diga lo mismo
    que la banda de estado (v323: una sola forma de decir cada cosa).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "campo000",
                            "rol": "field", "grupo": "cliente1"}

fallos = []
n_ok = 0


def ok(m, det=""):
    """⚠️ Acepta el 2º argumento y lo IGNORA: con `ok(m)` a secas el guardian
    revienta justo cuando PASA, y uno que revienta devuelve != 0 SIEMPRE — una tanda
    de roturas saldria «cazada» sin probar nada (v459/v463)."""
    global n_ok
    n_ok += 1
    print("   ok   " + m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO " + m + (" -> %r" % (det,) if det else ""))


def fuente(f):
    return io.open(os.path.join("core", f), encoding="utf-8").read()


SRC_T = fuente("timeclock_ui.py")
SRC_P = fuente("projects_ui.py")
SRC_S = fuente("prestart_ui.py")
SRC_H = fuente("home_ui.py")


def funcion(src, nombre):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n
    return None


# ── 1 ────────────────────────────────────────────────────────────────────────
print("1. Fichaje: la ACCION antes del resumen (medido: 618 -> arriba del pliegue)")
i_acc = SRC_T.index("col_jor, col_prj = st.columns")
i_kpi = SRC_T.index("tarj = [_tarjeta")
(ok if i_acc < i_kpi else fallo)("las dos acciones van antes que las tarjetas")
# ⚠️ Y no se quito NI UNA cifra: esto es priorizar, no encoger (v408). Si alguien
# «arregla» el alto borrando tarjetas, salta aqui.
(ok if SRC_T.count("_tarjeta(t(") == 4 else fallo)(
    "siguen estando las 4 tarjetas", SRC_T.count("_tarjeta(t("))
(ok if "resumen_semana" in SRC_T else fallo)("y el resumen de la semana sigue")
# `_hechos` tiene que existir aunque el roster falle: dentro del try quedaba
# indefinido y el bloque nuevo daria NameError (la clase de fallo de v370/v423).
_fn = funcion(SRC_T, "render_timeclock_tab")
_asig = [n.lineno for n in ast.walk(_fn)
         if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "_hechos"
                                              for x in n.targets)]
_tries = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Try)]
(ok if _asig and _tries and min(_asig) < min(t for t in _tries if t > min(_asig) - 40)
 else fallo)("`_hechos` se crea FUERA del try", (_asig, _tries))

# ── 2 ────────────────────────────────────────────────────────────────────────
print("")
print("2. Una sola obra: se abre sola al CONSULTAR, boton explicito al ACTUAR (v138)")
_fp = funcion(SRC_P, "render_field_projects")
_txt_fp = ast.unparse(_fp)
(ok if "len(idmap) == 1" in _txt_fp else fallo)("Mis proyectos: se abre sola si es una")
(ok if "'fieldproj_sel' not in st.session_state" in _txt_fp else fallo)(
    "...y solo si la persona no eligio ya otra cosa")
# Pre-Start: SOLO para el campo. A admin/propietario `_projects_for` les da las del
# GRUPO, y ahi «una» significaria «la empresa tiene una obra» — el «primero de la
# lista» que evito v139.
_ps = [n for n in ast.walk(ast.parse(SRC_S))
       if isinstance(n, ast.Compare) and "ps_proy" in ast.unparse(n)]
_cond_ps = [ast.unparse(n) for n in ast.walk(ast.parse(SRC_S))
            if isinstance(n, ast.BoolOp) and "len(idmap) == 1" in ast.unparse(n)]
(ok if any("field" in c for c in _cond_ps) else fallo)(
    "Pre-Start: la preseleccion es SOLO del campo", _cond_ps)
# Fichar: NUNCA preseleccion silenciosa — v138 pide una accion que diga a que ficha.
(ok if 'st.session_state["tc_prj_sel"]' not in SRC_T
    and "st.session_state['tc_prj_sel']" not in SRC_T else fallo)(
    "Fichar: NO se preselecciona el desplegable (v138)")
# ⚠️ Se filtra por el TEST, no por el texto del nodo entero: `ast.walk` devuelve
# tambien los `if` de fuera —el texto del hijo esta dentro del padre— y el primero
# que salia era el `if prj:` que envuelve todo. La sonda acusaba al codigo por un
# fallo suyo (trampa n12: una sonda no vale hasta validarla).
_bot = [n for n in ast.walk(funcion(SRC_T, "render_timeclock_tab"))
        if isinstance(n, ast.If) and "tc_prj_solo" in ast.unparse(n)
        and "len(idmap)" in ast.unparse(n.test)]
_cond = ast.unparse(_bot[0].test) if _bot else ""
(ok if _bot else fallo)("Fichar: hay un boton explicito para la obra unica")
(ok if "propios" in _cond and "len(idmap) == 1" in _cond and "_hechos" in _cond
 else fallo)("...y exige que sea SUYA y que el roster no lo haya puesto ya", _cond)

# ── 3 ────────────────────────────────────────────────────────────────────────
print("")
print("3. El contexto va DESPUES de la tarea, y no desaparece en las salidas")
_ctx = [n for n in ast.walk(_fp) if isinstance(n, ast.FunctionDef) and n.name == "_contexto"]
(ok if _ctx else fallo)("el contexto esta recogido en un sitio")
_llam = [n for n in ast.walk(_fp)
         if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_contexto"]
(ok if len(_llam) == 3 else fallo)("se llama en las 3 salidas de la pantalla", len(_llam))
# ⚠️ La comprobacion que de verdad importa: CADA return con mensaje lleva su contexto
# delante. Sin esto, mover los desplegables al final los habria borrado justo para
# quien todavia no tiene obra asignada — el unico caso en que son lo unico que hay.
_malos = []
for n in ast.walk(_fp):
    if not isinstance(n, ast.If):
        continue
    cuerpo = n.body
    if not (cuerpo and isinstance(cuerpo[-1], ast.Return)):
        continue
    _t = ast.unparse(n)
    if "No projects" in _t or "not proys" in _t or "_VACIO" in _t:
        if "_contexto()" not in _t:
            _malos.append(ast.unparse(n.test))
(ok if not _malos else fallo)("cada salida temprana lo pinta antes de irse", _malos)
# La linea «Hoy:» SI se queda arriba: es lo primero que hay que ver por la mañana.
(ok if _txt_fp.index("**Today:**") < _txt_fp.index("def _contexto") else fallo)(
    "pero la linea «Hoy:» sigue arriba del todo")
# ⚠️ Sonda validada contra un caso construido antes de creerse sus ceros (trampa n12)
_probe = ast.parse('def f():\n if not x:\n  st.info("No projects")\n  return\n')
_vistos = []
for n in ast.walk(_probe):
    if isinstance(n, ast.If) and n.body and isinstance(n.body[-1], ast.Return):
        if "_contexto()" not in ast.unparse(n):
            _vistos.append(1)
(ok if _vistos else fallo)("la sonda VE una salida sin contexto (control)")

# ── 4 ────────────────────────────────────────────────────────────────────────
print("")
print("4. La barra deja de tener 197 px vacios para el campo, y el chip se EJECUTA")
from core import home_ui as H                                     # noqa: E402
(ok if hasattr(H, "_chip_fichaje") else fallo)("existe el chip")
_tb = SRC_H[SRC_H.index("with c1:"):SRC_H.index("with cver:")]
(ok if '_rol() == "field"' in _tb and "_chip_fichaje(grupo)" in _tb else fallo)(
    "se pinta SOLO para el campo (el admin conserva su buscador)")
(ok if "st.text_input" in _tb else fallo)("...y el buscador del admin sigue ahi")
# ⚠️ EJECUTADO con los tres estados: importar no ejecuta (v378), y el fallo que esto
# caza —un nombre que no existe— es el NameError latente de v370/v423.
from core import timeclock as TC                                  # noqa: E402
_orig = TC.open_sessions
_visto = []
_orig_btn = st.button
st.button = lambda etq, **kw: _visto.append(etq) or False
try:
    for _estado, _ses in (
            ("en obra", {TC.TIPO_PROYECTO: {"clock_in": "2026-09-07 08:00", "proyecto": "X",
                                            "proyecto_id": "PRJ-0001"},
                         TC.TIPO_GENERAL: None}),
            ("jornada", {TC.TIPO_PROYECTO: None,
                         TC.TIPO_GENERAL: {"clock_in": "2026-09-07 08:00", "proyecto": "",
                                           "proyecto_id": ""}}),
            ("sin fichar", {TC.TIPO_PROYECTO: None, TC.TIPO_GENERAL: None})):
        TC.open_sessions = lambda *a, **k: _ses
        _visto.clear()
        H._chip_fichaje("cliente1")
        (ok if _visto else fallo)("pinta algo con el estado %r" % _estado)
finally:
    TC.open_sessions = _orig
    st.button = _orig_btn

# ⚠️ Los textos son los MISMOS de la banda de estado de Fichaje: una sola forma de
# decir cada estado (v323). Si alguien cambia uno por una frase larga, el boton parte
# la fila en dos y deshace lo que midio v479 — por eso se ata a la banda, no a una
# lista escrita a mano que se quedaria vieja (v433/v434).
_src_chip = ast.unparse(funcion(SRC_H, "_chip_fichaje"))
for _e in ("On a project", "Workday open, no project", "Not clocked in"):
    (ok if _e in _src_chip and _e in SRC_T else fallo)(
        "«%s» dice lo mismo que la banda de Fichaje" % _e)
# Y lleva a un destino que EXISTE en la nav del campo (el fallo real de v303).
_secs = [k for k, _d in H._SECCIONES_CAMPO]
_dest = [n.args[0].value for n in ast.walk(funcion(SRC_H, "_chip_fichaje"))
         if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "navegar"
         and n.args and isinstance(n.args[0], ast.Constant)]
(ok if _dest and all(d in _secs for d in _dest) else fallo)(
    "el chip lleva a una seccion que existe", (_dest, _secs))

print("")
if fallos:
    print("HAY FALLOS: %d" % len(fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
