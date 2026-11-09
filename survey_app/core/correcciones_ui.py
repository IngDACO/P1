"""Bandeja del administrador: las correcciones de fichaje que pidió el equipo (v461).

⚠️ La hora ya está aplicada cuando esta pantalla la muestra (decisión del usuario): lo
que se decide aquí es si se CONFIRMA o se REVIERTE, no si se aplica. Por eso la
tarjeta enseña las dos horas —la que había y la que hay— y no un «pendiente de
aplicar» que sería mentira.

v556 (recorrido de Time fixes): el DÍA del fichaje en la tarjeta y en el historial;
«Set the right time» en TODAS las tarjetas (cuando revertir choca con otra jornada no
quedaba salida); las correcciones que otra posterior volvió a cambiar se cierran como
sustituidas; la persona se entera cuando su hora cambia; acción DIFERIDA (trampa 37);
lo más antiguo primero y tarjetas activas.
"""
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from core import auth, clock, correcciones as C, flash, theme, timeclock
from core import i18n
from core.i18n import t

logger = logging.getLogger(__name__)

_DIAS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _etq(grupo) -> dict:
    """`{usuario: etiqueta}` del grupo, con el login detrás solo si el nombre se
    repite (v319).

    ⚠️ Se desempata sobre TODO el grupo, no sobre las correcciones visibles: si no,
    la misma persona sería «Mei Chen» en una bandeja donde está sola y «Mei Chen
    (mchen)» en otra, y una identidad que cambia de nombre según la pantalla no es
    una identidad (v413). `list_users` está cacheado → 0 lecturas nuevas.
    """
    try:
        return auth.etiqueta_usuarios(auth.list_users(grupo))
    except Exception as e:
        logger.warning("no se pudieron etiquetar los usuarios: %s", e)
        return {}


def _hhmm(v) -> str:
    """«2026-09-03 07:00:00» → «07:00». Vacío → «—» (una sesión abierta no tiene
    salida, y pintar un 0 la haría parecer una jornada de cero horas, v346)."""
    s = str(v or "").strip()
    return s[11:16] if len(s) >= 16 else (s or "—")


def _hora_de(v):
    """La parte de HORA de un timestamp, para sembrar el `time_input`."""
    try:
        return datetime.strptime(str(v), timeclock.FMT).time().replace(
            second=0, microsecond=0)
    except Exception:
        return clock.now().time().replace(second=0, microsecond=0)


def _dif_horas(r) -> str:
    """Cuánto cambió, en horas. Es el dato que decide: media hora es un olvido, seis
    es otra cosa."""
    # ⚠️ v663 · el EFECTO en horas trabajadas, no el desplazamiento de la marca: una entrada que
    # pasa de 14:48 a 14:30 SUMA 0,30 h y salía «−0.30 h» (ciclo 1).
    try:
        a = datetime.strptime(str(r.get("OldValue")), timeclock.FMT)
        b = datetime.strptime(str(r.get("NewValue")), timeclock.FMT)
        d = (b - a).total_seconds() / 3600.0
        if str(r.get("Field", "")) == C.CAMPO_IN:
            d = -d
        return t("{d} h worked", d=f"{d:+.2f}")
    except Exception:
        return "—"


def _dia(r) -> str:
    """El DÍA del fichaje corregido, «Thu 09/10/2026» (v556). La tarjeta decía «Was
    05:46 → now 05:45» sin decir de qué jornada; solo el «Asked on», que es otra cosa."""
    from core.projects_ui import _fmt_fecha
    for v in (r.get("NewValue"), r.get("OldValue")):
        try:
            d = datetime.strptime(str(v)[:10], "%Y-%m-%d")
        except (TypeError, ValueError):
            continue
        return f"{t(_DIAS[d.weekday()])} {_fmt_fecha(str(v)[:10])}"
    return "—"


def _fdmh(ts) -> str:
    """«2026-10-09 05:46:00» → «09/10/2026 05:46» (v556; salía en ISO)."""
    from core.projects_ui import _fmt_fecha
    s = str(ts or "").strip()
    if len(s) < 10:
        return s or "—"
    return (_fmt_fecha(s[:10]) + (" " + s[11:16] if len(s) >= 16 else "")).strip()


def _tipo_txt(r) -> str:
    """«workday» o «project» (v556): salía el dato crudo, «· `general`»."""
    return (t("workday") if str(r.get("Type", "")) == timeclock.TIPO_GENERAL
            else t("project"))


def _apuntar(cid, accion, **extra):
    """v556 · El botón solo APUNTA la acción y relanza: se ejecuta arriba, antes de
    pintar la lista (`_accion_pendiente`). Ver la trampa 37."""
    st.session_state["_cor_accion"] = dict(cid=str(cid), accion=accion, **extra)
    st.rerun()


