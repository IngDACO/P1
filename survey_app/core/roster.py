"""
Tablero semanal de asignación de cuadrilla (roster / dispatch) — v159.

Dos entidades nuevas, ambas por grupo (multi-tenant):
- **Trabajos** (catálogo): número + nombre + color + enlace OPCIONAL a un proyecto
  PRJ. Cubre lo que NO es un elevador (entregas, cursos, policía) sin ensuciar
  los proyectos; cuando enlaza a un PRJ, conecta con fichaje/costos.
- **Roster**: una fila por persona×semana con la asignación de Lun–Vie en JSON.
  Cada día es un trabajo (TRB-####) O un estado (OFF/LEAVE/FORMACION) + una nota
  libre (vehículo, equipo, horario, instrucción).

El diseño se acordó con el usuario antes de construir (una asignación por día,
semana Lun–Vie con "copiar la semana anterior", el campo ve todo el tablero).
"""
import json
import logging
from datetime import date, datetime, timedelta

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

TRAB_SHEET   = "Trabajos"
TRAB_HEADERS = ["ID", "Grupo", "Numero", "Nombre", "Color", "ProyectoID", "Activo"]

ROSTER_SHEET   = "Roster"
ROSTER_HEADERS = ["ID", "Grupo", "Semana", "Usuario", "DatosJSON"]

# Días de la semana laboral (claves internas) + etiqueta visible.
DIAS = ["lun", "mar", "mie", "jue", "vie"]
DIAS_LABEL = {"lun": "Lun", "mar": "Mar", "mie": "Mié", "jue": "Jue", "vie": "Vie"}

# Estados (NO-trabajo). Claves reservadas (no colisionan con TRB-####). El usuario
# eligió: OFF, Leave, Formación + nota libre.
ESTADOS = {
    "OFF":       {"nombre": "OFF",       "color": "#9aa7b8"},   # gris
    "LEAVE":     {"nombre": "Leave",     "color": "#c0392b"},   # rojo
    "FORMACION": {"nombre": "Formación", "color": "#8e44ad"},   # morado
}

# Paleta para los trabajos (el color es clave para leer el tablero de un vistazo).
PALETA = [
    ("Magenta",  "#e84393"), ("Naranja", "#e67e22"), ("Amarillo", "#f1c40f"),
    ("Verde",    "#27ae60"), ("Cian",    "#00b5cc"), ("Azul",     "#2e6da4"),
    ("Rosa",     "#f5a6c3"), ("Lila",    "#9b59b6"), ("Teal",     "#16a085"),
    ("Durazno",  "#f6b189"), ("Oliva",   "#7f8c8d"), ("Índigo",   "#34495e"),
]
_COLOR_DEFECTO = "#2e6da4"


# ── Utilidades de fecha ──────────────────────────────────────────
def lunes_de(d=None) -> date:
    """Lunes de la semana de `d` (hoy si None)."""
    d = d or date.today()
    if isinstance(d, datetime):
        d = d.date()
    return d - timedelta(days=d.weekday())


def semana_str(d=None) -> str:
    return lunes_de(d).isoformat()


def fecha_de_dia(lunes, dia_key) -> date:
    """Fecha real de un día ('lun'..'vie') de la semana que empieza en `lunes`."""
    return lunes + timedelta(days=DIAS.index(dia_key))


def rango_label(lunes) -> str:
    fin = lunes + timedelta(days=4)
    return f"{lunes.strftime('%d/%m')} – {fin.strftime('%d/%m/%Y')}"


def is_configured() -> bool:
    return timeclock.is_configured()


# ── Hojas ────────────────────────────────────────────────────────
def _ws_trab():
    try:
        return timeclock.get_sheet(TRAB_SHEET, TRAB_HEADERS)
    except Exception as e:
        logger.warning("roster/trabajos: no se pudo abrir la hoja: %s", e)
        return None


