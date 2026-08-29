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
            f"{r.get('Hasta')} · {r.get('Dias')} día(s) · {_chip_estado(str(r.get('Estado')))}")


# ═══════════════════════════════════════════════════════════════════
# CAMPO — Mis ausencias
# ═══════════════════════════════════════════════════════════════════
def render_mis_ausencias():
    """⚠️ CON título propio: es una sección del campo SIN sub-pestañas, así que la
    shell no pinta ninguna cabecera (regla v320: solo las que cuelgan de una sección
    con subs tienen título duplicado)."""
    st.markdown("## :material/event_busy: Mis ausencias")
    a = st.session_state.get("auth", {}) or {}
    usuario = str(a.get("usuario", ""))
    nombre = str(a.get("nombre") or usuario)
    grupo = str(a.get("grupo", ""))
    if not AU.is_configured():
        st.warning(":material/warning: Las ausencias necesitan Google Sheets configurado.")
        return

    # ── Saldo ──────────────────────────────────────────────────────
    tarj = []
    for t, cfg in AU.TIPOS.items():
        s = AU.saldo(grupo, usuario, t)
        if s["ilimitado"]:
            tarj.append(_kpi(cfg["nombre"], f"{s['usados']:.0f}",
                             pie="días usados este año"))
        else:
            _col = "#c0392b" if s["restantes"] <= 0 else None
            tarj.append(_kpi(cfg["nombre"], f"{s['restantes']:.0f}",
                             pie=f"de {s['asignados']:.0f} · usados {s['usados']:.0f}",
                             color=_col))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── Pedir ──────────────────────────────────────────────────────
    with st.expander("Pedir un día libre, vacaciones o avisar de una baja",
                     icon=":material/add_circle:", expanded=True):
        # ⚠️ El tipo va FUERA del form: el formulario tiene que poder reaccionar a él
        # (la enfermedad no se «pide», se avisa) y dentro de un form los widgets no
        # escriben hasta el submit — la razón de v127, v189 y v306.
        _tipos = list(AU.TIPOS)
        tipo = st.selectbox(
            "¿Qué necesitas?", _tipos, key="aus_tipo",
            # ⚠️ EMOJI, no `:material/…:`: en las opciones de un selectbox el material
            # sale como texto literal (medido en el Cloud). En `st.radio` sí funciona.
            format_func=lambda t: f"{AU.TIPOS[t]['emoji']} {AU.TIPOS[t]['nombre']}")
        cfg = AU.TIPOS[tipo]
        if not cfg["aprobacion"]:
            st.info(":material/info: Una baja por enfermedad **se registra al momento**: "
                    "no tienes que esperar a que nadie la apruebe. Tu responsable la verá "
                    "en cuanto la envíes.")
        _s = AU.saldo(grupo, usuario, tipo)
        if not _s["ilimitado"]:
            if _s["restantes"] <= 0:
                st.error(f":material/block: No te quedan días de {cfg['nombre'].lower()} "
                         f"este año (usados {_s['usados']:.0f} de {_s['asignados']:.0f}). "
                         "Habla con tu responsable.")
            elif _s["restantes"] <= 3:
                st.warning(f":material/warning: Te quedan solo **{_s['restantes']:.0f} "
                           f"día(s)** de {cfg['nombre'].lower()} este año.")

        with st.form("aus_form"):
            c1, c2 = st.columns(2)
            hoy = clock.today(grupo)
            desde = c1.date_input("Desde", value=hoy, key="aus_desde")
            hasta = c2.date_input("Hasta", value=hoy, key="aus_hasta")
            findes = st.checkbox("Incluir fines de semana", key="aus_findes",
                                 help="Márcalo solo si en esos días se trabaja. Si no, "
                                      "no se te descuentan del saldo.")
            motivo = st.text_input("Motivo (opcional)", key="aus_motivo",
                                   placeholder="Viaje familiar, cita médica…")
            _enviar = st.form_submit_button(
                (":material/send: Enviar solicitud" if cfg["aprobacion"]
                 else ":material/send: Registrar la baja"),
                type="primary", width="stretch")
        if _enviar:
            _d = AU.dias_del_rango(desde, hasta, findes)
            if not _s["ilimitado"] and len(_d) > _s["restantes"]:
                st.error(f":material/block: Pides **{len(_d)} día(s)** y te quedan "
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
                        f"{cfg['nombre']} registrada ({res})." if not cfg["aprobacion"]
                        else f"Solicitud enviada ({res}). Te avisaremos al resolverla.")
                    st.rerun()

    # ── Lo mío ─────────────────────────────────────────────────────
    st.markdown("#### :material/history: Mis solicitudes")
    mias = AU.list_group(grupo, usuario=usuario)
    if not mias:
        st.caption("Todavía no has pedido ninguna ausencia.")
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
                _pie.append(f"resuelta por {r.get('ResueltaPor')}")
            if _pie:
                st.caption(" · ".join(_pie))
            if str(r.get("Estado")) in AU.VIGENTES:
                if st.button(":material/undo: Cancelar", key=f"auscan_{r['ID']}"):
                    ok, msg = AU.cancelar(r["ID"], usuario)
                    if ok:
                        # si ya estaba en el tablero, hay que quitarla de ahí
                        AU.aplicar_al_roster(r, quitar=True)
                        flash.exito(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg):
    """Avisa a quien decide. ⚠️ Best-effort: que falle un correo no puede impedir
    registrar la ausencia — la solicitud ya está guardada cuando se llega aquí."""
    try:
        from core import notify
        from core.alerts import _admins_and_owners
        _subj = (f"{cfg['nombre']}: {nombre} ({desde} → {hasta})")
        _lines = [f"<b>{nombre}</b> ha registrado: <b>{cfg['nombre']}</b>",
                  f"Del {desde} al {hasta}.",
                  ("Se registró automáticamente (no requiere aprobación)."
                   if not cfg["aprobacion"] else
                   "Está PENDIENTE de tu aprobación → Planificación · Ausencias.")]
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
        st.warning(":material/warning: Las ausencias necesitan Google Sheets configurado.")
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
                    _kpi("Pendientes", str(len(pend)),
                         pie="esperan tu decisión",
                         color="#c77700" if pend else None),
                    _kpi("Fuera hoy", str(len(fuera_hoy)),
                         pie=", ".join(str(x.get("Nombre")) for x in fuera_hoy) or "nadie"),
                    _kpi("Próximos 7 días", str(len(_sem)), pie="ausencias aprobadas"),
                ]) + "</div>", unsafe_allow_html=True)

    # ── Pendientes ─────────────────────────────────────────────────
    st.markdown("#### :material/inbox: Pendientes de aprobar")
    if not pend:
        st.success(":material/check_circle: No hay solicitudes pendientes.")
    for r in pend:
        _tarjeta_pendiente(grupo, r, quien)

    # ── Histórico ──────────────────────────────────────────────────
    with st.expander(f"Histórico ({len(todas)})", icon=":material/history:"):
        if not todas:
            st.caption("Sin ausencias registradas.")
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
            _txt = (f"Le quedan **{s['restantes']:.0f}** de {s['asignados']:.0f} días "
                    f"de {cfg.get('nombre', '').lower()} este año")
            (st.error if s["restantes"] < 0 else st.caption)(
                _txt + (" — **se pasaría del saldo**" if s["restantes"] < 0 else "."))

        # ⚠️ Las obras que quedarían sin esa persona: lo que «todo lo que implica»
        # significa de verdad. Se enseña ANTES de decidir, no después.
        ch = AU.choques(grupo, usuario, r.get("Desde"), r.get("Hasta"))
        if ch:
            _obras = {}
            for c in ch:
                _obras.setdefault(c["etiqueta"], []).append(c["fecha"])
            st.warning(":material/warning: Ya está asignado esos días a **"
                       + "**, **".join(_obras) + "**. Si apruebas, esos días quedan "
                       "libres en el tablero.")
            with st.expander(f"Quién podría cubrirlo ({len(ch)} día(s))",
                             icon=":material/group:"):
                for c in ch:
                    subs = AU.sustitutos(grupo, c["fecha"], c.get("proyecto_id"),
                                         excluir=usuario)
                    _ok = [x["nombre"] for x in subs if x["cumple"]][:4]
                    _no = [x["nombre"] for x in subs if not x["cumple"]][:3]
                    st.markdown(f"**{c['fecha']}** · {c['etiqueta']}")
                    if _ok:
                        st.caption(":material/check: libres y con los certificados: "
                                   + ", ".join(_ok))
                    elif _no:
                        st.caption(":material/warning: libres pero SIN los certificados "
                                   "que exige la obra: " + ", ".join(_no))
                    else:
                        st.caption(":material/block: nadie libre ese día.")
        else:
            st.caption(":material/check: No tiene obras asignadas esos días.")

        # Cobertura: no vaciar el equipo la misma semana
        _otros = set()
        for d in AU.dias_del_rango(r.get("Desde"), r.get("Hasta"), True):
            for x in AU.ausentes_en(grupo, d):
                if str(x.get("ID")) != aid:
                    _otros.add(str(x.get("Nombre")))
        if _otros:
            st.info(f":material/groups: Esos días ya hay {len(_otros)} persona(s) fuera: "
                    + ", ".join(sorted(_otros)))

        nota = st.text_input("Nota (opcional)", key=f"ausnota_{aid}",
                             placeholder="Se le mostrará a la persona")
        c1, c2 = st.columns(2)
        if c1.button(":material/check_circle: Aprobar", key=f"ausok_{aid}",
                     type="primary", width="stretch"):
            ok, msg = AU.resolver(aid, True, quien, nota)
            if ok:
                # ⚠️ El orden importa: primero la decisión, luego el tablero. Si el
                # roster fallara, la ausencia queda aprobada y el tablero se puede
                # reintentar; al revés, el tablero diría que está fuera sin que nadie
                # lo haya aprobado.
                _ok2, _n = AU.aplicar_al_roster(AU.get(aid) or r)
                _avisar_persona(usuario, r, True, nota)
                flash.exito(msg + (f" {_n} día(s) marcados en el planificador."
                                   if _ok2 else
                                   f" ⚠️ No se pudo escribir en el planificador: {_n}"))
                st.rerun()
            else:
                st.error(msg)
        if c2.button(":material/cancel: Rechazar", key=f"ausno_{aid}",
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
        _l = [f"Tu solicitud de <b>{cfg.get('nombre')}</b> "
              f"({r.get('Desde')} → {r.get('Hasta')}) ha sido <b>{_s}</b>."]
        if str(nota or "").strip():
            _l.append(f"Nota: {nota}")
        notify.notify_user(usuario, f"Ausencia {_s}: {r.get('Desde')} → {r.get('Hasta')}", _l)
    except Exception as e:
        logger.warning("ausencias_ui._avisar_persona: %s", e)
