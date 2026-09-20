"""F5a — las frases que el invariante de posición NO podía ver.

⚠️ De dónde salen: son trozos de f-string y cadenas armadas antes en una VARIABLE
(`msg = f"..."; st.success(msg)`). El invariante de v441 mira el ARGUMENTO de la llamada
de display, así que estas pasaban por delante — el hueco de v349, aplicado al i18n.

⚠️ Se traducen EN SITIO, sin envolver en `t()`: un trozo de f-string no es una cadena
entera y envolverlo exigiría reestructurar la llamada. Es el mismo criterio que ya se
aplicó a los trozos de f-string en F2/F3/F4.

NO ENTRAN AQUÍ, a propósito:
  · `'🗺 Ruta del día'`  → es el **ID** de la sub-pestaña, lo compara `sub ==` y lo usan
    los deep-links (v232). Traducirlo rompe la navegación sin dar ningún error.
  · `'En progreso'` / `'En pausa'` → son ESTADOS guardados en la hoja `Proyectos`.
  · `'Duración (d)'` → la LEEN `report.py` y `user_report.py`: contrato entre módulos.
  · los bloques `<style>` → son comentarios CSS míos, no pantalla.
"""

TRAD = {
    # ── auth_ui ────────────────────────────────────────────────────────────────
    "Vencimiento (vacío si no vence)": "Expiry (blank if it does not expire)",
    "<p style='text-align:center;color:#5b6472;margin-top:-8px;font-size:16px;'>Gestión de instalación de elevadores<br><span style='font-size:13px;color:#8b95a5;'>Proyectos · Cuadrilla · Costos · Herramientas técnicas</span></p>":
        "<p style='text-align:center;color:#5b6472;margin-top:-8px;font-size:16px;'>Lift installation management<br><span style='font-size:13px;color:#8b95a5;'>Projects · Crew · Costs · Technical tools</span></p>",
    "Ahora inicia sesión.": "Now sign in.",
    "Error de autenticación.": "Authentication error.",
    "** usa su propio libro. `Login`, `Grupos` y `Rieles` siguen en el maestro: son el registro de la app, no datos suyos.":
        "** uses its own spreadsheet. `Login`, `Grupos` and `Rieles` stay in the master book: they are the app's own register, not that client's data.",
    ":material/warning: Con clientes en libros aparte, los **resúmenes consolidados del propietario** todavía solo cuentan los del maestro. Fuera del consolidado: **":
        ":material/warning: With clients in separate books, the **owner's consolidated summaries** still only count the ones in the master book. Left out of the consolidation: **",
    "**. Cada cliente sí ve lo suyo completo.": "**. Each client does see all of their own data.",
    ":material/warning: Campo sin contacto completo (no pueden usar la app):":
        ":material/warning: Field users without full contact details (they cannot use the app):",
    "— todos los grupos —": "— all companies —",
    "Reuniendo el estado de cada grupo…": "Gathering the status of each company…",
    ":material/notifications_off: **Las alarmas de este grupo no le llegan a":
        ":material/notifications_off: **This company's alerts do not reach",
    "** de sus destinatarios:": "** of their recipients:",
    ". Sin email ni Telegram, el aviso queda dentro de la app. Se arregla cargándoles un email en su ficha.":
        ". With no email and no Telegram, the alert stays inside the app. Fix it by adding an email on their profile.",

    # ── belting_ui ─────────────────────────────────────────────────────────────
    "Belting — posición de la cabina": "Belting — car position",
    "DSTS > 0 = bajar la cabina esa distancia bajo el FFL del piso más alto.":
        "DSTS > 0 = lower the car by that distance below the FFL of the top floor.",

    # ── buffer_cut_ui ──────────────────────────────────────────────────────────
    "PDF de planos (para HKP)": "Drawing PDF (for HKP)",
    "Corte = HKP − HKPR. Un valor negativo indica que el buffer real supera al del plano: no hay nada que cortar, revisar en obra.":
        "Cut = HKP − HKPR. A negative value means the actual buffer is longer than the drawing says: there is nothing to cut, check on site.",

    # ── clientes_ui ────────────────────────────────────────────────────────────
    "Ver dirección en el mapa": "See the address on the map",

    # ── home_ui ────────────────────────────────────────────────────────────────
    ":material/route: Ruta del día": ":material/route: Day route",
    '<div style="background:#fff4e5;border-left:5px solid #e67e22;border-radius:8px;padding:9px 14px;margin-bottom:10px;"><span style="font-weight:700;color:#a35b12;font-size:16px;">⚠️ Firma el Pre-Start de hoy</span><span style="color:#7a5b3a;font-size:13px;"> · la charla de <b>':
        '<div style="background:#fff4e5;border-left:5px solid #e67e22;border-radius:8px;padding:9px 14px;margin-bottom:10px;"><span style="font-weight:700;color:#a35b12;font-size:16px;">⚠️ Sign today\'s Pre-Start</span><span style="color:#7a5b3a;font-size:13px;"> · the talk for <b>',
    "</b> ya está hecha, pero tú no constas entre quienes la firmaron.</span></div>":
        "</b> is already recorded, but you are not among those who signed it.</span></div>",
    '<div style="background:#fff4e5;border-left:5px solid #e67e22;border-radius:8px;padding:9px 14px;margin-bottom:10px;"><span style="font-weight:700;color:#a35b12;font-size:16px;">⚠️ Falta el Pre-Start de hoy</span><span style="color:#7a5b3a;font-size:13px;"> · estás fichado en <b>':
        '<div style="background:#fff4e5;border-left:5px solid #e67e22;border-radius:8px;padding:9px 14px;margin-bottom:10px;"><span style="font-weight:700;color:#a35b12;font-size:16px;">⚠️ Today\'s Pre-Start is missing</span><span style="color:#7a5b3a;font-size:13px;"> · you are clocked in at <b>',
    "</b> y hoy nadie ha registrado la charla de seguridad.</span></div>":
        "</b> and nobody has recorded the safety talk today.</span></div>",
    "Posicionamiento del hueco y matriz de solución; genera los informes del cliente y de obra.":
        "Shaft positioning and solution matrix; generates the client and site reports.",
    "Líneas de plomada y replanteo; distancias de verificación en obra.":
        "Plumb lines and setting-out; check distances for the site.",
    "Cuánto cortar de cada riel de guía (Caso 1 / Caso 2).":
        "How much to cut off each guide rail (Case 1 / Case 2).",
    "Cuánto cortar de cada buffer (HKP − HKPR).":
        "How much to cut off each buffer (HKP − HKPR).",
    "Altura a la que dejar la cabina para instalar los belts (DSTS).":
        "The height to leave the car at to install the belts (DSTS).",
    ":orange[:material/warning:] Sin ubicación en el mapa:":
        ":orange[:material/warning:] No location on the map:",

    # ── invoices_ui ────────────────────────────────────────────────────────────
    # ⚠️ Opción de radio Y valor comparado en el MISMO módulo: las 3 apariciones se
    # traducen juntas, y la guarda de v369 suelta el valor viejo guardado en sesión.
    "Todo el cliente": "The whole client",
    ":material/contacts: Ese proyecto tiene el cliente **":
        ":material/contacts: That project has the client **",
    "**, que no es una ficha de :material/contacts: Contactos. Elige el cliente a mano, o enlaza el proyecto a su ficha para que el atajo funcione la próxima vez.":
        "**, which is not a :material/contacts: Contacts record. Choose the client by hand, or link the project to its record so the shortcut works next time.",

    # ── location_ui ────────────────────────────────────────────────────────────
    "Ubicación del proyecto": "Project location",

    # ── payroll_ui ─────────────────────────────────────────────────────────────
    "Todos los periodos": "All periods",
    "horas trabajadas pero **base $0**: les falta la tarifa/hora. La colilla sale en cero y su trabajo no cuenta en el costo.":
        "hours worked but **$0 base pay**: they have no hourly rate. The payslip comes out at zero and their work does not count towards the cost.",
    ":material/person_alert: Sin nómina en este periodo, teniendo horas:":
        ":material/person_alert: No payslip in this period despite having hours:",
    "ya existían para ese periodo.": "already existed for that period.",
    ":material/person_off: **No se generó la nómina de":
        ":material/person_off: **No payslip was generated for",
    "**: no tienen tarifa/hora, así que su colilla saldría en $0. Ponles la tarifa en :material/build: Planificación → Usuarios y vuelve a generar este mismo periodo — entrarán sin duplicar.":
        "**: they have no hourly rate, so their payslip would come out at $0. Set the rate in :material/build: Planning → Users and generate this same period again — they will be included without duplicating.",
    ":material/event_repeat: **No se generó** porque el periodo elegido se cruza con nóminas ya emitidas — se pagarían las mismas horas dos veces:":
        ":material/event_repeat: **Nothing was generated** because the chosen period overlaps payslips already issued — the same hours would be paid twice:",
    "Ajusta las fechas para que no se crucen, o anula esas nóminas en la lista de abajo y vuelve a generar.":
        "Adjust the dates so they do not overlap, or void those payslips in the list below and generate again.",
    "h, así que su ausencia paga": "h, so their absence pays",
    ":material/schedule: **Días con ausencia Y fichaje** — se paga una sola jornada por día:":
        ":material/schedule: **Days with both an absence and a clock-in** — only one working day is paid per day:",

    # ── plan_ui ────────────────────────────────────────────────────────────────
    "Usa los datos del plano guardados en el proyecto.":
        "It uses the drawing data stored on the project.",

    # ── plumb_ui ───────────────────────────────────────────────────────────────
    ":material/description: PDF de planos (autocompleta del plano)":
        ":material/description: Drawing PDF (fills in from the drawing)",
    "Por elevador — encaje y verificación": "Per lift — fit and check",
    "Plantilla — posiciones de las líneas": "Template — line positions",
    "La plantilla (DBP, d1, d2) es la misma para todo el shaft; el BSR se mide por elevador y define su encaje y su verificación.":
        "The template (DBP, d1, d2) is the same for the whole shaft; the BSR is measured per lift and sets its fit and its check.",
    "Comprobación de obra: di + DBP + dd = BSR.": "Site check: di + DBP + dd = BSR.",

    # ── quotes_ui ──────────────────────────────────────────────────────────────
    "cotización(es) vencida(s)** sin respuesta:": "expired quote(s)** with no answer:",
    ". Saca una versión nueva si sigue en pie.": ". Issue a new version if it still stands.",
    ":material/sync_problem: **El catálogo cambió** desde que armaste esta cotización:":
        ":material/sync_problem: **The catalogue changed** since you built this quote:",
    ". Los precios de la cotización NO se tocan solos.":
        ". The quote's prices do NOT change on their own.",
    "** — es tu **costo** cotizado, no el precio al cliente (":
        "** — that is your quoted **cost**, not the price to the client (",
    "). Así la alerta de sobre-presupuesto salta cuando te comes el margen, no cuando ya estás perdiendo dinero.":
        "). That way the over-budget alert fires when you are eating into the margin, not when you are already losing money.",
    "creado desde esta cotización.": "created from this quote.",
    "aún no hay avance ni costo": "there is no progress and no cost yet",
    ":material/trending_up: Al ritmo actual la obra costará":
        ":material/trending_up: At the current rate the job will cost",
    "por encima** de lo cotizado con el proyecto al **":
        "above** what was quoted, with the project at **",
    "%**. A este ritmo la ganancia final será menor que la cotizada.":
        "%**. At this rate the final profit will be lower than quoted.",
    "por debajo** de lo cotizado con el proyecto al":
        "below** what was quoted, with the project at",

    # ── rail_cut_ui ────────────────────────────────────────────────────────────
    "PDF de planos (para LFKK / LFGK)": "Drawing PDF (for LFKK / LFGK)",
    "Caso 1 — primero instalado (el de abajo)": "Case 1 — first installed (the bottom one)",
    "Caso 2 — último instalado (el de arriba)": "Case 2 — last installed (the top one)",
    "Caso 1: el riel a cortar es el primero instalado (abajo). CutRC = RC − A, CutRCW = RCW − A.":
        "Case 1: the rail to cut is the first one installed (at the bottom). CutRC = RC − A, CutRCW = RCW − A.",
    "Por debajo del FFL (suma)": "Below the FFL (add)",
    "Por encima del FFL (resta)": "Above the FFL (subtract)",
    "Caso 2: el riel a cortar es el último instalado (arriba).":
        "Case 2: the rail to cut is the last one installed (at the top).",

    # ── roster_ui ──────────────────────────────────────────────────────────────
    "h del día ocupadas": "h of the day taken",
    "todo el día": "all day",
    "No se puede quitar: hay": "It cannot be removed: there are",
    "persona(s) con trabajo ese día (": "person(s) with work that day (",
    "de esta semana": "of this week",
    "· todo el día</span></div>": "· all day</span></div>",
    "· fichado en jornada pero SIN imputar obra":
        "· clocked in for the workday but with NO job charged",
    "· sin fichar aún": "· not clocked in yet",
    "— fichó donde tocaba": "— clocked in where they should",
    "pero fichó en": "but clocked in at",
    "(sin proyecto que comparar)": "(no project to compare against)",
    "sin asignación · fichó en": "no assignment · clocked in at",
    "sin asignación · fichado en jornada, sin imputar obra":
        "no assignment · clocked in for the workday, with no job charged",
    ":material/schedule: la hora solo aparece si difiere del turno (":
        ":material/schedule: the time only shows when it differs from the standard shift (",
    ":red[:material/error:] borde rojo = choque de turno  ·  :orange[:material/shield:] borde ámbar = certificado que bloquea (una celda puede llevar **los dos**)":
        ":red[:material/error:] red border = shift clash  ·  :orange[:material/shield:] amber border = a certificate that blocks (a cell can carry **both**)",

    # ── survey_ui ──────────────────────────────────────────────────────────────
    "Ancho de la cabeza del riel (mm)": "Rail head width (mm)",
    "Longitud del template de plomada (mm) — para el esquema de plomado":
        "Plumb template length (mm) — for the plumb layout",
    ":material/check_circle: Matriz, parámetros y configuración cargados desde el Excel.":
        ":material/check_circle: Matrix, parameters and settings loaded from the Excel file.",
    ":green[:material/check_circle:] Matriz cargada desde el Excel (los parámetros del plano se conservan).":
        ":green[:material/check_circle:] Matrix loaded from the Excel file (the drawing's parameters are kept).",
    '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:12px;color:#5f6b7a;margin:-6px 0 10px 2px"><span><span style="display:inline-block;width:11px;height:11px;background:#c0392b;border-radius:2px;vertical-align:-1px"></span> fuera de límite — el valor más crítico de su columna</span><span><span style="display:inline-block;width:11px;height:11px;background:#f1948a;border-radius:2px;vertical-align:-1px"></span> fuera de límite</span><span><span style="display:inline-block;width:11px;height:11px;background:#e67e22;border-radius:2px;vertical-align:-1px"></span> requiere corte (OR/OL)</span><span style="opacity:.85">WR·WL·FR·FL incumplen por <b>debajo</b> del límite; OR·OL por <b>encima</b>.</span></div>':
        '<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:12px;color:#5f6b7a;margin:-6px 0 10px 2px"><span><span style="display:inline-block;width:11px;height:11px;background:#c0392b;border-radius:2px;vertical-align:-1px"></span> out of limit — the most critical value in its column</span><span><span style="display:inline-block;width:11px;height:11px;background:#f1948a;border-radius:2px;vertical-align:-1px"></span> out of limit</span><span><span style="display:inline-block;width:11px;height:11px;background:#e67e22;border-radius:2px;vertical-align:-1px"></span> needs cutting (OR/OL)</span><span style="opacity:.85">WR·WL·FR·FL fail <b>below</b> the limit; OR·OL fail <b>above</b> it.</span></div>',
    ":material/warning: La solución activa deja **": ":material/warning: The active solution leaves **",
    "valor(es) fuera de límite**": "value(s) out of limit**",
    "Dif vs Límite": "Diff vs Limit",
    "(ninguno tiene incidencias: se muestran todos)": "(none has any issue: all are shown)",
    ":material/search: Buscando combinación óptima...": ":material/search: Searching for the optimal combination...",
    ":material/smart_toy: Generando interpretación técnica con IA...":
        ":material/smart_toy: Generating the technical interpretation with AI...",
    ":material/smart_toy: Generando interpretación del informe de cliente...":
        ":material/smart_toy: Generating the client report's interpretation...",
    ":material/description: Preparando informe interno de administración...":
        ":material/description: Preparing the internal admin report...",
    ":material/info: El informe usará los datos de este proyecto":
        ":material/info: The report will use this project's details",
    "mm** (altura del diente desde la espalda, del catálogo).":
        "mm** (tooth height from the back, from the catalogue).",
    "** detectado pero **no está en el catálogo de Rieles**. Ingresa RAIL a mano o agrégalo al catálogo.":
        "** was detected but **it is not in the Rails catalogue**. Enter RAIL by hand or add it to the catalogue.",
    ":blue[:material/info:] No se detectó el código del riel de cabina; ingresa RAIL a mano.":
        ":blue[:material/info:] The car guide rail code was not detected; enter RAIL by hand.",
    ":blue[:material/info:] No se detectó NUMBER OF STOPS en el plano; ingresa NS a mano.":
        ":blue[:material/info:] NUMBER OF STOPS was not detected on the drawing; enter NS by hand.",
    ":gray[:material/radio_button_unchecked:] Sin plano (parámetros a mano)":
        ":gray[:material/radio_button_unchecked:] No drawing (parameters by hand)",
    ":green[:material/check_circle:] Parámetros completos": ":green[:material/check_circle:] Parameters complete",
    ":material/edit: Parámetros manuales": ":material/edit: Manual parameters",
    "parámetro(s) sin leer": "parameter(s) not read",
    ":red[:material/block:] **No se puede generar el informe sin la interpretación IA.**\n\nReason:":
        ":red[:material/block:] **The report cannot be generated without the AI interpretation.**\n\nReason:",
    "No hay proyectos todavía. Créalo en": "There are no projects yet. Create one in",
    "**👑 Administración → :material/folder: Proyectos**":
        "**👑 Administration → :material/folder: Projects**",
    "y vuelve aquí para adjuntarle este survey.": "and come back here to attach this survey to it.",
    "fuera de límite": "out of limit",

    # ── tool_save_ui ───────────────────────────────────────────────────────────
    "(El PDF no se archivó en Drive: revisa la conexión.)":
        "(The PDF was not filed in Drive: check the connection.)",

    # ── app.py ─────────────────────────────────────────────────────────────────
    "Asistente de gestión": "Management assistant",
    ":material/link: Con contexto del cálculo actual.": ":material/link: With the current calculation as context.",
    "Sin cálculo activo.": "No active calculation.",
    "Enfocado en la instalación en obra y el uso de la app en terreno.":
        "Focused on installing on site and using the app in the field.",
    "Enfocado en la gestión de proyectos e interpretación de resultados.":
        "Focused on project management and interpreting results.",
}
