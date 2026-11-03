# -*- coding: utf-8 -*-
"""v648 · EL RESUMEN DEL DÍA, CADA MAÑANA, A QUIEN LO PIDA (03/11/2026). Decisión del usuario (punto 6, el último porque
le toca a él poner el secreto en GitHub): cada persona de la oficina lo activa para sí en Home; lo manda GitHub Actions
cada mañana por correo o Telegram, con el resumen de Home.

Sin la hoja, sin la API y sin mandar nada: todo sustituido y apuntado.
"""
import contextlib
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import auth, clock, hojas, notify, resumen_dia as RD, resumen_envio as RE, tenant   # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(os.path.dirname(RAIZ), rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


AHORA = [dt.datetime(2026, 11, 4, 7, 20)]
clock.now = lambda *a: AHORA[0]
clock.today = lambda *a: AHORA[0].date()


class Hoja:
    """Una hoja de mentira: lo que tiene, y lo que le escriben."""

    def __init__(self, filas):
        self.filas = [dict(f) for f in filas]
        self.lecturas, self.anadidas, self.lotes = 0, [], []

    def get_all_records(self, **k):
        self.lecturas += 1
        return [dict(f) for f in self.filas]

    def append_row(self, fila, **k):
        self.anadidas.append(list(fila))

    def batch_update(self, lote, **k):
        self.lotes.append([(c["range"], c["values"][0][0]) for c in lote])


sec("1. La hoja: en el libro de cada empresa, en el lote de lectura, y su lector no la crea")
chk("⚠️ en el lote (fuera de él, `registros` sin cabeceras la leería VACÍA para siempre)", RE.SHEET in hojas.HOJAS_LECTURA)
chk("no es global: cada empresa en SU libro", RE.SHEET.lower() not in __import__("core.timeclock", fromlist=["x"]).SHEETS_GLOBALES)
chk("columnas fijas, las nuevas irían al final", RE.HEADERS == ["User", "Group", "Language", "Active", "Since", "LastSent", "Updated"])
_src = leer("survey_app/core/resumen_envio.py")
chk("⚠️ el lector de Home va sin cabeceras (con ellas `get_sheet` la CREA)", "return hojas.registros(SHEET) or []" in _src)
chk("de 7 a 11, hora de la empresa", (RE.HORA_DESDE, RE.HORA_HASTA) == (7, 11))
chk("toca a las 7:00 y a las 10:59, no a las 6:59 ni a las 11:00",
    RE.toca(dt.datetime(2026, 1, 1, 7, 0)) and RE.toca(dt.datetime(2026, 1, 1, 10, 59))
    and not RE.toca(dt.datetime(2026, 1, 1, 6, 59)) and not RE.toca(dt.datetime(2026, 1, 1, 11, 0)))

sec("2. Pedirlo y dejarlo")
_inv = []
RE._invalidate = lambda: _inv.append(1)
H = Hoja([])
RE._ws = lambda: H
ok, msg = RE.suscribir("cliente1", "Admin2", "es", True)
chk("la primera vez, una fila nueva con todo", ok and H.anadidas == [["Admin2", "cliente1", "es", "YES", "2026-11-04 07:20", "", "2026-11-04 07:20"]],
    (ok, H.anadidas))
chk("⚠️ se decide dónde escribir leyendo FRESCO", H.lecturas == 1)
chk("y lo de Home se vuelve a leer", _inv == [1])
chk("lo dice, con la hora", ok and "every morning" in msg and "7:00" in msg, msg)
H = Hoja([{"User": "otro", "Group": "cliente1", "Active": "YES"},
          {"User": "admin2", "Group": "cliente1", "Language": "en", "Active": "NO", "Since": "2026-10-01 08:00", "LastSent": "2026-10-02 07:17"}])
