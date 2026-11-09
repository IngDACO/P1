"""Ausencias: autogestión del equipo y bandeja del administrador (v430).

Dos pantallas sobre el mismo motor (`core.ausencias`):
  · **Mis ausencias** (campo): saldo, solicitar y ver/cancelar lo suyo.
  · **Ausencias** (Planificación, admin): lo pendiente, con el aviso de las obras que
    quedan sin esa persona y quién podría cubrirlas.

⚠️ Aprobar ESCRIBE en el planificador. Ese es el punto de toda la funcionalidad: si
la ausencia no llega al tablero, la ruta del día y «plan vs real» siguen contando con
alguien que no está.
"""
import logging

from core.i18n import t
from datetime import timedelta

import streamlit as st

from core import ausencias as AU
from core import clock, flash
from core.maps import literal_md

logger = logging.getLogger(__name__)

_MAX_MIAS = 10             # las solicitudes que se ven de entrada; el resto, con un botón


def _kpi(label, valor, pie=None, color=None):
    from core.projects_ui import _kpi_card       # el kit de siempre (v283)
    return _kpi_card(label, valor, color, pie=pie)


def _chip_estado(e: str) -> str:
    return {AU.PENDIENTE: "🟡 " + t("pending"), AU.APROBADA: "🟢 " + t("approved"),
            AU.RECHAZADA: "🔴 " + t("rejected"), AU.CANCELADA: "⚪ " + t("cancelled")}.get(e, e)


def _fdma(x) -> str:
    """dd/mm/aaaa (v555): la app enseña las fechas así (v544) con UN helper,
    `projects_ui._fmt_fecha`; el ISO es solo de la hoja."""
    from core.projects_ui import _fmt_fecha
    return _fmt_fecha(x.isoformat() if hasattr(x, "isoformat") else x)


def _rango(desde, hasta) -> str:
    """«13/10/2026 → 14/10/2026», o UN día si empieza y acaba el mismo (salía «22 → 22»)."""
    a, b = _fdma(desde), _fdma(hasta)
    return a if a == b else f"{a} → {b}"


def _dias(n) -> str:
    """«1 day» · «3 days» (v627: decía «1 day(s)»)."""
    n = int(float(n or 0))
    return t("1 day") if n == 1 else t("{n} days", n=n)


def _linea(r) -> str:
    return (f"**{AU.nombre_tipo(r.get('Type'))}** · {_rango(r.get('From'), r.get('To'))} · "
            f"{_dias(r.get('Days'))} · {_chip_estado(str(r.get('Status')))}")


# ═══════════════════════════════════════════════════════════════════
# CAMPO — Mis ausencias
# ═══════════════════════════════════════════════════════════════════
def render_mis_ausencias():
    """⚠️ SIN título propio: desde v478 cuelga de Self-service y `_sub_header` ya pinta «Self-service
    · My absences» (v627: salía dos veces, con la raya en medio)."""
    a = st.session_state.get("auth", {}) or {}
    usuario = str(a.get("usuario", ""))
    nombre = str(a.get("nombre") or usuario)
    grupo = str(a.get("grupo", ""))
    if not AU.is_configured():
        st.warning(t(":material/warning: Absences need Google Sheets configured."))
        return
    _accion_mia(grupo, usuario, nombre)      # v627 · ACCIÓN DIFERIDA (v555)
    _saldos(grupo, usuario)
    _pedir(grupo, usuario, nombre)
    _mis_solicitudes(grupo, usuario)


def _saldos(grupo, usuario):
    """El saldo. v627 · ACTIVO (era HTML): cada cifra filtra «My requests» por su tipo y baja
    hasta allí. La cifra es lo que aún se puede pedir: lo que espera decisión ya está contado."""
    from core import theme as T
    _per, _rojo, _items = None, "", []
    # ⚠️ `_tp`, no `t`: la variable del bucle taparía la función de idioma en el
    # ámbito ENTERO de la función (el fallo del glosario de v437).
    for _tp in AU.TIPOS:
        s = AU.saldo(grupo, usuario, _tp)
        _per = _per or s.get("periodo")
        if s["ilimitado"]:
            _v, _pie = f"{s['usados']:.0f}", t("days used in the period")
        else:
            # v634 · Con el exceso pagado saldría «-25» (10 de saldo, 35 días): no le queda nada.
            _v = f"{max(s['disponibles'], 0):.0f}"
            _pie = t("of {a} · used {b}", a=f"{s['asignados']:.0f}", b=f"{s['usados']:.0f}")
            if s["pendientes"]:
                _pie += " · " + t("{n} pending", n=f"{s['pendientes']:.0f}")
            if s["disponibles"] <= 0:
                _rojo += f".st-key-cpxkpi_mia_{_tp} button{{border-left-color:#c0392b!important}}"
        _items.append((_tp, AU.nombre_tipo(_tp), _v, _pie))
    st.markdown(T.por_fila("cpx_mia_kpis", 3)
                + (f"<style>{_rojo}</style>" if _rojo else ""), unsafe_allow_html=True)
    _f = st.session_state.get("_aus_mia_filtro", "")
    with st.container(key="cpx_mia_kpis"):
        for _col, (_tp, _l, _v, _pie) in zip(st.columns(len(_items)), _items):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_mia_{_tp}", width="stretch",
                           help=t("See my requests of this type")):
                st.session_state["_aus_mia_filtro"] = "" if _f == _tp else _tp
                st.session_state["_bajar_cpx_aus_lista"] = True
                st.rerun()
    # ⚠️ v433: DE QUÉ periodo habla el saldo. Sin esto, «te quedan 14» no dice hasta
    # cuándo, y con el año por aniversario cada persona tiene el suyo. Y si falta la
    # fecha de alta, se avisa de que es una estimación en vez de dar un número que
    # parece exacto.
    if _per and _per["origen"] == "aniversario":
        st.caption(t(":material/event_available: Your leave year runs from **{a}** to **{b}** "
                     "(since you started, on {c}).", a=_fdma(_per["desde"]), b=_fdma(_per["hasta"]),
                     c=_fdma(_per["ingreso"])))
    elif _per:
        st.caption(t(":material/help: We are counting by calendar year (**{a}** → **{b}**) because "
                     "your start date is not on record. Ask your manager to enter it and the "
                     "balance will count from your anniversary.", a=_fdma(_per["desde"]),
                     b=_fdma(_per["hasta"])))


