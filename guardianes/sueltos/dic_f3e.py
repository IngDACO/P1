"""F3-E · Las tarjetas KPI que el extractor no veía.

⚠️ Iban DENTRO de una lista de tuplas (`T.kpi_row([("Subtotal", …, "antes de impuesto")])`)
y el extractor solo miraba argumentos que fueran cadena directa. Son de lo más visible
de cada pantalla: el número grande de arriba.
"""
TRAD = {
    # catálogo
    "Artículos": "Items",
    "activos en el catálogo": "active in the catalogue",
    "Productos": "Products",
    "se cobran por cantidad": "charged by quantity",
    "Servicios": "Services",
    "se cobran por horas": "charged by the hour",
    # nóminas
    "Nóminas": "Payslips",
    " periodo(s)": " period(s)",
    "Pagado": "Paid",
    " pagada(s)": " paid",
    "Por pagar": "To pay",
    " emitida(s) sin pagar": " issued and unpaid",
    # cotizaciones
    "Cotizaciones": "Quotes",
    " vencida(s)": " expired",
    "En la calle": "Out with clients",
    " enviada(s) sin respuesta": " sent, awaiting reply",
    "Ganado": "Won",
    " aceptada(s)": " accepted",
    "Conversión": "Conversion",
    "de las decididas": "of those decided",
    "aún no hay decididas": "none decided yet",
    # totales de la cotización
    "Subtotal": "Subtotal",
    "antes de impuesto": "before tax",
    "Impuesto": "Tax",
    "Total al cliente": "Total to client",
    "lo que se le cobra": "what they are charged",
    "Tu ganancia": "Your profit",
    "margen efectivo ": "effective margin ",
    # detalle de cotización aceptada
    "Costo": "Cost",
    "Ingreso": "Revenue",
    "lo que aceptó el cliente": "what the client accepted",
    "Horas": "Hours",
    "The client could not be created: ": "The client could not be created: ",
}
