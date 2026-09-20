"""F3-D · Cotizaciones — diccionario ES→EN.

⚠️ Vocabulario de v355/v360, que aquí es lo que decide el precio y no puede quedar
ambiguo:  costo → cost (lo que te cuesta) · ganancia → profit (lo que quieres ganar,
en DINERO, que es lo que se teclea) · margen → margin (el %, que se DERIVA) ·
precio → price (lo que ve el cliente).
`NS` (number of stops) se conserva: es la sigla del plano.
"""
TRAD = {
    ":material/info: Configura Google Sheets para cotizar.":
        ":material/info: Configure Google Sheets to create quotes.",
    ":material/add_circle: Nueva cotización": ":material/add_circle: New quote",
    "Todavía no hay cotizaciones. Empieza con «Nueva cotización» — los artículos salen "
    "de :material/sell: Catálogo.":
        "No quotes yet. Start with «New quote» — the items come from "
        ":material/sell: Catalogue.",
    "Toca una cotización para ver el detalle, el PDF y marcar el resultado.":
        "Tap a quote to see the detail, the PDF and record the outcome.",
    "Total": "Total",
    "Margen": "Margin",
    ":material/sell: El catálogo está vacío. Da de alta productos y servicios en "
    ":material/sell: Catálogo antes de cotizar.":
        ":material/sell: The catalogue is empty. Add products and services in "
        ":material/sell: Catalogue before quoting.",
    "Añadir del catálogo": "Add from the catalogue",
    "Elige los artículos; luego ajustas cantidad y margen.":
        "Choose the items; then adjust quantity and margin.",
    ":material/add: Añadir a la cotización": ":material/add: Add to the quote",
    "Sin líneas todavía.": "No lines yet.",
    "**Líneas** — pon **cuánto quieres ganar** en cada rubro; el margen % y el precio "
    "salen solos":
        "**Lines** — enter **how much you want to make** on each item; the margin % and "
        "the price follow on their own",
    "Costo": "Cost",
    "Lo que te cuesta a ti. No lo ve el cliente.":
        "What it costs you. The client does not see this.",
    "Ganancia $": "Profit $",
    "Lo que quieres ganar en este rubro. El margen % se calcula solo.":
        "How much you want to make on this item. The margin % is worked out for you.",
    "Margen %": "Margin %",
    "Se calcula: ganancia ÷ costo.": "Worked out as profit ÷ cost.",
    "Costo + ganancia. Es lo que ve el cliente.":
        "Cost + profit. This is what the client sees.",
    "Cant.": "Qty",
    ":material/arrow_back: Cancelar": ":material/arrow_back: Cancel",
    "## :material/request_quote: Nueva cotización":
        "## :material/request_quote: New quote",
    "Cliente": "Client",
    ":material/person_add: Se creará su ficha en Contactos al guardar la cotización, y "
    "quedará enlazada a ella.":
        ":material/person_add: Their record will be created in Contacts when the quote "
        "is saved, and linked to it.",
    "Nombre del cliente *": "Client name *",
    "Persona de contacto": "Contact person",
    "Teléfono": "Phone",
    "Email": "Email",
    "Impuesto %": "Tax %",
    "Sale del valor por defecto del grupo.": "Taken from the company default.",
    "Notas para el cliente (opcional)": "Notes for the client (optional)",
    ":material/save: Crear cotización": ":material/save: Create quote",
    "El nombre del cliente es obligatorio.": "The client name is required.",
    "No se pudo crear el cliente: ": "The client could not be created: ",
    ":material/info: Ya existía una ficha de **":
        ":material/info: A record already existed for **",
    "**; la cotización se enlaza a esa.": "**; the quote is linked to that one.",
    ":material/schedule: La cotización incluye **":
        ":material/schedule: The quote includes **",
    " horas** de servicio. Al aceptarla podrás compararlas con las horas fichadas.":
        " service hours**. Once accepted you can compare them against the hours clocked.",
    ":material/arrow_back: Volver a cotizaciones": ":material/arrow_back: Back to quotes",
    "Cotización no encontrada.": "Quote not found.",
    ":material/sync: Actualizar precios desde el catálogo":
        ":material/sync: Refresh prices from the catalogue",
    "Trae los costos de hoy conservando lo que quieres ganar en cada línea.":
        "Brings today's costs across while keeping what you want to make on each line.",
    ":material/save: Guardar cambios": ":material/save: Save changes",
    "Precio": "Price",
    ":material/send: Marcar como enviada": ":material/send: Mark as sent",
    ":material/check_circle: El cliente la aceptó": ":material/check_circle: The client accepted it",
    ":material/block: La rechazó": ":material/block: They rejected it",
    ":material/content_copy: Nueva versión": ":material/content_copy: New version",
    "Clona esta cotización como borrador para cambiarla. La actual se conserva.":
        "Clones this quote as a draft so you can change it. The current one is kept.",
    ":material/download: Descargar cotización (PDF)":
        ":material/download: Download quote (PDF)",
    ":material/warning: No se pudo generar el PDF: ":
        ":material/warning: The PDF could not be generated: ",
    "### :material/construction: Convertirla en proyecto":
        "### :material/construction: Turn it into a project",
    "Nace con el cliente, el presupuesto y el margen que acabas de cotizar. Desde ahí "
    "sigue el flujo de siempre: costos, horas y factura.":
        "It starts with the client, the budget and the margin you have just quoted. "
        "From there the usual flow follows: costs, hours and invoice.",
    "Nombre del proyecto": "Project name",
    "Tipo": "Type",
    "Fecha de inicio": "Start date",
    "Paradas (NS)": "Stops (NS)",
    "Solo la instalación genera el cronograma estándar; con NS 0 el proyecto nace sin "
    "actividades.":
        "Only an installation generates the standard schedule; with NS 0 the project "
        "starts with no activities.",
    "Ubicación (opcional)": "Location (optional)",
    ":material/add_circle: Crear el proyecto": ":material/add_circle: Create the project",
}
