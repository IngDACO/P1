"""
Pestaña 📋 Pre-Start diario: el equipo llena la charla de seguridad del día,
se genera el PDF (marca = grupo), se archiva en Drive del proyecto + hoja, y si
hay Near Miss/Hazard se abre una alarma del proyecto.
"""
import streamlit as st
import pandas as pd

from core import prestart as PS
from core import projects as P
from core import maps
from core import clock

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— elige el proyecto —"


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
    st.markdown("### :material/health_and_safety: Pre-Start diario")
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
    # Campo: preselecciona el proyecto donde FICHÓ (lo primero que hace en el día),
    # como en 📋 Mis proyectos (v138). No es "el primero de la lista" que evitó v139:
    # es una señal FUERTE (donde está trabajando) que se MUESTRA y sigue siendo
    # cambiable. El pre-start se archiva y la near miss abre alarma en ese proyecto.
    _fich_key = None
    if rol == "campo":
        try:
            from core import timeclock
            _ses = timeclock.open_sessions(nombre, grupo, usuario)
            _open = (_ses.get(timeclock.TIPO_PROYECTO)
                     or _ses.get(timeclock.TIPO_GENERAL) or {})
            _fpid = str(_open.get("proyecto_id", "")).strip()
            _fpn  = str(_open.get("proyecto", "")).strip()
            if _fpid:                                  # ID primero, nombre de respaldo (v145)
                _fich_key = next((k for k in idmap if k.endswith(f"({_fpid})")), None)
            if not _fich_key and _fpn:
                _fich_key = next((k for k in idmap if k.startswith(_fpn + " (")), None)
        except Exception:
            pass
        if _fich_key and "ps_proy" not in st.session_state:
            st.session_state["ps_proy"] = _fich_key
    sel = st.selectbox("Proyecto", [_VACIO] + list(idmap.keys()), key="ps_proy")
    if _fich_key and sel == _fich_key:
        st.caption(":material/schedule: Es el proyecto donde fichaste hoy. Cámbialo si el pre-start es de otro.")
    if not sel or sel == _VACIO:
        st.info("Elige el proyecto en el que vas a trabajar hoy.")
        return
    prj = idmap[sel]
    pid = str(prj.get("ID", ""))
    pgrupo = str(prj.get("Grupo", "")) or grupo

    # ── Encabezado ──
    c1, c2, c3 = st.columns(3)
    f_fecha = c1.date_input("Date", value=clock.today(), key="ps_fecha")
    f_hora_t = c2.time_input("Time", value=clock.now().time().replace(second=0, microsecond=0),
                             key="ps_hora")
    f_hora   = f_hora_t.strftime("%H:%M") if f_hora_t else ""
    f_loc   = c3.text_input("Location", value=str(prj.get("Ubicacion", "")), key="ps_loc")
    if f_loc.strip():
        c3.caption(maps.maps_link_md(f_loc, "ver en Maps"))
    f_fac   = st.text_input("Facilitated by", value=nombre or usuario, key="ps_fac")

    st.markdown("---")

    # ⚠️ Los checks arrancan SIN respuesta (index=None, v158): hay que responder
    # cada uno para poder generar. Antes arrancaban en YES y el pre-start se podía
    # firmar en un toque sin revisar nada — vaciaba la charla de seguridad.
    st.caption("Responde cada punto: es una revisión de seguridad, no una firma.")

    # ── 1. Planned work activities ──
    st.markdown("**1. Planned work activities today**")
    s1 = {}
    for key, label in PS.CHECKS_S1:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s1[key] = cc[1].radio(label, PS.OPTS_YN, horizontal=True, index=None,
                              key=f"ps_s1_{key}", label_visibility="collapsed")
    act_notes = st.text_area("Notas de actividades / SWMS", key="ps_act", height=70)

    # ── 2. Issues / hazard / near miss ──
    st.markdown("**2. Issues, hazard / near miss reports**")
    nm = st.radio("Near Miss/Hazard Report submitted", PS.OPTS_YN, horizontal=True,
                  index=None, key="ps_nm")
    # Texto libre SIEMPRE visible (antes solo aparecía al marcar YES): permite
    # describir un issue/hazard aunque no sea un near miss formal.
    nm_desc = st.text_area("Describe el issue / hazard / near miss (opcional)",
                           key="ps_nmdesc", height=70,
                           help="Si marcas YES arriba, esta descripción abre una alarma del proyecto.")
    if nm == "YES" and not str(nm_desc).strip():
        st.caption(":red[:material/cancel:] Marcaste YES: describe el near miss/hazard (abrirá una alarma del proyecto).")

    # ── 3. Shaft protection ──
    st.markdown("**3. Shaft Protection & other daily checks**")
    s3 = {}
    for key, label in PS.CHECKS_S3:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s3[key] = cc[1].radio(label, PS.OPTS_YNA, horizontal=True, index=None,
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
    # Qué falta por responder (checks sin marcar + near miss + al menos 1 asistente)
    _pend = [PS._LABELS.get(k, k) for k, v in {**s1, **s3}.items() if v is None]
    _att_hay = any(str(r.get("Print Name", "")).strip() for _, r in att_edit.iterrows())
    if nm is None:
        _pend.append("Near Miss/Hazard (sección 2)")
    if not _att_hay:
        _pend.append("Al menos un asistente (sección 5)")
    if _pend:
        st.caption("Falta por completar: " + " · ".join(_pend))

    if st.button(":material/health_and_safety: Generar y archivar Pre-Start", type="primary", use_container_width=True,
                 key="ps_submit", disabled=bool(_pend)):
        attendees = [{"name": str(r["Print Name"]).strip(),
                      "initial": (str(r["Initial"]).strip()
                                  or _initials(str(r["Print Name"]).strip()))}
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
            st.success(f":material/check_circle: Pre-Start **{res['id']}** guardado como `{res['filename']}`.")
            if res["drive_id"]:
                st.caption(":material/attach_file: Archivado en los documentos del proyecto.")
            else:
                st.caption(":orange[:material/warning:] No se archivó en Drive (revisa la conexión); el registro sí quedó guardado.")
            _no = [PS._LABELS.get(k, k) for k, v in {**s1, **s3}.items() if v == "NO"]
            if _no:
                st.error(":material/warning: Checks marcados **NO** (revisar antes de trabajar): "
                         + " · ".join(_no))
            if res["alarma"]:
                st.warning(":material/cancel: Se abrió una alarma del proyecto por el near miss/hazard reportado.")
            st.download_button(":material/download: Descargar PDF", data=res["pdf"], file_name=res["filename"],
                               mime="application/pdf", use_container_width=True, key="ps_dl")

    # ── Historial ──
    _historial(pid)


def _historial(pid):
    prev = [PS.leer(r) for r in PS.list_prestarts(pid)]
    st.markdown("---")
    st.markdown("#### :material/account_tree: Pre-Starts anteriores")
    if not prev:
        st.caption("Aún no hay pre-starts registrados en este proyecto.")
        return

    # ── KPIs de seguridad ──
    n_nm  = sum(1 for d in prev if d["near_miss"])
    n_fail = sum(1 for d in prev if d["n_no"])
    tarj = [_kpi("Registrados", len(prev)),
            _kpi("Con near miss", n_nm, "#c0392b" if n_nm else None),
            _kpi("Con checks en NO", n_fail, "#c0392b" if n_fail else None),
            _kpi("Último", prev[0]["fecha"] or "—")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── Ficha desplegable por pre-start ──
    for d in prev:
        _flag = (":red[:material/cancel:]" if (d["near_miss"] or d["n_no"]) else ":green[:material/check_circle:]")
        _res = []
        if d["near_miss"]:      _res.append("near miss")
        if d["n_no"]:           _res.append(f"{d['n_no']} check(s) en NO")
        _tit = (f"{_flag}  {d['fecha']} · {d['facilitador'] or '—'}"
                + (f"  ·  :orange[:material/warning:] {', '.join(_res)}" if _res else "  ·  todo OK"))
        with st.expander(_tit):
            if d["asistentes"]:
                st.markdown("**:material/engineering: Asistentes:** " + " · ".join(d["asistentes"]))
            st.markdown("**Checks:**")
            for c in d["checks"]:
                _e = {"YES": ":green[:material/check_circle:]", "NO": ":red[:material/cancel:]", "N/A": ":gray[:material/crop_square:]"}.get(c["estado"], ":gray[:material/help:]")
                st.markdown(f"{_e} {c['label']}  ·  _{c['estado']}_")
            if d["near_miss"]:
                st.error(":material/cancel: **Near miss / hazard:** " + (d["near_miss_desc"] or "(sin descripción)"))
            if str(d["act_notes"]).strip():
                st.caption(":material/description: Actividades: " + d["act_notes"])
            if str(d["gen_notes"]).strip():
                st.caption(":material/description: Notas generales: " + d["gen_notes"])
            _did = str(d["drive_id"]).strip()
            if _did:
                try:
                    from core import drive_store
                    st.download_button(":material/download: PDF", data=drive_store.download(_did),
                                       file_name=d["archivo"] or f"{d['id']}.pdf",
                                       key=f"ps_hdl_{d['id']}")
                except Exception:
                    st.caption("PDF no disponible")


def _kpi(label, valor, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:110px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;{col}">{valor}</div></div>')
