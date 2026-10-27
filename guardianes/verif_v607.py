# -*- coding: utf-8 -*-
"""v607 · EL AGENTE DEL PARTE DIARIO (`core/parte_agente.py`) — decisión del usuario (26/10/2026):
«La solución es integrar un agente con el contexto y la capacidad de leer, interpretar,
preguntar y ejecutar». Modelo: Claude Sonnet 5.5 («Solo sonnet»).

Lo que protege, SIN red y SIN gastar (la llamada al modelo se sustituye):
  (a) el modelo, el esfuerzo, la salida con esquema, el respaldo del servidor y la caché del
      prompt (lo fijo delante y con su marca; nada que cambie entre partes en el prefijo);
  (b) ⚠️ lo que dice el modelo se VALIDA: un código fuera del plan se descarta y se cuenta, un
      «hecho» sin código válido se pregunta, y toda línea que el modelo se salte entra como
      «no entendido» — nada se ignora;
  (c) ⚠️ nada se acredita sin el clic del autor: lo empezado, lo pendiente, los problemas y lo
      que no es avance se ENSEÑAN, pero no se pueden marcar;
  (d) ⚠️ una lectura por parte: se guarda (`Reading`) y las recargas no vuelven a llamar; un
      parte revisado, ajeno o del admin no se lee; un fallo no se reintenta en cada recarga
      y la tarjeta sale con el vocabulario, diciéndolo;
  (e) «preguntar»: lo no entendido lleva su caja, «Read it again» relee con las respuestas, y
      hay un tope de rondas;
  (f) ⚠️ bajo AppTest NUNCA la clave de verdad (los guardianes de antes pintan la tarjeta y
      habrían llamado a la API de pago en cada suite), y la app no importa `streamlit.testing`;
  (g) el SDK fijo (`anthropic==1.17.0`), el mismo en local, y `Reading` al final de DailyLogs.
"""
import ast
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test",
                            "rol": "field", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import daily_log as DL                                  # noqa: E402
from core import parte_agente as AG                               # noqa: E402
from core import parte_propuestas as PP                           # noqa: E402
from core import stages as S                                      # noqa: E402

PLAN = S.plan_de("Installation", ())
_TXT, COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in COD.items()}
_ORIG = {"clave_api": AG.clave_api, "_llamar": AG._llamar}

# ═════════════════════════════════════════════════════════════════
sec("1. Modelo, SDK y la cabecera de la hoja")
chk("el modelo es Claude Sonnet 5.5 (lo eligió el usuario)", AG.MODELO == "claude-sonnet-5-5", AG.MODELO)
chk("esfuerzo bajo (leer y clasificar; el móvil)", AG.ESFUERZO == "low", AG.ESFUERZO)
_req = open(os.path.join(RAIZ, "requirements.txt"), encoding="utf-8").read()
_pin = re.search(r"^anthropic==([\d.]+)\s*$", _req, re.M)
chk("`anthropic` FIJO (==) en requirements", bool(_pin), re.findall(r"^anthropic.*$", _req, re.M))
import anthropic as _an                                           # noqa: E402
chk("...y el instalado en local es el mismo (lo que prueba la suite = lo que corre)",
    bool(_pin) and _an.__version__ == _pin.group(1), (_an.__version__, _pin and _pin.group(1)))
chk("`Reading` va AL FINAL de DailyLogs (v363) y lo de antes no se movió",
    DL.HEADERS[-1] == "Reading" and DL.HEADERS[:11] == [
        "ID", "Group", "ProjectID", "Date", "Author", "Text", "Source", "Created",
        "Reviewed", "ReviewedBy", "Proposals"], DL.HEADERS)
_src_dl = open(os.path.join(RAIZ, "core", "daily_log.py"), encoding="utf-8").read()
_m = re.search(r"w\.append_row\(\[(.*?)\],\s*value_input_option", _src_dl, re.S)
_nf = len(ast.parse("[" + _m.group(1) + "]", mode="eval").body.elts) if _m else 0
chk("`crear` escribe la fila ENTERA (tantos campos como cabeceras)", _nf == len(DL.HEADERS),
    (_nf, len(DL.HEADERS)))

# ═════════════════════════════════════════════════════════════════
sec("2. El plan en códigos y lo que se le manda al modelo")
chk("un código por actividad del plan, sin repetidos",
    len(COD) == sum(len(e["actividades"]) + len(S.informativas(e.get("pista"), e.get("numero")))
                    for e in PLAN), len(COD))
chk("el texto del plan sale IGUAL dos veces (va en la clave y en el prefijo cacheado)",
    AG.plan_en_codigos(PLAN)[0] == _TXT)
for _n in ("Install yoke/base, level it", "Install platform (cradle)", "Build cabin (walls)",
           "Install cabin ceiling (roof)", "Install rings to top", "Install motor bedplate",
           "Install single bedplate", "Install sills"):
    if _n not in C:
        fallo("el plan de prueba no tiene «%s» (la prueba no valdría)" % _n)
