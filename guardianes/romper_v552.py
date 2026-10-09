# -*- coding: utf-8 -*-
"""Bateria de roturas de v552. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera devuelve lo visto en producción con v551: la ficha abierta desde el Radar
salía arriba del Panel, 373 px por encima de la vista.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v552"
RU = "core/roster_ui.py"
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
    ("⚠️ la línea del Radar no apunta dónde se tocó (la ficha vuelve arriba, fuera de la vista)",
     RU, [('                        st.session_state["_panel_ficha_en"] = _kl\n', '')]),
    ("la ficha se pinta arriba Y en el Radar (arriba sin mirar de dónde viene)",
     RU, [('    if st.session_state.get("_panel_ficha") and not (\n'
           '            st.session_state.get("_panel_ficha_en")\n'
           '            and st.session_state.get("_panel_tool") == "radar"):\n',
           '    if st.session_state.get("_panel_ficha"):\n')]),
    ("la misma línea otra vez ya no cierra la ficha",
     RU, [('                    if _en == _kl and _fic == _u:          # la misma línea otra vez: cerrar\n',
           '                    if False:\n')]),
    ("⚠️ bajo una línea que ya es de OTRA persona (la lista cambió entre pasadas)",
     RU, [('                if _fic and _en == _kl and _fic == _u and not _pintada:\n',
           '                if _fic and _en == _kl and not _pintada:\n')]),
    ("⚠️ si su línea desaparece, la ficha no se pinta en ninguna parte",
     RU, [('        if _fic and _en.startswith("radar_") and not _pintada:\n'
           '            _ficha_rapida(grupo, _fic)         # su línea se movió o desapareció: al final\n',
           '')]),
    ("con el Radar VACÍO, la ficha abierta no se pinta en ninguna parte",
     RU, [('            if _fic and _en.startswith("radar_"):\n'
           '                _ficha_rapida(grupo, _fic)     # su línea ya no está: aquí, no en ninguna parte\n',
           '')]),
    ("un nombre del tablero no olvida la línea del Radar (su ficha no sale arriba)",
     RU, [('            st.session_state.pop("_panel_ficha_en", None)   # v552 · del tablero: arriba\n',
           '')]),
    ("el ✕ de la ficha no olvida de dónde venía",
     RU, [('            st.session_state.pop("_panel_ficha_en", None)      # v552\n', '')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           RU, [("    # el clic parecía no hacer nada (medido en producción).",
                 "    # el clic parecía no hacer nada (medido en producción, control).")])


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
