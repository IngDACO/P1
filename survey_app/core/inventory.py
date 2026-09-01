"""📦 Inventario — control de activos de la empresa vía QR (v263).

Cada activo tiene un registro (hoja `Activos`) y un QR que codifica un deep-link
a la app (`?activo=ACT-####`): al escanearlo se abre su ficha. Lleva ciclo de
vida (estado), ubicación/custodia, valor + depreciación (línea recta) y —en fases
siguientes— movimientos (entradas/salidas) y mantenimiento.

Hojas: `Activos` (registro) + `InvCategorias` (catálogo editable por grupo).
Multi-tenant, migran solas (`timeclock.get_sheet`). QR con `segno` (pure-python).
"""
import io
import logging

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter, num as _num, parse_date as _parse_date

from core.i18n import t
logger = logging.getLogger(__name__)

ACTIVOS_SHEET = "Activos"
ACTIVOS_HEADERS = [
    "ID", "Grupo", "Nombre", "Categoria", "Marca", "Modelo", "Serie",
    "FotoDriveID", "FechaCompra", "ValorCompra", "VidaUtilAnios",
    "Estado", "Condicion", "UbicacionTipo", "UbicacionRef", "AsignadoA",
    "FechaDevolucion", "ProximoMant", "Nota", "Activo", "CreadoPor", "Creado",
]
_ACOL = {h: i + 1 for i, h in enumerate(ACTIVOS_HEADERS)}

CAT_SHEET = "InvCategorias"
CAT_HEADERS = ["Grupo", "Nombre"]

MOV_SHEET = "MovimientosActivo"
MOV_HEADERS = ["ID", "Grupo", "ActivoID", "Tipo", "Fecha", "DesdeUbic", "HaciaUbic",
               "Usuario", "Costo", "Nota", "CreadoPor", "Creado"]
MOV_TIPOS = ["salida", "entrada", "traslado", "mantenimiento", "baja"]

ESTADOS = ["disponible", "en_uso", "mantenimiento", "dañado", "baja"]
CONDICIONES = ["bueno", "regular", "malo"]
UBIC_TIPOS = ["bodega", "proyecto", "usuario", "reparacion"]
CAT_DEFAULT = ["Herramienta", "Equipo", "Vehículo", "EPP", "Consumible", "Otro"]

_HEADERS = {ACTIVOS_SHEET: ACTIVOS_HEADERS, CAT_SHEET: CAT_HEADERS, MOV_SHEET: MOV_HEADERS}



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


def app_url() -> str:
    """URL base de la app (secret APP_URL), para el deep-link del QR."""
    try:
        return str(st.secrets.get("APP_URL", "")).rstrip("/")
    except Exception:
        return ""


