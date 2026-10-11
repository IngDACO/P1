# -*- coding: utf-8 -*-
"""v560 · LOS PENDIENTES DEL RECORRIDO, TODOS («Todo ya»).

  1. Cronograma: «TODAY» ya no pisa el subtítulo (título y subtítulo más arriba).
  2. Formularios que BORRABAN lo escrito al dar un error: recibo, actividad, empresa y riel
     (+ barrido: ningún `clear_on_submit=True` en la app).
  3. Gasto acumulado: el eje X por TIEMPO (no por posición) y etiquetas que no se montan.
  4. Cartera: el filtro de ritmo en su propia fila (a 846 px «On hold» caía a otra línea).
  5. Recuadros a la medida: se vuelven a medir solos si se pierde el primer aviso.
  6. La campana: 64 px fijos (escritorio y móvil); a 846 px con menú no cabía el «4».
  7. Home: «Refresh» GENERA otra lectura de la IA (antes solo borraba).
  8. La URL lleva `&p=` también cuando la obra se pide con `_prjsel_pending`.
  9. ⚠️ Avisos que se perdían si un componente relanzaba la página (Pre-Start: «Clock OUT»).
 10. Contacts: «Ficha» → «Record».
 11. Panel del propietario: empresa y riel conservan lo escrito.
  + Fichaje: «Clock IN … at 16:36» (salía «2026-10-11 16:36:14»).

AppTest y funciones con sus dependencias sustituidas: ninguna hoja se toca.
"""
import ast
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def kw(call, nombre):
    for k in call.keywords:
        if k.arg == nombre:
            return k.value
    return None


import datetime as dt                                                       # noqa: E402
from core import schedule as S, expenses as E, incrustar, tabla, timeclock  # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
print("1. Cronograma: «TODAY» no pisa el subtítulo")
_acts = [{"nombre": "A%d" % i, "duracion": 3, "peso": 1} for i in range(4)]
_sch = S.build_schedule(2, dt.date(2026, 10, 1), {}, custom_rows=None)
_svg = S.schedule_svg(_sch, today_day=2, titulo="Obra con un nombre bastante largo", vw=700)
_y = {m.group(2): float(m.group(1)) for m in
      re.finditer(r'<text x="[\d.]+" y="([\d.]+)"[^>]*>([^<]{4,30})</text>', _svg)}
_ysub = [float(m.group(1)) for m in re.finditer(r'<text x="18" y="([\d.]+)" font-size="8.5"', _svg)]
_yhoy = [float(m.group(1)) for m in re.finditer(
    r'<text x="[\d.]+" y="([\d.]+)" text-anchor="middle" font-size="8.5" fill="#c0392b" '
    r'font-weight="bold">TODAY<', _svg)]
chk("se leen el subtítulo y «TODAY»", bool(_ysub) and bool(_yhoy), (_ysub, _yhoy))
# 8,5 px de letra: el subtítulo baja ~2 px de su base; «TODAY» sube ~6,5 px de la suya.
chk("⚠️ la franja del subtítulo acaba antes de que empiece la de «TODAY»",
    _ysub and _yhoy and _ysub[0] + 2.0 < _yhoy[0] - 6.5, (_ysub, _yhoy))

# ══════════════════════════════════════════════════════════════════════════════
print("\n2. Formularios que conservan lo escrito")
_malos = []
for d, _, fs in os.walk(os.path.join(RAIZ, "core")):
    for f in fs:
        if f.endswith(".py"):
            for n in ast.walk(ast.parse(io.open(os.path.join(d, f), encoding="utf-8").read())):
                if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "form":
                    v = kw(n, "clear_on_submit")
                    if isinstance(v, ast.Constant) and v.value is True:
                        _malos.append("%s:%d" % (f, n.lineno))
chk("⚠️ ningún formulario con `clear_on_submit=True` (borraba lo escrito al dar error)",
    not _malos, _malos)

from streamlit.testing.v1 import AppTest                                    # noqa: E402

