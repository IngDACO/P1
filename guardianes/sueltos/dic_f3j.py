"""F3-J · projects_ui (1/4): localizaciones internas, horas, gastos, rentabilidad, P&L.

⚠️ Vocabulario que v313/v422/v425 obligaron a distinguir y que aquí NO puede volver a
mezclarse:
    «lo que PAGAS»  → costs you pay          (P&L)
    «cargado a obras» → charged to jobs      (horas imputadas × tarifa)
    «de estructura» → overhead               (localizaciones internas: nunca se factura)
    conciliación → reconciliation · sin explicar → unexplained
    comprometido → committed (órdenes de compra, v343)
"""
TRAD = {
    # ── localizaciones internas ────────────────────────────────────
    "Localizaciones": "Locations",
    "Oficinas, almacenes y talleres: aquí se ficha, se hace el pre-start y se cargan los "
    "gastos de administración. **No tienen cronograma ni avance, y su costo nunca se le "
    "carga a una obra ni se le factura a un cliente.**":
        "Offices, stores and workshops: this is where people clock in, do the pre-start "
        "and charge admin costs. **They have no schedule and no progress, and their "
        "cost is never charged to a job or invoiced to a client.**",
    "Horas trabajadas": "Hours worked",
    "Gasto de estructura": "Overhead spend",
    "Personas": "People",
    ":material/info: Aún no hay localizaciones. Crea la oficina o el almacén aquí abajo "
    "para que el equipo pueda fichar, hacer su pre-start y cargarle gastos.":
        ":material/info: No locations yet. Create the office or the store below so the "
        "team can clock in, do their pre-start and charge costs to it.",
    " h**  \n<small>trabajadas</small>": " h**  \n<small>worked</small>",
    "**  \n<small>gastado</small>": "**  \n<small>spent</small>",
    "**  \n<small>asignados</small>": "**  \n<small>assigned</small>",
    " aviso(s) abierto(s)]": " open alert(s)]",
    "Abrir →": "Open →",
    "Nueva localización": "New location",
    "**:material/map: Dónde está** — opcional, fija el pin":
        "**:material/map: Where it is** — optional, drops the pin",
    ":material/place: Se guardará: **": ":material/place: It will be saved as: **",
    "Estar asignado aquí es lo que da acceso permanente a ficharla. Quien venga un día "
    "suelto se asigna desde Planificación, sin tocar esta lista.":
        "Being assigned here is what gives permanent access to clock in. Anyone coming "
        "for a single day is assigned from Planning, without touching this list.",
    "Oficina Sydney, Almacén Chullora…": "Sydney office, Chullora store…",
    "opcional": "optional",
    "Horario, accesos, normas del sitio…": "Hours, access, site rules…",
    ":material/save: Crear localización": ":material/save: Create location",
    "No se pudo crear: ": "It could not be created: ",
    "Localización creada: ": "Location created: ",
    "#### :material/engineering: Quién ha trabajado aquí":
        "#### :material/engineering: Who has worked here",
    "No se pudieron leer las horas: ": "The hours could not be read: ",
    "Todavía nadie ha fichado aquí.": "Nobody has clocked in here yet.",
    " — ⚠️ esto es costo de **estructura**: no se le carga a ninguna obra ni se le "
    "factura a nadie.":
        " — ⚠️ this is **overhead**: it is not charged to any job and not invoiced to "
        "anyone.",
    "#### :material/health_and_safety: Pre-Start":
        "#### :material/health_and_safety: Pre-Start",
    "No se pudo leer el historial: ": "The history could not be read: ",
    "Sin pre-starts registrados en esta localización. Se hace desde la sección "
    "Pre-Start, eligiendo esta localización.":
        "No pre-starts recorded at this location. They are done from the Pre-Start "
        "section, choosing this location.",
    " más.": " more.",
    "No se encontró la localización.": "The location was not found.",
    "Ese ID no es una localización interna.": "That ID is not an internal location.",
    ":material/arrow_back: Volver a localizaciones": ":material/arrow_back: Back to locations",
    "Sección": "Section",
    "#### :material/badge: Asignados de forma habitual":
        "#### :material/badge: Permanently assigned",
    "Pueden ficharla siempre. Para un día suelto, asígnala desde Planificación.":
        "They can always clock in here. For a single day, assign it from Planning.",
    "Nadie asignado de forma permanente. Solo podrán ficharla quienes la tengan puesta "
    "hoy en Planificación.":
        "Nobody permanently assigned. Only those who have it set for today in Planning "
        "will be able to clock in.",
    ":material/engineering: Quién trabaja aquí de forma habitual":
        ":material/engineering: Who normally works here",
    "Nombre *": "Name *",
    "Tipo *": "Type *",
    "Responsable": "Person in charge",
    "Estado": "Status",
    "Cerrada = ya no se usa, pero su histórico se conserva. Archivada = además "
    "desaparece de la lista.":
        "Closed = no longer used, but its history is kept. Archived = it also "
        "disappears from the list.",
    ":material/push_pin: Instrucciones / notas": ":material/push_pin: Instructions / notes",
    ":material/save: Guardar": ":material/save: Save",
    "El nombre es obligatorio.": "The name is required.",
    "Localización actualizada.": "Location updated.",

    # ── horas del grupo ────────────────────────────────────────────
    "El fichaje necesita Google Sheets configurado.":
        "The time clock needs Google Sheets configured.",
    "Periodo": "Period",
    "Sin fichajes en el periodo.": "No time entries in the period.",
    "Jornada": "Workday",
    "En proyectos": "On projects",
    "En estructura": "On overhead",
    "Sin asignar": "Unallocated",
    "M.O. cargada a obras": "Labour charged to jobs",
    ":material/error: **": ":material/error: **",
    " h**: hay quien imputó a obras MÁS horas que las de su jornada (":
        " h**: some people charged MORE hours to jobs than their workday (",
    "). Fichó al proyecto sin abrir jornada, así que esas horas **se cargan al cliente y "
    "no entran en ninguna nómina**. Por eso «sin asignar» sale como «—»: no es "
    "calculable.":
        "). They clocked in to the project without opening their workday, so those hours "
        "**are charged to the client and appear in no payslip**. That is why "
        "«unallocated» shows «—»: it cannot be worked out.",
    "%** de la jornada del grupo fue traslados y espera (sin asignar).":
        "%** of the company's workday was travel and waiting (unallocated).",
    " M.O. cargada = horas imputadas × tarifa de cada persona; no incluye los aportes de "
    "ley (ver Resumen → Conciliación).":
        " Labour charged = hours charged × each person's rate; it does not include "
        "statutory contributions (see Summary → Reconciliation).",
    ":material/touch_app: Toca una persona y «Abrir ficha» para gestionarla.":
        ":material/touch_app: Tap a person and «Open record» to manage them.",
    "→ Abrir ficha de ": "→ Open record for ",
    "«—» en *sin asignar*: esa persona imputó a proyectos más horas que las de su "
    "jornada, así que el dato no es fiable (fichó al proyecto sin abrir jornada). Se "
    "corrige a partir de v150; el histórico anterior queda así.":
        "«—» under *unallocated*: that person charged more hours to projects than their "
        "workday, so the figure is not reliable (they clocked in to the project without "
        "opening their workday). Fixed from v150 onwards; earlier history stays as it is.",
    "**Horas del grupo por proyecto**": "**Company hours by project**",
    " h</div></div>": " h</div></div>",
    "**:material/search: Horas por persona y proyecto**":
        "**:material/search: Hours by person and project**",
    "Cada celda: horas que esa persona imputó a ese proyecto en el periodo. Las columnas "
    "son los proyectos.":
        "Each cell: hours that person charged to that project in the period. The columns "
        "are the projects.",

    # ── gastos del grupo ───────────────────────────────────────────
    "Los gastos necesitan Google Sheets configurado.":
        "Costs need Google Sheets configured.",
    "No hay proyectos en el grupo.": "There are no projects in this company.",
    "Costo cargado a obras": "Cost charged to jobs",
    "Presupuesto": "Budget",
    "% consumido": "% used",
    "Proyección al terminar": "Projected at completion",
    "Sobre presupuesto": "Over budget",
    "Comprometido": "Committed",
    ":material/business: **": ":material/business: **",
    "** de estructura (": "** of overhead (",
    " de mano de obra + ": " of labour + ",
    " de compras) en ": " of purchases) across ",
    " localización(es). **No se le carga a ninguna obra ni entra en el % consumido**, "
    "pero sí es costo del grupo y cuenta en el P&L.":
        " location(s). **It is not charged to any job and does not count towards % "
        "used**, but it is a company cost and does count in the P&L.",
    ":material/help: **": ":material/help: **",
    " compra(s) sin proyecto** (o de un proyecto borrado). Cuentan en el costo del "
    "grupo, pero no en el presupuesto de ninguna obra — asígnalas desde el recibo.":
        " purchase(s) with no project** (or from a deleted project). They count towards "
        "the company cost, but not towards any job's budget — assign them from the "
        "receipt.",
    "**Gasto por rubro**": "**Spend by category**",
    "Incluye la estructura: esta torta es el gasto del **grupo**, no solo el cargado a "
    "obras.":
        "Overhead included: this chart is the **company's** spend, not only what is "
        "charged to jobs.",
    "**Proyectos con presupuesto**": "**Projects with a budget**",
    ":material/touch_app: Toca una fila y «Abrir» para ir a ese proyecto. **Proyección** "
    "= costo al terminar al ritmo actual. sobre = ya se pasó · pedido = se pasará con el "
    "material ya encargado · riesgo = se pasará al ritmo actual · ok = dentro.":
        ":material/touch_app: Tap a row and «Open» to go to that project. **Projected** "
        "= cost at completion at the current rate. over = already over · ordered = will "
        "go over with the material already on order · at risk = will go over at the "
        "current rate · ok = within budget.",
    "→ Abrir ": "→ Open ",
    "**Proyectos sin presupuesto asignado**": "**Projects with no budget set**",
    " proyecto(s) sin presupuesto: no hay contra qué comparar su gasto. Se define en el "
    "detalle del proyecto → :material/edit: Datos.":
        " project(s) with no budget: there is nothing to compare their spend against. "
        "It is set in the project detail → :material/edit: Data.",
    ":material/download: Exportar CSV (contabilidad)":
        ":material/download: Export CSV (accounting)",

    # ── rentabilidad ───────────────────────────────────────────────
    ":material/info: Aún no hay proyectos con costo registrado (horas o compras).":
        ":material/info: No projects with recorded cost yet (hours or purchases).",
    "Lo que costó cada obra (horas imputadas × tarifa + materiales) frente a lo que "
    "cobrarías (MO × (1 + margen) + materiales). Aquí mismo se editan los márgenes y se "
    "ve cuánto de ese estimado ya está facturado.":
        "What each job cost (hours charged × rate + materials) against what you would "
        "charge (labour × (1 + margin) + materials). The margins are edited right here, "
        "and you can see how much of that estimate is already invoiced.",
    "Costo cargado": "Cost charged",
    "Ingreso estimado": "Estimated revenue",
    "Ganancia estimada": "Estimated profit",
    "Ya facturado": "Already invoiced",
    "Por facturar": "To invoice",
    "«Costo cargado» = horas imputadas × tarifa + materiales; NO incluye los aportes de "
    "ley ni las horas sin imputar — eso lo cubre el margen (Resumen → Conciliación).":
        "«Cost charged» = hours charged × rate + materials; it does NOT include "
        "statutory contributions or unallocated hours — the margin covers those "
        "(Summary → Reconciliation).",
    "Margen %": "Margin %",
    "Editable: cámbialo y pulsa Guardar.": "Editable: change it and press Save.",
    " margen(es) por guardar.": " margin(s) to save.",
    ":material/save: Guardar márgenes": ":material/save: Save margins",
    " margen(es) guardado(s).": " margin(s) saved.",
    " obra(s) sin movimiento (sin costo ni facturación)":
        " job(s) with no movement (no cost and no invoicing)",

    # ── resultado por proyecto / conciliación / P&L ────────────────
    "Costo = lo CARGADO a la obra (horas imputadas × tarifa + compras). Los aportes de "
    "ley y las horas sin imputar no son de ninguna obra en concreto: los cubre el margen "
    "(ver Conciliación).":
        "Cost = what is CHARGED to the job (hours charged × rate + purchases). Statutory "
        "contributions and unallocated hours do not belong to any one job: the margin "
        "covers them (see Reconciliation).",
    ":material/info: **De principio a fin de cada obra**, sin filtrar por periodo: es lo "
    "que un resumen por mes no puede decirte, porque la factura y sus costos caen en "
    "meses distintos.":
        ":material/info: **From start to finish of each job**, with no period filter: it "
        "is what a monthly summary cannot tell you, because the invoice and its costs "
        "fall in different months.",
    "Ninguna obra tiene facturación ni costo todavía.":
        "No job has any invoicing or cost yet.",
    "No se pudo calcular: ": "It could not be worked out: ",
    "Resultado acumulado de las obras: **": "Cumulative result across jobs: **",
    "No se pudo calcular la conciliación.": "The reconciliation could not be worked out.",
    ":material/warning: **": ":material/warning: **",
    " sin explicar** entre lo que deberías pagar y lo puesto en nóminas: trabajo aún sin "
    "nómina, o nóminas editadas a mano.":
        " unexplained** between what you should be paying and what is in the payslips: "
        "work not yet paid, or payslips edited by hand.",
    ":material/info: Con un periodo acotado la cadena **no cierra por construcción**: "
    "las horas cuentan por el día trabajado y las nóminas por el periodo que cierran, "
    "así que caen en meses distintos. Los ":
        ":material/info: With a narrow period the chain **cannot balance by "
        "construction**: hours count by the day worked and payslips by the period they "
        "close, so they fall in different months. The ",
    " de diferencia no son un descuadre — para conciliar de verdad, mira el periodo "
    "**Todo**.":
        " of difference is not a discrepancy — to reconcile properly, look at the "
        "**All** period.",
    "Tu margen tiene que cubrir los aportes de ley y las horas que pagas sin poder "
    "cargarlas a ninguna obra.":
        "Your margin has to cover the statutory contributions and the hours you pay for "
        "without being able to charge them to any job.",
    "Sin costos en este periodo.": "No costs in this period.",
    "Todo el costo del periodo es **": "All the cost in the period is **",
    "): no hay nada que repartir.": "): there is nothing to split.",
    "**Composición del costo**": "**Cost breakdown**",
    "Sin facturas en este periodo.": "No invoices in this period.",
    "**Facturado por cliente**": "**Invoiced by client**",
}
