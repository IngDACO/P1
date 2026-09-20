"""v403 · Firmar el Pre-Start al llegar tarde a la obra.

Lo que hay que proteger:
  (a) `pendiente_de_firma` distingue las DOS preguntas (¿hay que hacer la charla?
      vs ¿tengo que firmarla yo?) y no confunde a dos personas por el nombre;
  (b) el PDF se ANEXA, nunca se regenera: las firmas originales solo viven dentro
      del PDF ya emitido, así que rehacerlo las borraría;
  (c) el orden de escrituras: subir el nuevo ANTES de tocar la fila, borrar el
      viejo DESPUÉS (lección de v343 — mejor un archivo de más que uno de menos);
  (d) que se EJECUTE (importar no ejecuta, v378).

⚠️ La escritura va contra un worksheet SIMULADO, no contra un Pre-Start real:
`firmar` borra el PDF anterior de Drive y eso no tiene vuelta atrás.
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}

from core import prestart as PS                                   # noqa: E402
from core import prestart_pdf as PPDF                             # noqa: E402

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) el nombre se compara con criterio ==")
check("acentos", PS._norm_nombre("José Pérez"), PS._norm_nombre("jose perez"))
check("espacios de más", PS._norm_nombre("  Ana   Ruiz "), "ana ruiz")
check("...pero no mezcla a dos personas",
      PS._norm_nombre("Ana Ruiz") == PS._norm_nombre("Ana Ruz"), False)

print("\n== 2) las DOS preguntas son distintas ==")
import datetime as _dt                                            # noqa: E402
HOY = PS.clock.today("cliente1")
FILA = {"ID": "PS-0009", "ProjectID": "PRJ-0012", "Group": "cliente1",
        "Date": HOY.strftime("%Y-%m-%d"), "FacilitatedBy": "Ana Ruiz",
        "Location": "Level 3", "DriveID": "drv-viejo", "File": "24082026 AR.pdf",
        "Attendees": '[{"name": "Ana Ruiz", "initial": "AR", "firmado": true}]'}
_orig_records = PS._records
PS._records = lambda: [FILA]
try:
    check("hay Pre-Start hoy → `hecho_hoy` dice que NO hay que hacerlo",
          PS.hecho_hoy("PRJ-0012", "cliente1"), True)
    check("quien YA firmó no tiene nada pendiente",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", "Ana Ruiz"), {})
    check("...ni escribiéndolo distinto",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", "  ANA  RUIZ "), {})
    _p = PS.pendiente_de_firma("PRJ-0012", "cliente1", "Luis Gómez")
    check("quien NO firmó sí lo tiene", bool(_p), True)
    check("...y trae el Pre-Start al que añadirse", _p.get("id"), "PS-0009")
    check("otra obra no arrastra nada",
          PS.pendiente_de_firma("PRJ-0001", "cliente1", "Luis Gómez"), {})
    check("sin persona no se inventa un pendiente",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", ""), {})
    # ⚠️ v406 · DOS charlas el mismo día en la misma obra. Nada lo impide (dos turnos,
    # o un duplicado), y mirando solo la primera fila quien firmaba la SEGUNDA seguía
    # viendo «te falta firmar» para siempre.
    FILA2 = dict(FILA, ID="PS-0010", FacilitatedBy="Luis Gómez",
                 Attendees='[{"name": "Luis Gomez", "initial": "LG", "firmado": true}]')
    PS._records = lambda: [FILA, FILA2]
    check("quien firmó la SEGUNDA no tiene nada pendiente",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", "Luis Gómez"), {})
    check("...y quien firmó la PRIMERA tampoco",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", "Ana Ruiz"), {})
    _p2 = PS.pendiente_de_firma("PRJ-0012", "cliente1", "Nadie Aún")
    check("quien no firmó NINGUNA sí, y se le ofrece la más reciente",
          _p2.get("id"), "PS-0010")
    check("...y se le dice que hay más de una", _p2.get("otras"), 1)

    # ⚠️ un Pre-Start de AYER no vale para hoy
    PS._records = lambda: [FILA]
    FILA_AYER = dict(FILA, Date=(HOY - _dt.timedelta(days=1)).strftime("%Y-%m-%d"))
    PS._records = lambda: [FILA_AYER]
    check("el de ayer no cuenta: hay que HACER la charla",
          PS.hecho_hoy("PRJ-0012", "cliente1"), False)
    check("...y no se pide firmar el de ayer",
          PS.pendiente_de_firma("PRJ-0012", "cliente1", "Luis Gómez"), {})
finally:
    PS._records = _orig_records

print("\n== 3) el anexo se GENERA de verdad y se ANEXA, no reemplaza ==")
from reportlab.lib.pagesizes import A4                            # noqa: E402
from reportlab.pdfgen import canvas as _cv                        # noqa: E402
_b = io.BytesIO()
_c = _cv.Canvas(_b, pagesize=A4)
_c.drawString(80, 700, "PRE-START ORIGINAL — firma de Ana Ruiz")
_c.showPage()
_c.save()
ORIGINAL = _b.getvalue()

anexo = PPDF.generate_anexo_firmas_pdf({
    "marca": "cliente1", "ps_id": "PS-0009", "fecha": "2026-08-24",
    "proyecto": "PRJ-0012", "location": "Level 3",
    "firmas": [{"name": "Luis Gómez", "initial": "LG", "sig": None, "hora": "10:35"}]})
check("el anexo es un PDF", anexo[:4], b"%PDF")

from pypdf import PdfReader, PdfWriter                            # noqa: E402
_w = PdfWriter()
for _p in PdfReader(io.BytesIO(ORIGINAL)).pages:
    _w.add_page(_p)
for _p in PdfReader(io.BytesIO(anexo)).pages:
    _w.add_page(_p)
_o = io.BytesIO()
_w.write(_o)
FINAL = _o.getvalue()
_lect = PdfReader(io.BytesIO(FINAL))
check("el resultado tiene el original MÁS el anexo", len(_lect.pages),
      len(PdfReader(io.BytesIO(ORIGINAL)).pages) + len(PdfReader(io.BytesIO(anexo)).pages))
_txt0 = _lect.pages[0].extract_text() or ""
check("⚠️ la página original sigue intacta", "PRE-START ORIGINAL" in _txt0, True)
_txt1 = _lect.pages[-1].extract_text() or ""
check("el anexo nombra a quien firmó tarde", "Luis" in _txt1 and "10:35" in _txt1, True)
# ⚠️ CADUCADO en v436 y actualizado (regla v385): buscaba el literal español «no
# modifica», y el anexo pasó al INGLÉS con la traducción de los documentos. Lo que la
# regla protege es que el anexo DIGA que se añade al Pre-Start original sin
# modificarlo — no en qué idioma lo dice. Se acepta cualquiera de los dos, porque el
# día que se traduzca al español volvería a estar en español.
check("...y dice que no modifica el original",
      ("no modifica" in _txt1) or ("does not modify" in _txt1), True)

print("\n== 4) EJECUTAR `firmar` con worksheet SIMULADO ==")


class WSFalso:
    def __init__(self, filas):
        self.filas = [dict(f) for f in filas]
        self.escrituras = []

    def get_all_records(self, **kw):
        return [dict(f) for f in self.filas]

    def update_cell(self, fila, col, val):
        self.escrituras.append((fila, col, str(val)[:60]))
        self.filas[fila - 2][PS.HEADERS[col - 1]] = val

    # ⚠️ `submit` INSERTA, así que sin esto el caso de `forzar` fallaba y parecía que
    # el código no dejaba pasar la segunda charla. Era el doble, no la app.
    def append_row(self, valores, **kw):
        self.filas.append(dict(zip(PS.HEADERS, [str(v) for v in valores])))


orden = []
_ws_falso = WSFalso([FILA])
_bak = (PS._ws, PS._invalidate)
PS._ws = lambda: _ws_falso
PS._invalidate = lambda: None


class DriveFalso:
    @staticmethod
    def is_available():
        return True

    @staticmethod
    def download(fid):
        orden.append(f"download:{fid}")
        return ORIGINAL

    @staticmethod
    def upload(pid, fname, data, mime):
        orden.append("upload")
        return "drv-nuevo"

    @staticmethod
    def delete(fid):
        orden.append(f"delete:{fid}")


import types                                                      # noqa: E402
import core                                                       # noqa: E402
from core import projects as _P_real                              # noqa: E402

# ⚠️ `from core import drive_store` resuelve por el ATRIBUTO del paquete, no solo por
# `sys.modules`: hay que poner los dos o el doble se ignora y el test tocaría Drive.
_fake_drive = types.SimpleNamespace(
    is_available=DriveFalso.is_available, download=DriveFalso.download,
    upload=DriveFalso.upload, delete=DriveFalso.delete)
_bak_drive = sys.modules.get("core.drive_store")
_bak_attr = getattr(core, "drive_store", None)
_bak_add = _P_real.add_document
sys.modules["core.drive_store"] = _fake_drive
core.drive_store = _fake_drive
_P_real.add_document = lambda *a, **k: orden.append("add_document")

try:
    r = PS.firmar("PS-0009", "cliente1", "Luis Gómez", "LG", None, "lgomez")
    check("firmar devuelve ok", r.get("ok"), True)
    check("el PDF resultante trae las dos páginas",
          len(PdfReader(io.BytesIO(r["pdf"])).pages), 2)
    _as = _ws_falso.filas[0]["Attendees"]
    check("⚠️ Ana Ruiz SIGUE en la lista (se añade, no se reemplaza)",
          "Ana Ruiz" in _as, True)
    check("...y ahora también Luis", "Luis" in _as, True)
    check("la firma tardía queda marcada como tal", '"tarde": true' in _as.lower(), True)
    check("la fila apunta al PDF nuevo", _ws_falso.filas[0]["DriveID"], "drv-nuevo")
    print(f"         orden real de operaciones: {orden}")
    check("⚠️ se sube el nuevo ANTES de borrar el viejo (v343)",
          orden.index("upload") < orden.index("delete:drv-viejo"), True)
    check("un Pre-Start inexistente no rompe: devuelve error",
          bool(PS.firmar("PS-9999", "cliente1", "X", "X", None, "u").get("error")), True)
    check("sin nombre tampoco",
          bool(PS.firmar("PS-0009", "cliente1", "", "", None, "u").get("error")), True)
finally:
    PS._ws, PS._invalidate = _bak
    _P_real.add_document = _bak_add
    if _bak_drive is not None:
        sys.modules["core.drive_store"] = _bak_drive
    else:
        sys.modules.pop("core.drive_store", None)
    # ⚠️ Restaurar SIEMPRE el atributo del paquete: si el doble se queda puesto, el
    # intérprete revienta al cerrar (salida 255) y la suite lo cuenta como ROJO aunque
    # el guardián haya impreso TODO OK. Un test que aprueba y devuelve error es peor
    # que uno que falla: parece ruido y se acaba ignorando.
    if _bak_attr is not None:
        core.drive_store = _bak_attr
    else:
        try:
            del core.drive_store
        except Exception:
            pass

print("\n== 4b) v407 · no se cuela un SEGUNDO Pre-Start del día sin marcarlo ==")
_ws2 = WSFalso([FILA])
PS._ws = lambda: _ws2
_orig_rec = PS._records
PS._records = lambda: [FILA]          # ya hay uno hoy en PRJ-0012
try:
    _d = {"proyecto_id": "PRJ-0012", "grupo": "cliente1", "fecha": HOY,
          "hora": "13:00", "location": "L3", "facilitador": "Otro",
          "s1": {}, "s3": {}, "near_miss": "NO",
          "attendees": [{"name": "Zoe", "initial": "Z", "sig": None}],
          "creado_por": "zoe"}
    r1 = PS.submit(dict(_d))
    check("se BLOQUEA el segundo del día", r1.get("ok"), False)
    check("...y dice CUÁL es el que ya hay", r1.get("ya_hay"), "PS-0009")
    # ⚠️ CADUCADO por v447 (i18n F5c): el mensaje pasó al inglés. Lo que la
    # regla protege es que el bloqueo REMITA A FIRMAR en vez de dejar al usuario
    # sin salida — el duplicado se evita ofreciendo la alternativa, no negando.
    check("...y el mensaje invita a firmarlo en vez de duplicar",
          ("sign it" in (r1.get("error") or "").lower()
           or "fírmalo" in (r1.get("error") or "").lower()), True)
    check("no se escribió nada", len(_ws2.filas), 1)
    # ⚠️ y la salida explícita SÍ deja pasar: una segunda charla real existe
    r2 = PS.submit(dict(_d, forzar=True))
    check("con `forzar` se registra igual (otro turno)", r2.get("ok"), True)
finally:
    PS._records = _orig_rec
    PS._ws = lambda: _ws_falso

print("\n== 5) compila e importa ==")
import importlib                                                  # noqa: E402
import pathlib                                                    # noqa: E402
import py_compile                                                 # noqa: E402
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    if p.stem in ("drive_store",):        # simulado arriba
        continue
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:                                        # noqa: BLE001
        malos.append((p.stem, repr(e)[:80]))
check(f"{len(mods) - 1 - len(malos)}/{len(mods) - 1} modulos + app.py", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
