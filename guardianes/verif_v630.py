# -*- coding: utf-8 -*-
"""v630 · EL ASISTENTE DEL CAMPO (02/11/2026, «Dale»).

La auditoría de «¿ya terminamos con el campo?»: el asistente nunca entró en el recorrido y orientaba mal.
  (1) ⚠️ su menú era de otra época: mandaba a «Mis colillas» y «Mis credenciales» y no conocía Self-service ni
      Library → las líneas del menú se DERIVAN aquí de `home_ui`: tocar un menú sin tocar la guía pone rojo;
  (2) ⚠️ decía «si aún no ha fichado, la herramienta se lo pide» y que solo la oficina guarda el Survey (falso desde
      v625), y no sabía de Absences, To-do, Daily log ni Library;
  (3) ⚠️ todas las pantallas en español, con la app en inglés → los nombres que se ven;
  (4) ⚠️ inventó qué es LFKK (07/10) → regla: lo que no está definido, no se deduce.
Lo que afirma la guía se compara con el código: un guardián que solo busque el texto en la guía no prueba que sea
verdad (trampas 1 y 42). Sin red: la llamada a la API va sustituida (trampa 44).
"""
import os
import re
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                                       # noqa: E402
from core import ausencias as AU, chat_agent as CA, home_ui as H, payroll_ui as PAY   # noqa: E402

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


def lbl(d):
    return re.sub(r":material/[a-z0-9_]+:\s*", "", d).strip()


def linea(secs, subs):
    """Las secciones de un rol, como las dice la guía. Las de Tools van en su propia línea."""
    out = []
    for k, d in secs:
        x = lbl(d)
        if k in subs and k != "herramientas":
            x += " (%s)" % " · ".join(lbl(s[1]) for s in subs[k][1])
        out.append(x)
    return " · ".join(out)


P = CA.SYSTEM_PROMPT
_ini = P.index("## FUNCIONES DE LA APP COPEX")
_fin = P.index("Roles/grupos: cada empresa cliente")
G = P[_ini:_fin]
G_L = re.sub(r"\s+", " ", G)                                        # la guía va partida en líneas


sec("1. ⚠️ El menú de cada rol es el de la app (derivado de `home_ui`)")
_adm = linea(H._SECCIONES, H._SUBSECCIONES)
_cam = linea(H._SECCIONES_CAMPO, H._SUBSECCIONES_CAMPO)
_own = linea(H._SECCIONES_OWNER, H._SUBSECCIONES_OWNER)
chk("se extrajo algo de verdad", "Self-service (My absences" in _cam and "Planning (Panel" in _adm
    and "Administration (Summary" in _own, (_cam, _adm, _own))
chk("⚠️ campo", "- **Field:** %s.\n" % _cam in G, _cam)
chk("oficina", "- **Administrator:** %s.\n" % _adm in G, _adm)
chk("propietario", "- **Owner:** %s. No ficha.\n" % _own in G, _own)
_tools = [lbl(s[1]) for s in H._SUBSECCIONES_CAMPO["herramientas"][1] if lbl(s[1]) != "Home"]
chk("las 5 herramientas", len(_tools) == 5 and "**Tools**: %s (más" % " · ".join(_tools) in G, _tools)
chk("el Pre-Start no va entre las herramientas del campo", "Pre-Start" not in _tools)


sec("2. Las pestañas de «My projects» y del detalle de la obra")
_pu = leer("core/projects_ui.py")
_m = re.search(r'format_func=lambda o: \{"🏗 Avance".*?\}\.get\(o, o\)', _pu, re.S)
_tabs = [lbl(x) for x in re.findall(r't\("([^"]+)"\)', _m.group(0))] if _m else []
chk("se leyeron las 6 pestañas del campo", len(_tabs) == 6, _tabs)
_mp = G[G.index("- **My projects (field):**"):G.index("- **Administration (owner):**")]
for _t in _tabs:
    chk("⚠️ la guía explica «%s»" % _t, "  - **%s:**" % _t in _mp)
