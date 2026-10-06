# -*- coding: utf-8 -*-
"""v537 · LO QUE ENSEÑARON LOS LOGS DEL CLOUD (06/10/2026).

1. ⚠️ EL PRE-START ENTERO CAÍDO. Al despertar la app tras 6 días dormida, el Cloud reinstaló
   las dependencias y `streamlit-drawable-canvas` subió a 0.13.0 (el requirements decía
   `<1`). La 0.13 quita `display_toolbar` y ya no devuelve la imagen salvo que se le pida:
   `TypeError: st_canvas() got an unexpected keyword argument 'display_toolbar'` y el
   Pre-Start —la charla de seguridad diaria del campo— no abría.
   ⚠️ La suite NO lo vio aunque ya corría con el Python del Cloud: en local, sin servidor, la
   0.13 ni siquiera importaba y el Pre-Start caía a su plan B (iniciales) sin error. Un
   «verde» que no había probado el lienzo (trampa nº1).
   → versión FIJA (0.9.3, la probada en v383) y, además, se comprueba que la función acepta
   lo que le pasamos antes de usarla: si no, iniciales — nunca más la pantalla caída.
2. Una traza de error en cada cálculo del Survey: la tabla de parámetros calculados mezclaba
   números y letras («L») y no pasaba a Arrow. Ahora es texto (y las columnas CUT OR/OL).
3. Una traza de 30 líneas por el aviso «valor por defecto + Session State», que las
   herramientas provocan a propósito: se apaga ese aviso en `config.toml`.

Lo que protege, EJECUTANDO:
  (a) ⚠️ en el Python de la suite, el lienzo CARGA de verdad (no el plan B) y es la versión fija;
  (b) ⚠️ un lienzo como el de la 0.13 (sin `display_toolbar`) → `_canvas_disponible` da None
      y el Pre-Start sigue con iniciales; la sonda ve el TypeError sin la comprobación;
  (c) las dos firmas del Pre-Start usan `_LIENZO` (un solo sitio con los parámetros);
  (d) la tabla de parámetros y los cortes pasan a Arrow sin arreglos (la sonda ve el fallo);
  (e) el aviso apagado en `config.toml`, y solo ese.
"""
import ast
import importlib.metadata as md
import io
import os
import re
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ El lienzo de firma del Pre-Start")
_req = _fuente("requirements.txt")
_pin = re.search(r"^streamlit-drawable-canvas\s*([^\s#]+)", _req, re.M)
chk("⚠️ `requirements.txt` FIJA la versión del lienzo (==), no un rango",
    bool(_pin) and _pin.group(1).startswith("=="), _pin.group(1) if _pin else None)
_fija = _pin.group(1)[2:] if _pin and _pin.group(1).startswith("==") else None
try:
    _inst = md.version("streamlit-drawable-canvas")
except Exception as e:                                             # noqa: BLE001
    _inst = "NO INSTALADO (%s)" % e
chk("el Python de la suite tiene ESA versión instalada (si no, prueba otro lienzo)",
    _inst == _fija, (_inst, _fija))

from core import prestart_ui as PU                                 # noqa: E402

chk("⚠️ y en él el lienzo CARGA de verdad: el Pre-Start no está probando su plan B "
    "(lo que escondió la 0.13 en la suite)", PU._canvas_disponible() is not None)


# Un lienzo como el de la 0.13: sin `display_toolbar`.
def _st_canvas_013(fill_color=None, stroke_width=20, stroke_color="black", background_color="",
                   background_image=None, update_streamlit=True, height=400, width=600,
                   drawing_mode="freedraw", initial_drawing=None, point_display_radius=3,
                   return_image_data=False, key=None, on_change=None, disabled=False):
    return None


_real = sys.modules.get("streamlit_drawable_canvas")
_falso = types.ModuleType("streamlit_drawable_canvas")
_falso.st_canvas = _st_canvas_013
sys.modules["streamlit_drawable_canvas"] = _falso
try:
    _c = PU._canvas_disponible()
    chk("⚠️ con un lienzo que NO acepta los parámetros (como el de la 0.13), el Pre-Start "
        "cae a las iniciales en vez de caerse", _c is None, _c)
    _te = None
    try:
        _st_canvas_013(key="x", **PU._LIENZO)
    except TypeError as e:
        _te = str(e)
    chk("la sonda VE el fallo de producción: llamarlo con `_LIENZO` da el mismo TypeError "
        "(trampa nº12)", bool(_te) and "display_toolbar" in _te, _te)
