"""F3-F · Inventario de activos — diccionario ES→EN.

⚠️ NO se traduce el vocabulario que se GUARDA: `inventory.ESTADOS`, `CONDICIONES`,
`TIPOS_UBIC`, `CAT_DEFAULT` y los tipos de movimiento (`salida`/`entrada`/`traslado`/
`mantenimiento`) viven en la hoja y se comparan por su valor. Aquí solo entra lo que
se PINTA. Y `UbicacionRef` guarda el `PRJ-####` desde v306: el texto de ayuda lo dice
y por eso se conserva la sigla.
"""
TRAD = {
    "## :material/inventory_2: Inventario de activos":
        "## :material/inventory_2: Asset inventory",
    ":material/info: Configura Google Sheets para el inventario.":
        ":material/info: Configure Google Sheets for the inventory.",
    "Activos": "Assets",
    "Disponibles": "Available",
    "En uso": "In use",
    "Valor de compra: $": "Purchase value: $",
    " (depreciado línea recta)": " (straight-line depreciated)",
    "Mant. vencido": "Service overdue",
    ":material/add_circle: Registrar activo": ":material/add_circle: Register asset",
    ":material/archive: Ver también los dados de baja":
        ":material/archive: Show written-off ones too",
    "Un activo de baja sale del inventario pero conserva su historial de movimientos y "
    "su QR.":
        "A written-off asset leaves the inventory but keeps its movement history and "
        "its QR code.",
    " activo(s) dado(s) de baja oculto(s).": " written-off asset(s) hidden.",
    "Aún no hay activos. Registra el primero con «Registrar activo».":
        "No assets yet. Register the first one with «Register asset».",
    ":material/search: Buscar": ":material/search: Search",
    "nombre, serie, marca…": "name, serial, brand…",
    "Toca un activo para ver su ficha, su QR y gestionarlo. (":
        "Tap an asset to see its record, its QR code and manage it. (",
    "Valor": "Value",
    ":material/arrow_back: Volver al inventario": ":material/arrow_back: Back to inventory",
    "Activo no encontrado.": "Asset not found.",
    "## :material/inventory_2: ": "## :material/inventory_2: ",
    "Depreciación línea recta según vida útil.":
        "Straight-line depreciation over the useful life.",
    "**Ubicación:** ": "**Location:** ",
    "  ·  **Condición:** ": "  ·  **Condition:** ",
    ":material/build: Próximo mantenimiento: ": ":material/build: Next service: ",
    "#### :material/qr_code_2: QR": "#### :material/qr_code_2: QR code",
    ":material/info: Configura el secret APP_URL para que el QR abra la app.":
        ":material/info: Set the APP_URL secret so the QR code opens the app.",
    ":material/download: Etiqueta (PDF)": ":material/download: Label (PDF)",
    "No se pudo generar la etiqueta: ": "The label could not be generated: ",
    "No se pudo generar el QR: ": "The QR code could not be generated: ",
    "#### :material/swap_horiz: Acciones": "#### :material/swap_horiz: Actions",
    ":material/logout: Salida / entregar": ":material/logout: Check out / hand over",
    "Proyecto": "Project",
    "Usuario": "User",
    "Destino": "Destination",
    "Responsable": "Person responsible",
    ":material/check: Registrar salida": ":material/check: Record check-out",
    ":material/login: Entrada / devolver": ":material/login: Check in / return",
    "Bodega / ubicación de retorno": "Store / return location",
    "Bodega": "Store",
    ":material/check: Registrar entrada": ":material/check: Record check-in",
    ":material/move_up: Traslado": ":material/move_up: Transfer",
    "Nueva ubicación (tipo)": "New location (type)",
    "Detalle": "Detail",
    ":material/check: Trasladar": ":material/check: Transfer",
    ":material/build: Mantenimiento": ":material/build: Service",
    "Dejar el activo EN mantenimiento": "Leave the asset IN service",
    ":material/check: Registrar mantenimiento": ":material/check: Record service",
    "#### :material/history: Historial": "#### :material/history: History",
    "Sin movimientos todavía.": "No movements yet.",
    "Costo": "Cost",
    "#### :material/edit: Editar activo": "#### :material/edit: Edit asset",
    "Nombre": "Name",
    "Estado": "Status",
    "Bodega o usuario que lo tiene. Si el activo está en una obra, aquí va el ID del "
    "proyecto (PRJ-####) — se pone solo al registrar la salida; la lista muestra el "
    "nombre.":
        "Store or person holding it. If the asset is on a site, this holds the project "
        "ID (PRJ-####) — it is set automatically when the check-out is recorded; the "
        "list shows the name.",
    ":material/save: Guardar cambios": ":material/save: Save changes",
    ":material/block: Dar de baja": ":material/block: Write off",
    "Retira el activo del inventario (queda en el histórico). Para volver a verlo, marca "
    "«Ver también los dados de baja».":
        "Takes the asset out of the inventory (it stays in the history). To see it "
        "again, tick «Show written-off ones too».",
    "Motivo": "Reason",
    "Dar de baja este activo": "Write off this asset",
    ":material/block: Este activo está **dado de baja**: no aparece en el inventario "
    "salvo que marques «Ver también los dados de baja».":
        ":material/block: This asset is **written off**: it does not appear in the "
        "inventory unless you tick «Show written-off ones too».",
    ":material/restore: Reactivar este activo": ":material/restore: Reactivate this asset",
    ":material/arrow_back: Cancelar": ":material/arrow_back: Cancel",
    "## :material/add_circle: Registrar activo": "## :material/add_circle: Register asset",
    "Foto (opcional)": "Photo (optional)",
    "Nombre del activo *": "Asset name *",
    "Categoría": "Category",
    "Marca": "Brand",
    "Modelo": "Model",
    "Nº de serie": "Serial no.",
    "Condición": "Condition",
    "Ubicación (tipo)": "Location (type)",
    "Ubicación (detalle)": "Location (detail)",
    "Bodega, proyecto o usuario.": "Store, project or user.",
    "Valor de compra": "Purchase value",
    "Vida útil (años)": "Useful life (years)",
    "Para la depreciación. 0 = no depreciar.":
        "Used for depreciation. 0 = do not depreciate.",
    "Nota": "Note",
    ":material/add: Registrar": ":material/add: Register",
    "El nombre es obligatorio.": "The name is required.",
    ":material/warning: El activo se registra, pero **la foto no se pudo subir** a "
    "Drive. Añádela luego desde su ficha.":
        ":material/warning: The asset is registered, but **the photo could not be "
        "uploaded** to Drive. Add it later from its record.",
    ":material/insights: Reportes de valor": ":material/insights: Value reports",
    "**Por categoría**": "**By category**",
    "Compra": "Purchase",
    "Actual": "Current",
    "**Por ubicación**": "**By location**",
    "Valor actual": "Current value",
    ":material/category: Categorías": ":material/category: Categories",
    "Las de por defecto siempre están; aquí añades/quitas las tuyas.":
        "The default ones are always there; here you add/remove your own.",
    "Nueva categoría": "New category",
    "Nueva categoría…": "New category…",
    ":material/add: Añadir": ":material/add: Add",
    "Quitar una categoría propia": "Remove one of your categories",
    ":material/delete: Quitar": ":material/delete: Remove",
}
