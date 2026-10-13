"""👥 Nóminas — cuentas por pagar a los usuarios (Fase 3 financiera).

Admin/propietario: generar nómina por periodo (horas × tarifa + conceptos de ley
editables), lista, detalle (editar conceptos, marcar pagada, colilla PDF, anular).
Campo: «Mis colillas» (solo lectura + descargar su colilla PDF).

v574 · probada acción por acción (Finance → Payroll): cifras que filtran, anuladas a la
vista, fechas DD/MM/YYYY, dinero con céntimos, anular con confirmación y aviso, deshacer
un pago, conceptos legibles y a la vista, y la colilla con el nombre legal y el ABN.
"""
from datetime import timedelta

from core.i18n import t, etiqueta as _etq

import pandas as pd
import streamlit as st

from core import tenant
from core import auth, clock, timeclock
from core import payroll
from core import flash          # v365: mensajes que sobreviven al st.rerun()
from core.num import num as _num, dmy as _dmy
from core import tabla


def _creado_por() -> str:
    a = st.session_state.get("auth") or {}
    return str(a.get("usuario", "") or a.get("nombre", ""))


# Filtro de la lista: ID interno → (estados que entran, rótulo). ⚠️ Sin `t()` aquí: se
# construye al IMPORTAR (quedaría congelado en el idioma de ese instante, v445); el
# rótulo se traduce al pintar.
_FILTROS = {"Todas": (None, "All"),
            "PorPagar": (("emitida",), "To pay"),
            "Pagadas": (("pagada",), "Paid"),
            "Anuladas": (("anulada",), "Voided")}
# En una TABLA no se pintan `:color[]` ni `:material/…:` (v569): el estado, con un punto.
_EST_PUNTO = {"emitida": "🟠", "pagada": "🟢", "anulada": "⚫"}
_EST_ICONO = {"emitida": ":orange[:material/schedule:]", "pagada": ":green[:material/check_circle:]",
              "anulada": ":gray[:material/block:]"}


def _estado(x) -> str:
    return str(x.get("Status", "") or "emitida").lower()


def _est_celda(x) -> str:
    """El estado en una CELDA: punto + la etiqueta traducida (fuera del dict de la fila:
    verif_v452 no deja llamar en crudo a un DATO dentro de una celda)."""
    return f"{_EST_PUNTO.get(_estado(x), '')} " + _etq(_estado(x))


def _periodo(x) -> str:
    return f"{_dmy(x.get('PeriodFrom'))} → {_dmy(x.get('PeriodTo'))}"


def _nota_tarifa(r) -> str:
    return t("no rate — will be skipped") if _num(r) <= 0 else ""


def _accion_pendiente():
    """⚠️ v574 · ACCIÓN DIFERIDA (trampa 37): anular y deshacer un pago escriben en la
    hoja; el botón solo apunta y relanza, y se hace aquí, antes de pintar nada. Y se
    RELANZA para que el aviso salga en esta misma vista (v570): antes anular no avisaba."""
    _acc = st.session_state.pop("_nom_accion", None)
    if not _acc:
        return
    if _acc.get("accion") == "anular":
        _ok, _msg = payroll.anular(_acc.get("nid", ""))
    else:
        _ok, _msg = payroll.deshacer_pago(_acc.get("nid", ""))
    (flash.exito if _ok else flash.error)(_msg)
    st.rerun()


