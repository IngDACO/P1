"""F4-A · Las cuatro herramientas de cálculo: plomadas, rieles, buffers, belting.

⚠️ NO se traduce NINGUNA sigla del plano ni del dominio: BKS, RAIL, TKSW, SF1, SF2, BS,
BSR, SG, TG, DBP, DBPW, LengthTemplate, LFKK, LFGK, HKP, HKPR, HQ, HGP, HGPR, DSTS, RC,
RCW, RZ, RO, RF, RB, FFL, LIMIT_ZB, LIMIT_OB, DIF, Omega, Z. Son los NOMBRES que trae el
plano Schindler y por los que el técnico las busca; traducirlas haría ilegible la
herramienta y rompería la correspondencia con el PDF que tiene delante.
⚠️ Tampoco «Caso 1 / Caso 2» pierde su número: es el nombre del caso en el dominio.
Vocabulario: shaft → shaft (se usa en inglés ya en el original) · plomada → plumb line ·
replanteo → setting out · cortes → cuts · encaje → fit · plantilla → template.
"""
TRAD = {
    # ── plumb_ui ───────────────────────────────────────────────────
    "### :material/straighten: Cálculo de líneas de plomada":
        "### :material/straighten: Plumb line calculation",
    "Una **plantilla** para el shaft; el **BSR se mide por elevador**. Los valores del "
    "plano se rellenan solos; RAIL sale del catálogo.":
        "One **template** for the shaft; the **BSR is measured per lift**. The values "
        "from the drawing fill themselves in; RAIL comes from the catalogue.",
    ":material/replay: Reabierto el cálculo **": ":material/replay: Reopened calculation **",
    "**. Ajusta lo que necesites y vuelve a calcular.":
        "**. Adjust whatever you need and calculate again.",
    ":green[:material/check_circle:] ": ":green[:material/check_circle:] ",
    " valor(es) tomados del plano del proyecto.":
        " value(s) taken from the project drawing.",
    "¿El proyecto no tiene plano? Cárgalo aquí":
        "Does the project have no drawing? Upload it here",
    "Se leerá BKS, TKSW, SF1, SF2, BS, SG y TG de este PDF.":
        "BKS, TKSW, SF1, SF2, BS, SG and TG will be read from this PDF.",
    ":material/check_circle: Del plano: **": ":material/check_circle: From the drawing: **",
    "**. Completa LengthTemplate; RAIL sale del código de riel; el BSR se mide por "
    "elevador.":
        "**. Fill in LengthTemplate; RAIL comes from the rail code; the BSR is measured "
        "per lift.",
    "No se encontraron valores en el plano. Ingrésalos manualmente.":
        "No values were found in the drawing. Enter them by hand.",
    ":material/description: Plano cargado: **":
        ":material/description: Drawing loaded: **",
    "**Plantilla del shaft (compartida)**  ·  :material/description: = del plano · ✏️ = "
    "manual":
        "**Shaft template (shared)**  ·  :material/description: = from the drawing · "
        "✏️ = by hand",
    ":material/description: BKS (mm)": ":material/description: BKS (mm)",
    ":material/description: RAIL (mm)": ":material/description: RAIL (mm)",
    ":material/description: TKSW (mm)": ":material/description: TKSW (mm)",
    ":material/edit: LengthTemplate (mm)": ":material/edit: LengthTemplate (mm)",
    ":material/description: SF1 (mm)": ":material/description: SF1 (mm)",
    ":material/description: SF2 (mm)": ":material/description: SF2 (mm)",
    ":material/description: BS (mm)": ":material/description: BS (mm)",
    "Datos de encaje (SG, TG, lado Omega) — se usan cuando un BSR < BS":
        "Fit data (SG, TG, Omega side) — used when a BSR < BS",
    ":material/description: SG (mm)": ":material/description: SG (mm)",
    ":material/description: TG (mm)": ":material/description: TG (mm)",
    ":material/edit: Lado del Omega": ":material/edit: Omega side",
    "**BSR medido en cada elevador (mm)**": "**BSR measured on each lift (mm)**",
    "¿Cuántos elevadores hay en el shaft?": "How many lifts are there in the shaft?",
    ":material/straighten: Calcular plomadas": ":material/straighten: Calculate plumb lines",
    "#### :material/architecture: La plantilla (igual para todos los elevadores)":
        "#### :material/architecture: The template (the same for every lift)",
    "DBP": "DBP",
    "DBPW": "DBPW",
    "DBP = separación de los plomos · d1/d2 = diagonales plantilla→plomo (se miden con "
    "cinta).":
        "DBP = spacing between the plumb points · d1/d2 = template→plumb diagonals "
        "(measured with a tape).",
    ":material/warning: **BS incoherente:** el plano dice **":
        ":material/warning: **BS does not add up:** the drawing says **",
    "** pero SF1+BKS+2·RAIL+SF2 = **": "** but SF1+BKS+2·RAIL+SF2 = **",
    "** (dif ": "** (diff ",
    " mm). Con este desajuste los plomos quedan mal ubicados. Revisa BS, SF1, SF2, BKS o "
    "RAIL.":
        " mm). With this mismatch the plumb points end up in the wrong place. Check BS, "
        "SF1, SF2, BKS or RAIL.",
    "#### :material/elevator: Por elevador — encaje y verificación":
        "#### :material/elevator: Per lift — fit and check",
    "Comprobación de obra: **di + DBP + dd = BSR**. Si no cierra, hay error de medida.":
        "On-site check: **di + DBP + dd = BSR**. If it does not add up, there is a "
        "measurement error.",
    "#### :material/architecture: Diagramas de un elevador":
        "#### :material/architecture: Diagrams for one lift",
    "Ver el replanteo del elevador": "View the setting out for lift",
    "Elevador ": "Lift ",
    ": BSR > BS → el conjunto se **centra** (holgura ":
        ": BSR > BS → the assembly is **centred** (clearance ",
    " mm/lado).": " mm/side).",
    ":material/warning: Elevador ": ":material/warning: Lift ",
    ": NO CABE — sacrificar ": ": DOES NOT FIT — it would need ",
    " mm del Omega, pero el límite es ": " mm off the Omega, but the limit is ",
    ": BSR < BS → **acerca el conjunto ": ": BSR < BS → **move the assembly ",
    " mm al lado ": " mm towards the ",
    "** (Omega ": "** side (Omega ",
    " del otro lado).": " on the other side).",
    "Detalle del encaje (umbrales internos)": "Fit detail (internal thresholds)",
    "DIF = ": "DIF = ",
    " · LIMIT_ZB = ": " · LIMIT_ZB = ",
    " · LIMIT_OB = ": " · LIMIT_OB = ",
    " · sacrificio Z = ": " · Z give-up = ",
    " · sacrificio Omega = ": " · Omega give-up = ",
    ": BSR = BS → sin desplazar.": ": BSR = BS → no shift.",
    "Vistas 3D del replanteo": "3D views of the setting out",
    "Ficha de replanteo (para obra)": "Setting-out card (for site)",
    "Los números a medir con cinta. Imprímela o ábrela en el móvil.":
        "The numbers to measure with a tape. Print it or open it on your phone.",

    # ── rail_cut_ui ────────────────────────────────────────────────
    "### :material/content_cut: Corte de rieles": "### :material/content_cut: Rail cutting",
    "Calcula el corte de los rieles de cada elevador del shaft. LFKK y LFGK salen del "
    "plano del proyecto; si falta, se ingresan a mano.":
        "Works out the rail cut for each lift in the shaft. LFKK and LFGK come from the "
        "project drawing; if it is missing, they are entered by hand.",
    ":green[:material/check_circle:] LFKK y LFGK tomado(s) del plano del proyecto.":
        ":green[:material/check_circle:] LFKK and LFGK taken from the project drawing.",
    "**1. Parámetros del plano (LFKK, LFGK)**": "**1. Drawing parameters (LFKK, LFGK)**",
    "Se leerá LFKK y LFGK de este PDF. Lo normal es que ya vengan del plano del proyecto.":
        "LFKK and LFGK will be read from this PDF. Normally they already come from the "
        "project drawing.",
    "Encontrados en el PDF: ": "Found in the PDF: ",
    ". Verifica o completa abajo.": ". Check or complete below.",
    "LFKK (mm)": "LFKK (mm)",
    "LFGK (mm)": "LFGK (mm)",
    "**2. Elevadores en el shaft**": "**2. Lifts in the shaft**",
    "**3. Caso de corte**": "**3. Cutting case**",
    "¿Qué riel se corta?": "Which rail is cut?",
    "**Caso 1 — datos**": "**Case 1 — data**",
    "Nº de rieles de 2500 mm": "No. of 2500 mm rails",
    "Nº de rieles de 5000 mm": "No. of 5000 mm rails",
    "**L de cada elevador** (FFL del piso más alto → fondo del shaft):":
        "**L for each lift** (FFL of the top floor → bottom of the shaft):",
    ":material/content_cut: Calcular cortes (Caso 1)":
        ":material/content_cut: Calculate cuts (Case 1)",
    "A (pila instalada)": "A (stack installed)",
    "Detalle (RC, RCW)": "Detail (RC, RCW)",
    "**Caso 2 — sub-caso**": "**Case 2 — sub-case**",
    "El penúltimo riel está…": "The second-to-last rail is…",
    "**Matriz de entrada** (llena RZ, RO, RF, RB de cada elevador):":
        "**Input matrix** (fill in RZ, RO, RF, RB for each lift):",
    ":material/content_cut: Calcular cortes (Caso 2)":
        ":material/content_cut: Calculate cuts (Case 2)",
    "Fórmula": "Formula",
    "LFKK": "LFKK",
    "LFGK": "LFGK",
    "Elevadores": "Lifts",
    "Sub-caso: ": "Sub-case: ",
    "Resultado — cortes (mm)": "Result — cuts (mm)",
    ":material/architecture: Diagrama de cortes": ":material/architecture: Cutting diagram",

    # ── buffer_cut_ui ──────────────────────────────────────────────
    "### :material/shield: Corte de buffers": "### :material/shield: Buffer cutting",
    "Calcula cuánto cortar cada buffer. **HKP** sale del plano del proyecto; tú indicas "
    "el **HKPR** real medido en cada buffer.":
        "Works out how much to cut off each buffer. **HKP** comes from the project "
        "drawing; you enter the actual **HKPR** measured on each buffer.",
    ":green[:material/check_circle:] HKP tomado(s) del plano del proyecto.":
        ":green[:material/check_circle:] HKP taken from the project drawing.",
    "**1. Parámetro del plano (HKP)**": "**1. Drawing parameter (HKP)**",
    "Se leerá HKP de este PDF. Lo normal es que ya vengan del plano del proyecto.":
        "HKP will be read from this PDF. Normally it already comes from the project "
        "drawing.",
    "HKP encontrado en el PDF: ": "HKP found in the PDF: ",
    " mm. Verifica abajo.": " mm. Check below.",
    "No se encontró HKP en el PDF. Ingrésalo manualmente.":
        "HKP was not found in the PDF. Enter it by hand.",
    "HKP (mm) — sticker de cabina ↔ buffer sirviendo el 1er nivel":
        "HKP (mm) — car sticker ↔ buffer serving the 1st level",
    "**2. Buffers**": "**2. Buffers**",
    "¿Cuántos buffers hay?": "How many buffers are there?",
    "**3. HKPR real de cada buffer (mm)**": "**3. Actual HKPR of each buffer (mm)**",
    ":material/shield: Calcular cortes": ":material/shield: Calculate cuts",
    "HKP (plano)": "HKP (drawing)",
    "Buffers": "Buffers",
    "A revisar": "To check",
    "Corte = HKP − HKPR (por buffer).": "Cut = HKP − HKPR (per buffer).",
    ":material/warning: Un corte negativo significa que el HKPR real supera al HKP del "
    "plano: no hay nada que cortar en ese buffer, revísalo en obra.":
        ":material/warning: A negative cut means the actual HKPR is greater than the HKP "
        "on the drawing: there is nothing to cut off that buffer, check it on site.",
    ":material/architecture: Diagrama": ":material/architecture: Diagram",

    # ── belting_ui ─────────────────────────────────────────────────
    "### :material/swap_vert: Belting — posición de la cabina para instalar los belts":
        "### :material/swap_vert: Belting — car position for installing the belts",
    "Calcula **DSTS** = cuánto bajar la cabina bajo el FFL del piso más alto para "
    "instalar los belts respetando el recorrido de diseño.  DSTS = HGPR − HGP − HQ/1000 "
    "(mm), por elevador.":
        "Works out **DSTS** = how far to lower the car below the FFL of the top floor to "
        "install the belts while respecting the design travel.  DSTS = HGPR − HGP − "
        "HQ/1000 (mm), per lift.",
    ":green[:material/check_circle:] HQ y HGP tomado(s) del plano del proyecto.":
        ":green[:material/check_circle:] HQ and HGP taken from the project drawing.",
    "Se leerá HQ y HGP de este PDF. Lo normal es que ya vengan del plano del proyecto.":
        "HQ and HGP will be read from this PDF. Normally they already come from the "
        "project drawing.",
    " mm**. Ingresa los HGPR reales de cada elevador.":
        " mm**. Enter the actual HGPR for each lift.",
    "No se encontraron HQ/HGP en el plano. Ingrésalos a mano.":
        "HQ/HGP were not found in the drawing. Enter them by hand.",
    "**Datos**  ·  :material/description: = del plano · ✏️ = manual":
        "**Data**  ·  :material/description: = from the drawing · ✏️ = by hand",
    ":material/description: HQ — travel height (mm)":
        ":material/description: HQ — travel height (mm)",
    ":material/description: HGP — striker↔buffer de diseño (mm)":
        ":material/description: HGP — design striker↔buffer (mm)",
    "Número de elevadores": "Number of lifts",
    "**:material/edit: HGPR — distancia REAL striker↔buffer del contrapeso, por elevador "
    "(mm)**":
        "**:material/edit: HGPR — ACTUAL striker↔buffer distance on the counterweight, "
        "per lift (mm)**",
    "HGPR elevador ": "HGPR lift ",
    ":material/swap_vert: Calcular belting": ":material/swap_vert: Calculate belting",
    "HQ (travel)": "HQ (travel)",
    "HGP (diseño)": "HGP (design)",
    ":material/table_rows: Resultados (DSTS por elevador)":
        ":material/table_rows: Results (DSTS per lift)",
}