def registrar(grupo, usuario, nombre, tipo, desde, hasta, motivo="", incluir_findes=False) -> tuple:
    """Guarda la ausencia y hace lo que va detrás: `(ok, id_o_error, aviso)`. v640 · Una sola
    definición: la usan esta pantalla y el asistente, y cada paso que faltara en uno sería un fallo
    (una baja que no sale en el tablero, o una oficina que no se entera)."""
    cfg = AU.TIPOS.get(tipo, {})
    _ex = AU.exceso(grupo, usuario, tipo, len(AU.dias_del_rango(desde, hasta, incluir_findes)))
    ok, res = AU.solicitar(grupo, usuario, nombre, tipo, desde, hasta, motivo, incluir_findes=incluir_findes)
    if not ok:
        return False, res, ""
    _aviso = ""
    # La enfermedad nace aprobada → al tablero YA. Las demás, al aprobar.
    if not cfg["aprobacion"]:
        _ok2, _nd = AU.aplicar_al_roster(AU.get(res) or {})
        if not _ok2:
            logger.warning("ausencias_ui: roster: %s", _nd)
            _aviso = t("It is recorded, but the planner could not be updated: tell the office.")
    _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg, _ex)
    return True, res, _aviso


def _pedir(grupo, usuario, nombre):
    """Pedir o avisar. ⚠️ v627 · Sin `st.form`: dentro de un formulario nada reacciona hasta
    enviar, y lo primero que hace falta saber —cuántos días gasta esto— no se veía. Y los campos
    llevan generación: `pop` de una clave no le llega al navegador (trampa 31), así que el motivo
    y las fechas se quedaban y se colaban en la solicitud siguiente."""
    from core import theme as T
    with st.expander(t("Request a day off or annual leave, or report sick leave"),
                     icon=":material/add_circle:", expanded=True, key="exp_aus_pedir"):
        _tipos = list(AU.TIPOS)
        tipo = st.selectbox(
            t("What do you need?"), _tipos, key="aus_tipo",
            # ⚠️ EMOJI, no `:material/…:`: en las opciones de un selectbox el material
            # sale como texto literal (medido en el Cloud). En `st.radio` sí funciona.
            format_func=lambda _k: f"{AU.TIPOS[_k]['emoji']} {AU.nombre_tipo(_k)}")
        cfg = AU.TIPOS[tipo]
        _nom = AU.nombre_tipo(tipo).lower()
        _s = AU.saldo(grupo, usuario, tipo)
        if not cfg["aprobacion"]:
            st.info(t(":material/info: Sick leave **is recorded straight away**: you do not have to wait for anyone to approve it. If you can, send the medical certificate to your manager."))
        elif not _s["ilimitado"] and _s["disponibles"] <= 0:
            st.error(t(":material/block: You have no days left of {x} this year (used {a} of {b}). "
                       "Talk to your manager.", x=_nom, a=f"{_s['usados']:.0f}",
                       b=f"{_s['asignados']:.0f}"))
        elif not _s["ilimitado"] and _s["disponibles"] <= 3:
            st.warning(t(":material/warning: You have only **{n}** left of {x} this year.",
                         n=_dias(_s["disponibles"]), x=_nom))

        _g = st.session_state.get("_aus_gen", 0)
        hoy = clock.today(grupo)
        st.markdown(T.por_fila("cpx_aus_fechas", 2), unsafe_allow_html=True)
        with st.container(key="cpx_aus_fechas"):
            c1, c2 = st.columns(2)
            desde = c1.date_input(t("From"), value=hoy, key=f"aus_desde_{_g}", format="DD/MM/YYYY")
            hasta = c2.date_input(t("To"), value=hoy, key=f"aus_hasta_{_g}", format="DD/MM/YYYY")
        findes = st.checkbox(t("Include weekends"), key=f"aus_findes_{_g}",
                             help=t("Tick this only if those days are worked. Otherwise they are not taken off your balance."))
        motivo = st.text_input(t("Reason (optional)"), key=f"aus_motivo_{_g}",
                               placeholder=t("Family trip, medical appointment…"))

        _n = len(AU.dias_del_rango(desde, hasta, findes))
        _ex = AU.exceso(grupo, usuario, tipo, _n)
        _no = ""
        if hasta < desde:
            _no = t("The end date cannot be earlier than the start date.")
        elif not _n:
            _no = t("That range only covers the weekend. If those days are worked, tick "
                    "«include weekends».")
        elif _ex and cfg["aprobacion"]:
            _no = t(":material/block: You are asking for **{a}** and you have **{b}** available.",
                    a=_dias(_n), b=f"{max(_s['disponibles'], 0):.0f}")
        if _no:
            st.warning(_no)
        elif _ex:
            st.warning(t(":material/warning: This goes **{n}** over your sick leave balance. It is "
                         "recorded anyway: the office decides how those days are paid.", n=_dias(_ex)))
        else:
            _txt = t(":material/event: This takes **{n}**", n=_dias(_n))
            if not _s["ilimitado"]:
                _txt += " · " + t("{n} left after this", n=f"{_s['disponibles'] - _n:.0f}")
            st.caption(_txt)

        if st.button(t(":material/send: Send request") if cfg["aprobacion"]
                     else t(":material/send: Record the sick leave"),
                     type="primary", width="stretch", key="aus_enviar", disabled=bool(_no)):
            ok, res, _aviso = registrar(grupo, usuario, nombre, tipo, desde, hasta, motivo, findes)
            if not ok:
                st.error(res)
            else:
                if _aviso:
                    flash.aviso(_aviso)
                st.session_state["_aus_gen"] = _g + 1
                flash.exito(t("{x} recorded ({i}).", x=AU.nombre_tipo(tipo), i=res)
                            if not cfg["aprobacion"] else
                            t("Request sent ({i}). We will let you know when it is resolved.", i=res))
                st.rerun()


