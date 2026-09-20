# -*- coding: utf-8 -*-
"""v484 · el parte de horas en la pantalla de exportación."""
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\contable_ui.py"
s = io.open(P, encoding="utf-8").read()

# ── 1 · el caption de la pantalla, que ahora cubre dos cosas ────────────────
V1 = '''    st.caption(t("The CSV your accountant imports, so an invoice is not typed twice. "
                 "It does not talk to Xero or MYOB: it produces the file."))'''
N1 = '''    st.caption(t("The files your accountant and your payroll officer import, so nothing "
                 "is typed twice. It does not talk to Xero or MYOB: it produces them."))'''
if s.count(V1) != 1:
    raise SystemExit("ancla caption no unica: %d" % s.count(V1))
s = s.replace(V1, N1)

# ── 2 · la sección del parte, al final del render ───────────────────────────
V2 = '''    with st.expander(t("Chart of accounts and tax"), icon=":material/account_tree:"):
        _editor_cuentas(grupo, perfil, cfg)'''
N2 = '''    with st.expander(t("Chart of accounts and tax"), icon=":material/account_tree:"):
        _editor_cuentas(grupo, perfil, cfg)

    # ⚠️ El parte NO cuelga del selector de formato de arriba: es de nómina, no de
    # contabilidad, y su destino es otro. Va DESPUÉS para no reordenar lo que ya estaba.
    T.section(t("Timesheet for payroll"),
              t("Paid hours, person by person and day by day"))
    _partes_section(grupo)'''
if s.count(V2) != 1:
    raise SystemExit("ancla expander no unica: %d" % s.count(V2))
s = s.replace(V2, N2)

# ── 3 · las dos funciones nuevas ────────────────────────────────────────────
V3 = '''def render_contable(grupo):'''
N3 = '''def _editor_conceptos(grupo, cfg):
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
            "Cuenta":   st.column_config.TextColumn(t("Earnings rate name in payroll")),
        }))

    if st.button(t(":material/save: Save earnings rates"), key="cont_save_conceptos"):
        nuevo = dict(cfg)
        nuevo["conceptos"] = {filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
                              or filas[i]["_k"] for i in range(len(filas))}
        ok, msg = contable.guardar_mapa(grupo, nuevo)
        if ok:
            flash.exito(t("Earnings rates updated."))
            st.rerun()
        else:
            st.error(msg)


def _partes_section(grupo):
    """El parte de horas: periodo PROPIO, porque una nómina va por periodo de pago."""
    from core import theme as T

    hoy = clock.today(grupo)
    c1, c2 = st.columns(2)
    # ⚠️ Por defecto la última quincena: el periodo del parte es el de PAGO, no el mes
    # natural del resumen contable de arriba — por eso tiene su propio selector.
    desde = c1.date_input(t("From"), value=hoy - _timedelta(days=13), key="cont_p_d")
    hasta = c2.date_input(t("To"), value=hoy, key="cont_p_h")

    r = contable.csv_partes(grupo, desde, hasta)

    T.kpi_row([
        (t("People"), str(r["personas"]), t("with paid hours")),
        (t("Paid hours"), f"{r['total']:,.2f}", t("{n} days in the period",
                                                  n=len(r["dias"]))),
        (t("Lines"), str(r["filas"]), t("person × earnings rate")),
    ])

    for a in r["avisos"]:
        st.warning(a)

    st.download_button(
        t(":material/download: Timesheet (CSV)"), data=r["csv"].encode("utf-8"),
        file_name=f"timesheet_{desde}_{hasta}.csv", mime="text/csv",
        disabled=not r["filas"], width="stretch", key="cont_dl_partes")

    # ⚠️ Se dice en la pantalla, no solo en el código: Xero Payroll NO importa partes
    # por CSV (su propia petición de esa función sigue abierta), así que este fichero
    # se teclea o se manda por la API, que es la fase 2.3.
    st.caption(t("Xero Payroll has no CSV timesheet import, so this is keyed in (or "
                 "sent through the API later). The day columns are already in the order "
                 "its API expects. Unpaid days off are not here: they are not paid."))

    if r["filas"]:
        det = contable.partes(grupo, desde, hasta)
        _filas = [dict({t("Employee"): f["nombre"], t("Payroll ID"): f["payroll_id"],
                        t("Earnings rate"): f["etiqueta"]},
                       **{d.strftime("%a %d/%m"): f["horas"].get(d)
                          for d in det["dias"]},
                       **{t("Total"): f["total"]})
                  for f in det["filas"]]
        st.dataframe(pd.DataFrame(_filas), hide_index=True, width="stretch",
                     column_config=tabla.cfg())

    with st.expander(t("Earnings rate names"), icon=":material/badge:"):
        _editor_conceptos(grupo, contable.mapa(grupo))


def render_contable(grupo):'''
if s.count(V3) != 1:
    raise SystemExit("ancla render_contable no unica: %d" % s.count(V3))
s = s.replace(V3, N3)

# ── 4 · el import que las dos funciones nuevas necesitan ────────────────────
if "from datetime import timedelta as _timedelta" not in s:
    V4 = "import pandas as pd\n"
    if s.count(V4) != 1:
        raise SystemExit("ancla import no unica")
    s = s.replace(V4, "from datetime import timedelta as _timedelta\n\nimport pandas as pd\n")

compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("contable_ui: seccion del parte + editor de earnings rates")
