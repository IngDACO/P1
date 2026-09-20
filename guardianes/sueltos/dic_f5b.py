"""F5b — las frases de `projects_ui` que el invariante de posición no veía.

Mismo criterio que `dic_f5a`: trozos de f-string y cadenas armadas en una variable, que
NO son el argumento de la llamada de display y por eso se escaparon del barrido de v440.

⚠️ `'🔔 Resumen del día — '` (L401) es el ASUNTO de un correo/Telegram, no pantalla: va
en el idioma BASE (regla v436/v439), que es justo el inglés — así que traducirlo en sitio
es lo correcto, no una excepción.
"""

TRAD = {
    # ── cabecera y resumen del día ─────────────────────────────────────────────
    '</div><div style="color:#e2ecf9;font-size:13px;margin-top:2px;">Centro de control del grupo</div></div></div>':
        '</div><div style="color:#e2ecf9;font-size:13px;margin-top:2px;">Company control centre</div></div></div>',
    "todos al día": "all up to date",
    "sin avance aún": "no progress yet",
    "en todo el grupo": "across the whole company",
    ":material/notifications: Resumen del día — :green[todo en orden]":
        ":material/notifications: Today's summary — :green[all in order]",
    ":material/notifications: Resumen del día — :red[":
        ":material/notifications: Today's summary — :red[",
    ":material/notifications: Resumen del día — :orange[":
        ":material/notifications: Today's summary — :orange[",
    "🔔 Resumen del día —": "🔔 Today's summary —",

    # ── crear proyecto ─────────────────────────────────────────────────────────
    "Leído del plano.": "Read from the drawing.",
    "Define la duración de las actividades.": "It sets how long the activities take.",
    ":material/warning: Ya existe un proyecto con ese nombre:":
        ":material/warning: A project with that name already exists:",
    ". Si es otro elevador, marca la casilla y crea de nuevo.":
        ". If it is a different lift, tick the box and create it again.",
    "y los datos del plano cargados.": "and the drawing data loaded.",
    "El survey y las demás herramientas ya pueden alimentarlo.":
        "The survey and the other tools can now feed it.",
    "día(s) ya ocupados se respetaron": "day(s) already taken were left alone",
    ":material/calendar_month: Planificador: los días del rango ya estaban ocupados; no se pisó nada.":
        ":material/calendar_month: Planner: the days in the range were already taken; nothing was overwritten.",
    ":material/calendar_month: El proyecto no tiene **fecha de fin**, así que no se auto-planificó. Ponla en :material/edit: Datos, o planifica a mano en :material/calendar_month: Planificación.":
        ":material/calendar_month: The project has no **end date**, so nothing was auto-planned. Set one in :material/edit: Details, or plan by hand in :material/calendar_month: Planning.",
    "día(s) de los desasignados.": "day(s) of those unassigned.",

    # ── avisos al asignar personal ─────────────────────────────────────────────
    "(aún sin aprobar)": "(not approved yet)",
    ":material/event_busy: **No estarán disponibles esos días:**":
        ":material/event_busy: **They will not be available on those days:**",
    ":material/push_pin: **Ya asignados a otro proyecto:**":
        ":material/push_pin: **Already assigned to another project:**",
    ":material/cancel: **No cumplen los certificados que exige el proyecto:**":
        ":material/cancel: **They do not meet the certificates this project requires:**",
    ":material/badge: **Otras credenciales a revisar antes de mandarlos a obra:**":
        ":material/badge: **Other credentials to check before sending them to site:**",
    ". No recibirán la asignación ni las inducciones.":
        ". They will not receive the assignment or the inductions.",

    # ── rastro de cambios (etiquetas, NO las claves) ───────────────────────────
    "Peso en la agrupación": "Weight in the grouping",

    # ── diagnóstico del cronograma ─────────────────────────────────────────────
    "puntos por debajo</b> del plan": "points behind</b> plan",
    "puntos por encima</b> del plan": "points ahead of</b> plan",
    "Vas <b>en línea con el plan</b>": "You are <b>on plan</b>",
    "más de los": "more than the",
    "** aún no ha arrancado. Ahí está el retraso.":
        "** has not started yet. That is where the delay is.",
    ":material/stethoscope: Sin empezar y ya tocaba: **":
        ":material/stethoscope: Not started and already due: **",

    # ── editar proyecto / actividades ──────────────────────────────────────────
    "El nombre del proyecto no puede quedar vacío.": "The project name cannot be left empty.",
    "La fecha de fin no puede ser anterior a la de inicio.":
        "The end date cannot be earlier than the start date.",
    "Se actualizaron los datos del proyecto.": "The project details were updated.",
    "Se actualizó la tabla de actividades del cronograma.":
        "The schedule's activity table was updated.",
    "Se agregó la actividad:": "Activity added:",
    "Se eliminó una actividad del cronograma.": "An activity was removed from the schedule.",
    "Quedará sin proyecto:": "It will be left with no project:",
    "**. Esas quedan como estaban — escribe un número (0-100) si querías cambiarlas.":
        "**. Those are left as they were — type a number (0-100) if you meant to change them.",

    # ── agrupaciones ───────────────────────────────────────────────────────────
    "días de retraso**.": "days behind**.",
    "Es donde más rinde reforzar.": "That is where reinforcing pays off most.",
    "Sin cronograma para proyectar:": "No schedule to project from:",
    "Presupuesto de la agrupación $": "Grouping budget $",
    ":material/warning: Consumen bastantes más horas que sus gemelos: **":
        ":material/warning: They use noticeably more hours than their twins: **",
    "**. Vale la pena mirar por qué.": "**. Worth looking into why.",
    # ⚠️ Nombres de COLUMNA del editor de miembros: se usan en `disabled=`, en
    # `column_config` y al leer `r["…"]`. Todas las apariciones están en este módulo, así
    # que se traducen JUNTAS — media traducción dejaría la lectura buscando otra columna.
    "En la agrupación": "In the grouping",
    "Ya en otra": "Already in another",
    ". Añádele elevadores desde su panel.": ". Add lifts to it from its panel.",

    # ── ganancia / ingreso de la obra ──────────────────────────────────────────
    ":material/check_circle: El ingreso de esta obra es el **precio pactado** en la cotización":
        ":material/check_circle: This job's revenue is the **agreed price** on quote",
    "es consecuencia de ese precio.": "follows from that price.",
    ":material/info: Esta obra tiene una ganancia fija de":
        ":material/info: This job has a fixed profit of",
    "que **no se usa**: manda el precio que el cliente firmó. Ponla a 0 para quitar el ruido.":
        "that is **not used**: the price the client signed wins. Set it to 0 to remove the noise.",
    ":material/info: La mano de obra de esta obra todavía usa el **modelo viejo**: un":
        ":material/info: This job's labour still uses the **old model**: a",
    "%** sobre ella. En cuanto pongas aquí lo que quieres ganar por hora, pasa al modelo nuevo (importe por rubro) y el % se calcula solo.":
        "%** on top of it. As soon as you set what you want to earn per hour here, it moves to the new model (an amount per line) and the % works itself out.",
    ":material/check_circle: Esta obra ya usa el modelo por rubro. El":
        ":material/check_circle: This job already uses the per-line model. The",
    "de margen es consecuencia, no un dato que hayas tecleado.":
        "margin follows from it; it is not something you typed.",
    ":material/person_alert: Sin ganancia puesta, así que su trabajo se facturaría **a costo**: **":
        ":material/person_alert: With no profit set, their work would be invoiced **at cost**: **",
    "Con estos valores ganarías **": "With these values you would make **",
    "** de mano de obra en lo fichado hasta ahora. Los materiales se facturan a costo (decisión de v360).":
        "** on the labour clocked so far. Materials are invoiced at cost (decision from v360).",
    "Con este importe, el ingreso estimado de la obra sería **":
        "With this amount, the job's estimated revenue would be **",
    "** sobre un costo de": "** on a cost of",

    # ── costos del proyecto ────────────────────────────────────────────────────
    "Gasto de **estructura**: no se le carga a ninguna obra ni se le factura a un cliente.":
        "**Overhead** spend: it is not charged to any job and not invoiced to a client.",
    "Todavía no hay gastos registrados en esta localización.":
        "No spend has been recorded at this location yet.",
    "A este ritmo el proyecto costara **": "At this rate the project will cost **",
    "por encima** del presupuesto": "over** budget",
    "**, dentro del presupuesto de": "**, within the budget of",
    "Este proyecto **no tiene presupuesto asignado**, así que no hay contra qué comparar el gasto. Se define en :material/edit: Datos.":
        "This project **has no budget set**, so there is nothing to compare the spend against. Set it in :material/edit: Details.",
    "Todavía no hay costos registrados en este proyecto.":
        "No costs have been recorded on this project yet.",
    "pedido, aún sin recibir": "ordered, not received yet",
    ":material/warning: Sin tarifa/hora, así que sus horas suman **$0** al costo: **":
        ":material/warning: With no hourly rate, their hours add **$0** to the cost: **",
    "**: horas de alguien que **ya no está dado de alta**, así que suman $0 y no hay dónde ponerle tarifa.":
        "**: hours from someone **no longer on the books**, so they add $0 and there is nowhere to set a rate.",

    # ── P&L ────────────────────────────────────────────────────────────────────
    ":material/info: No hay facturas ni costos (nóminas/compras) en este periodo.":
        ":material/info: There are no invoices or costs (payroll/purchases) in this period.",
    ":material/info: Aún no hay facturas ni costos (nóminas/compras) registrados.":
        ":material/info: No invoices or costs (payroll/purchases) have been recorded yet.",
    "cliente(s) facturado(s)  ·  costos = nóminas + compras":
        "client(s) invoiced  ·  costs = payroll + purchases",
    "·  se compara con": "·  compared with",

    # ── resumen financiero ─────────────────────────────────────────────────────
    "en facturas pasadas de su vencimiento.": "in invoices past their due date.",
    "facturados y aún sin cobrar.": "invoiced and not yet collected.",
    "Todo lo trabajado está facturado.": "Everything worked has been invoiced.",
    "en nóminas emitidas sin marcar pagadas.": "in payslips issued and not marked paid.",
    "Horas sin nómina": "Hours with no payslip",
    "Horas imputadas a una obra SIN jornada abierta: se cargan al cliente pero no entran en ninguna nómina, así que inflan el margen.":
        "Hours charged to a job with NO workday open: they are billed to the client but do not enter any payslip, so they inflate the margin.",
    "Su trabajo cuenta como $0:": "Their work counts as $0:",
    "·  Además, con horas pero YA SIN cuenta (no se les puede poner tarifa):":
        "·  Plus, with hours but NO account any more (no rate can be set for them):",
    "Se factura al costo (ganancia estimada $0):": "Invoiced at cost (estimated profit $0):",

    # ── conciliación de mano de obra ───────────────────────────────────────────
    "− horas cobradas que NO pagaste (imputadas sin jornada)":
        "− hours billed that you did NOT pay (charged with no workday)",
    "· de las cuales, trabajo en estructura (oficina, almacén)":
        "· of which, overhead work (office, store)",
    "= base que deberías pagar": "= base pay you should be paying",
    "Base realmente puesta en nóminas": "Base pay actually entered in payslips",
    "= costo real de la mano de obra": "= real cost of labour",

    # ── rentabilidad ───────────────────────────────────────────────────────────
    "obra(s) con margen 0%**, así que su ingreso estimado es exactamente su costo y la ganancia sale $0:":
        "job(s) at 0% margin**, so their estimated revenue is exactly their cost and the profit comes out at $0:",
    ". Edítalos en la tabla de abajo.": ". Edit them in the table below.",
    ". No aportan a la rentabilidad todavía; su margen se edita en el proyecto.":
        ". They add nothing to profitability yet; their margin is edited on the project.",

    # ── gastos del grupo ───────────────────────────────────────────────────────
    "proyecto(s) ya sobre presupuesto:**": "project(s) already over budget:**",
    "más se saldrá(n) al ritmo actual** (aún dentro hoy):":
        "more will go over at the current rate** (still within budget today):",
    "se pasará(n) con el material ya pedido** (aún no está recibido):":
        "will go over with the material already ordered** (not received yet):",
    "orden(es) de compra sin llegar en la fecha prometida:**":
        "purchase order(s) that did not arrive on the promised date:**",

    # ── horas del grupo ────────────────────────────────────────────────────────
    "%** fue trabajo en **estructura** (oficina/almacén): se paga y no se le carga a ninguna obra.":
        "%** was **overhead** work (office/store): it is paid and not charged to any job.",
    ":material/warning: Sin **tarifa/hora**, así que su costo sale $0: **":
        ":material/warning: With no **hourly rate**, their cost comes out at $0: **",
    "**: horas de alguien que **ya no está dado de alta** (cuenta eliminada). Sus horas siguen contando, pero **no hay dónde ponerle tarifa**, así que suman $0. Para costearlas habría que volver a crear esa cuenta.":
        "**: hours from someone **no longer on the books** (account deleted). Their hours still count, but **there is nowhere to set a rate**, so they add $0. To cost them you would have to recreate that account.",
    ":material/warning: Sin tarifa/hora, así que su trabajo aquí cuenta $0:":
        ":material/warning: With no hourly rate, their work here counts as $0:",
}