def _accion_mia(grupo, usuario, nombre):
    """⚠️ v627 · ACCIÓN DIFERIDA, la de la bandeja (v555): el botón solo apunta y relanza, y aquí
    se ejecuta antes de pintar la lista. Solo lo suyo: una acción apuntada en la sesión no toca la
    ausencia de otra persona."""
    aid = st.session_state.pop("_aus_mia_accion", None)
    if not aid:
        return
    r = _de_grupo(grupo, aid)
    if str(r.get("User", "")) != str(usuario):
        flash.error(t("Request not found."))
        st.rerun()
    _estaba = str(r.get("Status")) == AU.APROBADA
    ok, msg = AU.cancelar(aid, usuario)
    if ok:
        flash.exito(msg)
        if _estaba:
            # si ya estaba en el tablero, hay que quitarla de ahí
            AU.aplicar_al_roster(r, quitar=True)
            # ⚠️ v432: cancelar una APROBADA devuelve esos días al tablero, y quien la aprobó pudo
            # haber reorganizado la cuadrilla contando con la ausencia. Solo para las aprobadas:
            # retirar una pendiente no cambia nada que nadie hubiera planificado.
            _avisar_cancelacion(grupo, nombre, r)
    else:
        flash.error(msg)
    st.rerun()


def _tarjeta_mia(r, usuario):
    aid = str(r.get("ID"))
    with st.container(border=True):
        st.markdown(_linea(r))
        _pie = []
        if str(r.get("Reason", "")).strip():
            _pie.append(literal_md(r.get("Reason")))
        if str(r.get("AdminNote", "")).strip():
            _pie.append(t("Note: {x}", x=literal_md(r.get("AdminNote"))))
        _ex = AU.exceso_de(r)                     # v633
        if _ex["dias"]:
            _n = _dias(len(_ex["dias"]))
            _pie.append({AU.EXCESO_PAGA: t("{n} over your balance: paid", n=_n),
                         AU.EXCESO_NO: t("{n} over your balance: unpaid", n=_n)}.get(
                _ex["decision"], t("{n} over your balance: the office decides how they are paid", n=_n)))
        # v627 · Su nombre, no su login. Lo automático y lo que cancela uno mismo no tienen «quién».
        _por = str(r.get("ResolvedBy", "")).strip()
        if _por and _por != str(usuario) and not _por.startswith("("):
            from core.projects_ui import _etq_us
            _pie.append(t("resolved by {x}", x=literal_md(_etq_us([_por]).get(_por, _por))))
        if _pie:
            st.caption(" · ".join(_pie))
        if str(r.get("Status")) not in AU.VIGENTES:
            return
        if not AU.cancelable_por_el_campo(r):
            st.caption(t(":material/lock: It has already started: ask the office if it needs "
                         "changing."))
            return
        # ⚠️ v627 · Con confirmación, como la oficina (v555): unas vacaciones aprobadas se iban de
        # un toque, con correo a todos los administradores.
        if st.session_state.get("_aus_mia_cancelar") != aid:
            if st.button(t(":material/undo: Cancel"), key=f"auscan_{aid}"):
                st.session_state["_aus_mia_cancelar"] = aid
                st.rerun()
            return
        st.warning(t("Cancel this absence? Its days go back to your balance and the office is "
                     "told.") if str(r.get("Status")) == AU.APROBADA else
                   t("Withdraw this request?"))
        b1, b2 = st.columns(2)
        if b1.button(t(":material/undo: Yes, cancel it"), key=f"auscanok_{aid}", type="primary",
                     width="stretch"):
            st.session_state.pop("_aus_mia_cancelar", None)
            st.session_state["_aus_mia_accion"] = aid
            st.rerun()
        if b2.button(t("Keep it"), key=f"auscanno_{aid}", width="stretch"):
            st.session_state.pop("_aus_mia_cancelar", None)
            st.rerun()


