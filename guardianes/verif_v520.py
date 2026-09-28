# -*- coding: utf-8 -*-
"""v520 · LA BIBLIOTECA SE LLENA: dos secciones nuevas y una carga en lote.

El usuario pasó su carpeta de obra (750 fotos) y decidió dónde va cada cosa. Dos
bolsas no cabían en ninguna de las catorce secciones —la plomada y el equipo de
montaje (false car, tirak, Blocstop, eslingas)— y pidió secciones propias.

Lo que protege:
  (a) ⚠️ que las catorce de SIEMPRE sigan escritas IGUAL: la sección vive como texto en
      cada fila de la hoja, así que renombrar una deja sus piezas fuera de todo filtro
      SIN dar ningún error. Solo se añade;
  (b) que el alta ACEPTE las dos nuevas y siga rechazando lo que no está en la lista —
      ejecutando `add_item` con la hoja sustituida, no mirando el texto (v378);
  (c) que las dos pantallas (el filtro y el alta) saquen sus opciones de SECCIONES:
      una lista copiada a mano dejaría las nuevas sin poder elegirse;
  (d) ⚠️ que la carga en lote valide LO MISMO que el alta, compruebe la cabecera REAL
      antes de escribir filas posicionales (v363), no repita nada al volver a correr
      (la llave es el nombre de archivo) y salte los IDs referenciados (v427).
      Ejecutándola entera contra una hoja y un Drive de mentira.
"""
import ast
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "owner", "grupo": ""}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s %s" % (q, ("-> %s" % (det,)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("")
    print(x)


from core import hojas, library as LIB, timeclock                 # noqa: E402

# ⚠️ Escritas A MANO, a propósito: son el contrato con las filas que YA están en la
# hoja. Derivarlas de `LIB.SECCIONES` haría que el guardián aceptara cualquier cambio.
CATORCE = ["Machine & traction", "Controller", "Shaft", "Pit", "Car", "Car door",
           "Landing doors", "Guide rails & brackets", "Counterweight",
           "Ropes & governor", "Safety gear", "Electrical & wiring", "Signalling",
           "Documentation"]
NUEVAS = ["Setting out", "Installation equipment"]

# ═════════════════════════════════════════════════════════════════
sec("1. Las catorce de siempre siguen escritas igual; las dos nuevas están")
_faltan = [s for s in CATORCE if s not in LIB.SECCIONES]
chk("ninguna de las 14 renombrada ni quitada", not _faltan, _faltan)
chk("'Setting out' e 'Installation equipment' en la lista",
    all(s in LIB.SECCIONES for s in NUEVAS), [s for s in NUEVAS if s not in LIB.SECCIONES])
chk("sin repetidas", len(LIB.SECCIONES) == len(set(LIB.SECCIONES)), LIB.SECCIONES)
chk("son 16 (si sale otra, que se añada aquí con su razón)", len(LIB.SECCIONES) == 16,
    len(LIB.SECCIONES))
# ⚠️ Se GUARDAN: en inglés y sin acentos, o el filtro por igualdad las perdería al
# traducir (v453).
chk("todas en inglés plano (ASCII)", all(s.isascii() for s in LIB.SECCIONES),
    [s for s in LIB.SECCIONES if not s.isascii()])


# ═════════════════════════════════════════════════════════════════
sec("2. El alta acepta las nuevas y sigue rechazando lo desconocido (ejecutando)")


class _WS:
    def __init__(self, cab=None, filas=None):
        self.cab = list(cab or LIB.HEADERS)
        self.filas = [list(f) for f in (filas or [])]
        self.escrituras = 0

    def row_values(self, n):
        return list(self.cab) if n == 1 else []

    def get_all_records(self, **kw):
        return [dict(zip(self.cab, f)) for f in self.filas]

    def append_row(self, fila, **kw):
        self.filas.append(list(fila))
        self.escrituras += 1

    def append_rows(self, filas, **kw):
        self.filas += [list(f) for f in filas]
        self.escrituras += 1


