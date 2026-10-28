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

# ⚠️ v616 · Lo marcado SIN GUARDAR, aparte de las casillas: `{"orden|actividad": bool}` por obra.
# Una casilla deja de existir en cuanto se cambia de pestaña o de etapa, y con ella lo marcado:
# medido en producción, se marcó «Install cabin doors», se fue a «Daily log» y al volver estaba
# desmarcada — sin un solo aviso. Aquí sobrevive mientras dure la sesión, y se ve.
_PEND = "_sp_pend"


def _clave_pend(kp, pid) -> str:
    return f"{_PEND}_{kp}_{pid}"


def pendientes(kp, pid) -> dict:
    """Lo marcado sin guardar en esa obra (lo usa también la cabecera de la obra del campo)."""
    return st.session_state.get(_clave_pend(kp, pid)) or {}


def _apuntar(kp, pid, orden, nombre, k, guardado) -> None:
    """on_change de cada casilla: apunta el cambio, o lo quita si vuelve a lo guardado."""
    d = st.session_state.setdefault(_clave_pend(kp, pid), {})
    v, ck = bool(st.session_state.get(k)), f"{orden}|{nombre}"
    if v == bool(guardado):
        d.pop(ck, None)
    else:
        d[ck] = v


def _nombre(login) -> str:
    """El NOMBRE de una persona (v559). Sin nombre, el login."""
    _u = str(login or "")
    try:
        from core import auth
        return auth.etiqueta_usuarios(auth.list_users()).get(_u, _u)
    except Exception:
        return _u


def _dmy(iso) -> str:
    s = str(iso or "")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
    return s


