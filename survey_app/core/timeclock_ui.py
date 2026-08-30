"""
UI de la pestaña de fichaje (clock in / clock out).
La identidad viene del login; ya no se pide usuario + PIN.

DOS relojes para TODOS los roles (v150): la **jornada general** (el tiempo
pagado) y el **segmento de proyecto** (a qué se imputa). De ahí sale
`sin_asignar` = jornada − Σproyectos, que son traslados y espera.

Hasta v149 solo el conductor tenía los dos y el resto un único reloj de
proyecto, lo que producía datos incoherentes (gente con horas de proyecto y 0
de jornada). Ahora hay UNA función en vez de dos que divergían.
"""
from datetime import datetime

from core.i18n import t

import pandas as pd
import streamlit as st

from core import flash
import streamlit.components.v1 as components

from core import timeclock
from core import projects as projects_data
from core import ui_common as ui
from core import clock
# v374: el recordatorio del Pre-Start del día. Sin ciclo: `prestart` importa
# `timeclock`/`clock`/`num`, nunca esta UI.
from core import prestart

_AZUL, _VERDE, _GRIS, _ROJO = "#1a3a5c", "#1e8449", "#6b7280", "#c0392b"


def _chronometer(clock_in_str, label="In progress", color=_VERDE, key="chrono"):
    """Cronómetro en vivo (client-side): cuenta desde el Clock In, sin recargar."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    components.html(
        '<div style="display:flex;align-items:baseline;gap:10px;'
        'font-family:Arial,Helvetica,sans-serif;">'
        f'<span style="font-size:12px;color:#6b7280;">{label}</span>'
        f'<span id="{key}" style="font-size:34px;font-weight:800;'
        f'font-family:\'Courier New\',monospace;color:{color};letter-spacing:1px;">'
        '00:00:00</span></div>'
        "<script>"
        f"var e={e0};"
        "function f(s){var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),x=s%60;"
        "return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'"
        "+String(x).padStart(2,'0');}"
        f"var el=document.getElementById('{key}');el.textContent=f(e);"
        "setInterval(function(){e++;el.textContent=f(e);},1000);"
        "</script>",
        height=52,
    )


def _chrono_mini(clock_in_str, label, color, key):
    """Cronómetro compacto para el sidebar (misma técnica JS que _chronometer)."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    components.html(
        '<div style="font-family:Arial,Helvetica,sans-serif;line-height:1.1;">'
        f'<div style="font-size:11px;color:#6b7280;white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;">{label}</div>'
        f'<span id="{key}" style="font-size:21px;font-weight:800;'
        f"font-family:'Courier New',monospace;color:{color};letter-spacing:.5px;\">"
        '00:00:00</span></div>'
        "<script>"
        f"var e={e0};"
        "function f(s){var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),x=s%60;"
        "return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'"
        "+String(x).padStart(2,'0');}"
        f"var el=document.getElementById('{key}');el.textContent=f(e);"
        "setInterval(function(){e++;el.textContent=f(e);},1000);"
        "</script>",
        height=44,
    )


def _ir_a_prestart():
    """Salta a la pantalla del Pre-Start, que NO está en el mismo sitio según el rol.

    ⚠️ Para el CAMPO es sección propia (`prestart`, v154: es su acción diaria y
    enterrarla un nivel le costaría un toque cada mañana en el móvil); para el
    admin es una sub-pestaña de Herramientas. El ID de la sub lleva el emoji a
    propósito: es el IDENTIFICADOR que usa el matching (v232), no un adorno.
    """
    from core import home_ui as _home
    if str(st.session_state.get("auth", {}).get("rol", "")) == "campo":
        _home.navegar("prestart")                       # `navegar` ya hace el rerun
    else:
        _home.navegar("herramientas", "🦺 Pre-Start")


def _ps_descartar():
    """Deja de recordar el Pre-Start de esta obra en lo que queda de sesión."""
    p = st.session_state.get("_ps_aviso") or {}
    pid = str(p.get("pid", ""))
    if pid:
        st.session_state[f"_ps_visto_{pid}"] = True
    st.session_state.pop("_ps_aviso", None)


@st.dialog(t(":material/health_and_safety: Today's Pre-Start is missing"), width="small",
           on_dismiss=_ps_descartar)
