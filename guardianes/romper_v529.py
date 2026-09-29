# -*- coding: utf-8 -*-
"""Bateria de roturas de v529. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura NO es una variante: devuelve la caja del parte EXACTAMENTE al codigo
de v528 (el `pop` que dejaba el texto en el navegador, visto en produccion).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v529"
DUI = "core/daily_log_ui.py"
TOPE_S = 420

_VACIAR = '    if st.session_state.pop(_kv, False):\n        st.session_state[_k] = ""\n'
_MARCA = "            st.session_state[_kv] = True\n"


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ la caja vuelve al codigo de v528 (`pop`: el texto se queda en el navegador)",
     DUI, [(_VACIAR, ""),
           (_MARCA, "            st.session_state.pop(_k, None)\n")]),

    ("la marca se enciende pero nadie la consume (la caja no se vacia nunca)",
     DUI, [("    if st.session_state.pop(_kv, False):", "    if False:")]),

    ("⚠️ la marca no se apaga: la caja se vacia en CADA pasada (se come lo que escribes)",
     DUI, [("    if st.session_state.pop(_kv, False):",
            "    if st.session_state.get(_kv, False):")]),

    ("⚠️ se vacia aunque la hoja FALLE (en la pasada siguiente: lo escrito se pierde)",
     DUI, [("        else:\n            st.error(msg)",
            "        else:\n            st.session_state[_kv] = True\n            st.error(msg)")]),

    ("se guarda sin la marca (vuelve a quedarse el texto)",
     DUI, [(_MARCA, "")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           DUI, [(_VACIAR, "    # comentario inocuo del control\n" + _VACIAR)])


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
