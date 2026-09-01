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
from core import clock

from core.i18n import t
logger = logging.getLogger(__name__)

TRAB_SHEET   = "Trabajos"
TRAB_HEADERS = ["ID", "Grupo", "Numero", "Nombre", "Color", "ProyectoID", "Activo"]

ROSTER_SHEET   = "Roster"
ROSTER_HEADERS = ["ID", "Grupo", "Semana", "Usuario", "DatosJSON"]

# Días de la semana laboral (claves internas) + etiqueta visible.
DIAS = ["lun", "mar", "mie", "jue", "vie"]          # la semana normal de la cuadrilla
DIAS_EXTRA = ["sab", "dom"]                        # se añaden a una semana concreta (v390)
DIAS_TODOS = DIAS + DIAS_EXTRA                     # ⚠️ el ORDEN es el de weekday()
DIAS_LABEL = {"lun": "Mon", "mar": "Tue", "mie": "Wed", "jue": "Thu", "vie": "Fri",
              "sab": "Sat", "dom": "Sun"}


def dias_con_datos(datos, extra_pedidos=()) -> list:
    """Los días que hay que PINTAR en una semana: los cinco de siempre, más los
    extra que o bien tienen algo asignado o bien se han pedido a mano (v390).

    ⚠️ Un día extra CON datos se muestra siempre, se haya pedido o no: si dependiera
    solo del botón, planificar un sábado y recargar lo escondería — y un dato que la
    app guarda pero no puede enseñar es el fallo de v340 (archivar sin poder volver).
    """
    con_datos = set()
    for _sem in (datos or {}).values():
        for _d, _c in (_sem or {}).items():
            if _d in DIAS_EXTRA and (_norm_cell(_c)["items"] or
                                     _norm_cell(_c)["nota"].strip()):
                con_datos.add(_d)
    pedidos = set(extra_pedidos or ())
    return DIAS + [d for d in DIAS_EXTRA if d in con_datos or d in pedidos]


def dia_tiene_datos(datos, dia) -> list:
    """Usuarios con algo asignado ese día — para no dejar quitar una columna con
    trabajo dentro (y poder DECIR de quién es)."""
    out = []
    for u, _sem in (datos or {}).items():
        c = _norm_cell((_sem or {}).get(dia, {}))
        if c["items"] or c["nota"].strip():
            out.append(u)
    return out

# Estados (NO-trabajo). Claves reservadas (no colisionan con TRB-####). El usuario
# eligió: OFF, Leave, Formación + nota libre.
ESTADOS = {
    "OFF":       {"nombre": "OFF",       "color": "#9aa7b8"},   # gris
    "LEAVE":     {"nombre": "Leave",     "color": "#c0392b"},   # rojo
    "FORMACION": {"nombre": "Training", "color": "#8e44ad"},   # morado
}

# Paleta para los trabajos (el color es clave para leer el tablero de un vistazo).
PALETA = [
    ("Magenta",  "#e84393"), ("Orange",  "#e67e22"), ("Yellow",   "#f1c40f"),
    ("Green",    "#27ae60"), ("Cyan",    "#00b5cc"), ("Blue",     "#2e6da4"),
    ("Pink",     "#f5a6c3"), ("Lilac",   "#9b59b6"), ("Teal",     "#16a085"),
    ("Peach",    "#f6b189"), ("Olive",   "#7f8c8d"), ("Indigo",   "#34495e"),
]
_COLOR_DEFECTO = "#2e6da4"



def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""

def _color_proyecto(pid) -> str:
    """Color estable y distinto para un proyecto (no tiene color propio): derivado de
    su ID sobre la misma PALETA. Usa hashlib (NO hash(), que va salteado por proceso y
    cambiaría el color en cada arranque)."""
    import hashlib
    h = int(hashlib.md5(str(pid).encode("utf-8")).hexdigest(), 16)
    return PALETA[h % len(PALETA)][1]


