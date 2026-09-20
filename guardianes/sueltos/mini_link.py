"""¿Que hace de verdad un `LinkColumn` en una tabla como la de la cartera?

Cuatro preguntas, ninguna se responde leyendo la documentacion:
  1. ¿puede MOSTRAR el importe formateado (`$27,883`) en vez de la URL?
  2. ¿como ORDENA al pulsar su cabecera: como numero o como texto?
  3. al pulsar el enlace, ¿RECARGA la pagina (y se pierde session_state) o navega en sesion?
  4. ¿el clic en el enlace dispara ADEMAS la seleccion de fila (`on_select`)?

La (3) es la que decide: v169 revirtio un `<a href>` propio por riesgo de deslogueo,
pero eso era HTML nuestro, no un LinkColumn — no es lo mismo y no se supone.
"""
import uuid

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# ⚠️ marca ESTABLE por sesion: si sobrevive al clic, no hubo recarga que resetee el estado
if "marca" not in st.session_state:
    st.session_state["marca"] = uuid.uuid4().hex[:8]
st.session_state["runs"] = st.session_state.get("runs", 0) + 1
st.session_state.setdefault("clics", 0)

st.write(f"MARCA={st.session_state['marca']} RUNS={st.session_state['runs']} "
         f"QP={dict(st.query_params)}")

BASE = "http://localhost:8548/"
filas = [
    {"Proyecto": "RNSH Lift 4",   "Num": 27882.67,
     "Link": f"{BASE}?fac=PRJ-0012&m=$27,883", "Rel": "?fac=PRJ-0012&m=$27,883"},
    {"Proyecto": "Stockland",     "Num": 2960.0,
     "Link": f"{BASE}?fac=PRJ-0016&m=$2,960",  "Rel": "?fac=PRJ-0016&m=$2,960"},
    {"Proyecto": "Meriton",       "Num": 980.0,
     "Link": f"{BASE}?fac=PRJ-0009&m=$980",    "Rel": "?fac=PRJ-0009&m=$980"},
    {"Proyecto": "Bespoke",       "Num": 5200.0,
     "Link": f"{BASE}?fac=PRJ-0011&m=$5,200",  "Rel": "?fac=PRJ-0011&m=$5,200"},
]

ev = st.dataframe(
    pd.DataFrame(filas), hide_index=True, use_container_width=True,
    on_select="rerun", selection_mode="single-row", key="t",
    column_config={
        "Num":  st.column_config.NumberColumn("Num (control)", format="$%,.0f"),
        # el importe formateado extraido de la URL con un grupo de captura
        "Link": st.column_config.LinkColumn("Sin facturar", display_text=r"m=(.*)$"),
        "Rel":  st.column_config.LinkColumn("Relativa", display_text=":material/receipt:"),
    })

sel = list(ev.selection.rows) if ev.selection else []
st.write(f"SELECCION={sel}")
