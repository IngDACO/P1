# -*- coding: utf-8 -*-
"""v632 · EL ASISTENTE EN SONNET, LA BAJA PASO A PASO, STRIKER (02/11/2026, «Dale con todo», «Es striker», «Pasalo a sonnet»).

  (1) ⚠️ Con Haiku rellenaba lo que no sabía → `claude-sonnet-5-5`. No basta cambiar el nombre: razona, así que la
      respuesta puede empezar por un bloque `thinking` (sin `.text`), un rechazo llega como respuesta normal y el
      razonamiento gasta del mismo `max_tokens`. Se ensaya aquí cada forma, con la API sustituida y sin red.
  (2) ⚠️ La baja: colocaba el atajo en My absences y decía que se enteraba la cuadrilla → los pasos, escritos en la
      guía, y lo que dicen comparado con la pantalla y con quien avisa de verdad.
  (3) «Es striker»: Buffers decía «car sticker» y Belting «striker».
  (4) El informe interno decía «Valor» y «SI» (destapado al barrer la forma de «Proyecto», v631).
"""
import ast
import os
import re
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                                       # noqa: E402
from core import ausencias as AU, buffer_cut as BC, chat_agent as CA  # noqa: E402

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


def bloque(tipo, **kw):
    return types.SimpleNamespace(type=tipo, **kw)


def respuesta(content, stop="end_turn"):
    return types.SimpleNamespace(content=content, stop_reason=stop)


_vistos, _resumen, _cola = [], [], []


class _Msgs:
    def __init__(self, destino):
        self.destino = destino

    def create(self, **kw):
        self.destino.append(kw)
        return _cola.pop(0) if _cola else respuesta([bloque("text", text="ok")])


_man = types.SimpleNamespace(is_available=lambda: False)
_dig = types.SimpleNamespace(group_snapshot_text=lambda g: "", group_digest=lambda g: {}, digest_text=lambda d: "hechos")
CA.anthropic = types.SimpleNamespace(
    # ⚠️ v655 · `**_kw`: el cliente de verdad lleva ahora timeout y max_retries (antes, solo la clave)
    Anthropic=lambda api_key=None, **_kw: types.SimpleNamespace(
        messages=_Msgs(_resumen), beta=types.SimpleNamespace(messages=_Msgs(_vistos))),
    AuthenticationError=type("A", (Exception,), {}), RateLimitError=type("R", (Exception,), {}))
CA.st = types.SimpleNamespace(secrets={"ANTHROPIC_API_KEY": "x"})
sys.modules["core.manuals"] = _man
sys.modules["core.admin_digest"] = _dig
core.manuals = _man
core.admin_digest = _dig


def pregunta(*resp, history=()):
    _cola[:] = list(resp)
    return CA.get_chat_response("hola", list(history), None, None, rol="field", grupo="cliente1")


# ─────────────────────────────────────────────────────────────────────────────
sec("1. Lo que se le pide a la API")
_h = [{"role": "user", "content": "antes"}, {"role": "assistant", "content": "respuesta"}]
chk("responde", pregunta(history=_h) == "ok")
_k = _vistos[-1]
chk("⚠️ el modelo es Sonnet 5.5", _k.get("model") == "claude-sonnet-5-5", _k.get("model"))
chk("esfuerzo bajo, dicho expresamente", _k.get("output_config") == {"effort": "low"}, _k.get("output_config"))
chk("⚠️ `max_tokens` da para razonar y responder", _k.get("max_tokens", 0) >= 4000, _k.get("max_tokens"))
chk("respaldo del servidor, con su beta",
    _k.get("fallbacks") == "default" and _k.get("betas") == ["server-side-fallback-2026-07-01"], _k.get("betas"))
chk("⚠️ nada que Sonnet 5.5 rechace (temperature, top_p, thinking disabled, budget_tokens)",
    not ({"temperature", "top_p", "top_k", "thinking"} & set(_k)), sorted(_k))
chk("el historial sigue siendo texto, y la pregunta va al final",
    [m["content"] for m in _k["messages"]] == ["antes", "respuesta", "hola"])
chk("mismo respaldo que `parte_agente`", CA._BETA_RESPALDO == __import__("core.parte_agente", fromlist=["x"])._BETA_RESPALDO)

# ⚠️ v647 · CADUCADO por decisión del usuario: el resumen del día pasa a Sonnet 5.5, como los demás agentes, en su
# propio módulo (verif_v647). Sin `admin_briefing` en el asistente.
from core import resumen_dia as _RD                                # noqa: E402
chk("el resumen del día, también en Sonnet 5.5 (y fuera del asistente)", _RD.MODELO == "claude-sonnet-5-5"
    and not hasattr(CA, "admin_briefing") and not hasattr(CA, "MODEL_RESUMEN"))

# ─────────────────────────────────────────────────────────────────────────────
sec("2. Lo que vuelve de la API: cada forma, sin error en el chat")
_pens = bloque("thinking", thinking="", signature="s")
chk("⚠️ empieza por razonamiento: se lee el texto", pregunta(respuesta([_pens, bloque("text", text="hola")])) == "hola")
chk("dos bloques de texto, juntos", pregunta(respuesta([bloque("text", text="a"), _pens, bloque("text", text="b")])) == "ab")
_x = pregunta(respuesta([], stop="refusal"))
chk("⚠️ un rechazo no sale como error de la API", _x.startswith("⚠️ I can't answer") and "API" not in _x, _x)
_x = pregunta(respuesta([bloque("text", text="medio")], stop="refusal"))
chk("...aunque traiga texto a medias", "medio" not in _x, _x)
_x = pregunta(respuesta([bloque("text", text="corta")], stop="max_tokens"))
chk("cortada por tokens: la parte que hay y lo dice", _x.startswith("corta") and "cut short" in _x, _x)
_x = pregunta(respuesta([_pens], stop="max_tokens"))
chk("⚠️ todo se fue en razonar: un mensaje, no un chat en blanco", _x.startswith("⚠️ I could not get an answer"), _x)
_x = pregunta(respuesta([]))
chk("sin contenido: un mensaje", _x.startswith("⚠️ I could not get an answer"), _x)
_cuerpo = leer("core/chat_agent.py")
_i = _cuerpo.index("def get_chat_response")
chk("ya no se lee por posición en el asistente", "content[0]" not in _cuerpo[_i:])

