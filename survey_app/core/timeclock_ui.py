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
import html
from datetime import datetime

from core.i18n import t

import pandas as pd
import streamlit as st

from core import flash

import logging

from core import timeclock
from core import projects as projects_data
from core import ui_common as ui
from core import clock
from core import correcciones

logger = logging.getLogger(__name__)
# v374: el recordatorio del Pre-Start del día. Sin ciclo: `prestart` importa
# `timeclock`/`clock`/`num`, nunca esta UI.
from core import prestart
from core import tabla
from core import incrustar
from core import theme
from core.maps import literal_md

_AZUL, _VERDE, _GRIS, _ROJO = "#1a3a5c", "#1e8449", "#6b7280", "#c0392b"


def _chronometer(clock_in_str, label="In progress", color=_VERDE, key="chrono"):
    """Cronómetro en vivo (client-side): cuenta desde el Clock In, sin recargar."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    # ⚠️ v534 · `flex-wrap`: en una columna estrecha (204 px: tableta, o PC con el menú
    # abierto) rótulo + reloj piden 259 px en una línea y el reloj salía CORTADO por la
    # derecha, sin los segundos (visto en producción). Ahora, si no caben, el reloj baja a
    # su propia línea. Sin márgenes del documento (8 px por lado), las dos líneas —13 + 37—
    # caben en los mismos 52 px; con sitio, se ve igual que antes.
    incrustar.dibujo('<body style="margin:0">'
        '<div style="display:flex;flex-wrap:wrap;align-items:baseline;column-gap:10px;'
        'row-gap:0;line-height:1.1;font-family:Arial,Helvetica,sans-serif;">'
        f'<span style="font-size:12px;color:#6b7280;white-space:nowrap;">{label}</span>'
        f'<span id="{key}" style="font-size:34px;font-weight:800;white-space:nowrap;'
        f'font-family:\'Courier New\',monospace;color:{color};letter-spacing:1px;">'
        '00:00:00</span></div>'
        "<script>"
        f"var e={e0};"
        "function f(s){var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),x=s%60;"
        "return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'"
        "+String(x).padStart(2,'0');}"
        f"var el=document.getElementById('{key}');el.textContent=f(e);"
        "setInterval(function(){e++;el.textContent=f(e);},1000);"
        "</script>", 52, ajustar=False)


def _chrono_mini(clock_in_str, label, color, key):
    """Cronómetro compacto para el sidebar (misma técnica JS que _chronometer)."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    incrustar.dibujo('<div style="font-family:Arial,Helvetica,sans-serif;line-height:1.1;">'
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
        "</script>", 44, ajustar=False)


def _ir_a_prestart(pid=""):
    """Salta a la pantalla del Pre-Start, que NO está en el mismo sitio según el rol.

    ⚠️ v623 · `pid`: la obra de la que se habla. Sin él, «Do it now» sobre la obra B dejaba elegida
    la A si ya se estaba en esa pantalla con ella, y el documento se archivaba en la A.

    ⚠️ Para el CAMPO es sección propia (`prestart`, v154: es su acción diaria y
    enterrarla un nivel le costaría un toque cada mañana en el móvil); para el
    admin es una sub-pestaña de Herramientas. El ID de la sub lleva el emoji a
    propósito: es el IDENTIFICADOR que usa el matching (v232), no un adorno.
    """
    from core import home_ui as _home
    if pid:
        st.session_state["_ps_proy_pending"] = str(pid)
    if str(st.session_state.get("auth", {}).get("rol", "")) == "field":
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
    st.markdown(t("You have just clocked in to **{o}** and there is still **no Pre-Start** "
                  "recorded on that site today.", o=literal_md(obra)))
    st.caption(t("It is the safety talk before starting: one per site per day. If you have already held it, record it so the signed PDF exists."))
    c1, c2 = st.columns(2)
    if c1.button(t(":material/health_and_safety: Do it now"), type="primary",
                 width="stretch", key="ps_dlg_ir"):
        _pid = (st.session_state.get("_ps_aviso") or {}).get("pid", "")
        _ps_descartar()
        _ir_a_prestart(_pid)
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
    st.markdown(t("You have just clocked in to **{o}**. Today's safety talk is already recorded, "
                  "but **you are not among those who signed it**.", o=literal_md(obra)))
    st.caption(t("The attendee list is the record of who received the talk. Your "
                 "signature is added to that same Pre-Start, on an annex sheet with "
                 "its time.")
               + (f" {t('Recorded by')} {quien}." if quien else ""))
    c1, c2 = st.columns(2)
    if c1.button(t(":material/draw: Sign it now"), type="primary",
                 width="stretch", key="ps_dlgf_ir"):
        _pid = (st.session_state.get("_ps_aviso") or {}).get("pid", "")
        _ps_descartar()
        _ir_a_prestart(_pid)
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
                _ir_a_prestart(pid)
            return
    except Exception:
        return                       # sin pre-starts configurados: no se estorba
    st.warning(t(":material/warning: Today's **Pre-Start** is missing on this site."))
    if st.button(t(":material/health_and_safety: Do it now"), width="stretch",
                 key="sb_ps_ir"):
        _ir_a_prestart(pid)


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

    if timeclock.olvidos(sess):
        _sidebar_olvido()
    elif gen or prj:
        _sidebar_fichado(nombre, usuario, grupo, gen, prj)
    else:
        _sidebar_sin_fichar(nombre, usuario, grupo, rol)
    st.markdown("---")


