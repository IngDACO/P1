"""Lector por LOTES del libro de Sheets (v339) — el techo de cuota.

## El problema, medido

La API de Sheets limita a **60 lecturas por minuto y por usuario**, y "usuario" aquí
es la **cuenta de servicio**: una sola para TODOS los grupos. O sea que el techo no
crece al añadir clientes, se reparte entre ellos.

Medido en producción antes de este módulo:
- arranque en frío: **12 llamadas** · 859 ms de media cada una
- estado sostenido: **~6 lecturas/min por usuario activo** (TTL 120 s)
- → **~10 usuarios activos en paralelo**, o **5 arranques por minuto**, antes del 429

De esas llamadas, **15 de 19 eran `values/{hoja}`: una por hoja**. La app lee 21 hojas
distintas con 30 lectores cacheados, y cada uno pedía la suya por separado.

## La palanca

`spreadsheets.values.batchGet` trae **muchos rangos en UNA sola petición**, y la cuota
cuenta peticiones. Pedir 10 hojas de golpe cuesta 1 lectura, no 10.

Este módulo hace exactamente eso: la primera hoja que alguien pida dispara **una**
llamada que se trae TODAS, y el resto salen de ahí.

## Lo que NO hace

⚠️ **Las rutas de ESCRITURA siguen leyendo frescas.** `_find_row`, `_next_id` y
`_ids_frescos` van directos al worksheet a propósito: usar una caché para decidir
dónde escribir o qué ID toca es como se corrompen los datos (v323). Este módulo es
solo para LECTURA de display.
"""
import logging
import time

import streamlit as st

from core import columnas
from core import valores
from core import timeclock

logger = logging.getLogger(__name__)

# Las hojas que la app lee para MOSTRAR. El orden no importa; la lista sí: pedir de
# más cuesta ancho de banda, no cuota (es 1 petición igual), pero pedir de menos
# obliga a una segunda llamada.
HOJAS_LECTURA = (
    # ⚠️ "Sheet1" es la del FICHAJE y es la más leída de todas (horas, costo de mano
    # de obra, conciliación, plan-vs-real). Se llama así porque es la hoja original
    # del libro; el nombre no se toca (renombrarla rompería `_cached_ws`).
    "Sheet1",
    "Projects", "Activities", "Groupings", "Documents", "Alerts",
    "Login", "Groups", "Credentials", "Expenses", "Clients", "Invoices",
    "Payroll", "Assets", "AssetCategories", "AssetMovements", "Absences",
    "Roster", "Jobs", "ToolRuns", "Rails",
    "AuditTrail", "PurchaseOrders",
    "Catalogue", "Quotes",   # v352/v353 — cotizaciones     # v342 — si no entra aquí, sería una llamada suelta
    # ⚠️ v461: si NO entra aquí, `registros(SHEET)` sin cabeceras devuelve None y
    # `correcciones` leería VACÍO PARA SIEMPRE, sin un solo error (regla v353).
    "TimeCorrections",
    # ⚠️ v472: misma regla — `library` lee con `hojas.registros(SHEET, HEADERS)`,
    # asi que fuera del lote costaria una llamada suelta por sesion (v339).
    "Library", "LibraryModels",
    # ⚠️ v507: MISMA regla que la nota de v461, y volvió a morder. `claims` lee con
    # `registros(SHEET)` sin cabeceras: fuera del lote devuelve None y el cobro de obra
    # leería VACÍO PARA SIEMPRE sin un solo error — la fila estaba escrita en la hoja y
    # la app no la veía. Lo cazó el ejercicio contra la hoja real, no la suite.
    "Variations", "Claims",
    # ⚠️ v514: y otra vez la misma regla. `stage_progress` lee con `registros(SHEET)`
    # sin cabeceras, así que fuera del lote devolvería None y el avance por actividad
    # se acreditaría en la hoja sin que la app volviera a verlo NUNCA — exactamente el
    # fallo de v507. Van tres veces (v461, v507, y esta sería la tercera si faltara):
    # por eso existe `check_hojas_en_lote`.
    "StageProgress",
    # ⚠️ v516: `daily_log` lee con `registros(SHEET)` sin cabeceras, igual que las tres
    # anteriores. Fuera del lote, un parte diario se escribiría en la hoja y la app no
    # volvería a verlo NUNCA — y aquí duele el doble, porque el valor de esto es
    # justamente que el texto se acumule.
    "DailyLogs",
    # ⚠️ v610: la memoria del agente del parte (`agente_memoria`) lee con `registros(SHEET)` sin
    # cabeceras. Fuera de aquí, las lecciones se escribirían en el maestro y el agente no las
    # volvería a leer NUNCA — la regla de v461/v507/v514 por cuarta vez. La cazó romper_v430
    # (su guardián, rojo de base) antes de desplegar; verif_v610 la vigila desde ahora.
    "AgentMemory",
)


