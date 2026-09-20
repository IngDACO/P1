"""F3-L · projects_ui (3/4): detalle del proyecto — datos, actividades, cronograma,
diagnóstico de ritmo, historial, archivar/eliminar y la cartera.

⚠️ El diagnóstico de RITMO (v143/v324) está partido en muchos trozos de f-string que se
concatenan; se traducen uno a uno conservando el orden y los `**` del original, porque
la frase se arma sumando piezas y cualquier hueco deja media frase en español.
⚠️ «archivar» ≠ «eliminar»: v149 los separó a propósito y los textos lo dicen.
"""
TRAD = {
    # ── cartera ────────────────────────────────────────────────────
    "← Volver a la cartera": "← Back to the portfolio",
    "Los archivados no salen en listas ni informes; ábrelos desde aquí para "
    "restaurarlos.":
        "Archived ones do not appear in lists or reports; open them from here to restore "
        "them.",
    " proyecto(s) archivado(s) oculto(s).": " archived project(s) hidden.",
    "Todavía no hay proyectos en este grupo. Crea el primero aquí; después el Survey y "
    "las demás herramientas podrán alimentarlo.":
        "No projects in this company yet. Create the first one here; after that the "
        "Survey and the other tools can feed it.",
    "Buscar": "Search",
    "Buscar proyecto o cliente…": "Search project or client…",
    "Filtro": "Filter",
    "Vista": "View",
    "Ningún proyecto coincide con el filtro.": "No project matches the filter.",
    "Cada tarjeta muestra el resumen; toca «Abrir» para ver el detalle.":
        "Each card shows the summary; tap «Open» to see the detail.",

    # ── instrucciones e inducciones ────────────────────────────────
    ":material/push_pin: Instrucciones e inducciones del proyecto":
        ":material/push_pin: Project instructions and inductions",
    "**Instrucciones particulares**": "**Specific instructions**",
    "**Inducciones a diligenciar**": "**Inductions to complete**",
    ":material/send: Reenviar inducción a los asignados":
        ":material/send: Resend the induction to those assigned",
    ":material/send: Enviado a ": ":material/send: Sent to ",
    " usuario(s) de campo.": " field user(s).",

    # ── quién ha trabajado / historial ─────────────────────────────
    "**:material/groups: Quién ha trabajado aquí**":
        "**:material/groups: Who has worked here**",
    "Nadie ha fichado horas a este proyecto todavía.":
        "Nobody has clocked hours to this project yet.",
    "Total: **": "Total: **",
    ":material/history: Historial de cambios (": ":material/history: Change history (",
    "Se anotan los cambios que mueven dinero o el estado de la obra (margen, "
    "presupuesto, fechas, avance, cliente, personal).":
        "Changes that move money or the job's status are recorded (margin, budget, "
        "dates, progress, client, staff).",
    "&nbsp;&nbsp;&nbsp;&nbsp;": "&nbsp;&nbsp;&nbsp;&nbsp;",

    # ── estado / diagnóstico de ritmo ──────────────────────────────
    "Este proyecto no tiene actividades, así que no hay cronograma que seguir. Añádelas "
    "en :material/edit: Datos.":
        "This project has no activities, so there is no schedule to follow. Add them in "
        ":material/edit: Data.",
    "Debería ir": "Should be at",
    "Desvío": "Variance",
    "Situación": "Situation",
    "Fin proyectado": "Projected finish",
    ":material/schedule: La fecha de fin planificada ya pasó y queda **":
        ":material/schedule: The planned finish date has already passed and there is **",
    "%** por completar.": "%** still to complete.",
    ":material/schedule: **Sin avance todavía**: necesitas **":
        ":material/schedule: **No progress yet**: you need **",
    " %/día** en los ": " %/day** over the ",
    " días que quedan para llegar a la fecha.": " days left to make the date.",
    " %/día** y necesitas **": " %/day** and you need **",
    " %/día** para llegar a la fecha: hay que **acelerar ×":
        " %/day** to make the date: you have to **speed up ×",
    "** en los ": "** over the ",
    " días que quedan.": " days left.",
    " %/día** y con **": " %/day** and at **",
    " %/día** llegas: hay margen.": " %/day** you make it: there is room.",
    ":material/schedule: Vas a **": ":material/schedule: You are running at **",
    " %/día**, justo el ritmo que hace falta (": " %/day**, exactly the rate needed (",
    " %/día).": " %/day).",
    "**:material/checklist: Actividades**": "**:material/checklist: Activities**",
    "** — sin empezar, tocaba el ": "** — not started, it was due on ",
    ":green[:material/check_circle:] ": ":green[:material/check_circle:] ",
    "% · toca hoy": "% · due today",
    "Ninguna actividad abierta ni arrastrada.": "No open or overdue activity.",
    ":material/flag: Próximo hito: **": ":material/flag: Next milestone: **",
    "** arranca el ": "** starts on ",
    " días).": " days).",
    "**:material/calendar_month: Cronograma y avance**":
        "**:material/calendar_month: Schedule and progress**",
    "La **banda de color** entre las dos curvas es la brecha contra el plan (roja si vas "
    "por detrás, verde si por delante). ● rojo = la actividad ya debería haber arrancado.":
        "The **coloured band** between the two curves is the gap against the plan (red if "
        "you are behind, green if ahead). ● red = the activity should already have "
        "started.",
    ":material/receipt: Sin facturar: **": ":material/receipt: Not invoiced: **",
    ":material/receipt_long: Facturar": ":material/receipt_long: Invoice",
    "Nueva factura con esta obra y su cliente ya elegidos.":
        "New invoice with this job and its client already chosen.",

    # ── datos del proyecto ─────────────────────────────────────────
    "Sección del proyecto": "Project section",
    ":material/engineering: Usuarios de campo asignados":
        ":material/engineering: Field users assigned",
    ":material/badge: Certificados que exige el proyecto":
        ":material/badge: Certificates the project requires",
    "Al asignar personal se avisa y marca a quien no los cumpla.":
        "When staff are assigned, anyone who does not meet them is flagged.",
    ":material/wrong_location: **Esta obra no está en el mapa.** Tiene dirección (*":
        ":material/wrong_location: **This job is not on the map.** It has an address (*",
    "*) pero no un punto, así que no aparece en el mapa de Home ni en la Ruta del día. "
    "Ábrelo abajo y pulsa **Buscar** para ubicarla.":
        "*) but no point, so it does not appear on the Home map or in the Day route. Open "
        "it below and press **Search** to place it.",
    "Ubicación en el mapa (pin del proyecto)": "Location on the map (project pin)",
    ":material/contacts: Cliente": ":material/contacts: Client",
    "Elige un cliente de Contactos o escribe uno nuevo.":
        "Choose a client from Contacts or type a new one.",
    "Nombre del nuevo cliente": "New client's name",
    "**Datos del proyecto**": "**Project data**",
    "Tipo de proyecto": "Project type",
    "Solo «Instalación» usa el cronograma estándar de obra.":
        "Only «Installation» uses the standard job schedule.",
    "Ubicación": "Location",
    "Sale del pin del mapa (arriba). Muévelo o busca la dirección para cambiarla.":
        "It comes from the map pin (above). Move it or search the address to change it.",
    "Modelo": "Model",
    "Ingeniero": "Engineer",
    "Fecha inicio": "Start date",
    "Fecha fin estimada": "Estimated finish date",
    ":material/push_pin: Instrucciones particulares":
        ":material/push_pin: Specific instructions",
    ":material/description: Inducciones (un link por línea)":
        ":material/description: Inductions (one link per line)",
    "Al asignar un usuario de campo se le envían por Telegram/email.":
        "They are sent by Telegram/email when a field user is assigned.",
    "Agrupación": "Group of lifts",
    "Peso en la agrupación": "Weight in the group",
    "Cuánto pesa este elevador en el avance consolidado de su agrupación.":
        "How much this lift weighs in its group's consolidated progress.",
    "Estado manual (override)": "Manual status (override)",
    ":material/payments: Presupuesto del proyecto (0 = sin presupuesto)":
        ":material/payments: Project budget (0 = no budget)",
    ":material/trending_up: Margen sobre mano de obra (%) — lo que cobras al cliente":
        ":material/trending_up: Margin on labour (%) — what you charge the client",
    "Venta de la MO = costo × (1+margen). Default del grupo: ":
        "Labour sell price = cost × (1+margin). Company default: ",
    "% (lo fija el propietario en Grupos).": "% (the owner sets it in Companies).",
    ":material/save: Guardar cambios": ":material/save: Save changes",

    # ── actividades ────────────────────────────────────────────────
    "**Actividades del cronograma** — tabla editable · el avance lo pone el campo":
        "**Schedule activities** — editable table · progress is set by the field team",
    "Orden": "Order",
    "Cambia el número para reordenar": "Change the number to reorder",
    "Días": "Days",
    "Peso": "Weight",
    "Peso relativo (el % se calcula proporcional)":
        "Relative weight (the % is worked out proportionally)",
    "Edita nombre, días, peso y el orden; el avance % es de solo lectura (lo actualiza "
    "el campo).":
        "Edit name, days, weight and order; the progress % is read-only (the field team "
        "updates it).",
    ":material/save: Guardar tabla de actividades": ":material/save: Save activity table",
    "Sin actividades registradas.": "No activities recorded.",
    "Agregar / eliminar actividad (recalcula el % automáticamente)":
        "Add / delete activity (the % is recalculated automatically)",
    "**:material/add: Agregar actividad**": "**:material/add: Add activity**",
    "Nombre": "Name",
    "Duración (días)": "Duration (days)",
    "Peso (relativo a las demás)": "Weight (relative to the others)",
    "Agregar": "Add",
    "**:material/delete: Eliminar actividad**": "**:material/delete: Delete activity**",
    "Actividad a eliminar": "Activity to delete",
    "Confirmo eliminar esta actividad": "I confirm I want to delete this activity",
    "Eliminar": "Delete",

    # ── archivar / eliminar ────────────────────────────────────────
    ":material/inventory_2: Este proyecto está **archivado**: no aparece en las listas ni "
    "en los informes, pero no se ha perdido nada.":
        ":material/inventory_2: This project is **archived**: it does not appear in lists "
        "or reports, but nothing has been lost.",
    ":material/recycling: Restaurar proyecto": ":material/recycling: Restore project",
    ":material/inventory_2: Archivar proyecto": ":material/inventory_2: Archive project",
    "Desaparece de las listas y de los informes, pero se conserva entero y puede "
    "restaurarse cuando quieras. Es lo recomendado al cerrar una obra.":
        "It disappears from lists and reports, but is kept in full and can be restored "
        "whenever you want. This is what is recommended when a job closes.",
    ":material/inventory_2: Archivar": ":material/inventory_2: Archive",
    ":material/delete_forever: Eliminar definitivamente (irreversible)":
        ":material/delete_forever: Delete permanently (irreversible)",
    "Se borrarán el proyecto y sus actividades. **No se puede deshacer.** Casi siempre lo "
    "que quieres es archivarlo.":
        "The project and its activities will be deleted. **This cannot be undone.** "
        "Almost always what you want is to archive it.",
    "Esas filas y sus archivos en Drive NO se borran: quedan apuntando a un proyecto que "
    "ya no existe.":
        "Those rows and their files in Drive are NOT deleted: they end up pointing at a "
        "project that no longer exists.",
    "Escribe «": "Type «",
    "» para confirmar": "» to confirm",
    "Eliminar definitivamente": "Delete permanently",

    # ── reconstruir en el Survey ───────────────────────────────────
    ":material/sync: Reconstruir proyecto en el Survey (regenerar informes)":
        ":material/sync: Rebuild the project in the Survey (regenerate reports)",
    "Carga los parámetros y la matriz guardados en la pestaña :material/architecture: "
    "Survey. Luego pulsa **Calcular** allí para regenerar diagramas e informes.":
        "Loads the saved parameters and matrix into the :material/architecture: Survey "
        "tab. Then press **Calculate** there to regenerate diagrams and reports.",
    ":material/sync: Cargar este proyecto en el Survey":
        ":material/sync: Load this project into the Survey",
    "Este proyecto no tiene parámetros guardados.":
        "This project has no saved parameters.",
    ":material/check_circle: Cargado. Ve a **:material/architecture: Survey** y pulsa "
    "**Calcular** para regenerar todo.":
        ":material/check_circle: Loaded. Go to **:material/architecture: Survey** and "
        "press **Calculate** to regenerate everything.",
}
