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
from core import estado_vivo
from core import plan_data
from core import timeclock


# v535 · Aviso de `selector_proyecto` a `aplicar`: la obra acaba de cambiar.
_FORZAR = "_pl_forzar"
# La opción «sin proyecto» del selector del admin (v542: el Survey la ASIGNA al duplicar y
# al guardarse en un proyecto, para que el siguiente se elija a propósito).
SIN_PROYECTO = "— no project (load the drawing by hand) —"


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
        if str(p.get("Name", "")).strip() == nombre:
            return p
    return None


def selector_proyecto(key: str, ayuda: str = "") -> tuple:
    """(proyecto, datos_del_plano). Ambos pueden ser None/{}.

    ⚠️ v534 · Aquí se sabe con qué OBRA se pinta la herramienta, y por eso aquí se decide si
    lo que quedó tecleado sigue valiendo: si la herramienta VUELVE a pintarse y la obra es
    otra, sus entradas se olvidan (`estado_vivo.al_pintar`) para que el plano de la obra
    nueva las rellene. Va antes de que la herramienta cree sus widgets — las cinco llaman a
    esta función lo primero.
    """
    prj, datos = _selector_proyecto(key, ayuda)
    # v535 · Si lo que tenía la herramienta era de OTRA obra, el plano de esta tiene que
    # MANDAR en el `aplicar` que viene justo después (si no, solo rellena lo vacío y se
    # quedaría el dato de la obra anterior). Se escribe SIEMPRE, para que un aviso viejo
    # no lo herede otra herramienta.
    st.session_state[_FORZAR] = bool(estado_vivo.al_pintar(key, (prj or {}).get("ID", "")))
    return prj, datos


def _selector_proyecto(key: str, ayuda: str = "") -> tuple:
    if not P.is_configured():
        return None, {}
    auth = st.session_state.get("auth", {}) or {}
    rol = auth.get("rol", "")

    # ── Campo: el proyecto viene del fichaje ──
    if rol == "field":
        prj = _proyecto_fichado(auth)
        if not prj:
            st.info(t(":material/info: **Clock in first at :material/schedule: Time clock**, choosing the project you are working on. That way the tool uses its drawing data and you will not have to upload the PDF."))
            return None, {}
        datos = plan_data.del_proyecto(str(prj.get("ID", "")))
        _cabecera(prj, datos, fichado=True)
        return prj, datos

    # ── Admin y propietario: eligen el proyecto aquí ──
    proys = (P.list_projects() if rol == "owner"
             else P.list_projects(grupo=auth.get("grupo", "")))
    if not proys:
        return None, {}
    idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in proys}
    opciones = [SIN_PROYECTO] + list(idmap.keys())
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
                   + f"**{prj.get('Name')}** · {plan_data.resumen(datos)}")
        if datos.get("faltan"):
            st.caption(t(":orange[:material/warning:] The drawing did not give: {x} — enter "
                         "them by hand.")
                       .replace("{x}", ", ".join(datos["faltan"][:8])
                                + ("…" if len(datos["faltan"]) > 8 else "")))
    else:
        st.warning(f"**{prj.get('Name')}** has no drawing data loaded. "
                   "Load it on the project (:material/build: My company → open the project → "
                   ":material/attach_file: Files) or upload the PDF below.")


def aplicar(datos: dict, mapa: dict, neutros: dict = None) -> int:
    """Vuelca valores del plano en session_state. `mapa` = {clave_plano: clave_widget}.

    Solo escribe si el widget está vacío/en cero, para no pisar algo que el
    usuario ya ajustó a mano. Devuelve cuántos aplicó.

    ⚠️ v535 · Salvo justo después de un cambio de OBRA (lo avisa `selector_proyecto`):
    entonces lo que hay es de la obra anterior y el plano de esta lo pisa — solo en lo que
    el plano trae; lo que no trae se queda como está.

    `neutros` = {clave_widget: valor} que cuenta como VACÍO: el nº de paradas del Survey
    nace en 2 («mínimo neutro; el NS real sale del plano») y el 2 no es cero, así que el
    NS del plano no se aplicaba nunca — solo funcionaba por accidente cuando Streamlit
    había borrado el campo al salir de la herramienta, que v534 dejó de hacer.
    """
    forzar = bool(st.session_state.pop(_FORZAR, False))
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
        if destino in (neutros or {}) and actual == (neutros or {})[destino]:
            vacio = True
        if vacio or forzar:
            try:
                # Un entero se queda entero (el nº de paradas): con `forzar` se escribe
                # también donde ya había un valor, y ese valor dice el tipo del widget.
                st.session_state[destino] = (int(round(float(val))) if isinstance(actual, int)
                                             and not isinstance(actual, bool) else float(val))
            except (TypeError, ValueError):
                st.session_state[destino] = val
            n += 1
    return n
