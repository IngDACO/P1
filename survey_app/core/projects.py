"""
Gestión de proyectos (un proyecto = un elevador) con persistencia en Google Sheets.

Modelo (ver CLAUDE.md):
  - Proyecto = 1 elevador. Se inicia con el survey (params + matriz + interpretaciones)
    y su cronograma. El avance = Σ(peso_actividad × avance) / Σ(peso).
  - Actividades = filas del cronograma; el usuario de campo actualiza su Avance%.
  - Agrupaciones = varios proyectos con peso; avance = Σ(peso_proy × avance_proy)/Σ(peso).
  - Horas: se suman del fichaje (hoja del timeclock) por nombre de proyecto.

Reusa la conexión del fichaje (core.timeclock._get_worksheet) y la misma hoja de cálculo.
Escrituras RAW + lecturas con numericise_ignore=['all'] (conserva textos/JSON/ceros).
"""
import json
import logging
from datetime import date

import streamlit as st

from core import timeclock
from core import clock
from core.num import col_letter as _col_letter, num as _num

logger = logging.getLogger(__name__)

PROJECTS_SHEET   = "Proyectos"
ACTIVITIES_SHEET = "Actividades"
GROUPINGS_SHEET  = "Agrupaciones"

PROJECTS_HEADERS = [
    "ID", "Grupo", "Nombre", "Cliente", "Ubicacion", "Modelo", "NS",
    "Estado", "EstadoManual", "FechaInicio", "FechaFinEst", "Ingeniero",
    "CampoAsignados", "Avance", "AgrupacionID", "PesoEnAgrupacion",
    "ParamsJSON", "MatrizJSON", "InterpJSON", "CreadoPor", "Creado",
    "Instrucciones", "InduccionLinks", "Presupuesto",
    # v137: datos leidos del PLANO (distintos de ParamsJSON, que es el survey e
    # incluye lo medido en obra). Se extraen UNA vez al cargar el plano y los
    # consumen las 5 herramientas sin volver a abrir el PDF.
    "PlanoJSON",
    # v193: coordenadas para el pin en el mapa (se fijan con el selector de ubicación).
    "Lat", "Lng",
    # v219: certificados/tickets que EXIGE el proyecto (tipos del catálogo, `;`), para
    # avisar y marcar a los asignados que no cumplen.
    "CertsReq",
    # v255: enlace robusto al cliente (CLI-#### de la hoja Clientes). El campo `Cliente`
    # (texto) se conserva; el match usa ID-primero, nombre-de-respaldo (como el fichaje, v145).
    "ClienteID",
    # v257: margen (%) sobre la mano de obra para facturar al cliente. Vacío = usa el
    # default del grupo (Grupos.MargenDefault). Base de la 'tarifa de venta' (Fase 1 finanzas).
    "MargenMO",
    # v306: qué clase de trabajo es. NO es cosmético: solo la instalación tiene el
    # cronograma estándar de 11 actividades que escalan con el NS, y ese plan alimenta
    # avance, curva S, SPI y el indicador «En retraso». Los proyectos anteriores a v306
    # lo tienen VACÍO a propósito (no se tocó la hoja): se muestran como "sin tipo".
    "Tipo",
]

# Tipos de proyecto (v306). `TIPO_INSTALACION` es el único que genera el cronograma
# estándar de obra; los demás nacen con UNA actividad genérica (ver `create_project`).
TIPO_INSTALACION = "Instalación"
TIPOS = [TIPO_INSTALACION, "Delivery", "Ripout", "Otro"]
TIPO_ICONO = {TIPO_INSTALACION: ":material/construction:", "Delivery": ":material/local_shipping:",
              "Ripout": ":material/delete_sweep:", "Otro": ":material/category:"}
ACTIVITIES_HEADERS = [
    "ProyectoID", "Orden", "Nombre", "DuracionDias", "Peso", "Avance",
    "FechaInicioReal", "FechaFinReal", "Nota",
]
GROUPINGS_HEADERS = ["ID", "Grupo", "Nombre", "Descripcion"]
DOCUMENTS_SHEET   = "Documentos"
DOCUMENTS_HEADERS = ["ProyectoID", "Nombre", "Tipo", "DriveID", "SubidoPor", "Fecha"]

_PCOL = {h: i + 1 for i, h in enumerate(PROJECTS_HEADERS)}
_ACOL = {h: i + 1 for i, h in enumerate(ACTIVITIES_HEADERS)}

ESTADOS_MANUAL = ["", "En pausa", "Cancelado", "Archivado"]
FMT_DATE = "%Y-%m-%d"


def is_configured() -> bool:
    return timeclock._secrets_present()


