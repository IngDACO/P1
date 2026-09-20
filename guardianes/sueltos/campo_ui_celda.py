"""¿Qué pasa si el campo BORRA una celda de la tabla de avance?

`_field_activities` hace `int(r["Avance %"])` y `str(r["Nota"])` sobre lo que
devuelve el `st.data_editor`. Una celda vaciada vuelve como None/NaN. Se replica
la aritmética EXACTA de esas dos líneas con lo que pandas produce en ese caso.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import pandas as pd     # noqa: E402

# Lo que devuelve el editor cuando el usuario deja la celda del avance vacía y
# borra el texto de la nota (NumberColumn → NaN, TextColumn → None).
_ed = pd.DataFrame([
    {"N": 1, "Actividad": "Survey",   "Avance %": 40,          "Nota": "ok"},
    {"N": 2, "Actividad": "Plomadas", "Avance %": float("nan"), "Nota": None},
])

print("== celda de AVANCE vaciada ==")
try:
    v = int(_ed.iloc[1]["Avance %"])
    print(f"   int(NaN) → {v}")
except Exception as e:
    print(f"   ‼️ {type(e).__name__}: {e}")
    print("      → el botón «Guardar avances» revienta y se pierde TODA la edición,")
    print("        no solo esa fila.")

print("\n== celda de NOTA vaciada ==")
n = str(_ed.iloc[1]["Nota"])
print(f"   str(None) → {n!r}")
if n == "None":
    print("      → se guardaría el TEXTO 'None' como nota del campo en la hoja.")

print("\n== una fila normal (control) ==")
print(f"   avance={int(_ed.iloc[0]['Avance %'])}  nota={str(_ed.iloc[0]['Nota'])!r}  ✓")
