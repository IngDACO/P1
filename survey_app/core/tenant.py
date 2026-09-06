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

from core.i18n import t
logger = logging.getLogger(__name__)


_CLAVE_ACTIVO = "_tenant_grupo_activo"


def _auth() -> dict:
    try:
        return st.session_state.get("auth") or {}
    except Exception:
        return {}


# ── Ámbito temporal de grupo (v379) ──────────────────────────────
#
# Las vistas del PROPIETARIO recorren varios clientes: `owner_digest` llama a
# `group_digest(g)` para cada grupo, y con un libro por cliente (v359) cada
# vuelta tiene que leer el libro DE ESE GRUPO. Pero los lectores de los módulos
# resuelven el libro desde la SESIÓN —y la del propietario no tiene grupo—, así
# que todas las vueltas leían el maestro.
#
# ⚠️ La alternativa era hilar un parámetro `grupo` por decenas de funciones
# públicas (`open_counts_all`, `group_expenses`, `list_group`…) y sus lectores.
# Esto lo resuelve en un sitio: se declara el grupo activo y `sheet_id_para` lo
# consulta antes que la sesión, así que TODA lectura de dentro cae en su libro.
#
# ⚠️ Vive en `st.session_state`, no en un global del módulo: `cache_data` y los
# globales se comparten por PROCESO, y ahí un «grupo activo» se filtraría a otra
# sesión — que es justo la clase de fallo que cerró v378.
def grupo_activo() -> str:
    try:
        return str(st.session_state.get(_CLAVE_ACTIVO) or "")
    except Exception:
        return ""


class como_grupo:
    """`with tenant.como_grupo(g):` → todo lo que se lea dentro sale del libro de `g`.

    Reentrante: al salir restaura el que hubiera antes, así se pueden anidar sin
    que una vuelta del bucle se lleve por delante a la siguiente.
    """

    def __init__(self, grupo):
        self.grupo = str(grupo or "")
        self.previo = None

    def __enter__(self):
        self.previo = grupo_activo()
        try:
            st.session_state[_CLAVE_ACTIVO] = self.grupo
        except Exception:
            pass
        return self

    def __exit__(self, *exc):
        try:
            st.session_state[_CLAVE_ACTIVO] = self.previo
        except Exception:
            pass
        return False


def rol() -> str:
    return str(_auth().get("rol", "") or "")


def grupo_sesion() -> str:
    return str(_auth().get("grupo", "") or "")


def es_propietario() -> bool:
    return rol() == "owner"


def puede_ver(obj_grupo) -> bool:
    """¿El usuario en sesión puede abrir algo de `obj_grupo`?"""
    if es_propietario():
        return True
    g_obj = str(obj_grupo or "").strip()
    if not g_obj:                      # sin grupo: histórico, no se bloquea (ver arriba)
        return True
    return g_obj.casefold() == grupo_sesion().strip().casefold()


def exigir(obj, etiqueta: str = "This item", campo: str = "Group") -> bool:
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
    st.error(f":material/lock: {etiqueta} " + t("does not exist or is not yours."))
    return False
