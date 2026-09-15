# -*- coding: utf-8 -*-
"""Pantalla de la conexión con Xero (v488): Finanzas → Contable, y la factura.

Tres estados, y cada uno dice qué hacer:
  · sin configurar  → qué secretos faltan y la dirección EXACTA que hay que registrar
                      en la app de Xero (la compara carácter a carácter);
  · sin conectar     → «Conectar con Xero», que abre Xero en una pestaña nueva;
  · conectada        → a qué organización, cómo llegan las facturas, cuántas faltan
                      por mandar, y desconectar.

⚠️ La vuelta desde Xero llega en una pestaña NUEVA, o sea en una sesión nueva: la
procesa `procesar_retorno`, llamada desde `app.py` después del login.
"""
import streamlit as st

from core import flash, invoices, tenant
from core import xero as X
from core.i18n import t

_ETQ_ESTADO = {X.BORRADOR: "Draft — your accountant approves them in Xero",
               X.APROBADA: "Approved — they go straight to accounts receivable"}


def _md(texto) -> str:
    """Texto ajeno dentro de markdown: sin LaTeX (dos «$», v309) ni negritas coladas."""
    limpio = str(texto or "")
    for c in ("\\", "$", "*", "_"):
        limpio = limpio.replace(c, "\\" + c)
    return limpio or "—"


def _usuario() -> str:
    return str((st.session_state.get("auth") or {}).get("usuario", ""))


def _flash_resultado(res: dict):
    """Lo que pasó al enviar, contado por separado: enviadas, enlazadas y errores."""
    if res["enviadas"]:
        flash.exito(t("{n} invoice(s) sent to Xero.", n=len(res["enviadas"])))
    if res["vinculadas"]:
        flash.info(t("{n} invoice(s) were already in Xero with the same number and were "
                     "linked instead of duplicated.", n=len(res["vinculadas"])))
    for _fid, numero, msgs in res["errores"]:
        flash.error(t("Invoice {n}: {m}", n=numero or "—", m=" · ".join(msgs)))
    for a in res["avisos"]:
        flash.aviso(a)


def procesar_retorno(rol: str, grupo: str) -> None:
    """Termina la conexión cuando Xero devuelve al usuario con `?code=&state=`.

    Solo el ADMINISTRADOR conecta (Finanzas es suya). ⚠️ Se marca como procesado
    ANTES de llamar a Xero: el código es de un solo uso, y un segundo canje por un
    rerun devolvería `invalid_grant` y taparía el éxito del primero.
    """
    if rol != "administrator":
        return
    try:
        qp = st.query_params
        code, state, error = qp.get("code"), qp.get("state"), qp.get("error")
    except Exception:
        return
    if not state or not (code or error):
        return
    if st.session_state.get("_xero_retorno") == state:
        return
    st.session_state["_xero_retorno"] = state
    if error:
        flash.aviso(t("The Xero connection was cancelled ({e}).", e=error))
    elif not X.configuracion()["ok"]:
        flash.error(t("Xero is not configured in this app."))
    else:
        with st.spinner(t("Connecting to Xero…")):
            ok, msg, avisos = X.completar_conexion(grupo, _usuario(), code, state)
        (flash.exito if ok else flash.error)(msg)
        for a in avisos:
            flash.aviso(a)
    try:
        st.query_params.clear()
    except Exception:
        pass
    from core import home_ui
    home_ui.navegar("finanzas", "📤 Contable")


def _pendientes(grupo, desde, hasta) -> dict:
    """{pendientes: [ID], enviables: n} del periodo.

    ⚠️ Dos cuentas y no una: sin `enviables`, un periodo SIN facturas y uno con todas
    ya mandadas daban lo mismo, y la pantalla decía «ya están todas en Xero» a quien no
    tenía ninguna (visto en producción con cliente1 vacío).
    """
    from core import contable
    etq = contable._etiquetas(grupo)
    fichas = contable.fichas_clientes(grupo)
    pend, total = [], 0
    for f in invoices.list_facturas(grupo):
        if not contable._rango(f.get("Date"), desde, hasta):
            continue
        if not contable.documento_venta(f, etq, fichas):
            continue
        total += 1
        if not str(f.get("XeroInvoiceID", "") or "").strip():
            pend.append(str(f.get("ID", "")))
    return {"pendientes": pend, "enviables": total}


