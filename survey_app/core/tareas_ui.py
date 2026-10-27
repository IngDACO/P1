# -*- coding: utf-8 -*-
"""La lista de pendientes de una obra, en pantalla (v615). Los datos, en `core/tareas.py`.

La misma pantalla para el campo («My projects» → «To-do») y para la oficina (detalle de la obra →
«To-do»); cambia solo quién puede borrar (`gestor`: admin o propietario borra cualquiera; el campo,
las que escribió). Marcar y desmarcar, cualquiera de la obra (decisión del usuario).

⚠️ ACCIÓN DIFERIDA (trampa 37): la caja, las casillas y «Delete» solo APUNTAN lo pedido; se hace
arriba, en `_atender`, antes de pintar la lista, y se relanza. Escribir en la hoja desde dentro de
una lista con claves y relanzar desde ahí es lo que deja bloques fantasma en Streamlit 1.64.
"""
import logging

import streamlit as st

from core import flash, tareas as T, theme
from core.i18n import t
from core.maps import literal_md

logger = logging.getLogger(__name__)

_PET = "_td_pet"           # lo que pidió la pantalla: alta / marcar / borrar
_GEN = "_td_gen"           # generación de la caja de alta: sube al guardar → nace vacía (v602)
_MAX_HECHAS = 30           # las hechas que se pintan (las más recientes); el resto se cuenta


def _nombre(login) -> str:
    """El NOMBRE de una persona (v559: el login no se enseña). Sin nombre, el login."""
    _u = str(login or "")
    try:
        from core import auth
        return auth.etiqueta_usuarios(auth.list_users()).get(_u, _u)
    except Exception:
        return _u


def _dmy(iso) -> str:
    """«2026-10-28 09:15:02» → «28/10/2026» (las fechas, DD/MM/YYYY en toda la app, v584)."""
    s = str(iso or "")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
    return s


def _clave_gen(kp, pid) -> str:
    return f"{_GEN}_{kp}_{pid}"


def _clave_alta(kp, pid) -> str:
    return f"{kp}_td_new_{pid}_{int(st.session_state.get(_clave_gen(kp, pid), 0))}"


def _pedir_alta(kp, pid) -> None:
    st.session_state[_PET] = {"accion": "alta", "pid": str(pid), "kp": kp,
                              "texto": str(st.session_state.get(_clave_alta(kp, pid)) or "")}


def _pedir_marcar(pid, tid, clave) -> None:
    st.session_state[_PET] = {"accion": "marcar", "pid": str(pid), "tid": str(tid),
                              "hecho": bool(st.session_state.get(clave))}


def _pedir_borrar(kp, pid) -> None:
    st.session_state[_PET] = {"accion": "borrar", "pid": str(pid),
                              "tid": st.session_state.get(f"{kp}_td_del_{pid}")}


def _atender(pid, grupo, usuario, gestor) -> None:
    """Lo pedido, ANTES de pintar (trampa 37). ⚠️ Una petición de OTRA obra (se cambió de obra
    con algo a medias) se tira: nunca se aplica a la obra que se está viendo."""
    pet = st.session_state.pop(_PET, None)
    if not pet or str(pet.get("pid")) != str(pid):
        return
    with st.spinner(t("Saving…")):
        if pet["accion"] == "alta":
            ok, r = T.crear(pid, grupo, pet.get("texto"), usuario)
            if ok:
                _k = _clave_gen(pet.get("kp"), pid)
                st.session_state[_k] = int(st.session_state.get(_k, 0)) + 1   # la caja nace vacía
                flash.exito(t("Task added."))
            else:
                # ⚠️ Lo escrito SE QUEDA (misma generación): quien lo tecleó lo corrige, no lo
                # vuelve a escribir.
                flash.error(r)
        elif pet["accion"] == "marcar":
            # Marcar no avisa: la tarea cambia de sitio delante de quien la tocó, ese es el aviso.
            ok, r = T.marcar(pet.get("tid"), pid, pet.get("hecho"), usuario)
            if not ok:
                flash.error(r)
        elif not pet.get("tid"):
            flash.aviso(t("Choose the task to delete first."))
        else:
            ok, r = T.borrar(pet["tid"], pid, usuario, gestor)
            (flash.exito if ok else flash.error)(r)
    st.rerun()


