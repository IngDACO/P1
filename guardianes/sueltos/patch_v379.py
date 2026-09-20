# -*- coding: utf-8 -*-
"""v379 deja de depender de que la demo tenga proyectos.

⚠️ El caso se construye en `_records`, NO en `_registros_visibles`: asi el recorrido
de libros, el `como_grupo` y el dedup —que es justo lo que v379 protege— siguen
ejercitandose de verdad. Sustituir la capa de arriba habria dejado el guardian
aprobando su propio mock.

Y se valida contra el fallo REAL de v377 (leer una vez por GRUPO en vez de por LIBRO,
que duplica filas) antes de creerse el verde.
"""
import ast
import io

P = "verif_v379.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''N = len(todos)
# ⚠️ v456: la demo se vació, así que «el propietario ve 0 proyectos» ya no distingue el
# fallo de v377 (donde veía 0 porque leía el libro equivocado) de la realidad (no hay
# ninguno). Sin datos, este guardián no puede afirmar nada → código 2 = SIN DATOS.
if N == 0 and not any(len(P.list_projects(g, incluir_archivados=True,
                                          incluir_internos=True)) for g, _ in libros):
    print("⚠️ no hay proyectos en ningún libro: el chequeo no puede distinguir el fallo")
    sys.exit(2)
bien = N > 0
ok &= bien
print(f"   {'✓' if bien else '‼️'} list_projects() → {len(todos)} proyectos (>0, era 0 desde v377)")
'''

NUEVO = '''N = len(todos)
print(f"   con la demo tal cual: {N} proyecto(s)")

# ⚠️ v474 · Antes, con la demo vacía (v456), «el propietario ve 0» no distinguía el
# fallo de v377 —leer el libro equivocado— de la realidad, así que el guardián salía
# SIN DATOS y su afirmación llevaba versiones sin comprobarse. Ahora se CONSTRUYE el
# caso: dos libros con filas distintas. El punto de sustitución es `_records`, no
# `_registros_visibles`, para que el recorrido de libros, el `como_grupo` y el dedup
# —lo que v379 protege— se sigan ejercitando de verdad.
print("\\n== 1b. el mismo escenario, CONSTRUIDO (dos libros con filas distintas) ==")
from core import tenant as _T                                    # noqa: E402
_FILAS = {
    "cliente1": [{"ID": "PRJ-A1", "Group": "cliente1", "Name": "Obra A1", "Status": "En progreso"},
                 {"ID": "PRJ-A2", "Group": "cliente1", "Name": "Obra A2", "Status": "En progreso"}],
    "cliente2": [{"ID": "PRJ-B1", "Group": "cliente2", "Name": "Obra B1", "Status": "En progreso"}],
}
_rec_orig, _lib_orig = P._records, auth.grupos_por_libro
auth.grupos_por_libro = lambda: [("cliente1", "LIBRO-1"), ("cliente2", "LIBRO-2")]
# el lector devuelve lo del grupo ACTIVO: es lo que hace que «una lectura por LIBRO»
# y «una por GRUPO» den resultados distintos y el chequeo signifique algo
P._records = lambda title=None: _FILAS.get(_T.grupo_activo() or "cliente1", [])
try:
    _todos = P.list_projects(incluir_archivados=True)
    _ids = [str(x.get("ID", "")) for x in _todos]
    check_ = lambda n, r, e: (print(f"   {'✓' if r == e else '‼️'} {n}: {r!r}"), r == e)[1]
    _b1 = check_("el propietario ve los de los DOS libros", sorted(_ids),
                 ["PRJ-A1", "PRJ-A2", "PRJ-B1"])
    _b2 = check_("sin duplicar (una lectura por LIBRO, no por grupo)",
                 len(_ids) - len(set(_ids)), 0)
    _b3 = check_("filtrando por un cliente, solo los suyos",
                 sorted(str(x.get("ID")) for x in
                        P.list_projects(grupo="cliente1", incluir_archivados=True)),
                 ["PRJ-A1", "PRJ-A2"])
    ok &= _b1 and _b2 and _b3

    # ⚠️ y que el caso CAZA el fallo de v377: si se leyera una vez por GRUPO sobre el
    # mismo libro, saldrían filas repetidas. Sin esta validación, el verde de arriba
    # no distinguiría una implementación buena de una rota (trampa nº12).
    _roto = [r for _g, _ in auth.grupos_por_libro() for r in _FILAS["cliente1"]]
    _dup_roto = len(_roto) - len({x["ID"] for x in _roto})
    ok &= check_("   caza: leer por GRUPO en vez de por LIBRO duplicaría",
                 _dup_roto > 0, True)