def _ayuda(cred, orden, nombre, pct):
    """v616 · El «?» de una casilla acreditada: QUIÉN, el DÍA del trabajo y, si vino de un parte,
    cuál (decisión del usuario). En un «?» y no en una línea: la lista de una etapa ya tiene 24
    casillas en el móvil."""
    if _num(pct) < 100:
        return None
    r = cred.get((int(orden), str(nombre)))
    if not r:
        return None
    _txt = t("Credited by {q} · {d}", q=_nombre(r.get("UpdatedBy")),
             d=_dmy(r.get("WorkDate") or r.get("Updated")))
    if str(r.get("Source", "")) == SP.PARTE and str(r.get("Note", "")).strip():
        _txt += " — " + t("from daily log {l}", l=str(r.get("Note")).strip())
    return _txt


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
    # ── v616 · lo marcado sin guardar: se tira lo que ya es verdad en la hoja (lo guardó otro, o
    # se guardó desde otra etapa) y se dice cuánto queda, con un «Save all» de UNA escritura ──
    _pend = st.session_state.setdefault(_clave_pend(key_prefix, pid), {})
    _guardado = {f"{e['orden']}|{a['nombre']}": _num(a["pct"]) >= 100
                 for e in _det for a in list(e["actividades"]) + list(e.get("informativas") or [])}
    for _ck in list(_pend):
        if _ck not in _guardado or _pend[_ck] == _guardado[_ck]:
            _pend.pop(_ck, None)
    if _pend and editable:
        st.warning(t(":material/edit_note: **{n} unsaved ticks.** They stay while you move around "
                     "this job, but they only count once saved.", n=len(_pend)))
        if st.button(t(":material/save: Save all ({n})", n=len(_pend)),
                     key="%s_save_all_%s" % (key_prefix, pid), type="primary", width="stretch"):
            _todos = [{"etapa": int(ck.split("|", 1)[0]), "actividad": ck.split("|", 1)[1],
                       "pct": 100.0 if v else 0.0} for ck, v in _pend.items()]
            with st.spinner(t("Saving…")):
                ok, msg = SP.acreditar(pid, grupo, prj, _todos, quien=_quien)
            (flash.exito if ok else st.error)(msg)
            if ok:
                _pend.clear()
                st.rerun()
    # v616 · quién y cuándo, para el «?» de cada casilla acreditada (la última fila de cada
    # actividad, como `stage_progress._mapa`: el texto cuenta lo mismo que la casilla)
    try:
        _cred = {(int(_num(r.get("StageOrder"))), str(r.get("Activity", ""))): r
                 for r in SP.creditos(pid)}
    except Exception:
        _cred = {}
    for e in _det:
        _pct = _num(e["pct"])
        _n_ok = sum(1 for a in e["actividades"] if _num(a["pct"]) >= 100)
        _n_pend = sum(1 for ck in _pend if ck.split("|", 1)[0] == str(e["orden"]))
        _tit = "%s **%d · %s** — %.0f%% (%d/%d)" % (
            _color(_pct) + "[:material/" +
            ("check_circle" if _pct >= 100 else "radio_button_unchecked") + ":]",
            e["orden"], e["nombre"], _pct, _n_ok, len(e["actividades"]))
        if _n_pend and editable:
            _tit += " · :orange[" + t("{n} unsaved", n=_n_pend) + "]"
        with st.expander(_tit, expanded=False, key="%s_exp_%s_%d" % (key_prefix, pid, e["orden"])):
            st.progress(min(1.0, _pct / 100.0))
            _marcas = {}
            for i, a in enumerate(e["actividades"]):
                _k = "%s_%s_%d_%d" % (key_prefix, pid, e["orden"], i)
                _sv = _num(a["pct"]) >= 100
                _marcas[a["nombre"]] = st.checkbox(
                    "%s  ·  %.1f%%" % (a["nombre"], _num(a["peso_en_etapa"])),
                    value=_pend.get(f"{e['orden']}|{a['nombre']}", _sv), key=_k,
                    disabled=not editable, help=_ayuda(_cred, e["orden"], a["nombre"], a["pct"]),
                    on_change=_apuntar, args=(key_prefix, pid, e["orden"], a["nombre"], _k, _sv))
            # ⚠️ v519 · Las INFORMATIVAS: se marcan, no cuentan (decisión del usuario).
            # Van DEBAJO y SIN porcentaje, con el aviso dicho: una casilla sin peso al
            # lado de las que pesan, sin decir nada, haría creer que marcarla sube la
            # etapa — y quien la marca esperando que suba acaba desconfiando del número.
            _info = e.get("informativas") or []
            if _info:
                st.caption(t(":material/info: For the record only — ticking these does "
                             "not change the progress."))
                for j, a in enumerate(_info):
                    _k = "%s_%s_%d_i%d" % (key_prefix, pid, e["orden"], j)
                    _sv = _num(a["pct"]) >= 100
                    _marcas[a["nombre"]] = st.checkbox(
                        a["nombre"], value=_pend.get(f"{e['orden']}|{a['nombre']}", _sv), key=_k,
                        disabled=not editable, help=_ayuda(_cred, e["orden"], a["nombre"], a["pct"]),
                        on_change=_apuntar, args=(key_prefix, pid, e["orden"], a["nombre"], _k, _sv))
            if not editable:
                continue
            # v616 · con cambios sin guardar, el botón lo dice y se resalta
            if st.button(t(":material/save: Save stage {n} ({c} changes)", n=e["orden"], c=_n_pend)
                         if _n_pend else t(":material/save: Save stage {n}", n=e["orden"]),
                         key="%s_save_%s_%d" % (key_prefix, pid, e["orden"]),
                         type="primary" if _n_pend else "secondary", width="stretch"):
                # ⚠️ Solo lo que CAMBIÓ. Reescribir las 24 filas de una etapa en cada
                # guardado es gastar cuota y arriesgarse a pisar lo que otro acaba de
                # marcar (el criterio del guardado parcial de v499/v502).
                _cambios = [{"etapa": e["orden"], "actividad": a["nombre"],
                             "pct": 100.0 if _marcas[a["nombre"]] else 0.0}
                            for a in list(e["actividades"]) + list(_info)
                            if (_num(a["pct"]) >= 100) != _marcas[a["nombre"]]]
                if not _cambios:
                    st.info(t("Nothing changed in this stage."))
                else:
                    # ⚠️ v528 · Se VE que está guardando: medido en producción, unos segundos
                    # con la pantalla quieta hacían creer que el clic no había entrado.
                    with st.spinner(t("Saving stage {n}…", n=e["orden"])):
                        ok, msg = SP.acreditar(pid, grupo, prj, _cambios, quien=_quien)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        # v616 · lo de ESTA etapa ya está guardado: fuera de lo pendiente
                        for _ck in [ck for ck in _pend if ck.split("|", 1)[0] == str(e["orden"])]:
                            _pend.pop(_ck, None)
                        st.rerun()
    return True
