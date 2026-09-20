"""v301: cabeceras legibles · planificar varios dias · eliminar sin perder historial."""
import sys, json, re, ast, pathlib, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
from core import roster as R, roster_ui as RU

ok = True
def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")

LUNES = datetime.date(2026, 8, 10)

print("== 1) cabecera de la rejilla ==")
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py").read_text(encoding="utf-8")
_m = re.search(r'_CAB = \((.*?)\)', src, re.S)
_cab = _m.group(1) if _m else ""
# v384: era 13.5px y v333 normalizó la app a 9 pasos (11,12,13,14,16,18,21,26,34).
# Lo que v301 protegía es que la cabecera fuera MÁS GRANDE que el texto de las
# celdas, no ese número concreto.
check("mas grande que el texto de celda (12px)", "13px" in _cab)
check("seminegrita", "font-weight:600" in _cab)
check("centrada", "text-align:center" in _cab)
# ⚠️ ACTUALIZADO en v411 (regla v385: caducado, no relajado — razón al lado).
# Antes se exigía que el literal `style='{_CAB}'` apareciera EXACTAMENTE 2 veces: una
# en «Persona» y otra en los días. v411 añadió una variante para el día de HOY, así que
# los días ahora usan `{_CAB_HOY if _es_hoy else _CAB}` y ese literal ya solo sale una
# vez. Lo que v301 protege NO es el número de apariciones: es que **«Persona» y los
# días compartan el MISMO estilo base**, porque antes Persona iba a la izquierda y los
# días centrados, y la fila no cuadraba. Eso se comprueba directamente.
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
check("«Persona» usa el estilo base de cabecera",
      "style='{_CAB}'>Persona" in src or "style='{_CAB}'>Person" in src)
check("...y los días también parten de ese mismo estilo base",
      "_CAB_HOY if _es_hoy else _CAB" in src or "style='{_CAB}'>{R.DIAS_LABEL" in src)
check("ya no queda el padding-left viejo", "padding-left:11px" not in src)

print("\n== 2) planificar VARIOS dias de una ==")
GUARDADO = {}
R.guardar_persona = lambda g, l, u, sem: (GUARDADO.update({u: sem}), (True, "ok"))[1]
DATOS = {"ana": {"lun": {"items": [{"a": "OFF", "i": "", "f": ""}], "nota": ""}}}
_items = [{"asig": "PRJ-1", "ini": "07:00", "fin": "15:30"}]

GUARDADO.clear()
RU._guardar_celda("g", LUNES, "ana", DATOS, ["mar"], _items, "furgo")
_sem = GUARDADO["ana"]
check("1 dia: escribe solo ese", sorted(_sem), ["lun", "mar"])
check("...y NO toca el lunes existente", _sem["lun"]["items"][0]["a"], "OFF")

GUARDADO.clear()
RU._guardar_celda("g", LUNES, "ana", DATOS, ["mar", "mie", "jue"], _items, "furgo")
_sem = GUARDADO["ana"]
check("3 dias: los tres escritos",
      [d for d in ("mar", "mie", "jue") if _sem.get(d, {}).get("items")], ["mar", "mie", "jue"])
check("mismo contenido en los 3",
      len({json.dumps(_sem[d], sort_keys=True) for d in ("mar", "mie", "jue")}), 1)
check("la franja viaja", _sem["mar"]["items"][0]["i"], "07:00")
check("la nota viaja", _sem["jue"]["nota"], "furgo")
check("el lunes SIGUE intacto", _sem["lun"]["items"][0]["a"], "OFF")
check("DATOS de entrada NO se muto", DATOS["ana"].get("mar"), None)

GUARDADO.clear()
RU._guardar_celda("g", LUNES, "ana", DATOS, R.DIAS, _items, "")
check("los 5 dias (lo que hacia el check viejo)",
      len([d for d in R.DIAS if GUARDADO["ana"][d]["items"]]), 5)
check("multiselect de dias en la UI",
      '"Aplicar a estos días"' in src or 't("Apply to these days")' in src)
check("guardar deshabilitado sin dias", "disabled=not _destino" in src)

# ── v302: atajo "toda la semana" ──
print("\n== 2b) atajo de la semana completa (v302) ==")
# ⚠️ v390 (CADUCADO, actualizado con la razón): estas dos afirmaciones estaban
# fijadas al literal «Toda la semana (Lun–Vie)» y a `list(R.DIAS)`. Desde que se
# puede añadir sábado/domingo a una semana, las DOS cosas tienen que seguir a los
# días VISIBLES: la etiqueta se compone con `DIAS_LABEL[dias[0]]–DIAS_LABEL[dias[-1]]`
# y el destino es `list(dias)`. Dejar «Lun–Vie» escribiendo seis días sería mentir,
# y usar R.DIAS dejaría el sábado fuera del atajo sin decirlo. Lo que la regla
# defiende —que el check MANDE sobre el selector y cubra la semana entera— se sigue
# comprobando, ahora contra la lista visible.
check("existe el check",
      '"Toda la semana ({R.DIAS_LABEL[dias[0]]}–"' in src
      or '"The whole week ({R.DIAS_LABEL[dias[0]]}–"' in src)
