# -*- coding: utf-8 -*-
"""v467 · El historial deja de estar en español, ninguna columna pinta «None», y
las carpetas de Drive pasan a ingles sin dejar huerfanos los archivos ya subidos.
"""
import ast
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:\Users\diego\P1\survey_app")     # ⚠️ o no hay secrets (trampa n19)
sys.path.insert(0, os.getcwd())
import streamlit as st
st.session_state["auth"] = {"usuario": "dacox", "rol": "owner", "grupo": "cliente1"}

_f = []
def ok(m):    print("   ok   %s" % m)
def fallo(m): print("   FALLO %s" % m); _f.append(m)

from core import inventory as INV, drive_store as DS
from core.i18n import etiqueta as _etq

print("1. El texto COMPUESTO del historial se traduce al PINTAR, no en la hoja")
# ⚠️ Las dos direcciones: si solo se comprobara la de pantalla, traducir tambien la
# escritura pasaria — y eso mete ingles en el DATO (el fallo que evito v464).
if INV.ubic_texto("bodega: X", _etq) == "warehouse: X":
    ok("con traductor: 'bodega: X' -> 'warehouse: X'")
else:
    fallo("la pantalla sigue en español: %r" % INV.ubic_texto("bodega: X", _etq))
if INV.ubic_texto("bodega: X") == "bodega: X":
    ok("SIN traductor devuelve el dato intacto (lo que se guarda)")
else:
    fallo("se estaria escribiendo ingles en el historial")
if INV.ubic_texto("proyecto: Torre: fase 2", _etq) == "project: Torre: fase 2":
    ok("una referencia con ':' dentro no se parte mal")
else:
    fallo("parte por el ':' equivocado")

print("")
print("2. Las celdas del historial pasan por ese traductor")
src = Path("core/inventory_ui.py").read_text(encoding="utf-8")
a = ast.parse(src)
crudas = []
for n in ast.walk(a):
    if isinstance(n, ast.Dict):
        for k, v in zip(n.keys, n.values):
            if isinstance(k, ast.Constant) and k.value in ("Desde", "Hacia"):
                if "ubic_texto" not in ast.dump(v):
                    crudas.append(k.value)
if crudas:
    fallo("el historial pinta %s crudo, en español junto a un tipo ya traducido" % crudas)
else:
    ok("Desde/Hacia pasan por ubic_texto")

print("")
print("3. Ninguna celda de tabla puede pintar el literal «None»")
# ⚠️ CORREGIDO EN v486: esta nota decia «con NaN es float y la celda sale vacia,
# medido» y era FALSO. Medido en 1.57 con una tabla por caso e interceptando
# `fillText`: `nan`, `None` y `pd.NA` pintan «None» LOS TRES —con o sin
# `NumberColumn`, con formato o sin el, y hasta con `Styler(na_rep="")`—, porque
# es el placeholder de valor ausente de Streamlit y una columna TIPADA convierte
# incluso `""` en nulo. Lo UNICO que vacia la celda es una CADENA en una columna
# sin tipar, y de ahi `tabla.celda()`. Por eso esta red caza tambien el NaN: con
# la afirmacion vieja, «arreglar» un None poniendo NaN pasaba el chequeo y seguia
# pintando «None» en pantalla (lo que hizo v485).
malas = []


def _celdas_de_tabla(fnodo):
    """Los pares (columna, valor) de todo dict que alimente una tabla en esta función.

    ⚠️ REHECHA en v485. La version anterior solo miraba `ast.Dict` DENTRO de la llamada
    a `pd.DataFrame(...)`, y tenia DOS puntos ciegos que dejaron pasar el fallo real de
    la tabla del parte de horas (v484):
      · el dict se construia FUERA y a `pd.DataFrame` le llegaba una VARIABLE — el
        mismo agujero que v471 tuvo que cerrar resolviendo variables;
      · y era un `ast.DictComp` (`{k: v for ...}`), que no tiene `.keys`/`.values`
        sino `.key`/`.value`.
    Con las dos cegueras, su «0» no significaba nada para esa tabla. Ahora se recorre
    la FUNCION que contiene la tabla: mas ancho, y el discriminador de abajo mantiene
    los falsos positivos a cero (validado en las dos direcciones).
    """
    # ⚠️ Se RESUELVE la variable que recibe `pd.DataFrame(...)` en vez de recorrer la
    # funcion entera: recorrerla marcaba 5 dicts sanos que no alimentan ninguna tabla, y
    # un detector con falsos positivos acaba ignorandose (v450). Es la sonda de v471.
    asign = {}
    for n in ast.walk(fnodo):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    asign.setdefault(tg.id, []).append(n.value)

    raices = []
    for n in ast.walk(fnodo):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "DataFrame":
            for a in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(a, ast.Name):
                    raices.extend(asign.get(a.id, []))
                else:
                    raices.append(a)

    out = []
    for raiz in raices:
        for n in ast.walk(raiz):
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    out.append((k.value if isinstance(k, ast.Constant) else "?", v))
            elif isinstance(n, ast.DictComp):
                out.append(("?" if not isinstance(n.key, ast.Constant)
                            else n.key.value, n.value))
    return out


