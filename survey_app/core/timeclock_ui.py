"""
UI de la pestaña de fichaje (clock in / clock out).
"""
import streamlit as st
import pandas as pd

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

    st.caption("Registra tu entrada y salida. Los fichajes se guardan en Google Sheets.")

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

    # ── Historial ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Registro de fichajes")
    if st.button("🔄 Actualizar registro", key="tc_refresh"):
        st.rerun()

    records = timeclock.get_records()
    if not records:
        st.info("Aún no hay fichajes registrados.")
        return

    df = pd.DataFrame(records)

    # Filtro opcional por nombre
    if nombre.strip():
        solo_mio = st.checkbox("Ver solo mis fichajes", value=False, key="tc_solo")
        if solo_mio:
            df = df[df["Nombre"].astype(str).str.strip() == nombre.strip()]

    # No mostrar la columna PIN por privacidad
    show_cols = [c for c in df.columns if c != "PIN"]
    st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    # Resumen de horas por persona (sesiones cerradas)
    if "Horas" in df.columns and "Estado" in df.columns:
        cerradas = df[df["Estado"].astype(str).str.upper() == "CERRADO"].copy()
        if not cerradas.empty:
            cerradas["Horas"] = pd.to_numeric(cerradas["Horas"], errors="coerce").fillna(0)
            resumen = cerradas.groupby("Nombre")["Horas"].sum().reset_index()
            resumen.columns = ["Nombre", "Horas totales"]
            st.subheader("Σ Horas totales por persona")
            st.dataframe(resumen, use_container_width=True, hide_index=True)
