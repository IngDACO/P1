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
    """⚠️ Delega en `theme.dinero`, que ESCAPA el `$` como `\\$` (v309).

    Aquí había un formateador propio y salió caro: Streamlit lee lo que hay entre dos
    `$` de una misma cadena como **LaTeX**, así que «work done $0.00 · already claimed
    $31,500.00» se renderizaba con el texto de en medio metido en un bloque matemático
    y los `**` literales. El docstring de `theme.dinero` describe ese síntoma palabra
    por palabra y avisa de que «cada vez que alguien escriba `f"${x:,.2f}"` a mano el
    fallo vuelve». Volvió. El formato de importes vive en UN sitio.
    """
    from core import theme
    return theme.dinero(_num(v))


def _descarga(pid, grupo, r, vars_, prj, d, key_prefix):
    """El botón que baja el PDF de ESTE documento (v510).

    ⚠️ Se genera en línea, sin caché: medido, son **4,7 ms** por documento (56 ms para
    doce), así que cachearlo solo añadiría una clave que hay que acordarse de meter el
    libro (v378) para que un inquilino no se descargue el papel de otro. Costaba menos
    medirlo que arriesgarlo.
    ⚠️ Envuelto: que el PDF falle no puede tumbar la lista de reclamaciones.
    """
    try:
        from core import claim_pdf
        _cli = {}
        try:
            from core import clientes
            _cid = str((prj or {}).get("ClientID", ""))
            _cli = clientes.get_cliente(_cid) if _cid else {}
        except Exception:
            _cli = {}
        _bytes = claim_pdf.generate_claim_pdf(
            r, vars_, _cli, grupo, prj,
            {"retenido": d["retenido_acumulado"], "liberado": d["retenido_liberado"],
             "pendiente": d["retenido_pendiente"]})
        _es_lib = CL.es_liberacion(r)
        st.download_button(
            t(":material/download: Download PDF"), data=_bytes,
            file_name="%s_%s_%s.pdf" % ("RetentionRelease" if _es_lib else "ProgressClaim",
                                        pid, r.get("Number", "")),
            mime="application/pdf", key=f"{key_prefix}_pdf_{r.get('ID')}")
    except Exception as e:
        st.caption(t(":material/warning: The PDF could not be generated ({e}).", e=e))


def _retencion(pid, grupo, prj, d, key_prefix):
    """Pedir de vuelta la retención cuando la obra está terminada (v510).

    ⚠️ Cuando NO se puede, el bloque sigue apareciendo **con el motivo**. Esconderlo
    haría que una función que existe pareciera no existir, y el usuario preguntaría por
    algo que ya tiene (misma decisión que en v505).
    """
    if d["retenido_acumulado"] <= 0:
        return
    st.markdown(t("**:material/lock_open: Retention**"))
    _puede, _motivo = CL.puede_liberar(pid, prj)
    st.caption("%s · %s" % (t("{x} held", x=_dinero(d["retenido_pendiente"])), _motivo))
    if not _puede:
        return
    with st.form(f"{key_prefix}_ret_{pid}"):
        r1, r2 = st.columns([1, 2])
        _imp = r1.number_input(
            t("Amount to release"), min_value=0.0,
            max_value=float(d["retenido_pendiente"]),
            value=float(d["retenido_pendiente"]), step=100.0,
            help=t("Defaults to everything still held. Release part of it if the "
                   "contract splits it between practical completion and the end of "
                   "the defects period."))
        _nota = r2.text_input(t("Note"), placeholder=t("Optional"),
                              key=f"{key_prefix}_retnote_{pid}")
        if st.form_submit_button(t(":material/lock_open: Release retention"),
                                 width="stretch"):
            ok, msg = CL.crear_liberacion(
                pid, grupo, _imp, _nota,
                st.session_state.get("auth", {}).get("usuario", ""), prj)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()


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
        # ⚠️ v510: lo que se ENSEÑA es lo que sigue retenido, no lo retenido histórico.
        # Con liberaciones de por medio son dos números distintos, y el que le importa a
        # quien mira es cuánto puede pedir de vuelta todavía.
        c4.metric(t("Retention held"), _dinero(d["retenido_pendiente"]),
                  help=(t("{x} released so far.", x=_dinero(d["retenido_liberado"]))
                        if d["retenido_liberado"] else None))

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
                # ⚠️ Una liberación se lee distinta o se confunde con una reclamación de
                # avance del mismo importe: no lleva % ni retención, y el porqué del
                # dinero es otro.
                if CL.es_liberacion(r):
                    st.markdown("%s **#%s** %s · %s — %s"
                                % (":violet[:material/lock_open:]", r.get("Number", "?"),
                                   r.get("Date", ""), t("retention release"),
                                   _dinero(r.get("ThisClaim"))))
                else:
                    st.markdown("%s **#%s** %s · %s%% · %s %s — %s %s"
                                % (_ic, r.get("Number", "?"), r.get("Date", ""),
                                   r.get("PctComplete", "0"), t("net"), _dinero(_neto),
                                   t("retention"), _dinero(r.get("Retention"))))
                _descarga(pid, grupo, r, vars_, prj, d, key_prefix)
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

        # ── Retención: pedirla de vuelta al terminar (v510) ──
        if editable:
            _retencion(pid, grupo, prj, d, key_prefix)

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