RE._ws = lambda: H
ok, msg = RE.suscribir("cliente1", "Admin2", "es", True)
_l = dict(H.lotes[0]) if H.lotes else {}
chk("⚠️ ya tenía fila (aunque sea en minúsculas): se reactiva ESA, no se duplica", ok and not H.anadidas and _l.get("D3") == "YES", H.lotes)
chk("con el idioma de ahora y «desde» de nuevo", _l.get("C3") == "es" and _l.get("E3") == "2026-11-04 07:20" and _l.get("G3") == "2026-11-04 07:20", _l)
H.filas[1]["Active"] = "YES"
H.lotes.clear()
ok, msg = RE.suscribir("cliente1", "Admin2", "en", False)
_l = dict(H.lotes[0]) if H.lotes else {}
chk("quitarlo deja la fila con Active=NO (queda desde cuándo lo recibió)", ok and _l.get("D3") == "NO" and "E3" not in _l and not H.anadidas, H.lotes)
chk("...y lo dice", "no more morning summaries" in msg, msg)
H = Hoja([])
RE._ws = lambda: H
ok, msg = RE.suscribir("cliente1", "Admin2", "en", False)
chk("quitar lo que no estaba: nada que escribir", ok and not H.anadidas and not H.lotes)
ok, msg = RE.suscribir("cliente1", "Admin2", "fr", True)
chk("un idioma raro, en inglés", H.anadidas and H.anadidas[0][2] == "en", H.anadidas)
H = Hoja([])
ok, msg = RE.suscribir("cliente1", "", "en", True)
chk("⚠️ sin usuario, nada", not ok and not H.anadidas)
RE._ws = lambda: None
ok, msg = RE.suscribir("cliente1", "Admin2", "en", True)
chk("sin hoja, lo dice", not ok and msg)


class Roto(Hoja):
    def get_all_records(self, **k):
        raise RuntimeError("503")


RE._ws = lambda: Roto([])
ok, msg = RE.suscribir("cliente1", "Admin2", "en", True)
chk("si Google falla, lo dice y no lanza", not ok and msg)

sec("3. Mandarlo: a quién, cuándo y una vez")
FILAS = [
    {"User": "Admin2", "Group": "cliente1", "Language": "en", "Active": "YES", "LastSent": ""},            # fila 2: sí
    {"User": "Jefa", "Group": "cliente1", "Language": "es", "Active": "YES", "LastSent": "2026-11-03 07:17"},  # 3: sí (ayer)
    {"User": "Otra", "Group": "cliente1", "Language": "en", "Active": "YES", "LastSent": ""},              # 4: sí, sin canal
    {"User": "Hoy", "Group": "cliente1", "Language": "en", "Active": "YES", "LastSent": "2026-11-04 07:17"},  # 5: ya hoy
    {"User": "campo000", "Group": "cliente1", "Language": "en", "Active": "YES", "LastSent": ""},          # 6: es de campo
    {"User": "Baja", "Group": "cliente1", "Language": "en", "Active": "YES", "LastSent": ""},              # 7: inactiva
    {"User": "Fuera", "Group": "otra", "Language": "en", "Active": "YES", "LastSent": ""},                 # 8: otra empresa
    {"User": "Dejo", "Group": "cliente1", "Language": "en", "Active": "NO", "LastSent": ""},               # 9: lo quitó
]
USUARIOS = [{"User": "Admin2", "Role": "administrator", "Active": "SI"}, {"User": "jefa", "Role": "administrator", "Active": ""},
            {"User": "Otra", "Role": "administrator", "Active": "YES"}, {"User": "Hoy", "Role": "administrator", "Active": "SI"},
            {"User": "campo000", "Role": "field", "Active": "SI"}, {"User": "Baja", "Role": "administrator", "Active": "NO"},
            {"User": "Dejo", "Role": "administrator", "Active": "SI"}]
E = {}


