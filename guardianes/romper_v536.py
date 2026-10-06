# -*- coding: utf-8 -*-
"""Bateria de roturas de v536. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el codigo de v535: app.py no descarta los modulos viejos al
desplegar (la app cayo con AttributeError hasta reiniciarla a mano).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v536"
APPF = "app.py"
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
    ("⚠️ vuelve el codigo de v535: no se descarta nada (la app cae con los modulos viejos)",
     APPF, [("        sys.modules.pop(_m, None)", "        pass")]),

    ("⚠️ solo se descarta si habia marca: el proceso de v535 (sin marca) seguiria caido",
     APPF, [('getattr(sys.modules["core"], "_VERSION_CARGADA", None) != _V_DISCO',
             'getattr(sys.modules["core"], "_VERSION_CARGADA", _V_DISCO) != _V_DISCO')]),

    ("se descarta SIEMPRE (cada pasada reimportaria la app entera)",
     APPF, [('if "core" in sys.modules and getattr(sys.modules["core"], "_VERSION_CARGADA", None) != _V_DISCO:',
             "if True:")]),

    ("se descartan modulos que solo EMPIEZAN como los de la app",
     APPF, [('m.startswith(("core.", "extractors."))', 'm.startswith(("core", "extractors"))')]),

    ("los extractors no se descartan",
     APPF, [('if m in ("core", "extractors") or m.startswith(("core.", "extractors."))]:',
             'if m == "core" or m.startswith("core.")]:')]),

    ("no se marca la version cargada",
     APPF, [("_core_pkg._VERSION_CARGADA = _V_DISCO", "_core_pkg._MARCA = _V_DISCO")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           APPF, [("_core_pkg._VERSION_CARGADA = _V_DISCO",
                   "# comentario inocuo del control\n_core_pkg._VERSION_CARGADA = _V_DISCO")])


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