def _dialogo_prestart(obra: str):
    """Pop-up tras fichar cuando la obra no tiene Pre-Start del día (v374/v375)."""
    st.markdown(f"You have just clocked in to **{obra}** and there is still "
                "**no Pre-Start** recorded on that site today.")
    st.caption(t("It is the safety talk before starting: one per site per day. If you have already held it, record it so the signed PDF exists."))
    c1, c2 = st.columns(2)
    if c1.button(t(":material/health_and_safety: Do it now"), type="primary",
                 width="stretch", key="ps_dlg_ir"):
        _ps_descartar()
        _ir_a_prestart()
    if c2.button(t("Not now"), width="stretch", key="ps_dlg_no"):
        _ps_descartar()
        st.rerun()


def _pend_firma_de(pid, grupo) -> dict:
    """El Pre-Start de hoy de esa obra que a MÍ me falta firmar, o {} (v403)."""
    a = st.session_state.get("auth", {}) or {}
    try:
        return prestart.pendiente_de_firma(pid, grupo,
                                           a.get("nombre") or a.get("usuario", "")) or {}
    except Exception:
        return {}


@st.dialog(t(":material/draw: Sign today's Pre-Start"), width="small",
           on_dismiss=_ps_descartar)
def _dialogo_firmar(obra: str, quien: str = ""):
    """Pop-up cuando la charla YA está hecha pero tú no la has firmado (v403)."""
    st.markdown(f"You have just clocked in to **{obra}**. Today's safety talk is already "
                "recorded, but **you are not among those who signed it**.")
    st.caption(t("The attendee list is the record of who received the talk. Your "
                 "signature is added to that same Pre-Start, on an annex sheet with "
                 "its time.")
               + (f" {t('Recorded by')} {quien}." if quien else ""))
    c1, c2 = st.columns(2)
    if c1.button(t(":material/draw: Sign it now"), type="primary",
                 width="stretch", key="ps_dlgf_ir"):
        _ps_descartar()
        _ir_a_prestart()
    if c2.button(t("Not now"), width="stretch", key="ps_dlgf_no"):
        _ps_descartar()
        st.rerun()


def aviso_prestart_pendiente(grupo: str = ""):
    """El modal, evaluado como CONDICIÓN de estado y no como evento de un solo uso.

    ⚠️ v375 — FALLO REAL, visto en producción y no en la mini-app: el modal salía y
    **se cerraba solo**. La v374 consumía la bandera con `pop`, así que se pintaba en
    esa pasada y desaparecía en la siguiente. Y en la app real SIEMPRE hay una pasada
    siguiente justo ahí: los cronómetros del sidebar son `components.html` y al
    MONTARSE disparan un rerun — y solo existen en el estado «fichado», que es
    exactamente cuando el modal debe verse. La mini-app no los tenía, por eso dio OK.
    Evaluándolo como condición, cualquier rerun lo vuelve a pintar.

    Se deja de mostrar cuando: se descarta (los dos botones y la X, vía `on_dismiss`)
    o el Pre-Start ya está hecho.

    ⚠️ Va llamada al TOP LEVEL del script (desde `app.py`), NO dentro de
    `with st.sidebar:`: en Streamlit manda el contenedor activo.
    """
    p = st.session_state.get("_ps_aviso") or {}
    pid, nombre = str(p.get("pid", "")), str(p.get("nombre", ""))
    if not pid or st.session_state.get(f"_ps_visto_{pid}"):
        return
    _g = grupo or p.get("grupo", "")
    # ⚠️ El `try` cubre SOLO la consulta, no el diálogo. Antes envolvía las dos cosas y
    # eso tenía un modo de fallo feo: si algo reventaba al pedir la firma, se caía al
    # diálogo de «Falta el Pre-Start» y se le decía a alguien que la charla no estaba
    # hecha cuando sí lo estaba — invitándole a emitir un SEGUNDO documento del día,
    # que es justo lo que v403 viene a evitar. Lo destapó el guardián de v375.
    try:
        _hecho = prestart.hecho_hoy(pid, _g)
    except Exception:
        _hecho = False
    if _hecho:
        # v403: «ya lo hicieron» dejó de ser motivo suficiente para callarse. Si la
        # charla está hecha pero yo no la firmé, el aviso no desaparece: cambia de
        # motivo. Hasta v402 aquí se hacía `pop` y quien llegaba después de la charla
        # no volvía a saber nada de ella.
        _pf = _pend_firma_de(pid, _g)          # ya devuelve {} si algo falla
        if not _pf:
            st.session_state.pop("_ps_aviso", None)
            return
        _dialogo_firmar(nombre or t("this site"), str(_pf.get("facilitador", "")))
        return
    _dialogo_prestart(nombre or t("this site"))


