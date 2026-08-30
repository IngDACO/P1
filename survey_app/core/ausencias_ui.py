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
    return {AU.PENDIENTE: "🟡 pendiente", AU.APROBADA: "🟢 aprobada",
            AU.RECHAZADA: "🔴 rechazada", AU.CANCELADA: "⚪ cancelada"}.get(e, e)


def _linea(r) -> str:
    cfg = AU.TIPOS.get(str(r.get("Tipo", "")), {})
    return (f"**{cfg.get('nombre', r.get('Tipo'))}** · {r.get('Desde')} → "
            f"{r.get('Hasta')} · {r.get('Dias')} {t('day(s)')} · {_chip_estado(str(r.get('Estado')))}")


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
            tarj.append(_kpi(cfg["nombre"], f"{s['usados']:.0f}",
                             pie=t("days used in the period")))
        else:
            _col = "#c0392b" if s["restantes"] <= 0 else None
            tarj.append(_kpi(cfg["nombre"], f"{s['restantes']:.0f}",
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
                     icon=":material/add_circle:", expanded=True):
        # ⚠️ El tipo va FUERA del form: el formulario tiene que poder reaccionar a él
        # (la enfermedad no se «pide», se avisa) y dentro de un form los widgets no
        # escriben hasta el submit — la razón de v127, v189 y v306.
        _tipos = list(AU.TIPOS)
        tipo = st.selectbox(
            t("What do you need?"), _tipos, key="aus_tipo",
            # ⚠️ EMOJI, no `:material/…:`: en las opciones de un selectbox el material
            # sale como texto literal (medido en el Cloud). En `st.radio` sí funciona.
            format_func=lambda _k: f"{AU.TIPOS[_k]['emoji']} {AU.TIPOS[_k]['nombre']}")
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
            if str(r.get("Motivo", "")).strip():
                _pie.append(str(r.get("Motivo")))
            if str(r.get("NotaAdmin", "")).strip():
                _pie.append(f"nota: {r.get('NotaAdmin')}")
            if str(r.get("ResueltaPor", "")).strip():
                _pie.append(f"{t('resolved by')} {r.get('ResueltaPor')}")
            if _pie:
                st.caption(" · ".join(_pie))
            if str(r.get("Estado")) in AU.VIGENTES:
                if st.button(t(":material/undo: Cancel"), key=f"auscan_{r['ID']}"):
                    _estaba = str(r.get("Estado")) == AU.APROBADA
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
        cfg = AU.TIPOS.get(str(r.get("Tipo", "")), {})
        _subj = (f"CANCELADA — {cfg.get('nombre', r.get('Tipo'))}: {nombre} "
                 f"({r.get('Desde')} → {r.get('Hasta')})")
        _lines = [f"<b>{nombre}</b> has CANCELLED their "
                  f"<b>{cfg.get('nombre', r.get('Tipo'))}</b> "
                  f"from {r.get('Desde')} to {r.get('Hasta')}.",
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
    todas = AU.list_group(grupo)
    pend = [r for r in todas if str(r.get("Estado")) == AU.PENDIENTE]
    hoy = clock.today(grupo)
    fuera_hoy = AU.ausentes_en(grupo, hoy)
    _sem = [r for r in todas if str(r.get("Estado")) == AU.APROBADA
            and any(hoy <= d <= hoy + timedelta(days=7)
                    for d in AU.dias_del_rango(r.get("Desde"), r.get("Hasta"), True))]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join([
                    _kpi(t("Pending"), str(len(pend)),
                         pie=t("waiting for your decision"),
                         color="#c77700" if pend else None),
                    _kpi(t("Away today"), str(len(fuera_hoy)),
                         pie=", ".join(str(x.get("Nombre")) for x in fuera_hoy) or t("nobody")),
                    _kpi(t("Next 7 days"), str(len(_sem)), pie=t("approved absences")),
                ]) + "</div>", unsafe_allow_html=True)

    # ── Pendientes ─────────────────────────────────────────────────
    st.markdown(t("#### :material/inbox: Waiting for approval"))
    if not pend:
        st.success(t(":material/check_circle: No pending requests."))
    for r in pend:
        _tarjeta_pendiente(grupo, r, quien)

    # ── Histórico ──────────────────────────────────────────────────
    with st.expander(f"History ({len(todas)})", icon=":material/history:"):
        if not todas:
            st.caption(t("No absences recorded."))
        for r in todas[:40]:
            st.markdown(f"`{r['ID']}` · **{r.get('Nombre')}** — " + _linea(r))


def _tarjeta_pendiente(grupo, r, quien):
    aid = str(r.get("ID"))
    usuario = str(r.get("Usuario"))
    cfg = AU.TIPOS.get(str(r.get("Tipo", "")), {})
    with st.container(border=True, key=f"auspend_{aid}"):
        st.markdown(f"**{r.get('Nombre')}** — " + _linea(r))
        if str(r.get("Motivo", "")).strip():
            st.caption(f":material/notes: {r.get('Motivo')}")

        # Saldo de esa persona: aprobar a ciegas es lo que esto viene a evitar
        s = AU.saldo(grupo, usuario, str(r.get("Tipo")))
        if not s["ilimitado"]:
            _txt = (f"They have **{s['restantes']:.0f}** of {s['asignados']:.0f} days "
                    f"{t('of')} {cfg.get('nombre', '').lower()} {t('this year')}")
            (st.error if s["restantes"] < 0 else st.caption)(
                _txt + (t(" — **this would go over the balance**") if s["restantes"] < 0 else "."))

        # ⚠️ Las obras que quedarían sin esa persona: lo que «todo lo que implica»
        # significa de verdad. Se enseña ANTES de decidir, no después.
        ch = AU.choques(grupo, usuario, r.get("Desde"), r.get("Hasta"))
        if ch:
            _obras = {}
            for c in ch:
                _obras.setdefault(c["etiqueta"], []).append(c["fecha"])
            st.warning(t(":material/warning: They are already assigned on those days to") + " **"
                       + "**, **".join(_obras) + t("**. If you approve, those days are freed on the board."))
            with st.expander(f"Who could cover it ({len(ch)} day(s))",
                             icon=":material/group:"):
                for c in ch:
                    subs = AU.sustitutos(grupo, c["fecha"], c.get("proyecto_id"),
                                         excluir=usuario)
                    _ok = [x["nombre"] for x in subs if x["cumple"]][:4]
                    _no = [x["nombre"] for x in subs if not x["cumple"]][:3]
                    st.markdown(f"**{c['fecha']}** · {c['etiqueta']}")
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
        for d in AU.dias_del_rango(r.get("Desde"), r.get("Hasta"), True):
            for x in AU.ausentes_en(grupo, d):
                if str(x.get("ID")) != aid:
                    _otros.add(str(x.get("Nombre")))
        if _otros:
            st.info(f":material/groups: {len(_otros)} {t('other person(s) are already away those days')}: "
                    + ", ".join(sorted(_otros)))

        nota = st.text_input(t("Note (optional)"), key=f"ausnota_{aid}",
                             placeholder=t("This will be shown to the person"))
        c1, c2 = st.columns(2)
        if c1.button(t(":material/check_circle: Approve"), key=f"ausok_{aid}",
                     type="primary", width="stretch"):
            ok, msg = AU.resolver(aid, True, quien, nota)
            if ok:
                # ⚠️ El orden importa: primero la decisión, luego el tablero. Si el
                # roster fallara, la ausencia queda aprobada y el tablero se puede
                # reintentar; al revés, el tablero diría que está fuera sin que nadie
                # lo haya aprobado.
                _ok2, _n = AU.aplicar_al_roster(AU.get(aid) or r)
                _avisar_persona(usuario, r, True, nota)
                flash.exito(msg + (f" {_n} {t('day(s) marked in the planner.')}"
                                   if _ok2 else
                                   f" ⚠️ {t('Could not write to the planner')}: {_n}"))
                st.rerun()
            else:
                st.error(msg)
        if c2.button(t(":material/cancel: Reject"), key=f"ausno_{aid}",
                     width="stretch"):
            ok, msg = AU.resolver(aid, False, quien, nota)
            if ok:
                _avisar_persona(usuario, r, False, nota)
                flash.aviso(msg)
                st.rerun()
            else:
                st.error(msg)


def _avisar_persona(usuario, r, aprobada, nota):
    """Best-effort: la decisión ya está guardada cuando se llega aquí."""
    try:
        from core import notify
        cfg = AU.TIPOS.get(str(r.get("Tipo", "")), {})
        _s = "aprobada" if aprobada else "rechazada"
        _l = [f"Your request for <b>{cfg.get('nombre')}</b> "
              f"({r.get('Desde')} → {r.get('Hasta')}) has been <b>{_s}</b>."]
        if str(nota or "").strip():
            _l.append(f"{t('Note')}: {nota}")
        notify.notify_user(usuario, f"Absence {_s}: {r.get('Desde')} → {r.get('Hasta')}", _l)
    except Exception as e:
        logger.warning("ausencias_ui._avisar_persona: %s", e)
