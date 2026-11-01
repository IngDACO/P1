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


def obra_del_fichaje(abierta: dict, proys: list):
    """v625 · La obra de un fichaje abierto, entre `proys`: por su ID (el nombre PUEDE
    repetirse). Un fichaje sin ID va por el nombre, y solo si ese nombre es de UNA obra.

    ⚠️ Iba por el nombre y se quedaba con la primera que casara: con dos obras «Torre Norte —
    Lift 1», fichado en PRJ-2, la herramienta usaba el plano de PRJ-1 (demostrado) y lo
    guardaba allí."""
    pid = str((abierta or {}).get("proyecto_id", "")).strip()
    if pid:
        return next((p for p in proys if str(p.get("ID", "")).strip() == pid), None)
    nombre = str((abierta or {}).get("proyecto", "")).strip().casefold()
    if not nombre:
        return None
    casan = [p for p in proys if str(p.get("Name", "")).strip().casefold() == nombre]
    return casan[0] if len(casan) == 1 else None


def _proyecto_fichado(auth: dict):
    """Proyecto del clock-in abierto del usuario de campo."""
    try:
        ses = timeclock.open_sessions(auth.get("nombre", ""), auth.get("grupo", ""),
                                      auth.get("usuario", ""))
    except Exception:
        return None
    abierta = ses.get(timeclock.TIPO_PROYECTO) or ses.get(timeclock.TIPO_GENERAL)
    if not abierta:
        return None
    # Resolucion del proyecto del clock-in: si esta archivado, que se encuentre
    # igual en vez de dejar la herramienta sin datos del plano y sin explicacion.
    return obra_del_fichaje(abierta, P.list_projects(grupo=auth.get("grupo", "") or None,
                                                     incluir_archivados=True))


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

    # ── Campo: manda el fichaje; sin fichar, sus obras ──
    # ⚠️ v625 · Sin fichar no se le cerraba nada, pero la herramienta salía sin obra y sin plano
    # («Clock in first»): quien mide en una visita, sin jornada abierta, tecleaba el plano a
    # mano. Con UNA obra asignada se usa sola; con varias elige entre las SUYAS.
    if rol == "field":
        prj = _proyecto_fichado(auth)
        if prj:
            datos = plan_data.del_proyecto(str(prj.get("ID", "")))
            _cabecera(prj, datos, fichado=True)
            return prj, datos
        suyas = [p for p in P.list_projects_for_field(auth.get("usuario", ""),
                                                      grupo=auth.get("grupo", "") or None)
                 if es_de_herramientas(p)]
        if not suyas:
            st.info(t(":material/info: You have no open installation assigned, so there is no "
                      "drawing to start from. Enter the data by hand, or clock in at "
                      ":material/schedule: Time clock."))
            return None, {}
        if len(suyas) == 1:
            prj = suyas[0]
        else:
            idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in suyas}
            opciones = [SIN_PROYECTO] + list(idmap)
            prj = idmap.get(st.selectbox(t("Project"), opciones, key=f"pl_prj_{key}",
                                         help=ayuda or t("Your open installation jobs. The tool "
                                                         "uses the drawing data stored on the "
                                                         "project.")))
            if prj is None:
                return None, {}
        datos = plan_data.del_proyecto(str(prj.get("ID", "")))
        _cabecera(prj, datos, fichado=False)
        return prj, datos

    # ── Admin y propietario: eligen el proyecto aquí ──
    proys = (P.list_projects() if rol == "owner"
             else P.list_projects(grupo=auth.get("grupo", "")))
    if not proys:
        return None, {}
    idmap = {f"{p.get('Name')} ({p.get('ID')})": p for p in proys}
    # ⚠️ v589 · solo las obras donde estas herramientas tienen sentido (un hueco que medir):
    # el selector ofrecía Deliveries, una reparación, una cancelada y un desmontaje ya
    # completado. La que ya estuviera elegida se queda, aunque hoy no entre.
    _ya = st.session_state.get(f"pl_prj_{key}")
    opciones = [SIN_PROYECTO] + [k for k, p in idmap.items() if es_de_herramientas(p) or k == _ya]
    sel = st.selectbox(t("Project"), opciones, key=f"pl_prj_{key}",
                       help=ayuda or t("Installation jobs still open. The tool uses the drawing "
                                       "data stored on the project."))
    if sel == opciones[0]:
        return None, {}
    prj = idmap[sel]
    datos = plan_data.del_proyecto(str(prj.get("ID", "")))
    _cabecera(prj, datos, fichado=False)
    return prj, datos


def es_de_herramientas(prj: dict) -> bool:
    """v589 · ¿Tiene sentido medir esta obra con las herramientas técnicas (survey, plomada,
    rieles, buffers, belting)? Una instalación —sola o tras un desmontaje— que no esté
    terminada ni cancelada. Sin tipo (obras viejas) sí: no se sabe, y esconderla sería peor."""
    from core import valores
    tipo = valores.canon(str((prj or {}).get("Type", "") or ""))
    if tipo and tipo not in (P.TIPO_INSTALACION, P.TIPO_RIPOUT_INST):
        return False
    return str((prj or {}).get("Status", "")) not in ("Completed", "Cancelled")


def _cabecera(prj: dict, datos: dict, fichado: bool):
    # v625 · El nombre lo teclea la oficina: tal cual, sin que un * o un _ lo deformen. Y la
    # frase entera por `t()` (el literal concatenado es la forma que las redes no ven).
    from core.maps import literal_md
    _n = literal_md(prj.get("Name"))
    if datos:
        st.caption(t(":material/schedule: Clocked in at **{x}** · {y}", x=_n,
                     y=plan_data.resumen(datos)) if fichado else
                   t(":material/description: **{x}** · {y}", x=_n, y=plan_data.resumen(datos)))
        if datos.get("faltan"):
            st.caption(t(":orange[:material/warning:] The drawing did not give: {x} — enter "
                         "them by hand.")
                       .replace("{x}", ", ".join(datos["faltan"][:8])
                                + ("…" if len(datos["faltan"]) > 8 else "")))
    else:
        # ⚠️ v589 · mandaba a «My company → open the project → Files», un menú que ya no
        # existe. El plano se carga en la obra → Files; el administrador, con un botón.
        rol = (st.session_state.get("auth") or {}).get("rol", "")
        if rol == "field":
            st.warning(t("**{n}** has no drawing data loaded. Ask the office to load it on the "
                         "project, or upload the PDF below.", n=_n))
            return
        st.warning(t("**{n}** has no drawing data loaded. Load it once in the project's "
                     ":material/attach_file: Files and every tool will use it — or upload the PDF "
                     "below.", n=_n))
        if rol == "administrator" and st.button(t(":material/attach_file: Open the project's Files"),
                                                key=f"pl_ir_archivos_{prj.get('ID')}", type="tertiary"):
            st.session_state["_prjsel_pending"] = str(prj.get("ID", ""))
            st.session_state["_prj_sec_pending"] = "📎 Archivos"
            st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
            st.rerun()


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