def _mis_solicitudes(grupo, usuario):
    from core import projects_ui as _PU
    with st.container(key="cpx_aus_lista"):      # v627 · destino de las cifras
        _PU._bajar_a("cpx_aus_lista", "_bajar_cpx_aus_lista", bloque="start")
        st.markdown(t("#### :material/history: My requests"))
    mias = AU.list_group(grupo, usuario=usuario)
    if not mias:
        st.caption(t("You have not requested any absence yet."))
        return
    _f = st.session_state.get("_aus_mia_filtro", "")
    _lista = [r for r in mias if not _f or str(r.get("Type")) == _f]
    if _f:
        st.caption(t("Showing only: {x}", x=AU.nombre_tipo(_f)))
        if st.button(t("Show all types"), key="aus_filtro_fuera", type="tertiary"):
            st.session_state.pop("_aus_mia_filtro", None)
            st.rerun()
        if not _lista:
            st.caption(t("None of this type."))
    # v627 · Se cortaba en 15 sin decirlo.
    _vis = _lista if st.session_state.get("_aus_mia_todas") else _lista[:_MAX_MIAS]
    for r in _vis:
        _tarjeta_mia(r, usuario)
    if len(_vis) < len(_lista) and st.button(t("Show all ({n})", n=len(_lista)), key="aus_ver_todas"):
        st.session_state["_aus_mia_todas"] = True
        st.rerun()


def _avisar_cancelacion(grupo, nombre, r):
    """Avisa de que una ausencia YA APROBADA se ha cancelado (v432).

    ⚠️ Best-effort, como los demás avisos: la cancelación ya está guardada y el
    tablero ya está limpio cuando se llega aquí.
    """
    try:
        from core import notify
        from core.alerts import _admins_and_owners
        cfg = AU.TIPOS.get(str(r.get("Type", "")), {})
        _subj = (f"CANCELLED — {cfg.get('nombre', r.get('Type'))}: {nombre} "
                 f"({_rango(r.get('From'), r.get('To'))})")
        _lines = [f"<b>{nombre}</b> has CANCELLED their "
                  f"<b>{cfg.get('nombre', r.get('Type'))}</b> "
                  f"from {_fdma(r.get('From'))} to {_fdma(r.get('To'))}.",
                  "Those days are free again in the planner: if you had reorganised "
                  "the crew, review it."]
        for d in _admins_and_owners(grupo):
            try:
                notify.notify_user(d, _subj, _lines)
            except Exception:
                pass
    except Exception as e:
        logger.warning("ausencias_ui._avisar_cancelacion: %s", e)


def _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg, exceso=0):
    """Avisa a quien decide. ⚠️ Best-effort: que falle un correo no puede impedir
    registrar la ausencia — la solicitud ya está guardada cuando se llega aquí.

    v627 · `exceso` = días de baja que pasan del saldo: se registran igual y decide la oficina."""
    try:
        from core import notify
        from core.alerts import _admins_and_owners
        _subj = (f"{cfg['nombre']}: {nombre} ({_rango(desde, hasta)})")
        _lines = [f"<b>{nombre}</b> has recorded: <b>{cfg['nombre']}</b>",
                  f"From {_fdma(desde)} to {_fdma(hasta)}.",
                  ("It was recorded automatically (no approval needed)."
                   if not cfg["aprobacion"] else
                   "It is PENDING your approval → Planning · Absences.")]
        if exceso:
            _lines.append(f"<b>It goes {exceso} day(s) over the balance</b>: decide how those "
                          "days are paid → Planning · Absences.")
        for d in _admins_and_owners(grupo):
            try:
                notify.notify_user(d, _subj, _lines)
            except Exception:
                pass
    except Exception as e:
        logger.warning("ausencias_ui._avisar_admins: %s", e)


