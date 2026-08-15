"""👥 Nóminas — cuentas por pagar a los usuarios (Fase 3 financiera).

Admin/propietario: generar nómina por periodo (horas × tarifa + conceptos de ley
editables), lista, detalle (editar conceptos, marcar pagada, colilla PDF, anular).
Campo: «Mis colillas» (solo lectura + descargar su colilla PDF).
"""
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import auth, clock, timeclock
from core import payroll


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


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
        st.info(":material/info: Configura Google Sheets para gestionar nóminas.")
        return
    if st.session_state.get("_nom_gen"):
        _generar(grupo)
        return
    if st.session_state.get("_nom_open"):
        _detalle(grupo, st.session_state["_nom_open"])
        return

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
        ("Por pagar", T.dinero(r["a_pagar"], 0),
         f"{len(noms) - _npag} emitida(s) sin pagar",
         T.ROJO if r["a_pagar"] > 0 else T.AZUL),
        ("Pagado", T.dinero(r["pagado"], 0), f"{_npag} pagada(s)"),
        ("Nóminas", str(r["n"]), f"{len(_peri)} periodo(s)"),
    ])

    if st.button(":material/add_circle: Generar nómina", type="primary", key="nom_gen_btn"):
        st.session_state["_nom_gen"] = True
        st.rerun()

    if not noms:
        st.caption("Aún no hay nóminas. Genera la primera con «Generar nómina».")
        return

    # ── Filtro de periodo ────────────────────────────────────────
    # Hoy son 5 filas del mismo periodo; en un año son 60 y la tabla deja de servir.
    _OPT_TODOS = "Todos los periodos"
    _lbl = {f"{d} → {h}": (d, h) for d, h in _peri}
    _sel = st.selectbox("Periodo", [_OPT_TODOS] + list(_lbl), key="nom_periodo",
                        label_visibility="collapsed")
    _rows = [x for x in noms
             if _sel == _OPT_TODOS
             or (str(x.get("PeriodoDesde", "")), str(x.get("PeriodoHasta", ""))) == _lbl[_sel]]
    _rows = sorted(_rows, key=lambda x: (str(x.get("PeriodoHasta", "")),
                                         str(x.get("Nombre", ""))), reverse=True)

    # ── Lo que la pantalla no decía ──────────────────────────────
    # (a) colillas de $0 porque esa persona no tiene tarifa/hora. `payroll.generar` ya
    #     lo detecta (devuelve `sin_tarifa`) pero eso se ve UNA vez, al generar, y
    #     después la lista deja las nóminas a 0 como si estuvieran bien.
    _cero = sorted({str(x.get("Nombre", "")) for x in _rows
                    if _num(x.get("Horas")) > 0 and _num(x.get("TarifaHora")) <= 0})
    if _cero:
        st.warning(":material/payments: **" + ", ".join(_cero) + "** "
                   f"tiene{'n' if len(_cero) > 1 else ''} horas trabajadas pero "
                   "**base $0**: les falta la tarifa/hora. La colilla sale en cero y su "
                   "trabajo no cuenta en el costo.")
        if st.button(":material/badge: Poner tarifas en Usuarios", key="nom_ir_users"):
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
            _etq = auth.etiqueta_usuarios(auth.list_users(grupo))
            _falta = [(_etq.get(u, u), v) for u, v in _hp.items()
                      if u not in _con and (v["jornada"] > 0 or v["proyecto"] > 0)]
        except Exception:
            _falta = []
        if _falta:
            st.error(":material/person_alert: Sin nómina en este periodo, teniendo horas: "
                     + " · ".join(f"**{n}** ({v['jornada']:.1f} h jornada / "
                                  f"{v['proyecto']:.1f} h en obra)" for n, v in _falta))

    # ── Tabla ────────────────────────────────────────────────────
    # ⚠️ El nombre PUEDE repetirse (hay dos `fijiofgjei` y dos `lksdfkldsf`): sin el
    # login, dos filas quedan indistinguibles. `auth.etiqueta_usuarios` solo añade el
    # login cuando hace falta.
    from core import auth as _A
    _et = _A.etiqueta_usuarios([{"Usuario": x.get("Usuario"), "Nombre": x.get("Nombre")}
                                for x in noms])
    st.caption("Toca una nómina para ver el detalle, editar conceptos y marcar pagada.")
    df = pd.DataFrame([{
        "Usuario":  _et.get(str(x.get("Usuario", "")), str(x.get("Nombre", ""))),
        "Periodo":  f"{x.get('PeriodoDesde', '')} → {x.get('PeriodoHasta', '')}",
        "Horas":    round(_num(x.get("Horas")), 1),
        "Tarifa/h": (round(_num(x.get("TarifaHora")), 2)
                     if _num(x.get("TarifaHora")) > 0 else None),
        "Base":     round(_num(x.get("Base")), 0),
        "Neto":     round(_num(x.get("Neto")), 0),
        "Estado":   str(x.get("Estado", "")),
    } for x in _rows])
    _ev = st.dataframe(
        df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="nom_tbl",
        column_config={"Base": st.column_config.NumberColumn("Base", format="$%d"),
                       "Neto": st.column_config.NumberColumn("Neto", format="$%d"),
                       "Tarifa/h": st.column_config.NumberColumn("Tarifa/h", format="$%.2f")})
    st.caption(f"{len(_rows)} nómina(s)  ·  base {T.dinero(sum(_num(x.get('Base')) for x in _rows), 0)}"
               f"  ·  neto {T.dinero(sum(_num(x.get('Neto')) for x in _rows), 0)}"
               "  ·  «Tarifa/h» vacía = esa persona no la tiene puesta.")
    _sr = list(_ev.selection.rows)
    if _sr:
        st.session_state["_nom_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.session_state.pop("nom_tbl", None)
        st.rerun()


def _generar(grupo):
    if st.button(":material/arrow_back: Cancelar", key="nom_gen_back"):
        st.session_state.pop("_nom_gen", None)
        st.rerun()
    st.markdown("## :material/add_circle: Generar nómina")

    hoy = clock.today(grupo)
    per = st.radio("Periodicidad", ["Semanal", "Quincenal", "Mensual", "Personalizado"],
                   horizontal=True, key="nom_per")
    _d0 = {"Semanal": hoy - timedelta(days=6), "Quincenal": hoy - timedelta(days=13),
           "Mensual": hoy - timedelta(days=29)}.get(per, hoy - timedelta(days=6))
    c1, c2 = st.columns(2)
    desde = c1.date_input("Desde", value=_d0, key=f"nom_desde_{per}")
    hasta = c2.date_input("Hasta", value=hoy, key=f"nom_hasta_{per}")

    _sup = auth.group_num_setting(grupo, "SuperDefault", 11.5)
    _ret = auth.group_num_setting(grupo, "RetencionDefault", 0.0)
    c3, c4 = st.columns(2)
    sup = c3.number_input("Superannuation % (aporte)", min_value=0.0, max_value=100.0,
                          value=float(_sup), step=0.5, key="nom_sup")
    ret = c4.number_input("Retención de impuesto % (deducción)", min_value=0.0, max_value=100.0,
                          value=float(_ret), step=1.0, key="nom_ret")
    st.caption(":material/info: Los % de super y retención vienen del grupo y son editables aquí y en "
               "cada nómina. No es un cálculo fiscal certificado; valida los importes.")

    horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)
    rates = auth.rate_map(grupo)
    if horas:
        st.markdown(f"**{len(horas)} usuario(s)** con horas de jornada en el periodo:")
        st.dataframe(pd.DataFrame([{
            "Usuario": v["nombre"], "Horas": round(v["horas"], 1),
            "Tarifa/h": _num(rates.get(k, 0)),
            "Base": round(v["horas"] * _num(rates.get(k, 0)), 0),
        } for k, v in sorted(horas.items())]), use_container_width=True, hide_index=True,
            column_config={"Tarifa/h": st.column_config.NumberColumn("Tarifa/h", format="$%d"),
                           "Base": st.column_config.NumberColumn("Base", format="$%d")})
    else:
        st.info("Nadie tiene horas de jornada en ese periodo.")

    if st.button(":material/payments: Generar nóminas", type="primary", disabled=not horas,
                 key="nom_do"):
        res = payroll.generar(grupo, desde.isoformat(), hasta.isoformat(), sup, ret, _creado_por())
        if res.get("error"):
            st.error(res["error"])
            return
        st.success(f"{res['creadas']} nómina(s) creada(s)."
                   + (f" {res['omitidas']} ya existían para ese periodo." if res['omitidas'] else ""))
        if res.get("sin_tarifa"):
            st.warning(f"{res['sin_tarifa']} usuario(s) sin tarifa (base $0). "
                       "Ponla en Planificación → Usuarios.")
        st.session_state.pop("_nom_gen", None)
        st.rerun()


