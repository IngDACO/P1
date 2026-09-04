"""Bandeja del administrador: las correcciones de fichaje que pidió el equipo (v461).

⚠️ La hora ya está aplicada cuando esta pantalla la muestra (decisión del usuario): lo
que se decide aquí es si se CONFIRMA o se REVIERTE, no si se aplica. Por eso la
tarjeta enseña las dos horas —la que había y la que hay— y no un «pendiente de
aplicar» que sería mentira.
"""
import logging

import pandas as pd
import streamlit as st

from core import auth, clock, correcciones as C, flash, theme, timeclock
from core.i18n import t

logger = logging.getLogger(__name__)


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
    from datetime import datetime
    try:
        return datetime.strptime(str(v), timeclock.FMT).time().replace(
            second=0, microsecond=0)
    except Exception:
        return clock.now().time().replace(second=0, microsecond=0)


def _dif_horas(r) -> str:
    """Cuánto cambió, en horas. Es el dato que decide: media hora es un olvido, seis
    es otra cosa."""
    from datetime import datetime
    try:
        a = datetime.strptime(str(r.get("ValorAnterior")), timeclock.FMT)
        b = datetime.strptime(str(r.get("ValorNuevo")), timeclock.FMT)
        d = (b - a).total_seconds() / 3600.0
        return f"{d:+.2f} h"
    except Exception:
        return "—"


def _tarjeta(grupo, r, quien, etq):
    _id = str(r.get("ID", ""))
    _campo = str(r.get("Campo", ""))
    _es_in = _campo == C.CAMPO_IN
    with st.container(border=True, key=f"cor_{_id}"):
        c1, c2 = st.columns([3, 2])
        # ⚠️ Dos personas pueden llamarse igual: en la pantalla donde se decide
        # sobre las horas de alguien, dos tarjetas idénticas son inservibles.
        _usr = str(r.get("Usuario", ""))
        _nom = etq.get(_usr) or str(r.get("Nombre") or _usr or "—")
        c1.markdown(f"**{_nom}** · "
                    + (t("clock in") if _es_in else t("clock out"))
                    + f" · `{r.get('Tipo', '')}`"
                    + (f" · {r.get('Proyecto')}" if str(r.get("Proyecto", "")).strip()
                       else ""))
        # ⚠️ Las DOS horas juntas: sin la anterior, el admin no puede juzgar nada.
        c1.markdown(t("Was **{a}** → now **{b}**  ·  {d}",
                      a=_hhmm(r.get("ValorAnterior")) if str(r.get("ValorAnterior", "")).strip()
                      else t("(open)"),
                      b=_hhmm(r.get("ValorNuevo")), d=_dif_horas(r)))
        if str(r.get("Motivo", "")).strip():
            c1.caption(f"«{r.get('Motivo')}»")
        c2.caption(t("Asked on {x}", x=str(r.get("Creado", ""))[:16]))

        # ⚠️ El aviso que pidió el usuario: si ese día ya se pagó, se dice CUÁL nómina,
        # para que se pueda ir a mirar en vez de un «ojo» que no lleva a ningún sitio.
        _nom_id = str(r.get("NominaCubre", "")).strip()
        if _nom_id:
            st.warning(t(":material/warning: That day was already paid in **{x}** — "
                         "check whether it needs regularising.", x=_nom_id))

        _nota = st.text_input(t("Note (optional)"), key=f"cor_nota_{_id}")
        b1, b2 = st.columns(2)
        if b1.button(t(":material/check_circle: Approve"), key=f"cor_ok_{_id}",
                     width="stretch", type="primary"):
            ok, msg = C.aprobar(_id, quien, _nota)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()
        # ⚠️ Un cierre de sesión OLVIDADA no tiene «hora anterior»: estaba abierta.
        # Revertirlo la devolvería a abierta, o sea a acumular horas contra el
        # reloj — 34 h al día siguiente, 130 a los cinco. Así que ahí no se
        # revierte: se AJUSTA, que es lo que el admin necesita de verdad.
        _sin_previo = not str(r.get("ValorAnterior", "")).strip()
        if _sin_previo:
            _h = b2.time_input(t("Set the right time"),
                               value=_hora_de(r.get("ValorNuevo")),
                               key=f"cor_fix_{_id}")
            if b2.button(t(":material/save: Apply this time"),
                         key=f"cor_fixb_{_id}", width="stretch"):
                ok, msg = C.ajustar(_id, quien, _h, _nota)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        elif b2.button(t(":material/undo: Revert to the original time"),
                       key=f"cor_no_{_id}", width="stretch"):
            ok, msg = C.revertir(_id, quien, _nota)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()


def render_bandeja(grupo: str):
    if not C.is_configured():
        st.warning(t(":material/warning: The timeclock is not connected yet."))
        return
    quien = str(st.session_state.get("auth", {}).get("usuario", ""))

    _etq_us = _etq(grupo)
    pend = C.pendientes(grupo)
    hechas = [r for r in C.list_group(grupo)
              if str(r.get("Estado", "")).strip().lower() != C.PENDIENTE]

    _n_aprob = sum(1 for r in hechas if str(r.get("Estado")) == C.APROBADA)
    _n_rev = sum(1 for r in hechas if str(r.get("Estado")) == C.REVERTIDA)
    theme.kpi_row([
        (t("To review"), str(len(pend)), t("time fixes"),
         # ⚠️ El 4º elemento es el ACENTO (borde), no texto: `theme.AMBAR` va bien
         # aquí y sería ilegible como color de letra (v329). Y nunca None: acabaría
         # como «--cpx-accent:None» en el CSS.
         theme.AMBAR if pend else theme.AZUL),
        (t("Approved"), str(_n_aprob), t("so far")),
        (t("Reverted"), str(_n_rev), t("so far")),
    ])

    if not pend:
        # ⚠️ Nada que revisar NO es una pantalla vacía: se dice, y se explica qué
        # significa (patrón v325: un estado sin explicación parece un fallo).
        st.success(t(":material/check_circle: Nothing to review. Corrections apply "
                     "straight away and show up here for you to confirm or undo."))
    else:
        st.caption(t("The time is **already applied**. Approve it, or put back the "
                     "original one."))
        for r in pend:
            _tarjeta(grupo, r, quien, _etq_us)

    if hechas:
        with st.expander(t("History"), icon=":material/history:"):
            _f = pd.DataFrame([{
                "Persona": (_etq_us.get(str(r.get("Usuario", "")))
                            or str(r.get("Nombre") or r.get("Usuario") or "")),
                "Campo": str(r.get("Campo", "")),
                "Antes": _hhmm(r.get("ValorAnterior")),
                "Ahora": _hhmm(r.get("ValorNuevo")),
                "Estado": str(r.get("Estado", "")),
                "Revisor": str(r.get("RevisadoPor", "")),
                "Fecha": str(r.get("RevisadoFecha", ""))[:16],
            } for r in hechas])
            from core import tabla
            st.dataframe(_f, hide_index=True, width="stretch",
                         column_config=tabla.cfg(_f))
