# -*- coding: utf-8 -*-
# =====================================================================
# HISTORICO - NO SE PUEDE EJECUTAR (marcado el 20/09/2026)
#
# Apunta al scratchpad temporal de la sesion 1734b676..., que ya no existe,
# y ademas opera sobre ficheros intermedios de aquella tanda que tampoco
# existen: era una transformacion de un solo uso, ya aplicada.
#
# Se conserva como RASTRO de como se hizo aquel cambio, no como herramienta.
# Arreglarle la ruta no lo haria funcionar: lo que leia ya no esta.
# =====================================================================
"""Los tres rojos de la suite de v482, clasificados uno a uno (regla v385).

Ninguno es un fallo de la app:
  · v298 CADUCADO — se le añadió a propósito la 7ª sub-pestaña del propietario;
  · v404 anclado a la FORMA de la llamada, que v482 cambió a propósito;
  · v397 tenía DOS defectos propios que solo salieron ahora, porque la demo tiene por
    primera vez una obra con pendiente.
"""
import io

D = "C:\\Users\\diego\\AppData\\Local\\Temp\\claude\\C--Users-diego\\1734b676-4bc1-41b7-b6b7-689294f44640\\scratchpad\\"

# ── v298 · CADUCADO: la lista de 6 pestañas era a mano ───────────────────────
P = D + "verif_v298.py"
s = io.open(P, encoding="utf-8").read()

V1 = '''check("las 6 pestañas de Administracion", [i for i, _ in _adm[1]],'''
# se localiza el bloque entero por su literal de 6 IDs
import re
m = re.search(r'check\("las 6 pestañas de Administracion".*?\n\s*\[[^\]]*\]\)', s, re.S)
if not m:
    raise SystemExit("v298: no encuentro el check de las 6 pestañas")
N1 = '''# ⚠️ CADUCADO en v482 y ACTUALIZADO: se añadió «📈 Cuota» (el medidor de consumo de
# la API). La afirmación era una LISTA A MANO de 6 IDs, así que cualquier pestaña nueva
# la ponía roja aunque no se hubiera perdido nada — el guardián atado a la FORMA de
# v392. Lo que de verdad protege es que el propietario **no pierda** ninguna y que las
# nuevas vayan DESPUÉS, que es como no se le reordena el menú a quien ya lo usa (v297).
_ADM_VIEJAS = ["🌐 Resumen", "🏢 Grupos", "👥 Usuarios", "📁 Proyectos", "🚆 Rieles",
               "📚 Manuales"]
_ids_adm = [i for i, _ in _adm[1]]
check("Administracion no pierde ninguna de sus pestañas",
      [x for x in _ADM_VIEJAS if x not in _ids_adm], [])
check("y lo nuevo va DESPUES (no le reordena el menu a nadie)",
      _ids_adm[:len(_ADM_VIEJAS)], _ADM_VIEJAS)
check("sin IDs duplicados", [i for i in _ids_adm if _ids_adm.count(i) > 1], [])'''
s = s[:m.start()] + N1 + s[m.end():]

m2 = re.search(r'check\("los IDs del propietario siguen siendo los 6 acordados".*?\n\s*\[[^\]]*\]\)', s, re.S)
if not m2:
    raise SystemExit("v298: no encuentro el check de los IDs")
N2 = '''# ⚠️ Lo que este chequeo protege son los DEEP-LINKS: `survey_ui` escribe
# `owner_sec = "📁 Proyectos"`, así que renombrar un ID rompería la navegación sin dar
# ningún error. Eso no depende de CUÁNTAS pestañas haya, así que se afirma sobre los
# IDs históricos, no sobre el total.
check("los IDs historicos del propietario intactos (deep-links)",
      [x for x in _ADM_VIEJAS if x not in _ids_adm], [])'''
s = s[:m2.start()] + N2 + s[m2.end():]
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v298: sobre el principio (no se pierde nada, lo nuevo va despues)")

# ── v404 · anclado a la llamada PELADA ───────────────────────────────────────
P = D + "verif_v404.py"
s = io.open(P, encoding="utf-8").read()
V = '''check("⚠️ tira el LOTE de v339 (si no, el riel nuevo no se ve en 120 s)",
      "hojas.invalidar()" in _t, True)'''
