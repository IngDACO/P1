"""F3-G · los 8 de `roster_ui` que la herramienta deja a mano.

Son trozos de f-string partidos en varias líneas (el AST los da como UN Constant y
sustituir su rango reescribiría la continuación) o fragmentos que llevan comillas de los
dos tipos. Se cambian por texto, con ancla única y `ast.parse` antes de escribir.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(r"C:\Users\diego\P1\survey_app\core\roster_ui.py")

R = [
    ('f"Suman **{_suma / 60:.1f} h asignadas** sobre "\n'
     '                       f"**{_ocup / 60:.1f} h de día**, así que ese rato se está "\n'
     '                       f"cargando a dos obras: o es un día partido que falta "\n'
     '                       f"detallar, o alguien está contado dos veces.")',
     'f"They add up to **{_suma / 60:.1f} h assigned** over "\n'
     '                       f"**{_ocup / 60:.1f} h of day**, so that time is being "\n'
     '                       f"charged to two sites: either it is a split day that "\n'
     '                       f"needs detailing, or someone is counted twice.")'),

    ('f":green[:material/sensors:] **{len(vivo)}** fichados ahora "',
     'f":green[:material/sensors:] **{len(vivo)}** clocked in right now "'),

    ('{n_desvio} en otro sitio  ·  "', '{n_desvio} somewhere else  ·  "'),

    # ⚠️ El apóstrofo es CONTENIDO del atributo `style='…'`, no un delimitador: por eso
    # la herramienta lo deja a mano (le añadiría comillas y rompería la f-string).
    ('''f"<div style='{_CAB}'>Persona</div>"''',
     '''f"<div style='{_CAB}'>Person</div>"'''),

    ('f":material/content_copy: Se guardará igual en "',
     'f":material/content_copy: It will be saved the same on "'),

    ("f\"{'día ya planificado' if _usos == 1 else 'días ya planificados'}: \"",
     "f\"{'day already planned' if _usos == 1 else 'days already planned'}: \""),

    ('f"al eliminarlo sale del catálogo, pero **el histórico se "\n'
     '                                       f"conserva** tal cual.")',
     'f"deleting it takes it out of the catalogue, but **the "\n'
     '                                       f"history is kept** as it is.")'),
]

s = P.read_text(encoding="utf-8")
fallos = [o for o, n in R if s.count(o) != 1 and s.count(n) == 0]
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines())[:110])
    sys.exit(1)

n = 0
for o, nv in R:
    if s.count(o) == 1:
        s = s.replace(o, nv, 1)
        n += 1
ast.parse(s)
P.write_text(s, encoding="utf-8")
print(f"  roster_ui  {n} reemplazos")
