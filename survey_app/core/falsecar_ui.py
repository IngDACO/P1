# -*- coding: utf-8 -*-
"""El Daily False Car Checklist, en pantalla (v636). Los datos, en `core/falsecar.py`.

Vive dentro de la sección Pre-Start, y solo aparece en las obras creadas con false car: es el
mismo gesto de cada mañana, en la misma pantalla, sin añadir nada al menú. La firma, el lienzo y
las iniciales son los del Pre-Start (`prestart_ui`), para que haya una sola definición de firmar.
"""
import logging

import streamlit as st

from core import clock, falsecar as FC, flash
from core.i18n import t
from core.maps import literal_md
from core.num import dmy

logger = logging.getLogger(__name__)

_MAX_HIST = 10             # los que se ven de entrada; el resto, con un botón
# v637 · En una pantalla estrecha, el texto a todo el ancho y ✓/X con Remarks en UNA fila: apilados,
# los 18 puntos medían 4416 px en un teléfono. Mide el CONTENEDOR, como `theme.dos_por_fila`.
_CSS_PUNTOS = ("<style>.st-key-cpx_fc_puntos{container-type:inline-size}@container (max-width:700px){"
               ".st-key-cpx_fc_puntos [data-testid='stHorizontalBlock']{flex-wrap:wrap!important}"
               ".st-key-cpx_fc_puntos [data-testid='stColumn']:nth-child(1)"
               "{flex:0 0 100%!important;min-width:100%!important;width:100%!important}"
               ".st-key-cpx_fc_puntos [data-testid='stColumn']:nth-child(2)"
               "{flex:0 0 96px!important;min-width:96px!important;width:96px!important}"
               ".st-key-cpx_fc_puntos [data-testid='stColumn']:nth-child(3)"
               "{flex:1 1 0!important;min-width:0!important;width:auto!important}}</style>")


def _no_usar(fallos) -> None:
    """⚠️ Decisión del usuario: con una X, la pantalla dice que no se use. La app no puede parar la
    máquina, pero tampoco puede dejar pasar el dato como si nada."""
    st.error(t(":material/dangerous: **Do not use the false car until it is fixed.** Items marked "
               "X: {n}.", n=", ".join(str(p["n"]) for p in fallos)))


def _boton_pdf(d, clave, etiqueta=None) -> None:
    """Con la descarga DIFERIDA, como el Pre-Start (v623): con los bytes, cada fila del historial
    bajaría su PDF de Drive al pintar la pantalla."""
    _did = str(d.get("drive_id") or "").strip()
    if not _did:
        return
    from core import drive_store
    st.download_button(etiqueta or t(":material/download: PDF"),
                       data=lambda: drive_store.download(_did),
                       file_name=d.get("archivo") or f"{d.get('id')}.pdf", mime="application/pdf",
                       key=clave, on_click="ignore")


def _tarjeta_hecho(d, pid, firmado) -> None:
    with st.container(border=True):
        st.markdown(t(":material/check_circle: **This job already has the checklist for that day and "
                      "you are already on it.**") if firmado else
                    t(":material/check_circle: **This job already has the checklist for that day.**"))
        st.caption(f"{d['id']} · {d['hora']} · {t('Signed by')}: "
                   + ", ".join(literal_md(n) for n in d["firmas"]))
        if d["fallos"]:
            _no_usar(d["fallos"])
        _boton_pdf(d, f"fc_hoy_pdf_{pid}", t(":material/download: Download PDF"))


