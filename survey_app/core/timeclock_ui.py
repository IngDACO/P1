"""
UI de la pestaña de fichaje (clock in / clock out).
La identidad viene del login; ya no se pide usuario + PIN.
"""
import streamlit as st

from core import timeclock


def render_timeclock_tab():
    st.markdown("### ⏱ Fichaje — Clock In / Clock Out")

    if not timeclock.is_configured():
        st.warning(
            "⚠️ El fichaje aún no está conectado a Google Sheets. "
            "Configura los Secrets en Streamlit Cloud."
        )
        return

    a       = st.session_state.get("auth", {})
    nombre  = a.get("nombre") or a.get("usuario") or ""
    grupo   = a.get("grupo", "")

    st.caption(f"Fichando como **{nombre}**"
               + (f"  ·  grupo **{grupo}**" if grupo else "")
               + ". Tus fichajes son privados.")

    c3, c4 = st.columns(2)
    proyecto  = c3.text_input("Proyecto / Cliente", key="tc_proyecto",
                              placeholder="Proyecto en el que trabajas")
    ubicacion = c4.text_input("Ubicación / Nota", key="tc_ubicacion",
                              placeholder="Obra, ubicación o comentario")

    b1, b2 = st.columns(2)
    if b1.button("🟢 Clock IN", use_container_width=True, key="tc_in"):
        ok, msg = timeclock.clock_in(nombre, proyecto, ubicacion, grupo)
        (st.success if ok else st.error)(msg)

    if b2.button("🔴 Clock OUT", use_container_width=True, key="tc_out"):
        ok, msg = timeclock.clock_out(nombre, grupo, ubicacion)
        (st.success if ok else st.error)(msg)

    st.markdown("---")
    st.caption("🔒 Tus fichajes se registran de forma privada. El historial completo "
               "solo está disponible para la administración.")
