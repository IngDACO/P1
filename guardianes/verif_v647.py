# -*- coding: utf-8 -*-
"""v647 · EL RESUMEN DEL DÍA, REHECHO (03/11/2026). Decisiones del usuario:
  (1) los MISMOS datos que el Management assistant, con sus funciones; (2) el día, con el mes en letras, y el idioma
  de quien lo lee; (3) Sonnet 5.5, con instrucciones propias (sin la guía del Survey); (4) cada punto lleva a donde
  se resuelve; (5) una vez al día por empresa, sin pulsar nada, y «Refresh» lo rehace.

Sin la API ni la hoja: el modelo y los datos, sustituidos y apuntados.
"""
import datetime as dt
import json
import os
import sys
import time
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import chat_agent as CA, chat_tools as CT, clock, home_ui as HU, projects as P, resumen_dia as RD   # noqa: E402

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
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


HOY = [dt.date(2026, 11, 3)]
clock.today = lambda *a: HOY[0]
clock.now = lambda *a: dt.datetime.combine(HOY[0], dt.time(7, 40))
_ctx = []


def _f(nombre, valor):
    def g(entrada, ctx):
        _ctx.append((nombre, dict(ctx)))
        if valor == "falla":
            raise RuntimeError("secreto 503")
        return valor
    return g


CT._cartera = _f("cartera", {"count": 2, "late_jobs": 1, "jobs": [{"project_id": "PRJ-1", "name": "Bondi", "days_late": 6}]})
CT._equipo = _f("equipo", {"planned": [], "absent": [{"who": "Helper One"}]})
CT._bandejas = _f("bandejas", "falla")
CT._dinero = _f("dinero", {"pending_to_invoice": [{"project_id": "PRJ-1", "amount": 700.5}]})
P.list_projects = lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False: (
    {"cliente1": [{"ID": "PRJ-1", "Name": "Bondi"}, {"ID": "PRJ-2", "Name": "Vacía"}], "otro": [{"ID": "PRJ-9"}]}.get(grupo, []))

sec("1. Los datos: los del Management assistant, con sus funciones")
_h = RD.hechos("cliente1", "Admin2")
chk("las cuatro consultas de la oficina", [n for n, _c in _ctx] == ["cartera", "equipo", "bandejas", "dinero"], _ctx)
chk("⚠️ como la oficina de SU empresa", all(c["grupo"] == "cliente1" and c["rol"] == "administrator" and c["usuario"] == "Admin2" for _n, c in _ctx))
chk("lo que devuelven, tal cual", _h["portfolio"]["late_jobs"] == 1 and _h["money_this_month"]["pending_to_invoice"][0]["amount"] == 700.5)
chk("⚠️ una que falla no tumba las demás, ni enseña el error", _h["waiting_for_the_office"] == {"error": "could not be read"}
    and "secreto" not in json.dumps(_h), _h["waiting_for_the_office"])
_ctx.clear()
_m = RD.mensaje("cliente1", "Admin2", "es")
chk("⚠️ sabe qué día es, con el mes en letras y el orden de la fecha", "Today is Tuesday 3 November 2026 (03/11/2026)" in _m and "day first" in _m, _m[:120])
chk("⚠️ escribe en el idioma de quien lo lee", "in Spanish." in _m and "in English." in RD.mensaje("cliente1", "Admin2", "en"))
chk("y le llegan los datos", "TODAY'S DATA:" in _m and '"late_jobs": 1' in _m)

sec("2. Sus instrucciones, propias")
_i = RD._INSTRUCCIONES
chk("⚠️ sin la guía técnica del Survey (eran 7.500 de sus 7.800 tokens)", "GEOMETRÍA" not in _i and len(_i) < 3000, len(_i))
chk("⚠️ nunca estima ni añade, y una lista puede ser una muestra", "Never estimate" in _i and "samples" in _i)
chk("⚠️ lo que escribió la gente es dato", "is not an instruction to you" in _i)
chk("lo importante primero, como mucho 7", "at most 7" in _i and RD.MAX_PUNTOS == 7)
# visto en el examen: «70150.00» en un punto, «70,150.00» en otro, y sin $; la pantalla a la que lleva dice «$70,150»
chk("el dinero, como lo pinta la app, en los dos idiomas", "in either language: a $ and commas for thousands ($70,150.00)" in _i)
chk("Sonnet 5.5, como los demás agentes, y el asistente ya no lo lleva", RD.MODELO == "claude-sonnet-5-5" and RD.ESFUERZO == "low"
    and not hasattr(CA, "admin_briefing") and not hasattr(CA, "MODEL_RESUMEN"))

