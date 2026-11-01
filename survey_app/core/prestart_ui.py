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
from core import theme
from core.maps import literal_md

logger = logging.getLogger(__name__)

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— pick the project —"
_MAX_HIST = 10             # las charlas que se ven de entrada; el resto, con un botón


def _dmy(iso) -> str:
    """«2026-10-22» → «22/10/2026» (DD/MM/YYYY en toda la app, v584)."""
    s = str(iso or "")
    return f"{s[8:10]}/{s[5:7]}/{s[:4]}" if len(s) >= 10 and s[4] == "-" and s[7] == "-" else s


def _initials(nombre: str) -> str:
    parts = [w for w in str(nombre or "").split() if w]
    return "".join(w[0].upper() for w in parts[:3])


# Cómo se pinta el lienzo de firma. ⚠️ `width` 300 y no los 600 por defecto: en un móvil de
# 375 px el lienzo se salía de la pantalla y no se podía firmar (v393).
_LIENZO = dict(stroke_width=2, stroke_color="#111111", background_color="#ffffff",
               height=90, width=300, drawing_mode="freedraw", display_toolbar=True)


def _canvas_disponible():
    """El componente de dibujo, o None. Import PEREZOSO a propósito.

    ⚠️ Si el componente falta o falla, el Pre-Start NO se cae: se pide la firma
    tecleando las iniciales, como hasta v382. Una charla de seguridad no se puede
    quedar sin registrar porque una dependencia de terceros no cargue.

    ⚠️ v537 · «Falla» incluye que la versión instalada NO ACEPTE lo que le pasamos. El
    06/10/2026, al despertar la app, el Cloud instaló `streamlit-drawable-canvas` 0.13.0
    (el requirements solo decía `<1`): ya no tiene `display_toolbar` y tampoco devuelve la
    imagen salvo que se le pida. El import iba bien y la llamada reventaba con `TypeError`:
    **el Pre-Start entero caído** en producción. Ahora la versión va fijada y, además, se
    comprueba que la función acepta `_LIENZO` antes de usarla; si no, iniciales.
    """
    try:
        from streamlit_drawable_canvas import st_canvas
    except Exception as e:
        logger.warning("prestart: sin lienzo de firma (%s)", e)
        return None
    try:
        import inspect
        inspect.signature(st_canvas).bind(key="prueba", **_LIENZO)
    except TypeError as e:
        logger.warning("prestart: el lienzo instalado no acepta los parámetros (%s)", e)
        return None
    return st_canvas


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
    asignados = [u.strip() for u in str(prj.get("FieldAssigned", "") or "").split(";")
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
    nom_de = {str(u.get("User", "")): str(u.get("Name", "") or u.get("User", ""))
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


def _asistentes_con_firma(yo: str, yo_usuario: str, cuadrilla: list, kp: str) -> list:
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
            key=f"ps_asist_sel_{kp}",
            help=t("This lists the people assigned to the site and those who clocked in there today."))
    else:
        sel = []
        st.caption(t(":material/info: This site has nobody assigned or clocked in today; add below whoever attends."))

    _inv = st.session_state.setdefault(f"ps_invitados_{kp}", [])
    with st.expander(t(":material/person_add: Is someone missing who is not on the list?"),
                     key=f"exp_ps_invitado_{kp}"):
        c1, c2 = st.columns([3, 1])
        _nuevo = c1.text_input(t("First and last name"), key=f"ps_invit_nom_{kp}",
                               placeholder=t("Subcontractor, visitor…"))
        if c2.button(t("Add"), key=f"ps_invit_add_{kp}", width="stretch") and _nuevo.strip():
            if _nuevo.strip() not in _inv:
                _inv.append(_nuevo.strip())
            st.rerun()
        if _inv:
            st.caption(t("Added") + ": " + " · ".join(literal_md(n) for n in _inv))
            if st.button(t("Remove the last one"), key=f"ps_invit_del_{kp}"):
                _inv.pop()
                st.rerun()

    personas = [dict(por_etq[e]) for e in sel if e in por_etq]
    personas += [{"usuario": "", "nombre": n, "etiqueta": n, "ficho": False}
                 for n in _inv]
    if not personas:
        st.caption(t(":orange[Pick at least one person so it can be signed.]"))

    out = []
    for a in personas:
        nom = a["nombre"]
        _k = _clave_firma(a)
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown(f"**{literal_md(nom)}**")
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
                # ⚠️ v623 · La clave lleva la obra y la generación: la firma de una charla no
                # puede aparecer ya hecha en la de otra obra.
                res = st_canvas(key=f"ps_firma_{kp}_{_k}", **_LIENZO)
                firma = _firma_png(res)
                st.caption(t(":green[✓ signed]") if firma else t(":orange[signature missing]"))
            else:
                ini = st.text_input(t("Initials"), key=f"ps_att_ini_{kp}_{_k}",
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
    if rol == "owner":
        return P.list_projects(incluir_internos=True)
    if rol == "administrator":
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
            f"{info.get('id', '')} · {t('recorded by')} **{literal_md(info.get('facilitador', '') or '—')}**"
            + (f" · {literal_md(info.get('location', ''))}" if info.get("location") else "")
            + (f" · {t('already signed')}: " + ", ".join(literal_md(a) for a in info.get("asistentes", []))
               if info.get("asistentes") else ""))
        # ⚠️ v406: si hoy hubo MÁS de una charla en esta obra, se dice. Se ofrece la
        # más reciente porque es la más probable, pero cuál le tocaba a cada uno no lo
        # sabe la app — y elegir en silencio sería peor que avisar.
        _otras = int(info.get("otras", 0) or 0)
        if _otras:
            st.warning(t(":material/info: Today there are **{n} talks** recorded on this site. The "
                         "most recent one is offered; if you signed a different one, tell whoever "
                         "recorded it.", n=_otras + 1))
        c1, c2 = st.columns([1, 2])
        _pid = str(info.get("pid", ""))
        ini = c1.text_input(t("Initial"), value=_initials(nombre), key=f"ps_tarde_ini_{_pid}")
        firma = None
        st_canvas = _canvas_disponible()
        with c2:
            if st_canvas is not None:
                st.caption(t("Sign here"))
                # ⚠️ 300 px, no los 600 por defecto del componente: en un móvil de
                # 375 el lienzo se salía de la pantalla y no se podía firmar (v393).
                res = st_canvas(key=f"ps_firma_tarde_{_pid}", **_LIENZO)   # v623: la de ESTA obra
                firma = _firma_png(res)
            else:
                st.caption(t("No canvas available: the typed initials are recorded instead."))
        if st.button(t(":material/draw: Sign the Pre-Start"), key=f"ps_tarde_ok_{_pid}",
                     type="primary"):
            if st_canvas is not None and not firma:
                st.error(t("Draw your signature before sending it."))
            elif not str(ini or "").strip():
                st.error(t("Enter at least your initials."))
            else:
                r = PS.firmar(info.get("id", ""), grupo, nombre, ini, firma, usuario)
                if r.get("ok"):
                    # ⚠️ por `flash`: lo que sigue es un rerun y se llevaría el mensaje (v365)
                    # ⚠️ v623 · Decía «added as an annex» aunque el PDF no se hubiera rehecho
                    if r.get("archivado"):
                        flash.exito(t("Signed. Your signature was added to {i} as an annex sheet, "
                                      "without touching the original.", i=info.get("id", "")))
                    else:
                        flash.aviso(t("Your signature is on record for {i}, but the PDF could not be "
                                      "updated. Tell your administrator.", i=info.get("id", "")))
                    st.rerun()
                else:
                    st.error(r.get("error") or t("Could not sign."))


def _boton_pdf(d, clave, etiqueta=None):
    """El PDF de una charla. ⚠️ v623 · Con la descarga DIFERIDA (`data` es una función): con los
    bytes, cada charla del historial bajaba su PDF de Drive al pintar la pantalla, aunque estuviera
    plegada, y la pantalla se iba haciendo más lenta con cada día de obra."""
    _did = str(d.get("drive_id") or "").strip()
    if not _did:
        return
    from core import drive_store
    st.download_button(etiqueta or t(":material/download: PDF"),
                       data=lambda: drive_store.download(_did),
                       file_name=d.get("archivo") or f"{d.get('id')}.pdf", mime="application/pdf",
                       key=clave, on_click="ignore")


def _resultado(r):
    """Lo que dejó el último «Generate». v623 · Vive en la sesión: era un aviso de una pasada, y el
    primer toque —incluida la descarga— se lo llevaba."""
    st.success(t(":material/check_circle: Pre-Start **{i}** saved as `{f}`.", i=r["id"], f=r["filename"]))
    if r.get("drive_id"):
        st.caption(t(":material/attach_file: Filed in the project documents."))
    else:
        st.caption(t(":orange[:material/warning:] It was not filed to Drive (check the connection); the record was saved."))
    # ⚠️ Se usa lo que devuelve `submit`, no una segunda cuenta a partir de
    #    s1/s3: si divergieran, la pantalla diría una cosa y la alarma otra.
    _no = r.get("checks_no") or []
    if _no:
        st.error(t(":material/warning: Checks answered **NO** (review before working)") + ": "
                 + " · ".join(t(x) for x in _no))
    if r.get("alarma"):
        st.warning(t(":material/cancel: A project alert was opened for the near miss/hazard reported."))
    elif r.get("nm"):
        # ⚠️ v623 · Fallar aquí era silencioso: el aviso de «tell your administrator» solo existía
        # para los NO, y un near miss se quedaba sin alarma y sin que nadie lo supiera.
        st.error(t(":material/error: The near miss alert could NOT be opened. Tell your administrator now."))
    if r.get("alarma_checks"):
        st.warning(t(":material/cancel: A project alert was opened for {n} control(s) answered NO. "
                     "The administrator has been notified.", n=len(_no)))
    elif _no:
        st.caption(t(":orange[:material/warning:] The alert for the NO checks could not be opened; tell your administrator."))
    st.download_button(t(":material/download: Download PDF"), data=r["pdf"], file_name=r["filename"],
                       mime="application/pdf", width="stretch", key=f"ps_dl_{r['id']}", on_click="ignore")


def _tarjeta_hecho(pid, grupo, consta):
    """v623 · La charla de hoy ya está: se dice ARRIBA y con su PDF. Antes salía el formulario entero
    y el aviso 2000 px más abajo, justo encima del botón."""
    d = PS.hoy_de_obra(pid, grupo)
    with st.container(border=True):
        st.markdown(t(":material/check_circle: **This site already has today's Pre-Start and you are already on it.**")
                    if consta else t(":material/check_circle: **This site already has today's Pre-Start.**"))
        if d:
            st.caption(f"{d.get('id', '')} · {t('recorded by')} **{literal_md(d.get('facilitador') or '—')}**"
                       + (f" · {d['hora']}" if d.get("hora") else "")
                       + (f" · {t('Attendees')}: " + ", ".join(literal_md(a) for a in d.get("asistentes", []))
                          if d.get("asistentes") else ""))
            _boton_pdf(d, f"ps_hoy_pdf_{pid}", t(":material/download: Download PDF"))


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
                + (t("The administrator must assign you to a project.") if rol == "field"
                   else t("Create a project from the Survey.")))
        return

    idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in proys}
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
    # v564 · «Do today's Pre-Start here» de una localización llega con ella YA elegida
    # (antes el texto mandaba a buscarla en el desplegable). Se ASIGNA (trampa 31) y
    # gana a la preselección por fichaje: es lo que se acaba de pedir.
    _ps_pend = st.session_state.pop("_ps_proy_pending", None)
    if _ps_pend:
        _k_pend = next((k for k in idmap if k.endswith(f"({_ps_pend})")), None)
        if _k_pend:
            st.session_state["ps_proy"] = _k_pend
        else:
            # v565 · la pedida no está en la lista (archivada, o de otra cuenta): decirlo, en
            # vez de dejar «pick the project» como si no se hubiera pedido nada.
            # ⚠️ El nombre solo si es de esta empresa (cerrojo v351): el pedido nace en la
            # propia ficha, pero el aviso no debe poder enseñar el de otra.
            _pn = str(_ps_pend)
            try:
                from core import tenant
                _pp = P.get_project(_ps_pend) or {}
                if _pp and tenant.puede_ver(_pp.get("Group", "")):
                    _pn = str(_pp.get("Name") or _ps_pend)
            except Exception:
                pass
            st.info(t(":material/info: «{x}» is not available for a pre-start (it may be "
                      "archived). Pick the project below.").replace("{x}", _pn))
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
    # v480 · Sin fichaje abierto pero con UNA sola obra asignada, se abre sola: misma
    # señal fuerte de v138 (no hay nada que elegir), mostrada y cambiable.
    # ⚠️ Solo para el CAMPO: `_projects_for` le devuelve solo las suyas, mientras que a
    # admin/propietario les da las del grupo — ahi «una» significaria «la empresa tiene
    # una obra», que no es lo mismo, y seria el «primero de la lista» que evito v139.
    elif rol == "field" and len(idmap) == 1 and "ps_proy" not in st.session_state:
        st.session_state["ps_proy"] = next(iter(idmap))
    sel = st.selectbox(t("Project"), [_VACIO] + list(idmap.keys()), key="ps_proy",
                       format_func=lambda o: t(o) if o == _VACIO else o)
    if _fich_key and sel == _fich_key:
        st.caption(t(":material/schedule: This is the project you clocked in to today. Change it if the pre-start is for another one."))
    if not sel or sel == _VACIO:
        st.info(t("Pick the project you are working on today."))
        return
    prj = idmap[sel]
    pid = str(prj.get("ID", ""))
    pgrupo = str(prj.get("Group", "")) or grupo

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
        _bloque_firmar({**_pf, "pid": pid}, pgrupo, nombre or usuario, usuario)
        if rol == "field":
            return

    # ⚠️ v623 · TODO el formulario lleva en la clave la obra y una generación. Las claves eran fijas:
    # al cambiar de obra se quedaban las respuestas, las notas, la UBICACIÓN de la anterior y las
    # firmas, con el botón activo (medido: se generaba el de la B sin tocar nada), que es lo que
    # v158 quiso impedir con «no se firma sin leer». Vaciarlas no llega al navegador (trampa 31):
    # hace falta OTRA clave. La generación sube al generar: el formulario nace vacío.
    _gen = int(st.session_state.get(f"_ps_gen_{pid}", 0))
    kp = f"{pid}_{_gen}"
    hoy = clock.today(pgrupo)
    _gestor = rol != "field"

    _r = st.session_state.get(f"_ps_res_{pid}")
    if _r and _r.get("dia") != hoy.isoformat():
        _r = None
    if _r:
        _resultado(_r)

    # ⚠️ v623 · Si la charla de hoy ya está y constas (o no se pudo mirar), lo que toca es decirlo y
    # enseñar su PDF. El formulario solo aparece si hubo de verdad una segunda charla (v407).
    _forzar = False
    try:
        _ya_hoy = PS.hecho_hoy(pid, pgrupo)
    except Exception:
        _ya_hoy = False
    if _ya_hoy and not _pf:
        if not _r:
            _tarjeta_hecho(pid, pgrupo, _pf_ok)
        _forzar = st.checkbox(
            t("There was a SECOND talk today (another shift or crew): record it anyway"),
            key=f"ps_forzar_{kp}")
        if not _forzar:
            _historial(pid)
            return

    # ── Encabezado ──
    # v623 · 2 + 2 también en el móvil (`por_fila`): apilados, la primera pregunta salía a 750 px
    st.markdown(theme.por_fila("cpx_ps_cab", 2), unsafe_allow_html=True)
    with st.container(key="cpx_ps_cab"):
        c1, c2, c3, c4 = st.columns(4)
    # ⚠️ v623 · El CAMPO no elige la fecha: la charla es la de hoy (decisión del usuario), y el
    # bloqueo de duplicados solo miraba hoy. La oficina sí, hacia atrás. La clave del campo lleva
    # el día: con la pantalla abierta de un día para otro seguiría enseñando ayer.
    if _gestor:
        f_fecha = c1.date_input(t("Date"), value=hoy, max_value=hoy, key=f"ps_fecha_{kp}",
                                format="DD/MM/YYYY")
    else:
        c1.date_input(t("Date"), value=hoy, key=f"ps_fecha_{kp}_{hoy.isoformat()}", format="DD/MM/YYYY",
                      disabled=True, help=t("The Pre-Start is always recorded for today."))
        f_fecha = hoy
    f_hora_t = c2.time_input(t("Time"), value=clock.now(pgrupo).time().replace(second=0, microsecond=0),
                             key=f"ps_hora_{kp}")
    f_hora   = f_hora_t.strftime("%H:%M") if f_hora_t else ""
    f_loc   = c3.text_input(t("Location"), value=str(prj.get("Location", "")), key=f"ps_loc_{kp}")
    if f_loc.strip():
        c3.caption(":material/place: " + maps.maps_link_md(f_loc, t("see on Maps")))
    f_fac   = c4.text_input(t("Facilitated by"), value=nombre or usuario, key=f"ps_fac_{kp}")

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
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{t(label)}</div>",
                       unsafe_allow_html=True)
        s1[key] = cc[1].radio(label, PS.OPTS_YN, horizontal=True, index=None,
                              key=f"ps_s1_{kp}_{key}", label_visibility="collapsed")
    act_notes = st.text_area(t("Activity notes / SWMS"), key=f"ps_act_{kp}", height=70)

    # ── 2. Issues / hazard / near miss ──
    st.markdown(t("**2. Issues, hazard / near miss reports**"))
    nm = st.radio(t("Near Miss/Hazard Report submitted"), PS.OPTS_YN, horizontal=True,
                  index=None, key=f"ps_nm_{kp}")
    # Texto libre SIEMPRE visible (antes solo aparecía al marcar YES): permite
    # describir un issue/hazard aunque no sea un near miss formal.
    # v623 · Con YES es obligatoria: decía «optional» y dejaba abrir una alarma sin contenido
    nm_desc = st.text_area(t("Describe the issue / hazard / near miss (required if you answered YES)"),
                           key=f"ps_nmdesc_{kp}", height=70,
                           help=t("If you answer YES above, this description opens a project alert."))
    if nm == "YES" and not str(nm_desc).strip():
        st.caption(t(":red[:material/cancel:] You answered YES: describe the near miss/hazard (it will open a project alert)."))

    # ── 3. Shaft protection ──
    st.markdown(t("**3. Shaft Protection & other daily checks**"))
    s3 = {}
    for key, label in PS.CHECKS_S3:
        cc = st.columns([3, 2])
        cc[0].markdown(f"<div style='font-size:14px;padding-top:6px'>{t(label)}</div>",
                       unsafe_allow_html=True)
        s3[key] = cc[1].radio(label, PS.OPTS_YNA, horizontal=True, index=None,
                              key=f"ps_s3_{kp}_{key}", label_visibility="collapsed")

    # ── 4. General notes ──
    st.markdown(t("**4. General Notes**"))
    gen_notes = st.text_area(t("General notes"), key=f"ps_gen_{kp}", height=70,
                             label_visibility="collapsed")

    # ── 5. Attendees — cada uno FIRMA (v383) ──
    st.markdown(t("**5. Attendees**"))
    attendees = _asistentes_con_firma(nombre or usuario, usuario,
                                  _cuadrilla(prj, pid, pgrupo), kp)

    st.markdown("---")
    # Qué falta por responder. v623 · Por SECCIÓN: con las frases enteras, en el móvil eran 211 px
    # de texto gris justo encima del botón.
    _pend = []
    _n1 = sum(1 for v in s1.values() if v is None)
    if _n1:
        _pend.append(t("section 1: {n} to answer", n=_n1))
    if nm is None:
        _pend.append(t("section 2: near miss / hazard"))
    elif nm == "YES" and not str(nm_desc).strip():
        _pend.append(t("section 2: describe the near miss / hazard"))
    _n3 = sum(1 for v in s3.values() if v is None)
    if _n3:
        _pend.append(t("section 3: {n} to answer", n=_n3))
    if not attendees:
        _pend.append(t("section 5: at least one attendee"))
    # ⚠️ v383: quien está en la lista, FIRMA. Es el mismo criterio de v158 («no se
    # puede firmar sin leer»): si el formato admite asistentes sin firma, la firma
    # deja de significar nada. Solo se exige si el lienzo está disponible.
    _sin_firma = [a["name"] for a in attendees
                  if a.get("sig") is None and _canvas_disponible() is not None]
    if _sin_firma:
        _pend.append(t("section 5: signature of {p}", p=", ".join(literal_md(n) for n in _sin_firma)))
    if _pend:
        st.caption(t("Still to complete") + ": " + " · ".join(_pend))

    # ⚠️ v407 · si esta obra YA tiene charla hoy, `submit` la bloquea. Quien ya consta salió arriba
    # (v623); aquí queda la oficina a la que aún le falta firmar: el aviso va ANTES del botón.
    if _ya_hoy and _pf:
        st.warning(t(":material/warning: **This site already has today's Pre-Start.** If you are the only one missing from it, sign it above instead of creating another."))
        _forzar = st.checkbox(
            t("There was a SECOND talk today (another shift or crew): record it anyway"),
            key=f"ps_forzar_{kp}")

    if st.button(t(":material/health_and_safety: Generate and file Pre-Start"), type="primary", width="stretch",
                 key=f"ps_submit_{kp}", disabled=bool(_pend) or (_ya_hoy and not _forzar)):
        data = {
            "grupo": pgrupo, "proyecto_id": pid, "proyecto_nombre": prj.get("Name", ""),
            "fecha": f_fecha, "hora": f_hora, "location": f_loc, "facilitador": f_fac,
            "activities_notes": act_notes, "s1": s1,
            "near_miss": nm, "near_miss_desc": nm_desc, "s3": s3,
            "general_notes": gen_notes, "attendees": attendees,
            "creado_por": usuario, "forzar": bool(_forzar), "gestor": _gestor,
        }
        with st.spinner(t("Generating the PDF and filing it…")):
            res = PS.submit(data)
        if not res["ok"]:
            st.error(res["error"] or t("The pre-start could not be saved."))
        else:
            st.session_state[f"_ps_res_{pid}"] = {**res, "nm": nm == "YES", "dia": hoy.isoformat()}
            st.session_state[f"_ps_gen_{pid}"] = _gen + 1      # el formulario nace vacío
            st.rerun()

    # ── Historial ──
    _historial(pid)


