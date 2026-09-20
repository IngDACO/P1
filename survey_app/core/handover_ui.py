# -*- coding: utf-8 -*-
"""Expediente de entrega: la pantalla y el recolector de hechos (v506).

`core/handover.py` es puro y no busca nada. Aquí se reúne el contexto de la obra desde
las hojas que ya están cacheadas y se pinta el resultado.

⚠️ El texto de la pantalla dice lo que el expediente ES: el registro del instalador con
sus huecos señalados, **no** un certificado. Prometer cumplimiento en la interfaz sería
la forma más rápida de meter a un cliente en un problema.
"""
import json

import streamlit as st

from core import flash
from core import handover as H
from core import projects as P
from core.i18n import t


def _params(prj) -> dict:
    try:
        return json.loads(prj.get("ParamsJSON", "") or "{}") or {}
    except Exception:
        return {}


def contexto(pid, grupo, prj) -> dict:
    """Los hechos de la obra, reunidos de lo que ya está cacheado.

    ⚠️ Cada fuente va en su propio `try`: el expediente es justo la pantalla que se abre
    cuando algo va mal, así que una hoja caída tiene que restarle un dato, no tumbarla.
    """
    _p = _params(prj)
    try:
        _mx = json.loads(prj.get("MatrixJSON", "") or "[]") or []
    except Exception:
        _mx = []

    acts = []
    try:
        acts = P.list_activities(pid) or []
    except Exception:
        pass

    # Pre-starts: `Attendees` trae el LOGIN de cada asistente; un invitado o
    # subcontratista lo trae vacío y no se le exige certificado propio.
    prestarts = []
    try:
        from core import prestart as PS
        if PS.is_configured():
            for r in (PS.list_prestarts(pid) or []):
                try:
                    _a = json.loads(r.get("Attendees", "") or "[]") or []
                except Exception:
                    _a = []
                prestarts.append({"Date": r.get("Date", ""),
                                  "Attendees": [str(x.get("usuario", "") or "").strip()
                                                for x in _a if isinstance(x, dict)
                                                and str(x.get("usuario", "") or "").strip()]})
    except Exception:
        pass

    # Quién trabajó de verdad aquí, con su último día
    trabajaron = {}
    try:
        from core import timeclock as TC
        _nom = str(prj.get("Name", "") or "")
        for r in (P._fichajes_visibles(grupo) or []):
            if not TC.es_del_proyecto(r, pid, _nom):
                continue
            _u = str(r.get("User", "") or "").strip()
            _d = str(r.get("Clock In", "") or "")[:10]
            if _u and _d:
                trabajaron[_u] = max(trabajaron.get(_u, ""), _d)
    except Exception:
        pass

    # Credenciales de esa gente: {login: [vencimiento, …]}
    creds = {}
    try:
        from core import credentials as CR
        if CR.is_configured():
            for c in (CR.list_group(grupo) or []):
                _u = str(c.get("User", "") or "").strip()
                if _u:
                    creds.setdefault(_u, []).append(c.get("ExpiryDate", ""))
    except Exception:
        pass

    # Documentos subidos contra un ítem del expediente
    docs = {}
    try:
        for d in (P.list_documents(pid) or []):
            _it = str(d.get("HandoverItem", "") or "").strip()
            if _it:
                docs[_it] = str(d.get("Name", "") or "")
    except Exception:
        pass

    return {
        "params": _p, "matrix": _mx,
        # La plomada se calcula del survey: si hay `LengthTemplate`, se midió.
        "plumb_ok": bool(P._num(_p.get("LengthTemplate"))),
        "acts": acts, "prestarts": prestarts,
        "trabajaron": trabajaron, "credenciales": creds, "docs": docs,
        "asignados": [x.strip() for x in str(prj.get("FieldAssigned", "")).split(";") if x.strip()],
    }


_ICONO = {H.OK: ":green[:material/check_circle:]",
          H.PARCIAL: ":orange[:material/pending:]",
          H.FALTA: ":red[:material/cancel:]"}


def render(pid, grupo, prj, editable=True, key_prefix="ho"):
    """Sección «Handover file» del detalle de la obra."""
    ctx = contexto(pid, grupo, prj)
    filas = H.estado(ctx)
    res = H.resumen(filas)
    malos = H.incoherencias(ctx)

    _tit = t("Handover file — {ok} of {n} items on file", ok=res["ok"], n=res["total"])
    with st.expander(f":material/inventory: {_tit}", expanded=False):
        st.caption(t("What this company has to keep for five years, gathered here with the "
                     "gaps flagged. ⚠️ This is **not** a compliance certificate: the "
                     "certifier's, the electrical and the Safe-to-Operate certificates are "
                     "issued by third parties."))

        c1, c2, c3 = st.columns(3)
        c1.metric(t("On file"), res["ok"])
        c2.metric(t("Partial"), res["parcial"])
        c3.metric(t("Missing"), res["falta"])

        # ⚠️ Los cruces van ARRIBA: una contradicción entre dos datos que sí tenemos es
        # más grave que un documento que aún no ha llegado, y es lo único que nadie más
        # puede decir. Enterrarla bajo la tabla sería desperdiciarla.
        if malos:
            st.markdown(t("**:material/warning: What does not add up**"))
            for m in malos:
                st.warning(":material/priority_high: " + m["texto"])

        st.markdown(t("**The thirteen items**"))
        for f in filas:
            _org = t("we can evidence it") if f["fuente"] == H.COPEX else t("third party")
            st.markdown("%s **(%s)** %s — %s  \n&nbsp;&nbsp;&nbsp;:gray[%s · %s]"
                        % (_ICONO[f["estado"]], f["letra"], f["nombre"],
                           f["detalle"], _org, f.get("nota", "") or _org),
                        unsafe_allow_html=True)

        _faltan = [f for f in filas if f["fuente"] == H.TERCERO and f["estado"] != H.OK]
        if editable and _faltan:
            st.markdown(t("**Attach a third-party document**"))
            with st.form(f"{key_prefix}_up_{pid}"):
                _op = {f["nombre"]: f["clave"] for f in _faltan}
                _sel = st.selectbox(t("Which item does it evidence?"), list(_op.keys()))
                _fh = st.file_uploader(t("File"), key=f"{key_prefix}_file_{pid}")
                if st.form_submit_button(t(":material/upload: Attach"), width="stretch"):
                    if not _fh:
                        st.error(t("Choose a file first."))
                    else:
                        ok, msg = _subir(pid, _fh, _op[_sel])
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()

        st.caption(t("Generating the full file with every document embedded comes next; "
                     "for now this is the index and what is missing."))


def _subir(pid, fh, item) -> tuple:
    """Sube el documento a Drive y lo registra contra su ítem del expediente."""
    try:
        from core import drive_store as DS
        did = DS.upload(pid, fh.name, fh.getvalue(), fh.type or "application/octet-stream")
        if not did:
            return False, t("The file could not be uploaded to Drive.")
        return P.add_document(pid, fh.name, "certificado", did,
                              st.session_state.get("auth", {}).get("usuario", ""),
                              handover_item=item)
    except Exception as e:
        return False, "%s: %s" % (t("Error attaching the document"), e)
