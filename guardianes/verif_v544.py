# -*- coding: utf-8 -*-
"""v544 · LA PANTALLA HOME DEL ADMIN, PROBADA ACCIÓN POR ACCIÓN EN PRODUCCIÓN.

Lo que salió al recorrerla con la cuenta admin (08/10/2026), y lo que aquí se protege
EJECUTANDO las pantallas reales con AppTest:

1. Las tarjetas KPI no se leían: Streamlit 1.64 pinta la etiqueta de un botón EN COLUMNAS
   en una sola línea (`nowrap` + elipsis, los <p> en línea). Se leía «AC…», «PR…», «HO…».
2. El MISMO pin del mapa no se podía volver a abrir: pin → «Back to the list» → mismo pin =
   nada. `st_folium` devuelve el último clic en cada pasada y el filtro de repetidos lo
   descartaba para siempre.
3. La tarjeta «Hours · 4 h» suma todo el histórico y Horas abría en «Today»: «No time
   entries in the period».
4. La campana decía «No alerts for now» con el resumen marcando 4 urgentes (decisión del
   usuario: que entren). Y cada alerta lleva a donde se resuelve.
5. Textos: «6 paradas», «alarma(s)», «13 pendings», «18.0 d», fechas ISO y logins.
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
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


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from streamlit.testing.v1 import AppTest                          # noqa: E402


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def ss(at, k, defecto=None):
    try:
        return at.session_state[k]
    except KeyError:
        return defecto


ADMIN = '{"rol": "administrator", "usuario": "adm", "nombre": "Adm", "grupo": "g"}'

# ─────────────────────────────────────────────────────────────────────────────
sec("1. Las tarjetas KPI vuelven a tener 3 líneas")
from core import theme                                            # noqa: E402
_css = theme._CSS
_i_kpi = _css.find('[class*="st-key-cpxkpi_"] button p {')
_i_mc = _css.find('[class*="st-key-cpxkpi_"] button [data-testid="stMarkdownContainer"] {')
_i_p = _css.find('[class*="st-key-cpxkpi_"] button [data-testid="stMarkdownContainer"] p {')
chk("se encontraron las reglas de la tarjeta (no es un paso en vacío)",
    min(_i_kpi, _i_mc, _i_p) > 0, (_i_kpi, _i_mc, _i_p))
_r_mc = _css[_i_mc:_css.find("}", _i_mc)]
_r_p = _css[_i_p:_css.find("}", _i_p)]
chk("⚠️ el contenedor del markdown vuelve a partir líneas (white-space:normal)",
    "white-space: normal !important" in _r_mc, _r_mc)
chk("⚠️ cada línea es un BLOQUE (los <p> salían inline, uno detrás de otro)",
    "display: block !important" in _r_p, _r_p)
chk("...acotado a las tarjetas `cpxkpi_` (no a todos los botones de la app)",
    _r_mc.startswith('[class*="st-key-cpxkpi_"]') and _r_p.startswith('[class*="st-key-cpxkpi_"]'))
chk("la elipsis por línea sigue (una línea que no cabe se recorta, no salta)",
    _css.count("text-overflow: ellipsis") >= 2)

# ─────────────────────────────────────────────────────────────────────────────
sec("2. El mapa del Home: el MISMO pin se puede volver a abrir")
GUION_MAPA = r'''
import sys, types
sys.path.insert(0, r"%s")
import streamlit as st
# `st_folium` de mentira con la conducta del de verdad: devuelve el ÚLTIMO clic de ESA
# clave en cada pasada; con otra clave, nace sin clic.
_m = types.ModuleType("streamlit_folium")
def st_folium(m, key=None, **kw):
    clicks = st.session_state.setdefault("_fk_clicks", {})
    nuevo = st.session_state.pop("_fk_nuevo", None)
    if nuevo:
        clicks[key] = nuevo
    return {"last_object_clicked": clicks.get(key)}
_m.st_folium = st_folium
sys.modules["streamlit_folium"] = _m
from core import home_ui as H, projects as P, alerts, auth
st.session_state["auth"] = %s
PRJS = [{"ID": "PRJ-A", "Name": "Obra A", "Status": "Planned", "Lat": -33.84, "Lng": 151.20,
         "Progress": 0},
        {"ID": "PRJ-B", "Name": "Obra B", "Status": "Planned", "Lat": -33.89, "Lng": 151.25,
         "Progress": 0}]
P.list_projects = lambda *a, **k: [dict(p) for p in PRJS]
P.delays_of_group = lambda g: {}
P.aheads_of_group = lambda g: {}
alerts.is_configured = lambda: False
auth.list_users = lambda *a, **k: []
H._mapa_proyectos("g")
H._proyectos_home("g")
''' % (RAIZ, ADMIN)
PIN_A = {"lat": -33.84, "lng": 151.20}
PIN_B = {"lat": -33.89, "lng": 151.25}


def pin(at, p):
    at.session_state["_fk_nuevo"] = dict(p)
    return corre(at)


at = corre(AppTest.from_string(GUION_MAPA, default_timeout=120))
chk("de partida, la lista (sin resumen)", ss(at, "_home_proj_sel") is None)
pin(at, PIN_A)
chk("el pin A abre el resumen de A", ss(at, "_home_proj_sel") == "PRJ-A",
    ss(at, "_home_proj_sel"))
at.button(key="hpr_back").click()
corre(at)
chk("«Back to the list» vuelve a la lista", ss(at, "_home_proj_sel") is None)
pin(at, PIN_A)
chk("⚠️ el MISMO pin otra vez abre A (el fallo visto en producción)",
    ss(at, "_home_proj_sel") == "PRJ-A", ss(at, "_home_proj_sel"))
corre(at)
chk("...y el resumen no se reabre solo en cada pasada (el filtro de repetidos sigue)",
    ss(at, "_home_proj_sel") == "PRJ-A")
at.button(key="hpr_back").click()
corre(at)
pin(at, PIN_B)
chk("otro pin abre su obra (lo que ya funcionaba sigue)", ss(at, "_home_proj_sel") == "PRJ-B")
at.button(key="hpr_full").click()
corre(at)
chk("«See the full project» cierra el resumen y navega a Proyectos",
    ss(at, "_home_proj_sel") is None
    and ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"))
chk("...y el mapa vuelve a nacer sin clic (sube la generación)",
    ss(at, "_home_map_gen", 0) >= 3 and ss(at, "_home_map_click") is None,
    (ss(at, "_home_map_gen"), ss(at, "_home_map_click")))
pin(at, PIN_B)
chk("al volver, el MISMO pin (B) se abre otra vez", ss(at, "_home_proj_sel") == "PRJ-B")

# Volver al Home desde otra pantalla: Streamlit suelta el estado del mapa (nace sin clic)
# pero el recuerdo del último pin seguía ahí.
at = corre(AppTest.from_string(GUION_MAPA, default_timeout=120))
at.session_state["_home_map_click"] = (-33.84, 151.2)
corre(at)
chk("⚠️ un mapa sin clic olvida el último pin (volver al Home desde otra pantalla)",
    ss(at, "_home_map_click") is None, ss(at, "_home_map_click"))
pin(at, PIN_A)
chk("...y ese pin se abre al primer toque", ss(at, "_home_proj_sel") == "PRJ-A")

# ─────────────────────────────────────────────────────────────────────────────
sec("3. «Hours» del Home abre Horas en el periodo que cuenta (todo)")
GUION_HORAS = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import projects_ui as PU, timeclock
st.session_state["auth"] = %s
PU._kpis = lambda g=None: {"total": 3, "activos": 3, "avg": 0, "riesgo": 3, "alarmas": 0,
                           "horas": 4}
PU.P.is_configured = lambda: True
timeclock.is_configured = lambda: True
timeclock.group_hours = lambda g, days=None: {}
if st.session_state.get("_en_horas"):
    PU.render_group_hours("g")
else:
    PU.render_kpis("g")
''' % (RAIZ, ADMIN)
at = corre(AppTest.from_string(GUION_HORAS, default_timeout=120))
at.button(key="cpxkpi_horas").click()
corre(at)
chk("la tarjeta lleva a Finanzas · Horas", ss(at, "_admin_nav_pending") == ("finanzas", "⏱ Horas"))
at.session_state["_en_horas"] = True
corre(at)
chk("⚠️ ...y Horas abre en «All» (el número de la tarjeta es de TODO el histórico)",
    at.radio(key="gh_per").value == "Todo", at.radio(key="gh_per").value)
chk("...la marca se consume (no se queda pegada)", ss(at, "_gh_per_pending") is None)
at = AppTest.from_string(GUION_HORAS, default_timeout=120)
at.session_state["_en_horas"] = True
corre(at)
chk("entrar a Horas por el menú sigue abriendo en «Today»", at.radio(key="gh_per").value == "Hoy",
    at.radio(key="gh_per").value)

# ─────────────────────────────────────────────────────────────────────────────
sec("4. La campana: entran los urgentes del resumen y cada alerta lleva a su sitio")
GUION_CAMPANA = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import home_ui as H, admin_digest as AD, credentials as C, inventory as INV, auth
st.session_state["auth"] = st.session_state.get("_fk_auth") or %s
AD.group_digest = lambda g: {
    "retrasos": [{"id": "PRJ-1", "nombre": "Uno", "dias": 31},
                 {"id": "PRJ-2", "nombre": "Dos", "dias": 18}],
    "vencidos": [{"id": "PRJ-1", "nombre": "Uno", "fin": "2026-10-02", "dias": -6}],
    "alarmas": [{"id": "PRJ-3", "nombre": "Tres", "n": 2}]}
C.is_configured = lambda: True
C.expiring = lambda g: [{"tipo": "White Card", "usuario": "campo1", "dias": -3}]
INV.is_configured = lambda: True
INV.alertas = lambda g: [{"tipo": "mantenimiento", "activo": "Taladro", "dias": 4}]
auth.list_users = lambda *a, **k: [{"User": "campo1", "Name": "Campo Uno"}]
H._campana("g")
st.session_state["_fk_textos"] = H._alertas("g")
''' % (RAIZ, ADMIN)


def campana(auth=None):
    at = AppTest.from_string(GUION_CAMPANA, default_timeout=120)
    if auth:
        at.session_state["_fk_auth"] = auth
    return corre(at)


def bell(at):
    return [b for b in at.button if str(b.key or "").startswith("bell_")]


def toca(at, trozo):
    b = next(b for b in bell(at) if trozo in b.label)
    b.click()
    return corre(at)


at = campana()
_lbl = [b.label for b in bell(at)]
chk("⚠️ al admin le entran los 4 urgentes del resumen (3 motivos + el vencido)",
    sum(1 for x in _lbl if "behind schedule" in x or "overdue since" in x
        or "open alarm" in x) == 4, _lbl)
chk("...con los días ENTEROS y la fecha como en Proyectos (dd/mm/aaaa)",
    any("31 d behind schedule" in x for x in _lbl)
    and any("overdue since 02/10/2026" in x for x in _lbl), _lbl)
chk("...y el plural de las alarmas", any("2 open alarms" in x for x in _lbl), _lbl)
chk("credencial e inventario siguen", any("White Card" in x for x in _lbl)
    and any("Taladro" in x for x in _lbl), _lbl)
chk("⚠️ NADA pasivo: las 6 alertas del admin son botones", len(_lbl) == 6, len(_lbl))
_tx = ss(at, "_fk_textos") or []
chk("`_alertas` sigue dando TEXTOS (lo que leen los guardianes de v297/v298/v443)",
    len(_tx) == 6 and all(isinstance(x, str) for x in _tx), _tx[:2])
toca(at, "overdue since")
chk("tocar una obra la abre en Proyectos",
    ss(at, "_admin_open_proj") == "PRJ-1"
    and ss(at, "_admin_nav_pending") == ("proyectos", "📊 Proyectos"),
    (ss(at, "_admin_open_proj"), ss(at, "_admin_nav_pending")))
at = campana()
toca(at, "White Card")
chk("tocar una credencial abre la ficha de ESA persona (con su nombre)",
    ss(at, "gp_fichasel") == "Campo Uno (campo1)"
    and ss(at, "_admin_nav_pending") == ("planificacion", "👷 Usuarios"),
    (ss(at, "gp_fichasel"), ss(at, "_admin_nav_pending")))
at = campana()
toca(at, "Taladro")
chk("tocar un activo lleva a Inventario", ss(at, "_admin_nav_pending") == ("inventario", None),
    ss(at, "_admin_nav_pending"))

at = campana({"rol": "field", "usuario": "campo1", "nombre": "Campo Uno", "grupo": "g"})
_lbl = [b.label for b in bell(at)]
chk("al CAMPO no le entran los urgentes de gestión (solo lo suyo, v297)",
    len(_lbl) == 1 and "White Card" in _lbl[0], _lbl)
toca(at, "White Card")
chk("...y su credencial le lleva a «My credentials»",
    ss(at, "_admin_nav_pending") == ("autogestion", "🎫 Credenciales"),
    ss(at, "_admin_nav_pending"))

# ─────────────────────────────────────────────────────────────────────────────
sec("5. Textos del Home en inglés y como en el resto de la app")
GUION_RES = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import home_ui as H, projects as P, alerts, auth
st.session_state["auth"] = %s
P.list_projects = lambda *a, **k: [{"ID": "PRJ-A", "Name": "Obra A", "Status": "Planned",
    "Progress": 0, "Client": "Cli", "StartDate": "2026-09-20", "EndDateEst": "2026-10-25",
    "NS": st.session_state.get("_fk_ns", "6"), "FieldAssigned": "u1;u2", "Location": ""}]
P.delays_of_group = lambda g: {"PRJ-A": 18.0}
P.aheads_of_group = lambda g: {}
alerts.is_configured = lambda: True
alerts.open_counts_all = lambda: {"PRJ-A": st.session_state.get("_fk_al", 1)}
auth.list_users = lambda *a, **k: [{"User": "u1", "Name": "Uno Nombre"}, {"User": "u2", "Name": ""}]
if st.session_state.get("_fk_lista"):
    H._proyectos_home("g")
else:
    H._resumen_proyecto_home("g", "PRJ-A")
''' % (RAIZ, ADMIN)


def resumen(**kw):
    at = AppTest.from_string(GUION_RES, default_timeout=120)
    for k, v in kw.items():
        at.session_state[k] = v
    corre(at)
    return at, " | ".join(m.value for m in at.markdown) + " | " + " | ".join(
        c.value for c in at.caption)


at, txt = resumen()
chk("«18 d behind», no «18.0 d»", "18 d behind" in txt and "18.0" not in txt, txt[:300])
chk("⚠️ «1 alarm» en inglés (decía «alarma(s)»)", "1 alarm" in txt and "alarma" not in txt)
chk("⚠️ «6 stops» en inglés (decía «6 paradas»)", "6 stops" in txt and "paradas" not in txt)
chk("fechas dd/mm/aaaa como en Proyectos", "20/09/2026 → 25/10/2026" in txt, txt[:300])
chk("la cuadrilla con su NOMBRE; sin nombre, su login", "Uno Nombre, u2" in txt, txt)
at, txt = resumen(_fk_ns="1", _fk_al=3)
chk("singular y plural bien: «1 stop», «3 alarms»",
    "1 stop" in txt and "1 stops" not in txt and "3 alarms" in txt, txt[:300])
at, txt = resumen(_fk_ns="")
chk("sin paradas en la ficha, no se inventa ninguna", "stop" not in txt)
at, txt = resumen(_fk_lista=True)
_hp = [b.label for b in at.button if str(b.key or "").startswith("hp_")]
chk("la lista de obras: «18d», no «18.0d»", _hp and "18d" in _hp[0] and "18.0" not in _hp[0], _hp)

GUION_DIA = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import projects_ui as PU, admin_digest as AD, auth
st.session_state["auth"] = %s
AD.group_digest = lambda g: {
    "retrasos": [{"id": "1", "nombre": "A", "dias": 31}, {"id": "2", "nombre": "B", "dias": 18},
                 {"id": "3", "nombre": "C", "dias": 10}],
    "vencidos": [{"id": "1", "nombre": "A", "fin": "2026-10-02", "dias": -6}],
    "por_vencer": [], "sin_asignar": [], "cred_venc": [], "alarmas": [],
    "campo_sin_contacto": ["u1", "u2"],
    "near_miss": [{"proyecto": "C", "fecha": "2026-10-05", "desc": ""}],
    "sobre_presupuesto": []}
auth.list_users = lambda *a, **k: [{"User": "u1", "Name": "Uno Nombre"}, {"User": "u2", "Name": ""}]
PU._resumen_del_dia("g")
''' % (RAIZ, ADMIN)
at = corre(AppTest.from_string(GUION_DIA, default_timeout=120))
_tit = at.expander[0].label
chk("⚠️ «7 pending», no «7 pendings»", "7 pending" in _tit and "pendings" not in _tit, _tit)
chk("...y el singular sigue igual («1 pending» no cambia de forma)",
    "pending{_p}" not in _fuente("core/projects_ui.py"))


def detalle(at, slug):
    at.button(key="resind_" + slug).click()
    corre(at)
    return " | ".join(c.value for c in at.caption)


chk("vencidos con fecha dd/mm/aaaa", "A (02/10/2026)" in detalle(at, "vencidos"))
chk("near miss con fecha dd/mm/aaaa", "C (05/10/2026)" in detalle(at, "near"))
chk("⚠️ «No contact details» con NOMBRES (salía «appretince», el login)",
    "Uno Nombre, u2" in detalle(at, "sincont"))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
