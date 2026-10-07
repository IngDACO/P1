# -*- coding: utf-8 -*-
"""Bateria de roturas de v541. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el «volver» de v540: los botones del fichaje cortan la pasada
con `st.rerun()` y cerrar la jornada dentro de una herramienta borraba lo tecleado.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v541"
EV = "core/estado_vivo.py"
TOPE_S = 420


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ vuelve el «volver» de v540: tambien olvida al pasar a «sin obra» (cerrar la jornada "
     "borra lo tecleado)",
     EV, [("    if obra and ult_real != obra:",
           "    if antes[0] < n - 1 and antes[1] != obra:\n        olvidar(h)\n"
           "        return True\n    if obra and ult_real != obra:")]),

    ("de «sin obra» a una obra ya no olvida (lo tecleado sin obra se queda bajo la obra)",
     EV, [("    if obra and ult_real != obra:", "    if obra and ult_real and ult_real != obra:")]),

    ("lo cargado sin obra conocida no lo adopta nadie (fichar en una obra lo borra)",
     # v542 · re-anclada: la adopción vive ahora en el bloque de `_ADOPTAR` (también la de
     # «Duplicate»); la rotura equivalente es no adoptar la obra.
     EV, [('            adopta = "|" in ult_real                    # el duplicado: su plano manda\n'
           "            ult_real = obra\n",
           '            adopta = "|" in ult_real                    # el duplicado: su plano manda\n')]),

    ("`respetar` sin obra vuelve a ser «de ninguna» (no se adopta)",
     EV, [("        ult_real = resp if isinstance(resp, str) else _ADOPTAR\n",
           '        ult_real = resp if isinstance(resp, str) else ""\n')]),

    # v542 · RETIRADAS «la pasada no se cuenta» y «el Survey no sabe si vuelve»: desde v542
    # el Survey empieza de cero al pasar de una obra real a otra sin mirar si «vuelve», así
    # que el contador de pasadas ya no decide nada (trampa nº32). Lo nuevo lo vigila
    # romper_v542.

    ("⚠️ el nº de paradas sin valor por defecto (vuelve como 5.0 al cambiar de obra)",
     EV, [('    "ns": 2,\n', "")]),

    ("el nº de paradas con un valor por defecto DECIMAL",
     EV, [('    "ns": 2,', '    "ns": 2.0,')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           EV, [("    adopta = False\n",
                 "    # comentario inocuo del control\n    adopta = False\n")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


print("0. Verde de base")
_base = corre()
if not _base:
    print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
          % ("COLGADO" if _base is None else "rojo"))
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
saltadas, colgadas = [], []
for desc, rel, cambios in ROTURAS:
    _ok, bak, p, det = aplica(rel, cambios)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    if verde is None:
        colgadas.append(desc)
        print("  COLGADA  %s" % desc)
        continue
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

print("")
print("2. Control (debe seguir VERDE)")
_d, _r, _c = CONTROL
_ok, bak, p, det = aplica(_r, _c)
control_ok = False
if _ok is None:
    print("  ??      ancla del control %s" % det)
else:
    try:
        control_ok = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

print("")
print("=== %d de %d roturas cazadas ===" % (cazadas, total))
if saltadas:
    print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
          % len(saltadas))
if colgadas:
    print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
          % (len(colgadas), TOPE_S))
sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