def _sidebar_olvido():
    """v621 · Una entrada de un día anterior abierta: ni cronómetro de 33 horas ni botones de
    cerrar «ahora». Lleva a Timeclock, que pide la hora real (`_aviso_olvido`)."""
    st.markdown(t("###### :material/schedule: TIME CLOCK"))
    st.warning(t(":material/warning: You have an entry from a previous day still open."))
    if st.button(t(":material/schedule: Close it now"), width="stretch", type="primary",
                 key="sb_tc_olvido"):
        from core.home_ui import navegar          # perezoso: evita el ciclo
        navegar("fichaje")


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
    nom_de = {str(p.get("ID", "")): str(p.get("Name", "")) for p in proys}

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

    # v621 · Con UNA sola obra propia, un toque: como en la pantalla (v480), que aquí seguía
    # pidiendo elegir de una lista de uno.
    if _propios and len(idmap) == 1 and not _hechos:
        _lbl1, _p1 = next(iter(idmap.items()))
        if st.button(f"{t(':material/check_circle: Clock in to')} {literal_md(_lbl1)}",
                     width="stretch", type="primary", key="sb_tc_solo"):
            _fichar(nombre, nom_de.get(_p1, ""), grupo, usuario, _p1)
        return

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
    _armar_aviso_prestart(pid, nom_obra, grupo)
    st.rerun()


def _armar_aviso_prestart(pid, nom_obra, grupo):
    """Deja pendiente el modal «falta el Pre-Start» de la obra a la que se acaba de fichar.

    ⚠️ v546 · Fichar es UNA acción y se avisa igual venga de donde venga (decisión del
    usuario): hasta aquí solo el menú lateral (v374) dejaba la bandera; fichar desde la
    pantalla de Fichaje —el selector, la obra única, el atajo del roster o «Switch»— no
    sacaba el modal (visto en producción).
    """
    try:
        if not prestart.hecho_hoy(pid, grupo):
            st.session_state["_ps_aviso"] = {"pid": pid, "nombre": nom_obra, "grupo": grupo}
            # Re-armar: si lo descartaste antes y vuelves a fichar aquí, se recuerda.
            st.session_state.pop(f"_ps_visto_{pid}", None)
    except Exception:
        pass                          # sin pre-starts configurados: no se estorba


def _es_hoy(clock_in_str) -> bool:
    try:
        return (datetime.strptime(str(clock_in_str), timeclock.FMT).date()
                == clock.now().date())
    except Exception:
        return True


def _privacidad():
    """⚠️ v621 · Decía que la oficina solo veía el resumen del grupo, y era falso: ve las horas de
    cada persona, en qué obra está y cuánto lleva fichada en vivo. Es un compromiso escrito hacia
    quien ficha."""
    st.caption(t(":material/lock: Other workers cannot see your time entries. The office sees "
                 "your hours and the sites you clock in to."))


