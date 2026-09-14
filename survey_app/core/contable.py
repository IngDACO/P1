# -*- coding: utf-8 -*-
"""Exportación contable: el CSV que el contable importa en Xero o en MYOB (v483).

El dolor que quita: hoy cada factura y cada recibo se teclean DOS veces, una en COPEX
y otra en la contabilidad. Es la objeción más fácil de anticipar en la venta.

⚠️ **Los importes que salen son SIEMPRE sin impuesto**, con el impuesto en su propia
columna. Xero pregunta al importar si el archivo viene «tax inclusive» o «exclusive»:
si el exportador cambiara de criterio según el caso, esa pregunta se contestaría mal
tarde o temprano y el GST del cliente saldría mal. Un solo criterio, dicho en pantalla.

⚠️ **El impuesto se REPARTE entre las líneas de forma que sume exactamente el de la
factura.** Redondear línea a línea da diferencias de un centavo contra el total que ya
está emitido y cobrado, y una factura que no cuadra al centavo la rebota el contable.

⚠️ **El mapa de cuentas es por PERFIL, no compartido**: en Xero las ventas son `200` y
en MYOB `4-1000`. Un solo mapa habría exportado a MYOB códigos que no existen en su
archivo — y MYOB rechaza la fila entera, no la avisa.

Lo que este módulo NO hace, dicho aquí para que no se suponga:
  · no habla con Xero ni con MYOB (eso es la fase 2.3, OAuth y tokens);
  · no crea los contactos: los dos casan por NOMBRE y MYOB además exige que la ficha
    ya exista;
  · no inventa el plan de cuentas: trae el de fábrica de cada uno y se edita.
"""
import csv
import datetime as _dt
import io
import json
import logging

from core import auth, clientes, expenses, invoices
from core.num import num as _num, parse_date as _parse_date

from core.i18n import t

logger = logging.getLogger(__name__)

# ⚠️ DERIVADO de la lista real de categorías de gasto, nunca copiado (v433). Si mañana
# se añade una categoría, aparece sola en el editor de cuentas en vez de exportarse con
# la cuenta vacía —que en MYOB es una fila rechazada— sin que nadie se entere.
CATEGORIAS = tuple(expenses.CATEGORIAS)

VENTAS = "_ventas"          # clave del mapa para la cuenta de ingresos

# Plan de cuentas DE FÁBRICA de cada producto. No es una recomendación contable: es el
# punto de partida para que la exportación funcione el primer día, y se edita.
_CUENTAS_DEFECTO = {
    "xero": {VENTAS: "200", "Materials": "300", "Tools": "429", "Transport": "425",
             "Fuel": "449", "Subcontractor": "310", "Rental": "469", "Other": "429"},
    "myob": {VENTAS: "4-1000", "Materials": "5-1000", "Tools": "6-1000",
             "Transport": "6-1000", "Fuel": "6-1000", "Subcontractor": "5-1000",
             "Rental": "6-1000", "Other": "6-1000"},
}

_DEFECTOS = {
    "moneda": "AUD",
    "gastos_incluyen_impuesto": True,   # en AU el recibo viene con el GST dentro
    "categoria_seguimiento": "Project",
    "seguimiento": True,
    "cuentas": _CUENTAS_DEFECTO,
}

# ── Parte de horas (fase 2.2) ───────────────────────────────────────────────
# El nombre del «earnings rate» con el que cada concepto entra en la nómina. Son los
# nombres de fábrica de Xero Payroll AU; se editan, porque cada organización los tiene
# a su manera y el proveedor casa por NOMBRE.
ORDINARIAS = "ordinarias"
_CONCEPTOS_DEFECTO = {
    ORDINARIAS:   "Ordinary Hours",
    "vacaciones": "Annual Leave",
    "enfermedad": "Personal/Carer's Leave",
}
_MAX_DIAS = 62          # tope de columnas: un año daría 365 y no lo lee nadie


