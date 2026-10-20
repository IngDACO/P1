"""
UI de la pestaña de líneas de plomada (Streamlit).
Herramienta independiente del survey.
"""
import streamlit as st

from core.i18n import t, d
import pandas as pd

from core.plumb import compute_plumb, plumb_table, plumb_svg, plumb_iso_svg, plumb_detail_svg, plumb_card_svg
from core import plan_store
from core import plan_ui
from core import estado_vivo
from core.tool_pdf import tool_pdf
from core.tool_save_ui import render_guardar
from core import tool_save_ui
from core import tabla
from core import incrustar
from core import flash
from core import clock
from core import theme as T
from core.num import nombre_archivo as _archivo


def _lado(s) -> str:
    """v592 · «L»/«R» de los textos, dichos con palabras (decía «towards the L side»)."""
    return d("left") if str(s) == "L" else d("right") if str(s) == "R" else str(s or "")


def _encaje_txt(disp) -> str:
    """Resumen accionable del encaje de un elevador (para la tabla, el PDF y lo guardado).

    ⚠️ v592 · Texto LIMPIO: llevaba `:orange[:material/warning:]`, que una tabla no interpreta —
    salía literal en pantalla, en el PDF y en el cálculo guardado (visto en producción). La
    fila que no cabe se marca en rojo en la tabla de pantalla. Y UN decimal, como los avisos
    (la tabla decía «6 mm» y el aviso «6.5 mm»; «83 > 81» frente a «82.7 > 81.0»).
    """
    if not disp:
        return d("no shift (BSR = BS)")
    if disp.get("centrado"):
        return d("centred · clearance {x} mm/side", x=f"{disp.get('holgura_lado', 0):.1f}")
    if disp.get("fuera_rango"):
        return d("DOES NOT FIT · Omega {a} > limit {b}", a=f"{disp.get('omega_sacrificio', 0):.1f}",
                 b=f"{disp.get('limit_ob', 0):.1f}")
    return d("move {x} mm towards the {s}", x=f"{abs(disp.get('desp_conjunto', 0)):.1f}",
             s=_lado(disp.get("z_side", "")))


def _firma(*vals) -> tuple:
    """v592 · Las ENTRADAS de un cálculo, para saber si lo de pantalla sigue valiendo."""
    out = []
    for v in vals:
        if isinstance(v, (list, tuple)):
            out.append(tuple(round(float(x or 0), 3) for x in v))
        elif isinstance(v, (int, float)):
            out.append(round(float(v), 3))
        else:
            out.append(str(v))
    return tuple(out)


def _se_puede(bks, rail, tksw, lt, bs, bsr_list) -> bool:
    """⚠️ v594 · Sin datos no se calcula: con un BSR en 0 (un ascensor sin medir) la plomada
    calculaba igual y daba un replanteo sin sentido — como Rails (v593) y Buffers (v594). Si
    falta algo, lo dice, quita el resultado anterior y devuelve False."""
    _faltan = [x for x, v in (("BKS", bks), ("RAIL", rail), ("TKSW", tksw),
                              ("LengthTemplate", lt), ("BS", bs)) if float(v or 0) <= 0]
    _sin = [str(i + 1) for i, x in enumerate(bsr_list) if float(x or 0) <= 0]
    if _sin:
        _faltan.append(t("the BSR measured on lift {x}", x=", ".join(_sin)))
    if not _faltan:
        return True
    st.session_state.pop("plb_res_multi", None)
    st.warning(t(":material/edit: Fill in before calculating: {x}.", x=", ".join(_faltan)))
    return False


