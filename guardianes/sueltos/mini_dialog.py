"""MINI-APP: ¿funciona `st.dialog` como pop-up disparado DESDE EL SIDEBAR?

Replica el flujo real: botón «Fichar» en el sidebar → acción → `st.rerun()` →
en la pasada siguiente se abre el modal. Hay que comprobar tres cosas, ninguna
deducible del código:
  1. que el modal se pinte SOBRE la página aunque lo dispare el sidebar;
  2. que SOBREVIVA al `st.rerun()` (el deltas-descartados de v365 mata mensajes,
     y un modal es un delta más);
  3. que no se reabra solo en cada pasada (sería inaguantable).
"""
import streamlit as st

st.set_page_config(page_title="mini dialog", layout="wide")


@st.dialog("Falta el Pre-Start de hoy", width="small")
def _aviso_prestart(obra):
    st.markdown(f"Acabas de fichar a **{obra}** y hoy todavía **no hay Pre-Start** "
                "registrado en esa obra.")
    st.caption("Es la charla de seguridad antes de empezar: una por obra y día.")
    c1, c2 = st.columns(2)
    if c1.button("Ir al Pre-Start", type="primary", use_container_width=True):
        st.session_state["_destino"] = "prestart"
        st.rerun()
    if c2.button("Ahora no", use_container_width=True):
        st.session_state["_destino"] = "cerrado sin ir"
        st.rerun()


st.session_state.setdefault("_fichado", False)
st.session_state.setdefault("_pasadas", 0)
st.session_state["_pasadas"] += 1

with st.sidebar:
    st.markdown("### FICHAJE")
    if not st.session_state["_fichado"]:
        if st.button("Fichar a Meriton Torre A", type="primary", use_container_width=True):
            st.session_state["_fichado"] = True
            st.session_state["_ps_pendiente"] = "Meriton Torre A"   # bandera
            st.rerun()
    else:
        st.success("En obra")
        if st.button("Cerrar jornada", use_container_width=True):
            st.session_state["_fichado"] = False
            st.rerun()
    st.markdown("---")
    st.caption(f"pasadas del script: {st.session_state['_pasadas']}")

# ⚠️ El modal se dispara en la pasada SIGUIENTE al rerun, leyendo la bandera.
#    `pop` para que se abra UNA vez y no en cada pasada.
_obra = st.session_state.pop("_ps_pendiente", None)
if _obra:
    _aviso_prestart(_obra)

st.markdown("# Contenido principal")
st.write("Si el modal tapa esto, el pop-up funciona disparado desde el sidebar.")
st.write("destino elegido:", st.session_state.get("_destino", "— nada aún —"))
st.write("fichado:", st.session_state["_fichado"])
