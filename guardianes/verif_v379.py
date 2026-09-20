"""GUARDIÁN v379 — FASE 2: el propietario ve todos los libros.

Desde v377 cada cliente vive en su libro y el maestro está vacío, así que el
propietario veía **0 proyectos**. Ahora recorre los libros.

⚠️ Lo que más miedo da NO es que salga 0: es que salga el DOBLE. Si se lee una vez
por GRUPO en vez de una vez por LIBRO, los grupos que comparten el maestro traen
sus filas repetidas y el consolidado infla sin avisar.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, auth, tenant, admin_digest as AD   # noqa: E402

ok = True


def como(rol, grupo=""):
    st.session_state["auth"] = {"usuario": "u", "grupo": grupo, "rol": rol}
    st.session_state.pop("_tenant_grupo_activo", None)


print("== los libros que hay ==")
libros = auth.grupos_por_libro()
for g, sid in libros:
    print(f"   {g:<14} → {'maestro' if not sid else '…' + sid[-6:]}")
print(f"   {len(libros)} libro(s) distinto(s)")

print("\n== 1. ⚠️ EL PROPIETARIO VE LOS PROYECTOS (era 0 desde v377) ==")
como("owner")
todos = P.list_projects(incluir_archivados=True)
# CADUCADO en v450 y REANCLADO, no relajado: el numero estaba fijo en 16 y la demo
# paso a 18, asi que el guardian se puso rojo sin que nada estuviera mal. Un ancla
# sobre un CONTEO de datos caduca cada vez que alguien crea un proyecto (trampa
# n16). Lo que la regla protege es la CONDUCTA: el propietario ve ALGO (era 0 desde
# v377) y ve LO MISMO que el admin de ese grupo. El numero se DERIVA.
N = len(todos)
print(f"   con la demo tal cual: {N} proyecto(s)")

# ⚠️ v474 · Antes, con la demo vacía (v456), «el propietario ve 0» no distinguía el
# fallo de v377 —leer el libro equivocado— de la realidad, así que el guardián salía
# SIN DATOS y su afirmación llevaba versiones sin comprobarse. Ahora se CONSTRUYE el
# caso: dos libros con filas distintas. El punto de sustitución es `_records`, no
# `_registros_visibles`, para que el recorrido de libros, el `como_grupo` y el dedup
# —lo que v379 protege— se sigan ejercitando de verdad.
print("\n== 1b. el mismo escenario, CONSTRUIDO (dos libros con filas distintas) ==")
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
print(f"\n   (con datos reales serían {N}; el caso construido ya afirmó la conducta)")

print("\n== 2. ⚠️ y NO duplicados (una lectura por LIBRO, no por grupo) ==")
ids = [str(p.get("ID", "")) for p in todos]
dup = len(ids) - len(set(ids))
ok &= dup == 0
print(f"   {'✓ sin duplicar' if dup == 0 else f'‼️ {dup} filas repetidas'} "
      f"({len(set(ids))} IDs distintos de {len(ids)} filas)")

print("\n== 3. el propietario filtrando por UN cliente ==")
uno = P.list_projects(grupo="cliente1", incluir_archivados=True)
bien = len(uno) == N
ok &= bien
print(f"   {'✓' if bien else '‼️'} list_projects(grupo='cliente1') → {len(uno)}")

print("\n== 4. abrir un proyecto por ID desde el panel del propietario ==")
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

print("\n== 5. el resumen multi-grupo ==")
try:
    d = AD.owner_digest()
    print(f"   filas: {len(d)}")
    for f in d:
        print(f"      {f['grupo']:<12} activos={f['activos']:<3} avance={f['avance']}% "
              f"retrasos={f['retrasos']} alarmas={f['alarmas']}")
    # ⚠️ informativo: con la demo vacía no hay activos que contar, y exigirlo sería
    # atar el guardián a que existan datos (que es lo que lo dejó SIN DATOS).
    bien = bool(d) and any(f["activos"] > 0 for f in d)
    print(f"   {'✓ con datos reales' if bien else '(demo vacía: informativo)'}")
except Exception as e:
    ok = False
    print(f"   ‼️ {type(e).__name__}: {e}")

print("\n== 6. ⚠️ nadie más cambia de comportamiento ==")
como("administrator", "cliente1")
a = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
ok &= a == N
print(f"   {'✓' if a == N else '‼️'} admin de cliente1 → {a} proyectos (su libro, como siempre)")
como("field", "cliente1")
c = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
ok &= c == N
print(f"   {'✓' if c == N else '‼️'} campo de cliente1 → {c}")

print("\n== 7. el ámbito se DESHACE al salir (si no, contamina lo siguiente) ==")
como("owner")
antes = tenant.grupo_activo()
with tenant.como_grupo("cliente1"):
    dentro = tenant.grupo_activo()
despues = tenant.grupo_activo()
bien = antes == "" and dentro == "cliente1" and despues == ""
ok &= bien
print(f"   {'✓' if bien else '‼️'} fuera={antes!r} · dentro={dentro!r} · al salir={despues!r}")
# anidado
with tenant.como_grupo("a"):
    with tenant.como_grupo("b"):
        _b = tenant.grupo_activo()
    _a = tenant.grupo_activo()
bien2 = _b == "b" and _a == "a"
ok &= bien2
print(f"   {'✓' if bien2 else '‼️'} anidado: dentro={_b!r}, al salir del interior={_a!r}")

print("\n== 8. la fuga de v378 sigue cerrada ==")
como("owner")
x = len(P.list_projects(incluir_archivados=True))
como("administrator", "cliente1")
y = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
bien = x == N and y == N
ok &= bien
print(f"   {'✓' if bien else '‼️'} propietario {x} · admin {y} (sin limpiar caché entre medias)")

print("\n" + ("✅ v379 OK: el propietario ve todos los libros, sin duplicar, y nadie "
              "más cambia" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