def conceptos() -> tuple:
    """Las claves del parte: ordinarias + los tipos de ausencia **PAGADA**.

    ⚠️ Los tipos se DERIVAN de `ausencias.TIPOS`, no se copian (v433/v434): un tipo
    nuevo aparece solo, y uno que deje de pagarse desaparece. Copiarlos dejaría el
    parte pagando lo que la app ya no paga, sin que nada avise.

    ⚠️ Y es una FUNCIÓN, no una constante de módulo: una constante se evaluaría al
    importar y se quedaría congelada (la familia del `t()` congelado, v445).
    """
    try:
        from core import ausencias as _AU
        pag = tuple(k for k, v in _AU.TIPOS.items() if v.get("pagado"))
    except Exception as e:
        logger.warning("contable: no se pudieron leer los tipos de ausencia: %s", e)
        pag = ()
    return (ORDINARIAS,) + pag

_FECHA = "%d/%m/%Y"          # AU, día primero: lo mismo en Xero y en MYOB
_MAX_OPCION = 50             # tope de una opción de seguimiento en Xero


# ─────────────────────────────────────────────────────────────────────────────
# Configuración del grupo
# ─────────────────────────────────────────────────────────────────────────────
def identidad(grupo: str) -> dict:
    """Identidad fiscal del grupo: {abn, legal, plazo}.

    `legal` cae al nombre del grupo si no se ha puesto, para que un grupo sin migrar
    se comporte como antes en vez de sacar una factura sin emisor.
    """
    return {
        "abn": auth.group_text_setting(grupo, "ABN", ""),
        "legal": auth.group_text_setting(grupo, "LegalName", "") or str(grupo or ""),
        "plazo": int(_num(auth.group_text_setting(grupo, "PaymentTermsDays", "")) or 14),
    }


def mapa(grupo: str) -> dict:
    """Ajustes contables del grupo, con los de fábrica debajo.

    Lo guardado solo SOBRESCRIBE; nunca sustituye el diccionario entero. Así una
    categoría nueva (o un perfil nuevo) trae su cuenta por defecto en vez de salir
    vacía porque el JSON se guardó antes de que existiera.
    """
    cfg = dict(_DEFECTOS)
    cfg["cuentas"] = {p: dict(c) for p, c in _CUENTAS_DEFECTO.items()}
    cfg["conceptos"] = dict(_CONCEPTOS_DEFECTO)
    crudo = auth.group_text_setting(grupo, "AccountingJSON", "")
    if crudo:
        try:
            guardado = json.loads(crudo)
        except Exception as e:
            logger.warning("contable: AccountingJSON ilegible en %s: %s", grupo, e)
            guardado = {}
        for k, v in (guardado or {}).items():
            if k == "cuentas" and isinstance(v, dict):
                for p, c in v.items():
                    cfg["cuentas"].setdefault(p, {}).update(
                        {kk: str(vv) for kk, vv in (c or {}).items()})
            elif k == "conceptos" and isinstance(v, dict):
                # ⚠️ Mismo criterio que las cuentas: SOBRESCRIBE lo tocado y conserva
                # el resto. Sustituir el diccionario dejaría sin nombre un tipo de
                # ausencia añadido despues de guardar, y esa línea saldría en blanco.
                cfg["conceptos"].update({kk: str(vv) for kk, vv in (v or {}).items()})
            else:
                cfg[k] = v
    return cfg


def guardar_mapa(grupo: str, cfg: dict) -> tuple:
    """Guarda los ajustes contables del grupo (una escritura)."""
    try:
        crudo = json.dumps(cfg or {}, ensure_ascii=False)
    except Exception as e:
        return False, f"Error: {e}"
    return auth.set_group_setting(grupo, "AccountingJSON", crudo)


