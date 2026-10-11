# -*- coding: utf-8 -*-
"""v561 · LO VISTO VERIFICANDO v560 (decisión del usuario: «Dale»).

  1. Cronograma: «TODAY» ya no pisaba el subtítulo, pero quedaba PEGADO debajo (a 472 px,
     menos de 1 px entre «14 activities» y «TODAY», medido en producción) → aire de verdad.
  2. Home a ≤1280 px CON el menú: las 3 columnas no cabían (a 840, tarjetas KPI de 37 px;
     a 1280, el pie recortado). Por debajo de 1140 px de fila, KPI + mapa a todo el ancho
     y Projects | agenda debajo; los indicadores del resumen, 3 por fila bajo 560 px
     («Credenti als» se partía a mitad de palabra).
  3. La lectura de la IA (y el texto de respaldo sin IA): fechas ISO, «VENCIDA» / «en N d» /
     «s/d» y logins → DD/MM/YYYY, inglés y nombres. El Home: «tipo·login (-3d)» → nombre y
     «expired 3 d ago».

El 4º punto (el clic que se pierde) se reprodujo en una mini-app y su cura va APARTE.
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


import datetime as dt                                                       # noqa: E402
from core import schedule as S                                              # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
print("1. Cronograma: aire entre el subtítulo y «TODAY»")
_sch = S.build_schedule(2, dt.date(2026, 10, 1), {}, custom_rows=None)
for _vw in (700, 1000, 1280):
    _svg = S.schedule_svg(_sch, today_day=2, titulo="Obra con un nombre bastante largo", vw=_vw)
    _yt = [float(m.group(1)) for m in re.finditer(r'<text x="18" y="([\d.]+)" font-size="13"', _svg)]
    _ys = [float(m.group(1)) for m in re.finditer(r'<text x="18" y="([\d.]+)" font-size="8.5"', _svg)]
    _yh = [float(m.group(1)) for m in re.finditer(
        r'<text x="[\d.]+" y="([\d.]+)" text-anchor="middle" font-size="8.5" fill="#c0392b" '
        r'font-weight="bold">TODAY<', _svg)]
    chk("lienzo %d: se leen título, subtítulo y «TODAY»" % _vw, bool(_yt and _ys and _yh),
        (_yt, _ys, _yh))
    if _yt and _ys and _yh:
        # tinta a 8,5 px: el subtítulo baja ~2 de su base; «TODAY» (mayúsculas) sube ~6,5.
        _aire = (_yh[0] - 6.5) - (_ys[0] + 2.0)
        chk("⚠️ lienzo %d: ≥ 3 unidades de aire entre subtítulo y «TODAY» (v560 dejaba 0,5)"
            % _vw, _aire >= 3.0, _aire)
        chk("lienzo %d: el título no se sale por arriba y no toca el subtítulo" % _vw,
            _yt[0] - 13 * 0.75 >= 0 and _ys[0] - 8.5 * 0.75 - (_yt[0] + 3) >= 0, (_yt, _ys))

# ══════════════════════════════════════════════════════════════════════════════
print("\n2. Home: las columnas se reparten por el ancho de la FILA")
HUS = fuente(os.path.join("core", "home_ui.py"))
_t = ast.parse(HUS)
_rh = next((n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == "render_home"), None)
chk("se localiza render_home", _rh is not None)
_with = [n for n in ast.walk(_rh) if isinstance(n, ast.With)
         and any("cpx_home_fila" in ast.unparse(i.context_expr) for i in n.items)] if _rh else []
chk("⚠️ las 3 columnas van DENTRO de `st.container(key=\"cpx_home_fila\")` (la regla las encuentra)",
    len(_with) == 1 and any(isinstance(c, ast.Call) and ast.unparse(c.func) == "st.columns"
                            for c in ast.walk(_with[0])), len(_with))
_css = [n.value for n in ast.walk(_rh) if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and "cpx_home_fila" in n.value] if _rh else []
_c = "".join(_css)
chk("el estilo va por `st.html` (solo <style>: no ocupa sitio)",
    _rh is not None and any(isinstance(c, ast.Call) and ast.unparse(c.func) == "st.html"
                            for c in ast.walk(_rh)))
chk("la fila es un contenedor de consultas por ancho", "container-type:inline-size" in _c)
_m1140 = _c.split("@container (max-width:1140px){", 1)[1].split("}@container", 1)[0] if "@container (max-width:1140px){" in _c else ""
chk("⚠️ bajo 1140 px de fila: KPI + mapa a TODO el ancho", "nth-child(1){flex:1 1 100%" in _m1140, _m1140[:200])
chk("⚠️ …y Projects | agenda debajo, a medias", "nth-child(n+2){flex:1 1 calc(50% - 1rem)" in _m1140)
chk("la regla solo toca la fila de fuera (no las tarjetas KPI de dentro)",
    _m1140.count(":not([data-testid='stColumn'] *)") >= 3)
_m520 = _c.split("@container (max-width:520px){", 1)[1] if "@container (max-width:520px){" in _c else ""
chk("bajo 520 px, una sola columna", "[data-testid='stColumn']{flex:1 1 100%" in _m520)

PUS = fuente(os.path.join("core", "projects_ui.py"))
chk("⚠️ resumen: bajo 560 px los indicadores van 3 por fila (no se parten palabras)",
    '@container (max-width:560px){.st-key-cpxresumen ' in PUS
    and 'flex:1 1 calc(33.3% - 1rem)' in PUS
    and '.st-key-cpxresumen [data-testid="stExpanderDetails"]' in PUS)

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. Lo que lee la IA (y el texto sin IA)")
from core import admin_digest as AD, auth                                    # noqa: E402
_lu = auth.list_users
auth.list_users = lambda *a, **k: [{"User": "appretince", "Name": "apprentice 1"},
                                   {"User": "jefa", "Name": "Bobo"}]
try:
    _d = {"grupo": "cliente1", "n_activos": 3, "n_total": 3, "avance_prom": 0, "horas": 4,
          "vencidos": [{"nombre": "PRUEBA MOVIL", "dias": -9, "fin": "2026-10-02"}],
          "por_vencer": [{"nombre": "88 walker", "dias": 3, "fin": "2026-10-14"}],
          "retrasos": [], "alarmas": [],
          "near_miss": [{"proyecto": "ZZ", "fecha": "2026-10-10", "desc": ""}],
          "sin_asignar": [], "campo_sin_contacto": ["appretince"],
          "avisos_sin_canal": [{"usuario": "jefa", "rol": "administrator"}],
          "cred_venc": [{"usuario": "appretince", "tipo": "White card", "dias": -3},
                        {"usuario": "appretince", "tipo": "First aid", "dias": 0},
                        {"usuario": "jefa", "tipo": "EWP", "dias": 5}],
          "sobre_presupuesto": []}
    _tx = AD.digest_text(_d)
finally:
    auth.list_users = _lu
chk("⚠️ fechas en DD/MM/YYYY («end 02/10/2026», «14/10/2026», «10/10/2026»)",
    "end 02/10/2026" in _tx and "14/10/2026" in _tx and "10/10/2026" in _tx, _tx)
chk("⚠️ ninguna fecha ISO", not re.search(r"\d{4}-\d{2}-\d{2}", _tx))
chk("⚠️ nombres, no logins (campo sin contacto, avisos sin canal, credenciales)",
    "apprentice 1" in _tx and "Bobo (administrator)" in _tx and "appretince" not in _tx
    and "jefa" not in _tx)
chk("⚠️ en inglés: «expired 3 d ago», «expires today», «in 5 d», «no description»",
    "(expired 3 d ago)" in _tx and "(expires today)" in _tx and "(in 5 d)" in _tx
    and "no description" in _tx)
chk("sin «VENCIDA», «en N d» ni «s/d»",
    "VENCIDA" not in _tx and not re.search(r"\ben \d+ d\b", _tx) and "s/d" not in _tx)

from streamlit.testing.v1 import AppTest                                    # noqa: E402

G_CRED = r'''
import streamlit as st
from core import projects_ui as PU, admin_digest, auth
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
auth.list_users = lambda *a, **k: [{"User": "appretince", "Name": "apprentice 1"}]
_d = {"retrasos": [], "vencidos": [], "por_vencer": [], "sin_asignar": [], "alarmas": [],
      "near_miss": [], "campo_sin_contacto": [], "sobre_presupuesto": [],
      "cred_venc": [{"usuario": "appretince", "tipo": "White card", "dias": -3}]}
class _Dig:
    def __call__(self, g):
        return _d
    def clear(self):
        pass
admin_digest.group_digest = _Dig()
PU._resumen_del_dia("G")
'''
at = AppTest.from_string(G_CRED, default_timeout=60)
at.run()
chk("Home: el resumen se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_b = [b for b in at.button if b.key == "resind_cred"]
chk("se localiza el indicador «Credentials»", len(_b) == 1)
if _b:
    _b[0].click()
    at.run()
    _cap = " ".join(c.value for c in at.caption)
    chk("⚠️ Home: «White card · apprentice 1 (expired 3 d ago)» (salía «White card·appretince (-3d)»)",
        "White card · apprentice 1 (expired 3 d ago)" in _cap and "(-3d)" not in _cap, _cap)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
