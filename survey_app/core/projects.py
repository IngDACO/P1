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
from core import columnas
from core import valores
from core.num import col_letter as _col_letter, num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

PROJECTS_SHEET   = "Projects"
ACTIVITIES_SHEET = "Activities"
GROUPINGS_SHEET  = "Groupings"

PROJECTS_HEADERS = [
    "ID", "Group", "Name", "Client", "Location", "Model", "NS",
    "Status", "ManualStatus", "StartDate", "EndDateEst", "HeadInstallers",
    "FieldAssigned", "Progress", "GroupingID", "WeightInGrouping",
    "ParamsJSON", "MatrixJSON", "InterpJSON", "CreatedBy", "Created",
    "Instructions", "InductionLinks", "Budget",
    # v137: datos leidos del PLANO (distintos de ParamsJSON, que es el survey e
    # incluye lo medido en obra). Se extraen UNA vez al cargar el plano y los
    # consumen las 5 herramientas sin volver a abrir el PDF.
    "DrawingJSON",
    # v193: coordenadas para el pin en el mapa (se fijan con el selector de ubicación).
    "Lat", "Lng",
    # v219: certificados/tickets que EXIGE el proyecto (tipos del catálogo, `;`), para
    # avisar y marcar a los asignados que no cumplen.
    "RequiredCerts",
    # v255: enlace robusto al cliente (CLI-#### de la hoja Clientes). El campo `Cliente`
    # (texto) se conserva; el match usa ID-primero, nombre-de-respaldo (como el fichaje, v145).
    "ClientID",
    # ⚠️ COLUMNA MUERTA. Era el margen (%) sobre la mano de obra del modelo viejo,
    # RETIRADO: la ganancia es hoy un IMPORTE por rubro (GananciaHoraJSON / GananciaFija).
    # Se conserva en la cabecera a propósito: quitarla desplazaría las 20 columnas
    # siguientes y, como la fila es POSICIONAL, cada dato caería en la de al lado.
    # Se escribe vacía y no la lee nadie.
    "LabourMargin",
    # v306: qué clase de trabajo es. NO es cosmético: solo la instalación tiene el
    # cronograma estándar de 11 actividades que escalan con el NS, y ese plan alimenta
    # avance, curva S, SPI y el indicador «En retraso». Los proyectos anteriores a v306
    # lo tienen VACÍO a propósito (no se tocó la hoja): se muestran como "sin tipo".
    "Type",
    # v360: {usuario: ganancia $/h} de ESTE proyecto. La ganancia es un IMPORTE por
    # rubro, no un %. VACÍO = la obra vale su COSTO (y la app avisa de quién trabajaría
    # sin ganancia); antes caía al modelo viejo del %, que se retiró.
    "HourlyProfitJSON",
    # v373: ganancia FIJA de la obra, en dinero. Cubre el hueco que v370 dejó abierto:
    # una obra cuyo valor NO está en las horas (un delivery, un suministro) y que NO
    # nació de una cotización valía exactamente lo que costó, porque los materiales
    # van a costo en los dos modelos. Medido: «Bespoke — Delivery Chullora» estimado
    # en $380 habiendo facturado $5.200. VACÍO = no aporta nada (retrocompatible).
    "FixedProfit",
]

# Tipos de proyecto (v306). `TIPO_INSTALACION` es el único que genera el cronograma
# estándar de obra; los demás nacen con UNA actividad genérica (ver `create_project`).
TIPO_INSTALACION = "Installation"
# v470 · sustituir un ascensor: primero se desmonta el viejo y luego se instala el
# nuevo. Genera el MISMO cronograma que una instalación con la actividad de
# desmontaje delante (`schedule.FASE_RIPOUT`).
TIPO_RIPOUT_INST = "Ripout + Installation"
TIPOS = [TIPO_INSTALACION, TIPO_RIPOUT_INST, "Delivery", "Ripout", "Other"]


def genera_cronograma(tipo) -> bool:
    """¿Este tipo nace con el cronograma estándar de obra?

    ⚠️ ÚNICA definición, y no es ceremonia: hasta v470 la pregunta se hacía en TRES
    sitios —el alta a mano, la edición y `quotes.aceptar_y_crear_proyecto`— y uno de
    ellos comparaba contra el LITERAL `"Installation"` en vez de la constante. Añadir
    un tipo a dos de los tres lo deja comportándose como «Other» **sin dar ningún
    error**: es el fallo de v454, donde una obra creada desde cotización nació con
    CERO actividades y se quedó clavada en 0% para siempre, porque el avance es
    Σ(peso·avance)/Σpeso sobre las actividades.
    """
    return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST)


def con_ripout(tipo) -> bool:
    """¿Lleva por delante la actividad de desmontaje?"""
    return str(tipo) == TIPO_RIPOUT_INST

# ── v422: LOCALIZACIONES INTERNAS (oficina, almacén, taller) ──────────────────
# No todo el mundo trabaja en obra: hay gente de oficina y de almacén que también
# ficha, hace su pre-start y genera gastos. Se modelan como un proyecto para reusar
# toda la fontanería que ya existe (fichaje, pre-start, gastos, documentos, alarmas,
# roster) SIN duplicar nada — pero con una diferencia que lo decide todo:
#
#   ⚠️ Una localización interna NO SE LE FACTURA A NADIE.
#
# Su costo es ESTRUCTURA, no obra. Medido antes de construir: sin cerrojo, la oficina
# aparecería como «$X sin facturar» (un pendiente que nadie puede cerrar), como una
# obra a margen 0% en Rentabilidad, con pérdida garantizada en el resultado por
# proyecto, y su 0% eterno arrastraría el avance promedio del grupo. Además movería
# sus horas a «cargado a obras», que es lo que en v313 el usuario definió como *lo
# que se le cobra al cliente*.
#
# El cerrojo es el DEFAULT de `list_projects` (`incluir_internos=False`): así los ~59
# call-sites quedan protegidos de golpe y solo quien las necesita las pide. Es el
# mismo patrón que `incluir_archivados` (v149) — y la misma trampa, al revés: por eso
# v423 les da su propia sección, porque *lo que se puede ocultar tiene que poder
# verse* (regla v340).
TIPO_OFICINA = "Office"
TIPOS_INTERNOS = [TIPO_OFICINA, "Warehouse", "Workshop"]

