# -*- coding: utf-8 -*-
"""v397 deja de depender de que la demo tenga obras con pendiente.

Salia «SIN DATOS» desde que v456 vacio la demo, o sea que sus afirmaciones llevaban
versiones sin comprobarse. Se construye el caso —ejercitando la funcion REAL, que es
lo unico que importa— y **se valida contra tres implementaciones rotas** antes de
creerse su verde: sin eso, un caso construido es justo el «OK en vacio» que el
mecanismo de SIN DATOS existia para no fingir.
"""
import ast
import io

P = "verif_v397.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''print("== 1) el mapa, contra la hoja REAL ==")
_m = I.pendiente_por_proyecto(G)
print(f"         {len(_m)} obras con pendiente · {sum(_m.values()):,.2f}")
# ⚠️ v456: la demo se vació, así que este chequeo ya no tiene DATOS que mirar.
# Sale con código 2 (SIN DATOS): ni verde —sería un OK que no comprobó nada,
# trampa nº1— ni rojo, porque no hay nada roto. El runner lo lista aparte y
# avisa de que esa afirmación dejó de comprobarse.
if not _m:
    print("⚠️ no hay obras con pendiente de facturar: nada que comprobar")
    sys.exit(2)
'''

NUEVO = '''print("== 1) el mapa, sobre un caso CONSTRUIDO ==")
# ⚠️ v474: antes esto leia la demo y salia «SIN DATOS» desde que v456 la vacio — las
# afirmaciones de abajo llevaban versiones sin comprobarse. Ahora el caso se construye
# y la funcion que se ejercita sigue siendo la REAL: solo se sustituyen sus dos
# fuentes (`list_projects` y `pendiente_de_facturar`), que es lo que la demo aportaba.
_FIX = [
    {"ID": "PRJ-T-1", "Nombre": "Obra con pendiente", "Estado": "En progreso"},
    {"ID": "PRJ-T-2", "Nombre": "Obra ya facturada", "Estado": "En progreso"},
    {"ID": "PRJ-T-3", "Nombre": "Obra archivada", "Estado": "Archivado"},
]
_PEND = {"PRJ-T-1": 1200.0, "PRJ-T-2": 0.0, "PRJ-T-3": 340.5}
_lp_orig, _pf_orig = P.list_projects, I.pendiente_de_facturar
P.list_projects = lambda grupo=None, incluir_archivados=False, **k: (
    _FIX if incluir_archivados else [x for x in _FIX if x["Estado"] != "Archivado"])
I.pendiente_de_facturar = lambda pid, grupo="", p=None: _PEND.get(str(pid), 0.0)
try:
    _m = I.pendiente_por_proyecto(G)
    print(f"         {len(_m)} obras con pendiente · {sum(_m.values()):,.2f}")
    check("indexado por ID, no por nombre (v306)",
          sorted(_m), ["PRJ-T-1", "PRJ-T-3"])
    check("la que no debe nada NO entra", "PRJ-T-2" in _m, False)
    check("la ARCHIVADA con pendiente SI entra (v369)", _m.get("PRJ-T-3"), 340.5)
    check("y respeta incluir_archivados=False",
          sorted(I.pendiente_por_proyecto(G, incluir_archivados=False)), ["PRJ-T-1"])

    # ⚠️ La prueba, validada contra roturas: si no cazara ninguna, su verde no diria
    # nada (trampa nº12). Se comprueba que el caso construido DISTINGUE cada fallo.
    print("\\n   ¿el caso construido CAZA una agregacion rota?")
    for _nom, _roto in (
            ("indexa por NOMBRE (v306)",
             lambda g=None, incluir_archivados=True, **k: {
                 x["Nombre"]: _PEND[x["ID"]] for x in _FIX if _PEND[x["ID"]] > 0}),
            ("cuela las que no deben nada",
             lambda g=None, incluir_archivados=True, **k: {
                 x["ID"]: _PEND[x["ID"]] for x in _FIX}),
            ("se deja fuera las ARCHIVADAS (v369)",
             lambda g=None, incluir_archivados=True, **k: {
                 x["ID"]: _PEND[x["ID"]] for x in _FIX
                 if _PEND[x["ID"]] > 0 and x["Estado"] != "Archivado"})):
        _r = _roto()
        _caza = not (sorted(_r) == ["PRJ-T-1", "PRJ-T-3"]
                     and "PRJ-T-2" not in _r and _r.get("PRJ-T-3") == 340.5)
        check("   caza: %s" % _nom, _caza, True)
finally:
    P.list_projects, I.pendiente_de_facturar = _lp_orig, _pf_orig

print("\\n== 1b) y con la hoja REAL (informativo, no afirma si esta vacia) ==")
_m = I.pendiente_por_proyecto(G)
print(f"         {len(_m)} obras con pendiente · {sum(_m.values()):,.2f}")
if not _m:
    print("         (demo vacía: lo de arriba ya lo afirmo el caso construido)")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# los chequeos que seguian dependiendo de datos reales pasan a ser condicionales
VIEJO2 = '''check("cada obra cuadra con `pendiente_de_facturar`", _dif, [])
'''
NUEVO2 = '''if _m:
    check("cada obra cuadra con `pendiente_de_facturar`", _dif, [])
'''
if s.count(VIEJO2) != 1:
    raise SystemExit("ancla 2 no unica: %d" % s.count(VIEJO2))
s = s.replace(VIEJO2, NUEVO2)

VIEJO3 = '''check("las ARCHIVADAS con pendiente están en el mapa",
      bool(_arch & set(_m)), True)
'''
NUEVO3 = '''if _m:
    check("las ARCHIVADAS con pendiente están en el mapa",
          bool(_arch & set(_m)), True)
'''
if s.count(VIEJO3) != 1:
    raise SystemExit("ancla 3 no unica: %d" % s.count(VIEJO3))
s = s.replace(VIEJO3, NUEVO3)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v397.py: caso construido + validado contra 3 roturas")