def _chip_prestart(pid, nombre_obra, grupo):
    """Recordatorio PERSISTENTE mientras falte el Pre-Start de esa obra.

    El modal se puede cerrar y perderse; esto se queda en el sidebar hasta que el
    Pre-Start esté hecho. `hecho_hoy` sale de registros ya cacheados (0 llamadas).
    """
    try:
        if prestart.hecho_hoy(pid, grupo):
            # v403: hecha pero sin mi firma → el chip sigue, con otro motivo
            if not _pend_firma_de(pid, grupo):
                return
            st.warning(t(":material/draw: Sign today's **Pre-Start** for this site."))
            if st.button(t(":material/draw: Sign"), width="stretch",
                         key="sb_ps_firmar"):
                _ir_a_prestart()
            return
    except Exception:
        return                       # sin pre-starts configurados: no se estorba
    st.warning(t(":material/warning: Today's **Pre-Start** is missing on this site."))
    if st.button(t(":material/health_and_safety: Do it now"), width="stretch",
                 key="sb_ps_ir"):
        _ir_a_prestart()


def render_sidebar_chrono():
    """FICHAJE en el sidebar: cronómetros en vivo + fichar y cerrar desde aquí (v374).

    v202 lo dejó como MIRADOR («solo muestra; el fichaje se gestiona en la pestaña»)
    y solo aparecía si ya estabas fichado — o sea, que para la acción más repetida
    del día había que ir a la sección. Ahora:
      · sin fichar → botón de tu asignación de hoy (1 toque) + selector del resto;
      · fichado    → los cronómetros + salir del proyecto / cerrar la jornada;
      · y el recordatorio del Pre-Start del día mientras falte.

    ⚠️ Todo mensaje va por `flash`: estas acciones terminan en `st.rerun()`, que
    descarta los deltas de la pasada (v365) — un `st.success` aquí no se vería nunca.
    """
    if not timeclock.is_configured():
        return
    a = st.session_state.get("auth", {})
    nombre  = a.get("nombre") or a.get("usuario") or ""
    usuario = a.get("usuario", "")
    grupo   = a.get("grupo", "")
    rol     = a.get("rol", "")
    if not (nombre or usuario):
        return
    try:
        sess = timeclock.open_sessions(nombre, grupo, usuario)
    except Exception:
        return
    gen = sess.get(timeclock.TIPO_GENERAL)
    prj = sess.get(timeclock.TIPO_PROYECTO)

    if gen or prj:
        _sidebar_fichado(nombre, usuario, grupo, gen, prj)
    else:
        _sidebar_sin_fichar(nombre, usuario, grupo, rol)
    st.markdown("---")


def _sidebar_fichado(nombre, usuario, grupo, gen, prj):
    """Estás fichado: cronómetros + las dos salidas + el aviso del Pre-Start."""
    st.markdown(t("###### :material/schedule: CLOCKED IN"))
    # ⚠️ v375: la etiqueta del cronómetro va DENTRO de HTML crudo (`components.html`),
    # donde `:material/...:` no es nada — es sintaxis de markdown de Streamlit. Desde
    # la migración de iconos (v233) se veía el literal «:material/schedule: Jornada»
    # en el sidebar. Se vio mirando la pantalla en producción, no leyendo el código.
    if gen:
        _chrono_mini(gen["clock_in"], t("Workday"), _AZUL, "sb_chrono_gen")
    if prj:
        _pn = str(prj.get("proyecto") or t("Project")).replace("&", "&amp;").replace("<", "&lt;")
        _chrono_mini(prj["clock_in"], _pn, _VERDE, "sb_chrono_prj")
        if st.button(t(":material/cancel: Leave the project"), width="stretch",
                     key="sb_tc_prj_out"):
            ok, msg = timeclock.clock_out(nombre, grupo,
                                          tipo=timeclock.TIPO_PROYECTO, usuario=usuario)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    if gen:
        _lbl = (t("Close the workday") if not prj else t("Close workday and project"))
        if st.button(f":material/logout: {_lbl}", width="stretch",
                     key="sb_tc_gen_out"):
            ok, msg = timeclock.cerrar_jornada(nombre, grupo, usuario)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
    if prj:
        _chip_prestart(str(prj.get("proyecto_id", "") or ""),
                       str(prj.get("proyecto", "") or ""), grupo)


