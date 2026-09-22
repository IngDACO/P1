# -*- coding: utf-8 -*-
"""El campo marca QUÉ hizo, no cuánto cree que va (v514).

Sustituye la rejilla de porcentajes por la lista de actividades reales de la obra. En
vez de estimar «¿cuánto va de Car Assembly?», se marca «instalé el sill de cabina» y el
porcentaje **sale solo**, ponderado por lo que pesa cada cosa.

## ⚠️ Por qué casillas y no porcentajes

Casi todas las actividades del catálogo son **binarias**: el bedplate del motor está
instalado o no lo está. Pedir un % por cada una en un móvil, con 143 de ellas, sería
peor que la rejilla que venimos a quitar.

Lo parcial —«8 puertas de 10»— llega con el parte diario en texto, donde el número está
en la frase y no hay que teclearlo en ningún sitio. Hasta entonces, media actividad
cuenta como no hecha: **quedarse corto es el error seguro**. Inflar el avance mueve una
reclamación (v507/v510); quedarse corto solo la retrasa.

## ⚠️ Un guardado por ETAPA, no por clic

Marcar una casilla no escribe. Cada guardado es un lote contra Sheets y el techo son 60
lecturas/min (la lección de v511): con 143 casillas, escribir a cada clic sería un 429
garantizado a media obra.
"""
import streamlit as st

from core import flash
from core import stage_progress as SP
from core.i18n import t
from core.num import num as _num


def _color(pct) -> str:
    p = _num(pct)
    return ":green" if p >= 100 else (":orange" if p > 0 else ":gray")


def render(pid, grupo, prj, editable=True, key_prefix="sp"):
    """Las etapas de la obra con sus actividades. `False` si esta obra no usa el
    catálogo — quien llama decide qué pintar entonces (la rejilla de siempre)."""
    if not SP.is_configured():
        return False
    try:
        _det = SP.detalle(pid, prj)
    except Exception as e:
        # ⚠️ Nunca tumba la pantalla del campo: sin esto, un fallo leyendo el catálogo
        # dejaría al técnico sin poder reportar nada en toda la obra.
        st.caption(t("The stage list is unavailable right now ({e}).", e=e))
        return False
    if not _det:
        return False

    # ⚠️ Si el catálogo cambió desde que nació la obra, se AVISA y se deja en solo
    # lectura: acreditar contra otro menú colgaría el trabajo de la etapa equivocada.
    _vieja = SP.version_desfasada(prj)
    if _vieja:
        st.warning(t(":material/warning: This job was planned with an older stage "
                     "catalogue ({v}), so progress cannot be credited until it is "
                     "migrated.", v=_vieja))
        editable = False

    _hechas = sum(1 for e in _det for a in e["actividades"] if _num(a["pct"]) >= 100)
    _total = sum(len(e["actividades"]) for e in _det)
    st.markdown(t("#### What has been done — {h} of {n} activities",
                  h=_hechas, n=_total))
    st.caption(t("Tick what is finished. The stage percentage works itself out from "
                 "what each activity is worth."))

    _quien = st.session_state.get("auth", {}).get("usuario", "")
    for e in _det:
        _pct = _num(e["pct"])
        _n_ok = sum(1 for a in e["actividades"] if _num(a["pct"]) >= 100)
        _tit = "%s **%d · %s** — %.0f%% (%d/%d)" % (
            _color(_pct) + "[:material/" +
            ("check_circle" if _pct >= 100 else "radio_button_unchecked") + ":]",
            e["orden"], e["nombre"], _pct, _n_ok, len(e["actividades"]))
        with st.expander(_tit, expanded=False):
            st.progress(min(1.0, _pct / 100.0))
            _marcas = {}
            for i, a in enumerate(e["actividades"]):
                _k = "%s_%s_%d_%d" % (key_prefix, pid, e["orden"], i)
                _marcas[a["nombre"]] = st.checkbox(
                    "%s  ·  %.1f%%" % (a["nombre"], _num(a["peso_en_etapa"])),
                    value=_num(a["pct"]) >= 100, key=_k, disabled=not editable)
            if not editable:
                continue
            if st.button(t(":material/save: Save stage {n}", n=e["orden"]),
                         key="%s_save_%s_%d" % (key_prefix, pid, e["orden"]),
                         width="stretch"):
                # ⚠️ Solo lo que CAMBIÓ. Reescribir las 24 filas de una etapa en cada
                # guardado es gastar cuota y arriesgarse a pisar lo que otro acaba de
                # marcar (el criterio del guardado parcial de v499/v502).
                _cambios = [{"etapa": e["orden"], "actividad": a["nombre"],
                             "pct": 100.0 if _marcas[a["nombre"]] else 0.0}
                            for a in e["actividades"]
                            if (_num(a["pct"]) >= 100) != _marcas[a["nombre"]]]
                if not _cambios:
                    st.info(t("Nothing changed in this stage."))
                else:
                    ok, msg = SP.acreditar(pid, grupo, prj, _cambios, quien=_quien)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()
    return True
