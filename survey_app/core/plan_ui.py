"""
Selector de proyecto para las herramientas, según el rol.

De aquí sale el plano con el que trabaja cada herramienta, sin volver a subir
el PDF:

- **admin / propietario**: elige el proyecto dentro de la herramienta (trabaja
  sobre varias obras desde el escritorio).
- **campo**: el proyecto sale del **clock-in**, que ya lo pide
  desde v67. Cero fricción: ficha y las herramientas ya saben dónde está.

Devuelve `(proyecto|None, datos_del_plano)` para que la herramienta prellene
sus campos y sepa a dónde guardar.
"""
import streamlit as st

from core.i18n import t

from core import projects as P
from core import plan_data
from core import timeclock


def _proyecto_fichado(auth: dict):
    """Proyecto del clock-in abierto del usuario de campo."""
    try:
        ses = timeclock.open_sessions(auth.get("nombre", ""), auth.get("grupo", ""),
                                      auth.get("usuario", ""))
    except Exception:
        return None
    abierta = ses.get(timeclock.TIPO_PROYECTO) or ses.get(timeclock.TIPO_GENERAL)
    nombre = str((abierta or {}).get("proyecto", "")).strip()
    if not nombre:
        return None
    # Resolucion del proyecto del clock-in: si esta archivado, que se encuentre
    # igual en vez de dejar la herramienta sin datos del plano y sin explicacion.
    for p in P.list_projects(grupo=auth.get("grupo", "") or None,
                             incluir_archivados=True):
        if str(p.get("Nombre", "")).strip() == nombre:
            return p
    return None


def selector_proyecto(key: str, ayuda: str = "") -> tuple:
    """(proyecto, datos_del_plano). Ambos pueden ser None/{}."""
    if not P.is_configured():
        return None, {}
    auth = st.session_state.get("auth", {}) or {}
    rol = auth.get("rol", "")

    # ── Campo: el proyecto viene del fichaje ──
    if rol == "campo":
        prj = _proyecto_fichado(auth)
        if not prj:
            st.info(t(":material/info: **Clock in first at :material/schedule: Time clock**, choosing the project you are working on. That way the tool uses its drawing data and you will not have to upload the PDF."))
            return None, {}
        datos = plan_data.del_proyecto(str(prj.get("ID", "")))
        _cabecera(prj, datos, fichado=True)
        return prj, datos

    # ── Admin y propietario: eligen el proyecto aquí ──
    proys = (P.list_projects() if rol == "propietario"
             else P.list_projects(grupo=auth.get("grupo", "")))
    if not proys:
        return None, {}
    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p for p in proys}
    opciones = ["— no project (load the drawing by hand) —"] + list(idmap.keys())
    sel = st.selectbox(t("Project"), opciones, key=f"pl_prj_{key}",
                       help=ayuda or "It uses the drawing data stored on the project.")
    if sel == opciones[0]:
        return None, {}
    prj = idmap[sel]
    datos = plan_data.del_proyecto(str(prj.get("ID", "")))
    _cabecera(prj, datos, fichado=False)
    return prj, datos


def _cabecera(prj: dict, datos: dict, fichado: bool):
    if datos:
        st.caption((":material/schedule: Clocked in at " if fichado else ":material/description: ")
                   + f"**{prj.get('Nombre')}** · {plan_data.resumen(datos)}")
        if datos.get("faltan"):
            st.caption(f":orange[:material/warning:] The drawing did not give: {', '.join(datos['faltan'][:8])}"
                       + ("…" if len(datos["faltan"]) > 8 else "")
                       + " — enter them by hand.")
    else:
        st.warning(f"**{prj.get('Nombre')}** has no drawing data loaded. "
                   "Load it on the project (:material/build: My company → open the project → "
                   ":material/attach_file: Files) or upload the PDF below.")


def aplicar(datos: dict, mapa: dict) -> int:
    """Vuelca valores del plano en session_state. `mapa` = {clave_plano: clave_widget}.

    Solo escribe si el widget está vacío/en cero, para no pisar algo que el
    usuario ya ajustó a mano. Devuelve cuántos aplicó.
    """
    n = 0
    for origen, destino in (mapa or {}).items():
        val = (datos or {}).get(origen)
        if origen.startswith("params."):
            val = ((datos or {}).get("params") or {}).get(origen.split(".", 1)[1])
        if val in (None, ""):
            continue
        actual = st.session_state.get(destino)
        try:
            vacio = actual in (None, "", 0, 0.0) or float(actual) == 0.0
        except Exception:
            vacio = not actual
        if vacio:
            try:
                st.session_state[destino] = float(val)
            except (TypeError, ValueError):
                st.session_state[destino] = val
            n += 1
    return n
