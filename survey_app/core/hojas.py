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

import streamlit as st

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
        return {}


def invalidar():
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
    datos = _lote(timeclock.sheet_id_para(titulo, grupo)).get(titulo)
    if datos is None:
        if cabeceras is None:
            return None                   # que el llamador use su propio lector
        try:
            w = timeclock.get_sheet(titulo, tuple(cabeceras), grupo=grupo)
            return w.get_all_records(numericise_ignore=["all"])
        except Exception as e:
            logger.warning("hojas: lectura suelta de %s falló: %s", titulo, e)
            return []
    if not datos:
        return []
    cab = [str(c) for c in datos[0]]
    n = len(cab)
    out = []
    for fila in datos[1:]:
        vals = [str(v) for v in fila[:n]] + [""] * max(0, n - len(fila))
        out.append(dict(zip(cab, vals)))
    return out


# ── IDs que NO se reciclan (v427) ────────────────────────────────────────────
_RE_ID = None


def ids_referenciados(prefijo: str, propia: str = "", sheet_id: str = "") -> set:
    """IDs con ese `prefijo` que aparecen en CUALQUIER hoja menos la suya.

    ## Por qué existe

    Los 13 generadores de la app hacen `max(los que existen) + 1`, así que **borrar
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
        hay = _existentes(sheet_id)
        # Todas las del lote MÁS `Auditoria`, que no está en HOJAS_LECTURA (su lector
        # va aparte) y es justamente donde queda constancia de lo borrado.
        titulos = [h for h in tuple(HOJAS_LECTURA) + ("Auditoria",)
                   if h.strip().lower() in hay and h.strip().lower() != propia_l]
        if not titulos:
            return set()
        r = lib.values_batch_get([f"'{h}'" for h in titulos])
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
    saltados = []
    for _ in range(tope):
        if f"{prefijo}{n:0{ancho}d}" not in usados:
            break
        saltados.append(n)
        n += 1
    if saltados:
        logger.info("hojas: %s salta %s (referenciados en otras hojas)",
                    prefijo, saltados)
    return f"{prefijo}{n:0{ancho}d}"
