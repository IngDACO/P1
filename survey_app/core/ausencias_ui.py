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

logger = logging.getLogger(__name__)


def _kpi(label, valor, pie=None, color=None):
    from core.projects_ui import _kpi_card       # el kit de siempre (v283)
    return _kpi_card(label, valor, color, pie=pie)


def _chip_estado(e: str) -> str:
    return {AU.PENDIENTE: "🟡 pending", AU.APROBADA: "🟢 approved",
            AU.RECHAZADA: "🔴 rejected", AU.CANCELADA: "⚪ cancelled"}.get(e, e)


def _fdma(x) -> str:
    """dd/mm/aaaa (v555): la app enseña las fechas así (v544) con UN helper,
    `projects_ui._fmt_fecha`; el ISO es solo de la hoja."""
    from core.projects_ui import _fmt_fecha
    return _fmt_fecha(x.isoformat() if hasattr(x, "isoformat") else x)


def _rango(desde, hasta) -> str:
    """«13/10/2026 → 14/10/2026», o UN día si empieza y acaba el mismo (salía «22 → 22»)."""
    a, b = _fdma(desde), _fdma(hasta)
    return a if a == b else f"{a} → {b}"


def _linea(r) -> str:
    return (f"**{AU.nombre_tipo(r.get('Type'))}** · {_rango(r.get('From'), r.get('To'))} · "
            f"{r.get('Days')} {t('day(s)')} · {_chip_estado(str(r.get('Status')))}")