# ── Utilidades de fecha ──────────────────────────────────────────
def lunes_de(d=None) -> date:
    """Lunes de la semana de `d` (hoy si None)."""
    d = d or clock.today()
    if isinstance(d, datetime):
        d = d.date()
    return d - timedelta(days=d.weekday())


def fecha_de_dia(lunes, dia_key) -> date:
    """Fecha real de un día ('lun'..'dom') de la semana que empieza en `lunes`.
    ⚠️ Índice sobre DIAS_TODOS, que va en el orden de `weekday()`: así 'sab' cae en
    lunes+5 sin tocar la aritmética que ya había."""
    return lunes + timedelta(days=DIAS_TODOS.index(dia_key))


def rango_label(lunes, dias=None, corto=False) -> str:
    """Etiqueta del rango visible. Con sábado en pantalla el rango es hasta el
    sábado — decir «– vie» mientras se ve una columna del sábado sería mentir.

    `corto` quita el año («17 – 21/08»): medido en producción, la versión larga
    necesita ~140 px y en una ventana de 780 su columna tiene 56 → se partía en
    TRES líneas. Al navegar semana a semana el año no aporta (y sigue completo en
    el selector de día), así que se sacrifica antes que la legibilidad."""
    fin = lunes + timedelta(days=DIAS_TODOS.index((dias or DIAS)[-1]))
    if corto:
        return f"{lunes.strftime('%d')} – {fin.strftime('%d/%m')}"
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


@st.cache_data(ttl=120, show_spinner=False)
def _trab_records_cached(libro: str) -> list:
    """Registros de TRABAJOS_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(TRAB_SHEET, TRAB_HEADERS) or []




def _trab_records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _trab_records_cached(_libro_de(TRAB_SHEET))
@st.cache_data(ttl=120, show_spinner=False)
def _roster_records_cached(libro: str) -> list:
    """Registros de ROSTER_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(ROSTER_SHEET, ROSTER_HEADERS) or []




def _roster_records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _roster_records_cached(_libro_de(ROSTER_SHEET))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    # ⚠️ v344 — misma regresión que en `projects` (ver allí): al quitar el bucle en
    # v339 quedó `f.clear()`, un nombre inexistente, y el `except` se tragaba el
    # NameError → el tablero podía seguir enseñando la asignación vieja hasta 120 s.
    from core import hojas
    hojas.invalidar()
    # ⚠️ v378: las CACHEADAS (`*_cached`), no los envoltorios (ver `projects`).
    for fn in (_trab_records_cached, _roster_records_cached):
        try:
            fn.clear()
        except Exception as e:
            logger.warning("roster._invalidate: no se pudo limpiar %s: %s", fn, e)


def _next_id(ws, prefijo) -> str:
    """FRESCO a propósito (ruta de escritura, regla v108).

    ⚠️ v428 — ANTES CONTABA FILAS, y eso producía **colisiones**, no un simple
    reciclaje: `delete_trabajo` borra la fila de verdad cuando el trabajo no está
    asignado en ningún roster, así que al borrar uno del medio el conteo baja y el
    siguiente alta emite un ID **que ya existe**.

    Estaba pasando de verdad. Medido en la hoja real: 4 filas con IDs
    `TRB-0002..TRB-0005`, así que `len-1+1` daba **TRB-0005**, ya usado. Y como
    `trabajos_idx` indexa por ID, uno de los dos habría desaparecido del índice y las
    celdas del tablero que lo tienen asignado resolverían al trabajo equivocado —
    nombre y color de otro— sin ningún error.

    Ahora: **máximo real + 1**, y además saltando los que otra hoja siga referenciando
    (v427). Un trabajo se referencia en `Roster.DatosJSON`, así que reutilizar su ID
    reasignaría solo las celdas del histórico.
    """
    if ws is None:
        return f"{prefijo}-0001"
    mx = 0
    try:
        for fila in ws.get_all_values()[1:]:
            tid = str(fila[0] if fila else "")
            if tid.startswith(f"{prefijo}-"):
                try:
                    mx = max(mx, int(tid.split("-")[1]))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("roster._next_id(%s): %s", prefijo, e)
        return f"{prefijo}-0001"
    try:
        from core import hojas
        return hojas.siguiente_id_libre(f"{prefijo}-", mx,
                                        propia=(TRAB_SHEET if prefijo == "TRB"
                                                else ROSTER_SHEET))
    except Exception as e:
        logger.warning("roster: no se pudo comprobar IDs referenciados: %s", e)
        return f"{prefijo}-{mx + 1:04d}"


