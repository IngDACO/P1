# -*- coding: utf-8 -*-
"""Pantalla de exportación contable (v483): Finanzas → 📤 Contable.

Genera el CSV que el contable importa. Lo que se enseña ANTES de descargar es lo que
va a fallar al importar —cuentas sin poner, proveedores escritos de dos formas, la
categoría de seguimiento que hay que crear— porque un importador rechaza la fila y no
siempre dice por qué.

⚠️ 0 lecturas nuevas de Sheets: facturas, gastos, clientes y proyectos salen de
lectores ya cacheados, y el mapa contable de la fila de `Groups`, que también lo está.
"""
from datetime import timedelta as _timedelta

import pandas as pd
import streamlit as st

from core import clock, contable, flash, tabla
from core.i18n import etiqueta as _etq
from core.i18n import t


def _periodo(grupo):
    """Selector de periodo, el MISMO idioma que el P&L (v309/v317).

    ⚠️ Las opciones se comparan aquí abajo, así que se traduce el DISPLAY y no la
    opción: traducir el valor dejaría estas cuatro ramas muertas sin dar error (v442).
    """
    hoy = clock.today(grupo)
    _PER = {"Este mes": "This month", "Trimestre": "Quarter",
            "Este año": "This year", "Todo": "All"}
    # v584 · recordado al volver (como el de Quotes y el de Invoices)
    per = st.radio(t("Period"), list(_PER), format_func=lambda o: t(_PER[o]),
                   horizontal=True, key="cpxseg_cont_per", label_visibility="collapsed",
                   persist_state="session")
    if per == "Este mes":
        return hoy.replace(day=1), hoy
    if per == "Trimestre":
        return hoy.replace(day=1, month=((hoy.month - 1) // 3) * 3 + 1), hoy
    if per == "Este año":
        return hoy.replace(day=1, month=1), hoy
    return None, None


def _editor_cuentas(grupo, perfil, cfg):
    """El plan de cuentas del grupo para ESTE perfil.

    ⚠️ Es por perfil a propósito: en Xero las ventas son `200` y en MYOB `4-1000`. Un
    solo mapa habría mandado a MYOB códigos que no existen en su archivo, y MYOB
    rechaza la fila entera sin explicar por qué.
    """
    cuentas = dict(cfg.get("cuentas", {}).get(perfil, {}))
    st.caption(t("These are {p}'s factory chart of accounts, not accounting advice: "
                 "confirm them with the accountant before the first import.",
                 p=contable.PERFILES[perfil]["nombre"]))

    filas = [{"Rubro": t("Sales"), "_k": contable.VENTAS,
              "Cuenta": cuentas.get(contable.VENTAS, "")}]
    for cat in contable.CATEGORIAS:
        filas.append({"Rubro": _etq(cat), "_k": cat, "Cuenta": cuentas.get(cat, "")})

    ed = st.data_editor(
        pd.DataFrame([{"Rubro": f["Rubro"], "Cuenta": f["Cuenta"]} for f in filas]),
        hide_index=True, width="stretch", disabled=["Rubro"],
        key=f"cont_cuentas_{perfil}",
        column_config=tabla.cfg(extra={
            "Rubro":  st.column_config.TextColumn(t("Item"), width="medium"),
            "Cuenta": st.column_config.TextColumn(t("Account code")),
        }))

    c1, c2 = st.columns(2)
    seg = c1.text_input(t("Tracking category / job name"),
                        value=str(cfg.get("categoria_seguimiento", "Project")),
                        key=f"cont_seg_{perfil}",
                        help=t("The project of each line travels in it, so cost and "
                               "revenue land per job in the accounting."))
    dentro = c2.checkbox(t("Receipts already include tax (GST)"),
                         value=bool(cfg.get("gastos_incluyen_impuesto", True)),
                         key=f"cont_dentro_{perfil}",
                         help=t("In Australia a receipt normally includes GST. The export "
                                "always writes the amount WITHOUT tax, whichever this is."))

    if st.button(t(":material/save: Save accounting settings"), key=f"cont_save_{perfil}"):
        # ⚠️ Solo lo de esta pantalla, y de las cuentas solo el perfil que se edita:
        # `guardar_claves` fusiona un nivel, así que las de MYOB sobreviven a guardar las
        # de Xero. Antes se escribía `mapa()` entero y se congelaba lo de fábrica (v492).
        ok, msg = contable.guardar_claves(grupo, {
            "cuentas": {perfil: {filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
                                 for i in range(len(filas))}},
            "categoria_seguimiento": seg.strip() or "Project",
            "gastos_incluyen_impuesto": bool(dentro)})
        if ok:
            flash.exito(t("Accounting settings updated."))
            st.rerun()
        else:
            st.error(msg)


def _editor_conceptos(grupo, cfg):
    """El nombre del «earnings rate» con el que cada concepto entra en la nómina.

    ⚠️ Se edita porque el proveedor casa por NOMBRE y cada organización los tiene a su
    manera: los de fábrica son los de Xero Payroll AU, no una imposición.
    """
    from core import ausencias as AU

    nombres = dict(cfg.get("conceptos", {}))
    filas = []
    for k in contable.conceptos():
        filas.append({
            "Concepto": (t("Ordinary hours") if k == contable.ORDINARIAS
                         else AU.nombre_tipo(k)),
            "_k": k,
            "Cuenta": nombres.get(k, k)})

    ed = st.data_editor(
        pd.DataFrame([{"Concepto": f["Concepto"], "Cuenta": f["Cuenta"]} for f in filas]),
        hide_index=True, width="stretch", disabled=["Concepto"], key="cont_conceptos",
        column_config=tabla.cfg(extra={
            "Concepto": st.column_config.TextColumn(t("Item"), width="medium"),
            "Cuenta":   st.column_config.TextColumn(t("Name in payroll")),
        }))

    if st.button(t(":material/save: Save earnings rates"), key="cont_save_conceptos"):
        ok, msg = contable.guardar_claves(grupo, {"conceptos": {
            filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip() or filas[i]["_k"]
            for i in range(len(filas))}})
        if ok:
            flash.exito(t("Earnings rates updated."))
            st.rerun()
        else:
            st.error(msg)


def _parte_csv(grupo, desde, hasta):
    """El parte de ese periodo: cifras, avisos, la descarga y la tabla (v584: aparte, para
    que unas fechas al revés no se lleven también lo de Xero Payroll)."""
    from core import theme as T

    r = contable.csv_partes(grupo, desde, hasta)

    # v584 · las cifras, ACTIVAS: personas y horas llevan a Hours; las líneas, a la tabla
    _kp = [("pers", t("People"), str(r["personas"]), t("with paid hours")),
           ("horas", t("Paid hours"), f"{r['total']:,.2f}",
            t("1 day in the period") if len(r["dias"]) == 1
            else t("{n} days in the period", n=len(r["dias"]))),
           ("lin", t("Lines"), str(r["filas"]), t("person × earnings rate"))]
    st.markdown(T.por_fila("cpx_cont_pkpis", 3), unsafe_allow_html=True)
    with st.container(key="cpx_cont_pkpis"):
        for _col, (_s, _l, _v, _pie) in zip(st.columns(len(_kp)), _kp):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_contp_{_s}",
                           width="stretch",
                           help=t("See the table below") if _s == "lin"
                           else t("Open Finance → Hours")):
                if _s == "lin":
                    st.session_state["_cont_bajar_p"] = True
                    st.rerun()
                from core import projects_ui as _PU
                _PU._ir_a("finanzas", "⏱ Horas")

    for a in r["avisos"]:
        st.warning(a)

    st.download_button(
        t(":material/download: Timesheet (CSV)"), data=r["csv"].encode("utf-8"),
        file_name=f"timesheet_{desde}_{hasta}.csv", mime="text/csv",
        disabled=not r["filas"], width="stretch", key="cont_dl_partes")

    # ⚠️ Se dice en la pantalla, no solo en el código: Xero Payroll NO importa partes
    # por CSV (su propia petición de esa función sigue abierta), así que este fichero
    # se teclea o se manda por la API, que es la fase 2.3.
    st.caption(t("Xero Payroll has no CSV timesheet import, so this file is keyed in — or "
                 "sent to Xero below. The day columns are already in the order "
                 "its API expects. Unpaid days off are not here: they are not paid."))

    if r["filas"]:
        from core import projects_ui as _PU
        with st.container(key="cpx_cont_ptabla"):
            _PU._bajar_a("cpx_cont_ptabla", "_cont_bajar_p")
        det = contable.partes(grupo, desde, hasta)
        # Una sola definición de la etiqueta del día: la usan las filas Y la
        # configuración de columnas, así que no hay dos listas en paralelo que
        # puedan desincronizarse (v433/v434).
        _etq_dia = {d: d.strftime("%a %d/%m") for d in det["dias"]}
        _filas = [dict({t("Employee"): f["nombre"], t("Payroll ID"): f["payroll_id"],
                        t("Earnings rate"): f["etiqueta"]},
                       # ⚠️ Cadena, NO un nulo: `st.dataframe` pinta cualquier nulo
                       # como el literal «None» en gris y no hay configuración que lo
                       # evite — el cuadro de lo medido está en `tabla.celda`. Con NaN
                       # (v485) se seguía viendo «None» en producción. El día sin
                       # horas sale vacío, igual que en el CSV.
                       **{_etq_dia[d]: tabla.celda(f["horas"].get(d), 2)
                          for d in det["dias"]},
                       **{t("Total"): tabla.celda(f["total"], 2)})
                  for f in det["filas"]]
        _df = pd.DataFrame(_filas)
        # v584 · «Payroll ID» en pantalla solo si alguien lo tiene (era una columna vacía;
        # es opcional: solo hace falta con dos nombres iguales). El CSV la conserva: el
        # importador la espera.
        if not any(str(f["payroll_id"] or "").strip() for f in det["filas"]):
            _df = _df.drop(columns=[t("Payroll ID")])
        st.dataframe(_df, hide_index=True, width="stretch",
                     column_config=tabla.cfg(None, dict(
                         {c: tabla.derecha(c) for c in _etq_dia.values()},
                         **{t("Total"): tabla.derecha(t("Total"))})))


def _partes_section(grupo):
    """El parte de horas: periodo PROPIO, porque una nómina va por periodo de pago."""
    hoy = clock.today(grupo)
    c1, c2 = st.columns(2)
    # ⚠️ Por defecto la última quincena: el periodo del parte es el de PAGO, no el mes
    # natural del resumen contable de arriba — por eso tiene su propio selector.
    desde = c1.date_input(t("From"), value=hoy - _timedelta(days=13), key="cont_p_d", format="DD/MM/YYYY")
    hasta = c2.date_input(t("To"), value=hoy, key="cont_p_h", format="DD/MM/YYYY")

    # ⚠️ v584 · al revés, salía vacío sin decir por qué. Se salta SOLO el parte: el envío a
    # Xero Payroll y los nombres de nómina, de debajo, siguen
    if desde and hasta and desde > hasta:
        st.warning(t(":material/event_busy: «From» is after «To»: pick the period again."))
    else:
        _parte_csv(grupo, desde, hasta)

    # v490 · el envío a Xero Payroll: parte + permisos, con el periodo de SU calendario.
    from core import xero_ui
    xero_ui.render_partes_xero(grupo)

    # ⚠️ «Payroll names»: desde v490 aquí hay tipos de ganancia Y tipos de permiso, así
    # que llamarlo «Earnings rate names» mentiría para vacaciones y bajas.
    with st.expander(t("Payroll names"), icon=":material/badge:", key="exp_cont_nombres"):
        _editor_conceptos(grupo, contable.mapa(grupo))


def render_contable(grupo):
    """⚠️ Sin título: la sección tiene sub-pestañas, así que `_sub_header` ya pinta
    «Finanzas · Contable» (la lección de v212/v291/v314/v319/v320)."""
    from core import theme as T

    st.caption(t("The files your accountant and your payroll officer import, so nothing "
                 "is typed twice. Invoices can also go straight to Xero (below)."))

    # ⚠️ v584 · el aviso del ABN es UNO, el del motor (`contable.csv_ventas`), con el sitio
    # de verdad: aquí había otro que mandaba a «Administration → Companies», que no existe
    # (es «Groups») y que el administrador —quien ve esta pantalla— ni siquiera tiene.

    c1, c2 = st.columns([2, 3])
    perfil = c1.radio(t("Format"), [k for k, _ in contable.perfiles()],
                      format_func=lambda k: contable.PERFILES[k]["nombre"],
                      horizontal=True, key="cpxseg_cont_perfil", persist_state="session")
    with c2:
        desde, hasta = _periodo(grupo)

    ventas = contable.csv_ventas(grupo, perfil, desde, hasta)
    compras = contable.csv_compras(grupo, perfil, desde, hasta)

    # v584 · las cifras, ACTIVAS: facturas y gastos llevan a su pantalla; las opciones de
    # seguimiento abren la lista de obras que tienen que existir antes de importar
    def _filas_txt(n):
        return t("1 row") if n == 1 else t("{n} rows", n=n)

    _nop = len(set(ventas["opciones"]) | set(compras["opciones"]))
    _kc = [("fac", t("Invoices"), str(ventas["documentos"]), _filas_txt(ventas["filas"]),
            ("finanzas", "🧾 Facturas")),
           ("gas", t("Expenses"), str(compras["documentos"]), _filas_txt(compras["filas"]),
            ("finanzas", "💰 Gastos")),
           ("seg", t("Tracking options"), str(_nop),
            t("1 job involved") if _nop == 1 else t("jobs involved"), None)]
    st.markdown(T.por_fila("cpx_cont_kpis", 3), unsafe_allow_html=True)
    with st.container(key="cpx_cont_kpis"):
        for _col, (_s, _l, _v, _pie, _dest) in zip(st.columns(len(_kc)), _kc):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_cont_{_s}",
                           width="stretch", disabled=(_s == "seg" and not _nop),
                           help=(t("See the jobs that must exist first") if _dest is None
                                 else t("Open it"))):
                if _dest is None:
                    st.session_state["_cont_ver_jobs"] = not st.session_state.get("_cont_ver_jobs")
                    st.session_state["_cont_bajar_jobs"] = st.session_state["_cont_ver_jobs"]
                    st.rerun()
                from core import projects_ui as _PU
                _PU._ir_a(*_dest)

    # ⚠️ Lo que va a fallar AL IMPORTAR, dicho antes de descargar: un importador
    # rechaza la fila y no siempre explica el motivo.
    avisos = list(dict.fromkeys(ventas["avisos"] + compras["avisos"]))
    for a in avisos:
        st.warning(a)

    # v584 · con «All» el fichero se llamaba `xero_bills_todo_todo.csv` (en español)
    _suf = f"{desde}_{hasta}" if desde and hasta else "all"
    d1, d2 = st.columns(2)
    d1.download_button(
        t(":material/download: Invoices (CSV)"), data=ventas["csv"].encode("utf-8"),
        file_name=f"{perfil}_invoices_{_suf}.csv", mime="text/csv",
        disabled=not ventas["filas"], width="stretch", key="cont_dl_ventas")
    d2.download_button(
        t(":material/download: Expenses (CSV)"), data=compras["csv"].encode("utf-8"),
        file_name=f"{perfil}_bills_{_suf}.csv", mime="text/csv",
        disabled=not compras["filas"], width="stretch", key="cont_dl_compras")

    if perfil == "xero":
        st.caption(t("At Xero's import screen choose «Tax Exclusive»: this file always "
                     "writes the amount without tax, with the tax in its own column."))

    # v488: la conexión con Xero va DESPUÉS de las descargas, para no reordenarle la
    # pantalla a quien ya la usa (v297), y usa el MISMO periodo que el CSV.
    from core import xero_ui
    xero_ui.render_conexion(grupo, desde, hasta)

    cfg = contable.mapa(grupo)
    opciones = sorted(set(ventas["opciones"]) | set(compras["opciones"]))
    if opciones:
        # ⚠️ La condición va en la CLAVE (verif_v547): con clave fija, el desplegable recuerda
        # su estado y la cifra no lo abriría. Se queda abierto hasta volver a tocarla.
        _ver = bool(st.session_state.get("_cont_ver_jobs"))
        from core import projects_ui as _PU
        with st.container(key="cpx_cont_jobs"):
            _PU._bajar_a("cpx_cont_jobs", "_cont_bajar_jobs")
        with st.expander(t("Jobs that must exist first ({n})", n=len(opciones)),
                         icon=":material/checklist:", expanded=_ver,
                         key=f"exp_cont_jobs_{_ver}"):
            st.caption(t("Create them with these exact names, then import."))
            st.code("\n".join(opciones), language=None)

    with st.expander(t("Chart of accounts and tax"), icon=":material/account_tree:", key="exp_cont_cuentas"):
        _editor_cuentas(grupo, perfil, cfg)

    # ⚠️ El parte NO cuelga del selector de formato de arriba: es de nómina, no de
    # contabilidad, y su destino es otro. Va DESPUÉS para no reordenar lo que ya estaba.
    T.section(t("Timesheet for payroll"),
              t("Paid hours, person by person and day by day"))
    _partes_section(grupo)
