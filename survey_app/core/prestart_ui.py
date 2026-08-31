"""
Pestaña 📋 Pre-Start diario: el equipo llena la charla de seguridad del día,
se genera el PDF (marca = grupo), se archiva en Drive del proyecto + hoja, y se
abre una alarma del proyecto si hay Near Miss/Hazard o si algún control quedó en
NO (v373).
"""
import io

from core.i18n import t
import logging

import streamlit as st

from core import prestart as PS
from core import projects as P
from core import maps
from core import clock

logger = logging.getLogger(__name__)

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— pick the project —"


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


def _cuadrilla(prj, pid, grupo) -> list:
    """Quién puede firmar esta charla: los ASIGNADOS al proyecto + los que han FICHADO
    HOY en esa obra. Devuelve `[{usuario, nombre, etiqueta, ficho}]` (v418).

    Decisión del usuario: la unión de las dos, no solo una. Los asignados son el plan y
    los fichados son la realidad — quien echa una mano sin estar asignado aparece igual,
    y quien está asignado sale aunque todavía no haya fichado cuando se hace la charla.

    ⚠️ 0 lecturas nuevas: `list_users` y los fichajes del día ya están cacheados.
    """
    from core import auth
    from core import timeclock
    asignados = [u.strip() for u in str(prj.get("CampoAsignados", "") or "").split(";")
                 if u.strip()]
    try:
        _hoy = timeclock.proyectos_por_usuario_dia(grupo, clock.today(grupo)) or {}
    except Exception as e:                                        # noqa: BLE001
        logger.warning("prestart: no se pudo mirar quién fichó hoy: %s", e)
        _hoy = {}
    ficharon = [u for u, prjs in _hoy.items()
                if any(str(p.get("pid", "")) == str(pid) for p in (prjs or []))]

    try:
        users = auth.list_users(grupo=grupo) or []
    except Exception:
        users = []
    nom_de = {str(u.get("Usuario", "")): str(u.get("Nombre", "") or u.get("Usuario", ""))
              for u in users}
    # ⚠️ La etiqueta desambigua homónimos SOLO para elegir en la lista (v413); lo que se
    # GUARDA es el nombre + el login, nunca la etiqueta. Es el fallo de v308.
    etq_de = auth.etiqueta_usuarios(users)

    out, vistos = [], set()
    for u in ficharon + asignados:                # los que ficharon, primero
        if u in vistos or u not in nom_de:
            continue
        vistos.add(u)
        out.append({"usuario": u, "nombre": nom_de[u],
                    "etiqueta": etq_de.get(u) or nom_de[u], "ficho": u in ficharon})
    return out


def _clave_firma(a) -> str:
    """Clave ESTABLE del lienzo de una persona.

    ⚠️ No se indexa por posición: al añadir o quitar a alguien, los índices se
    recolocan y la firma ya dibujada pasaría a otra persona — precisamente en el
    documento donde la firma es lo que vale.
    """
    base = str(a.get("usuario") or a.get("nombre") or "")
    return "".join(c if c.isalnum() else "_" for c in base)[:28]