G_GRUPO = r'''
import streamlit as st
from core import auth, auth_ui, flash
st.session_state.setdefault("_R", (False, "Ya existe"))
auth.list_groups = lambda *a, **k: []
auth.add_group = lambda n, d: st.session_state["_R"]
auth_ui._owner_grupos()
'''
at = AppTest.from_string(G_GRUPO, default_timeout=60)
at.run()
chk("empresa: se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.text_input(key="fg_n_0").set_value("Empresa X")
[b for b in at.button if "Create company" in str(b.label)][0].click()
at.run()
chk("⚠️ empresa: con error, el nombre SIGUE escrito",
    at.text_input(key="fg_n_0").value == "Empresa X" and any("Ya existe" in e.value for e in at.error))
at.session_state["_R"] = (True, "Creada")
[b for b in at.button if "Create company" in str(b.label)][0].click()
at.run()
chk("empresa: al crear, el formulario nace vacío (otra generación)",
    "_form_grupo_gen" in at.session_state and at.session_state["_form_grupo_gen"] == 1
    and at.text_input(key="fg_n_1").value == "")

G_RIEL = r'''
import streamlit as st
from core import auth_ui, rails
rails.list_rieles = lambda: [{"Reference": "T1"}]
rails.get_rail = lambda r: {}
rails.add_riel = lambda *a: (True, "Añadido")
auth_ui._owner_rieles()
'''
at = AppTest.from_string(G_RIEL, default_timeout=60)
at.run()
chk("riel: se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.number_input(key="fr_alt_0").set_value(12.5)
[b for b in at.button if str(b.label) == "Add"][0].click()
at.run()
chk("⚠️ riel: sin referencia, la altura tecleada SIGUE", at.number_input(key="fr_alt_0").value == 12.5
    and any("reference is required" in e.value for e in at.error))
at.text_input(key="fr_ref_0").set_value("T89/B")
[b for b in at.button if str(b.label) == "Add"][0].click()
at.run()
chk("riel: al añadir, el formulario nace vacío (otra generación)",
    "_form_riel_gen" in at.session_state and at.session_state["_form_riel_gen"] == 1
    and at.number_input(key="fr_alt_1").value == 0.0)

# El recibo de la ficha: proveedor, descripción y FOTO se perdían si faltaba el importe.
G_REC = r'''
import streamlit as st
from core import projects_ui as PU, expenses as E
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state.setdefault("_R", (False, "No"))
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"items": []}
E.upload_receipt = lambda *a: ""
def _add(*a):
    st.session_state["_ADD"] = a
    return st.session_state["_R"]
E.add = _add
PU.render_expenses("PRJ-9", "G")
'''
at = AppTest.from_string(G_REC, default_timeout=60)
at.run()
chk("recibo: se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
at.text_input(key="ex_prov").set_value("Ferretería Uno")
at.text_input(key="ex_desc").set_value("tornillos")
[b for b in at.button if "Save receipt" in str(b.label)][0].click()
at.run()
chk("⚠️ recibo: sin importe, proveedor y descripción SIGUEN escritos",
    at.text_input(key="ex_prov").value == "Ferretería Uno" and at.text_input(key="ex_desc").value == "tornillos"
    and any("value of the receipt" in e.value for e in at.error))
chk("…y no se guardó nada", "_ADD" not in at.session_state)
at.number_input(key="ex_val").set_value(5.0)
at.session_state["_R"] = (True, "Guardado")
[b for b in at.button if "Save receipt" in str(b.label)][0].click()
at.run()
chk("recibo: se guarda con lo que estaba escrito",
    "_ADD" in at.session_state and at.session_state["_ADD"][4] == "Ferretería Uno"
    and at.session_state["_ADD"][2] == 5.0, at.session_state["_ADD"] if "_ADD" in at.session_state else "")
chk("recibo: al guardar, el formulario nace vacío (otra generación)",
    at.session_state["_rec_gen_ex_PRJ-9"] == 1 and at.text_input(key="ex_prov_1").value == "")

# «Add activity» vive dentro de la ficha entera (muchas hojas): estático, sobre el AST.
_fa = [n for n in ast.walk(ast.parse(fuente(os.path.join("core", "projects_ui.py"))))
       if isinstance(n, ast.With) and any("addact_" in ast.unparse(i.context_expr) for i in n.items)]
chk("se localiza el formulario «Add activity»", len(_fa) == 1, len(_fa))
if _fa:
    _wf = ast.unparse(_fa[0])
    chk("«Add activity»: la clave del formulario lleva su generación",
        "_ag" in ast.unparse(_fa[0].items[0].context_expr), ast.unparse(_fa[0].items[0].context_expr))
    chk("⚠️ «Add activity»: la generación sube SOLO tras añadir (dentro de `if ok:`)",
        any(isinstance(n, ast.If) and ast.unparse(n.test) == "ok"
            and "_addact_gen_" in ast.unparse(n) and "_ag + 1" in ast.unparse(n)
            for n in ast.walk(_fa[0])))

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. Gasto acumulado: el eje por tiempo")
_cur = {"fechas": ["2026-09-30", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"],
        "mano_obra": [0, 0.5, 1.0, 1.5, 1.8], "total": [0, 0.5, 1.0, 1.5, 1.8], "presupuesto": 0}
_sv = E.spend_svg(_cur, None, "Obra")
_pl = re.search(r'<polyline points="([^"]+)" fill="none" stroke="#1a3a5c"', _sv)
_xs = [float(p.split(",")[0]) for p in _pl.group(1).split()] if _pl else []
chk("se leen los 5 puntos de la curva", len(_xs) == 5, _xs)
if len(_xs) == 5:
    _g1, _g2 = _xs[1] - _xs[0], _xs[2] - _xs[1]
    chk("⚠️ 30/09→06/10 (6 días) mide 6 veces 06/10→07/10 (1 día)", abs(_g1 / _g2 - 6) < 0.01,
        (_g1, _g2))
_lx = [float(m.group(1)) for m in re.finditer(
    r'<text x="([\d.]+)" y="[\d.]+" text-anchor="middle" font-size="7.5"', _sv)]
_lt = re.findall(r'font-size="7.5" fill="#5b6472">(\d\d/\d\d)</text>', _sv)
chk("las etiquetas de fecha no se montan (≥ 36 unidades)",
    all(b - a >= 36 for a, b in zip(_lx, _lx[1:])), _lx)
chk("…y la última es la del último día (09/10)", _lt and _lt[-1] == "09/10", _lt)
# Con muchos días seguidos los puntos se juntan: de 5 a 60 días, nunca dos etiquetas encima
# y siempre la del último día (hay largos en que el último cae a menos de 36 del anterior).
_mal = []
for _nd in range(5, 61):
    _f = [(dt.date(2026, 8, 1) + dt.timedelta(days=k)).isoformat() for k in range(_nd)]
    _v = [k * 1.0 for k in range(_nd)]
    _s = E.spend_svg({"fechas": _f, "mano_obra": _v, "total": _v, "presupuesto": 0}, None, "")
    _x = [float(m.group(1)) for m in re.finditer(
        r'<text x="([\d.]+)" y="[\d.]+" text-anchor="middle" font-size="7.5"', _s)]
    _e = re.findall(r'font-size="7.5" fill="#5b6472">(\d\d/\d\d)</text>', _s)
    if not _x or any(b - a < 36 for a, b in zip(_x, _x[1:])) or _e[-1] != _f[-1][8:10] + "/" + _f[-1][5:7]:
        _mal.append(_nd)
chk("⚠️ de 5 a 60 días seguidos: etiquetas sin montarse y con el último día", not _mal, _mal)

# ══════════════════════════════════════════════════════════════════════════════
print("\n4. Cartera: el filtro de ritmo en su fila")
PUS = fuente(os.path.join("core", "projects_ui.py"))
_rad = [n for n in ast.walk(ast.parse(PUS)) if isinstance(n, ast.Call)
        and isinstance(kw(n, "key"), ast.Constant) and kw(n, "key").value == "cpxseg_cart_filt"]
chk("se localiza el filtro", len(_rad) == 1)
chk("⚠️ el filtro es `st.radio` a todo el ancho, no dentro de una columna",
    _rad and ast.unparse(_rad[0].func) == "st.radio", ast.unparse(_rad[0].func) if _rad else "")

# ══════════════════════════════════════════════════════════════════════════════
print("\n5. Recuadros que se vuelven a medir")
import streamlit as st                                                      # noqa: E402
_cap = []
_oi = st.iframe
st.iframe = lambda h, height=None, **k: _cap.append((h, height))
try:
    incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0"><svg></svg></body></html>', 330)
    incrustar.dibujo("<svg></svg>", 52, ajustar=False)
finally:
    st.iframe = _oi
_h0 = _cap[0][0]
chk("⚠️ un dibujo a la medida lleva el re-medido, DENTRO del <body>",
    "appendChild(d)" in _h0 and _h0.find("appendChild(d)") < _h0.lower().rfind("</body>"))
chk("…y uno de alto fijo no lo lleva (no lo necesita)", "appendChild(d)" not in _cap[1][0])

# ══════════════════════════════════════════════════════════════════════════════
print("\n6. La campana")
HUS = fuente(os.path.join("core", "home_ui.py"))
_c4 = "[data-testid='stColumn']:nth-child(4){flex:0 0 64px !important;"
chk("⚠️ 64 px para la campana en escritorio Y en móvil (2 reglas)", HUS.count(_c4) == 2, HUS.count(_c4))
# El CSS es UNA cadena (concatenación implícita): se lee el bloque de escritorio entero.
_css = [n.value for n in ast.walk(ast.parse(HUS)) if isinstance(n, ast.Constant)
        and isinstance(n.value, str) and "@media (min-width:641px){" in n.value]
chk("se localiza el CSS de la barra superior", len(_css) == 1, len(_css))
_esc_b = _css[0].split("@media (min-width:641px){", 1)[1].split("}@media", 1)[0] if _css else ""
chk("⚠️ escritorio: la fila NO salta de línea (la campana caía a otra fila)",
    "stHorizontalBlock']{flex-wrap:nowrap" in _esc_b, _esc_b[:120])
chk("escritorio: las columnas pueden encoger (min-width:0) y «←» guarda 44 px",
    "[data-testid='stColumn']{min-width:0" in _esc_b and "nth-child(1){flex:0 0 44px" in _esc_b)
chk("escritorio: la campana, 64 px", "nth-child(4){flex:0 0 64px" in _esc_b)

# ══════════════════════════════════════════════════════════════════════════════
print("\n7. Home: «Refresh» genera otra lectura")
G_IA = r'''
import streamlit as st
from core import projects_ui as PU, admin_digest, chat_agent, auth
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state.setdefault("_N", 0)
auth.list_users = lambda *a, **k: []
_d = {"retrasos": [], "vencidos": [], "por_vencer": [], "sin_asignar": [], "alarmas": [],
      "near_miss": [], "campo_sin_contacto": [], "cred_venc": [], "sobre_presupuesto": []}
class _Dig:
    def __call__(self, g):
        return _d
    def clear(self):
        st.session_state["_LIMPIO"] = True
admin_digest.group_digest = _Dig()
def _brief(g):
    st.session_state["_N"] += 1
    return "LECTURA %d" % st.session_state["_N"]
chat_agent.admin_briefing = _brief
st.session_state.setdefault("_brief_G", "LECTURA VIEJA")
PU._resumen_del_dia("G")
'''
at = AppTest.from_string(G_IA, default_timeout=60)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
[b for b in at.button if b.key == "brief_ref_G"][0].click()
at.run()
chk("⚠️ «Refresh» deja una lectura NUEVA (no la borra)",
    at.session_state["_brief_G"] == "LECTURA 1", at.session_state["_brief_G"])
chk("…con los datos de ahora (vacía la caché del resumen)",
    "_LIMPIO" in at.session_state and at.session_state["_LIMPIO"] is True)

# ══════════════════════════════════════════════════════════════════════════════
print("\n8. La URL con `&p=` cuando la obra se pide")
G_URL = r'''
import streamlit as st
from core import home_ui
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state["_prjsel_pending"] = "PRJ-0009"
home_ui._estado_a_url("proyectos")
'''
at = AppTest.from_string(G_URL, default_timeout=60)
at.run()
chk("⚠️ «See the full project» / Day route: la URL lleva p=PRJ-0009",
    at.query_params.get("p") in ("PRJ-0009", ["PRJ-0009"]), dict(at.query_params))

# ══════════════════════════════════════════════════════════════════════════════
print("\n9. ⚠️ Los avisos sobreviven a un relanzamiento inmediato")
G_FL = r'''
import streamlit as st
from core import flash
if st.session_state.pop("_poner", False):
    flash.exito("Clock OUT at 16:36.")
st.session_state["_vistos"] = flash.mostrar()
'''
at = AppTest.from_string(G_FL, default_timeout=60)
at.session_state["_poner"] = True
at.run()
chk("la pasada del aviso lo pinta", any("Clock OUT" in s.value for s in at.success))
at.run()        # el relanzamiento de un componente, enseguida
chk("⚠️ el relanzamiento INMEDIATO lo sigue pintando (antes desaparecía)",
    any("Clock OUT" in s.value for s in at.success))
from core import flash as _FL                                               # noqa: E402
_t0 = _FL.time.monotonic
_FL.time.monotonic = lambda: _t0() + 10
try:
    at.run()
finally:
    _FL.time.monotonic = _t0
chk("…y pasado el margen se olvida (no se queda pegado)",
    not any("Clock OUT" in s.value for s in at.success))

# ══════════════════════════════════════════════════════════════════════════════
print("\n10-12. Contacts, fichaje")
chk("Contacts: «Ficha» → «Record»", tabla.CABECERAS.get("Ficha") == "Record")
_n0 = timeclock._now
timeclock._now = lambda: "2026-10-11 16:40:00"
try:
    chk("⚠️ fichaje de hoy: «16:36» (no «2026-10-11 16:36:14»)",
        timeclock._ts_legible("2026-10-11 16:36:14") == "16:36")
    chk("fichaje de otro día: «10/10/2026 16:36»",
        timeclock._ts_legible("2026-10-10 16:36:14") == "10/10/2026 16:36")
    chk("lo que no se puede leer, tal cual", timeclock._ts_legible("x") == "x")
finally:
    timeclock._now = _n0
_tcs = fuente(os.path.join("core", "timeclock.py"))
chk("los avisos de entrada y salida usan la hora legible",
    "Clock IN {etq} {t('at')} {_ts_legible(in_ts)}" in _tcs
    and "Clock OUT {t('at')} {_ts_legible(out_ts)}" in _tcs)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
