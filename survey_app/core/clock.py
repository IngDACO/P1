"""
Hora LOCAL por grupo (v173).

Streamlit Cloud corre el proceso en UTC, y ese proceso es COMPARTIDO por todos los
usuarios, así que no se puede fijar una zona global (tzset) para todos: cada grupo
(empresa) puede estar en otro país. Este helper resuelve la zona del grupo del
usuario EN SESIÓN (o de un grupo explícito) y devuelve datetime/date NAIVE en esa
hora local, para que TODOS los datetime.now()/date.today() de la app graben y
comparen "hoy" en la hora local correcta.

La zona de cada grupo se guarda en `Grupos.Zona` (la fija el propietario). Sin zona
—o para el propietario, que no tiene grupo— se usa DEFAULT_TZ.
"""
from datetime import datetime, date

try:
    from zoneinfo import ZoneInfo
except Exception:                      # pragma: no cover
    ZoneInfo = None

DEFAULT_TZ = "Australia/Sydney"


def _zone_name(grupo=None) -> str:
    """Nombre de zona (p.ej. 'Australia/Sydney') del grupo dado o del de la sesión."""
    g = grupo
    if not g:
        try:
            import streamlit as st
            g = (st.session_state.get("auth", {}) or {}).get("grupo", "")
        except Exception:
            g = ""
    if g:
        try:
            from core import auth
            z = (auth.group_timezone(g) or "").strip()
            if z:
                return z
        except Exception:
            pass
    return DEFAULT_TZ


def _zone(grupo=None):
    if ZoneInfo is None:
        return None
    for name in (_zone_name(grupo), DEFAULT_TZ):
        try:
            return ZoneInfo(name)
        except Exception:
            continue
    return None


def now(grupo=None) -> datetime:
    """datetime NAIVE en la hora local del grupo (o del grupo del usuario en sesión)."""
    z = _zone(grupo)
    if z is None:
        return datetime.now()
    return datetime.now(z).replace(tzinfo=None)


def today(grupo=None) -> date:
    return now(grupo).date()
