"""
Bloque compartido "descargar + guardar en el proyecto" para las herramientas.

Las cuatro herramientas de cálculo lo usan igual, así que vive aquí en vez de
copiarse cuatro veces (y desviarse cuatro veces).

Flujo: elegir proyecto → descargar el PDF → guardarlo contra el proyecto
(`toolruns.registrar`, que escribe en la hoja Calculos y archiva en Drive).
"""
import streamlit as st

from core.i18n import t

from core import estado_vivo
from core import projects as P
from core import toolruns

# Prefijo de las claves de session_state de cada herramienta. Sirve para
# fotografiar sus entradas sin enumerarlas a mano (asi las claves dinamicas,
# como `belt_hgpr_3`, entran solas).
_PREFIJO = {"plomada": "plb_", "rieles": "rc_", "buffers": "bc_", "belting": "belt_"}
_PENDIENTE = "_toolrestore"

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— choose the project —"


def _proyectos_de(rol, usuario, grupo):
    """Mismo criterio que el Pre-Start: cada rol ve lo suyo."""
    if rol == "owner":
        return P.list_projects()
    if rol == "administrator":
        return P.list_projects(grupo=grupo)
    return P.list_projects_for_field(usuario, grupo=grupo)


def _restaurable(clave) -> bool:
    """¿Se puede guardar y volver a poner esta clave? Solo las ENTRADAS y las tablas (`*_df`).

    ⚠️ v534 · Antes se guardaba todo lo que empezara por el prefijo y fuera un valor
    simple — incluido el BOTÓN de calcular (`rc_calc1`, que vale True/False). Al reabrir
    el cálculo se le asignaba ese valor y Streamlit tumbaba la pantalla: «Values for the
    widget with key 'rc_calc1' cannot be set using st.session_state». Reabrir un cálculo
    no funcionaba en ninguna de las cuatro herramientas. El filtro va también al
    RESTAURAR, porque los cálculos ya guardados traen el botón dentro.
    """
    k = str(clave)
    return estado_vivo.es_entrada(k) or k.endswith("_df")


def _snapshot(herramienta: str) -> dict:
    """Entradas actuales de la herramienta, en algo serializable a JSON.

    Se recogen por PREFIJO de clave en vez de enumerarlas: asi las que se crean
    sobre la marcha (`belt_hgpr_2`) entran sin mantener una lista aparte.
    Los `st.data_editor` se saltan (clave `*_editor`) porque su contenido ya vive
    en el `*_df` que la herramienta guarda al lado, y ese NO es clave de widget:
    restaurarlo es seguro (regla v111).
    """
    pref = _PREFIJO.get(herramienta)
    if not pref:
        return {}
    out = {}
    for k, v in st.session_state.items():
        if not str(k).startswith(pref) or not _restaurable(k):
            continue
        if v is None or isinstance(v, (int, float, str, bool)):
            out[k] = v
        elif hasattr(v, "to_dict"):                 # DataFrame (matrices)
            try:
                out[k] = {"__df__": v.to_dict(orient="records")}
            except Exception:
                pass
    return out


def aplicar_restauracion(herramienta: str) -> str:
    """Vuelca las entradas de un calculo que se pidio reabrir. Devuelve su ID.

    ⚠️ HAY QUE LLAMARLA ANTES DE CREAR NINGUN WIDGET de la herramienta: escribe
    claves de widget y Streamlit prohibe tocarlas una vez instanciadas (v111).
    """
    pend = st.session_state.get(_PENDIENTE)
    if not pend or pend.get("herramienta") != herramienta:
        return ""
    st.session_state.pop(_PENDIENTE, None)
    import pandas as _pd
    # v534 · Estos valores se cargan A PROPÓSITO: que la herramienta no los olvide al
    # pintarse aunque la última vez estuviera con otra obra. ⚠️ v539 · Y son de la obra
    # del cálculo: elegirla luego en el selector ya no los borra.
    estado_vivo.respetar(_PREFIJO.get(herramienta, "").rstrip("_"), pend.get("obra", ""))
    for k, v in (pend.get("valores") or {}).items():
        if not _restaurable(k):
            continue
        try:
            if isinstance(v, dict) and "__df__" in v:
                st.session_state[k] = _pd.DataFrame(v["__df__"])
            else:
                st.session_state[k] = v
        except Exception:
            pass
    # ⚠️ v592 · Y su OBRA en el selector de arriba: reabría con «— no project —» (visto en
    # producción con CAL-0003 de PRJ-0026), y sin obra los diagramas y el PDF salían sin
    # nombre y guardar de nuevo había que buscarla. Va antes del selector (las cuatro
    # herramientas llaman a esto primero), así que se puede asignar su clave.
    _obra = str(pend.get("obra", "") or "")
    if _obra:
        try:
            _p = P.get_project(_obra)
            if _p:
                st.session_state["pl_prj_" + _PREFIJO.get(herramienta, "").rstrip("_")] = (
                    f"{_p.get('Name')} ({_p.get('ID')})")
        except Exception:
            pass
    return str(pend.get("id", ""))


