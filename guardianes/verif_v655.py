# -*- coding: utf-8 -*-
"""v655 · Dependencias al día y limpieza (3ª versión de la revisión del código).

1. `requirements.txt` lleva los suelos de seguridad, y lo instalado los cumple.
2. Pillow solo ABRE JPEG, PNG y WEBP (`core/imagenes`), validado con un TIFF que antes sí abría.
3. Tiempo límite en todo SMTP y en todo cliente de Anthropic.
4. La búsqueda de carpetas de Drive escapa el nombre.
5. El tope de subida (50 MB) y el código muerto, fuera.

Nada sale a la red ni escribe.
"""
import ast
import io
import os
import sys
import tomllib

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


FICHEROS = [os.path.relpath(os.path.join(dp, fn), RAIZ).replace("\\", "/")
            for dp, _d, fs in os.walk(RAIZ) if "__pycache__" not in dp for fn in fs if fn.endswith(".py")]

# ═════════════════════════════════════════════════════════════════════════════
sec("1. Los suelos de seguridad")
from importlib.metadata import version                                   # noqa: E402
from packaging.requirements import Requirement                           # noqa: E402

_req = {}
for ln in src("requirements.txt").splitlines():
    ln = ln.split("#")[0].strip()
    if ln:
        r = Requirement(ln)
        _req[r.name.lower()] = r
# ⚠️ v657 · CADUCADO a propósito (2ª vez). En v655 el Cloud no arrancó y v656 volvió a lo de v654; el
# registro no servía (el Reboot lo borra), pero resolver como el Cloud (`libs_cloud.py`: uv, Linux)
# lo destapó: con `lxml>=6` el resolvedor elegía svglib 1.6.0, que trae pycairo, sin rueda para Linux.
# Se vigila: svglib por debajo de 1.6; cada suelo de seguridad, de UNA en UNA (`_ESPERAN` = los que
# aún no han subido: se vacía al subirlos); y lo instalado en local, dentro del rango (local = Cloud).
_SVG = _req.get("svglib")
chk("svglib por debajo de 1.6 (la 1.6.0 trae pycairo: el Cloud no la puede instalar)",
    _SVG is not None and _SVG.specifier.contains("1.5.1") and not _SVG.specifier.contains("1.6.0"), str(_SVG))
chk("svglib: lo instalado en local está dentro", _SVG is not None and _SVG.specifier.contains(version("svglib")))
# paquete: (suelo de seguridad, la versión justo por debajo, que ya no debe entrar)
_SUELO = {"pypdf": ("6.21.4", "6.21.3"), "cryptography": ("50.0.0", "49.0.0"),
          "pyarrow": ("23.0.1", "23.0.0"), "pillow": ("12.3.0", "12.2.0"), "lxml": ("6.1.0", "6.0.2")}
_ESPERAN = set()          # todas subidas, de una en una: pyarrow en v658, Pillow en v659 y lxml en v660
chk("lo que espera es parte de los suelos", _ESPERAN <= set(_SUELO), _ESPERAN)
for pkg, (suelo, debajo) in _SUELO.items():
    r = _req.get(pkg)
    if pkg in _ESPERAN:
        chk(f"{pkg}: todavía sin subir (no deja {suelo})", r is not None and not r.specifier.contains(suelo), str(r))
    else:
        chk(f"{pkg}: el suelo de seguridad puesto (deja {suelo}, no {debajo})",
            r is not None and r.specifier.contains(suelo) and not r.specifier.contains(debajo), str(r))
    chk(f"{pkg}: lo instalado en local ({version(pkg)}) está dentro (local = Cloud)",
        r is not None and r.specifier.contains(version(pkg)))
# lo que la limitación de formatos cubre mientras Pillow no pueda subir: ver la sección 2

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Pillow solo abre JPEG, PNG y WEBP")
from PIL import Image, UnidentifiedImageError                            # noqa: E402


def _bytes(fmt, **kw):
    b = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 10, 10)).save(b, fmt, **kw)
    return b.getvalue()


_TIFF, _GIF, _BMP = _bytes("TIFF"), _bytes("GIF"), _bytes("BMP")
with Image.open(io.BytesIO(_TIFF)) as _im:
    chk("la sonda: ANTES de limitar, un TIFF se abre (lo que se prueba existe)", _im.format == "TIFF")
from core import imagenes as IM                                           # noqa: E402

IM.limitar_pillow()
IM.limitar_pillow()


def _abre(datos):
    try:
        with Image.open(io.BytesIO(datos)) as im:
            im.load()
            return im.format
    except UnidentifiedImageError:
        return None


chk("tras limitar, un TIFF, un GIF y un BMP ya NO se abren", (_abre(_TIFF), _abre(_GIF), _abre(_BMP)) == (None, None, None),
    (_abre(_TIFF), _abre(_GIF), _abre(_BMP)))
chk("...y JPEG, PNG y WEBP sí", (_abre(_bytes("JPEG")), _abre(_bytes("PNG")), _abre(_bytes("WEBP"))) == ("JPEG", "PNG", "WEBP"))
chk("guardar sigue igual (un PNG se escribe)", len(_bytes("PNG")) > 50)
try:
    IM.abrir(_TIFF)
    _r = "abrió"