def _aviso_olvido(nombre, grupo, usuario, sess) -> bool:
    """Sesión abierta de un día anterior: la cierra a la hora que el usuario indique. True si hay.

    Cerrarla «ahora» registraría como trabajadas todas las horas de la noche que
    nadie hizo. Por eso se pide la hora REAL de fin (v164) y se cierra con ella.
    """
    from datetime import datetime as _dt, timedelta as _td
    stale = timeclock.olvidos(sess)
    if not stale:
        return False
    lineas, ci_min, ci_max = [], None, None
    for tipo, s in stale.items():
        etq = (t("general workday") if tipo == timeclock.TIPO_GENERAL
               else f"{t('project')} «{literal_md(s['proyecto'] or '—')}»")
        # v621 · la fecha DD/MM/YYYY, como en toda la app: salía tal cual se guarda
        lineas.append(f"- **{etq}** {t('open since')} **{timeclock._ts_legible(s['clock_in'])}**")
        try:
            # ⚠️ NO llamar `t` a esta variable: taparía la función de idioma en el
            # ámbito ENTERO de la función y las etiquetas de arriba darían
            # UnboundLocalError (el fallo del glosario de v437).
            _ci = _dt.strptime(s["clock_in"], timeclock.FMT)
            ci_min = _ci if ci_min is None or _ci < ci_min else ci_min
            ci_max = _ci if ci_max is None or _ci > ci_max else ci_max
        except Exception:
            pass
    st.warning(t(":material/warning: You have time entries from a previous day **still open**:\n")
               + "\n".join(lineas)
               + t("\n\nClose them stating **what time you actually finished** — "
                   "otherwise the overnight hours would count as worked."))
    sugerido = (min(max(ci_min + _td(hours=8), ci_max + _td(minutes=1)), clock.now())
                if ci_min else clock.now())
    c1, c2 = st.columns(2)
    d_fin = c1.date_input(t("Day you finished"), value=sugerido.date(), key="olv_d", format="DD/MM/YYYY")
    t_fin = c2.time_input(t("Time"), value=sugerido.time().replace(second=0, microsecond=0),
                          key="olv_t")
    fin = datetime.combine(d_fin, t_fin)
    # ⚠️ v621 · Después de la ÚLTIMA entrada: la jornada y la obra se cierran a la misma hora, y
    # antes de la de la obra (que empieza después) esta quedaría con horas negativas.
    ok_rango = ci_max is not None and ci_max < fin <= clock.now()
    if not ok_rango:
        st.caption(t(":orange[:material/warning:] The finish time must be between the clock-in and now."))
    if st.button(t(":material/cancel: Close forgotten session"), key="olv_btn", width="stretch",
                 disabled=not ok_rango):
        _mal = []
        for tipo in stale:
            _s = stale[tipo]
            _ok, _m = timeclock.clock_out(nombre, grupo, tipo=tipo, usuario=usuario,
                                          out_ts=fin)
            if not _ok:
                _mal.append(_m)
            # ⚠️ Se anota DESPUÉS de cerrar y su fallo no deshace el cierre: la
            # sesión ya estaba sangrando horas contra el reloj y pararla es lo
            # urgente. Si el apunte falla, queda en el log (criterio de v342).
            if _ok:
                try:
                    correcciones.registrar(
                        grupo, usuario, nombre, tipo, _s.get("proyecto", ""),
                        correcciones.CAMPO_OUT, "", fin.strftime(timeclock.FMT),
                        motivo=t("Forgotten clock out (session left open)"))
                except Exception as _e:
                    logger.warning("no se pudo anotar la corrección: %s", _e)
        # ⚠️ v621 · El «cerrado» se decía aunque el cierre hubiera fallado.
        if _mal:
            flash.error(_mal[0])
        else:
            flash.exito(t("Session closed at the time given. Your supervisor will review it."))
        st.rerun()
    return True


def _sesiones_de_hoy(nombre, grupo, usuario) -> list:
    """Los fichajes de HOY de esta persona, abiertos o cerrados."""
    try:
        return [r for r in timeclock.mis_fichajes(nombre, grupo, usuario, limite=20)
                if _es_hoy(r.get("entrada"))]
    except Exception as e:
        logger.warning("_sesiones_de_hoy: %s", e)
        return []