def _asistentes_con_firma(yo: str, yo_usuario: str, cuadrilla: list) -> list:
    """Asistentes con su firma DIBUJADA (v383), elegidos de la CUADRILLA (v418).

    ⚠️ Antes el nombre se TECLEABA uno a uno. Con la cuadrilla del proyecto delante,
    escribirlo es trabajo manual y además abre la puerta al dedazo: un nombre mal
    escrito no casa con `pendiente_de_firma` y a esa persona se le seguiría pidiendo
    firmar una charla en la que ya consta.

    Se conserva la vía de **nombre libre** para quien no está dado de alta (un
    subcontratista, una visita): el formato en papel admite a cualquiera y en obra pasa.
    """
    st_canvas = _canvas_disponible()
    if st_canvas is None:
        st.warning(t(":material/warning: The signature canvas is not available in this deployment; the typed initials are recorded instead."))

    por_etq = {a["etiqueta"]: a for a in cuadrilla}
    # Por defecto, quien HA FICHADO hoy aquí (están, seguro) y uno mismo.
    _def = [a["etiqueta"] for a in cuadrilla
            if a["ficho"] or (yo_usuario and a["usuario"] == yo_usuario)]
    if cuadrilla:
        sel = st.multiselect(
            t("Who is attending the talk?"), list(por_etq.keys()), default=_def,
            key="ps_asist_sel",
            help=t("This lists the people assigned to the site and those who clocked in there today."))
    else:
        sel = []
        st.caption(t(":material/info: This site has nobody assigned or clocked in today; add below whoever attends."))

    st.session_state.setdefault("ps_invitados", [])
    with st.expander(t(":material/person_add: Is someone missing who is not on the list?")):
        c1, c2 = st.columns([3, 1])
        _nuevo = c1.text_input(t("First and last name"), key="ps_invit_nom",
                               placeholder=t("Subcontractor, visitor…"))
        if c2.button(t("Add"), key="ps_invit_add", width="stretch") and _nuevo.strip():
            if _nuevo.strip() not in st.session_state["ps_invitados"]:
                st.session_state["ps_invitados"].append(_nuevo.strip())
            st.rerun()
        if st.session_state["ps_invitados"]:
            st.caption(t("Added") + ": " + " · ".join(st.session_state["ps_invitados"]))
            if st.button(t("Remove the last one"), key="ps_invit_del"):
                st.session_state["ps_invitados"].pop()
                st.rerun()

    personas = [dict(por_etq[e]) for e in sel if e in por_etq]
    personas += [{"usuario": "", "nombre": n, "etiqueta": n, "ficho": False}
                 for n in st.session_state["ps_invitados"]]
    if not personas:
        st.caption(t(":orange[Pick at least one person so it can be signed.]"))

    out = []
    for a in personas:
        nom = a["nombre"]
        _k = _clave_firma(a)
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown(f"**{nom}**")
            st.caption(t("clocked in here today") if a["ficho"] else
                       (t("from the crew") if a["usuario"] else t("added by hand")))
        firma = None
        with c2:
            if st_canvas is not None:
                st.caption(t("Signature"))
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
                                drawing_mode="freedraw", key=f"ps_firma_{_k}",
                                display_toolbar=True)
                firma = _firma_png(res)
                st.caption(t(":green[✓ signed]") if firma else t(":orange[signature missing]"))
            else:
                ini = st.text_input(t("Initials"), key=f"ps_att_ini_{_k}",
                                    value=_initials(nom))
                out.append({"name": nom, "initial": ini.strip(),
                            "usuario": a["usuario"], "sig": None})
                continue
        out.append({"name": nom, "initial": _initials(nom),
                    "usuario": a["usuario"], "sig": firma})
    return [a for a in out if a["name"]]


def _projects_for(rol, usuario, grupo):
    # v422: **con las localizaciones internas**. El pre-start es la charla de seguridad
    # del SITIO, y un almacén es un sitio con sus riesgos (montacargas, estanterías,
    # manipulación) — de hecho es una de las tres cosas que se pidieron para ellas.
    if rol == "propietario":
        return P.list_projects(incluir_internos=True)
    if rol == "administrador":
        return P.list_projects(grupo=grupo, incluir_internos=True)
    return P.list_projects_for_field(usuario, grupo=grupo, incluir_internos=True)


