# -*- coding: utf-8 -*-
"""Bateria de roturas de v530. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura NO es una variante: devuelve la solucion activa y los pisos
EXACTAMENTE al codigo de v529 (el bucle de pasadas sin fin y el `pop`).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v530"
SUI = "core/survey_ui.py"
TOPE_S = 420

_ORDEN_NUEVO = ('            _reco = opt_result.setdefault("recomendada", best)\n'
                '            reco_pair = (_reco["rl"], _reco["fb"])\n')
_ORDEN_VIEJO = '            best_pair = (best["rl"], best["fb"])\n'
_IDX_NUEVO = ('            _idx_act = next((k for k, s in enumerate(sorted_solutions) if s is best),\n'
              '                            next((k for k, s in enumerate(sorted_solutions)\n'
              '                                  if (s["rl"], s["fb"]) == (best["rl"], best["fb"])), 0))\n')
_IDX_VIEJO = ('            _idx_act = next((k for k, s in enumerate(sorted_solutions)\n'
              '                             if (s["rl"], s["fb"]) == best_pair), 0)\n')
_N_NUEVO = ('        st.session_state["_calc_n"] = int(st.session_state.get("_calc_n", 0) or 0) + 1\n'
            '        st.session_state.calc_results["_n"] = st.session_state["_calc_n"]\n')
_N_VIEJO = ('        st.session_state.pop("sol_activa", None)\n'
            '        st.session_state.pop("diag_pisos", None)\n')


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ vuelve el codigo EXACTO de v529 (bucle al elegir + `pop` tras recalcular)",
     SUI, [(_ORDEN_NUEVO, _ORDEN_VIEJO),
           ('0 if (s["rl"], s["fb"]) == reco_pair else 1,',
            '0 if (s["rl"], s["fb"]) == best_pair else 1,'),
           (_IDX_NUEVO, _IDX_VIEJO),
           ('key=f"sol_activa_{_n_calc}",', 'key="sol_activa",'),
           ("is_best   = idx_sol == _idx_act", 'is_best   = (sol["rl"], sol["fb"]) == best_pair'),
           ("with st.expander(sol_label, expanded=is_best):",
            "with st.expander(sol_label, expanded=(idx_sol == 0)):"),
           ('default=_prob[:1] or [0], key=f"diag_pisos_{_n_calc}",',
            'default=_prob[:1] or [0], key="diag_pisos",'),
           ('        opt_result["recomendada"] = best_sol\n', ""),
           (_N_NUEVO, _N_VIEJO)]),

    ("⚠️ el orden vuelve a salir de la ACTIVA (vuelve el bucle)",
     SUI, [('0 if (s["rl"], s["fb"]) == reco_pair else 1,',
            '0 if (s["rl"], s["fb"]) == (best["rl"], best["fb"]) else 1,')]),

    ("la «recomendada» pasa a ser la activa (el orden vuelve a moverse)",
     SUI, [('_reco = opt_result.setdefault("recomendada", best)', "_reco = best")]),

    ("⚠️ la solucion activa vuelve a clave FIJA (el navegador devuelve la vieja)",
     SUI, [('key=f"sol_activa_{_n_calc}",', 'key="sol_activa",')]),

    ("los pisos vuelven a clave FIJA",
     SUI, [('key=f"diag_pisos_{_n_calc}",', 'key="diag_pisos",')]),

    ("el numero de calculo no avanza (la clave no cambia al recalcular)",
     SUI, [('st.session_state["_calc_n"] = int(st.session_state.get("_calc_n", 0) or 0) + 1',
            'st.session_state["_calc_n"] = 1')]),

    ("la estrella vuelve a la PRIMERA en vez de a la activa",
     SUI, [("is_best   = idx_sol == _idx_act", "is_best   = idx_sol == 0")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           SUI, [(_ORDEN_NUEVO, "            # comentario inocuo del control\n" + _ORDEN_NUEVO)])


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
