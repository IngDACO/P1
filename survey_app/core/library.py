"""Biblioteca técnica: fotos, manuales y fichas por MARCA · MODELO · SECCIÓN.

Hasta v472 el material técnico vivía en dos sitios y ninguno servía para buscar «cómo
es el cuadro de maniobra de un Monospace»:

  · `manuals.py` indexa el TEXTO de los manuales (BM25) pero solo los identifica por un
    nombre libre — sin marca, sin modelo, sin sección.
  · `Documents` guarda fotos y archivos **pegados a un PROYECTO**, así que la foto de
    un operador de puerta vive dentro de la obra donde se sacó y no la encuentra quien
    la necesita tres meses después en otra obra.

Esto es la capa que faltaba. NO sustituye a `manuals`: aquel sigue dando la búsqueda
dentro del PDF (que es lo que alimenta al asistente); esta le pone encima la taxonomía
y añade el material que no es un manual.

## Decisiones del usuario, que explican la forma del módulo

| | |
|---|---|
| **Biblioteca aparte**, con su propia subida | no se alimenta etiquetando lo de las obras: es material de REFERENCIA, curado, no el archivo de una obra |
| **Vocabulario propio** de secciones | pensado para buscar documentación, no para planificar obra — por eso no reusa `schedule.PHASES` |
| **Catálogo mantenido por el propietario** | como `Rails`: se elige de una lista, no se teclea |
| **GLOBAL**, como los manuales | una sola biblioteca en el maestro; un manual de fábrica sirve a todos |
| **Solo el propietario sube** | control de calidad del material; todos consultan |

⚠️ Las dos hojas son GLOBALES, así que van en `timeclock.SHEETS_GLOBALES`. Sin eso,
cada cliente acabaría con su propia biblioteca VACÍA en su libro — lo contrario de
«global», y sin dar ningún error.

⚠️ Y se abren con `timeclock.get_sheet`, nunca con `_get_worksheet`: es el fallo real
de v404, donde el catálogo de rieles **escribía en el libro del cliente y leía del
maestro** porque el lector resuelve con `sheet_id_para` y el escritor no.
"""
import logging

import streamlit as st

from core import columnas, hojas, timeclock
from core.i18n import t

logger = logging.getLogger(__name__)

SHEET = "Library"
HEADERS = ["ID", "Brand", "Model", "Section", "Type", "Title", "Notes",
           "DriveID", "FileName", "MimeType", "UploadedBy", "Date"]

MODELOS_SHEET = "LibraryModels"
MODELOS_HEADERS = ["Brand", "Model", "Active"]

FOLDER_NAME = "COPEX Library"

# ⚠️ Vocabulario PROPIO de biblioteca (decisión del usuario), no las fases del
# cronograma: aquí se busca documentación, no se planifica obra. Y nace en INGLÉS
# porque se GUARDA en la hoja — traducirlo después obliga a migrar el histórico, que
# es lo que costó v453.
SECCIONES = [
    "Machine & traction",
    "Controller",
    "Shaft",
    "Pit",
    "Car",
    "Car door",
    "Landing doors",
    "Guide rails & brackets",
    "Counterweight",
    "Ropes & governor",
    "Safety gear",
    "Electrical & wiring",
    "Signalling",
    "Documentation",
]

TIPOS = ["photo", "manual", "datasheet", "diagram", "other"]

# ⚠️ Sin marca y sin modelo es un estado LEGÍTIMO, no un hueco: hay material de una
# marca sin modelo concreto (un catálogo general) y material que no es de ninguna
# (normativa, fichas genéricas). Exigirlos dejaría ese material fuera de la biblioteca,
# que es justo donde tiene que estar.
SIN_MARCA = "— any brand —"
SIN_MODELO = "— any model —"


def is_configured() -> bool:
    return timeclock._secrets_present()


