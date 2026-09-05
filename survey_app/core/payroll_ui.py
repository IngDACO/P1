"""👥 Nóminas — cuentas por pagar a los usuarios (Fase 3 financiera).

Admin/propietario: generar nómina por periodo (horas × tarifa + conceptos de ley
editables), lista, detalle (editar conceptos, marcar pagada, colilla PDF, anular).
Campo: «Mis colillas» (solo lectura + descargar su colilla PDF).
"""
from datetime import timedelta

from core.i18n import t, etiqueta as _etq

import pandas as pd
import streamlit as st

from core import tenant
from core import auth, clock, timeclock
from core import payroll
from core import flash          # v365: mensajes que sobreviven al st.rerun()
from core.num import num as _num
from core import tabla


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# ── Vista admin ──────────────────────────────────────────────────
def render_nominas(grupo):
    """Lista de nóminas + lo que la pantalla CALLABA (v319).

    ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · Nóminas». Es la
    4ª vez que aparecía este título duplicado (v212, v291, v314).
    """
    if not payroll.is_configured():
        st.info(t(":material/info: Configure Google Sheets to manage payroll."))
        return
    if st.session_state.get("_nom_gen"):
        _generar(grupo)
        return
    if st.session_state.get("_nom_open"):
        _detalle(grupo, st.session_state["_nom_open"])
        return

    # (los mensajes de generar los pinta `flash`, desde la shell — ver core/flash.py)

    noms = payroll.list_nominas(grupo)
    r = payroll.resumen(grupo)
    _npag = sum(1 for x in noms if str(x.get("Estado", "")).lower() == "pagada")
    _peri = sorted({(str(x.get("PeriodoDesde", "")), str(x.get("PeriodoHasta", "")))
                    for x in noms}, reverse=True)

    # Tarjetas del KIT (`theme.kpi_row`), con línea de contexto: «Nóminas 5» a secas no
    # decía nada. ⚠️ `T.dinero` escapa el `$` para markdown y `kpi_row` pasa por
    # `theme._esc`, que deshace ese escape al montar el HTML (v312).
    from core import theme as T
    T.kpi_row([
        (t("To pay"), T.dinero(r["a_pagar"], 0),
         f"{len(noms) - _npag} issued and unpaid",
         T.ROJO if r["a_pagar"] > 0 else T.AZUL),
        (t("Paid"), T.dinero(r["pagado"], 0), f"{_npag} paid"),
        (t("Payslips"), str(r["n"]), f"{len(_peri)} period(s)"),
    ])

    if st.button(t(":material/add_circle: Generate payroll"), type="primary", key="nom_gen_btn"):
        st.session_state["_nom_gen"] = True
        st.rerun()

    if not noms:
        st.caption(t("No payslips yet. Generate the first one with «Generate payroll»."))
        return

    # ── Filtro de periodo ────────────────────────────────────────
    # Hoy son 5 filas del mismo periodo; en un año son 60 y la tabla deja de servir.
    _OPT_TODOS = "All periods"
    _lbl = {f"{d} → {h}": (d, h) for d, h in _peri}
    _sel = st.selectbox(t("Period"), [_OPT_TODOS] + list(_lbl), key="nom_periodo",
                        label_visibility="collapsed")
    _rows = [x for x in noms
             if _sel == _OPT_TODOS
             or (str(x.get("PeriodoDesde", "")), str(x.get("PeriodoHasta", ""))) == _lbl[_sel]]
    _rows = sorted(_rows, key=lambda x: (str(x.get("PeriodoHasta", "")),
                                         str(x.get("Nombre", ""))), reverse=True)

    # ── Lo que la pantalla no decía ──────────────────────────────
    # (a) colillas de $0 porque esa persona no tenía tarifa/hora cuando se generó.
    #     ⚠️ Desde v346 ya NO se pueden crear (`generar` salta a quien no tiene tarifa),
    #     pero este aviso SE QUEDA: las de antes siguen en la hoja —en producción está
    #     `NOM-0002`, 8,69 h de trabajo real emitidas en $0— y hay que poder verlas para
    #     anularlas y regenerarlas una vez puesta la tarifa.
    _cero = sorted({str(x.get("Nombre", "")) for x in _rows
                    if _num(x.get("Horas")) > 0 and _num(x.get("TarifaHora")) <= 0})
    if _cero:
        st.warning(":material/payments: **" + ", ".join(_cero) + "** "
                   f"ha{'ve' if len(_cero) > 1 else 's'} hours worked but "
                   "**$0 base pay**: they have no hourly rate. The payslip comes out at "
                   "zero and their work does not count towards the cost.")
        if st.button(t(":material/badge: Set rates in Users"), key="nom_ir_users"):
            from core import home_ui
            home_ui.navegar("planificacion", "👷 Usuarios")

    # (b) gente con horas en el periodo y SIN nómina. Es el hueco que el resumen
    #     financiero marca como «Horas sin nómina», pero aquí es donde se arregla.
    if _sel != _OPT_TODOS:
        _d, _h = _lbl[_sel]
        try:
            from core import timeclock, auth
            from datetime import datetime as _dt
            _f = lambda s: _dt.strptime(str(s)[:10], "%Y-%m-%d").date()
            _hp = timeclock.jornada_y_proyecto(grupo, _f(_d), _f(_h))
            _con = {str(x.get("Usuario", "")) for x in _rows}
            # ⚠️ NO `_etq`: ese nombre es la función `i18n.etiqueta` a nivel de módulo,
            # y asignarlo aquí la tapa en TODA la función (v437/v439/v440, cuarta vez).
            _etu = auth.etiqueta_usuarios(auth.list_users(grupo))
            _falta = [(_etu.get(u, u), v) for u, v in _hp.items()
                      if u not in _con and (v["jornada"] > 0 or v["proyecto"] > 0)]
        except Exception:
            _falta = []
        if _falta:
            st.error(":material/person_alert: No payslip in this period despite having hours: "
                     + " · ".join(f"**{n}** ({v['jornada']:.1f} h on shift / "
                                  f"{v['proyecto']:.1f} h on jobs)" for n, v in _falta))

    # ── Tabla ────────────────────────────────────────────────────
    # ⚠️ El nombre PUEDE repetirse (hay dos `fijiofgjei` y dos `lksdfkldsf`): sin el
    # login, dos filas quedan indistinguibles. `auth.etiqueta_usuarios` solo añade el
    # login cuando hace falta.
    from core import auth as _A
    _et = _A.etiqueta_usuarios([{"Usuario": x.get("Usuario"), "Nombre": x.get("Nombre")}
                                for x in noms])
    st.caption(t("Tap a payslip to see the detail, edit items and mark it paid."))
    df = pd.DataFrame([{
        "Usuario":  _et.get(str(x.get("Usuario", "")), str(x.get("Nombre", ""))),
        "Periodo":  f"{x.get('PeriodoDesde', '')} → {x.get('PeriodoHasta', '')}",
        "Horas":    round(_num(x.get("Horas")), 1),
        "Rate/h": (round(_num(x.get("TarifaHora")), 2)
                     if _num(x.get("TarifaHora")) > 0 else float("nan")),
        "Base":     round(_num(x.get("Base")), 0),
        "Neto":     round(_num(x.get("Neto")), 0),
        "Estado":   _etq(str(x.get("Estado", ""))),
    } for x in _rows])
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        on_select="rerun", selection_mode="single-row", key="nom_tbl",
        column_config=tabla.cfg(None, {"Base": st.column_config.NumberColumn(t("Base pay"), format="$%,d"),
                       "Neto": st.column_config.NumberColumn(t("Net"), format="$%,d"),
                       "Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f")}))
    st.caption(f"{len(_rows)} payslip(s)  ·  base pay {T.dinero(sum(_num(x.get('Base')) for x in _rows), 0)}"
               f"  ·  net {T.dinero(sum(_num(x.get('Neto')) for x in _rows), 0)}"
               "  ·  an empty «Rate/h» means that person has no rate set.")
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_nom_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("nom_tbl", None)
        st.rerun()