except UnidentifiedImageError:
    _r = "no"
chk("`imagenes.abrir` con un TIFF (aunque se llame foto.jpg) no lo abre", _r == "no", _r)
with IM.abrir(_bytes("JPEG")) as _im:
    chk("`imagenes.abrir` abre un JPEG", _im.format == "JPEG")
_mpo = io.BytesIO()
Image.new("RGB", (8, 8), "red").save(_mpo, "MPO", save_all=True, append_images=[Image.new("RGB", (8, 8), "blue")])
with IM.abrir(_mpo.getvalue()) as _im:
    chk("...y una foto MPO de móvil (lo abre el de JPEG), con sus 2 cuadros",
        _im.format == "MPO" and getattr(_im, "n_frames", 1) == 2, (_im.format, getattr(_im, "n_frames", 1)))
_app = src("app.py")
chk("app.py limita Pillow ANTES de abrir el icono", 0 < _app.find("_imagenes.limitar_pillow()") < _app.find("Image.open("),
    (_app.find("_imagenes.limitar_pillow()"), _app.find("Image.open(")))
_open = []
for rel in FICHEROS:
    for c in ast.walk(ast.parse(src(rel))):
        if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "open" and getattr(c.func.value, "id", "") == "Image":
            _open.append((rel, c.lineno))
chk("`Image.open` directo solo en app.py (el icono) y en core/imagenes.py",
    {r for r, _ in _open} == {"app.py", "core/imagenes.py"}, _open)
chk("las fotos subidas (asistente y miniaturas) van por `imagenes.abrir`",
    "imagenes.abrir(archivo)" in src("core/chat_ui.py") and "imagenes.abrir(datos)" in src("core/drive_store.py"))

# ═════════════════════════════════════════════════════════════════════════════
sec("3. Tiempo límite en SMTP y en Anthropic")
_smtp, _ant = [], []
for rel in FICHEROS:
    for c in ast.walk(ast.parse(src(rel))):
        if not isinstance(c, ast.Call):
            continue
        nom = getattr(c.func, "attr", getattr(c.func, "id", ""))
        base = getattr(getattr(c.func, "value", None), "id", "")
        kws = {k.arg for k in c.keywords}
        if nom in ("SMTP", "SMTP_SSL") and base == "smtplib":
            _smtp.append((rel, c.lineno, "timeout" in kws))
        if nom == "Anthropic" and base == "anthropic":
            _ant.append((rel, c.lineno, "timeout" in kws))
chk("todo `smtplib.SMTP` lleva timeout (y hay alguno)", _smtp and all(x[2] for x in _smtp), _smtp)
chk("todo `anthropic.Anthropic` lleva timeout (y hay alguno)", _ant and all(x[2] for x in _ant), _ant)

# ═════════════════════════════════════════════════════════════════════════════
sec("4. La búsqueda de carpetas de Drive")
from core import drive_store as DS                                         # noqa: E402

_cap = []


class _R:
    def raise_for_status(self):
        pass

    def json(self):
        return {"files": []}


_o = (DS.requests.get, DS._headers)
DS.requests.get = lambda url, **kw: (_cap.append(kw.get("params", {}).get("q", "")) or _R())
DS._headers = lambda: {}
try:
    DS._find_folder("O'Brien \\ Co", parent="pa'dre")
finally:
    DS.requests.get, DS._headers = _o
chk("el nombre y la carpeta madre, escapados en la consulta",
    _cap and "name = 'O\\'Brien \\\\ Co'" in _cap[0] and "'pa\\'dre' in parents" in _cap[0], _cap)

# ═════════════════════════════════════════════════════════════════════════════
sec("5. El tope de subida y el código muerto")
_cfg = tomllib.loads(src(".streamlit/config.toml"))
chk("config.toml: maxUploadSize = 50", _cfg.get("server", {}).get("maxUploadSize") == 50, _cfg.get("server"))
from core import orders, admin_digest, vocabulario                         # noqa: E402

chk("fuera `orders.sin_gasto`, `admin_digest.grupos_fuera_del_maestro` y `vocabulario._tokens`",
    not hasattr(orders, "sin_gasto") and not hasattr(admin_digest, "grupos_fuera_del_maestro")
    and not hasattr(vocabulario, "_tokens"))
_restos = [rel for rel in FICHEROS
           if any(isinstance(n, (ast.Name, ast.Attribute)) and getattr(n, "id", getattr(n, "attr", "")) in
                  ("sin_gasto", "grupos_fuera_del_maestro") for n in ast.walk(ast.parse(src(rel))))]
chk("...y nadie los nombra en el código", _restos == [], _restos)
chk("la lista de órdenes de la obra sigue avisando de una orden recibida sin gasto (lo que hacía falta)",
    "O.completar_gasto(" in src("core/projects_ui.py"))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLOS: " + " | ".join(FALLOS)))
sys.exit(1 if FALLOS else 0)