def _tarjeta(grupo, r, quien, etq, por=""):
    _id = str(r.get("ID", ""))
    _es_in = str(r.get("Field", "")) == C.CAMPO_IN
    with st.container(border=True, key=f"cor_{_id}"):
        c1, c2 = st.columns([3, 2])
        # ⚠️ Dos personas pueden llamarse igual: en la pantalla donde se decide
        # sobre las horas de alguien, dos tarjetas idénticas son inservibles.
        _usr = str(r.get("User", ""))
        _nom = etq.get(_usr) or str(r.get("Name") or _usr or "—")
        c1.markdown(f"**{_nom}** · "
                    + (t("clock in") if _es_in else t("clock out"))
                    + f" · **{_dia(r)}** · {_tipo_txt(r)}"
                    + (f" · {r.get('Project')}" if str(r.get("Project", "")).strip()
                       else ""))
        # ⚠️ Las DOS horas juntas: sin la anterior, el admin no puede juzgar nada.
        c1.markdown(t("Was **{a}** → now **{b}**  ·  {d}",
                      a=_hhmm(r.get("OldValue")) if str(r.get("OldValue", "")).strip()
                      else t("(open)"),
                      b=_hhmm(r.get("NewValue")), d=_dif_horas(r)))
        if str(r.get("Reason", "")).strip():
            c1.caption(f"«{r.get('Reason')}»")
        c2.caption(t("Asked on {x}", x=_fdmh(r.get("Created"))))

        # ⚠️ El aviso que pidió el usuario: si ese día ya se pagó, se dice CUÁL nómina,
        # para que se pueda ir a mirar en vez de un «ojo» que no lleva a ningún sitio.
        _nom_id = str(r.get("PayslipCovers", "")).strip()
        if _nom_id:
            st.warning(t(":material/warning: That day was already paid in **{x}** — "
                         "check whether it needs regularising.", x=_nom_id))

        # ⚠️ v556 · Otra corrección POSTERIOR volvió a cambiar este fichaje: aquí ni se
        # puede revertir (la hora que dejó ya no está) ni aprobar sin mentir. La hora
        # buena se revisa en la tarjeta de la posterior.
        if por:
            st.info(t(":material/info: Superseded by **{x}**: the same entry was changed "
                      "again later. Its time is reviewed there.", x=por))
            if st.button(t(":material/done_all: Close as superseded"),
                         key=f"cor_sus_{_id}", width="stretch"):
                _apuntar(_id, "sustituida", por=por)
            return

        _nota = st.text_input(t("Note (optional)"), key=f"cor_nota_{_id}")
        b1, b2 = st.columns(2)
        if b1.button(t(":material/check_circle: Approve"), key=f"cor_ok_{_id}",
                     width="stretch", type="primary"):
            _apuntar(_id, "aprobar", nota=_nota)
        # ⚠️ Un cierre de sesión OLVIDADA no tiene «hora anterior»: estaba abierta.
        # Revertirlo la devolvería a abierta, o sea a acumular horas contra el
        # reloj — 34 h al día siguiente, 130 a los cinco. Ahí no se revierte.
        if (str(r.get("OldValue", "")).strip()
                and b2.button(t(":material/undo: Revert to the original time"),
                              key=f"cor_no_{_id}", width="stretch")):
            _apuntar(_id, "revertir", nota=_nota)
        # ⚠️ v556 · «Set the right time» en TODAS: si revertir choca con otra jornada
        # (la regla anti-solapes de v546), el admin no tenía otra salida que aprobar.
        h1, h2 = st.columns(2, vertical_alignment="bottom")   # el botón, a la altura del campo
        _h = h1.time_input(t("Set the right time"), value=_hora_de(r.get("NewValue")),
                           key=f"cor_fix_{_id}")
        if h2.button(t(":material/save: Apply this time"), key=f"cor_fixb_{_id}",
                     width="stretch"):
            _apuntar(_id, "ajustar", nota=_nota, hora=_h.strftime("%H:%M"))


def _de_grupo(grupo, cid) -> dict:
    """La corrección `cid` SOLO si es de este grupo (v556; `C.get` busca en todas)."""
    return next((r for r in C.list_group(grupo) if str(r.get("ID", "")) == str(cid)), {})