# Estados propios: una localización no está «Planificada al 0%» — está abierta o
# cerrada. No tiene actividades, así que su avance sería 0 para siempre y
# `derive_estado` la dejaría eternamente en «Planificado», que no significa nada.
INTERNO_ABIERTA = "Open"
INTERNO_CERRADA = "Closed"

TIPO_ICONO = {TIPO_INSTALACION: ":material/construction:",
              TIPO_RIPOUT_INST: ":material/autorenew:",
              "Delivery": ":material/local_shipping:",
              "Ripout": ":material/delete_sweep:", "Other": ":material/category:",
              TIPO_OFICINA: ":material/business:", "Warehouse": ":material/warehouse:",
              "Workshop": ":material/handyman:"}


def es_interno(prj) -> bool:
    """¿Es una localización interna (oficina/almacén/taller) y no una obra?

    UNA sola definición, a propósito: cinco copias divergentes de un helper es lo
    que causó los fallos de v323. Acepta el dict del proyecto o su tipo suelto.
    """
    tipo = prj.get("Type", "") if isinstance(prj, dict) else prj
    return str(tipo or "").strip() in TIPOS_INTERNOS


def solo_obras(proys) -> list:
    """Las que SÍ son obra (para cualquier cifra que se le cobre a un cliente)."""
    return [p for p in proys if not es_interno(p)]


def solo_internas(proys) -> list:
    """Las localizaciones internas (para el costo de estructura)."""
    return [p for p in proys if es_interno(p)]
ACTIVITIES_HEADERS = [
    "ProjectID", "Order", "Name", "DurationDays", "Weight", "Progress",
    "ActualStartDate", "ActualEndDate", "Note",
]
GROUPINGS_HEADERS = ["ID", "Group", "Name", "Description"]
DOCUMENTS_SHEET   = "Documents"
DOCUMENTS_HEADERS = ["ProjectID", "Name", "Type", "DriveID", "UploadedBy", "Date"]

_PCOL = {h: i + 1 for i, h in enumerate(PROJECTS_HEADERS)}
_ACOL = {h: i + 1 for i, h in enumerate(ACTIVITIES_HEADERS)}

ESTADOS_MANUAL = ["", "On hold", "Cancelled", "Archived"]
FMT_DATE = "%Y-%m-%d"



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
        _vistos[str(p.get("Name") or "")] = _vistos.get(str(p.get("Name") or ""), 0) + 1
    out = {}
    for p in proys or []:
        _pid = str(p.get("ID") or "")
        _nom = str(p.get("Name") or "") or t("(no name)")
        out[_pid] = f"{_nom} ({_pid})" if _vistos.get(str(p.get("Name") or ""), 0) > 1 else _nom
    return out


# ── Worksheets (crea la pestaña si no existe) ────────────────────
def _get_ws(title, headers):
    if not timeclock._secrets_present():
        return None, t("Google Sheets is not configured.")
    try:
        return timeclock.get_sheet(title, tuple(headers)), None
    except Exception as e:
        logger.warning("projects: no se pudo abrir la hoja %s: %s", title, e)
        return None, f"{t('Could not open sheet')} {title}: {e}"


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
def _records_cached(libro: str, title):
    """Registros de una hoja (cacheados). Solo lecturas de DISPLAY."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(title, _HEADERS_BY_TITLE.get(title, [])) or []




def _records(title):
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(title), title)
@st.cache_data(ttl=120, show_spinner=False)
def _fichaje_records_cached(libro: str):
    """Registros del fichaje (cacheados) para sumar horas."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros("Sheet1", timeclock.HEADERS) or []




def _fichaje_records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _fichaje_records_cached(_libro_de("Sheet1"))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    #
    # ⚠️ v344 — REGRESIÓN MÍA DE v339, viva 4 versiones: al reescribir esto quité el
    # bucle `for fn in (...)` y dejé `fn.clear()`, un nombre que ya no existía. El
    # `except Exception` de abajo se tragaba el NameError, así que **estas dos cachés
    # NO se limpiaban nunca** y tras guardar un proyecto la pantalla podía enseñar el
    # valor viejo hasta 120 s. No lo vio ningún test: solo salió al ejercitar la
    # escritura contra la hoja real y ver un «antes» rancio en la auditoría.
    from core import hojas
    hojas.invalidar()
    # Y las DERIVADAS (v344): `gaps_by_group`/`projections_by_group` cachean el
    # retraso y la fecha proyectada de cada obra; sin limpiarlas, tras tocar las
    # actividades el retraso y el «en riesgo» seguían con el valor viejo.
    # ⚠️ v378: van las CACHEADAS (`*_cached`), no los envoltorios. Limpiar el
    # envoltorio lanza AttributeError, el `except` lo apunta en el log y la caché
    # se queda sin limpiar — el mismo agujero de v344 por otro camino. El guardián
    # de v378 comprueba que cada `.clear()` apunte a algo de verdad cacheado.
    for fn in (_records_cached, _fichaje_records_cached,
               gaps_by_group, projections_by_group):
        try:
            fn.clear()
        except Exception as e:                 # deja rastro (v323): si falla, se sabe
            logger.warning("projects._invalidate: no se pudo limpiar %s: %s", fn, e)


# ── Helpers de dominio ───────────────────────────────────────────
def compute_avance(activities: list) -> float:
    """% del proyecto = Σ(peso × avance) / Σ(peso).  activities: list de dicts."""
    tot_peso = sum(_num(a.get("Weight")) for a in activities)
    if tot_peso <= 0:
        return 0.0
    acc = sum(_num(a.get("Weight")) * _num(a.get("Progress")) for a in activities)
    return round(acc / tot_peso, 1)


