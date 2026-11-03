# -*- coding: utf-8 -*-
"""v649 · LO VISTO EN LA PRUEBA DE v646 Y LO QUE COSTABA DOS VECES (04/11/2026). Aprobado por el usuario («Ok 1-3»):
  (1) el agente del parte premarcaba una actividad de varias partes con una sola («the CW buffer» → «Install/trim
      buffers (car + CW)» entera): ahora es una PREGUNTA, sin marcar, con su encabezado;
  (2) la tarjeta de la OFICINA decía «your log» de un parte ajeno, y «1 activities»;
  (3) el resumen del día se pagaba dos veces (el envío de la mañana y Home no comparten memoria): se deja en la hoja de
      la empresa y el que llega después lo usa.

Sin la API y sin la hoja: todo sustituido y apuntado.
"""
import datetime as dt
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}

from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import clock, hojas, parte_agente as AG, resumen_dia as RD, timeclock   # noqa: E402

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


sec("1. El agente: una actividad de varias partes, con solo una nombrada, es una pregunta")
_i = AG._INSTRUCCIONES
chk("⚠️ la regla, con el caso de producción", "joins two or more parts" in _i and "Install/trim buffers (car + CW)" in _i
    and "class question with that one" in _i and "Is the car buffer done too?" in _i)
chk("⚠️ ceñida a las partes del NOMBRE (sin esto preguntaba por «finished with rails», visto en el examen)",
    "only about the parts the" in _i and '"finished the rails" still finishes a rails activity' in _i)
chk("y la clase «question» la incluye", "or that covers only part of one activity" in _i)
chk("⚠️ PROMPT_V subido: los partes sin revisar se releen con la regla nueva", AG.PROMPT_V == 3)

sec("2. La tarjeta: la pregunta de una opción, la oficina y el singular")
GUION = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import daily_log_ui as DU
E = st.session_state["_e"]
DU._pintar(E["p"], "k", oficina=E.get("of", False))
'''
_OP = {"orden": 12, "etapa": "Pit Mechanical", "actividad": "Install/trim buffers (car + CW)", "cuenta": True, "hecha": False}
P_UNA = {"actividades": [], "etapas": [], "pendientes": [], "retiradas": [], "fuera": [],
         "preguntas": [{"termino": "and the CW buffer", "regla": "Is the car buffer done too?", "opciones": [dict(_OP)], "pruebas": []}]}
P_VARIAS = dict(P_UNA, preguntas=[{"termino": "did door wiring", "regla": "Which one?", "pruebas": [],
                                   "opciones": [dict(_OP, actividad="Door locks"), dict(_OP, actividad="Call button wiring")]}])
P_TODO = {"actividades": [{"orden": 9, "etapa": "CW", "actividad": "Install CW guide shoes", "cuenta": True, "hecha": False,
                           "pruebas": ["Installed the CW guide shoes"], "aviso": "bajo_pendiente", "fuente": "agente"}],
          "etapas": [{"termino": "doors", "pruebas": [], "opciones": [dict(_OP, actividad="Door locks")]}],
          "preguntas": [], "pendientes": [{"termino": "screen", "actividades": [], "pruebas": ["the CW safety screen"]}],
          "retiradas": [], "fuera": []}


def app(p, of=False):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_e"] = {"p": p, "of": of}
    at.run()
    chk("se pinta sin excepción", not at.exception, [x.value for x in at.exception][:1])
    return at


def textos(at):
    return ([m.value for m in at.markdown] + [c.value for c in at.caption]
            + [e.label for e in list(at.expander) + list(at.status)])


at = app(P_UNA)
chk("⚠️ UNA opción: «tick it only if all of it is done», no «can mean several things»",
    any("«and the CW buffer» — tick it only if all of it is done." in x for x in textos(at))
    and not any("can mean several things" in x for x in textos(at)), textos(at))
chk("con la pregunta del agente debajo", any("Is the car buffer done too?" in x for x in textos(at)))
chk("⚠️ y SIN marcar", [c.value for c in at.checkbox] == [False], [c.value for c in at.checkbox])
at = app(P_VARIAS)
chk("varias opciones: lo de siempre", any("«did door wiring» can mean several things" in x for x in textos(at)))
at = app(P_TODO, of=True)
_t = textos(at)
chk("⚠️ la oficina: «Activities this log mentions»", any("Activities this log mentions" in x for x in _t)
    and not any("your log" in x.lower() for x in _t), [x for x in _t if "log" in x.lower()])
chk("...«This log names» y «Pending in this log»", any("This log names «doors»" in x for x in _t)
    and any("Pending in this log — not credited (1)" in x for x in _t), _t)
chk("...y el aviso de «Issues/Pending», también", any("This log lists this under «Issues/Pending»" in x for x in _t), _t)
at = app(P_TODO, of=False)
_t = textos(at)
chk("el autor sigue con «your log»", any("Activities your log mentions" in x for x in _t)
    and any("Pending in your log — not credited (1)" in x for x in _t) and any("Your log lists this under" in x for x in _t), _t)

from core import daily_log_ui as DU                                # noqa: E402
chk("⚠️ «1 activity», en singular", DU._acreditadas(1) == "Credited 1 activity from your log."
    and DU._acreditadas(3) == "Credited 3 activities from your log.", (DU._acreditadas(1), DU._acreditadas(3)))
chk("⚠️ la oficina dice de QUIÉN era", DU._acreditadas(1, "Ana") == "Credited 1 activity from Ana's log, on their behalf."
    and DU._acreditadas(2, "Ana") == "Credited 2 activities from Ana's log, on their behalf.")
_dl = leer("core/daily_log_ui.py")
chk("y se usa al confirmar, con el autor si es la oficina", '_acreditadas(n, _nombre(_autor) if oficina else "")' in _dl
    and "Credited {n} activities from your log.\", n=n) if ok" not in _dl)
chk("⚠️ la tarjeta pasa `oficina` a lo que pinta", "todo=(lid, str(d)), oficina=oficina)" in _dl
    and "_nada_que_confirmar(_prev, oficina)" in _dl)
G2 = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import daily_log_ui as DU, stage_progress as SP
E = st.session_state["_e"]
SP.de_parte = lambda pid, lid: [{}] * E["n"]
DU._nombre = lambda u: {"Admin2": "Bobo", "campo000": "Ana"}.get(u, u)
DU._estado_revision({"Reviewed": "2026-11-03 22:39", "ReviewedBy": "Admin2", "Author": "campo000", "ID": "LOG-1"}, "PRJ-1")
DU._nada_que_confirmar({"actividades": [], "etapas": [], "preguntas": [], "fuera": [], "retiradas": [], "no_avance": [],
                        "pendientes": [{"termino": "x"}]}, oficina=E.get("of", False))
'''
for n, esp in ((1, "1 activity credited from this log"), (2, "2 activities credited from this log")):
    at = AppTest.from_string(G2, default_timeout=60)
    at.session_state["_e"] = {"n": n, "of": True}
    at.run()
    _c = [c.value for c in at.caption]
    chk("«%s» (y por quién, en nombre de quién)" % esp, any(esp in x and "Bobo (on behalf of Ana)" in x for x in _c), _c)