def etiqueta_proyectos(proys) -> dict:
    """`{ID: etiqueta única}` para cualquier desplegable/tabla de proyectos.

    El **ID es la identidad** (único, irrepetible, lo pone el sistema); el nombre es
    solo comodidad para el usuario y **puede repetirse** — `create_project` avisa de
    los duplicados pero no los impide, a propósito (dos elevadores en la misma torre
    se llaman igual).

    ⚠️ Por eso NUNCA se debe indexar un dict de proyectos por nombre: los homónimos
    colapsan y uno se vuelve inalcanzable EN SILENCIO. Ya pasó tres veces (v147 con
    documentos, v150 con el fichaje, y hasta v306 en Panel→Asignar, Facturas e
    Inventario). Aquí la clave es el ID y el nombre solo se muestra.

    La etiqueta lleva el ID detrás **solo si el nombre se repite**: sin colisión la
    pantalla queda limpia, y con colisión se pueden distinguir.
    """
    _vistos = {}
    for p in proys or []:
        _vistos[str(p.get("Nombre") or "")] = _vistos.get(str(p.get("Nombre") or ""), 0) + 1
    out = {}
    for p in proys or []:
        _pid = str(p.get("ID") or "")
        _nom = str(p.get("Nombre") or "") or "(sin nombre)"
        out[_pid] = f"{_nom} ({_pid})" if _vistos.get(str(p.get("Nombre") or ""), 0) > 1 else _nom
    return out


# ── Worksheets (crea la pestaña si no existe) ────────────────────
def _get_ws(title, headers):
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(title, tuple(headers)), None
    except Exception as e:
        logger.warning("projects: no se pudo abrir la hoja %s: %s", title, e)
        return None, f"No se pudo abrir la hoja {title}: {e}"


def _projects_ws():   return _get_ws(PROJECTS_SHEET,   PROJECTS_HEADERS)
def _activities_ws(): return _get_ws(ACTIVITIES_SHEET, ACTIVITIES_HEADERS)
def _groupings_ws():  return _get_ws(GROUPINGS_SHEET,  GROUPINGS_HEADERS)


# ── Lecturas CACHEADAS (evitan golpear la API en cada rerun) ─────
# Google Sheets limita ~60 lecturas/min. Sin caché, cada slider/rerun re-leía
# las hojas y disparaba APIError (429). Se cachea 20s y se invalida al escribir.
_HEADERS_BY_TITLE = {
    PROJECTS_SHEET:   PROJECTS_HEADERS,
    ACTIVITIES_SHEET: ACTIVITIES_HEADERS,
    GROUPINGS_SHEET:  GROUPINGS_HEADERS,
    DOCUMENTS_SHEET:  DOCUMENTS_HEADERS,
}


@st.cache_data(ttl=120, show_spinner=False)
def _records(title):
    """Registros de una hoja (cacheados). Solo lecturas de DISPLAY."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(title, _HEADERS_BY_TITLE.get(title, [])) or []


@st.cache_data(ttl=120, show_spinner=False)
def _fichaje_records():
    """Registros del fichaje (cacheados) para sumar horas."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Sheet1", timeclock.HEADERS) or []


def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        fn.clear()
    except Exception:
        pass


# ── Helpers de dominio ───────────────────────────────────────────
def compute_avance(activities: list) -> float:
    """% del proyecto = Σ(peso × avance) / Σ(peso).  activities: list de dicts."""
    tot_peso = sum(_num(a.get("Peso")) for a in activities)
    if tot_peso <= 0:
        return 0.0
    acc = sum(_num(a.get("Peso")) * _num(a.get("Avance")) for a in activities)
    return round(acc / tot_peso, 1)


def derive_estado(avance: float, estado_manual: str = "") -> str:
    """Estado automático por avance, salvo override manual (En pausa / Cancelado)."""
    if estado_manual in ("En pausa", "Cancelado", "Archivado"):
        return estado_manual
    if avance <= 0:
        return "Planificado"
    if avance >= 100:
        return "Completado"
    return "En progreso"


def _next_project_id(pws) -> str:
    """PRJ-#### incremental (máximo existente + 1)."""
    mx = 0
    for r in pws.get_all_records(numericise_ignore=["all"]):
        pid = str(r.get("ID", ""))
        if pid.startswith("PRJ-"):
            try:
                mx = max(mx, int(pid.split("-")[1]))
            except Exception:
                pass
    return f"PRJ-{mx + 1:04d}"


def _find_row(ws, header, value):
    """Nº de fila (1-based, incluye cabecera) del primer registro con header==value."""
    records = ws.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(records):
        if str(r.get(header, "")) == str(value):
            return i + 2  # +1 cabecera, +1 base-1
    return None