def _ws_roster():
    try:
        return timeclock.get_sheet(ROSTER_SHEET, ROSTER_HEADERS)
    except Exception as e:
        logger.warning("roster: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=30, show_spinner=False)
def _trab_records() -> list:
    w = _ws_trab()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _roster_records() -> list:
    w = _ws_roster()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate():
    for f in (_trab_records, _roster_records):
        try:
            f.clear()
        except Exception:
            pass


def _next_id(ws, prefijo) -> str:
    """FRESCO a propósito (ruta de escritura, regla v108)."""
    if ws is None:
        return f"{prefijo}-0001"
    try:
        n = len(ws.get_all_values()) - 1
    except Exception:
        n = 0
    return f"{prefijo}-{max(0, n) + 1:04d}"


# ── Catálogo de trabajos ─────────────────────────────────────────
def list_trabajos(grupo, incluir_inactivos=False) -> list:
    out = []
    for r in _trab_records():
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        if not incluir_inactivos and str(r.get("Activo", "SI")).upper() not in ("SI", "SÍ", "TRUE", "1"):
            continue
        out.append(r)
    out.sort(key=lambda r: _num_orden(r.get("Numero", "")))
    return out


def _num_orden(v):
    """Ordena por número si es numérico, si no alfabético al final."""
    try:
        return (0, float(str(v).strip()))
    except Exception:
        return (1, str(v))


def trabajos_idx(grupo) -> dict:
    """{TRB-id: fila} de todos los trabajos del grupo (activos e inactivos), para
    resolver color/etiqueta aunque un trabajo se haya desactivado."""
    return {str(r.get("ID", "")): r for r in _trab_records()
            if str(r.get("Grupo", "")) == str(grupo)}


def add_trabajo(grupo, numero, nombre, color, proyecto_id="") -> tuple:
    w = _ws_trab()
    if w is None:
        return False, "Google Sheets no está configurado."
    if not str(nombre).strip():
        return False, "El nombre del trabajo es obligatorio."
    tid = _next_id(w, "TRB")
    try:
        w.append_row([tid, str(grupo), str(numero).strip(), str(nombre).strip(),
                      str(color) or _COLOR_DEFECTO, str(proyecto_id or ""), "SI"],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"Error guardando: {e}"
    _invalidate()
    return True, tid


def update_trabajo(tid, cambios: dict) -> tuple:
    w = _ws_trab()
    if w is None:
        return False, "Google Sheets no está configurado."
    try:
        recs = w.get_all_values()
        fila = next((i for i, r in enumerate(recs) if r and r[0] == str(tid)), None)
        if fila is None:
            return False, "Trabajo no encontrado."
        col = {h: i for i, h in enumerate(TRAB_HEADERS)}
        peticiones = []
        for k, v in cambios.items():
            if k in col:
                a1 = _a1(fila + 1, col[k] + 1)
                peticiones.append({"range": a1, "values": [[str(v)]]})
        if peticiones:
            w.batch_update(peticiones, value_input_option="RAW")
    except Exception as e:
        return False, f"Error actualizando: {e}"
    _invalidate()
    return True, "Trabajo actualizado."


def set_activo_trabajo(tid, activo: bool) -> tuple:
    return update_trabajo(tid, {"Activo": "SI" if activo else "NO"})


def _a1(fila, col) -> str:
    """(fila, col) 1-indexado → 'A1'. col máx 26 nos sobra (7 columnas)."""
    return f"{chr(64 + col)}{fila}"


# ── Resolución de una celda (trabajo o estado) ───────────────────
def color_de(asig, tidx) -> str:
    asig = str(asig or "")
    if asig in ESTADOS:
        return ESTADOS[asig]["color"]
    r = tidx.get(asig)
    if r:
        return str(r.get("Color", "")) or _COLOR_DEFECTO
    return "#eef1f5"          # sin asignar


def etiqueta_de(asig, tidx) -> str:
    asig = str(asig or "")
    if not asig:
        return ""
    if asig in ESTADOS:
        return ESTADOS[asig]["nombre"]
    r = tidx.get(asig)
    if r:
        num = str(r.get("Numero", "")).strip()
        return (f"{num}. {r.get('Nombre','')}" if num else str(r.get("Nombre", "")))
    return "?"


def proyecto_de(asig, tidx) -> str:
    """PRJ enlazado a la asignación (o '' si es estado / trabajo sin enlace)."""
    r = tidx.get(str(asig or ""))
    return str(r.get("ProyectoID", "")).strip() if r else ""


# ── Roster semanal ───────────────────────────────────────────────
def get_semana(grupo, lunes) -> dict:
    """{usuario: {'lun': {'asig','nota'}, ...}} de la semana. Días ausentes = {}."""
    sem = lunes.isoformat() if hasattr(lunes, "isoformat") else str(lunes)
    out = {}
    for r in _roster_records():
        if str(r.get("Grupo", "")) != str(grupo) or str(r.get("Semana", "")) != sem:
            continue
        try:
            datos = json.loads(r.get("DatosJSON", "") or "{}")
        except Exception:
            datos = {}
        out[str(r.get("Usuario", ""))] = datos
    return out


def celda(semana_datos, usuario, dia) -> dict:
    """{'asig','nota'} de una celda; {} si no hay."""
    return (semana_datos.get(usuario, {}) or {}).get(dia, {}) or {}


def guardar_persona(grupo, lunes, usuario, dias: dict) -> tuple:
    """Escribe la semana COMPLETA de una persona en UNA fila (1 escritura).

    `dias` = {'lun': {'asig','nota'}, ...}. Las celdas vacías se omiten para no
    engordar el JSON.
    """
    w = _ws_roster()
    if w is None:
        return False, "Google Sheets no está configurado."
    sem = lunes.isoformat() if hasattr(lunes, "isoformat") else str(lunes)
    limpio = {d: v for d, v in (dias or {}).items()
              if v and (str(v.get("asig", "")).strip() or str(v.get("nota", "")).strip())}
    payload = json.dumps(limpio, ensure_ascii=False)
    try:
        recs = w.get_all_values()
        fila = next((i for i, r in enumerate(recs)
                     if r and str(r[1]) == str(grupo) and str(r[2]) == sem
                     and str(r[3]) == str(usuario)), None)
        if fila is None:
            rid = _next_id(w, "ROS")
            w.append_row([rid, str(grupo), sem, str(usuario), payload],
                         value_input_option="RAW")
        else:
            w.batch_update([{"range": _a1(fila + 1, 5), "values": [[payload]]}],
                           value_input_option="RAW")
    except Exception as e:
        return False, f"Error guardando: {e}"
    _invalidate()
    return True, "Guardado."


def asignacion_dia(grupo, usuario, fecha=None) -> dict:
    """Qué le toca a una persona un día concreto (hoy si None).

    Devuelve {asig, nota, proyecto_id, etiqueta, color, es_estado}. Vacío si el
    día no es laboral (fin de semana) o no hay asignación. Lo usan el fichaje
    (pre-proponer el proyecto) y la vista del campo.
    """
    fecha = fecha or date.today()
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    wd = fecha.weekday()                       # 0=lun .. 6=dom
    if wd > 4:                                 # sáb/dom: no hay rejilla
        return {}
    dia = DIAS[wd]
    lunes = lunes_de(fecha)
    c = celda(get_semana(grupo, lunes), str(usuario), dia)
    asig = str(c.get("asig", ""))
    if not asig and not str(c.get("nota", "")).strip():
        return {}
    tidx = trabajos_idx(grupo)
    return {"asig": asig, "nota": str(c.get("nota", "")),
            "proyecto_id": proyecto_de(asig, tidx),
            "etiqueta": etiqueta_de(asig, tidx),
            "color": color_de(asig, tidx),
            "es_estado": asig in ESTADOS}


def copiar_semana(grupo, lunes_origen, lunes_destino) -> tuple:
    """Clona todas las asignaciones de una semana a otra (1 fila por persona)."""
    datos = get_semana(grupo, lunes_origen)
    if not datos:
        return False, "La semana de origen está vacía."
    n = 0
    for usuario, dias in datos.items():
        ok, _ = guardar_persona(grupo, lunes_destino, usuario, dias)
        n += 1 if ok else 0
    return True, f"{n} persona(s) copiada(s)."