def _historial(pid):
    prev = [PS.leer(r) for r in PS.list_prestarts(pid)]
    st.markdown("---")
    st.markdown(t("#### :material/account_tree: Previous Pre-Starts"))
    if not prev:
        st.caption(t("No pre-starts recorded on this project yet."))
        return

    # ── KPIs de seguridad ── v623 · ACTIVAS: cada una filtra la lista de abajo
    n_nm  = sum(1 for d in prev if d["near_miss"])
    n_fail = sum(1 for d in prev if d["n_no"])
    _K = [("todas", t("Recorded"), str(len(prev))), ("nm", t("With near miss"), str(n_nm)),
          ("no", t("With NO checks"), str(n_fail)), ("ult", t("Latest"), _dmy(prev[0]["fecha"]) or "—")]
    _fk = f"_ps_filtro_{pid}"
    _rojas = [f".st-key-cpxkpi_ps_{k} button p:nth-child(2){{color:#c0392b!important}}"
              for k, n in (("nm", n_nm), ("no", n_fail)) if n]
    if _rojas:
        st.markdown("<style>" + "".join(_rojas) + "</style>", unsafe_allow_html=True)
    st.markdown(theme.por_fila("cpx_ps_kpis", 4), unsafe_allow_html=True)
    with st.container(key="cpx_ps_kpis"):
        for _col, (_s, _l, _v) in zip(st.columns(len(_K)), _K):
            if _col.button(f"{_l}\n\n{_v}", key=f"cpxkpi_ps_{_s}", width="stretch"):
                st.session_state[_fk] = _s
    _f = st.session_state.get(_fk, "todas")
    _lista = ([d for d in prev if d["near_miss"]] if _f == "nm" else
              [d for d in prev if d["n_no"]] if _f == "no" else prev)
    if _f in ("nm", "no"):
        st.caption(t("Showing {n} of {m}. Tap «Recorded» to see them all.", n=len(_lista), m=len(prev)))

    # ── Ficha desplegable por pre-start ── v623 · las últimas; el resto, a un toque
    _tk = f"_ps_hist_todas_{pid}"
    _vis = _lista if st.session_state.get(_tk) else _lista[:_MAX_HIST]
    for d in _vis:
        _flag = (":red[:material/cancel:]" if (d["near_miss"] or d["n_no"]) else ":green[:material/check_circle:]")
        _res = []
        if d["near_miss"]:      _res.append(t("near miss"))
        if d["n_no"]:           _res.append(t("{n} check(s) answered NO")
                                            .replace("{n}", str(d["n_no"])))
        _tit = (f"{_flag}  {_dmy(d['fecha'])} · {literal_md(d['facilitador'] or '—')}"
                + (f"  ·  :orange[:material/warning:] {', '.join(_res)}" if _res else t("  ·  all OK")))
        with st.expander(_tit, key=f"exp_ps_hist_{d['id']}"):
            if d["asistentes"]:
                st.markdown(f"**:material/engineering: {t('Attendees')}:** "
                            + " · ".join(literal_md(a) for a in d["asistentes"]))
            st.markdown(t("**Checks:**"))
            for c in d["checks"]:
                _e = {"YES": ":green[:material/check_circle:]", "NO": ":red[:material/cancel:]", "N/A": ":gray[:material/crop_square:]"}.get(c["estado"], ":gray[:material/help:]")
                st.markdown(f"{_e} {t(c['label'])}  ·  _{c['estado']}_")
            # ⚠️ v623 · Lo escrito va escapado: un «*» o un «$» salía en cursiva o como fórmula
            if d["near_miss"]:
                st.error(t(":material/cancel: **Near miss / hazard:** ")
                         + (literal_md(d["near_miss_desc"]) or t("(no description)")))
            if str(d["act_notes"]).strip():
                st.caption(t(":material/description: Activities: ") + literal_md(d["act_notes"]))
            if str(d["gen_notes"]).strip():
                st.caption(t(":material/description: General notes: ") + literal_md(d["gen_notes"]))
            _boton_pdf(d, f"ps_hdl_{d['id']}")
    if len(_lista) > len(_vis):
        if st.button(t("Show the {n} older ones", n=len(_lista) - len(_vis)), key=f"ps_hist_mas_{pid}"):
            st.session_state[_tk] = True
            st.rerun()