def _corregir_horas(nombre, grupo, usuario, sess):
    """«Se me olvidó fichar»: poner la hora REAL de entrada o de salida.

    Decisiones del usuario (v461): la hora nueva **se aplica ya** y el
    administrador la revisa después; y **solo el mismo día** — lo de ayer ya no se
    toca aquí (la excepción es cerrar una sesión que sigue ABIERTA, que hace
    `_aviso_olvido`, porque esa sigue acumulando horas contra el reloj).
    """
    _hoy = _sesiones_de_hoy(nombre, grupo, usuario)
    _gen = sess.get(timeclock.TIPO_GENERAL)
    _prj = sess.get(timeclock.TIPO_PROYECTO)
    # ⚠️ v546 · CON clave. Sin ella, cuando el aviso verde de arriba aparece o se va
    # (cada acción deja uno, por `flash`), Streamlit crea el desplegable de nuevo y nace
    # CERRADO: tras poner la hora había que reabrirlo para llegar al botón (visto 3 veces
    # en producción; comprobado en una mini-app 1.64 que con clave sigue abierto).
    with st.expander(t("Did you forget to clock in or out?"),
                     icon=":material/schedule_send:", key="tc_corregir"):
        st.caption(t("Put the time you actually started or finished. It applies "
                     "right away and your supervisor reviews it. Today only."))
        # ── (a) Empecé antes de fichar y AÚN NO he fichado ──
        if not _gen and not _prj:
            st.markdown(t("**I started earlier and had not clocked in**"))
            _c1, _c2 = st.columns([2, 1])
            _t0 = _c1.time_input(t("Time I actually started"),
                                 value=clock.now(grupo).time().replace(second=0,
                                                                      microsecond=0),
                                 key="cor_in_t")
            _ini = datetime.combine(clock.today(grupo), _t0)
            _ok_ini = _ini < clock.now(grupo)
            if not _ok_ini:
                st.caption(t(":orange[:material/warning:] That time is still to come."))
            if _c2.button(t(":material/play_circle: Open workday at that time"),
                          key="cor_in_btn", width="stretch", disabled=not _ok_ini):
                _ok, _msg = timeclock.clock_in(
                    nombre, "", "", grupo, tipo=timeclock.TIPO_GENERAL,
                    usuario=usuario, in_ts=_ini)
                if _ok:
                    correcciones.registrar(
                        grupo, usuario, nombre, timeclock.TIPO_GENERAL, "",
                        correcciones.CAMPO_IN,
                        clock.now(grupo).strftime(timeclock.FMT),
                        _ini.strftime(timeclock.FMT),
                        motivo=t("Forgot to clock in"))
                    flash.exito(t("Clocked in at the time given. Your supervisor "
                                  "will review it."))
                else:
                    flash.error(_msg)
                st.rerun()
        # ── (b) Ya fiché, pero con la hora equivocada ──
        if not _hoy:
            return
        st.markdown(t("**Fix the time of one of today's entries**"))
        _et = {}
        for _i, _r in enumerate(_hoy):
            _lab = (f"{_r.get('proyecto') or t('Workday (general)')} · "
                    f"{str(_r.get('entrada'))[11:16]}"
                    + (f" → {str(_r.get('salida'))[11:16]}" if _r.get('salida')
                       else f" → {t('open')}"))
            # ⚠️ Dos fichajes del mismo proyecto entrados en el MISMO minuto dan
            # la misma etiqueta, y un dict la colapsa: una de las dos filas
            # quedaría IMPOSIBLE de corregir, sin ningún error. Es el fallo de
            # v147/v150/v413 — una clave hecha con datos del usuario tiene que ser
            # única DE VERDAD o pierde filas en silencio.
            if _lab in _et:
                _lab = f"{_lab}  ({_i + 1})"
            _et[_lab] = _r
        _sel = ui.elegir(t("Entry"), list(_et), key="cor_sel")
        if not _sel:
            return
        _r = _et[_sel]
        # ⚠️ Solo se ofrece corregir la SALIDA si existe: en una sesión abierta la
        # salida se pone al cerrar, y ofrecer las dos invitaría a inventarse una.
        _campos = [correcciones.CAMPO_IN] + ([correcciones.CAMPO_OUT]
                                             if _r.get("salida") else [])
        # v621 · Con una sola opción no hay nada que preguntar; con dos, el segmentado de la app.
        _cual = (st.radio(t("What was wrong?"), _campos, horizontal=True, key="cpxseg_cor_campo",
                          format_func=lambda c: t(c)) if len(_campos) > 1 else _campos[0])
        _act = str(_r.get("entrada") if _cual == correcciones.CAMPO_IN
                   else _r.get("salida"))
        try:
            _base = datetime.strptime(_act, timeclock.FMT)
        except Exception:
            st.caption(t("That entry has an unreadable time; ask your supervisor."))
            return
        _c1, _c2 = st.columns([2, 1])
        _nt = _c1.time_input(t("Correct time"), value=_base.time().replace(
            second=0, microsecond=0), key="cor_new_t")
        _nuevo = datetime.combine(clock.today(grupo), _nt)
        _motivo = st.text_input(t("Why (optional)"), key="cor_motivo",
                                placeholder=t("I forgot to clock in on arrival…"))
        # La entrada no puede ir por delante de la salida ni al revés.
        _otro = (_r.get("salida") if _cual == correcciones.CAMPO_IN
                 else _r.get("entrada"))
        _valido = _nuevo <= clock.now(grupo)
        if _valido and _otro:
            try:
                _o = datetime.strptime(str(_otro), timeclock.FMT)
                _valido = (_nuevo < _o if _cual == correcciones.CAMPO_IN
                           else _nuevo > _o)
            except Exception:
                pass
        if not _valido:
            st.caption(t(":orange[:material/warning:] The clock in must come before "
                         "the clock out, and neither can be in the future."))
        if st.button(t(":material/save: Apply the correct time"), key="cor_btn",
                     width="stretch", disabled=not _valido):
            _ok, _msg = timeclock.corregir_fichaje(
                grupo=grupo, usuario=usuario, nombre=nombre,
                tipo=_r.get("tipo"), campo=_cual, valor_actual=_act,
                valor_nuevo=_nuevo)
            if _ok:
                correcciones.registrar(
                    grupo, usuario, nombre, _r.get("tipo"), _r.get("proyecto", ""),
                    _cual, _act, _nuevo.strftime(timeclock.FMT), motivo=_motivo)
                flash.exito(t("Time corrected. Your supervisor will review it."))
            else:
                flash.error(_msg)
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
        if rol == "field":
            asignados = projects_data.list_projects_for_field(
                usuario, grupo=grupo, incluir_internos=True)
            if asignados or _hoy:
                return _mezclar(asignados, _hoy), True
            # Sin nada asignado: las obras del grupo, NUNCA las localizaciones.
            return projects_data.list_projects(grupo=grupo), False
        # Gestión (administrador/propietario) sí ficha en la oficina.
        if rol == "owner":
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
            if _p and str(_p.get("Group", "")) == str(grupo):
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