# ── hojas ────────────────────────────────────────────────────────────────────
def _ws():
    """⚠️ `get_sheet`, no `_get_worksheet`: resuelve el libro con el MISMO
    `sheet_id_para` que usa el lector. Con el otro se escribiría en el libro del
    cliente y se leería del maestro — el fallo real de v404 con el catálogo de rieles,
    que hacía que un riel nuevo no se encontrara nunca."""
    if not is_configured():
        return None, t("The library is not connected: credentials are missing from Secrets.")
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS)), None
    except Exception as e:
        return None, "%s %s: %s" % (t("Could not open sheet"), SHEET, e)


def _ws_modelos():
    if not is_configured():
        return None, t("The library is not connected: credentials are missing from Secrets.")
    try:
        return timeclock.get_sheet(MODELOS_SHEET, tuple(MODELOS_HEADERS)), None
    except Exception as e:
        return None, "%s %s: %s" % (t("Could not open sheet"), MODELOS_SHEET, e)


def _invalidate():
    """⚠️ Tira su caché Y la del LOTE de v339: `_records` lee por `hojas.registros`,
    así que limpiar solo la de aquí dejaría saliendo el valor viejo hasta 120 s — el
    «lo guardé y no sale» que v344 encontró vivo durante cuatro versiones."""
    hojas.invalidar()
    for fn in (_records, _modelos_records):
        try:
            fn.clear()
        except Exception:
            logger.warning("library: no se pudo limpiar la cache de %s", fn)


@st.cache_data(ttl=120, show_spinner=False)
def _records():
    return hojas.registros(SHEET, HEADERS) or []


@st.cache_data(ttl=120, show_spinner=False)
def _modelos_records():
    return hojas.registros(MODELOS_SHEET, MODELOS_HEADERS) or []


# ── catálogo de marcas y modelos (lo mantiene el propietario) ────────────────
def list_modelos(incluir_inactivos: bool = False) -> list:
    """⚠️ El default OCULTA los desactivados, así que la pantalla tiene que ofrecer
    verlos Y una vuelta — si no, desactivar un modelo lo haría inalcanzable (v340)."""
    out = []
    for r in _modelos_records():
        if not incluir_inactivos and str(r.get("Active", "")).strip().upper() == "NO":
            continue
        if not str(r.get("Model", "")).strip() and not str(r.get("Brand", "")).strip():
            continue
        out.append(r)
    return sorted(out, key=lambda r: (str(r.get("Brand", "")).lower(),
                                      str(r.get("Model", "")).lower()))


def marcas(incluir_inactivos: bool = False) -> list:
    vistas = []
    for r in list_modelos(incluir_inactivos):
        b = str(r.get("Brand", "")).strip()
        if b and b not in vistas:
            vistas.append(b)
    return sorted(vistas, key=str.lower)


def modelos_de(marca, incluir_inactivos: bool = False) -> list:
    m = str(marca or "").strip().lower()
    out = []
    for r in list_modelos(incluir_inactivos):
        if str(r.get("Brand", "")).strip().lower() != m:
            continue
        mod = str(r.get("Model", "")).strip()
        if mod and mod not in out:
            out.append(mod)
    return sorted(out, key=str.lower)


