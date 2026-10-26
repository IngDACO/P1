"""v606 · LIBRARY: LAS PÍLDORAS, SOLO LAS QUE TIENEN PIEZAS (decisión del usuario: «Si deja esto finalizado»).

Visto verificando v605 en producción: con el filtro «Documents» las píldoras enseñaban secciones a
CERO («Controller · 0», «Shaft · 0»…), que en la fila deslizable del móvil solo estorbaban. Ahora
salen las que tienen piezas con la búsqueda y los filtros de ahora, y la ELEGIDA aunque se quede en
cero (para poder soltarla). La hoja va SUSTITUIDA en memoria.
"""
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


def _pieza(n, tipo, titulo, seccion):
    return {"ID": "LIB-%04d" % n, "Brand": "Schindler", "Model": "", "Section": seccion, "Type": tipo,
            "Title": titulo, "Notes": "", "DriveID": "D%04d" % n, "FileName": "L%04d.jpg" % n,
            "MimeType": "image/jpeg", "UploadedBy": "import", "Date": "2026-09-28 17:56:35"}


DATOS = ([_pieza(n, "photo", "Foto de cabina %d" % n, "Car") for n in range(1, 6)]
         + [_pieza(6, "photo", "Cuadro", "Controller"), _pieza(7, "photo", "Foso", "Pit")]
         + [_pieza(n, "manual", "Manual de puertas", "Landing doors") for n in range(8, 12)])
SNAP = os.path.join(os.environ.get("TEMP", "."), "verif_v606_datos.json")
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
UI._drive = lambda: _Dr()
flash.mostrar()
UI.render_biblioteca()
''' % SNAP


def _pills(a):
    _p = [w for w in a.get("button_group") if w.key == "lib_seccion"]
    return list(_p[0].options) if _p else None


def _clic(a, key):
    next(b for b in a.button if b.key == key).click()
    a.run()


print("1. Sin filtros: las cuatro secciones que tienen piezas, con su número")
at = AppTest.from_string(G, default_timeout=120)
at.run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("«Controller · 1», «Pit · 1», «Car · 5», «Landing doors · 4» (en el orden de SECCIONES)",
    _pills(at) == ["Controller · 1", "Pit · 1", "Car · 5", "Landing doors · 4"], _pills(at))

print("\n2. ⚠️ Con «Documents»: solo la sección que tiene documentos (salían las demás a CERO)")
_clic(at, "cpxkpi_lib_doc")
chk("⚠️ solo «Landing doors · 4» (antes, también «Controller · 0», «Pit · 0», «Car · 0»)",
    _pills(at) == ["Landing doors · 4"], _pills(at))
_clic(at, "cpxkpi_lib_tot")
at.get("button_group")[0].set_value("Car").run()
_clic(at, "cpxkpi_lib_doc")
chk("⚠️ la ELEGIDA se queda aunque se quede en cero («Car · 0»), para poder soltarla",
    _pills(at) == ["Car · 0", "Landing doors · 4"] and at.session_state["lib_seccion"] == "Car", _pills(at))
at.text_input(key="lib_q").set_value("nadie se llama asi").run()
_clic(at, "cpxkpi_lib_sec")                          # suelta la sección
chk("sin ninguna pieza (y sin sección elegida) no hay píldoras: ni una fila vacía",
    _pills(at) is None and not at.exception, _pills(at))
chk("…y «Nothing matches» con «Show all» sigue saliendo",
    any("Nothing matches those filters" in str(w.value) for w in at.warning)
    and any(b.key == "lib_ver_todo" for b in at.button))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
