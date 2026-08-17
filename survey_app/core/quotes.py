"""Cotizaciones: del catálogo al precio que ve el cliente (v353, fase 2).

Cierra por delante el ciclo que ya existía —obra → costo → factura— empezando donde
empieza el dinero de verdad. Estructuralmente es hermana de `invoices`: mismas líneas en
JSON, mismos totales con impuesto, mismo PDF. Lo que cambia es que aquí el precio se
CONSTRUYE (costo + margen) en vez de escribirse a mano.

## ⚠️ La línea guarda su propia copia del precio

Cada línea congela `costo_unit`, `margen_pct` y `precio_total` **en el momento de
cotizar**. NO es una referencia al catálogo. Si mañana sube el costo del riel, la
cotización que mandaste la semana pasada sigue diciendo lo mismo — un documento cuenta lo
que se pactó, no lo que hay hoy. Es el mismo principio del historial de inventario
(v306/v350) y de la nómina.

## El margen manda aquí

Decisión del usuario: el margen se pone **línea a línea** (a un cliente le cobras 20% y a
otro 35% por lo mismo) y al aceptar la cotización el margen efectivo se escribe como
`MargenMO` del proyecto. Una sola fuente de verdad, en vez de dos números que digan cosas
distintas del mismo trabajo.

## Estados

`borrador → enviada → aceptada | rechazada`, y **vencida** se DERIVA de la fecha de
validez (no se guarda), igual que `invoices.estado_cobro`: un estado calculado no puede
quedarse desactualizado en la hoja.
"""
import json
import logging
from datetime import timedelta

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter
from core.num import num as _num
from core.num import parse_date as _parse_date

logger = logging.getLogger(__name__)

SHEET = "Cotizaciones"
HEADERS = ["ID", "Grupo", "ClienteID", "ClienteNombre", "Numero", "Fecha", "Validez",
           "LineasJSON", "Subtotal", "ImpuestoPct", "Impuesto", "Total", "MargenPct",
           "Estado", "ProyectoID", "Version", "Origen", "Nota", "CreadoPor", "Creado"]

BORRADOR, ENVIADA, ACEPTADA, RECHAZADA = "borrador", "enviada", "aceptada", "rechazada"
VENCIDA = "vencida"                       # ⚠️ derivado, nunca se guarda
ESTADOS = (BORRADOR, ENVIADA, ACEPTADA, RECHAZADA)
VALIDEZ_DIAS = 30

