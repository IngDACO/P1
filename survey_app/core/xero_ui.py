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


def _flash_cobros(res: dict):
    """Lo que trajo Xero, contado por separado (v495).

    ⚠️ Cada caso se dice: un «se actualizaron 2» que calle que otras tres siguen en
    borrador —y que por eso nunca traerán un cobro— deja la pantalla tranquila y el
    «por cobrar» mal (v325).
    """
    from core import theme as T          # ⚠️ local: en este módulo theme se importa así
    for _fid, numero, antes, ahora in res["actualizadas"]:
        flash.exito(t("Invoice {n}: collected {a} in Xero (it was {b} here).",
                      n=numero or "—", a=T.dinero(ahora), b=T.dinero(antes)))
    if res["iguales"]:
        flash.info(t("{n} invoice(s) already matched Xero.", n=len(res["iguales"])))
    if res["en_borrador"]:
        flash.aviso(t("Still a draft in Xero, so no payment can arrive: {l}. Your accountant "
                      "approves them in Xero.",
                      l=", ".join(_md(x[1] or x[0]) for x in res["en_borrador"])))
    for _fid, numero, credito in res["con_credito"]:
        flash.aviso(t("Invoice {n} has {c} of credit notes or prepayments applied in Xero. "
                      "That is not money received, so it is not counted as collected here.",
                      n=numero or "—", c=T.dinero(credito)))
    for _fid, numero, est in res["muertas"]:
        flash.aviso(t("Invoice {n} is {e} in Xero: nothing was changed here.",
                      n=numero or "—", e=est.lower()))
    if res["no_encontradas"]:
        flash.aviso(t("Not found in Xero (deleted there?): {l}",
                      l=", ".join(_md(x[1] or x[0]) for x in res["no_encontradas"])))
    for e in res["errores"]:
        flash.error(_md(str(e)))
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
        ok, msg = contable.guardar_claves(
            grupo, {"xero_estado": st.session_state.get("cpxseg_xero_estado", actual)})
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

    # ── v495 · dirección Xero → COPEX: el cobro lo registra el contable allí ──
    # ⚠️ Con un BOTÓN (decisión del usuario): leerlo al abrir la pantalla gastaría
    # llamadas a Xero en cada visita, y así se ve en cada pasada qué se movió.
    st.markdown(t("**Payments**"))
    st.caption(t("Your accountant reconciles the bank in Xero; this brings what is "
                 "collected there into COPEX, so «to collect» here is not left stale."))
    if st.button(t(":material/download: Bring payments from Xero"), key="xero_traer_cobros"):
        with st.spinner(t("Reading Xero…")):
            res = X.traer_cobros(grupo)
        if not any(res[k] for k in res):
            flash.info(t("No invoice of this company has been sent to Xero yet."))
        _flash_cobros(res)
        st.rerun()

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


# ─────────────────────────────────────────────────────────────────────────────
# Parte de horas y permisos → Xero Payroll AU (v490)
# ─────────────────────────────────────────────────────────────────────────────
def _datos_nomina(grupo, forzar=False) -> dict:
    """Empleados, calendarios y tipos de permiso de Xero, guardados en la SESIÓN.

    ⚠️ En la sesión y no en `st.cache_data`: son datos personales de los empleados de
    una empresa, y esa caché se comparte por proceso entre todas. Leerlos cuesta 3
    llamadas a Xero, así que se piden una vez y hay un botón para refrescar.
    """
    from core import xero_nomina as XN
    clave = f"_xero_nomina_{grupo}"
    if forzar or clave not in st.session_state:
        with st.spinner(t("Reading employees and pay calendars from Xero…")):
            st.session_state[clave] = XN.datos(grupo)
    return st.session_state[clave]


def _flash_nomina(res: dict):
    n_c, n_a, n_p = (len(res["partes_creados"]), len(res["partes_actualizados"]),
                     len(res["permisos_creados"]))
    if n_c or n_a or n_p:
        flash.exito(t("Xero Payroll: {c} timesheet(s) created, {a} updated, {p} leave "
                      "application(s) created.", c=n_c, a=n_a, p=n_p))
    for nombre, motivo in res["omitidos"]:
        flash.info(t("{n}: {m}", n=nombre, m=motivo))
    for nombre, msgs in res["errores"]:
        flash.error(t("{n}: {m}", n=nombre, m=" · ".join(msgs)))
    for a in res["avisos"]:
        flash.aviso(a)