chk("⚠️ y sin nada que acreditar, la oficina lee «this log»", any("What this log lists as still to do" in x for x in _c), _c)

sec("3. El resumen del día: uno al día también ENTRE procesos")
chk("la hoja, en el lote de lectura (si no, se leería VACÍA para siempre)", RD.SHEET == "DailyBriefs" and RD.SHEET in hojas.HOJAS_LECTURA)
chk("en el libro de cada empresa, no en el maestro", RD.SHEET.lower() not in timeclock.SHEETS_GLOBALES)
chk("columnas fijas", RD.HEADERS == ["Group", "Date", "Language", "Prepared", "Model", "Brief"])
_rd = leer("core/resumen_dia.py")
chk("⚠️ se lee SIN cabeceras (leer no crea la hoja)", "for r in (hojas.registros(SHEET) or [])" in _rd)
HOY = dt.date(2026, 11, 4)
clock.today = lambda *a: HOY
clock.now = lambda *a: dt.datetime.combine(HOY, dt.time(7, 17))
HOJA = []


class W:
    def append_row(self, fila, **k):
        HOJA.append(dict(zip(RD.HEADERS, [str(x) for x in fila])))


_reg = hojas.registros
hojas.registros = lambda titulo, *a, **k: ([dict(r) for r in HOJA] if titulo == RD.SHEET else _reg(titulo, *a, **k)) if HOJA else None
_gs = timeclock.get_sheet
timeclock.get_sheet = lambda titulo, cab, grupo=None: W() if titulo == RD.SHEET else _gs(titulo, cab, grupo)
hojas.invalidar = lambda *a, **k: None
GEN = []
RES = {"titular": "T", "puntos": [{"texto": "P", "urgente": True, "ir": "project", "obra": "PRJ-1"}], "hora": "07:17",
       "modelo": "claude-sonnet-5-5", "uso": {"in": 1, "out": 1}}


def _gen(g, u, idi, api_key=None):
    GEN.append((g, idi))
    return dict(RES, titular="T " + idi), ""


