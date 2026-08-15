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

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import timeclock
from core import projects as projects_data
from core import ui_common as ui
from core import clock

_AZUL, _VERDE, _GRIS, _ROJO = "#1a3a5c", "#1e8449", "#6b7280", "#c0392b"


def _chronometer(clock_in_str, label="En curso", color=_VERDE, key="chrono"):
    """Cronómetro en vivo (client-side): cuenta desde el Clock In, sin recargar."""
    e0 = timeclock.elapsed_seconds(clock_in_str)
    components.html(
        '<div style="display:flex;align-items:baseline;gap:10px;'
        'font-family:Arial,Helvetica,sans-serif;">'
        f'<span style="font-size:12.5px;color:#6b7280;">{label}</span>'
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


def render_sidebar_chrono():
    """Cronómetro(s) de fichaje EN VIVO en el sidebar — SOLO si el usuario está fichado
    (v202). Lo llaman admin y campo desde la barra lateral, para verlo desde cualquier
    sección. Solo muestra; el fichaje se sigue gestionando en la pestaña ⏱ Fichaje."""
    if not timeclock.is_configured():
        return
    a = st.session_state.get("auth", {})
    nombre  = a.get("nombre") or a.get("usuario") or ""
    usuario = a.get("usuario", "")
    grupo   = a.get("grupo", "")
    if not (nombre or usuario):
        return
    try:
        sess = timeclock.open_sessions(nombre, grupo, usuario)
    except Exception:
        return
    gen = sess.get(timeclock.TIPO_GENERAL)
    prj = sess.get(timeclock.TIPO_PROYECTO)
    if not (gen or prj):
        return                       # solo cuando estás fichado
    st.markdown("###### :material/schedule: FICHAJE EN CURSO")
    if gen:
        _chrono_mini(gen["clock_in"], ":material/schedule: Jornada", _AZUL, "sb_chrono_gen")
    if prj:
        _pn = str(prj.get("proyecto") or "Proyecto").replace("&", "&amp;").replace("<", "&lt;")
        _chrono_mini(prj["clock_in"], f":material/apartment: {_pn}", _VERDE, "sb_chrono_prj")
    st.markdown("---")


def _tarjeta(titulo, valor, pie="", color=None, activo=False):
    """Tarjeta de estado, mismo lenguaje visual que los KPI de los proyectos."""
    borde = f"border-left:4px solid {color};" if (activo and color) else ""
    col = f"color:{color};" if color else ""
    return (
        '<div style="background:#ffffff;border:1px solid #e6e9ef;border-radius:12px;'
        f'padding:12px 14px;flex:1;min-width:132px;{borde}">'
        f'<div style="font-size:12.5px;color:#6b7280;line-height:1.2;">{titulo}</div>'
        f'<div style="font-size:24px;font-weight:700;margin-top:2px;{col}">{valor}</div>'
        + (f'<div style="font-size:11.5px;color:#9aa7b8;margin-top:2px;">{pie}</div>'
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
    from datetime import datetime as _dt, time as _t, timedelta as _td
    stale = {tipo: s for tipo, s in sess.items()
             if s and not _es_hoy(s["clock_in"])}
    if not stale:
        return
    lineas, ci_min = [], None
    for tipo, s in stale.items():
        etq = ("jornada general" if tipo == timeclock.TIPO_GENERAL
               else f"proyecto «{s['proyecto'] or '—'}»")
        lineas.append(f"- **{etq}** abierta desde **{s['clock_in']}**")
        try:
            t = _dt.strptime(s["clock_in"], timeclock.FMT)
            ci_min = t if ci_min is None or t < ci_min else ci_min
        except Exception:
            pass
    st.warning(":material/warning: Tienes fichaje(s) de un día anterior **sin cerrar**:\n"
               + "\n".join(lineas)
               + "\n\nCiérralos indicando **a qué hora terminaste de verdad** — si no, "
                 "se contarían como trabajadas las horas de la noche.")
    sugerido = min(ci_min + _td(hours=8), clock.now()) if ci_min else clock.now()
    c1, c2 = st.columns(2)
    d_fin = c1.date_input("Día que terminaste", value=sugerido.date(), key="olv_d")
    t_fin = c2.time_input("Hora", value=sugerido.time().replace(second=0, microsecond=0),
                          key="olv_t")
    fin = _dt.combine(d_fin, t_fin)
    ok_rango = ci_min is not None and ci_min < fin <= clock.now()
    if not ok_rango:
        st.caption(":orange[:material/warning:] La hora de fin debe estar entre la entrada y ahora.")
    if st.button(":material/cancel: Cerrar sesión olvidada", key="olv_btn", use_container_width=True,
                 disabled=not ok_rango):
        for tipo in stale:
            timeclock.clock_out(nombre, grupo, tipo=tipo, usuario=usuario, out_ts=fin)
        st.success("Sesión cerrada a la hora indicada.")
        st.rerun()


def _proyectos_para(rol, usuario, grupo):
    """Proyectos que esta persona puede fichar. Devuelve (lista, son_suyos).

    ⚠️ Siempre una LISTA, nunca texto libre. Escribir el proyecto a mano dejaba
    el `ProyectoID` vacío (v145) y entonces las horas dependían de que el nombre
    coincidiera exacto: con un dedazo **no contaban para ningún proyecto** y
    desaparecían del costo de mano de obra, sin ningún aviso.
    """
    try:
        if rol == "campo":
            asignados = projects_data.list_projects_for_field(usuario, grupo=grupo)
            if asignados:
                return asignados, True
            return projects_data.list_projects(grupo=grupo), False
        if rol == "propietario":
            return projects_data.list_projects(), True
        return projects_data.list_projects(grupo=grupo), True
    except Exception:
        return [], True


def render_timeclock_tab():
    st.markdown("### :material/schedule: Fichaje")
    if not timeclock.is_configured():
        st.warning(":material/warning: El fichaje aún no está conectado a Google Sheets. "
                   "Configura los Secrets.")
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

    st.caption(f"**{nombre}**" + (f"  ·  grupo **{grupo}**" if grupo else "")
               + "  ·  tus fichajes son privados.")
    _aviso_olvido(nombre, grupo, usuario, sess)

    # ── Estado: una FRANJA, no una tarjeta KPI (v308) ──
    # "Sin fichar" no es una cifra y competía visualmente con las horas; además, sin
    # haber fichado, la pantalla eran cuatro tarjetas a 0.00. Ahora el estado es una
    # banda de color arriba y las tarjetas quedan solo para lo que son números.
    _est = ("En un proyecto" if prj else
            ("Jornada abierta, sin proyecto" if gen else "Sin fichar"))
    _col = _VERDE if prj else (_AZUL if gen else _GRIS)
    _det = (f"{prj['proyecto'] or '—'} · desde las {prj['clock_in'][11:16]}" if prj else
            (f"desde las {gen['clock_in'][11:16]}" if gen else
             "abre la jornada o ficha directamente a un proyecto"))
    st.markdown(
        f'<div style="border-left:4px solid {_col};background:#f8fafc;border-radius:8px;'
        'padding:9px 14px;margin-bottom:12px;">'
        f'<span style="font-weight:700;color:{_col};font-size:1.02rem;">{_est}</span>'
        f'<span style="color:#6b7280;font-size:12.5px;"> · {_det}</span></div>',
        unsafe_allow_html=True)

    # Semana en curso (v308): lo que de verdad quiere saber quien ficha. Sale de los
    # mismos registros cacheados → 0 lecturas nuevas.
    try:
        sem = timeclock.resumen_semana(nombre, grupo, usuario)
    except Exception:
        sem = {"general": 0.0, "proyecto": 0.0, "dias": 0}
    tarj = [_tarjeta("Jornada de hoy", f"{hoy['general']:.2f} h",
                     "el tiempo pagado", _AZUL, bool(gen)),
            _tarjeta("Imputado a proyectos", f"{hoy['proyecto']:.2f} h",
                     f"{len(hoy['por_proyecto'])} proyecto(s)", _VERDE, bool(prj)),
            _tarjeta("Sin asignar", f"{hoy['sin_asignar']:.2f} h",
                     "traslados, espera o proyecto sin fichar",
                     _ROJO if hoy["sin_asignar"] > 2 else None),
            _tarjeta("Esta semana", f"{sem['general']:.2f} h",
                     f"lunes a hoy · {sem['dias']} día(s)", _AZUL)]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── Las DOS acciones, lado a lado (v308) ──────────────────────
    # Antes iban apiladas y separadas por una línea, con los botones estirados a todo
    # el ancho. ⚠️ En móvil —donde el campo usa esto— Streamlit apila las columnas
    # solo, así que no se pierde nada; en PC se acaba el scroll y el botón de 1350 px.
    col_jor, col_prj = st.columns(2, gap="large")

    # ── Jornada general ──
    with col_jor:
        st.markdown("#### :material/schedule: Jornada")
        if gen:
            _chronometer(gen["clock_in"], "Llevas abierta", _AZUL, "chrono_gen")
            st.caption(f"Desde las {gen['clock_in'][11:16]}."
                       + ("  Al cerrarla se cierra también el proyecto en curso." if prj else ""))
            if st.button(":material/cancel: Cerrar la jornada", use_container_width=True, key="tc_gen_out"):
                ok, msg = timeclock.cerrar_jornada(nombre, grupo, usuario)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            st.caption("La jornada es tu tiempo de trabajo del día. Se abre sola al "
                       "fichar a un proyecto, o puedes abrirla aquí.")
            if st.button(":material/check_circle: Abrir jornada", use_container_width=True, key="tc_gen_in",
                         type="primary"):
                ok, msg = timeclock.clock_in(nombre, "", "", grupo,
                                             tipo=timeclock.TIPO_GENERAL, usuario=usuario)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # ── Segmento por proyecto ──
    _prj_ctx = col_prj
    with _prj_ctx:
        st.markdown("#### :material/apartment: Proyecto")
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
            st.markdown(f"Estás en **{prj['proyecto'] or '—'}**")
            _chronometer(prj["clock_in"], "En este proyecto", _VERDE, "chrono_prj")
            c1, c2 = st.columns(2)
            if c1.button(":material/cancel: Salir del proyecto", use_container_width=True, key="tc_prj_out"):
                ok, msg = timeclock.clock_out(nombre, grupo,
                                              tipo=timeclock.TIPO_PROYECTO, usuario=usuario)
                (st.success if ok else st.error)(msg)
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
                    _nuevo = ui.elegir("Cambiar de proyecto", _otros, key="tc_switch",
                                       vacio="— cambiar a… —")
                    if st.button(":material/sync: Cambiar", use_container_width=True, key="tc_switch_btn",
                                 disabled=(_nuevo is None)):
                        _nom = _nom_de.get(_nuevo, "")
                        ok, msg = timeclock.switch_project(nombre, grupo, _nom,
                                                           usuario=usuario, new_pid=_nuevo)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()
        elif not idmap:
            st.info("No hay proyectos disponibles para fichar. Pídele al administrador "
                    "que te asigne uno.")
        else:
            if not propios:
                st.caption("No tienes proyectos asignados; se muestran los de tu grupo.")
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
                        if st.button(f":material/check_circle: Fichar a {_a['etiqueta']} (tu asignación de hoy)",
                                     use_container_width=True, type="primary",
                                     key=f"tc_roster_in_{_rpid}"):
                            ok, msg, auto = timeclock.fichar_proyecto(
                                nombre, _rnom, grupo, usuario, _rpid)
                            if ok:
                                st.success(msg + ("  :material/schedule: Se abrió también tu jornada." if auto else ""))
                                st.rerun()
                            else:
                                st.error(msg)
                    if _hechos:
                        st.caption("O elige otro proyecto abajo.")
            except Exception:
                pass
            _pid = ui.elegir("¿En qué proyecto vas a trabajar?", idmap, key="tc_prj_sel",
                             vacio="— elige el proyecto —")
            if st.button(":material/check_circle: Fichar al proyecto", use_container_width=True, type="primary",
                         key="tc_prj_in", disabled=(_pid is None)):
                _nom = _nom_de.get(_pid, "")               # v308: el nombre, no la etiqueta
                ok, msg, auto = timeclock.fichar_proyecto(nombre, _nom, grupo, usuario, _pid)
                if ok:
                    st.success(msg + ("  :material/schedule: Se abrió también tu jornada." if auto else ""))
                    st.rerun()
                else:
                    st.error(msg)

    # ── Lo de hoy, por proyecto ──
    if hoy["por_proyecto"]:
        st.markdown("---")
        st.markdown("**Hoy has imputado**")
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
        with st.expander(":material/account_tree: Tus últimos fichajes"):
            st.dataframe(pd.DataFrame([{
                "": "Jornada" if f["tipo"] == timeclock.TIPO_GENERAL else "Proyecto",
                "Proyecto": f["proyecto"] or "—",
                "Entrada": f["entrada"][5:16].replace("-", "/"),
                "Salida": (f["salida"][11:16] if f["salida"] else "en curso"),
                "Horas": f["horas"],
            } for f in _mios]), hide_index=True, use_container_width=True)

    st.caption(":material/lock: Tus fichajes son privados. La administración ve el resumen de "
               "horas del grupo, no el detalle de cada persona.")