def render_partes_xero(grupo):
    """Mandar el parte y las ausencias pagadas del periodo a Xero Payroll."""
    import pandas as pd
    from core import auth, contable, tabla, ui_common as ui
    from core import xero_nomina as XN

    st.markdown(t("#### :material/cloud_upload: Send to Xero Payroll"))
    if not X.configuracion()["ok"] or not X.estado(grupo)["conectada"]:
        st.caption(t("Connect Xero at the top of this screen to send timesheets and paid "
                     "leave to Xero Payroll."))
        return
    tenant_id = X.estado(grupo)["tenant_id"]
    d = _datos_nomina(grupo)
    if st.button(t(":material/refresh: Read again from Xero"), key="xn_releer"):
        _datos_nomina(grupo, forzar=True)
        st.rerun()
    if d.get("error"):
        st.warning(d["error"])
        return
    if not d["empleados"]:
        st.info(t("This Xero organisation has no active employees in Payroll."))
        return

    # ── quién es quién ──
    # ⚠️ Los valores de «activo» son los de `auth`, no una copia: dos listas de lo mismo
    # divergen (v323).
    usuarios = [u for u in auth.list_users(grupo)
                if str(u.get("Active", "")).strip().upper() in auth._ACTIVE_OK]
    etq_u = auth.etiqueta_usuarios(usuarios)
    guardado = XN.emparejado(grupo, tenant_id)
    propuesto = XN.propuesta(usuarios, d["empleados"])
    etq_e = {"": t("— not in Xero —")}
    etq_e.update({e["EmployeeID"]: f"{XN.nombre_empleado(e)} · {e.get('Email') or '—'}"
                  for e in d["empleados"]})
    base = [""] + [e["EmployeeID"] for e in d["empleados"]]
    sin_confirmar = [u for u in usuarios if str(u.get("User", "")) not in guardado]
    with st.expander(t("Who is who in Xero ({n} to confirm)", n=len(sin_confirmar)),
                     icon=":material/group:", expanded=bool(sin_confirmar)):
        st.caption(t("Proposed by email, then by name. Check them and save once; people "
                     "not in Xero Payroll stay «not in Xero»."))
        elegidos = {}
        for u in usuarios:
            login = str(u.get("User", ""))
            actual = guardado.get(login, propuesto.get(login, ""))
            # ⚠️ v487: el valor guardado se ANTEPONE si ya no está en la lista (un
            # empleado dado de baja en Xero), en vez de mostrar otro y pisarlo al guardar.
            opciones, idx = ui.opciones_con_actual(base, actual)
            elegidos[login] = st.selectbox(
                etq_u.get(login, login), opciones, index=idx,
                format_func=lambda o: etq_e.get(o, t("(no longer active in Xero)")),
                key=f"xn_emp_{login}")
        repetidos = {v for v in elegidos.values() if v and list(elegidos.values()).count(v) > 1}
        if repetidos:
            st.warning(t("Two people point to the same Xero employee: fix it before saving."))
        if st.button(t(":material/save: Save matches"), key="xn_guardar",
                     disabled=bool(repetidos)):
            ok, msg = XN.guardar_emparejado(grupo, tenant_id, elegidos)
            (flash.exito if ok else flash.error)(t("Matches saved.") if ok else msg)
            st.rerun()

    # ── periodo del calendario de Xero ──
    claves, etiquetas = [], {}
    for cal in d["calendarios"]:
        for p in XN.periodos(cal):
            k = f"{cal.get('PayrollCalendarID')}|{p['inicio'].isoformat()}|{p['fin'].isoformat()}"
            claves.append(k)
            etiquetas[k] = t("{c} · {a} – {b}{x}", c=cal.get("Name", ""),
                             a=p["inicio"].strftime("%a %d %b"),
                             b=p["fin"].strftime("%a %d %b %Y"),
                             x=t(" (next pay run)") if p["proximo"] else "")
    if not claves:
        st.warning(t("None of the pay calendars in Xero has a period type COPEX can "
                     "calculate."))
        return
    sel = st.selectbox(t("Pay period in Xero"), claves, format_func=lambda k: etiquetas[k],
                       key="xn_periodo",
                       help=t("Xero only accepts a timesheet whose dates are exactly a pay "
                              "period of the employee's pay calendar."))
    cal_id, ini, fin = sel.split("|")

    # ── lo que se va a mandar ──
    pareja = XN.emparejado(grupo, tenant_id)
    emp_por_id = {e["EmployeeID"]: e for e in d["empleados"]}
    partes = contable.partes(grupo, ini, fin)
    nombres = contable.mapa(grupo).get("conceptos", {})
    filas, listas = {}, 0
    for f in partes.get("filas") or []:
        r = filas.setdefault(f["usuario"], {"nombre": f["nombre"], "ord": 0.0, "perm": []})
        if f["concepto"] == contable.ORDINARIAS:
            r["ord"] += f["total"]
        else:
            r["perm"].append(f"{nombres.get(f['concepto'], f['concepto'])} {f['total']:g} h")
    tabla_filas = []
    for login, r in sorted(filas.items(), key=lambda kv: kv[1]["nombre"].casefold()):
        eid = pareja.get(login)
        emp = emp_por_id.get(eid) if eid else None
        if not eid:
            estado = t("not matched — confirm above")
        elif emp is None:
            estado = t("matched employee not active in Xero")
        elif emp.get("PayrollCalendarID") != cal_id:
            estado = t("on another pay calendar")
        else:
            estado = t("will be sent")
            listas += 1
        tabla_filas.append({
            "Persona": etq_u.get(login, r["nombre"]),
            "Empleado": XN.nombre_empleado(emp) if emp else "—",
            "Horas": tabla.celda(r["ord"], 2),
            "Permisos": " · ".join(r["perm"]),
            "Estado": estado})
    if not tabla_filas:
        st.caption(t("Nobody has paid hours in this pay period."))
        return
    st.dataframe(pd.DataFrame(tabla_filas), hide_index=True, width="stretch",
                 column_config=tabla.cfg(None, {
                     "Persona": st.column_config.Column(t("Person")),
                     "Empleado": st.column_config.Column(t("Xero employee")),
                     "Horas": tabla.derecha(t("Ordinary hours")),
                     "Permisos": st.column_config.Column(t("Paid leave")),
                     "Estado": st.column_config.Column(t("Status"))}))
    st.caption(t("Timesheets arrive in Xero as drafts. A timesheet already approved in Xero "
                 "is not changed, and leave already in Xero is not sent twice."))
    if st.button(t(":material/send: Send {n} person(s) to Xero Payroll", n=listas),
                 type="primary", key="xn_enviar", disabled=not listas):
        with st.spinner(t("Sending to Xero Payroll…")):
            res = XN.enviar(grupo, cal_id, ini, fin)
        _flash_nomina(res)
        st.rerun()