_sis = AG._sistema()
chk("instrucciones + documento del oficio, con su marca de caché",
    len(_sis) == 1 and _sis[0].get("cache_control") == {"type": "ephemeral"}
    and "<domain_reference>" in _sis[0]["text"] and "GLOSSARY" in _sis[0]["text"])
_doc = open(os.path.join(RAIZ, "..", "docs", "Process_Knowledge_Reference.md"), encoding="utf-8").read()
_atr = re.findall(r"\([A-Z][a-z]+, Sep 2026[^)]*\)", _doc)
chk("⚠️ las atribuciones con nombre del documento NO van al modelo (y había que quitar: %d)" % len(_atr),
    _atr and not re.search(r"\([A-Z][a-z]+, Sep 2026", _sis[0]["text"]) and "GLOSSARY" in _sis[0]["text"],
    len(_atr))
chk("...y lo demás del documento sí (más del 90 %)", len(AG._referencia()) > 0.9 * len(_doc),
    (len(AG._referencia()), len(_doc)))
chk("...y el sistema sale idéntico en cada llamada (nada de fecha ni idioma dentro)",
    AG._sistema() == _sis and not re.search(r"20\d\d-\d\d|Spanish", AG._INSTRUCCIONES))
_msj = AG._mensaje("a\nb", "2026-10-26", PLAN, {}, None, None, "es")
_b = _msj[0]["content"]
chk("el plan va PRIMERO en el mensaje y con su marca (fijo por obra)",
    _b[0].get("cache_control") == {"type": "ephemeral"} and _b[0]["text"].startswith("JOB PLAN"))
chk("...lo que cambia va DESPUÉS, sin marca: idioma, avance y el parte numerado",
    all("cache_control" not in x for x in _b[1:]) and len(_b) == 4
    and _b[1]["text"] == "Write `question` and `reason` in Spanish."
    and _b[2]["text"].startswith("PROGRESS"), [x["text"][:40] for x in _b])
chk("⚠️ el parte va el ÚLTIMO y CERRADO con su marca (examen C: «light raysWrite»)",
    _b[-1]["text"].endswith("1| a\n2| b\n<end of log>"), _b[-1]["text"][-40:])
_m2 = AG._mensaje("a", "", PLAN, {}, {"fragmentos": [{"linea": 1, "texto": "a", "clase": "unclear"}]},
                  [{"linea": 1, "texto": "a", "respuesta": "it was X"}], "en")
chk("una ronda con respuestas lleva la lectura anterior y las respuestas como DATOS",
    any("YOUR PREVIOUS READING" in x["text"] and "it was X" in x["text"] for x in _m2[0]["content"]))
_av = AG._avance(PLAN, {(COD[C["Install sills"]][0], "Install sills"): 100.0})
chk("el avance dice lo acreditado al 100 %, en códigos", C["Install sills"] in _av, _av)


def _esquema_ok(s):
    if s.get("type") == "object":
        if s.get("additionalProperties") is not False:
            return False
        if sorted(s.get("required") or []) != sorted(s.get("properties") or {}):
            return False
        return all(_esquema_ok(v) for v in s["properties"].values())
    if s.get("type") == "array":
        return _esquema_ok(s.get("items") or {})
    return True


chk("el esquema es válido para salida estricta (todo objeto cerrado y con todo requerido)",
    _esquema_ok(AG._ESQUEMA))
chk("...y sus clases son las que entiende la app", AG._ESQUEMA["properties"]["fragments"]["items"]
    ["properties"]["class"]["enum"] == list(AG.CLASES))

# ═════════════════════════════════════════════════════════════════
sec("3. La llamada (cliente sustituido: sin red)")
CAP, CAPC = {}, {}


class _Blq:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Uso:
    input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens = 120, 80, 9000, 0


RESP = {"stop": "end_turn", "txt": json.dumps({"fragments": []})}


class _Msgs:
    def create(self, **kw):
        CAP.clear()
        CAP.update(kw)
        return _Blq(stop_reason=RESP["stop"], model="claude-sonnet-5-5", usage=_Uso(),
                    content=[_Blq(type="thinking", thinking=""), _Blq(type="text", text=RESP["txt"])])


class _Cli:
    def __init__(self, **kw):
        CAPC.clear()
        CAPC.update(kw)
        self.beta = _Blq(messages=_Msgs())


