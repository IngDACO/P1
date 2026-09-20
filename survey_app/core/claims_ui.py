# -*- coding: utf-8 -*-
"""Cobro de obra: variaciones y reclamaciones en el detalle de la obra (v507).

Contesta una sola pregunta, y por eso va todo en una sección: **«¿cuánto puedo reclamar
este mes?»**. Arriba el valor de contrato y lo que lo mueve; debajo lo que se puede
reclamar hoy; al final lo ya emitido.
"""
import streamlit as st

from core import claims as CL
from core import flash
from core.i18n import t
from core.num import num as _num


def _dinero(v) -> str:
    return "%s%s" % ("-$" if _num(v) < 0 else "$", format(abs(_num(v)), ",.2f"))


def render(pid, grupo, prj, editable=True, key_prefix="clm"):
    if not CL.is_configured():
        return
    try:
        d = CL.calcular(pid, grupo, None, prj)
        vars_ = CL.variaciones(pid)
        recs = CL.reclamaciones(pid)
    except Exception as e:                      # nunca tumba el detalle de la obra
        st.caption(t("Progress claims are unavailable right now ({e}).", e=e))
        return

    _pend = [r for r in recs if str(r.get("Status", "")) == CL.EMITIDA]
    _tit = t("Progress claims ({n} issued · {m} claimable now)",
             n=len(_pend), m=_dinero(d["neto"]))
    with st.expander(f":material/request_quote: {_tit}", expanded=False):

        # ⚠️ Sin cotización aceptada no hay contra qué reclamar, y se dice ANTES de
        # enseñar ninguna cifra: un «valor» compuesto solo de variaciones induce a creer
        # que hay algo que cobrar cuando no hay contrato debajo.
        if not d["hay_contrato"]:
            st.warning(t(":material/info: This job has no accepted quote, so there is no "
                         "contract value. Accept a quote for it and the claims will "
                         "become available."))
            return

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("Contract"), _dinero(d["contrato"]))
        c2.metric(t("Approved variations"), _dinero(d["variaciones"]))
        c3.metric(t("Contract value"), _dinero(d["valor"]))
        c4.metric(t("Retention held"), _dinero(d["retenido_acumulado"]))

        # ── Lo que se puede reclamar hoy ──
        st.markdown(t("**:material/calculate: What can be claimed now**"))
        st.markdown(
            t("Progress **{p}%** → work done {h} · already claimed {a} · "
              "**this claim {b}** − retention {r} ({rp}%) = **net {n}**",
              p=("%.1f" % d["pct"]), h=_dinero(d["hecho"]), a=_dinero(d["antes"]),
              b=_dinero(d["bruto"]), r=_dinero(d["retencion"]),
              rp=("%.1f" % d["retencion_pct"]), n=_dinero(d["neto"])))

        if editable:
            with st.form(f"{key_prefix}_new_{pid}"):
                k1, k2 = st.columns(2)
                _pct = k1.number_input(t("Progress to claim (%)"), min_value=0.0,
                                       max_value=100.0, value=float(d["pct"]), step=1.0,
                                       help=t("Defaults to the job's real progress. Lower "
                                              "it to claim less than what is done."))
                _hasta = k2.date_input(t("Period to"), value=None)
                _nota = st.text_input(t("Note"), placeholder=t("Optional"))
                if st.form_submit_button(t(":material/send: Issue claim"), width="stretch"):
                    ok, msg = CL.crear_reclamacion(
                        pid, grupo, _pct, _hasta.strftime("%Y-%m-%d") if _hasta else "",
                        _nota, st.session_state.get("auth", {}).get("usuario", ""), prj)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        # ── Lo ya emitido ──
        if recs:
            st.markdown(t("**:material/receipt_long: Claims issued**"))
            for r in recs:
                _est = str(r.get("Status", ""))
                _ic = (":green[:material/paid:]" if _est == CL.PAGADA
                       else ":blue[:material/schedule:]")
                _neto = _num(r.get("ThisClaim")) - _num(r.get("Retention"))
                st.markdown("%s **#%s** %s · %s%% · %s %s — %s %s"
                            % (_ic, r.get("Number", "?"), r.get("Date", ""),
                               r.get("PctComplete", "0"), t("net"), _dinero(_neto),
                               t("retention"), _dinero(r.get("Retention"))))
                if editable and _est == CL.EMITIDA:
                    b1, b2 = st.columns(2)
                    if b1.button(t("Mark paid"), key=f"{key_prefix}_pay_{r.get('ID')}"):
                        ok, msg = CL.marcar_pagada(r.get("ID"))
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()
                    if b2.button(t("Cancel"), key=f"{key_prefix}_void_{r.get('ID')}"):
                        ok, msg = CL.anular(r.get("ID"))
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()

        # ── Variaciones ──
        st.markdown(t("**:material/edit_note: Variations**"))
        st.caption(t("Only approved variations change the contract value. A proposed one "
                     "is not money yet."))
        for v in vars_:
            _e = str(v.get("Status", ""))
            _ic = {CL.APROBADA: ":green[:material/check_circle:]",
                   CL.RECHAZADA: ":red[:material/cancel:]"}.get(_e, ":orange[:material/pending:]")
            st.markdown("%s **#%s** %s — %s  \n&nbsp;&nbsp;&nbsp;:gray[%s]"
                        % (_ic, v.get("Number", "?"), _dinero(v.get("Amount")),
                           v.get("Description", ""), _e),
                        unsafe_allow_html=True)
            if editable and _e == CL.PROPUESTA:
                a1, a2 = st.columns(2)
                _quien = st.session_state.get("auth", {}).get("usuario", "")
                if a1.button(t("Approve"), key=f"{key_prefix}_ok_{v.get('ID')}"):
                    ok, msg = CL.decidir_variacion(v.get("ID"), True, _quien, grupo)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if a2.button(t("Reject"), key=f"{key_prefix}_no_{v.get('ID')}"):
                    ok, msg = CL.decidir_variacion(v.get("ID"), False, _quien, grupo)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        if editable:
            with st.form(f"{key_prefix}_var_{pid}"):
                st.markdown(t("**New variation**"))
                v1, v2 = st.columns([3, 1])
                _desc = v1.text_input(t("Description"),
                                      placeholder=t("e.g. extra landing door"))
                _imp = v2.number_input(t("Amount"), step=100.0,
                                       help=t("Negative for a reduction in scope."))
                if st.form_submit_button(t(":material/add_circle: Record variation"),
                                         width="stretch"):
                    ok, msg = CL.crear_variacion(
                        pid, grupo, _desc, _imp, "",
                        st.session_state.get("auth", {}).get("usuario", ""))
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