# ── Vista admin ──────────────────────────────────────────────────
def render_nominas(grupo):
    """Lista de nóminas + lo que la pantalla CALLABA (v319).

    ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · Nóminas». Es la
    4ª vez que aparecía este título duplicado (v212, v291, v314).
    """
    if not payroll.is_configured():
        st.info(t(":material/info: Configure Google Sheets to manage payroll."))
        return
    _accion_pendiente()
    if st.session_state.get("_nom_gen"):
        _generar(grupo)
        return
    if st.session_state.get("_nom_open"):
        _detalle(grupo, st.session_state["_nom_open"])
        return

    # (los mensajes de generar los pinta `flash`, desde la shell — ver core/flash.py)

    # ⚠️ v574 · CON las anuladas: antes desaparecían sin rastro (filtro «Voided»).
    noms = payroll.list_nominas(grupo, incluir_anuladas=True)
    r = payroll.resumen(grupo)
    _vivas = [x for x in noms if _estado(x) != "anulada"]
    _npag = sum(1 for x in _vivas if _estado(x) == "pagada")
    _peri = sorted({(str(x.get("PeriodFrom", "")), str(x.get("PeriodTo", "")))
                    for x in _vivas}, reverse=True)

    # ── Las 3 cifras, ACTIVAS (v574: eran HTML): cada una aplica su filtro ──
    from core import theme as T
    _K = [("apag", t("To pay"), T.dinero(r["a_pagar"], 2),
           t("{n} issued and unpaid", n=len(_vivas) - _npag), "PorPagar"),
          ("pag", t("Paid"), T.dinero(r["pagado"], 2), t("{n} paid", n=_npag), "Pagadas"),
          ("tot", t("Payslips"), str(r["n"]), t("{n} period(s)", n=len(_peri)), "Todas")]
    if r["a_pagar"] > 0:
        st.markdown("<style>.st-key-cpxkpi_nom_apag button{border-left-color:#c0392b!important}"
                    ".st-key-cpxkpi_nom_apag button p:nth-child(2):not(:last-child)"
                    "{color:#c0392b!important}</style>", unsafe_allow_html=True)
    st.markdown(T.dos_por_fila("cpx_nom_kpis"), unsafe_allow_html=True)   # v576 · 2 por fila en estrecho
    with st.container(key="cpx_nom_kpis"):
        for _col, (_s, _l, _v, _pie, _fl) in zip(st.columns(3), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_nom_{_s}", width="stretch"):
                st.session_state["_nom_filt_pending"] = _fl
                st.rerun()

    if st.button(t(":material/add_circle: Generate payroll"), type="primary", key="nom_gen_btn"):
        st.session_state["_nom_gen"] = True
        st.rerun()

    if not noms:
        st.caption(t("No payslips yet. Generate the first one with «Generate payroll»."))
        return

    # ── Filtros: estado (recordado) y periodo ────────────────────
    _pp = st.session_state.pop("_nom_filt_pending", None)
    if _pp in _FILTROS:
        st.session_state["cpxseg_nom_filt"] = _pp
    _filt = st.radio(t("Filter"), list(_FILTROS), format_func=lambda o: t(_FILTROS[o][1]),
                     horizontal=True, key="cpxseg_nom_filt", label_visibility="collapsed",
                     persist_state="session")
    _entran = _FILTROS.get(_filt or "Todas", (None, ""))[0]
    # Hoy son 5 filas del mismo periodo; en un año son 60 y la tabla deja de servir.
    # ⚠️ v574 · la opción «todos» es un ID interno (verif_v436: no se compara con un
    # texto traducido) y los periodos se leen DD/MM/YYYY (salían en ISO).
    _OPT_TODOS = "__todos__"
    _ids = {f"{d}|{h}": (d, h) for d, h in sorted({(str(x.get("PeriodFrom", "")),
                                                     str(x.get("PeriodTo", "")))
                                                    for x in noms}, reverse=True)}
    _sel = st.selectbox(t("Period"), [_OPT_TODOS] + list(_ids), key="nom_per_filt",
                        label_visibility="collapsed",
                        format_func=lambda o: t("All periods") if o == _OPT_TODOS else
                        f"{_dmy(_ids[o][0])} → {_dmy(_ids[o][1])}")
    _rows = [x for x in noms
             if (_entran is None or _estado(x) in _entran)
             and (_sel == _OPT_TODOS
                  or (str(x.get("PeriodFrom", "")), str(x.get("PeriodTo", ""))) == _ids.get(_sel))]
    _rows = sorted(_rows, key=lambda x: (str(x.get("PeriodTo", "")),
                                         str(x.get("Name", ""))), reverse=True)

    # ── Lo que la pantalla no decía ──────────────────────────────
    # (a) colillas de $0 porque esa persona no tenía tarifa/hora cuando se generó.
    #     ⚠️ Desde v346 ya NO se pueden crear (`generar` salta a quien no tiene tarifa),
    #     pero este aviso SE QUEDA: las de antes siguen en la hoja y hay que poder verlas
    #     para anularlas y regenerarlas una vez puesta la tarifa.
    _cero = sorted({str(x.get("Name", "")) for x in _rows if _estado(x) != "anulada"
                    and _num(x.get("Hours")) > 0 and _num(x.get("HourlyRate")) <= 0})
    if _cero:
        st.warning(t(":material/payments: **{n}** — hours worked but **zero base pay**: no hourly "
                     "rate. The payslip comes out at zero and the work does not count towards the cost.",
                     n=", ".join(_cero)))
        if st.button(t(":material/badge: Set rates in Users"), key="nom_ir_users"):
            from core import home_ui
            home_ui.navegar("planificacion", "👷 Usuarios")

    # (b) gente con horas en el periodo y SIN nómina. Es el hueco que el resumen
    #     financiero marca como «Horas sin nómina», pero aquí es donde se arregla.
    if _sel != _OPT_TODOS and _sel in _ids:
        _d, _h = _ids[_sel]
        try:
            from core import timeclock, auth
            from datetime import datetime as _dt
            _f = lambda s: _dt.strptime(str(s)[:10], "%Y-%m-%d").date()
            _hp = timeclock.jornada_y_proyecto(grupo, _f(_d), _f(_h))
            _con = {str(x.get("User", "")) for x in _rows if _estado(x) != "anulada"}
            # ⚠️ NO `_etq`: ese nombre es la función `i18n.etiqueta` a nivel de módulo,
            # y asignarlo aquí la tapa en TODA la función (v437/v439/v440, cuarta vez).
            _etu = auth.etiqueta_usuarios(auth.list_users(grupo))
            _falta = [(_etu.get(u, u), v) for u, v in _hp.items()
                      if u not in _con and (v["jornada"] > 0 or v["proyecto"] > 0)]
        except Exception:
            _falta = []
        if _falta:
            st.error(t(":material/person_alert: No payslip in this period despite having hours: {l}",
                       l=" · ".join(t("**{n}** ({j} h on shift / {p} h on jobs)", n=n,
                                      j=f"{v['jornada']:.1f}", p=f"{v['proyecto']:.1f}")
                                    for n, v in _falta)))

    if not _rows:
        st.caption(t("No payslips in this filter."))
        return

    # ── Tabla ────────────────────────────────────────────────────
    # ⚠️ El nombre PUEDE repetirse: `auth.etiqueta_usuarios` añade el login solo cuando
    # hace falta. ⚠️ v574 · UNA entrada por PERSONA: con una por colilla, quien tenía dos
    # contaba como dos homónimos y salía «ZZ Prueba nomina (zz_prueba_nomina)».
    from core import auth as _A
    _et = _A.etiqueta_usuarios(list({str(x.get("User", "")): {"User": x.get("User"), "Name": x.get("Name")}
                                     for x in noms}.values()))
    st.caption(t("Tap a payslip to see the detail, edit items and mark it paid."))
    _gen = st.session_state.get("_nom_tbl_gen", 0)
    # ⚠️ v574 · la persona FIJADA y lo que se mira primero delante (a 800 px el estado
    # quedaba fuera), dinero CON céntimos (salía «$321» por $320.78) y fechas DD/MM/YYYY.
    df = pd.DataFrame([{
        "Usuario":  _et.get(str(x.get("User", "")), str(x.get("Name", ""))),
        "Estado":   _est_celda(x),
        "Neto":     round(_num(x.get("Net")), 2),
        "Periodo":  _periodo(x),
        "Horas":    round(_num(x.get("Hours")), 1),
        "Base":     round(_num(x.get("Base")), 2),
        # ⚠️ Cadena vacía, NO NaN: un nulo se pinta «None» en gris (ver el cuadro
        # en `tabla.celda`), y el pie de ESTA tabla promete que un «Rate/h» vacío
        # significa que esa persona no tiene tarifa puesta. Decía «None».
        "Rate/h": (tabla.celda(x.get("HourlyRate"), 2, "$")
                     if _num(x.get("HourlyRate")) > 0 else ""),
    } for x in _rows])
    _ev = st.dataframe(
        df, width="stretch", hide_index=True,
        # v574 · un toque en cualquier celda abre la colilla (antes, solo la casilla)
        on_select="rerun", selection_mode="single-cell", key=f"nom_tbl_{_gen}",
        column_config=tabla.cfg(None, {"Usuario": st.column_config.TextColumn(t("Employee"), pinned=True),
                       "Estado": st.column_config.TextColumn(t("Status")),
                       "Periodo": st.column_config.TextColumn(t("Period")),
                       "Base": st.column_config.NumberColumn(t("Base pay"), format="$%,.2f"),
                       "Neto": st.column_config.NumberColumn(t("Net"), format="$%,.2f"),
                       "Rate/h": tabla.derecha(t("Rate/h"))}))
    _vv = [x for x in _rows if _estado(x) != "anulada"]
    st.caption(t("{n} payslip(s) · base pay {b} · net {nt} · voided ones do not count · an empty "
                 "«Rate/h» means that person has no rate set.", n=len(_rows),
                 b=T.dinero(sum(_num(x.get("Base")) for x in _vv), 2),
                 nt=T.dinero(sum(_num(x.get("Net")) for x in _vv), 2)))
    _s = getattr(_ev, "selection", None)
    _sr = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
    if _sr and 0 <= _sr[0] < len(_rows):
        # ⚠️ Otra generación de clave: soltar el estado del widget no llega al navegador
        # (trampa 31) y al volver la tabla reabriría la misma colilla.
        st.session_state["_nom_tbl_gen"] = _gen + 1
        st.session_state["_nom_open"] = str(_rows[_sr[0]].get("ID", ""))
        st.rerun()


def _generar(grupo):
    if st.button(t(":material/arrow_back: Cancel"), key="nom_gen_back"):
        st.session_state.pop("_nom_gen", None)
        st.rerun()
    st.markdown(t("## :material/add_circle: Generate payroll"))

    hoy = clock.today(grupo)
    # v574 · el SEGMENTADO del kit (`cpxseg_*`), como el resto de «una de N»
    per = st.radio(t("Frequency"), ["Semanal", "Quincenal", "Mensual", "Personalizado"],
                   format_func=lambda o: t({"Semanal": "Weekly", "Quincenal": "Fortnightly",
                                            "Mensual": "Monthly",
                                            "Personalizado": "Custom"}.get(o, o)),
                   horizontal=True, key="cpxseg_nom_per")
    _d0 = {"Semanal": hoy - timedelta(days=6), "Quincenal": hoy - timedelta(days=13),
           "Mensual": hoy - timedelta(days=29)}.get(per, hoy - timedelta(days=6))
    c1, c2 = st.columns(2)
    desde = c1.date_input(t("From"), value=_d0, key=f"nom_desde_{per}", format="DD/MM/YYYY")
    hasta = c2.date_input(t("To"), value=hoy, key=f"nom_hasta_{per}", format="DD/MM/YYYY")

    _sup = auth.group_num_setting(grupo, "DefaultSuper", 11.5)
    _ret = auth.group_num_setting(grupo, "DefaultWithholding", 0.0)
    c3, c4 = st.columns(2)
    sup = c3.number_input(t("Superannuation % (employer contribution)"), min_value=0.0, max_value=100.0,
                          value=float(_sup), step=0.5, key="nom_sup")
    ret = c4.number_input(t("Tax withholding % (deduction)"), min_value=0.0, max_value=100.0,
                          value=float(_ret), step=1.0, key="nom_ret")
    st.caption(t(":material/info: The super and withholding percentages come from the company and can be edited here and on each payslip. This is not a certified tax calculation; check the amounts."))

    horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)
    rates = auth.rate_map(grupo)
    if horas:
        st.markdown(t("**{n} user(s)** with workday hours in the period:", n=len(horas)))
        # ⚠️ v574 · quien no tiene tarifa se dice ANTES de generar (salía a $0 en la
        # vista previa y el aviso llegaba después, cuando ya se había saltado).
        _sin = sorted(str(v["nombre"]) for k, v in horas.items() if _num(rates.get(k, 0)) <= 0)
        if _sin:
            st.warning(t(":material/person_off: No hourly rate: **{l}** — they will be skipped "
                         "(their payslip would be zero). Set the rate first, or generate and add "
                         "them later: the same period takes them without duplicating.",
                         l=", ".join(_sin)))
            if st.button(t(":material/badge: Set rates in Users"), key="nom_gen_ir_users"):
                from core import home_ui
                home_ui.navegar("planificacion", "👷 Usuarios")
        # ⚠️ v574 · `$%,d` TRUNCA (trampa 20): una tarifa de $30.55 salía «$30». Céntimos.
        st.dataframe(pd.DataFrame([{
            "Usuario": v["nombre"], "Horas": round(v["horas"], 1),
            "Rate/h": round(_num(rates.get(k, 0)), 2),
            "Base": round(v["horas"] * _num(rates.get(k, 0)), 2),
            "Nota": _nota_tarifa(rates.get(k, 0)),
        } for k, v in sorted(horas.items())]), width="stretch", hide_index=True,
            column_config=tabla.cfg(None, {"Usuario": st.column_config.TextColumn(t("Employee")),
                           "Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f"),
                           "Base": st.column_config.NumberColumn(t("Base pay"), format="$%,.2f"),
                           "Nota": st.column_config.TextColumn(t("Note"))}))
    else:
        st.info(t("Nobody has workday hours in that period."))

    if st.button(t(":material/payments: Generate payslips"), type="primary", disabled=not horas,
                 key="nom_do"):
        res = payroll.generar(grupo, desde.isoformat(), hasta.isoformat(), sup, ret, _creado_por())
        if res.get("error"):
            st.error(res["error"])          # este SÍ se ve: no hay rerun detrás
            return
        # ⚠️ v365: los mensajes NO se pintan aquí. El `st.rerun()` de abajo descarta los
        # deltas del run en curso, así que se perdían TODOS. Van a `flash`, que los pinta
        # la shell del otro lado del rerun (mecanismo ÚNICO para toda la app).
        flash.exito(t("{n} payslip(s) created.", n=res.get("creadas", 0))
                    + ((" " + t("{n} already existed for that period.", n=res["omitidas"]))
                       if res.get("omitidas") else ""))
        # ⚠️ v346: ya NO se crea una colilla de $0. Se salta y se dice a quién, con el
        # camino para arreglarlo; al ponerle la tarifa y regenerar el mismo periodo
        # entra sin duplicar (no dejó fila).
        _st = res.get("sin_tarifa") or []
        if _st:
            flash.aviso(t(":material/person_off: **No payslip was generated for {l}**: they have no "
                          "hourly rate, so their payslip would come out at zero. Set the rate in "
                          ":material/build: Planning → Users and generate this same period again — "
                          "they will be included without duplicating.", l=", ".join(_st)))
        # ⚠️ v364: periodos que SOLAPAN con una nómina ya emitida. Se bloquea y se NOMBRA
        # la nómina que estorba, porque el error es invisible después.
        _sol = res.get("solapadas") or []
        if _sol:
            _líneas = "\n".join(t("- **{n}** already has `{i}` from {d} to {h}", n=s["nombre"],
                                  i=s["id"], d=_dmy(s["desde"]), h=_dmy(s["hasta"])) for s in _sol)
            flash.error(t(":material/event_repeat: **Nothing was generated** because the chosen "
                          "period overlaps payslips already issued — the same hours would be paid "
                          "twice:")
                        + "\n\n" + _líneas + "\n\n"
                        + t("Adjust the dates so they do not overlap, or void those payslips in "
                            "the list below and generate again."))
        # ⚠️ v432: días en que la persona tenía ausencia pagada Y además fichó. Un día
        # vale UNA jornada, así que la ausencia paga solo lo que falta — y se DICE.
        _rec = res.get("recortes") or []
        if _rec:
            _l = "\n".join(
                t("- **{n}** on {f}: clocked {c} h, so their absence pays {p} h (not the whole "
                  "working day)", n=r["nombre"], f=_dmy(r["fecha"]), c=f"{r['fichadas']:g}",
                  p=f"{r['pagadas']:g}")
                for r in _rec[:12])
            flash.info(t(":material/schedule: **Days with both an absence and a clock-in** — only "
                         "one working day is paid per day:") + "\n\n" + _l
                       + (("\n\n" + t("…and more.")) if len(_rec) > 12 else ""))
        st.session_state.pop("_nom_gen", None)
        st.rerun()


