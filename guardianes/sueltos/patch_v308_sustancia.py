# -*- coding: utf-8 -*-
"""v308 CADUCADO por v480, y NO se relaja: se ata a la regla, no a su forma.

Los tres rojos eran proxies de forma:
  · «0 `next(...)` en la funcion» — el fallo de v306 no era usar `next`, era que el
    NOMBRE que se escribe en la hoja saliera de la ETIQUETA del desplegable. v480 usa
    `next(iter(idmap))` para el TEXTO DEL BOTON y coge el nombre de `_nom_de`, o sea
    que cumple la regla y rompe el proxy.
  · «los 3 nombres salen de `_nom_de`» — un numero escrito a mano en paralelo con la
    verdad; con un cuarto sitio de fichaje se queda viejo (v433/v434).
  · la lista de keys de la columna del Proyecto, tambien a mano.

Pasan a afirmar lo que de verdad protegian, y **mas fuerte que antes**: que CADA
llamada a `fichar_proyecto` tome su nombre de `_nom_de`, sea una o sean cuatro.
"""
import ast
import io

P = "verif_v308.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''# Ya NO puede quedar ningun `next(k for k, v in ...)` sacando la clave (=etiqueta)
_nexts = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Call)
          and getattr(n.func, "id", "") == "next"]
check("0 `next(...)` sacando la etiqueta del idmap", _nexts, [])
# y las 3 asignaciones de nombre salen de `_nom_de`
_desde_nomde = [n.lineno for n in ast.walk(_fn) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") == "get"
                and getattr(getattr(n.func, "value", None), "id", "") == "_nom_de"]
check("los 3 nombres salen de `_nom_de`", len(_desde_nomde), 3)
'''

NUEVO = '''# ⚠️ v480 · Esto afirmaba la FORMA («0 `next(...)`, 3 `_nom_de.get`») y caducó en
# cuanto apareció un cuarto sitio donde fichar. El fallo de v306 no era usar `next`:
# era que el NOMBRE escrito en la hoja saliera de la ETIQUETA del desplegable (que
# lleva el ID detrás con homónimos), dejando fichajes con un nombre inventado. Ahora
# se afirma ESO, y sirve para una llamada o para diez.
_vars_nom = {t.id for n in ast.walk(_fn) if isinstance(n, ast.Assign)
             for t in n.targets if isinstance(t, ast.Name)
             if isinstance(n.value, ast.Call)
             and getattr(n.value.func, "attr", "") == "get"
             and getattr(getattr(n.value.func, "value", None), "id", "") == "_nom_de"}
_fichadas = [n for n in ast.walk(_fn) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "fichar_proyecto"]
check("hay al menos un sitio donde se ficha", len(_fichadas) >= 1, True)
_mal = [n.lineno for n in _fichadas
        if not (len(n.args) >= 2 and isinstance(n.args[1], ast.Name)
                and n.args[1].id in _vars_nom)]
check("TODA llamada a fichar_proyecto toma el nombre de `_nom_de`", _mal, [])
# ⚠️ Sonda validada contra el fallo de v306 reconstruido: si no ve ESE caso, su cero
# no vale nada (trampa nº12).
_p = ast.parse("def f():\\n _x = next(iter(idmap))\\n"
               " timeclock.fichar_proyecto(nombre, _x, g, u, pid)\\n")
_pf = [n for n in ast.walk(_p) if isinstance(n, ast.FunctionDef)][0]
_pv = {t.id for n in ast.walk(_pf) if isinstance(n, ast.Assign)
       for t in n.targets if isinstance(t, ast.Name)
       if isinstance(n.value, ast.Call)
       and getattr(n.value.func, "attr", "") == "get"
       and getattr(getattr(n.value.func, "value", None), "id", "") == "_nom_de"}
_pm = [n.lineno for n in ast.walk(_pf) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "fichar_proyecto"
       and not (len(n.args) >= 2 and isinstance(n.args[1], ast.Name)
                and n.args[1].id in _pv)]
check("la sonda VE el fallo de v306 reconstruido (control)", bool(_pm), True)
'''

V2 = '''check("el Proyecto se queda con LOS SUYOS", _withs.get("_prj_ctx"),
      ["tc_prj_in", "tc_prj_out", "tc_prj_sel", "tc_switch", "tc_switch_btn"])
'''
N2 = '''# ⚠️ v480 · Era una lista a mano y caducó al añadir `tc_prj_solo`. Lo que protege es
# que la reindentación no haya movido un widget de columna, y eso se DERIVA: en la
# columna del Proyecto solo puede haber keys suyas, y ninguna puede estar en las dos.
_kp = _withs.get("_prj_ctx") or []
_kj = _withs.get("col_jor") or []
check("el Proyecto solo tiene keys suyas",
      [k for k in _kp if not (k.startswith("tc_prj") or k.startswith("tc_switch"))], [])
check("y ninguna key está en las dos columnas", sorted(set(_kp) & set(_kj)), [])
check("la columna del Proyecto no se quedó vacía", len(_kp) >= 4, True)
'''
for etq, v in (("bloque 1", VIEJO), ("lista de keys", V2)):
    if s.count(v) != 1:
        raise SystemExit("%s no unico: %d" % (etq, s.count(v)))
s = s.replace(VIEJO, NUEVO).replace(V2, N2)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v308.py: atado a la regla (el nombre sale de _nom_de), no a su forma")