RD.generar = _gen
RD._almacen().update(datos={}, fallos={})
a, _m = RD.del_dia("cliente1", "Admin2", "en")                    # el envío de la mañana (proceso 1)
chk("el primero lo prepara y lo DEJA en la hoja de la empresa", GEN == [("cliente1", "en")] and len(HOJA) == 1
    and HOJA[0]["Group"] == "cliente1" and HOJA[0]["Date"] == "2026-11-04" and HOJA[0]["Language"] == "en"
    and json.loads(HOJA[0]["Brief"])["titular"] == "T en", HOJA)
RD._almacen().update(datos={}, fallos={})                          # Home (proceso 2: otra memoria)
b, _m = RD.del_dia("cliente1", "jefa", "en")
chk("⚠️ el otro proceso lo usa: sin otra llamada", GEN == [("cliente1", "en")] and b and b["titular"] == "T en"
    and b["puntos"][0]["obra"] == "PRJ-1", (GEN, b))
chk("y lo guarda en su memoria (la siguiente pasada no lee la hoja)", RD.guardado("cliente1", "en") == b)
RD._almacen().update(datos={}, fallos={})
RD.del_dia("cliente1", "jefa", "es")
chk("otro idioma es otro resumen", GEN[-1] == ("cliente1", "es") and len(HOJA) == 2)
RD._almacen().update(datos={}, fallos={})
RD.del_dia("otra", "x", "en")
chk("⚠️ el de otra empresa no vale", GEN[-1] == ("otra", "en"), GEN)
RD.del_dia("cliente1", "Admin2", "en", rehacer=True)
chk("«Refresh» lo rehace sin mirar la hoja, y deja el nuevo", GEN[-1] == ("cliente1", "en") and len(HOJA) == 4)
HOJA[-1]["Brief"] = json.dumps(dict(RES, titular="EL ÚLTIMO"))
RD._almacen().update(datos={}, fallos={})
c, _m = RD.del_dia("cliente1", "Admin2", "en")
chk("⚠️ manda el ÚLTIMO del día (el de «Refresh»)", c and c["titular"] == "EL ÚLTIMO", c)
_n = len(GEN)
HOY = dt.date(2026, 11, 5)
RD._almacen().update(datos={}, fallos={})
RD.del_dia("cliente1", "Admin2", "en")
chk("⚠️ el de ayer no vale hoy", len(GEN) == _n + 1)
HOJA.append({"Group": "cliente1", "Date": "2026-11-05", "Language": "fr", "Brief": "{roto"})
chk("lo que no se entiende, no se usa", RD._de_la_hoja("cliente1", "fr") is None)
HOJA.append({"Group": "cliente1", "Date": "2026-11-05", "Language": "it", "Brief": json.dumps({"titular": "X", "puntos": [
    {"texto": "a", "ir": "inventado", "obra": "PRJ-9"}, {"texto": "b", "ir": "invoices", "obra": "PRJ-9"},
    {"texto": "", "ir": "none"}] + [{"texto": "n%d" % i, "ir": "none"} for i in range(10)]})})
_x = RD._de_la_hoja("cliente1", "it")
chk("⚠️ y lo que sí, con las reglas de siempre: destino desconocido sin botón, obra solo con «project», tope de 7",
    _x and _x["puntos"][0]["ir"] == "none" and _x["puntos"][1] == {"texto": "b", "urgente": False, "ir": "invoices", "obra": ""}
    and len(_x["puntos"]) == RD.MAX_PUNTOS and all(p["texto"] for p in _x["puntos"]), _x)
GEN.clear()
RD.generar = lambda g, u, idi, api_key=None: (None, "api")
_h = len(HOJA)
RD._almacen().update(datos={}, fallos={})
RD.del_dia("nueva", "x", "en")
chk("un fallo no deja nada en la hoja", len(HOJA) == _h)


def _peta(*a, **k):
    raise RuntimeError("503")


timeclock.get_sheet = _peta
RD.generar = _gen
RD._almacen().update(datos={}, fallos={})
r, _m = RD.del_dia("nueva2", "x", "en")
chk("si no se puede dejar en la hoja, el resumen sale igual", r and r["titular"] == "T en")
chk("⚠️ el envío de la mañana pide `del_dia` (y no paga otro si Home ya lo hizo)",
    "RD.del_dia(grupo, gente[0][1].get(\"User\", \"\"), idi)" in leer("core/resumen_envio.py")
    and "RD.generar(" not in leer("core/resumen_envio.py"))
hojas.registros, timeclock.get_sheet = _reg, _gs

print("\n=== verif_v649: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