_AnthOrig = _an.Anthropic
_an.Anthropic = _Cli
try:
    crudo, info = AG._llamar("sk-x", "installed sills", "2026-10-26", PLAN, {}, None, None, "en")
    chk("modelo, tokens y beta del respaldo", CAP.get("model") == "claude-sonnet-5-5"
        and CAP.get("max_tokens", 0) >= 8000 and CAP.get("betas") == ["server-side-fallback-2026-07-01"],
        {k: CAP.get(k) for k in ("model", "max_tokens", "betas")})
    chk("⚠️ respaldo del servidor ante un rechazo: `fallbacks=\"default\"`", CAP.get("fallbacks") == "default")
    chk("salida con ESQUEMA y esfuerzo bajo", CAP.get("output_config") == {
        "effort": "low", "format": {"type": "json_schema", "schema": AG._ESQUEMA}})
    chk("sin `temperature`/`top_p`/`top_k` (400 en todo modelo desde el 21/10/2026)",
        not {"temperature", "top_p", "top_k"} & set(CAP))
    chk("tiempo máximo y reintentos acotados (el móvil no espera minutos)",
        CAPC.get("timeout") == AG.TIEMPO <= 30 and CAPC.get("max_retries") == AG.REINTENTOS <= 1, CAPC)
    chk("lee el bloque de TEXTO aunque venga detrás de uno de pensamiento", crudo == {"fragments": []})
    chk("anota tokens (con caché) y segundos", info["uso"] == {"in": 120, "out": 80, "cache_r": 9000,
                                                               "cache_w": 0} and "seg" in info, info)
    for _stop, _mot in (("refusal", "refusal"), ("max_tokens", "max_tokens")):
        RESP["stop"] = _stop
        r, m = AG.leer("installed sills", PLAN, api_key="sk-x")
        chk("`%s` → sin lectura (`%s`), sin leer el contenido" % (_stop, _mot), r is None and m == _mot, m)
    RESP.update(stop="end_turn", txt="{no es json")
    r, m = AG.leer("installed sills", PLAN, api_key="sk-x")
    chk("un JSON que no se entiende → sin lectura", r is None and m == "json", m)
finally:
    _an.Anthropic = _AnthOrig
chk("sin clave → sin lectura y sin llamar", AG.leer("x", PLAN, api_key="") == (None, "no_key"))
chk("sin plan → sin lectura", AG.leer("x", [], api_key="sk-x") == (None, "no_plan"))
chk("⚠️ tope de rondas: la cuarta no llama",
    AG.leer("x", PLAN, previa={"rondas": AG.MAX_RONDAS}, respuestas=[{"respuesta": "y"}],
            api_key="sk-x") == (None, "max_rondas"))

# ═════════════════════════════════════════════════════════════════
sec("4. Validar lo que dijo el modelo")
_t = "Installed yoke, walls\nsecond line\n\nthird"
_f, _inv, _an2 = AG.validar({"fragments": [
    {"line": 1, "text": "Installed yoke", "class": "done", "codes": [C["Install yoke/base, level it"], "99.9", "9.x"],
     "question": "", "reason": "", "lift": ""},
    {"line": 1, "text": "walls", "class": "done", "codes": ["77.1"], "question": "", "reason": "", "lift": ""},
    {"line": 2, "text": "second line", "class": "question", "codes": ["88.8"], "question": "?", "reason": "", "lift": ""},
    {"line": 40, "text": "x", "class": "inventada", "codes": [], "question": "", "reason": "", "lift": ""},
]}, PLAN, _t)
chk("⚠️ los códigos fuera del plan se DESCARTAN y se cuentan", _inv == 4 and
    _f[0]["actividades"] == ["Install yoke/base, level it"], (_inv, _f[0]))
chk("«done» sin ningún código válido pasa a «unclear» (se pregunta, no se adivina)",
    [x["clase"] for x in _f if x["texto"] == "walls"] == ["unclear"])
chk("«question» sin opciones válidas, igual", [x["clase"] for x in _f if x["texto"] == "second line"] == ["unclear"])
_fq, _i, _a = AG.validar({"fragments": [{"line": 1, "text": "Set up", "class": "unclear",
                                         "codes": [C["Install sills"], C["Install frames"]],
                                         "question": "Which?", "reason": "", "lift": ""}]}, PLAN, "Set up")
chk("«no entendido» CON candidatas pasa a pregunta (opciones mejor que una caja en blanco)",
    _fq[0]["clase"] == "question" and _fq[0]["actividades"] == ["Install sills", "Install frames"], _fq)
chk("una clase que no existe → «unclear»; una línea fuera de rango → 0",
    any(x["clase"] == "unclear" and x["linea"] == 0 and x["texto"] == "x" for x in _f))
chk("⚠️ la línea que el modelo se SALTÓ entra como «no entendido» (nada se ignora)",
    _an2 == 1 and any(x["linea"] == 4 and x["texto"] == "third" and x["clase"] == "unclear" for x in _f), _an2)
chk("...y la línea vacía no cuenta", not any(x["linea"] == 3 for x in _f))
_tp = "Installed sills\nIssues: installed headers\nfinished the frames"
_fp, _i, _a = AG.validar({"fragments": [
    {"line": n, "text": t_, "class": "done", "codes": [C[a_]], "question": "", "reason": "", "lift": ""}
    for n, t_, a_ in ((1, "Installed sills", "Install sills"), (2, "installed headers", "Install headers"),
                      (3, "finished the frames", "Install frames"))]}, PLAN, _tp)
