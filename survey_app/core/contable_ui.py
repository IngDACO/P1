# -*- coding: utf-8 -*-
"""Pantalla de exportación contable (v483): Finanzas → 📤 Contable.

Genera el CSV que el contable importa. Lo que se enseña ANTES de descargar es lo que
va a fallar al importar —cuentas sin poner, proveedores escritos de dos formas, la
categoría de seguimiento que hay que crear— porque un importador rechaza la fila y no
siempre dice por qué.

⚠️ 0 lecturas nuevas de Sheets: facturas, gastos, clientes y proyectos salen de
lectores ya cacheados, y el mapa contable de la fila de `Groups`, que también lo está.
"""
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
    per = st.radio(t("Period"), list(_PER), format_func=lambda o: t(_PER[o]),
                   horizontal=True, key="cpxseg_cont_per", label_visibility="collapsed")
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
        nuevo = dict(cfg)
        # ⚠️ Solo se toca el perfil que se está editando: `mapa()` fusiona sobre los de
        # fábrica, así que escribir el diccionario entero borraría lo del otro perfil.
        nuevo.setdefault("cuentas", {})
        nuevo["cuentas"] = {p: dict(c) for p, c in cfg.get("cuentas", {}).items()}
        nuevo["cuentas"][perfil] = {
            filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
            for i in range(len(filas))}
        nuevo["categoria_seguimiento"] = seg.strip() or "Project"
        nuevo["gastos_incluyen_impuesto"] = bool(dentro)
        ok, msg = contable.guardar_mapa(grupo, nuevo)
        if ok:
            flash.exito(t("Accounting settings updated."))
            st.rerun()
        else:
            st.error(msg)


def render_contable(grupo):
    """⚠️ Sin título: la sección tiene sub-pestañas, así que `_sub_header` ya pinta
    «Finanzas · Contable» (la lección de v212/v291/v314/v319/v320)."""
    from core import theme as T

    st.caption(t("The CSV your accountant imports, so an invoice is not typed twice. "
                 "It does not talk to Xero or MYOB: it produces the file."))

    ident = contable.identidad(grupo)
    if not ident["abn"]:
        st.warning(t(":material/warning: This company has no ABN. Set it in "
                     "Administration → Companies before sending invoices out."))

    c1, c2 = st.columns([2, 3])
    perfil = c1.radio(t("Format"), [k for k, _ in contable.perfiles()],
                      format_func=lambda k: contable.PERFILES[k]["nombre"],
                      horizontal=True, key="cpxseg_cont_perfil")
    with c2:
        desde, hasta = _periodo(grupo)

    ventas = contable.csv_ventas(grupo, perfil, desde, hasta)
    compras = contable.csv_compras(grupo, perfil, desde, hasta)

    T.kpi_row([
        (t("Invoices"), str(ventas["documentos"]), t("{n} rows", n=ventas["filas"])),
        (t("Expenses"), str(compras["documentos"]), t("{n} rows", n=compras["filas"])),
        (t("Tracking options"),
         str(len(set(ventas["opciones"]) | set(compras["opciones"]))),
         t("jobs involved")),
    ])

    # ⚠️ Lo que va a fallar AL IMPORTAR, dicho antes de descargar: un importador
    # rechaza la fila y no siempre explica el motivo.
    avisos = list(dict.fromkeys(ventas["avisos"] + compras["avisos"]))
    for a in avisos:
        st.warning(a)

    _suf = f"{desde or 'todo'}_{hasta or 'todo'}"
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

    cfg = contable.mapa(grupo)
    opciones = sorted(set(ventas["opciones"]) | set(compras["opciones"]))
    if opciones:
        with st.expander(t("Jobs that must exist first ({n})", n=len(opciones)),
                         icon=":material/checklist:"):
            st.caption(t("Create them with these exact names, then import."))
            st.code("\n".join(opciones), language=None)

    with st.expander(t("Chart of accounts and tax"), icon=":material/account_tree:"):
        _editor_cuentas(grupo, perfil, cfg)
