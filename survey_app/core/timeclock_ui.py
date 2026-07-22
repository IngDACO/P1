"""
UI de la pestaña de fichaje (clock in / clock out).
La identidad viene del login; ya no se pide usuario + PIN.

- Todos los roles: clock in/out por proyecto, con CRONÓMETRO en vivo.
- Conductor: DOS relojes — jornada GENERAL (total de horas) + segmentos por PROYECTO
  (para fichar a un proyecto debe haber jornada general abierta). Cronómetro en ambos,
  cambio de proyecto en 1 toque, aviso de jornada olvidada.
"""
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core import timeclock
from core import projects as projects_data

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— elige el proyecto —"

_OTRO = "✏️ Otro (escribir)…"


def _chronometer(clock_in_str, label="En curso", color="#1e8449"):
    """Cronómetro en vivo (client-side): cuenta desde el Clock In, sin recargar la app."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    components.html(
        "<div style=\"display:flex;align-items:center;gap:10px;"
        "font-family:'Segoe UI',sans-serif;\">"
        f"<span style=\"font-size:13px;color:#6b7280;\">{label}</span>"
        f"<span id=\"chrono\" style=\"font-size:26px;font-weight:800;"
        f"font-family:'Courier New',monospace;color:{color};\">00:00:00</span></div>"
        "<script>"
        f"var e={e0};"
        "function f(s){var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),x=s%60;"
        "return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(x).padStart(2,'0');}"
        "var el=document.getElementById('chrono');el.textContent=f(e);"
        "setInterval(function(){e++;el.textContent=f(e);},1000);"
        "</script>",
        height=42,
    )


def _es_hoy(clock_in_str) -> bool:
    try:
        return datetime.strptime(str(clock_in_str), timeclock.FMT).date() == datetime.now().date()
    except Exception:
        return True


def _aviso_olvido(sess):
    """Avisa si una sesión abierta viene de un día anterior."""
    for tipo, s in sess.items():
        if s and not _es_hoy(s["clock_in"]):
            etq = "jornada general" if tipo == timeclock.TIPO_GENERAL else f"proyecto «{s['proyecto']}»"
            st.warning(f"⚠️ Tienes una **{etq}** abierta desde **{s['clock_in']}** (día anterior). "
                       "Haz clock out si la olvidaste.")


def render_timeclock_tab():
    st.markdown("### ⏱ Fichaje — Clock In / Clock Out")
    if not timeclock.is_configured():
        st.warning("⚠️ El fichaje aún no está conectado a Google Sheets. Configura los Secrets.")
        return

    a       = st.session_state.get("auth", {})
    rol     = a.get("rol", "")
    nombre  = a.get("nombre") or a.get("usuario") or ""
    usuario = a.get("usuario", "")
    grupo   = a.get("grupo", "")

    if rol == "conductor":
        _render_conductor(nombre, usuario, grupo)
    else:
        _render_normal(nombre, usuario, grupo)


# ── Fichaje estándar (campo/admin/propietario): solo proyecto + cronómetro ──
def _render_normal(nombre, usuario, grupo):
    st.caption(f"Fichando como **{nombre}**" + (f"  ·  grupo **{grupo}**" if grupo else "")
               + ". Tus fichajes son privados.")

    sess = timeclock.open_sessions(nombre, grupo, usuario)
    _aviso_olvido(sess)
    abierto = sess.get(timeclock.TIPO_PROYECTO)
    if abierto:
        st.success(f"🟢 Clock in abierto — proyecto **{abierto['proyecto'] or '—'}** "
                   f"desde {abierto['clock_in']}")
        _chronometer(abierto["clock_in"], "⏱ Tiempo en curso:")

    asignados = []
    try:
        if grupo:
            asignados = projects_data.list_projects_for_field(usuario, grupo=grupo)
    except Exception:
        asignados = []

    # nombre -> ID: el fichaje guarda el ID para no perder las horas si el
    # proyecto se renombra (v145). Escribir el nombre a mano deja el ID vacio.
    _ids = {str(p.get("Nombre", "")): str(p.get("ID", "")) for p in asignados}

    c3, c4 = st.columns(2)
    if asignados:
        nombres = [p.get("Nombre") for p in asignados]
        # Sin preseleccion: fichar en el proyecto equivocado desvirtua las horas
        # y, con ellas, el costo de mano de obra del elevador.
        sel = c3.selectbox("Proyecto (de tus asignados)",
                           [_VACIO] + nombres + [_OTRO], key="tc_proyecto_sel")
        proyecto = (c3.text_input("Nombre del proyecto", key="tc_proyecto_otro")
                    if sel == _OTRO else ("" if sel == _VACIO else sel))
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
            ok, msg = timeclock.clock_in(nombre, proyecto, ubicacion, grupo,
                                         usuario=usuario,
                                         proyecto_id=_ids.get(proyecto, ""))
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    if b2.button("🔴 Clock OUT", use_container_width=True, key="tc_out"):
        ok, msg = timeclock.clock_out(nombre, grupo, ubicacion, usuario=usuario)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()

    st.markdown("---")
    st.caption("🔒 Tus fichajes son privados. El resumen de horas lo ve la administración.")


# ── Fichaje del CONDUCTOR: jornada general + segmentos de proyecto ──
def _render_conductor(nombre, usuario, grupo):
    st.caption(f"Conductor: **{nombre}**" + (f"  ·  grupo **{grupo}**" if grupo else "")
               + ". Jornada general + segmentos por proyecto.")
    sess = timeclock.open_sessions(nombre, grupo, usuario)
    _aviso_olvido(sess)
    gen = sess.get(timeclock.TIPO_GENERAL)
    prj = sess.get(timeclock.TIPO_PROYECTO)

    # ── Jornada general ──
    st.markdown("#### 🚚 Jornada (general)")
    if gen:
        st.success(f"🟢 Jornada abierta desde {gen['clock_in']}")
        _chronometer(gen["clock_in"], "⏱ Jornada:", color="#1a3a5c")
        if st.button("🔴 Clock OUT jornada", use_container_width=True, key="cd_gen_out"):
            # cerrar también el segmento de proyecto si sigue abierto
            if prj:
                timeclock.clock_out(nombre, grupo, tipo=timeclock.TIPO_PROYECTO, usuario=usuario)
            ok, msg = timeclock.clock_out(nombre, grupo, tipo=timeclock.TIPO_GENERAL, usuario=usuario)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    else:
        if st.button("🟢 Clock IN jornada", use_container_width=True, key="cd_gen_in", type="primary"):
            ok, msg = timeclock.clock_in(nombre, "", "", grupo, tipo=timeclock.TIPO_GENERAL, usuario=usuario)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.markdown("---")

    # ── Segmento por proyecto ──
    st.markdown("#### 🏗 Proyecto que estás atendiendo")
    if not gen:
        st.info("Primero abre la **jornada general** para poder fichar a un proyecto.")
        return

    proys = []
    try:
        proys = projects_data.list_projects(grupo=grupo)
    except Exception:
        proys = []
    nombres = [p.get("Nombre") for p in proys] or []
    _ids    = {str(p.get("Nombre", "")): str(p.get("ID", "")) for p in proys}

    if prj:
        st.success(f"🟢 Atendiendo **{prj['proyecto'] or '—'}** desde {prj['clock_in']}")
        _chronometer(prj["clock_in"], "⏱ En este proyecto:", color="#1e8449")
        c1, c2 = st.columns(2)
        if c1.button("🔴 Clock OUT proyecto", use_container_width=True, key="cd_prj_out"):
            ok, msg = timeclock.clock_out(nombre, grupo, tipo=timeclock.TIPO_PROYECTO, usuario=usuario)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
        # Cambio de proyecto en 1 toque
        opts = [n for n in nombres if n != prj["proyecto"]]
        if opts:
            nuevo = c2.selectbox("Cambiar a otro proyecto", ["—"] + opts, key="cd_switch_sel")
            if c2.button("🔄 Cambiar de proyecto", use_container_width=True, key="cd_switch"):
                if nuevo and nuevo != "—":
                    ok, msg = timeclock.switch_project(nombre, grupo, nuevo,
                                                       usuario=usuario,
                                                       new_pid=_ids.get(nuevo, ""))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
    else:
        if nombres:
            sel = st.selectbox("Proyecto al que le prestas servicio",
                               [_VACIO] + nombres, key="cd_prj_sel")
            sel = "" if sel == _VACIO else sel
        else:
            sel = st.text_input("Proyecto (no hay proyectos en el grupo, escribe uno)", key="cd_prj_txt")
        if st.button("🟢 Clock IN proyecto", use_container_width=True, key="cd_prj_in"):
            if not sel:
                st.error("Elige el proyecto.")
            else:
                ok, msg = timeclock.clock_in(nombre, sel, "", grupo,
                                             tipo=timeclock.TIPO_PROYECTO,
                                             usuario=usuario,
                                             proyecto_id=_ids.get(sel, ""))
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    st.markdown("---")
    st.caption("🔒 Tus fichajes son privados. La administración ve el resumen de horas del grupo.")
