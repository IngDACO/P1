"""v604 · LIBRARY, PROBADA (decisión del usuario: «Dale con todo»).

Medido en producción (26/10/2026, cuenta admin) con las 750 piezas reales del usuario y, lo del
propietario, en un ensayo con esos datos en solo lectura:
  ⚠️ los 218 documentos (páginas de manual en JPEG) se abrían SIN imagen, solo «Download»;
  ⚠️ 101 títulos repetidos (30 «… — manual page») sin decir qué página es, y sin «siguiente»;
  ⚠️ 9,1 s al abrir y 4-6 s por página: 6 fotos ENTERAS de Drive, una detrás de otra;
  ⚠️ en el móvil una foto por fila (los documentos a 4543 px);
  ⚠️ los filtros se perdían al abrir una pieza y la página se quedaba («Page 2 of 89» de otro
     conjunto); ⚠️ el alta repetía con un 2º clic; ⚠️ Drive sin tiempo máximo y un borrado que
  decía «Removed» con el archivo aún en Drive; cifras mudas; fechas ISO; «photo»; «item(s)».
Todo con la hoja y Drive SUSTITUIDOS: nada se lee ni se escribe de verdad.
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


# ── los datos: como los del usuario, sintéticos ─────────────────────────────────────────────
def _pieza(n, tipo, titulo, seccion, marca="Schindler", notas="", fecha="2026-09-28 17:56:35"):
    return {"ID": "LIB-%04d" % n, "Brand": marca, "Model": "", "Section": seccion, "Type": tipo,
            "Title": titulo, "Notes": notas, "DriveID": "D%04d" % n, "FileName": "L%04d.jpg" % n,
            "MimeType": "image/jpeg", "UploadedBy": "COPEX library import", "Date": fecha}


DATOS = ([_pieza(n, "photo", "Foto %d del hueco" % n, "Shaft") for n in range(1, 26)]
         + [_pieza(26, "photo", "Counterweight frame bottom", "Counterweight"),
            _pieza(27, "photo", "Counterweight frame bottom", "Counterweight", notas="Ver *gate 2* y_b")]
         + [_pieza(n, "manual", "Landing door SEMATIC 2000 — manual page", "Landing doors", marca="Sematic")
            for n in range(28, 58)]
         + [_pieza(58, "diagram", "Wiring diagram", "Electrical & wiring", marca="")])
MODELOS = [{"Brand": "Schindler", "Model": "", "Active": "SI"}, {"Brand": "Sematic", "Model": "", "Active": "SI"}]
SNAP = os.path.join(os.environ.get("TEMP", "."), "verif_v604_datos.json")
json.dump({"L": DATOS, "M": MODELOS}, open(SNAP, "w", encoding="utf-8"))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. El motor: «todos los documentos» y la página n de m (sin tocar la hoja)")
from core import library as LIB                                  # noqa: E402
LIB._records = lambda: [dict(r) for r in DATOS]
LIB._modelos_records = lambda: [dict(r) for r in MODELOS]
_docs = LIB.list_items(tipo=LIB.DOCUMENTOS)
chk("`DOCUMENTOS` = todo lo que NO es una foto (31: 30 páginas + 1 diagrama)",
    len(_docs) == 31 and all(r["Type"] != "photo" for r in _docs), len(_docs))
chk("…y NO es un tipo que se guarde (no está en TIPOS: solo filtra)", LIB.DOCUMENTOS not in LIB.TIPOS)
_p = LIB.paginas()
chk("⚠️ `paginas`: las 30 que comparten título, 1/30 … 30/30 por orden de ID",
    _p.get("LIB-0028") == (1, 30) and _p.get("LIB-0057") == (30, 30) and _p.get("LIB-0040") == (13, 30), _p.get("LIB-0028"))
chk("…las 2 fotos repetidas, 1/2 y 2/2; una pieza de título único, sin número",
    _p.get("LIB-0026") == (1, 2) and _p.get("LIB-0027") == (2, 2) and "LIB-0001" not in _p)
chk("el orden por ID es NUMÉRICO (LIB-10000 detrás de LIB-9999)",
    sorted(["LIB-10000", "LIB-9999"], key=LIB._orden_id) == ["LIB-9999", "LIB-10000"])

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n2. ⚠️ Drive: tiempo máximo en TODO, un borrado que dice si falló, miniaturas en paralelo")
_ds = fuente("core/drive_store.py")
_llam = [n for n in ast.walk(ast.parse(_ds)) if isinstance(n, ast.Call)
         and ast.unparse(n.func) in ("requests.get", "requests.post", "requests.patch", "requests.delete")]
_sin = [ast.unparse(n)[:60] for n in _llam if not any(k.arg == "timeout" for k in n.keywords)]
chk("⚠️ las %d llamadas de drive_store llevan `timeout` (sin él una descarga colgaba la página)" % len(_llam),
    len(_llam) >= 10 and not _sin, _sin)
from core import drive_store as DS                               # noqa: E402


class _R:
    def __init__(self, code, content=b""):
        self.status_code, self.content = code, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP %d" % self.status_code)


_orig = (DS.requests.delete, DS.requests.get, DS._headers)
DS._headers = lambda: {"Authorization": "Bearer x"}
_res = []
for code in (204, 404, 403):
    DS.requests.delete = lambda *a, _c=code, **k: _R(_c)
    _res.append(DS.delete("F1"))
DS.requests.delete = lambda *a, **k: (_ for _ in ()).throw(OSError("red caída"))
_res.append(DS.delete("F1"))
chk("⚠️ `delete` DICE si falló: True con 204 y 404 (ya no está), False con 403 y con la red caída",
    _res == [True, True, False, False], _res)
from PIL import Image                                            # noqa: E402
_b = io.BytesIO()
# mitad izquierda ROJA, derecha AZUL: girada 90° (EXIF 6) el rojo pasa ARRIBA — con una foto de
# un solo color, girarla o no daría lo mismo y la sonda no sabría verlo (trampa 12)
_im = Image.new("RGB", (1200, 800), (20, 20, 220))
_im.paste((220, 20, 20), (0, 0, 600, 800))
_ex = _im.getexif()
_ex[0x0112] = 6                                                  # «gira 90°»: como las fotos del móvil
_im.save(_b, "JPEG", exif=_ex)
GRANDE = _b.getvalue()
_pedidas, _hilos = [], set()
import threading                                                 # noqa: E402


def _get(url, **k):
    _pedidas.append(url.rsplit("/", 1)[-1])
    _hilos.add(threading.get_ident())
    import time
    time.sleep(0.2)
    return _R(500) if url.endswith("/MAL") else _R(200, GRANDE)


DS.requests.get = _get
DS._almacen_miniaturas()["datos"].clear()
import time                                                      # noqa: E402
_t0 = time.time()
_m = DS.miniaturas(["A", "B", "C", "D", "E", "F", "MAL"])
_dt = time.time() - _t0
chk("⚠️ las 7 se piden A LA VEZ (7 × 0,2 s en %.2f s; una detrás de otra serían 1,4 s)" % _dt,
    _dt < 0.8 and len(_hilos) > 1, (_dt, len(_hilos)))
chk("…una que falla (HTTP 500) no tumba las demás: 6 de 7", sorted(_m) == ["A", "B", "C", "D", "E", "F"], sorted(_m))
_mi = Image.open(io.BytesIO(_m["A"]))
chk("⚠️ la miniatura, CUADRADA y reducida (360×360, %d KB de %d KB)" % (len(_m["A"]) // 1024, len(GRANDE) // 1024),
    _mi.size == (360, 360) and len(_m["A"]) < len(GRANDE), _mi.size)
_arr, _aba = _mi.getpixel((300, 60)), _mi.getpixel((300, 300))
chk("…y GIRADA según el EXIF (sin `exif_transpose` saldría tumbada): rojo ARRIBA, azul abajo",
    _arr[0] > 150 and _arr[2] < 100 and _aba[2] > 150 and _aba[0] < 100, (_arr, _aba))
_pedidas.clear()
DS.miniaturas(["A", "B"])
chk("las ya hechas salen de la caché: ninguna descarga más", _pedidas == [], _pedidas)
DS.requests.delete, DS.requests.get, DS._headers = _orig

# ═══════════════════════════════════════════════════════════════════════════════════════════
G = r'''
import io, json
import streamlit as st
from PIL import Image
from core import library as LIB, library_ui as UI, flash, incrustar
S = json.load(open(r"%s", encoding="utf-8"))
st.session_state.setdefault("auth", {"usuario": "duena", "rol": st.session_state.get("_ROL", "administrator"), "grupo": ""})
W = st.session_state.setdefault("_W", [])
LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: LL.append(h)
LIB.is_configured = lambda: True
LIB._records = lambda: [dict(r) for r in S["L"]]
LIB._modelos_records = lambda: [dict(r) for r in S["M"]]
def _add(*a, **k):
    W.append(("add_item", a[0])); return True, "LIB-0099"
LIB.add_item = _add
LIB.delete_item = lambda lid: (W.append(("delete_item", lid)) or (True, "Removed from the library."))
LIB.add_modelo = lambda mk, md: (W.append(("add_modelo", mk)) or (True, "Added to the catalogue."))
_b = io.BytesIO(); Image.new("RGB", (20, 30), (9, 9, 9)).save(_b, "JPEG"); JPG = _b.getvalue()
class _Dr:
    def download(self, did): return JPG
    def miniaturas(self, ids, lado=360):
        W.append(("minis", tuple(ids))); return {i: JPG for i in ids}
    def delete(self, did):
        W.append(("drive_delete", did)); return st.session_state.get("_DEL_OK", True)
    def folder(self, n): return "F"
    def upload_to(self, *a):
        W.append(("drive_upload", a[1])); return "D1"
UI._drive = lambda: _Dr()
flash.mostrar()
UI.render_biblioteca()
''' % SNAP


def _txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success")
                      for x in getattr(a, k, []))


def _ss(a, k, d=None):
    return a.session_state[k] if k in a.session_state else d


def _caps(a, s):
    return [str(c.value) for c in a.caption if s in str(c.value)]


def _clic(a, key):
    next(b for b in a.button if b.key == key).click()
    a.run()


def _app(**ss):
    a = AppTest.from_string(G, default_timeout=120)
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a


print("\n3. La lista: cifras ACTIVAS, secciones con su número, filtros recordados")
at = _app()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_lib_")}
chk("⚠️ 4 cifras-BOTÓN: Items 58 · Photos 27 · Documents 31 · Sections 4 (eran HTML mudo; sin «Models 0»)",
    list(_kb) == ["cpxkpi_lib_tot", "cpxkpi_lib_fot", "cpxkpi_lib_doc", "cpxkpi_lib_sec"]
    and "\n\n58\n\n" in _kb["cpxkpi_lib_tot"] and "\n\n27\n\n" in _kb["cpxkpi_lib_fot"]
    and "\n\n31\n\n" in _kb["cpxkpi_lib_doc"] and "\n\n4\n\n" in _kb["cpxkpi_lib_sec"], _kb)
chk("…dos por fila en estrecho (`dos_por_fila`)", "@container (max-width:700px)" in _txt(at) and "cpx_lib_kpis" in _txt(at))
_pl = [w for w in at.get("button_group") if w.key == "lib_seccion"]
chk("⚠️ las secciones, PÍLDORAS con su número («Shaft · 25»)",
    # (AppTest devuelve las opciones YA formateadas)
    len(_pl) == 1 and "Shaft · 25" in list(_pl[0].options), _pl[0].options if _pl else None)
_clic(at, "cpxkpi_lib_doc")
chk("⚠️ «Documents» filtra los documentos y BAJA a su tabla",
    _ss(at, "lib_tipo") == LIB.DOCUMENTOS and not [b for b in at.button if str(b.key).startswith("libfoto_")]
    and any(".st-key-lib_docs" in s for s in _ss(at, "_LL", [])[-3:]), _ss(at, "lib_tipo"))
_clic(at, "cpxkpi_lib_fot")
chk("«Photos» filtra las fotos y baja a la galería",
    _ss(at, "lib_tipo") == "photo" and not at.dataframe and any(".st-key-lib_gal" in s for s in _ss(at, "_LL", [])[-3:]))
at.text_input(key="lib_q").set_value("hueco").run()
_clic(at, "cpxkpi_lib_tot")
chk("«Items» lo devuelve TODO (sin búsqueda ni filtros) y baja a los resultados",
    _ss(at, "lib_tipo") == "" and at.text_input(key="lib_q").value == "" and _caps(at, "Tap")
    == ["58 items. Tap one to open it."], _caps(at, "Tap"))
at.get("button_group")[0].set_value("Counterweight").run()
chk("tocar «Counterweight · 2» filtra a esa sección", _caps(at, "Tap") == ["2 items. Tap one to open it."], _caps(at, "Tap"))
_clic(at, "cpxkpi_lib_tot")                          # (suelta la sección: todo)
at.text_input(key="lib_q").set_value("wiring diagram").run()
chk("el singular de verdad: «1 item. Tap it to open it.» (salía «1 item(s)»)",
    _caps(at, "Tap") == ["1 item. Tap it to open it."], _caps(at, "Tap"))
# (lo hace Streamlit: un valor recordado que ya no está entre las opciones vuelve al de por
# defecto — v604 llevaba cuatro guardas propias y la batería las vio de más: escapaban)
at = _app(lib_marca="Schindler", lib_modelo="ZZ-no-existe", lib_seccion="Sección vieja")
chk("un modelo o una sección RECORDADOS que ya no valen se sueltan (no rompen la pantalla)",
    not at.exception and _ss(at, "lib_modelo") == "" and _ss(at, "lib_seccion") is None,
    ([e.value for e in at.exception][:1], _ss(at, "lib_modelo"), _ss(at, "lib_seccion")))
at = _app(lib_marca="Otis", lib_tipo="tipo-viejo")
chk("…y lo mismo una marca desactivada o un tipo que ya no existe",
    not at.exception and _ss(at, "lib_marca") == "" and _ss(at, "lib_tipo") == "",
    ([e.value for e in at.exception][:1], _ss(at, "lib_marca"), _ss(at, "lib_tipo")))
_pers = {ast.unparse(k.value) for n in ast.walk(ast.parse(fuente("core/library_ui.py"))) if isinstance(n, ast.Call)
         for k in n.keywords if k.arg == "key" and any(kk.arg == "persist_state" for kk in n.keywords)}
chk("⚠️ búsqueda, tipo, marca, modelo y sección se RECUERDAN (`persist_state`)",
    {"'lib_q'", "'lib_tipo'", "'lib_marca'", "'lib_modelo'", "'lib_seccion'"} <= _pers, sorted(_pers))

print("\n4. ⚠️ La galería: miniaturas en una sola petición, 3 por fila SIEMPRE, la pieza entera se toca")
at = _app()
_t = [b for b in at.button if str(b.key).startswith("libfoto_")]
_mn = [w for w in _ss(at, "_W", []) if w[0] == "minis"]
chk("12 por página, y sus miniaturas pedidas de UNA vez (no la foto entera, una a una)",
    len(_t) == 12 and len(_mn) == 1 and len(_mn[0][1]) == 12, (len(_t), _mn))
chk("«Page 1 of 3» y plurales de verdad («27 photos», «31 items»)",
    _caps(at, "Page") == ["Page 1 of 3"] and "27 photos" in _txt(at) and "31 items" in _txt(at), _caps(at, "Page"))
_css = fuente("core/library_ui.py")
chk("⚠️ el CSS: 3 por fila sin apilar (`nowrap`) y el botón ENCIMA de toda la pieza (`absolute`, `inset:0`)",
    "flex-wrap:nowrap!important" in _css and "position:absolute!important;inset:0" in _css
    and "height:100%!important;opacity:0" in _css)
_at3 = _app(_lib_pag=2)                                # las dos repetidas están en la página 3
chk("el número de página en la pieza repetida («Counterweight frame bottom (1/2)» y «(2/2)»)",
    "Counterweight frame bottom (1/2)" in _txt(_at3) and "Counterweight frame bottom (2/2)" in _txt(_at3))
_clic(at, "lib_next")
chk("⚠️ «Next» pasa de página y BAJA al principio de la galería (se quedaba en los botones)",
    _caps(at, "Page") == ["Page 2 of 3"] and any(".st-key-lib_gal" in s for s in _ss(at, "_LL", [])[-3:]))
at.text_input(key="lib_q").set_value("frame").run()
chk("⚠️ otra búsqueda vuelve a la PÁGINA 1 (se quedaba en la de antes)", _ss(at, "_lib_pag") == 0, _ss(at, "_lib_pag"))

print("\n5. ⚠️ La ficha: «Previous / Next», volver a su sitio, cualquier imagen, Download arriba")
at = _app()
_clic(at, "lib_next")
_t = [b for b in at.button if str(b.key).startswith("libfoto_")]
_clic(at, _t[3].key)                                  # la 4ª de la página 2 = la 16ª
_lid = _ss(at, "_lib_open")
chk("abrir una foto: «16 of 27» (navega por las FOTOS de los resultados)", _caps(at, " of 27") == ["16 of 27"], _caps(at, " of "))
for _ in range(9):
    _clic(at, "lib_it_next")
chk("«Next» nueve veces → la 25ª", _caps(at, " of 27") == ["25 of 27"], _caps(at, " of "))
_clic(at, "lib_back")
chk("⚠️ volver: la galería en la página de ESA foto (la 3) y bajando a ella",
    _ss(at, "_lib_pag") == 2 and _caps(at, "Page") == ["Page 3 of 3"]
    and any(".st-key-lib_gal" in s for s in _ss(at, "_LL", [])[-3:]), (_ss(at, "_lib_pag"), _caps(at, "Page")))
at.get("button_group")[0].set_value("Landing doors").run()
_df = at.dataframe[0].value
chk("⚠️ la tabla: «… — manual page (1/30)», «Manual» y DD/MM/YYYY (eran «photo» y ISO)",
    list(_df["Title"])[0] == "Landing door SEMATIC 2000 — manual page (1/30)" and list(_df["Type"])[0] == "Manual"
    and list(_df["Date"])[0] == "28/09/2026", (list(_df["Title"])[:1], list(_df["Type"])[:1], list(_df["Date"])[:1]))
chk("…sin la columna Model cuando no hay ningún modelo (era «—» entero)", "Model" not in _df.columns, list(_df.columns))
_g = _ss(at, "_lib_tbl_gen", 0)
at.session_state["lib_tbl_%d" % _g] = {"selection": {"rows": [], "columns": [], "cells": [(2, "Title")]}}
at.run()
chk("⚠️ una página de MANUAL se abre CON su imagen (salía sin ella, solo «Download»)",
    _ss(at, "_lib_open") == "LIB-0030" and [type(e).__name__ for e in at.main].count("Image") == 1,
    (_ss(at, "_lib_open"), [type(e).__name__ for e in at.main]))
_ord = [type(e).__name__ for e in at.main]
chk("⚠️ «Download» ANTES de la imagen (una foto vertical lo dejaba bajo la pantalla)",
    "DownloadButton" in _ord and _ord.index("DownloadButton") < max(i for i, x in enumerate(_ord) if x == "Image"), _ord)
chk("el título con su página y «3 of 30» para leer el manual seguido",
    any("manual page \\(3/30\\)" in str(m.value) for m in at.markdown) and _caps(at, " of 30") == ["3 of 30"])
at = _app(_lib_open="LIB-0027", _lib_nav=["LIB-0027"])
chk("⚠️ la nota TAL CUAL («*gate 2*» no se vuelve cursiva) y la fecha en DD/MM/YYYY",
    any("Ver \\*gate 2\\* y\\_b" in str(m.value) for m in at.markdown)
    and _caps(at, "Filed by") == ["Filed by COPEX library import on 28/09/2026 17:56"], _caps(at, "Filed by"))
chk("…una pieza sola no ofrece «Previous / Next»", not any(b.key in ("lib_it_prev", "lib_it_next") for b in at.button))

print("\n6. ⚠️ El propietario: el alta no repite, abre lo archivado; el borrado no miente")
_lu = ast.parse(fuente("core/library_ui.py"))
_forms = [n for n in ast.walk(_lu) if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.form"]
chk("⚠️ los DOS formularios (alta y catálogo) por GENERACIÓN y sin enviar con Enter",
    len(_forms) == 2 and all(isinstance(f.args[0], ast.JoinedStr) for f in _forms)
    and all(any(k.arg == "enter_to_submit" and ast.unparse(k.value) == "False" for k in f.keywords) for f in _forms),
    [ast.unparse(f)[:50] for f in _forms])
at = _app(_ROL="owner")
next(t_ for t_ in at.text_input if t_.key == "lib_up_tit_0").set_value("Placa nueva")
next(b for b in at.button if "File it" in str(b.label)).click()
at.run()
chk("archiva, avisa «Filed as LIB-0099.» y ABRE la ficha nueva",
    [w[0] for w in _ss(at, "_W") if w[0] == "add_item"] == ["add_item"] and _ss(at, "_lib_open") == "LIB-0099"
    and "Filed as LIB-0099." in _txt(at), (_ss(at, "_lib_open"), _txt(at)[:120]))
at.session_state["_lib_open"] = None
at.run()
_tit = next(t_ for t_ in at.text_input if str(t_.key).startswith("lib_up_tit_"))
next(b for b in at.button if "File it" in str(b.label)).click()
at.run()
chk("⚠️ y el alta nace VACÍA: un 2º clic NO archiva otra vez (pide el título)",
    _tit.key == "lib_up_tit_1" and _tit.value == "" and [w[0] for w in _ss(at, "_W")].count("add_item") == 1
    and "The title is required." in _txt(at), (_tit.key, [w[0] for w in _ss(at, "_W")]))
next(t_ for t_ in at.text_input if t_.key == "lib_cat_mk_0").set_value("Otis")
next(b for b in at.button if "Add to catalogue" in str(b.label)).click()
at.run()
chk("el catálogo, igual: añade y el campo nace vacío (otra generación)",
    ("add_modelo", "Otis") in _ss(at, "_W") and any(t_.key == "lib_cat_mk_1" and t_.value == "" for t_ in at.text_input))
at = _app(_ROL="owner", _lib_open="LIB-0002", _DEL_OK=False)
at.checkbox(key="lib_del_ok").check().run()
_clic(at, "lib_del")
chk("⚠️ si Drive NO borra el archivo, no se borra nada y se DICE (decía «Removed» con el archivo en Drive)",
    ("drive_delete", "D0002") in _ss(at, "_W") and not [w for w in _ss(at, "_W") if w[0] == "delete_item"]
    and "could not be deleted from Drive" in _txt(at), (_ss(at, "_W"), _txt(at)[:200]))
at = _app(_ROL="owner", _lib_open="LIB-0002")
at.checkbox(key="lib_del_ok").check().run()
_clic(at, "lib_del")
# (después la lista vuelve a pedir sus miniaturas: se miran solo las escrituras)
chk("…y si lo borra, Drive primero y después la fila",
    [w[0] for w in _ss(at, "_W") if w[0] != "minis"][-2:] == ["drive_delete", "delete_item"], _ss(at, "_W"))

print("\n7. Ninguna fecha cortada como texto se PINTA en ISO (en toda la app)")
_exentas = {("handover_ui.py", "str(r.get('Clock In', '') or '')[:10]"),      # calcula la más reciente
            ("invoices_ui.py", "str(f.get('ExpiryDate'))[:10]")}               # cuenta los días de retraso
_hall = []
for f in sorted(os.listdir(os.path.join(RAIZ, "core"))):
    if not f.endswith("_ui.py"):
        continue
    _arb = ast.parse(fuente("core/" + f))
    _pad = {h: n for n in ast.walk(_arb) for h in ast.iter_child_nodes(n)}
    for n in ast.walk(_arb):
        if (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Slice) and n.slice.lower is None
                and isinstance(n.slice.upper, ast.Constant) and n.slice.upper.value in (10, 16, 19)
                and any(k in ast.unparse(n.value) for k in ("Date", "Fecha", "Created", "Clock", "date"))):
            p = _pad.get(n)
            while p is not None and not (isinstance(p, ast.Call) and ast.unparse(p.func).split(".")[-1] in ("dmy", "_fecha", "_dmy")):
                p = _pad.get(p)
            if p is None and (f, ast.unparse(n)) not in _exentas:
                _hall.append("%s:%d %s" % (f, n.lineno, ast.unparse(n)[:60]))
chk("⚠️ todo `…Date…[:10]` de pantalla va por `dmy` (Library salía «2026-09-28»)", not _hall, _hall)
chk("…la sonda SABE verlo: el corte de Invoices (exento con su razón) existe de verdad",
    'str(f.get("ExpiryDate"))[:10]' in fuente("core/invoices_ui.py"))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
