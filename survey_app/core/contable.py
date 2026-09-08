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


def _dinero(v) -> str:
    """Número plano para un importador: sin separador de miles y con punto decimal."""
    return f"{round(_num(v), 2):.2f}"


def _fila_xero(c: dict) -> list:
    seg_n = c["cfg"].get("categoria_seguimiento", "Project") if c["seguimiento"] else ""
    seg_v = c["proyecto"] if c["seguimiento"] else ""
    return [c["contacto"], c["email"], c["direccion"], "", "", "", "", "", "", "",
            c["numero"], c["referencia"], c["fecha"], c["vence"], "",
            c["descripcion"], "1", _dinero(c["neto"]), "",
            c["cuenta"], c["impuesto_nombre"], _dinero(c["impuesto"]),
            seg_n, seg_v, "", "", c["cfg"].get("moneda", "AUD")]


def _fila_myob(c: dict) -> list:
    # ⚠️ La 4ª columna de MYOB es «Customer PO» / «Supplier Invoice #»: el número de
    # pedido DEL CLIENTE o la factura DEL PROVEEDOR. La app no tiene ninguno de los dos,
    # así que va VACÍA — meter ahí el proyecto llenaría un campo con un dato que no es
    # ese, y el contable lo leería como el número del proveedor. El proyecto viaja en
    # `Job`, que es su sitio. En Xero sí se usa `Reference`, que es texto libre.
    return [c["contacto"], c["numero"], c["fecha"], "", c["descripcion"],
            c["cuenta"], _dinero(c["neto"]), _dinero(_num(c["neto"]) + _num(c["impuesto"])),
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