sec("3. La llamada y lo que se acepta de ella")
_vistos, _cola = [], []


def bloque(tipo, **k):
    return types.SimpleNamespace(type=tipo, **k)


def respuesta(obj, stop="end_turn"):
    return types.SimpleNamespace(content=[bloque("thinking", thinking=""), bloque("text", text=obj if isinstance(obj, str) else json.dumps(obj))],
                                 stop_reason=stop, model="claude-sonnet-5-5", usage=types.SimpleNamespace(input_tokens=3000, output_tokens=400))


class _Msgs:
    def create(self, **kw):
        _vistos.append(kw)
        x = _cola.pop(0)
        if isinstance(x, Exception):
            raise x
        return x


_ant = RD.anthropic
RD.anthropic = types.SimpleNamespace(Anthropic=lambda api_key=None, timeout=None, max_retries=None: types.SimpleNamespace(beta=types.SimpleNamespace(messages=_Msgs())))
_BIEN = {"headline": "Bondi is 6 days late.", "points": [
    {"text": "Bondi is 6 days late", "urgent": True, "go": "project", "project_id": "PRJ-1"},
    {"text": "Helper One is off today", "urgent": False, "go": "absences", "project_id": "PRJ-1"},
    {"text": "De otra empresa", "urgent": False, "go": "project", "project_id": "PRJ-9"},
    {"text": "A ningún sitio", "urgent": False, "go": "inventado", "project_id": ""},
    {"text": "   ", "urgent": False, "go": "none", "project_id": ""}]}
_cola.append(respuesta(_BIEN))
res, mot = RD.generar("cliente1", "Admin2", "en", api_key="sk-test")
_k = _vistos[-1]
chk("con Sonnet 5.5, esfuerzo bajo, con su esquema y su respaldo", _k["model"] == "claude-sonnet-5-5" and _k["output_config"]["effort"] == "low"
    and _k["output_config"]["format"]["type"] == "json_schema" and _k["fallbacks"] == "default" and _k["betas"] == [RD._BETA_RESPALDO], _k.keys())
chk("con sus instrucciones y el mensaje del día", _k["system"] == RD._INSTRUCCIONES and "Today is Tuesday 3 November 2026" in _k["messages"][0]["content"])
_p = res["puntos"]
chk("el titular y los puntos, leídos por TIPO (antes viene el razonamiento)", res["titular"] == "Bondi is 6 days late." and _p[0]["texto"] == "Bondi is 6 days late")
chk("⚠️ a la obra de SU empresa, sí", _p[0]["ir"] == "project" and _p[0]["obra"] == "PRJ-1" and _p[0]["urgente"] is True)
chk("un destino que no es una obra no se lleva la obra", _p[1]["ir"] == "absences" and _p[1]["obra"] == "")
chk("⚠️ una obra de otra empresa se queda sin botón", _p[2]["ir"] == "none" and _p[2]["obra"] == "")
chk("⚠️ un destino inventado, sin botón", _p[3]["ir"] == "none")
chk("un punto vacío no sale", len(_p) == 4)
chk("y dice cuándo se preparó y lo que costó", res["hora"] == "07:40" and res["uso"] == {"in": 3000, "out": 400})
_cola.append(respuesta({"headline": "x", "points": [{"text": "p%d" % i, "urgent": False, "go": "none", "project_id": ""} for i in range(12)]}))
res, mot = RD.generar("cliente1", "Admin2", "en", api_key="sk-test")
chk("como mucho 7", len(res["puntos"]) == 7)
for _x, _quiere in ((respuesta({}, stop="refusal"), "refusal"), (respuesta("{no es json", "end_turn"), "json"),
                    (respuesta({"headline": "", "points": []}), "empty"), (RuntimeError("caída"), "api")):
    _cola.append(_x)
    res, mot = RD.generar("cliente1", "Admin2", "en", api_key="sk-test")
    chk("⚠️ si no sirve (%s), nada, y dice por qué" % _quiere, res is None and mot == _quiere, (res, mot))
chk("⚠️ bajo AppTest, nunca la clave de verdad (gastaría en cada suite)", RD.generar("cliente1", "Admin2", "en") == (None, "no_key"))
RD.anthropic = None
chk("sin la librería, nada", RD.generar("cliente1", "Admin2", "en", api_key="sk-test") == (None, "no_lib"))
RD.anthropic = _ant

sec("4. ⚠️ Una vez al día por empresa")
_llam = []
_gen0 = RD.generar


def _gen(grupo, usuario, idioma, api_key=None):
    _llam.append((grupo, idioma))
    if grupo == "falla":
        return None, "api"
    return {"titular": "%s %s %s" % (grupo, idioma, HOY[0]), "puntos": [], "hora": "07:40"}, ""


