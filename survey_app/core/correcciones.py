"""Correcciones de fichaje: el campo arregla su hora, el admin la revisa (v461).

## El problema

El técnico llega a la obra a las 7:00 y se acuerda de fichar a las 9:00. Hasta ahora
la app registraba las 9:00 y no había forma de arreglarlo: esas dos horas se perdían,
o se «arreglaban» pidiéndole al administrador que tocara la hoja a mano.

## Las tres decisiones del usuario

| | |
|---|---|
| **Cuándo cuenta** | la hora nueva **se aplica YA**; el admin la revisa después y puede revertirla |
| **Si el periodo ya se pagó** | se permite, pero al admin **se le avisa** de qué nómina lo cubre |
| **Plazo** | **el mismo día**, salvo cerrar una sesión que sigue ABIERTA (ver abajo) |

⚠️ **Por qué el cierre de una sesión abierta es la excepción, y no un capricho.** Una
fila con `Estado == "ABIERTO"` **acumula contra el reloj**: `_row_segmentos` la cuenta
hasta AHORA. Medido con la función real, una entrada a las 7:00 sin salida da 34,56 h
al día siguiente y **130,56 h** a los cinco — a 40/h son más de 5.000 USD de mano de
obra que nadie trabajó, y esas horas entran en la nómina y en el costo de la obra.
Cerrarla no es corregir el pasado: es parar una hemorragia. Por eso se puede hacer
aunque la sesión sea de otro día, y por eso también pasa por la bandeja del admin.

## Qué se guarda, y por qué el valor ANTERIOR

Cada corrección anota el valor viejo y el nuevo. Sin el viejo, «revertir» no
significaría nada: el admin podría rechazar la corrección y la app no sabría a qué
hora volver. Es la misma razón por la que `orders` guarda el enlace al gasto (v343).

⚠️ El fichaje se localiza por **usuario + hora de entrada original + tipo**, NO por el
número de fila: las filas se desplazan y una referencia posicional envejece mal.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core.i18n import t

logger = logging.getLogger(__name__)

SHEET = "TimeCorrections"
HEADERS = ["ID", "Group", "User", "Name", "Type", "Project",
           "Field", "OldValue", "NewValue", "Reason",
           "Status", "Created", "ReviewedBy", "ReviewedDate", "AdminNote",
           # ⚠️ Se guarda el ID de la nómina que YA cubría ese día, si la había. No
           # es decorativo: es lo que convierte «esto ya se pagó» en algo que el
           # admin puede ir a mirar, en vez de un aviso genérico que no lleva a nada.
           "PayslipCovers"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}

# ── Estados ──────────────────────────────────────────────────────
# ⚠️ Se reusa el vocabulario de `ausencias` (v430) en vez de inventar otro: la app ya
# tiene un flujo de aprobación y dos vocabularios distintos para lo mismo divergen.
PENDIENTE, APROBADA, REVERTIDA = "pendiente", "aprobada", "revertida"
ESTADOS = (PENDIENTE, APROBADA, REVERTIDA)

# Qué campo del fichaje se corrigió.
CAMPO_IN, CAMPO_OUT = "Clock In", "Clock Out"


def _libro_de(_hoja) -> str:
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("correcciones: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja — un lector
    que escribe (regla v145). La crea la primera ESCRITURA."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    """⚠️ El libro va en la CLAVE de caché (v378): `st.cache_data` se comparte por
    proceso, así que sin él el segundo cliente recibiría lo del primero."""
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas                      # v339: tirar también el LOTE
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception as e:
        logger.warning("correcciones: no se pudo limpiar la caché: %s", e)


def _next_id() -> str:
    """⚠️ Lee FRESCO y salta los IDs ya referenciados (v323/v427): decidir qué ID se
    emite con una caché es como se corrompe la identidad."""
    from core import hojas
    ws = _ws()
    try:
        usados = {str(r[0]).strip() for r in ws.get_all_values()[1:] if r and r[0]}
    except Exception:
        usados = set()
    n = 0
    for u in usados:
        try:
            n = max(n, int(str(u).split("-")[-1]))
        except Exception:
            pass
    try:
        return hojas.siguiente_id_libre(SHEET, "COR", n + 1)
    except Exception:
        return f"COR-{n + 1:04d}"


# ── Lectura ──────────────────────────────────────────────────────
def list_group(grupo, estado=None, usuario=None) -> list:
    _g = str(grupo or "").strip().lower()
    out = []
    for r in _records():
        if str(r.get("Group", "")).strip().lower() != _g:
            continue
        if estado and str(r.get("Status", "")).strip().lower() != estado:
            continue
        if usuario and str(r.get("User", "")).strip() != str(usuario):
            continue
        out.append(r)
    return sorted(out, key=lambda r: str(r.get("Created", "")), reverse=True)


def pendientes(grupo) -> list:
    """Lo que el administrador tiene que mirar."""
    return list_group(grupo, estado=PENDIENTE)


def get(cid: str) -> dict:
    for r in _records():
        if str(r.get("ID", "")).strip() == str(cid).strip():
            return r
    return {}


# ── El aviso de «esto ya se pagó» ────────────────────────────────
def nomina_que_cubre(grupo, usuario, fecha) -> str:
    """ID de la nómina VIVA cuyo periodo cubre ese día, o "".

    ⚠️ Solo las vivas: una nómina anulada no pagó nada, así que avisar por ella sería
    un falso positivo (misma lógica que v426 con las facturas anuladas en el P&L).
    ⚠️ Degrada a "" si no se puede leer: no poder comprobarlo NO es lo mismo que
    «no está pagado», pero un aviso que no se puede dar no debe bloquear la
    corrección — el admin sigue viendo la fecha en la bandeja.
    """
    try:
        from core import payroll
        from core.num import parse_date
        d = parse_date(fecha)
        if not d:
            return ""
        for n in payroll.list_nominas(grupo):
            if str(n.get("User", "")).strip() != str(usuario).strip():
                continue
            d0, d1 = parse_date(n.get("PeriodFrom")), parse_date(n.get("PeriodTo"))
            if d0 and d1 and d0 <= d <= d1:
                return str(n.get("ID", ""))
    except Exception as e:
        logger.warning("nomina_que_cubre: no se pudo comprobar: %s", e)
    return ""


# ── Escritura ────────────────────────────────────────────────────
def registrar(grupo, usuario, nombre, tipo, proyecto, campo,
              valor_anterior, valor_nuevo, motivo="") -> tuple:
    """Anota una corrección YA APLICADA al fichaje. Devuelve (ok, id|mensaje).

    ⚠️ Se llama DESPUÉS de tocar el fichaje y su fallo no revierte el cambio del
    usuario: el arreglo del campo ya se hizo y no puede deshacerse porque falle el
    apunte (mismo criterio que la auditoría de v342). Si esto falla, queda en el log.
    """
    ws = _ws()
    if ws is None:
        return False, t("The timeclock is not configured.")
    cid = _next_id()
    fila = [cid, str(grupo or ""), str(usuario or ""), str(nombre or ""),
            str(tipo or ""), str(proyecto or ""), str(campo or ""),
            str(valor_anterior or ""), str(valor_nuevo or ""), str(motivo or ""),
            PENDIENTE, clock.now(grupo).strftime(timeclock.FMT), "", "", "",
            nomina_que_cubre(grupo, usuario, valor_nuevo)]
    # ⚠️ La fila es POSICIONAL: si no casa con HEADERS, cada dato cae en la columna
    # de al lado y en silencio. Es lo que mató a `create_project` 3 versiones (v363).
    if len(fila) != len(HEADERS):
        return False, f"internal: {len(fila)} valores para {len(HEADERS)} columnas"
    try:
        ws.append_row(fila, value_input_option="RAW")
    except Exception as e:
        logger.error("correcciones.registrar: no se pudo anotar: %s", e)
        return False, f"{t('Error writing')}: {e}"
    _invalidate()
    return True, cid


def _set(cid, campos: dict) -> tuple:
    ws = _ws()
    if ws is None:
        return False, t("The timeclock is not configured.")
    try:
        valores = ws.get_all_values()
    except Exception as e:
        return False, f"{t('Error reading the sheet')}: {e}"
    fila = next((i for i, r in enumerate(valores[1:], start=2)
                 if r and str(r[0]).strip() == str(cid).strip()), None)
    if fila is None:
        return False, t("Correction not found.")
    try:
        ws.batch_update([{"range": f"{chr(64 + _COL[k])}{fila}", "values": [[v]]}
                         for k, v in campos.items() if k in _COL],
                        value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error writing')}: {e}"
    _invalidate()
    return True, cid


def aprobar(cid, revisor, nota="") -> tuple:
    """El admin confirma la hora que puso el usuario. El fichaje NO se toca: ya
    llevaba esa hora desde que se pidió (decisión del usuario: se aplica ya)."""
    r = get(cid)
    if not r:
        return False, t("Correction not found.")
    if str(r.get("Status", "")).strip().lower() != PENDIENTE:
        return False, t("This correction was already reviewed.")
    ok, msg = _set(cid, {"Status": APROBADA, "ReviewedBy": str(revisor or ""),
                         "ReviewedDate": clock.now(r.get("Group")).strftime(timeclock.FMT),
                         "AdminNote": str(nota or "")})
    return (True, t("Correction approved.")) if ok else (False, msg)


def ajustar(cid, revisor, hora, nota="") -> tuple:
    """El admin FIJA la hora buena, en vez de revertir. Devuelve (ok, mensaje).

    Existe por un caso que revertir no puede resolver: cerrar una sesión OLVIDADA
    no tiene «hora anterior» —estaba abierta—, así que devolverla la pondría otra
    vez a acumular horas contra el reloj (34 h al día siguiente, 130 a los cinco).
    Lo que el admin necesita ahí no es deshacer: es poner la hora correcta.

    ⚠️ Se corrige el fichaje PRIMERO y solo después se marca (orden de v343), y se
    reescribe `ValorNuevo`: si no, el histórico diría una hora y la hoja tendría
    otra — un rastro que miente es peor que no tenerlo.
    """
    r = get(cid)
    if not r:
        return False, t("Correction not found.")
    if str(r.get("Status", "")).strip().lower() != PENDIENTE:
        return False, t("This correction was already reviewed.")
    actual = str(r.get("NewValue", "")).strip()
    from datetime import datetime
    try:
        base = datetime.strptime(actual, timeclock.FMT)
    except Exception:
        return False, t("That entry has an unreadable time.")
    # ⚠️ Solo se cambia la HORA: el DÍA es el del fichaje y moverlo lo pasaría a
    # otra jornada — y con ello a otra nómina y a otro día de costo de obra.
    nuevo = base.replace(hour=getattr(hora, "hour", 0),
                         minute=getattr(hora, "minute", 0),
                         second=0, microsecond=0)
    ok, msg = timeclock.corregir_fichaje(
        grupo=r.get("Group"), usuario=r.get("User"), nombre=r.get("Name"),
        tipo=r.get("Type"), campo=r.get("Field"),
        valor_actual=actual, valor_nuevo=nuevo)
    if not ok:
        return False, f"{t('The time entry could not be updated')}: {msg}"
    ok2, msg2 = _set(cid, {"NewValue": nuevo.strftime(timeclock.FMT),
                           "Status": APROBADA, "ReviewedBy": str(revisor or ""),
                           "ReviewedDate": clock.now(r.get("Group")).strftime(timeclock.FMT),
                           "AdminNote": str(nota or "")})
    if not ok2:
        return False, (t("The time entry was updated, but the correction could not "
                         "be marked as reviewed: ") + str(msg2))
    return True, t("Time set to {x}.", x=nuevo.strftime("%H:%M"))


def revertir(cid, revisor, nota="") -> tuple:
    """El admin rechaza: el fichaje vuelve a la hora que tenía ANTES.

    ⚠️ Se restaura PRIMERO el fichaje y solo después se marca la corrección. Al revés,
    un fallo a mitad dejaría la corrección marcada como revertida con el fichaje aún
    cambiado — o sea, la app diciendo que deshizo algo que sigue hecho. Es el orden
    de v343: primero lo que no se puede quedar a medias.
    """
    r = get(cid)
    if not r:
        return False, t("Correction not found.")
    if str(r.get("Status", "")).strip().lower() != PENDIENTE:
        return False, t("This correction was already reviewed.")
    ok, msg = timeclock.corregir_fichaje(
        grupo=r.get("Group"), usuario=r.get("User"), nombre=r.get("Name"),
        tipo=r.get("Type"), campo=r.get("Field"),
        valor_actual=r.get("NewValue"), valor_nuevo=r.get("OldValue"))
    if not ok:
        return False, f"{t('The time entry could not be restored')}: {msg}"
    ok2, msg2 = _set(cid, {"Status": REVERTIDA, "ReviewedBy": str(revisor or ""),
                           "ReviewedDate": clock.now(r.get("Group")).strftime(timeclock.FMT),
                           "AdminNote": str(nota or "")})
    if not ok2:
        # El fichaje YA se restauró: se dice, en vez de fingir que no pasó nada.
        return False, (t("The time entry was restored, but the correction could not "
                         "be marked as reviewed: ") + str(msg2))
    return True, t("Correction reverted: the original time is back.")
