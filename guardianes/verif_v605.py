"""v605 · LO VISTO VERIFICANDO v604 EN LIBRARY (decisión del usuario: «Dale no dejes nada pendiente»).

Medido en producción (26/10/2026, con las 750 piezas reales):
  ⚠️ el número de página «(n/m)», pegado al final del título, se CORTABA donde el título es largo:
     en la tabla (340 px: «… — installation ste…» sin su «(2/7)») y, en el móvil, en las 9 de 9
     miniaturas que lo llevaban (el límite de 2 líneas);
  ⚠️ en el móvil las 16 píldoras de sección ocupaban ~320 px y la galería empezaba a 958 (antes 766).
CSS medido antes en una mini-app (Streamlit 1.64): una fila de 66 px que se desliza (2011 en 343),
la elegida la primera (`aria-checked`), la insignia a 6 px de la esquina de la foto.
"""
import ast
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


def _pieza(n, tipo, titulo, seccion):
    return {"ID": "LIB-%04d" % n, "Brand": "Schindler", "Model": "", "Section": seccion, "Type": tipo,
            "Title": titulo, "Notes": "", "DriveID": "D%04d" % n, "FileName": "L%04d.jpg" % n,
            "MimeType": "image/jpeg", "UploadedBy": "import", "Date": "2026-09-28 17:56:35"}


LARGO = "Traveling cable for CWT with safety gear — installation steps"
DATOS = ([_pieza(1, "photo", "Counterweight frame bottom and striker plate", "Counterweight"),
          _pieza(2, "photo", "Counterweight frame bottom and striker plate", "Counterweight"),
          _pieza(3, "photo", "Machine with terminal box", "Machine & traction")]
         + [_pieza(n, "manual", LARGO, "Electrical & wiring") for n in range(4, 11)]
         + [_pieza(11, "manual", "Single manual page", "Controller")])
SNAP = os.path.join(os.environ.get("TEMP", "."), "verif_v605_datos.json")
json.dump({"L": DATOS, "M": [{"Brand": "Schindler", "Model": "", "Active": "SI"}]}, open(SNAP, "w", encoding="utf-8"))

G = r'''
import io, json
import streamlit as st
from PIL import Image
from core import library as LIB, library_ui as UI, flash, incrustar
S = json.load(open(r"%s", encoding="utf-8"))
st.session_state.setdefault("auth", {"usuario": "x", "rol": "administrator", "grupo": ""})
incrustar.script = lambda h, *a, **k: None
LIB.is_configured = lambda: True
LIB._records = lambda: [dict(r) for r in S["L"]]
LIB._modelos_records = lambda: [dict(r) for r in S["M"]]
_b = io.BytesIO(); Image.new("RGB", (20, 20)).save(_b, "JPEG"); JPG = _b.getvalue()
class _Dr:
    def download(self, did): return JPG
    def miniaturas(self, ids, lado=360): return {i: JPG for i in ids}
    def delete(self, did): return True
UI._drive = lambda: _Dr()
flash.mostrar()
UI.render_biblioteca()
''' % SNAP


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption") for x in getattr(a, k, []))


print("1. ⚠️ El número de página, aparte (ya no al final del título, donde se cortaba)")
at = AppTest.from_string(G, default_timeout=120)
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value
chk("⚠️ la tabla: «Page» es la PRIMERA columna («1/7»…) y el título va limpio",
    list(_df.columns)[:2] == ["Page", "Title"] and list(_df["Page"])[:2] == ["1/7", "2/7"]
    and list(_df["Title"])[0] == LARGO, (list(_df.columns), list(_df["Page"])[:3]))
chk("…una pieza de título único, la celda vacía", list(_df["Page"])[-1] == "", list(_df["Page"]))
_cfg = json.loads(at.dataframe[0].proto.columns)
chk("…estrecha (56 px) y con su nombre", (_cfg.get("Page") or {}).get("width") == 56
    and (_cfg.get("Page") or {}).get("label") == "Page", _cfg.get("Page"))
_t = _txt(at)
chk("⚠️ en la galería, una INSIGNIA «1/2» y «2/2» sobre la foto; el título, sin el número",
    '<div class="lib-pag">1/2</div>' in _t and '<div class="lib-pag">2/2</div>' in _t
    and '<div class="lib-tt">Counterweight frame bottom and striker plate</div>' in _t, _t[:300])
chk("…y la de título único no lleva insignia", _t.count('class="lib-pag"') == 2, _t.count('class="lib-pag"'))
_css = fuente("core/library_ui.py")
chk("la insignia, FUERA del flujo (su bloque, `absolute` arriba a la izquierda; sin él subía la foto)",
    "[data-testid='stElementContainer']:has(.lib-pag){position:absolute!important;" in _css
    and "top:6px;left:6px;z-index:1" in _css)
_tabla = next(n for n in ast.walk(ast.parse(_css)) if isinstance(n, ast.FunctionDef) and n.name == "_tabla")
_gal = next(n for n in ast.walk(ast.parse(_css)) if isinstance(n, ast.FunctionDef) and n.name == "_galeria")
chk("ni la tabla ni la galería pegan el número al título (`_titulo` solo en el botón y la ficha)",
    "'Title': _titulo(" not in ast.unparse(_tabla) and "_h.escape(_titulo(" not in ast.unparse(_gal))
at.session_state["_lib_open"] = "LIB-0005"
at.session_state["_lib_nav"] = ["LIB-0004", "LIB-0005"]
at.run()
chk("la ficha sí lo lleva en su título (ancho completo): «… (2/7)»",
    any("installation steps \\(2/7\\)" in str(m.value) for m in at.markdown))

print("\n2. ⚠️ En estrecho, las secciones en UNA fila que se desliza (ocupaban ~320 px en el móvil)")
at = AppTest.from_string(G, default_timeout=120)
at.run()
_t = _txt(at)
chk("el CSS va en la página, con una consulta de CONTENEDOR (≤700 px: el móvil y el escritorio con menú)",
    ".st-key-lib_secs{container-type:inline-size}@container (max-width:700px){" in _t, _t[:200])
chk("…sin saltar de línea y deslizándose (`nowrap` + `overflow-x:auto`), cada píldora entera",
    "[data-testid='stButtonGroup']>div{flex-wrap:nowrap!important;overflow-x:auto!important" in _t
    and "button{flex:0 0 auto!important}" in _t)
chk("…y la ELEGIDA la primera (`aria-checked`, el contrato de accesibilidad), para que no quede escondida",
    "button[aria-checked='true']{order:-1}" in _t)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
