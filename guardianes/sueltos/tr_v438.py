"""F1c — las etiquetas de los DIAGRAMAS y las PLOMADAS, en inglés. Cierra F1.

Solo se traduce lo que se PINTA. Quedan fuera, a propósito:

 · las CLAVES de `schedule_table` / `plumb_table` / `plumb_checks` (`Actividad`,
   `Línea`, `Medida`, `Duración (d)`…): las indexan `report.py` y `user_report.py`,
   así que tocarlas daría KeyError o una columna vacía;
 · los NOMBRES de `schedule.ACTIVIDADES`: son DATO — se guardan en la hoja
   `Actividades` de cada proyecto, así que van en la migración del histórico;
 · las claves internas (`origen`, `peso`, `inicio`, `cortes`, `izq`, `der`,
   `cabina`, `contra`, `elevador`): banderas, no texto.

⚠️ El motor se importa con ALIAS **`_d`**, no como `d`. En estos seis módulos `d` ya
es una variable corriente (días, dicts, deltas) en **14 sitios**, y Python marca el
nombre local en el ÁMBITO ENTERO de la función: un `d = 0` al final del cuerpo
reventaría las etiquetas de arriba con UnboundLocalError. Es el fallo del glosario de
v437, y renombrar 14 variables es más riesgo que aliasear el import.
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

PLUMB = [
    ('    "V1": "Plomo riel izquierdo",\n'
     '    "V2": "Plomo riel derecho",\n'
     '    "V3": "Pared teórica izquierda",\n'
     '    "V4": "Pared real izquierda",\n'
     '    "V5": "Pared teórica derecha",\n'
     '    "V6": "Pared real derecha",',
     '    # ⚠️ Son ETIQUETAS: nadie compara contra ellas (barrido de todo el repo),\n'
     '    # solo se pintan y viajan como VALOR de la clave "Línea", que sí es dato.\n'
     '    "V1": _d("Left rail plumb line"),\n'
     '    "V2": _d("Right rail plumb line"),\n'
     '    "V3": _d("Left theoretical wall"),\n'
     '    "V4": _d("Left real wall"),\n'
     '    "V5": _d("Right theoretical wall"),\n'
     '    "V6": _d("Right real wall"),'),
    ('    "V1": "Riel I",  "V2": "Riel D",',
     '    "V1": _d("Rail L"),  "V2": _d("Rail R"),'),
    ('    "V3": "Teór I",  "V5": "Teór D",\n    "V4": "Real I",  "V6": "Real D",',
     '    "V3": _d("Theor L"),  "V5": _d("Theor R"),\n'
     '    "V4": _d("Real L"),  "V6": _d("Real R"),'),
    ('letter-spacing="0.1em">PARED FRONTAL</text>',
     'letter-spacing="0.1em">{_d("FRONT WALL")}</text>'),
    ('fill="#667080">pared teórica</text>', 'fill="#667080">{_d("theoretical wall")}</text>'),
    ('fill="#5b6472">plantilla</text>', 'fill="#5b6472">{_d("template")}</text>'),
    ('font-weight="bold">COMPROBAR EN OBRA</text>',
     'font-weight="bold">{_d("CHECK ON SITE")}</text>'),
    ('font-weight="bold">COMPROBACIÓN</text>', 'font-weight="bold">{_d("CHECK")}</text>'),
    ('Proporción real · cotas en mm</text>',
     '{_d("Real proportion · dimensions in mm")}</text>'),
    ('Origen X: pared real izquierda</text>', '{_d("X origin: left real wall")}</text>'),
    (' · planta a escala, altura esquemática</text>',
     ' · {_d("plan to scale, schematic height")}</text>'),
    ("f'plantilla, plomos y cuerdas a medir · {(proyecto or \"COPEX\")[:30]}</text>')",
     "f'{_d(\"template, plumb lines and chords to measure\")} · '\n"
     "             f'{(proyecto or \"COPEX\")[:30]}</text>')"),
    ("f'DETALLE DE REPLANTEO</text>')", "f'{_d(\"SET-OUT DETAIL\")}</text>')"),
    (' · medidas en mm</text>', ' · {_d("dimensions in mm")}</text>'),
    ('"entre los dos plomos"', '_d("between the two plumb lines")'),
    ('"plantilla P → plomo C1"', '_d("template P → plumb line C1")'),
    ('"plantilla P → plomo C2"', '_d("template P → plumb line C2")'),
    ('"pared real izq → C1"', '_d("left real wall → C1")'),
    ('"C2 → pared real der"', '_d("C2 → right real wall")'),
    ('"Desplazada":     "Sí" if moved else "—",',
     '"Desplazada":     _d("Yes") if moved else "—",'),
    ('"Pared real izquierda → plomo riel izquierdo"',
     '_d("Left real wall → left rail plumb line")'),
    ('"Plomo riel derecho → pared real derecha"',
     '_d("Right rail plumb line → right real wall")'),
    ('font-weight="bold">⚠ BS INCOHERENTE</text>',
     'font-weight="bold">{_d("⚠ BS INCONSISTENT")}</text>'),
    ('>AJUSTE BSR &lt; BS</text>', '>{_d("BSR &lt; BS ADJUSTMENT")}</text>'),
    ('>NO CABE — revisar</text>', '>{_d("DOES NOT FIT — review")}</text>'),
    ('>REPLANTEO DE PLOMADAS</text>', '>{_d("PLUMB LINE SET-OUT")}</text>'),
]

DIAG = [
    ('fill="#667080">POS. DISEÑO</text>', 'fill="#667080">{_d("DESIGN POS.")}</text>'),
    ('fill="#1a3a5c" letter-spacing="0.08em">CABINA</text>',
     'fill="#1a3a5c" letter-spacing="0.08em">{_d("CAR")}</text>'),
    ('fill="#ffffff" letter-spacing="0.08em">CABINA</text>',
     'fill="#ffffff" letter-spacing="0.08em">{_d("CAR")}</text>'),
    ('fill="#5f6b7a">APERTURA BT {bt:.0f}</text>',
     'fill="#5f6b7a">{_d("BT OPENING")} {bt:.0f}</text>'),
    ('letter-spacing="0.1em">FONDO DEL HUECO</text>',
     'letter-spacing="0.1em">{_d("SHAFT REAR")}</text>'),
    ('letter-spacing="0.1em">PARED FRONTAL — ACCESO</text>',
     'letter-spacing="0.1em">{_d("FRONT WALL — ACCESS")}</text>'),
    ('font-weight="bold">DETALLE A — {crit[1]}</text>',
     'font-weight="bold">{_d("DETAIL A")} — {crit[1]}</text>'),
    ('fill="#5b6472">ampliado ×{z:.0f}</text>',
     'fill="#5b6472">{_d("enlarged")} ×{z:.0f}</text>'),
    ('font-weight="bold">DESPLAZAMIENTO</text>', 'font-weight="bold">{_d("SHIFT")}</text>'),
    ("f'RL {_rl:+.1f} mm  (lateral)</text>')",
     "f'RL {_rl:+.1f} mm  ({_d(\"lateral\")})</text>')"),
    ("f'FB {_fb:+.1f} mm  (frontal)</text>')",
     "f'FB {_fb:+.1f} mm  ({_d(\"front\")})</text>')"),
    ('font-weight="bold">PISO {floor_idx+1}{_tot}</text>',
     'font-weight="bold">{_d("FLOOR")} {floor_idx+1}{_tot}</text>'),
    ("f'Proporción real · cotas en mm</text>')",
     "f'{_d(\"Real proportion · dimensions in mm\")}</text>')"),
    ("f'Planta · vista superior</text>')", "f'{_d(\"Plan · top view\")}</text>')"),
    ('fill="#5b6472">valor fuera de límite</text>',
     'fill="#5b6472">{_d("value out of limit")}</text>'),
    ('[("Ancho del hueco", f"{W:.0f} mm"),\n'
     '                                  ("Profundidad", f"{D:.0f} mm"),\n'
     '                                  ("Bloque cabina", f"{cab_w:.0f} mm")]',
     '[(_d("Shaft width"), f"{W:.0f} mm"),\n'
     '                                  (_d("Depth"), f"{D:.0f} mm"),\n'
     '                                  (_d("Car block"), f"{cab_w:.0f} mm")]'),
    ("f'VISTA ISOMÉTRICA DEL HUECO</text>')", "f'{_d(\"SHAFT ISOMETRIC VIEW\")}</text>')"),
    ("f'{(proyecto or \"COPEX\")[:40]} · {ns} paradas · planta a escala, '\n"
     "             f'altura comprimida (no a escala)</text>')",
     "f'{(proyecto or \"COPEX\")[:40]} · {ns} {_d(\"stops\")} · '\n"
     "             f'{_d(\"plan to scale, compressed height (not to scale)\")}</text>')"),
    ("f'nivel con valores fuera de límite</text>')",
     "f'{_d(\"level with values out of limit\")}</text>')"),
    ('Paragraph(f"Piso {i + 1}", ss["Heading3"])',
     'Paragraph(_d("Floor {n}", n=i + 1), ss["Heading3"])'),
    ('"<p style=\'color:#888;font-family:system-ui\'>No hay solución para graficar.</p>"',
     'f"<p style=\'color:#888;font-family:system-ui\'>{_d(\'No solution to plot.\')}</p>"'),
]

SCHED = [
    ("f'CRONOGRAMA Y AVANCE</text>'", "f'{_d(\"SCHEDULE AND PROGRESS\")}</text>'"),
    ("f'{total} días · {n} actividades</text>']",
     "f'{total} {_d(\"days\")} · {n} {_d(\"activities\")}</text>']"),
    ('font-weight="bold">HOY</text>', 'font-weight="bold">{_d("TODAY")}</text>'),
    ('leyenda = [("Planificado", C_PLAN, False), ("Real", C_REAL, False)]',
     'leyenda = [(_d("Planned"), C_PLAN, False), (_d("Actual"), C_REAL, False)]'),
    ('leyenda.append(("Brecha", C_HOY, True))', 'leyenda.append((_d("Gap"), C_HOY, True))'),
    ('leyenda.append(("Proyección al ritmo actual", C_PROJ, True))',
     'leyenda.append((_d("Projection at current rate"), C_PROJ, True))'),
]

RAIL = [
    ("'CORTE DE RIELES</text>')", "f'{_d(\"RAIL CUTTING\")}</text>')"),
    ("f'Caso 1 &#183; pila instalada A = {_mm(A)} mm '\n"
     "             f'({n2500}&#215;2500 + {n5000}&#215;5000) &#183; corte = requerido &#8722; A</text>']",
     "f'{_d(\"Case 1\")} &#183; {_d(\"installed stack\")} A = {_mm(A)} mm '\n"
     "             f'({n2500}&#215;2500 + {n5000}&#215;5000) &#183; '\n"
     "             f'{_d(\"cut = required &#8722; A\")}</text>']"),
    ('fill="#667080">pila estándar</text>', 'fill="#667080">{_d("standard stack")}</text>'),
    ('font-weight="bold">Elev. {i+1}</text>', 'font-weight="bold">{_d("Elev.")} {i+1}</text>'),
    ("f'recorta el 1er riel</text>')", "f'{_d(\"trims the 1st rail\")}</text>')"),
    ("f'a&#241;ade al 1er riel &#183; el corte va en el riel de ABAJO '",
     "f'{_d(\"adds to the 1st rail\")} &#183; '\n"
     "                 f'{_d(\"the cut goes on the BOTTOM rail\")} '"),
    ('font-weight="bold">Cabina</text>', 'font-weight="bold">{_d("Car")}</text>'),
    ('font-weight="bold">Contrapeso</text>', 'font-weight="bold">{_d("Counterweight")}</text>'),
    ('font-weight="bold">Elevador {i+1}</text>',
     'font-weight="bold">{_d("Elevator")} {i+1}</text>'),
    ('fill="#5b6472">cabina (RZ, RO)</text>', 'fill="#5b6472">{_d("car")} (RZ, RO)</text>'),
]

BUF = [
    ("f'CORTE DE BUFFERS</text>',", "f'{_d(\"BUFFER CUTTING\")}</text>',"),
    ("f'cortar el buffer baja su borde y agranda la holgura sticker↔buffer '\n"
     "         f'hasta HKP = {_mm(hkp)} mm · corte = HKP − HKPR</text>']",
     "f'{_d(\"cutting the buffer lowers its edge and widens the sticker\")}↔'\n"
     "         f'{_d(\"buffer clearance up to\")} HKP = {_mm(hkp)} mm · '\n"
     "         f'{_d(\"cut\")} = HKP − HKPR</text>']"),
    ('font-weight="bold">STICKER DE CABINA</text>',
     'font-weight="bold">{_d("CAR STICKER")}</text>'),
    ('font-weight="bold">HKP diseño {_mm(hkp)}</text>',
     'font-weight="bold">HKP {_d("design")} {_mm(hkp)}</text>'),
    ('font-weight="bold">revisar</text>', 'font-weight="bold">{_d("review")}</text>'),
    ('fill="{RED}">borde real</text>', 'fill="{RED}">{_d("real edge")}</text>'),
    ('fill="{GREEN}">sin corte</text>', 'fill="{GREEN}">{_d("no cut")}</text>'),
    ("f'corte {_mm(corte)}</text>')", "f'{_d(\"cut\")} {_mm(corte)}</text>')"),
    ("fill=\"{MUT}\">material a cortar '\n"
     "             f'(rebaja el buffer hasta HKP)</text>')",
     "fill=\"{MUT}\">{_d(\"material to cut\")} '\n"
     "             f'({_d(\"lowers the buffer down to HKP\")})</text>')"),
    ("fill=\"{MUT}\">holgura ya mayor '\n"
     "             f'que HKP → revisar</text>')",
     "fill=\"{MUT}\">{_d(\"clearance already greater\")} '\n"
     "             f'{_d(\"than HKP → review\")}</text>')"),
    ("f'holgura ≈ no a escala · corte a escala ampliada</text>')",
     "f'{_d(\"clearance ≈ not to scale · cut at enlarged scale\")}</text>')"),
]

BELT = [
    ('font-weight="bold">FFL piso más alto</text>',
     'font-weight="bold">FFL {_d("top floor")}</text>'),
    ('fill="{CABS}">Cabina</text>', 'fill="{CABS}">{_d("Car")}</text>'),
    ('_dir, _dc = "por debajo del FFL", RED', '_dir, _dc = _d("below FFL"), RED'),
    ('_dir, _dc = "por encima del FFL", CABS', '_dir, _dc = _d("above FFL"), CABS'),
    ('_dir, _dc = "en el FFL", MUT', '_dir, _dc = _d("at FFL"), MUT'),
    ('font-weight="bold">Elevador {r["elevador"]}</text>',
     'font-weight="bold">{_d("Elevator")} {r["elevador"]}</text>'),
]

TODO = [("core/plumb.py", PLUMB), ("core/diagrams.py", DIAG), ("core/schedule.py", SCHED),
        ("core/rail_cut.py", RAIL), ("core/buffer_cut.py", BUF), ("core/belting.py", BELT)]

fallos = []
for rel, reps in TODO:
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        # idempotente: si el reemplazo YA está puesto, ese ancla no tiene que casar
        if s.count(nv) == 1 and s.count(o) == 0:
            continue
        if s.count(o) != 1:
            fallos.append(f"{rel}  ({s.count(o)}x)  {o[:85]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan exactamente una vez:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in TODO:
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o) == 1:
            s = s.replace(o, nv, 1); n += 1
    if "from core.i18n import d as _d" not in s:
        # ⚠️ diagrams/buffer_cut/belting NO tienen imports (solo construyen cadenas),
        # así que el import va tras el DOCSTRING del módulo, localizado por AST con
        # `end_lineno` (con lineno caería DENTRO del docstring — lección v128).
        tr = ast.parse(s)
        ins = 0
        if (tr.body and isinstance(tr.body[0], ast.Expr)
                and isinstance(tr.body[0].value, ast.Constant)
                and isinstance(tr.body[0].value.value, str)):
            ins = tr.body[0].end_lineno
        lin = s.splitlines(True)
        lin.insert(ins, chr(10) + "from core.i18n import d as _d" + chr(10))
        s = "".join(lin)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:22} {n:2} reemplazos")

print(f"OK - {sum(len(r) for _, r in TODO)} reemplazos en {len(TODO)} modulos")