def _bloque_firmar(info: dict, grupo: str, nombre: str, usuario: str):
    """«La charla ya está hecha: firma tú» — para quien llega después (v403).

    ⚠️ NO ofrece rehacer el Pre-Start, y es a propósito: la charla del sitio es una
    por obra y día. Lo que faltaba no era otra charla, era **constar en la que hubo**.
    """
    from core import flash
    with st.container(border=True):
        st.markdown(t(":material/draw: **This site already has today's Pre-Start — sign it**"))
        st.caption(
            f"{info.get('id', '')} · {t('recorded by')} **{info.get('facilitador', '') or '—'}**"
            + (f" · {info.get('location', '')}" if info.get("location") else "")
            + (f" · {t('already signed')}: " + ", ".join(info.get("asistentes", []))
               if info.get("asistentes") else ""))
        # ⚠️ v406: si hoy hubo MÁS de una charla en esta obra, se dice. Se ofrece la
        # más reciente porque es la más probable, pero cuál le tocaba a cada uno no lo
        # sabe la app — y elegir en silencio sería peor que avisar.
        _otras = int(info.get("otras", 0) or 0)
        if _otras:
            st.warning(f":material/info: Today there are **{_otras + 1} talks** recorded on this "
                       f"site. The most recent one is offered; if you signed a "
                       f"different one, tell whoever recorded it.")
        c1, c2 = st.columns([1, 2])
        ini = c1.text_input(t("Initial"), value=_initials(nombre), key="ps_tarde_ini")
        firma = None
        st_canvas = _canvas_disponible()
        with c2:
            if st_canvas is not None:
                st.caption(t("Sign here"))
                # ⚠️ 300 px, no los 600 por defecto del componente: en un móvil de
                # 375 el lienzo se salía de la pantalla y no se podía firmar (v393).
                res = st_canvas(stroke_width=2, stroke_color="#111111",
                                background_color="#ffffff", height=90, width=300,
                                drawing_mode="freedraw", key="ps_firma_tarde",
                                display_toolbar=True)
                firma = _firma_png(res)
            else:
                st.caption(t("No canvas available: the typed initials are recorded instead."))
        if st.button(t(":material/draw: Sign the Pre-Start"), key="ps_tarde_ok",
                     type="primary"):
            if st_canvas is not None and not firma:
                st.error(t("Draw your signature before sending it."))
            elif not str(ini or "").strip():
                st.error(t("Enter at least your initials."))
            else:
                r = PS.firmar(info.get("id", ""), grupo, nombre, ini, firma, usuario)
                if r.get("ok"):
                    # ⚠️ por `flash`: lo que sigue es un rerun y se llevaría el mensaje (v365)
                    flash.exito(f"Signed. Your signature was added to {info.get('id', '')} "
                                "as an annex sheet, without touching the original.")
                    st.rerun()
                else:
                    st.error(r.get("error") or t("Could not sign."))