chk("⚠️ lo HECHO bajo «Issues/Pendings» (la cabecera con texto y lo que va debajo) lleva la marca",
    [bool(x.get("bajo_pendiente")) for x in _fp] == [False, True, True], [x.get("bajo_pendiente") for x in _fp])
_pp = AG.propuestas({"fragmentos": _fp}, PLAN, {}, _tp)
chk("...y se OFRECE con su aviso (sin marcar, como todo), no como un hecho limpio",
    [a["aviso"] for a in _pp["actividades"]] == ["", "bajo_pendiente", "bajo_pendiente"])
_pp2 = AG.propuestas({"fragmentos": _fp + [dict(_fp[2], linea=1, bajo_pendiente=False)]}, PLAN, {}, _tp)
chk("...salvo que el parte lo diga TAMBIÉN fuera del bloque",
    [a["aviso"] for a in _pp2["actividades"] if a["actividad"] == "Install frames"] == [""])

# ═════════════════════════════════════════════════════════════════
sec("5. De la lectura a la tarjeta")
_txt5 = "Installed yoke and walls\nstarted the climb\nPending: car rails\nwaiting on parts\nInduction\nbuilt a gate\nmotor"
REG5 = {"fragmentos": [
    {"linea": 1, "texto": "Installed yoke", "clase": "done", "actividades": ["Install yoke/base, level it"], "pregunta": "", "motivo": ""},
    {"linea": 1, "texto": "and walls", "clase": "done", "actividades": ["Build cabin (walls)", "Install yoke/base, level it"], "pregunta": "", "motivo": ""},
    {"linea": 2, "texto": "started the climb", "clase": "started", "actividades": ["Install rings to top"], "pregunta": "", "motivo": "not finished"},
    {"linea": 3, "texto": "car rails", "clase": "pending", "actividades": [], "pregunta": "", "motivo": ""},
    {"linea": 4, "texto": "waiting on parts", "clase": "problem", "actividades": [], "pregunta": "", "motivo": "missing parts"},
    {"linea": 5, "texto": "Induction", "clase": "not_progress", "actividades": [], "pregunta": "", "motivo": "induction"},
    {"linea": 6, "texto": "built a gate", "clase": "outside_plan", "actividades": [], "pregunta": "", "motivo": "site gate"},
    {"linea": 7, "texto": "motor", "clase": "question", "actividades": ["Install motor bedplate", "Build cabin (walls)"], "pregunta": "Which?", "motivo": ""},
]}
_p = AG.propuestas(REG5, PLAN, {}, _txt5)
chk("lo HECHO, una fila por actividad, con las palabras del autor como prueba",
    [a["actividad"] for a in _p["actividades"]] == ["Install yoke/base, level it", "Build cabin (walls)"]
    and _p["actividades"][0]["pruebas"] == ["Installed yoke", "and walls"], _p["actividades"])
chk("una opción de pregunta que ya se propone suelta no se repite",
    [o["actividad"] for q in _p["preguntas"] for o in q["opciones"]] == ["Install motor bedplate"])
chk("⚠️ lo EMPEZADO no se puede marcar (no está en actividades ni preguntas)",
    "Install rings to top" not in {a["actividad"] for a in _p["actividades"]}
    | {o["actividad"] for q in _p["preguntas"] for o in q["opciones"]}
    and _p["empezadas"][0]["texto"] == "started the climb")
chk("pendiente, problema, no-avance y fuera del plan: cada uno en su sitio",
    _p["pendientes"][0]["termino"] == "car rails" and _p["problemas"][0]["motivo"] == "missing parts"
    and _p["aparte"][0]["texto"] == "Induction" and _p["fuera"][0]["actividad"] == "«built a gate»")
_solo = AG.propuestas({"fragmentos": [x for x in REG5["fragmentos"] if x["clase"] in ("started", "pending", "problem")]},
                      PLAN, {}, _txt5)
chk("⚠️ con solo empezado/pendiente/problema NO hay nada que confirmar", _solo["hay_algo"] is False)
_ya = AG.propuestas(REG5, PLAN, {(COD[C["Install yoke/base, level it"]][0], "Install yoke/base, level it"): 100.0}, _txt5)
chk("lo ya acreditado lo marca la PANTALLA (`hecha`), no la lectura",
    [a["hecha"] for a in _ya["actividades"]] == [True, False])
_d = AG.propuestas(REG5, PLAN, {}, _txt5, lineas=["car rails", "motor"])
chk("repartida la nota, cada destino ve SOLO los trozos de sus líneas (y «Pending: x» llega como «x»)",
    not _d["actividades"] and _d["pendientes"] and [q["termino"] for q in _d["preguntas"]] == ["motor"], _d)
_rip = S.plan_de("Ripout", ("traction",))
_o = AG.propuestas(REG5, _rip, {}, _txt5)
chk("en un destino cuyo plan NO tiene la actividad → «fuera del plan», no se marca",
    not _o["actividades"] and "Install yoke/base, level it" in {x["actividad"] for x in _o["fuera"]})