def add_modelo(marca, modelo) -> tuple:
    marca, modelo = str(marca or "").strip(), str(modelo or "").strip()
    if not marca:
        return False, t("The brand is required.")
    ws, err = _ws_modelos()
    if err:
        return False, err
    # ⚠️ FRESCO, no de la caché: decidir si ya existe con un dato de hasta 120 s
    # duplicaría el modelo (regla v323).
    try:
        actuales = columnas.canonizar(
            ws.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        return False, "%s: %s" % (t("Could not read the catalogue"), e)
    for r in actuales:
        if str(r.get("Brand", "")).strip().lower() == marca.lower() \
           and str(r.get("Model", "")).strip().lower() == modelo.lower():
            return False, t("That brand and model are already in the catalogue.")
    try:
        ws.append_row([marca, modelo, "SI"], value_input_option="RAW")
    except Exception as e:
        return False, "%s: %s" % (t("Could not save"), e)
    _invalidate()
    return True, t("Added to the catalogue.")


def set_modelo_activo(marca, modelo, activo: bool) -> tuple:
    ws, err = _ws_modelos()
    if err:
        return False, err
    try:
        vals = ws.get_all_values()
    except Exception as e:
        return False, "%s: %s" % (t("Could not read the catalogue"), e)
    cab = vals[0] if vals else list(MODELOS_HEADERS)
    i_b = cab.index("Brand") if "Brand" in cab else 0
    i_m = cab.index("Model") if "Model" in cab else 1
    i_a = cab.index("Active") if "Active" in cab else 2
    marca, modelo = str(marca or "").strip().lower(), str(modelo or "").strip().lower()
    for n, r in enumerate(vals[1:], start=2):
        b = (r[i_b] if len(r) > i_b else "").strip().lower()
        m = (r[i_m] if len(r) > i_m else "").strip().lower()
        if b == marca and m == modelo:
            try:
                ws.update_cell(n, i_a + 1, "SI" if activo else "NO")
            except Exception as e:
                return False, "%s: %s" % (t("Could not save"), e)
            _invalidate()
            return True, (t("Model reactivated.") if activo else t("Model deactivated."))
    return False, t("That model is not in the catalogue.")


# ── la biblioteca ────────────────────────────────────────────────────────────
def _next_id() -> str:
    """El siguiente ID libre.

    ⚠️ Lee FRESCO, nunca de la caché: decidir qué ID se emite con un dato de hasta
    120 s puede devolver uno YA usado, y el ID es la identidad (v323).
    ⚠️ Y salta los que alguien referencie en otra hoja (v427): borrar la última fila
    liberaría su número y el alta siguiente heredaría lo que colgara de él.
    ⚠️ La firma es `(prefijo, maximo, propia=…)`. Pasarla en otro orden lanza
    `ValueError`, que el `except` se traga — y entonces el salto NO se aplica nunca y
    todo cae al `max+1` de siempre, en silencio. Le pasaba a `correcciones` desde v461.
    """
    ws, err = _ws()
    if err:
        return "LIB-0001"
    mx = 0
    try:
        for r in columnas.canonizar(
                ws.get_all_records(numericise_ignore=["all"])):
            u = str(r.get("ID", ""))
            if u.startswith("LIB-"):
                try:
                    mx = max(mx, int(u.split("-")[1]))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("library: no se pudo leer para el ID (%s); se emite el 1", e)
        return "LIB-0001"
    try:
        return hojas.siguiente_id_libre("LIB-", mx, propia=SHEET)
    except Exception as e:
        # ⚠️ Un fallo de lectura NO puede impedir dar de alta: se cae al comportamiento
        # de siempre, que es peor pero funciona.
        logger.warning("library: sin comprobar IDs referenciados (%s)", e)
        return "LIB-%04d" % (mx + 1)


def add_item(titulo, seccion, tipo, marca="", modelo="", notas="",
             drive_id="", filename="", mime="", creado_por="") -> tuple:
    titulo = str(titulo or "").strip()
    if not titulo:
        return False, t("The title is required.")
    if str(seccion) not in SECCIONES:
        return False, "%s %s" % (t("Invalid section:"), seccion)
    if str(tipo) not in TIPOS:
        return False, "%s %s" % (t("Invalid type:"), tipo)
    ws, err = _ws()
    if err:
        return False, err
    lid = _next_id()
    # ⚠️ La fila es POSICIONAL: si no casa con HEADERS, cada dato cae en la columna de
    # al lado. Olvidar un valor al añadir una columna dejó `create_project` muerto tres
    # versiones (v363), así que se comprueba antes de escribir.
    fila = [lid, str(marca or "").strip(), str(modelo or "").strip(), str(seccion),
            str(tipo), titulo, str(notas or "").strip(), str(drive_id or ""),
            str(filename or ""), str(mime or ""), str(creado_por or ""),
            timeclock._now()]
    if len(fila) != len(HEADERS):
        return False, "%s (%d != %d)" % (t("Internal error: row does not match header"),
                                         len(fila), len(HEADERS))
    try:
        ws.append_row(fila, value_input_option="RAW")
    except Exception as e:
        return False, "%s: %s" % (t("Could not save"), e)
    _invalidate()
    return True, lid


def delete_item(lid) -> tuple:
    """Borra la fila. ⚠️ El archivo de Drive lo borra el llamador ANTES de perder su
    DriveID: al revés queda un huérfano que ya nadie puede alcanzar (v456)."""
    ws, err = _ws()
    if err:
        return False, err
    try:
        vals = ws.get_all_values()
    except Exception as e:
        return False, "%s: %s" % (t("Could not read the library"), e)
    cab = vals[0] if vals else list(HEADERS)
    i = cab.index("ID") if "ID" in cab else 0
    for n, r in enumerate(vals[1:], start=2):
        if (r[i] if len(r) > i else "").strip() == str(lid).strip():
            try:
                ws.delete_rows(n)
            except Exception as e:
                return False, "%s: %s" % (t("Could not delete"), e)
            _invalidate()
            return True, t("Removed from the library.")
    return False, t("That item is not in the library.")


def get_item(lid) -> dict:
    for r in _records():
        if str(r.get("ID", "")).strip() == str(lid).strip():
            return r
    return {}


def list_items(marca="", modelo="", seccion="", tipo="") -> list:
    """El material, filtrado por la taxonomía. Un filtro vacío no filtra."""
    out = []
    for r in _records():
        if not str(r.get("ID", "")).strip():
            continue
        if marca and str(r.get("Brand", "")).strip().lower() != str(marca).strip().lower():
            continue
        if modelo and str(r.get("Model", "")).strip().lower() != str(modelo).strip().lower():
            continue
        if seccion and str(r.get("Section", "")).strip() != str(seccion).strip():
            continue
        if tipo and str(r.get("Type", "")).strip() != str(tipo).strip():
            continue
        out.append(r)
    return sorted(out, key=lambda r: str(r.get("Date", "")), reverse=True)


def _norm(s) -> str:
    """Sin acentos ni mayúsculas: «grua» tiene que encontrar «grúa» (v330)."""
    s = str(s or "").lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ñ", "n"), ("ü", "u")):
        s = s.replace(a, b)
    return s


def buscar(q, marca="", modelo="", seccion="", tipo="") -> list:
    """Busca en título, notas, marca, modelo, sección y nombre de archivo.

    ⚠️ NO es un motor nuevo: `manuals.search` sigue siendo el que busca DENTRO del PDF
    (BM25) y alimenta al asistente. Esto solo filtra la ficha. Dos verbos distintos con
    el mismo nombre serían la tercera definición de «buscar» del repo (v323).
    """
    base = list_items(marca, modelo, seccion, tipo)
    qn = _norm(q).strip()
    if len(qn) < 2:                       # con una letra todo coincide y no informa
        return base
    out = []
    for r in base:
        heno = _norm(" ".join(str(r.get(c, "")) for c in
                             ("Title", "Notes", "Brand", "Model", "Section", "FileName")))
        if qn in heno:
            out.append(r)
    return out


def resumen() -> dict:
    """Cuántas piezas hay y cómo se reparten (para los KPI de la pantalla)."""
    items = list_items()
    por_tipo, por_seccion = {}, {}
    for r in items:
        por_tipo[str(r.get("Type", ""))] = por_tipo.get(str(r.get("Type", "")), 0) + 1
        s = str(r.get("Section", ""))
        por_seccion[s] = por_seccion.get(s, 0) + 1
    return {"total": len(items), "por_tipo": por_tipo, "por_seccion": por_seccion,
            "marcas": len(marcas()), "modelos": len(list_modelos())}
