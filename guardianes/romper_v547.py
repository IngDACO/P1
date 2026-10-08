# -*- coding: utf-8 -*-
"""Bateria de roturas de v547. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera devuelve lo visto en producción: un desplegable con controles SIN clave,
que se cierra solo cuando el aviso de arriba aparece o se va (trampa nº35).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v547"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
SV = "core/survey_ui.py"
SP = "core/stage_progress_ui.py"
QU = "core/quotes_ui.py"
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
    ("⚠️ un desplegable con controles vuelve a ir SIN clave",
     PU, [('with st.expander(t(":material/inventory_2: Archive project"), key=f"exp_arch_{pid}"):',
           'with st.expander(t(":material/inventory_2: Archive project")):')]),

    ("dos desplegables con la MISMA clave fija",
     SV, [('key="exp_sv_dup"', 'key="exp_sv_nuevo"')]),

    ("dentro de un bucle, una clave sin la variable del bucle",
     SP, [('key="%s_exp_%s_%d" % (key_prefix, pid, e["orden"])', 'key="%s_exp_%s" % (key_prefix, pid)')]),

    ("«se abre solo si hay instrucciones» sin la condición en la clave",
     PU, [('key=f"exp_ind_{pid}_{bool(links)}"', 'key=f"exp_ind_{pid}"')]),

    ("una clave fuera de convenio",
     QU, [('key="exp_cot_plano"', 'key="cot_plano"')]),

    ("un CSS por subcadena que atrapa las claves «exp_»",
     HU, [("\".st-key-cpxtop [data-testid='stPopoverButton']{padding-left:6px !important;\"\n",
           "\"[class*='st-key-exp_'] button{color:red;}\"\n"
           "        \".st-key-cpxtop [data-testid='stPopoverButton']{padding-left:6px !important;\"\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           QU, [('    with st.expander(t(":material/architecture: Price it from the drawing")',
                 '    # comentario inocuo del control\n'
                 '    with st.expander(t(":material/architecture: Price it from the drawing")')])


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