chk("`propone_algo` mira las líneas: «started…» sola no propone; «Installed yoke…» sí",
    not AG.propone_algo(REG5, PLAN, ["started the climb"], _txt5)
    and AG.propone_algo(REG5, PLAN, ["Installed yoke and walls"], _txt5))

# ═════════════════════════════════════════════════════════════════
sec("6. Guardar y recuperar la lectura")
_r = {"v": AG.LECTURA_V, "clave": AG.clave("x", PLAN), "fragmentos": [], "rondas": 1}
chk("la clave cambia con el texto y con el plan…", AG.clave("x", PLAN) != AG.clave("y", PLAN)
    and AG.clave("x", PLAN) != AG.clave("x", _rip))
chk("...y una lectura de otro texto NO vale", AG.vigente(_r, "x", PLAN) and not AG.vigente(_r, "x2", PLAN))
chk("un JSON de otra versión o roto no se toma por lectura",
    AG.de_json(json.dumps(dict(_r, v=99))) == {} and AG.de_json("{roto") == {})
_g = dict(_r, fragmentos=[{"texto": "x" * 1000}] * 60)
_s = AG.a_json(_g)
chk("⚠️ una lectura enorme cabe en la celda (recortada) y deja de valer",
    len(_s) <= 45000 and not AG.vigente(AG.de_json(_s), "x", PLAN), len(_s))
chk("el coste se calcula con los precios de Sonnet 5.5",
    AG.coste_usd({"in": 1_000_000, "out": 0, "cache_r": 0, "cache_w": 0}) == 2.0
    and AG.coste_usd({"in": 0, "out": 1_000_000, "cache_r": 1_000_000, "cache_w": 0}) == 10.2)