def _bloque_firmar(d, pid, grupo, nombre, usuario) -> None:
    """Hecho por otro: se firma, no se rehace (decisión del usuario, como el Pre-Start)."""
    from core.prestart_ui import _LIENZO, _canvas_disponible, _firma_png, _initials
    with st.container(border=True):
        st.markdown(t(":material/draw: **Today's check is already recorded — sign it**"))
        st.caption(f"{d['id']} · {d['hora']} · {t('Signed by')}: "
                   + ", ".join(literal_md(n) for n in d["firmas"]))
        if d["fallos"]:
            _no_usar(d["fallos"])
        c1, c2 = st.columns([1, 2])
        ini = c1.text_input(t("Initial"), value=_initials(nombre), key=f"fc_tarde_ini_{pid}")
        firma, st_canvas = None, _canvas_disponible()
        with c2:
            if st_canvas is not None:
                st.caption(t("Sign here"))
                firma = _firma_png(st_canvas(key=f"fc_firma_tarde_{pid}", **_LIENZO))
            else:
                st.caption(t("No canvas available: the typed initials are recorded instead."))
        if st.button(t(":material/draw: Sign the checklist"), key=f"fc_tarde_ok_{pid}", type="primary"):
            if st_canvas is not None and not firma:
                st.error(t("Draw your signature before sending it."))
            elif not str(ini or "").strip():
                st.error(t("Enter at least your initials."))
            else:
                r = FC.firmar(d["id"], grupo, nombre, ini, firma, usuario)
                if not r.get("ok"):
                    st.error(r.get("error") or t("Could not sign."))
                else:
                    if r.get("archivado"):
                        flash.exito(t("Signed. Your signature was added to {i} as an annex sheet, "
                                      "without touching the original.", i=d["id"]))
                    else:
                        flash.aviso(t("Your signature is on record for {i}, but the PDF could not be "
                                      "updated. Tell your administrator.", i=d["id"]))
                    st.rerun()


def _resultado(r) -> None:
    """Lo que dejó el último envío. Vive en la sesión, como el Pre-Start (v623)."""
    st.success(t(":material/check_circle: Checklist **{i}** saved as `{f}`.", i=r["id"], f=r["filename"]))
    if not r.get("drive_id"):
        st.caption(t(":orange[:material/warning:] It was not filed to Drive (check the connection); the record was saved."))
    if r.get("fallos"):
        _no_usar([{"n": n} for n in r["fallos"]])
        if r.get("alarma"):
            st.warning(t(":material/cancel: A project alert was opened. The administrator has been notified."))
        else:
            st.error(t(":material/error: The alert could NOT be opened. Tell your administrator now."))
    st.download_button(t(":material/download: Download PDF"), data=r["pdf"], file_name=r["filename"],
                       mime="application/pdf", width="stretch", key=f"fc_dl_{r['id']}", on_click="ignore")


def _marcar_todo(kp) -> None:
    """✓ en los puntos SIN responder (decisión del usuario, v638). ⚠️ Una X no se pisa: una alarma no
    puede borrarse con un toque general. Se ASIGNA, y antes de pintar: es lo que llega al navegador
    (trampa 31), y como `on_click` no lo corta el lienzo de la firma al montarse (trampa 39)."""
    for k, _x in FC.CHECKS:
        if st.session_state.get(f"fc_res_{kp}_{k}") is None:
            st.session_state[f"fc_res_{kp}_{k}"] = FC.PASA