def render_prestart_tab():
    st.markdown(t("### :material/health_and_safety: Daily Pre-Start"))
    st.caption(t("Record of the safety talk before starting on site. It generates the PDF, files it in the project and opens an alert if there is a near miss/hazard or any control is answered NO."))

    if not PS.is_configured():
        st.warning(t("Google Sheets must be configured (gcp_service_account + TIMECLOCK_SHEET_ID)."))
        return

    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    grupo, nombre = a.get("grupo", ""), a.get("nombre", "")

    proys = _projects_for(rol, usuario, grupo)
    if not proys:
        st.info(t("No projects available.") + " "
                + (t("The administrator must assign you to a project.") if rol == "campo"
                   else t("Create a project from the Survey.")))
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p for p in proys}
    # Campo: preselecciona el proyecto donde FICHÓ (lo primero que hace en el día),
    # como en 📋 Mis proyectos (v138). No es "el primero de la lista" que evitó v139:
    # es una señal FUERTE (donde está trabajando) que se MUESTRA y sigue siendo
    # cambiable. El pre-start se archiva y la near miss abre alarma en ese proyecto.
    # ⚠️ v418: la preselección ya NO depende del ROL, sino de tener FICHAJE ABIERTO.
    # v170 la limitó al campo dando por hecho que «admin/propietario no fichan», y es
    # falso: desde v150 el fichaje es de dos relojes para TODOS los roles y el
    # administrador ficha a diario. Resultado: quien ya estaba fichado en la obra tenía
    # que volver a buscarla en el desplegable. Ahora manda el dato (¿dónde estás
    # fichado?) y no la etiqueta del rol. Quien no tenga fichaje abierto —el
    # propietario, que no ficha— sigue eligiendo de la lista, sin cambio.
    _fich_key = None
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
    sel = st.selectbox(t("Project"), [_VACIO] + list(idmap.keys()), key="ps_proy")
    if _fich_key and sel == _fich_key:
        st.caption(t(":material/schedule: This is the project you clocked in to today. Change it if the pre-start is for another one."))
    if not sel or sel == _VACIO:
        st.info(t("Pick the project you are working on today."))
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
    # ⚠️ `_pf_ok` distingue «consultado, no le falta firmar» de «no se pudo consultar».
    # Los dos dejan `_pf` vacío, pero significan cosas distintas: el aviso de v407 de más
    # abajo afirma que YA CONSTAS, y eso no se puede decir cuando la consulta ha fallado.
    # Es el fallo de v375 (un `try` que abarcaba de más hacía decir «Falta el Pre-Start»
    # a quien solo tenía que firmar), aquí en la otra dirección.
    _pf_ok = True
    try:
        _pf = PS.pendiente_de_firma(pid, pgrupo, nombre or usuario, usuario=usuario)
    except Exception as e:                                        # noqa: BLE001
        logger.warning("prestart: no se pudo mirar la firma pendiente: %s", e)
        _pf, _pf_ok = {}, False
    if _pf:
        _bloque_firmar(_pf, pgrupo, nombre or usuario, usuario)
        if rol == "campo":
            return

    # ── Encabezado ──
    c1, c2, c3 = st.columns(3)
    f_fecha = c1.date_input(t("Date"), value=clock.today(), key="ps_fecha")
    f_hora_t = c2.time_input(t("Time"), value=clock.now().time().replace(second=0, microsecond=0),
                             key="ps_hora")
    f_hora   = f_hora_t.strftime("%H:%M") if f_hora_t else ""
    f_loc   = c3.text_input(t("Location"), value=str(prj.get("Ubicacion", "")), key="ps_loc")
    if f_loc.strip():
        c3.caption(maps.maps_link_md(f_loc, "see on Maps"))
    f_fac   = st.text_input(t("Facilitated by"), value=nombre or usuario, key="ps_fac")

    st.markdown("---")

    # ⚠️ Los checks arrancan SIN respuesta (index=None, v158): hay que responder
    # cada uno para poder generar. Antes arrancaban en YES y el pre-start se podía
    # firmar en un toque sin revisar nada — vaciaba la charla de seguridad.
    st.caption(t("Answer every item: this is a safety review, not a signature."))

    # ── 1. Planned work activities ──
    st.markdown(t("**1. Planned work activities today**"))
    s1 = {}
    for key, label in PS.CHECKS_S1:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s1[key] = cc[1].radio(label, PS.OPTS_YN, horizontal=True, index=None,
                              key=f"ps_s1_{key}", label_visibility="collapsed")
    act_notes = st.text_area(t("Activity notes / SWMS"), key="ps_act", height=70)

    # ── 2. Issues / hazard / near miss ──
    st.markdown(t("**2. Issues, hazard / near miss reports**"))
    nm = st.radio(t("Near Miss/Hazard Report submitted"), PS.OPTS_YN, horizontal=True,
                  index=None, key="ps_nm")
    # Texto libre SIEMPRE visible (antes solo aparecía al marcar YES): permite
    # describir un issue/hazard aunque no sea un near miss formal.
    nm_desc = st.text_area(t("Describe the issue / hazard / near miss (optional)"),
                           key="ps_nmdesc", height=70,
                           help=t("If you answer YES above, this description opens a project alert."))
    if nm == "YES" and not str(nm_desc).strip():
        st.caption(t(":red[:material/cancel:] You answered YES: describe the near miss/hazard (it will open a project alert)."))

    # ── 3. Shaft protection ──
    st.markdown(t("**3. Shaft Protection & other daily checks**"))
    s3 = {}
    for key, label in PS.CHECKS_S3:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{label}</div>",
                       unsafe_allow_html=True)
        s3[key] = cc[1].radio(label, PS.OPTS_YNA, horizontal=True, index=None,
                              key=f"ps_s3_{key}", label_visibility="collapsed")

    # ── 4. General notes ──
    st.markdown(t("**4. General Notes**"))
    gen_notes = st.text_area(t("General notes"), key="ps_gen", height=70,
                             label_visibility="collapsed")

    # ── 5. Attendees — cada uno FIRMA (v383) ──
    st.markdown(t("**5. Attendees**"))
    attendees = _asistentes_con_firma(nombre or usuario, usuario,
                                  _cuadrilla(prj, pid, pgrupo))

    st.markdown("---")
    # Qué falta por responder (checks sin marcar + near miss + al menos 1 asistente)
    _pend = [PS._LABELS.get(k, k) for k, v in {**s1, **s3}.items() if v is None]
    if nm is None:
        _pend.append(t("Near Miss/Hazard (section 2)"))
    if not attendees:
        _pend.append(t("At least one attendee (section 5)"))
    # ⚠️ v383: quien está en la lista, FIRMA. Es el mismo criterio de v158 («no se
    # puede firmar sin leer»): si el formato admite asistentes sin firma, la firma
    # deja de significar nada. Solo se exige si el lienzo está disponible.
    _sin_firma = [a["name"] for a in attendees
                  if a.get("sig") is None and _canvas_disponible() is not None]
    if _sin_firma:
        _pend.append(t("Signature of") + ": " + ", ".join(_sin_firma))
    if _pend:
        st.caption(t("Still to complete") + ": " + " · ".join(_pend))

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
        # ⚠️ v408 · el texto se decide por `_pf`, no por `_ya_hoy`. Antes decía siempre
        # «fírmalo ARRIBA», pero el bloque de firma solo se pinta a quien le falta
        # firmar: a quien ya constaba se le señalaba algo que no estaba en pantalla.
        # Son las dos preguntas que v403 separó a propósito —«¿hay charla?» y «¿me toca
        # firmar a mí?»— y el aviso las había vuelto a mezclar.
        if _pf:
            st.warning(t(":material/warning: **This site already has today's Pre-Start.** If you are the only one missing from it, sign it above instead of creating another."))
        elif _pf_ok:
            st.warning(t(":material/warning: **This site already has today's Pre-Start and you are already on it.** Another one is only needed if there really was a second talk."))
        else:
            st.warning(t(":material/warning: **This site already has today's Pre-Start.** Another one is only needed if there really was a second talk."))
        _forzar = st.checkbox(
            t("There was a SECOND talk today (another shift or crew): record it anyway"),
            key="ps_forzar")

    if st.button(t(":material/health_and_safety: Generate and file Pre-Start"), type="primary", width="stretch",
                 key="ps_submit", disabled=bool(_pend) or (_ya_hoy and not _forzar)):
        data = {
            "grupo": pgrupo, "proyecto_id": pid, "proyecto_nombre": prj.get("Nombre", ""),
            "fecha": f_fecha, "hora": f_hora, "location": f_loc, "facilitador": f_fac,
            "activities_notes": act_notes, "s1": s1,
            "near_miss": nm, "near_miss_desc": nm_desc, "s3": s3,
            "general_notes": gen_notes, "attendees": attendees,
            "creado_por": usuario, "forzar": bool(_forzar),
        }
        with st.spinner(t("Generating the PDF and filing it…")):
            res = PS.submit(data)
        if not res["ok"]:
            st.error(res["error"] or t("The pre-start could not be saved."))
        else:
            st.success(f":material/check_circle: Pre-Start **{res['id']}** saved as `{res['filename']}`.")
            if res["drive_id"]:
                st.caption(t(":material/attach_file: Filed in the project documents."))
            else:
                st.caption(t(":orange[:material/warning:] It was not filed to Drive (check the connection); the record was saved."))
            # ⚠️ Se usa lo que devuelve `submit`, no una segunda cuenta a partir de
            #    s1/s3: si divergieran, la pantalla diría una cosa y la alarma otra.
            _no = res.get("checks_no") or []
            if _no:
                st.error(t(":material/warning: Checks answered **NO** (review before working)") + ": "
                         + " · ".join(_no))
            if res["alarma"]:
                st.warning(t(":material/cancel: A project alert was opened for the near miss/hazard reported."))
            if res.get("alarma_checks"):
                st.warning(f":material/cancel: A project alert was opened for {len(_no)} "
                           "control(s) answered NO. The administrator has been notified.")
            elif _no:
                st.caption(t(":orange[:material/warning:] The alert for the NO checks could not be opened; tell your administrator."))
            st.download_button(t(":material/download: Download PDF"), data=res["pdf"], file_name=res["filename"],
                               mime="application/pdf", width="stretch", key="ps_dl")

    # ── Historial ──
    _historial(pid)


