"""Verifica v295: etiqueta de celda, usos/borrado de trabajos y estructura."""
import sys, json, ast, re, pathlib
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

from core import roster as R

ok = True
def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")


# ── 1) etiqueta del trigger (la logica exacta que quedo en _tablero_editable) ──
def etiqueta(items, etq=lambda a: {"P1": "prueba2", "P2": "prueba 3",
                                   "P3": "Redfen"}.get(a, a)):
    trig = []
    for it in items:
        fl = R.franja_label(it["ini"], it["fin"])
        if (it["ini"], it["fin"]) == R.TURNO_DEFAULT:
            fl = ""
        trig.append(etq(it["asig"]) + (f" {fl}" if fl else ""))
    return f"{trig[0]} +{len(trig) - 1}" if len(trig) > 2 else " · ".join(trig)


T = R.TURNO_DEFAULT
print("== 1) etiqueta de la celda ==")
print(f"   turno estandar = {T}")
check("1 trabajo en turno estandar -> sin hora",
      etiqueta([{"asig": "P1", "ini": T[0], "fin": T[1]}]), "prueba2")
check("TU CASO: 2 en turno estandar",
      etiqueta([{"asig": "P1", "ini": T[0], "fin": T[1]},
                {"asig": "P2", "ini": T[0], "fin": T[1]}]), "prueba2 · prueba 3")
check("hora DISTINTA -> si se muestra",
      etiqueta([{"asig": "P1", "ini": "06:00", "fin": "14:00"}]), "prueba2 6:00–14:00")
check("mezcla: solo la excepcion lleva hora",
      etiqueta([{"asig": "P1", "ini": T[0], "fin": T[1]},
                {"asig": "P2", "ini": "16:00", "fin": "20:00"}]),
      "prueba2 · prueba 3 16:00–20:00")
check("3 trabajos -> primero + contador",
      etiqueta([{"asig": "P1", "ini": T[0], "fin": T[1]},
                {"asig": "P2", "ini": T[0], "fin": T[1]},
                {"asig": "P3", "ini": T[0], "fin": T[1]}]), "prueba2 +2")
check("celda vacia", etiqueta([]), "")

# ── 2) usos_de_trabajo / delete_trabajo ──
print("\n== 2) usos y borrado de trabajos ==")
ROSTER = [
    {"Group": "g", "Week": "2026-08-10", "User": "ana",
     "DataJSON": json.dumps({"lun": {"items": [{"a": "TRB-1", "i": "", "f": ""}]},
                              "mar": {"items": [{"a": "TRB-1", "i": "", "f": ""},
                                                {"a": "TRB-2", "i": "", "f": ""}]}})},
    {"Group": "g", "Week": "2026-08-17", "User": "beto",
     "DataJSON": json.dumps({"jue": {"items": [{"a": "TRB-1", "i": "", "f": ""}]}})},
    {"Group": "OTRO", "Week": "2026-08-10", "User": "zzz",     # otro grupo: NO cuenta
     "DataJSON": json.dumps({"lun": {"items": [{"a": "TRB-9", "i": "", "f": ""}]}})},
]
R._roster_records = lambda: ROSTER
check("TRB-1 usado 3 veces (2 semanas)", R.usos_de_trabajo("g", "TRB-1"), 3)
check("TRB-2 usado 1 vez",               R.usos_de_trabajo("g", "TRB-2"), 1)
check("TRB-3 sin usar",                  R.usos_de_trabajo("g", "TRB-3"), 0)
check("no cuenta el de OTRO grupo",      R.usos_de_trabajo("g", "TRB-9"), 0)
check("id vacio",                        R.usos_de_trabajo("g", ""), 0)

_BORRADAS = []
class _WS:
    def get_all_values(self): return [["ID"], ["TRB-1"], ["TRB-3"]]
    def delete_rows(self, i): _BORRADAS.append(i)
R._ws_trab = lambda: _WS()

_r, _m = R.delete_trabajo("g", "TRB-1")
check("trabajo EN USO no se borra", _r, False)
check("...y no toca la hoja", len(_BORRADAS), 0)
print(f"         motivo: {_m}")
_r, _m = R.delete_trabajo("g", "TRB-3")
check("trabajo SIN usar si se borra", _r, True)
check("...borra la fila correcta (3 = TRB-3)", _BORRADAS, [3])

# ── 3) estructura del modulo ──
print("\n== 3) estructura ==")
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py").read_text(encoding="utf-8")
arbol = ast.parse(src)

# ⚠️ Las keys se sacan por AST (keyword `key=` de una LLAMADA). Con regex se colaba
# `key = f"roscel_..."`, que es una VARIABLE local para armar el CSS, y salia como
# duplicado de la key real del popover. Falso positivo del verificador, no del codigo.
ks = []
for n in ast.walk(arbol):
    if isinstance(n, ast.Call):
        for kw in n.keywords:
            if kw.arg == "key":
                ks.append(ast.get_source_segment(src, kw.value) or "?")
check("keys de widget sin duplicar", sorted({k for k in ks if ks.count(k) > 1}), [])
check("_colmap definido una sola vez", len(re.findall(r"_colmap = ", src)), 1)
check("borrado tras confirmacion (disabled=not _conf)", "disabled=not _conf" in src)
# la cabecera de DIAS (la que lleva DIAS_LABEL) debe ir centrada y con aire abajo
# v384: v301 movió esa cabecera a la constante `_CAB` y v333 normalizó el
# tamaño a la escala de 9 pasos, así que el literal «font-size:12px» en la
# línea ya no existe. Lo que se protege sigue siendo: centrada y con aire.
_cab = next((l for l in src.splitlines() if "_CAB = (" in l), "")
_cab_bloque = src[src.index("_CAB = ("):src.index("_CAB = (") + 200] if _cab else ""
check("cabecera de dias centrada", "text-align:center" in _cab_bloque)
check("...y con margen abajo", "margin-bottom:" in _cab_bloque)

fn = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "_catalogo")
import builtins
globales = {n.name for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for n in arbol.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        globales |= {(a.asname or a.name.split(".")[0]) for a in n.names}
locales = {a.arg for a in fn.args.args}
for nodo in ast.walk(fn):
    if isinstance(nodo, ast.Lambda):
        locales |= {a.arg for a in nodo.args.args}
    if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
        locales.add(nodo.id)
libres = sorted({n.id for n in ast.walk(fn) if isinstance(n, ast.Name)
                 and not isinstance(n.ctx, ast.Store)
                 and n.id not in locales and n.id not in globales
                 and not hasattr(builtins, n.id)})
check("_catalogo: 0 nombres libres", libres, [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
