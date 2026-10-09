# -*- coding: utf-8 -*-
"""v551 · EL PANEL DE PLANIFICACIÓN, PROBADO ACCIÓN POR ACCIÓN.

Recorrido en producción (09/10/2026, cuenta admin). Lo arreglado, con la decisión del usuario
(«Dale 2-9 / 1 confirmacion»):
  1. «Copy previous week» pisaba semanas enteras SIN preguntar → confirmación que dice a
     quién le reemplaza lo que ya tiene (también si solo tenía notas).
  2. El selector segmentado (Week/Day/Free…) salía con bolitas: el DOM del radio de 1.64
     (react-aria) dejó muertas las reglas `> label` de v292 → CSS sobre `data-testid` y
     `data-selected`.
  3. Las 4 tarjetas KPI eran HTML pasivo → botones que llevan a su sitio (Compliance, la
     vista «Free» en HOY, el Radar).
  4. Las líneas del Radar eran texto → botones que abren la ficha rápida de esa persona; y
     « y » / «se solapan» salían en español.
  5. «Free» y el día de «Assign» abrían en el lunes (un día pasado) → hoy, como «Day».
  6. Compliance decía «not clocked in yet» de un día PASADO.
  7. El editor de la celda se quedaba ABIERTO tras «Save» y «View the day» → generación en
     la clave (la del popover Y la de su CSS de color, que tienen que casar).
  8. El editor ofrecía «Select all» (1.64): asignaba TODAS las obras y estados a la vez.
  9. «←» desde Users no volvía al Panel: el historial apilaba solo SECCIONES.
  + textos en español (Activar/Desactivar/inactivo, libre, Exige, Asignar) y el botón de
    asignar con el NOMBRE de la obra.

⚠️ La parte de AppTest va AL FINAL: corre en el mismo proceso y sus sustituciones se
filtran a los módulos (reference_apptest_ui). Datos INVENTADOS, ninguna hoja se toca:
`guardar_persona` y `_ws_roster` están sustituidos.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


RU_SRC = io.open(os.path.join("core", "roster_ui.py"), encoding="utf-8").read()
HU_SRC = io.open(os.path.join("core", "home_ui.py"), encoding="utf-8").read()


def _func_src(src, nombre):
    arb = ast.parse(src)
    for n in ast.walk(arb):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(src, n) or ""
    return ""


# ═════════════════════════════════════════════════════════════════════════════
print("1. El selector segmentado, para el DOM de 1.64")
from core import theme                                              # noqa: E402

_css = theme._CSS
chk("la bolita se oculta por `data-testid` (no por `> label`)",
    '[class*="st-key-cpxseg_"] [data-testid="stRadioOption"] > div > div:first-child'
    ':not([data-testid]) {\n  display: none !important;' in _css)
chk("la elegida se resalta con `data-selected` (1.64 la marca de serie)",
    '[class*="st-key-cpxseg_"] [data-testid="stRadioOption"][data-selected="true"] {\n'
    '  background: #e8eef6 !important;' in _css)
chk("…y su texto en azul y negrita",
    '[data-testid="stRadioOption"][data-selected="true"] p {' in _css)
chk("no queda ninguna regla `cpxseg … > label` (el DOM de 1.64 ya no la casa)",
    "radiogroup\"] > label" not in _css and "radiogroup'] > label" not in _css)

# ═════════════════════════════════════════════════════════════════════════════
print("\n2. Textos de la pantalla inglesa")
_cat = _func_src(RU_SRC, "_catalogo")
chk("se encontró `_catalogo` (no es un paso en vacío)", "trab_act_" in _cat)
chk("«Activate» / «Deactivate» con t()", 't("Activate")' in _cat and 't("Deactivate")' in _cat)
chk("«inactive» con t()", "t('inactive')" in _cat or 't("inactive")' in _cat)
chk("ni «Activar», ni «Desactivar», ni «_inactivo_» en el catálogo",
    not any(x in _cat for x in ('"Activar"', '"Desactivar"', "_inactivo_")))
_asig = _func_src(RU_SRC, "_asignacion_inteligente")
chk("se encontró `_asignacion_inteligente`", bool(_asig))
# ⚠️ «Exige» sigue en el COMENTARIO que explica el cambio: se busca como literal (trampa 2)
chk("«Requires:» con t() (era «Exige:»)", 't(":material/badge: Requires: ")' in _asig
    and '"Exige' not in _asig and "'Exige" not in _asig)
chk("el botón de asignar lleva el NOMBRE de la obra", "Assign {n} to «{p}»" in _asig
    and "_nom_prj" in _asig)
chk("el día de «Assign» abre en HOY", "index=_idx_hoy(lunes, dias)" in _asig)
chk("la herramienta «Assign» con t() (era «Asignar» suelto)",
    't(":material/bolt: Assign")' in RU_SRC and '"⚡ Asignar"' not in RU_SRC)
chk("la vista Día dice «free» con t() (era «libre»)", 't("free")' in RU_SRC)

print("\n2b. «Hoy» por defecto en Day, Free y Assign (`_idx_hoy`, ejecutado)")
import datetime as _dt                                              # noqa: E402
from core import roster_ui as RU, roster as R0                      # noqa: E402

chk("las tres pantallas abren con `_idx_hoy` (Day, Free, Assign)",
    RU_SRC.count("index=_idx_hoy(lunes, dias)") >= 3, RU_SRC.count("index=_idx_hoy(lunes, dias)"))
_L = _dt.date(2026, 10, 5)
_today_orig = RU.clock.today
try:
    for _d, _dias, _esp, _q in (
            (_dt.date(2026, 10, 7), R0.DIAS, 2, "miércoles → 2"),
            (_dt.date(2026, 10, 9), R0.DIAS, 4, "viernes → 4 (lo visto en producción)"),
            (_dt.date(2026, 10, 10), R0.DIAS, 0, "sábado sin sábado en pantalla → 0"),
            (_dt.date(2026, 10, 10), R0.DIAS + ["sab"], 5, "sábado CON sábado → 5"),
            (_dt.date(2026, 10, 20), R0.DIAS, 0, "hoy fuera de la semana vista → 0")):
        RU.clock.today = (lambda *a, _x=_d, **k: _x)
        _v = RU._idx_hoy(_L, list(_dias))
        chk(_q, _v == _esp, _v)
finally:
    RU.clock.today = _today_orig

# ═════════════════════════════════════════════════════════════════════════════
print("\n3. «←» recuerda la sub-pestaña (ejecutado, con un `st` de mentira)")
from core import home_ui as HU                                      # noqa: E402


class _Rerun(Exception):
    pass


class _StFalso:
    def __init__(self):
        self.session_state = {"auth": {"rol": "administrator"}}

    def rerun(self):
        raise _Rerun()


_st_orig = HU.st
try:
    F = _StFalso()
    HU.st = F
    SS = F.session_state
    _SK = HU._subkey()["planificacion"]

    def _pasa(sec, sub=None):
        """Una pasada de la shell en (sec, sub): lo que hace `sidebar_menu` con el historial."""
        if sub is not None:
            SS[_SK] = sub
        HU._track_history(sec)

    def _atras():
        """Pulsar «←»: devuelve (sección, sub) a la que manda `navegar`."""
        try:
            HU.ir_atras()
        except _Rerun:
            pass
        p = SS.pop("_admin_nav_pending", None)
        HU.st.session_state[_SK] = p[1] if p and p[1] else SS.get(_SK)
        return p

    _pasa("home")
    _pasa("planificacion")                    # primera visita: SIN estado de sub-pestaña
    _pasa("planificacion")                    # la pasada siguiente (aún sin estado)
    chk("la primera visita (sin estado) no apila un falso cambio",
        SS.get("_nav_hist") == [("home", None)], SS.get("_nav_hist"))
    _pasa("planificacion", "🎛 Panel")         # el estado aparece con el valor por defecto
    chk("…ni cuando el estado aparece con la sub-pestaña por defecto",
        SS.get("_nav_hist") == [("home", None)], SS.get("_nav_hist"))
    _pasa("planificacion", "👷 Usuarios")      # Panel → Users (misma sección)
    chk("⚠️ Panel → Users SÍ se apila (antes no: misma sección)",
        SS.get("_nav_hist") == [("home", None), ("planificacion", "🎛 Panel")],
        SS.get("_nav_hist"))
    _p = _atras()
    chk("⚠️ «←» desde Users manda al PANEL", _p == ("planificacion", "🎛 Panel"), _p)
    _pasa("planificacion")                    # la pasada del «atrás» (no se re-apila)
    chk("…y el atrás no se re-apila", SS.get("_nav_hist") == [("home", None)],
        SS.get("_nav_hist"))
    _p = _atras()
    chk("otro «←» vuelve al Home", _p == ("home", None), _p)

    # Sesión abierta ANTES de v551: `_nav_cur` y el historial son solo la sección
    SS.clear()
    SS.update({"auth": {"rol": "administrator"}, "_nav_cur": "planificacion",
               "_nav_hist": ["home"], _SK: "🎛 Panel"})
    _pasa("planificacion")
    chk("una sesión vieja no apila un falso cambio al desplegar",
        SS.get("_nav_hist") == ["home"], SS.get("_nav_hist"))
    _p = _atras()
    chk("…y su entrada vieja (solo la sección) sigue sirviendo", _p == ("home", None), _p)
finally:
    HU.st = _st_orig

# ═════════════════════════════════════════════════════════════════════════════
print("\n4. El Panel con clics reales (AppTest, datos inventados, sin hoja)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import json, datetime
import streamlit as st
from core import roster as R, roster_ui as RU, auth, projects as P, credentials as C
from core import timeclock as TC, clock as CK

LUNES = R.lunes_de()
ANT = LUNES - datetime.timedelta(days=7)
def _c(*asigs, nota=""):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": nota}
ESTA = {"ana": {"mar": _c("PRJ-1", "PRJ-2"), "mie": _c("PRJ-1")},
        "beto": {"jue": _c("PRJ-9")},
        "dani": {"vie": {"items": [], "nota": "solo una nota"}}}
PREV = {"ana": {"lun": _c("PRJ-1")}, "beto": {"lun": _c("PRJ-2")},
        "carl": {"lun": _c("PRJ-2")}, "dani": {"lun": _c("PRJ-1")}}
FILAS = ([{"Group": "G", "Week": LUNES.isoformat(), "User": u, "DataJSON": json.dumps(d)}
          for u, d in ESTA.items()] +
         [{"Group": "G", "Week": ANT.isoformat(), "User": u, "DataJSON": json.dumps(d)}
          for u, d in PREV.items()])
R._roster_records = lambda: FILAS
R._trab_records = lambda: [{"ID": "TRB-1", "Group": "G", "Number": "1", "Name": "Delivery",
                            "Active": "NO", "Color": "#2e6da4", "ProjectID": ""}]
R.is_configured = lambda: True
R._ws_roster = lambda: None
def _gp(grupo, lunes, usuario, dias):
    st.session_state.setdefault("_ESCRITURAS", []).append((usuario, str(lunes)))
    return True, "ok"
R.guardar_persona = _gp
# ⚠️ Lo que se sustituye por pasada se REPONE si la pasada no lo pide (reference_apptest_ui)
if not hasattr(CK, "_v551_today"):
    CK._v551_today = CK.today
_hoy = st.session_state.get("_HOY")
CK.today = ((lambda *a, **k: LUNES + datetime.timedelta(days=_hoy)) if _hoy is not None
            else CK._v551_today)
TC.is_configured = lambda: bool(st.session_state.get("_TC"))
TC.open_now = lambda g: []
TC.proyectos_por_usuario_dia = lambda g, f: {}
USERS = [{"User": u, "Name": n, "Role": "field", "Group": "G"}
         for u, n in (("ana", "Ana"), ("beto", "Beto"), ("carl", "Carl"), ("dani", "Dani"))]
auth.list_users = lambda *a, **k: USERS
auth.get_user = lambda u: next((x for x in USERS if x["User"] == u), None)
PRJ = [{"ID": "PRJ-1", "Name": "Torre", "Group": "G", "Status": "In progress"},
       {"ID": "PRJ-2", "Name": "Redfen", "Group": "G", "Status": "In progress"},
       {"ID": "PRJ-9", "Name": "Agecare", "Group": "G", "Status": "In progress"}]
P.list_projects = lambda *a, **k: PRJ
P.get_project = lambda pid: dict(next((p for p in PRJ if p["ID"] == pid), {}),
                                 RequiredCerts=("White Card" if pid == "PRJ-9" else ""))
P.add_field_user = lambda *a, **k: None
C.compliance = lambda usr, certs: {"cumple": False, "por_tipo": {"White Card": "vencido"}}
C.list_for = lambda u: []
RU._ficha_rapida = lambda grupo, usuario: st.markdown("FICHA:" + usuario)
RU.render_planificacion("G")
'''


def boton(at, k):
    b = [x for x in at.button if x.key == k]
    return b[0] if b else None


def textos(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.warning]
                      + [m.value for m in at.info] + [m.value for m in at.caption])


def escrituras(at):
    return at.session_state["_ESCRITURAS"] if "_ESCRITURAS" in at.session_state else []


def pops(at):
    return [p.key or p.proto.id for p in at.get("popover")]


def css_cel(at):
    return " ".join(m.value for m in at.markdown if "st-key-roscel_" in m.value)


from core import roster as _R                                       # noqa: E402
_WK = _R.lunes_de().strftime("%Y%m%d")

at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("el Panel se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])

print("   a) el editor de la celda")
_ms = [m for m in at.multiselect if (m.key or "").startswith("pva_")]
chk("hay editores de celda (no es un paso en vacío)", bool(_ms), len(_ms))
chk("⚠️ ninguno ofrece «Select all» (asignaría TODO a la vez)",
    bool(_ms) and all(not m.proto.select_all for m in _ms), [m.proto.select_all for m in _ms[:2]])
_dd = [m for m in at.multiselect if (m.key or "").startswith("pvw_")]
chk("CONTROL: el de «Apply to these days» SÍ lo conserva (la sonda ve el campo)",
    bool(_dd) and all(m.proto.select_all for m in _dd), [m.proto.select_all for m in _dd[:2]])
chk("los popovers de celda llevan la generación 0",
    any(("roscel_%s_0_" % _WK) in k for k in pops(at)), pops(at)[:3])
chk("…y el CSS del color de la celda usa la MISMA clave",
    (".st-key-roscel_%s_0_" % _WK) in css_cel(at))
_vd = [b for b in at.button if (b.key or "").startswith("pvd_")]
chk("hay «View the day» en las celdas con trabajo", bool(_vd))
if _vd:
    _vd[0].click()
    at.run()
chk("⚠️ «View the day» sube la generación (el popover nace CERRADO)",
    any(("roscel_%s_1_" % _WK) in k for k in pops(at))
    and not any(("roscel_%s_0_" % _WK) in k for k in pops(at)), pops(at)[:3])
chk("…y el CSS del color sigue a la clave nueva (la celda no pierde su color)",
    (".st-key-roscel_%s_1_" % _WK) in css_cel(at) and (".st-key-roscel_%s_0_" % _WK) not in css_cel(at))
_sv = [b for b in at.button if (b.key or "").startswith("pvs_")]
if _sv:
    _sv[0].click()
    at.run()
chk("⚠️ «Save» sube la generación otra vez", any(("roscel_%s_2_" % _WK) in k for k in pops(at)),
    pops(at)[:3])
chk("…y «Save» escribió (1 persona)", len(escrituras(at)) == 1, escrituras(at))
at.session_state["_ESCRITURAS"] = []

print("   b) las tarjetas KPI y el Radar")
for k in ("cpxkpi_pnl_fich", "cpxkpi_pnl_libres", "cpxkpi_pnl_choques", "cpxkpi_pnl_certs"):
    chk("la tarjeta %s es un botón" % k[7:], boton(at, k) is not None)
boton(at, "cpxkpi_pnl_choques").click()
at.run()
chk("«Shift clashes» abre el Radar", at.session_state["_panel_tool"] == "radar")
_rad = [b for b in at.button if (b.key or "").startswith("radar_")]
chk("las líneas del Radar son BOTONES (1 choque + 1 cert)", len(_rad) == 2, [b.label for b in _rad])
chk("…en inglés («and» / «overlap»)",
    any(" and " in b.label and b.label.endswith("overlap") for b in _rad), [b.label for b in _rad])
boton(at, "radar_ch_0").click()
at.run()
chk("⚠️ tocar el choque abre la ficha de ANA", "FICHA:ana" in textos(at))
boton(at, "radar_ce_0").click()
at.run()
chk("tocar el cert abre la ficha de BETO", "FICHA:beto" in textos(at))
boton(at, "cpxkpi_pnl_certs").click()
at.run()
chk("«Blocking certs» abre el Radar", at.session_state["_panel_tool"] == "radar")
boton(at, "cpxkpi_pnl_fich").click()
at.run()
chk("«Clocked in now» abre Compliance", at.session_state["_panel_tool"] == "cumpl")

print("   c) Compliance: un día PASADO no es «yet»")
at.session_state["_TC"] = True
at.session_state["_HOY"] = 2                  # «hoy» = miércoles de la semana vista
at.run()
_r = [r for r in at.radio if r.key == "cpxseg_cumpl_dia"]
chk("Compliance abre en HOY (miércoles)", bool(_r) and _r[0].value == "mie",
    _r[0].value if _r else "sin radio")
chk("hoy: Ana asignada a Torre «not clocked in yet»", "not clocked in yet" in textos(at),
    textos(at)[-300:])
if _r:
    _r[0].set_value("mar")
    at.run()
_t = textos(at)
chk("⚠️ ayer (martes): «no time charged to it», sin «yet»",
    "no time charged to it" in _t and "not clocked in yet" not in _t, _t[-300:])
at.session_state["_TC"] = False
at.session_state["_HOY"] = None

print("   d) «Free today» lleva a la vista de libres")
boton(at, "cpxkpi_pnl_libres").click()
at.run()
chk("«Free today» cambia a la vista de disponibilidad",
    at.session_state["cpxseg_vista"] == "👀 Disponibilidad", at.session_state["cpxseg_vista"])
chk("…sin excepción (la clave se escribe ANTES de crear el selector, regla v111)",
    not at.exception, [e.value for e in at.exception][:1])

print("   e) «Copy previous week» pide confirmación")
boton(at, "ros_copy").click()
at.run()
chk("⚠️ pulsar «Copy» NO escribe nada", not escrituras(at), escrituras(at))
_t = textos(at)
chk("la confirmación dice cuántos reciben la semana anterior (4)", "4 person(s)" in _t, _t[:300])
_w = " ".join(w.value for w in at.warning)
chk("⚠️ avisa que REEMPLAZA a Ana, Beto y Dani (Dani solo tenía una nota)",
    all(n in _w for n in ("Ana", "Beto", "Dani")), _w)
chk("…y no nombra a Carl (no tenía nada esta semana)", "Carl" not in _w, _w)
boton(at, "ros_copy_no").click()
at.run()
chk("«Cancel» cierra la confirmación sin escribir",
    boton(at, "ros_copy_si") is None and not escrituras(at), escrituras(at))
boton(at, "ros_copy").click()
at.run()
boton(at, "ros_copy_si").click()
at.run()
chk("«Yes, copy it» copia las 4 personas", len(escrituras(at)) == 4, escrituras(at))
chk("…y la confirmación desaparece", boton(at, "ros_copy_si") is None)

print("   f) el catálogo en inglés")
at.session_state["_panel_tool"] = "cat"
at.run()
_b = boton(at, "trab_act_TRB-1")
chk("el trabajo inactivo ofrece «Activate»", _b is not None and _b.label == "Activate",
    _b.label if _b else "sin botón")
chk("…y se marca «inactive»", "_inactive_" in textos(at))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
