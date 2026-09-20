"""v387 · Vista del día de una persona (línea de tiempo con carriles).

Lo que hay que proteger:
  (a) que los carriles SEPAREN lo que se solapa — si dos bloques comparten carril,
      uno tapa al otro y el aviso deja de tener respaldo visual;
  (b) que ningún bloque se salga del eje (aritmética de %);
  (c) que las franjas RARAS no desaparezcan en silencio;
  (d) que la vista se cierre sola al cambiar de semana (enseñar el día equivocado
      sería peor que no enseñar nada);
  (e) ⚠️ que las funciones se EJECUTEN, no solo se importen (lección v378: los
      NameError dentro de una función pasan compileall, imports y AST).
"""
import ast
import importlib
import pathlib
import py_compile
import sys

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ok = True


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


import streamlit as st                                          # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}
from core import roster_ui as RU                                # noqa: E402
from core import roster as R                                    # noqa: E402

SRC = (BASE / "core" / "roster_ui.py").read_text(encoding="utf-8")
ARB = ast.parse(SRC)

print("== 1) clasificar la franja (las 'raras' NO se descartan) ==")
_c = RU._clase_franja
check("07:00–15:30 → hora", _c({"ini": "07:00", "fin": "15:30"}), "hora")
check("vacía → día completo", _c({"ini": "", "fin": ""}), "dia")
check("solo inicio → rara", _c({"ini": "07:00", "fin": ""}), "rara")
check("fin ANTES del inicio → rara", _c({"ini": "15:30", "fin": "07:00"}), "rara")
check("inicio == fin → rara (ancho 0)", _c({"ini": "08:00", "fin": "08:00"}), "rara")
check("basura → rara", _c({"ini": "ayer", "fin": "15:30"}), "rara")

print("\n== 2) carriles: lo que se solapa NO comparte carril ==")


def _it(a, i, f):
    return {"asig": a, "ini": i, "fin": f}


# ⚠️ EL CASO REAL medido en la hoja: campo1, martes 10/08, dos obras a la MISMA hora.
_real = [_it("PRJ-0005", "07:00", "15:30"), _it("PRJ-0006", "07:00", "15:30")]
check("caso real (dos obras 07:00–15:30) → 2 carriles", len(RU._carriles(_real)), 2)
_seg = [_it("A", "07:00", "11:00"), _it("B", "11:00", "15:30")]
check("consecutivas (tocan en 11:00) → 1 carril", len(RU._carriles(_seg)), 1)
check("...y las dos en él", len(RU._carriles(_seg)[0]), 2)
_mix = [_it("A", "07:00", "12:00"), _it("B", "10:00", "14:00"), _it("C", "15:00", "17:00")]
_cs = RU._carriles(_mix)
check("A∩B + C suelta → 2 carriles", len(_cs), 2)
check("C se reaprovecha en el 1er carril (no abre uno nuevo)",
      sorted(x["asig"] for x in _cs[0]), ["A", "C"])
check("una sola → 1 carril", len(RU._carriles([_it("A", "07:00", "15:30")])), 1)
# ninguna asignación puede perderse por el camino
for _n, _lst in (("real", _real), ("seg", _seg), ("mix", _mix)):
    _plano = [x for c in RU._carriles(_lst) for x in c]
    check(f"{_n}: no se pierde ninguna", len(_plano), len(_lst))

print("\n== 2b) las horas del día son la UNIÓN, no la suma ==")
# ⚠️ El caso que lo motivó: la pantalla decía «17.0 h» de una persona que trabajó
# 8,5 — el mismo rato contado en dos obras, justo lo que el aviso de al lado
# denuncia. Un número que miente con esa cara es peor que no ponerlo.
check("caso real (dos obras 07:00–15:30) = 8.5 h, NO 17",
      RU._ocupado(_real) / 60, 8.5)
check("...la suma ingenua sí daría 17 (por eso hacía falta)",
      sum(RU._min(i["fin"]) - RU._min(i["ini"]) for i in _real) / 60, 17.0)
check("día partido de verdad → se suman los dos tramos",
      RU._ocupado(_seg) / 60, 8.5)
check("solape PARCIAL (07–12 + 10–14) → 7 h, no 9",
      RU._ocupado([_it("A", "07:00", "12:00"), _it("B", "10:00", "14:00")]) / 60, 7.0)
check("una DENTRO de otra (07–15 + 09–10) → 8 h",
      RU._ocupado([_it("A", "07:00", "15:00"), _it("B", "09:00", "10:00")]) / 60, 8.0)
check("tres encadenadas con hueco (7–9, 8–11, 13–14) → 5 h",
      RU._ocupado([_it("A", "07:00", "09:00"), _it("B", "08:00", "11:00"),
                   _it("C", "13:00", "14:00")]) / 60, 5.0)
check("sin franjas → 0", RU._ocupado([]), 0)
check("la unión NUNCA supera la suma",
      all(RU._ocupado(l) <= sum(RU._min(i["fin"]) - RU._min(i["ini"]) for i in l)
          for l in (_real, _seg, _mix)), True)