# ═══════════════════════════════════════════════════════════════════
# ADMIN — bandeja
# ═══════════════════════════════════════════════════════════════════
def render_bandeja(grupo: str):
    """⚠️ SIN título propio: `_sub_header` ya pinta «Planificación · Ausencias»."""
    if not AU.is_configured():
        st.warning(t(":material/warning: Absences need Google Sheets configured."))
        return
    quien = str((st.session_state.get("auth", {}) or {}).get("usuario", ""))

    _accion_pendiente(grupo, quien)          # v555 · ACCIÓN DIFERIDA (ver su docstring)

    todas = AU.list_group(grupo)
    # v555 · lo más PRÓXIMO primero: `list_group` ordena de la más lejana a la más
    # cercana, y la del 13/10 quedaba debajo de las del 19 y el 22.
    pend = sorted([r for r in todas if str(r.get("Status")) == AU.PENDIENTE],
                  key=lambda r: str(r.get("From", "")))
    hoy = clock.today(grupo)
    fuera_hoy = AU.ausentes_en(grupo, hoy)
    _sem = sorted([r for r in todas if str(r.get("Status")) == AU.APROBADA
                   and any(hoy <= d <= hoy + timedelta(days=7)
                           for d in AU.dias_del_rango(r.get("From"), r.get("To"), True))],
                  key=lambda r: str(r.get("From", "")))
    _kpis_bandeja(pend, fuera_hoy, _sem)

    # ── Pendientes ─────────────────────────────────────────────────
    st.markdown(t("#### :material/inbox: Waiting for approval"))
    if not pend:
        st.success(t(":material/check_circle: No pending requests."))
    for r in pend:
        _tarjeta_pendiente(grupo, r, quien)

    # ── Bajas por enfermedad (v555) ────────────────────────────────
    # ⚠️ Nacen APROBADAS (nadie pide permiso para estar enfermo) y el docstring de
    # `ausencias` dice que el admin «la ve y la confirma después»… pero esta bandeja
    # solo enseñaba lo pendiente: una baja no le llegaba nunca. Aquí las de los últimos
    # 14 días y las próximas, con «Cancel» si no procede.
    # ⚠️ v633 · Y las que tienen días sobre el saldo sin decidir, por viejas que sean: esos días no
    # se pagan hasta que se decida, y se saldrían de la lista sin que nadie lo hubiera hecho.
    from core.num import parse_date as _pd
    _sin_decidir = {x["id"] for x in AU.excesos_por_decidir(grupo)}
    _bajas = [r for r in todas if str(r.get("Type")) == AU.ENFERMEDAD
              and str(r.get("Status")) == AU.APROBADA
              and ((_pd(r.get("To")) or hoy) >= hoy - timedelta(days=14)
                   or str(r.get("ID")) in _sin_decidir)]
    if _bajas:
        st.markdown(t("#### :material/sick: Sick leave recorded"))
        st.caption(t("Recorded straight away, without approval. Review it: if it is not "
                     "right, cancel it (the days are freed on the board and the person is "
                     "told)."))
        for r in _bajas:
            _fila_con_cancelar(r, "baja")

    # ── Histórico ──────────────────────────────────────────────────
    # ⚠️ v555 · con clave: ya lleva controles dentro (trampa 35)
    with st.expander(t("History ({n})").replace("{n}", str(len(todas))),
                     icon=":material/history:", key="exp_aus_hist"):
        if not todas:
            st.caption(t("No absences recorded."))
        if len(todas) > 40:
            st.caption(t("The latest 40 of {n}.").replace("{n}", str(len(todas))))
        for r in todas[:40]:
            _fila_con_cancelar(r, "hist")


def _accion_pendiente(grupo, quien):
    """⚠️ v555 · ACCIÓN DIFERIDA. Aprobar, rechazar y cancelar escriben en la hoja y
    avisan a la persona: 3-5 s. Hechos DENTRO de la tarjeta, con un `st.rerun()` al
    final, Streamlit 1.64 dejaba la tarjeta resuelta en pantalla —atenuada, con sus
    botones— aunque ya no se pintara (visto en producción al rechazar AUS-0002, y
    reproducido en una mini-app: el servidor tenía solo C y había cuatro «A»). Pasa con
    tarjetas y desplegables CON clave cuando la que ocupa su sitio tiene otra forma.
    Los botones solo APUNTAN la acción y relanzan al instante; aquí se ejecuta, ANTES de
    pintar la lista, y se relanza otra vez para que el aviso salga arriba."""
    _acc = st.session_state.pop("_aus_accion", None)
    if _acc:
        _ejecutar(_acc, quien, grupo)
        st.rerun()


