"""F3-G · Planificación (tablero de cuadrilla) — diccionario ES→EN.

⚠️ Vocabulario del módulo, fijado para que las tres vistas hablen igual:
    tablero → board · día → day · disponibilidad → availability
    choque de turno → shift clash · franja horaria → time slot
    trabajo (del catálogo) → job · asignación → assignment · libre → free
⚠️ NO se traducen los ESTADOS del roster (`roster.ESTADOS`: OFF/LEAVE/FORMACION) ni los
IDs `TRB-####`/`PRJ-####`: se guardan en `DatosJSON` y se comparan por su valor.
"""
TRAD = {
    "La planificación necesita Google Sheets configurado.":
        "Planning needs Google Sheets configured.",
    "Aún no tienes personal de campo. Créalo en :material/build: Usuarios de campo.":
        "You have no field staff yet. Create them in :material/build: Field users.",
    "vista": "view",
    "**Tablero**: la semana entera, y se asigna tocando una celda.  ·  **Día**: la "
    "cuadrilla sobre un reloj, para ver a qué hora está cada uno y dónde quedan huecos."
    "  ·  **Disponibilidad**: quién está libre.":
        "**Board**: the whole week, assign by tapping a cell.  ·  **Day**: the crew on "
        "a clock, to see what time each person is on and where the gaps are.  ·  "
        "**Availability**: who is free.",
    ":material/assignment: Copiar semana anterior":
        ":material/assignment: Copy previous week",
    "¿Quién está libre el…?": "Who is free on…?",
    ":material/warning: Nadie libre el ": ":material/warning: Nobody free on ",
    "Verde = libre · gris = ocupado (con su franja horaria).":
        "Green = free · grey = busy (with its time slot).",
    "Necesita el fichaje configurado.": "This needs the time clock configured.",
    "Día": "Day",
    ":green[:material/sensors:] **": ":green[:material/sensors:] **",
    "** fichados ahora · ": "** clocked in right now · ",
    " en un proyecto": " on a project",
    ":material/sensors: Nadie fichado en este momento.":
        ":material/sensors: Nobody is clocked in right now.",
    ":green[:material/check_circle:] ": ":green[:material/check_circle:] ",
    " donde tocaba  ·  :red[:material/cancel:] ": " where they were due  ·  :red[:material/cancel:] ",
    " en otro sitio  ·  :orange[:material/warning:] ": " somewhere else  ·  :orange[:material/warning:] ",
    " sin fichar": " not clocked in",
    "Nada que comparar este día (sin asignaciones a proyecto ni fichajes).":
        "Nothing to compare on this day (no project assignments and no time entries).",
    "Cumple los certificados del proyecto: ":
        "Meets the certificates required by the project: ",
    ":material/warning: No cumple todos los certificados: ":
        ":material/warning: Does not meet all the certificates: ",
    "'>Persona</div>": "'>Person</div>",
    "Ver ficha rápida de la persona": "Quick view of this person",
    ":material/timeline: Ver el día": ":material/timeline: View the day",
    "Asignaciones del día (puedes elegir varias)":
        "Assignments for the day (you can pick several)",
    " · inicio": " · start",
    " · fin": " · end",
    "Nota (para todo el día)": "Note (for the whole day)",
    "vehículo, equipo…": "vehicle, equipment…",
    "Toda la semana (": "The whole week (",
    "Aplicar a estos días": "Apply to these days",
    ":material/content_copy: Se guardará igual en **":
        ":material/content_copy: It will be saved the same on **",
    " días**.": " days**.",
    ":material/save: Guardar": ":material/save: Save",
    "Para trabajos que **no** son un proyecto: entregas, cursos, policía, traslados… Los "
    "**proyectos se asignan directo** en el tablero (ya son un trabajo en sí mismos), no "
    "hace falta crearlos aquí.":
        "For work that is **not** a project: deliveries, courses, traffic control, "
        "transfers… **Projects are assigned directly** on the board (they are a job in "
        "themselves), there is no need to create them here.",
    ":material/edit: Editar": ":material/edit: Edit",
    ":material/save: Guardar cambios": ":material/save: Save changes",
    ":material/history: Está en **": ":material/history: It is used in **",
    ": al eliminarlo sale del catálogo, pero **el histórico se conserva** tal cual.":
        ": deleting it takes it out of the catalogue, but **the history is kept** as it is.",
    "Confirmo eliminarlo": "I confirm I want to delete it",
    ":material/delete: Eliminar": ":material/delete: Delete",
    "Aún no hay trabajos. Añade el primero abajo.":
        "No jobs yet. Add the first one below.",
    "**:material/add: Nuevo trabajo** (no-proyecto)":
        "**:material/add: New job** (non-project)",
    "Número": "Number",
    "Nombre": "Name",
    "Entrega / Curso / Traslado…": "Delivery / Course / Transfer…",
    "Color": "Colour",
    "Crear trabajo": "Create job",
    "El nombre es obligatorio.": "The name is required.",
    # KPIs del panel
    "Fichados ahora": "Clocked in now",
    "Libres hoy": "Free today",
    "sin huecos": "no gaps",
    "hoy no está en la vista": "today is not in this view",
    "Choques de turno": "Shift clashes",
    "franjas que se solapan": "overlapping time slots",
    "Certs que bloquean": "Blocking certs",
    "asignado sin cumplir": "assigned without meeting them",
    "Sin choques de turno ni certificados que bloqueen esta semana.":
        "No shift clashes and no blocking certificates this week.",
    "**:orange[:material/warning:] Choques de turno:**":
        "**:orange[:material/warning:] Shift clashes:**",
    "**:red[:material/block:] Certificados que bloquean:**":
        "**:red[:material/block:] Blocking certificates:**",
    ":material/today: **Hoy:** ": ":material/today: **Today:** ",
    ":material/today: Hoy: sin asignación": ":material/today: Today: no assignment",
    "→ Ver ficha completa": "→ See full record",
    # asignación inteligente
    "No hay proyectos activos para asignar.": "There are no active projects to assign.",
    "Proyecto": "Project",
    "Inicio": "Start",
    "Fin": "End",
    "Sugeridos (libres) — elige a quién asignar:":
        "Suggested (free) — choose who to assign:",
    ":material/check: Asignar ": ":material/check: Assign ",
    "Asignados ": "Assigned ",
    # vista por día
    "Este día está sin asignar.": "Nothing is assigned on this day.",
    ":material/warning: **Se pisan en la misma franja:** ":
        ":material/warning: **They overlap in the same slot:** ",
    ". Suman **": ". They add up to **",
    " h asignadas** sobre **": " h assigned** over **",
    " h de día**, así que ese rato se está cargando a dos obras: o es un día partido que "
    "falta detallar, o alguien está contado dos veces.":
        " h of day**, so that time is being charged to two sites: either it is a split "
        "day that needs detailing, or someone is counted twice.",
    ":material/close: Cerrar": ":material/close: Close",
    " con asignación · ": " with an assignment · ",
    " libres</div>": " free</div>",
    "Nadie tiene franja horaria este día, así que no hay nada que situar en el reloj. "
    "Las asignaciones sin hora se listan abajo como «todo el día».":
        "Nobody has a time slot on this day, so there is nothing to place on the clock. "
        "Assignments with no time are listed below as «all day».",
    "Trama = asignado sin franja horaria («todo el día»)  ·  una persona con dos bloques "
    "a la misma hora se pisa a sí misma":
        "Hatched = assigned with no time slot («all day»)  ·  a person with two blocks "
        "at the same time overlaps themselves",
}
