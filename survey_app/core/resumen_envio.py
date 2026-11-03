# -*- coding: utf-8 -*-
"""El resumen del día, cada mañana por correo o Telegram, a quien lo pida (v648).

## Decisiones del usuario (03/11/2026)

- Cada persona de la oficina lo activa PARA SÍ, en Home («Every morning too»): nadie lo recibe sin haberlo pedido.
- Lo manda un trabajo de GitHub Actions (`.github/workflows/resumen_manana.yml`, cada hora) que lanza
  `resumen_manana.py`: a cada empresa cuando en SU hora local son entre las 7 y las 11, una vez al día por persona.
- Es el resumen de Home (`resumen_dia.generar`), con los mismos datos y las mismas reglas: UNA llamada por empresa e
  idioma, y la reciben todos los suscritos de ese idioma.

## ⚠️ El repositorio es PÚBLICO

Lo que imprime el trabajo lo puede leer cualquiera. `enviar_todo` devuelve solo cuentas: ni empresas, ni personas,
ni el texto, ni el mensaje de un error.

## ⚠️ A quién

Solo a quien sigue siendo administrador ACTIVO de ESA empresa (`_admins_activos`): darse de baja de la oficina, o
cambiar de rol, corta el envío aunque la fila diga «YES». Cada empresa se recorre dentro de `tenant.como_grupo`, así
que todo lo que se lee sale de SU libro.

## Una vez al día

`LastSent` se apunta tras enviar. Si el apunte falla, la hora siguiente lo vuelve a mandar: dos es mejor que ninguno.
"""
import logging

import streamlit as st

from core import clock, columnas, timeclock
from core.i18n import t
from core.num import col_letter as _col_letter

logger = logging.getLogger(__name__)