_m = re.search(r'format_func=lambda o: \{"📊 Estado".*?\}\.get\(o, o\)', _pu, re.S)
_det = [lbl(x) for x in re.findall(r't\("([^"]+)"\)', _m.group(0))] if _m else []
_dg = G[G.index("- **Detalle de un proyecto**"):G.index("- **Finance (administrator):**")]
chk("las 5 del detalle", len(_det) == 5 and "(%d pestañas)" % len(_det) in _dg
    and all("**%s**" % d in _dg for d in _det), _det)


sec("3. ⚠️ Lo que era falso ya no se dice")
for _f in ("no elige nada", "la herramienta se lo pide", "Mis colillas", "Mis credenciales", "Mis proyectos",
           "Planificación", "Finanzas", "**Fichaje", "**Archivos**", "**Costos**", "**Datos**", "**Estado**",
           "Nuevo proyecto", "Corte de rieles", "Corte de buffers", "Líneas de plomada", "**Inventario",
           "**Contactos", "**Agrupaciones", "**Administración", "DOS relojes para TODOS"):
    chk("fuera: «%s»" % _f, _f not in G)
chk("sin versiones internas en la guía", not re.search(r"\bv\d{2,3}\b", G), re.findall(r"\bv\d{2,3}\b", G))
chk("sin nombres de código (confidencialidad)", not re.search(r"\.py\b|core\.|_ui\b|session_state", G))


sec("4. Lo nuevo del campo, y que sea VERDAD en el código")
chk("Annual leave y Day off esperan aprobación",
    AU.TIPOS[AU.VACACIONES]["aprobacion"] is True and AU.TIPOS[AU.LIBRE]["aprobacion"] is True
    and "**%s** y **%s** esperan" % (AU.TIPOS[AU.VACACIONES]["nombre"], AU.TIPOS[AU.LIBRE]["nombre"]) in G)
chk("⚠️ Sick leave se registra al momento", AU.TIPOS[AU.ENFERMEDAD]["aprobacion"] is False
    and "**%s** no: se registra al momento" % AU.TIPOS[AU.ENFERMEDAD]["nombre"] in G)
chk("las nóminas salen de 10 en 10", PAY._MAX_COLILLAS == 10 and "Salen las %d últimas" % PAY._MAX_COLILLAS in G)
chk("⚠️ el campo guarda el Survey", 'if _ROL in ("administrator", "owner", "field"):' in leer("core/survey_ui.py")
    and "El campo lo guarda en la\n  obra donde midió" in G)
_pl = leer("core/plan_ui.py")
chk("⚠️ sin fichar usa su obra o elige", "if len(suyas) == 1:\n            prj = suyas[0]" in _pl
    and "con varias, elige entre las suyas" in G)
chk("otro PDF a mano sigue siendo cierto en las 4 herramientas",
    all("plan_store.selector(" in leer("core/%s_ui.py" % h) for h in ("plumb", "rail_cut", "buffer_cut", "belting"))
    and "Siempre se puede cargar otro PDF a mano" in G)
for _b, _f in (("Assigned project", "projects_ui"), ("Report a problem to the administrator", "projects_ui"),
               ("See the week's plan (the whole crew)", "projects_ui"), ("My route (my sites on the map)", "projects_ui"),
               ("Save all", "stage_progress_ui"), ("Save stage", "stage_progress_ui"),
               ("Request a day off or annual leave, or report sick leave", "ausencias_ui"),
               ("Record the sick leave", "ausencias_ui"), ("Include weekends", "ausencias_ui"),
               ("My requests", "ausencias_ui"), ("I cannot make it today — report sick leave", "timeclock_ui"),
               ("Did you forget to clock in or out?", "timeclock_ui"), ("Close forgotten session", "timeclock_ui"),
               ("Entry left open", "home_ui"), ("Sign the Pre-Start", "prestart_ui"),
               ("Download payslip", "payroll_ui"), ("Show all", "payroll_ui"), ("New project", "projects_ui")):
    chk("«%s»: en la guía y en la app" % _b, _b in G_L and _b in leer("core/%s.py" % _f), _f)
chk("Library: el zoom y los filtros de la guía", all(x in G for x in ("1× · 2× · 3×", "**Type**", "**Brand**"))
    and '_ZOOMS = ["1×", "2×", "3×"]' in leer("core/library_ui.py"))
chk("Library: solo el propietario añade", "Only the owner adds material" in leer("core/library_ui.py")
    and "Solo el propietario añade material" in G)