def preparar(filas=FILAS, gen_ok=True):
    E.clear()
    E.update(gen=[], env=[], ws=0, reg=[], lu=[])
    hojas.registros = lambda titulo, *a, **k: (E["reg"].append((titulo, tenant.grupo_activo())), None if filas is None else [dict(f) for f in filas])[1]
    auth.list_users = lambda g=None: (E["lu"].append(g), [dict(u) for u in USUARIOS])[1]

    def _gen(g, u, idi, api_key=None):
        E["gen"].append((g, u, idi))
        return ({"titular": "TITULAR " + idi, "puntos": [{"texto": "PUNTO", "urgente": False, "ir": "none", "obra": ""}], "hora": "07:20"}, "")\
            if gen_ok else (None, "api")
    # v649 · el envío pide `del_dia` (que reutiliza lo de Home): se sustituye ESE, con el mismo apunte
    RD.del_dia = lambda g, u, idi, rehacer=False: _gen(g, u, idi)
    notify.notify_user = lambda u, asunto, lineas, link=None: (E["env"].append((u, asunto, list(lineas), link)),
                                                                 {"email": u != "Otra", "telegram": False})[1]
    notify._sec = lambda k, d="": "https://APP" if k == "APP_URL" else d
    E["hoja"] = Hoja([])

    def _ws():
        E["ws"] += 1
        return E["hoja"]
    RE._ws = _ws


preparar()
c = RE.enviar_empresa("cliente1")
_quien = [x[0] for x in E["env"]]
chk("⚠️ solo a administradores ACTIVOS de esa empresa que lo pidieron y no lo tienen hoy", sorted(_quien) == ["Admin2", "Jefa", "Otra"], _quien)
chk("las cuentas cuadran", c["enviados"] == 2 and c["sin_canal"] == 1 and c["ya_hoy"] == 1 and c["sin_permiso"] == 2 and c["fallos"] == 0, c)
chk("⚠️ UNA llamada al modelo por idioma, no por persona", sorted(E["gen"]) == [("cliente1", "Admin2", "en"), ("cliente1", "Jefa", "es")], E["gen"])
chk("cada uno, en SU idioma", next(x for x in E["env"] if x[0] == "Jefa")[2][0] == "TITULAR es"
    and next(x for x in E["env"] if x[0] == "Admin2")[2][0] == "TITULAR en")
_e = next(x for x in E["env"] if x[0] == "Admin2")
chk("el asunto de «Send it to me» y el enlace a la app", _e[1] == "🔔 Today's summary — cliente1" and _e[3] == "https://APP", _e)
chk("⚠️ dice por qué le llega y cómo dejarlo", any("untick it there to stop" in x for x in _e[2]) and "• PUNTO" in _e[2], _e[2])
_lote = E["hoja"].lotes[0] if E["hoja"].lotes else []
chk("⚠️ «enviado hoy» SOLO a quien le llegó, en su fila (col F = LastSent)", sorted(_lote) == [("F2", "2026-11-04 07:20"), ("F3", "2026-11-04 07:20")], _lote)
chk("las personas, del usuario de la empresa", E["lu"] == ["cliente1"], E["lu"])
AHORA[0] = dt.datetime(2026, 11, 4, 6, 40)
preparar()
c = RE.enviar_empresa("cliente1")
chk("⚠️ antes de las 7, nada (ni el modelo)", not E["env"] and not E["gen"] and c["fuera_de_hora"] == 6 and not E["hoja"].lotes, c)
preparar()
c = RE.enviar_empresa("cliente1", ignorar_hora=True)
chk("«ignorar la hora» (la prueba a mano) sí manda, y sigue siendo una vez al día", c["enviados"] == 2 and c["ya_hoy"] == 1, c)
AHORA[0] = dt.datetime(2026, 11, 4, 11, 5)
preparar()
c = RE.enviar_empresa("cliente1")
chk("a las 11, ya no", not E["env"] and c["fuera_de_hora"] == 6, c)
AHORA[0] = dt.datetime(2026, 11, 4, 7, 20)
preparar(gen_ok=False)
c = RE.enviar_empresa("cliente1")
chk("si el modelo falla, no se manda nada a medias ni se marca", not E["env"] and not E["hoja"].lotes and c["fallos"] == 3, c)
preparar(filas=None)
c = RE.enviar_empresa("cliente1")
chk("⚠️ una empresa donde nadie lo pidió: no se abre la hoja (abrirla la CREARÍA)", E["ws"] == 0 and not E["gen"] and not any(c.values()), (E["ws"], c))
preparar(filas=[FILAS[3]])
c = RE.enviar_empresa("cliente1")
chk("todo ya enviado hoy: ni modelo ni escritura", E["ws"] == 0 and not E["gen"] and c["ya_hoy"] == 1, c)