# ═══════════════════════════════════════════════════════════════════
# CAMPO — Mis ausencias
# ═══════════════════════════════════════════════════════════════════
def render_mis_ausencias():
    """⚠️ CON título propio: es una sección del campo SIN sub-pestañas, así que la
    shell no pinta ninguna cabecera (regla v320: solo las que cuelgan de una sección
    con subs tienen título duplicado)."""
    st.markdown(t("## :material/event_busy: My absences"))
    a = st.session_state.get("auth", {}) or {}
    usuario = str(a.get("usuario", ""))
    nombre = str(a.get("nombre") or usuario)
    grupo = str(a.get("grupo", ""))
    if not AU.is_configured():
        st.warning(t(":material/warning: Absences need Google Sheets configured."))
        return

    # ── Saldo ──────────────────────────────────────────────────────
    tarj = []
    _per = None
    # ⚠️ `_tp`, no `t`: la variable del bucle taparía la función de idioma en el
    # ámbito ENTERO de la función (el fallo del glosario de v437).
    for _tp, cfg in AU.TIPOS.items():
        s = AU.saldo(grupo, usuario, _tp)
        _per = _per or s.get("periodo")
        if s["ilimitado"]:
            tarj.append(_kpi(AU.nombre_tipo(_tp), f"{s['usados']:.0f}",
                             pie=t("days used in the period")))
        else:
            _col = "#c0392b" if s["restantes"] <= 0 else None
            tarj.append(_kpi(AU.nombre_tipo(_tp), f"{s['restantes']:.0f}",
                             pie=f"{t('of')} {s['asignados']:.0f} · {t('used')} {s['usados']:.0f}",
                             color=_col))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    # ⚠️ v433: DE QUÉ periodo habla el saldo. Sin esto, «te quedan 14» no dice hasta
    # cuándo, y con el año por aniversario cada persona tiene el suyo. Y si falta la
    # fecha de alta, se avisa de que es una estimación en vez de dar un número que
    # parece exacto.
    if _per:
        if _per["origen"] == "aniversario":
            st.caption(f"{t(':material/event_available: Your leave year runs from')} "
                       f"**{_per['desde']}** to **{_per['hasta']}** "
                       f"({t('since you started, on')} {_per['ingreso']}).")
        else:
            st.caption(f"{t(':material/help: We are counting by calendar year')} "
                       f"(**{_per['desde']}** → **{_per['hasta']}**) because your start date "
                       "is not on record. Ask your manager to enter it and the "
                       "balance will count from your anniversary.")

    # ── Pedir ──────────────────────────────────────────────────────
    with st.expander(t("Request a day off or annual leave, or report sick leave"),
                     icon=":material/add_circle:", expanded=True, key="exp_aus_pedir"):
        # ⚠️ El tipo va FUERA del form: el formulario tiene que poder reaccionar a él
        # (la enfermedad no se «pide», se avisa) y dentro de un form los widgets no
        # escriben hasta el submit — la razón de v127, v189 y v306.
        _tipos = list(AU.TIPOS)
        tipo = st.selectbox(
            t("What do you need?"), _tipos, key="aus_tipo",
            # ⚠️ EMOJI, no `:material/…:`: en las opciones de un selectbox el material
            # sale como texto literal (medido en el Cloud). En `st.radio` sí funciona.
            format_func=lambda _k: f"{AU.TIPOS[_k]['emoji']} {AU.nombre_tipo(_k)}")
        cfg = AU.TIPOS[tipo]
        if not cfg["aprobacion"]:
            st.info(t(":material/info: Sick leave **is recorded straight away**: you do not have to wait for anyone to approve it. Your manager will see it as soon as you send it."))
        _s = AU.saldo(grupo, usuario, tipo)
        if not _s["ilimitado"]:
            if _s["restantes"] <= 0:
                st.error(f":material/block: You have no days left of {cfg['nombre'].lower()} "
                         f"this year (used {_s['usados']:.0f} of {_s['asignados']:.0f}). "
                         "Talk to your manager.")
            elif _s["restantes"] <= 3:
                st.warning(f":material/warning: You have only **{_s['restantes']:.0f} "
                           f"day(s)** of {cfg['nombre'].lower()} this year.")

        with st.form("aus_form"):
            c1, c2 = st.columns(2)
            hoy = clock.today(grupo)
            desde = c1.date_input(t("From"), value=hoy, key="aus_desde")
            hasta = c2.date_input(t("To"), value=hoy, key="aus_hasta")
            findes = st.checkbox(t("Include weekends"), key="aus_findes",
                                 help=t("Tick this only if those days are worked. Otherwise they are not taken off your balance."))
            motivo = st.text_input(t("Reason (optional)"), key="aus_motivo",
                                   placeholder=t("Family trip, medical appointment…"))
            _enviar = st.form_submit_button(
                (t(":material/send: Send request") if cfg["aprobacion"]
                 else t(":material/send: Record the sick leave")),
                type="primary", width="stretch")
        if _enviar:
            _d = AU.dias_del_rango(desde, hasta, findes)
            if not _s["ilimitado"] and len(_d) > _s["restantes"]:
                st.error(f":material/block: You are asking for **{len(_d)} {t('day(s)')}** and you have "
                         f"**{_s['restantes']:.0f}**.")
            else:
                ok, res = AU.solicitar(grupo, usuario, nombre, tipo, desde, hasta,
                                       motivo, incluir_findes=findes)
                if not ok:
                    st.error(res)
                else:
                    # La enfermedad nace aprobada → al tablero YA. Las demás, al aprobar.
                    if not cfg["aprobacion"]:
                        _ok2, _n = AU.aplicar_al_roster(AU.get(res) or {})
                        if not _ok2:
                            logger.warning("ausencias_ui: roster: %s", _n)
                    _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg)
                    for k in ("aus_motivo", "aus_findes"):
                        st.session_state.pop(k, None)
                    flash.exito(
                        f"{cfg['nombre']} recorded ({res})." if not cfg["aprobacion"]
                        else f"{t('Request sent')} ({res}). {t('We will let you know when it is resolved.')}")
                    st.rerun()

    # ── Lo mío ─────────────────────────────────────────────────────
    st.markdown(t("#### :material/history: My requests"))
    mias = AU.list_group(grupo, usuario=usuario)
    if not mias:
        st.caption(t("You have not requested any absence yet."))
        return
    for r in mias[:15]:
        with st.container(border=True):
            st.markdown(_linea(r))
            _pie = []
            if str(r.get("Reason", "")).strip():
                _pie.append(str(r.get("Reason")))
            if str(r.get("AdminNote", "")).strip():
                _pie.append(f"nota: {r.get('AdminNote')}")
            if str(r.get("ResolvedBy", "")).strip():
                _pie.append(f"{t('resolved by')} {r.get('ResolvedBy')}")
            if _pie:
                st.caption(" · ".join(_pie))
            if str(r.get("Status")) in AU.VIGENTES:
                if st.button(t(":material/undo: Cancel"), key=f"auscan_{r['ID']}"):
                    _estaba = str(r.get("Status")) == AU.APROBADA
                    ok, msg = AU.cancelar(r["ID"], usuario)
                    if ok:
                        # si ya estaba en el tablero, hay que quitarla de ahí
                        AU.aplicar_al_roster(r, quitar=True)
                        # ⚠️ v432: cancelar una APROBADA devuelve esos días al tablero,
                        # y quien la aprobó pudo haber reorganizado la cuadrilla
                        # contando con la ausencia. La solicitud le llegaba; la
                        # cancelación no. Solo para las aprobadas: retirar una
                        # pendiente no cambia nada que nadie hubiera planificado.
                        if _estaba:
                            _avisar_cancelacion(grupo, nombre, r)
                        flash.exito(msg)
                        st.rerun()
                    else:
                        st.error(msg)


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
                 f"({r.get('From')} → {r.get('To')})")
        _lines = [f"<b>{nombre}</b> has CANCELLED their "
                  f"<b>{cfg.get('nombre', r.get('Type'))}</b> "
                  f"from {r.get('From')} to {r.get('To')}.",
                  "Those days are free again in the planner: if you had reorganised "
                  "the crew, review it."]
        for d in _admins_and_owners(grupo):
            try:
                notify.notify_user(d, _subj, _lines)
            except Exception:
                pass
    except Exception as e:
        logger.warning("ausencias_ui._avisar_cancelacion: %s", e)


