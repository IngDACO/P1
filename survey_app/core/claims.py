# -*- coding: utf-8 -*-
"""Cobro de obra: variaciones y reclamaciones de avance (v507).

Cierra la brecha 2 del estudio de mercado del 20/09/2026. Hasta aquí se podía facturar,
pero no **reclamar**: sin variaciones, sin *progress claims* y sin retenciones, la
reclamación mensual se seguía armando en Excel — que es justo donde el contratista pelea
su dinero.

## Las dos hojas, y por qué van juntas en un módulo

`Variations` y `Claims` contestan UNA pregunta entre las dos: «¿cuánto puedo reclamar
este mes?». Una variación existe para entrar en una reclamación; separarlas en dos
módulos obligaría a que cada uno supiera del otro para responder nada.

## ⚠️ El valor de contrato sale de la cotización ACEPTADA

Decisión del usuario. Ya está enlazada a la obra (`aceptar_y_crear_proyecto`) y es el
precio que el cliente firmó: una sola fuente de verdad, sin un dato nuevo que mantener y
que pueda contradecirla. Una obra sin cotización aceptada no puede emitir reclamaciones,
y se dice.

⚠️ Se usa el **Subtotal** (sin impuesto), no el Total. Es la misma base que usan
`finance.project_revenue` e `invoices.facturado_por_proyecto`, que suman importes de
línea. Mezclar las dos bases haría que los totales comparasen peras con manzanas — el
error que v370 dejó anotado.

## ⚠️ Una reclamación CONGELA sus números

`ContractValue`, `VariationsValue`, `PctComplete` y `RetentionPct` se guardan **en el
momento de reclamar**. No son referencias: si mañana se aprueba otra variación o el
avance sube, la reclamación que ya mandaste sigue diciendo lo mismo. Un documento cuenta
lo que se pactó, no lo que hay hoy — el mismo principio de las líneas de cotización
(v353), de la nómina y de la línea base (v501).

## La aritmética, que es la de siempre en obra

    valor          = contrato + variaciones APROBADAS
    trabajo_hecho  = valor × avance%                    (acumulado, desde el principio)
    bruto          = trabajo_hecho − lo reclamado antes  (lo nuevo de este periodo)
    retención      = bruto × retención%
    neto           = bruto − retención

⚠️ Lo acumulado se lleva en `WorkDone`, no sumando los netos: la retención se descuenta
del pago, no del trabajo hecho. Sumar netos haría que el trabajo pareciera menor cada mes
y la obra nunca llegara al 100%.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter
from core.num import num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

VARIACIONES = "Variations"
V_HEADERS = ["ID", "Group", "ProjectID", "Number", "Date", "Description", "Amount",
             "Status", "DecidedBy", "DecidedDate", "Note", "CreatedBy", "Created"]

RECLAMACIONES = "Claims"
C_HEADERS = ["ID", "Group", "ProjectID", "Number", "Date", "PeriodTo", "PctComplete",
             "ContractValue", "VariationsValue", "WorkDone", "PreviouslyClaimed",
             "RetentionPct", "Retention", "ThisClaim", "Status", "Note",
             "CreatedBy", "Created",
             # v510: qué CLASE de documento es esta fila. ⚠️ AL FINAL (v363) y opcional:
             # vacío = reclamación de avance, que es lo que son todas las anteriores.
             "Type"]

# Clase de documento. Las dos piden dinero y por eso viven en la MISMA hoja: separarlas
# obligaría a numerarlas en dos series y el cliente recibiría dos «nº 3» distintos.
PROGRESO, LIBERACION = "", "retention_release"

# Variación: propuesta → aprobada | rechazada. Solo la APROBADA es dinero.
PROPUESTA, APROBADA, RECHAZADA = "proposed", "approved", "rejected"
V_ESTADOS = (PROPUESTA, APROBADA, RECHAZADA)

# Reclamación: emitida → pagada. Una anulada no cuenta para lo reclamado.
EMITIDA, PAGADA, ANULADA = "issued", "paid", "cancelled"
C_ESTADOS = (EMITIDA, PAGADA, ANULADA)

_VCOL = {h: i + 1 for i, h in enumerate(V_HEADERS)}
_CCOL = {h: i + 1 for i, h in enumerate(C_HEADERS)}

RETENCION_DEFECTO = 5.0          # el 5% habitual en obra AU; se edita por grupo


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws(hoja, headers):
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(hoja, tuple(headers))
    except Exception as e:
        logger.warning("claims: no se pudo abrir %s: %s", hoja, e)
        return None


def _motivo_sin_hoja() -> str:
    """Delega en `timeclock.motivo_sin_hoja` — UNA definición (v361, v510)."""
    return timeclock.motivo_sin_hoja()


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str, hoja: str) -> list:
    """⚠️ SIN cabeceras: `registros(t, cabeceras)` cae a `get_sheet`, que CREA la hoja
    (regla v145). La crea la primera ESCRITURA, no una lectura."""
    from core import hojas
    return hojas.registros(hoja) or []


def _records(hoja):
    return _records_cached(_libro_de(hoja), hoja)


def _invalidate():
    from core import hojas
    for h in (VARIACIONES, RECLAMACIONES):
        hojas.invalidar(h)
    try:
        _records_cached.clear()
    except Exception:
        pass


# ═════════════════════════════════════════════════════════════════
# Lecturas
# ═════════════════════════════════════════════════════════════════
def variaciones(pid, estado=None) -> list:
    out = [r for r in _records(VARIACIONES)
           if str(r.get("ProjectID", "")) == str(pid)]
    if estado:
        out = [r for r in out if str(r.get("Status", "")) == estado]
    return sorted(out, key=lambda r: _num(r.get("Number")))


def reclamaciones(pid, incluir_anuladas=False) -> list:
    out = [r for r in _records(RECLAMACIONES)
           if str(r.get("ProjectID", "")) == str(pid)]
    if not incluir_anuladas:
        out = [r for r in out if str(r.get("Status", "")) != ANULADA]
    return sorted(out, key=lambda r: _num(r.get("Number")))


def es_liberacion(r) -> bool:
    """¿Esta fila es una liberación de retención y no una reclamación de avance?"""
    return str((r or {}).get("Type", "")) == LIBERACION


def retenido(pid) -> dict:
    """Cuánto se ha retenido, cuánto se ha devuelto y cuánto sigue en manos del cliente.

    ⚠️ Es el ÚNICO sitio donde se decide qué queda retenido. La pantalla, el PDF y la
    comprobación de si se puede liberar preguntan aquí, porque dos fórmulas para el
    mismo número es como se acaba mostrando un saldo y cobrando otro (regla v361).

    ⚠️ Una liberación **no retiene nada**: su `Retention` es 0 y lo que devuelve va en
    `ThisClaim`. Así `neto = ThisClaim − Retention` sigue valiendo para las dos clases
    de documento, sin un solo `if` en la pantalla.
    """
    _rs = reclamaciones(pid)
    _ret = round(sum(_num(r.get("Retention")) for r in _rs if not es_liberacion(r)), 2)
    _lib = round(sum(_num(r.get("ThisClaim")) for r in _rs if es_liberacion(r)), 2)
    # ⚠️ Nunca negativo: si por lo que sea se liberó de más, el pendiente es CERO y no
    # una deuda al revés. Un número negativo aquí se presentaría como «te deben» en la
    # pantalla, que es exactamente lo contrario de lo que pasa.
    return {"retenido": _ret, "liberado": _lib,
            "pendiente": round(max(0.0, _ret - _lib), 2)}


def valor_variaciones(pid) -> float:
    """⚠️ Solo las APROBADAS. Una variación propuesta no es dinero: meterla en el valor
    de contrato sería reclamar trabajo que el cliente todavía no ha aceptado."""
    return round(sum(_num(v.get("Amount")) for v in variaciones(pid, APROBADA)), 2)


def retencion_pct(grupo) -> float:
    """El % de retención del grupo, o el habitual en obra si nadie lo ha tocado."""
    try:
        from core import contable
        v = (contable.mapa(grupo) or {}).get("retencion_pct")
        return _num(v) if v not in (None, "") else RETENCION_DEFECTO
    except Exception:
        return RETENCION_DEFECTO


def contrato(pid) -> tuple:
    """`(valor, id de la cotización)` — el Subtotal de la cotización ACEPTADA.

    ⚠️ Sin cotización aceptada no hay contrato, y por tanto no hay nada que reclamar:
    se devuelve 0 y quien pregunte lo dice, en vez de inventar un valor.
    """
    try:
        from core import quotes as Q
        c = Q.cotizacion_de_proyecto(pid) or {}
        return (round(_num(c.get("Subtotal")), 2), str(c.get("ID", ""))) if c else (0.0, "")
    except Exception as e:
        logger.warning("claims.contrato(%s): %s", pid, e)
        return (0.0, "")


# ═════════════════════════════════════════════════════════════════
# El cálculo: qué se puede reclamar ahora
# ═════════════════════════════════════════════════════════════════
def calcular(pid, grupo, pct=None, prj=None) -> dict:
    """Lo que se puede reclamar HOY, sin escribir nada.

    `pct` = avance a reclamar; si no se da, el avance real de la obra. Se devuelve todo
    lo que va a congelarse, para que la pantalla enseñe exactamente lo que se guardará.
    """
    _c, _cid = contrato(pid)
    _var = valor_variaciones(pid)
    _valor = round(_c + _var, 2)

    if pct is None:
        try:
            from core import projects as P
            pct = _num((prj or P.get_project(pid) or {}).get("Progress"))
        except Exception:
            pct = 0.0
    pct = max(0.0, min(100.0, _num(pct)))

    _hecho = round(_valor * pct / 100.0, 2)
    _antes = round(max([_num(r.get("WorkDone")) for r in reclamaciones(pid)], default=0.0), 2)
    # ⚠️ El bruto no puede ser negativo: si el avance BAJA (una actividad se reabre), la
    # reclamación de este periodo es 0, no una devolución. Devolver dinero ya cobrado es
    # una nota de crédito, otro documento con otras consecuencias — no se hace en silencio.
    _bruto = round(max(0.0, _hecho - _antes), 2)
    _ret_pct = retencion_pct(grupo)
    _ret = round(_bruto * _ret_pct / 100.0, 2)
    _r = retenido(pid)
    return {
        "contrato": _c, "cotizacion": _cid, "variaciones": _var, "valor": _valor,
        "pct": round(pct, 2), "hecho": _hecho, "antes": _antes, "bruto": _bruto,
        "retencion_pct": _ret_pct, "retencion": _ret, "neto": round(_bruto - _ret, 2),
        "hay_contrato": bool(_cid),
        # v510: «retenido» es lo que se retuvo en total y NO cambia de significado —
        # el resto del módulo lo venía usando así. Lo que hacía falta era distinguirlo
        # de lo que SIGUE retenido, que es lo que se puede pedir de vuelta.
        "retenido_acumulado": _r["retenido"],
        "retenido_liberado": _r["liberado"],
        "retenido_pendiente": _r["pendiente"],
    }


# ═════════════════════════════════════════════════════════════════
# Escrituras
# ═════════════════════════════════════════════════════════════════
def _siguiente(hoja, headers, pid) -> int:
    """El siguiente número DENTRO de la obra, leyendo FRESCO (nunca de la caché: un
    número sacado de datos de hasta 120 s duplica documentos, v323)."""
    w = _ws(hoja, headers)
    if w is None:
        return 1
    try:
        from core import columnas, valores
        recs = valores.canonizar(columnas.canonizar(
            w.get_all_records(numericise_ignore=["all"])), hoja)
    except Exception:
        return 1
    _n = [int(_num(r.get("Number"))) for r in recs
          if str(r.get("ProjectID", "")) == str(pid)]
    return (max(_n) + 1) if _n else 1


def crear_variacion(pid, grupo, descripcion, importe, nota="", creado_por="") -> tuple:
    w = _ws(VARIACIONES, V_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    if not str(descripcion).strip():
        return False, t("Describe the variation.")
    # ⚠️ Un importe de 0 se admite (una variación puede no cambiar el precio y sí el
    # alcance), pero uno NEGATIVO también: es una reducción de alcance, y en obra existe.
    n = _siguiente(VARIACIONES, V_HEADERS, pid)
    try:
        w.append_row([f"VAR-{pid}-{n:03d}", str(grupo), str(pid), str(n),
                      clock.now(grupo).strftime("%Y-%m-%d"), str(descripcion).strip(),
                      str(_num(importe)), PROPUESTA, "", "", str(nota), str(creado_por),
                      clock.now(grupo).strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving the variation')}: {e}"
    _invalidate()
    return True, "%s %d %s" % (t("Variation"), n, t("recorded."))


def decidir_variacion(vid, aprobada: bool, quien="", grupo=None) -> tuple:
    """Aprueba o rechaza. ⚠️ Solo desde PROPUESTA: cambiar una ya decidida movería el
    valor de contrato por debajo de reclamaciones que ya se emitieron con él."""
    w = _ws(VARIACIONES, V_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    fila, r = _fila(w, VARIACIONES, vid)
    if fila is None:
        return False, t("Variation not found.")
    if str(r.get("Status", "")) != PROPUESTA:
        return False, t("That variation was already decided.")
    ok, err = _set(w, _VCOL, fila, {
        "Status": APROBADA if aprobada else RECHAZADA,
        "DecidedBy": str(quien),
        "DecidedDate": clock.now(grupo or r.get("Group")).strftime("%Y-%m-%d")})
    if not ok:
        return False, err
    _invalidate()
    return True, t("Variation approved.") if aprobada else t("Variation rejected.")


def crear_reclamacion(pid, grupo, pct=None, periodo_hasta="", nota="",
                      creado_por="", prj=None) -> tuple:
    """Emite la reclamación CONGELANDO los números de hoy."""
    w = _ws(RECLAMACIONES, C_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    d = calcular(pid, grupo, pct, prj)
    if not d["hay_contrato"]:
        return False, t("This job has no accepted quote, so there is no contract value "
                        "to claim against.")
    if d["bruto"] <= 0:
        return False, t("There is nothing new to claim: the work done has already been "
                        "claimed in full.")
    n = _siguiente(RECLAMACIONES, C_HEADERS, pid)
    try:
        w.append_row([f"CLM-{pid}-{n:03d}", str(grupo), str(pid), str(n),
                      clock.now(grupo).strftime("%Y-%m-%d"), str(periodo_hasta or ""),
                      str(d["pct"]), str(d["contrato"]), str(d["variaciones"]),
                      str(d["hecho"]), str(d["antes"]), str(d["retencion_pct"]),
                      str(d["retencion"]), str(d["bruto"]), EMITIDA, str(nota),
                      str(creado_por), clock.now(grupo).strftime("%Y-%m-%d %H:%M"),
                      PROGRESO],                  # v510: clase de documento
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving the claim')}: {e}"
    _invalidate()
    return True, "%s %d: %s %.2f" % (t("Claim"), n, t("net payable"), d["neto"])


def puede_liberar(pid, prj=None) -> tuple:
    """`(se_puede, motivo)` — por qué SÍ o por qué NO se puede pedir la retención.

    ⚠️ Devuelve el motivo siempre, también cuando se puede: la pantalla enseña el botón
    deshabilitado **con la razón al lado** en vez de esconderlo. Un botón que no está no
    se distingue de una función que no existe, y el usuario acaba preguntando por algo
    que sí tiene (la misma decisión que en v505 con las órdenes que no bloquean).
    """
    _p = retenido(pid)["pendiente"]
    if _p <= 0:
        return False, t("There is no retention left to release on this job.")
    # ⚠️ El 100% se mira sobre el avance REAL, no sobre el estado: el estado admite
    # override manual (pausada, archivada) y una obra archivada al 90% no está acabada.
    try:
        from core import projects as P
        _av = _num((prj or P.get_project(pid) or {}).get("Progress"))
    except Exception as e:
        # No poder leer el avance no es «está terminada»: ante la duda, NO se libera.
        logger.warning("claims.puede_liberar(%s): %s", pid, e)
        return False, t("The job progress could not be read, so the release is on hold.")
    if _av < 100:
        return False, t("Retention is released once the job is complete; this one is "
                        "at {pct}%.", pct=round(_av, 1))
    return True, t("{amount} of retention is still held.", amount="%.2f" % _p)


def crear_liberacion(pid, grupo, importe=None, nota="", creado_por="", prj=None) -> tuple:
    """Pide de vuelta la retención: un documento más, en la misma serie que las demás.

    `importe` vacío = todo lo pendiente. ⚠️ Se admite PARCIAL a propósito: en obra
    australiana la retención se suele devolver en dos mitades —una en *practical
    completion* y otra al acabar el periodo de defectos, meses después—, así que un
    «todo o nada» no serviría para el caso normal.
    """
    w = _ws(RECLAMACIONES, C_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    _ok, _motivo = puede_liberar(pid, prj)
    if not _ok:
        return False, _motivo
    _pend = retenido(pid)["pendiente"]
    _imp = _pend if importe in (None, "") else round(_num(importe), 2)
    if _imp <= 0:
        return False, t("The amount to release must be greater than 0.")
    # ⚠️ Nunca más de lo retenido: pedir de vuelta dinero que nunca se retuvo no es una
    # liberación, es una factura — otro documento, con otro impuesto y otras consecuencias.
    if _imp > _pend:
        return False, t("You cannot release {amount} when only {held} is being held.",
                        amount="%.2f" % _imp, held="%.2f" % _pend)
    # El último documento manda sus cifras de obra: una liberación NO añade trabajo
    # ejecutado, así que repite las de la última reclamación en vez de inventar un 0
    # que luego se leería como si la obra hubiese retrocedido.
    _ult = [r for r in reclamaciones(pid) if not es_liberacion(r)]
    _prev = _ult[-1] if _ult else {}
    n = _siguiente(RECLAMACIONES, C_HEADERS, pid)
    try:
        w.append_row([f"CLM-{pid}-{n:03d}", str(grupo), str(pid), str(n),
                      clock.now(grupo).strftime("%Y-%m-%d"), "",
                      str(_num(_prev.get("PctComplete")) or 100.0),
                      str(_num(_prev.get("ContractValue"))),
                      str(_num(_prev.get("VariationsValue"))),
                      str(_num(_prev.get("WorkDone"))),
                      str(_num(_prev.get("WorkDone"))),
                      "0", "0",                   # una liberación no retiene nada
                      str(_imp), EMITIDA, str(nota),
                      str(creado_por), clock.now(grupo).strftime("%Y-%m-%d %H:%M"),
                      LIBERACION],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving the release')}: {e}"
    _invalidate()
    return True, "%s %d: %s %.2f" % (t("Retention release"), n, t("net payable"), _imp)


def _fila(w, hoja, oid):
    """(nº de fila 1-based, registro) leyendo FRESCO: decidir DÓNDE escribir con una
    caché es como se corrompen los datos (v323)."""
    try:
        from core import columnas, valores
        recs = valores.canonizar(columnas.canonizar(
            w.get_all_records(numericise_ignore=["all"])), hoja)
    except Exception as e:
        logger.warning("claims._fila: %s", e)
        return None, None
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(oid):
            return i + 2, r
    return None, None


def _set(w, col, fila, campos: dict) -> tuple:
    """Varias columnas de una fila en UNA sola llamada (patrón v80)."""
    lote = [{"range": f"{_col_letter(col[k])}{fila}", "values": [[str(v)]]}
            for k, v in campos.items() if k in col]
    if not lote:
        return True, ""
    try:
        w.batch_update(lote, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error updating')}: {e}"
    return True, ""


def marcar_pagada(cid) -> tuple:
    w = _ws(RECLAMACIONES, C_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    fila, r = _fila(w, RECLAMACIONES, cid)
    if fila is None:
        return False, t("Claim not found.")
    ok, err = _set(w, _CCOL, fila, {"Status": PAGADA})
    if not ok:
        return False, err
    _invalidate()
    return True, t("Claim marked as paid.")


def anular(cid) -> tuple:
    """⚠️ Anular la ÚLTIMA es lo único seguro: las siguientes se emitieron restando el
    `WorkDone` de ésta, así que anular una del medio dejaría un hueco en lo acumulado."""
    w = _ws(RECLAMACIONES, C_HEADERS)
    if w is None:
        return False, _motivo_sin_hoja()
    fila, r = _fila(w, RECLAMACIONES, cid)
    if fila is None:
        return False, t("Claim not found.")
    _pid = str(r.get("ProjectID", ""))
    _ultima = max([_num(x.get("Number")) for x in reclamaciones(_pid)], default=0)
    if _num(r.get("Number")) != _ultima:
        return False, t("Only the latest claim can be cancelled: the ones after it were "
                        "issued on top of this one.")
    ok, err = _set(w, _CCOL, fila, {"Status": ANULADA})
    if not ok:
        return False, err
    _invalidate()
    return True, t("Claim cancelled.")