def _formulario(prj, pid, grupo, dia, nombre, usuario, gestor) -> None:
    from core.prestart_ui import _LIENZO, _canvas_disponible, _firma_png, _initials
    # ⚠️ Con la obra, el día y una generación en la clave (v623): sin eso, las respuestas y la firma
    # pasarían de una obra a otra, y vaciarlas no llega al navegador (trampa 31).
    _gen = int(st.session_state.get(f"_fc_gen_{pid}", 0))
    kp = f"{pid}_{dia.isoformat()}_{_gen}"
    # Sin respuesta por defecto (v158): es una revisión, no una firma. El botón no cambia eso: el
    # formulario nace vacío, marcar es un gesto de quien revisa y lo que respalda es su firma (v638).
    st.caption(t("Answer every item: ✓ if it passes, X if it does not. With X, the remarks are required."))
    # `disabled` y no ocultarlo: que no salte lo que hay debajo del dedo.
    st.button(t(":material/done_all: Mark all as passed"), key=f"fc_todo_{kp}", width="stretch",
              on_click=_marcar_todo, args=(kp,),
              disabled=not any(st.session_state.get(f"fc_res_{kp}_{k}") is None for k, _x in FC.CHECKS))
    resultados = {}
    st.markdown(_CSS_PUNTOS, unsafe_allow_html=True)
    with st.container(key="cpx_fc_puntos"):
        for n, (k, texto) in enumerate(FC.CHECKS, 1):
            c1, c2, c3 = st.columns([5, 2, 3])
            c1.markdown(f"**{n}.** " + literal_md(texto).replace("\n", "  \n"))
            _res = c2.radio(t("Inspection results"), [FC.PASA, FC.FALLA], index=None, horizontal=True,
                            format_func=FC.SIMBOLO.get, key=f"fc_res_{kp}_{k}",
                            label_visibility="collapsed")
            _nota = c3.text_input(t("Remarks"), key=f"fc_nota_{kp}_{k}", label_visibility="collapsed",
                                  placeholder=t("Remarks"), max_chars=200)
            resultados[k] = {"res": _res, "nota": str(_nota or "").strip()}

    st.markdown("---")
    st.markdown(t("**Name of person conducting daily check:** {n}", n=literal_md(nombre)))
    st.markdown(t("**Date of Daily Check:** {d}", d=dmy(dia)))
    firma, ini, st_canvas = None, _initials(nombre), _canvas_disponible()
    if st_canvas is not None:
        st.caption(t("Signature"))
        firma = _firma_png(st_canvas(key=f"fc_firma_{kp}", **_LIENZO))
    else:
        ini = st.text_input(t("Initial"), value=ini, key=f"fc_ini_{kp}")

    _falta = FC.valida(resultados)
    if not _falta and st_canvas is not None and not firma:
        _falta = t("Draw your signature before sending it.")
    if _falta:
        st.caption(t("Still to complete") + ": " + _falta)
    if st.button(t(":material/verified: Generate and file checklist"), type="primary", width="stretch",
                 key=f"fc_submit_{kp}", disabled=bool(_falta)):
        with st.spinner(t("Generating the PDF and filing it…")):
            res = FC.submit({"grupo": grupo, "proyecto_id": pid, "proyecto_nombre": prj.get("Name", ""),
                             "fecha": dia, "hora": clock.now(grupo).strftime("%H:%M"),
                             "resultados": resultados, "nombre": nombre, "iniciales": ini,
                             "firma": firma, "usuario": usuario, "gestor": gestor})
        if not res["ok"]:
            st.error(res["error"] or t("The checklist could not be saved."))
        else:
            st.session_state[f"_fc_res_{pid}"] = {**res, "dia": clock.today(grupo).isoformat(),
                                                  "fecha": dia.isoformat()}
            st.session_state[f"_fc_gen_{pid}"] = _gen + 1
            st.rerun()


def _historial(pid) -> None:
    prev = [FC.leer(r) for r in FC.de_obra(pid)]
    st.markdown("---")
    st.markdown(t("#### :material/account_tree: Previous checklists"))
    if not prev:
        st.caption(t("No checklists recorded on this project yet."))
        return
    _tk = f"_fc_hist_todas_{pid}"
    for d in (prev if st.session_state.get(_tk) else prev[:_MAX_HIST]):
        _flag = ":red[:material/cancel:]" if d["fallos"] else ":green[:material/check_circle:]"
        _tit = (f"{_flag}  {dmy(d['fecha'])} · " + literal_md(", ".join(d["firmas"]) or "—")
                + (t("  ·  {n} marked X", n=len(d["fallos"])) if d["fallos"] else t("  ·  all OK")))
        with st.expander(_tit, key=f"exp_fc_hist_{d['id']}"):
            for p in d["puntos"]:
                _e = FC.SIMBOLO.get(p["res"], "—")
                st.markdown(f"`{_e}` **{p['n']}.** " + literal_md(p["texto"]).replace("\n", " ")
                            + (f"  \n_{literal_md(p['nota'])}_" if p["nota"] else ""))
            _boton_pdf(d, f"fc_hdl_{d['id']}")
    if len(prev) > _MAX_HIST and not st.session_state.get(_tk):
        if st.button(t("Show the {n} older ones", n=len(prev) - _MAX_HIST), key=f"fc_hist_mas_{pid}"):
            st.session_state[_tk] = True
            st.rerun()