def _historial(pid):
    prev = [PS.leer(r) for r in PS.list_prestarts(pid)]
    st.markdown("---")
    st.markdown(t("#### :material/account_tree: Previous Pre-Starts"))
    if not prev:
        st.caption(t("No pre-starts recorded on this project yet."))
        return

    # ── KPIs de seguridad ──
    n_nm  = sum(1 for d in prev if d["near_miss"])
    n_fail = sum(1 for d in prev if d["n_no"])
    tarj = [_kpi(t("Recorded"), len(prev)),
            _kpi(t("With near miss"), n_nm, "#c0392b" if n_nm else None),
            _kpi(t("With NO checks"), n_fail, "#c0392b" if n_fail else None),
            _kpi(t("Latest"), prev[0]["fecha"] or "—")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── Ficha desplegable por pre-start ──
    for d in prev:
        _flag = (":red[:material/cancel:]" if (d["near_miss"] or d["n_no"]) else ":green[:material/check_circle:]")
        _res = []
        if d["near_miss"]:      _res.append("near miss")
        if d["n_no"]:           _res.append(f"{d['n_no']} check(s) answered NO")
        _tit = (f"{_flag}  {d['fecha']} · {d['facilitador'] or '—'}"
                + (f"  ·  :orange[:material/warning:] {', '.join(_res)}" if _res else "  ·  todo OK"))
        with st.expander(_tit):
            if d["asistentes"]:
                st.markdown(f"**:material/engineering: {t('Attendees')}:** " + " · ".join(d["asistentes"]))
            st.markdown(t("**Checks:**"))
            for c in d["checks"]:
                _e = {"YES": ":green[:material/check_circle:]", "NO": ":red[:material/cancel:]", "N/A": ":gray[:material/crop_square:]"}.get(c["estado"], ":gray[:material/help:]")
                st.markdown(f"{_e} {c['label']}  ·  _{c['estado']}_")
            if d["near_miss"]:
                st.error(":material/cancel: **Near miss / hazard:** " + (d["near_miss_desc"] or t("(no description)")))
            if str(d["act_notes"]).strip():
                st.caption(t(":material/description: Activities: ") + d["act_notes"])
            if str(d["gen_notes"]).strip():
                st.caption(t(":material/description: General notes: ") + d["gen_notes"])
            _did = str(d["drive_id"]).strip()
            if _did:
                try:
                    from core import drive_store
                    st.download_button(t(":material/download: PDF"), data=drive_store.download(_did),
                                       file_name=d["archivo"] or f"{d['id']}.pdf",
                                       key=f"ps_hdl_{d['id']}")
                except Exception:
                    st.caption(t("PDF not available"))


def _kpi(label, valor, color=None):
    col = f"color:{color};" if color else ""
    return ('<div style="background:#fff;border:1px solid #e6e9ef;border-radius:12px;'
            'padding:10px 14px;flex:1;min-width:110px;">'
            f'<div style="font-size:12px;color:#6b7280;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;{col}">{valor}</div></div>')
