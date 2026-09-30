# -*- coding: utf-8 -*-
"""Bateria de roturas de v533. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el heartbeat al codigo de v532: el veredicto no se olvida en
ningun sitio (el fallo visto en produccion al probar la expulsion).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v533"
AU = "core/auth.py"
AUI = "core/auth_ui.py"
APPF = "app.py"
BUF = "core/buffer_cut.py"
PRJ = "core/projects.py"
TOPE_S = 420

_OLV_APP = '    heartbeat_olvidar(_a.get("usuario", ""), _a.get("token", ""))\n'
_OLV_UI = '                auth.heartbeat_olvidar(_a.get("usuario", ""), _a.get("token", ""))\n'
_OLV_POP = "        _HB.pop((str(usuario), str(token)), None)"


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ vuelve el codigo de v532: el veredicto no se olvida (restaurada y expulsada al instante)",
     AU, [(_OLV_POP, "        pass")]),

    ("la app no olvida al EXPULSAR",
     APPF, [(_OLV_APP, "")]),

    ("⚠️ restaurar desde la cookie no olvida el veredicto viejo",
     AUI, [(_OLV_UI, "")]),

    ("un hilo que termina tarde vuelve a meter su veredicto aunque se olvidara",
     AU, [('        if (_HB.get(clave) or {}).get("hilo") is threading.current_thread():',
           "        if True:")]),

    ("⚠️ la leyenda de Buffers vuelve a una sola linea (los textos se pisan)",
     BUF, [("    p.append(f'<text x=\"18\" y=\"{VH-12}\" font-size=\"7\" fill=\"{MUT}\">'",
            "    p.append(f'<text x=\"{VW-18}\" y=\"{_yl}\" text-anchor=\"end\" font-size=\"7\" "
            "fill=\"{MUT}\">'")]),

    ("⚠️ a 0% el inicio real se queda (el caso de PRJ-0015)",
     PRJ, [("        elif av <= 0 and fi:", "        elif False:")]),

    ("el inicio real se borra tambien con avance (se pierde la fecha de arranque)",
     PRJ, [("        elif av <= 0 and fi:", "        elif fi:")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           AU, [(_OLV_POP, "        # comentario inocuo del control\n" + _OLV_POP)])


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