# ── Agrupaciones ─────────────────────────────────────────────────
def list_groupings(grupo: str = None) -> list:
    out = []
    for r in _records(GROUPINGS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        out.append(r)
    return out


def create_grouping(grupo: str, nombre: str, descripcion: str = "") -> tuple:
    gws, err = _groupings_ws()
    if err:
        return False, err
    existing = gws.get_all_records(numericise_ignore=["all"])
    mx = 0
    for r in existing:
        gid = str(r.get("ID", ""))
        if gid.startswith("AGR-"):
            try:
                mx = max(mx, int(gid.split("-")[1]))
            except Exception:
                pass
        if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")) == nombre:
            return False, "Ya existe una agrupación con ese nombre en el grupo."
    gid = f"AGR-{mx + 1:04d}"
    gws.append_row([gid, grupo, nombre, descripcion], value_input_option="RAW")
    _invalidate()
    return True, gid


def delete_grouping(gid: str) -> tuple:
    gws, err = _groupings_ws()
    if err:
        return False, err
    row = _find_row(gws, "ID", gid)
    if row is None:
        return False, "Agrupación no encontrada."
    gws.delete_rows(row)
    _invalidate()
    return True, "Agrupación eliminada."


# ── Proyectos ────────────────────────────────────────────────────
def create_project(grupo, nombre, cliente="", ubicacion="", modelo="", ns=0,
                   ingeniero="", campo_asignados=None, fecha_inicio="", fecha_fin_est="",
                   params=None, matriz=None, interp=None, activities=None,
                   creado_por="", agrupacion_id="", peso_agrupacion=0,
                   instrucciones="", induccion_links="", presupuesto="",
                   lat="", lng="", certs_req="", cliente_id="", margen_mo="",
                   tipo="") -> tuple:
    """Crea un proyecto (fila en Proyectos + filas en Actividades). Devuelve (ok, id|error)."""
    pws, err = _projects_ws()
    if err:
        return False, err
    aws, err2 = _activities_ws()
    if err2:
        return False, err2

    pid = _next_project_id(pws)
    campo = ";".join(campo_asignados or [])
    avance = compute_avance(activities or [])
    estado = derive_estado(avance, "")

    row = [
        pid, grupo, nombre, cliente, ubicacion, modelo, str(ns),
        estado, "", fecha_inicio, fecha_fin_est, ingeniero,
        campo, str(avance), agrupacion_id, str(peso_agrupacion),
        json.dumps(params or {}, ensure_ascii=False, default=str),
        json.dumps(matriz or [], ensure_ascii=False, default=str),
        json.dumps(interp or {}, ensure_ascii=False, default=str),
        creado_por, clock.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(instrucciones or ""), str(induccion_links or ""), str(presupuesto or ""),
        "",                                 # PlanoJSON (se llena aparte con plan_data.guardar)
        str(lat or ""), str(lng or ""),     # v194: coordenadas fijadas al crear (pin en el mapa)
        str(certs_req or ""),               # v219: certificados requeridos por el proyecto
        str(cliente_id or ""),              # v255: enlace robusto a la ficha de cliente
        str(margen_mo or ""),               # v257: margen % sobre MO (vacío = default del grupo)
        str(tipo or ""),                    # v306: instalación / delivery / ripout / otro
    ]
    # ⚠️ La fila es POSICIONAL: si no cuadra con la cabecera, cada dato se guarda en la
    # columna de al lado (silencioso y difícil de ver). Se comprueba aquí, no en un test.
    if len(row) != len(PROJECTS_HEADERS):
        return False, (f"Error interno: la fila tiene {len(row)} valores y la cabecera "
                       f"{len(PROJECTS_HEADERS)} columnas.")
    pws.append_row(row, value_input_option="RAW")

    # Actividades del cronograma (batch: 1 sola llamada a la API)
    act_rows = [[
        pid, str(i + 1), a.get("nombre", a.get("Nombre", f"Actividad {i+1}")),
        str(a.get("duracion", a.get("DuracionDias", 0))),
        str(a.get("peso", a.get("Peso", 0))),
        "0", "", "", "",
    ] for i, a in enumerate(activities or [])]
    if act_rows:
        aws.append_rows(act_rows, value_input_option="RAW")
    _invalidate()
    return True, pid


def attach_survey(pid: str, params: dict = None, matriz=None,
                  interp: dict = None) -> tuple:
    """Adjunta el resultado de un survey a un proyecto YA EXISTENTE.

    Desde v135 el survey no crea el proyecto: es una herramienta que lo
    alimenta, como Plomadas o Corte de rieles. Esto escribe las columnas
    ParamsJSON/MatrizJSON/InterpJSON, de las que depende "Reconstruir proyecto
    en el Survey" (y el recalculo determinista de `survey_calc.recalcular`).

    ⚠️ NO toca las actividades: el cronograma se crea con el proyecto y el
    campo ya puede haber cargado avances. Sobrescribirlo aquí los borraría.
    """
    campos = {}
    if params is not None:
        campos["ParamsJSON"] = json.dumps(params or {}, ensure_ascii=False, default=str)
    if matriz is not None:
        campos["MatrizJSON"] = json.dumps(matriz or [], ensure_ascii=False, default=str)
    if interp is not None:
        campos["InterpJSON"] = json.dumps(interp or {}, ensure_ascii=False, default=str)
    if not campos:
        return False, "Nada que adjuntar."
    return update_project(pid, campos)


def parse_links(text) -> list:
    """Lista de links (uno por línea) desde el texto de InduccionLinks."""
    return [l.strip() for l in str(text or "").splitlines() if l.strip()]


def _gaps_for(proys) -> dict:
    """{pid: dias_gap} de la proyección (SPI) de los proyectos activos.
    dias_gap > 0 = retraso, < 0 = adelanto."""
    out = {}
    for p in proys:
        if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
            continue
        try:
            ps = project_schedule(p.get("ID"))
            pr = ps.get("proj") if ps else None
            if pr and pr.get("pv", 0) > 0:
                out[str(p.get("ID", ""))] = pr.get("dias_gap", 0)
        except Exception:
            pass
    return out


@st.cache_data(ttl=120, show_spinner=False)
def gaps_by_group(grupo) -> dict:
    """{pid: dias_gap} del grupo, CACHEADO 60 s. El cronograma de cada proyecto se
    reconstruía varias veces por render (KPIs + tarjetas + tabla + radar)."""
    return _gaps_for(list_projects(grupo=grupo))


@st.cache_data(ttl=120, show_spinner=False)
def projections_by_group(grupo) -> dict:
    """{pid: {"fecha","spi","gap"}} del grupo, CACHEADO 60 s.

    `project_schedule` reconstruye el cronograma de un proyecto y NO esta
    cacheado. Sin esto, pintar la fecha de entrega en una lista de N
    agrupaciones × M elevadores lo recalculaba todo en cada rerun — el mismo
    problema que resolvio `gaps_by_group` en v107.
    """
    out = {}
    for p in list_projects(grupo=grupo):
        pid = str(p.get("ID", ""))
        try:
            ps = project_schedule(pid)
            pr = ps.get("proj") if ps else None
            if pr:
                out[pid] = {"fecha": pr.get("fecha_proj"), "spi": pr.get("spi"),
                            "gap": pr.get("dias_gap")}
        except Exception:
            pass
    return out


def delays_for(proys) -> dict:
    """{pid: días de RETRASO} (proyección SPI)."""
    return {k: v for k, v in _gaps_for(proys).items() if v > 0.5}


def aheads_for(proys) -> dict:
    """{pid: días de ADELANTO} (proyección SPI)."""
    return {k: abs(v) for k, v in _gaps_for(proys).items() if v < -0.5}


def delays_of_group(grupo) -> dict:
    return {k: v for k, v in gaps_by_group(grupo).items() if v > 0.5}


def aheads_of_group(grupo) -> dict:
    return {k: abs(v) for k, v in gaps_by_group(grupo).items() if v < -0.5}


ARCHIVADO = "Archivado"


def list_projects(grupo: str = None, agrupacion_id: str = None,
                  incluir_archivados: bool = False) -> list:
    """Proyectos del grupo. **Oculta los archivados salvo que se pidan** (v149).

    ⚠️ Archivar sustituye a borrar: `delete_project` solo quitaba el proyecto y
    sus actividades, dejando huerfanos sus documentos (con sus archivos en
    Drive), gastos, calculos, pre-starts, alarmas y fichajes. Datos de obra que
    pueden hacer falta despues.

    ⚠️ El defecto es OCULTAR, asi que las **busquedas por identidad** tienen que
    pedir `incluir_archivados=True` explicitamente: `plan_data.del_proyecto`,
    el mapa nombre->ID de `project_hours_bulk`, el proyecto del clock-in
    (`plan_ui`) y el chequeo de nombres duplicados. Si no, archivar romperia esas
    resoluciones en silencio.
    """
    out = []
    for r in _records(PROJECTS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if agrupacion_id is not None and str(r.get("AgrupacionID", "")) != str(agrupacion_id):
            continue
        if not incluir_archivados and str(r.get("Estado", "")) == ARCHIVADO:
            continue
        out.append(r)
    return out


def set_archivado(pid: str, archivar: bool = True) -> tuple:
    """Archiva o restaura un proyecto. No borra nada."""
    prj = get_project(pid)
    if not prj:
        return False, "Proyecto no encontrado."
    if archivar:
        return update_project(pid, {"EstadoManual": ARCHIVADO, "Estado": ARCHIVADO})
    return update_project(pid, {"EstadoManual": "",
                                "Estado": derive_estado(_num(prj.get("Avance")), "")})


def datos_asociados(pid: str) -> dict:
    """Cuanto cuelga de este proyecto. Se enseña ANTES de borrar de verdad."""
    out = {}
    try:
        out["Documentos"] = len(list_documents(pid))
    except Exception:
        out["Documentos"] = 0
    for etiqueta, hoja, col in (("Gastos", "Gastos", "ProyectoID"),
                                ("Cálculos", "Calculos", "ProyectoID"),
                                ("Pre-Starts", "PreStarts", "ProyectoID"),
                                ("Alarmas", "Alarmas", "ProyectoID")):
        try:
            out[etiqueta] = sum(1 for r in _records(hoja)
                                if str(r.get(col, "")) == str(pid))
        except Exception:
            out[etiqueta] = 0
    try:
        out["Actividades"] = len(list_activities(pid))
        nom = str((get_project(pid) or {}).get("Nombre", ""))
        out["Fichajes"] = sum(1 for r in _fichaje_records()
                              if timeclock.es_del_proyecto(r, pid, nom))
    except Exception:
        pass
    return out


def list_projects_for_field(usuario: str, grupo: str = None) -> list:
    """Proyectos donde el usuario de campo está asignado (CampoAsignados)."""
    out = []
    for r in list_projects(grupo=grupo):
        asignados = [x.strip() for x in str(r.get("CampoAsignados", "")).split(";") if x.strip()]
        if usuario in asignados:
            out.append(r)
    return out


def add_field_user(pid: str, usuario: str) -> tuple:
    """Añade un usuario de campo a CampoAsignados del proyecto (para que tenga acceso
    desde su cuenta). Idempotente: si ya está, no reescribe. NO quita a nadie.
    Devuelve (ok, nuevo) donde `nuevo`=True solo si se acaba de agregar."""
    usuario = str(usuario or "").strip()
    if not usuario:
        return False, False
    prj = get_project(pid)
    if not prj:
        return False, False
    actuales = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
    if usuario in actuales:
        return True, False
    actuales.append(usuario)
    ok, _ = update_project(pid, {"CampoAsignados": ";".join(actuales)})
    return ok, ok


def get_project(pid: str) -> dict:
    for r in _records(PROJECTS_SHEET):
        if str(r.get("ID", "")) == str(pid):
            return r
    return {}


def get_project_full(pid: str) -> dict:
    """Proyecto + JSONs deserializados (params, matriz, interp) + actividades."""
    r = get_project(pid)
    if not r:
        return {}
    def _load(key):
        try:
            return json.loads(r.get(key) or ("[]" if "Matriz" in key else "{}"))
        except Exception as e:
            logger.warning("projects: JSON inválido en %s de %s: %s", key, pid, e)
            return {} if "Matriz" not in key else []
    r["params"]     = _load("ParamsJSON")
    r["matriz"]     = _load("MatrizJSON")
    r["interp"]     = _load("InterpJSON")
    r["activities"] = list_activities(pid)
    return r


def update_project(pid: str, fields: dict) -> tuple:
    """Actualiza columnas sueltas del proyecto (fields = {Header: valor})."""
    pws, err = _projects_ws()
    if err:
        return False, err
    row = _find_row(pws, "ID", pid)
    if row is None:
        return False, "Proyecto no encontrado."
    # v342: el ANTES se captura aquí, antes de escribir. Sale de la caché (0 llamadas).
    _antes = dict(get_project(pid) or {})
    # Una sola llamada a la API (batch) en vez de N update_cell → evita rate limit.
    batch = [{"range": f"{_col_letter(_PCOL[k])}{row}", "values": [[str(v)]]}
             for k, v in fields.items() if k in _PCOL]
    if batch:
        try:
            pws.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, f"Error actualizando: {e}"
    _invalidate()
    # ⚠️ v342: FUERA del try del guardado y DESPUÉS de invalidar. Si la anotación
    # falla, el cambio del usuario ya está hecho y no se va a deshacer por eso.
    try:
        from core import auditoria
        auditoria.registrar("proyecto", pid, auditoria.diff(_antes, fields),
                            grupo=str(_antes.get("Grupo", "")))
    except Exception:
        pass
    return True, "Proyecto actualizado."
def delete_project(pid: str) -> tuple:
    pws, err = _projects_ws()
    if err:
        return False, err
    row = _find_row(pws, "ID", pid)
    if row is None:
        return False, "Proyecto no encontrado."
    pws.delete_rows(row)
    # borrar sus actividades
    aws, err2 = _activities_ws()
    if not err2:
        recs = aws.get_all_records(numericise_ignore=["all"])
        for i in range(len(recs) - 1, -1, -1):
            if str(recs[i].get("ProyectoID", "")) == str(pid):
                aws.delete_rows(i + 2)
    _invalidate()
    return True, "Proyecto eliminado."


# ── Actividades ──────────────────────────────────────────────────
def list_activities(pid: str) -> list:
    out = [r for r in _records(ACTIVITIES_SHEET)
           if str(r.get("ProyectoID", "")) == str(pid)]
    out.sort(key=lambda r: _num(r.get("Orden")))
    return out


def update_activity_progress(pid: str, orden, avance, fecha_inicio="", fecha_fin="",
                             nota=None) -> tuple:
    """El usuario de campo actualiza el Avance% (0-100) de una actividad.
    Recalcula el avance y el estado del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    avance = max(0.0, min(100.0, _num(avance)))
    recs = aws.get_all_records(numericise_ignore=["all"])
    target = None
    for i, r in enumerate(recs):
        if str(r.get("ProyectoID", "")) == str(pid) and str(r.get("Orden", "")) == str(orden):
            target = i + 2
            break
    if target is None:
        return False, "Actividad no encontrada."
    aws.update_cell(target, _ACOL["Avance"], str(avance))
    if fecha_inicio:
        aws.update_cell(target, _ACOL["FechaInicioReal"], fecha_inicio)
    if fecha_fin:
        aws.update_cell(target, _ACOL["FechaFinReal"], fecha_fin)
    if nota is not None:
        aws.update_cell(target, _ACOL["Nota"], nota)

    # Recalcular el avance del proyecto EN MEMORIA (recs ya leídas, sin re-leer)
    proj_acts = []
    for r in recs:
        if str(r.get("ProyectoID", "")) != str(pid):
            continue
        rr = dict(r)
        if str(rr.get("Orden", "")) == str(orden):
            rr["Avance"] = avance
        proj_acts.append(rr)
    nuevo  = compute_avance(proj_acts)
    prj    = get_project(pid)                       # cacheado
    manual = str(prj.get("EstadoManual", "")) if prj else ""
    update_project(pid, {"Avance": nuevo, "Estado": derive_estado(nuevo, manual)})
    # update_project ya invalida el caché de lecturas
    return True, f"Avance actualizado. Proyecto: {nuevo}%"


def _recompute_project_avance(pid):
    """Recalcula el avance y el estado del proyecto según sus actividades actuales."""
    acts   = list_activities(pid)
    nuevo  = compute_avance(acts)
    prj    = get_project(pid)
    manual = str(prj.get("EstadoManual", "")) if prj else ""
    update_project(pid, {"Avance": nuevo, "Estado": derive_estado(nuevo, manual)})
    return nuevo


def add_activity(pid, nombre, duracion=1, peso=0) -> tuple:
    """Agrega una actividad al final del cronograma (avance 0) y recalcula el % del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    acts  = list_activities(pid)
    orden = int(max([_num(a.get("Orden")) for a in acts], default=0) + 1)
    aws.append_row([pid, str(orden), str(nombre), str(int(_num(duracion) or 1)),
                    str(_num(peso)), "0", "", "", ""], value_input_option="RAW")
    _invalidate()
    _recompute_project_avance(pid)
    return True, "Actividad agregada."


def delete_activity(pid, orden) -> tuple:
    """Elimina una actividad y recalcula el % del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    recs = aws.get_all_records(numericise_ignore=["all"])
    target = None
    for i, r in enumerate(recs):
        if str(r.get("ProyectoID", "")) == str(pid) and str(r.get("Orden", "")) == str(orden):
            target = i + 2
            break
    if target is None:
        return False, "Actividad no encontrada."
    aws.delete_rows(target)
    _invalidate()
    _recompute_project_avance(pid)
    return True, "Actividad eliminada."


def save_field_progress(pid, cambios) -> tuple:
    """El campo actualiza el avance de VARIAS actividades en UNA escritura (batch).

    `cambios` = [{'orden', 'avance', 'nota'(opc)}]. Fechas reales AUTOMATICAS
    (decision del usuario, v162): el campo no teclea fechas.
      - FechaInicioReal: el primer dia que el avance pasa de 0 (si estaba vacia).
      - FechaFinReal: el dia que llega a 100 (si estaba vacia).
      - Si una actividad al 100% se REABRE (baja de 100), se borra la fin real
        (dejaria "terminada" una fecha que ya no es cierta).
    ⚠️ Reemplaza el `update_activity_progress` por-actividad (hasta 5 update_cell
    cada uno) — el escenario de 429 que v80/v150 ya arreglaron en otros sitios.
    """
    aws, err = _activities_ws()
    if err:
        return False, err
    hoy = clock.today().isoformat()
    recs = aws.get_all_records(numericise_ignore=["all"])
    rowmap = {str(r.get("Orden", "")): (i + 2, r)
              for i, r in enumerate(recs) if str(r.get("ProyectoID", "")) == str(pid)}
    batch = []
    for c in (cambios or []):
        hit = rowmap.get(str(c.get("orden")))
        if hit is None:
            continue
        row, r = hit
        av = max(0.0, min(100.0, _num(c.get("avance"))))
        fi = str(r.get("FechaInicioReal", "")).strip()
        ff = str(r.get("FechaFinReal", "")).strip()
        batch.append({"range": f"{_col_letter(_ACOL['Avance'])}{row}", "values": [[str(av)]]})
        if av > 0 and not fi:                        # arranca → inicio real = hoy
            batch.append({"range": f"{_col_letter(_ACOL['FechaInicioReal'])}{row}",
                          "values": [[hoy]]})
        if av >= 100 and not ff:                     # completa → fin real = hoy
            batch.append({"range": f"{_col_letter(_ACOL['FechaFinReal'])}{row}",
                          "values": [[hoy]]})
        elif av < 100 and ff:                        # reabierta → borrar fin real
            batch.append({"range": f"{_col_letter(_ACOL['FechaFinReal'])}{row}",
                          "values": [[""]]})
        if "nota" in c:
            batch.append({"range": f"{_col_letter(_ACOL['Nota'])}{row}",
                          "values": [[str(c.get("nota", ""))]]})
    if not batch:
        return True, "Sin cambios que guardar."
    try:
        aws.batch_update(batch, value_input_option="RAW")
    except Exception as ex:
        return False, f"Error guardando: {ex}"
    _recompute_project_avance(pid)
    _invalidate()
    return True, "Avances guardados."


def save_activities(pid, edits) -> tuple:
    """Guarda ediciones de la tabla (nombre/días/peso/orden) en UNA sola escritura (batch).
    `edits`: lista de dicts con 'orden0' (orden original, para localizar la fila) +
    los campos nuevos (Nombre/DuracionDias/Peso/Orden). Preserva el Avance (lo pone el campo)."""
    aws, err = _activities_ws()
    if err:
        return False, err
    recs = aws.get_all_records(numericise_ignore=["all"])
    rowmap = {str(r.get("Orden", "")): i + 2
              for i, r in enumerate(recs) if str(r.get("ProyectoID", "")) == str(pid)}
    batch = []
    for e in edits:
        row = rowmap.get(str(e.get("orden0")))
        if row is None:
            continue
        for field in ("Nombre", "DuracionDias", "Peso", "Orden"):
            if field in e and field in _ACOL:
                batch.append({"range": f"{_col_letter(_ACOL[field])}{row}",
                              "values": [[str(e[field])]]})
    if batch:
        try:
            aws.batch_update(batch, value_input_option="RAW")
        except Exception as ex:
            return False, f"Error guardando actividades: {ex}"
    _invalidate()
    _recompute_project_avance(pid)
    return True, "Actividades actualizadas."


# ── Horas trabajadas (desde el fichaje) ──────────────────────────
def project_hours(proyecto_nombre: str, grupo: str = None, pid: str = "") -> float:
    """Horas del fichaje de un proyecto. Con `pid` cruza por ID (v145); si no, por nombre."""
    total = 0.0
    for r in _fichaje_records():
        if not timeclock.es_del_proyecto(r, pid, proyecto_nombre):
            continue
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        total += _num(r.get("Horas"))
    return round(total, 2)


def project_hours_bulk(grupo: str = None) -> dict:
    """**{ProyectoID: horas}** (v145; antes iba por nombre). 1 lectura del fichaje.

    ⚠️ Cambio de clave: el nombre no es identidad estable y renombrar un proyecto
    partia sus horas en dos. Las filas anteriores a v145 no traen ProyectoID, asi
    que su nombre se resuelve contra los proyectos del grupo y tambien acaban
    sumando bajo el ID correcto.
    """
    idx = {}                                   # nombre normalizado -> ID
    # Mapa de resolucion, no lista: incluye archivados para que sus fichajes
    # historicos sigan sumando bajo su ID.
    for p in list_projects(grupo=grupo, incluir_archivados=True):
        n = str(p.get("Nombre", "")).strip().casefold()
        if n:
            idx[n] = str(p.get("ID", ""))
    out = {}
    for r in _fichaje_records():
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        pid = timeclock.pid_of(r) or idx.get(
            str(r.get("Proyecto", "")).strip().casefold(), "")
        if not pid:
            continue                           # fichaje de algo que ya no existe
        out[pid] = out.get(pid, 0.0) + _num(r.get("Horas"))
    return {k: round(v, 2) for k, v in out.items()}


# ── Avance de una agrupación ─────────────────────────────────────
def set_grouping_members(gid: str, miembros: dict, grupo: str = None) -> tuple:
    """Define QUÉ proyectos componen una agrupación. `miembros` = {pid: peso}.

    Desde v141 la agrupación se arma desde la agrupación (elegir sus proyectos),
    no proyecto a proyecto: antes había que crear la agrupación vacía y luego
    editar cada elevador por separado para asignarlo.

    Los proyectos que estaban y ya no figuran se DESAGRUPAN (no se borran).
    Devuelve (ok, mensaje). ⚠️ Es 1 escritura por proyecto que cambia.
    """
    actuales = {str(p.get("ID")): _num(p.get("PesoEnAgrupacion"))
                for p in list_projects(grupo=grupo, agrupacion_id=gid, incluir_archivados=True)}
    nuevos = {str(k): float(v or 1) for k, v in (miembros or {}).items()}

    cambios, errores = 0, []
    for pid, peso in nuevos.items():                   # altas y cambios de peso
        if pid not in actuales or abs(actuales[pid] - peso) > 1e-9:
            ok, msg = update_project(pid, {"AgrupacionID": gid,
                                           "PesoEnAgrupacion": peso})
            cambios += 1 if ok else 0
            if not ok:
                errores.append(f"{pid}: {msg}")
    for pid in actuales:                               # bajas
        if pid not in nuevos:
            ok, msg = update_project(pid, {"AgrupacionID": "", "PesoEnAgrupacion": 0})
            cambios += 1 if ok else 0
            if not ok:
                errores.append(f"{pid}: {msg}")

    if errores:
        return False, "  ·  ".join(errores[:3])
    return True, (f"{cambios} proyecto(s) actualizados." if cambios
                  else "Sin cambios que guardar.")


def grouping_projection(gid: str, grupo: str = None) -> dict:
    """Cuándo se entrega el CONJUNTO y quién lo determina.

    El avance consolidado (un promedio ponderado) no responde la pregunta que
    importa en un edificio: la entrega la marca **el último** elevador, no el
    promedio. Aquí se toma el máximo de las fechas proyectadas por SPI.
    """
    out = {"fecha": None, "critico": "", "critico_id": "", "spi_min": None,
           "sin_datos": [], "detalle": []}
    cache = projections_by_group(grupo) if grupo else {}
    for p in list_projects(grupo=grupo, agrupacion_id=gid, incluir_archivados=True):
        pid, nom = str(p.get("ID", "")), str(p.get("Nombre", ""))
        pr = cache.get(pid)                       # cacheado por grupo (60 s)
        if pr is None:
            ps = project_schedule(pid)
            pr = ps.get("proj") if ps else None
        if not pr:
            out["sin_datos"].append(nom)
            continue
        fecha, spi = pr.get("fecha"), pr.get("spi")
        if fecha is None and "fecha_proj" in pr:
            fecha = pr.get("fecha_proj")
        out["detalle"].append({"id": pid, "nombre": nom, "fecha": fecha,
                               "spi": spi,
                               "gap": pr.get("gap", pr.get("dias_gap"))})
        if fecha and (out["fecha"] is None or fecha > out["fecha"]):
            out["fecha"], out["critico"], out["critico_id"] = fecha, nom, pid
        if spi is not None and (out["spi_min"] is None or spi < out["spi_min"]):
            out["spi_min"] = spi
    return out


def grouping_curve(gid: str, grupo: str = None) -> dict:
    """Curva S CONSOLIDADA de la agrupación (plan vs real), en fechas reales.

    Cada elevador tiene su propio cronograma y su propia fecha de inicio, así
    que no se pueden sumar por "día N": se llevan todos a un eje de FECHAS y se
    combinan ponderando por el peso de cada uno en la agrupación.
    """
    from datetime import timedelta
    series = []
    for p in list_projects(grupo=grupo, agrupacion_id=gid, incluir_archivados=True):
        ps = project_schedule(str(p.get("ID", "")))
        if not ps:
            continue
        peso = _num(p.get("PesoEnAgrupacion")) or 1.0
        series.append({"peso": peso, "inicio": ps["sched"]["start_date"],
                       "plan": ps["sched"]["scurve"], "real": ps["real"],
                       "hoy": ps["today_day"]})
    if not series:
        return {}

    ini = min(s["inicio"] for s in series)
    fin = max(s["inicio"] + timedelta(days=int(s["plan"][-1][0])) for s in series
              if s["plan"])
    tot_peso = sum(s["peso"] for s in series) or 1.0

    def _pct(curva, dia):
        """% de una curva [(dia,%)] en `dia`; 0 antes de empezar, último valor después."""
        if not curva:
            return 0.0
        if dia <= curva[0][0]:
            return 0.0
        if dia >= curva[-1][0]:
            return curva[-1][1]
        for i in range(1, len(curva)):
            if curva[i][0] >= dia:                       # interpolación lineal
                (x0, y0), (x1, y1) = curva[i - 1], curva[i]
                t = (dia - x0) / (x1 - x0) if x1 != x0 else 0
                return y0 + (y1 - y0) * t
        return curva[-1][1]

    fechas, plan, real = [], [], []
    d, hoy = ini, clock.today()
    while d <= fin:
        pl = rl = 0.0
        for s in series:
            off = (d - s["inicio"]).days
            pl += s["peso"] * _pct(s["plan"], off)
            if d <= hoy:                                  # la real se corta en HOY
                rl += s["peso"] * _pct(s["real"], off)
        fechas.append(d)
        # tope 100: cada scurve individual redondea y la suma daba 100.2 %
        plan.append(min(100.0, round(pl / tot_peso, 1)))
        real.append(min(100.0, round(rl / tot_peso, 1)) if d <= hoy else None)
        d += timedelta(days=max(1, (fin - ini).days // 60 or 1))
    return {"fechas": fechas, "plan": plan, "real": real, "hoy": hoy}


def grouping_progress(gid: str) -> dict:
    """Avance ponderado de una agrupación: Σ(peso_proy × avance_proy)/Σ(peso)."""
    proys = list_projects(agrupacion_id=gid, incluir_archivados=True)
    tot_peso = sum(_num(p.get("PesoEnAgrupacion")) for p in proys)
    if tot_peso <= 0:
        avance = 0.0
    else:
        avance = round(sum(_num(p.get("PesoEnAgrupacion")) * _num(p.get("Avance"))
                           for p in proys) / tot_peso, 1)
    return {"avance": avance, "n_proyectos": len(proys), "peso_total": tot_peso}


# ── Cronograma planificado + curva S real ────────────────────────
def project_schedule(pid: str):
    """Reconstruye el cronograma PLANIFICADO (de las actividades guardadas) y calcula
    la curva S REAL (del avance de cada actividad). Devuelve {sched, real, today_day} o None."""
    from core.schedule import build_schedule, real_scurve, schedule_projection
    prj  = get_project(pid)
    acts = list_activities(pid)
    if not prj or not acts:
        return None
    try:
        y, m, d = str(prj.get("FechaInicio", "")).split("-")
        start = date(int(y), int(m), int(d))
    except Exception:
        start = clock.today()
    custom = [{"nombre":   a.get("Nombre", ""),
               "duracion": _num(a.get("DuracionDias")) or 1.0,
               "peso":     _num(a.get("Peso"))} for a in acts]
    sched     = build_schedule(1, start, {}, custom_rows=custom)
    avances   = [_num(a.get("Avance")) for a in acts]
    today_day = (clock.today() - start).days

    def _day_off(s):
        try:
            y, m, dd = str(s).split("-")
            return (date(int(y), int(m), int(dd)) - start).days
        except Exception:
            return None
    windows = [(_day_off(a.get("FechaInicioReal")), _day_off(a.get("FechaFinReal")))
               for a in acts]

    real = real_scurve(sched, avances, upto_day=today_day, windows=windows)  # se corta en HOY
    proj = schedule_projection(sched, avances, today_day)
    return {"sched": sched, "real": real, "today_day": today_day,
            "avances": avances, "proj": proj}


# ── Documentos del proyecto (metadatos; los archivos viven en Drive) ──
def _documents_ws():
    return _get_ws(DOCUMENTS_SHEET, DOCUMENTS_HEADERS)


def list_documents(pid: str) -> list:
    return [r for r in _records(DOCUMENTS_SHEET)
            if str(r.get("ProyectoID", "")) == str(pid)]


def add_document(pid, nombre, tipo, drive_id, subido_por="") -> tuple:
    dws, err = _documents_ws()
    if err:
        return False, err
    dws.append_row([pid, nombre, tipo, drive_id, subido_por,
                    clock.now().strftime("%Y-%m-%d %H:%M:%S")], value_input_option="RAW")
    _invalidate()
    return True, "Documento registrado."


def delete_document_record(pid, drive_id) -> tuple:
    dws, err = _documents_ws()
    if err:
        return False, err
    recs = dws.get_all_records(numericise_ignore=["all"])
    for i, r in enumerate(recs):
        if str(r.get("ProyectoID", "")) == str(pid) and str(r.get("DriveID", "")) == str(drive_id):
            dws.delete_rows(i + 2)
            _invalidate()
            return True, "Documento eliminado."
    return False, "Registro no encontrado."