def _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg):
    """Avisa a quien decide. ⚠️ Best-effort: que falle un correo no puede impedir
    registrar la ausencia — la solicitud ya está guardada cuando se llega aquí."""
    try:
        from core import notify
        from core.alerts import _admins_and_owners
        _subj = (f"{cfg['nombre']}: {nombre} ({desde} → {hasta})")
        _lines = [f"<b>{nombre}</b> has recorded: <b>{cfg['nombre']}</b>",
                  f"From {desde} to {hasta}.",
                  ("It was recorded automatically (no approval needed)."
                   if not cfg["aprobacion"] else
                   "It is PENDING your approval → Planning · Absences.")]
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
    from core.num import parse_date as _pd
    _bajas = [r for r in todas if str(r.get("Type")) == AU.ENFERMEDAD
              and str(r.get("Status")) == AU.APROBADA
              and (_pd(r.get("To")) or hoy) >= hoy - timedelta(days=14)]
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
    if acc.get("cancelar"):
        _estaba = str(r.get("Status")) == AU.APROBADA
        ok, msg = AU.cancelar(aid, quien)
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
    nota = str(acc.get("nota") or "")
    ok, msg = AU.resolver(aid, aprobar, quien, nota)
    if not ok:
        flash.error(msg)
        return
    if aprobar:
        # ⚠️ El orden importa: primero la decisión, luego el tablero. Si el roster
        # fallara, la ausencia queda aprobada y el tablero se puede reintentar; al
        # revés, el tablero diría que está fuera sin que nadie lo haya aprobado.
        _ok2, _n = AU.aplicar_al_roster(_de_grupo(grupo, aid) or r)
        _avisar_persona(usuario, r, True, nota)
        flash.exito(msg + (f" {_n} {t('day(s) marked in the planner.')}" if _ok2 else
                           f" ⚠️ {t('Could not write to the planner')}: {_n}"))
    else:
        _avisar_persona(usuario, r, False, nota)
        flash.aviso(msg)


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
            with st.expander(t("Who could cover it ({n} day(s))").replace("{n}", str(len(ch))),
                             icon=":material/group:"):
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
