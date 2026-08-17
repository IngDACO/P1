"""Aislamiento entre empresas cliente: nadie abre lo que no es de su grupo (v351).

## El fallo que cierra

Hasta v350 el aislamiento **no lo garantizaba el código**: lo garantizaba que la
interfaz nunca te *ofreciera* el ID de otra empresa. Ninguna de las seis vistas de
detalle comprobaba el grupo del objeto; `_detalle_proyecto` incluso **adoptaba** el del
proyecto (`grupo = prj["Grupo"] or grupo`) y pintaba con él costos, horas, personal y
archivos. Y desde v337 los deep-links por URL están cableados, así que bastaba cambiar
`?p=PRJ-0007` por otro ID — o escanear el QR de un activo ajeno.

Con un solo grupo real (`cliente1`) era latente. Deja de serlo con el segundo cliente.

## La regla, en un solo sitio

Una sola definición a propósito: cinco copias divergentes de un helper es exactamente
lo que causó los fallos de v323. Módulo HOJA (solo importa streamlit) → sin ciclos.

- **propietario**: ve todos los grupos. Es su función; no se le bloquea.
- **administrador / campo**: solo su grupo.
- Objeto **sin grupo** (datos viejos, antes de que la columna existiera): se deja pasar
  y se registra. Bloquear por un campo vacío rompería registros históricos legítimos;
  el aislamiento de verdad llega con un libro por cliente.

⚠️ La comprobación va en la **frontera de render**, no en la capa de datos. `get_project`
y compañía los llaman por dentro flujos que cruzan grupos a propósito (las vistas del
propietario, `project_hours_bulk`, el digest multi-grupo). Poner el filtro ahí rompería
esos caminos y daría una falsa sensación de blindaje.
"""
import logging

import streamlit as st

logger = logging.getLogger(__name__)


def _auth() -> dict:
    try:
        return st.session_state.get("auth") or {}
    except Exception:
        return {}


def rol() -> str:
    return str(_auth().get("rol", "") or "")


def grupo_sesion() -> str:
    return str(_auth().get("grupo", "") or "")


def es_propietario() -> bool:
    return rol() == "propietario"


def puede_ver(obj_grupo) -> bool:
    """¿El usuario en sesión puede abrir algo de `obj_grupo`?"""
    if es_propietario():
        return True
    g_obj = str(obj_grupo or "").strip()
    if not g_obj:                      # sin grupo: histórico, no se bloquea (ver arriba)
        return True
    return g_obj.casefold() == grupo_sesion().strip().casefold()


def exigir(obj, etiqueta: str = "Esto", campo: str = "Grupo") -> bool:
    """Guardián de las vistas de detalle.

    Devuelve True si se puede seguir. Si no, pinta el aviso y devuelve False, para
    usarse como `if not tenant.exigir(prj, "Este proyecto"): return`.

    ⚠️ El mensaje NO dice de qué empresa es: confirmar que un ID existe en otro grupo
    ya es filtrar información. Se responde igual que si no existiera.
    """
    g_obj = (obj or {}).get(campo, "") if isinstance(obj, dict) else obj
    if puede_ver(g_obj):
        return True
    logger.warning("tenant: %s de grupo %r pedido por %r (grupo %r) — bloqueado",
                   etiqueta, str(g_obj), _auth().get("usuario", ""), grupo_sesion())
    st.error(f":material/lock: {etiqueta} no existe o no es de tu empresa.")
    return False