SHEET = "DailySummary"
# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL.
HEADERS = ["User", "Group", "Language", "Active", "Since", "LastSent", "Updated"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}
SI = "YES"
HORA_DESDE, HORA_HASTA = 7, 11        # hora LOCAL de la empresa, [7, 11): un trabajo que se retrasa aún llega
IDIOMAS = ("en", "es")
CUENTAS = ("empresas", "enviados", "ya_hoy", "fuera_de_hora", "sin_canal", "sin_permiso", "fallos", "errores")


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def _ws():
    """⚠️ `get_sheet` CREA la hoja si falta: solo lo usan las escrituras."""
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("resumen_envio: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras, y por eso la hoja va en `hojas.HOJAS_LECTURA`: fuera del lote se leería VACÍA para siempre
    (v461/v507/v514/v610). La crea la primera persona que lo active."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas
    hojas.invalidar(SHEET)
    try:
        _records_cached.clear()
    except Exception as e:
        logger.warning("resumen_envio._invalidate: %s", e)


def _es(r, grupo, usuario) -> bool:
    return (str(r.get("Group", "")).strip().lower() == str(grupo or "").strip().lower()
            and str(r.get("User", "")).strip().lower() == str(usuario or "").strip().lower())


def _activa(r) -> bool:
    return str(r.get("Active", "")).strip().upper() == SI


# ═════════════════════════════════════════════════════════════════
# Pedirlo y dejarlo (Home)
# ═════════════════════════════════════════════════════════════════
def suscrito(grupo, usuario) -> bool:
    """¿Lo recibe cada mañana? (lectura del lote: no cuesta una llamada)."""
    return any(_es(r, grupo, usuario) and _activa(r) for r in _records())


def suscribir(grupo, usuario, idioma, si=True) -> tuple:
    """Lo activa (`si`) o lo quita para `usuario` en `grupo`. `(ok, mensaje)`. Una fila por persona y empresa: quitarlo
    deja la fila con `Active=NO`, que dice desde cuándo y hasta cuándo lo recibió."""
    if not str(usuario or "").strip() or not str(grupo or "").strip():
        return False, t("Sign in again to change this.")
    idioma = idioma if idioma in IDIOMAS else IDIOMAS[0]
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        # ⚠️ FRESCO: para decidir DÓNDE escribir, nunca la caché (v323)
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
        ahora = clock.now(grupo).strftime("%Y-%m-%d %H:%M")
        fila = next((i + 2 for i, r in enumerate(recs) if _es(r, grupo, usuario)), None)
        if fila is None:
            if si:
                w.append_row([str(usuario), str(grupo), idioma, SI, ahora, "", ahora], value_input_option="RAW")
        else:
            _c = {"Language": idioma, "Active": SI if si else "NO", "Updated": ahora}
            if si and not _activa(recs[fila - 2]):
                _c["Since"] = ahora
            w.batch_update([{"range": "%s%d" % (_col_letter(_COL[k]), fila), "values": [[v]]} for k, v in _c.items()],
                           value_input_option="RAW")
    except Exception as e:
        logger.warning("resumen_envio.suscribir: %s", e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, (t("Done: you will get today's summary every morning, around {h}:00 your company's time.", h=HORA_DESDE)
                  if si else t("Done: no more morning summaries."))


# ═════════════════════════════════════════════════════════════════
# Mandarlo (el trabajo de cada hora)
# ═════════════════════════════════════════════════════════════════
def toca(ahora) -> bool:
    """¿Es la hora de la mañana de ESA empresa?"""
    return HORA_DESDE <= ahora.hour < HORA_HASTA


def _admins_activos(grupo) -> set:
    from core import auth
    return {str(u.get("User", "")).strip().lower() for u in auth.list_users(grupo)
            if str(u.get("Role", "")).strip().lower() == "administrator"
            and str(u.get("Active", "SI")).strip().upper() in auth._ACTIVE_OK}


def lineas(res) -> list:
    """Lo que se manda: el resumen y cómo dejar de recibirlo."""
    from core import resumen_dia as RD
    return RD.como_texto(res) + ["", t("Prepared at {h} with the app's data. You get it because you asked for it in "
                                       "Home → Today's summary → «Every morning too»: untick it there to stop.",
                                       h=res.get("hora", ""))]


def enviar_empresa(grupo, ignorar_hora=False) -> dict:
    """Dentro de `tenant.como_grupo(grupo)`. Devuelve SOLO cuentas (ver el módulo)."""
    from core import hojas, notify, resumen_dia as RD
    cuenta = dict.fromkeys(CUENTAS, 0)
    # ⚠️ SIN cabeceras: en una empresa donde nadie lo pidió, la hoja no existe y así NO se crea (un lector que escribe,
    # regla v145). El trabajo es un proceso nuevo cada hora: el lote se lee ahora, y la fila i es la i + 2 de la hoja.
    recs = hojas.registros(SHEET) or []
    filas = [(i + 2, r) for i, r in enumerate(recs)
             if str(r.get("Group", "")).strip().lower() == str(grupo).strip().lower() and _activa(r)]
    if not filas:
        return cuenta
    ahora = clock.now(grupo)
    if not ignorar_hora and not toca(ahora):
        cuenta["fuera_de_hora"] += len(filas)
        return cuenta
    hoy = ahora.strftime("%Y-%m-%d")
    adm = _admins_activos(grupo)
    por_idioma = {}
    for n, r in filas:
        if str(r.get("LastSent", "")).strip()[:10] == hoy:
            cuenta["ya_hoy"] += 1
        elif str(r.get("User", "")).strip().lower() not in adm:
            cuenta["sin_permiso"] += 1
        else:
            _i = str(r.get("Language", "")).strip()
            por_idioma.setdefault(_i if _i in IDIOMAS else IDIOMAS[0], []).append((n, r))
    lote = []
    for idi, gente in por_idioma.items():
        res, _mot = RD.generar(grupo, gente[0][1].get("User", ""), idi)      # UNA vez por idioma
        if not res:
            cuenta["fallos"] += len(gente)
            continue
        _lin = lineas(res)
        for n, r in gente:
            rr = notify.notify_user(str(r.get("User", "")), f"🔔 Today's summary — {grupo}", _lin,
                                    notify._sec("APP_URL", notify._APP_URL_DEFAULT))
            if rr.get("email") or rr.get("telegram"):
                cuenta["enviados"] += 1
                lote.append({"range": "%s%d" % (_col_letter(_COL["LastSent"]), n),
                             "values": [[ahora.strftime("%Y-%m-%d %H:%M")]]})
            else:
                cuenta["sin_canal"] += 1
    if lote:
        w = _ws()                       # la hoja ya existe (hay filas): abrirla no crea nada
        if w is None:
            cuenta["errores"] += 1
            return cuenta
        w.batch_update(lote, value_input_option="RAW")
        _invalidate()
    return cuenta


def enviar_todo(ignorar_hora=False) -> dict:
    """Todas las empresas activas, cada una en SU libro. Un fallo en una no para las demás. SOLO cuentas."""
    from core import auth, tenant
    total = dict.fromkeys(CUENTAS, 0)
    for g in auth.list_groups(only_active=True):
        grupo = str(g.get("Group", "")).strip()
        if not grupo:
            continue
        total["empresas"] += 1
        with tenant.como_grupo(grupo):
            try:
                c = enviar_empresa(grupo, ignorar_hora)
            except Exception as e:
                logger.warning("resumen_envio.enviar_todo: %s", type(e).__name__)
                c = {"errores": 1}
        for k, v in c.items():
            total[k] = total.get(k, 0) + v
    return total