def _libro(sheet_id: str = ""):
    """El Spreadsheet del libro que toque (v359: uno por cliente)."""
    return timeclock._abrir(sheet_id or timeclock.sheet_id_para("Sheet1"))


def _existentes(sheet_id: str = "") -> set:
    """Títulos de las hojas que EXISTEN, en minúsculas.

    ⚠️ Sale del índice que `timeclock._libro()` ya construye y cachea (v290), así
    que **no cuesta ninguna llamada**. Hace falta porque `values_batch_get`
    rechaza la petición ENTERA si un solo rango no existe: pedir una hoja que
    todavía no se ha creado (p. ej. `MovimientosActivo` mientras no haya activos)
    tumbaba el lote completo y devolvía a leer hoja por hoja.
    """
    try:
        hojas, _cab = timeclock._libro(sheet_id or timeclock.sheet_id_para("Sheet1"))
        return set(hojas or {})
    except Exception as e:
        logger.warning("hojas: no se pudo leer el índice del libro: %s", e)
        return set()


# ⚠️ v611 · El índice de pestañas (`timeclock._libro`) vive en `@st.cache_resource` y NO
# caduca, y el lote solo pide las hojas que están en él. Una hoja que crea OTRO proceso (un
# script de siembra o de migración) no entraba nunca: los lectores sin cabeceras leían VACÍO
# hasta reiniciar la app. Visto el 27/10/2026 con `AgentMemory`, sembrada desde fuera: «Nothing
# learned yet» con 8 filas en la hoja. Se rehace el índice de ESE libro (2 llamadas) como mucho
# una vez cada `_REFRESCO_S`: una hoja que de verdad no existe (las de grupo en el maestro) no
# cuesta más que eso, y «para siempre» pasa a ser «10 minutos como mucho».
_REFRESCO_S = 600
_refrescado = {}            # {sheet_id: time.monotonic() del último refresco}


def _indice_al_dia(sheet_id: str) -> bool:
    """Rehace el índice de pestañas de `sheet_id` si no se rehízo en `_REFRESCO_S`.
    True si lo rehízo (y entonces el índice ya trae lo que haya creado otro proceso)."""
    if not sheet_id:
        return False
    ahora = time.monotonic()
    _ult = _refrescado.get(sheet_id)
    if _ult is not None and ahora - _ult < _REFRESCO_S:
        return False
    _refrescado[sheet_id] = ahora
    try:
        timeclock._libro.clear(sheet_id)
        return True
    except Exception as e:
        logger.warning("hojas: no se pudo refrescar el índice de %s: %s", sheet_id, e)
        return False