def _detalle(grupo, nid):
    if st.button(":material/arrow_back: Volver a nóminas", key="nom_back"):
        st.session_state.pop("_nom_open", None)
        st.rerun()
    f = payroll.get_nomina(nid)
    if not f:
        st.warning("Nómina no encontrada.")
        st.session_state.pop("_nom_open", None)
        return
    base = _num(f.get("Base"))
    est = str(f.get("Estado", "emitida"))
    st.markdown(f"## :material/payments: Nómina — {f.get('Nombre', '')}")
    # ⚠️ v309: dos importes en la misma línea → Streamlit lo renderizaba como LaTeX
    # (la tarifa y la base salían como fórmula). `theme.dinero` escapa el `$`.
    from core import theme as _T
    st.markdown(f"Periodo **{f.get('PeriodoDesde', '')} → {f.get('PeriodoHasta', '')}**  ·  "
                f"{_num(f.get('Horas')):.1f} h × {_T.dinero(f.get('TarifaHora'))} = "
                f"base **{_T.dinero(base)}**  ·  estado: **{est}**")

    izq, der = st.columns([3, 2])
    with izq:
        st.markdown("#### :material/list: Conceptos (devengos, deducciones, aportes)")
        _cs = payroll.conceptos_de(f)
        _pre = [{"Concepto": c.get("concepto", ""), "Tipo": c.get("tipo", "deduccion"),
                 "Monto": _num(c.get("monto"))} for c in _cs] or \
               [{"Concepto": "", "Tipo": "deduccion", "Monto": 0.0}]
        _ed = st.data_editor(
            pd.DataFrame(_pre), num_rows="dynamic", use_container_width=True, key=f"nom_ed_{nid}",
            column_config={
                "Concepto": st.column_config.TextColumn("Concepto", width="large"),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=payroll.TIPOS, required=True),
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f", min_value=0.0),
            })
        if est != "anulada" and st.button(":material/save: Guardar conceptos", key=f"nom_save_{nid}"):
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
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    with der:
        st.metric("Neto a pagar", f"${_num(f.get('Neto')):,.2f}")
        try:
            from core import payslip_pdf
            _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
            st.download_button(":material/download: Descargar colilla (PDF)", data=_pdf,
                               file_name=f"Colilla_{f.get('Nombre', '')}_{f.get('PeriodoHasta', '')}.pdf",
                               mime="application/pdf", key=f"nom_pdf_{nid}")
        except Exception as e:
            st.caption(f":material/warning: No se pudo generar el PDF: {e}")
        if est == "pagada":
            st.success(f":material/check_circle: Pagada ({f.get('FechaPago', '')}).")
        elif est != "anulada":
            with st.form(f"nom_pay_{nid}"):
                _fch = st.date_input("Fecha de pago", value=clock.today(grupo))
                if st.form_submit_button(":material/check: Marcar pagada", type="primary"):
                    ok, msg = payroll.marcar_pagada(nid, _fch.isoformat())
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        if est != "anulada":
            with st.expander(":material/block: Anular nómina"):
                if st.button("Anular esta nómina", key=f"nom_anul_{nid}"):
                    payroll.anular(nid)
                    st.session_state.pop("_nom_open", None)
                    st.rerun()


# ── Vista del campo: Mis colillas ────────────────────────────────
def render_mis_colillas(usuario, grupo):
    st.markdown("## :material/payments: Mis colillas de pago")
    if not payroll.is_configured():
        st.info(":material/info: Aún no está disponible.")
        return
    noms = payroll.list_nominas(grupo, usuario=usuario)
    if not noms:
        st.caption("Aún no tienes colillas de pago.")
        return
    for f in sorted(noms, key=lambda x: str(x.get("PeriodoHasta", "")), reverse=True):
        with st.container(border=True):
            st.markdown(f"**{f.get('PeriodoDesde', '')} → {f.get('PeriodoHasta', '')}**  ·  "
                        f"{_num(f.get('Horas')):.1f} h  ·  neto **${_num(f.get('Neto')):,.2f}**  ·  "
                        f"{f.get('Estado', '')}")
            try:
                from core import payslip_pdf
                _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
                st.download_button(":material/download: Descargar colilla", data=_pdf,
                                   file_name=f"Colilla_{f.get('PeriodoHasta', '')}.pdf",
                                   mime="application/pdf", key=f"myp_{f.get('ID', '')}")
            except Exception as e:
                st.caption(str(e))