def _generar(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="nom_gen_back"):
        st.session_state.pop("_nom_gen", None)
        st.rerun()
    st.markdown(t("## :material/add_circle: Generate payroll"))

    hoy = clock.today(grupo)
    per = st.radio(t("Frequency"), ["Semanal", "Quincenal", "Mensual", "Personalizado"],
                   format_func=lambda o: t({"Semanal": "Weekly", "Quincenal": "Fortnightly",
                                            "Mensual": "Monthly",
                                            "Personalizado": "Custom"}.get(o, o)),
                   horizontal=True, key="nom_per")
    _d0 = {"Semanal": hoy - timedelta(days=6), "Quincenal": hoy - timedelta(days=13),
           "Mensual": hoy - timedelta(days=29)}.get(per, hoy - timedelta(days=6))
    c1, c2 = st.columns(2)
    desde = c1.date_input(t("From"), value=_d0, key=f"nom_desde_{per}")
    hasta = c2.date_input(t("To"), value=hoy, key=f"nom_hasta_{per}")

    _sup = auth.group_num_setting(grupo, "SuperDefault", 11.5)
    _ret = auth.group_num_setting(grupo, "RetencionDefault", 0.0)
    c3, c4 = st.columns(2)
    sup = c3.number_input(t("Superannuation % (employer contribution)"), min_value=0.0, max_value=100.0,
                          value=float(_sup), step=0.5, key="nom_sup")
    ret = c4.number_input(t("Tax withholding % (deduction)"), min_value=0.0, max_value=100.0,
                          value=float(_ret), step=1.0, key="nom_ret")
    st.caption(t(":material/info: The super and withholding percentages come from the company and can be edited here and on each payslip. This is not a certified tax calculation; check the amounts."))

    horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)
    rates = auth.rate_map(grupo)
    if horas:
        st.markdown(f"**{len(horas)} user(s)** with workday hours in the period:")
        st.dataframe(pd.DataFrame([{
            "Usuario": v["nombre"], "Horas": round(v["horas"], 1),
            "Rate/h": _num(rates.get(k, 0)),
            "Base": round(v["horas"] * _num(rates.get(k, 0)), 0),
        } for k, v in sorted(horas.items())]), width="stretch", hide_index=True,
            column_config=tabla.cfg(None, {"Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,d"),
                           "Base": st.column_config.NumberColumn(t("Base pay"), format="$%,d")}))
    else:
        st.info(t("Nobody has workday hours in that period."))

    if st.button(t(":material/payments: Generate payslips"), type="primary", disabled=not horas,
                 key="nom_do"):
        res = payroll.generar(grupo, desde.isoformat(), hasta.isoformat(), sup, ret, _creado_por())
        if res.get("error"):
            st.error(res["error"])          # este SÍ se ve: no hay rerun detrás
            return
        # ⚠️ v365: los mensajes NO se pintan aquí. El `st.rerun()` de abajo descarta los
        # deltas del run en curso, así que se perdían TODOS — incluido el aviso de v346
        # (gente sin tarifa) y el bloqueo de solape de v364. Van a `flash`, que los pinta
        # la shell del otro lado del rerun. Mecanismo ÚNICO para toda la app: tener aquí
        # uno propio y otro general sería el doble camino que hubo que desmontar en v140.
        flash.exito(f"{res.get('creadas', 0)} payslip(s) created."
                    + (f" {res['omitidas']} already existed for that period." if res.get("omitidas") else ""))
        # ⚠️ v346: ya NO se crea una colilla de $0. Se salta y se dice a quién, con el
        # camino para arreglarlo; al ponerle la tarifa y regenerar el mismo periodo
        # entra sin duplicar (no dejó fila).
        _st = res.get("sin_tarifa") or []
        if _st:
            flash.aviso(":material/person_off: **No payslip was generated for "
                        + ", ".join(_st) + "**: they have no hourly rate, so their payslip would come out at $0. Set the rate in :material/build: Planning → Users and generate this same period again — they will be included without duplicating.")
        # ⚠️ v364: periodos que SOLAPAN con una nómina ya emitida. El salto de duplicados
        # solo veía la terna exacta, así que un rango corrido pagaba las mismas horas dos
        # veces sin decir nada. Se bloquea y se NOMBRA la nómina que estorba, porque el
        # error es invisible después: cada colilla suelta sale bien.
        _sol = res.get("solapadas") or []
        if _sol:
            _líneas = "\n".join(f"- **{s['nombre']}** already has `{s['id']}` from "
                                f"{s['desde']} to {s['hasta']}" for s in _sol)
            flash.error(t(":material/event_repeat: **Nothing was generated** because the chosen "
                          "period overlaps payslips already issued — the same hours would be paid "
                          "twice:")
                        + "\n\n" + _líneas + "\n\n"
                        + t("Adjust the dates so they do not overlap, or void those payslips in "
                            "the list below and generate again."))
        # ⚠️ v432: días en que la persona tenía ausencia pagada Y además fichó. Un día
        # vale UNA jornada, así que la ausencia paga solo lo que falta — pero el ajuste
        # se DICE: un recorte de dinero que nadie ve es la mitad del problema que
        # venía a arreglar (antes se pagaban las dos cosas, $670 por un día).
        _rec = res.get("recortes") or []
        if _rec:
            _l = "\n".join(
                f"- **{r['nombre']}** on {r['fecha']}: clocked {r['fichadas']:g} h, "
                f"so their absence pays {r['pagadas']:g} h (not the whole working day)"
                for r in _rec[:12])
            flash.info(":material/schedule: **Days with both an absence and a clock-in** — only one working day is paid per day:\n\n" + _l
                       + ("\n\n…and more." if len(_rec) > 12 else ""))
        st.session_state.pop("_nom_gen", None)
        st.rerun()


