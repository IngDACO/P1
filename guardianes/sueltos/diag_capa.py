"""¿En qué capa se queda pegada la fuga? Se prueba `hojas.registros` directamente."""
import inspect
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, hojas                      # noqa: E402


def como(rol, g):
    st.session_state["auth"] = {"usuario": "x", "grupo": g, "rol": rol}


print("== capa `hojas.registros` (por DEBAJO de la caché del módulo) ==")
como("propietario", "")
a = hojas.registros("Proyectos", P.PROJECTS_HEADERS) or []
print(f"   propietario (maestro) → {len(a)} filas")
como("administrador", "cliente1")
b = hojas.registros("Proyectos", P.PROJECTS_HEADERS) or []
print(f"   admin cliente1 (demo) → {len(b)} filas")
print(f"   ¿la capa de abajo distingue? {len(a) != len(b)}")

print("\n== cómo resuelve `registros` el libro ==")
for linea in inspect.getsource(hojas.registros).splitlines():
    s = linea.strip()
    if any(k in s for k in ("def registros", "_lote", "sheet_id", "grupo")):
        print(f"   {s[:104]}")

print(f"\n   firma de _lote: {inspect.signature(hojas._lote)}")

print("\n== ¿y si se le pasa el grupo explícito? ==")
como("propietario", "")
c = hojas.registros("Proyectos", P.PROJECTS_HEADERS, grupo="cliente1") or []
print(f"   registros(..., grupo='cliente1') desde sesión de propietario → {len(c)} filas")
