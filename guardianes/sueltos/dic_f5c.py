"""F5c — las etiquetas CORTAS (2 palabras) que ninguna de las dos redes veía.

⚠️ Viven dentro de listas de tuplas, de dicts de tabla y de f-strings: ni el invariante
de posición (miran el argumento de `st.*`) ni el barrido de FRASES (pide 3+ palabras) las
alcanzan. Es la tercera bolsa que destapó v441.

NO ENTRAN, por ser DATO:
  · `'En progreso'` · `'En pausa'` · `'⏸ En pausa'` → estados guardados en la hoja; se
    MUESTRAN con `i18n.etiqueta()`, que no toca el dato.
  · `'por vencer'` → lo devuelve `credentials.status()`.
  · `'🗺 Ruta del día'` · `'📊 Su trabajo'` → IDs de sub-pestaña (v232).
"""

TRAD = {
    # ── auth_ui ────────────────────────────────────────────────────────────────
    "sin grupo": "no company",
    "— elige un usuario —": "— choose a user —",
    "Grupos con pendientes:": "Companies with pending items:",
    ":orange[:material/warning:] Sin contacto": ":orange[:material/warning:] No contact details",
    ":material/badge: Credenciales": ":material/badge: Credentials",
    ":material/work: Su trabajo": ":material/work: Their work",
    "**Horas por proyecto:**": "**Hours per project:**",
    "** sin contacto": "** with no contact details",
    "** cred. por vencer": "** cred. expiring",

    # ── belting_ui ─────────────────────────────────────────────────────────────
    ":material/description: PDF de planos (autocompleta HQ)":
        ":material/description: Drawing PDF (fills in HQ)",
    "Leyendo el plano...": "Reading the drawing...",
    "del FFL top": "from the top FFL",
    "por debajo": "below",
    "por encima": "above",

    # ── buffer_cut_ui ──────────────────────────────────────────────────────────
    "Leyendo HKP del PDF...": "Reading HKP from the PDF...",

    # ── home_ui ────────────────────────────────────────────────────────────────
    ":material/folder: Proyectos": ":material/folder: Projects",
    ":material/event_busy: Ausencias": ":material/event_busy: Absences",
    ":material/badge: Usuarios": ":material/badge: Users",
    ":material/format_list_bulleted: Proyectos": ":material/format_list_bulleted: Projects",
    ":material/payments: Nóminas": ":material/payments: Payroll",
    ":material/schedule: Horas": ":material/schedule: Hours",
    ":material/content_cut: Rieles": ":material/content_cut: Rails",
    ":material/assignment: Mis proyectos": ":material/assignment: My projects",
    ":material/badge: Mis credenciales": ":material/badge: My credentials",
    ":material/event_busy: Mis ausencias": ":material/event_busy: My absences",
    ":material/group: Usuarios": ":material/group: Users",
    ":material/train: Rieles": ":material/train: Rails",
    "esta obra": "this job",
    "en retraso": "behind schedule",
    "sobre presupuesto": "over budget",
    ":orange[:material/schedule:] vence en": ":orange[:material/schedule:] expires in",
    "Charla diaria de seguridad de obra (Daily Pre-Start).":
        "Daily site safety talk (Daily Pre-Start).",
    "d de retraso": "d behind",
    "d de adelanto": "d ahead",
    "</b> asignados &nbsp;·&nbsp; <b>": "</b> assigned &nbsp;·&nbsp; <b>",
    "</b> sin asignar</div>": "</b> unassigned</div>",
    "sin asignar": "unassigned",

    # ── inventory_ui ───────────────────────────────────────────────────────────
    ":blue[en uso]": ":blue[in use]",
    "(sin proyectos)": "(no projects)",
    "(sin usuarios)": "(no users)",
    "Fecha de compra": "Purchase date",

    # ── payroll_ui ─────────────────────────────────────────────────────────────
    "h en obra)": "h on jobs)",
    "nómina(s) creada(s).": "payslip(s) created.",
    "Esta nómina": "This payslip",

    # ── plan_ui ────────────────────────────────────────────────────────────────
    "— sin proyecto (cargar plano a mano) —": "— no project (load the drawing by hand) —",
    ":material/schedule: Fichado en": ":material/schedule: Clocked in at",
    ":orange[:material/warning:] El plano no dio:":
        ":orange[:material/warning:] The drawing did not give:",

    # ── plumb_ui ───────────────────────────────────────────────────────────────
    "sin desplazar (BSR = BS)": "no shift (BSR = BS)",

    # ── prestart_ui ────────────────────────────────────────────────────────────
    "ver en Maps": "see on Maps",

    # ── projects_ui ────────────────────────────────────────────────────────────
    "— elige un proyecto —": "— choose a project —",
    "Alarma enviada al administrador.": "Alert sent to the administrator.",
    "En retraso": "Behind schedule",
    "Por vencer": "Due soon",
    "Sin asignar": "Unassigned",
    "Sin contacto": "No contact details",
    "proyecto(s) sobre presupuesto": "project(s) over budget",
    "Informe cliente": "Client report",
    "Nombre A–Z": "Name A–Z",
    "Subido por": "Uploaded by",
    "— sin cliente —": "— no client —",
    "** creado con": "** created with",
    ":material/check_circle: Proyecto **": ":material/check_circle: Project **",
    "día(s) asignados a": "day(s) assigned to",
    "persona(s) en": "person(s) in",
    ":material/schedule: **Certificados requeridos POR VENCER (renovar):**":
        ":material/schedule: **Required certificates EXPIRING SOON (renew):**",
    ":material/warning: **Sin contacto completo (email + Telegram):**":
        ":material/warning: **Without full contact details (email + Telegram):**",
    "Sin facturar": "Not invoiced",
    "** not invoiced en": "** not invoiced in",
    "sin facturar": "not invoiced",
    ":material/check: nada pendiente de facturar": ":material/check: nothing left to invoice",
    ":material/pause: En pausa": ":material/pause: On hold",
    "— sin tipo —": "— no type —",
    "con retraso": "behind schedule",
    "(sin nombre)": "(no name)",
    "En fecha": "On time",
    "de adelanto": "ahead",
    "de retraso": "behind",
    ":material/stethoscope: El equipo sigue terminando **":
        ":material/stethoscope: The crew is still finishing **",
    "**, así que **": "**, so **",
    "Este proyecto": "This project",
    ":material/insights: Estado": ":material/insights: Status",
    ":material/payments: Costos": ":material/payments: Costs",
    ":material/event: **La entrega la marca «": ":material/event: **Delivery is set by «",
    ", en fecha.": ", on time.",
    ":red[:material/block:] SOBRE PRESUPUESTO": ":red[:material/block:] OVER BUDGET",
    "en fecha": "on time",
    "Asignando proyectos...": "Assigning projects...",
    "Dejaste el avance en blanco en: **": "You left the progress blank on: **",
    "Órdenes de compra (": "Purchase orders (",
    "d de retraso**]": "d late**]",
    ":material/receipt: **Pendiente de facturar:": ":material/receipt: **Left to invoice:",
    "% de avance**": "% progress**",
    "por punto)": "per point)",
    "**. Se fija en :material/build: Usuarios.": "**. It is set in :material/build: Users.",
    "· sin archivo": "· no file",
    "Por cobrar": "To collect",
    "Por pagar": "To pay",
    "Sin tarifa": "No rate",
    "Sin margen": "No margin",
    "Ninguna obra pasada de presupuesto.": "No job is over budget.",
    ":material/groups: Por cliente": ":material/groups: By client",
    ":material/apartment: Por proyecto": ":material/apartment: By project",
    "Cargado a las obras (horas imputadas × tarifa)":
        "Charged to jobs (hours booked × rate)",
    "+ horas pagadas que NO cargaste (traslados, espera)":
        "+ hours paid that you did NOT charge (travel, waiting)",
    "Mano de obra": "Labour",
    "Por facturar": "To invoice",
    "oficina y almacén": "office and store",
    "Costo total": "Total cost",
    "En proyectos (h)": "On jobs (h)",
    "En estructura (h)": "On overhead (h)",
    "Sin asignar (h)": "Unassigned (h)",
    "Costo M.O.": "Labour cost",
    "control(es) en NO]": "control(s) answered NO]",
    "no se cargan a obra": "not charged to any job",
    "asignadas de forma habitual": "assigned on a regular basis",

    # ── quotes_ui ──────────────────────────────────────────────────────────────
    "➕ Nuevo cliente": "➕ New client",
    "·  viene de": "·  from",
    ":material/savings: Presupuesto del proyecto: **":
        ":material/savings: Project budget: **",
    "Enlazada al proyecto": "Linked to project",
    "al ritmo actual · cotizaste": "at the current rate · you quoted",
    "contra los": "against the",

    # ── rail_cut_ui ────────────────────────────────────────────────────────────
    "Leyendo LFKK / LFGK del PDF...": "Reading LFKK / LFGK from the PDF...",
    "Por encima": "Above",

    # ── roster_ui ──────────────────────────────────────────────────────────────
    "** en obra": "** on site",
    "** sin asignar (": "** unassigned (",
    ":green[:material/check_circle:] nadie sin asignar":
        ":green[:material/check_circle:] nobody unassigned",
    "Añadir el": "Add",
    "ado a esta semana": " to this week",
    "— elige el proyecto —": "— choose the project —",
    ":material/warning: Sin contacto registrado": ":material/warning: No contact details on record",
    "Sin certificados": "No certificates",
    ":material/calendar_view_week: Semana": ":material/calendar_view_week: Week",
    ":material/schedule: Día": ":material/schedule: Day",
    "** libres el": "** free on",
    ":material/palette: Trabajos": ":material/palette: Jobs",
    "· :green[en curso": "· :green[in progress",
    "· fichó en": "· clocked in at",
    "jornada (sin obra)": "workday (no job)",
    "— sin asignar —": "— unassigned —",
    "Trabajo creado (": "Job created (",

    # ── survey_ui ──────────────────────────────────────────────────────────────
    "Ancho real del hueco medido en obra (mm)": "Actual shaft width measured on site (mm)",
    "Distancia frontal de seguridad (mm)": "Front safety distance (mm)",
    "Marco de puerta de entrada (mm)": "Entrance door frame (mm)",
    "Offset de cabina (mm)": "Car offset (mm)",
    "📝 Datos del survey": "📝 Survey data",
    ":material/edit: Datos del survey": ":material/edit: Survey data",
    "Con incidencias": "With issues",
    "Generando PDF de diagramas...": "Generating the diagrams PDF...",
    "Diagramas de posicionamiento —": "Positioning diagrams —",
    ":material/place: ver en Maps": ":material/place: see on Maps",
    ":material/hourglass_empty: Extrayendo datos del PDF...":
        ":material/hourglass_empty: Extracting data from the PDF...",
    ":material/edit: Completa a mano: **": ":material/edit: Fill in by hand: **",
    ":green[:material/check_circle:] Plano cargado":
        ":green[:material/check_circle:] Drawing loaded",
    "Generando informe del cliente...": "Generating the client report...",
    "Archivando documentos en Drive...": "Filing documents in Drive...",
    "informe cliente": "client report",

    # ── app.py ─────────────────────────────────────────────────────────────────
    "Asistente de campo": "Field assistant",
}