_COL = {h: i + 1 for i, h in enumerate(HEADERS)}


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("quotes: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records() -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja (regla v145)."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _invalidate():
    from core import hojas                 # v339: tirar también el LOTE compartido
    hojas.invalidar()
    for fn in (_records, resumen):
        try:
            fn.clear()
        except Exception as e:             # v344: deja rastro, no lo tragues
            logger.warning("quotes._invalidate: no se pudo limpiar %s: %s", fn, e)


# ── Construir las líneas ─────────────────────────────────────────
def linea_de(item: dict, cantidad=1, margen_pct=None) -> dict:
    """Una línea de cotización a partir de un artículo del catálogo.

    ⚠️ SNAPSHOT: se copian el costo y el margen, no una referencia. Ver el módulo.
    """
    from core import catalogo as CAT
    cant = _num(cantidad, 0.0)
    costo = CAT.costo_de(item, cant)
    m = _num(margen_pct, 0.0)
    precio = round(costo * (1.0 + m / 100.0), 2)
    return {
        "catalogo_id": str(item.get("ID", "")),
        "tipo": str(item.get("Tipo", "")),
        "concepto": str(item.get("Nombre", "")),
        "descripcion": str(item.get("Descripcion", "")),
        "unidad": str(item.get("Unidad", "")),
        "cantidad": cant,
        # las horas viajan en la línea: son la base del «cotizado vs real» (fase 3)
        "horas": CAT.horas_de(item, cant),
        "costo_unit": _num(item.get("CostoUnit")) if str(item.get("Tipo", "")) != CAT.SERVICIO
                      else round(_num(item.get("HorasEst")) * _num(item.get("TarifaHora")), 2),
        "costo_total": costo,
        "margen_pct": m,
        "precio_total": precio,
    }


def recalcular(linea: dict) -> dict:
    """Reaplica el margen sobre el costo YA CONGELADO (no vuelve al catálogo)."""
    l = dict(linea)
    l["precio_total"] = round(_num(l.get("costo_total")) * (1.0 + _num(l.get("margen_pct")) / 100.0), 2)
    return l


def totales(lineas: list, impuesto_pct=0.0) -> dict:
    """Todo lo que hay que saber de una cotización, en una sola pasada."""
    costo = round(sum(_num(l.get("costo_total")) for l in lineas or []), 2)
    sub = round(sum(_num(l.get("precio_total")) for l in lineas or []), 2)
    imp = round(sub * _num(impuesto_pct) / 100.0, 2)
    horas = round(sum(_num(l.get("horas")) for l in lineas or []), 2)
    return {"costo": costo, "subtotal": sub, "impuesto": imp,
            "total": round(sub + imp, 2), "ganancia": round(sub - costo, 2),
            # margen efectivo = el que se escribirá como MargenMO al aceptar
            "margen_pct": round(100.0 * (sub - costo) / costo, 2) if costo > 0 else 0.0,
            "horas": horas}


def lineas_de(c: dict) -> list:
    try:
        return json.loads(c.get("LineasJSON", "") or "[]")
    except Exception as e:
        logger.warning("quotes: LineasJSON inválido en %s: %s", c.get("ID"), e)
        return []


# ── Lecturas ─────────────────────────────────────────────────────
def estado_de(c: dict) -> str:
    """⚠️ `vencida` se DERIVA de la validez; nunca se guarda (como `estado_cobro`)."""
    est = str(c.get("Estado", "") or BORRADOR).lower()
    if est in (ACEPTADA, RECHAZADA):
        return est
    v = _parse_date(c.get("Validez"))
    if est == ENVIADA and v and v < clock.today():
        return VENCIDA
    return est


def list_cotizaciones(grupo=None, cliente_id=None, incluir_rechazadas=True) -> list:
    out = list(_records())
    if grupo:
        out = [c for c in out if str(c.get("Grupo", "")) == str(grupo)]
    if cliente_id:
        out = [c for c in out if str(c.get("ClienteID", "")) == str(cliente_id)]
    if not incluir_rechazadas:
        out = [c for c in out if estado_de(c) != RECHAZADA]
    return sorted(out, key=lambda c: str(c.get("Fecha", "")), reverse=True)


def get_cotizacion(cid) -> dict:
    return next((c for c in _records() if str(c.get("ID", "")) == str(cid)), {})


@st.cache_data(ttl=120, show_spinner=False)
def resumen(grupo) -> dict:
    """Lo que importa de un cotizador: cuánto hay en la calle y cuánto se gana."""
    cs = [c for c in _records() if str(c.get("Grupo", "")) == str(grupo)]
    por_estado, en_calle, ganado = {}, 0.0, 0.0
    for c in cs:
        e = estado_de(c)
        por_estado[e] = por_estado.get(e, 0) + 1
        if e in (ENVIADA, VENCIDA):
            en_calle += _num(c.get("Total"))
        elif e == ACEPTADA:
            ganado += _num(c.get("Total"))
    decididas = por_estado.get(ACEPTADA, 0) + por_estado.get(RECHAZADA, 0)
    return {"n": len(cs), "por_estado": por_estado,
            "en_calle": round(en_calle, 2), "ganado": round(ganado, 2),
            # ⚠️ None, no 0: sin cotizaciones decididas la tasa NO es "0%", es que
            # todavía no se puede calcular (la trampa de v320 con «sin asignar»).
            "conversion": (round(100.0 * por_estado.get(ACEPTADA, 0) / decididas, 1)
                           if decididas else None)}


# ── Escrituras ───────────────────────────────────────────────────
def _ids_frescos() -> tuple:
    """IDs y números LEÍDOS DE LA HOJA, saltándose la caché: un ID sacado de datos de
    hasta 120 s puede salir REPETIDO, y el ID es la identidad (v323)."""
    w = _ws()
    if w is None:
        return 0, 0
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("quotes._ids_frescos: %s", e)
        return 0, 0
    mx_id = mx_num = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("COT-"):
            try:
                mx_id = max(mx_id, int(i.split("-")[1]))
            except Exception:
                pass
        try:
            mx_num = max(mx_num, int(_num(r.get("Numero"))))
        except Exception:
            pass
    return mx_id, mx_num


def crear(grupo, cliente_id, cliente_nombre, lineas, impuesto_pct=0.0,
          validez=None, nota="", creado_por="", origen="") -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    if not lineas:
        return False, "Añade al menos una línea a la cotización."
    if not str(cliente_nombre or "").strip():
        return False, "Elige a quién va la cotización."
    t = totales(lineas, impuesto_pct)
    mx_id, mx_num = _ids_frescos()
    cid, num = f"COT-{mx_id + 1:04d}", f"{mx_num + 1:04d}"
    hoy = clock.today(grupo)
    val = validez or (hoy + timedelta(days=VALIDEZ_DIAS))
    try:
        w.append_row([cid, str(grupo), str(cliente_id), str(cliente_nombre), num,
                      hoy.isoformat(), str(val), json.dumps(lineas, ensure_ascii=False),
                      str(t["subtotal"]), str(_num(impuesto_pct)), str(t["impuesto"]),
                      str(t["total"]), str(t["margen_pct"]), BORRADOR, "", "1",
                      str(origen), str(nota), str(creado_por),
                      clock.now(grupo).strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"Error guardando la cotización: {e}"
    _invalidate()
    return True, cid


def _fila(w, cid):
    """(nº de fila, registro) leyendo FRESCO (regla v323)."""
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("quotes._fila: %s", e)
        return None, None
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(cid):
            return i + 2, r
    return None, None


def _set(w, row, campos: dict) -> tuple:
    lote = [{"range": f"{_col_letter(_COL[k])}{row}", "values": [[str(v)]]}
            for k, v in campos.items() if k in _COL]
    if not lote:
        return True, ""
    try:
        w.batch_update(lote, value_input_option="RAW")
    except Exception as e:
        return False, f"Error actualizando: {e}"
    return True, ""


def guardar_lineas(cid, lineas, impuesto_pct=None) -> tuple:
    """Reemplaza las líneas y recalcula los totales. Solo en BORRADOR."""
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    row, c = _fila(w, cid)
    if row is None:
        return False, "Cotización no encontrada."
    if estado_de(c) != BORRADOR:
        # ⚠️ Una cotización ya enviada es un documento que el cliente tiene en la mano:
        # cambiarla por debajo es como reescribir una factura emitida. Se saca una
        # versión nueva (`nueva_version`), que además deja rastro de lo que cambió.
        return False, ("Esta cotización ya no es un borrador. Crea una versión nueva "
                       "para cambiarla.")
    imp = _num(c.get("ImpuestoPct")) if impuesto_pct is None else _num(impuesto_pct)
    t = totales(lineas, imp)
    ok, err = _set(w, row, {
        "LineasJSON": json.dumps(lineas, ensure_ascii=False),
        "Subtotal": t["subtotal"], "ImpuestoPct": imp, "Impuesto": t["impuesto"],
        "Total": t["total"], "MargenPct": t["margen_pct"]})
    if not ok:
        return False, err
    _invalidate()
    return True, "Cotización actualizada."


def set_estado(cid, estado) -> tuple:
    if estado not in ESTADOS:
        return False, f"Estado no válido: {estado}."
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    row, c = _fila(w, cid)
    if row is None:
        return False, "Cotización no encontrada."
    antes = estado_de(c)
    if antes == ACEPTADA and estado != ACEPTADA and str(c.get("ProyectoID", "")).strip():
        return False, ("Esta cotización ya generó el proyecto "
                       f"{c.get('ProyectoID')}: no se puede cambiar su estado.")
    ok, err = _set(w, row, {"Estado": estado})
    if not ok:
        return False, err
    _invalidate()
    # ⚠️ FUERA del try del guardado y DESPUÉS de invalidar (v342/v344).
    try:
        from core import auditoria
        auditoria.registrar("cotizacion", cid, {"Estado": [antes, estado]},
                            grupo=str(c.get("Grupo", "")))
    except Exception:
        pass
    return True, f"Cotización marcada como {estado}."


def nueva_version(cid, creado_por="") -> tuple:
    """Clona la cotización como versión siguiente, en borrador.

    El cliente pide cambios y sale la v2. La anterior **se conserva**: es el documento
    que llegó a mandarse.
    """
    c = get_cotizacion(cid)
    if not c:
        return False, "Cotización no encontrada."
    ok, nuevo = crear(c.get("Grupo"), c.get("ClienteID"), c.get("ClienteNombre"),
                      lineas_de(c), _num(c.get("ImpuestoPct")),
                      nota=str(c.get("Nota", "")), creado_por=creado_por,
                      origen=str(c.get("ID", "")))
    if not ok:
        return False, nuevo
    w = _ws()
    row, _r = _fila(w, nuevo)
    if row is not None:
        _set(w, row, {"Version": int(_num(c.get("Version"), 1)) + 1})
        _invalidate()
    return True, nuevo