# ─────────────────────────────────────────────────────────────────────────────
# Perfiles de formato
# ─────────────────────────────────────────────────────────────────────────────
_XERO_COLS = ["*ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2",
              "POAddressLine3", "POAddressLine4", "POCity", "PORegion", "POPostalCode",
              "POCountry", "*InvoiceNumber", "Reference", "*InvoiceDate", "*DueDate",
              "InventoryItemCode", "*Description", "*Quantity", "*UnitAmount", "Discount",
              "*AccountCode", "*TaxType", "TaxAmount", "TrackingName1", "TrackingOption1",
              "TrackingName2", "TrackingOption2", "Currency"]

_MYOBVENTAS_COLS = ["Co./Last Name", "Invoice #", "Date", "Customer PO", "Description",
                     "Account #", "Amount", "Inc-Tax Amount", "Job", "Tax Code"]
_MYOB_COMPRAS_COLS = ["Co./Last Name", "Purchase #", "Date", "Supplier Invoice #",
                      "Description", "Account #", "Amount", "Inc-Tax Amount", "Job",
                      "Tax Code"]

# ⚠️ Verificados en la documentación de Xero (Accounting API · Types and Codes, tabla de
# Australia), no de memoria. La API usa el CÓDIGO (`OUTPUT`) y el CSV el NOMBRE que se ve
# en pantalla; aquí va el nombre porque esto es el CSV. Cuando se construya la API (2.3)
# hará falta el código, por eso van los dos.
IMPUESTOS_XERO = {
    "venta_con":  ("OUTPUT",         "GST on Income"),
    "venta_sin":  ("EXEMPTOUTPUT",   "GST Free Income"),
    "compra_con": ("INPUT",          "GST on Expenses"),
    "compra_sin": ("EXEMPTEXPENSES", "GST Free Expenses"),
}
# MYOB va por código corto: GST (10 %), FRE (libre de GST), N-T (no declarable).
IMPUESTOS_MYOB = {"venta_con": "GST", "venta_sin": "FRE",
                  "compra_con": "GST", "compra_sin": "FRE"}


def _numero(v) -> str:
    """Número plano para un importador: sin separador de miles, punto decimal.

    ⚠️ Sirve para importes Y para horas (el parte de v484), así que NO se llama
    `_dinero`: un nombre que miente sobre lo que hace es como se cuelan los errores.
    """
    return f"{round(_num(v), 2):.2f}"


def _fila_xero(c: dict) -> list:
    seg_n = c["cfg"].get("categoria_seguimiento", "Project") if c["seguimiento"] else ""
    seg_v = c["proyecto"] if c["seguimiento"] else ""
    return [c["contacto"], c["email"], c["direccion"], "", "", "", "", "", "", "",
            c["numero"], c["referencia"], c["fecha"], c["vence"], "",
            c["descripcion"], "1", _numero(c["neto"]), "",
            c["cuenta"], c["impuesto_nombre"], _numero(c["impuesto"]),
            seg_n, seg_v, "", "", c["cfg"].get("moneda", "AUD")]


def _fila_myob(c: dict) -> list:
    # ⚠️ La 4ª columna de MYOB es «Customer PO» / «Supplier Invoice #»: el número de
    # pedido DEL CLIENTE o la factura DEL PROVEEDOR. La app no tiene ninguno de los dos,
    # así que va VACÍA — meter ahí el proyecto llenaría un campo con un dato que no es
    # ese, y el contable lo leería como el número del proveedor. El proyecto viaja en
    # `Job`, que es su sitio. En Xero sí se usa `Reference`, que es texto libre.
    return [c["contacto"], c["numero"], c["fecha"], "", c["descripcion"],
            c["cuenta"], _numero(c["neto"]), _numero(_num(c["neto"]) + _num(c["impuesto"])),
            c["proyecto"] if c["seguimiento"] else "", c["impuesto_codigo"]]


PERFILES = {
    "xero": {"nombre": "Xero", "ventas": _XERO_COLS, "compras": _XERO_COLS,
             "fila": _fila_xero},
    "myob": {"nombre": "MYOB", "ventas": _MYOBVENTAS_COLS,
             "compras": _MYOB_COMPRAS_COLS, "fila": _fila_myob},
}