def _sidebar_sin_fichar(nombre, usuario, grupo, rol):
    """Sin fichar: la asignación de hoy a un toque, y el resto en un selector.

    ⚠️ El proyecto SIEMPRE de una lista y sin preselección silenciosa (v139/v150):
    escribirlo a mano dejaba el `ProyectoID` vacío y esas horas se caían del costo
    de mano de obra sin ningún aviso (v145).
    """
    st.markdown(t("###### :material/schedule: TIME CLOCK"))
    try:
        proys, _propios = _proyectos_para(rol, usuario, grupo)
    except Exception:
        proys = []
    if not proys:
        # Sin obras que imputar, al menos que pueda abrir su jornada (el tiempo pagado).
        if st.button(t(":material/play_circle: Open workday"), width="stretch",
                     type="primary", key="sb_tc_gen_in"):
            ok, msg = timeclock.clock_in(nombre, "", "", grupo,
                                         tipo=timeclock.TIPO_GENERAL, usuario=usuario)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
        return

    from core import projects as _P
    idmap = {_lbl: _pid for _pid, _lbl in _P.etiqueta_proyectos(proys).items()}
    # ⚠️ El NOMBRE limpio va aparte de la etiqueta: la etiqueta puede llevar el ID
    # detrás (`prueba (PRJ-0007)`) y `fichar_proyecto` lo escribe TAL CUAL en la
    # columna `Proyecto` de la hoja — el fallo que v308 tuvo que corregir.
    nom_de = {str(p.get("ID", "")): str(p.get("Nombre", "")) for p in proys}

    # ── Atajo: tu asignación de hoy (del tablero) ──
    # Acción EXPLÍCITA (dice a qué fichará), no una preselección silenciosa (v138).
    _hechos = set()
    try:
        from core import roster
        if roster.is_configured():
            for _a in roster.asignaciones_dia(grupo, usuario):
                _rpid = (_a or {}).get("proyecto_id", "")
                if not _rpid or _rpid in _hechos or _rpid not in idmap.values():
                    continue
                _hechos.add(_rpid)
                if st.button(f"{t(':material/check_circle: Clock in to')} {_a['etiqueta']}",
                             width="stretch", type="primary",
                             key=f"sb_tc_roster_{_rpid}"):
                    _fichar(nombre, nom_de.get(_rpid, ""), grupo, usuario, _rpid)
    except Exception:
        pass
    if _hechos:
        st.caption(t("Your assignment for today. A different site?"))

    _pid = ui.elegir(t("Project"), idmap, key="sb_tc_prj_sel", vacio=t("— pick the site —"))
    if st.button(t(":material/check_circle: Clock in"), width="stretch",
                 type=("secondary" if _hechos else "primary"),
                 key="sb_tc_prj_in", disabled=(_pid is None)):
        _fichar(nombre, nom_de.get(_pid, ""), grupo, usuario, _pid)


def _fichar(nombre, nom_obra, grupo, usuario, pid):
    """Ficha al proyecto y deja pendiente el aviso del Pre-Start si falta.

    ⚠️ El aviso se deja como BANDERA y lo pinta `aviso_prestart_pendiente()` en la
    pasada siguiente: abrir el modal aquí no serviría de nada porque el
    `st.rerun()` de abajo descarta los deltas de esta pasada (v365).
    """
    ok, msg, auto = timeclock.fichar_proyecto(nombre, nom_obra, grupo, usuario, pid)
    if not ok:
        st.error(msg)
        return
    flash.exito(msg + (t("  :material/schedule: Your workday was opened too.") if auto else ""))
    try:
        if not prestart.hecho_hoy(pid, grupo):
            st.session_state["_ps_aviso"] = {"pid": pid, "nombre": nom_obra, "grupo": grupo}
            # Re-armar: si lo descartaste antes y vuelves a fichar aquí, se recuerda.
            st.session_state.pop(f"_ps_visto_{pid}", None)
    except Exception:
        pass                          # sin pre-starts configurados: no se estorba
    st.rerun()


def _tarjeta(titulo, valor, pie="", color=None, activo=False):
    """Tarjeta de estado, mismo lenguaje visual que los KPI de los proyectos."""
    borde = f"border-left:4px solid {color};" if (activo and color) else ""
    col = f"color:{color};" if color else ""
    return (
        '<div style="background:#ffffff;border:1px solid #e6e9ef;border-radius:12px;'
        f'padding:12px 14px;flex:1;min-width:132px;{borde}">'
        f'<div style="font-size:12px;color:#6b7280;line-height:1.2;">{titulo}</div>'
        f'<div style="font-size:26px;font-weight:700;margin-top:2px;{col}">{valor}</div>'
        + (f'<div style="font-size:11px;color:#667080;margin-top:2px;">{pie}</div>'
           if pie else "")
        + "</div>")


