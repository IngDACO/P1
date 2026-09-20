# -*- coding: utf-8 -*-
"""Añade a verif_v482 el bloque del MEDIDOR (fase 0.2)."""
import ast
import io

P = "verif_v482.py"
s = io.open(P, encoding="utf-8").read()

BLOQUE = '''
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
try:
    metrics.anota(None, None)
    metrics.anota(123, object())
    ok("con argumentos basura no lanza")
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
_base = _time.time() - 300
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
from core import auth as _auth                                    # noqa: E402
metrics.reiniciar()
hojas.invalidar()                       # obliga a que la siguiente lectura salga a la API
try:
    _auth.list_groups()
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
(ok if "\\U0001F4C8 Cuota" in _comparados else fallo)("y la de Cuota se despacha explicita")
(ok if _ids[-1] == "\\U0001F4C8 Cuota" else fallo)(
    "la sub-seccion nueva va la ULTIMA (v297)", _ids)
'''

A = '\nprint("")\nif fallos:'
if s.count(A) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(A))
s = s.replace(A, BLOQUE + A)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v482: bloques 6-10 (el medidor)")