sec("4. Todas las empresas, cada una en su libro")
auth.list_groups = lambda only_active=False: [{"Group": "cliente1"}, {"Group": ""}, {"Group": "otra"}]
_vis, _orig = [], RE.enviar_empresa


def _por(g, ignorar_hora=False):
    _vis.append((g, tenant.grupo_activo(), ignorar_hora))
    if g == "cliente1":
        raise RuntimeError("Admin2 secreto 1PK7")
    return {"enviados": 1}


RE.enviar_empresa = _por
c = RE.enviar_todo(ignorar_hora=True)
chk("⚠️ cada empresa DENTRO de su ámbito (lo que se lea sale de su libro)", _vis == [("cliente1", "cliente1", True), ("otra", "otra", True)], _vis)
chk("una empresa que falla no para las demás", c["errores"] == 1 and c["enviados"] == 1 and c["empresas"] == 2, c)
chk("⚠️ solo cuentas (nada con nombres)", set(c) <= set(RE.CUENTAS) and all(isinstance(v, int) for v in c.values()), c)
chk("y el ámbito se cierra al acabar", tenant.grupo_activo() in ("", None))
chk("solo las empresas activas", "list_groups(only_active=True)" in _src)
RE.enviar_empresa = _orig

sec("5. El script: en un registro PÚBLICO, solo cuentas")
_scr = leer("survey_app/resumen_manana.py")
chk("⚠️ apaga los avisos de la app (llevan usuarios y errores)", "logging.disable(logging.CRITICAL)" in _scr)
chk("el CWD, el de la app (los secretos se buscan desde ahí)", "os.chdir(_RAIZ)" in _scr)
# por su RUTA: es un script de la app, no un módulo de `core` (check_suite_integra no deja importar lo que no lo es)
import importlib.util                                             # noqa: E402
_spec = importlib.util.spec_from_file_location("resumen_manana_v648", os.path.join(RAIZ, "resumen_manana.py"))
SM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SM)
RE.enviar_todo = lambda ignorar_hora=False: (E.__setitem__("ign", ignorar_hora), {"empresas": 2, "enviados": 3})[1]
_o = io.StringIO()
with contextlib.redirect_stdout(_o):
    r = SM.main(["--ignorar-hora"])
chk("imprime las cuentas y sale bien", r == 0 and _o.getvalue().strip().startswith("empresas 2 | enviados 3") and E.get("ign") is True, _o.getvalue())


def _peta(ignorar_hora=False):
    raise RuntimeError("cliente1 Admin2 diegoaco93 1PK7")


RE.enviar_todo = _peta
_o = io.StringIO()
with contextlib.redirect_stdout(_o):
    r = SM.main([])
chk("⚠️ un fallo se dice por su TIPO, nunca por su mensaje", r == 1 and "RuntimeError" in _o.getvalue()
    and not any(x in _o.getvalue() for x in ("cliente1", "Admin2", "diegoaco93", "1PK7")), _o.getvalue())
RE.enviar_todo = lambda ignorar_hora=False: {"fallos": 1}
with contextlib.redirect_stdout(io.StringIO()):
    r = SM.main([])
chk("con fallos, sale en rojo (GitHub avisa al dueño)", r == 1)

sec("6. El trabajo de GitHub")
W = leer(".github/workflows/resumen_manana.yml")
chk("cada hora (el script decide la hora de cada empresa) y a mano", 'cron: "17 * * * *"' in W and "workflow_dispatch:" in W)
chk("⚠️ sin pull_request: el código de otro nunca corre con los secretos", "pull_request" not in W)
chk("solo lectura del repositorio", "permissions:\n  contents: read" in W)
chk("dos a la vez no (mandarían dos veces)", "concurrency:" in W and "cancel-in-progress: false" in W)
_runs = [l for l in W.split("\n") if l.strip().startswith(("run:", "printf", "if [", "python", "echo", "rm "))]
chk("⚠️ el secreto entra por `env`, nunca escrito en una orden", "SECRETS_TOML: ${{ secrets.STREAMLIT_SECRETS_TOML }}" in W
    and not any("${{ secrets." in l for l in _runs), _runs)
