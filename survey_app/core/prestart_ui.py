"""
Pestaña 📋 Pre-Start diario: el equipo llena la charla de seguridad del día,
se genera el PDF (marca = grupo), se archiva en Drive del proyecto + hoja, y si
hay Near Miss/Hazard se abre una alarma del proyecto.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from core import prestart as PS
from core import projects as P
from core import maps


def _initials(nombre: str) -> str:
    parts = [w for w in str(nombre or "").split() if w]
    return "".join(w[0].upper() for w in parts[:3])


def _projects_for(rol, usuario, grupo):
    if rol == "propietario":
        return P.list_projects()
    if rol == "administrador":
        return P.list_projects(grupo=grupo)
    return P.list_projects_for_field(usuario, grupo=grupo)


def render_prestart_tab():
    st.markdown("### 📋 Pre-Start diario")
    st.caption("Registro de la charla de seguridad antes de empezar en obra. Genera el PDF, "
               "lo archiva en el proyecto y —si hay near miss/hazard— abre una alarma.")

    if not PS.is_configured():
        st.warning("Necesita Google Sheets configurado (gcp_service_account + TIMECLOCK_SHEET_ID).")
        return

    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    grupo, nombre = a.get("grupo", ""), a.get("nombre", "")

    proys = _projects_for(rol, usuario, grupo)
    if not proys:
        st.info("No hay proyectos disponibles. "
                + ("El administrador debe asignarte a un proyecto." if rol == "campo"
                   else "Crea un proyecto desde el Survey."))
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p for p in proys}
    sel = st.selectbox("Proyecto", list(idmap.keys()), key="ps_proy")
    prj = idmap[sel]
    pid = str(prj.get("ID", ""))
    pgrupo = str(prj.get("Grupo", "")) or grupo

    # ── Encabezado ──
    c1, c2, c3 = st.columns(3)
    f_fecha = c1.date_input("Date", value=date.today(), key="ps_fecha")
    f_hora  = c2.text_input("Time", value=datetime.now().strftime("%H:%M"), key="ps_hora")
    f_loc   = c3.text_input("Location", value=str(prj.get("Ubicacion", "")), key="ps_loc")
    if f_loc.strip():
        c3.caption(maps.maps_link_md(f_loc, "ver en Maps"))
    f_fac   = st.text_input("Facilitated by", value=nombre or usuario, key="ps_fac")

    st.markdown("---")

    # ── 1. Planned work activities ──
    st.markdown("**1. Planned work activities today**")
    s1 = {}
    for key, label in PS.CHECKS_S1:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:0.9rem;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s1[key] = cc[1].radio(label, PS.OPTS_YN, horizontal=True, index=0,
                              key=f"ps_s1_{key}", label_visibility="collapsed")
    act_notes = st.text_area("Notas de actividades / SWMS", key="ps_act", height=70)

    # ── 2. Issues / hazard / near miss ──
    st.markdown("**2. Issues, hazard / near miss reports**")
    nm = st.radio("Near Miss/Hazard Report submitted", PS.OPTS_YN, horizontal=True,
                  index=1, key="ps_nm")
    nm_desc = ""
    if nm == "YES":
        nm_desc = st.text_area("Describe el near miss / hazard (abrirá una alarma del proyecto)",
                               key="ps_nmdesc", height=70)

    # ── 3. Shaft protection ──
    st.markdown("**3. Shaft Protection & other daily checks**")
    s3 = {}
    for key, label in PS.CHECKS_S3:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:0.9rem;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s3[key] = cc[1].radio(label, PS.OPTS_YNA, horizontal=True, index=0,
                              key=f"ps_s3_{key}", label_visibility="collapsed")

    # ── 4. General notes ──
    st.markdown("**4. General Notes**")
    gen_notes = st.text_area("Notas generales", key="ps_gen", height=70,
                             label_visibility="collapsed")

    # ── 5. Attendees ──
    st.markdown("**5. Attendees**")
    base = st.session_state.get("ps_att_df")
    if base is None:
        base = pd.DataFrame({"Print Name": [nombre or usuario], "Initial": [_initials(nombre or usuario)]})
    att_edit = st.data_editor(base, use_container_width=True, hide_index=True,
                              num_rows="dynamic", key="ps_att_editor")
    st.session_state["ps_att_df"] = att_edit

    st.markdown("---")
    if st.button("📋 Generar y archivar Pre-Start", type="primary", use_container_width=True,
                 key="ps_submit"):
        attendees = [{"name": str(r["Print Name"]).strip(), "initial": str(r["Initial"]).strip()}
                     for _, r in att_edit.iterrows()
                     if str(r.get("Print Name", "")).strip() or str(r.get("Initial", "")).strip()]
        data = {
            "grupo": pgrupo, "proyecto_id": pid, "proyecto_nombre": prj.get("Nombre", ""),
            "fecha": f_fecha, "hora": f_hora, "location": f_loc, "facilitador": f_fac,
            "activities_notes": act_notes, "s1": s1,
            "near_miss": nm, "near_miss_desc": nm_desc, "s3": s3,
            "general_notes": gen_notes, "attendees": attendees,
            "creado_por": usuario,
        }
        with st.spinner("Generando PDF y archivando..."):
            res = PS.submit(data)
        if not res["ok"]:
            st.error(res["error"] or "No se pudo guardar el pre-start.")
        else:
            st.success(f"✅ Pre-Start **{res['id']}** guardado como `{res['filename']}`.")
            if res["drive_id"]:
                st.caption("📎 Archivado en los documentos del proyecto.")
            else:
                st.caption("⚠️ No se archivó en Drive (revisa la conexión); el registro sí quedó guardado.")
            if res["alarma"]:
                st.warning("🔴 Se abrió una alarma del proyecto por el near miss/hazard reportado.")
            st.download_button("⬇️ Descargar PDF", data=res["pdf"], file_name=res["filename"],
                               mime="application/pdf", use_container_width=True, key="ps_dl")

    # ── Historial ──
    prev = PS.list_prestarts(pid)
    if prev:
        with st.expander(f"🗂 Pre-Starts anteriores ({len(prev)})"):
            st.dataframe(pd.DataFrame([{
                "Fecha": r.get("Fecha"), "Hora": r.get("Hora"),
                "Facilitador": r.get("Facilitador"),
                "Near miss": r.get("NearMiss"), "Archivo": r.get("Archivo"),
            } for r in prev]), hide_index=True, use_container_width=True)