finally:
    if _real is not None:
        sys.modules["streamlit_drawable_canvas"] = _real
    else:
        sys.modules.pop("streamlit_drawable_canvas", None)

_tpu = ast.parse(_fuente("core/prestart_ui.py"))
_llam = [n for n in ast.walk(_tpu) if isinstance(n, ast.Call)
         and isinstance(n.func, ast.Name) and n.func.id == "st_canvas"]
_bien = [n for n in _llam
         if [k.arg for k in n.keywords] == ["key", None]
         and ast.unparse(n.keywords[1].value) == "_LIENZO"]
chk("las DOS firmas del Pre-Start (la charla y firmar después) usan `_LIENZO` y nada más",
    len(_llam) == 2 and len(_bien) == 2, [ast.unparse(n) for n in _llam])
chk("`_LIENZO` conserva el ancho de móvil (300, v393) y la barra del lienzo",
    PU._LIENZO.get("width") == 300 and PU._LIENZO.get("display_toolbar") is True, PU._LIENZO)

# ═════════════════════════════════════════════════════════════════
sec("2. Las tablas del Survey pasan a Arrow sin arreglos")
import pandas as pd                                                # noqa: E402
import pyarrow as pa                                               # noqa: E402

_tsv = ast.unparse(ast.parse(_fuente("core/survey_ui.py")))
_m = re.search(r"\{'Parameter': k, 'Valor': (.+?)\} for k, v in limits\.items\(\)", _tsv)
chk("se encontró la tabla de parámetros calculados", bool(_m), "")
if _m:
    _expr = eval("lambda k, v: " + _m.group(1))                    # la expresión REAL del código
    _lim = {"LIMIT_WR": 82.0, "LIMIT_FR": 815.0, "Z_SIDE": "L", "BC_CALC": 60, "OK": True}
    _df = pd.DataFrame([{"Parameter": k, "Valor": _expr(k, v)} for k, v in _lim.items()])
    try:
        pa.Table.from_pandas(_df)
        _ok = True
    except Exception as e:                                          # noqa: BLE001
        _ok = repr(e)[:90]
    chk("⚠️ con números Y letras («L», el lado Z) la tabla pasa a Arrow tal cual (antes, traza "
        "de error en los logs del Cloud en cada cálculo)", _ok is True, _ok)
    _viejo = pd.DataFrame([{"Parameter": k, "Valor": round(v, 3) if isinstance(v, (int, float))
                            else v} for k, v in _lim.items()])
    try:
        pa.Table.from_pandas(_viejo)
        _vf = None
    except Exception as e:                                          # noqa: BLE001
        _vf = type(e).__name__
    chk("la sonda VE el fallo de producción con la expresión vieja (ArrowInvalid/TypeError)",
        _vf is not None, _vf)
_cut = re.findall(r"cut_o[rl]_vals\.append\((.+?)\)\n", _tsv)
chk("las columnas CUT OR / CUT OL también son texto (vacío o «3.5»)",
    len(_cut) == 2 and all(c.startswith("f'{") and ":.1f}'" in c for c in _cut), _cut)

# ═════════════════════════════════════════════════════════════════
sec("3. El aviso «valor por defecto + Session State», apagado y solo ese")
import tomllib                                                     # noqa: E402  (3.11+)

_cfg = tomllib.loads(_fuente(".streamlit/config.toml"))
chk("`global.disableWidgetStateDuplicationWarning = true` en config.toml",
    _cfg.get("global", {}).get("disableWidgetStateDuplicationWarning") is True, _cfg.get("global"))
chk("...y `[global]` no apaga nada más (ni toca el servidor ni el tema)",
    set(_cfg.get("global", {})) == {"disableWidgetStateDuplicationWarning"}
    and _cfg.get("server", {}).get("enableStaticServing") is True and "theme" in _cfg,
    (_cfg.get("global"), _cfg.get("server")))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