sec("5. ⚠️ Lo que no sabe, no lo inventa")
_r = P[P.index("## LO QUE NO SABES, NO LO INVENTES"):P.index("## CONFIDENCIALIDAD")] \
    if "## LO QUE NO SABES, NO LO INVENTES" in P else ""
chk("la regla existe y va antes de la confidencialidad", bool(_r))
chk("⚠️ siglas: no se deducen por el nombre", "NUNCA deduzcas" in _r and "Saber que la app LEE un valor" in _r)
chk("pantallas: no se suponen", "No supongas que existe" in _r)
chk("sus datos: no da cifras que no tiene", "sin dar ninguna cifra" in _r)
chk("no le quita responder de instalación", "preguntas generales de instalación" in _r)
chk("⚠️ LFKK sigue sin definirse (espera al glosario): no le demos una definición falsa",
    all(not re.search(r"(LFKK|LFGK)\s*(=|:|es |significa)", ln) for ln in P.splitlines()),
    [ln for ln in P.splitlines() if "LFKK" in ln])


sec("6. La persona del campo")
_pf = CA._PERSONA["field"]
for _x in ("parte del día", "lista de pendientes", "Pre-Start", "ausencia", "baja", "Library", "nóminas",
           "línea **Field** de la guía"):
    chk("sabe de: %s" % _x, _x in _pf)
chk("no le dice que solo actualice el % de avance", "actualizar el % de avance" not in _pf)


sec("7. Y eso es lo que llega al modelo (API sustituida, sin red)")
_vistos = []


class _Msgs:
    def create(self, **kw):
        _vistos.append(kw)
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text="ok")],
                                     stop_reason="end_turn")


_falso = types.SimpleNamespace(
    Anthropic=lambda api_key=None: types.SimpleNamespace(messages=_Msgs(),
                                                         beta=types.SimpleNamespace(messages=_Msgs())),
    AuthenticationError=type("A", (Exception,), {}), RateLimitError=type("R", (Exception,), {}))
_man = types.SimpleNamespace(is_available=lambda: False)
_dig = types.SimpleNamespace(group_snapshot_text=lambda g: "VIVO DEL GRUPO",
                             group_digest=lambda g: {}, digest_text=lambda d: "hechos")
CA.anthropic = _falso
CA.st = types.SimpleNamespace(secrets={"ANTHROPIC_API_KEY": "x"})
sys.modules["core.manuals"] = _man
sys.modules["core.admin_digest"] = _dig
core.manuals = _man
core.admin_digest = _dig
chk("campo", CA.get_chat_response("hola", [], None, None, rol="field", grupo="cliente1") == "ok")
_s = _vistos[-1]["system"] if _vistos else ""
chk("⚠️ al campo le llega la guía y su persona", "- **Field:** %s." % _cam in _s and "TÉCNICO DE CAMPO" in _s)
chk("...con la regla", "LO QUE NO SABES, NO LO INVENTES" in _s)
chk("...y sin el estado del grupo ni la persona de la oficina",
    "VIVO DEL GRUPO" not in _s and "TU INTERLOCUTOR: ADMINISTRADOR" not in _s)
CA.get_chat_response("hola", [], None, None, rol="administrator", grupo="cliente1")
_s = _vistos[-1]["system"]
chk("a la oficina, su persona y su grupo", "TU INTERLOCUTOR: ADMINISTRADOR" in _s and "VIVO DEL GRUPO" in _s
    and "- **Administrator:** %s." % _adm in _s)
# ⚠️ v647 · CADUCADO por decisión del usuario: el resumen del día tiene instrucciones PROPIAS, sin la guía del Survey
# (eran 7.500 de sus 7.800 tokens) y sin menú: sus botones llevan a IDs que comprueba verif_v647.
from core import resumen_dia as _RD                                # noqa: E402
chk("el resumen del día, con instrucciones propias y sin la guía", "GEOMETRÍA DEL HUECO" not in _RD._INSTRUCCIONES
    and "FUNCIONES DE LA APP COPEX" not in _RD._INSTRUCCIONES)
_app = leer("app.py")
chk("la app le pasa el rol", "rol          = _ROL," in _app and 'if _ROL == "field"' in _app)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
sys.exit(1 if fallos else 0)