def _nulo_num(n):
    """¿Este nodo es un nulo numerico? Devuelve como se escribio, o "".

    ⚠️ v486: `float("nan")`, `np.nan` y `pd.NA` se pintan «None» igual que None
    (medido), asi que para esta red son el mismo fallo.
    """
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "float":
        a = n.args[0] if n.args else None
        if isinstance(a, ast.Constant) and str(a.value).strip().lower() == "nan":
            return 'float("nan")'
    if isinstance(n, ast.Attribute) and n.attr in ("nan", "NA", "NaN"):
        mod = getattr(n.value, "id", "")
        if mod in ("np", "numpy", "pd", "pandas", "math"):
            return "%s.%s" % (mod, n.attr)
    return ""

for p in sorted(Path("core").glob("*_ui.py")):
    t = ast.parse(p.read_text(encoding="utf-8"))
    for f_ in [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)]:
        for col, v in _celdas_de_tabla(f_):
            if isinstance(v, ast.IfExp) and isinstance(v.orelse, ast.Constant)                and v.orelse.value is None:
                malas.append("%s:%s %s" % (p.name, v.lineno, col))
            elif isinstance(v, ast.Constant) and v.value is None:
                malas.append("%s:%s %s" % (p.name, v.lineno, col))
            # ⚠️ Un `.get(k)` SIN defecto devuelve None implicitamente. Acotado a la
            # clave VARIABLE, que es el discriminador de verdad: una fila de hoja se lee
            # con el nombre LITERAL de su cabecera y `hojas.registros` siempre las trae
            # todas, asi que `.get("Type")` nunca da None (da "", que SI sale vacio). Lo
            # que puede faltar es la clave calculada — un dict indexado por los dias que
            # tienen horas. Sin el matiz, la red marcaba 12 sitios sanos, y un detector
            # que grita sobre lo que esta bien acaba ignorandose entero (v450).
            elif (isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "get"
                    and len(v.args) == 1 and not v.keywords
                    and not isinstance(v.args[0], ast.Constant)):
                malas.append("%s:%s %s (.get de clave variable, sin defecto)"
                             % (p.name, v.lineno, col))
            # ⚠️ v486: el NaN cuenta IGUAL que el None. Cubre las tres formas de
            # escribirlo —`float("nan")`, `np.nan`/`numpy.nan` y `pd.NA`— tanto como
            # valor directo como en la rama `else` de un ternario, que es como se
            # colo en las cuatro tablas de v467/v485.
            else:
                # ⚠️ Se recorre el SUBARBOL del valor, no una lista de posiciones.
                # Enumerarlas ya fallo: cubria el valor directo y la rama `else` de
                # un ternario, y se le escapo `.get(d, float("nan"))` — el nulo
                # metido en el DEFECTO del `.get`, que es EXACTAMENTE la forma que
                # tenia v485 en produccion. Medido: 0 falsos positivos en el repo.
                _nulo = next((z for z in (_nulo_num(n2) for n2 in ast.walk(v)) if z),
                             "")
                if _nulo:
                    malas.append("%s:%s %s (%s: se pinta «None» igual que None)"
                                 % (p.name, v.lineno, col, _nulo))
if malas:
    for m in malas:
        fallo("pintaria «None» si la columna entera esta vacia: %s" % m)
else:
    ok("0 celdas con un nulo (None ni NaN): se usa `tabla.celda` -> cadena")

print("")
print("4. Las carpetas de Drive: ingles, con respaldo que RENOMBRA")
if DS.ROOT_NAME == "COPEX Projects":
    ok("la raiz es %r" % DS.ROOT_NAME)
else:
    fallo("la raiz sigue siendo %r" % DS.ROOT_NAME)
_viejas = set(DS.LEGADO_CARPETAS.values())
usos = []
for p in sorted(list(Path("core").glob("*.py")) + [Path("app.py")]):
    if p.name == "drive_store.py":
        continue
    t = ast.parse(p.read_text(encoding="utf-8"))
    for n in ast.walk(t):
        if isinstance(n, ast.Constant) and n.value in _viejas:
            usos.append("%s:%s %r" % (p.name, n.lineno, n.value))
if usos:
    for u in usos:
        fallo("usa el nombre viejo de carpeta: %s" % u)
else:
    ok("ningun modulo pide una carpeta con el nombre viejo")

# ⚠️ Lo que hace segura la migracion es que se RENOMBRE en vez de crear: renombrar
# conserva el contenido (los ficheros cuelgan por id), crear deja los 27 documentos
# ya subidos en la carpeta vieja, invisibles y sin ningun error.
_fn = next((n for n in ast.walk(ast.parse(Path("core/drive_store.py").read_text(encoding="utf-8")))
            if isinstance(n, ast.FunctionDef) and n.name == "carpeta_con_legado"), None)
if _fn is None:
    fallo("no existe carpeta_con_legado")
else:
    d = ast.dump(_fn)
    if "_rename_folder" in d and "_create_folder" in d:
        ok("busca el nuevo, RENOMBRA el viejo y solo crea si no hay ninguno")
    else:
        fallo("no renombra: crearia una carpeta nueva y dejaria los archivos huerfanos")
    l_ren = next((n.lineno for n in ast.walk(_fn)
                  if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_rename_folder"), None)
    l_cre = next((n.lineno for n in ast.walk(_fn)
                  if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_create_folder"), None)
    if l_ren and l_cre and l_ren < l_cre:
        ok("el renombrado (L%s) se intenta ANTES de crear (L%s)" % (l_ren, l_cre))
    else:
        fallo("crea antes de mirar si la carpeta vieja existe")

print("")
if _f:
    print("FALLOS: %d" % len(_f))
    sys.exit(1)
print("TODO OK - v467")
