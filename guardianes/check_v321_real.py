"""Lo que v321 protege, contra DATOS REALES en vez de un simulacro.

El guardián original monta un proyecto archivado de mentira y espera 1.750 de
ingreso. Desde v361 el ingreso ya no se calcula ahí: lo produce `project_revenue`,
que además consulta cotización (v370) y ganancias (v360/v373). Su mock se quedó
corto — pero la REGLA que defendía sigue vigente y hay que comprobarla:

    un proyecto ARCHIVADO usa su margen PROPIO, no el default del grupo,
    y aparece en la rentabilidad con su ingreso.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1", "rol": "administrator"}

from core import projects as P, finance as F               # noqa: E402

G = "cliente1"
arch = [p for p in P.list_projects(grupo=G, incluir_archivados=True)
        if str(p.get("Estado", "")) == P.ARCHIVADO]
print(f"== {len(arch)} proyectos archivados ==")
ok = True
for p in arch:
    pid = str(p.get("ID"))
    propio = str(p.get("MargenMO", "")).strip()
    r = F.project_revenue(pid, G, p)
    print(f"   {pid} {str(p.get('Nombre'))[:20]:<21} margen propio={propio or '(vacío)':<7} "
          f"modelo={str(r.get('modelo')):<10} costo=${P._num(r.get('costo')):>9,.2f} "
          f"ingreso=${P._num(r.get('ingreso')):>9,.2f}")

print("\n== los archivados ENTRAN en la rentabilidad del grupo ==")
gp = F.group_profitability(G)
filas = gp.get("rows", gp) if isinstance(gp, dict) else gp
ids = {str(f.get("id", "")) for f in filas}
faltan = [str(p.get("ID")) for p in arch if str(p.get("ID")) not in ids]
ok &= not faltan
print(f"   filas: {len(filas)} · archivados ausentes: {faltan or 'ninguno'}")

print("\n== y su margen es el PROPIO, no el default del grupo ==")
malos = []
for f in filas:
    pid = str(f.get("id", ""))
    p = next((x for x in arch if str(x.get("ID")) == pid), None)
    if not p:
        continue
    propio = str(p.get("MargenMO", "")).strip()
    if propio and abs(P._num(f.get("margen")) - P._num(propio)) > 0.01:
        # solo aplica al modelo viejo: con rubro/cotizado el % es consecuencia
        if str(f.get("modelo", "")).startswith("margen"):
            malos.append((pid, propio, f.get("margen")))
ok &= not malos
print(f"   {'✓ cada archivado con su margen' if not malos else '‼️ ' + str(malos)}")

print("\n" + ("✅ la regla de v321 se cumple con datos reales" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