print("\n== 3) el eje: ningún bloque se sale ==")


def _eje(items):
    """Réplica EXACTA de la aritmética de `_vista_dia` (mismos números, no parecidos)."""
    lo = max(0, (min(RU._min(i["ini"]) for i in items) // 60 - 1) * 60)
    hi = min(1440, (-(-max(RU._min(i["fin"]) for i in items) // 60) + 1) * 60)
    if hi - lo < RU._EJE_MIN:
        hi = min(1440, lo + RU._EJE_MIN)
        lo = max(0, hi - RU._EJE_MIN)
    return lo, hi


_lo, _hi = _eje(_real)
check("07:00–15:30 → eje 06:00", RU._hm(_lo), "06:00")
check("...a 17:00 (una hora de aire a cada lado)", RU._hm(_hi), "17:00")
_span = _hi - _lo
for _nom, _lst in (("real", _real), ("mix", _mix), ("seg", _seg),
                   ("madrugada", [_it("A", "00:00", "02:00")]),
                   ("hasta el final", [_it("A", "22:00", "23:59")]),
                   ("cortito", [_it("A", "09:00", "09:30")])):
    _l, _h = _eje(_lst)
    _sp = _h - _l
    _fuera = [i["asig"] for i in _lst
              if (RU._min(i["ini"]) - _l) < 0
              or (RU._min(i["fin"]) - _l) / _sp * 100 > 100.001]
    check(f"{_nom}: eje {RU._hm(_l)}–{RU._hm(_h)}, 0 bloques fuera", _fuera, [])
    check(f"{_nom}: el eje nunca se sale del día", (_l >= 0 and _h <= 1440), True)
    check(f"{_nom}: eje de al menos 4 h", _sp >= RU._EJE_MIN, True)

print("\n== 4) tamaños de fuente dentro de la escala de v333 ==")
import re                                                        # noqa: E402
_ESCALA = {11, 12, 13, 14, 16, 18, 21, 26, 34}
_fn = next(n for n in ast.walk(ARB) if isinstance(n, ast.FunctionDef)
           and n.name == "_vista_dia")
_txt = ast.get_source_segment(SRC, _fn) or ""
_malos = [int(m) for m in re.findall(r"font-size:(\d+)px", _txt) if int(m) not in _ESCALA]
check("0 tamaños fuera de la escala", _malos, [])
check("...y se comprobó algo (no pasó en vacío)",
      len(re.findall(r"font-size:(\d+)px", _txt)) >= 5, True)

print("\n== 5) los ticks de los extremos no se recortan ==")
check("el primero no se centra", 'if m == lo else' in _txt and '"none"' in _txt)
check("el último se alinea a la derecha", 'translateX(-100%)' in _txt)

print("\n== 6) EJECUTAR de verdad (importar no ejecuta — lección v378) ==")
TIDX = {"PRJ-0005": {"ID": "PRJ-0005", "Nombre": "Meriton Zetland", "Color": "#1d9e75",
                     "ProyectoID": "PRJ-0005", "Numero": ""},
        "PRJ-0006": {"ID": "PRJ-0006", "Nombre": "Green Square", "Color": "#d85a30",
                     "ProyectoID": "PRJ-0006", "Numero": ""},
        "TRB-0001": {"ID": "TRB-0001", "Nombre": "Entrega material", "Color": "#7f77dd",
                     "ProyectoID": "", "Numero": "12"}}


def _datos(items, nota=""):
    return {"campo1": {"mar": {"items": [{"a": i["asig"], "i": i["ini"], "f": i["fin"]}
                                         for i in items], "nota": nota}}}


from datetime import date                                        # noqa: E402
_LUN = date(2026, 8, 10)
_ESCENARIOS = [
    ("caso real: dos obras a la misma hora", _real, "llevar andamio"),
    ("una sola con horario", [_it("PRJ-0005", "07:00", "15:30")], ""),
    ("solo día completo (sin eje)", [_it("PRJ-0005", "", ""), _it("TRB-0001", "", "")], ""),
    ("mezcla: con hora + día completo + rara",
     [_it("PRJ-0005", "07:00", "12:00"), _it("TRB-0001", "", ""),
      _it("PRJ-0006", "15:30", "07:00")], "nota"),
    ("estado OFF", [_it("OFF", "", "")], ""),
    ("día vacío (la guarda tiene que aguantar)", [], ""),
]
for _nom, _its, _nota in _ESCENARIOS:
    try:
        RU._vista_dia("cliente1", _LUN, "campo1", "Jaime López", "mar",
                      _datos(_its, _nota), TIDX)
        check(f"corre: {_nom}", True)
    except Exception as e:
        check(f"corre: {_nom}", f"{type(e).__name__}: {e}", True)

print("\n== 7) enganche: botón, estado y cierre por cambio de semana ==")
_tab = next(n for n in ast.walk(ARB) if isinstance(n, ast.FunctionDef)
            and n.name == "_tablero_editable")
_ttxt = ast.get_source_segment(SRC, _tab) or ""
check("el popover ofrece «Ver el día»", "Ver el día" in _ttxt)
check("...solo si la celda tiene algo", "if items_cur and st.button" in _ttxt)
check("...y guarda persona + día + SEMANA",
      '"_dia_abierto"' in _ttxt and '"wk": lunes.isoformat()' in _ttxt)
_rp = next(n for n in ast.walk(ARB) if isinstance(n, ast.FunctionDef)
           and n.name == "render_planificacion")
_rtxt = ast.get_source_segment(SRC, _rp) or ""
check("la vista se pinta bajo el tablero", "_vista_dia(" in _rtxt)
check("...comparando la semana", '_da.get("wk") == lunes.isoformat()' in _rtxt)
check("...y se descarta si ya no aplica", 'st.session_state.pop("_dia_abierto"' in _rtxt)
# la simulación del guardado de estado, con las MISMAS condiciones del código
STAFF = [{"Usuario": "campo1", "Nombre": "Jaime López"}]


def _abre(da, lunes, staff):
    u = next((x for x in staff if x["Usuario"] == da.get("u")), None)
    return bool(u and da.get("wk") == lunes.isoformat() and da.get("d") in R.DIAS)


check("misma semana → abre",
      _abre({"u": "campo1", "d": "mar", "wk": "2026-08-10"}, _LUN, STAFF), True)
check("OTRA semana → NO abre (no enseña el día equivocado)",
      _abre({"u": "campo1", "d": "mar", "wk": "2026-08-03"}, _LUN, STAFF), False)
check("persona que ya no está → NO abre",
      _abre({"u": "borrado", "d": "mar", "wk": "2026-08-10"}, _LUN, STAFF), False)
check("día inválido → NO abre",
      _abre({"u": "campo1", "d": "sab", "wk": "2026-08-10"}, _LUN, STAFF), False)
check("estado vacío → NO abre", _abre({}, _LUN, STAFF), False)

print("\n== 8) keys de widget sin duplicar ==")
_keys = []
for n in ast.walk(ARB):
    if isinstance(n, ast.Call):
        for kw in n.keywords:
            if kw.arg == "key":
                _keys.append(ast.get_source_segment(SRC, kw.value))
_dup = sorted({k for k in _keys if _keys.count(k) > 1 and k})
check("0 keys literales repetidas", _dup, [])
# ⚠️ Las keys de la vista llevan (semana, usuario, día), así que DOS llamadas a
# `_vista_dia` en la misma pasada darían StreamlitDuplicateElementKey y cortarían
# el render. Hoy el call-site es único; esto lo mantiene así (lo encontré cuando mi
# propia mini-app la llamó cuatro veces y reventó la página).
_llamadas = [n for n in ast.walk(ARB) if isinstance(n, ast.Call)
             and getattr(n.func, "id", "") == "_vista_dia"]
check("_vista_dia se llama desde UN solo sitio", len(_llamadas), 1)
check("las nuevas existen", all(k in SRC for k in (
    'key=f"pvd_{_wk}_{idx}"',
    'key=f"vdcl_{lunes:%Y%m%d}_{usuario}_{dia}"')))
# todas las keys de la vista comparten la tripleta (semana, persona, día)
_vk = [k for k in _keys if k and ("vdop_" in k or "vdcl_" in k)]
check("las keys de la vista llevan semana+persona+día",
      [k for k in _vk if not ("{usuario}" in k and "{dia}" in k
                              and "%Y%m%d" in k)], [])
check("...y son 2 (no pasó en vacío)", len(_vk), 2)

print("\n== 9) nombres libres + compila + importa ==")
import builtins                                                  # noqa: E402
_B = set(dir(builtins)) | {"__file__"}
_mod = set()
for n in ARB.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        _mod.add(n.name)
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        for x in n.names:
            _mod.add((x.asname or x.name).split(".")[0])
    elif isinstance(n, ast.Assign):
        for t in n.targets:
            for s in ast.walk(t):
                if isinstance(s, ast.Name):
                    _mod.add(s.id)

for _f in ("_vista_dia", "_carriles", "_clase_franja", "_hm", "_ocupado"):
    _node = next(n for n in ast.walk(ARB) if isinstance(n, ast.FunctionDef)
                 and n.name == _f)
    asign, usados = set(_mod) | _B, []
    for n in ast.walk(_node):
        if isinstance(n, ast.arg):
            asign.add(n.arg)
        elif isinstance(n, ast.Name):
            (asign.add(n.id) if isinstance(n.ctx, ast.Store) else usados.append(n.id))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                asign.add((x.asname or x.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            asign.add(n.name)
        elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
            asign.add(getattr(n, "name", ""))
            for x in getattr(n.args, "args", []):
                asign.add(x.arg)
        elif isinstance(n, ast.comprehension):
            for s in ast.walk(n.target):
                if isinstance(s, ast.Name):
                    asign.add(s.id)
    check(f"{_f} sin nombres libres", sorted({u for u in usados if u not in asign}), [])

mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:80]))
check(f"{len(mods) - len(malos)}/{len(mods)} modulos + app.py", malos, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
