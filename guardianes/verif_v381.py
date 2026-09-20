"""GUARDIÁN v381 — la cartera del propietario, POR LA FUNCIÓN QUE USA LA PANTALLA.

⚠️ v380 arregló `project_hours_bulk` dando por hecho que era la que alimentaba las
tarjetas. No lo era: `render_owner_projects` llama a `project_hours()` UNA VEZ POR
OBRA, así que en pantalla seguían saliendo `0h` en las 12 tarjetas mientras el test
daba ✓. Este guardián replica lo que hace la pantalla, no lo que yo creía.
"""
import inspect
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, alerts                     # noqa: E402

ok = True


def como(rol, g=""):
    st.session_state["auth"] = {"usuario": "u", "grupo": g, "rol": rol}
    st.session_state.pop("_tenant_grupo_activo", None)


# ── 1) el CAMINO REAL de la pantalla ────────────────────────────────
print("== 1. ¿qué función usa la cartera del propietario? ==")
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py").read_text(encoding="utf-8")
fn = src[src.index("def render_owner_projects"):]
fn = fn[:fn.index("\ndef ", 10)]
usa_bulk = "project_hours_bulk" in fn
usa_uno = "project_hours(" in fn
print(f"   project_hours_bulk: {usa_bulk}   ·   project_hours(): {usa_uno}")
print("   → el guardián prueba la que de verdad se llama")

# ── 2) replicando la pantalla: horas obra a obra ────────────────────
print("\n== 2. horas por obra, como las calcula la cartera ==")
como("administrator", "cliente1")
proys = P.list_projects(grupo="cliente1", incluir_archivados=True)
adm = {str(p.get("ID")): P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                         pid=str(p.get("ID", ""))) for p in proys}
como("owner")
proys_o = P.list_projects(incluir_archivados=True)
dueno = {str(p.get("ID")): P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                           pid=str(p.get("ID", ""))) for p in proys_o}
con_horas_adm = {k: v for k, v in adm.items() if v > 0}
con_horas_due = {k: v for k, v in dueno.items() if v > 0}
print(f"   admin       → {len(con_horas_adm)} obras con horas, "
      f"{sum(con_horas_adm.values()):.1f} h en total")
print(f"   propietario → {len(con_horas_due)} obras con horas, "
      f"{sum(con_horas_due.values()):.1f} h en total")
bien = (len(con_horas_due) == len(con_horas_adm)
        and abs(sum(con_horas_due.values()) - sum(con_horas_adm.values())) < 0.05)
ok &= bien
print(f"   {'✓ coinciden' if bien else '‼️ el propietario sigue viendo 0 en pantalla'}")

# ── 3) alarmas ──────────────────────────────────────────────────────
print("\n== 3. alarmas ==")
como("administrator", "cliente1")
a1 = sum(alerts.open_counts_all().values())
como("owner")
a2 = sum(alerts.open_counts_all().values())
ok &= a1 == a2
print(f"   {'✓' if a1 == a2 else '‼️'} admin={a1} · propietario={a2}")

# ── 4) el recuento previo a BORRAR ──────────────────────────────────
print("\n== 4. ⚠️ lo que se enseña antes de un borrado irreversible ==")
# ⚠️ Caso CONSTRUIDO (v477): antes iba fijado a `PRJ-0007`, que dejo de existir al
# vaciarse la demo (v456) — y con un pid inexistente `datos_asociados` no puede
# resolver el grupo y cae a la sesion, asi que la diferencia que salia NO era el fallo
# de v381 sino el ancla caducada. Ademas el caso trae datos que CONTAR: comparar dos
# ceros no distingue una lectura buena de una rota.
_FILA_Z = [{"ID": "PRJ-Z1", "Group": "cliente1", "Name": "Obra Z", "Status": "En progreso"}]
_GASTOS_Z = [{"ProjectID": "PRJ-Z1"}, {"ProjectID": "PRJ-Z1"}, {"ProjectID": "OTRO"}]
_FICH_Z = [{"ProjectID": "PRJ-Z1", "Project": "Obra Z"}]
_rec_z, _fic_z = P._records, P._fichaje_records
P._records = lambda t=None: (_FILA_Z if t == P.PROJECTS_SHEET
                             else _GASTOS_Z if t == "Gastos" else [])
P._fichaje_records = lambda: _FICH_Z
try:
    como("administrator", "cliente1")
    d1 = P.datos_asociados("PRJ-Z1")
    como("owner")
    d2 = P.datos_asociados("PRJ-Z1")
finally:
    P._records, P._fichaje_records = _rec_z, _fic_z
# sin datos que contar, comparar los dos recuentos no distinguiria nada
if not any(d1.values()):
    ok = False
    print("   ‼️ el caso construido no cuenta nada: la comparacion no probaria nada")
print(f"   admin       → {d1}")
print(f"   propietario → {d2}")
ok &= d1 == d2
print(f"   {'✓ el mismo recuento' if d1 == d2 else '‼️ al propietario le saldría 0 y borraría a ciegas'}")

print("\n" + ("✅ v381 OK: la cartera del propietario cuadra por el camino que usa la "
              "pantalla" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