def _fila_hist(f) -> dict:
    """Un fichaje en una fila que quepa en el móvil (v621): antes salían Tipo y Obra delante, y la
    entrada, la salida y las horas se quedaban fuera de la pantalla a 375 px. La obra va la
    última, y la salida lleva su día si no es el de la entrada (decía solo «16:23» del día siguiente)."""
    _e, _s = f["entrada"], f["salida"]
    _h = _s[11:16] if _s[:10] == _e[:10] else f"{_s[8:10]}/{_s[5:7]} {_s[11:16]}"
    return {t("Day"): f"{_e[8:10]}/{_e[5:7]}",
            t("Time"): f"{_e[11:16]} → {_h if _s else t('in progress')}",
            t("Hours"): f"{f['horas']:.2f}" if _s else "—",
            t("Entry"): f["proyecto"] or t("Workday")}


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

    st.caption(f"**{literal_md(nombre)}**" + (f"  ·  {t('group')} **{literal_md(grupo)}**" if grupo else ""))
    # ⚠️ v621 · Con una entrada de otro día abierta, lo ÚNICO que hay es cerrarla: los botones de
    # siempre la cerrarían «ahora» y las tarjetas enseñarían 16 h de hoy que nadie trabajó.
    if _aviso_olvido(nombre, grupo, usuario, sess):
        _privacidad()
        return
    _corregir_horas(nombre, grupo, usuario, sess)

    # ── Estado: una FRANJA, no una tarjeta KPI (v308) ──
    # "Sin fichar" no es una cifra y competía visualmente con las horas; además, sin
    # haber fichado, la pantalla eran cuatro tarjetas a 0.00. Ahora el estado es una
    # banda de color arriba y las tarjetas quedan solo para lo que son números.
    _est = (t("On a project") if prj else
            (t("Workday open, no project") if gen else t("Not clocked in")))
    _col = _VERDE if prj else (_AZUL if gen else _GRIS)
    # v621 · el nombre va dentro de HTML: un «<» se comería el resto de la franja
    _det = (f"{html.escape(prj['proyecto'] or '—')} · {t('since')} {prj['clock_in'][11:16]}" if prj else
            (f"{t('since')} {gen['clock_in'][11:16]}" if gen else
             t("open the workday or clock straight in to a project")))
    st.markdown(
        f'<div style="border-left:4px solid {_col};background:#f8fafc;border-radius:8px;'
        'padding:9px 14px;margin-bottom:12px;">'
        f'<span style="font-weight:700;color:{_col};font-size:16px;">{_est}</span>'
        f'<span style="color:#6b7280;font-size:12px;"> · {_det}</span></div>',
        unsafe_allow_html=True)

    # ── Atajo: «hoy no puedo ir» (v478) ──────────────────────────────────────
    # ⚠️ v478 metio las tres pantallas «mias» del campo bajo un nivel, y avisar de una
    # baja es la UNICA accion urgente de las tres: se usa la mañana que alguien se
    # levanta enfermo, en el movil. v430 la registra al instante justo por eso, asi que
    # el toque que perdio en el menu se devuelve AQUI, que es la pantalla que esa
    # persona abre esa misma mañana.
    # ⚠️ Solo si NO esta fichado: quien ya ficho no va a avisar de una baja, y el
    # boton solo seria ruido en la pantalla que mas se usa.
    # ⚠️ v621 · Ni quien ya ha trabajado hoy: tras cerrar la jornada seguía saliendo.
    if rol == "field" and not gen and not prj and hoy["general"] <= 0 and hoy["proyecto"] <= 0:
        if st.button(t(":material/sick: I cannot make it today — report sick leave"),
                     key="tc_baja", width="stretch"):
            from core.home_ui import navegar          # perezoso: evita el ciclo
            navegar("autogestion", "🌴 Ausencias")

    # ── Las DOS acciones, lado a lado (v308) ──────────────────────
    # Antes iban apiladas y separadas por una línea, con los botones estirados a todo
    # el ancho. ⚠️ En móvil —donde el campo usa esto— Streamlit apila las columnas
    # solo, así que no se pierde nada; en PC se acaba el scroll y el botón de 1350 px.
    # ⚠️ v480 MATIZA esa última frase, con medida: apilarse no cuesta ANCHO, pero sí
    # ALTO — y el alto era el problema. Con las tarjetas delante, este bloque empezaba
    # en y=618 de 812 en un teléfono, o sea que fichar (lo primero que hace el campo
    # cada mañana) quedaba bajo el pliegue. Por eso el resumen se movió DEBAJO. Las dos
    # columnas se quedan como están: esa parte de v308 sigue siendo cierta.
    col_jor, col_prj = st.columns(2, gap="large")

    # ── Jornada general ──
    with col_jor:
        st.markdown(t("#### :material/schedule: Workday"))
        if gen:
            _chronometer(gen["clock_in"], t("Open for"), _AZUL, "chrono_gen")
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
        _nom_de = {str(p.get("ID", "")): str(p.get("Name", "")) for p in proys}

        if prj:
            st.markdown(t("You are on **{p}**", p=literal_md(prj['proyecto'] or '—')))
            _chronometer(prj["clock_in"], t("On this project"), _VERDE, "chrono_prj")
            if st.button(t(":material/cancel: Leave the project"), width="stretch", key="tc_prj_out"):
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
                # ⚠️ v631 · En su propia fila. Iba en la mitad derecha de esta columna, que ya es media
                # pantalla: con el menú abierto a 859 px el selector medía 64 y cortaba los nombres de
                # las obras. En el móvil no se veía, porque ahí las columnas se apilan.
                # v546 · decía «— cambiar a… —», en español y sin `t()`
                _nuevo = ui.elegir(t("Switch project"), _otros, key="tc_switch",
                                   vacio=t("— switch to… —"))
                if st.button(t(":material/sync: Switch"), width="stretch", key="tc_switch_btn",
                             disabled=(_nuevo is None)):
                    _nom = _nom_de.get(_nuevo, "")
                    ok, msg = timeclock.switch_project(nombre, grupo, _nom,
                                                       usuario=usuario, new_pid=_nuevo)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        _armar_aviso_prestart(_nuevo, _nom, grupo)   # otra obra: su charla
                        st.rerun()
        elif not idmap:
            st.info(t("No projects available to clock in to. Ask your administrator to assign you one."))
        else:
            if not propios:
                st.caption(t("You have no projects assigned; your group's projects are shown."))
            # ── Atajo: tu asignación de hoy (del roster) ──
            # Accion EXPLICITA (dice a que fichara), no una preseleccion silenciosa (v138).
            # ⚠️ v480: `_hechos` se crea FUERA del try. Dentro, si el roster no esta
            # configurado o la llamada revienta, no existiria y el bloque de abajo
            # petaria con NameError — el fallo latente de v370/v423.
            _hechos = set()
            try:
                from core import roster
                if roster.is_configured():
                    _aa = roster.asignaciones_dia(grupo, usuario)   # v274: varias por día
                    for _a in _aa:
                        _rpid = (_a or {}).get("proyecto_id", "")
                        if not _rpid or _rpid in _hechos or _rpid not in idmap.values():
                            continue
                        _hechos.add(_rpid)
                        _rnom = _nom_de.get(_rpid, "")     # v308: el nombre, no la etiqueta
                        if st.button(f"{t(':material/check_circle: Clock in to')} {_a['etiqueta']} {t('(your assignment for today)')}",
                                     width="stretch", type="primary",
                                     key=f"tc_roster_in_{_rpid}"):
                            _fichar(nombre, _rnom, grupo, usuario, _rpid)   # v546: = lateral
                    if _hechos:
                        st.caption(t("Or pick another project below."))
            except Exception:
                pass
            # v480 · Con UNA sola obra propia, el desplegable era elegir de una lista de
            # uno: dos toques en el movil para algo sin alternativa. ⚠️ NO se
            # preselecciona —v138 pide aqui una accion EXPLICITA que diga a que se
            # fichara— sino que se usa el MISMO patron del atajo del roster de arriba: un
            # boton que lleva el nombre de la obra. Se exige `propios` porque sin ello
            # «una» puede ser el respaldo del grupo, que no es suya (v422), y `not
            # _hechos` para no repetir el boton que el roster ya puso.
            if propios and len(idmap) == 1 and not _hechos:
                _lbl1 = next(iter(idmap))
                _pid1 = idmap[_lbl1]
                if st.button(f"{t(':material/check_circle: Clock in to')} {literal_md(_lbl1)}",
                             width="stretch", type="primary", key="tc_prj_solo"):
                    _fichar(nombre, _nom_de.get(_pid1, ""), grupo, usuario, _pid1)   # v546
            else:
                _pid = ui.elegir(t("Which project are you working on?"), idmap, key="tc_prj_sel",
                                 vacio=t("— pick the project —"))
                if st.button(t(":material/check_circle: Clock in to the project"), width="stretch", type="primary",
                             key="tc_prj_in", disabled=(_pid is None)):
                    # v308: el nombre, no la etiqueta · v546: la MISMA acción que el lateral
                    _fichar(nombre, _nom_de.get(_pid, ""), grupo, usuario, _pid)

    # ⚠️ v480 · MEDIDO a 375x812 con sesion de campo: estas cuatro tarjetas ocupaban
    # 230 px —el 28% del telefono— enseñando "0.00 h" de un dia que aun no ha empezado, y
    # empujaban «Workday» a y=618 y «Project» a y=759, o sea la accion de CADA MAÑANA
    # bajo el pliegue. ⚠️ Esto matiza lo que dejó escrito v308 aqui mismo —«en movil se
    # apilan solas, asi que no se pierde nada»—: horizontalmente no se pierde nada,
    # verticalmente se pierde la pantalla entera.
    # No se quita NI UNA cifra: se baja el resumen a donde estan las otras cifras del
    # dia (barras por proyecto e historial), que ademas las deja juntas. Criterio de
    # v408: priorizar, no encoger.
    # Semana en curso (v308): lo que de verdad quiere saber quien ficha. Sale de los
    # mismos registros cacheados → 0 lecturas nuevas.
    try:
        sem = timeclock.resumen_semana(nombre, grupo, usuario)
    except Exception:
        sem = {"general": 0.0, "proyecto": 0.0, "dias": 0}
    # v621 · ACTIVAS (eran HTML): cada una baja a lo que cuenta. Dos por fila a cualquier ancho: a
    # 800 px con el menú eran 3 + 1 (v581), y con cuatro cifras 2 + 2 no deja ninguna suelta.
    _K = [("jorn", t("Today's workday"), f"{hoy['general']:.2f} h", t("the paid time")),
          ("proy", t("Charged to projects"), f"{hoy['proyecto']:.2f} h",
           f"{len(hoy['por_proyecto'])} {t('project(s)')}"),
          ("sina", t("Unassigned"), f"{hoy['sin_asignar']:.2f} h",
           t("travel or waiting")),       # v622 · el largo se cortaba a 375 px («…or a proje…»)
          ("sem", t("This week"), f"{sem['general']:.2f} h",
           f"{t('Monday to today')} · {sem['dias']} {t('day(s)')}")]
    if hoy["sin_asignar"] > 2:
        st.markdown("<style>.st-key-cpxkpi_tc_sina button p:nth-child(2):not(:last-child)"
                    "{color:#c0392b!important}</style>", unsafe_allow_html=True)
    st.markdown(theme.por_fila("cpx_tc_kpis", 2), unsafe_allow_html=True)
    with st.container(key="cpx_tc_kpis"):
        for _col, (_s, _l, _v, _pie) in zip(st.columns(len(_K)), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_tc_{_s}", width="stretch"):
                st.session_state["_tc_hist_gen"] = int(st.session_state.get("_tc_hist_gen", 0)) + 1
                st.session_state["_tc_bajar"] = True

    with st.container(key="cpx_tc_detalle"):
        from core import projects_ui as _PU
        _PU._bajar_a("cpx_tc_detalle", "_tc_bajar", bloque="start")
        # ── Lo de hoy, por proyecto ──
        if hoy["por_proyecto"]:
            st.markdown("---")
            st.markdown(t("**Charged today**"))
            _tot = sum(hoy["por_proyecto"].values()) or 1
            for nom, h in sorted(hoy["por_proyecto"].items(), key=lambda x: -x[1]):
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                    f'<div style="width:170px;flex:none;font-size:13px;color:#374151;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(nom)}</div>'
                    '<div style="flex:1;height:8px;background:#eef1f5;border-radius:20px;">'
                    f'<div style="height:8px;width:{100*h/_tot:.0f}%;background:{_VERDE};'
                    'border-radius:20px;"></div></div>'
                    f'<div style="width:58px;flex:none;text-align:right;font-size:13px;'
                    f'font-weight:600;color:#1f2937;">{h:.2f} h</div></div>',
                    unsafe_allow_html=True)

        # ── Historial propio ──
        _mios = timeclock.mis_fichajes(nombre, grupo, usuario, 14)
        if _mios:
            # La clave lleva generación: una tarjeta lo vuelve a abrir aunque se haya cerrado a mano
            _g = int(st.session_state.get("_tc_hist_gen", 0))
            _abrir = _g > 0
            with st.expander(t(":material/account_tree: Your latest time entries"), expanded=_abrir,
                             key=f"tc_exp_hist_{_g}_{_abrir}"):
                st.dataframe(pd.DataFrame([_fila_hist(f) for f in _mios]), hide_index=True,
                             width="stretch", column_config=tabla.cfg(extra={
                                 t("Day"): st.column_config.TextColumn(width=56),
                                 t("Time"): st.column_config.TextColumn(width=112),
                                 t("Hours"): st.column_config.TextColumn(width=56)}))

    _privacidad()
