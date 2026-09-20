"""PASO 4+5 — enlazar cliente1 a su libro y comprobar que la app lo ENRUTA allí.

⚠️ Ahora mismo los dos libros tienen los MISMOS datos, así que «la app muestra 16
obras» NO demuestra que lea del nuevo. El discriminador de verdad es el enrutado:
`timeclock.sheet_id_para(hoja, grupo)` tiene que devolver el libro de la demo para
las hojas de inquilino y el MAESTRO para las globales. La prueba funcional
definitiva llega en el paso 7, cuando el maestro esté vacío y la app siga viendo
las 16 obras.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1", "rol": "administrador"}

from core import auth, timeclock, projects as P, invoices as I, finance as F   # noqa: E402

DEMO_ID = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
MAESTRO_ID = str(st.secrets["TIMECLOCK_SHEET_ID"])
G = "cliente1"

print("== antes ==")
print(f"   SheetID de cliente1: {auth.group_sheet_id(G) or '(vacío → maestro)'}")

print("\n== enlazar ==")
ok, msg = auth.set_group_sheet_id(G, DEMO_ID)
print(f"   set_group_sheet_id → {ok} · {msg}")
if not ok:
    sys.exit(1)

# tirar cachés para que la siguiente lectura resuelva de nuevo
for fn in (getattr(auth, "_group_records", None),):
    try:
        fn.clear()
    except Exception:
        pass
try:
    from core import hojas
    hojas.invalidar()
except Exception:
    pass

print("\n== ⚠️ el ENRUTADO, que es la prueba de verdad ==")
casos = [
    ("Proyectos", G, DEMO_ID, "hoja de inquilino → libro de la demo"),
    ("Sheet1", G, DEMO_ID, "el fichaje → libro de la demo"),
    ("Facturas", G, DEMO_ID, "el dinero → libro de la demo"),
    ("Login", G, MAESTRO_ID, "GLOBAL → siempre el maestro"),
    ("Grupos", G, MAESTRO_ID, "GLOBAL → siempre el maestro"),
    ("Rieles", G, MAESTRO_ID, "GLOBAL → siempre el maestro"),
    ("Proyectos", "", MAESTRO_ID, "sin grupo (propietario) → el maestro"),
]
bien = True
for hoja, grupo, esperado, que in casos:
    got = timeclock.sheet_id_para(hoja, grupo)
    b = got == esperado
    bien &= b
    print(f"   {'✓' if b else '‼️'} {hoja:<10} grupo={grupo or '—':<9} → "
          f"{'DEMO' if got == DEMO_ID else ('MAESTRO' if got == MAESTRO_ID else got[:12])}"
          f"   ({que})")

print("\n== y que las cifras sigan siendo las mismas ==")
try:
    proys = P.list_projects(grupo=G, incluir_archivados=True)
    fact = sum(I.facturado_por_proyecto(G).values())
    pnl = F.pnl(G)
    print(f"   obras            {len(proys)}")
    print(f"   facturado        ${fact:,.2f}")
    print(f"   P&L ingresos     ${pnl.get('ingresos', 0):,.2f}")
    print(f"   P&L ganancia     ${pnl.get('ganancia', 0):,.2f}")
    bien &= len(proys) == 16
except Exception as e:
    print(f"   ‼️ {type(e).__name__}: {e}")
    bien = False

print("\n" + ("✅ enlazado y enrutando a la demo. El maestro TODAVÍA tiene los datos"
              " (paso 6)" if bien else "⛔ revisar antes de seguir"))
sys.exit(0 if bien else 1)