def _kpis_bandeja(pend, fuera_hoy, sem):
    """Tarjetas ACTIVAS (v555; eran HTML que no se podía tocar): cada una abre su lista
    debajo — lo pendiente por fecha, quién está fuera hoy y lo de los próximos 7 días."""
    from core import theme
    _ver = st.session_state.get("_aus_kpi", "")
    _kp = [("pend", ":material/inbox:", t("Pending"), pend, t("waiting for your decision"),
            theme.AMBAR if pend else theme.GRIS_TXT),
           ("today", ":material/event_busy:", t("Away today"), fuera_hoy,
            ", ".join(str(x.get("Name")) for x in fuera_hoy) or t("nobody"),
            theme.AZUL if fuera_hoy else theme.GRIS_TXT),
           ("week", ":material/date_range:", t("Next 7 days"), sem, t("approved absences"),
            theme.AZUL if sem else theme.GRIS_TXT)]
    # El borde, en el color vivo; la CIFRA es texto: `AMBAR` sobre blanco se lee a 2,85:1
    # (v328) → `AMBAR_TXT`.
    _txt = {theme.AMBAR: theme.AMBAR_TXT}
    st.markdown("<style>" + "".join(
        f".st-key-cpxkpi_aus_{k} button{{border-left-color:{c}!important;}}"
        f".st-key-cpxkpi_aus_{k} button p:nth-child(2){{color:{_txt.get(c, c)}!important;}}"
        for k, _i, _l, _r, _p, c in _kp) + "</style>", unsafe_allow_html=True)
    for _col, (k, ico, lbl, filas, pie, _c) in zip(st.columns(len(_kp)), _kp):
        if _col.button(f"{ico} {lbl}\n\n{len(filas)}\n\n{pie}", key=f"cpxkpi_aus_{k}",
                       width="stretch"):
            st.session_state["_aus_kpi"] = "" if _ver == k else k
            st.rerun()
    if _ver:
        _filas = {k: f for k, _i, _l, f, _p, _c in _kp}.get(_ver, [])
        with st.container(border=True):
            if not _filas:
                st.caption(t("Nobody."))
            for r in _filas:
                st.markdown(f"**{r.get('Name')}** — " + _linea(r))


def _de_grupo(grupo, aid) -> dict:
    """La ausencia `aid` SOLO si es de este grupo (v555). ⚠️ `AU.get` busca por ID en
    todas: una acción apuntada en la sesión no puede tocar la de otra empresa (v351)."""
    return next((r for r in AU.list_group(grupo) if str(r.get("ID")) == str(aid)), {})


def _decidir_exceso(r, donde):
    """v633 · Los días de baja que pasan del saldo: aquí decide la oficina. Los botones van en la
    sección de bajas (ACCIÓN DIFERIDA, v555); en el histórico, solo se dice cómo quedó."""
    ex = AU.exceso_de(r)
    if not ex["dias"]:
        return
    aid = str(r.get("ID"))
    _n, _rg = _dias(len(ex["dias"])), _rango(ex["dias"][0], ex["dias"][-1])
    if ex["decision"]:
        c1, c2 = st.columns([5, 1])
        c1.caption(t(":material/payments: {n} over the balance ({r}): paid", n=_n, r=_rg)
                   if ex["decision"] == AU.EXCESO_PAGA else
                   t(":material/money_off: {n} over the balance ({r}): unpaid", n=_n, r=_rg))
        if donde != "hist" and c2.button(t(":material/undo: Change"), key=f"ausexc_{donde}_{aid}",
                                         width="stretch"):
            st.session_state["_aus_accion"] = {"aid": aid, "exceso": ""}
            st.rerun()
        return
    st.warning(t(":material/rule: **{n} over the balance** ({r}): not paid until you decide.",
                 n=_n, r=_rg))
    if donde == "hist":
        return
    b1, b2 = st.columns(2)
    if b1.button(t(":material/payments: Pay them"), key=f"ausexp_{donde}_{aid}", width="stretch"):
        st.session_state["_aus_accion"] = {"aid": aid, "exceso": AU.EXCESO_PAGA}
        st.rerun()
    if b2.button(t(":material/money_off: Leave them unpaid"), key=f"ausexn_{donde}_{aid}",
                 width="stretch"):
        st.session_state["_aus_accion"] = {"aid": aid, "exceso": AU.EXCESO_NO}
        st.rerun()


def _fila_con_cancelar(r, donde):
    """Una ausencia en una línea y, si está APROBADA, «Cancel» con confirmación (v555).

    ⚠️ Antes el admin no podía deshacer nada aprobado: `resolver` dice «para deshacer
    una aprobada, cancélala», pero el botón solo existía en la pantalla del campo. Las
    pendientes no lo llevan: para ellas están «Approve» y «Reject».
    `donde` va en la clave: una baja reciente sale en su sección Y en el histórico.
    """
    aid = str(r.get("ID"))
    c1, c2 = st.columns([5, 1])
    c1.markdown(f"`{aid}` · **{r.get('Name')}** — " + _linea(r))
    if str(r.get("AdminNote", "")).strip():
        c1.caption(literal_md(r.get("AdminNote")))
    _decidir_exceso(r, donde)
    if str(r.get("Status")) != AU.APROBADA:
        return
    _conf = st.session_state.get("_aus_cancelar") == (donde, aid)
    if not _conf and c2.button(t(":material/undo: Cancel"), key=f"auscx_{donde}_{aid}",
                               width="stretch"):
        st.session_state["_aus_cancelar"] = (donde, aid)
        st.rerun()
    if _conf:
        st.warning(t("Cancel this absence? Its days are freed on the board and {who} is "
                     "told.").replace("{who}", str(r.get("Name"))))
        b1, b2 = st.columns(2)
        if b1.button(t(":material/undo: Yes, cancel it"), key=f"auscxok_{donde}_{aid}",
                     type="primary", width="stretch"):
            st.session_state.pop("_aus_cancelar", None)
            st.session_state["_aus_accion"] = {"aid": aid, "cancelar": True}
            st.rerun()
        if b2.button(t("Keep it"), key=f"auscxno_{donde}_{aid}", width="stretch"):
            st.session_state.pop("_aus_cancelar", None)
            st.rerun()


