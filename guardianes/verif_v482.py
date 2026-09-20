# -*- coding: utf-8 -*-
"""v482 · FASE 0.1 — la caché del lote deja de acoplar a todos los clientes.

Lo que hay que proteger:
  (a) que `invalidar(titulo)` limpie **el libro donde vive esa hoja**, y NINGÚN otro;
  (b) que una hoja GLOBAL (Login, Rails, Library…) limpie el MAESTRO y no el libro
      del grupo de la sesión — si no, el valor viejo se queda hasta 120 s;
  (c) que sin título se siga tirando ENTERO (el comportamiento seguro de siempre);
  (d) que ningún llamador se quede con la llamada pelada, que es la que acopla.
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
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

fallos = []
n_ok = 0


def ok(m, det=""):
    """⚠️ Acepta el 2º argumento y lo IGNORA: con `ok(m)` a secas el guardian revienta
    justo cuando PASA, y uno que revienta devuelve != 0 SIEMPRE — una tanda de roturas
    saldria «cazada» sin probar nada (v459/v463)."""
    global n_ok
    n_ok += 1
    print("   ok   " + m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO " + m + (" -> %r" % (det,) if det else ""))


from core import hojas, timeclock                                 # noqa: E402

# ── 1 ────────────────────────────────────────────────────────────────────────
print("1. Los dos libros son DISTINTOS (si no, nada de lo de abajo prueba nada)")
_maestro = timeclock.sheet_id_para("Login")          # GLOBAL
_grupo = timeclock.sheet_id_para("Projects")         # inquilino
# ⚠️ Este es el chequeo que evita el paso en vacio (trampa n1): con los dos libros
# iguales, «limpia solo el suyo» pasaria sin significar nada.
(ok if _maestro and _grupo and _maestro != _grupo else fallo)(
    "el libro global y el del grupo no son el mismo", (_maestro[:12], _grupo[:12]))

# ── 2 ────────────────────────────────────────────────────────────────────────
print("")
print("2. Cada titulo resuelve al libro que le toca")
for _t, _esperado, _que in (("Login", _maestro, "GLOBAL"), ("Rails", _maestro, "GLOBAL"),
                            ("Library", _maestro, "GLOBAL"),
                            ("Projects", _grupo, "del grupo"), ("Sheet1", _grupo, "del grupo"),
                            ("Invoices", _grupo, "del grupo")):
    (ok if timeclock.sheet_id_para(_t) == _esperado else fallo)(
        "%-10s -> libro %s" % (_t, _que), timeclock.sheet_id_para(_t)[:12])

# ── 3 ────────────────────────────────────────────────────────────────────────
print("")
print("3. EJECUTADO: invalidar() limpia SOLO el libro de esa hoja")
# ⚠️ Se ejercita la funcion REAL (no una copia de su logica, el error de v412)
# sustituyendo unicamente el lote, para no gastar cuota: asi lo que se prueba es la
# RESOLUCION del libro y el enrutado del clear, que es lo que cambio.
_leidos = []
_orig = hojas._lote


@st.cache_data(ttl=120, show_spinner=False)
def _lote_falso(sheet_id: str = ""):
    _leidos.append(sheet_id)
    return {"_libro": sheet_id}


hojas._lote = _lote_falso
try:
    def _poblar():
        _lote_falso(_maestro)
        _lote_falso(_grupo)

    def _cuenta(sid):
        return _leidos.count(sid)

    _lote_falso.clear()
    _leidos.clear()
    _poblar()
    _poblar()                                   # la 2a no deberia leer nada
    (ok if _cuenta(_maestro) == 1 and _cuenta(_grupo) == 1 else fallo)(
        "el lote cachea por libro", _leidos)

    # escribir en una hoja del GRUPO no puede tocar el maestro
    hojas.invalidar("Projects")
    _poblar()
    (ok if _cuenta(_grupo) == 2 else fallo)("escribir en el grupo relee SU libro")
    (ok if _cuenta(_maestro) == 1 else fallo)(
        "...y NO toca el libro maestro", _leidos)

    # y escribir en una GLOBAL no puede tocar el del grupo
    hojas.invalidar("Login")
    _poblar()
    (ok if _cuenta(_maestro) == 2 else fallo)("escribir en una hoja GLOBAL relee el maestro")
    (ok if _cuenta(_grupo) == 2 else fallo)(
        "...y NO toca el libro del grupo", _leidos)

    # sin titulo: se tira entero (comportamiento seguro de siempre)
    hojas.invalidar()
    _poblar()
    (ok if _cuenta(_maestro) == 3 and _cuenta(_grupo) == 3 else fallo)(
        "sin titulo se tira el lote ENTERO", _leidos)

    # un titulo que no resuelve NO puede dejar la cache sucia
    hojas.invalidar("HojaQueNoExisteJamas")
    _poblar()
    (ok if _cuenta(_maestro) == 4 or _cuenta(_grupo) == 4 else fallo)(
        "un titulo irresoluble limpia de MAS, nunca de menos", _leidos)
finally:
    hojas._lote = _orig

# ── 4 ────────────────────────────────────────────────────────────────────────
print("")
print("4. Ningun llamador se queda con la llamada pelada")
_pelados = []
_con_arg = 0
for _f in sorted(os.listdir("core")):
    if not _f.endswith(".py"):
        continue
    _src = io.open(os.path.join("core", _f), encoding="utf-8").read()
    for _n in ast.walk(ast.parse(_src)):
        if (isinstance(_n, ast.Call) and getattr(_n.func, "attr", "") == "invalidar"
                and getattr(getattr(_n.func, "value", None), "id", "") == "hojas"):
            if _n.args or _n.keywords:
                _con_arg += 1
            else:
                _pelados.append("%s:%d" % (_f, _n.lineno))
(ok if not _pelados else fallo)("todas las llamadas dicen de que hoja son", _pelados)
(ok if _con_arg >= 20 else fallo)("y son las 23 de siempre, no menos", _con_arg)
# ⚠️ Sonda validada contra un caso construido antes de creerse su cero (trampa n12)
_p = ast.parse("hojas.invalidar()\nhojas.invalidar(SHEET)\n")
_ve = [n for n in ast.walk(_p) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "invalidar" and not n.args]
(ok if len(_ve) == 1 else fallo)("la sonda VE una llamada pelada (control)")

# ── 5 ────────────────────────────────────────────────────────────────────────
print("")
print("5. Las hojas GLOBALES siguen siendo las mismas")
# ⚠️ Si alguien saca una hoja de aqui, su modulo empezaria a limpiar el libro del
# grupo y el maestro se quedaria con el valor viejo, sin dar ningun error.
# ⚠️ v488 · `xeroconnections` entra A PROPOSITO (la conexion de cada empresa vive en
# el maestro, decision del usuario). Se mantiene la IGUALDAD y no un «contiene»: asi
# la proxima global que alguien añada tambien obliga a pasar por aqui y decidirlo.
_esp = {"login", "grupos", "rieles", "manuales", "groups", "rails", "manuals",
        "library", "librarymodels", "xeroconnections"}
(ok if timeclock.SHEETS_GLOBALES == _esp else fallo)(
    "las 10 globales intactas", sorted(timeclock.SHEETS_GLOBALES ^ _esp))

# ── 6 ────────────────────────────────────────────────────────────────────────
print("")
print("6. El medidor clasifica bien (lectura y escritura tienen cuotas SEPARADAS)")
from core import metrics                                          # noqa: E402
_CASOS = [
    ("GET",  "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678/values:batchGet", "lectura"),
    ("POST", "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678/values:batchGet", "lectura"),
    ("POST", "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678:batchUpdate",     "escritura"),
    ("POST", "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678/values/A1:append", "escritura"),
    ("PUT",  "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678/values/A1",        "escritura"),
    ("GET",  "/spreadsheets/1AbCdEfGhIjKlMnOpQrStUvWxYz012345678",                 "lectura"),
]
for _m, _ep, _esp in _CASOS:
    (ok if metrics._tipo(_m, _ep) == _esp else fallo)(
        "%-5s %-22s -> %s" % (_m, _ep.split("/")[-1][:22], _esp), metrics._tipo(_m, _ep))
# ⚠️ El contador NUNCA puede tumbar una peticion: se le da basura a proposito.
class _Explota:
    """Su `str()` revienta. Es la unica forma de comprobar de verdad que `anota` se
    traga lo suyo: con argumentos «basura» normales no llega a fallar nunca, asi que
    ese chequeo no distinguia nada — lo destapo la bateria de roturas, no leerlo."""

    def __str__(self):
        raise RuntimeError("boom")


try:
    metrics.anota(None, None)
    metrics.anota("GET", _Explota())
    ok("ni con un argumento que revienta al convertirlo a texto")
except Exception as _e:
    fallo("el contador propago una excepcion", str(_e))

# ── 7 ────────────────────────────────────────────────────────────────────────
print("")
print("7. El PICO usa ventana deslizante (la rafaga de las 7:00 cae entre dos minutos)")
# ⚠️ Este es el caso que decide el diseno: 40 llamadas a las 06:59:40 y 40 a las
# 07:00:20 son OCHENTA en un minuto real, pero partidas en dos minutos de RELOJ
# darian 40 y 40 — y nadie veria el pico que revienta la cuota.
import time as _time                                              # noqa: E402
metrics.reiniciar()
# ⚠️ El instante se ANCLA al segundo :40 de un minuto de reloj, no a `ahora - 300`:
# asi los dos grupos caen SIEMPRE a caballo de dos minutos. Con el ancla movil, el
# chequeo pasaba o fallaba segun el segundo en que se lanzara — un rojo intermitente,
# la familia del guardian que se ponia rojo todos los lunes (v443), y el que ensena a
# ignorar la suite. Lo destapo la bateria de roturas, no leerlo.
_base = (int(_time.time() // 60) * 60) - 300 + 40
with metrics._LOCK:
    for _i in range(40):
        metrics._EVENTOS.append((_base + 0.1 * _i, "LIBRO_X", "lectura"))
    for _i in range(40):
        metrics._EVENTOS.append((_base + 40 + 0.1 * _i, "LIBRO_X", "lectura"))
_r = metrics.resumen()
(ok if _r["pico"]["lectura"] == 80 else fallo)(
    "el pico ve las 80 juntas, no 40+40", _r["pico"]["lectura"])
_relojes = {int(t // 60) for t, _l, _k in list(metrics._EVENTOS)}
(ok if len(_relojes) == 2 else fallo)(
    "...y de verdad caian en DOS minutos de reloj distintos", len(_relojes))
metrics.reiniciar()

# ── 8 ────────────────────────────────────────────────────────────────────────
print("")
print("8. EJECUTADO: una lectura REAL de Sheets incrementa el contador")
# ⚠️ Importar no ejecuta (v378), y el enganche vive dentro de una clase que se
# construye en caliente: la unica forma de saber que cuenta es hacer una llamada.
# ⚠️ NO vale llamar a `auth.list_groups()` tras `hojas.invalidar()`: esa funcion sale
# de la cache PROPIA de `auth`, que el lote no toca (cada modulo limpia la suya en su
# `_invalidate`). El primer intento de este chequeo medio CERO llamadas y parecia que
# el enganche no contaba — un cero medido sobre nada, el paso en vacio de la trampa n1.
# Lo que obliga a salir a la API de verdad es tirar el lote y pedirlo.
metrics.reiniciar()
try:
    hojas._lote.clear()
    _hojas_leidas = hojas._lote(_grupo)
    (ok if _hojas_leidas else fallo)("la lectura forzada trajo datos", len(_hojas_leidas))
except Exception as _e:
    fallo("no se pudo leer para medir", str(_e))
_r2 = metrics.resumen()
(ok if _r2["total"] >= 1 else fallo)("la llamada quedo apuntada", _r2["total"])
(ok if _r2["ahora"]["lectura"] >= 1 else fallo)(
    "...y clasificada como LECTURA", _r2["ahora"])
(ok if any(len(k) > 20 for k in _r2["por_libro"]) else fallo)(
    "...con el libro identificado", list(_r2["por_libro"]))

# ── 9 ────────────────────────────────────────────────────────────────────────
print("")
print("9. La pantalla del propietario se EJECUTA (no solo importa)")
from core import auth_ui as _AU                                   # noqa: E402
_orig_btn = st.button
st.button = lambda *a, **k: False
try:
    _AU._owner_cuota()
    ok("con datos, pinta sin reventar")
    metrics.reiniciar()
    _AU._owner_cuota()
    ok("y con el contador vacio tambien")
except Exception as _e:
    fallo("la pantalla de cuota revienta", "%s: %s" % (type(_e).__name__, _e))
finally:
    st.button = _orig_btn

# ── 10 ───────────────────────────────────────────────────────────────────────
print("")
print("10. El despacho del propietario no deja ninguna sub-seccion muerta")
# ⚠️ La leccion de v449: un if/elif/else puede dejar EXACTAMENTE una sin comparar
# (la que cae al else). Dos significa que un ID cambio en un lado y no en el otro.
from core import home_ui as _H                                    # noqa: E402
_src_au = io.open(os.path.join("core", "auth_ui.py"), encoding="utf-8").read()
_fn = next(n for n in ast.walk(ast.parse(_src_au))
           if isinstance(n, ast.FunctionDef) and n.name == "render_owner_seccion")
_comparados = {c.value for n in ast.walk(_fn) if isinstance(n, ast.Compare)
               for c in n.comparators if isinstance(c, ast.Constant)}
_ids = [i for i, _d in _H._SUBSECCIONES_OWNER["administracion"][1]]
_sin = [i for i in _ids if i not in _comparados]
(ok if len(_sin) == 1 else fallo)(
    "exactamente una cae al else", _sin)
(ok if "\U0001F4C8 Cuota" in _comparados else fallo)("y la de Cuota se despacha explicita")
(ok if _ids[-1] == "\U0001F4C8 Cuota" else fallo)(
    "la sub-seccion nueva va la ULTIMA (v297)", _ids)
# ⚠️ Y ninguna repetida: dos entradas con el mismo ID pintan dos botones que llevan al
# mismo sitio, y el despachador no puede distinguirlos.
(ok if len(_ids) == len(set(_ids)) else fallo)(
    "sin IDs duplicados", [i for i in _ids if _ids.count(i) > 1])

print("")
if fallos:
    print("HAY FALLOS: %d" % len(fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