def _accion_pendiente(grupo, quien, etq):
    """⚠️ v556 · ACCIÓN DIFERIDA (trampa 37, vista en Absences en v555): aprobar,
    revertir y fijar la hora escriben en la hoja. Hechas DENTRO de la tarjeta, con un
    `st.rerun()` al final, Streamlit 1.64 puede dejar la tarjeta resuelta en pantalla
    cuando la que ocupa su sitio tiene otra forma (el aviso de nómina, el motivo, una
    sustituida…). Aquí se ejecuta ANTES de pintar la lista."""
    acc = st.session_state.pop("_cor_accion", None)
    if acc:
        _ejecutar(acc, grupo, quien, etq)
        st.rerun()


def _ejecutar(acc, grupo, quien, etq):
    r = _de_grupo(grupo, str(acc.get("cid", "")))
    if not r:
        flash.error(t("Correction not found."))
        return
    _quien = f"{etq.get(str(r.get('User', ''))) or r.get('Name') or r.get('User')} · {_dia(r)}"
    ok, msg = hacer(acc, grupo, quien)
    if msg:
        (flash.exito if ok else flash.error)(f"{_quien}: {msg}")


def no_se_puede(r, accion, todas=None) -> str:
    """Por qué esa acción no vale para esa corrección, o "" (v644). La tarjeta ni ofrece esos botones;
    se mira también aquí porque el Management assistant pide por ID, sin la tarjeta delante."""
    if accion in ("aprobar", "revertir"):
        _por = C.sustituida_por(r, todas)
        if _por:
            return t("Superseded by {x}: the same entry was changed again later. Its time is reviewed there.", x=_por)
    # ⚠️ Revertir el cierre de una sesión olvidada la REABRE: 34 h al día siguiente (ver `_tarjeta`)
    if accion == "revertir" and not str(r.get("OldValue", "")).strip():
        return t("It closed an entry that was left open: there is no earlier time to go back to.")
    return ""


def hacer(acc, grupo, quien) -> tuple:
    """La acción sobre una corrección, con el aviso a la persona cuando su hora cambia: `(ok, mensaje)`.
    v644 · Aparte para que el Management assistant haga lo mismo que esta bandeja. ⚠️ Solo una de
    ESTE grupo; un mensaje vacío es que no había nada que hacer."""
    cid = str(acc.get("cid", ""))
    r = _de_grupo(grupo, cid)
    if not r:
        return False, t("Correction not found.")
    nota = str(acc.get("nota") or "")
    accion = acc.get("accion")
    _no = no_se_puede(r, accion)
    if _no:
        return False, _no
    if accion == "aprobar":
        return C.aprobar(cid, quien, nota)
    if accion == "revertir":
        ok, msg = C.revertir(cid, quien, nota)
        if ok:
            _avisar_persona(r, "revertir", nota)
        return ok, msg
    if accion == "ajustar":
        try:
            _h = datetime.strptime(str(acc.get("hora")), "%H:%M").time()
        except (TypeError, ValueError):
            return False, t("That time could not be read.")
        ok, msg = C.ajustar(cid, quien, _h, nota)
        if ok:
            _avisar_persona(r, "ajustar", nota, _h.strftime("%H:%M"))
        return ok, msg
    if accion == "sustituida":
        return C.cerrar_sustituida(cid, quien, str(acc.get("por", "")))
    return False, ""


def _avisar_persona(r, accion, nota="", hora=""):
    """v556 · La persona se entera cuando su hora CAMBIA (revertir o fijar otra): sus
    horas pagadas cambian. Antes no había ni un aviso en este flujo. Aprobar no avisa:
    no cambia nada. Best-effort: el cambio ya está guardado cuando se llega aquí.
    ⚠️ En inglés y SIN `t()`: es un mensaje para la persona, no la pantalla del admin."""
    try:
        from core import notify
        _campo = "clock in" if str(r.get("Field", "")) == C.CAMPO_IN else "clock out"
        from core.projects_ui import _fmt_fecha
        _d = _fmt_fecha(str(r.get("NewValue") or r.get("OldValue") or "")[:10])
        if accion == "revertir":
            _subj = f"Time correction reverted: {_d}"
            _l = [f"The administrator <b>reverted</b> your {_campo} correction for "
                  f"<b>{_d}</b>: it is back to <b>{_hhmm(r.get('OldValue'))}</b>."]
        else:
            _subj = f"Time correction adjusted: {_d}"
            _l = [f"The administrator set your {_campo} for <b>{_d}</b> to <b>{hora}</b>."]
        if str(nota or "").strip():
            _l.append(f"Note: {nota}")
        notify.notify_user(str(r.get("User", "")), _subj, _l)
    except Exception as e:
        logger.warning("correcciones_ui._avisar_persona: %s", e)