def _aparecio(sheet_id: str, titulo: str) -> bool:
    """Una hoja del lote que NO vino en él: ¿existe, rehecho el índice? Si sí, se tira el lote
    de ese libro para que la próxima petición la traiga (1 llamada).
    (Si otro camino —`ids_referenciados`— ya rehízo el índice dentro del tope, aquí no se rehace,
    pero el lote la recoge solo al caducar: 120 s como mucho.)"""
    if titulo not in HOJAS_LECTURA or not _indice_al_dia(sheet_id):
        return False
    if timeclock.titulo_real(titulo, sheet_id).strip().lower() not in _existentes(sheet_id):
        return False
    logger.info("hojas: %s apareció al rehacer el índice; se vuelve a pedir el lote", titulo)
    try:
        _lote.clear(sheet_id)
    except Exception:
        # como `invalidar`: si no se puede tirar el de ese libro, todos; y si tampoco, nada
        # (una LECTURA no puede reventar por esto — lo cazó verif_v590 en la suite de v611).
        try:
            _lote.clear()
        except Exception:
            pass
    return True


@st.cache_data(ttl=120, show_spinner=False)
def _lote(sheet_id: str = "") -> dict:
    """UNA llamada `values:batchGet` con todas las hojas → {titulo: [[celdas]]}.

    ⚠️ Devuelve valores CRUDOS (como `get_all_values`), no registros: así este
    módulo no impone un formato y cada lector arma lo suyo con `registros()`.
    """
    # ⚠️ v359: el lote se cachea POR LIBRO. Con una sola entrada, el segundo cliente
    # leería los datos del primero — justo lo que este cambio viene a impedir.
    sheet_id = sheet_id or timeclock.sheet_id_para("Sheet1")
    lib = _libro(sheet_id)
    if lib is None:
        return {}
    try:
        hay = _existentes(sheet_id)
        # v465: se pide el titulo que EXISTE (el nuevo o, mientras el libro no se
        # haya renombrado, el viejo) y se devuelve bajo el nombre CANONICO, para
        # que `registros("Projects")` funcione con el libro en cualquiera de los
        # dos estados. Sin esto el lote se saltaria esas hojas y cada una costaria
        # una llamada suelta — el problema que v339 vino a quitar.
        _reales = {}
        for h in HOJAS_LECTURA:
            r = timeclock.titulo_real(h, sheet_id)
            if r.strip().lower() in hay:
                _reales[r] = h
        if not _reales:
            return {}
        # `values_batch_get` acepta A1 por hoja. Sin límite de columna: trae lo que haya.
        rangos = [f"'{r}'" for r in _reales]
        r = lib.values_batch_get(rangos)
        out = {}
        for tramo in (r.get("valueRanges") or []):
            # el rango vuelve como "'Hoja'!A1:Z99" → recuperamos el título
            rng = str(tramo.get("range", ""))
            titulo = rng.split("!")[0].strip("'")
            out[_reales.get(titulo, titulo)] = tramo.get("values") or []
        return out
    except Exception as e:
        # Si el lote falla (una hoja que aún no existe, un hipo de la API), NO se
        # rompe nada: `registros()` cae al lector de siempre, hoja por hoja.
        logger.warning("hojas: el lote falló, se lee hoja por hoja: %s", e)
        # ⚠️ v466: y se TIRA el índice de pestañas. Vive en `@st.cache_resource`, que
        # NO caduca, así que si una hoja se renombra el proceso se queda pidiendo el
        # nombre viejo **para toda su vida**: el lote falla en cada pasada y las
        # pantallas salen a CERO con los datos intactos en el libro. Pasó al renombrar
        # las pestañas al inglés (v465) y solo se arreglaba reiniciando a mano.
        # Tirarlo aquí es barato —se reconstruye en 2 llamadas (v290)— y solo ocurre
        # cuando el lote ya ha fallado.
        try:
            timeclock._libro.clear()
        except Exception:
            pass
        return {}


