# -*- coding: utf-8 -*-
"""Bateria de roturas de v553. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto verificando v552: la ficha fuera de la vista (cortada
bajo el Radar, o entera por encima con un nombre del tablero) y el Radar centrado.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v553"
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
    ("⚠️ abrir desde el Radar no lleva la vista a la ficha",
     RU, [('                        st.session_state["_fp_ir"] = True          # v553 · llevar la vista\n',
           '')]),
    ("⚠️ abrir desde un nombre del tablero no lleva la vista a la ficha",
     RU, [('            st.session_state["_fp_ir"] = True               # v553 · llevar la vista\n',
           '')]),
    ("⚠️ el script se queda en CADA pasada (cualquier clic devolvería la vista a la ficha)",
     RU, [('        if st.session_state.pop("_fp_ir", False):\n',
           '        if st.session_state.get("_fp_ir", False):\n')]),
    ("el script busca la ficha con otra clave (no la encontraría nunca)",
     RU, [("function ir(){var c=D.querySelector('.st-key-fp_card'),",
           "function ir(){var c=D.querySelector('.st-key-ficha'),")]),
    ("la ficha pierde su clave",
     RU, [('    with st.container(border=True, key="fp_card"):\n',
           '    with st.container(border=True):\n')]),
    ("desplaza aunque la ficha ya se vea (`block:'start'` en vez de `nearest`)",
     RU, [("\"block:'nearest'});return;}\"", "\"block:'start'});return;}\"")]),
    ("desplaza sin esperar a que la pasada termine",
     RU, [("\"if(c&&s!=='running'){c.scrollIntoView", "\"if(c){c.scrollIntoView")]),
    ("⚠️ el envoltorio del script vuelve al flujo (hueco de 9,6 px en la ficha)",
     RU, [(".st-key-fp_ir,[data-testid=\\\"stLayoutWrapper\\\"]:has(> \"\n"
           "                            \".st-key-fp_ir){", ".st-key-fp_ir{\"\n                            \"")]),
    ("⚠️ el texto del Radar vuelve a salir centrado",
     RU, [("                    '[class*=\"st-key-radar_\"] button > div,'\n"
           "                    '[class*=\"st-key-radar_\"] button > div > span{'\n",
           "                    '[class*=\"st-key-radar_\"] button{'\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           RU, [("    # v553 · con clave: el script de abajo la busca por `.st-key-fp_card`",
                 "    # v553 · con clave: el script de abajo la busca por `.st-key-fp_card` (control)")])


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