def _detalle(grupo, nid):
    if st.button(t(":material/arrow_back: Back to payroll"), key="nom_back"):
        st.session_state.pop("_nom_open", None)
        st.session_state.pop("_nom_conf", None)
        st.rerun()
    f = payroll.get_nomina(nid)
    if not f:
        st.warning(t("Payslip not found."))
        st.session_state.pop("_nom_open", None)
        return
    if not tenant.exigir(f, t("This payslip")):        # v351
        st.session_state.pop("_nom_open", None)
        return
    base = _num(f.get("Base"))
    est = _estado(f)
    # ⚠️ v309: dos importes en la misma línea → Streamlit lo renderizaba como LaTeX
    # (la tarifa y la base salían como fórmula). `theme.dinero` escapa el `$`.
    from core import theme as _T
    st.markdown(t("## :material/payments: Payslip — {n}", n=f.get("Name", "")))
    # ⚠️ v574 · fechas DD/MM/YYYY y el estado TRADUCIDO (decía «status: **emitida**»)
    st.markdown(t("Period **{p}** · {h} h × {r} = base pay **{b}** · {e}",
                  p=_periodo(f), h=f"{_num(f.get('Hours')):.1f}", r=_T.dinero(f.get("HourlyRate")),
                  b=_T.dinero(base), e=f"{_EST_ICONO.get(est, '')} {_etq(est)}".strip()))

    # ⚠️ v574 · arriba lo que se decide (neto, PDF, pagar/deshacer/anular) y los conceptos
    # a TODO el ancho: en la columna de 3/5 la tabla medía 601 px en 376 y el importe y el
    # tipo quedaban fuera de la vista.
    izq, der = st.columns([2, 3])
    with izq:
        st.metric(t("Net pay"), f"${_num(f.get('Net')):,.2f}")
        try:
            from core import payslip_pdf
            _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
            # v574 · «Payslip_», no «Colilla_» (el archivo lo recibe la persona)
            st.download_button(t(":material/download: Download payslip (PDF)"), data=_pdf,
                               file_name=f"Payslip_{f.get('Name', '')}_{f.get('PeriodTo', '')}.pdf",
                               mime="application/pdf", key=f"nom_pdf_{nid}")
        except Exception as e:
            st.caption(t(":material/warning: The PDF could not be generated: {e}", e=str(e)))
    with der:
        _conf = st.session_state.get("_nom_conf")
        if est == "anulada":
            st.info(t(":material/block: Voided: it is not paid and does not count towards the cost."))
        elif est == "pagada":
            st.success(t(":material/check_circle: Paid on {f}.", f=_dmy(f.get("PaymentDate"))))
            # ⚠️ v574 · «Mark as paid» por error no tenía vuelta atrás
            with st.expander(t(":material/undo: Undo payment"), key=f"exp_nom_desh_{nid}"):
                st.caption(t("Back to unpaid, e.g. if it was marked by mistake. A paid payslip "
                             "cannot be voided: undo the payment first."))
                if _conf == ("deshacer", nid):
                    st.warning(t("Undo the payment of this payslip?"))
                    _y, _k = st.columns(2)
                    if _y.button(t(":material/undo: Yes, undo it"), key=f"nom_desh_si_{nid}", type="primary"):
                        st.session_state.pop("_nom_conf", None)
                        st.session_state["_nom_accion"] = {"accion": "deshacer", "nid": nid}
                        st.rerun()
                    if _k.button(t("Keep it"), key=f"nom_desh_no_{nid}"):
                        st.session_state.pop("_nom_conf", None)
                        st.rerun()
                elif st.button(t("Undo the payment"), key=f"nom_desh_{nid}"):
                    st.session_state["_nom_conf"] = ("deshacer", nid)
                    st.rerun()
        else:
            with st.form(f"nom_pay_{nid}"):
                _fch = st.date_input(t("Payment date"), value=clock.today(grupo), format="DD/MM/YYYY")
                if st.form_submit_button(t(":material/check: Mark as paid"), type="primary"):
                    ok, msg = payroll.marcar_pagada(nid, _fch.isoformat())
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
            # ⚠️ v574 · PREGUNTA antes (un clic anulaba, sin aviso y sin vuelta atrás) y la
            # acción va diferida a `render_nominas` (trampa 37)
            with st.expander(t(":material/block: Void payslip"), key=f"exp_nom_anul_{nid}"):
                st.caption(t("It no longer counts as payroll to pay. This cannot be undone."))
                if _conf == ("anular", nid):
                    st.warning(t("Void this payslip? It cannot be undone."))
                    _y, _k = st.columns(2)
                    if _y.button(t(":material/block: Yes, void it"), key=f"nom_anul_si_{nid}", type="primary"):
                        st.session_state.pop("_nom_conf", None)
                        st.session_state["_nom_accion"] = {"accion": "anular", "nid": nid}
                        st.rerun()
                    if _k.button(t("Keep it"), key=f"nom_anul_no_{nid}"):
                        st.session_state.pop("_nom_conf", None)
                        st.rerun()
                elif st.button(t("Void this payslip"), key=f"nom_anul_{nid}"):
                    st.session_state["_nom_conf"] = ("anular", nid)
                    st.rerun()

    st.markdown(t("#### :material/list: Items (earnings, deductions, employer contributions)"))
    # ⚠️ v574 · el TIPO con su nombre (salía el valor interno «deduccion» / «aporte»); se
    # traduce para el editor y se devuelve al DATO al guardar.
    _TL = {"devengo": t("Earning"), "deduccion": t("Deduction"), "aporte": t("Employer contribution")}
    _inv = {v: k for k, v in _TL.items()}
    _cs = payroll.conceptos_de(f)
    _pre = [{"Concepto": c.get("concepto", ""),
             "Type": _TL.get(str(c.get("tipo", "deduccion")), str(c.get("tipo", ""))),
             "Monto": _num(c.get("monto"))} for c in _cs] or \
           [{"Concepto": "", "Type": _TL["deduccion"], "Monto": 0.0}]
    # Solo se edita una EMITIDA: cambiar los conceptos de una pagada movería un neto que
    # ya se pagó (v574).
    _editable = est == "emitida"
    _ed = st.data_editor(
        pd.DataFrame(_pre), num_rows="dynamic" if _editable else "fixed", width="stretch",
        key=f"nom_ed_{nid}", disabled=not _editable,
        column_config=tabla.cfg(None, {
            "Concepto": st.column_config.TextColumn(t("Item")),
            "Type": st.column_config.SelectboxColumn(t("Type"), options=list(_TL.values()),
                                                     required=True, width="medium"),
            "Monto": st.column_config.NumberColumn(t("Amount"), format="$%,.2f", min_value=0.0,
                                                   width="small"),
        }))
    if not _editable:
        st.caption(t(":material/lock: Paid or voided: the items can no longer be edited."))
    elif st.button(t(":material/save: Save items"), key=f"nom_save_{nid}"):
        conceptos = []
        for _, rr in _ed.iterrows():
            con = str(rr.get("Concepto", "")).strip()
            mon = _num(rr.get("Monto"))
            if not con and mon == 0:
                continue
            _tp = str(rr.get("Type", "") or "")
            conceptos.append({"concepto": con, "tipo": _inv.get(_tp, _tp or "deduccion"),
                              "monto": mon})
        ok, msg = payroll.update_conceptos(nid, conceptos)
        (flash.exito if ok else st.error)(msg)
        if ok:
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
    for f in sorted(noms, key=lambda x: str(x.get("PeriodTo", "")), reverse=True):
        with st.container(border=True):
            # v574 · DD/MM/YYYY (iban en ISO)
            st.markdown(f"**{_periodo(f)}**  ·  "
                        f"{_num(f.get('Hours')):.1f} h  ·  net **${_num(f.get('Net')):,.2f}**  ·  "
                        f"{_etq(str(f.get('Status', '')))}")
            try:
                from core import payslip_pdf
                _pdf = payslip_pdf.generate_payslip_pdf(f, grupo)
                st.download_button(t(":material/download: Download payslip"), data=_pdf,
                                   file_name=f"Payslip_{f.get('PeriodTo', '')}.pdf",
                                   mime="application/pdf", key=f"myp_{f.get('ID', '')}")
            except Exception as e:
                st.caption(str(e))