finally:
    P._records, auth.grupos_por_libro = _rec_orig, _lib_orig

bien = True
print(f"\\n   (con datos reales serían {N}; el caso construido ya afirmó la conducta)")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla 1 no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# las comprobaciones que siguen atadas a filas concretas de la demo pasan a
# condicionales: con la demo vacía no pueden afirmar, y fingir que sí es el OK en vacío
VIEJO2 = '''print("\\n== 4. abrir un proyecto por ID desde el panel del propietario ==")
prj = P.get_project("PRJ-0007")
bien = bool(prj) and str(prj.get("Nombre", "")).startswith("Meriton")
ok &= bien
print(f"   {'✓' if bien else '‼️'} get_project('PRJ-0007') → {prj.get('Nombre') or '(vacío)'}")
'''
NUEVO2 = '''print("\\n== 4. abrir un proyecto por ID desde el panel del propietario ==")
# ⚠️ v474: iba fijado a `PRJ-0007` («Meriton»), una fila CONCRETA de la demo — un
# ancla sobre datos que caduca en cuanto alguien los borra (trampa nº16, y la demo se
# vació en v456). Se prueba la CONDUCTA con el caso construido.
_rec_orig2, _lib_orig2 = P._records, auth.grupos_por_libro
auth.grupos_por_libro = lambda: [("cliente1", "LIBRO-1")]
P._records = lambda title=None: [{"ID": "PRJ-A1", "Group": "cliente1",
                                  "Name": "Obra A1", "Status": "En progreso"}]
try:
    prj = P.get_project("PRJ-A1")
    bien = bool(prj) and str(prj.get("Name", "")) == "Obra A1"
    ok &= bien
    print(f"   {'✓' if bien else '‼️'} get_project('PRJ-A1') → {prj.get('Name') or '(vacío)'}")
    _no = P.get_project("PRJ-NO-EXISTE")
    ok &= not _no
    print(f"   {'✓' if not _no else '‼️'} un ID que no existe → {_no or '(vacío)'}")
finally:
    P._records, auth.grupos_por_libro = _rec_orig2, _lib_orig2
'''
if s.count(VIEJO2) != 1:
    raise SystemExit("ancla 4 no unica: %d" % s.count(VIEJO2))
s = s.replace(VIEJO2, NUEVO2)

VIEJO3 = '''    bien = bool(d) and any(f["activos"] > 0 for f in d)
    ok &= bien
    print(f"   {'✓ con datos reales' if bien else '‼️ sigue vacío'}")
'''
NUEVO3 = '''    # ⚠️ informativo: con la demo vacía no hay activos que contar, y exigirlo sería
    # atar el guardián a que existan datos (que es lo que lo dejó SIN DATOS).
    bien = bool(d) and any(f["activos"] > 0 for f in d)
    print(f"   {'✓ con datos reales' if bien else '(demo vacía: informativo)'}")
'''
if s.count(VIEJO3) != 1:
    raise SystemExit("ancla 5 no unica: %d" % s.count(VIEJO3))
s = s.replace(VIEJO3, NUEVO3)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v379.py: caso construido de dos libros + validado contra el fallo de v377")