def _ejecutar(acc, quien, grupo):
    """La acción apuntada por un botón (v555): ver la ACCIÓN DIFERIDA en `render_bandeja`.
    Deja el resultado en `flash`, que se pinta arriba en la pasada siguiente."""
    aid = str(acc.get("aid", ""))
    r = _de_grupo(grupo, aid)
    if not r:
        flash.error(t("Request not found."))
        return
    usuario = str(r.get("User", ""))
    if "exceso" in acc:
        _como = str(acc.get("exceso") or "")
        ok, msg = AU.decidir_exceso(aid, _como, quien)
        if not ok:
            flash.error(msg)
            return
        if _como:
            _avisar_exceso(usuario, r, _como)
        flash.exito(msg)
        if _como == AU.EXCESO_PAGA:
            flash.info(t("If a payslip for those dates is already issued, void it and generate it "
                         "again so they are included."))
        return
    if acc.get("cancelar"):
        _estaba = str(r.get("Status")) == AU.APROBADA
        ok, msg = AU.cancelar(aid, quien, gestor=True)
        if not ok:
            flash.error(msg)
            return
        _extra = ""
        if _estaba:
            _ok2, _n = AU.aplicar_al_roster(r, quitar=True)
            _extra = (f" {_n} {t('day(s) freed in the planner.')}" if _ok2 else
                      f" ⚠️ {t('Could not write to the planner')}: {_n}")
        _avisar_persona_cancelada(usuario, r)
        flash.exito(msg + _extra)
        return
    aprobar = bool(acc.get("aprobar"))
    ok, msg = decidir(grupo, aid, aprobar, quien, str(acc.get("nota") or ""))
    (flash.error if not ok else flash.exito if aprobar else flash.aviso)(msg)


def decidir(grupo, aid, aprobar, quien, nota="") -> tuple:
    """Aprobar o rechazar una solicitud con todo lo que implica: el tablero y el aviso a la persona.
    `(ok, mensaje)`. v644 · Aparte de `_ejecutar` para que el Management assistant haga exactamente
    lo mismo que esta bandeja. ⚠️ Solo una de ESTE grupo (`_de_grupo`)."""
    r = _de_grupo(grupo, aid)
    if not r:
        return False, t("Request not found.")
    usuario = str(r.get("User", ""))
    ok, msg = AU.resolver(aid, aprobar, quien, nota)
    if not ok:
        return False, msg
    if aprobar:
        # ⚠️ El orden importa: primero la decisión, luego el tablero. Si el roster
        # fallara, la ausencia queda aprobada y el tablero se puede reintentar; al
        # revés, el tablero diría que está fuera sin que nadie lo haya aprobado.
        _ok2, _n = AU.aplicar_al_roster(_de_grupo(grupo, aid) or r)
        _avisar_persona(usuario, r, True, nota)
        return True, msg + (f" {_n} {t('day(s) marked in the planner.')}" if _ok2 else
                            f" ⚠️ {t('Could not write to the planner')}: {_n}")
    _avisar_persona(usuario, r, False, nota)
    return True, msg


