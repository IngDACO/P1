"""Traza: ¿cuántas veces se EJECUTA de verdad el lector, y con qué libro?

Si `hojas.registros` se llama una sola vez, el que sirve la segunda es la caché
del módulo. Si se llama dos veces y devuelve lo mismo, el problema está debajo.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
from core import projects as P, hojas, timeclock as T      # noqa: E402

llamadas = []
_orig = hojas.registros


def espia(titulo, cabeceras=None, grupo=None):
    libro = T.sheet_id_para(titulo, grupo)
    r = _orig(titulo, cabeceras, grupo)
    llamadas.append((titulo, libro[-6:], len(r or [])))
    return r


hojas.registros = espia


def como(rol, g):
    st.session_state["auth"] = {"usuario": "x", "grupo": g, "rol": rol}


print("== 1ª: propietario (maestro) ==")
como("propietario", "")
lib1 = P._libro_de("Proyectos")
n1 = len(P.list_projects(incluir_archivados=True))
print(f"   _libro_de → …{lib1[-6:]}   resultado: {n1} proyectos")
print(f"   ejecuciones reales de hojas.registros: {llamadas}")

print("\n== 2ª: admin de cliente1 (demo) ==")
llamadas.clear()
como("administrador", "cliente1")
lib2 = P._libro_de("Proyectos")
n2 = len(P.list_projects(grupo="cliente1", incluir_archivados=True))
print(f"   _libro_de → …{lib2[-6:]}   resultado: {n2} proyectos")
print(f"   ejecuciones reales de hojas.registros: {llamadas}")

print("\n== veredicto ==")
if not llamadas:
    print("   → la CACHÉ DEL MÓDULO sirvió la segunda: la clave no está separando")
    print(f"     (claves: …{lib1[-6:]} vs …{lib2[-6:]}, distintas={lib1 != lib2})")
else:
    print("   → sí se ejecutó; el problema está por debajo de `hojas.registros`")

# ¿la función que list_projects usa es realmente el envoltorio?
import inspect                                             # noqa: E402
print("\n== ¿está cacheado el `_records_cached`? ==")
print(f"   _records          tiene .clear(): {hasattr(P._records, 'clear')}")
print(f"   _records_cached   tiene .clear(): {hasattr(P._records_cached, 'clear')}")
print(f"   list_projects llama a: "
      f"{[l for l in inspect.getsource(P.list_projects).splitlines() if '_records' in l]}")