def perfiles() -> list:
    """[(id, nombre)] para el desplegable."""
    return [(k, v["nombre"]) for k, v in PERFILES.items()]


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo
# ─────────────────────────────────────────────────────────────────────────────
def reparte_impuesto(importes, impuesto_total) -> list:
    """Reparte `impuesto_total` entre `importes` de modo que la suma CUADRE exacta.

    ⚠️ Redondear cada línea por su cuenta da diferencias de centavos contra el total
    que ya está emitido y cobrado (100 líneas de 0,333 al 10 % no suman el impuesto de
    la factura). El resto se le da a la línea MÁS GRANDE, que es donde menos se nota y
    donde el contable lo esperaría.
    """
    importes = [_num(x) for x in (importes or [])]
    total = round(_num(impuesto_total), 2)
    if not importes:
        return []
    base = sum(importes)
    if base == 0:
        # Sin base no hay proporción posible: todo a la primera, y la suma cuadra igual.
        return [total] + [0.0] * (len(importes) - 1)
    partes = [round(total * x / base, 2) for x in importes]
    resto = round(total - sum(partes), 2)
    if resto:
        i = max(range(len(importes)), key=lambda k: abs(importes[k]))
        partes[i] = round(partes[i] + resto, 2)
    return partes


def _opcion_seguimiento(pid: str, etiqueta: str) -> str:
    """La opción de seguimiento (Xero) o el Job (MYOB) de un proyecto.

    ⚠️ Xero corta las opciones de seguimiento en 50 caracteres. Recortar la etiqueta
    podría hacer que dos proyectos distintos acabaran con la MISMA opción —y el costo
    de uno se cargaría al otro—, así que cuando no cabe se usa el ID, que es la
    identidad y siempre es único.
    """
    etq = str(etiqueta or "").strip()
    if not etq or len(etq) > _MAX_OPCION:
        return str(pid or "")
    return etq


def _rango(f, desde, hasta) -> bool:
    d = _parse_date(f)
    if not d:
        return False            # sin fecha legible no se puede afirmar que esté dentro
    return (not desde or d >= desde) and (not hasta or d <= hasta)


def _etiquetas(grupo: str) -> dict:
    """{pid: etiqueta única}. Una lectura, e incluye archivados e internos: una factura
    vieja puede apuntar a un proyecto que ya se archivó, y sin él la línea saldría sin
    seguimiento."""
    try:
        from core import projects as P
        proys = P.list_projects(grupo, incluir_archivados=True, incluir_internos=True)
        return P.etiqueta_proyectos(proys)
    except Exception as e:
        logger.warning("contable: no se pudieron leer los proyectos de %s: %s", grupo, e)
        return {}


def _escribe(columnas, filas) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(columnas)
    for f in filas:
        w.writerow(f)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Ventas (facturas emitidas)