def derive_estado(avance: float, estado_manual: str = "", tipo: str = "") -> str:
    """Estado automático por avance, salvo override manual (En pausa / Cancelado).

    ⚠️ v422: una localización interna NO tiene actividades, así que su avance es 0
    para siempre y la máquina de estados de obra la dejaría eternamente en
    «Planificado» — una oficina «planificada» no significa nada. Se le da su propio
    par: **Abierta / Cerrada**. El override manual (archivar, pausar) sigue mandando,
    porque es lo que hace que `list_projects` la oculte y que se pueda restaurar.
    """
    if estado_manual in ("On hold", "Cancelled", "Archived"):
        return estado_manual
    if es_interno(tipo):
        return INTERNO_CERRADA if estado_manual == INTERNO_CERRADA else INTERNO_ABIERTA
    if avance <= 0:
        return "Planned"
    if avance >= 100:
        return "Completed"
    return "In progress"


def _next_project_id(pws) -> str:
    """PRJ-#### incremental, **saltando los que otra hoja aún referencia** (v427).

    ⚠️ `max + 1` sobre las filas VIVAS recicla el ID de un proyecto borrado, y con él
    los huérfanos que hubieran quedado apuntando ahí. Medido en v426: dos facturas de
    una prueba vieja apuntaban a `PRJ-0017` y, al recrear ese ID, la obra nueva
    **heredó $1.000 de facturación ajena**. El proyecto es la entidad con más
    referencias de toda la app (fichajes, gastos, actividades, documentos,
    pre-starts, alarmas, cálculos, órdenes, roster, inventario, cotizaciones y las
    líneas de factura), así que es donde más duele.
    """
    mx = 0
    for r in valores.canonizar(columnas.canonizar(pws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET):
        pid = str(r.get("ID", ""))
        if pid.startswith("PRJ-"):
            try:
                mx = max(mx, int(pid.split("-")[1]))
            except Exception:
                pass
    try:
        from core import hojas
        return hojas.siguiente_id_libre("PRJ-", mx, propia=PROJECTS_SHEET)
    except Exception as e:
        # Un fallo aquí no puede impedir crear: se cae al comportamiento de siempre.
        logger.warning("projects: no se pudo comprobar IDs referenciados: %s", e)
        return f"PRJ-{mx + 1:04d}"


def _find_row(ws, header, value):
    """Nº de fila (1-based, incluye cabecera) del primer registro con header==value."""
    records = valores.canonizar(columnas.canonizar(ws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    for i, r in enumerate(records):
        if str(r.get(header, "")) == str(value):
            return i + 2  # +1 cabecera, +1 base-1
    return None


# ── Agrupaciones ─────────────────────────────────────────────────
def list_groupings(grupo: str = None) -> list:
    out = []
    for r in _records(GROUPINGS_SHEET):
        if grupo is not None and str(r.get("Group", "")) != str(grupo):
            continue
        out.append(r)
    return out


def create_grouping(grupo: str, nombre: str, descripcion: str = "") -> tuple:
    gws, err = _groupings_ws()
    if err:
        return False, err
    existing = valores.canonizar(columnas.canonizar(gws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    mx = 0
    for r in existing:
        gid = str(r.get("ID", ""))
        if gid.startswith("AGR-"):
            try:
                mx = max(mx, int(gid.split("-")[1]))
            except Exception:
                pass
        if str(r.get("Group", "")) == str(grupo) and str(r.get("Name", "")) == nombre:
            return False, t("A grouping with that name already exists in this group.")
    # ⚠️ v428: sin reciclar. `delete_grouping` borra la fila de verdad, así que su ID
    # queda libre — y los proyectos guardan `AgrupacionID`. Reutilizarlo metería en la
    # agrupación nueva los elevadores que colgaban de la borrada.
    try:
        from core import hojas
        gid = hojas.siguiente_id_libre("AGR-", mx, propia=GROUPINGS_SHEET)
    except Exception as e:
        logger.warning("projects: no se pudo comprobar IDs de agrupación: %s", e)
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
        return False, t("Grouping not found.")
    gws.delete_rows(row)
    _invalidate()
    return True, t("Grouping deleted.")


# ── Proyectos ────────────────────────────────────────────────────
def create_project(grupo, nombre, cliente="", ubicacion="", modelo="", ns=0,
                   ingeniero="", campo_asignados=None, fecha_inicio="", fecha_fin_est="",
                   params=None, matriz=None, interp=None, activities=None,
                   creado_por="", agrupacion_id="", peso_agrupacion=0,
                   instrucciones="", induccion_links="", presupuesto="",
                   lat="", lng="", certs_req="", cliente_id="",
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
    estado = derive_estado(avance, "", tipo)      # v422: «Abierta» si es interna

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
        "",                                 # MargenMO: columna MUERTA (modelo viejo, retirado).
        #                                     ⚠️ Se deja en HEADERS a propósito: quitarla
        #                                     DESPLAZARÍA las 20 columnas siguientes y cada
        #                                     dato caería en la de al lado (la fila es
        #                                     POSICIONAL). Se escribe vacía y nadie la lee.
        str(tipo or ""),                    # v306: instalación / delivery / ripout / otro
        "",                                 # v360: GananciaHoraJSON — una obra NACE sin ganancias
        #                                     por hora, así que arranca valiendo su COSTO hasta que
        #                                     alguien decida cuánto ganar con cada persona (o ponga
        #                                     una ganancia fija). ⚠️ v363: esta línea FALTABA
        #                                     desde v360 (se añadió la columna a la cabecera y no
        #                                     su valor aquí), y el guardián de abajo dejaba
        #                                     «Nuevo proyecto» y «aceptar cotización» MUERTOS.
        "",                                 # v373: GananciaFija — una obra nace sin ganancia
        #                                     fija; se pone a mano cuando su valor no está
        #                                     en las horas. ⚠️ Añadir la columna arriba SIN
        #                                     esta línea es exactamente lo que mató a
        #                                     `create_project` durante 3 versiones (v363).
    ]
    # ⚠️ La fila es POSICIONAL: si no cuadra con la cabecera, cada dato se guarda en la
    # columna de al lado (silencioso y difícil de ver). Se comprueba aquí, no en un test.
    if len(row) != len(PROJECTS_HEADERS):
        return False, (f"{t('Internal error: the row has')} {len(row)} "
                       f"{t('values and the header has')} "
                       f"{len(PROJECTS_HEADERS)} {t('columns.')}")
    pws.append_row(row, value_input_option="RAW")

    # Actividades del cronograma (batch: 1 sola llamada a la API)
    act_rows = [[
        pid, str(i + 1), a.get("nombre", a.get("Name", f"Actividad {i+1}")),
        str(a.get("duracion", a.get("DurationDays", 0))),
        str(a.get("peso", a.get("Weight", 0))),
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
        campos["MatrixJSON"] = json.dumps(matriz or [], ensure_ascii=False, default=str)
    if interp is not None:
        campos["InterpJSON"] = json.dumps(interp or {}, ensure_ascii=False, default=str)
    if not campos:
        return False, t("Nothing to attach.")
    return update_project(pid, campos)


def parse_links(text) -> list:
    """Lista de links (uno por línea) desde el texto de InduccionLinks."""
    return [l.strip() for l in str(text or "").splitlines() if l.strip()]


def _gaps_for(proys) -> dict:
    """{pid: dias_gap} de la proyección (SPI) de los proyectos activos.
    dias_gap > 0 = retraso, < 0 = adelanto."""
    out = {}
    for p in proys:
        if str(p.get("Status", "")) in ("Completed", "Cancelled"):
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


ARCHIVADO = "Archived"


def list_projects(grupo: str = None, agrupacion_id: str = None,
                  incluir_archivados: bool = False,
                  incluir_internos: bool = False) -> list:
    """Proyectos del grupo. **Oculta los archivados salvo que se pidan** (v149)
    y **las localizaciones internas salvo que se pidan** (v422).

    ⚠️ Archivar sustituye a borrar: `delete_project` solo quitaba el proyecto y
    sus actividades, dejando huerfanos sus documentos (con sus archivos en
    Drive), gastos, calculos, pre-starts, alarmas y fichajes. Datos de obra que
    pueden hacer falta despues.

    ⚠️ El defecto es OCULTAR, asi que las **busquedas por identidad** tienen que
    pedir `incluir_archivados=True` explicitamente: `plan_data.del_proyecto`,
    el mapa nombre->ID de `project_hours_bulk`, el proyecto del clock-in
    (`plan_ui`) y el chequeo de nombres duplicados. Si no, archivar romperia esas
    resoluciones en silencio.

    ⚠️ **`incluir_internos` sigue exactamente la misma regla, y por el mismo motivo.**
    El default OCULTA la oficina y el almacén, así que toda cifra de obra —cartera,
    KPIs, rentabilidad, «sin facturar», retrasos— queda protegida sin tocar sus 59
    call-sites. Tienen que pedirlas explícitamente:

      · las **resoluciones por identidad**, o el enlace se rompe en silencio:
        `project_hours_bulk` (las horas fichadas al almacén se PERDERÍAN),
        `roster.trabajos_idx` (una localización asignada en el tablero saldría sin
        nombre ni color), la agenda de HOME, el buscador y `plan_data.del_proyecto`;
      · **dónde se ficha y se trabaja**: `list_projects_for_field`, el fichaje, el
        pre-start, el roster y la ubicación de un activo del inventario — el almacén
        es justo donde están las cosas.

    Y NO deben pedirlas: nada que hable de dinero de cliente, de cronograma o de la
    cartera de obras. `verif_v422.py` lo comprueba en las DOS direcciones.
    """
    out = []
    for r in _registros_visibles(PROJECTS_SHEET, grupo):
        if grupo is not None and str(r.get("Group", "")) != str(grupo):
            continue
        if agrupacion_id is not None and str(r.get("GroupingID", "")) != str(agrupacion_id):
            continue
        if not incluir_archivados and str(r.get("Status", "")) == ARCHIVADO:
            continue
        if not incluir_internos and es_interno(r):
            continue
        out.append(r)
    return out


def list_locations(grupo: str = None, incluir_cerradas: bool = False) -> list:
    """Las localizaciones internas del grupo (oficina/almacén/taller).

    La cara B de `solo_obras`: quien quiera hablar de estructura pide esto, en vez
    de acordarse de pasar `incluir_internos=True` y filtrar a mano.
    """
    out = solo_internas(list_projects(grupo=grupo, incluir_archivados=True,
                                      incluir_internos=True))
    if not incluir_cerradas:
        out = [p for p in out if str(p.get("Status", "")) not in (INTERNO_CERRADA, ARCHIVADO)]
    return out


def _fichajes_visibles(grupo) -> list:
    """Las filas del FICHAJE que le tocan a quien pregunta (v379).

    Gemela de `_registros_visibles` para la hoja del fichaje, que es la que alimenta
    las horas de la cartera.
    """
    from core import tenant
    if grupo is not None:
        if tenant.puede_ver(grupo):
            with tenant.como_grupo(grupo):
                return _fichaje_records()
        return _fichaje_records()
    if not tenant.es_propietario():
        return _fichaje_records()
    from core import auth as _auth
    try:
        libros = _auth.grupos_por_libro()
    except Exception as e:
        logger.warning("projects: no se pudieron listar los libros: %s", e)
        return _fichaje_records()
    out = []
    for g, _sid in libros:
        with tenant.como_grupo(g):
            out.extend(_fichaje_records())
    return out


def _registros_visibles(title, grupo) -> list:
    """Las filas que le tocan a quien pregunta (v379).

    ⚠️ El PROPIETARIO sin filtro de grupo tiene que ver TODOS los clientes, y desde
    v359 cada uno vive en su propio libro. Su sesión no tiene grupo, así que el
    lector normal cae al maestro — y tras la mudanza de v377 el maestro está vacío:
    el propietario veía **0 proyectos**. Aquí se recorren los libros.

    Para todos los demás (y para el propietario que SÍ filtra por un grupo) el
    camino es el de siempre, byte a byte: una sola lectura de su libro.
    """
    from core import tenant
    if grupo is not None:
        # Un grupo explícito selecciona el libro **solo si quien pregunta puede ver
        # ese grupo** (propietario, o es el suyo). Sin esto el propietario filtrando
        # por un cliente leía el maestro y le salían 0 proyectos.
        #
        # ⚠️ La comprobación NO es decorativa: sin ella el argumento se convierte en
        # una LLAVE — un admin de otra empresa que pasara `grupo="cliente1"` leería
        # el libro de cliente1. Lo cazó el test de dos inquilinos, y solo después de
        # reescribirlo: la versión anterior comparaba propietario contra admin y con
        # la fase 2 había dejado de distinguir una fuga de la funcionalidad nueva.
        if tenant.puede_ver(grupo):
            with tenant.como_grupo(grupo):
                return _records(title)
        return _records(title)          # sin permiso: su libro de siempre
    if not tenant.es_propietario():
        return _records(title)
    from core import auth as _auth
    try:
        libros = _auth.grupos_por_libro()
    except Exception as e:
        logger.warning("projects: no se pudieron listar los libros: %s", e)
        return _records(title)
    out = []
    for g, _sid in libros:
        # Dentro del `with`, TODA lectura sale del libro de ese grupo (v379).
        with tenant.como_grupo(g):
            out.extend(_records(title))
    return out


def set_archivado(pid: str, archivar: bool = True) -> tuple:
    """Archiva o restaura un proyecto. No borra nada."""
    prj = get_project(pid)
    if not prj:
        return False, t("Project not found.")
    if archivar:
        return update_project(pid, {"ManualStatus": ARCHIVADO, "Status": ARCHIVADO})
    # ⚠️ v422: con el tipo. Sin él, restaurar una localización interna la devolvía a
    # «Planificado» en vez de «Abierta» — se puede archivar y no se puede volver bien,
    # que es media aplicación de la regla v340.
    return update_project(pid, {"ManualStatus": "",
                                "Status": derive_estado(_num(prj.get("Progress")), "",
                                                        prj.get("Type", ""))})


def datos_asociados(pid: str) -> dict:
    """Cuanto cuelga de este proyecto. Se enseña ANTES de borrar de verdad.

    ⚠️ v380: todo esto vive en el libro del cliente. Para el PROPIETARIO —cuya sesión
    no tiene grupo— salía a CERO, y este recuento es justo lo que se le enseña antes
    de un borrado irreversible: «no cuelga nada» cuando cuelgan documentos, gastos y
    fichajes es el peor sitio posible para un cero falso.
    """
    _prj = get_project(pid) or {}
    _g = str(_prj.get("Group", "")) or None
    out = {}
    from core import tenant
    with tenant.como_grupo(_g or tenant.grupo_sesion()):
        try:
            out["Documentos"] = len(list_documents(pid))
        except Exception:
            out["Documentos"] = 0
        for etiqueta, hoja, col in (("Gastos", "Gastos", "ProjectID"),
                                    ("Cálculos", "Calculos", "ProjectID"),
                                    ("Pre-Starts", "PreStarts", "ProjectID"),
                                    ("Alarmas", "Alarmas", "ProjectID")):
            try:
                out[etiqueta] = sum(1 for r in _records(hoja)
                                    if str(r.get(col, "")) == str(pid))
            except Exception:
                out[etiqueta] = 0
        try:
            out["Actividades"] = len(list_activities(pid))
            nom = str(_prj.get("Name", ""))
            out["Fichajes"] = sum(1 for r in _fichaje_records()
                                  if timeclock.es_del_proyecto(r, pid, nom))
        except Exception:
            pass
    return out


def list_projects_for_field(usuario: str, grupo: str = None,
                            incluir_internos: bool = False) -> list:
    """Proyectos donde el usuario de campo está asignado (CampoAsignados).

    ⚠️ v422: `CampoAsignados` es también lo que define un «perfil de oficina» — estar
    asignado de forma PERMANENTE a la oficina o al almacén. No se inventó ni un rol ni
    una columna para eso: el mecanismo que ya decide qué proyectos ve cada quien sirve
    igual, y un almacenero no puede ser rol `administrador` (vería las finanzas).
    Quien las necesita (fichaje, pre-start) pasa `incluir_internos=True`.
    """
    out = []
    for r in list_projects(grupo=grupo, incluir_internos=incluir_internos):
        asignados = [x.strip() for x in str(r.get("FieldAssigned", "")).split(";") if x.strip()]
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
    actuales = [x.strip() for x in str(prj.get("FieldAssigned", "")).split(";") if x.strip()]
    if usuario in actuales:
        return True, False
    actuales.append(usuario)
    ok, _ = update_project(pid, {"FieldAssigned": ";".join(actuales)})
    return ok, ok


def get_project(pid: str) -> dict:
    # v379: para el propietario busca en TODOS los libros — si no, abrir un proyecto
    # de un cliente desde su panel devolvía {} y la ficha salía vacía.
    for r in _registros_visibles(PROJECTS_SHEET, None):
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
    r["matriz"]     = _load("MatrixJSON")
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
        return False, t("Project not found.")
    # v342: el ANTES se captura aquí, antes de escribir. Sale de la caché (0 llamadas).
    _antes = dict(get_project(pid) or {})
    # ⚠️ v344: lo que de verdad se va a escribir. Una clave que no está en `_PCOL`
    # se DESCARTA (un typo, o un nombre de columna que ya no existe), y hasta ahora
    # eso pasaba en silencio devolviendo «Proyecto actualizado.». Se separa para (a)
    # auditar solo lo escrito y (b) poder avisar de lo ignorado.
    _escritos = {k: v for k, v in fields.items() if k in _PCOL}
    _ignorados = [k for k in fields if k not in _PCOL]
    if _ignorados:
        logger.warning("update_project(%s): columnas desconocidas, NO se escriben: %s",
                       pid, ", ".join(_ignorados))
    if fields and not _escritos:
        return False, (t("No recognised field") + ": " + ", ".join(_ignorados)
                       + ". " + t("Nothing was saved."))
    # Una sola llamada a la API (batch) en vez de N update_cell → evita rate limit.
    batch = [{"range": f"{_col_letter(_PCOL[k])}{row}", "values": [[str(v)]]}
             for k, v in _escritos.items()]
    if batch:
        try:
            pws.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, f"{t('Error updating')}: {e}"
    _invalidate()
    # ⚠️ v342: FUERA del try del guardado y DESPUÉS de invalidar. Si la anotación
    # falla, el cambio del usuario ya está hecho y no se va a deshacer por eso.
    try:
        from core import auditoria
        # ⚠️ v344: se audita `_escritos`, NO `fields`. Con `fields` se anotaba un
        # cambio que la hoja nunca recibió, y en cada guardado otra vez (el «antes»
        # no cambiaba nunca porque no se escribía nada).
        auditoria.registrar("proyecto", pid, auditoria.diff(_antes, _escritos),
                            grupo=str(_antes.get("Group", "")))
    except Exception as e:
        # ⚠️ Deja RASTRO (regla v323): `registrar` ya logea sus propios fallos, pero
        # si lo que revienta es `diff` o el import, el apunte se perdía en silencio
        # y el histórico se quedaba con un hueco que nadie podía explicar.
        logger.warning("projects: no se pudo auditar %s: %s", pid, e)
    return True, t("Project updated.")
def delete_project(pid: str) -> tuple:
    pws, err = _projects_ws()
    if err:
        return False, err
    row = _find_row(pws, "ID", pid)
    if row is None:
        return False, t("Project not found.")
    pws.delete_rows(row)
    # borrar sus actividades
    aws, err2 = _activities_ws()
    if not err2:
        recs = valores.canonizar(columnas.canonizar(aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
        for i in range(len(recs) - 1, -1, -1):
            if str(recs[i].get("ProjectID", "")) == str(pid):
                aws.delete_rows(i + 2)
    _invalidate()
    return True, t("Project deleted.")


# ── Actividades ──────────────────────────────────────────────────
def list_activities(pid: str) -> list:
    out = [r for r in _records(ACTIVITIES_SHEET)
           if str(r.get("ProjectID", "")) == str(pid)]
    out.sort(key=lambda r: _num(r.get("Order")))
    return out


def update_activity_progress(pid: str, orden, avance, fecha_inicio="", fecha_fin="",
                             nota=None) -> tuple:
    """El usuario de campo actualiza el Avance% (0-100) de una actividad.
    Recalcula el avance y el estado del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    avance = max(0.0, min(100.0, _num(avance)))
    recs = valores.canonizar(columnas.canonizar(aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    target = None
    for i, r in enumerate(recs):
        if str(r.get("ProjectID", "")) == str(pid) and str(r.get("Order", "")) == str(orden):
            target = i + 2
            break
    if target is None:
        return False, t("Activity not found.")
    aws.update_cell(target, _ACOL["Progress"], str(avance))
    if fecha_inicio:
        aws.update_cell(target, _ACOL["ActualStartDate"], fecha_inicio)
    if fecha_fin:
        aws.update_cell(target, _ACOL["ActualEndDate"], fecha_fin)
    if nota is not None:
        aws.update_cell(target, _ACOL["Note"], nota)

    # Recalcular el avance del proyecto EN MEMORIA (recs ya leídas, sin re-leer)
    proj_acts = []
    for r in recs:
        if str(r.get("ProjectID", "")) != str(pid):
            continue
        rr = dict(r)
        if str(rr.get("Order", "")) == str(orden):
            rr["Progress"] = avance
        proj_acts.append(rr)
    nuevo  = compute_avance(proj_acts)
    prj    = get_project(pid)                       # cacheado
    manual = str(prj.get("ManualStatus", "")) if prj else ""
    _tipo  = str(prj.get("Type", "")) if prj else ""
    update_project(pid, {"Progress": nuevo, "Status": derive_estado(nuevo, manual, _tipo)})
    # update_project ya invalida el caché de lecturas
    return True, f"{t('Progress updated. Project')}: {nuevo}%"


def _recompute_project_avance(pid):
    """Recalcula el avance y el estado del proyecto según sus actividades actuales."""
    acts   = list_activities(pid)
    nuevo  = compute_avance(acts)
    prj    = get_project(pid)
    manual = str(prj.get("ManualStatus", "")) if prj else ""
    _tipo  = str(prj.get("Type", "")) if prj else ""
    update_project(pid, {"Progress": nuevo, "Status": derive_estado(nuevo, manual, _tipo)})
    return nuevo


def add_activity(pid, nombre, duracion=1, peso=0) -> tuple:
    """Agrega una actividad al final del cronograma (avance 0) y recalcula el % del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    acts  = list_activities(pid)
    orden = int(max([_num(a.get("Order")) for a in acts], default=0) + 1)
    aws.append_row([pid, str(orden), str(nombre), str(int(_num(duracion) or 1)),
                    str(_num(peso)), "0", "", "", ""], value_input_option="RAW")
    _invalidate()
    _recompute_project_avance(pid)
    return True, t("Activity added.")


def delete_activity(pid, orden) -> tuple:
    """Elimina una actividad y recalcula el % del proyecto."""
    aws, err = _activities_ws()
    if err:
        return False, err
    recs = valores.canonizar(columnas.canonizar(aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    target = None
    for i, r in enumerate(recs):
        if str(r.get("ProjectID", "")) == str(pid) and str(r.get("Order", "")) == str(orden):
            target = i + 2
            break
    if target is None:
        return False, t("Activity not found.")
    aws.delete_rows(target)
    _invalidate()
    _recompute_project_avance(pid)
    return True, t("Activity deleted.")


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
    recs = valores.canonizar(columnas.canonizar(aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    rowmap = {str(r.get("Order", "")): (i + 2, r)
              for i, r in enumerate(recs) if str(r.get("ProjectID", "")) == str(pid)}
    batch = []
    for c in (cambios or []):
        hit = rowmap.get(str(c.get("orden")))
        if hit is None:
            continue
        row, r = hit
        av = max(0.0, min(100.0, _num(c.get("avance"))))
        fi = str(r.get("ActualStartDate", "")).strip()
        ff = str(r.get("ActualEndDate", "")).strip()
        batch.append({"range": f"{_col_letter(_ACOL['Progress'])}{row}", "values": [[str(av)]]})
        if av > 0 and not fi:                        # arranca → inicio real = hoy
            batch.append({"range": f"{_col_letter(_ACOL['ActualStartDate'])}{row}",
                          "values": [[hoy]]})
        if av >= 100 and not ff:                     # completa → fin real = hoy
            batch.append({"range": f"{_col_letter(_ACOL['ActualEndDate'])}{row}",
                          "values": [[hoy]]})
        elif av < 100 and ff:                        # reabierta → borrar fin real
            batch.append({"range": f"{_col_letter(_ACOL['ActualEndDate'])}{row}",
                          "values": [[""]]})
        if "nota" in c:
            batch.append({"range": f"{_col_letter(_ACOL['Note'])}{row}",
                          "values": [[str(c.get("nota", ""))]]})
    if not batch:
        return True, t("No changes to save.")
    try:
        aws.batch_update(batch, value_input_option="RAW")
    except Exception as ex:
        return False, f"{t('Error saving')}: {ex}"
    # ⚠️ El ORDEN importa: `_recompute_project_avance` lee `list_activities`, que
    #    está CACHEADA (120 s). Hasta v372 esto corría ANTES de `_invalidate()`, así
    #    que el % del proyecto se recalculaba con las actividades VIEJAS — y la
    #    caché está caliente SIEMPRE, porque la pantalla acaba de pintar esa misma
    #    tabla para editarla. Medido contra la hoja real: actividades al 26,0% y el
    #    proyecto escrito en 0,0%. Los otros 3 sitios (add/delete_activity,
    #    save_activities) ya lo hacían en este orden.
    _invalidate()
    _recompute_project_avance(pid)
    return True, t("Progress saved.")


def save_activities(pid, edits) -> tuple:
    """Guarda ediciones de la tabla (nombre/días/peso/orden) en UNA sola escritura (batch).
    `edits`: lista de dicts con 'orden0' (orden original, para localizar la fila) +
    los campos nuevos (Nombre/DuracionDias/Peso/Orden). Preserva el Avance (lo pone el campo)."""
    aws, err = _activities_ws()
    if err:
        return False, err
    recs = valores.canonizar(columnas.canonizar(aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    rowmap = {str(r.get("Order", "")): i + 2
              for i, r in enumerate(recs) if str(r.get("ProjectID", "")) == str(pid)}
    batch = []
    for e in edits:
        row = rowmap.get(str(e.get("orden0")))
        if row is None:
            continue
        for field in ("Name", "DurationDays", "Weight", "Order"):
            if field in e and field in _ACOL:
                batch.append({"range": f"{_col_letter(_ACOL[field])}{row}",
                              "values": [[str(e[field])]]})
    if batch:
        try:
            aws.batch_update(batch, value_input_option="RAW")
        except Exception as ex:
            return False, f"{t('Error saving activities')}: {ex}"
    _invalidate()
    _recompute_project_avance(pid)
    return True, t("Activities updated.")


# ── Horas trabajadas (desde el fichaje) ──────────────────────────
def project_hours(proyecto_nombre: str, grupo: str = None, pid: str = "") -> float:
    """Horas del fichaje de un proyecto. Con `pid` cruza por ID (v145); si no, por nombre."""
    total = 0.0
    # ⚠️ v380: también por aquí. Arreglé `project_hours_bulk` dando por hecho que era
    # la que usaban las tarjetas, y la cartera del PROPIETARIO llama a ESTA una vez por
    # obra — así que en pantalla seguían saliendo `0h` en las 12. Medir qué función
    # llama la pantalla, no suponerlo.
    for r in _fichajes_visibles(grupo):
        if not timeclock.es_del_proyecto(r, pid, proyecto_nombre):
            continue
        if grupo is not None and str(r.get("Group", "")) != str(grupo):
            continue
        total += _num(r.get("Hours"))
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
    # ⚠️ v422: e incluye las localizaciones internas por el MISMO motivo — es un mapa
    # de identidad, no una lista de obras. Sin ellas, las horas fichadas al almacén no
    # resolverían su ID y se perderían de la cuenta, en silencio.
    for p in list_projects(grupo=grupo, incluir_archivados=True, incluir_internos=True):
        n = str(p.get("Name", "")).strip().casefold()
        if n:
            idx[n] = str(p.get("ID", ""))
    out = {}
    # ⚠️ v379: el fichaje vive en el libro del cliente. La sesión del PROPIETARIO no
    # tiene grupo, así que sin el ámbito leía el maestro y su cartera mostraba **0 h
    # en todas las obras** — visible en pantalla en cuanto la fase 2 le devolvió los
    # proyectos. Mismo criterio que `_registros_visibles`: el grupo explícito manda
    # solo si quien pregunta puede verlo, para no convertir el argumento en llave.
    for r in _fichajes_visibles(grupo):
        if grupo is not None and str(r.get("Group", "")) != str(grupo):
            continue
        pid = timeclock.pid_of(r) or idx.get(
            str(r.get("Project", "")).strip().casefold(), "")
        if not pid:
            continue                           # fichaje de algo que ya no existe
        out[pid] = out.get(pid, 0.0) + _num(r.get("Hours"))
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
    actuales = {str(p.get("ID")): _num(p.get("WeightInGrouping"))
                for p in list_projects(grupo=grupo, agrupacion_id=gid, incluir_archivados=True)}
    nuevos = {str(k): float(v or 1) for k, v in (miembros or {}).items()}

    cambios, errores = 0, []
    for pid, peso in nuevos.items():                   # altas y cambios de peso
        if pid not in actuales or abs(actuales[pid] - peso) > 1e-9:
            ok, msg = update_project(pid, {"GroupingID": gid,
                                           "WeightInGrouping": peso})
            cambios += 1 if ok else 0
            if not ok:
                errores.append(f"{pid}: {msg}")
    for pid in actuales:                               # bajas
        if pid not in nuevos:
            ok, msg = update_project(pid, {"GroupingID": "", "WeightInGrouping": 0})
            cambios += 1 if ok else 0
            if not ok:
                errores.append(f"{pid}: {msg}")

    if errores:
        return False, "  ·  ".join(errores[:3])
    return True, (f"{cambios} " + t("project(s) updated.") if cambios
                  else t("No changes to save."))


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
        pid, nom = str(p.get("ID", "")), str(p.get("Name", ""))
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
        peso = _num(p.get("WeightInGrouping")) or 1.0
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
                _f = (dia - x0) / (x1 - x0) if x1 != x0 else 0
                return y0 + (y1 - y0) * _f
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
    tot_peso = sum(_num(p.get("WeightInGrouping")) for p in proys)
    if tot_peso <= 0:
        avance = 0.0
    else:
        avance = round(sum(_num(p.get("WeightInGrouping")) * _num(p.get("Progress"))
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
        y, m, d = str(prj.get("StartDate", "")).split("-")
        start = date(int(y), int(m), int(d))
    except Exception:
        start = clock.today()
    custom = [{"nombre":   a.get("Name", ""),
               "duracion": _num(a.get("DurationDays")) or 1.0,
               "peso":     _num(a.get("Weight"))} for a in acts]
    sched     = build_schedule(1, start, {}, custom_rows=custom)
    avances   = [_num(a.get("Progress")) for a in acts]
    today_day = (clock.today() - start).days

    def _day_off(s):
        try:
            y, m, dd = str(s).split("-")
            return (date(int(y), int(m), int(dd)) - start).days
        except Exception:
            return None
    windows = [(_day_off(a.get("ActualStartDate")), _day_off(a.get("ActualEndDate")))
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
            if str(r.get("ProjectID", "")) == str(pid)]


def add_document(pid, nombre, tipo, drive_id, subido_por="") -> tuple:
    dws, err = _documents_ws()
    if err:
        return False, err
    dws.append_row([pid, nombre, tipo, drive_id, subido_por,
                    clock.now().strftime("%Y-%m-%d %H:%M:%S")], value_input_option="RAW")
    _invalidate()
    return True, t("Document recorded.")


def delete_document_record(pid, drive_id) -> tuple:
    dws, err = _documents_ws()
    if err:
        return False, err
    recs = valores.canonizar(columnas.canonizar(dws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
    for i, r in enumerate(recs):
        if str(r.get("ProjectID", "")) == str(pid) and str(r.get("DriveID", "")) == str(drive_id):
            dws.delete_rows(i + 2)
            _invalidate()
            return True, t("Document deleted.")
    return False, t("Record not found.")


# ── Ganancia por trabajador y hora (v360) ────────────────────────
def ganancia_hora(pid: str, prj: dict = None) -> dict:
    """{usuario: ganancia $/h} de este proyecto. {} si aún usa el modelo viejo."""
    if prj is None:
        prj = get_project(pid) or {}
    try:
        d = json.loads(str(prj.get("HourlyProfitJSON", "") or "{}"))
        return {str(k): _num(v) for k, v in d.items() if _num(v) != 0}
    except Exception as e:
        logger.warning("projects: GananciaHoraJSON inválido en %s: %s", pid, e)
        return {}


def set_ganancia_hora(pid: str, mapa: dict) -> tuple:
    """Fija cuánto se quiere ganar por hora con cada persona en ESTE proyecto.

    ⚠️ Un mapa vacío devuelve el proyecto al modelo viejo (`MargenMO`), que es una
    vuelta atrás legítima: si te equivocaste al migrarlo, puedes deshacerlo.
    """
    limpio = {str(k): round(_num(v), 2) for k, v in (mapa or {}).items() if _num(v) > 0}
    return update_project(pid, {"HourlyProfitJSON": json.dumps(limpio, ensure_ascii=False)})


def ganancia_fija(pid: str, prj: dict = None) -> float:
    """Ganancia FIJA de la obra, en dinero (v373). 0.0 si no tiene.

    ⚠️ Es un importe a nivel de PROYECTO, no por persona ni por hora: existe para las
    obras cuyo valor no está en las horas (un delivery, un suministro), donde la
    ganancia por hora no tiene sobre qué aplicarse y la obra saldría valiendo su costo.
    """
    if prj is None:
        prj = get_project(pid) or {}
    return max(0.0, _num(prj.get("FixedProfit")))


def set_ganancia_fija(pid: str, valor) -> tuple:
    """Fija (o quita, con 0) la ganancia fija de la obra.

    ⚠️ Poner 0 la QUITA — la vuelta atrás tiene que existir (regla v340/v346): si te
    equivocaste de obra, se deshace sin dejar un número inventado en la estimación.
    """
    v = max(0.0, _num(valor))
    return update_project(pid, {"FixedProfit": str(round(v, 2)) if v > 0 else ""})

# ══════════════════════════════════════════════════════════
#  Head installer/s (v459) — antes «Engineer in charge»
# ══════════════════════════════════════════════════════════
# ⚠️ Se guardan los LOGIN, no los nombres, separados por «;» (igual que
# `CampoAsignados`). El login ES la identidad: dos personas pueden llamarse igual —
# ya pasó con «Mei Chen» (v413)— y un nombre además puede cambiar, mientras que el
# login no. El nombre se resuelve solo al MOSTRAR.
#
# ⚠️ La columna sigue llamándose `Ingeniero`: renombrarla obligaría a tocar los ~10
# sitios que la leen sin ganar nada, y el nombre de una columna es un identificador
# interno, no una etiqueta de pantalla (la regla de v232/v442: se cambia lo que se
# MUESTRA, nunca la clave).
def head_installers(prj: dict) -> list:
    """Los LOGIN de los head installers de una obra. [] si no hay."""
    return [x.strip() for x in str((prj or {}).get("HeadInstallers", "")).split(";") if x.strip()]


def head_installers_label(prj: dict, grupo: str = "") -> str:
    """«Javier López, Mei Chen» — para pantalla, informes y correos.

    ⚠️ Desempata homónimos con `auth.etiqueta_usuarios` (v413): si dos personas se
    llaman igual, se añade el login para poder distinguirlas.
    ⚠️ Y degrada al valor CRUDO si no se puede leer la lista de usuarios: un fallo de
    lectura no puede dejar el informe sin responsable.
    """
    _ids = head_installers(prj)
    if not _ids:
        return ""
    try:
        from core import auth
        _us = auth.list_users(grupo or str((prj or {}).get("Group", "")))
        _etq = auth.etiqueta_usuarios(_us)
        _por_login = {str(u.get("User")): u for u in _us}
        return ", ".join(_etq.get(i) or str(_por_login.get(i, {}).get("Name") or i)
                         for i in _ids)
    except Exception as e:
        logger.warning("head_installers_label: no se pudo resolver el nombre: %s", e)
        return ", ".join(_ids)

