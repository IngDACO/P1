# -*- coding: utf-8 -*-
"""F2 — la app de CAMPO: fichaje, pre-start, ausencias y ruta del día.

Se conservan tal cual los `:material/…:`, el markdown (`**`, `:red[…]`) y los saltos:
solo cambian las palabras. Las claves de datos NO están aquí.
"""
TRAD = {
    # ── timeclock_ui ──
    ":material/lock: Tus fichajes son privados. La administración ve el resumen de horas del grupo, no el detalle de cada persona.":
        ":material/lock: Your time entries are private. Management sees the group's hours summary, not each person's detail.",
    ":material/account_tree: Tus últimos fichajes": ":material/account_tree: Your latest time entries",
    ":material/check_circle: Fichar al proyecto": ":material/check_circle: Clock in to the project",
    "¿En qué proyecto vas a trabajar?": "Which project are you working on?",
    "O elige otro proyecto abajo.": "Or pick another project below.",
    " (tu asignación de hoy)": " (your assignment for today)",
    "No tienes proyectos asignados; se muestran los de tu grupo.":
        "You have no projects assigned; your group's projects are shown.",
    "No hay proyectos disponibles para fichar. Pídele al administrador que te asigne uno.":
        "No projects available to clock in to. Ask your administrator to assign you one.",
    "Cambiar de proyecto": "Switch project",
    ":material/cancel: Salir del proyecto": ":material/cancel: Leave the project",
    "Estás en **": "You are on **",
    "#### :material/apartment: Proyecto": "#### :material/apartment: Project",
    "La jornada es tu tiempo de trabajo del día. Se abre sola al fichar a un proyecto, o puedes abrirla aquí.":
        "The workday is your working time for the day. It opens by itself when you clock in to a project, or you can open it here.",
    ":material/cancel: Cerrar la jornada": ":material/cancel: Close the workday",
    ":material/warning: El fichaje aún no está conectado a Google Sheets. Configura los Secrets.":
        ":material/warning: Time tracking is not connected to Google Sheets yet. Configure the Secrets.",
    "Sesión cerrada a la hora indicada.": "Session closed at the time given.",
    ":material/cancel: Cerrar sesión olvidada": ":material/cancel: Close forgotten session",
    ":orange[:material/warning:] La hora de fin debe estar entre la entrada y ahora.":
        ":orange[:material/warning:] The finish time must be between the clock-in and now.",
    "Día que terminaste": "Day you finished",
    "Proyecto": "Project",
    "Tu asignación de hoy. ¿Otra obra?": "Your assignment for today. A different site?",
    "###### :material/schedule: FICHAJE EN CURSO": "###### :material/schedule: CLOCKED IN",
    ":material/warning: Falta el **Pre-Start** de hoy en esta obra.":
        ":material/warning: Today's **Pre-Start** is missing on this site.",
    ":material/draw: Firma el **Pre-Start** de hoy de esta obra.":
        ":material/draw: Sign today's **Pre-Start** for this site.",
    "Ahora no": "Not now",
    "**. La charla de seguridad de hoy ya está registrada, pero **tú no constas entre quienes la firmaron**.":
        "**. Today's safety talk is already recorded, but **you are not among those who signed it**.",
    "Acabas de fichar a **": "You have just clocked in to **",
    ":material/draw: Firma el Pre-Start de hoy": ":material/draw: Sign today's Pre-Start",
    "Es la charla de seguridad antes de empezar: una por obra y día. Si ya la hicisteis, regístrala para que quede el PDF firmado.":
        "It is the safety talk before starting: one per site per day. If you have already held it, record it so the signed PDF exists.",
    "** y hoy todavía **no hay Pre-Start** registrado en esa obra.":
        "** and there is still **no Pre-Start** recorded on that site today.",
    ":material/health_and_safety: Falta el Pre-Start de hoy": ":material/health_and_safety: Today's Pre-Start is missing",

    # ── prestart_ui ──
    "PDF no disponible": "PDF not available",
    "Aún no hay pre-starts registrados en este proyecto.": "No pre-starts recorded on this project yet.",
    ":orange[:material/warning:] No se pudo abrir la alarma de los checks en NO; avisa al administrador.":
        ":orange[:material/warning:] The alert for the NO checks could not be opened; tell your administrator.",
    " control(es) en NO. El administrador queda avisado.": " control(s) answered NO. The administrator has been notified.",
    ":material/cancel: Se abrió una alarma del proyecto por ": ":material/cancel: A project alert was opened for ",
    ":material/cancel: Se abrió una alarma del proyecto por el near miss/hazard reportado.":
        ":material/cancel: A project alert was opened for the near miss/hazard reported.",
    ":orange[:material/warning:] No se archivó en Drive (revisa la conexión); el registro sí quedó guardado.":
        ":orange[:material/warning:] It was not filed to Drive (check the connection); the record was saved.",
    ":material/attach_file: Archivado en los documentos del proyecto.": ":material/attach_file: Filed in the project documents.",
    "** guardado como `": "** saved as `",
    ":material/health_and_safety: Generar y archivar Pre-Start": ":material/health_and_safety: Generate and file Pre-Start",
    "Hubo una SEGUNDA charla hoy (otro turno u otra cuadrilla): regístrala igual":
        "There was a SECOND talk today (another shift or crew): record it anyway",
    ":material/warning: **Esta obra ya tiene el Pre-Start de hoy.** Solo hace falta otro si hubo una segunda charla de verdad.":
        ":material/warning: **This site already has today's Pre-Start.** Another one is only needed if there really was a second talk.",
    ":material/warning: **Esta obra ya tiene el Pre-Start de hoy y tú ya constas en él.** Solo hace falta otro si hubo una segunda charla de verdad.":
        ":material/warning: **This site already has today's Pre-Start and you are already on it.** Another one is only needed if there really was a second talk.",
    ":material/warning: **Esta obra ya tiene el Pre-Start de hoy.** Si solo faltas tú por constar, fírmalo arriba en vez de crear otro.":
        ":material/warning: **This site already has today's Pre-Start.** If you are the only one missing from it, sign it above instead of creating another.",
    ":red[:material/cancel:] Marcaste YES: describe el near miss/hazard (abrirá una alarma del proyecto).":
        ":red[:material/cancel:] You answered YES: describe the near miss/hazard (it will open a project alert).",
    "Si marcas YES arriba, esta descripción abre una alarma del proyecto.":
        "If you answer YES above, this description opens a project alert.",
    "Describe el issue / hazard / near miss (opcional)": "Describe the issue / hazard / near miss (optional)",
    "Notas de actividades / SWMS": "Activity notes / SWMS",
    "Responde cada punto: es una revisión de seguridad, no una firma.":
        "Answer every item: this is a safety review, not a signature.",
    "Elige el proyecto en el que vas a trabajar hoy.": "Pick the project you are working on today.",
    ":material/schedule: Es el proyecto donde fichaste hoy. Cámbialo si el pre-start es de otro.":
        ":material/schedule: This is the project you clocked in to today. Change it if the pre-start is for another one.",
    "Registro de la charla de seguridad antes de empezar en obra. Genera el PDF, lo archiva en el proyecto y abre una alarma si hay near miss/hazard o si algún control queda en NO.":
        "Record of the safety talk before starting on site. It generates the PDF, files it in the project and opens an alert if there is a near miss/hazard or any control is answered NO.",
    " como hoja de anexo, sin tocar el documento original.": " as an annex sheet, without touching the original document.",
    "Firmado. Se añadió tu firma al ": "Signed. Your signature was added to the ",
    "Pon al menos tus iniciales.": "Enter at least your initials.",
    "Dibuja tu firma antes de enviarla.": "Draw your signature before sending it.",
    ":material/draw: Firmar el Pre-Start": ":material/draw: Sign the Pre-Start",
    "Sin lienzo disponible: se registran las iniciales tecleadas.":
        "No canvas available: the typed initials are recorded instead.",
    "Firma aquí": "Sign here",
    " charlas** registradas en esta obra. Se te ofrece la más reciente; si firmaste otra, díselo a quien la registró.":
        " talks** recorded on this site. The most recent one is offered; if you signed a different one, tell whoever recorded it.",
    ":material/info: Hoy hay **": ":material/info: Today there are **",
    ":material/draw: **Esta obra ya tiene el Pre-Start de hoy — fírmalo**":
        ":material/draw: **This site already has today's Pre-Start — sign it**",
    ":orange[Elige al menos a una persona para poder firmar.]":
        ":orange[Pick at least one person so it can be signed.]",
    "Quitar el último": "Remove the last one",
    "Añadir": "Add",
    "Nombre y apellido": "First and last name",
    ":material/person_add: ¿Falta alguien que no está en la lista?":
        ":material/person_add: Is someone missing who is not on the list?",
    ":material/info: Esta obra no tiene a nadie asignado ni fichado hoy; añade abajo a quien asista.":
        ":material/info: This site has nobody assigned or clocked in today; add below whoever attends.",
    "Salen los asignados a la obra y los que han fichado hoy en ella.":
        "This lists the people assigned to the site and those who clocked in there today.",
    "¿Quiénes asisten a la charla?": "Who is attending the talk?",
    ":material/warning: El lienzo de firma no está disponible en este despliegue; se registran las iniciales tecleadas.":
        ":material/warning: The signature canvas is not available in this deployment; the typed initials are recorded instead.",

    # ── ausencias_ui ──
    "Se le mostrará a la persona": "This will be shown to the person",
    ":material/check: No tiene obras asignadas esos días.": ":material/check: They have no sites assigned on those days.",
    ":material/block: nadie libre ese día.": ":material/block: nobody free that day.",
    " día(s))": " day(s))",
    "Quién podría cubrirlo (": "Who could cover it (",
    "Sin ausencias registradas.": "No absences recorded.",
    "Histórico (": "History (",
    ":material/check_circle: No hay solicitudes pendientes.": ":material/check_circle: No pending requests.",
    "#### :material/inbox: Pendientes de aprobar": "#### :material/inbox: Waiting for approval",
    ":material/warning: Las ausencias necesitan Google Sheets configurado.":
        ":material/warning: Absences need Google Sheets configured.",
    "Todavía no has pedido ninguna ausencia.": "You have not requested any absence yet.",
    " día(s)** y te quedan **": " day(s)** and you have **",
    "Viaje familiar, cita médica…": "Family trip, medical appointment…",
    "Márcalo solo si en esos días se trabaja. Si no, no se te descuentan del saldo.":
        "Tick this only if those days are worked. Otherwise they are not taken off your balance.",
    "Incluir fines de semana": "Include weekends",
    "Hasta": "To",
    "Desde": "From",
    " este año.": " this year.",
    " día(s)** de ": " day(s)** of ",
    ":material/warning: Te quedan solo **": ":material/warning: You have only **",
    "). Habla con tu responsable.": "). Talk to your manager.",
    " de ": " of ",
    " este año (usados ": " this year (used ",
    ":material/block: No te quedan días de ": ":material/block: You have no days left of ",
    ":material/info: Una baja por enfermedad **se registra al momento**: no tienes que esperar a que nadie la apruebe. Tu responsable la verá en cuanto la envíes.":
        ":material/info: Sick leave **is recorded straight away**: you do not have to wait for anyone to approve it. Your manager will see it as soon as you send it.",
    "¿Qué necesitas?": "What do you need?",
    "Pedir un día libre, vacaciones o avisar de una baja":
        "Request a day off or annual leave, or report sick leave",
    "**) porque no consta tu fecha de alta. Pídele a tu responsable que la cargue y el saldo pasará a contar desde tu aniversario.":
        "**) because your start date is not on record. Ask your manager to enter it and the balance will count from your anniversary.",
    ":material/help: Contamos por año natural (**": ":material/help: We are counting by calendar year (**",
    "** (desde que entraste, el ": "** (since you started, on ",
    "** al **": "** to **",
    ":material/event_available: Tu año de vacaciones va del **": ":material/event_available: Your leave year runs from **",

    # ── route_ui ──
    ":material/info: «Estado» compara la planificación con el fichaje real de ese día.":
        ":material/info: 'Status' compares the plan against the actual clock-ins for that day.",
    "**Quién va a dónde**": "**Who goes where**",
    "Abrir la ruta completa en Google Maps": "Open the full route in Google Maps",
    "Cómo llegar": "Directions",
    "**Sitios de hoy** — en orden de recorrido": "**Today's sites** — in travel order",
    "Nadie tiene una obra con ubicación asignada para ese día.":
        "Nobody has a site with a location assigned for that day.",
    ":material/help: Sin plan\n\n": ":material/help: No plan\n\n",
    "\n\nde ": "\n\nof ",
    ":material/engineering: En obra\n\n": ":material/engineering: On site\n\n",
    "No hay usuarios de campo en el grupo.": "There are no field users in the group.",
    ". La semana normal es de lunes a viernes; el fin de semana se añade desde el Panel.":
        ". The normal week is Monday to Friday; the weekend is added from the Panel.",
    ":material/weekend: No hay nada planificado para este ": ":material/weekend: Nothing is planned for this ",
    "Día siguiente": "Next day",
    "Día anterior": "Previous day",
    "A dónde va cada persona de campo según la planificación.":
        "Where each field member is going according to the plan.",
    "Día": "Day",
    "La navegación paso a paso la abre Google Maps desde tu ubicación actual, pasando por todas las obras en este orden.":
        "Turn-by-turn navigation opens in Google Maps from your current location, going through every site in this order.",
    "Abrir la ruta en Google Maps": "Open the route in Google Maps",
    "**Orden sugerido** (de la más cercana a la más lejana):":
        "**Suggested order** (nearest to farthest):",
    "Ninguna de tus obras tiene ubicación en el mapa todavía. Pídele al administrador que la fije en el proyecto.":
        "None of your sites has a map location yet. Ask your administrator to set it on the project.",
    "No tienes obras activas asignadas.": "You have no active sites assigned.",
}