# ─────────────────────────────────────────────────────────────────────────────
def csv_ventas(grupo: str, perfil: str, desde=None, hasta=None) -> dict:
    """CSV de facturas del periodo. {csv, filas, documentos, avisos, opciones}."""
    p = PERFILES.get(perfil)
    if not p:
        return {"csv": "", "filas": 0, "documentos": 0,
                "avisos": [t("Unknown format profile.")], "opciones": []}
    cfg = mapa(grupo)
    ident = identidad(grupo)
    cuentas = cfg.get("cuentas", {}).get(perfil, {})
    etq = _etiquetas(grupo)
    seg = bool(cfg.get("seguimiento", True))

    fichas = {}
    for c in clientes.list_clientes(grupo, incluir_inactivos=True) or []:
        fichas[str(c.get("ID", ""))] = c

    avisos, filas, docs, opciones = [], [], 0, set()
    if not ident["abn"]:
        avisos.append(t("This company has no ABN: its invoices already say «TAX INVOICE» "
                        "without one, which Australia requires above $82.50."))

    facturas = [f for f in invoices.list_facturas(grupo)
                if _rango(f.get("Date"), desde, hasta)]
    for f in sorted(facturas, key=lambda x: str(x.get("Number", ""))):
        if str(f.get("Status", "")).strip().lower() in ("anulada", "cancelled", "void"):
            continue
        lineas = invoices.lineas_de(f) or []
        if not lineas:
            continue
        pct = _num(f.get("TaxPct"))
        impuestos = reparte_impuesto([_num(l.get("importe")) for l in lineas],
                                     _num(f.get("Tax")))
        cli = fichas.get(str(f.get("ClientID", ""))) or {}
        vence = str(f.get("ExpiryDate", "") or "").strip()
        if not vence:
            avisos.append(t("Invoice {n} has no due date; the date of issue is used.",
                            n=f.get("Number", "")))
        fecha_d = _parse_date(f.get("Date"))
        vence_d = _parse_date(vence) or fecha_d
        docs += 1
        for ln, imp in zip(lineas, impuestos):
            pid = str(ln.get("proyecto_id", "") or "")
            opcion = _opcion_seguimiento(pid, etq.get(pid, "")) if pid else ""
            if seg and opcion:
                opciones.add(opcion)
            cod, nombre = IMPUESTOS_XERO["venta_con" if pct else "venta_sin"]
            filas.append(p["fila"]({
                "cfg": cfg, "seguimiento": seg,
                "contacto": str(f.get("ClientName", "") or cli.get("Name", "")),
                "email": str(cli.get("Email", "")),
                "direccion": str(cli.get("Address", "")),
                "numero": str(f.get("Number", "")),
                "referencia": opcion,
                "fecha": fecha_d.strftime(_FECHA) if fecha_d else "",
                "vence": vence_d.strftime(_FECHA) if vence_d else "",
                "descripcion": str(ln.get("concepto", "") or t("Services"))[:255],
                "neto": _num(ln.get("importe")),
                "impuesto": imp,
                "cuenta": cuentas.get(VENTAS, ""),
                "impuesto_nombre": nombre,
                "impuesto_codigo": IMPUESTOS_MYOB["venta_con" if pct else "venta_sin"],
                "proyecto": opcion,
            }))
    avisos += _avisos_comunes(perfil, cuentas, [VENTAS], cfg, seg, opciones)
    return {"csv": _escribe(p["ventas"], filas), "filas": len(filas),
            "documentos": docs, "avisos": avisos, "opciones": sorted(opciones)}


