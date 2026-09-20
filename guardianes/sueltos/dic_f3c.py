"""F3-C · CABECERAS DE COLUMNA (el hueco que el extractor no veía) + los últimos restos.

⚠️ Se traduce la ETIQUETA de la columna, NUNCA la clave del `column_config`, que es el
nombre de la columna del dataframe: `st.data_editor` devuelve las columnas con ESE
nombre, y el código las lee después (`edits["Importe"]`). Cambiarla dejaría la lectura
buscando una columna que ya no existe — sin ningún error, con la fila entera vacía.
"""
TRAD = {
    # cabeceras de tabla
    "Importe": "Amount",
    "Monto": "Amount",
    "Concepto": "Item",
    "Cantidad": "Qty",
    "Proyecto": "Project",
    "Cliente": "Client",
    "Costo": "Cost",
    "Avance": "Progress",
    "Total": "Total",
    "Cobrado": "Collected",
    "Pendiente": "Outstanding",
    "Base": "Base pay",
    "Neto": "Net",
    "Tarifa/h": "Rate/h",
    "Tipo": "Type",
    "Nombre": "Name",
    "Fecha": "Date",
    "Estado": "Status",
    "Horas": "Hours",
    # el que quedaba suelto del catálogo
    "Producto: costo unitario. Servicio: horas × tarifa.":
        "Product: unit cost. Service: hours × rate.",
}