def invalidar(titulo: str = "", grupo: str = None):
    """Tira el lote. Con `titulo`, SOLO el del libro donde vive esa hoja.

    ## Por qué recibe el título

    ⚠️ Antes hacía `_lote.clear()` sin argumento, que borra la entrada de **todos los
    libros**: una escritura de un cliente obligaba a releer a todos los demás, así que
    los inquilinos se acoplaban entre sí contra el techo de 60 lecturas/min de la
    ÚNICA cuenta de servicio.

    ⚠️ Y el argumento es el TÍTULO, no el `sheet_id`, porque las hojas GLOBALES
    (`Login`, `Groups`, `Rails`, `Manuals`, `Library`, `LibraryModels`) viven en el
    MAESTRO y no en el libro del grupo: resolver «el libro de la sesión» tras escribir
    en una de ellas limpiaría **otro** libro y dejaría el valor viejo hasta 120 s —
    el «lo guardé y no sale» que v339 vino a evitar.

    ⚠️ **Sin título se tira ENTERO**, que es el comportamiento de siempre y el seguro:
    limpiar de más cuesta una lectura; limpiar el libro equivocado enseña datos viejos.
    Un llamador que se olvide degrada al comportamiento anterior, no rompe nada.
    """
    sid = ""
    if titulo:
        try:
            sid = timeclock.sheet_id_para(titulo, grupo)
        except Exception as e:
            # No se pudo resolver el libro: se limpia TODO, que es lo conservador.
            logger.warning("hojas: no se pudo resolver el libro de %s: %s", titulo, e)
    try:
        if sid:
            _lote.clear(sid)
        else:
            _lote.clear()
    except Exception:
        # `clear(arg)` existe desde Streamlit 1.36; si algún día no estuviera, se cae
        # al borrado completo antes que dejar la caché sucia.
        try:
            _lote.clear()
        except Exception:
            pass


def registros(titulo: str, cabeceras=None, grupo: str = None):
    """Filas de una hoja como dicts, **idéntico a `get_all_records(numericise_ignore=['all'])`**.

    Es decir: la fila 1 es la cabecera, todo llega como TEXTO (nunca numerizado —
    conservar los ceros a la izquierda importa, regla de v42) y las filas cortas se
    rellenan con "" hasta la cabecera.

    Si la hoja no vino en el lote, cae al camino de siempre (una llamada suya).
    """
    sid = timeclock.sheet_id_para(titulo, grupo)
    datos = _lote(sid).get(titulo)
    # ⚠️ v611 · puede existir sin estar en el índice (la creó otro proceso): ver `_aparecio`.
    # Solo sin cabeceras: con ellas cae a `get_sheet`, que ya rehace el índice antes de crear.
    if datos is None and cabeceras is None and _aparecio(sid, titulo):
        datos = _lote(sid).get(titulo)
    if datos is None:
        if cabeceras is None:
            return None                   # que el llamador use su propio lector
        try:
            w = timeclock.get_sheet(titulo, tuple(cabeceras), grupo=grupo)
            return valores.canonizar(
                columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), titulo)
        except Exception as e:
            logger.warning("hojas: lectura suelta de %s falló: %s", titulo, e)
            return []
    if not datos:
        return []
    # ⚠️ v468: se canoniza la CABECERA (una vez), no fila a fila: asi el codigo ve
    # siempre el nombre nuevo, tenga el libro el viejo o el nuevo.
    cab = [columnas.canon(str(c)) for c in datos[0]]
    n = len(cab)
    out = []
    for fila in datos[1:]:
        vals = [str(v) for v in fila[:n]] + [""] * max(0, n - len(fila))
        out.append(dict(zip(cab, vals)))
    # ⚠️ v469: y despues los VALORES, solo en las columnas de negocio. El orden
    # importa: `valores.canonizar` espera las claves ya canonizadas.
    return valores.canonizar(out, titulo)


