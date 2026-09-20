"""¿Por qué un riel recién creado no se lee de vuelta?

Hipótesis: `add_riel` limpia SU caché (`_records.clear()`) pero los datos vienen de
`hojas.registros`, que lee del LOTE de v339 — con su propia caché. Si es eso, el riel
está en la hoja y solo la lectura llega tarde.

Se comprueba, no se supone: si tras `hojas.invalidar()` aparece, la hipótesis es buena.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import hojas, rails                                     # noqa: E402

REF = "ZZZ-DIAG-T1"
print("estado inicial:", rails.get_rail(REF))

ok, msg = rails.add_riel(REF, 10, 62)
print(f"add_riel -> {ok} · {msg}")

print("A) get_rail JUSTO DESPUÉS      :", rails.get_rail(REF))
hojas.invalidar()
print("B) tras `hojas.invalidar()`    :", rails.get_rail(REF))

# la prueba definitiva: ¿está la fila en la HOJA?
w, err = rails._ws()
crudo = [r for r in w.get_all_records(numericise_ignore=["all"])
         if str(r.get("Referencia", "")) == REF]
print("C) leyendo la hoja en crudo    :", crudo)

print("\nVEREDICTO:")
if crudo and rails.get_rail(REF):
    print("  la fila SÍ estaba; solo la lectura por lote llegaba tarde → falta invalidar el lote")
elif crudo:
    print("  la fila está en la hoja pero get_rail sigue sin verla → mirar más adentro")
else:
    print("  la fila NO se escribió → el problema es la escritura, no la caché")

ok, msg = rails.delete_riel(REF)
hojas.invalidar()
print(f"\nlimpieza: delete_riel -> {ok} · {msg} · queda: {rails.get_rail(REF)}")
