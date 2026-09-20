# -*- coding: utf-8 -*-
"""v487 amplia `verif_v469`: el valor viejo no solo se COMPARA, tambien se BUSCA y se ESCRIBE.

Su bloque 1 barre `ast.Compare`, y los dos fallos de v487 entraban por otras puertas:
  · como CLAVE de busqueda — `est.get("disponible")` —, que dejaba las KPIs de
    inventario en 0 SIEMPRE;
  · como valor ESCRITO o por defecto — `campos["Status"] = "mantenimiento"`,
    `or "campo"`, una fila con "disponible" —, que dejaba la hoja mezclada y, en
    Usuarios, un usuario sin rol con OWNER preseleccionado.
Se inserta ANTES del veredicto final: un bloque despues del `sys.exit` no corre (v452).
"""
import io
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v469.py")
NL = chr(10)
s = io.open(RUTA, encoding="utf-8").read()

ANCLA = NL.join(['print("")', 'if _f:', '    print("FALLOS: %d" % len(_f))'])
if s.count(ANCLA) != 1:
    raise SystemExit("ancla del veredicto aparece %d veces" % s.count(ANCLA))

BLOQUE = r'''print("")
print("9. v487 · el valor viejo tampoco se BUSCA ni se ESCRIBE")
import ast as _ast9
from pathlib import Path as _P9
from core import valores as _V9

_VIEJOS9 = {k for k, v in _V9.LEGADO.items() if k != v}
_COLS9 = {c for _, c in _V9.COLUMNAS}


def _es_viejo9(n):
    return (isinstance(n, _ast9.Constant) and isinstance(n.value, str)
            and n.value in _VIEJOS9)


def _barre9(fuentes):
    """(busquedas, escrituras) sobre {nombre: arbol}."""
    # ⚠️ Discriminador de las BUSQUEDAS: muchas palabras viejas son tambien CLAVES
    # internas de diccionarios que la propia app construye (`usuario`, `proyecto`,
    # `entrada`, `pendiente`…), y buscarlas ahi es correcto. Lo que falla es buscar una
    # clave que NADIE mete a mano: esa solo puede venir de los DATOS, y los datos llegan
    # canonizados. Sin este matiz la red daba 171 falsos positivos (v450: un detector
    # que grita sobre lo que esta bien acaba ignorandose).
    construidas = set()
    for arb in fuentes.values():
        for n in _ast9.walk(arb):
            if isinstance(n, _ast9.Dict):
                construidas |= {k.value for k in n.keys if isinstance(k, _ast9.Constant)}
            elif isinstance(n, _ast9.Assign):
                for tg in n.targets:
                    if isinstance(tg, _ast9.Subscript) and isinstance(tg.slice, _ast9.Constant):
                        construidas.add(tg.slice.value)
            elif isinstance(n, _ast9.Call) and getattr(n.func, "id", "") == "dict":
                construidas |= {kw.arg for kw in n.keywords if kw.arg}
    busq, escr = [], []
    for nom, arb in fuentes.items():
        for n in _ast9.walk(arb):
            if (isinstance(n, _ast9.Call) and getattr(n.func, "attr", "") == "get"
                    and n.args and _es_viejo9(n.args[0])
                    and n.args[0].value not in construidas):
                busq.append("%s:%d .get(%r)" % (nom, n.lineno, n.args[0].value))
            elif (isinstance(n, _ast9.Subscript) and _es_viejo9(n.slice)
                    and isinstance(n.ctx, _ast9.Load) and n.slice.value not in construidas):
                busq.append("%s:%d [%r]" % (nom, n.lineno, n.slice.value))
            elif isinstance(n, _ast9.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, _ast9.Constant) and k.value in _COLS9 and _es_viejo9(v):
                        escr.append("%s:%d {%r: %r}" % (nom, v.lineno, k.value, v.value))
            elif (isinstance(n, _ast9.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], _ast9.Subscript)
                    and isinstance(n.targets[0].slice, _ast9.Constant)
                    and n.targets[0].slice.value in _COLS9 and _es_viejo9(n.value)):
                escr.append("%s:%d [%r] = %r" % (nom, n.lineno, n.targets[0].slice.value,
                                                 n.value.value))
            elif isinstance(n, _ast9.BoolOp) and isinstance(n.op, _ast9.Or):
                for v in n.values[1:]:
                    if _es_viejo9(v):
                        escr.append("%s:%d or %r" % (nom, v.lineno, v.value))
        for f in [x for x in _ast9.walk(arb) if isinstance(x, _ast9.FunctionDef)]:
            if not any(isinstance(c, _ast9.Call) and getattr(c.func, "attr", "")
                       in ("append_row", "append_rows") for c in _ast9.walk(f)):
                continue
            for lst in [x for x in _ast9.walk(f) if isinstance(x, _ast9.List)]:
                for sub in _ast9.walk(lst):
                    if _es_viejo9(sub):
                        escr.append("%s:%d fila de %s(): %r" % (nom, sub.lineno, f.name,
                                                                 sub.value))
    return sorted(set(busq)), sorted(set(escr))


# ⚠️ La red se VALIDA contra el fallo real construido antes de creerse su cero (trampa
# n12): una clave vieja que nadie construye, una escritura y un defecto por `or`.
_caso9 = _ast9.parse(
    "def resumen():\n"
    "    por = {}\n"
    "    for a in xs:\n"
    "        por[a.get('Status')] = 1\n"
    "    return por\n"
    "def kpi(est):\n"
    "    return est.get('disponible', 0)\n"
    "def alta(w):\n"
    "    w.append_row(['A1', 'disponible'])\n"
    "def rol(u):\n"
    "    return u.get('Role') or 'campo'\n"
    "def sano(r):\n"
    "    d = {'usuario': 1}\n"
    "    return r.get('usuario')\n")
_b9, _e9 = _barre9({"caso": _caso9})
(ok if (any("disponible" in x for x in _b9) and any("disponible" in x for x in _e9)
        and any("campo" in x for x in _e9) and not any("usuario" in x for x in _b9))
 else fallo)("la red VE el fallo construido (busqueda, fila y `or`) y NO marca la clave interna"
             + ("" if _b9 else " -> no vio nada: %r %r" % (_b9, _e9)))

_fuentes9 = {}
for _p9 in sorted(_P9("core").glob("*.py")) + [_P9("app.py")]:
    _fuentes9[_p9.name] = _ast9.parse(io.open(_p9, encoding="utf-8").read())
_b9, _e9 = _barre9(_fuentes9)
(ok if not _b9 else fallo)(
    "ninguna BUSQUEDA de un valor viejo que nadie construye (dejaba KPIs en 0)"
    + ("" if not _b9 else " -> " + " · ".join(_b9)))
(ok if not _e9 else fallo)(
    "ninguna ESCRITURA ni defecto con un valor viejo (hoja mezclada / owner preseleccionado)"
    + ("" if not _e9 else " -> " + " · ".join(_e9)))

'''

s = s.replace(ANCLA, BLOQUE + ANCLA, 1)
compile(s, RUTA, "exec")
if "import io" not in s.split("print(\"1.")[0]:
    s = s.replace("import ast", "import ast\nimport io", 1)
    compile(s, RUTA, "exec")
io.open(RUTA, "w", encoding="utf-8", newline="").write(s)
print("verif_v469: bloque 9 (busquedas + escrituras) insertado ANTES del veredicto")