# ─────────────────────────────────────────────────────────────────────────────
sec("3. La baja: lo que dicen los pasos es lo que hace la pantalla")
P = CA.SYSTEM_PROMPT
G = re.sub(r"\s+", " ", P)
_a = G.index("**Si hoy está enfermo y no puede ir:**")
_rec = G[_a:G.index("- **My credentials (Self-service):**")]
_u = leer("core/ausencias_ui.py")
chk("el paso 1 es la pantalla", "1. **Self-service → My absences**." in _rec, _rec[:120])
chk("el paso 2 cita el selector real", 't("What do you need?")' in _u and "En **What do you need?** elige **Sick leave**" in _rec)
chk("...y el nombre del tipo", AU.TIPOS[AU.ENFERMEDAD]["nombre"] == "Sick leave", AU.TIPOS[AU.ENFERMEDAD])
chk("las fechas vienen con hoy, como dice", 't("From"), value=hoy' in _u and 't("To"), value=hoy' in _u)
chk("el paso 3 cita el botón real", "Record the sick leave" in _u and "3. Pulsa **Record the sick leave**." in _rec)
chk("sin aprobación, como dice", AU.TIPOS[AU.ENFERMEDAD]["aprobacion"] is False and "sin aprobación" in _rec)
# ⚠️ v640 · Lo que va tras guardar vive en `registrar`, una sola definición para la pantalla y el asistente
_b = _u[_u.index('def registrar('):_u.index('def _pedir(')]
chk("sale en la planificación, como dice", "AU.aplicar_al_roster" in _b and "sale en la planificación" in _rec)
chk("avisa a la oficina, como dice", "_avisar_admins(" in _b and "la oficina recibe el aviso" in _rec)
_v = _u[_u.index("def _avisar_admins"):]
chk("⚠️ y solo a ella: a la cuadrilla no se le avisa", "_admins_and_owners(grupo)" in _v[:1500] and "crew" not in _rec.lower())
chk("⚠️ el atajo es de Timeclock, no de My absences", "es un botón de **Timeclock**, NO de My absences" in _rec)
_tc = leer("core/timeclock_ui.py")
chk("...que sale si no ha fichado ni trabajado hoy, como dice",
    'if rol == "field" and not gen and not prj and hoy["general"] <= 0 and hoy["proyecto"] <= 0:' in _tc
    and "sale si aún no ha fichado ni ha trabajado hoy" in _rec)
chk("...y desde ahí sigue por el paso 2", "donde sigue por el paso 2" in _rec)
chk("solo hay una receta", G.count("**Record the sick leave**") == 2, G.count("**Record the sick leave**"))

# ─────────────────────────────────────────────────────────────────────────────
sec("4. La regla: ni pasos ni sitios que no estén en la guía")
_r = re.sub(r"\s+", " ", P[P.index("## LO QUE NO SABES"):P.index("## SIGLAS DE LAS HERRAMIENTAS")])
chk("⚠️ no añade pasos", "No añadas pasos ni digas quién se entera o qué pasa después si no está aquí" in _r, _r[-300:])
chk("⚠️ no inventa dónde está un dato", "No inventes en qué sección o página está un dato" in _r)

# ─────────────────────────────────────────────────────────────────────────────
sec("5. «Es striker»")
_rest = []
for _carp in ("core", "extractors"):
    for _f in os.listdir(os.path.join(RAIZ, _carp)):
        if _f.endswith(".py") and "sticker" in leer("%s/%s" % (_carp, _f)).lower():
            _rest.append(_f)
chk("⚠️ ni un «sticker» en la app, tampoco en las traducciones", not _rest, _rest)
chk("Buffers lo dice", "HKP (mm) — car striker ↔ buffer serving the 1st level" in leer("core/buffer_cut_ui.py"))
chk("Belting ya lo decía", "HGP — design striker↔buffer (mm)" in leer("core/belting_ui.py"))
chk("la guía del asistente también", "- **HKP:** car striker ↔ buffer serving the 1st level" in G)
_svg = BC.buffer_cut_svg(BC.compute_buffer_cut(520.0, [500.0, 505.0]), "Obra")
chk("⚠️ en el diagrama de verdad", "CAR STRIKER" in _svg and "widens the striker" in _svg and "sticker" not in _svg.lower(), _svg[:200])

# ─────────────────────────────────────────────────────────────────────────────
sec("6. El informe interno, en inglés")
_rp = leer("core/report.py")
_arbol = ast.parse(_rp)
_yn = next(n for n in ast.walk(_arbol) if isinstance(n, ast.FunctionDef) and n.name == "_yn")
_ns = {}
exec(compile(ast.Module([_yn], []), "yn", "exec"), _ns)
chk("⚠️ «YES», no «SI»", (_ns["_yn"](True), _ns["_yn"](False)) == ("YES", "NO"), _ns["_yn"](True))
chk("⚠️ «Value», no «Valor»", "<b>Valor</b>" not in _rp and _rp.count("_d('Value')") == 2, _rp.count("_d('Value')"))

print("\n=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
for x in fallos:
    print("  FALLO: %s" % x)
sys.exit(1 if fallos else 0)
