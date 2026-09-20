"""Segunda vuelta: ¿qué hay que limpiar para que un riel nuevo se vea?

En la primera, la fila estaba en la hoja y `get_rail` seguía sin verla tras
`hojas.invalidar()`. Sospecha: son DOS cachés en cadena y hay que tirar las dos —
el lote (v339) y la `@st.cache_data` del propio módulo, que entre medias había
vuelto a memoizar el resultado VACÍO.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import hojas, rails                                     # noqa: E402

REF = "ZZZ-DIAG-T2"
rails.add_riel(REF, 10, 62)
print("A) justo después                 :", rails.get_rail(REF))

rails._records.clear()
print("B) solo `_records.clear()`       :", rails.get_rail(REF))

hojas.invalidar()
rails._records.clear()
print("C) lote + `_records.clear()`     :", rails.get_rail(REF))

print("D) qué devuelve `hojas.registros`:",
      [r for r in (hojas.registros(rails.RIELES_SHEET, rails.RIELES_HEADERS) or [])
       if str(r.get("Referencia", "")) == REF])

rails.delete_riel(REF)
hojas.invalidar()
rails._records.clear()
print("\nlimpieza · queda:", rails.get_rail(REF))
