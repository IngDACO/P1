"""
UI de la pestaña de fichaje (clock in / clock out).
La identidad viene del login; ya no se pide usuario + PIN.
El proyecto se elige de los proyectos asignados (así las horas quedan atadas al proyecto).
"""
import streamlit as st

from core import timeclock
from core import projects as projects_data

_OTRO = "✏️ Otro (escribir)…"


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
    usuario = a.get("usuario", "")
    grupo   = a.get("grupo", "")

    st.caption(f"Fichando como **{nombre}**"
               + (f"  ·  grupo **{grupo}**" if grupo else "")
               + ". Tus fichajes son privados.")

    # ── Proyecto: desplegable de proyectos asignados ────────
    asignados = []
    try:
        if grupo:
            asignados = projects_data.list_projects_for_field(usuario, grupo=grupo)
    except Exception:
        asignados = []

    c3, c4 = st.columns(2)
    if asignados:
        nombres = [p.get("Nombre") for p in asignados]
        sel = c3.selectbox("Proyecto (de tus asignados)", nombres + [_OTRO],
                           key="tc_proyecto_sel")
        proyecto = (c3.text_input("Nombre del proyecto", key="tc_proyecto_otro")
                    if sel == _OTRO else sel)
    else:
        c3.caption("No tienes proyectos asignados; escribe el proyecto a mano.")
        proyecto = c3.text_input("Proyecto / Cliente", key="tc_proyecto",
                                 placeholder="Proyecto en el que trabajas")

    ubicacion = c4.text_input("Ubicación / Nota", key="tc_ubicacion",
                              placeholder="Obra, ubicación o comentario")

    b1, b2 = st.columns(2)
    if b1.button("🟢 Clock IN", use_container_width=True, key="tc_in"):
        if not proyecto:
            st.error("Elige o escribe el proyecto antes de fichar.")
        else:
            ok, msg = timeclock.clock_in(nombre, proyecto, ubicacion, grupo)
            (st.success if ok else st.error)(msg)

    if b2.button("🔴 Clock OUT", use_container_width=True, key="tc_out"):
        ok, msg = timeclock.clock_out(nombre, grupo, ubicacion)
        (st.success if ok else st.error)(msg)

    st.markdown("---")
    st.caption("🔒 Tus fichajes se registran de forma privada. El historial completo "
               "solo está disponible para la administración. Las horas se suman al "
               "proyecto elegido.")
