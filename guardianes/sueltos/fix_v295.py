"""v295 comprobaba la cabecera del tablero con el CSS ANTERIOR a v301.

v295 la pedía `font-size:12px` + `margin-bottom:5px` escritos en la línea. v301
reescribió esa cabecera en una constante `_CAB` (13px, seminegrita, centrada,
margen 6px) y v333 normalizó el tamaño a la escala. La afirmación envejeció: lo
que hay que seguir protegiendo es que la cabecera esté CENTRADA y con aire, no el
literal exacto de entonces.

⚠️ Se comprueba que el ancla exista antes de tocar nada (lección de v361).
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = pathlib.Path(r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
                 r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad")
p = S / "verif_v295.py"
src = p.read_text(encoding="utf-8")

VIEJO = ('_cab = next((l for l in src.splitlines()\n'
         '             if "text-align:center" in l and "font-size:12px" in l), "")\n'
         'check("cabecera de dias centrada", bool(_cab))\n')
NUEVO = ('# v384: v301 movió esa cabecera a la constante `_CAB` y v333 normalizó el\n'
         '# tamaño a la escala de 9 pasos, así que el literal «font-size:12px» en la\n'
         '# línea ya no existe. Lo que se protege sigue siendo: centrada y con aire.\n'
         '_cab = next((l for l in src.splitlines() if "_CAB = (" in l), "")\n'
         '_cab_bloque = src[src.index("_CAB = ("):src.index("_CAB = (") + 200] if _cab else ""\n'
         'check("cabecera de dias centrada", "text-align:center" in _cab_bloque)\n')

if VIEJO not in src:
    print("   ‼️ el ancla de «cabecera de dias centrada» no existe — revisar a mano")
    sys.exit(1)
src = src.replace(VIEJO, NUEVO)

V2 = 'check("...y con margen abajo", "margin-bottom:5px" in src)'
N2 = ('check("...y con margen abajo", "margin-bottom:" in _cab_bloque)')
if V2 not in src:
    print("   ‼️ el ancla de «margen abajo» no existe — revisar a mano")
    sys.exit(1)
src = src.replace(V2, N2)

p.write_text(src, encoding="utf-8")
print("   ✓ verif_v295.py: las dos afirmaciones de cabecera actualizadas a `_CAB`")
