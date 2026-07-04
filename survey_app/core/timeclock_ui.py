"""
UI de la pestaña de fichaje (clock in / clock out).
"""
import streamlit as st

from core import timeclock


def render_timeclock_tab():
    st.markdown("### ⏱ Fichaje — Clock In / Clock Out")

    if not timeclock.is_configured():
        st.warning(
            "⚠️ El fichaje aún no está conectado a Google Sheets.\n\n"
            "Falta configurar las credenciales (`gcp_service_account`) y "
            "`TIMECLOCK_SHEET_ID` en los **Secrets de Streamlit Cloud**. "
            "Una vez configurado, esta pestaña quedará operativa."
        )
        return

    st.caption("Registra tu entrada y salida. Solo usuarios autorizados (Nombre + PIN "
               "en la pestaña 'Usuarios' de la hoja) pueden fichar.")

    # ── Identificación ──────────────────────────────────────
    c1, c2 = st.columns(2)
    nombre = c1.text_input("Nombre", key="tc_nombre", placeholder="Tu nombre")
    pin    = c2.text_input("PIN", key="tc_pin", type="password",
                           placeholder="PIN personal", max_chars=8)

    c3, c4 = st.columns(2)
    proyecto  = c3.text_input("Proyecto / Cliente", key="tc_proyecto",
                              placeholder="Proyecto en el que trabajas")
    ubicacion = c4.text_input("Ubicación / Nota", key="tc_ubicacion",
                              placeholder="Obra, ubicación o comentario")

    # ── Botones ─────────────────────────────────────────────
    b1, b2 = st.columns(2)
    if b1.button("🟢 Clock IN", use_container_width=True, key="tc_in"):
        ok, msg = timeclock.clock_in(nombre, pin, proyecto, ubicacion)
        (st.success if ok else st.error)(msg)

    if b2.button("🔴 Clock OUT", use_container_width=True, key="tc_out"):
        ok, msg = timeclock.clock_out(nombre, pin, ubicacion)
        (st.success if ok else st.error)(msg)

    st.markdown("---")
    st.caption("🔒 Tus fichajes se registran de forma privada. El historial completo "
               "solo está disponible para la administración.")