def _es_hoy(clock_in_str) -> bool:
    try:
        return (datetime.strptime(str(clock_in_str), timeclock.FMT).date()
                == clock.now().date())
    except Exception:
        return True


def _aviso_olvido(nombre, grupo, usuario, sess):
    """Sesión abierta de un día anterior: la cierra a la hora que el usuario indique.

    Cerrarla «ahora» registraría como trabajadas todas las horas de la noche que
    nadie hizo. Por eso se pide la hora REAL de fin (v164) y se cierra con ella.
    """
    from datetime import datetime as _dt, timedelta as _td
    stale = {tipo: s for tipo, s in sess.items()
             if s and not _es_hoy(s["clock_in"])}
    if not stale:
        return
    lineas, ci_min = [], None
    for tipo, s in stale.items():
        etq = (t("general workday") if tipo == timeclock.TIPO_GENERAL
               else f"{t('project')} «{s['proyecto'] or '—'}»")
        lineas.append(f"- **{etq}** {t('open since')} **{s['clock_in']}**")
        try:
            # ⚠️ NO llamar `t` a esta variable: taparía la función de idioma en el
            # ámbito ENTERO de la función y las etiquetas de arriba darían
            # UnboundLocalError (el fallo del glosario de v437).
            _ci = _dt.strptime(s["clock_in"], timeclock.FMT)
            ci_min = _ci if ci_min is None or _ci < ci_min else ci_min
        except Exception:
            pass
    st.warning(t(":material/warning: You have time entries from a previous day **still open**:\n")
               + "\n".join(lineas)
               + t("\n\nClose them stating **what time you actually finished** — "
                   "otherwise the overnight hours would count as worked."))
    sugerido = min(ci_min + _td(hours=8), clock.now()) if ci_min else clock.now()
    c1, c2 = st.columns(2)
    d_fin = c1.date_input(t("Day you finished"), value=sugerido.date(), key="olv_d")
    t_fin = c2.time_input(t("Time"), value=sugerido.time().replace(second=0, microsecond=0),
                          key="olv_t")
    fin = _dt.combine(d_fin, t_fin)
    ok_rango = ci_min is not None and ci_min < fin <= clock.now()
    if not ok_rango:
        st.caption(t(":orange[:material/warning:] The finish time must be between the clock-in and now."))
    if st.button(t(":material/cancel: Close forgotten session"), key="olv_btn", width="stretch",
                 disabled=not ok_rango):
        for tipo in stale:
            timeclock.clock_out(nombre, grupo, tipo=tipo, usuario=usuario, out_ts=fin)
        flash.exito(t("Session closed at the time given."))
        st.rerun()


def _proyectos_para(rol, usuario, grupo):
    """Proyectos que esta persona puede fichar. Devuelve (lista, son_suyos).

    ⚠️ Siempre una LISTA, nunca texto libre. Escribir el proyecto a mano dejaba
    el `ProyectoID` vacío (v145) y entonces las horas dependían de que el nombre
    coincidiera exacto: con un dedazo **no contaban para ningún proyecto** y
    desaparecían del costo de mano de obra, sin ningún aviso.

    ⚠️ v422 — quién puede fichar en una LOCALIZACIÓN interna (oficina/almacén), que es
    distinto de quién puede fichar en una obra. Dos vías, y solo dos:

      1. **Perfil de oficina** = estar asignado de forma permanente a ella
         (`CampoAsignados`). No hay rol nuevo ni columna nueva: el mecanismo que ya
         decide qué proyectos ve cada quien sirve igual, y un almacenero no puede ser
         rol `administrador` porque vería las finanzas.
      2. **Asignado puntualmente por la planificación**: si el roster le pone hoy esa
         localización, la ve HOY. Se añade aquí, al selector, y no solo como el botón
         de atajo — si no, quien pasa la mañana en el almacén tiene que acordarse de
         pulsarlo antes de que el día avance.

    ⚠️ Y el FALLBACK deja de regalarlas: un usuario de campo sin ninguna asignación
    recibía **todos** los proyectos del grupo, así que la oficina se le colaría a
    cualquiera. Ese agujero ya existía para las obras; aquí se cierra al menos para lo
    interno, que es lo que se acaba de crear.
    """
    try:
        _hoy = _asignadas_hoy(usuario, grupo)
        if rol == "campo":
            asignados = projects_data.list_projects_for_field(
                usuario, grupo=grupo, incluir_internos=True)
            if asignados or _hoy:
                return _mezclar(asignados, _hoy), True
            # Sin nada asignado: las obras del grupo, NUNCA las localizaciones.
            return projects_data.list_projects(grupo=grupo), False
        # Gestión (administrador/propietario) sí ficha en la oficina.
        if rol == "propietario":
            return projects_data.list_projects(incluir_internos=True), True
        return projects_data.list_projects(grupo=grupo, incluir_internos=True), True
    except Exception:
        return [], True


