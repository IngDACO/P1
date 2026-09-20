"""v459 — «Engineer in charge» pasa a ser «Head installer/s», elegidos de una LISTA.

Petición del usuario: *«cambiar en proyectos el engineer in charge por head installer/s,
el cual o los cuales deben ser seleccionados de la lista de usuarios»*, y su regla más
amplia: **«lo único que debe ser de texto libre es cuando estamos creando algo nuevo; de
resto todo debe ser de listas»**.

## Por qué importa que sea una lista

Escrito a mano, el responsable de una obra era una cadena que no casaba con nadie: una
errata («Javer López») no da error, simplemente deja el proyecto con un responsable que
no existe en el sistema y que ningún filtro puede cruzar.

## Qué se guarda

Los **LOGIN**, separados por `;` (igual que `CampoAsignados`). ⚠️ El login ES la
identidad: dos personas pueden llamarse igual —ya pasó con «Mei Chen» (v413)— y un nombre
puede cambiar, mientras que el login no. El nombre se resuelve solo al MOSTRAR, con
`head_installers_label`, que además desempata homónimos.

⚠️ La columna sigue llamándose `Ingeniero`: renombrarla obligaría a tocar los ~10 sitios
que la leen sin ganar nada, y el nombre de una columna es un identificador interno, no una
etiqueta de pantalla (regla v232/v442: se cambia lo que se MUESTRA, nunca la clave).

## Quién puede serlo

**Head installer/s → solo usuarios de CAMPO** (decisión del usuario): es quien va a obra.
**Responsable de una localización → cualquiera del grupo**: una oficina o un almacén los
suele llevar alguien de administración, así que filtrar por campo dejaría fuera al
responsable real.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
CORE = RAIZ / "core"
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


_pu = (CORE / "projects_ui.py").read_text(encoding="utf-8")

print("== 1. Ningún texto libre para el responsable ==")
# ⚠️ La regla del usuario: solo el NOMBRE de la cosa nueva es texto libre. Elegir una
# persona que YA existe es siempre de lista.
chk('text_input(t("Engineer' not in _pu, "no queda `text_input` para «Engineer»")
chk('text_input(t("Person in charge' not in _pu,
    "…ni para «Person in charge» (ni al crear ni al editar una localización)")
_a = ast.parse(_pu)
_ms = [n for n in ast.walk(_a) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", None) == "multiselect"
       and n.args and "Head installer" in ast.dump(n.args[0])]
chk(len(_ms) >= 2, f"el alta Y la edición de obra usan multiselect ({len(_ms)})")

print("\n== 2. Se guardan los LOGIN, unidos por «;» ==")
chk(_pu.count('";".join(ing)') >= 2, "los dos guardados de obra unen con «;»")
chk(_pu.count('";".join(resp)') >= 2, "…y los dos de localización, también")
chk("resp.strip()" not in _pu, "no queda el guardado de texto libre")

print("\n== 3. Quién sale en cada lista ==")
# ⚠️ Por AST y sobre el CUERPO de cada función: `== "campo"` aparece en 5 sitios del
# módulo, así que buscarlo por subcadena aprobaría aunque `_campos_de` dejara de filtrar.
def _fn(nombre):
    return next((n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
                 and n.name == nombre), None)


def _consts(fn):
    """Los literales de texto del cuerpo. ⚠️ NO se mira `ast.dump`: usa `repr`, o sea
    comillas SIMPLES, así que buscar `'"campo"'` daba FALLO con el código correcto —
    el test fallando por su propio formato (v363, v372)."""
    return {n.value for n in ast.walk(fn)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


_cf, _uf = _fn("_field_users"), _fn("_usuarios_de")
chk(_cf is not None and "field" in _consts(_cf),
    "head installer: SOLO usuarios de campo (decisión del usuario)")
chk(_uf is not None and "Role" not in _consts(_uf),
    "responsable de localización: TODOS los del grupo, sin filtrar por rol")

# ⚠️ UNA sola definición del filtro. Yo mismo escribí `_campos_de` sin mirar que
# `_field_users` ya existía, dejando TRES copias en el módulo: es el patrón de los
# cinco `_num` divergentes de v323, donde dos de las divergencias eran fallos de
# dinero. Dos definiciones de lo mismo no fallan hoy; divergen mañana.
_filtros = [n for n in ast.walk(_a)
            if isinstance(n, ast.Compare)
            and any(isinstance(c, ast.Constant) and c.value == "field"
                    for c in n.comparators)
            and "Role" in ast.dump(n.left)]
chk(len(_filtros) == 1,
    f"el filtro «rol == campo» se define UNA sola vez ({len(_filtros)})")

print("\n== 4. Los helpers, EJECUTADOS (importar no ejecuta, v378) ==")
import streamlit as st  # noqa: E402
st.session_state["auth"] = {"usuario": "dacox", "rol": "owner", "grupo": ""}
from core import projects as P, projects_ui as PU  # noqa: E402

chk(P.head_installers({"HeadInstallers": "  a ; ; b "}) == ["a", "b"],
    "head_installers limpia espacios y entradas vacías")
chk(P.head_installers({}) == [], "…y devuelve [] si no hay nada")
# ⚠️ Un login que ya no existe NO desaparece del informe: se muestra crudo.
chk(P.head_installers_label({"HeadInstallers": "fantasma"}, "cliente1") == "fantasma",
    "un login desconocido se muestra crudo, no se pierde")
chk(isinstance(PU._field_users("noexiste"), list),
    "_field_users degrada a lista vacía si el grupo no existe")
chk(isinstance(PU._usuarios_de("cliente1"), list), "_usuarios_de ejecuta")
chk(isinstance(PU._etq_us(["x"]), dict), "_etq_us ejecuta")

print("\n== 5. Lo que sale FUERA de la app ==")
# ⚠️ Que el documento diga «Head installer/s» NO basta: hay que comprobar que el
# VALOR llega resuelto. `session_state["ingeniero"]` es lo que pintan el informe del
# CLIENTE y el correo, y `survey_ui` lo llenaba con la columna CRUDA — o sea que el
# documento que se manda al cliente habría dicho «campo1;mchen». Media unificación
# otra vez (v419, v454): la regla aplicada en projects_ui y no en su gemelo.
_sv = (CORE / "survey_ui.py").read_text(encoding="utf-8")
chk(_sv.count('get("Ingeniero"') == 0,
    "survey_ui no lee la columna cruda para el informe")
chk("head_installers_label" in _sv,
    "…la resuelve con head_installers_label")
# Y ningún módulo puede volver a meter el valor crudo en la clave del informe.
_crudos = []
for _f in sorted(CORE.glob("*.py")):
    for _n in ast.walk(ast.parse(_f.read_text(encoding="utf-8"))):
        if not (isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Call)):
            continue
        _t = ast.unparse(_n.targets[0]) if _n.targets else ""
        if "ingeniero" in _t and "HeadInstallers" in ast.unparse(_n.value):
            _crudos.append(f"{_f.name}:{_n.lineno}")
chk(not _crudos, f"nadie mete el valor CRUDO en la clave del informe ({_crudos})")

for fn, viejo, nuevo in (("email_notify.py", "<strong>Engineer:</strong>", "Head installer/s"),
                         ("user_report.py", 'd("Engineer in charge")', "Head installer/s")):
    _s = (CORE / fn).read_text(encoding="utf-8")
    chk(viejo not in _s, f"{fn}: ya no dice «Engineer»")
    chk(nuevo in _s, f"{fn}: dice «Head installer/s»")

print("\n== 6. El PDF del CLIENTE, GENERADO y LEÍDO ==")
# ⚠️ Medir sobre la SALIDA, no sobre el código que la produce: un barrido del fuente
# ya se dejó cinco etiquetas en v438. Aquí se genera el informe de verdad y se lee su
# texto.
# ⚠️ Con params SINTÉTICOS a propósito: así el chequeo no depende de que la demo tenga
# datos — que es justo lo que dejó a verif_v437/v448 sin poder afirmar nada.
# ⚠️ Y sin gastar IA: se le pasa `interpretation_user` ya hecho.
import io  # noqa: E402
from core import user_report  # noqa: E402

_ETQ = "Ana Pérez, Mei Chen"      # lo que head_installers_label produce
_par = {"PROYECTO": "G", "CLIENTE": "C", "UBICACION": "U", "MODELO": "M", "NS": 2,
        "INGENIERO": _ETQ,
        "BKS": 1600, "RAIL": 62, "TKSW": 965, "SF1": 51, "SF2": 51, "BS": 1998,
        "BSR": 1998, "BT": 900, "FRAME": 30, "TS": 1750, "TK": 1400, "TKA": 100,
        "TKS": 30, "TSW": 100, "FS": 100, "OFFSET_CABIN": 0, "OFFSET_SIDE": "L",
        "SG": 300, "TG": 60, "OMEGA_SIDE": "R", "WALL_LIMITING": False}
_cal = {"LIMIT_WR": 82.0, "LIMIT_WL": 82.0, "LIMIT_FR": 815.0, "LIMIT_FL": 815.0,
        "LIMIT_OR": 300.0, "LIMIT_OL": 300.0, "CS": 1500.0, "TL": 1630.0,
        "TLBC": 1700.0, "BC_CALC": 70.0}
_opt = {"best": {"rl": 0.0, "fb": 0.0, "total_off": 0, "modified": [
        {"WR": 90.0, "FR": 820.0, "OR": 290.0, "WL": 90.0, "FL": 820.0,
         "OL": 290.0}]}, "solutions": [], "log": []}
_lm = {"WR": "LIMIT_WR", "FR": "LIMIT_FR", "OR": "LIMIT_OR",
       "WL": "LIMIT_WL", "FL": "LIMIT_FL", "OL": "LIMIT_OL"}
_int = {"resumen": ".", "desplazamientos": ".", "cortes": ".",
        "implementacion": ".", "verificacion": ".", "_ok": True}
try:
    _pdf = user_report.generate_user_report(
        _par, _cal, _opt, _lm, ["WR", "FR", "OR", "WL", "FL", "OL"], _int)
    _b = _pdf.getvalue() if hasattr(_pdf, "getvalue") else _pdf
    from pypdf import PdfReader
    _txt = "".join((_p.extract_text() or "") + chr(10)
                   for _p in PdfReader(io.BytesIO(_b)).pages)
except Exception as _e:
    _txt = ""
    chk(False, f"el informe del cliente se genera ({type(_e).__name__}: {_e})")
if _txt:
    chk(_ETQ in _txt, "el PDF pinta el NOMBRE que recibe, no otra cosa")
    chk("Head installer/s" in _txt, "…bajo la etiqueta «Head installer/s»")
    # El pie de cada página lo repite: si se rompiera, saldría «Prepared by: —».
    chk(f"Prepared by: {_ETQ}" in _txt, "…y el pie «Prepared by» también")
    chk(";" not in _ETQ or ";" not in _txt, "no aparece la forma con «;» de la hoja")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