chk("⚠️ y nunca se imprime", 'echo "$SECRETS_TOML"' not in W and "cat .streamlit/secrets.toml" not in W and "set -x" not in W)
chk("se escribe donde lo busca la app, con permisos solo del dueño", "working-directory: survey_app" in W and "umask 077" in W
    and "> .streamlit/secrets.toml" in W)
chk("⚠️ y se borra pase lo que pase", "if: always()" in W and "rm -f survey_app/.streamlit/secrets.toml" in W)
chk("sin el secreto, no hace nada (y lo dice)", "STREAMLIT_SECRETS_TOML is not set" in W and W.count("if: steps.sec.outputs.ok == 'true'") == 4)
chk("el Python del Cloud y sus librerías", 'python-version: "3.12"' in W and "pip install -q -r survey_app/requirements.txt" in W)
chk("«ignorar la hora» solo a mano", "github.event_name == 'workflow_dispatch' && inputs.ignorar_hora" in W and "--ignorar-hora" in W)
chk("⚠️ el secreto local no está en el repositorio", ".streamlit/secrets.toml" in leer(".gitignore") or "secrets.toml" in leer(".gitignore"))

sec("7. En Home: cada uno lo pide para sí")
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import auth, flash, projects_ui as PU, resumen_envio as RE
E = st.session_state["_e"]
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "G"}
auth.get_user = lambda u: E.get("user", {})
RE.suscrito = lambda g, u: E.get("sus", False)
def _sus(g, u, idi, si):
    E["llamadas"].append((g, u, idi, si))
    return E.get("ok", True), ("HECHO" if E.get("ok", True) else "NO SE PUDO")
RE.suscribir = _sus
flash.mostrar()
PU._cada_manana("G", "Admin2", "es")
'''


def app(**e):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_e"] = {"llamadas": [], **e}
    at.run()
    chk("se pinta sin excepción", not at.exception, [x.value for x in at.exception][:1])
    return at


def tog(at):
    return next((x for x in at.toggle if x.key == "brief_cada_dia_G"), None)


at = app(sus=False, user={"Email": "a@b.com"})
chk("el interruptor, con su clave y apagado si no lo pidió", tog(at) is not None and tog(at).value is False)
tog(at).set_value(True).run()
chk("⚠️ al encenderlo, lo pide PARA QUIEN está en la sesión, en su idioma", at.session_state["_e"]["llamadas"] == [("G", "Admin2", "es", True)],
    at.session_state["_e"]["llamadas"])
chk("y lo dice en esa misma pasada", any("HECHO" in x.value for x in at.success), [x.value for x in at.success])
at = app(sus=True, user={"Email": "a@b.com"})
chk("encendido si ya lo pidió", tog(at).value is True)
tog(at).set_value(False).run()
chk("al apagarlo, lo quita", at.session_state["_e"]["llamadas"] == [("G", "Admin2", "es", False)])
at = app(sus=False, ok=False, user={"Email": "a@b.com"})
tog(at).set_value(True).run()
chk("⚠️ si no se pudo guardar, lo dice y el interruptor vuelve a como estaba", any("NO SE PUDO" in x.value for x in at.error)
    and tog(at).value is False, (tog(at).value, [x.value for x in at.error]))
at = app(sus=True, user={})
chk("⚠️ sin email ni Telegram, avisa de que no le llegará", any("no email or Telegram" in c.value for c in at.caption))
at = app(sus=True, user={"TelegramChatID": "1"})
chk("con Telegram basta", not any("no email or Telegram" in c.value for c in at.caption))
_pu = leer("survey_app/core/projects_ui.py")
chk("va bajo «Send it to me», en la lectura del Home", "    _cada_manana(grupo, _u, _id)\n" in _pu
    and _pu.index("brief_send_{grupo}") < _pu.index("    _cada_manana(grupo, _u, _id)\n"))

print("\n=== verif_v648: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