# ── Catálogo de trabajos ─────────────────────────────────────────
# Estado "borrado" de un trabajo (v301). NO es lo mismo que inactivo:
#   SI/SÍ/TRUE/1 → activo: se ofrece al asignar y sale en el catálogo.
#   NO           → desactivado: NO se ofrece, pero sigue EN el catálogo (se reactiva).
#   ELIMINADO    → fuera del catálogo y del desplegable, pero la FILA SE CONSERVA para
#                  que `trabajos_idx` siga resolviendo nombre y color de las
#                  asignaciones históricas. Borrar la fila las dejaría mostrando el ID
#                  crudo (TRB-0003) sin color — perder historia sin avisar.
ELIMINADO = "ELIMINADO"
_ACTIVO_OK = ("SI", "SÍ", "TRUE", "1")


def list_trabajos(grupo, incluir_inactivos=False, incluir_eliminados=False) -> list:
    out = []
    for r in _trab_records():
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        _act = str(r.get("Activo", "SI")).strip().upper()
        if _act == ELIMINADO and not incluir_eliminados:
            continue
        if not incluir_inactivos and _act not in _ACTIVO_OK:
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
    """{id: fila} de TODO lo asignable del grupo, para resolver color/etiqueta/proyecto:
    los trabajos del catálogo (TRB-####, activos e inactivos) MÁS los proyectos del grupo
    (PRJ-####) como entradas sintéticas — un proyecto ya es un trabajo en sí mismo (v218),
    así se asigna directo sin duplicarlo en el catálogo. Incluye archivados para que una
    asignación/fichaje histórico a un proyecto archivado siga resolviendo su nombre.
    (TRB-#### y PRJ-#### nunca colisionan; `setdefault` no pisa un trabajo real.)"""
    idx = {str(r.get("ID", "")): r for r in _trab_records()
           if str(r.get("Grupo", "")) == str(grupo)}
    try:
        from core import projects as P
        # ⚠️ v422: **con las localizaciones internas**. Este índice es lo que resuelve
        # nombre y color de un `asig`; sin ellas, asignar el almacén en el tablero
        # pintaría una celda muda — y asignar ahí puntualmente es justo la vía por la
        # que alguien de obra puede fichar en una localización.
        for p in P.list_projects(grupo=grupo, incluir_archivados=True, incluir_internos=True):
            pid = str(p.get("ID", ""))
            if pid:
                idx.setdefault(pid, {"ID": pid, "Numero": "",
                                     "Nombre": str(p.get("Nombre", "")),
                                     "Color": _color_proyecto(pid), "ProyectoID": pid})
    except Exception:
        pass
    return idx


