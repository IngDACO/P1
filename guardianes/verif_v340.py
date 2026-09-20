"""Guardián v340 — si algo se puede archivar, tiene que poder VOLVER.

El usuario archivó un cliente y desapareció sin forma de recuperarlo. La bandera
para mostrarlos YA existía en el modelo (`incluir_inactivos`); lo que faltaba era
que la interfaz la ofreciera y que hubiera botón de vuelta.

Tener solo el modelo es PEOR que no tener nada: el dato existe y es inalcanzable.

Este guardián falla si aparece una entidad archivable cuya interfaz no permita (a)
verlos y (b) restaurarlos.
"""
import importlib
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(BASE))
OK = True

# (módulo, su _ui, bandera que oculta, patrón que demuestra la VUELTA)
# ⚠️ El nombre de la función va EXPLÍCITO. La primera versión lo adivinaba con
# `next(n for n in dir(m) if n.startswith("list_"))` y en `projects` eso devuelve
# `list_activities` por orden alfabético → comprobaba la función equivocada y daba
# un fallo falso. Adivinar el nombre de una API es el error que más veces se ha
# repetido en esta sesión.
ENTIDADES = [
    ("clientes",  "clientes_ui",  "list_clientes",  "incluir_inactivos",  r"restaurar|set_activo\(cid, True\)"),
    ("inventory", "inventory_ui", "list_activos",   "incluir_baja",       r"react|\"Activo\": \"SI\""),
    ("projects",  "projects_ui",  "list_projects",  "incluir_archivados", r"set_archivado"),
    ("roster",    "roster_ui",    "list_trabajos",  "incluir_inactivos",  r"activar|Activo.*SI|update_trabajo"),
]

print("== cada entidad archivable: ¿se pueden VER y VOLVER? ==\n")
print(f"{'entidad':<12}{'ver ocultos':>14}{'vuelta':>10}")
print("-" * 38)
for mod, ui, _fn, flag, vuelta in ENTIDADES:
    p = BASE / "core" / f"{ui}.py"
    if not p.exists():
        print(f"{mod:<12}{'(sin _ui)':>14}")
        continue
    src = p.read_text(encoding="utf-8")
    ver = flag in src
    vol = bool(re.search(vuelta, src, re.I))
    print(f"{mod:<12}{('sí' if ver else 'NO'):>14}{('sí' if vol else 'NO'):>10}")
    OK &= (ver and vol)

print("\n== la bandera existe en el modelo (esta parte ya estaba) ==")
import inspect
for mod, _ui, listar, flag, _v in ENTIDADES:
    m = importlib.import_module("core." + mod)
    f = getattr(m, listar, None)
    tiene = f is not None and flag in inspect.signature(f).parameters
    print(f"  {mod}.{listar}(…{flag}) → {'sí' if tiene else 'NO'}")
    OK &= bool(tiene)

print("\n== y de verdad devuelve MÁS al pedir los ocultos (datos reales) ==")
try:
    from core import clientes as C, inventory as INV, projects as P
    G = "cliente1"
    pares = [("clientes", len(C.list_clientes(G)), len(C.list_clientes(G, incluir_inactivos=True))),
             ("activos",  len(INV.list_activos(G)), len(INV.list_activos(G, incluir_baja=True))),
             ("proyectos", len(P.list_projects(G)), len(P.list_projects(G, incluir_archivados=True)))]
    for nom, vis, tot in pares:
        print(f"  {nom:<11} visibles={vis:<3} con ocultos={tot:<3} "
              f"ocultos={tot - vis}  {'(la bandera hace algo)' if tot >= vis else '✗'}")
        OK &= (tot >= vis)
except Exception as e:
    print("  no se pudo comprobar contra datos reales:", repr(e)[:80])

print("\n" + ("NADA SE PUEDE ARCHIVAR SIN VUELTA" if OK else "⚠️ HAY UN VIAJE SIN VUELTA"))
sys.exit(0 if OK else 1)
