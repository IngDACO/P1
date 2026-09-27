# -*- coding: utf-8 -*-
"""El parte diario en pantalla: escribirlo (campo) y leerlo (admin) — v516.

⚠️ Esto se escribe en un MÓVIL, de pie, al final de la jornada. Lo que decide si se usa
o no es cuántos toques hay entre abrir la obra y haber guardado. Así que: una caja de
texto y un botón. Sin fecha que elegir (es hoy), sin categoría, sin adjuntos.

⚠️ La fecha se puede cambiar, pero está ESCONDIDA detrás de un desplegable cerrado. El
caso normal —escribo hoy lo de hoy— no paga el precio de un widget más, y el caso raro
—ayer no hubo cobertura— sigue siendo posible. Poner el selector siempre visible habría
invitado a tocarlo, y un parte con fecha equivocada es peor que uno sin fecha.
"""
import logging

import streamlit as st

from core import clock, daily_log as DL, flash, theme
from core.i18n import t

logger = logging.getLogger(__name__)


def _linea(r, puede_borrar, key_prefix) -> None:
    """Un parte ya guardado: quién, cuándo y qué escribió."""
    _autor = str(r.get("Author", "") or "—")
    _dia = str(r.get("Date", "") or "")
    _creado = str(r.get("Created", "") or "")
    # ⚠️ La hora solo se enseña si NO coincide con el día: «23/09 · 18:40» informa, pero
    # repetir la fecha dos veces en una línea de móvil solo gasta ancho.
    # ⚠️ Recortada a `hh:mm`: `Created` guarda SEGUNDOS para poder ordenar dos partes del
    # mismo minuto (ver `daily_log.partes`), pero a quien lee no le dicen nada.
    _hora = _creado[11:16] if _creado[:10] == _dia and len(_creado) >= 16 else _creado
    st.markdown(
        theme.chip(f"{_dia} · {_autor}" + (f" · {_hora}" if _hora else ""),
                   color=theme.GRIS_TXT),
        unsafe_allow_html=True)
    st.markdown(str(r.get("Text", "")))
    if puede_borrar:
        if st.button(t(":material/delete: Delete"), key=f"{key_prefix}_del_{r.get('ID')}",
                     type="tertiary"):
            ok, msg = DL.borrar(r.get("ID"), _autor)
            (flash.exito if ok else flash.error)(msg)
            st.rerun()
    st.divider()


def render_campo(pid, grupo, usuario, key_prefix="fld") -> None:
    """Lo que ve y usa quien está en la obra."""
    theme.section(t("Daily log"),
                  t("Write what you did today, in your own words."))

    _k = f"{key_prefix}_dl_txt_{pid}"
    _kf = f"{key_prefix}_dl_dia_{pid}"
    _hoy = clock.today(grupo)

    txt = st.text_area(
        t("What did you do today?"), key=_k, height=140,
        placeholder=t("e.g. Finished the bedplates on levels 3 and 4. Started running "
                      "the shaft wiring. Waiting on the landing door frames."),
        label_visibility="collapsed")

    # ⚠️ El contador solo aparece cuando ya se acerca al tope: enseñarlo desde el
    # carácter uno es ruido y le dice a quien escribe que hay un examen de longitud.
    if len(txt or "") > DL.MAX_TEXTO * 0.8:
        st.caption(t("{n} of {max} characters.", n=len(txt), max=DL.MAX_TEXTO))

    with st.expander(t("It is not for today"), icon=":material/event:"):
        dia = st.date_input(t("Day being reported"), value=_hoy, max_value=_hoy,
                            key=_kf, format="DD/MM/YYYY")
    if st.button(t(":material/save: Save the daily log"), key=f"{key_prefix}_dl_save_{pid}",
                 type="primary", width="stretch"):
        ok, msg = DL.crear(pid, grupo, txt, usuario, dia=dia)
        if ok:
            # ⚠️ La caja SOLO se vacía cuando la hoja confirmó. Si falla, el texto sigue
            # ahí: quien acaba de escribir doscientas palabras en un sótano no las
            # vuelve a escribir, deja de usar la pantalla (ver la nota de `daily_log`).
            st.session_state.pop(_k, None)
            flash.exito(t("Daily log saved."))
            st.rerun()
        else:
            st.error(msg)

    _mios = DL.partes(pid)
    if not _mios:
        st.caption(t("No daily logs yet for this job."))
        return
    st.markdown("")
    st.caption(t("{n} logs · {d} days covered", n=len(_mios),
                 d=DL.dias_cubiertos(pid)))
    _hoy_txt = _hoy.strftime("%Y-%m-%d")
    for r in _mios[:10]:
        # Borrar solo lo PROPIO y solo lo de hoy — el módulo lo vuelve a comprobar;
        # aquí es para no ofrecer un botón que va a decir que no (v499).
        _puede = (str(r.get("Author", "")) == str(usuario)
                  and str(r.get("Date", "")) == _hoy_txt)
        _linea(r, _puede, key_prefix)
    if len(_mios) > 10:
        st.caption(t("…and {n} older ones.", n=len(_mios) - 10))


def render_admin(pid, grupo, key_prefix="adm") -> None:
    """Lo que ve quien lleva la obra desde la oficina. Solo lectura: el parte es de
    quien lo escribió, y un admin corrigiéndolo destruiría lo único que lo hace valer."""
    _p = DL.partes(pid)
    theme.section(t("Daily logs"),
                  t("What the crew reported, in their own words."))
    if not _p:
        st.caption(t("The crew has not written any daily log for this job yet."))
        return
    st.caption(t("{n} logs · {d} days covered", n=len(_p), d=DL.dias_cubiertos(pid)))
    for r in _p[:25]:
        _linea(r, False, key_prefix)
    if len(_p) > 25:
        st.caption(t("…and {n} older ones.", n=len(_p) - 25))