# ─────────────────────────────────────────────────────────────────────────────
# Compras (gastos con recibo)
# ─────────────────────────────────────────────────────────────────────────────
def csv_compras(grupo: str, perfil: str, desde=None, hasta=None) -> dict:
    """CSV de gastos del periodo, como facturas de proveedor."""
    p = PERFILES.get(perfil)
    if not p:
        return {"csv": "", "filas": 0, "documentos": 0,
                "avisos": [t("Unknown format profile.")], "opciones": []}
    cfg = mapa(grupo)
    cuentas = cfg.get("cuentas", {}).get(perfil, {})
    etq = _etiquetas(grupo)
    seg = bool(cfg.get("seguimiento", True))
    pct = auth.group_tax_default(grupo)
    dentro = bool(cfg.get("gastos_incluyen_impuesto", True))

    filas, avisos, opciones, proveedores = [], [], set(), {}
    gastos = [g for g in (expenses.list_group(grupo) or [])
              if _rango(g.get("Date"), desde, hasta)]
    usadas = set()
    for g in sorted(gastos, key=lambda x: str(x.get("ID", ""))):
        bruto = _num(g.get("Amount"))
        if not bruto:
            continue
        # ⚠️ Siempre se exporta el importe SIN impuesto, venga el recibo como venga:
        # un solo criterio para no depender de qué casilla marque quien importa.
        if dentro and pct:
            neto = round(bruto / (1.0 + pct / 100.0), 2)
            imp = round(bruto - neto, 2)
        else:
            neto, imp = round(bruto, 2), round(bruto * pct / 100.0, 2)
        cat = str(g.get("Category", "") or "Other")
        usadas.add(cat)
        pid = str(g.get("ProjectID", "") or "")
        opcion = _opcion_seguimiento(pid, etq.get(pid, "")) if pid else ""
        if seg and opcion:
            opciones.add(opcion)
        prov = str(g.get("Supplier", "") or "").strip()
        if prov:
            proveedores.setdefault(" ".join(prov.lower().split()), set()).add(prov)
        fecha_d = _parse_date(g.get("Date"))
        cod, nombre = IMPUESTOS_XERO["compra_con" if pct else "compra_sin"]
        filas.append(p["fila"]({
            "cfg": cfg, "seguimiento": seg,
            "contacto": prov or t("Unnamed supplier"),
            "email": "", "direccion": "",
            "numero": str(g.get("ID", "")),
            "referencia": opcion,
            "fecha": fecha_d.strftime(_FECHA) if fecha_d else "",
            "vence": fecha_d.strftime(_FECHA) if fecha_d else "",
            "descripcion": str(g.get("Description", "") or cat)[:255],
            "neto": neto, "impuesto": imp,
            "cuenta": cuentas.get(cat, ""),
            "impuesto_nombre": nombre,
            "impuesto_codigo": IMPUESTOS_MYOB["compra_con" if pct else "compra_sin"],
            "proyecto": opcion,
        }))

    # ⚠️ Los dos casan el proveedor por NOMBRE EXACTO: «Bunnings» y «bunnings  » son dos
    # fichas distintas, y el gasto del año queda partido en dos sin que nada avise.
    for _k, variantes in proveedores.items():
        if len(variantes) > 1:
            avisos.append(t("The supplier «{p}» is written {n} different ways; they "
                            "will become separate contacts.",
                            p=sorted(variantes)[0], n=len(variantes)))
    avisos += _avisos_comunes(perfil, cuentas, sorted(usadas), cfg, seg, opciones)
    return {"csv": _escribe(p["compras"], filas), "filas": len(filas),
            "documentos": len(filas), "avisos": avisos, "opciones": sorted(opciones)}


def _avisos_comunes(perfil, cuentas, claves, cfg, seg, opciones) -> list:
    """Lo que va a fallar AL IMPORTAR, dicho antes de descargar."""
    avisos = []
    faltan = [k for k in claves if not str(cuentas.get(k, "")).strip()]
    if faltan:
        legibles = [t("Sales") if k == VENTAS else k for k in faltan]
        avisos.append(t("No account is set for: {c}. MYOB rejects a row without a valid "
                        "account; Xero leaves it unallocated.",
                        c=", ".join(legibles)))
    if seg and opciones and perfil == "xero":
        avisos.append(t("In Xero, create the tracking category «{c}» with these {n} "
                        "options BEFORE importing, or the file is rejected.",
                        c=cfg.get("categoria_seguimiento", "Project"),
                        n=len(opciones)))
    if seg and opciones and perfil == "myob":
        avisos.append(t("In MYOB, the {n} jobs must already exist in the file.",
                        n=len(opciones)))
    return avisos


