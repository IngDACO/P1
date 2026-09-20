"""F3-K · projects_ui (2/4): costos del proyecto, ganancia por rubro, órdenes de compra,
Mis proyectos (campo) y agrupaciones.

⚠️ Vocabulario de v355/v360/v370/v373, que decide el precio:
    costo/h → cost/h (lo que te cuesta) · ganancia/h → profit/h (lo que quieres ganar)
    precio/h → price/h (lo que se le cobra) · ganancia fija → fixed profit
    precio pactado → agreed price (manda sobre todo lo anterior)
⚠️ Una AGRUPACIÓN es un edificio con varios elevadores: se traduce «group of lifts»
(no «grouping»), y ELEVADOR se conserva como «lift», que es el término del sector en AU.
"""
TRAD = {
    # ── resumen financiero ─────────────────────────────────────────
    "**:material/notifications: Pendientes**": "**:material/notifications: Pending**",
    "Ver el detalle e ir a resolverlo": "See the detail and go and sort it out",
    "Ingresos (facturado)": "Income (invoiced)",
    "Costos (lo que pagas)": "Costs (what you pay)",
    "Ganancia": "Profit",
    "Lo realmente facturado menos los costos (nóminas + compras) = ganancia. "
    "«Rentabilidad» es la estimación por margen; esto es lo ejecutado.":
        "What was actually invoiced minus the costs (payroll + purchases) = profit. "
        "«Profitability» is the estimate from the margin; this is what actually happened.",

    # ── recibos / costos del proyecto ──────────────────────────────
    "Cargar recibo": "Upload receipt",
    "Categoría": "Category",
    "Valor total del recibo": "Total value of the receipt",
    "Proveedor": "Supplier",
    "Descripción": "Description",
    "Foto / PDF del recibo": "Photo / PDF of the receipt",
    "Guardar recibo": "Save receipt",
    "Ingresa el valor del recibo.": "Enter the value of the receipt.",
    ":material/receipt_long: Recibos (": ":material/receipt_long: Receipts (",
    "Toca un recibo para ver la foto.": "Tap a receipt to see the photo.",
    " — es un PDF; descárgalo para verlo.": " — it is a PDF; download it to view it.",
    ":material/download: Descargar recibo": ":material/download: Download receipt",
    "No se pudo cargar el archivo del recibo.": "The receipt file could not be loaded.",
    "**Reparto del costo**": "**Cost split**",
    "Mano de obra": "Labour",
    "Compras": "Purchases",
    "**Compras por categoría**": "**Purchases by category**",
    "**Mano de obra por persona**": "**Labour by person**",
    "Coste acumulado día a día. La línea discontinua gris es el presupuesto; la de "
    "color, dónde acabas al ritmo actual.":
        "Cumulative cost day by day. The dashed grey line is the budget; the coloured "
        "one is where you end up at the current rate.",
    "Hace falta más de un movimiento para dibujar la curva de gasto.":
        "More than one movement is needed to draw the spend curve.",
    "Costo total": "Total cost",
    "Costará al terminar": "Cost at completion",
    ":material/shopping_cart: Vas dentro de presupuesto, pero con las **":
        ":material/shopping_cart: You are within budget, but with the **",
    " ya pedidos** el proyecto llega a **": " already ordered** the project reaches **",
    " por encima** de los ": " over** the ",
    " presupuestados.": " budgeted.",
    ":material/receipt_long: Facturar esta obra": ":material/receipt_long: Invoice this job",
    "Abre la nueva factura con este cliente y este proyecto ya elegidos.":
        "Opens the new invoice with this client and this project already chosen.",
    "Ingreso estimado del proyecto menos lo ya facturado.":
        "The project's estimated revenue minus what has already been invoiced.",

    # ── ganancia por rubro (v360) ──────────────────────────────────
    ":material/savings: Cuánto ganas con esta obra":
        ":material/savings: How much you make on this job",
    "Nadie ha fichado horas en esta obra todavía, así que no hay ganancia por hora que "
    "repartir. Si su valor no está en el tiempo (un delivery, un suministro), usa la "
    "**ganancia fija** de abajo.":
        "Nobody has clocked hours on this job yet, so there is no hourly profit to set. "
        "If its value is not in the time (a delivery, a supply job), use the **fixed "
        "profit** below.",
    "Costo/h": "Cost/h",
    "Su tarifa. Lo que te cuesta.": "Their rate. What it costs you.",
    "Ganancia/h": "Profit/h",
    "Lo que quieres ganar por cada hora suya en esta obra.":
        "What you want to make on each of their hours on this job.",
    "Precio/h": "Price/h",
    "Costo + ganancia. Lo que se le cobra al cliente.":
        "Cost + profit. What the client is charged.",
    "Ganas": "You make",
    "Horas × ganancia/h.": "Hours × profit/h.",
    ":material/save: Guardar ganancias": ":material/save: Save profits",
    ":material/undo: Volver al %": ":material/undo: Back to the %",
    "Quita las ganancias por hora y vuelve al margen %.":
        "Removes the hourly profits and goes back to the margin %.",
    "**Ganancia fija de la obra**": "**Fixed profit for the job**",
    "Lo que vale esta obra por sí misma, **además** de lo que ganes con las horas. Para "
    "delivery, suministro o cualquier trabajo cuyo valor no esté en el tiempo. Déjala en "
    "0 si no aplica.":
        "What this job is worth in itself, **on top of** what you make on the hours. For "
        "deliveries, supply or any work whose value is not in the time. Leave it at 0 if "
        "it does not apply.",
    "Ganancia fija ($)": "Fixed profit ($)",
    "Se suma al ingreso estimado de la obra. Una obra que nació de una cotización "
    "aceptada NO la usa: ahí manda el precio que el cliente firmó.":
        "It is added to the job's estimated revenue. A job that came from an accepted "
        "quote does NOT use it: there the price the client signed wins.",
    ":orange[Esta obra tiene precio pactado, así que este importe no se usa.]":
        ":orange[This job has an agreed price, so this amount is not used.]",
    ":material/save: Guardar ganancia fija": ":material/save: Save fixed profit",

    # ── órdenes de compra (v343) ───────────────────────────────────
    "Lo que ya se pidió al proveedor y todavía no ha llegado. Al marcarla **recibida** se "
    "carga sola al costo del proyecto.":
        "What has already been ordered from the supplier and has not arrived yet. When "
        "it is marked **received** it is charged to the project cost on its own.",
    " · pedida ": " · ordered ",
    ":material/warning: Esta orden está recibida pero **su gasto no se registró**, así "
    "que su costo no está contado.":
        ":material/warning: This order is received but **its cost was not recorded**, so "
        "it is not being counted.",
    "Registrar el gasto ahora": "Record the cost now",
    "Valor recibido": "Value received",
    "Si llegó por otro importe, corrígelo aquí antes de recibir.":
        "If it arrived at a different amount, correct it here before receiving.",
    "Recibir": "Receive",
    "Cancelar": "Cancel",
    "Todavía no hay órdenes registradas en este proyecto.":
        "No orders recorded on this project yet.",
    "**Nueva orden**": "**New order**",
    "Valor": "Value",
    "p. ej. rieles T75-3/B ×12": "e.g. T75-3/B rails ×12",
    "Fecha esperada de entrega": "Expected delivery date",
    "Opcional. Sin ella, la orden nunca se marca como atrasada — no se puede decir que "
    "llega tarde si nadie dijo cuándo llegaba.":
        "Optional. Without it the order is never flagged as late — you cannot say it is "
        "late if nobody said when it was due.",
    ":material/add_circle: Registrar orden": ":material/add_circle: Record order",

    # ── Mis proyectos (campo) ──────────────────────────────────────
    "Tipo": "Type",
    "Avance del proyecto": "Project progress",
    "Cliente": "Client",
    "Proyecto no encontrado.": "Project not found.",
    "No tienes proyectos asignados todavía. El administrador te asigna a un proyecto.":
        "You have no projects assigned yet. The administrator assigns you to a project.",
    "Proyecto asignado": "Assigned project",
    "Elige el proyecto en el que estás trabajando. Si fichas en :material/schedule: "
    "Fichaje, se abre solo.":
        "Choose the project you are working on. If you clock in at :material/schedule: "
        "Time clock, it opens on its own.",
    ":material/route: Mi ruta (mis obras en el mapa)":
        ":material/route: My route (my sites on the map)",
    ":material/calendar_month: Ver la planificación de la semana (toda la cuadrilla)":
        ":material/calendar_month: See the week's plan (the whole crew)",
    "No se pudo cargar la ruta ahora mismo.": "The route could not be loaded right now.",
    "### :material/assignment: Mis proyectos": "### :material/assignment: My projects",
    "La gestión de proyectos necesita Google Sheets configurado.":
        "Project management needs Google Sheets configured.",
    "#### Actividades — actualiza tu avance": "#### Activities — update your progress",
    "Este proyecto no tiene actividades registradas.":
        "This project has no activities recorded.",
    "Tu avance en esta actividad": "Your progress on this activity",
    "Opcional": "Optional",
    "Las fechas se registran solas: **inicio** al pasar de 0, **fin** al llegar a 100.":
        "The dates record themselves: **start** when it goes above 0, **end** when it "
        "reaches 100.",
    ":material/save: Guardar avances": ":material/save: Save progress",
    "No cambiaste ningún avance.": "You did not change any progress.",

    # ── panel del propietario ──────────────────────────────────────
    "#### :material/search: Abrir proyecto": "#### :material/search: Open project",
    "Proyecto": "Project",
    "Mapa": "Map",
    ":material/assignment: Ver tabla detallada": ":material/assignment: See detailed table",
    "### :material/folder: Todos los proyectos": "### :material/folder: All projects",
    ":material/archive: Ver también los archivados":
        ":material/archive: Show archived ones too",
    "Grupo para el nuevo proyecto": "Company for the new project",
    "Aún no hay grupos. Crea uno en **:material/business: Grupos** para poder registrar "
    "proyectos.":
        "No companies yet. Create one in **:material/business: Companies** so projects "
        "can be recorded.",

    # ── agrupaciones ───────────────────────────────────────────────
    "**Agrupaciones — ": "**Groups of lifts — ",
    "Toca una agrupación para abrir su tablero.": "Tap a group to open its dashboard.",
    "No hay agrupaciones. Crea una abajo y elige qué elevadores la componen.":
        "No groups yet. Create one below and choose which lifts belong to it.",
    "Nueva agrupación": "New group of lifts",
    "Los proyectos se crean primero; aquí eliges cuáles forman parte.":
        "Projects are created first; here you choose which ones belong.",
    "Nombre de la agrupación": "Group name",
    "Descripción (opcional)": "Description (optional)",
    "Crear agrupación": "Create group",
    "Agrupación creada, pero: ": "Group created, but: ",
    "Agrupación no encontrada.": "Group not found.",
    "← Volver a las agrupaciones": "← Back to the groups",
    "Esta agrupación aún no tiene elevadores. Añádelos abajo.":
        "This group has no lifts yet. Add them below.",
    "Avance consolidado": "Consolidated progress",
    "Elevadores": "Lifts",
    "Entrega del conjunto": "Delivery of the whole group",
    "Con retraso": "Behind schedule",
    "Alarmas": "Alerts",
    "Horas": "Hours",
    "**:material/trending_up: Avance del conjunto — plan vs real**":
        "**:material/trending_up: Progress of the whole group — plan vs actual**",
    "Ponderado por el peso de cada elevador. La curva real se corta en HOY.":
        "Weighted by each lift's weight. The actual curve stops at TODAY.",
    "**:material/analytics: Comparativa entre elevadores**":
        "**:material/analytics: Comparison between lifts**",
    "«vs media» compara cada elevador con el promedio de la agrupación; solo se marca si "
    "se desvía 15% o más.":
        "«vs avg» compares each lift with the group average; it is only flagged if it "
        "differs by 15% or more.",
    "No hay proyectos en el grupo todavía.": "There are no projects in this company yet.",
    "Cuánto pesa este elevador en el avance consolidado.":
        "How much this lift weighs in the consolidated progress.",
    ":material/warning: Ya en otra": ":material/warning: Already in another",
    "Marcarlo aquí lo MUEVE a esta agrupación.": "Ticking it here MOVES it to this group.",
    ":material/build: Proyectos de esta agrupación": ":material/build: Projects in this group",
    "Marca los elevadores que la componen. Al quitar uno se **desagrupa**, no se borra.":
        "Tick the lifts that belong to it. Unticking one **ungroups** it, it is not "
        "deleted.",
    " proyectos: cada cambio es una escritura en la hoja; puede tardar unos segundos.":
        " projects: each change is a write to the sheet; it may take a few seconds.",
    ":material/save: Guardar los proyectos de la agrupación":
        ":material/save: Save the group's projects",
    ":material/delete: Eliminar agrupación": ":material/delete: Delete group",
    "Los proyectos no se borran; solo se desagrupan.":
        "The projects are not deleted; they are only ungrouped.",
    "Confirmo eliminar esta agrupación": "I confirm I want to delete this group",
    "Eliminar agrupación": "Delete group",
}