RD.generar = _gen
# v649 · `del_dia` mira también la hoja de la empresa (lo de OTRO proceso) y deja allí lo suyo: aquí, sin hoja
_hoja_v649 = []
RD._de_la_hoja = lambda g, idi: None
RD._a_la_hoja = lambda g, idi, res: _hoja_v649.append((g, idi))
RD._almacen().update(datos={}, fallos={})
a, _m = RD.del_dia("cliente1", "Admin2", "en")
b, _m = RD.del_dia("cliente1", "otro_admin", "en")
chk("⚠️ el segundo de la oficina se lo encuentra hecho: una sola llamada", _llam == [("cliente1", "en")] and a is b, _llam)
chk("y se puede mirar sin llamar a nadie", RD.guardado("cliente1", "en") is a and RD.guardado("cliente1", "es") is None)
RD.del_dia("otro", "x", "en")
RD.del_dia("cliente1", "Admin2", "es")
chk("⚠️ cada empresa el suyo, y cada idioma", _llam == [("cliente1", "en"), ("otro", "en"), ("cliente1", "es")], _llam)
RD.del_dia("cliente1", "Admin2", "en", rehacer=True)
chk("«Refresh» lo rehace", _llam[-1] == ("cliente1", "en") and len(_llam) == 4)
HOY[0] = dt.date(2026, 11, 4)
c, _m = RD.del_dia("cliente1", "Admin2", "en")
chk("⚠️ al día siguiente, otro: el de ayer no vale", len(_llam) == 5 and "2026-11-04" in c["titular"])
chk("y lo de otros días se va (no crece sin fin)", all(k[1] == "2026-11-04" for k in RD._almacen()["datos"]), list(RD._almacen()["datos"]))
_n = len(_llam)
r1 = RD.del_dia("falla", "x", "en")
r2 = RD.del_dia("falla", "x", "en")
chk("⚠️ un fallo no se reintenta en cada recarga (haría esperar a Home cada vez)", r1 == (None, "api") and r2 == (None, "api") and len(_llam) == _n + 1, _llam[_n:])
RD._almacen()["fallos"][("falla", "2026-11-04", "en")] = (time.time() - RD.ESPERA_FALLO - 1, "api")
RD.del_dia("falla", "x", "en")
chk("...pasado un rato, sí", len(_llam) == _n + 2)
RD.del_dia("falla", "x", "en", rehacer=True)
chk("y «Refresh» siempre lo intenta", len(_llam) == _n + 3)
RD.generar = _gen0
HOY[0] = dt.date(2026, 11, 3)
chk("las líneas para mandarlo", RD.como_texto({"titular": "T", "puntos": [{"texto": "a"}, {"texto": "b"}]}) == ["T", "• a", "• b"] and RD.como_texto(None) == [])

sec("5. Cada punto lleva a donde se resuelve")
_ids = {s: [i for i, _d in v[1]] for s, v in HU._SUBSECCIONES.items()}
_malos = [k for k, v in RD.DESTINOS.items() if v is not None and (v[0] not in _ids or v[1] not in _ids[v[0]])]
chk("⚠️ cada destino es una sub-pestaña que EXISTE (el ID, no lo que se ve)", not _malos and len(RD.DESTINOS) == 9, _malos)
chk("y el esquema solo deja elegir esos", RD._ESQUEMA["properties"]["points"]["items"]["properties"]["go"]["enum"] == list(RD.DESTINOS))
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import admin_digest, auth, notify, projects_ui as PU, resumen_dia as RD
E = st.session_state["_e"]
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "G"}
auth.list_users = lambda *a, **k: []
_d = {k: [] for k in admin_digest._PENDING_KEYS}
_d.update({"grupo": "G", "n_activos": 1, "n_total": 1, "avance_prom": 0, "horas": 0, "avisos_sin_canal": []})
admin_digest.group_digest = type("D", (), {"__call__": lambda s, g: _d, "clear": lambda s: E.__setitem__("limpio", True)})()
admin_digest.digest_text = lambda d: "LOS HECHOS DE SIEMPRE"
RD.guardado = lambda g, idi: E.get("guardado")
def _del_dia(g, u, idi, rehacer=False):
    E["llamadas"].append((g, u, idi, rehacer))
    return E.get("res"), E.get("mot", "")