# ─────────────────────────────────────────────────────────────────────────────
# Parte de horas para la nómina (fase 2.2-A)
# ─────────────────────────────────────────────────────────────────────────────
def partes(grupo: str, desde, hasta) -> dict:
    """Las horas PAGADAS del periodo, persona × concepto × día.

    `{dias: [date...], filas: [{usuario, nombre, payroll_id, concepto, etiqueta,
      horas: {date: h}, total}], avisos: [...], total: h, personas: n}`

    ⚠️ **Formato ANCHO (una columna por día) a propósito.** Un parte de Xero Payroll es
    `TimesheetLines[] = {EarningsRateID, NumberOfUnits[]}`, y `NumberOfUnits` es un
    ARRAY con una entrada por día del periodo — verificado en su documentación, no
    supuesto. Construirlo largo (una fila por día) obligaría a pivotarlo cuando exista
    OAuth; así, 2.3 es un mapeo: cada fila de aquí ES una línea de allí y el orden de
    las columnas ES el orden del array.

    ⚠️ **Son las horas que se PAGAN, no las que se cargan a obra.** La base es la
    JORNADA fichada (lo mismo que usa `payroll.generar`), más las ausencias pagadas.
    Las horas de proyecto son otra cosa —lo que se le cobra al cliente— y meterlas
    aquí pagaría de más: la app ya mide que pueden superar la jornada (v320/v422). Por
    eso el desvío se AVISA en vez de sumarse.

    ⚠️ El día de ausencia sale de `ausencias.horas_pagadas_dia`, que es donde vive el
    criterio de v432 («un día vale UNA jornada, nunca dos»). Recalcularlo aquí sería
    una segunda definición de lo que se paga.
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1 or d1 < d0:
        return {"dias": [], "filas": [], "avisos": [t("The dates could not be read.")],
                "total": 0.0, "personas": 0}

    avisos = []
    dias = []
    d = d0
    while d <= d1 and len(dias) < _MAX_DIAS:
        dias.append(d)
        d += _dt.timedelta(days=1)
    if d <= d1:
        avisos.append(t("The period is longer than {n} days: only the first {n} are "
                        "exported. A timesheet goes per pay period.", n=_MAX_DIAS))
        d1 = dias[-1]

    cfg = mapa(grupo)
    nombres_concepto = cfg.get("conceptos", {})

    # ── de dónde salen las horas ──
    try:
        from core import timeclock as _TC
        jornada = _TC.horas_por_usuario_dia(grupo, d0, d1) or {}
    except Exception as e:
        logger.warning("contable: no se pudo leer la jornada de %s: %s", grupo, e)
        jornada = {}
        avisos.append(
            t("The clocked hours could not be read: the timesheet is incomplete."))
    try:
        from core import ausencias as _AU
        aus = _AU.horas_pagadas_dia(grupo, d0, d1) or {}
    except Exception as e:
        logger.warning("contable: no se pudieron leer las ausencias de %s: %s", grupo, e)
        aus = {}
        avisos.append(
            t("The paid absences could not be read: the timesheet is incomplete."))

    # ── quién es quién ──
    try:
        usuarios = auth.list_users(grupo) or []
    except Exception as e:
        logger.warning("contable: no se pudieron leer los usuarios de %s: %s", grupo, e)
        usuarios = []
    por_login = {str(u.get("User", "")): u for u in usuarios}
    _cuenta_nombre = {}
    for u in usuarios:
        _n = str(u.get("Name", "") or u.get("User", "")).strip().lower()
        _cuenta_nombre[_n] = _cuenta_nombre.get(_n, 0) + 1

    filas, sin_id, de_baja = [], [], []
    claves = sorted(set(jornada) | set(aus))
    for clave in claves:
        u = por_login.get(clave) or {}
        nombre = str(u.get("Name", "") or aus.get(clave, {}).get("nombre") or clave)
        pid = str(u.get("PayrollID", "") or "").strip()
        if not u:
            # ⚠️ Tiene horas y NO está en Login: una cuenta dada de baja con fichajes
            # históricos (el caso de v325). El proveedor no la conoce, así que se dice
            # en vez de exportar una línea que su nómina va a rechazar.
            de_baja.append(nombre)
        elif not pid and _cuenta_nombre.get(nombre.strip().lower(), 0) > 1:
            # ⚠️ Sin código y con el nombre REPETIDO: el proveedor casa por nombre y
            # no puede distinguirlos. Con el nombre único, no tener código es normal.
            sin_id.append(nombre)

        porc = {}
        for f, h in (jornada.get(clave) or {}).items():
            if _num(h):
                porc.setdefault(ORDINARIAS, {})[f] = round(_num(h), 2)
        for f, portipo in ((aus.get(clave) or {}).get("dias") or {}).items():
            for tipo, h in (portipo or {}).items():
                if _num(h):
                    porc.setdefault(tipo, {})[f] = round(_num(h), 2)

        for concepto in conceptos():
            horas = porc.get(concepto)
            if not horas:
                continue
            filas.append({
                "usuario": clave, "nombre": nombre, "payroll_id": pid,
                "concepto": concepto,
                "etiqueta": nombres_concepto.get(concepto, concepto),
                "horas": horas,
                "total": round(sum(horas.values()), 2)})

    # ── lo que hay que saber ANTES de mandarlo a la nómina ──
    if de_baja:
        avisos.append(t("These people have paid hours and are no longer in the app, so "
                        "the payroll provider does not know them: {q}",
                        q=", ".join(sorted(set(de_baja)))))
    if sin_id:
        avisos.append(t("Same name, no payroll ID — the provider matches by name and "
                        "cannot tell them apart: {q}",
                        q=", ".join(sorted(set(sin_id)))))
    recortes = [(aus[k].get("nombre") or k, r) for k in aus
                for r in (aus[k].get("recortados") or [])]
    if recortes:
        avisos.append(t("Days with BOTH an absence and clocked hours — one day pays one "
                        "shift, so the absence only pays the remainder: {q}",
                        q=" · ".join(f"{n} {r['fecha']}: {r['pagadas']} h"
                                     for n, r in recortes[:6])))
    # ⚠️ Horas de obra por encima de la jornada = alguien fichó a una obra sin abrir
    # jornada (v320). Sus horas PAGADAS salen de la jornada, así que ese parte va corto
    # y hay que decirlo: es el hueco que el resumen financiero llama «horas sin nómina».
    try:
        from core import timeclock as _TC2
        jp = _TC2.jornada_y_proyecto(grupo, d0, d1) or {}
        _desc = [str(v.get("nombre") or k) for k, v in jp.items()
                 if _num(v.get("proyecto")) > _num(v.get("jornada")) + 0.05]
        if _desc:
            avisos.append(t("More job hours than workday hours, so they clocked onto a "
                            "job without opening their workday and these paid hours "
                            "fall short: {q}", q=", ".join(sorted(set(_desc)))))
    except Exception as e:
        logger.warning("contable: no se pudo contrastar jornada y obra: %s", e)

    return {"dias": dias, "filas": filas, "avisos": avisos,
            "total": round(sum(f["total"] for f in filas), 2),
            "personas": len({f["usuario"] for f in filas})}


def csv_partes(grupo: str, desde, hasta) -> dict:
    """El parte en CSV ancho. {csv, filas, personas, total, avisos, dias}.

    ⚠️ **Xero Payroll AU no importa partes por CSV** —comprobado en su documentación,
    en sus Product Ideas (la petición sigue abierta) y en sus foros—, así que este
    fichero es para que lo lea una persona y lo teclee, y sirve para cualquier
    proveedor. El camino que SÍ conecta con Xero es la API (`POST /timesheets`), que
    necesita OAuth y los GUID de empleado y de earnings rate: eso es la fase 2.3, y
    esta forma ancha es exactamente la que esa API pide.
    """
    r = partes(grupo, desde, hasta)
    cab = ([t("Employee"), t("Payroll ID"), t("Earnings rate")]
           + [d.strftime(_FECHA) for d in r["dias"]] + [t("Total")])
    filas = [[f["nombre"], f["payroll_id"], f["etiqueta"]]
             + [(_numero(f["horas"][d]) if d in f["horas"] else "") for d in r["dias"]]
             + [_numero(f["total"])]
             for f in r["filas"]]
    return {"csv": _escribe(cab, filas), "filas": len(filas),
            "personas": r["personas"], "total": r["total"],
            "avisos": r["avisos"], "dias": r["dias"]}