def render(prj, grupo, rol, usuario, nombre, dia_pedido=None) -> None:
    """El checklist de esa obra. Solo se llama en obras con false car. `dia_pedido`: el día tocado
    en la lista de días sin registro."""
    pid = str(prj.get("ID", ""))
    st.markdown(t("### :material/verified: Daily False Car Checklist"))
    st.caption(t("Daily inspections are to be carried out according to the following schedule."))
    gestor = rol != "field"
    hoy = clock.today(grupo)
    # La oficina puede ponerse al día con un día pasado; el campo registra el de hoy (como el Pre-Start).
    # ⚠️ El día pedido con OTRA clave: asignar sobre una fecha ya pintada avisa, y sin asignar no llega
    # al navegador (trampa 31).
    if dia_pedido:
        st.session_state[f"_fc_fgen_{pid}"] = int(st.session_state.get(f"_fc_fgen_{pid}", 0)) + 1
    _fg = int(st.session_state.get(f"_fc_fgen_{pid}", 0))
    if dia_pedido:
        st.session_state[f"_fc_dia_{pid}_{_fg}"] = dia_pedido
    dia = (st.date_input(t("Date"), value=st.session_state.get(f"_fc_dia_{pid}_{_fg}", hoy), max_value=hoy,
                         key=f"fc_fecha_{pid}_{_fg}", format="DD/MM/YYYY") if gestor else hoy)

    _r = st.session_state.get(f"_fc_res_{pid}")
    # ⚠️ v637 · El aviso es de SU día: con otro elegido, decía «saved» encima de un formulario vacío.
    if _r and (_r.get("dia") != hoy.isoformat() or _r.get("fecha") != dia.isoformat()):
        _r = None
    if _r:
        _resultado(_r)

    d = FC.del_dia(pid, dia)
    if d:
        _pf = FC.pendiente_de_firma(pid, grupo, nombre, usuario) if dia == hoy else {}
        if _pf:
            _bloque_firmar(_pf, pid, grupo, nombre, usuario)
        elif not _r:
            _tarjeta_hecho(d, pid, firmado=dia == hoy)
    elif FC.activo(prj, dia):
        _formulario(prj, pid, grupo, dia, nombre, usuario, gestor)
    else:
        st.info(t(":material/info: The false car is not recorded as installed on that day. It is "
                  "required from when **Install sky climber** is ticked in the job's progress until "
                  "it is marked as removed."))
    _historial(pid)


def faltantes(grupo) -> None:
    """Días con gente fichada y sin su Pre-Start o su checklist (decisión del usuario): lo que
    pediría un inspector. ⚠️ Tocar una fila elige esa obra aquí mismo, para ponerse al día."""
    filas = FC.dias_sin_registro(grupo)
    _doc = {"prestart": t("Pre-Start"), "falsecar": t("False car check")}
    with st.expander(t("Days worked with no record, last 30 days ({n})", n=len(filas)),
                     icon=":material/rule:", key="exp_ps_faltantes"):
        if not filas:
            st.caption(t(":material/check_circle: Every day worked has its records."))
            return
        import pandas as pd
        from core import tabla
        from core.projects_ui import _etq_us
        _nom = _etq_us(sorted({u for f in filas for u in f["usuarios"]}))
        _gk = "_ps_falt_gen"
        _ev = st.dataframe(pd.DataFrame([{
            "Date": dmy(f["fecha"]), "Project": f["nombre"],
            "Missing": " · ".join(_doc[x] for x in f["falta"]),
            "Who": ", ".join(_nom.get(u, u) for u in f["usuarios"])} for f in filas]),
            hide_index=True, width="stretch", on_select="rerun", selection_mode="single-cell",
            key=f"ps_faltantes_{st.session_state.get(_gk, 0)}", column_config=tabla.cfg())
        st.caption(t(":material/touch_app: Tap a row to open that project here and catch up that day."))
        # ⚠️ La selección sobrevive en el widget: otra generación de clave tras usarla (v568).
        _s = getattr(_ev, "selection", None)
        _f = [c[0] for c in (getattr(_s, "cells", None) or [])] or list(getattr(_s, "rows", None) or [])
        if _f and 0 <= _f[0] < len(filas):
            _x = filas[_f[0]]
            st.session_state[_gk] = st.session_state.get(_gk, 0) + 1
            st.session_state["_ps_proy_pending"] = _x["pid"]
            st.session_state["_ps_dia_pending"] = _x["fecha"]
            st.session_state["_bajar_cpx_ps_obra"] = True
            # Si faltan los dos, primero la charla (decisión del usuario).
            if _x["falta"] == ["falsecar"]:
                st.session_state["_ps_doc_pending"] = "falsecar"
            st.rerun()
