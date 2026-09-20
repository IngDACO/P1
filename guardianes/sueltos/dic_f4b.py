"""F4-B · survey_ui — la herramienta más potente, en inglés.

⚠️ NO se traduce NINGUNA sigla del dominio ni del plano: NS, RAIL, BS, BSR, SF1, SF2,
BKS, TSW, FS, RL, FB, OR, OL, WR, WL, FR, FL, CUT OR, CUT OL, LIMIT, DIF, MAX OFF,
BC_CALC, DBP, DBPW, LengthTemplate, Omega, Z, C1/C2, ANTHROPIC_API_KEY. Son los nombres
que el técnico ve en el plano y en la matriz; traducirlos rompería la correspondencia
con el PDF y con las columnas del Excel de survey.
⚠️ Tampoco se tocan «Fase», «Lateral (RL)», «Frontal (FB)» como CLAVES: aquí solo se
traduce lo que se PINTA — el extractor ya solo trae posiciones de display.
Vocabulario: hueco/shaft → shaft · replanteo → setting out · plomado → plumb setting ·
matriz → matrix · paso → step · encaje → fit.
"""
TRAD = {
    # ── cabecera y flujo ───────────────────────────────────────────
    ":material/summarize: Survey duplicado: se conservaron parámetros y configuración. "
    "Ingresa la matriz del siguiente elevador y calcula.":
        ":material/summarize: Survey duplicated: parameters and configuration were kept. "
        "Enter the matrix for the next lift and calculate.",
    ":material/download: Cargaste el proyecto **": ":material/download: You loaded project **",
    "**. Pulsa **:material/play_arrow: Calcular** para regenerar diagramas e informes.":
        "**. Press **:material/play_arrow: Calculate** to regenerate diagrams and reports.",
    ":material/cleaning_services: Empezar un survey nuevo":
        ":material/cleaning_services: Start a new survey",
    "Borra parámetros, matriz, configuración y resultados de esta sesión. No afecta a los "
    "proyectos ya guardados.":
        "Clears the parameters, matrix, configuration and results of this session. It "
        "does not affect projects already saved.",
    ":material/cleaning_services: Limpiar todo y empezar de cero":
        ":material/cleaning_services: Clear everything and start over",
    "Fase": "Phase",

    # ── resultados del optimizador ─────────────────────────────────
    "Lateral (RL)": "Lateral (RL)",
    "Frontal (FB)": "Front (FB)",
    "Fuera de límite": "Out of limit",
    "Soluciones óptimas": "Optimal solutions",
    ":material/check_circle: Solución encontrada **sin valores fuera de límite**.":
        ":material/check_circle: Solution found **with no values out of limit**.",
    ":material/cancel: No se encontró ninguna combinación válida con estos parámetros.":
        ":material/cancel: No valid combination was found with these parameters.",
    "Parámetros calculados": "Calculated parameters",
    "Matriz SURVEY ajustada": "Adjusted SURVEY matrix",
    "Resumen por columna — Estado inicial": "Column summary — initial state",
    "**MAX OFF RL:** ": "**MAX OFF RL:** ",
    " mm  |  **MAX OFF FB:** ": " mm  |  **MAX OFF FB:** ",
    " mm  |  **BC_CALC:** ": " mm  |  **BC_CALC:** ",
    " mm  |  **DIF TSW-FS:** ": " mm  |  **DIF TSW-FS:** ",
    " mm  |  **FB máx. hacia atrás:** ": " mm  |  **FB max. backwards:** ",
    ":material/search: Optimización": ":material/search: Optimisation",
    ":green[:material/check_circle:] Se encontraron **":
        ":green[:material/check_circle:] Found **",
    " solución(es) óptima(s)** con **": " optimal solution(s)** with **",
    " valor(es) fuera de límite**": " value(s) out of limit**",
    ":material/star: Solución activa — se usa en diagramas, plomado e informes":
        ":material/star: Active solution — used in diagrams, plumb setting and reports",
    "Comparar soluciones lado a lado": "Compare solutions side by side",
    "CUT OR / CUT OL: valor a cortar si OR/OL supera el límite (OR/OL − LIMIT). Positivo "
    "= requiere corte. Blanco = dentro del límite.":
        "CUT OR / CUT OL: how much to cut if OR/OL exceeds the limit (OR/OL − LIMIT). "
        "Positive = a cut is needed. Blank = within the limit.",
    "Log del optimizador (": "Optimiser log (",
    " pasos evaluados)": " steps evaluated)",
    "Válidos: ": "Valid: ",
    "  |  Omitidos por límite físico (RL/FB): ":
        "  |  Skipped for physical limit (RL/FB): ",
    "  |  Omitidos por pared: ": "  |  Skipped for the wall: ",
    "  |  Omitidos por apertura tapada: ": "  |  Skipped for a blocked opening: ",
    "No se encontró combinación válida.": "No valid combination was found.",

    # ── diagramas ──────────────────────────────────────────────────
    ":material/architecture: Diagrama de posicionamiento — planta por piso":
        ":material/architecture: Positioning diagram — plan view per floor",
    "Vista superior de cómo encaja la cabina en el shaft en cada piso (matriz de la "
    "solución seleccionada). Verde = dentro de límite, naranja = al límite, rojo = fuera.":
        "Top view of how the car fits in the shaft on each floor (matrix of the selected "
        "solution). Green = within limit, orange = at the limit, red = out.",
    "Vista isométrica del hueco": "Isometric view of the shaft",
    "Pisos a mostrar": "Floors to show",
    "Pisos": "Floors",
    ":material/picture_as_pdf: Preparar PDF de estos diagramas":
        ":material/picture_as_pdf: Prepare a PDF of these diagrams",
    ":material/download: Descargar diagramas (PDF)":
        ":material/download: Download diagrams (PDF)",

    # ── BSR vs BS y plomado ────────────────────────────────────────
    ":material/straighten: Análisis BSR vs BS": ":material/straighten: BSR vs BS analysis",
    "BSR ≥ BS — No se requiere ajuste de shaft.":
        "BSR ≥ BS — no shaft adjustment is needed.",
    "No se encontró paso. DIF BS = ": "No step was found. DIF BS = ",
    ":green[:material/check_circle:] Paso: **": ":green[:material/check_circle:] Step: **",
    " mm**  |  Rango: **": " mm**  |  Range: **",
    "**  |  Zona: **": "**  |  Zone: **",
    ":material/straighten: Plomado definitivo (según el survey)":
        ":material/straighten: Final plumb setting (from the survey)",
    "Esquema de plomado con los desplazamientos que determinó el survey. El conjunto "
    "(plomos + paredes teóricas + template) se mueve; las paredes reales quedan fijas "
    "(eje cero = pared real izquierda).":
        "Plumb layout with the shifts the survey worked out. The assembly (plumb points "
        "+ theoretical walls + template) moves; the real walls stay fixed (zero axis = "
        "real left wall).",
    "Desplazamiento aplicado:  lateral (rl) = **": "Shift applied:  lateral (rl) = **",
    " mm**  ·  frontal (fb) = **": " mm**  ·  front (fb) = **",
    "DBP": "DBP",
    "DBPW": "DBPW",
    ":orange[:material/warning:] **BS incoherente:** el plano dice **":
        ":orange[:material/warning:] **BS does not add up:** the drawing says **",
    "** pero SF1+BKS+2·RAIL+SF2 = **": "** but SF1+BKS+2·RAIL+SF2 = **",
    "** (dif ": "** (diff ",
    " mm). El encaje usa (BSR−BS)/2, así que con este desajuste los plomos quedan mal "
    "ubicados. Revisa BS, SF1, SF2, BKS o RAIL.":
        " mm). The fit uses (BSR−BS)/2, so with this mismatch the plumb points end up in "
        "the wrong place. Check BS, SF1, SF2, BKS or RAIL.",
    "Vistas 3D del replanteo": "3D views of the setting out",
    "Ficha de replanteo (para obra)": "Setting-out card (for site)",
    "Los números a medir con cinta. Imprímela o ábrela en el móvil.":
        "The numbers to measure with a tape. Print it or open it on your phone.",
    "**:material/straighten: Verificación en campo — distancias plomo ↔ pared real**":
        "**:material/straighten: On-site check — plumb ↔ real wall distances**",
    ":material/lightbulb: Ingresa **LengthTemplate** en los parámetros para ver el "
    "template completo (punto P, cortes C1/C2 y diagonales).":
        ":material/lightbulb: Enter **LengthTemplate** in the parameters to see the full "
        "template (point P, cuts C1/C2 and diagonals).",
    "Se mostrará cuando el survey encuentre una solución válida.":
        "It will be shown once the survey finds a valid solution.",

    # ── cálculo, IA y correo ───────────────────────────────────────
    ":orange[:material/warning:] **No se pudo generar la interpretación técnica:** ":
        ":orange[:material/warning:] **The technical interpretation could not be "
        "generated:** ",
    "\n\nLos informes **requieren** la interpretación IA. Verifica que "
    "`ANTHROPIC_API_KEY` esté configurada en los **Secrets de Streamlit Cloud**.":
        "\n\nThe reports **require** the AI interpretation. Check that "
        "`ANTHROPIC_API_KEY` is configured in the **Streamlit Cloud Secrets**.",
    ":material/warning: Problemas en los parámetros — revisar antes de calcular:":
        ":material/warning: Problems in the parameters — check before calculating:",
    "Error en cálculo: ": "Error in the calculation: ",
    "No se pudo generar el plomado definitivo: ":
        "The final plumb setting could not be generated: ",
    "No se pudo generar el informe admin para el correo: ":
        "The admin report for the email could not be generated: ",
    ":material/mail: Informe interno de administración enviado por correo.":
        ":material/mail: Internal management report sent by email.",
    ":material/smart_toy: Interpretaciones generadas correctamente.":
        ":material/smart_toy: Interpretations generated successfully.",
    ":material/check_circle: Cálculo e interpretación completados.":
        ":material/check_circle: Calculation and interpretation completed.",

    # ── plano y parámetros ─────────────────────────────────────────
    ":material/description: Plano del elevador": ":material/description: Lift drawing",
    ":green[:material/check_circle:] ": ":green[:material/check_circle:] ",
    " valor(es) tomados del plano del proyecto. Revísalos y completa los medidos en obra.":
        " value(s) taken from the project drawing. Check them and fill in the ones "
        "measured on site.",
    ":material/train: Riel del plano: **": ":material/train: Rail from the drawing: **",
    "** — ajusta RAIL si el catálogo no lo tiene.":
        "** — adjust RAIL if the catalogue does not have it.",
    "Marca": "Brand",
    "PDF de planos": "Drawings PDF",
    " parámetros encontrados.": " parameters found.",
    ":material/warning: Ingresar manualmente: **": ":material/warning: Enter by hand: **",
    ":material/description: Datos de: **": ":material/description: Data from: **",
    "** — ver sidebar.": "** — see the sidebar.",
    ":material/tune: Parámetros": ":material/tune: Parameters",
    "Leídos del plano": "Read from the drawing",
    ":green[:material/check_circle:] El plano aportó todos los parámetros.":
        ":green[:material/check_circle:] The drawing supplied every parameter.",
    "Parámetros del plano (editables)": "Drawing parameters (editable)",
    "**Otros**": "**Others**",
    "Parámetros medidos en obra": "Parameters measured on site",
    "**:material/tune: Configuración**": "**:material/tune: Configuration**",
    "Lado del Omega": "Omega side",
    "¿Hay pared limitante?": "Is there a limiting wall?",
    "Lado offset cabina": "Car offset side",
    "Parada limitante": "Limiting stop",
    "Lado de la pared": "Wall side",
    "¿Controlador hace parte del frame?": "Is the controller part of the frame?",
    "Lado del controlador": "Controller side",

    # ── matriz ─────────────────────────────────────────────────────
    ":material/grid_on: Matriz del survey": ":material/grid_on: Survey matrix",
    "Número de paradas (NS)": "Number of stops (NS)",
    ":material/folder_open: Cargar matriz (.xlsx)": ":material/folder_open: Load matrix (.xlsx)",
    "Restaurar también parámetros y configuración del Excel":
        "Also restore parameters and configuration from the Excel file",
    "Desmarcado: solo se importa la matriz de medidas.":
        "Unticked: only the measurement matrix is imported.",
    ":material/refresh: Volver a importar el Excel": ":material/refresh: Import the Excel again",
    "Error al importar Excel: ": "Error importing the Excel file: ",
    "Ingresa o edita las medidas en campo (mm).":
        "Enter or edit the measurements taken on site (mm).",
    ":material/download: Guardar matriz (.xlsx)": ":material/download: Save matrix (.xlsx)",
    " aviso(s) en los parámetros": " warning(s) in the parameters",
    ":material/play_arrow: Calcular y ver resultados":
        ":material/play_arrow: Calculate and see the results",
    ":material/summarize: Duplicar para el siguiente elevador":
        ":material/summarize: Duplicate for the next lift",
    "Conserva parámetros y configuración de este survey y limpia la matriz y los "
    "resultados. Útil cuando hay varios elevadores en el mismo hueco.":
        "Keeps this survey's parameters and configuration and clears the matrix and the "
        "results. Useful when there are several lifts in the same shaft.",
    ":material/summarize: Duplicar survey": ":material/summarize: Duplicate survey",

    # ── resultados / cronograma / informes ─────────────────────────
    ":material/insights: Resultados": ":material/insights: Results",
    "Aún no hay cálculo. Ve a **:material/edit: Datos del survey**, completa la "
    "información y pulsa **:material/play_arrow: Calcular y ver resultados**.":
        "No calculation yet. Go to **:material/edit: Survey data**, fill in the "
        "information and press **:material/play_arrow: Calculate and see the results**.",
    ":material/warning: Cambiaste datos desde el último cálculo. Lo de abajo corresponde "
    "al cálculo anterior — recalcula para actualizarlo.":
        ":material/warning: You changed data since the last calculation. What is below "
        "belongs to the previous one — recalculate to update it.",
    ":material/sync: Recalcular con los datos actuales":
        ":material/sync: Recalculate with the current data",
    ":material/calendar_month: Cronograma": ":material/calendar_month: Schedule",
    "Cronograma y curva S generados automáticamente según el proyecto (escalados por NS y "
    "por los hallazgos del análisis). Ajusta duraciones y pesos si lo necesitas — la "
    "curva S se recalcula sola.":
        "Schedule and S-curve generated automatically for the project (scaled by NS and "
        "by what the analysis found). Adjust durations and weights if you need to — the "
        "S-curve recalculates itself.",
    "Fecha de inicio del proyecto": "Project start date",
    "Duración total": "Total duration",
    " días": " days",
    "Inicio": "Start",
    "Fin estimado": "Estimated finish",
    "Realiza el cálculo primero para generar el cronograma.":
        "Do the calculation first to generate the schedule.",
    ":material/lock: La descarga de informes está disponible para administración "
    "(propietario / administrador).":
        ":material/lock: Report downloads are available to management (owner / "
        "administrator).",
    ":material/description: Informe del cliente": ":material/description: Client report",
    "Informe profesional para entregar al cliente (solución final, diagramas e "
    "instrucciones de implementación). El informe técnico interno se envía "
    "automáticamente por correo a administración.":
        "A professional report to hand to the client (final solution, diagrams and "
        "implementation instructions). The internal technical report is emailed to "
        "management automatically.",
    ".\n\nConfigura `ANTHROPIC_API_KEY` en los Secrets de Streamlit Cloud y vuelve a "
    "calcular.":
        ".\n\nConfigure `ANTHROPIC_API_KEY` in the Streamlit Cloud Secrets and calculate "
        "again.",
    ":material/description: Generar informe del cliente":
        ":material/description: Generate the client report",
    ":material/download: Descargar informe del cliente":
        ":material/download: Download the client report",
    "Realiza el cálculo primero para poder generar el informe.":
        "Do the calculation first so the report can be generated.",

    # ── guardar en el proyecto ─────────────────────────────────────
    ":material/save: Guardar en el proyecto": ":material/save: Save to the project",
    "Calcula primero para poder guardar el survey en un proyecto.":
        "Calculate first so the survey can be saved to a project.",
    ":material/lock: Requiere Google Sheets configurado.":
        ":material/lock: This needs Google Sheets configured.",
    "Se adjuntan los parámetros, la matriz y las interpretaciones al proyecto, y se "
    "archivan plano, matriz e informe del cliente. El cronograma y los avances del "
    "proyecto NO se tocan.":
        "The parameters, the matrix and the interpretations are attached to the project, "
        "and the drawing, the matrix and the client report are filed. The project's "
        "schedule and progress are NOT touched.",
    "Proyecto de destino": "Target project",
    "Elige a qué proyecto adjuntar este survey.":
        "Choose which project to attach this survey to.",
    ":material/warning: El proyecto tiene **NS = ": ":material/warning: The project has **NS = ",
    "** y este survey **NS = ": "** and this survey has **NS = ",
    "**. Revisa cuál es el correcto: el cronograma del proyecto se calculó con el suyo.":
        "**. Check which one is right: the project's schedule was worked out with its own.",
    ":material/save: Guardar el survey en este proyecto":
        ":material/save: Save the survey to this project",
    "No se pudo guardar: ": "It could not be saved: ",
    ":material/attach_file: Documentos archivados en Drive.":
        ":material/attach_file: Documents filed in Drive.",
    ":material/attach_file: Documentos no archivados: Drive no conectado.":
        ":material/attach_file: Documents not filed: Drive is not connected.",
    ":material/check_circle: Survey guardado en **":
        ":material/check_circle: Survey saved to **",
    "Proyecto **": "Project **",
    "** actualizado con este survey.": "** updated with this survey.",
    "Abrir proyecto ➜": "Open project ➜",
}