def render_plumb_tab():
    st.markdown(t("### :material/straighten: Plumb line calculation"))
    st.caption(t("One **template** for the shaft; the **BSR is measured per lift**. The values from the drawing fill themselves in; RAIL comes from the catalogue."))

    # ── Inicializar en 0 (BSR ya NO es global: se mide por elevador) ──
    _keys = ["plb_bks", "plb_rail", "plb_tksw", "plb_lt", "plb_sf1", "plb_sf2",
             "plb_bs", "plb_sg", "plb_tg"]
    for _k in _keys:
        st.session_state.setdefault(_k, 0.0)

    # Reabrir un calculo guardado: escribe claves de widget, va ANTES de crearlos (v111).
    _reab = tool_save_ui.aplicar_restauracion("plomada")
    if _reab:
        st.info(t(":material/replay: Reopened calculation **{x}**. Adjust whatever you need and "
                  "calculate again.", x=_reab))

    # ── Proyecto: el plano ya leído ──
    _prj, _plano = plan_ui.selector_proyecto("plb")
    _pr_base = str((_prj or {}).get("Name", "") or "")     # v179: el proyecto SÍ se conoce
    if _plano:
        plan_ui.aplicar(_plano, {
            "params.BKS": "plb_bks", "params.TKSW": "plb_tksw",
            "params.SF1": "plb_sf1", "params.SF2": "plb_sf2",
            "params.BS": "plb_bs", "params.SG": "plb_sg", "params.TG": "plb_tg",
            "rail_altura": "plb_rail"})   # RAIL = altura del diente, del catálogo
        # ⚠️ v592 · FIJO, como en el Survey (v591): «8 value(s) taken from the project drawing»
        # salía solo en la pasada que rellenaba y se iba al tocar cualquier otro campo.
        if _plano.get("params"):
            st.caption(t(":green[:material/check_circle:] The drawing fields come from the "
                         "project's drawing data. Check them and fill in the ones measured "
                         "on site."))

    with st.expander(t("Does the project have no drawing? Upload it here"), icon=":material/description:", key="exp_plb_plano"):
        st.caption(t("BKS, TKSW, SF1, SF2, BS, SG and TG will be read from this PDF."))
        pdf = plan_store.selector(":material/description: Drawing PDF (fills in from the drawing)", "plb_pdf")
        if pdf is not None and pdf.name != st.session_state.get("plb_pdf_name"):
            from extractors.schindler import extract_from_pdf
            with st.spinner(t("Reading the drawing...")):
                ex = extract_from_pdf(pdf)
            st.session_state["plb_pdf_name"] = pdf.name
            mapping = {"BKS": "plb_bks", "TKSW": "plb_tksw", "SF1": "plb_sf1", "SF2": "plb_sf2",
                       "BS": "plb_bs", "SG": "plb_sg", "TG": "plb_tg"}
            found = []
            for src, key in mapping.items():
                if ex.get(src) is not None:
                    st.session_state[key] = float(ex[src]); found.append(src)
            # ⚠️ v592 · Por `flash`: iban con `st.success`/`st.warning` justo antes del
            # `st.rerun()` y no los veía nadie.
            if found:
                flash.exito(t(":material/check_circle: From the drawing: **{x}**. Fill in "
                              "LengthTemplate; RAIL comes from the rail code; the BSR is measured "
                              "per lift.", x=", ".join(found)))
            else:
                flash.aviso(t("No values were found in the drawing. Enter them by hand."))
            st.rerun()
        elif pdf is not None:
            st.caption(t(":material/description: Drawing loaded: **{x}**", x=pdf.name))

    # ── Entradas COMPARTIDAS del shaft (la plantilla es una sola) ──
    # v592 · el mismo icono que llevan los campos (decía «✏️ = by hand» con otro lápiz)
    st.markdown(t("**Shaft template (shared)**  ·  :material/description: = from the drawing · "
                  ":material/edit: = by hand"))
    c1, c2, c3, c4 = st.columns(4)
    bks  = c1.number_input(t(":material/description: BKS (mm)"),            step=0.5, key="plb_bks")
    rail = c2.number_input(t(":material/description: RAIL (mm)"),           step=0.5, key="plb_rail")
    tksw = c3.number_input(t(":material/description: TKSW (mm)"),           step=0.5, key="plb_tksw")
    lt   = c4.number_input(t(":material/edit: LengthTemplate (mm)"), step=0.5, key="plb_lt")
    g1, g2, g3, _g4 = st.columns(4)
    sf1 = g1.number_input(t(":material/description: SF1 (mm)"), step=0.5, key="plb_sf1")
    sf2 = g2.number_input(t(":material/description: SF2 (mm)"), step=0.5, key="plb_sf2")
    bs  = g3.number_input(t(":material/description: BS (mm)"),  step=0.5, key="plb_bs")

    with st.expander(t("Fit data (SG, TG, Omega side) — used when a BSR < BS"), key="exp_plb_ajuste"):
        e1, e2, e3 = st.columns(3)
        sg    = e1.number_input(t(":material/description: SG (mm)"), step=0.5, key="plb_sg")
        tg    = e2.number_input(t(":material/description: TG (mm)"), step=0.5, key="plb_tg")
        omega = e3.radio(t(":material/edit: Omega side"), ["R", "L"], horizontal=True, key="plb_omega")

    # ── BSR por elevador (lo que varía entre huecos) ──
    st.markdown(t("**BSR measured on each lift (mm)**"))
    n = int(st.number_input(t("How many lifts are there in the shaft?"), min_value=1, max_value=12,
                            step=1, value=int(st.session_state.get("plb_n", 1)), key="plb_n"))
    base = st.session_state.get("plb_bsr_df")
    if base is None or len(base) != n:
        # ⚠️ v593 · Cambiar el nº de ascensores CONSERVA los BSR tecleados (antes la tabla
        # nacía entera en 0) y estrena la tabla editable (v542).
        _prev = [float(x or 0) for x in (list(base["BSR (mm)"]) if base is not None else [])]
        # v534 · «Elevador 1» salía en español; solo cambia lo que se lee (ver rail_cut_ui).
        base = pd.DataFrame({"Elevador": [t("Lift {n}", n=i + 1) for i in range(n)],
                             "BSR (mm)": (_prev + [0.0] * n)[:n]})
        if _prev:
            estado_vivo.tabla_nueva("plb")
    bsr_edit = st.data_editor(base, width="stretch", hide_index=True,
                              num_rows="fixed", disabled=["Elevador"],
                              # v540 · Clave con generación: al cambiar de obra, tabla nueva.
                              key=estado_vivo.clave_tabla("plb", "plb_bsr_editor"),
                              column_config=tabla.cfg())
    st.session_state["plb_bsr_df"] = bsr_edit
    bsr_list = [float(x or 0) for x in bsr_edit["BSR (mm)"].tolist()]
    _ahora = _firma(bks, rail, tksw, lt, sf1, sf2, bs, sg, tg, omega, n, bsr_list)

    if st.button(t(":material/straighten: Calculate plumb lines"), type="primary", width="stretch",
                 key="plb_calc") and _se_puede(bks, rail, tksw, lt, bs, bsr_list):
        st.session_state["plb_res_multi"] = {"n": n, "firma": _ahora, "results": [compute_plumb({
            "BKS": bks, "RAIL": rail, "TKSW": tksw, "LengthTemplate": lt,
            "SF1": sf1, "SF2": sf2, "BSR": b, "BS": bs,
            "SG": sg, "TG": tg, "OMEGA_SIDE": omega,
        }) for b in bsr_list]}

    data = st.session_state.get("plb_res_multi")
    if not data:
        return
    results, n = data["results"], data["n"]
    r0 = results[0]                       # la plantilla es la misma para todos
    # ⚠️ v592 · Lo de abajo es del ÚLTIMO cálculo: si un dato cambió después, se dice — y no
    # se descarga ni se guarda (se mezclarían las entradas nuevas con los resultados viejos:
    # visto en producción, plantilla 350 en pantalla y RW de la de 300).
    _vigente = data.get("firma") == _ahora
    if not _vigente:
        st.warning(t(":material/warning: You changed data since the last calculation. What is "
                     "below belongs to the previous one — press **Calculate plumb lines** to "
                     "update it."))

    def _et(i) -> str:
        """El ascensor del CÁLCULO («Lift 3 of 3»): la obra ya puede llamarse «… — Lift 1»."""
        return t("Lift {i} of {n}", i=i, n=n) if n > 1 else t("Lift {i}", i=i)

    def _nombre(i) -> str:
        """v592 · El cajetín: «Bondi Junction Tower — Lift 1 · lift 3 of 3» (decía «… Lift 1 · Lift 3»)."""
        suf = d("lift {i} of {n}", i=i, n=n) if n > 1 else ""
        return " · ".join(x for x in (_pr_base, suf) if x) or d("Lift {i}", i=i)

    # ── La plantilla (compartida, UNA vez) ──
    st.markdown(t("#### :material/architecture: The template (the same for every lift)"))
    # ⚠️ v592 · ACTIVAS (eran HTML): cada cifra lleva al dibujo donde se ve y se mide.
    _K = [("dbp", t("DBP"), f"{r0['dbp']:.1f}", t("between the plumb lines")),
          ("dbpw", t("DBPW"), f"{r0['dbpw']:.1f}", t("front wall → plumb")),
          ("rw", "RW", f"{r0['rw']:.1f}", t("front wall → template")),
          ("d1", "d1", f"{r0['d1']:.1f}", t("template → plumb C1")),
          ("d2", "d2", f"{r0['d2']:.1f}", t("template → plumb C2"))]
    st.markdown(T.por_fila("cpx_plb_kpis", 5), unsafe_allow_html=True)
    with st.container(key="cpx_plb_kpis"):
        for _col, (_s, _l, _v, _pie) in zip(st.columns(len(_K)), _K):
            if _col.button(f"{_l}\n\n{_v}\n\n{_pie}", key=f"cpxkpi_plb_{_s}", width="stretch",
                           help=t("See it on the drawing")):
                st.session_state["_bajar_cpx_plb_dibujo"] = True
                st.rerun()
    st.caption(t("DBP = spacing between the plumb points · d1/d2 = template→plumb diagonals (measured with a tape)."))

    _bs = r0.get("bs_check") or {}
    if _bs and not _bs.get("ok", True):
        st.error(t(":material/warning: **BS does not add up:** the drawing says **{a}** but "
                   "SF1+BKS+2·RAIL+SF2 = **{b}** (diff {c} mm). With this mismatch the plumb points "
                   "end up in the wrong place. Check BS, SF1, SF2, BKS or RAIL.",
                   a=f"{_bs['bs_plano']:.0f}", b=f"{_bs['bs_componentes']:.0f}",
                   c=f"{_bs['dif']:+.0f}"))

    # ── Tabla por elevador ──
    st.markdown(t("#### :material/elevator: Per lift — fit and check"))
    # ⚠️ v592 · La COMPROBACIÓN delante y el texto del encaje al final: a 1024 px «dd» y
    # «di+DBP+dd» quedaban fuera de la vista (la columna «Fit» se comía el ancho).
    _rows = []
    for i, r in enumerate(results):
        v = r.get("verif") or {}
        cierre = (r.get("cierre") or {}).get("suma", 0.0)
        _rows.append({
            d("Lift"): i + 1,
            "BSR (mm)": round(r.get("bsr", 0), 1),
            d("di (left wall→plumb)"): round(v.get("plomo_izq_pared_izq", 0), 1),
            d("dd (plumb→right wall)"): round(v.get("plomo_der_pared_der", 0), 1),
            "di+DBP+dd": round(cierre, 1),
            d("Fit"): _encaje_txt(r.get("displacement")),
        })
    # la fila del ascensor que NO cabe, en rojo (por su índice: el texto es dato)
    _mal = {i for i, r in enumerate(results) if (r.get("displacement") or {}).get("fuera_rango")}
    _df = pd.DataFrame(_rows)
    st.dataframe(
        _df.style.apply(lambda fila: (["color:#c0392b;font-weight:600"] * len(fila)
                                      if fila.name in _mal else [""] * len(fila)),
                        axis=1).format(precision=1),
        width="stretch", hide_index=True,
        column_config=tabla.cfg(None, {d("Lift"): st.column_config.NumberColumn(
            t("Lift"), format="%d", pinned=True)}))
    st.caption(t("On-site check: **di + DBP + dd = BSR**. If it does not add up, there is a measurement error."))

    # ── Diagramas de un elevador ──
    from core import projects_ui as _PU
    with st.container(key="cpx_plb_dibujo"):     # v592 · destino de las cifras de la plantilla
        _PU._bajar_a("cpx_plb_dibujo", "_bajar_cpx_plb_dibujo", bloque="start")
        st.markdown(t("#### :material/architecture: Diagrams for one lift"))
    sel = st.selectbox(t("View the setting out for lift"), list(range(1, n + 1)),
                       format_func=_et, key="plb_sel_e")
    r = results[sel - 1]
    _pr = _nombre(sel)

    disp = r.get("displacement")
    if disp and disp.get("centrado"):
        st.success(t("{l}: BSR > BS → the assembly is **centred** (clearance {x} mm/side).",
                     l=_et(sel), x=f"{disp['holgura_lado']:.1f}"))
    elif disp:
        if disp.get("fuera_rango"):
            # ⚠️ v592 · SOLO el aviso: debajo salía también «move the assembly 33.7 mm towards
            # the L side», una instrucción para algo que no cabe. Se dice cuánto falta y qué hacer.
            st.error(t(":material/warning: {l}: **DOES NOT FIT.** The shaft is {dif} mm narrower "
                       "than the drawing (BS − BSR): after {z} mm on the Z side, the Omega side would "
                       "have to give {o} mm and its limit is {lim} mm — **{f} mm short**. Re-measure "
                       "the BSR or review the fit with the office.",
                       l=_et(sel), dif=f"{disp['dif_bs']:.1f}", z=f"{disp['z_sacrificio']:.1f}",
                       o=f"{disp['omega_sacrificio']:.1f}", lim=f"{disp['limit_ob']:.1f}",
                       f=f"{disp['omega_sacrificio'] - disp['limit_ob']:.1f}"))
        else:
            st.info(t("{l}: BSR < BS → **move the assembly {x} mm towards the {s}** (the Omega "
                      "is on the {o}).", l=_et(sel), x=f"{abs(disp['desp_conjunto']):.1f}",
                      s=_lado(disp['z_side']), o=_lado(disp['omega_side'])))
        with st.expander(t("Fit detail (internal thresholds)")):
            st.caption(t("DIF = {a} · LIMIT_ZB = {b} · LIMIT_OB = {c} · Z give-up = {e} · "
                         "Omega give-up = {f}", a=f"{disp['dif_bs']:.1f}", b=f"{disp['limit_zb']:.1f}",
                         c=f"{disp['limit_ob']:.1f}", e=f"{disp['z_sacrificio']:.1f}",
                         f=f"{disp['omega_sacrificio']:.1f}"))
    else:
        st.success(t("{l}: BSR = BS → no shift.", l=_et(sel)))

    incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                    + plumb_svg(r, proyecto=_pr) + '</body></html>', 500)
    _v3d, _vfi = st.columns(2)
    with _v3d.expander(t("3D views of the setting out"), icon=":material/view_in_ar:", expanded=False):
        incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_iso_svg(r, proyecto=_pr) + '</body></html>', 650)
        incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_detail_svg(r, proyecto=_pr) + '</body></html>', 500)
    with _vfi.expander(t("Setting-out card (for site)"), icon=":material/assignment:", expanded=False):
        st.caption(t("The numbers to measure with a tape. Print it or open it on your phone."))
        incrustar.dibujo('<!DOCTYPE html><html><body style="margin:0;background:transparent">'
                        + plumb_card_svg(r, proyecto=_pr) + '</body></html>', 430)

    # ── PDF (con el nombre del proyecto) + guardar contra el proyecto ──
    _svgs = []
    for i, rr in enumerate(results):
        _lbl = _nombre(i + 1)
        _svgs.append(plumb_svg(rr, proyecto=_lbl))
        _svgs.append((plumb_card_svg(rr, proyecto=_lbl), 0.60))
    pdf_bytes = tool_pdf(
        d("Plumb setting-out"),
        meta={d("Project"): _pr_base or "—", d("Lifts"): str(n),
              "DBP": f"{r0['dbp']:.1f} mm", "DBPW": f"{r0['dbpw']:.1f} mm",
              "RW": f"{r0['rw']:.1f} mm", "d1 / d2": f"{r0['d1']:.1f} / {r0['d2']:.1f} mm"},
        svgs=_svgs,
        tablas=[(d("Per lift — fit and check"), _rows),
                (d("Template — line positions"), plumb_table(r0))],
        notas=[d("The template (DBP, d1, d2) is the same for the whole shaft; the BSR is measured "
                 "per lift and sets its fit and its check."),
               d("Site check: di + DBP + dd = BSR.")])
    render_guardar(herramienta="plomada", titulo_pdf=d("plumb setting-out"),
                   pdf_bytes=pdf_bytes,
                   resumen=(d("Template DBP {a} · d1 {b}/d2 {c} · {n} lift", a=f"{r0['dbp']:.1f}",
                              b=f"{r0['d1']:.1f}", c=f"{r0['d2']:.1f}", n=n) if n == 1 else
                            d("Template DBP {a} · d1 {b}/d2 {c} · {n} lifts", a=f"{r0['dbp']:.1f}",
                              b=f"{r0['d1']:.1f}", c=f"{r0['d2']:.1f}", n=n)),
                   datos={"n": n,
                          "plantilla": {k: r0.get(k) for k in ("dbp", "dbpw", "rw", "d1", "d2")},
                          "elevadores": _rows},
                   # v592 · con la obra y la fecha (todos se llamaban «plumb_setout.pdf»)
                   nombre_archivo=f"Plumb_setout_{_archivo(_pr_base, 'shaft')}_"
                                  f"{clock.today().strftime('%Y-%m-%d')}.pdf",
                   key="plb", obra_id=str((_prj or {}).get("ID", "")), vigente=_vigente)