def pedir_reapertura(fila, herramienta: str, sub_herramienta: str) -> bool:
    """Deja pendiente reabrir este calculo y navega a su herramienta.

    v299: `sub_herramienta` es el ID de la sub-pestaña dentro de 🛠 Herramientas
    (p. ej. "🔩 Plomada"), no la etiqueta de la nav vieja — esa nav se borró y su
    `_nav_pending` ya no lo lee nadie. El salto va por `_admin_nav_pending`, que
    `home_ui._aplicar_nav_pending` aplica ANTES de instanciar los menús (regla v111).
    """
    vals = toolruns.entradas_de(fila)
    if not vals:
        return False
    st.session_state[_PENDIENTE] = {"herramienta": herramienta, "valores": vals,
                                    "id": str(fila.get("ID", "")),
                                    "obra": str(fila.get("ProjectID", "") or "")}
    st.session_state["_admin_nav_pending"] = ("herramientas", sub_herramienta)
    return True


def _firma(resumen, datos) -> str:
    """Huella de UN cálculo (sus resultados): para saber si ya se guardó (v592)."""
    import hashlib
    import json
    try:
        s = json.dumps([resumen, datos], sort_keys=True, default=str)
    except Exception:
        s = repr((resumen, datos))
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def render_guardar(herramienta: str, titulo_pdf: str, pdf_bytes: bytes,
                   resumen: str, datos: dict, nombre_archivo: str,
                   key: str, obra_id: str = "", vigente: bool = True) -> None:
    """Descarga del PDF + guardado contra un proyecto.

    `herramienta` es la clave de `toolruns.HERRAMIENTAS`. Junto a los resultados
    se guardan las ENTRADAS (`_snapshot`), que es lo que permite reabrirlo luego.

    v592 · `obra_id` = la obra elegida ARRIBA en la herramienta: el destino viene con ella
    y solo se ofrecen instalaciones abiertas (como el Survey en v590). `vigente=False` = los
    datos cambiaron tras el último cálculo: ni se descarga ni se guarda (se mezclarían las
    entradas nuevas con los resultados viejos).
    """
    if not pdf_bytes:
        return

    st.markdown("---")
    if not vigente:
        st.caption(t(":material/lock: Recalculate to download or save it: the data changed "
                     "after the last calculation."))
        return
    c1, c2 = st.columns([1, 1])
    c1.download_button(t(":material/download: Download {x} (PDF)", x=titulo_pdf), data=pdf_bytes,
                       file_name=nombre_archivo, mime="application/pdf",
                       width="stretch", key=f"dl_{key}")

    if not toolruns.is_configured():
        c2.caption(t(":material/lock: Saving to the project needs Google Sheets configured."))
        return

    a = st.session_state.get("auth", {}) or {}
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    grupo = a.get("grupo", "")
    nombre = a.get("nombre") or usuario
    proys = _proyectos_de(rol, usuario, grupo)
    # ⚠️ v592 · Solo obras donde la herramienta tiene sentido (el filtro del selector de arriba,
    # `plan_ui.es_de_herramientas`) y la elegida: salían las 9, con entregas y una CANCELADA.
    obra_id = str(obra_id or "")
    from core import plan_ui
    proys = [p for p in proys if plan_ui.es_de_herramientas(p) or str(p.get("ID", "")) == obra_id]
    if not proys:
        c2.caption(t("There are no open installation projects to attach this calculation to."))
        return

    idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in proys}
    firma = _firma(resumen, datos)
    _kg = f"_guardado_{key}"
    hecho = st.session_state.get(_kg) or {}

    def _ya(prj) -> bool:
        """v592 · ¿Este MISMO cálculo ya está guardado en esa obra? (un 2º toque duplicaba)."""
        return bool(prj) and hecho.get("firma") == firma and hecho.get("pid") == str(prj.get("ID", ""))

    def _guardar(prj):
        with st.spinner(t("Saving…")):
            res = toolruns.registrar(
                pid=str(prj.get("ID", "")),
                grupo=str(prj.get("Group", grupo)),
                herramienta=herramienta, resumen=resumen,
                datos={"entradas": _snapshot(herramienta), "resultados": datos},
                usuario=usuario, pdf=pdf_bytes, filename=nombre_archivo)
        if res.get("ok"):
            # v592 · Se apunta y se relanza: el aviso se queda (antes era de UNA pasada) y el
            # botón pasa a «Saved» mientras el cálculo sea el mismo.
            st.session_state[_kg] = {"firma": firma, "pid": str(prj.get("ID", "")),
                                     "id": res.get("id", ""), "nombre": str(prj.get("Name", "")),
                                     "drive": bool(res.get("drive_id"))}
            st.rerun()
        else:
            st.error(t("It could not be saved: {e}", e=res.get("error")))

    if hecho.get("firma") == firma:
        c2.success(t(":green[:material/check_circle:] Saved as **{i}** in {x}.", i=hecho.get("id"),
                     x=hecho.get("nombre"))
                   + ("" if hecho.get("drive") else " " + t("(The PDF was not filed in Drive: "
                                                             "check the connection.)")))

    # ── Campo: destino AUTOMÁTICO = el proyecto donde fichó ──
    # No lo elige de una lista; ya está trabajando allí. Mismo criterio que el plano
    # (v137), Mis proyectos (v138) y el Pre-Start (v170). ID primero, nombre de
    # respaldo (v145).
    _fich = None
    if rol == "field":
        try:
            from core import timeclock
            _ses = timeclock.open_sessions(nombre, grupo, usuario)
            _open = (_ses.get(timeclock.TIPO_PROYECTO)
                     or _ses.get(timeclock.TIPO_GENERAL) or {})
            _fpid = str(_open.get("proyecto_id", "")).strip()
            _fpn  = str(_open.get("proyecto", "")).strip()
            for _p in proys:
                if (_fpid and str(_p.get("ID", "")).strip() == _fpid) or \
                   (not _fpid and _fpn and
                    str(_p.get("Name", "")).strip().casefold() == _fpn.casefold()):
                    _fich = _p
                    break
        except Exception:
            pass

    with c2:
        if _fich is not None:
            st.caption(t(":material/save: It will be saved to **{x}** — where you clocked in.",
                         x=_fich.get('Name')))
            if st.button(t(":material/check: Saved") if _ya(_fich) else
                         t(":material/save: Save to the project"), width="stretch",
                         key=f"save_{key}", disabled=_ya(_fich)):
                _guardar(_fich)
            with st.expander(t("Is it for a different project?"), key=f"exp_otraobra_{key}"):
                sel = st.selectbox(t("Project"), [_VACIO] + list(idmap.keys()),
                                   key=f"prj_{key}", label_visibility="collapsed")
                if st.button(t("Save to the chosen one"), key=f"save2_{key}",
                             width="stretch",
                             disabled=(not sel or sel == _VACIO or _ya(idmap.get(sel)))):
                    _guardar(idmap[sel])
        else:
            if rol == "field":
                st.caption(t("You have not clocked in to a project yet (:material/schedule: Time clock). Choose one:"))
            # ⚠️ v592 · Con la obra elegida ARRIBA, ya elegida (una vez por cálculo, o si el
            # widget es nuevo; si quien guarda elige otra, se respeta). Sin obra arriba, sin
            # preselección: guardar contra otro elevador ensucia su historial y su Drive.
            _kp = f"prj_{key}"
            _lbl = next((k for k, p in idmap.items() if str(p.get("ID", "")) == obra_id), None)
            if _lbl and (_kp not in st.session_state or st.session_state.get(f"_dest_{key}") != firma):
                st.session_state[_kp] = _lbl
                st.session_state[f"_dest_{key}"] = firma
            elif st.session_state.get(_kp) not in [_VACIO, *idmap]:
                st.session_state[_kp] = _VACIO
            sel = st.selectbox(t("Save to the project"), [_VACIO] + list(idmap.keys()),
                               key=_kp)
            _destino = idmap.get(sel)
            if st.button(t(":material/check: Saved") if _ya(_destino) else
                         t(":material/save: Save to the project"), width="stretch",
                         key=f"save_{key}",
                         disabled=(not sel or sel == _VACIO or _ya(_destino))):
                _guardar(idmap[sel])