_ws = _WS()
_orig = (LIB._ws, LIB._next_id, LIB._invalidate, timeclock._now)
LIB._ws = lambda: (_ws, None)
LIB._next_id = lambda: "LIB-0001"
LIB._invalidate = lambda: None
timeclock._now = lambda: "2026-09-28 12:00:00"
for s in NUEVAS:
    _ok, _msg = LIB.add_item("Prueba " + s, s, "photo")
    chk("add_item acepta %r" % s, _ok, _msg)
_ok, _msg = LIB.add_item("Prueba", "Plumbing", "photo")
chk("add_item sigue rechazando una sección que no está ('Plumbing')", not _ok, _msg)
_ok, _msg = LIB.add_item("Prueba", "Car doors", "photo")
chk("...y una mal escrita ('Car doors')", not _ok, _msg)
chk("solo se escribieron las dos válidas", _ws.escrituras == 2, _ws.escrituras)
LIB._ws, LIB._next_id, LIB._invalidate, timeclock._now = _orig


# ═════════════════════════════════════════════════════════════════
sec("3. Las dos pantallas sacan sus opciones de SECCIONES")
_ui = ast.parse(io.open("core/library_ui.py", encoding="utf-8").read())
_usan = {}
for n in ast.walk(_ui):
    if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "selectbox":
        _k = [kw.value.value for kw in n.keywords
              if kw.arg == "key" and isinstance(kw.value, ast.Constant)]
        if _k and _k[0] in ("lib_seccion", "lib_up_sec"):
            _usan[_k[0]] = any(isinstance(x, ast.Attribute) and x.attr == "SECCIONES"
                               for a in n.args for x in ast.walk(a))
chk("se encontraron los dos desplegables (si no, esto pasaría en vacío)",
    set(_usan) == {"lib_seccion", "lib_up_sec"}, _usan)
chk("el filtro y el alta leen LIB.SECCIONES", all(_usan.values()), _usan)


# ═════════════════════════════════════════════════════════════════
sec("4. La carga en lote, ejecutada entera contra una hoja y un Drive de mentira")
_ruta = os.path.join(RAIZ, "..", "guardianes", "sueltos", "importar_biblioteca.py")
_spec = importlib.util.spec_from_file_location("importar_biblioteca", _ruta)
IMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(IMP)
os.chdir(RAIZ)

_tmp = tempfile.mkdtemp(prefix="v520_")
os.makedirs(os.path.join(_tmp, "Pit"))
_fotos = []
for i in range(1, 4):
    k = "L%04d" % i
    io.open(os.path.join(_tmp, "Pit", k + ".jpg"), "wb").write(b"\xff\xd8fake\xff\xd9")
    _fotos.append({"clave": k, "archivo": os.path.join("Pit", k + ".jpg")})
json.dump({"fotos": _fotos, "casi_repetidas": []},
          io.open(os.path.join(_tmp, "_indice.json"), "w", encoding="utf-8"))


def _clasif(secc="Setting out", pend=False):
    io.open(os.path.join(_tmp, "_clasificacion.py"), "w", encoding="utf-8").write(
        "C = {\n"
        "  'L0001': (%r, 'photo', 'Plumb line', 'n1', '', ''),\n"
        "  'L0002': ('Installation equipment', 'photo', 'Tirak', '', '', ''),\n"
        "  'L0003': ('Pit', 'manual', 'Pit ladder', '', 'Sematic', 'X1'),\n"
        "}\n"
        "def marca_final(k):\n"
        "    return C[k][4] or ('' if k == 'L0002' else 'Schindler')\n"
        "def pendientes():\n"
        "    return %r\n" % (secc, ["L0001"] if pend else []))


_subidas = []
IMP.dr.folder = lambda name: "CARPETA"


def _upload(folder, name, data, mime):
    _subidas.append(name)
    return "DRV-" + name


