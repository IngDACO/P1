# -*- coding: utf-8 -*-
"""v696 · Lo visto verificando v695 en producción (22/11): con «reducir movimiento» (sistema o navegador), la regla
global de `theme` deja toda animación en .001 ms y el aviso flotante de `flash`, con `forwards`, pasaba al instante a
su estado final: INVISIBLE. Medido: «Task added.» con opacidad 0 desde el primer momento y su animación «finished».

Lo que se afirma, sobre el CSS de `theme._CSS` (lo que llega al navegador), sin red ni escrituras.
"""
import os
import re
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from core import theme                                                     # noqa: E402

CSS = theme._CSS
_bloques = re.findall(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", CSS, flags=re.S)
chk("la sonda SABE ver un bloque de «reducir movimiento» (el global de toda la app)",
    any("animation-duration: .001ms !important" in b for b in _bloques), _bloques)
chk("hay un bloque que quita la animación al aviso flotante: `.st-key-cpx_flash { animation: none !important; }`",
    any(re.search(r"\.st-key-cpx_flash \{ animation: none !important; \}", b) for b in _bloques), _bloques)
_i_glob = CSS.find("animation-duration: .001ms !important")
_i_fl = CSS.find(".st-key-cpx_flash { animation: none !important; }")
chk("…y va DESPUÉS del global (con los dos `!important`, decide la especificidad, y el orden no estorba)",
    0 < _i_glob < _i_fl, (_i_glob, _i_fl))
chk("el aviso sigue con su desvanecido para el resto (no se quitó para todos)",
    "animation: cpxFlashFuera 9s ease forwards;" in CSS)

print()
print("verif_v696: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v696: TODO OK")
sys.exit(1 if FALLOS else 0)
