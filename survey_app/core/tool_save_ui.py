"""
Bloque compartido "descargar + guardar en el proyecto" para las herramientas.

Las cuatro herramientas de cálculo lo usan igual, así que vive aquí en vez de
copiarse cuatro veces (y desviarse cuatro veces).

Flujo: elegir proyecto → descargar el PDF → guardarlo contra el proyecto
(`toolruns.registrar`, que escribe en la hoja Calculos y archiva en Drive).
"""
import streamlit as st

from core import projects as P
from core import toolruns

# Prefijo de las claves de session_state de cada herramienta. Sirve para
# fotografiar sus entradas sin enumerarlas a mano (asi las claves dinamicas,
# como `belt_hgpr_3`, entran solas).
_PREFIJO = {"plomada": "plb_", "rieles": "rc_", "buffers": "bc_", "belting": "belt_"}
_PENDIENTE = "_toolrestore"

# Opción neutra: sin ella el selectbox devuelve el primer proyecto y se
# escribiría sobre un elevador que nadie eligió.
_VACIO = "— elige el proyecto —"


def _proyectos_de(rol, usuario, grupo):
    """Mismo criterio que el Pre-Start: cada rol ve lo suyo."""
    if rol == "propietario":
        return P.list_projects()
    if rol == "administrador":
        return P.list_projects(grupo=grupo)
    return P.list_projects_for_field(usuario, grupo=grupo)


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
        if not str(k).startswith(pref) or str(k).endswith("_editor"):
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
    for k, v in (pend.get("valores") or {}).items():
        try:
            if isinstance(v, dict) and "__df__" in v:
                st.session_state[k] = _pd.DataFrame(v["__df__"])
            else:
                st.session_state[k] = v
        except Exception:
            pass
    return str(pend.get("id", ""))


def pedir_reapertura(fila, herramienta: str, etiqueta_nav: str) -> bool:
    """Deja pendiente reabrir este calculo y navega a su herramienta."""
    vals = toolruns.entradas_de(fila)
    if not vals:
        return False
    st.session_state[_PENDIENTE] = {"herramienta": herramienta, "valores": vals,
                                    "id": str(fila.get("ID", ""))}
    st.session_state["_nav_pending"] = etiqueta_nav
    return True


def render_guardar(herramienta: str, titulo_pdf: str, pdf_bytes: bytes,
                   resumen: str, datos: dict, nombre_archivo: str,
                   key: str) -> None:
    """Descarga del PDF + guardado contra un proyecto.

    `herramienta` es la clave de `toolruns.HERRAMIENTAS`. Junto a los resultados
    se guardan las ENTRADAS (`_snapshot`), que es lo que permite reabrirlo luego.
    """
    if not pdf_bytes:
        return

    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    c1.download_button(f":material/download: Descargar {titulo_pdf} (PDF)", data=pdf_bytes,
                       file_name=nombre_archivo, mime="application/pdf",
                       use_container_width=True, key=f"dl_{key}")

    if not toolruns.is_configured():
        c2.caption(":material/lock: Guardar en el proyecto requiere Google Sheets configurado.")
        return

    a = st.session_state.get("auth", {}) or {}
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    grupo = a.get("grupo", "")
    nombre = a.get("nombre") or usuario
    proys = _proyectos_de(rol, usuario, grupo)
    if not proys:
        c2.caption("No hay proyectos disponibles para asociar este cálculo.")
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p for p in proys}

    def _guardar(prj):
        with st.spinner("Guardando..."):
            res = toolruns.registrar(
                pid=str(prj.get("ID", "")),
                grupo=str(prj.get("Grupo", grupo)),
                herramienta=herramienta, resumen=resumen,
                datos={"entradas": _snapshot(herramienta), "resultados": datos},
                usuario=usuario, pdf=pdf_bytes, filename=nombre_archivo)
        if res.get("ok"):
            msg = f"✅ Guardado como **{res['id']}** en {prj.get('Nombre')}."
            if not res.get("drive_id"):
                msg += " (El PDF no se archivó en Drive: revisa la conexión.)"
            st.success(msg)
        else:
            st.error(f"No se pudo guardar: {res.get('error')}")

    # ── Campo: destino AUTOMÁTICO = el proyecto donde fichó ──
    # No lo elige de una lista; ya está trabajando allí. Mismo criterio que el plano
    # (v137), Mis proyectos (v138) y el Pre-Start (v170). ID primero, nombre de
    # respaldo (v145).
    _fich = None
    if rol == "campo":
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
                    str(_p.get("Nombre", "")).strip().casefold() == _fpn.casefold()):
                    _fich = _p
                    break
        except Exception:
            pass

    with c2:
        if _fich is not None:
            st.caption(f":material/save: Se guardará en **{_fich.get('Nombre')}** — donde fichaste.")
            if st.button(":material/save: Guardar en el proyecto", use_container_width=True,
                         key=f"save_{key}"):
                _guardar(_fich)
            with st.expander("¿Es de otro proyecto?"):
                sel = st.selectbox("Proyecto", [_VACIO] + list(idmap.keys()),
                                   key=f"prj_{key}", label_visibility="collapsed")
                if st.button("Guardar en el elegido", key=f"save2_{key}",
                             use_container_width=True,
                             disabled=(not sel or sel == _VACIO)):
                    _guardar(idmap[sel])
        else:
            if rol == "campo":
                st.caption("Aún no has fichado a un proyecto (:material/schedule: Fichaje). Elige uno:")
            # Sin preseleccion: guardar el calculo contra otro elevador ensucia su
            # historial y su carpeta de Drive sin que nadie lo note.
            sel = st.selectbox("Guardar en el proyecto", [_VACIO] + list(idmap.keys()),
                               key=f"prj_{key}")
            if st.button(":material/save: Guardar en el proyecto", use_container_width=True,
                         key=f"save_{key}", disabled=(not sel or sel == _VACIO)):
                _guardar(idmap[sel])