# ── Worksheet + lecturas cacheadas ───────────────────────────────
def _ws(title):
    if not timeclock._secrets_present():
        return None, t("Google Sheets is not configured.")
    try:
        return timeclock.get_sheet(title, tuple(_HEADERS[title])), None
    except Exception as e:
        logger.warning("inventory: no se pudo abrir %s: %s", title, e)
        return None, f"{t('Could not open sheet')} {title}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str, title):
    """Registros de la hoja (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(title, _HEADERS[title]) or []




def _records(title):
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(title), title)
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception:
        pass


# ── Categorías (catálogo editable) ───────────────────────────────
def categorias(grupo: str) -> list:
    """Categorías del grupo: los defaults + las añadidas (dedup, ordenadas)."""
    extra = [str(r.get("Nombre", "")).strip() for r in _records(CAT_SHEET)
             if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")).strip()]
    return sorted(set(CAT_DEFAULT) | set(extra), key=str.lower)


def add_categoria(grupo: str, nombre: str) -> tuple:
    nombre = str(nombre or "").strip()
    if not nombre:
        return False, t("Empty name.")
    if nombre in categorias(grupo):
        return False, t("That category already exists.")
    w, err = _ws(CAT_SHEET)
    if err:
        return False, err
    w.append_row([grupo, nombre], value_input_option="RAW")
    _invalidate()
    return True, t("Category added.")


def del_categoria(grupo: str, nombre: str) -> tuple:
    w, err = _ws(CAT_SHEET)
    if err:
        return False, err
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("Grupo", "")) == str(grupo) and str(r.get("Nombre", "")).strip() == str(nombre).strip():
            w.delete_rows(i + 2)
            _invalidate()
            return True, t("Category deleted.")
    return False, t("Not found (is it a default one? those cannot be removed).")


# ── Activos ──────────────────────────────────────────────────────
def list_activos(grupo: str = None, incluir_baja: bool = False) -> list:
    out = []
    for r in _records(ACTIVOS_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if not incluir_baja and str(r.get("Activo", "SI")).upper() in ("NO", "FALSE", "0"):
            continue
        out.append(r)
    return out


def get_activo(aid: str) -> dict:
    for r in _records(ACTIVOS_SHEET):
        if str(r.get("ID", "")) == str(aid):
            return r
    return {}


def _ids_frescos(title: str, col: str = "ID") -> list:
    """Los IDs LEÍDOS DE LA HOJA, saltándose la caché (ver `invoices._ids_frescos`).

    ⚠️ v323: `_next_id` leía de `_records()` (cacheado 120 s desde v290) y podía
    devolver un ID **ya usado**. Con el inventario duele el doble: el QR pegado en
    el activo apunta al ID, así que dos activos con el mismo ACT-#### comparten
    etiqueta física y su historial de movimientos se mezcla.
    """
    w, err = _ws(title)
    if err or w is None:
        return []
    try:
        vals = w.get_all_values()
    except Exception as e:
        logger.warning("inventory: lectura fresca de IDs de %s falló: %s", title, e)
        return []
    if not vals:
        return []
    try:
        i = vals[0].index(col)
    except ValueError:
        return []
    return [f[i] for f in vals[1:] if len(f) > i]


def _next_id() -> str:
    mx = 0
    for aid in _ids_frescos(ACTIVOS_SHEET):
        aid = str(aid)
        if aid.startswith("ACT-"):
            try:
                mx = max(mx, int(aid.split("-")[1]))
            except Exception:
                pass
    return f"ACT-{mx + 1:04d}"


def create_activo(grupo, nombre, categoria="", marca="", modelo="", serie="",
                  foto_id="", fecha_compra="", valor_compra="", vida_util="",
                  condicion="bueno", ubicacion_tipo="bodega", ubicacion_ref="",
                  proximo_mant="", nota="", creado_por="") -> tuple:
    """Registra un activo (estado inicial 'disponible'). Devuelve (ok, id|error)."""
    w, err = _ws(ACTIVOS_SHEET)
    if err:
        return False, err
    if not str(nombre or "").strip():
        return False, t("The asset name is required.")
    aid = _next_id()
    row = [aid, grupo, str(nombre).strip(), str(categoria or ""), str(marca or ""),
           str(modelo or ""), str(serie or ""), str(foto_id or ""),
           str(fecha_compra or ""), str(_num(valor_compra)), str(_num(vida_util)),
           "disponible", str(condicion or "bueno"), str(ubicacion_tipo or "bodega"),
           str(ubicacion_ref or ""), "", "", str(proximo_mant or ""),
           str(nota or ""), "SI", str(creado_por or ""),
           clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, aid


def update_activo(aid: str, fields: dict) -> tuple:
    w, err = _ws(ACTIVOS_SHEET)
    if err:
        return False, err
    row = None
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("ID", "")) == str(aid):
            row = i + 2
            break
    if row is None:
        return False, t("Asset not found.")
    batch = [{"range": f"{_col_letter(_ACOL[k])}{row}", "values": [[str(v)]]}
             for k, v in fields.items() if k in _ACOL]
    if batch:
        try:
            w.batch_update(batch, value_input_option="RAW")
        except Exception as e:
            return False, str(e)
    _invalidate()
    return True, t("Asset updated.")


def dar_de_baja(aid: str, grupo: str = "", motivo: str = "", creado_por: str = "") -> tuple:
    a = get_activo(aid)
    ok, msg = update_activo(aid, {"Activo": "NO", "Estado": "baja",
                                  "Nota": (motivo or "Decommissioned")})
    if ok:
        _log_mov(grupo or str(a.get("Grupo", "")), aid, "baja", ubic_str(a), "baja",
                 "", "", motivo, creado_por=creado_por)
    return ok, msg


# ── Valor / depreciación (línea recta) ───────────────────────────
def valor_actual(a: dict) -> float:
    """Valor depreciado (línea recta): compra × (1 − años/vida útil), ≥ 0."""
    vc = _num(a.get("ValorCompra"))
    vida = _num(a.get("VidaUtilAnios"))
    fc = _parse_date(a.get("FechaCompra"))
    if vc <= 0 or vida <= 0 or not fc:
        return round(vc, 2)
    anios = (clock.today() - fc).days / 365.25
    return round(max(0.0, vc * (1 - anios / vida)), 2)


def resumen(grupo: str) -> dict:
    acts = list_activos(grupo)
    hoy = clock.today()
    por_estado = {}
    v_compra = v_actual = 0.0
    mant_venc = 0
    for a in acts:
        por_estado[a.get("Estado", "")] = por_estado.get(a.get("Estado", ""), 0) + 1
        v_compra += _num(a.get("ValorCompra"))
        v_actual += valor_actual(a)
        pm = _parse_date(a.get("ProximoMant"))
        if pm and pm < hoy:
            mant_venc += 1
    return {"n": len(acts), "por_estado": por_estado,
            "valor_compra": round(v_compra, 2), "valor_actual": round(v_actual, 2),
            "mant_vencido": mant_venc}


def alertas(grupo: str) -> list:
    """Alertas del inventario para la campana: mantenimiento vencido y activos no
    devueltos (salida con FechaDevolucion pasada y aún en_uso)."""
    out = []
    hoy = clock.today()
    for a in list_activos(grupo):
        pm = _parse_date(a.get("ProximoMant"))
        if pm and pm < hoy:
            out.append({"tipo": "mantenimiento", "activo": str(a.get("Nombre", "")),
                        "id": str(a.get("ID", "")), "dias": (hoy - pm).days})
        fd = _parse_date(a.get("FechaDevolucion"))
        if fd and fd < hoy and str(a.get("Estado", "")).lower() == "en_uso":
            out.append({"tipo": "no_devuelto", "activo": str(a.get("Nombre", "")),
                        "id": str(a.get("ID", "")), "dias": (hoy - fd).days,
                        "usuario": str(a.get("AsignadoA", ""))})
    return out


def reporte_valor(grupo: str) -> dict:
    """Valor (compra y actual) agrupado por categoría y por ubicación (tipo)."""
    cat, ubi = {}, {}
    for a in list_activos(grupo):
        va = valor_actual(a)
        vc = _num(a.get("ValorCompra"))
        k = str(a.get("Categoria", "")) or "—"
        d = cat.setdefault(k, {"n": 0, "compra": 0.0, "actual": 0.0})
        d["n"] += 1
        d["compra"] += vc
        d["actual"] += va
        u = str(a.get("UbicacionTipo", "")) or "—"
        e = ubi.setdefault(u, {"n": 0, "actual": 0.0})
        e["n"] += 1
        e["actual"] += va
    return {"por_categoria": cat, "por_ubicacion": ubi}


# ── Movimientos (entradas/salidas/traslado/mantenimiento) — Fase 2 ─
def ubic_ref_label(ref: str) -> str:
    """Texto legible de una `UbicacionRef`.

    ⚠️ v306: cuando el destino es un proyecto se guarda su **ID** (`PRJ-####`), no el
    nombre — el nombre puede repetirse y además cambia al renombrar, y entonces el
    histórico del activo quedaría colgando de un texto que ya no existe (el mismo fallo
    que tenían las horas antes de v145). Aquí se resuelve al nombre ACTUAL. Las filas
    anteriores a v306 guardan el nombre: no casan con ningún ID y se muestran tal cual.
    """
    ref = str(ref or "")
    if not ref.startswith("PRJ-"):
        return ref
    try:
        from core import projects as P
        p = P.get_project(ref)
        return f"{p.get('Nombre') or ref}" if p else ref
    except Exception:
        return ref


def ubic_str(a: dict) -> str:
    _tp = str(a.get("UbicacionTipo", "") or "")
    ref = ubic_ref_label(a.get("UbicacionRef", ""))
    return f"{_tp}: {ref}" if ref else (_tp or "—")


def list_movimientos(grupo: str = None, activo_id: str = None) -> list:
    out = []
    for r in _records(MOV_SHEET):
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if activo_id is not None and str(r.get("ActivoID", "")) != str(activo_id):
            continue
        out.append(r)
    return out


def _next_mov_id() -> str:
    mx = 0
    for r in _records(MOV_SHEET):
        mid = str(r.get("ID", ""))
        if mid.startswith("MOV-"):
            try:
                mx = max(mx, int(mid.split("-")[1]))
            except Exception:
                pass
    return f"MOV-{mx + 1:04d}"


def _log_mov(grupo, aid, tipo, desde="", hacia="", usuario="", costo="", nota="",
             fecha="", creado_por="") -> tuple:
    w, err = _ws(MOV_SHEET)
    if err:
        return False, err
    row = [_next_mov_id(), grupo, aid, tipo, str(fecha or clock.today().isoformat()),
           str(desde or ""), str(hacia or ""), str(usuario or ""),
           (str(_num(costo)) if str(costo).strip() != "" else ""), str(nota or ""),
           str(creado_por or ""), clock.now().strftime("%Y-%m-%d %H:%M:%S")]
    w.append_row(row, value_input_option="RAW")
    _invalidate()
    return True, "ok"


def salida(aid, grupo, usuario="", hacia_tipo="usuario", hacia_ref="",
           fecha_devolucion="", nota="", creado_por="") -> tuple:
    """Check-out: el activo sale a un proyecto/usuario. Estado→en_uso."""
    a = get_activo(aid)
    if not a:
        return False, t("Asset not found.")
    desde = ubic_str(a)
    # ⚠️ El ACTIVO guarda el ID (`UbicacionRef`), que es la relación viva y sobrevive a
    # renombrar el proyecto. El MOVIMIENTO es un registro histórico, así que guarda el
    # nombre ya resuelto: debe seguir leyéndose años después aunque el proyecto se
    # archive o cambie de nombre — un log cuenta lo que pasó, no lo que hay ahora.
    hacia = (f"{hacia_tipo}: {ubic_ref_label(hacia_ref)}" if hacia_ref else hacia_tipo)
    ok, msg = update_activo(aid, {"Estado": "en_uso", "UbicacionTipo": hacia_tipo,
                                  "UbicacionRef": hacia_ref, "AsignadoA": usuario,
                                  "FechaDevolucion": fecha_devolucion})
    if not ok:
        return ok, msg
    _log_mov(grupo, aid, "salida", desde, hacia, usuario, "", nota, creado_por=creado_por)
    return True, t("Check-out recorded.")


def entrada(aid, grupo, bodega="", nota="", creado_por="") -> tuple:
    """Check-in: el activo vuelve a bodega. Estado→disponible."""
    a = get_activo(aid)
    if not a:
        return False, t("Asset not found.")
    desde = ubic_str(a)
    ok, msg = update_activo(aid, {"Estado": "disponible", "UbicacionTipo": "bodega",
                                  "UbicacionRef": bodega, "AsignadoA": "", "FechaDevolucion": ""})
    if not ok:
        return ok, msg
    _log_mov(grupo, aid, "entrada", desde, (f"bodega: {bodega}" if bodega else "bodega"),
             a.get("AsignadoA", ""), "", nota, creado_por=creado_por)
    return True, t("Return recorded.")


def traslado(aid, grupo, hacia_tipo, hacia_ref, nota="", creado_por="") -> tuple:
    """Cambia la ubicación (sin cambiar la custodia)."""
    a = get_activo(aid)
    if not a:
        return False, t("Asset not found.")
    desde = ubic_str(a)
    # ⚠️ v350: el historial guarda el nombre YA RESUELTO (regla v306: un histórico
    # cuenta lo que pasó, no lo que hay ahora). `salida` sí lo hacía y aquí se quedó el
    # ID crudo, así que el mismo sitio aparecía como «proyecto: PRJ-0005» al llegar y
    # como «proyecto: prueba2» al salir — dos grafías para el mismo evento.
    hacia = f"{hacia_tipo}: {ubic_ref_label(hacia_ref)}" if hacia_ref else hacia_tipo
    ok, msg = update_activo(aid, {"UbicacionTipo": hacia_tipo, "UbicacionRef": hacia_ref})
    if not ok:
        return ok, msg
    _log_mov(grupo, aid, "traslado", desde, hacia, "", "", nota, creado_por=creado_por)
    return True, t("Transfer recorded.")


def mantenimiento(aid, grupo, costo="", proximo="", nota="", en_mant=False, creado_por="") -> tuple:
    """Registra un mantenimiento (costo + próxima fecha); opcional deja el activo en mantenimiento."""
    a = get_activo(aid)
    if not a:
        return False, t("Asset not found.")
    campos = {}
    if proximo:
        campos["ProximoMant"] = proximo
    if en_mant:
        campos["Estado"] = "mantenimiento"
    if campos:
        ok, msg = update_activo(aid, campos)
        if not ok:
            return ok, msg
    _log_mov(grupo, aid, "mantenimiento", ubic_str(a), ubic_str(a), "", costo, nota, creado_por=creado_por)
    return True, t("Maintenance recorded.")


# ── QR ───────────────────────────────────────────────────────────
def qr_data(aid: str) -> str:
    base = app_url()
    return f"{base}/?activo={aid}" if base else str(aid)


def qr_png(aid: str, scale: int = 6) -> bytes:
    """PNG del QR (deep-link a la app). `segno` es pure-python (sin pillow)."""
    import segno
    buf = io.BytesIO()
    segno.make(qr_data(aid), error="m").save(buf, kind="png", scale=scale, border=2)
    return buf.getvalue()