check("el destino son los días VISIBLES cuando manda el check",
      "list(dias) if _all else _dd" in src)
check("el selector se deshabilita cuando manda el check", "disabled=_all" in src)
# el check va ANTES del multiselect (si no, no se puede deshabilitar)
# ⚠️ CADUCADO por v440 (i18n F3): los dos textos pasaron al inglés. Se resuelve la
# etiqueta que EXISTA; `str.index` lanza si no está, así que buscar solo el español
# hacía REVENTAR el guardián en vez de dar un FALLO legible.
_lbl_all = "Toda la semana (" if "Toda la semana (" in src else "The whole week ("
_lbl_dias = ("Aplicar a estos días" if "Aplicar a estos días" in src
             else "Apply to these days")
check("check declarado ANTES del multiselect",
      src.index(_lbl_all) < src.index(_lbl_dias))
# y sin rerun dentro del popover para el atajo (cerraria el popover)
_bloque = src[src.index(_lbl_all):src.index('"pvs_{_wk}_{idx}"')]
check("el atajo NO usa st.rerun (cerraria el popover)", "st.rerun" not in _bloque)

print("\n== 3) eliminar SIN perder el historial ==")
FILAS = [
    {"ID": "TRB-1", "Group": "g", "Number": "1", "Name": "Entrega", "Color": "#111",
     "ProjectID": "", "Active": "SI"},
    {"ID": "TRB-2", "Group": "g", "Number": "2", "Name": "Curso", "Color": "#222",
     "ProjectID": "", "Active": "SI"},
]
R._trab_records = lambda: FILAS
ROSTER = [{"Group": "g", "Week": "2026-08-10", "User": "ana",
           "DataJSON": json.dumps({"mar": {"items": [{"a": "TRB-1", "i": "", "f": ""}]},
                                    "mie": {"items": [{"a": "TRB-1", "i": "", "f": ""}]}})}]
R._roster_records = lambda: ROSTER
_UPD = []
def _upd(tid, cambios):
    _UPD.append((tid, cambios))
    for f in FILAS:
        if f["ID"] == tid:
            f.update({k: str(v) for k, v in cambios.items()})
    return True, "Trabajo actualizado."
R.update_trabajo = _upd
_BORRADAS = []
class _WS:
    def get_all_values(self): return [["ID"]] + [[f["ID"]] for f in FILAS]
    def delete_rows(self, i): _BORRADAS.append(i)
R._ws_trab = lambda: _WS()

check("TRB-1 esta en 2 dias", R.usos_de_trabajo("g", "TRB-1"), 2)
_r, _m = R.delete_trabajo("g", "TRB-1")
check("EN USO: se elimina igual (ya no lo impide)", _r, True)
print(f"         {_m}")
check("...marcandolo, NO borrando la fila", _BORRADAS, [])
check("...con estado ELIMINADO", _UPD, [("TRB-1", {"Active": R.ELIMINADO})])

# LO CRITICO: el historico sigue resolviendo
import core.projects as P
P.list_projects = lambda **k: []
_idx = R.trabajos_idx("g")
check("HISTORICO: trabajos_idx SIGUE conociendo TRB-1", "TRB-1" in _idx)
check("...con su nombre", R.etiqueta_de("TRB-1", _idx), "1. Entrega")
check("...y su color", R.color_de("TRB-1", _idx), "#111")

check("fuera del catalogo", [r["ID"] for r in R.list_trabajos("g", incluir_inactivos=True)],
      ["TRB-2"])
check("fuera del desplegable de asignar",
      "TRB-1" not in [v for _, v in RU._opciones("g", _idx)])
check("recuperable si hace falta",
      [r["ID"] for r in R.list_trabajos("g", incluir_inactivos=True, incluir_eliminados=True)],
      ["TRB-1", "TRB-2"])

_r, _m = R.delete_trabajo("g", "TRB-2")   # sin usar
check("SIN usar: se borra la fila de verdad", _r and _BORRADAS == [3], True)

print("\n== 4) compila e importa ==")
import py_compile, importlib
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
malos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:70]))
check(f"{len(mods)-len(malos)}/{len(mods)} modulos + app.py", malos, [])
# ⚠️ Por AST: `toda_semana` aparece en la DOCSTRING que explica que habia antes, y un
# grep lo cuenta como si siguiera vivo (la misma trampa que en v296/v299).
_a = ast.parse(src)
_fn = next(n for n in _a.body if isinstance(n, ast.FunctionDef)
           and n.name == "_guardar_celda")
check("la firma ya no tiene `toda_semana`",
      [p.arg for p in _fn.args.args],
      ["grupo", "lunes", "usuario", "datos", "dias_destino", "items", "nota"])
_llamadas = [n for n in ast.walk(_a) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "_guardar_celda"]
check("1 sola llamada", len(_llamadas), 1)
check("...con 7 argumentos posicionales", len(_llamadas[0].args), 7)
check("...y sin keyword `toda_semana`",
      [k.arg for k in _llamadas[0].keywords], [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