N = '''# ⚠️ CADUCADO en v482 y ACTUALIZADO: la llamada dejó de ser pelada — ahora recibe el
# TÍTULO de la hoja (`hojas.invalidar(RIELES_SHEET)`) para limpiar SOLO el libro donde
# vive, en vez de la caché de todos los clientes. La regla no cambia: el lote se tiene
# que tirar, o el riel nuevo no se ve en 120 s. Se afirma sobre la LLAMADA, no sobre su
# forma exacta, que es lo que la hizo caducar.
_inv_calls = [n for n in ast.walk(_inv) if isinstance(n, ast.Call)
              and getattr(n.func, "attr", "") == "invalidar"
              and getattr(getattr(n.func, "value", None), "id", "") == "hojas"]
check("⚠️ tira el LOTE de v339 (si no, el riel nuevo no se ve en 120 s)",
      len(_inv_calls) >= 1, True)
# ⚠️ Y `Rails` es hoja GLOBAL: si se le pasara el título de una hoja de inquilino,
# limpiaría el libro del grupo y el maestro se quedaría con el riel viejo.
check("...y dice de QUE hoja, para no limpiar el libro equivocado (v482)",
      all(c.args or c.keywords for c in _inv_calls), True)'''
if s.count(V) != 1:
    raise SystemExit("v404: ancla no unica (%d)" % s.count(V))
s = s.replace(V, N)
if "\nimport ast" not in s:
    s = s.replace("import io", "import ast\nimport io", 1)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v404: sobre la llamada, no sobre su forma")

# ── v397 · dos defectos PROPIOS que la demo destapó ──────────────────────────
P = D + "verif_v397.py"
s = io.open(P, encoding="utf-8").read()

V3 = '''if _m:
    check("las ARCHIVADAS con pendiente están en el mapa",
          bool(_arch & set(_m)), True)'''
N3 = '''# ⚠️ Esta afirmación exigía que la DEMO tuviera una obra archivada con pendiente, o
# sea que dependía de la forma de los datos de producción: el día que la demo tuvo una
# obra viva con pendiente y ninguna archivada, salió roja sin que nada estuviera mal.
# La regla YA está probada arriba con un caso CONSTRUIDO y validada contra roturas, así
# que aquí solo se comprueba si de verdad hay una archivada que comprobar.
if _m and _arch:
    check("las ARCHIVADAS con pendiente están en el mapa",
          bool(_arch & set(_m)), True)
elif _m:
    print("         (no hay obras archivadas ahora mismo: lo afirma el caso construido)")'''
if s.count(V3) != 1:
    raise SystemExit("v397: ancla archivadas no unica (%d)" % s.count(V3))
s = s.replace(V3, N3)

V4 = '''_esperado = sorted(
    (str(p.get("Nombre", "")), I.pendiente_de_facturar(str(p.get("ID", "")), G, p))
    for p in P.list_projects(G, incluir_archivados=True)
    if I.pendiente_de_facturar(str(p.get("ID", "")), G, p) > 0)'''
N4 = '''# ⚠️ La columna es `Name`, no `Nombre`: **v468 renombró las columnas al inglés** y este
# guardián se quedó con el nombre viejo, así que comparaba contra cadenas VACÍAS. No
# saltó antes porque la demo no tenía ninguna obra con pendiente. Es la cuarta vez de
# esa clase (v475 encontró tres): algo migrado en el código y olvidado en lo que lo
# comprueba.
_esperado = sorted(
    (str(p.get("Name", "")), I.pendiente_de_facturar(str(p.get("ID", "")), G, p))
    for p in P.list_projects(G, incluir_archivados=True)
    if I.pendiente_de_facturar(str(p.get("ID", "")), G, p) > 0)'''
if s.count(V4) != 1:
    raise SystemExit("v397: ancla Nombre no unica (%d)" % s.count(V4))
s = s.replace(V4, N4)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v397: columna Name (v468) + la archivada solo si la hay")
