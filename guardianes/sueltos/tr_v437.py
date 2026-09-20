"""F1b — traduce el informe del CLIENTE al inglés.

⚠️ Se traducen ETIQUETAS, nunca CLAVES: los encabezados de las tablas de
cronograma y plomado cambian, pero `r["Actividad"]` / `r["Línea"]` siguen igual
— esas claves las produce `schedule.schedule_table` y `plumb.plumb_table`, así
que tocarlas rompería la lectura sin dar ningún error.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"C:\Users\diego\P1\survey_app\core\user_report.py")
s = p.read_text(encoding="utf-8")

R = [
    # ── portada ──
    ('canv.drawString(20 * mm, h - 110 * mm, "INFORME TÉCNICO")',
     'canv.drawString(20 * mm, h - 110 * mm, d("TECHNICAL REPORT"))'),
    ('canv.drawString(20 * mm, h - 121 * mm, "Posicionamiento")\n'
     '    canv.drawString(20 * mm, h - 133 * mm, "de elevador")',
     'canv.drawString(20 * mm, h - 121 * mm, d("Elevator"))\n'
     '    canv.drawString(20 * mm, h - 133 * mm, d("positioning"))'),
    ('filas = [("Cliente", meta.get("cliente") or "—", "Informe", meta.get("informe") or "—"),\n'
     '             ("Proyecto", meta.get("proyecto") or "—", "Fecha", meta.get("fecha") or "—"),\n'
     '             ("Ubicación", meta.get("ubicacion") or "—", "Paradas", str(meta.get("ns") or "—"))]',
     'filas = [(d("Client"), meta.get("cliente") or "—", d("Report"), meta.get("informe") or "—"),\n'
     '             (d("Project"), meta.get("proyecto") or "—", d("Date"), meta.get("fecha") or "—"),\n'
     '             (d("Location"), meta.get("ubicacion") or "—", d("Stops"), str(meta.get("ns") or "—"))]'),
    ('f"Preparado por: {meta.get(\'ingeniero\') or \'—\'}"',
     'd("Prepared by: {x}", x=meta.get("ingeniero") or "—")'),
    ('f"Página {pagina} de {total}"', 'd("Page {a} of {b}", a=pagina, b=total)'),

    # ── IA no disponible ──
    ('return [Paragraph("<i>Interpretación no disponible.</i>", styles["UBody"])]',
     'return [Paragraph(f"<i>{d(\'Interpretation not available.\')}</i>", styles["UBody"])]'),

    # ── ficha del proyecto ──
    ('_fila("Cliente", meta["cliente"], "Nº de informe", n_inf),\n'
     '        _fila("Proyecto", meta["proyecto"], "Fecha", fecha),\n'
     '        _fila("Ubicación", meta["ubicacion"], "Modelo", meta["modelo"]),\n'
     '        _fila("Ingeniero responsable", meta["ingeniero"], "Número de paradas", meta["ns"]),',
     '_fila(d("Client"), meta["cliente"], d("Report no."), n_inf),\n'
     '        _fila(d("Project"), meta["proyecto"], d("Date"), fecha),\n'
     '        _fila(d("Location"), meta["ubicacion"], d("Model"), meta["modelo"]),\n'
     '        _fila(d("Engineer in charge"), meta["ingeniero"], d("Number of stops"), meta["ns"]),'),

    # ── índice ──
    ('_idx = ["1. Resumen de la solución", "2. Posicionamiento final", "3. Cortes necesarios",\n'
     '            "4. Matriz de la solución", "5. Diagramas de planta por piso"]',
     '_idx = [d("1. Solution summary"), d("2. Final positioning"), d("3. Cuts required"),\n'
     '            d("4. Solution matrix"), d("5. Floor plan diagrams")]'),
    ('_idx.append("6. Cronograma y curva S")', '_idx.append(d("6. Schedule and S-curve"))'),
    ('_idx += ["7. Implementación en obra", "8. Verificación final"]',
     '_idx += [d("7. Site implementation"), d("8. Final verification")]'),
    ('_idx.append("9. Esquema de plomado definitivo")',
     '_idx.append(d("9. Final plumb line layout"))'),
    ('_idx += ["10. Alcance y metodología", "11. Glosario de términos", "12. Conclusiones"]',
     '_idx += [d("10. Scope and methodology"), d("11. Glossary"), d("12. Conclusions")]'),
    ('Paragraph("<b>Contenido</b>", styles["UBody"])',
     'Paragraph(f"<b>{d(\'Contents\')}</b>", styles["UBody"])'),

    # ── títulos de sección ──
    ('_section("1. Resumen de la solución", styles)', '_section(d("1. Solution summary"), styles)'),
    ('_section("2. Posicionamiento final", styles)', '_section(d("2. Final positioning"), styles)'),
    ('_section("3. Cortes necesarios", styles)', '_section(d("3. Cuts required"), styles)'),
    ('_section("4. Matriz de la solución (por piso)", styles)',
     '_section(d("4. Solution matrix (by floor)"), styles)'),
    ('_section("5. Diagramas del hueco", styles)', '_section(d("5. Shaft diagrams"), styles)'),
    ('_section("6. Cronograma y curva S del proyecto", styles)',
     '_section(d("6. Project schedule and S-curve"), styles)'),
    ('_section("7. Implementación en obra", styles)', '_section(d("7. Site implementation"), styles)'),
    ('_section("8. Verificación final", styles)', '_section(d("8. Final verification"), styles)'),
    ('_section("9. Esquema de plomado definitivo", styles)',
     '_section(d("9. Final plumb line layout"), styles)'),
    ('_section("10. Alcance y metodología", styles)',
     '_section(d("10. Scope and methodology"), styles)'),
    ('_section("11. Glosario de términos", styles)', '_section(d("11. Glossary"), styles)'),
    ('_section("12. Conclusiones", styles)', '_section(d("12. Conclusions"), styles)'),

    # ── KPI + acción principal ──
    ('("Desplazamiento lateral (RL)", f"{rl:+.1f} mm", None),\n'
     '            ("Desplazamiento frontal (FB)", f"{fb:+.1f} mm", None),\n'
     '            ("Valores fuera de límite", f"{off}", "#1e8449" if off == 0 else "#c0392b"),\n'
     '            ("Paradas", str(meta["ns"]), None),',
     '(d("Lateral shift (RL)"), f"{rl:+.1f} mm", None),\n'
     '            (d("Front shift (FB)"), f"{fb:+.1f} mm", None),\n'
     '            (d("Values out of limit"), f"{off}", "#1e8449" if off == 0 else "#c0392b"),\n'
     '            (d("Stops"), str(meta["ns"]), None),'),
    ('            f"<b>Acción principal:</b> desplazar el bloque de cabina <b>{abs(rl):.1f} mm</b> hacia "\n'
     '            f"{\'la derecha\' if rl >= 0 else \'la izquierda\'} y <b>{abs(fb):.1f} mm</b> hacia "\n'
     '            f"{\'atrás\' if fb >= 0 else \'adelante\'} respecto a la posición de diseño.", styles), _sp(8)]',
     '            d("<b>Main action:</b> shift the car block <b>{lat} mm</b> to the {dir_lat} "\n'
     '              "and <b>{frt} mm</b> to the {dir_frt}, relative to the design position.",\n'
     '              lat=f"{abs(rl):.1f}", frt=f"{abs(fb):.1f}",\n'
     '              dir_lat=d("right") if rl >= 0 else d("left"),\n'
     '              dir_frt=d("rear") if fb >= 0 else d("front")), styles), _sp(8)]'),
    ('Paragraph("No se encontró una solución válida.", styles["UBody"])',
     'Paragraph(d("No valid solution was found."), styles["UBody"])'),
    ('Paragraph("<b>Desplazamientos a realizar:</b>", styles["UBody"])',
     'Paragraph(f"<b>{d(\'Shifts to carry out:\')}</b>", styles["UBody"])'),

    # ── matriz ──
    ('header = [Paragraph("<b>Piso</b>", styles["UCell"])] + \\',
     'header = [Paragraph(f"<b>{d(\'Floor\')}</b>", styles["UCell"])] + \\'),
    ('Paragraph("Celdas en rojo: valores que requieren atención (holgura por debajo del "\n'
     '                            "mínimo, o apertura que requiere corte).", styles["USmall"])',
     'Paragraph(d("Cells in red: values needing attention (clearance below the minimum, "\n'
     '                              "or an opening that requires cutting)."), styles["USmall"])'),

    # ── diagramas ──
    ('Paragraph("Plantas a proporción real, con cotas acotadas contra su límite. "\n'
     '                            "Las cotas en <b>rojo</b> son las que quedan fuera de límite; el "\n'
     '                            "resto cumple. Cuando una holgura es muy ajustada se añade un "\n'
     '                            "<b>Detalle</b> ampliado de esa esquina.",\n'
     '                            styles["UInfo"])',
     'Paragraph(d("Floor plans drawn to real proportion, with every dimension checked "\n'
     '                              "against its limit. Dimensions in <b>red</b> are out of limit; the "\n'
     '                              "rest comply. Where a clearance is very tight, an enlarged "\n'
     '                              "<b>Detail</b> of that corner is added."),\n'
     '                            styles["UInfo"])'),

    # ── cronograma ──
    ('Paragraph(f"Inicio: <b>{schedule[\'start_date\'].strftime(\'%d/%m/%Y\')}</b>  ·  "\n'
     '                            f"Fin estimado: <b>{schedule[\'fecha_fin\'].strftime(\'%d/%m/%Y\')}</b>  ·  "\n'
     '                            f"Duración total: <b>{schedule[\'total_dias\']} días</b>.", styles["UBody"])',
     'Paragraph(d("Start: <b>{ini}</b>  ·  Estimated finish: <b>{fin}</b>  ·  "\n'
     '                              "Total duration: <b>{n} days</b>.",\n'
     '                              ini=schedule["start_date"].strftime("%d/%m/%Y"),\n'
     '                              fin=schedule["fecha_fin"].strftime("%d/%m/%Y"),\n'
     '                              n=schedule["total_dias"]), styles["UBody"])'),
    # ⚠️ SOLO el encabezado: las claves del dict las produce schedule.schedule_table
    ('                 ["Actividad", "Inicio", "Fin", "Días", "Peso %"]]',
     '                 [d("Activity"), d("Start"), d("Finish"), d("Days"), d("Weight %")]]'),

    # ── plomado ──
    ('Paragraph("Ubicación final de las líneas de plomada con los desplazamientos del "\n'
     '                            "análisis. El conjunto (plomos, paredes teóricas y template) se desplaza "\n'
     '                            "en bloque; las paredes reales quedan fijas. El eje cero es la pared real "\n'
     '                            "izquierda.", styles["UBody"])',
     'Paragraph(d("Final position of the plumb lines including the shifts from the "\n'
     '                              "analysis. The assembly (plumb lines, theoretical walls and "\n'
     '                              "template) moves as one block; the real walls stay fixed. The "\n'
     '                              "zero axis is the left real wall."), styles["UBody"])'),
    ('                f"Desplazamiento aplicado: lateral = <b>{_pd.get(\'rl\', 0):.1f} mm</b> · "\n'
     '                f"frontal = <b>{_pd.get(\'fb\', 0):.1f} mm</b>.", styles["UBody"])',
     '                d("Shift applied: lateral = <b>{a} mm</b> · front = <b>{b} mm</b>.",\n'
     '                  a=f"{_pd.get(\'rl\', 0):.1f}", b=f"{_pd.get(\'fb\', 0):.1f}"), styles["UBody"])'),
    ('_callout("<b>Ficha de replanteo</b> — los valores a medir con cinta "\n'
     '                               "en obra. La comprobación de cierre debe dar BSR.", styles)',
     '_callout(d("<b>Set-out card</b> — the values to measure with a tape on "\n'
     '                                 "site. The closing check must add up to BSR."), styles)'),
    ('                 ["Línea", "X inicial (mm)", "X final (mm)", "Desplazada"]]',
     '                 [d("Line"), d("Initial X (mm)"), d("Final X (mm)"), d("Shifted")]]'),
    ('Paragraph("<b>Verificación en campo — distancias plomo ↔ pared real</b>",\n'
     '                            styles["UBody"])',
     'Paragraph(f"<b>{d(\'Site verification — plumb line ↔ real wall distances\')}</b>",\n'
     '                            styles["UBody"])'),
    ('chead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in ["Medida", "Distancia (mm)"]]',
     'chead = [Paragraph(f"<b>{h}</b>", styles["UCell"]) for h in [d("Measurement"), d("Distance (mm)")]]'),

    # ── 10. Alcance ──
    ('        "Este informe determina la <b>posición óptima del bloque de cabina</b> (rieles y guías) dentro "\n'
     '        "del hueco existente, a partir de las medidas tomadas en obra nivel a nivel y de los parámetros "\n'
     '        "del plano del fabricante.", styles["UBody"])',
     '        d("This report determines the <b>optimum position of the car block</b> (rails and "\n'
     '          "guides) within the existing shaft, based on the measurements taken on site level "\n'
     '          "by level and on the parameters of the manufacturer\'s drawing."), styles["UBody"])'),
    ('        "<b>Qué se midió:</b> en cada parada se registran las holguras laterales (izquierda y derecha), "\n'
     '        "la distancia de la pared frontal al eje de rieles y el espacio disponible a cada lado de la "\n'
     '        "apertura de puerta de rellano.", styles["UBody"])',
     '        d("<b>What was measured:</b> at every stop we record the side clearances (left and "\n'
     '          "right), the distance from the front wall to the rail axis, and the space available "\n'
     '          "on each side of the landing door opening."), styles["UBody"])'),
    ('        "<b>Cómo se evalúa:</b> cada medida se compara contra su límite admisible. Se busca la "\n'
     '        "combinación de desplazamiento lateral y frontal que minimiza los incumplimientos, respetando "\n'
     '        "las restricciones físicas del hueco y, cuando aplica, la pared limitante y el controlador "\n'
     '        "integrado en el marco.", styles["UBody"])',
     '        d("<b>How it is assessed:</b> every measurement is compared against its allowable "\n'
     '          "limit. We look for the combination of lateral and front shift that minimises the "\n'
     '          "breaches, respecting the physical constraints of the shaft and, where it applies, "\n'
     '          "the limiting wall and the controller built into the frame."), styles["UBody"])'),
    ('        "<b>Limitaciones y validez.</b> Las conclusiones se basan en las medidas aportadas y en los "\n'
     '        "parámetros del plano vigentes a la fecha del informe. Cambios en el hueco, en el equipo o "\n'
     '        "medidas tomadas con criterios distintos pueden alterar el resultado. Los valores están "\n'
     '        "expresados en milímetros y deben verificarse en obra antes del montaje definitivo.",\n'
     '        styles, color=C_ORANGE)',
     '        d("<b>Limitations and validity.</b> The conclusions are based on the measurements "\n'
     '          "supplied and on the drawing parameters current at the date of this report. Changes "\n'
     '          "to the shaft or to the equipment, or measurements taken to different criteria, may "\n'
     '          "alter the result. All values are in millimetres and must be verified on site before "\n'
     '          "final installation."),\n'
     '        styles, color=C_ORANGE)'),

    # ── 11. Glosario ──
    ('        ("RL", "Desplazamiento lateral del bloque de cabina respecto al diseño."),\n'
     '        ("FB", "Desplazamiento frontal (hacia el fondo o hacia la puerta)."),\n'
     '        ("WR / WL", "Holgura entre el bloque de cabina y la pared derecha / izquierda."),\n'
     '        ("FR / FL", "Distancia de la pared frontal al eje del riel derecho / izquierdo."),\n'
     '        ("OR / OL", "Espacio a la derecha / izquierda en la apertura de puerta de rellano."),\n'
     '        ("BS / BSR", "Ancho del hueco según plano / ancho realmente medido en obra."),\n'
     '        ("Plomada", "Línea vertical de referencia para alinear los rieles en toda la altura."),\n'
     '        ("Corte", "Material a retirar cuando la apertura supera el límite admisible."),',
     '        ("RL", d("Lateral shift of the car block relative to the design.")),\n'
     '        ("FB", d("Front shift (towards the rear wall or towards the door).")),\n'
     '        ("WR / WL", d("Clearance between the car block and the right / left wall.")),\n'
     '        ("FR / FL", d("Distance from the front wall to the right / left rail axis.")),\n'
     '        ("OR / OL", d("Space to the right / left in the landing door opening.")),\n'
     '        ("BS / BSR", d("Shaft width per drawing / width actually measured on site.")),\n'
     '        (d("Plumb line"), d("Vertical reference line used to align the rails over the "\n'
     '                            "full height.")),\n'
     '        (d("Cut"), d("Material to be removed when the opening exceeds the allowable limit.")),'),

    # ── 12. Conclusiones y firma ──
    ('            f"El posicionamiento propuesto es RL {best.get(\'rl\', 0):+.1f} mm y "\n'
     '            f"FB {best.get(\'fb_applied\', best.get(\'fb\', 0)):+.1f} mm.",\n'
     '            "Los diagramas de planta muestran, piso a piso, cómo queda el encaje de la cabina.",',
     '            d("The proposed positioning is RL {rl} mm and FB {fb} mm.",\n'
     '              rl=f"{best.get(\'rl\', 0):+.1f}",\n'
     '              fb=f"{best.get(\'fb_applied\', best.get(\'fb\', 0)):+.1f}"),\n'
     '            d("The floor plans show, level by level, how the car fits in the shaft."),'),
    ('            _concl.append(f"Quedan {_off} valor(es) fuera de límite: revisar las celdas marcadas en "\n'
     '                          "la matriz antes de fijar los brackets.")\n'
     '        else:\n'
     '            _concl.append("No quedan valores fuera de límite con la solución adoptada.")\n'
     '        _concl.append("Verificar en obra las distancias de plomada indicadas antes del montaje definitivo.")',
     '            _concl.append(d("{n} value(s) remain out of limit: review the cells marked in the "\n'
     '                            "matrix before fixing the brackets.", n=_off))\n'
     '        else:\n'
     '            _concl.append(d("No values remain out of limit with the solution adopted."))\n'
     '        _concl.append(d("Verify the plumb line distances shown on site before final installation."))'),
    ('        [Paragraph("<font size=8 color=\'#666666\'>PREPARADO POR</font><br/><br/><br/>"\n'
     '                   "_______________________________<br/>"\n'
     '                   f"<b>{meta[\'ingeniero\']}</b><br/>"\n'
     '                   "<font size=8 color=\'#666666\'>Ingeniero responsable · COPEX</font>", styles["UInfo"]),\n'
     '         Paragraph("<font size=8 color=\'#666666\'>RECIBIDO POR</font><br/><br/><br/>"\n'
     '                   "_______________________________<br/>"\n'
     '                   f"<b>{meta[\'cliente\']}</b><br/>"\n'
     '                   "<font size=8 color=\'#666666\'>Nombre, cargo y fecha</font>", styles["UInfo"])],',
     '        [Paragraph(f"<font size=8 color=\'#666666\'>{d(\'PREPARED BY\')}</font><br/><br/><br/>"\n'
     '                   "_______________________________<br/>"\n'
     '                   f"<b>{meta[\'ingeniero\']}</b><br/>"\n'
     '                   f"<font size=8 color=\'#666666\'>{d(\'Engineer in charge\')} · COPEX</font>",\n'
     '                   styles["UInfo"]),\n'
     '         Paragraph(f"<font size=8 color=\'#666666\'>{d(\'RECEIVED BY\')}</font><br/><br/><br/>"\n'
     '                   "_______________________________<br/>"\n'
     '                   f"<b>{meta[\'cliente\']}</b><br/>"\n'
     '                   f"<font size=8 color=\'#666666\'>{d(\'Name, position and date\')}</font>",\n'
     '                   styles["UInfo"])],'),
    ('Paragraph(f"COPEX · Elevator Survey Analyzer · {n_inf} · Generado el {fecha}",\n'
     '                        styles["USmall"])',
     'Paragraph(d("COPEX · Elevator Survey Analyzer · {n} · Generated on {f}",\n'
     '                          n=n_inf, f=fecha), styles["USmall"])'),
]

falt = [o for o, _ in R if s.count(o) != 1]
if falt:
    print(f"⚠️ {len(falt)} anclas NO casan exactamente una vez:")
    for x in falt:
        print("   ···", x[:110].replace("\n", " ⏎ "), f"  (veces={s.count(x)})")
    sys.exit(1)

for o, n in R:
    s = s.replace(o, n, 1)
p.write_text(s, encoding="utf-8")
print(f"OK — {len(R)} reemplazos aplicados en user_report.py")
