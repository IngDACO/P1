"""F3-M · projects_ui (4/4): lista de proyectos, notificación de asignados,
crear proyecto (con lectura del plano), archivos, resumen del día y alarmas.

⚠️ Se conservan las SIGLAS del plano: NS (number of stops), PRODUCT LINE, y los nombres
de las 5 herramientas técnicas. Y las CLAVES de las columnas de la lista (`Ppto`, etc.)
se traducen solo donde son etiqueta, no donde indexan el dataframe.
"""
TRAD = {
    # ── columnas y ayudas de la lista ──────────────────────────────
    "Avance": "Progress",
    "Sin facturar": "Not invoiced",
    "Ingreso estimado de la obra menos lo ya facturado. Se factura desde la tarjeta o "
    "desde la propia obra.":
        "The job's estimated revenue minus what has already been invoiced. You invoice "
        "from the card or from the job itself.",
    "Ritmo": "Pace",
    "Días de retraso o de adelanto respecto al plan.":
        "Days behind or ahead of the plan.",
    "Avisos": "Alerts",
    "Alarmas abiertas de la obra.": "Open alerts on the job.",
    "Equipo": "Team",
    "Personas de campo asignadas.": "Field staff assigned.",
    ":material/receipt: **": ":material/receipt: **",
    "** sin facturar en ": "** not invoiced across ",
    " obra(s) de las que se ven.": " of the jobs shown.",
    ":material/touch_app: Toca una fila y elige qué hacer con ella.  Ppto = % del "
    "presupuesto ejecutado (:orange[:material/warning:] si se pasó) y over = sobre "
    "presupuesto.":
        ":material/touch_app: Tap a row and choose what to do with it.  Budget = % of "
        "the budget used (:orange[:material/warning:] if it went over) and over = over "
        "budget.",
    "Nueva factura con esta obra y su cliente ya elegidos · pendiente ":
        "New invoice with this job and its client already chosen · outstanding ",

    # ── avisos al asignar ──────────────────────────────────────────
    "**:material/verified_user: Cumplimiento de certificados del equipo**":
        "**:material/verified_user: Team certificate compliance**",
    "Sin usuarios de campo asignados todavía.": "No field users assigned yet.",
    ":green[:material/check_circle:] vigente · :orange[:material/schedule:] por vencer "
    "(renovar) · :red[:material/cancel:] vencido · — falta.  **Cumple** = ningún "
    "certificado requerido vencido ni faltante.":
        ":green[:material/check_circle:] valid · :orange[:material/schedule:] expiring "
        "(renew) · :red[:material/cancel:] expired · — missing.  **Compliant** = no "
        "required certificate expired or missing.",
    ":material/mail: Sin canales de aviso configurados (Gmail / Telegram).":
        ":material/mail: No notification channels configured (Gmail / Telegram).",
    " usuario(s) de campo notificado(s).": " field user(s) notified.",
    ":material/mail: Notificados ": ":material/mail: Notified ",
    ". Al resto le falta contacto.": ". The rest have no contact details.",
    ":material/warning: No se pudo notificar a nadie: revisa email y Telegram en "
    ":material/build: Mi grupo → Usuarios.":
        ":material/warning: Nobody could be notified: check email and Telegram in "
        ":material/build: My company → Users.",

    # ── crear proyecto ─────────────────────────────────────────────
    "Nuevo proyecto": "New project",
    "**:material/description: Plano del elevador** — opcional, pero recomendado":
        "**:material/description: Lift drawing** — optional, but recommended",
    "Se leen los datos del plano una sola vez y quedan en el proyecto: el equipo de campo "
    "ya no tendrá que cargar el PDF en ninguna herramienta.":
        "The drawing is read once and its data stays with the project: the field team "
        "will no longer have to upload the PDF in any tool.",
    "PDF del plano": "Drawing PDF",
    "Leyendo el plano…": "Reading the drawing…",
    "Leyendo el plano… ": "Reading the drawing… ",
    "No se pudo leer el plano: ": "The drawing could not be read: ",
    ":material/check_circle: Plano leído — alimenta tus **5 herramientas técnicas**:":
        ":material/check_circle: Drawing read — it feeds your **5 technical tools**:",
    "**:material/map: Ubicación en el mapa** — opcional, fija el pin del proyecto":
        "**:material/map: Location on the map** — optional, drops the project pin",
    ":material/category: Tipo de proyecto": ":material/category: Project type",
    "Solo «Instalación» genera el cronograma estándar de obra (11 actividades que "
    "escalan con el NS).":
        "Only «Installation» generates the standard job schedule (11 activities that "
        "scale with NS).",
    ":material/place: Ubicación que se guardará: **":
        ":material/place: Location that will be saved: **",
    "Nombre del proyecto *": "Project name *",
    "Ingeniero responsable": "Engineer in charge",
    "Fecha de inicio": "Start date",
    "Número de paradas (NS) *": "Number of stops (NS) *",
    ":material/event_available: Fin estimado: **":
        ":material/event_available: Estimated finish: **",
    " días) — del NS y las actividades estándar.":
        " days) — from the NS and the standard activities.",
    "Fecha de fin estimada": "Estimated finish date",
    "Este tipo de proyecto no tiene cronograma estándar, así que la fecha la pones tú.":
        "This project type has no standard schedule, so you set the date yourself.",
    ":material/payments: Presupuesto (0 = sin presupuesto)":
        ":material/payments: Budget (0 = no budget)",
    "Modelo de elevador": "Lift model",
    "Prellenado del plano (PRODUCT LINE), si se leyó. Editable.":
        "Prefilled from the drawing (PRODUCT LINE), if it was read. Editable.",
    "Indicaciones específicas para el equipo…": "Specific instructions for the team…",
    "Se envían por Telegram/email a los asignados.":
        "They are sent by Telegram/email to those assigned.",
    ":material/add_circle: Crear proyecto": ":material/add_circle: Create project",
    "El nombre del proyecto es obligatorio.": "The project name is required.",
    "Crear aunque el nombre se repita": "Create even though the name is repeated",
    "El proyecto se creó, pero no se guardaron los datos del plano: ":
        "The project was created, but the drawing data was not saved: ",
    ":material/attach_file: El plano no se pudo archivar en Drive.":
        ":material/attach_file: The drawing could not be filed in Drive.",

    # ── datos del plano ────────────────────────────────────────────
    ":material/upload: Cargar / actualizar el plano del proyecto":
        ":material/upload: Upload / update the project drawing",
    "Sube el PDF y se extraen sus datos para que las herramientas los usen sin volver a "
    "pedir el plano. Tarda ~1 min.":
        "Upload the PDF and its data is extracted so the tools can use it without asking "
        "for the drawing again. It takes about 1 min.",
    ":material/info: Los datos del plano quedaron guardados, pero **el PDF no se pudo "
    "archivar** en Drive.":
        ":material/info: The drawing data was saved, but **the PDF could not be filed** "
        "in Drive.",
    ":material/check_circle: Plano cargado — alimenta tus 5 herramientas técnicas.":
        ":material/check_circle: Drawing uploaded — it feeds your 5 technical tools.",
    "**:material/description: Datos del plano**": "**:material/description: Drawing data**",
    "Este proyecto no tiene datos de plano guardados, así que las herramientas le pedirán "
    "el PDF a quien las use. Cárgalo aquí una vez y dejarán de pedirlo.":
        "This project has no saved drawing data, so the tools will ask whoever uses them "
        "for the PDF. Upload it here once and they will stop asking.",
    "Un solo plano alimenta **tus 5 herramientas técnicas** — todas por igual:":
        "A single drawing feeds **your 5 technical tools** — all of them equally:",
    ":material/check_circle: El plano dio todo lo que las herramientas necesitan.":
        ":material/check_circle: The drawing gave everything the tools need.",
    "Ver los ": "See the ",
    " parámetros del plano": " drawing parameters",

    # ── fotos y archivos ───────────────────────────────────────────
    "**:material/photo_camera: Fotos de obra** — ":
        "**:material/photo_camera: Site photos** — ",
    ":material/broken_image: no disponible": ":material/broken_image: not available",
    "Ver ": "See ",
    " más (": " more (",
    " restantes)": " left)",
    "**:material/folder: Archivos**": "**:material/folder: Files**",
    ":material/lock: Almacenamiento en Drive no configurado (faltan los secrets "
    "`[gdrive]`).":
        ":material/lock: Drive storage is not configured (the `[gdrive]` secrets are "
        "missing).",
    "Sin archivos todavía.": "No files yet.",
    ":material/search: Buscar": ":material/search: Search",
    "nombre, tipo…": "name, type…",
    "Mostrando **": "Showing **",
    " archivos.": " files.",
    ":material/touch_app: Toca una fila para descargar o reabrir ese archivo.":
        ":material/touch_app: Tap a row to download or reopen that file.",
    "Ningún archivo coincide con el filtro.": "No file matches the filter.",
    "No se pudo descargar: ": "It could not be downloaded: ",
    ":material/replay: Reabrir en la herramienta": ":material/replay: Reopen in the tool",
    "Este cálculo no guardó sus entradas (es anterior a v148).":
        "This calculation did not save its inputs (it predates v148).",
    ":material/delete: Borrar": ":material/delete: Delete",
    "Este cálculo no tiene PDF archivado ni entradas para reabrir.":
        "This calculation has no filed PDF and no inputs to reopen.",
    "Subir documento": "Upload document",
    "Como usuario de campo, solo puedes subir **fotos**.":
        "As a field user you can only upload **photos**.",
    "Archivo": "File",
    "Subir": "Upload",
    "Elige un archivo primero.": "Choose a file first.",
    "Documento subido.": "Document uploaded.",
    "No se pudo subir: ": "It could not be uploaded: ",

    # ── resumen del día ────────────────────────────────────────────
    ":material/folder: Activos\n\n": ":material/folder: Active\n\n",
    ":material/trending_up: Avance\n\n": ":material/trending_up: Progress\n\n",
    ":material/schedule: Horas\n\n": ":material/schedule: Hours\n\n",
    "Ver el detalle e ir a ": "See the detail and go to ",
    " a resolverlo": " and sort it out",
    "Sin pendientes aquí. :green[:material/check_circle:]":
        "Nothing pending here. :green[:material/check_circle:]",
    ":material/forum: Lectura del asistente (IA)":
        ":material/forum: The assistant's read (AI)",
    ":material/refresh: Actualizar": ":material/refresh: Refresh",
    ":material/send: Enviármelo": ":material/send: Send it to me",
    ":material/send: Resumen enviado.": ":material/send: Summary sent.",
    "No tienes email/Telegram configurado en tu usuario.":
        "Your user has no email/Telegram configured.",
    "No se pudo enviar: ": "It could not be sent: ",
    "El asistente redacta el estado del grupo en pocas frases, con una recomendación.":
        "The assistant writes the company's status in a few sentences, with a "
        "recommendation.",
    "✨ Generar lectura": "✨ Generate the read",

    # ── alarmas ────────────────────────────────────────────────────
    " Alarmas / avisos**": " Alerts**",
    "Marcar resuelta": "Mark as resolved",
    "Sin alarmas abiertas.": "No open alerts.",
    ":material/report: Reportar un problema al administrador":
        ":material/report: Report a problem to the administrator",
    "Describe el problema o inconveniente en obra":
        "Describe the problem or issue on site",
    "Enviar alarma": "Send alert",
    "Escribe el problema.": "Describe the problem.",
}
