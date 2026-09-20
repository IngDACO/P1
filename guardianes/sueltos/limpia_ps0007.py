"""Borra el PS-0007 que creé por error y monta el escenario en una obra libre.

Lo que pasó: PRJ-0009 YA tenía Pre-Start hoy (PS-0006) con `asfgjjd` entre los
asistentes, así que mi `submit` creó un SEGUNDO documento del mismo día y la misma
obra. Nada lo impide — es el hueco que v403 documenta pero no cierra.

En seco por defecto; `--apply` escribe.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import clock, prestart as PS, projects as P             # noqa: E402

G = "cliente1"
APLICAR = "--apply" in sys.argv
HOY = clock.today(G)

print("== pre-starts de HOY ==")
for r in PS._records():
    from core.num import parse_date as _pd
    if _pd(r.get("Fecha")) == HOY:
        d = PS.leer(r)
        print(f"  {r.get('ID')} · {r.get('ProyectoID')} · facilitador "
              f"{r.get('Facilitador')} · asistentes {d.get('asistentes')}")

print("\n== obras SIN pre-start hoy (para montar el caso) ==")
libres = [p for p in P.list_projects(G)
          if str(p.get("Estado")) not in ("Archivado", "Cancelado", "Completado")
          and not PS.hecho_hoy(str(p.get("ID")), G)]
for p in libres[:6]:
    print(f"  {p.get('ID')} · {p.get('Nombre')}")

if not APLICAR:
    print("\n(en seco — repetir con --apply)")
    sys.exit(0)

# 1) borrar PS-0007 (mi duplicado)
w = PS._ws()
filas = w.get_all_records(numericise_ignore=["all"])
idx = next((i for i, r in enumerate(filas) if str(r.get("ID")) == "PS-0007"), -1)
if idx >= 0:
    w.delete_rows(idx + 2)
    PS._invalidate()
    print("\nPS-0007 borrado")
else:
    print("\nPS-0007 no está (ya borrado)")

# 2) el caso, en una obra libre y con asistentes que NO son el admin
if not libres:
    print("no hay obra libre para montar el caso")
    sys.exit(0)
obj = libres[0]
pid = str(obj.get("ID"))
data = {
    "proyecto_id": pid, "grupo": G, "fecha": HOY, "hora": "07:00",
    "location": str(obj.get("Ubicacion", "")) or "Level 1",
    "facilitador": "Marcus Chen",
    "activities_notes": "Montaje de rieles. SWMS revisado.",
    "near_miss": "NO", "near_miss_desc": "",
    "s1": {k: "YES" for k, _t in PS.CHECKS_S1},
    "s3": {k: "YES" for k, _t in PS.CHECKS_S3},
    "general_notes": "Charla sembrada para probar la firma tardía (v403).",
    "attendees": [{"name": "Marcus Chen", "initial": "MC", "sig": None},
                  {"name": "Tom O'Brien", "initial": "TO", "sig": None}],
    "creado_por": "mchen",
}
res = PS.submit(data)
PS._invalidate()
print(f"\ncaso montado en {pid} ({obj.get('Nombre')}) -> {res.get('id')} · ok={res.get('ok')}")
for u in ("asfgjjd", "dmoreno"):
    p = PS.pendiente_de_firma(pid, G, u)
    print(f"  a {u:<10} {'LE FALTA firmar → ' + str(p.get('id')) if p else 'no le falta'}")