def render(pid, grupo, usuario, gestor=False, key_prefix="fld") -> None:
    """La lista de pendientes de la obra `pid`. `gestor`: admin o propietario (borra cualquiera)."""
    _atender(pid, grupo, usuario, gestor)
    kp = key_prefix
    theme.section(t("To-do"), t("What is still pending on this job. Anyone on the job can tick it off."))
    if not T.is_configured():
        st.warning(t("The to-do list needs Google Sheets configured."))
        return

    # ── Apuntar: Enter o el botón (un formulario: escribir y SOLTAR la caja no envía nada) ──
    with st.form(f"{kp}_td_form_{pid}", border=False):
        st.text_input(t("New task"), key=_clave_alta(kp, pid), max_chars=T.MAX_TEXTO,
                      placeholder=t("e.g. Pick up the landing door keys"),
                      label_visibility="collapsed")
        st.form_submit_button(t(":material/add: Add to the list"), key=f"{kp}_td_add_{pid}",
                              on_click=_pedir_alta, args=(kp, pid), type="primary")

    _p, _h = T.pendientes(pid), T.hechas(pid)
    if not _p and not _h:
        st.caption(t("Nothing on the list yet. Write the first task above."))
        return
    st.caption(t("{p} pending · {h} done", p=len(_p), h=len(_h)))
    if not _p:
        st.caption(t(":material/task_alt: Nothing pending."))
    for r in _p:
        _tid = str(r.get("ID", ""))
        _c = f"{kp}_tdp_{pid}_{_tid}"
        # ⚠️ El texto lo escribe una persona: escapado (un «*» o un «$» lo convertiría en cursiva
        # o en una fórmula — medido en v603).
        st.checkbox(literal_md(r.get("Text", "")), value=False, key=_c,
                    on_change=_pedir_marcar, args=(pid, _tid, _c))
        st.caption(t("Added by {q} · {d}", q=_nombre(r.get("CreatedBy")), d=_dmy(r.get("Created"))))

    if _h:
        # ⚠️ Con clave (trampa 35): con controles dentro, sin ella se cierra solo con cada aviso. Y
        # con «exp» en ella: el convenio de la app para las claves de desplegable (verif_v547).
        with st.expander(t("Done ({n})", n=len(_h)), icon=":material/task_alt:",
                         key=f"{kp}_td_exp_hechas_{pid}"):
            for r in _h[:_MAX_HECHAS]:
                _tid = str(r.get("ID", ""))
                _c = f"{kp}_tdd_{pid}_{_tid}"
                st.checkbox("~~" + literal_md(r.get("Text", "")) + "~~", value=True, key=_c,
                            on_change=_pedir_marcar, args=(pid, _tid, _c))
                _da = str(r.get("DoneAt", ""))
                st.caption(t("Done by {q} · {d}", q=_nombre(r.get("DoneBy")),
                             d=_dmy(_da) + (" " + _da[11:16] if len(_da) >= 16 else "")))
            if len(_h) > _MAX_HECHAS:
                st.caption(t("…and {n} older ones.", n=len(_h) - _MAX_HECHAS))

    # ── Quitar una de la lista: elegirla Y pulsar (dos gestos a propósito: no es un toque suelto) ──
    _mias = [r for r in _p + _h if T.puede_borrar(r, usuario, gestor)]
    if _mias:
        with st.expander(t("Delete a task"), icon=":material/delete:", key=f"{kp}_td_exp_del_{pid}"):
            # Las opciones de un selectbox NO interpretan markdown (trampa 24): el texto, tal cual.
            _opc = {str(r.get("ID", "")): ("✓ " if T.hecha(r) else "") + str(r.get("Text", ""))
                    for r in _mias}
            st.selectbox(t("Task"), list(_opc), index=None, key=f"{kp}_td_del_{pid}",
                         format_func=lambda i: _opc.get(i, i),
                         placeholder=t("— choose the task —"))
            st.button(t(":material/delete: Delete"), key=f"{kp}_td_delb_{pid}",
                      on_click=_pedir_borrar, args=(kp, pid))
            st.caption(t("The office can delete any task.") if gestor else
                       t("You can delete the tasks you wrote. The office can delete any."))