def add_trabajo(grupo, numero, nombre, color, proyecto_id="") -> tuple:
    w = _ws_trab()
    if w is None:
        return False, t("Google Sheets is not configured.")
    if not str(nombre).strip():
        return False, t("The job name is required.")
    tid = _next_id(w, "TRB")
    try:
        w.append_row([tid, str(grupo), str(numero).strip(), str(nombre).strip(),
                      str(color) or _COLOR_DEFECTO, str(proyecto_id or ""), "SI"],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, tid


def update_trabajo(tid, cambios: dict) -> tuple:
    w = _ws_trab()
    if w is None:
        return False, t("Google Sheets is not configured.")
    try:
        recs = w.get_all_values()
        fila = next((i for i, r in enumerate(recs) if r and r[0] == str(tid)), None)
        if fila is None:
            return False, t("Job not found.")
        col = {h: i for i, h in enumerate(TRAB_HEADERS)}
        peticiones = []
        for k, v in cambios.items():
            if k in col:
                a1 = _a1(fila + 1, col[k] + 1)
                peticiones.append({"range": a1, "values": [[str(v)]]})
        if peticiones:
            w.batch_update(peticiones, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating')}: {e}"
    _invalidate()
    return True, t("Job updated.")


def set_activo_trabajo(tid, activo: bool) -> tuple:
    return update_trabajo(tid, {"Activo": "SI" if activo else "NO"})


def usos_de_trabajo(grupo, tid) -> int:
    """En cuántas celdas del roster (todas las semanas) está asignado este trabajo.

    Sirve para decidir si se puede BORRAR sin dejar huérfano el histórico: el
    tablero resuelve nombre y color por ID (`trabajos_idx`), así que borrar un
    trabajo asignado dejaría esas celdas mostrando el ID crudo y sin color.
    Lectura CACHEADA (`_roster_records`), no cuesta una llamada nueva.
    """
    tid = str(tid or "").strip()
    if not tid:
        return 0
    n = 0
    for r in _roster_records():
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        try:
            datos = json.loads(r.get("DatosJSON", "") or "{}")
        except Exception:
            continue
        for d in DIAS:
            for it in _norm_cell(datos.get(d, {}))["items"]:
                if str(it.get("asig", "")) == tid:
                    n += 1
    return n


def delete_trabajo(grupo, tid) -> tuple:
    """Quita un trabajo del catálogo. SIEMPRE se puede (v301).

    Dos caminos según si tiene historia, para que borrar nunca destruya datos:
      · **Sin usar en ningún roster** → se borra la FILA de verdad. No hay nada que
        conservar.
      · **Asignado alguna vez** → se marca `Activo = ELIMINADO`: desaparece del
        catálogo y del desplegable de asignación, pero la fila SIGUE ahí, así que
        `trabajos_idx` continúa resolviendo su nombre y su color en las semanas
        pasadas del tablero. Sin eso, esas celdas mostrarían `TRB-####` sin color.

    (v295 lo IMPEDÍA cuando estaba en uso; el usuario pidió poder borrarlo igual
    «sin eliminar el historial de que existió» — esto es exactamente eso.)
    """
    usos = usos_de_trabajo(grupo, tid)
    if usos:
        ok, _ = update_trabajo(tid, {"Activo": ELIMINADO})
        if not ok:
            return False, t("Could not delete.")
        return True, (t("Job removed from the catalogue. The history is kept: it "
                        "still shows with its name and colour on") + f" {usos} "
                      + (t("day already planned") if usos == 1
                         else t("days already planned")) + ".")
    w = _ws_trab()
    if w is None:
        return False, t("Google Sheets is not configured.")
    try:
        recs = w.get_all_values()          # FRESCO: ruta de escritura (regla v108)
        fila = next((i for i, r in enumerate(recs) if r and r[0] == str(tid)), None)
        if fila is None:
            return False, t("Job not found.")
        w.delete_rows(fila + 1)
    except Exception as e:
        return False, f"{t('Error deleting')}: {e}"
    _invalidate()
    return True, t("Job deleted.")


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


def _norm_cell(c) -> dict:
    """Normaliza una celda a {'items':[{'asig','ini','fin'}], 'asigs':[...], 'nota':str}.

    Compat con TODOS los formatos:
    - viejo `{'asig','nota'}` → 1 item (día completo, sin franja).
    - v274 `{'asigs':[str],'nota'}` → items día completo.
    - v277 `{'items':[{'a','i','f'}],'nota'}` → tal cual (a=asig, i=inicio 'HH:MM', f=fin).
    `ini`/`fin` vacíos = **día completo** (sin franja horaria). `asigs` se deriva de `items`
    para no romper a los consumidores que solo miran la lista de proyectos. Una nota por día."""
    c = c or {}
    items = []
    if "items" in c:
        for it in (c.get("items") or []):
            a = str((it or {}).get("a", "")).strip()
            if a:
                items.append({"asig": a, "ini": str((it or {}).get("i", "") or ""),
                              "fin": str((it or {}).get("f", "") or "")})
    elif "asigs" in c:
        for a in (c.get("asigs") or []):
            a = str(a).strip()
            if a:
                items.append({"asig": a, "ini": "", "fin": ""})
    else:
        a = str(c.get("asig", "")).strip()
        if a:
            items.append({"asig": a, "ini": "", "fin": ""})
    return {"items": items, "asigs": [it["asig"] for it in items],
            "nota": str(c.get("nota", "") or "")}


def _compact(datos) -> dict:
    """Deja solo las celdas no vacías, normalizadas al formato nuevo {'items','nota'}."""
    out = {}
    for k, v in (datos or {}).items():
        n = _norm_cell(v)
        if n["items"] or n["nota"].strip():
            out[k] = {"items": [{"a": it["asig"], "i": it["ini"], "f": it["fin"]}
                               for it in n["items"]],
                      "nota": n["nota"]}
    return out


def celda(semana_datos, usuario, dia) -> dict:
    """Celda como {'asig','nota'} — `asig` = la PRIMERA asignación del día (compat con los
    consumidores de una sola). Para TODAS: `celda_asigs` / `celda_items`. {} si vacía."""
    n = _norm_cell((semana_datos.get(usuario, {}) or {}).get(dia, {}))
    if not n["asigs"] and not n["nota"].strip():
        return {}
    return {"asig": n["asigs"][0] if n["asigs"] else "", "nota": n["nota"]}


def celda_asigs(semana_datos, usuario, dia) -> list:
    """Lista de asignaciones (valores) de una celda; [] si no hay. Varios por día (v274)."""
    return _norm_cell((semana_datos.get(usuario, {}) or {}).get(dia, {}))["asigs"]


def celda_items(semana_datos, usuario, dia) -> list:
    """Asignaciones con franja horaria: [{'asig','ini','fin'}]; [] si no hay (v277).
    `ini`/`fin` vacíos = día completo."""
    return _norm_cell((semana_datos.get(usuario, {}) or {}).get(dia, {}))["items"]


TURNO_DEFAULT = ("07:00", "15:30")   # turno estándar de la cuadrilla (v277)


def franja_label(ini, fin) -> str:
    """'7:00–15:30' desde ('07:00','15:30'); '' si es día completo (sin franja)."""
    ini, fin = str(ini or "").strip(), str(fin or "").strip()
    if not ini and not fin:
        return ""

    def _h(_v):
        try:
            hh, mm = _v.split(":")
            return f"{int(hh)}:{mm}"
        except Exception:
            return _v

    return f"{_h(ini)}–{_h(fin)}" if (ini and fin) else (_h(ini) or _h(fin))


def guardar_persona(grupo, lunes, usuario, dias: dict) -> tuple:
    """Escribe la semana COMPLETA de una persona en UNA fila (1 escritura).

    `dias` = {'lun': {'asig','nota'}, ...}. Las celdas vacías se omiten para no
    engordar el JSON.
    """
    w = _ws_roster()
    if w is None:
        return False, t("Google Sheets is not configured.")
    sem = lunes.isoformat() if hasattr(lunes, "isoformat") else str(lunes)
    limpio = _compact(dias)
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
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, t("Saved.")


def asignaciones_dia(grupo, usuario, fecha=None) -> list:
    """TODAS las asignaciones de una persona un día (varias posibles, v274). Cada una:
    {asig, nota, proyecto_id, etiqueta, color, es_estado}. [] si no hay nada ese día.
    La `nota` es una sola por día (se repite en cada asignación).

    ⚠️ v390: el sábado y el domingo YA NO se descartan de entrada. Antes se cortaba
    por `weekday() > 4` porque la rejilla era Lun–Vie; ahora se puede planificar un
    fin de semana, y devolver [] escondería lo que alguien acaba de asignar (lo vería
    en el tablero y no en su móvil). Si no hay nada guardado, sale [] igual."""
    fecha = fecha or clock.today()
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    dia = DIAS_TODOS[fecha.weekday()]
    lunes = lunes_de(fecha)
    sem = get_semana(grupo, lunes)
    raw = _norm_cell((sem.get(str(usuario), {}) or {}).get(dia, {}))
    if not raw["items"]:
        return []
    tidx = trabajos_idx(grupo)
    return [{"asig": it["asig"], "nota": raw["nota"],
             "ini": it["ini"], "fin": it["fin"],
             "proyecto_id": proyecto_de(it["asig"], tidx),
             "etiqueta": etiqueta_de(it["asig"], tidx),
             "color": color_de(it["asig"], tidx),
             "es_estado": it["asig"] in ESTADOS} for it in raw["items"]]


def copiar_semana(grupo, lunes_origen, lunes_destino) -> tuple:
    """Clona todas las asignaciones de una semana a otra (1 fila por persona)."""
    datos = get_semana(grupo, lunes_origen)
    if not datos:
        return False, t("The source week is empty.")
    n = 0
    for usuario, dias in datos.items():
        ok, _ = guardar_persona(grupo, lunes_destino, usuario, dias)
        n += 1 if ok else 0
    return True, f"{n} " + t("person(s) copied.")


def _a_date(x):
    """ISO 'YYYY-MM-DD' o date/datetime → date; None si no se puede."""
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    try:
        y, m, d = str(x)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


_MAX_SEMANAS = 104   # tope de seguridad (~2 años) para no auto-poblar rangos absurdos


def autopoblar_proyecto(grupo, pid, usuarios, fecha_ini, fecha_fin,
                        solo_vacias=True) -> dict:
    """Rellena el planificador con un PROYECTO (asig=PRJ-####) entre sus fechas, Lun–Vie,
    para los usuarios dados y SOLO en celdas vacías (no pisa OFF ni otro proyecto). v219.

    Eficiente: lee la hoja UNA vez y escribe en 1 `batch_update` (filas existentes) + 1
    `append_rows` (semanas nuevas), así el rango no dispara el rate limit. Devuelve
    {llenadas, ocupadas, actualizadas, nuevas, semanas}."""
    vacio = {"llenadas": 0, "ocupadas": 0, "actualizadas": 0, "nuevas": 0, "semanas": 0}
    w = _ws_roster()
    if w is None or not usuarios or not pid:
        return vacio
    ini, fin = _a_date(fecha_ini), _a_date(fecha_fin)
    if not ini or not fin or fin < ini:
        return vacio
    usuarios = [str(u) for u in usuarios]

    semanas = []
    lun = lunes_de(ini)
    while lun <= fin and len(semanas) < _MAX_SEMANAS:
        semanas.append(lun)
        lun = lun + timedelta(days=7)

    try:
        vals = w.get_all_values()
    except Exception:
        return vacio
    existentes = {}                       # (semana, usuario) -> (row_idx0, datos)
    for i, r in enumerate(vals):
        if i == 0:                        # cabecera
            continue
        r = list(r) + [""] * (5 - len(r))
        if str(r[1]) != str(grupo):
            continue
        try:
            d = json.loads(r[4] or "{}")
        except Exception:
            d = {}
        existentes[(str(r[2]), str(r[3]))] = (i, d)

    llenadas = ocupadas = 0
    updates, nuevas = [], []
    next_n = len(vals)                    # id incremental para filas nuevas
    for lu in semanas:
        sem = lu.isoformat()
        # ⚠️ Los días extra (sáb/dom) NO se rellenan por defecto: la semana normal es
        # de cinco días y auto-poblar el fin de semana convertiría la excepción en
        # norma, llenando los sábados de todo el mundo (v390). Pero si en ESA semana
        # ya hay alguien trabajando ese día, la cuadrilla sí trabaja ese día y dejar
        # al recién asignado fuera obligaría a añadirlo a mano, persona por persona.
        # La condición sale del DATO, no de una preferencia que haya que mantener.
        _dias_sem = list(DIAS) + [
            d for d in DIAS_EXTRA
            if any(_norm_cell((dat or {}).get(d))["items"]
                   for (s, _u), (_i, dat) in existentes.items() if s == sem)]
        for u in usuarios:
            idx0, datos = existentes.get((sem, u), (None, {}))
            datos = dict(datos)
            cambiado = False
            for dk in _dias_sem:
                fdia = lu + timedelta(days=DIAS_TODOS.index(dk))
                if fdia < ini or fdia > fin:
                    continue
                cell = _norm_cell(datos.get(dk))
                if cell["asigs"]:
                    if str(pid) not in cell["asigs"]:
                        ocupadas += 1     # ya tiene asignación(es): no se pisa (solo vacías)
                    continue
                datos[dk] = {"items": [{"a": str(pid), "i": "", "f": ""}], "nota": ""}
                llenadas += 1
                cambiado = True
            if not cambiado:
                continue
            payload = json.dumps(_compact(datos), ensure_ascii=False)
            if idx0 is not None:
                updates.append({"range": _a1(idx0 + 1, 5), "values": [[payload]]})
            else:
                next_n += 1
                nuevas.append([f"ROS-{next_n:04d}", str(grupo), sem, str(u), payload])

    try:
        if updates:
            w.batch_update(updates, value_input_option="RAW")
        if nuevas:
            w.append_rows(nuevas, value_input_option="RAW")
    except Exception as e:
        logger.warning("autopoblar_proyecto: %s", e)
        return vacio
    _invalidate()
    return {"llenadas": llenadas, "ocupadas": ocupadas,
            "actualizadas": len(updates), "nuevas": len(nuevas), "semanas": len(semanas)}


def limpiar_proyecto(grupo, pid, usuarios=None) -> int:
    """Quita del planificador TODAS las celdas asignadas a un proyecto (para cuando se
    desasigna a alguien). Si `usuarios` se da, solo esas personas. 1 `batch_update`. v219."""
    w = _ws_roster()
    if w is None or not pid:
        return 0
    us = set(str(u) for u in usuarios) if usuarios else None
    try:
        vals = w.get_all_values()
    except Exception:
        return 0
    updates, quitadas = [], 0
    for i, r in enumerate(vals):
        if i == 0:
            continue
        r = list(r) + [""] * (5 - len(r))
        if str(r[1]) != str(grupo):
            continue
        if us is not None and str(r[3]) not in us:
            continue
        try:
            datos = json.loads(r[4] or "{}")
        except Exception:
            continue
        ch = False
        for dk in list(datos.keys()):
            n = _norm_cell(datos.get(dk))
            if str(pid) in n["asigs"]:
                rest = [it for it in n["items"] if it["asig"] != str(pid)]
                if rest or n["nota"].strip():
                    datos[dk] = {"items": [{"a": it["asig"], "i": it["ini"], "f": it["fin"]}
                                          for it in rest], "nota": n["nota"]}
                else:
                    datos.pop(dk)
                ch = True
                quitadas += 1
        if ch:
            updates.append({"range": _a1(i + 1, 5),
                            "values": [[json.dumps(_compact(datos), ensure_ascii=False)]]})
    try:
        if updates:
            w.batch_update(updates, value_input_option="RAW")
    except Exception as e:
        logger.warning("limpiar_proyecto: %s", e)
        return 0
    _invalidate()
    return quitadas