# ── Leer y escribir VARIAS hojas en una llamada, para GUARDAR (v528) ──────────
# ⚠️ Para escribir hay que leer FRESCO (decidir dónde escribir con una caché es como se
# corrompen los datos, v323), y eso costaba una lectura POR HOJA. Guardar una etapa
# leía y escribía tres hojas por separado: ~9 llamadas, 7-8 s en producción, donde cada
# llamada tarda ~1 s. Las tres viven en el MISMO libro, así que se piden juntas.
def _mismo_libro(hojas_ws):
    """El Spreadsheet común a todas, o `None` si no lo comparten (o no se sabe)."""
    ss = None
    for w in hojas_ws:
        s = getattr(w, "spreadsheet", None)
        if s is None or not hasattr(s, "values_batch_get") or not getattr(s, "id", ""):
            return None
        if ss is not None and s.id != ss.id:
            return None
        ss = s
    return ss


def _a_registros(datos, titulo):
    """Filas crudas → registros, **idéntico a `get_all_records(numericise_ignore=['all'])`**
    canonizado: el registro `i` es la fila `i + 2` de la hoja (las filas vacías de en
    medio vienen como `[]` y cuentan, igual que ahí)."""
    if not datos:
        return []
    cab = [columnas.canon(str(c)) for c in datos[0]]
    n = len(cab)
    out = [dict(zip(cab, [str(v) for v in f[:n]] + [""] * max(0, n - len(f))))
           for f in datos[1:]]
    return valores.canonizar(out, titulo)


def frescas(hojas_ws: dict) -> dict:
    """`{titulo: worksheet}` → `{titulo: [registros]}` leídos AHORA, en UNA llamada.

    `titulo` es el nombre CANÓNICO de la hoja (el que decide qué valores se canonizan);
    el que se pide a Google es el de la worksheet, que ya es el que existe en el libro.

    ⚠️ Si alguna no comparte libro con las demás, se lee cada una por su lado: más
    lento, igual de correcto. Y si Google falla, **lanza**: quien guarda no puede
    decidir filas sobre una lectura que no llegó.
    """
    # ⚠️ La variable es `tit`, nunca `t`: `t` es la función de traducción (v439/v498).
    ws = [w for w in hojas_ws.values() if w is not None]
    ss = _mismo_libro(ws)
    if ss is None:
        return {tit: valores.canonizar(columnas.canonizar(
                    w.get_all_records(numericise_ignore=["all"])), tit)
                for tit, w in hojas_ws.items() if w is not None}
    from gspread.utils import absolute_range_name
    claves = [tit for tit, w in hojas_ws.items() if w is not None]
    r = ss.values_batch_get([absolute_range_name(hojas_ws[tit].title) for tit in claves])
    tramos = r.get("valueRanges") or []
    if len(tramos) != len(claves):
        # ⚠️ En inglés: puede llegar a la pantalla dentro de «Error saving: …» (v448).
        raise RuntimeError("Google returned %d of the %d sheets requested"
                           % (len(tramos), len(claves)))
    # ⚠️ Google devuelve los rangos en el MISMO orden en que se pidieron.
    return {tit: _a_registros(tr.get("values") or [], tit) for tit, tr in zip(claves, tramos)}


def escribir(partes) -> None:
    """`[(worksheet, [{"range": "G5", "values": [[...]]}, ...]), ...]` en UNA llamada.

    ⚠️ RAW, como todas las escrituras de la app (conserva ceros a la izquierda, v42).
    Si las hojas no comparten libro, una llamada por hoja, en el orden dado. Lanza si
    Google falla: quien llama decide qué decirle al usuario.
    """
    partes = [(w, lote) for w, lote in (partes or []) if w is not None and lote]
    if not partes:
        return
    ss = _mismo_libro([w for w, _l in partes])
    if ss is None or not hasattr(ss, "values_batch_update"):
        for w, lote in partes:
            w.batch_update([dict(x) for x in lote], value_input_option="RAW")
        return
    from gspread.utils import absolute_range_name
    ss.values_batch_update({
        "valueInputOption": "RAW",
        "data": [{"range": absolute_range_name(w.title, x["range"]), "values": x["values"]}
                 for w, lote in partes for x in lote]})


# ── IDs que NO se reciclan (v427) ────────────────────────────────────────────
_RE_ID = None


