"""¿La caché mezcla los datos de DOS INQUILINOS? (v378, revisado en v379)

⚠️ La primera versión comparaba «propietario» contra «admin de cliente1» y daba por
fuga que el propietario viera 16 obras. Desde la fase 2 (v379) eso es lo CORRECTO:
el propietario recorre todos los libros a propósito. Ese test había dejado de
distinguir una fuga de la funcionalidad nueva — y un test así solo puede dar
veredictos falsos.

Ahora se comparan DOS ADMINISTRADORES de grupos distintos, que es lo que el
aislamiento tiene que garantizar:
  · `cliente1` → su propio libro (16 obras)
  · `otro`     → sin libro propio → el maestro (vacío tras la mudanza de v377)
Ninguno de los dos puede ver lo del otro, en ningún orden y sin limpiar la caché.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P                             # noqa: E402

ok = True


def como(grupo):
    st.session_state["auth"] = {"usuario": "x", "grupo": grupo, "rol": "administrador"}
    st.session_state.pop("_tenant_grupo_activo", None)


print("== A→B: primero cliente1, luego otro (sin limpiar la caché) ==")
como("cliente1")
a = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
como("otro")
b = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
print(f"   admin de cliente1 → {a} obras   (esperado 16)")
print(f"   admin de «otro»   → {b} obras   (esperado 0: su libro es el maestro, vacío)")
bien = a == 16 and b == 0
ok &= bien
print(f"   {'✓ el segundo NO ve lo del primero' if bien else '‼️ FUGA'}")

print("\n== B→A: al revés ==")
P._invalidate()
como("otro")
c = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
como("cliente1")
d = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
print(f"   admin de «otro»   → {c} obras   (esperado 0)")
print(f"   admin de cliente1 → {d} obras   (esperado 16)")
bien = c == 0 and d == 16
ok &= bien
print(f"   {'✓ el segundo recibe LO SUYO, no la caché del primero' if bien else '‼️ FUGA'}")

print("\n== y el propietario sigue viéndolo todo (fase 2, v379) ==")
st.session_state["auth"] = {"usuario": "dacox", "grupo": "", "rol": "propietario"}
st.session_state.pop("_tenant_grupo_activo", None)
e = len(P.list_projects(incluir_archivados=True))
ok &= e == 16
print(f"   {'✓' if e == 16 else '‼️'} propietario → {e} obras de todos los libros")

print("\n" + ("✓ sin fuga: cada inquilino ve lo suyo y el propietario ve todo"
              if ok else "‼️ HAY FUGA ENTRE INQUILINOS"))
sys.exit(0 if ok else 1)
