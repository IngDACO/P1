# -*- coding: utf-8 -*-
"""Bateria de roturas de v537. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el requirements de v536: el lienzo de firma sin fijar
(`<1`), que en el Cloud instalo la 0.13.0 y dejo el Pre-Start caido.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v537"
APPF = "app.py"
REQ = "requirements.txt"
PRE = "core/prestart_ui.py"
SV = "core/survey_ui.py"
CFG = ".streamlit/config.toml"
EV = "core/estado_vivo.py"
PLA = "core/plan_ui.py"
SV = "core/survey_ui.py"
INC = "core/incrustar.py"
TCU = "core/timeclock_ui.py"
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
    ("⚠️ vuelve el requirements de v536: el lienzo sin fijar (`>=0.9.3,<1`)",
     REQ, [("streamlit-drawable-canvas==0.9.3", "streamlit-drawable-canvas>=0.9.3,<1")]),

    ("⚠️ sin comprobar que el lienzo acepta los parametros (la 0.13 tumbaria el Pre-Start)",
     PRE, [("        inspect.signature(st_canvas).bind(key=\"prueba\", **_LIENZO)\n",
            "        pass\n")]),

    ("una firma vuelve a escribir sus parametros a mano (dos sitios que divergen)",
     PRE, [('res = st_canvas(key="ps_firma_tarde", **_LIENZO)',
            'res = st_canvas(key="ps_firma_tarde", width=600, display_toolbar=True)')]),

    ("el lienzo pierde el ancho de movil (600 por defecto: media firma fuera de pantalla)",
     PRE, [("height=90, width=300, drawing_mode", "height=90, width=600, drawing_mode")]),

    ("⚠️ vuelve la tabla de parametros mezclada (numeros y letras: traza en cada calculo)",
     SV, [("{\"Parameter\": k, \"Valor\": str(round(v, 3)) if isinstance(v, (int, float))\n"
           "                     else str(v)}",
           "{\"Parameter\": k, \"Valor\": round(v, 3) if isinstance(v, (int, float))\n"
           "                     else v}")]),

    ("los cortes CUT OR vuelven a mezclar numeros y vacios",
     SV, [('cut_or_vals.append(f"{or_v - or_lim:.1f}" if or_v - or_lim > 0 else "")',
           'cut_or_vals.append(round(or_v - or_lim, 1) if or_v - or_lim > 0 else "")')]),

    ("el aviso de Session State vuelve a los logs",
     CFG, [("disableWidgetStateDuplicationWarning = true",
            "disableWidgetStateDuplicationWarning = false")]),

    ("[global] apaga algo mas que ese aviso",
     CFG, [("disableWidgetStateDuplicationWarning = true",
            "disableWidgetStateDuplicationWarning = true\nshowWarningOnDirectExecution = false")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PRE, [("    return st_canvas\n", "    # comentario inocuo del control\n    return st_canvas\n")])


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
