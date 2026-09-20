"""F3-B · Facturas y Nóminas — diccionario ES→EN.

⚠️ Vocabulario fijado a propósito, porque estas dos pantallas son las que el usuario
enseña a un cliente y las que v313 obligó a distinguir:
    Facturado / Invoiced · Cobrado / Collected · Por cobrar / Outstanding
    Vencido / Overdue · base / base pay · devengo / earning · deducción / deduction
    aporte / employer contribution · Neto / Net pay
`Superannuation` NO se traduce: es el nombre legal del aporte en Australia (AU).
Y `GST` tampoco — es el impuesto australiano; se conserva junto a VAT en el rótulo.
"""
TRAD = {
    # ── invoices_ui ────────────────────────────────────────────────
    ":material/info: Configura Google Sheets para gestionar facturas.":
        ":material/info: Configure Google Sheets to manage invoices.",
    "Facturado": "Invoiced",
    "Cobrado": "Collected",
    "Vencido": "Overdue",
    ":material/add_circle: Nueva factura": ":material/add_circle: New invoice",
    "Aún no hay facturas. Crea la primera con «Nueva factura».":
        "No invoices yet. Create the first one with «New invoice».",
    "Toca una factura para ver el detalle y registrar cobros.":
        "Tap an invoice to see the detail and record payments.",
    ":material/arrow_back: Volver a facturas": ":material/arrow_back: Back to invoices",
    "Factura no encontrada.": "Invoice not found.",
    "## :material/receipt_long: Factura Nº ": "## :material/receipt_long: Invoice No. ",
    "#### :material/list: Líneas": "#### :material/list: Lines",
    "Subtotal: **": "Subtotal: **",
    "**  ·  Impuesto (": "**  ·  Tax (",
    "**  ·  Total: **": "**  ·  Total: **",
    "Nota: ": "Note: ",
    ":material/download: Descargar factura (PDF)":
        ":material/download: Download invoice (PDF)",
    ":material/warning: No se pudo generar el PDF: ":
        ":material/warning: The PDF could not be generated: ",
    "#### :material/payments: Cobros": "#### :material/payments: Payments received",
    "Por cobrar": "Outstanding",
    "Cobrado ": "Collected ",
    "Registrar cobro ($)": "Record payment ($)",
    "Fecha del cobro": "Payment date",
    ":material/check: Registrar cobro": ":material/check: Record payment",
    ":material/check_circle: Factura cobrada por completo.":
        ":material/check_circle: Invoice fully collected.",
    "Cobros registrados:": "Payments recorded:",
    ":material/block: Anular factura": ":material/block: Void invoice",
    "La saca de las cuentas por cobrar. No se puede deshacer.":
        "It is taken out of accounts receivable. This cannot be undone.",
    "Anular esta factura": "Void this invoice",
    ":material/arrow_back: Cancelar": ":material/arrow_back: Cancel",
    "## :material/add_circle: Nueva factura": "## :material/add_circle: New invoice",
    ":material/info: Primero crea un cliente en 👥 Contactos.":
        ":material/info: Create a client first in 👥 Contacts.",
    ":material/contacts: Cliente": ":material/contacts: Client",
    ":material/archive: Incluir obras archivadas (":
        ":material/archive: Include archived sites (",
    "Archivar no es no-cobrar: lo habitual es archivar al terminar y facturar después.":
        "Archiving is not the same as not charging: the usual thing is to archive when "
        "the job ends and invoice afterwards.",
    ":material/info: No se pudo preseleccionar ese proyecto para este cliente (revisa a "
    "qué cliente está enlazado). Elige el alcance a mano.":
        ":material/info: That project could not be preselected for this client (check "
        "which client it is linked to). Choose the scope by hand.",
    "Alcance": "Scope",
    "Líneas de la factura — edita, agrega o quita. El «Proyecto» enlaza la línea para no "
    "volver a facturarla.":
        "Invoice lines — edit, add or remove. The «Project» links the line so it is not "
        "invoiced twice.",
    "Fecha": "Date",
    "Vencimiento": "Due date",
    "Impuesto % (GST/IVA)": "Tax % (GST/VAT)",
    "Nota (opcional)": "Note (optional)",
    "Subtotal **": "Subtotal **",
    "**  ·  Impuesto **": "**  ·  Tax **",
    "**  ·  Total **": "**  ·  Total **",
    ":material/receipt_long: Emitir factura": ":material/receipt_long: Issue invoice",
    "Agrega al menos una línea con importe.": "Add at least one line with an amount.",

    # ── payroll_ui ─────────────────────────────────────────────────
    ":material/info: Configura Google Sheets para gestionar nóminas.":
        ":material/info: Configure Google Sheets to manage payroll.",
    ":material/add_circle: Generar nómina": ":material/add_circle: Generate payroll",
    "Aún no hay nóminas. Genera la primera con «Generar nómina».":
        "No payslips yet. Generate the first one with «Generate payroll».",
    "Periodo": "Period",
    ":material/badge: Poner tarifas en Usuarios":
        ":material/badge: Set rates in Users",
    "Toca una nómina para ver el detalle, editar conceptos y marcar pagada.":
        "Tap a payslip to see the detail, edit items and mark it paid.",
    " nómina(s)  ·  base ": " payslip(s)  ·  base pay ",
    "  ·  neto ": "  ·  net ",
    "  ·  «Tarifa/h» vacía = esa persona no la tiene puesta.":
        "  ·  an empty «Rate/h» means that person has no rate set.",
    "## :material/add_circle: Generar nómina": "## :material/add_circle: Generate payroll",
    "Periodicidad": "Frequency",
    "Desde": "From",
    "Hasta": "To",
    "Superannuation % (aporte)": "Superannuation % (employer contribution)",
    "Retención de impuesto % (deducción)": "Tax withholding % (deduction)",
    ":material/info: Los % de super y retención vienen del grupo y son editables aquí y "
    "en cada nómina. No es un cálculo fiscal certificado; valida los importes.":
        ":material/info: The super and withholding percentages come from the company "
        "and can be edited here and on each payslip. This is not a certified tax "
        "calculation; check the amounts.",
    " usuario(s)** con horas de jornada en el periodo:":
        " user(s)** with workday hours in the period:",
    "Nadie tiene horas de jornada en ese periodo.":
        "Nobody has workday hours in that period.",
    ":material/payments: Generar nóminas": ":material/payments: Generate payslips",
    ":material/arrow_back: Volver a nóminas": ":material/arrow_back: Back to payroll",
    "Nómina no encontrada.": "Payslip not found.",
    "## :material/payments: Nómina — ": "## :material/payments: Payslip — ",
    "Periodo **": "Period **",
    " = base **": " = base pay **",
    "**  ·  estado: **": "**  ·  status: **",
    "#### :material/list: Conceptos (devengos, deducciones, aportes)":
        "#### :material/list: Items (earnings, deductions, employer contributions)",
    ":material/save: Guardar conceptos": ":material/save: Save items",
    "Neto a pagar": "Net pay",
    ":material/download: Descargar colilla (PDF)":
        ":material/download: Download payslip (PDF)",
    ":material/check_circle: Pagada (": ":material/check_circle: Paid (",
    "Fecha de pago": "Payment date",
    ":material/check: Marcar pagada": ":material/check: Mark as paid",
    ":material/block: Anular nómina": ":material/block: Void payslip",
    "Anular esta nómina": "Void this payslip",
    "## :material/payments: Mis colillas de pago": "## :material/payments: My payslips",
    ":material/info: Aún no está disponible.": ":material/info: Not available yet.",
    "Aún no tienes colillas de pago.": "You have no payslips yet.",
    " h  ·  neto **$": " h  ·  net **$",
    ":material/download: Descargar colilla": ":material/download: Download payslip",
}