def _tarjeta_pendiente(grupo, r, quien):
    aid = str(r.get("ID"))
    usuario = str(r.get("User"))
    cfg = AU.TIPOS.get(str(r.get("Type", "")), {})
    with st.container(border=True, key=f"auspend_{aid}"):
        st.markdown(f"**{r.get('Name')}** — " + _linea(r))
        if str(r.get("Reason", "")).strip():
            st.caption(f":material/notes: {r.get('Reason')}")

        # Saldo de esa persona: aprobar a ciegas es lo que esto viene a evitar.
        # ⚠️ v555 · con lo que QUEDA tras esta solicitud: el aviso de «se pasa del saldo»
        # miraba el saldo de ANTES, así que una de 5 días con 3 libres no avisaba.
        s = AU.saldo(grupo, usuario, str(r.get("Type")))
        if not s["ilimitado"]:
            try:
                _dias = float(str(r.get("Days") or 0).replace(",", "."))
            except ValueError:
                _dias = 0.0
            _tras = s["restantes"] - _dias
            _txt = (t("They have **{r}** of {a} days of {tipo} this year → **{d}** after "
                      "this request")
                    .replace("{r}", f"{s['restantes']:.0f}").replace("{a}", f"{s['asignados']:.0f}")
                    .replace("{tipo}", cfg.get("nombre", "").lower()).replace("{d}", f"{_tras:.0f}"))
            (st.error if _tras < 0 else st.caption)(
                _txt + (t(" — **this would go over the balance**") if _tras < 0 else "."))

        # ⚠️ Las obras que quedarían sin esa persona: lo que «todo lo que implica»
        # significa de verdad. Se enseña ANTES de decidir, no después.
        ch = AU.choques(grupo, usuario, r.get("From"), r.get("To"))
        if ch:
            _obras = {}
            for c in ch:
                _obras.setdefault(c["etiqueta"], []).append(c["fecha"])
            st.warning(t(":material/warning: They are already assigned on those days to") + " **"
                       + "**, **".join(_obras) + t("**. If you approve, those days are freed on the board."))
            # ⚠️ v666 · `ch` es una fila por (día, obra): 1 día con 2 obras decía «(2 day(s))» (ciclo 1)
            _nd = len({c["fecha"] for c in ch})
            _tit_c = (t("Who could cover it ({n} day(s))").replace("{n}", str(_nd)) if _nd == len(ch)
                      else t("Who could cover it ({d} day(s) · {n} assignments)").replace("{d}", str(_nd))
                      .replace("{n}", str(len(ch))))
            with st.expander(_tit_c, icon=":material/group:"):
                for c in ch:
                    subs = AU.sustitutos(grupo, c["fecha"], c.get("proyecto_id"),
                                         excluir=usuario)
                    _ok = [x["nombre"] for x in subs if x["cumple"]][:4]
                    _no = [x["nombre"] for x in subs if not x["cumple"]][:3]
                    st.markdown(f"**{_fdma(c['fecha'])}** · {c['etiqueta']}")
                    if _ok:
                        st.caption(t(":material/check: free and holding the certificates") + ": "
                                   + ", ".join(_ok))
                    elif _no:
                        st.caption(t(":material/warning: free but WITHOUT the certificates the "
                                     "site requires") + ": " + ", ".join(_no))
                    else:
                        st.caption(t(":material/block: nobody free that day."))
        else:
            st.caption(t(":material/check: They have no sites assigned on those days."))

        # Cobertura: no vaciar el equipo la misma semana
        _otros = set()
        for d in AU.dias_del_rango(r.get("From"), r.get("To"), True):
            for x in AU.ausentes_en(grupo, d):
                if str(x.get("ID")) != aid:
                    _otros.add(str(x.get("Name")))
        if _otros:
            st.info(f":material/groups: {len(_otros)} {t('other person(s) are already away those days')}: "
                    + ", ".join(sorted(_otros)))

        nota = st.text_input(t("Note (optional)"), key=f"ausnota_{aid}",
                             placeholder=t("This will be shown to the person"))
        c1, c2 = st.columns(2)
        # v555 · los dos botones solo APUNTAN la acción (ver `render_bandeja`)
        if c1.button(t(":material/check_circle: Approve"), key=f"ausok_{aid}",
                     type="primary", width="stretch"):
            st.session_state["_aus_accion"] = {"aid": aid, "aprobar": True, "nota": nota}
            st.rerun()
        if c2.button(t(":material/cancel: Reject"), key=f"ausno_{aid}",
                     width="stretch"):
            st.session_state["_aus_accion"] = {"aid": aid, "aprobar": False, "nota": nota}
            st.rerun()


def _avisar_exceso(usuario, r, como):
    """v633 · Le toca a su nómina: que no se entere por la colilla. Best-effort, como las demás."""
    try:
        from core import notify
        _rg = _rango(r.get("From"), r.get("To"))
        _s = "will be paid" if como == AU.EXCESO_PAGA else "stay unpaid"
        notify.notify_user(usuario, f"Sick leave: {_rg}",
                           [f"The days of your sick leave ({_rg}) that go over your balance "
                            f"<b>{_s}</b>."])
    except Exception as e:
        logger.warning("ausencias_ui._avisar_exceso: %s", e)


def _avisar_persona(usuario, r, aprobada, nota):
    """Best-effort: la decisión ya está guardada cuando se llega aquí.
    ⚠️ v555 · decía «has been aprobada» / «Absence rechazada» en un correo en inglés."""
    try:
        from core import notify
        cfg = AU.TIPOS.get(str(r.get("Type", "")), {})
        _s = "approved" if aprobada else "rejected"
        _l = [f"Your request for <b>{cfg.get('nombre')}</b> "
              f"({_rango(r.get('From'), r.get('To'))}) has been <b>{_s}</b>."]
        if str(nota or "").strip():
            _l.append(f"{t('Note')}: {nota}")
        notify.notify_user(usuario, f"Absence {_s}: {_rango(r.get('From'), r.get('To'))}", _l)
    except Exception as e:
        logger.warning("ausencias_ui._avisar_persona: %s", e)


def _avisar_persona_cancelada(usuario, r):
    """Avisa a la persona de que el ADMIN le ha cancelado una ausencia (v555).
    Best-effort: la cancelación ya está guardada y el tablero limpio."""
    try:
        from core import notify
        cfg = AU.TIPOS.get(str(r.get("Type", "")), {})
        _rg = _rango(r.get("From"), r.get("To"))
        notify.notify_user(usuario, f"Absence cancelled: {_rg}",
                           [f"Your <b>{cfg.get('nombre', r.get('Type'))}</b> ({_rg}) has been "
                            "<b>cancelled</b> by the administrator.",
                            "Those days are back in the planner."])
    except Exception as e:
        logger.warning("ausencias_ui._avisar_persona_cancelada: %s", e)