def _kpis(pend, hechas, etq):
    """Tarjetas ACTIVAS (v556; eran HTML): cada una abre su lista debajo."""
    _ver = st.session_state.get("_cor_kpi", "")
    _ok = [r for r in hechas if str(r.get("Status")) == C.APROBADA]
    _rev = [r for r in hechas if str(r.get("Status")) == C.REVERTIDA]
    _kp = [("pend", ":material/pending_actions:", t("To review"), pend, t("time fixes"),
            theme.AMBAR if pend else theme.AZUL),
           ("ok", ":material/check_circle:", t("Approved"), _ok, t("so far"), theme.AZUL),
           ("rev", ":material/undo:", t("Reverted"), _rev, t("so far"), theme.AZUL)]
    # El borde, en el color vivo; la CIFRA es texto (v328): el ámbar, el legible.
    _txt = {theme.AMBAR: theme.AMBAR_TXT}
    st.markdown("<style>" + "".join(
        f".st-key-cpxkpi_cor_{k} button{{border-left-color:{c}!important;}}"
        f".st-key-cpxkpi_cor_{k} button p:nth-child(2){{color:{_txt.get(c, c)}!important;}}"
        for k, _i, _l, _r, _p, c in _kp) + "</style>", unsafe_allow_html=True)
    for _col, (k, ico, lbl, filas, pie, _c) in zip(st.columns(len(_kp)), _kp):
        if _col.button(f"{ico} {lbl}\n\n{len(filas)}\n\n{pie}", key=f"cpxkpi_cor_{k}",
                       width="stretch"):
            st.session_state["_cor_kpi"] = "" if _ver == k else k
            st.rerun()
    if _ver:
        _filas = {k: f for k, _i, _l, f, _p, _c in _kp}.get(_ver, [])
        with st.container(border=True):
            if not _filas:
                st.caption(t("Nothing."))
            for r in _filas:
                _usr = str(r.get("User", ""))
                st.markdown(f"**{etq.get(_usr) or r.get('Name') or _usr}** · "
                            + (t("clock in") if str(r.get("Field")) == C.CAMPO_IN
                               else t("clock out"))
                            + f" · {_dia(r)} · {_hhmm(r.get('OldValue'))} → "
                              f"{_hhmm(r.get('NewValue'))}")


def render_bandeja(grupo: str):
    if not C.is_configured():
        st.warning(t(":material/warning: The timeclock is not connected yet."))
        return
    quien = str(st.session_state.get("auth", {}).get("usuario", ""))

    _etq_us = _etq(grupo)
    _accion_pendiente(grupo, quien, _etq_us)          # v556 · ANTES de pintar nada
    todas = C.list_group(grupo)
    # v556 · lo más ANTIGUO primero: con correcciones encadenadas sobre el mismo fichaje
    # (COR-0001 y luego COR-0002) se leían al revés
    pend = sorted([r for r in todas if str(r.get("Status", "")).strip().lower() == C.PENDIENTE],
                  key=lambda r: str(r.get("Created", "")))
    hechas = [r for r in todas
              if str(r.get("Status", "")).strip().lower() != C.PENDIENTE]
    _kpis(pend, hechas, _etq_us)

    if not pend:
        # ⚠️ Nada que revisar NO es una pantalla vacía: se dice, y se explica qué
        # significa (patrón v325: un estado sin explicación parece un fallo).
        st.success(t(":material/check_circle: Nothing to review. Corrections apply "
                     "straight away and show up here for you to confirm or undo."))
    else:
        st.caption(t("The time is **already applied**. Approve it, or put back the "
                     "original one."))
        for r in pend:
            _tarjeta(grupo, r, quien, _etq_us, por=C.sustituida_por(r, todas))

    if hechas:
        with st.expander(t("History"), icon=":material/history:"):
            _f = pd.DataFrame([{
                "Persona": (_etq_us.get(str(r.get("User", "")))
                            or str(r.get("Name") or r.get("User") or "")),
                "Día": _dia(r),                                     # v556
                "Campo": str(r.get("Field", "")),
                "Antes": _hhmm(r.get("OldValue")),
                "Ahora": _hhmm(r.get("NewValue")),
                # ⚠️ El VALOR se muestra traducido, la hoja guarda el español
                # (v442): `etiqueta()` cambia lo que se ve, nunca el dato.
                "Estado": i18n.etiqueta(str(r.get("Status", ""))),
                # v556 · el NOMBRE, no el login («Admin2» donde la app dice «Bobo»)
                "Revisor": (_etq_us.get(str(r.get("ReviewedBy", "")))
                            or str(r.get("ReviewedBy", ""))),
                "Fecha": _fdmh(r.get("ReviewedDate")),
            } for r in hechas])
            from core import tabla
            st.dataframe(_f, hide_index=True, width="stretch",
                         column_config=tabla.cfg(_f))