# ═════════════════════════════════════════════════════════════════
sec("7. ⚠️ Bajo AppTest, nunca la clave de verdad")
_at0 = AppTest.from_string(r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import parte_agente as AG
st.write("CLAVE:%s" % ("si" if AG.clave_api() else "no"))
st.write("SECRETO:%s" % ("si" if st.secrets.get("ANTHROPIC_API_KEY", "") else "no"))
''', default_timeout=60).run()
_v = [m.value for m in _at0.markdown]
chk("AppTest VE el secreto local (la prueba vale)…", "SECRETO:si" in _v, _v)
chk("...y aun así `clave_api()` devuelve vacío", "CLAVE:no" in _v, _v)
_imp = []
for _dp, _dn, _fs in os.walk(RAIZ):
    if "__pycache__" in _dp or ".venv" in _dp:
        continue
    for _fn in _fs:
        if _fn.endswith(".py"):
            try:
                _tr = ast.parse(open(os.path.join(_dp, _fn), encoding="utf-8").read())
            except Exception:
                continue
            for _n in ast.walk(_tr):
                if isinstance(_n, ast.ImportFrom) and (_n.module or "").startswith("streamlit.testing"):
                    _imp.append(_fn)
                elif isinstance(_n, ast.Import) and any(a.name.startswith("streamlit.testing") for a in _n.names):
                    _imp.append(_fn)
chk("la app NO importa `streamlit.testing` en ningún sitio (si no, el agente se apagaría)", not _imp, _imp)

# ═════════════════════════════════════════════════════════════════
sec("8. La tarjeta EJECUTADA (AppTest, modelo sustituido)")
APP = r'''
import datetime as _dt
import sys
import time
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import clock, daily_log as DL, daily_log_ui as DLU, flash, parte_agente as AG
from core import projects as P, stage_progress as SP, stages as S

PLAN = S.plan_de("Installation", ())
_T, _COD = AG.plan_en_codigos(PLAN)
C = {v[2]: k for k, v in _COD.items()}
HOY = "2026-10-26"
ss = st.session_state
for _k, _v in (("_rev", {}), ("_reg", {}), ("_cred", []), ("_hecho", {}), ("_guard", {})):
    ss.setdefault(_k, _v)
if not hasattr(AG, "_llam"):
    AG._llam = []
INFO = {"seg": 0.05, "modelo": "claude-sonnet-5-5", "uso": {"in": 100, "out": 50, "cache_r": 0, "cache_w": 0}}
T1 = "Installed yoke, platform, walls, and ceiling, start climbing the shaft"
T2 = "Isntalled the motor\ndid the thing"
T3 = "TIMEOUT installed sills"
T4 = "zzz qqq"
T5 = "Installed sills\nIssues:\nfinished the frames"


def _fr(line, text, cl, names=(), q="", r=""):
    return {"line": line, "text": text, "class": cl, "codes": [C[n] for n in names],
            "question": q, "reason": r, "lift": ""}


# v610 · `_llamar` recibe también la memoria del agente (CREW MEMORY).
def _llamar(api_key, texto, fecha, plan, mapa, previa, respuestas, idioma, memoria=""):
    AG._llam.append({"texto": texto, "previa": bool(previa), "resp": list(respuestas or []),
                     "key": api_key, "t0": time.time()})
    time.sleep(0.05)
    AG._llam[-1]["t1"] = time.time()
    if texto.startswith("TIMEOUT"):
        raise AG._Fallo("timeout")
    if texto == T4:
        return {"fragments": [_fr(1, T4, "unclear", q="What is zzz?")]}, INFO
    if texto == T5:
        return {"fragments": [_fr(1, "Installed sills", "done", ["Install sills"]),
                              _fr(2, "Issues:", "not_progress", r="Section heading only"),
                              _fr(3, "finished the frames", "done", ["Install frames"])]}, INFO
    if texto == T1:
        return {"fragments": [
            _fr(1, "Installed yoke", "done", ["Install yoke/base, level it"]),
            _fr(1, "platform", "done", ["Install platform (cradle)"]),
            _fr(1, "walls", "done", ["Build cabin (walls)"]),
            _fr(1, "and ceiling", "done", ["Install cabin ceiling (roof)"]),
            _fr(1, "start climbing the shaft", "started", ["Install rings to top"], r="not finished")]}, INFO
    if texto == T2:
        if respuestas:
            return {"fragments": [_fr(1, "Isntalled the motor", "done", ["Install motor bedplate"]),
                                  _fr(2, "did the thing", "unclear", q="Still unclear?")]}, INFO
        return {"fragments": [
            _fr(1, "Isntalled the motor", "question", ["Install motor bedplate", "Install single bedplate"], q="Which bedplate?"),
            _fr(2, "did the thing", "unclear", q="What thing?")]}, INFO
    return {"fragments": []}, INFO


AG._llamar = _llamar
AG.clave_api = lambda: ss.get("_clave", "sk-test")
LOGS = ss.get("_logs") or [
    {"ID": "LOG-9101", "Date": "2026-10-25", "Author": "campo000", "Created": HOY + " 17:50:00", "Text": T1},
    {"ID": "LOG-9102", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:40:00", "Text": T2},
    {"ID": "LOG-9103", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:30:00", "Text": T3},
    {"ID": "LOG-9104", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:20:00", "Text": "Installed frames",
     "Reviewed": HOY + " 18:00:00", "ReviewedBy": "campo000"},
    {"ID": "LOG-9105", "Date": HOY, "Author": "otro", "Created": HOY + " 17:10:00", "Text": "Installed headers"},
    {"ID": "LOG-9106", "Date": HOY, "Author": "campo000", "Created": HOY + " 17:00:00", "Text": T4},
    {"ID": "LOG-9107", "Date": HOY, "Author": "campo000", "Created": HOY + " 16:50:00", "Text": T5},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001")
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = HOY + " 18:00:00", ss["_rev"][r["ID"]]
        out.append(_r)
    return out


def _acreditar(pid, grupo, prj, creditos, quien="", origen=SP.MANUAL, fecha=None):
    ss["_cred"].append({"pid": pid, "origen": origen, "fecha": fecha,
                        "creditos": [dict(c) for c in creditos]})
    return True, "ok"


def _revisar(lid, quien, propuestas=""):
    ss["_rev"][lid] = quien
    ss["_reg"][lid] = propuestas
    return True, "Reviewed."


def _guardar(d):
    ss["_guard"].update(d)
    return True, len(d)


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = _revisar
DL.crear = lambda *a, **k: (True, "LOG-X")
DL.guardar_lecturas = _guardar
clock.today = lambda grupo=None: _dt.date(2026, 10, 26)
P.get_project = lambda pid: {"ID": pid, "Name": "ZZ Test tower · Lift 1", "Type": "Installation"}
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [{"ID": "PRJ-9001", "Name": "ZZ Test"}]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: dict(ss["_hecho"].get(pid, {}))
SP.acreditar = _acreditar
SP.de_parte = lambda pid, lid: []
# ⚠️ El ORDEN de la shell (trampa 41): los avisos se pintan ANTES de la sección.
flash.mostrar()
if ss.get("_admin"):
    DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
else:
    DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _cb(at, pref):
    return {c.key: c for c in at.checkbox if (c.key or "").startswith(pref)}


def _ti(at, key):
    return next((x for x in at.text_input if x.key == key), None)


def _todo(at):
    # ⚠️ Los avisos de `flash` son `st.success`/`st.warning`/…: sin ellos la sonda no los ve.
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(getattr(e, "label", "")) for e in list(at.expander) + list(at.status)] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


AG._llam = []
at = AppTest.from_string(APP, default_timeout=90).run()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ll = list(AG._llam)
chk("⚠️ se leen los CINCO propios sin revisar — ni el revisado ni el ajeno",
    sorted(x["texto"][:12] for x in _ll) == sorted(["Installed yo", "Isntalled th", "TIMEOUT inst",
                                                    "zzz qqq", "Installed si"]),
    [x["texto"][:20] for x in _ll])
chk("...con la clave que da `clave_api` (la sustituida)", all(x["key"] == "sk-test" for x in _ll))
_pri = min(_ll, key=lambda x: x["t0"]) if _ll else {}
chk("⚠️ el PRIMERO solo y el resto después (escribe la caché del prompt para los demás)",
    len(_ll) == 5 and all(x["t0"] >= _pri["t1"] - 1e-3 for x in _ll if x is not _pri), _ll)
chk("se GUARDAN en la hoja las que se leyeron; la fallida no",
    sorted(at.session_state["_guard"]) == ["LOG-9101", "LOG-9102", "LOG-9106", "LOG-9107"],
    sorted(at.session_state["_guard"]))
_g1 = AG.de_json(at.session_state["_guard"].get("LOG-9101", ""))
chk("lo guardado dice cuánto documento del oficio llegó (`ref`, para verlo en producción)",
    _g1.get("ref") == len(AG._referencia()) > 0, _g1.get("ref"))
chk("...y lo guardado es una lectura vigente de ese texto", AG.vigente(
    _g1, "Installed yoke, platform, walls, and ceiling, start climbing the shaft", PLAN))
_md = _todo(at)
chk("cuatro tarjetas «What the assistant read» y una «What the app read» (la que falló)",
    sum("What the assistant read in your log" in x for x in _md) == 4
    and sum("What the app read in your log" in x for x in _md) == 1, [x for x in _md if "read in your log" in x])
chk("⚠️ la que falló LO DICE (no se toma la lista de palabras por el agente)",
    any("The assistant could not read this log (it took too long)" in x for x in _md))
_a1 = _cb(at, "fld_pp_LOG-9101_PRJ-9001_a_")
chk("las 4 actividades hechas, como casillas, TODAS sin marcar",
    sorted(k.split("_a_", 1)[1].split("_", 1)[1] for k in _a1) == sorted(
        ["Install yoke/base, level it", "Install platform (cradle)", "Build cabin (walls)",
         "Install cabin ceiling (roof)"]) and not any(c.value for c in _a1.values()), list(_a1))
chk("⚠️ lo empezado NO es una casilla", not [k for k in _cb(at, "fld_pp_LOG-9101") if "rings to top" in k])
chk("...pero se enseña, con sus palabras", any("Started, not finished" in x and "start climbing the shaft" in x
                                               for x in _md))
_q2 = _cb(at, "fld_pp_LOG-9102_PRJ-9001_q_")
chk("la pregunta del agente: las dos opciones como casillas", len(_q2) == 2, list(_q2))
chk("lo no entendido lleva su CAJA para contestar", _ti(at, "fld_pp_LOG-9102_ag1_0") is not None
    and "did the thing" in (_ti(at, "fld_pp_LOG-9102_ag1_0").label or ""))
chk("...y «Read it again»", _bt(at, "fld_pp_LOG-9102_ag_releer") is not None)
chk("⚠️ un parte que el agente no entendió ENTERO tiene tarjeta: su caja y «Nothing to credit»",
    _ti(at, "fld_pp_LOG-9106_ag1_0") is not None and _bt(at, "fld_pp_LOG-9106_no") is not None)

_a7 = _cb(at, "fld_pp_LOG-9107_PRJ-9001_a_")
chk("lo hecho bajo «Issues:» se ofrece (casilla) CON el aviso a la vista",
    len(_a7) == 2 and any("lists this under «Issues/Pending»" in x for x in _md), list(_a7))
chk("lo que no es avance, en un desplegable CERRADO con su motivo",
    any("Not progress on this job (1)" in x for x in _md)
    and any("Section heading only" in x for x in _md))

at.run()
chk("⚠️ una recarga NO vuelve a llamar (lectura de la sesión) ni reintenta la que falló",
    len(AG._llam) == 5, len(AG._llam))

# ── confirmar: solo lo marcado, con el lector en el registro ──
for _k in ("fld_pp_LOG-9101_PRJ-9001_a_%d_Install yoke/base, level it" % COD[C["Install yoke/base, level it"]][0],
           "fld_pp_LOG-9101_PRJ-9001_a_%d_Build cabin (walls)" % COD[C["Build cabin (walls)"]][0]):
    _c = _cb(at, _k).get(_k)
    if _c is not None:
        _c.check()
at.run()
_b = _bt(at, "fld_pp_LOG-9101_ok")
if _b is not None:
    _b.click()
    at.run()
_cr = at.session_state["_cred"]
chk("⚠️ se acredita SOLO lo marcado, desde el parte y con SU fecha",
    len(_cr) == 1 and sorted(c["actividad"] for c in _cr[0]["creditos"]) == [
        "Build cabin (walls)", "Install yoke/base, level it"] and _cr[0]["origen"] == "log"
    and _cr[0]["fecha"] == "2026-10-25", _cr)
_R = PP.leer_registro(at.session_state["_reg"].get("LOG-9101", ""))
chk("el registro dice QUIÉN leyó el parte (para medir el agente aparte)",
    _R.get("lector") == "claude-sonnet-5-5/p%s" % AG.PROMPT_V, _R.get("lector"))

# ── preguntar: «Read it again» ──
_n0 = len(AG._llam)
_b = _bt(at, "fld_pp_LOG-9102_ag_releer")
if _b is not None:
    _b.click()
    at.run()
chk("«Read it again» SIN respuestas no llama y lo dice", len(AG._llam) == _n0
    and any("Write what you meant first" in x for x in _todo(at)), len(AG._llam) - _n0)
_x = _ti(at, "fld_pp_LOG-9102_ag1_0")
if _x is not None:
    _x.set_value("the controller wiring")
    at.run()
_b = _bt(at, "fld_pp_LOG-9102_ag_releer")
if _b is not None:
    _b.click()
    at.run()
_u = AG._llam[-1] if len(AG._llam) > _n0 else {}
chk("con respuesta: UNA lectura nueva, con la anterior y la respuesta como datos",
    len(AG._llam) == _n0 + 1 and _u.get("previa") and _u.get("resp") == [
        {"linea": 2, "texto": "did the thing", "respuesta": "the controller wiring"}], _u)
_g2 = AG.de_json(at.session_state["_guard"].get("LOG-9102", ""))
chk("...guardada como ronda 2", _g2.get("rondas") == 2, _g2.get("rondas"))
chk("...la tarjeta enseña lo nuevo (el motor, ahora propuesto)",
    any(k.endswith("_a_%d_Install motor bedplate" % COD[C["Install motor bedplate"]][0])
        for k in _cb(at, "fld_pp_LOG-9102_PRJ-9001_a_")), list(_cb(at, "fld_pp_LOG-9102")))
chk("...y lo dice", any("read your log again with your answers" in x for x in _todo(at)))
chk("las cajas nuevas nacen VACÍAS (otra ronda, otra clave)",
    _ti(at, "fld_pp_LOG-9102_ag2_0") is not None and not _ti(at, "fld_pp_LOG-9102_ag2_0").value)
_x = _ti(at, "fld_pp_LOG-9102_ag2_0")
if _x is not None:
    _x.set_value("it was the cabin header")
    at.run()
    _b = _bt(at, "fld_pp_LOG-9102_ag_releer")
    if _b is not None:
        _b.click()
        at.run()
_u = AG._llam[-1]
chk("la ronda 3 lleva TODAS las respuestas, no solo la última",
    [x["respuesta"] for x in _u.get("resp", [])] == ["the controller wiring", "it was the cabin header"], _u.get("resp"))
chk("⚠️ con el tope de rondas, ya no hay «Read it again» y se dice qué hacer",
    _bt(at, "fld_pp_LOG-9102_ag_releer") is None
    and any("has read this log 3 times" in x for x in _todo(at)))
chk("nada más se acreditó sin un clic", len(at.session_state["_cred"]) == 1)

# ── lo guardado en la hoja se reutiliza en otra sesión; lo de otro texto, no ──
_guard = dict(at.session_state["_guard"])
_logs2 = [
    {"ID": "LOG-9101", "Date": "2026-10-25", "Author": "campo000", "Created": "2026-10-26 17:50:00",
     "Text": "Installed yoke, platform, walls, and ceiling, start climbing the shaft", "Reading": _guard["LOG-9101"]},
    {"ID": "LOG-9102", "Date": "2026-10-26", "Author": "campo000", "Created": "2026-10-26 17:40:00",
     "Text": "Isntalled the motor\ndid the thing", "Reading": json.dumps(dict(_g2, clave="otra"))},
]
AG._llam = []
at2 = AppTest.from_string(APP, default_timeout=90)
at2.session_state["_logs"] = _logs2
at2.run()
chk("otra sesión: la lectura guardada en la hoja se USA (no se paga otra vez)",
    "Installed yoke, platform, walls, and ceiling, start climbing the shaft" not in [x["texto"] for x in AG._llam]
    and any("What the assistant read" in x for x in _todo(at2)), [x["texto"][:15] for x in AG._llam])
chk("...y una lectura que ya no vale (otra clave) se rehace", [x["texto"][:10] for x in AG._llam] == ["Isntalled "])

# ── sin agente (sin clave): la tarjeta de siempre, sin llamar ──
AG._llam = []
at3 = AppTest.from_string(APP, default_timeout=90)
at3.session_state["_clave"] = ""
at3.run()
_m3 = _todo(at3)
chk("sin clave: ninguna llamada", not AG._llam, len(AG._llam))
chk("...la tarjeta del vocabulario, como hasta v606, y sin el aviso de fallo",
    any("What the app read in your log" in x for x in _m3)
    and not any("What the assistant read" in x for x in _m3)
    and not any("could not read this log" in x for x in _m3))

# ── el admin no lee (no tiene tarjeta) ──
AG._llam = []
at4 = AppTest.from_string(APP, default_timeout=90)
at4.session_state["_admin"] = True
at4.run()
chk("la vista del admin NO llama al modelo", not AG._llam and not at4.exception, len(AG._llam))

AG.clave_api, AG._llamar = _ORIG["clave_api"], _ORIG["_llamar"]

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