IMP.dr.upload_to = _upload
IMP.LIB.marcas = lambda incluir_inactivos=False: ["Schindler"]
_catalogo = []
IMP.LIB.add_modelo = lambda m, mo: (_catalogo.append((m, mo)), (True, "ok"))[1]
IMP.LIB._invalidate = lambda: None
IMP.hojas.ids_referenciados = lambda pref, propia="": {"LIB-0002"}
IMP.timeclock._now = lambda: "2026-09-28 12:00:00"
IMP.time.sleep = lambda s: None


def _corre(ws, *args):
    IMP.LIB._ws = lambda: (ws, None)
    sys.argv = ["importar_biblioteca.py", _tmp] + list(args)
    try:
        IMP.main()
        return "ok"
    except SystemExit as e:
        return "abort: %s" % e


_clasif()
_w = _WS()
chk("el ensayo no escribe nada", _corre(_w, "--ensayo") == "ok" and not _w.filas
    and not _subidas, (_w.filas, _subidas))
chk("la carga corre", _corre(_w) == "ok")
_ids = [f[0] for f in _w.filas]
chk("tres fichas, con el ID referenciado SALTADO (LIB-0002, v427)",
    _ids == ["LIB-0001", "LIB-0003", "LIB-0004"], _ids)
_por = {f[8]: dict(zip(LIB.HEADERS, f)) for f in _w.filas}
chk("la llave es '<clave>.jpg' y el archivo va con su DriveID",
    _por.get("L0001.jpg", {}).get("DriveID") == "DRV-L0001.jpg", _por.get("L0001.jpg"))
chk("sección, marca y notas llegan a su columna",
    (_por["L0001.jpg"]["Section"], _por["L0001.jpg"]["Brand"], _por["L0001.jpg"]["Notes"])
    == ("Setting out", "Schindler", "n1"), _por["L0001.jpg"])
chk("lo ajeno va sin marca", _por["L0002.jpg"]["Brand"] == "", _por["L0002.jpg"])
chk("la marca que falta entra al catálogo (sin ella el filtro no la ofrece)",
    ("Sematic", "") in _catalogo, _catalogo)
chk("se escribió en UNA tanda, no fila a fila", _w.escrituras == 1, _w.escrituras)

_n_sub = len(_subidas)
chk("volver a correr NO repite nada (ni fichas ni archivos)",
    _corre(_w) == "ok" and len(_w.filas) == 3 and len(_subidas) == _n_sub,
    (len(_w.filas), len(_subidas)))

# Cortada entre Drive y la hoja: el estado evita duplicar en Drive.
_w2 = _WS()
chk("con el Drive ya subido (estado local) y la hoja vacía, no se resube nada",
    _corre(_w2) == "ok" and len(_w2.filas) == 3 and len(_subidas) == _n_sub,
    (len(_w2.filas), len(_subidas)))

_r = _corre(_WS(cab=["ID", "Brand", "Section", "Model"] + LIB.HEADERS[4:]))
chk("⚠️ con otra cabecera NO escribe (la fila es posicional, v363)",
    _r.startswith("abort") and "cabecera" in _r, _r)
_clasif(secc="Plumbing")
_r = _corre(_WS())
chk("una sección fuera de la lista para la carga ENTERA antes de tocar nada",
    _r.startswith("abort") and "Plumbing" in _r and len(_subidas) == _n_sub, _r)
_clasif(pend=True)
_r = _corre(_WS())
chk("con algo sin decidir, no sube", _r.startswith("abort") and "sin sección" in _r, _r)
shutil.rmtree(_tmp, ignore_errors=True)

# ⚠️ Y que el importador no lleve datos dentro: el repo se sube entero (git add).
_src = io.open(_ruta, encoding="utf-8").read()
chk("el importador no apunta a la carpeta de datos (se le pasa por argumento)",
    "CopeX" not in _src and "Library_subida" not in _src)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
