"""¿Los 6 ceros de la cartera son obras SIN horas, o un hueco más?

En pantalla salen 12 tarjetas con: 6h, 0h, 117h, 44h, 434h, 176h, 0h, 726h, 0h×4.
Aquí se calcula lo mismo obra a obra y se mira si los ceros tienen fichajes.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "dacox", "grupo": "", "rol": "owner"}

from core import projects as P, timeclock as T             # noqa: E402

proys = P.list_projects(incluir_archivados=False)          # los 12 de la cartera
fich = P._fichajes_visibles(None)
print(f"== {len(proys)} obras en la cartera · {len(fich)} fichajes visibles ==\n")

con, sin = [], []
for p in proys:
    # ⚠️ v480: `Nombre`/`Grupo` son de ANTES de v468. Con la clave vieja llegaba el
    # nombre vacío y `es_del_proyecto` casaba con cualquier jornada general, así que
    # este chequeo acusaba a obras inocentes. Se mantuvo verde solo mientras el libro
    # de la demo estuvo sin obras.
    pid, nom = str(p.get("ID", "")), str(p.get("Name", ""))
    h = P.project_hours(nom, p.get("Group"), pid=pid)
    n = sum(1 for r in fich if T.es_del_proyecto(r, pid, nom))
    (con if h > 0 else sin).append((pid, nom, h, n))

print("-- con horas --")
for pid, nom, h, n in con:
    print(f"   {pid}  {nom[:34]:<35} {h:>8.1f} h   ({n} fichajes)")
print(f"\n-- en 0 --")
for pid, nom, h, n in sin:
    marca = "  ← ‼️ TIENE fichajes y marca 0" if n else "  ✓ no tiene fichajes"
    print(f"   {pid}  {nom[:34]:<35} {h:>8.1f} h   ({n} fichajes){marca}")

malos = [x for x in sin if x[3] > 0]
print(f"\n   {len(con)} con horas · {len(sin)} en cero, de los cuales "
      f"{len(malos)} con fichajes sin contar")
print("\n" + ("✅ los ceros son obras sin fichajes: la cartera dice la verdad"
              if not malos else "⚠️ hay ceros con fichajes detrás"))
sys.exit(0 if not malos else 1)