def _titulos(sheet_id: str = "") -> list:
    """Títulos REALES (con su caja) de todas las hojas del libro (v581).

    Sale del índice que `timeclock._libro()` ya construye y cachea (v290): **0
    llamadas**. Hace falta el título tal cual, no en minúsculas como `_existentes`,
    porque es lo que se pide en `values_batch_get`.
    """
    try:
        hojas, _cab = timeclock._libro(sheet_id or timeclock.sheet_id_para("Sheet1"))
        return [str(w.title) for w in (hojas or {}).values()]
    except Exception as e:
        logger.warning("hojas: no se pudo leer el índice del libro: %s", e)
        return []


def ids_referenciados(prefijo: str, propia: str = "", sheet_id: str = "") -> set:
    """IDs con ese `prefijo` que aparecen en CUALQUIER hoja menos la suya.

    ## Por qué existe

    Los generadores de la app hacen `max(los que existen) + 1`, así que **borrar
    la fila con el ID más alto libera ese número** y el siguiente alta lo reutiliza.
    Todo lo que hubiera quedado apuntando al ID viejo —una factura, un gasto, un
    fichaje— **se pega a la entidad nueva**.

    ⚠️ No es teórico: pasó en el ejercicio del ciclo de negocio de v426. Dos facturas
    de una prueba vieja apuntaban a `PRJ-0017`; al recrear ese ID, la obra nueva
    **heredó $1.000 de facturación ajena** y su pendiente de facturar bajó de $4.000
    a $3.000. Fue lo que destapó, tirando del hilo, que el P&L contaba las facturas
    anuladas.

    ## Qué se considera «referenciado»

    Que el ID aparezca **en cualquier celda de cualquier otra hoja**, incluidos los
    JSON incrustados (líneas de factura, `DatosJSON` del roster). Se busca por texto a
    propósito: saber en qué columna vive cada referencia obligaría a mantener un mapa
    de 12 hojas que envejecería al añadir la siguiente.

    ⚠️ **La hoja `Auditoria` cuenta también.** Ahí quedan registrados cambios de
    objetos que ya no existen, y eso es justo la señal que interesa: ese ID *se usó*.
    Reutilizarlo mezclaría dos historiales en el mismo identificador.

    ⚠️ v581 · **TODAS las hojas del libro, no una lista.** Hasta aquí se miraban las del
    lote (`HOJAS_LECTURA`) más la auditoría, y la lista envejeció exactamente como avisa
    el párrafo de arriba: `PreStarts` no está en el lote (su lector va aparte) y apunta
    a obras (PS-0002 → PRJ-0015 en cliente1). Borrada la obra, el ID se habría
    reutilizado y la obra nueva habría heredado el Pre-Start de otra. Los títulos salen
    del índice del libro (0 llamadas), así que la hoja que se añada mañana entra sola.

    ⚠️ **La hoja propia se EXCLUYE**: ahí el ID vive legítimamente, y contarla haría
    que ningún ID vivo pudiera existir.

    ## Coste

    Una llamada `values:batchGet` — la misma mecánica del lote de v339, pero **FRESCA**:
    esto es una ruta de ESCRITURA (decide qué ID se emite) y usar una caché para eso
    es como se corrompen los datos (regla v323). Crear algo es una acción humana y
    rara; una lectura de más ahí es barata.

    Si algo falla devuelve **vacío**, o sea el comportamiento de siempre: un fallo de
    lectura no puede impedir dar de alta.
    """
    import re
    pref = str(prefijo or "").strip()
    if not pref:
        return set()
    rx = re.compile(re.escape(pref) + r"\d+")
    propia_l = str(propia or "").strip().lower()
    try:
        sheet_id = sheet_id or timeclock.sheet_id_para("Sheet1")
        lib = _libro(sheet_id)
        if lib is None:
            return set()
        # ⚠️ La propia se excluye por su título REAL: en un libro que aún conserve el
        # nombre viejo (`Cotizaciones`), comparar con el nuevo no la excluiría.
        if propia_l:
            propia_l = timeclock.titulo_real(str(propia).strip(), sheet_id).strip().lower()
        # v581 · Todas las hojas que EXISTEN (la auditoría incluida, que es donde queda
        # constancia de lo borrado), no las de una lista que hay que acordarse de ampliar.
        # ⚠️ v611 · con el índice al día (como mucho 10 min de retraso): sale de una caché que
        # no caduca, y una pestaña que creó OTRO proceso se quedaba fuera de esta comprobación
        # para siempre — en una ruta de ESCRITURA, que es justo donde no puede fallar.
        _indice_al_dia(sheet_id)
        titulos = [h for h in _titulos(sheet_id) if h.strip().lower() != propia_l]
        if not titulos:
            return set()
        # ⚠️ v581 · `absolute_range_name` (como `frescas`): ahora entran títulos que pone
        # cualquiera, y con un apóstrofo («Rick's») el `'{h}'` a mano tumbaba el lote ENTERO
        # → vacío → la comprobación apagada sin avisar.
        from gspread.utils import absolute_range_name
        r = lib.values_batch_get([absolute_range_name(h) for h in titulos])
        out = set()
        for tramo in (r.get("valueRanges") or []):
            for fila in (tramo.get("values") or []):
                for celda in fila:
                    if pref in celda:
                        out.update(rx.findall(celda))
        return out
    except Exception as e:
        logger.warning("hojas.ids_referenciados(%s): %s", prefijo, e)
        return set()


