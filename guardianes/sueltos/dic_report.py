# -*- coding: utf-8 -*-
"""Diccionario español → inglés del informe ADMIN (`report.py`).

Es un DOCUMENTO, así que va en el idioma BASE con `_d()` (alias: `d` ya es variable
en `fstr()`). ⚠️ Se excluyen las cadenas que se usan como ÍNDICE en algún sitio
—`'Duración (d)'`, `'Actividad'`…—: son el contrato con `schedule_table` y
`plumb_table`, y traducirlas deja la lectura buscando una clave que no existe.
"""
DIC = {
    # ── cabeceras de sección ──
    "1. PARÁMETROS DE ENTRADA": "1. INPUT PARAMETERS",
    "1.1  Extraídos del PDF": "1.1  Extracted from the PDF",
    "1.2  Ingresados por el usuario": "1.2  Entered by the user",
    "1.3  Condiciones y configuración del proyecto":
        "1.3  Project conditions and configuration",
    "2. DIMENSIONES DE CABINA": "2. CAR DIMENSIONS",
    "3. LÍMITES GEOMÉTRICOS": "3. GEOMETRIC LIMITS",
    "3.1  Límites laterales": "3.1  Side limits",
    "3.2  Límites frontales": "3.2  Front limits",
    "3.3  Límites Omega / Zona B": "3.3  Omega / Zone B limits",
    "4. CÁLCULO DE OFFSETS": "4. OFFSET CALCULATION",
    "5. MATRIZ SURVEY — MEDIDAS EN CAMPO": "5. SURVEY MATRIX — FIELD MEASUREMENTS",
    "6. MATRIZ SURVEY AJUSTADA Y ANÁLISIS": "6. ADJUSTED SURVEY MATRIX AND ANALYSIS",
    "6.1  Diferencias respecto a límites (columna por columna)":
        "6.1  Differences against limits (column by column)",
    "6.2  Estado inicial — límites incumplidos antes de la optimización":
        "6.2  Initial state — limits breached before optimisation",
    "7. OPTIMIZACIÓN — TRAZABILIDAD COMPLETA DE CADA PASO":
        "7. OPTIMISATION — FULL TRACEABILITY OF EVERY STEP",
    "7.1  Parámetros del optimizador": "7.1  Optimiser parameters",
    "7.2  Log de todos los pasos evaluados": "7.2  Log of every step evaluated",
    "8. DIAGRAMA DE POSICIONAMIENTO — PLANTA POR PISO":
        "8. POSITIONING DIAGRAM — FLOOR PLAN PER LEVEL",
    "9. ANÁLISIS BSR vs BS": "9. BSR vs BS ANALYSIS",
    "10. CONSIDERACIONES FINALES Y PUNTOS A VERIFICAR EN CAMPO":
        "10. FINAL CONSIDERATIONS AND POINTS TO CHECK ON SITE",
    "11. GESTIÓN DE PROYECTO — CRONOGRAMA Y CURVA S":
        "11. PROJECT MANAGEMENT — SCHEDULE AND S-CURVE",
    "12. ESQUEMA DE PLOMADO DEFINITIVO": "12. FINAL PLUMB LINE LAYOUT",

    # ── bloques de interpretación (IA) ──
    "🤖 Interpretación técnica": "🤖 Technical interpretation",
    "🤖 Interpretación — Análisis BSR vs BS":
        "🤖 Interpretation — BSR vs BS analysis",
    "🤖 Interpretación — Desplazamientos requeridos":
        "🤖 Interpretation — Required displacements",
    "🤖 Interpretación — Estado inicial del hueco":
        "🤖 Interpretation — Initial shaft state",
    "🤖 Interpretación — Evasión de pared limitante":
        "🤖 Interpretation — Limiting wall avoidance",
    "🤖 Interpretación — Geometría y configuración del proyecto":
        "🤖 Interpretation — Project geometry and configuration",
    "🤖 Interpretación — Solución óptima encontrada":
        "🤖 Interpretation — Optimal solution found",
    "🤖 Puntos críticos para el equipo de instalación":
        "🤖 Critical points for the installation team",

    # ── etiquetas y textos ──
    "Elevator Survey Analyzer — Reporte generado automáticamente":
        "Elevator Survey Analyzer — Automatically generated report",
    "Reporte de cálculo con trazabilidad completa — incluyendo cada paso del optimizador":
        "Calculation report with full traceability — including every optimiser step",
    "Análisis del estado de la cabina ajustada ANTES de aplicar cualquier desplazamiento:":
        "State of the adjusted car BEFORE applying any displacement:",
    "Valores medidos en obra antes de aplicar offsets:":
        "Values measured on site before applying offsets:",
    "Totales de la última fila de la matriz SURVEY:":
        "Totals from the last row of the SURVEY matrix:",
    "Matriz con desplazamientos aplicados:": "Matrix with displacements applied:",
    "Restricciones aplicadas en cada paso:": "Constraints applied at each step:",
    "Resumen de optimización": "Optimisation summary",
    "Rango de búsqueda RL": "RL search range",
    "Rango de búsqueda FB": "FB search range",
    "Diagrama de rango RL": "RL range diagram",
    "Diagrama de rango FB": "FB range diagram",
    "Diagrama no disponible en este entorno.":
        "Diagram not available in this environment.",
    "No hay solución para graficar.": "No solution to plot.",
    "No se encontró combinación válida.": "No valid combination was found.",
    "No se encontró paso en ningún rango.": "No step was found in any range.",
    "No se requiere ajuste de shaft": "No shaft adjustment required",
    "BSR >= BS  ->  Sin ajuste requerido": "BSR >= BS  ->  No adjustment required",
    "Buscando paso donde la resta de DIF BS llega a 0":
        "Looking for the step where the DIF BS subtraction reaches 0",
    "Búsqueda del paso en los 3 rangos (paso 0.5 mm):":
        "Step search across the 3 ranges (0.5 mm step):",
    "Ciclos de 0 hasta LIMIT ZB": "Cycles from 0 to LIMIT ZB",
    "Ciclos de LIMIT ZB hasta (LIMIT ZB + LIMIT OB)":
        "Cycles from LIMIT ZB to (LIMIT ZB + LIMIT OB)",
    "Ciclos de (LIMIT ZB + LIMIT OB) hasta 1000":
        "Cycles from (LIMIT ZB + LIMIT OB) to 1000",
    "Perfil longitudinal del hueco": "Longitudinal shaft profile",
    "Vista superior del encaje de la cabina en el shaft, piso a piso "
    "(matriz de la solución activa).":
        "Top view of how the car fits in the shaft, floor by floor "
        "(active solution matrix).",
    "Plomado con los desplazamientos determinados por el survey. El conjunto "
    "(plomos + paredes teóricas + template) se mueve rígido; las paredes reales "
    "no se tocan.":
        "Plumb lines with the displacements determined by the survey. The assembly "
        "(plumb lines + theoretical walls + template) moves as a rigid body; the "
        "real walls are not touched.",
    "Número de paradas (NS)": "Number of stops (NS)",
    "Lado del Omega": "Omega side",
    "Lado del controlador": "Controller side",
    "Controlador en frame?": "Controller in frame?",
    "- Controlador en frame:": "- Controller in frame:",
    "CS — Profundidad total de cabina": "CS — Total car depth",
    "TL — Profundidad del bloque cabina (riel a riel)":
        "TL — Car block depth (rail to rail)",
    "TLBC — Longitud total con espacio trasero":
        "TLBC — Total length including rear clearance",
    "BC_CALC — Espacio libre detras de la cabina":
        "BC_CALC — Free space behind the car",
    "25 mm    (holgura minima de seguridad al fondo)":
        "25 mm    (minimum safety clearance at the rear)",
    "VALIDO  (BC_CALC no restringe el rango FB)":
        "VALID  (BC_CALC does not restrict the FB range)",
    "FB_MAX_BACK = 0.0  (sin desplazamiento hacia atras)":
        "FB_MAX_BACK = 0.0  (no rearward displacement)",
    "OR/OL: si v > LIMIT -> requiere CORTE en la apertura de la puerta":
        "OR/OL: if v > LIMIT -> a CUT is required at the door opening",
    "CUT OR = OR - LIMIT OR  /  CUT OL = OL - LIMIT OL  "
    "(valor a cortar si supera el limite)":
        "CUT OR = OR - LIMIT OR  /  CUT OL = OL - LIMIT OL  "
        "(amount to cut if it exceeds the limit)",
    "Criterio 1: menor número de valores fuera de límite\n"
    "Criterio 2 (desempate): menor |RL| + |FB|":
        "Criterion 1: fewest values out of limit\n"
        "Criterion 2 (tie-break): lowest |RL| + |FB|",
    "Dif vs Límite": "Diff vs Limit",
    "Fórmula:": "Formula:",
}