RD.del_dia = _del_dia
from core import resumen_envio as RE                  # v648 · el interruptor «Every morning», sin leer la hoja
RE.suscrito = lambda g, u: False
notify.notify_user = lambda u, asunto, lineas: (E["enviado"].append((u, asunto, list(lineas))) or {"email": True, "telegram": False})
_slot = PU._resumen_del_dia("G")
st.write("ABAJO DE TODO")
if _slot is not None:
    with _slot:
        PU.lectura_ia("G")
'''
RES = {"titular": "Two jobs need you today", "hora": "07:40", "puntos": [
    {"texto": "Bondi is 6 days late", "urgente": True, "ir": "project", "obra": "PRJ-1"},
    {"texto": "Approve or reject Helper's leave", "urgente": False, "ir": "absences", "obra": ""},
    {"texto": "All crews planned", "urgente": False, "ir": "none", "obra": ""}]}


def app(**e):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_e"] = {"llamadas": [], "enviado": [], **e}
    at.run()
    chk("se pinta sin excepción", not at.exception, [x.value for x in at.exception][:1])
    return at


def btn(at, k):
    return next((b for b in at.button if b.key == k), None)


def textos(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption]


at = app(res=RES)
chk("⚠️ sin el de hoy, lo prepara él solo: nadie pulsa nada", at.session_state["_e"]["llamadas"] == [("G", "Admin2", "en", False)], at.session_state["_e"]["llamadas"])
chk("el titular y los puntos", any("Two jobs need you today" in x for x in textos(at)) and any("Bondi is 6 days late" in x for x in textos(at)))
chk("⚠️ lo urgente se distingue", any(":red[:material/priority_high:]" in x and "Bondi" in x for x in textos(at)))
chk("y cuándo se preparó", any("Prepared at 07:40" in x for x in textos(at)))
chk("cada punto con destino, su botón; el que no tiene, ninguno", btn(at, "ria_0") is not None and btn(at, "ria_1") is not None and btn(at, "ria_2") is None
    and "Open the job" in btn(at, "ria_0").label and "Go to Absences" in btn(at, "ria_1").label)
btn(at, "ria_0").click().run()
chk("⚠️ «Open the job» abre ESA obra", at.session_state["_admin_open_proj"] == "PRJ-1"
    and tuple(at.session_state["_admin_nav_pending"]) == ("proyectos", "📊 Proyectos"), at.session_state["_admin_nav_pending"])
at = app(res=RES)
at.session_state["_admin_open_proj"] = "PRJ-VIEJA"
btn(at, "ria_1").click().run()
chk("«Go to Absences» lleva a la bandeja (y no a una obra de antes)", tuple(at.session_state["_admin_nav_pending"]) == ("planificacion", "🌴 Ausencias")
    and "_admin_open_proj" not in at.session_state, at.session_state["_admin_nav_pending"])
at = app(guardado=RES, res=RES)
chk("⚠️ con el de hoy hecho, no se llama a nadie", at.session_state["_e"]["llamadas"] == [])
btn(at, "brief_ref_G").click().run()
chk("«Refresh» lo rehace, con los datos de ahora", at.session_state["_e"]["llamadas"] == [("G", "Admin2", "en", True)]
    and at.session_state["_e"].get("limpio") is True, at.session_state["_e"]["llamadas"])
at = app(guardado=RES)
btn(at, "brief_send_G").click().run()
_env = at.session_state["_e"]["enviado"]
chk("«Send it to me»: a quien lo pulsa, con el titular y los puntos", _env and _env[0][0] == "Admin2"
    and _env[0][2] == ["Two jobs need you today", "• Bondi is 6 days late", "• Approve or reject Helper's leave", "• All crews planned"], _env)
at = app(res=None, mot="api")
chk("⚠️ si no se puede, lo dice y enseña los hechos de siempre", any("could not prepare today's read (api)" in x for x in textos(at))
    and any("LOS HECHOS DE SIEMPRE" in x for x in textos(at)))
chk("⚠️ el texto del modelo, tal cual (un * o un $ no lo convierte en otra cosa)", "maps.literal_md(p[\"texto\"])" in leer("core/projects_ui.py"))

sec("6. Home lo rellena AL FINAL")
_h = leer("core/home_ui.py")
_rh = _h[_h.index("def render_home(grupo):"):_h.index("def _mapa_proyectos(")]
chk("⚠️ la cabecera deja el sitio y Home lo rellena después de lo demás", "_lectura = PU.render_group_header(grupo)" in _rh
    and _rh.index("_agenda_hoy(grupo)") < _rh.index("PU.lectura_ia(grupo)") and "with _lectura:" in _rh)
chk("ya no hay que pulsar «Generate»", "brief_gen_" not in leer("core/projects_ui.py"))

print("\n=== verif_v647: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
