"""F3-I · Acceso, usuarios, grupos, credenciales, rieles y manuales — ES→EN.

⚠️ NO se traduce nada que se guarde o se compare:
  · los ROLES (`auth.ROLES`: propietario/administrador/campo) y los GRUPOS son datos;
  · `credentials.CATALOGO` (White Card, Forklift…) ya está en inglés y es catálogo;
  · las referencias de riel (`T75-3/B`) y las siglas del plano (RAIL, CAR GUIDE RAIL);
  · `Superannuation`, `GST` y `IANA` son nombres propios / legales.
⚠️ `_delok`, `man_del_ok`, `del_g_ok` salen del extractor porque son el 1er argumento de
`st.checkbox`… que SÍ es la etiqueta. Se comprueba uno a uno: aquí son KEYS pasadas por
posición a `ui.confirmar_borrado`, así que NO se traducen (no están en este dict).
"""
TRAD = {
    # ── login / bootstrap ──────────────────────────────────────────
    ":material/lock: El acceso no está conectado a Google Sheets. Configura los Secrets "
    "(gcp_service_account + TIMECLOCK_SHEET_ID) en Streamlit Cloud.":
        ":material/lock: Sign-in is not connected to Google Sheets. Configure the "
        "Secrets (gcp_service_account + TIMECLOCK_SHEET_ID) in Streamlit Cloud.",
    ":material/shield_person: **Configuración inicial** — crea la cuenta de propietario.":
        ":material/shield_person: **Initial setup** — create the owner account.",
    "Repetir contraseña": "Repeat password",
    "Crear propietario": "Create owner",
    "Completa usuario y contraseña.": "Fill in username and password.",
    "Las contraseñas no coinciden.": "The passwords do not match.",
    "#### Iniciar sesión": "#### Sign in",
    "Mantener la sesión iniciada en este dispositivo":
        "Keep me signed in on this device",
    "Si lo activas, este dispositivo recordará tu sesión ~7 días y no tendrás que volver "
    "a escribir usuario y contraseña. Déjalo sin marcar en un equipo compartido o "
    "público.":
        "If you turn this on, this device will remember your session for about 7 days "
        "and you will not have to type your username and password again. Leave it "
        "unticked on a shared or public computer.",
    "Iniciar sesión": "Sign in",
    "Si eres **tú** y dejaste la sesión abierta en otro dispositivo, puedes cerrarla e "
    "iniciar aquí.":
        "If this is **you** and you left the session open on another device, you can "
        "close it and sign in here.",
    ":material/lock_open: Cerrar la otra sesión e iniciar aquí":
        ":material/lock_open: Close the other session and sign in here",
    ":material/logout: Cerrar sesión": ":material/logout: Sign out",

    # ── grupos (empresas cliente) ──────────────────────────────────
    "Aún no hay grupos. Crea el primero abajo.":
        "No companies yet. Create the first one below.",
    "Nombre del grupo (empresa cliente)": "Company name (client company)",
    "Descripción (opcional)": "Description (optional)",
    ":material/add: Crear grupo": ":material/add: Create company",
    "Libro de datos de cada cliente": "Each client's data workbook",
    "Cada empresa cliente puede tener su **propio archivo de Google Sheets**, para que "
    "sus datos no compartan fichero con los de otra. Vacío = usa el libro maestro.":
        "Each client company can have its **own Google Sheets file**, so its data does "
        "not share a file with anyone else's. Empty = it uses the master workbook.",
    ":material/info: Crea una hoja de cálculo en blanco, **compártela como editor** con "
    "la cuenta de servicio de la app, y pega aquí su enlace o su ID.":
        ":material/info: Create a blank spreadsheet, **share it as editor** with the "
        "app's service account, and paste its link or its ID here.",
    "Enlace o ID del libro": "Workbook link or ID",
    ":material/link: Guardar enlace": ":material/link: Save link",
    ":material/link_off: Volver al maestro": ":material/link_off: Back to the master",
    "Zona horaria de cada grupo": "Each company's time zone",
    "En qué hora local se graban los registros (fichaje, pre-start, alarmas…) de ese "
    "grupo. Sin fijar = ":
        "The local time in which that company's records are written (time clock, "
        "pre-start, alerts…). Not set = ",
    "Zona horaria (IANA)": "Time zone (IANA)",
    "** ahora son las **": "** it is now **",
    "**.  (Actual del grupo: ": "**.  (Company's current one: ",
    ":material/save: Guardar zona": ":material/save: Save time zone",
    "Margen de facturación por defecto": "Default invoicing margin",
    "Ganancia (%) sobre la mano de obra que se cobra al cliente. Cada proyecto puede "
    "sobrescribirlo (✏️ Datos). Base de la 'tarifa de venta' y la rentabilidad.":
        "Profit (%) on the labour charged to the client. Each project can override it "
        "(✏️ Data). It is the basis of the sell rate and of profitability.",
    "Margen por defecto (%)": "Default margin (%)",
    ":material/save: Guardar margen": ":material/save: Save margin",
    "Impuesto de facturación por defecto (GST/IVA)": "Default invoicing tax (GST/VAT)",
    "Se aplica por defecto a las facturas nuevas; editable por factura. Australia = 10 "
    "(GST).":
        "Applied by default to new invoices; editable per invoice. Australia = 10 (GST).",
    "Impuesto por defecto (%)": "Default tax (%)",
    ":material/save: Guardar impuesto": ":material/save: Save tax",
    "Nómina: super y retención por defecto":
        "Payroll: default super and withholding",
    "Se precargan al generar una nómina; editables por nómina. Australia: super ~11.5%. "
    "No es cálculo fiscal certificado.":
        "These are preloaded when payroll is generated; editable per payslip. Australia: "
        "super ~11.5%. This is not a certified tax calculation.",
    "Superannuation % (aporte)": "Superannuation % (employer contribution)",
    "Retención de impuesto % (deducción)": "Tax withholding % (deduction)",
    ":material/save: Guardar nómina": ":material/save: Save payroll settings",
    "Configuración de nómina actualizada.": "Payroll settings updated.",
    "Eliminar grupo": "Delete company",
    "Confirmo eliminar el grupo **": "I confirm I want to delete the company **",
    ":material/delete: Eliminar grupo": ":material/delete: Delete company",

    # ── usuarios ───────────────────────────────────────────────────
    "Propietario puede ir sin grupo; admin y campo requieren grupo.":
        "An owner can have no company; admin and field users need one.",
    ":material/mail: Email (obligatorio para campo)":
        ":material/mail: Email (required for field users)",
    "Crear usuario": "Create user",
    "#### :material/manage_accounts: Gestionar un usuario":
        "#### :material/manage_accounts: Manage a user",
    "Filtrar por grupo": "Filter by company",
    "#### :material/public: Resumen de todos los grupos":
        "#### :material/public: Summary of all companies",
    "Aún no hay grupos con datos.": "No companies with data yet.",
    "Ningún grupo tiene pendientes urgentes.": "No company has anything urgent pending.",
    "Aún no tienes usuarios de campo. Crea el primero aquí.":
        "You have no field users yet. Create the first one here.",
    ":material/touch_app: Toca una fila para abrir y gestionar la ficha de esa persona.  "
    "Credenciales: vigente / por vencer / vencido / — sin registrar.":
        ":material/touch_app: Tap a row to open and manage that person's record.  "
        "Credentials: valid / expiring / expired / — not recorded.",
    "Matriz de credenciales (usuarios × tickets)":
        "Credentials matrix (users × tickets)",
    "Credenciales: vigente / por vencer (≤30 d) / vencido / — no registrada":
        "Credentials: valid / expiring (≤30 d) / expired / — not recorded",
    "Crear usuario de campo": "Create field user",
    "Usuario": "Username",
    "Nombre": "Name",
    "Contraseña": "Password",
    ":material/mail: Email (OBLIGATORIO para campo)":
        ":material/mail: Email (REQUIRED for field users)",
    "El Telegram se vincula en su ficha tras crearlo.":
        "Telegram is linked from their record once created.",
    "Crear": "Create",
    "El email es obligatorio para usuarios de campo.":
        "Email is required for field users.",
    "Sección del usuario": "User section",
    "Nueva contraseña": "New password",
    "Cambiar contraseña": "Change password",
    "Escribe la nueva contraseña.": "Type the new password.",
    ":material/payments: Tarifa por hora": ":material/payments: Hourly rate",
    "Para costear la mano de obra.": "Used to cost the labour.",
    "Guardar tarifa": "Save rate",
    ":material/event_available: Fecha de alta en la empresa":
        ":material/event_available: Start date at the company",
    "Desde aquí cuenta su año de vacaciones.":
        "Their leave year is counted from here.",
    "Guardar fecha de alta": "Save start date",
    ":material/warning: Sin fecha de alta: su saldo de vacaciones se cuenta por año "
    "natural (1 ene – 31 dic), no desde su aniversario.":
        ":material/warning: With no start date their leave balance is counted by "
        "calendar year (1 Jan – 31 Dec), not from their anniversary.",
    "Rol": "Role",
    "Aplicar rol": "Apply role",
    "Grupo": "Company",
    "Aplicar grupo": "Apply company",
    ":material/block: Desactivar (no podrá entrar)":
        ":material/block: Deactivate (they will not be able to sign in)",
    ":material/check_circle: Activar": ":material/check_circle: Activate",
    "El contacto (email + Telegram) solo es obligatorio para usuarios de campo. Puedes "
    "registrarlo igual.":
        "Contact details (email + Telegram) are only required for field users. You can "
        "record them anyway.",
    ":material/warning: Sin contacto completo **no puede usar la app** y no recibe "
    "asignaciones ni inducciones.":
        ":material/warning: Without complete contact details they **cannot use the app** "
        "and receive no assignments or inductions.",
    "Horas registradas": "Hours recorded",
    "Recibos cargados": "Receipts uploaded",
    "Proyectos asignados": "Projects assigned",
    "**Asignado a** — toca para abrir:": "**Assigned to** — tap to open:",
    "Sin proyectos asignados.": "No projects assigned.",
    "Ha cargado recibos por **$": "They have uploaded receipts totalling **$",
    "** en total.": "** in all.",
    "Las horas y los recibos se gestionan desde :material/schedule: Fichaje y el detalle "
    "de cada proyecto; aquí es un resumen.":
        "Hours and receipts are managed from :material/schedule: Time clock and each "
        "project's detail; this is a summary.",
    "Eliminar quita al usuario y su acceso. Sus fichajes, recibos y credenciales ya "
    "registrados **no se borran** (quedan a su nombre).":
        "Deleting removes the user and their access. Their time entries, receipts and "
        "credentials already recorded **are not deleted** (they stay under their name).",
    "Confirmo eliminar a «": "I confirm I want to delete «",
    "Eliminar definitivamente": "Delete permanently",

    # ── contacto / Telegram ────────────────────────────────────────
    ":material/mail: Email": ":material/mail: Email",
    "Guardar email": "Save email",
    "**:material/send: Telegram**": "**:material/send: Telegram**",
    ":material/info: Telegram no está configurado en esta instalación (falta el bot en "
    "Secrets), así que **no se le exige** para entrar. Con el email basta.":
        ":material/info: Telegram is not configured on this installation (the bot is "
        "missing from Secrets), so it is **not required** to sign in. Email is enough.",
    "Poner el chat_id a mano": "Enter the chat_id by hand",
    "Chat ID de Telegram": "Telegram chat ID",
    "Solo si ya lo tienes por otra vía. Sin bot configurado, la app no puede enviarle "
    "nada.":
        "Only if you already have it another way. With no bot configured the app cannot "
        "send them anything.",
    "Guardar chat_id": "Save chat_id",
    "Desvincular Telegram": "Unlink Telegram",
    "1) El usuario abre el bot y pulsa **Start** (envíale este link):":
        "1) The user opens the bot and presses **Start** (send them this link):",
    "2) Cuando lo haya hecho, pulsa:": "2) Once they have, press:",
    ":material/link: Vincular Telegram de este usuario":
        ":material/link: Link this user's Telegram",
    ":material/check_circle: Telegram vinculado.": ":material/check_circle: Telegram linked.",
    "No encontré su mensaje. Asegúrate de que pulsó Start y reintenta.":
        "I could not find their message. Make sure they pressed Start and try again.",

    # ── credenciales ───────────────────────────────────────────────
    "Las credenciales necesitan Google Sheets configurado.":
        "Credentials need Google Sheets configured.",
    "Credenciales": "Credentials",
    ":material/check_circle: Vigentes": ":material/check_circle: Valid",
    ":material/schedule: Por vencer": ":material/schedule: Expiring",
    ":material/cancel: Vencidas": ":material/cancel: Expired",
    ":material/download: Documentos (": ":material/download: Documents (",
    "Sin credenciales registradas.": "No credentials recorded.",
    "Agregar credencial": "Add credential",
    "Tipo": "Type",
    "Especifica el tipo": "Specify the type",
    "Clase (licencia)": "Class (licence)",
    "Foto o documento (opcional)": "Photo or document (optional)",
    "No se pudo subir el archivo a Drive; se guarda el resto.":
        "The file could not be uploaded to Drive; everything else is saved.",
    "Editar / eliminar credencial": "Edit / delete credential",
    "Credencial": "Credential",
    "Número": "Number",
    "Nota": "Note",
    "### :material/badge: Mis credenciales": "### :material/badge: My credentials",
    "Tus tickets y credenciales registrados por tu administrador. Muéstralos en obra si "
    "te los piden.":
        "Your tickets and credentials as recorded by your administrator. Show them on "
        "site if you are asked for them.",
    "Emisión": "Issued",
    "Vencimiento (vacío si no vence)": "Expiry (leave empty if it does not expire)",
    "Agregar": "Add",

    # ── manuales ───────────────────────────────────────────────────
    "#### :material/menu_book: Banco de manuales del asistente":
        "#### :material/menu_book: The assistant's manual library",
    "El asistente de IA consulta estos manuales para responder dudas técnicas de "
    "instalación y **cita la fuente** (manual · sección · página).":
        "The AI assistant consults these manuals to answer technical installation "
        "questions and **cites the source** (manual · section · page).",
    "**Pre-cargados** (incluidos en la app):": "**Preloaded** (shipped with the app):",
    "- :material/menu_book: ": "- :material/menu_book: ",
    "Para subir manuales nuevos hace falta Google Drive + Sheets configurados (mismos "
    "secrets que documentos y fichaje).":
        "Uploading new manuals needs Google Drive + Sheets configured (the same secrets "
        "as documents and the time clock).",
    "**Subidos por ti:**": "**Uploaded by you:**",
    "Quitar un manual": "Remove a manual",
    "Manual": "Manual",
    "Confirmo eliminar este manual": "I confirm I want to delete this manual",
    "Manual eliminado.": "Manual deleted.",
    "No se pudo eliminar.": "It could not be deleted.",
    "Aún no has subido manuales. Agrega el primero abajo.":
        "You have not uploaded any manuals yet. Add the first one below.",
    "Subir manual": "Upload manual",
    "Acepta un PDF con texto (no escaneado) o un ZIP con varios PDFs. Evita PDFs enormes "
    "(>50 MB): se procesan en el navegador.":
        "It accepts a PDF with text (not scanned) or a ZIP with several PDFs. Avoid huge "
        "PDFs (>50 MB): they are processed in the browser.",
    "Archivo (PDF o ZIP)": "File (PDF or ZIP)",
    "Nombre del manual (ej. 'KONE MonoSpace')": "Manual name (e.g. 'KONE MonoSpace')",
    ":material/upload: Procesar y guardar": ":material/upload: Process and save",
    "Selecciona un archivo.": "Choose a file.",
    "Manual «": "Manual «",
    "» agregado: ": "» added: ",
    " fragmentos indexados.": " fragments indexed.",

    # ── catálogo de rieles ─────────────────────────────────────────
    "#### :material/train: Catálogo de rieles": "#### :material/train: Rail catalogue",
    "Al cargar un plano, el lector detecta el código del **CAR GUIDE RAIL** y "
    "autocompleta **RAIL** con la *altura del diente desde la espalda* de esta tabla.":
        "When a drawing is loaded, the reader detects the **CAR GUIDE RAIL** code and "
        "fills in **RAIL** with the *tooth height from the back* from this table.",
    "Necesita Google Sheets configurado.": "This needs Google Sheets configured.",
    "Catálogo vacío. Agrega el primer riel abajo.":
        "The catalogue is empty. Add the first rail below.",
    "Agregar riel": "Add rail",
    "Referencia (ej. T75-3/B)": "Reference (e.g. T75-3/B)",
    "Altura del diente desde la espalda (RAIL) mm":
        "Tooth height from the back (RAIL) mm",
    "Ancho del diente (mm)": "Tooth width (mm)",
    "La referencia es obligatoria.": "The reference is required.",
    "Editar / eliminar riel": "Edit / delete rail",
    "Referencia": "Reference",
    "Altura diente desde espalda (RAIL)": "Tooth height from back (RAIL)",
    "Ancho diente": "Tooth width",
    ":material/save: Guardar": ":material/save: Save",
    ":material/delete: Eliminar": ":material/delete: Delete",
}