def siguiente_id_libre(prefijo: str, maximo: int, propia: str = "",
                       ancho: int = 4, tope: int = 200) -> str:
    """El siguiente ID que NO esté ya referenciado en otra hoja (v427).

    `maximo` es el mayor número en uso HOY (lo que cada `_next_id` ya calcula leyendo
    fresco su propia hoja). Desde ahí se avanza saltando los que alguien referencia.

    ⚠️ `tope` acota el barrido: si algo va mal y todo pareciera ocupado, se devuelve
    el siguiente sin más en vez de colgarse. Fallar hacia el comportamiento de
    siempre es mejor que no poder crear nada.
    """
    return siguientes_ids_libres(prefijo, maximo, 1, propia=propia, ancho=ancho,
                                 tope=tope)[0]


def siguientes_ids_libres(prefijo: str, maximo: int, cuantos: int = 1, propia: str = "",
                          ancho: int = 4, tope: int = 200) -> list:
    """Los `cuantos` IDs siguientes que nadie referencia, con UNA sola lectura (v581).

    Para los altas EN LOTE (las nóminas de un periodo, las semanas nuevas del roster):
    pedir `siguiente_id_libre` fila a fila costaría una lectura del libro entero por
    fila contra el techo de 60/min, y numerar `max + 1, + 2…` a mano se saltaba la
    comprobación entera — así se colaban esos dos.
    """
    # ⚠️ Con su propia red, no solo con la de `ids_referenciados`: esta es la función
    # PÚBLICA, y un fallo de lectura NO puede impedir dar de alta. Hoy los tres
    # generadores además la envuelven en su try, pero depender de que el llamador se
    # acuerde es como se cuelan los fallos silenciosos.
    try:
        usados = ids_referenciados(prefijo, propia)
    except Exception as e:
        logger.warning("hojas.siguiente_id_libre(%s): %s — se emite sin comprobar",
                       prefijo, e)
        usados = set()
    n = int(maximo) + 1
    saltados, out = [], []
    for _k in range(max(1, int(cuantos or 1))):
        for _ in range(tope):
            if f"{prefijo}{n:0{ancho}d}" not in usados:
                break
            saltados.append(n)
            n += 1
        out.append(f"{prefijo}{n:0{ancho}d}")
        n += 1
    if saltados:
        logger.info("hojas: %s salta %s (referenciados en otras hojas)",
                    prefijo, saltados)
    return out