def _detalle(grupo, nid):
    if st.button(t(":material/arrow_back: Back to payroll"), key="nom_back"):
        st.session_state.pop("_nom_open", None)
        st.rerun()
    f = payroll.get_nomina(nid)
    if not f:
        st.warning(t("Payslip not found."))
        st.session_state.pop("_nom_open", None)
        return
    if not tenant.exigir(f, "This payslip"):        # v351
        st.session_state.pop("_nom_open", None)
        return
    base = _num(f.get("Base"))
    est = str(f.get("Estado", "emitida"))
    st.markdown(f"## :material/payments: Payslip — {f.get('Nombre', '')}")
    # ⚠️ v309: dos importes en la misma línea → Streamlit lo renderizaba como LaTeX
    # (la tarifa y la base salían como fórmula). `theme.dinero` escapa el `$`.
    from core import theme as _T
    st.markdown(f"Period **{f.get('PeriodoDesde', '')} → {f.get('PeriodoHasta', '')}**  ·  "
                f"{_num(f.get('Horas')):.1f} h × {_T.dinero(f.get('TarifaHora'))} = "
                f"base pay **{_T.dinero(base)}**  ·  status: **{est}**")

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(t("#### :material/list: Items (earnings, deductions, employer contributions)"))
        _cs = payroll.conceptos_de(f)
        _pre = [{"Concepto": c.get("concepto", ""), "Tipo": c.get("tipo", "deduccion"),
                 "Monto": _num(c.get("monto"))} for c in _cs] or \
               [{"Concepto": "", "Tipo": "deduccion", "Monto": 0.0}]
        _ed = st.data_editor(
            pd.DataFrame(_pre), num_rows="dynamic", width="stretch", key=f"nom_ed_{nid}",
            column_config=tabla.cfg(None, {
                "Concepto": st.column_config.TextColumn(t("Item"), width="large"),
                "Tipo": st.column_config.SelectboxColumn(t("Type"), options=payroll.TIPOS, required=True),
                "Monto": st.column_config.NumberColumn(t("Amount"), format="$%,.2f", min_value=0.0),
            }))
        if est != "anulada" and st.button(t(":material/save: Save items"), key=f"nom_save_{nid}"):
            conceptos = []
            for _, rr in _ed.iterrows():
                con = str(rr.get("Concepto", "")).strip()
                mon = _num(rr.get("Monto"))
                if not con and mon == 0:
                    continue
                conceptos.append({"concepto": con,
                                  "tipo": str(rr.get("Tipo", "deduccion") or "deduccion"),
                                  "monto": mon})
            ok, msg = payroll.update_conceptos(nid, conceptos)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()

    with der:
        st.metric(t("Net pay"), f"${_num(f.get('Neto')):,.2f}")
        try:
            from core import payslip_pdf
            _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
            st.download_button(t(":material/download: Download payslip (PDF)"), data=_pdf,
                               file_name=f"Colilla_{f.get('Nombre', '')}_{f.get('PeriodoHasta', '')}.pdf",
                               mime="application/pdf", key=f"nom_pdf_{nid}")
        except Exception as e:
            st.caption(f":material/warning: The PDF could not be generated: {e}")
        if est == "pagada":
            st.success(f":material/check_circle: Paid ({f.get('FechaPago', '')}).")
        elif est != "anulada":
            with st.form(f"nom_pay_{nid}"):
                _fch = st.date_input(t("Payment date"), value=clock.today(grupo))
                if st.form_submit_button(t(":material/check: Mark as paid"), type="primary"):
                    ok, msg = payroll.marcar_pagada(nid, _fch.isoformat())
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        if est != "anulada":
            with st.expander(t(":material/block: Void payslip")):
                if st.button(t("Void this payslip"), key=f"nom_anul_{nid}"):
                    payroll.anular(nid)
                    st.session_state.pop("_nom_open", None)
                    st.rerun()


# ── Vista del campo: Mis colillas ────────────────────────────────
def render_mis_colillas(usuario, grupo):
    st.markdown(t("## :material/payments: My payslips"))
    if not payroll.is_configured():
        st.info(t(":material/info: Not available yet."))
        return
    noms = payroll.list_nominas(grupo, usuario=usuario)
    if not noms:
        st.caption(t("You have no payslips yet."))
        return
    for f in sorted(noms, key=lambda x: str(x.get("PeriodoHasta", "")), reverse=True):
        with st.container(border=True):
            st.markdown(f"**{f.get('PeriodoDesde', '')} → {f.get('PeriodoHasta', '')}**  ·  "
                        f"{_num(f.get('Horas')):.1f} h  ·  net **${_num(f.get('Neto')):,.2f}**  ·  "
                        f"{_etq(str(f.get('Estado', '')))}")
            try:
                from core import payslip_pdf
                _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
                st.download_button(t(":material/download: Download payslip"), data=_pdf,
                                   file_name=f"Colilla_{f.get('PeriodoHasta', '')}.pdf",
                                   mime="application/pdf", key=f"myp_{f.get('ID', '')}")
            except Exception as e:
                st.caption(str(e))