def render_conexion(grupo, desde=None, hasta=None):
    """El bloque de Xero dentro de Finanzas → Contable."""
    from core import contable
    from core import theme as T

    T.section(t("Xero connection"), t("Send invoices straight to Xero, without a CSV"))
    conf = X.configuracion()
    if not conf["ok"]:
        st.info(t(":material/key: Xero is not set up in this app yet. Add these secrets in "
                  "Streamlit Cloud → Settings → Secrets: {s}.",
                  s=", ".join(conf["faltan"]) or "—"))
        for p in conf["problemas"]:
            st.warning(p)
        st.caption(t("In the Xero developer app, the redirect URI must be exactly:"))
        st.code(conf["redirect"] or "https://<your-app>.streamlit.app/", language=None)
        return

    est = X.estado(grupo)
    if not est["conectada"]:
        if est["estado"] == X.CADUCADA:
            st.warning(t(":material/link_off: The Xero connection expired (unused for 60 "
                         "days, or revoked in Xero). Connect again."))
        st.link_button(t(":material/link: Connect to Xero"),
                       X.url_autorizacion(grupo, _usuario()), type="primary")
        st.caption(t("Xero opens in a new tab. Approve the organisation there and COPEX "
                     "comes back in that tab already connected; this tab can be closed."))
        return

    # ⚠️ El nombre de la organización lo escribe el cliente en Xero: dos «$» en él
    # harían que Streamlit pintara LaTeX (v309).
    st.markdown(t(":material/check_circle: Connected to **{o}** · since {d} · by {u}",
                  o=_md(est["tenant"]), d=est["desde"] or "—", u=_md(est["por"])))

    cfg = contable.mapa(grupo)
    actual = X.estado_envio(grupo)

    def _guardar_estado():
        nuevo = dict(contable.mapa(grupo))
        nuevo["xero_estado"] = st.session_state.get("cpxseg_xero_estado", actual)
        ok, msg = contable.guardar_mapa(grupo, nuevo)
        (flash.exito if ok else flash.error)(t("Saved.") if ok else msg)

    st.radio(t("Invoices arrive in Xero as"), list(X.ESTADOS_ENVIO),
             index=list(X.ESTADOS_ENVIO).index(actual),
             format_func=lambda o: t(_ETQ_ESTADO[o]), key="cpxseg_xero_estado",
             on_change=_guardar_estado)

    if not str(cfg.get("cuentas", {}).get("xero", {}).get(contable.VENTAS, "")).strip():
        st.warning(t(":material/warning: No Xero sales account is set: fill it in "
                     "«Chart of accounts and tax» below before sending."))

    _p = _pendientes(grupo, desde, hasta)
    pend = _p["pendientes"]
    if pend:
        if st.button(t(":material/send: Send {n} invoice(s) of this period to Xero",
                       n=len(pend)), type="primary", key="xero_enviar_lote"):
            with st.spinner(t("Sending to Xero…")):
                res = X.enviar_facturas(grupo, pend)
            _flash_resultado(res)
            st.rerun()
    elif _p["enviables"]:
        st.caption(t("Every invoice of this period is already in Xero."))
    else:
        st.caption(t("There are no invoices to send in this period."))

    # ⚠️ v489: era un desplegable TITULADO «Disconnect Xero» con una casilla y el botón
    # dentro. El título parecía el botón y solo abría el desplegable: en producción el
    # usuario lo pulsó y «no desconectaba». Ahora es un botón de verdad que PREGUNTA.
    if not st.session_state.get("_xero_confirmar_desconexion"):
        if st.button(t(":material/link_off: Disconnect Xero"), key="xero_desconectar_pedir"):
            st.session_state["_xero_confirmar_desconexion"] = True
            st.rerun()
        return
    st.warning(t("Disconnect «{o}»? COPEX stops sending invoices to it. What is already in "
                 "Xero stays there.", o=_md(est["tenant"])))
    c1, c2 = st.columns(2)
    if c1.button(t("Yes, disconnect"), type="primary", key="xero_desconectar_si"):
        st.session_state.pop("_xero_confirmar_desconexion", None)
        ok, msg = X.desconectar(grupo)
        (flash.exito if ok else flash.error)(msg)
        st.rerun()
    if c2.button(t("Cancel"), key="xero_desconectar_no"):
        st.session_state.pop("_xero_confirmar_desconexion", None)
        st.rerun()


def boton_factura(grupo, f):
    """En el detalle de una factura: dónde está en Xero, o el botón para mandarla."""
    fid = str(f.get("ID", ""))
    xid = str(f.get("XeroInvoiceID", "") or "").strip()
    if xid:
        est = X.estado(grupo)
        st.caption(t(":material/cloud_done: In Xero since {d}", d=f.get("XeroSentAt", "") or "—"))
        st.link_button(t(":material/open_in_new: Open in Xero"),
                       X.url_factura(est.get("short_code", ""), xid))
        return
    if str(f.get("Status", "")).strip().lower() == "anulada":
        return
    if not tenant.puede_ver(f.get("Group", "")) or not X.configuracion()["ok"]:
        return
    if not X.estado(grupo)["conectada"]:
        st.caption(t("Connect Xero in Finance → Accounting to send this invoice there."))
        return
    if st.button(t(":material/send: Send to Xero"), key=f"xero_enviar_{fid}"):
        with st.spinner(t("Sending to Xero…")):
            res = X.enviar_facturas(grupo, [fid])
        _flash_resultado(res)
        st.rerun()

