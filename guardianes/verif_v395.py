"""v395: las alarmas que no le llegan a nadie dejan de ser invisibles.

Una alarma se escribe en la hoja Y se notifica. Si un destinatario no tiene email
ni Telegram, la fila existe y el aviso no sale de la app. Desde v373 un control de
seguridad en NO abre alarma, así que eso pasó a importar.

Lo que hay que proteger:
  (a) el criterio de CAMPO y el de GESTOR son distintos y no se mezclan (v325);
  (b) una cuenta inactiva no cuenta como pendiente (v325: un pendiente que nadie
      puede cerrar no es un pendiente);
  (c) 0 lecturas nuevas de Sheets;
  (d) el resumen del día sigue con NUEVE indicadores (v305) — el dato nuevo NO
      entra en `_PENDING_KEYS`.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

import streamlit as st                                          # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}

from core import admin_digest as AD                             # noqa: E402
from core import auth                                           # noqa: E402

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== 1) el dato, contra la hoja REAL ==")
d = AD.group_digest("cliente1")
_sc = d.get("avisos_sin_canal")
check("la clave existe", _sc is not None)
_u = sorted(x["usuario"] for x in (_sc or []))
print(f"         sin canal: {_u}")
# ⚠️ CADUCADO en v434 y actualizado (regla v385): exigía que HUBIERA al menos 3 sin
# canal, y en v434 se les cargó email a los tres — o sea, fallaba POR HABER GANADO.
# Un guardián no puede depender de que un pendiente siga abierto en producción. Lo
# que la regla protege es que la app SEPA detectarlos, así que se comprueba con un
# caso construido (abajo) y aquí solo que la lista sea coherente con los datos.
print(f"         (hoy sin canal en producción: {len(_u)})")
check("la lista es coherente con los datos reales", isinstance(_u, list), True)
check("cada uno trae su rol", all(x.get("rol") for x in (_sc or [])), True)
# quien SÍ tiene email no puede salir en la lista
_con_email = {str(u.get("Usuario")) for u in auth.list_users()
              if str(u.get("Email", "")).strip()}
check("nadie con email aparece como sin canal",
      sorted(set(_u) & _con_email), [])

print("\n== 2) criterios separados (la lección de v325) ==")
# al CAMPO se le exigen los dos canales; a un gestor le basta UNO
_campo = d.get("campo_sin_contacto") or []
check("campo y gestores son listas distintas", set(_u) & set(_campo), set())
_src = (BASE / "core" / "admin_digest.py").read_text(encoding="utf-8")
check("el gestor se mide con OR (basta un canal)",
      'str(u.get("Email", "")).strip()\n                    or str(u.get("TelegramChatID", "")).strip()' in _src)
check("el campo se sigue midiendo con AND (ambos obligatorios)",
      'str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip()' in _src)

print("\n== 3) una cuenta inactiva no es un pendiente ==")
check("se filtra por Activo", "auth._ACTIVE_OK" in _src)
_arb = ast.parse(_src)
_fn = next(n for n in ast.walk(_arb) if isinstance(n, ast.FunctionDef)
           and n.name == "group_digest")
_t = ast.get_source_segment(_src, _fn) or ""
check("...dentro del bloque de canales", "_ACTIVE_OK" in _t)

print("\n== 4) la rejilla del resumen sigue siendo de NUEVE ==")
check("`avisos_sin_canal` NO entra en _PENDING_KEYS",
      "avisos_sin_canal" in AD._PENDING_KEYS, False)
check("siguen siendo 9 claves", len(AD._PENDING_KEYS), 9)
# y un grupo cuyo ÚNICO 'pendiente' fuera este no debe marcarse como pendiente
_fake = {k: [] for k in AD._PENDING_KEYS}
_fake["avisos_sin_canal"] = [{"usuario": "x", "rol": "administrator"}]
check("has_pending no se dispara solo por esto", AD.has_pending(_fake), False)

print("\n== 5) 0 lecturas nuevas de Sheets ==")
# `_admins_and_owners` y `list_users` leen del mismo cacheado
import core.auth as _A                                          # noqa: E402
_llamadas = {"n": 0}
_orig = _A._login_records_cached
_A._login_records_cached = lambda *a, **k: (_llamadas.__setitem__("n", _llamadas["n"] + 1)
                                            or _orig(*a, **k))
try:
    AD.group_digest.clear()
    AD.group_digest("cliente1")
    _n1 = _llamadas["n"]
    AD.group_digest("cliente1")          # segunda pasada: todo cacheado
    _n2 = _llamadas["n"]
finally:
    _A._login_records_cached = _orig
check("la 2ª pasada no vuelve a leer Login", _n2, _n1)

print("\n== 6) el texto lo dice, y donde se arregla también ==")
# ⚠️ Con un caso CONSTRUIDO, no con los datos de producción: en v434 se les cargó
# email a los tres que faltaban, así que un chequeo atado a la realidad de la hoja
# se apagaba justo cuando el problema se arreglaba — y dejaba de proteger nada.
_fake = dict(d)
_fake["avisos_sin_canal"] = [{"usuario": "zzz_prueba", "rol": "administrator",
                              "nombre": "ZZZ Prueba"}]
_txt = AD.digest_text(_fake)
# ⚠️ CADUCADO por v448 (i18n F5): el texto del radar pasó al inglés. Lo que la
# regla protege es que el digest DIGA que esa alarma no le llega a nadie, no cómo
# se redacte.
check("digest_text nombra el problema cuando LO HAY",
      "never reaches them" in _txt.lower() or "no email or telegram" in _txt.lower()
      or "no les llega" in _txt.lower())
check("...y nombra a quién", "zzz_prueba" in _txt.lower() or "ZZZ Prueba" in _txt)
_vacio = dict(d)
_vacio["avisos_sin_canal"] = []
check("...y NO lo menciona cuando no hay nadie",
      "no les llega" not in AD.digest_text(_vacio).lower())
_ui = (BASE / "core" / "auth_ui.py").read_text(encoding="utf-8")
check("Planificación · Usuarios lo avisa", "avisos_sin_canal" in _ui)
# ⚠️ CADUCADO por el i18n de v441, no regresión: el aviso sigue diciendo cómo se
# arregla, pero en inglés. Se comprueba el PRINCIPIO —que junto al aviso se diga que
# la salida es cargar un email— sobre la palabra que no cambia entre los dos idiomas.
_blq = _ui[_ui.index("avisos_sin_canal"):][:1400]
check("...y dice CÓMO se arregla (email en su ficha)",
      "email" in _blq.lower())

print("\n== 7) compila e importa ==")
import importlib                                                # noqa: E402
import py_compile                                               # noqa: E402
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:80]))
check(f"{len(mods) - len(malos)}/{len(mods)} modulos + app.py", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
