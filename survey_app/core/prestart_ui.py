"""
Pestaña 📋 Pre-Start diario: el equipo llena la charla de seguridad del día,
se genera el PDF (marca = grupo), se archiva en Drive del proyecto + hoja, y se
abre una alarma del proyecto si hay Near Miss/Hazard o si algún control quedó en
NO (v373).
"""
import io
import logging

import streamlit as st

from core import prestart as PS
from core import projects as P
from core import maps
from core import clock

logger = logging.getLogger(__name__)

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— elige el proyecto —"


def _initials(nombre: str) -> str:
    parts = [w for w in str(nombre or "").split() if w]
    return "".join(w[0].upper() for w in parts[:3])


def _canvas_disponible():
    """El componente de dibujo, o None. Import PEREZOSO a propósito.

    ⚠️ Si el componente falta o falla, el Pre-Start NO se cae: se pide la firma
    tecleando las iniciales, como hasta v382. Una charla de seguridad no se puede
    quedar sin registrar porque una dependencia de terceros no cargue.
    """
    try:
        from streamlit_drawable_canvas import st_canvas
        return st_canvas
    except Exception as e:
        logger.warning("prestart: sin lienzo de firma (%s)", e)
        return None


def _firma_png(res, fondo="#ffffff"):
    """El PNG de lo dibujado, o None si el lienzo está EN BLANCO.

    ⚠️ Detectar la firma por el canal ALFA no sirve: con fondo opaco, un lienzo
    vacío da alfa=255 en los 58.800 píxeles y TODO EL MUNDO constaría como firmado.
    Se compara contra el color de fondo, que es lo que de verdad distingue un trazo.
    """
    if res is None or getattr(res, "image_data", None) is None:
        return None
    try:
        import numpy as np
        from PIL import Image
        arr = res.image_data.astype("uint8")
        rgb = arr[:, :, :3]
        alfa = arr[:, :, 3]
        f = tuple(int(fondo.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        # píxel "con tinta" = visible y distinto del fondo
        tinta = ((alfa > 10) & (np.abs(rgb.astype(int) - np.array(f)).sum(axis=2) > 40)).sum()
        if tinta < 40:                      # cuatro píxeles sueltos no son una firma
            return None
        img = Image.fromarray(arr, mode="RGBA")
        base = Image.new("RGB", img.size, "white")
        base.paste(img, mask=img.split()[3])
        buf = io.BytesIO()
        base.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as e:
        logger.warning("prestart: no se pudo convertir la firma: %s", e)
        return None


def _asistentes_con_firma(yo: str) -> list:
    """Lista de asistentes, cada uno con su nombre y su firma DIBUJADA (v383).

    ⚠️ Deja de ser un `st.data_editor`: una tabla no puede llevar un lienzo dentro.
    Es una lista de filas (nombre + recuadro de firma) con un botón para añadir,
    que además se parece más al formato en papel donde cada uno firma su línea.
    """
    st.session_state.setdefault("ps_n_asist", 1)
    st_canvas = _canvas_disponible()
    if st_canvas is None:
        st.warning(":material/warning: El lienzo de firma no está disponible en este "
                   "despliegue; se registran las iniciales tecleadas.")

    out = []
    for i in range(int(st.session_state["ps_n_asist"])):
        c1, c2 = st.columns([2, 3])
        with c1:
            nom = st.text_input(f"Nombre {i + 1}", key=f"ps_att_nom_{i}",
                                value=(yo if i == 0 else ""),
                                placeholder="Nombre y apellido")
        firma = None
        with c2:
            if st_canvas is not None:
                st.caption("Firma")
                # ⚠️ `width` por defecto es 600 y el componente NO tiene
                # `use_container_width`: medido en un viewport de móvil (375 px), el
                # lienzo salía de 600 dentro de un hueco de 343 → **la mitad derecha
                # quedaba fuera de pantalla y ahí no se podía firmar**. Es el mismo
                # defecto que el `st_folium` de 500 px fijos (v307).
                # 300 px caben en el teléfono más estrecho de uso real y siguen
                # sobrando para una firma; el Pre-Start se llena EN OBRA, así que
                # manda el móvil aunque en escritorio el recuadro se vea más pequeño.
                res = st_canvas(stroke_width=2, stroke_color="#111111",
                                background_color="#ffffff", height=90, width=300,
                                drawing_mode="freedraw", key=f"ps_firma_{i}",
                                display_toolbar=True)
                firma = _firma_png(res)
                if nom.strip():
                    st.caption(":green[✓ firmado]" if firma
                               else ":orange[falta la firma]")
            else:
                ini = st.text_input(f"Iniciales {i + 1}", key=f"ps_att_ini_{i}",
                                    value=_initials(nom) if nom else "")
                out.append({"name": nom.strip(), "initial": ini.strip(), "sig": None})
                continue
        out.append({"name": nom.strip(), "initial": _initials(nom), "sig": firma})

    c1, c2 = st.columns([1, 4])
    if c1.button(":material/person_add: Añadir asistente", key="ps_add_att",
                 width="stretch"):
        st.session_state["ps_n_asist"] = int(st.session_state["ps_n_asist"]) + 1
        st.rerun()
    return [a for a in out if a["name"]]


def _projects_for(rol, usuario, grupo):
    if rol == "propietario":
        return P.list_projects()
    if rol == "administrador":
        return P.list_projects(grupo=grupo)
    return P.list_projects_for_field(usuario, grupo=grupo)


def _bloque_firmar(info: dict, grupo: str, nombre: str, usuario: str):
    """«La charla ya está hecha: firma tú» — para quien llega después (v403).

    ⚠️ NO ofrece rehacer el Pre-Start, y es a propósito: la charla del sitio es una
    por obra y día. Lo que faltaba no era otra charla, era **constar en la que hubo**.
    """
    from core import flash
    with st.container(border=True):
        st.markdown(":material/draw: **Esta obra ya tiene el Pre-Start de hoy — fírmalo**")
        st.caption(
            f"{info.get('id', '')} · lo registró **{info.get('facilitador', '') or '—'}**"
            + (f" · {info.get('location', '')}" if info.get("location") else "")
            + (" · ya firmaron: " + ", ".join(info.get("asistentes", []))
               if info.get("asistentes") else ""))
        # ⚠️ v406: si hoy hubo MÁS de una charla en esta obra, se dice. Se ofrece la
        # más reciente porque es la más probable, pero cuál le tocaba a cada uno no lo
        # sabe la app — y elegir en silencio sería peor que avisar.
        _otras = int(info.get("otras", 0) or 0)
        if _otras:
            st.warning(f":material/info: Hoy hay **{_otras + 1} charlas** registradas en "
                       f"esta obra. Se te ofrece la más reciente; si firmaste otra, "
                       f"díselo a quien la registró.")
        c1, c2 = st.columns([1, 2])
        ini = c1.text_input("Initial", value=_initials(nombre), key="ps_tarde_ini")
        firma = None
        st_canvas = _canvas_disponible()
        with c2:
            if st_canvas is not None:
                st.caption("Firma aquí")
                # ⚠️ 300 px, no los 600 por defecto del componente: en un móvil de
                # 375 el lienzo se salía de la pantalla y no se podía firmar (v393).
                res = st_canvas(stroke_width=2, stroke_color="#111111",
                                background_color="#ffffff", height=90, width=300,
                                drawing_mode="freedraw", key="ps_firma_tarde",
                                display_toolbar=True)
                firma = _firma_png(res)
            else:
                st.caption("Sin lienzo disponible: se registran las iniciales tecleadas.")
        if st.button(":material/draw: Firmar el Pre-Start", key="ps_tarde_ok",
                     type="primary"):
            if st_canvas is not None and not firma:
                st.error("Dibuja tu firma antes de enviarla.")
            elif not str(ini or "").strip():
                st.error("Pon al menos tus iniciales.")
            else:
                r = PS.firmar(info.get("id", ""), grupo, nombre, ini, firma, usuario)
                if r.get("ok"):
                    # ⚠️ por `flash`: lo que sigue es un rerun y se llevaría el mensaje (v365)
                    flash.exito(f"Firmado. Se añadió tu firma al {info.get('id', '')} "
                                "como hoja de anexo, sin tocar el documento original.")
                    st.rerun()
                else:
                    st.error(r.get("error") or "No se pudo firmar.")


def render_prestart_tab():
    st.markdown("### :material/health_and_safety: Pre-Start diario")
    st.caption("Registro de la charla de seguridad antes de empezar en obra. Genera el PDF, "
               "lo archiva en el proyecto y abre una alarma si hay near miss/hazard "
               "o si algún control queda en NO.")

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

    # ── ¿La charla ya está hecha y me falta firmar? (v403) ──
    # ⚠️ Al CAMPO se le corta aquí: lo que necesita es constar en la charla que hubo,
    # no rellenar otra. Dejarle el formulario completo debajo invitaría a emitir un
    # SEGUNDO Pre-Start del mismo día y la misma obra — dos documentos para una charla,
    # que es justo lo que hoy no impide nada. Gestión sí sigue, porque a veces hay que
    # registrar una segunda charla de verdad (otro turno, otra cuadrilla).
    try:
        _pf = PS.pendiente_de_firma(pid, pgrupo, nombre or usuario)
    except Exception as e:                                        # noqa: BLE001
        logger.warning("prestart: no se pudo mirar la firma pendiente: %s", e)
        _pf = {}
    if _pf:
        _bloque_firmar(_pf, pgrupo, nombre or usuario, usuario)
        if rol == "campo":
            return

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

    # ── 5. Attendees — cada uno FIRMA (v383) ──
    st.markdown("**5. Attendees**")
    attendees = _asistentes_con_firma(nombre or usuario)

    st.markdown("---")
    # Qué falta por responder (checks sin marcar + near miss + al menos 1 asistente)
    _pend = [PS._LABELS.get(k, k) for k, v in {**s1, **s3}.items() if v is None]
    if nm is None:
        _pend.append("Near Miss/Hazard (sección 2)")
    if not attendees:
        _pend.append("Al menos un asistente (sección 5)")
    # ⚠️ v383: quien está en la lista, FIRMA. Es el mismo criterio de v158 («no se
    # puede firmar sin leer»): si el formato admite asistentes sin firma, la firma
    # deja de significar nada. Solo se exige si el lienzo está disponible.
    _sin_firma = [a["name"] for a in attendees
                  if a.get("sig") is None and _canvas_disponible() is not None]
    if _sin_firma:
        _pend.append("Firma de: " + ", ".join(_sin_firma))
    if _pend:
        st.caption("Falta por completar: " + " · ".join(_pend))

    # ⚠️ v407 · si esta obra YA tiene charla hoy, `submit` la bloquea. Aquí se ofrece
    # la salida explícita, para que un segundo turno real se pueda registrar — pero
    # marcándolo, no por descuido. El aviso se muestra ANTES del botón: enterarse
    # después de rellenar el formulario entero sería una tomadura de pelo.
    _forzar = False
    try:
        _ya_hoy = PS.hecho_hoy(pid, pgrupo)
    except Exception:
        _ya_hoy = False
    if _ya_hoy:
        st.warning(":material/warning: **Esta obra ya tiene el Pre-Start de hoy.** "
                   "Si solo faltas tú por constar, fírmalo arriba en vez de crear otro.")
        _forzar = st.checkbox(
            "Hubo una SEGUNDA charla hoy (otro turno u otra cuadrilla): regístrala igual",
            key="ps_forzar")

    if st.button(":material/health_and_safety: Generar y archivar Pre-Start", type="primary", width="stretch",
                 key="ps_submit", disabled=bool(_pend) or (_ya_hoy and not _forzar)):
        data = {
            "grupo": pgrupo, "proyecto_id": pid, "proyecto_nombre": prj.get("Nombre", ""),
            "fecha": f_fecha, "hora": f_hora, "location": f_loc, "facilitador": f_fac,
            "activities_notes": act_notes, "s1": s1,
            "near_miss": nm, "near_miss_desc": nm_desc, "s3": s3,
            "general_notes": gen_notes, "attendees": attendees,
            "creado_por": usuario, "forzar": bool(_forzar),
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
            # ⚠️ Se usa lo que devuelve `submit`, no una segunda cuenta a partir de
            #    s1/s3: si divergieran, la pantalla diría una cosa y la alarma otra.
            _no = res.get("checks_no") or []
            if _no:
                st.error(":material/warning: Checks marcados **NO** (revisar antes de trabajar): "
                         + " · ".join(_no))
            if res["alarma"]:
                st.warning(":material/cancel: Se abrió una alarma del proyecto por el near miss/hazard reportado.")
            if res.get("alarma_checks"):
                st.warning(f":material/cancel: Se abrió una alarma del proyecto por {len(_no)} "
                           "control(es) en NO. El administrador queda avisado.")
            elif _no:
                st.caption(":orange[:material/warning:] No se pudo abrir la alarma de los "
                           "checks en NO; avisa al administrador.")
            st.download_button(":material/download: Descargar PDF", data=res["pdf"], file_name=res["filename"],
                               mime="application/pdf", width="stretch", key="ps_dl")

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