def _asignadas_hoy(usuario, grupo) -> list:
    """Proyectos que el ROSTER le asigna hoy a esta persona (v422).

    Es la segunda vía de acceso a una localización: «asignado en un momento
    particular mediante la planificación». Sale de `roster.asignaciones_dia`, el
    mismo dato que ya alimenta el atajo de v274/v374 → **0 lecturas nuevas**.
    """
    out = []
    try:
        from core import roster
        if not roster.is_configured():
            return []
        for _a in roster.asignaciones_dia(grupo, usuario):
            _pid = str(_a.get("proyecto_id") or "").strip()
            if not _pid:
                continue
            _p = projects_data.get_project(_pid)
            if _p and str(_p.get("Grupo", "")) == str(grupo):
                out.append(_p)
    except Exception:
        return []
    return out


def _mezclar(a, b) -> list:
    """Une dos listas de proyectos sin repetir, conservando el orden (a manda)."""
    vistos, out = set(), []
    for p in list(a) + list(b):
        pid = str(p.get("ID", ""))
        if pid and pid not in vistos:
            vistos.add(pid)
            out.append(p)
    return out


def render_timeclock_tab():
    st.markdown(t("### :material/schedule: Time clock"))
    if not timeclock.is_configured():
        st.warning(t(":material/warning: Time tracking is not connected to Google Sheets yet. Configure the Secrets."))
        return

    a       = st.session_state.get("auth", {})
    rol     = a.get("rol", "")
    nombre  = a.get("nombre") or a.get("usuario") or ""
    usuario = a.get("usuario", "")
    grupo   = a.get("grupo", "")

    sess = timeclock.open_sessions(nombre, grupo, usuario)
    gen  = sess.get(timeclock.TIPO_GENERAL)
    prj  = sess.get(timeclock.TIPO_PROYECTO)
    hoy  = timeclock.resumen_hoy(nombre, grupo, usuario)

    st.caption(f"**{nombre}**" + (f"  ·  {t('group')} **{grupo}**" if grupo else "")
               + t("  ·  your time entries are private."))
    _aviso_olvido(nombre, grupo, usuario, sess)

    # ── Estado: una FRANJA, no una tarjeta KPI (v308) ──
    # "Sin fichar" no es una cifra y competía visualmente con las horas; además, sin
    # haber fichado, la pantalla eran cuatro tarjetas a 0.00. Ahora el estado es una
    # banda de color arriba y las tarjetas quedan solo para lo que son números.
    _est = (t("On a project") if prj else
            (t("Workday open, no project") if gen else t("Not clocked in")))
    _col = _VERDE if prj else (_AZUL if gen else _GRIS)
    _det = (f"{prj['proyecto'] or '—'} · {t('since')} {prj['clock_in'][11:16]}" if prj else
            (f"{t('since')} {gen['clock_in'][11:16]}" if gen else
             t("open the workday or clock straight in to a project")))
    st.markdown(
        f'<div style="border-left:4px solid {_col};background:#f8fafc;border-radius:8px;'
        'padding:9px 14px;margin-bottom:12px;">'
        f'<span style="font-weight:700;color:{_col};font-size:16px;">{_est}</span>'
        f'<span style="color:#6b7280;font-size:12px;"> · {_det}</span></div>',
        unsafe_allow_html=True)

    # Semana en curso (v308): lo que de verdad quiere saber quien ficha. Sale de los
    # mismos registros cacheados → 0 lecturas nuevas.
    try:
        sem = timeclock.resumen_semana(nombre, grupo, usuario)
    except Exception:
        sem = {"general": 0.0, "proyecto": 0.0, "dias": 0}
    tarj = [_tarjeta(t("Today's workday"), f"{hoy['general']:.2f} h",
                     t("the paid time"), _AZUL, bool(gen)),
            _tarjeta(t("Charged to projects"), f"{hoy['proyecto']:.2f} h",
                     f"{len(hoy['por_proyecto'])} {t('project(s)')}", _VERDE, bool(prj)),
            _tarjeta(t("Unassigned"), f"{hoy['sin_asignar']:.2f} h",
                     t("travel, waiting or a project not clocked in"),
                     _ROJO if hoy["sin_asignar"] > 2 else None),
            _tarjeta(t("This week"), f"{sem['general']:.2f} h",
                     f"{t('Monday to today')} · {sem['dias']} {t('day(s)')}", _AZUL)]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── Las DOS acciones, lado a lado (v308) ──────────────────────
    # Antes iban apiladas y separadas por una línea, con los botones estirados a todo
    # el ancho. ⚠️ En móvil —donde el campo usa esto— Streamlit apila las columnas
    # solo, así que no se pierde nada; en PC se acaba el scroll y el botón de 1350 px.
    col_jor, col_prj = st.columns(2, gap="large")

    # ── Jornada general ──
    with col_jor:
        st.markdown(t("#### :material/schedule: Workday"))
        if gen:
            _chronometer(gen["clock_in"], "Llevas abierta", _AZUL, "chrono_gen")
            st.caption(f"{t('Since')} {gen['clock_in'][11:16]}."
                       + (t("  Closing it also closes the project in progress.") if prj else ""))
            if st.button(t(":material/cancel: Close the workday"), width="stretch", key="tc_gen_out"):
                ok, msg = timeclock.cerrar_jornada(nombre, grupo, usuario)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            st.caption(t("The workday is your working time for the day. It opens by itself when you clock in to a project, or you can open it here."))
            if st.button(t(":material/check_circle: Open workday"), width="stretch", key="tc_gen_in",
                         type="primary"):
                ok, msg = timeclock.clock_in(nombre, "", "", grupo,
                                             tipo=timeclock.TIPO_GENERAL, usuario=usuario)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # ── Segmento por proyecto ──
    _prj_ctx = col_prj
    with _prj_ctx:
        st.markdown(t("#### :material/apartment: Project"))
        proys, propios = _proyectos_para(rol, usuario, grupo)
        # ⚠️ Un dict comprehension por NOMBRE descarta homonimos en silencio y ese
        # proyecto se volveria imposible de fichar (mismo fallo que en v147). El
        # nombre puede repetirse: `create_project` solo AVISA de duplicados.
        # v306: el desempate estaba escrito AQUI a mano y solo marcaba el segundo homonimo
        # (el primero se quedaba sin ID, asi que seguian sin poder distinguirse). Ahora sale
        # de `P.etiqueta_proyectos`, la misma que usan Panel/Facturas/Inventario.
        from core import projects as _P
        idmap = {_lbl: _pid for _pid, _lbl in _P.etiqueta_proyectos(proys).items()}
        # ⚠️ v308: el NOMBRE limpio, aparte de la etiqueta. La etiqueta puede llevar el ID
        # detrás (`prueba (PRJ-0007)`) y se estaba pasando como nombre a `fichar_proyecto`,
        # que lo escribe TAL CUAL en la columna `Proyecto` de la hoja → el fichaje quedaba
        # con un nombre inventado. No rompía las cuentas (manda el ProyectoID desde v145),
        # pero el dato guardado tiene que ser el nombre de verdad.
        _nom_de = {str(p.get("ID", "")): str(p.get("Nombre", "")) for p in proys}

        if prj:
            st.markdown(f"You are on **{prj['proyecto'] or '—'}**")
            _chronometer(prj["clock_in"], t("On this project"), _VERDE, "chrono_prj")
            c1, c2 = st.columns(2)
            if c1.button(t(":material/cancel: Leave the project"), width="stretch", key="tc_prj_out"):
                ok, msg = timeclock.clock_out(nombre, grupo,
                                              tipo=timeclock.TIPO_PROYECTO, usuario=usuario)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
            # ⚠️ v308: se excluye el proyecto actual por **ID**, no comparando la etiqueta
            # del desplegable contra el nombre guardado en el fichaje. Con homónimos la
            # etiqueta lleva el ID y el nombre no, así que no coincidían nunca y te ofrecía
            # "cambiar" al proyecto en el que YA estás. `open_sessions` trae `proyecto_id`
            # desde v145 justamente para esto.
            _pid_actual = str(prj.get("proyecto_id", "") or "")
            _otros = {k: v for k, v in idmap.items()
                      if (v != _pid_actual if _pid_actual else k != prj["proyecto"])}
            if _otros:
                with c2:
                    _nuevo = ui.elegir(t("Switch project"), _otros, key="tc_switch",
                                       vacio="— cambiar a… —")
                    if st.button(t(":material/sync: Switch"), width="stretch", key="tc_switch_btn",
                                 disabled=(_nuevo is None)):
                        _nom = _nom_de.get(_nuevo, "")
                        ok, msg = timeclock.switch_project(nombre, grupo, _nom,
                                                           usuario=usuario, new_pid=_nuevo)
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()
        elif not idmap:
            st.info(t("No projects available to clock in to. Ask your administrator to assign you one."))
        else:
            if not propios:
                st.caption(t("You have no projects assigned; your group's projects are shown."))
            # ── Atajo: tu asignación de hoy (del roster) ──
            # Accion EXPLICITA (dice a que fichara), no una preseleccion silenciosa (v138).
            try:
                from core import roster
                if roster.is_configured():
                    _aa = roster.asignaciones_dia(grupo, usuario)   # v274: varias por día
                    _hechos = set()
                    for _a in _aa:
                        _rpid = (_a or {}).get("proyecto_id", "")
                        if not _rpid or _rpid in _hechos or _rpid not in idmap.values():
                            continue
                        _hechos.add(_rpid)
                        _rnom = _nom_de.get(_rpid, "")     # v308: el nombre, no la etiqueta
                        if st.button(f"{t(':material/check_circle: Clock in to')} {_a['etiqueta']} {t('(your assignment for today)')}",
                                     width="stretch", type="primary",
                                     key=f"tc_roster_in_{_rpid}"):
                            ok, msg, auto = timeclock.fichar_proyecto(
                                nombre, _rnom, grupo, usuario, _rpid)
                            if ok:
                                flash.exito(msg + (t("  :material/schedule: Your workday was opened too.") if auto else ""))
                                st.rerun()
                            else:
                                st.error(msg)
                    if _hechos:
                        st.caption(t("Or pick another project below."))
            except Exception:
                pass
            _pid = ui.elegir(t("Which project are you working on?"), idmap, key="tc_prj_sel",
                             vacio=t("— pick the project —"))
            if st.button(t(":material/check_circle: Clock in to the project"), width="stretch", type="primary",
                         key="tc_prj_in", disabled=(_pid is None)):
                _nom = _nom_de.get(_pid, "")               # v308: el nombre, no la etiqueta
                ok, msg, auto = timeclock.fichar_proyecto(nombre, _nom, grupo, usuario, _pid)
                if ok:
                    flash.exito(msg + (t("  :material/schedule: Your workday was opened too.") if auto else ""))
                    st.rerun()
                else:
                    st.error(msg)

    # ── Lo de hoy, por proyecto ──
    if hoy["por_proyecto"]:
        st.markdown("---")
        st.markdown(t("**Charged today**"))
        _tot = sum(hoy["por_proyecto"].values()) or 1
        for nom, h in sorted(hoy["por_proyecto"].items(), key=lambda x: -x[1]):
            st.markdown(
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                f'<div style="width:170px;flex:none;font-size:13px;color:#374151;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{nom}</div>'
                '<div style="flex:1;height:8px;background:#eef1f5;border-radius:20px;">'
                f'<div style="height:8px;width:{100*h/_tot:.0f}%;background:{_VERDE};'
                'border-radius:20px;"></div></div>'
                f'<div style="width:58px;flex:none;text-align:right;font-size:13px;'
                f'font-weight:600;color:#1f2937;">{h:.2f} h</div></div>',
                unsafe_allow_html=True)

    # ── Historial propio ──
    _mios = timeclock.mis_fichajes(nombre, grupo, usuario, 8)
    if _mios:
        with st.expander(t(":material/account_tree: Your latest time entries")):
            st.dataframe(pd.DataFrame([{
                "": t("Workday") if f["tipo"] == timeclock.TIPO_GENERAL else t("Project"),
                t("Project"): f["proyecto"] or "—",
                t("In"): f["entrada"][5:16].replace("-", "/"),
                t("Out"): (f["salida"][11:16] if f["salida"] else t("in progress")),
                t("Hours"): f["horas"],
            } for f in _mios]), hide_index=True, width="stretch")

    st.caption(t(":material/lock: Your time entries are private. Management sees the group's hours summary, not each person's detail."))
