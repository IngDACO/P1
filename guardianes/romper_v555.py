# -*- coding: utf-8 -*-
"""Bateria de roturas de v555. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Absences en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v555"
AUI = "core/ausencias_ui.py"
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
    ("⚠️ aprobar vuelve a ejecutarse DENTRO de la tarjeta (el fantasma)",
     AUI, [('            st.session_state["_aus_accion"] = {"aid": aid, "aprobar": True, "nota": nota}\n',
            '            _ejecutar({"aid": aid, "aprobar": True, "nota": nota}, quien, grupo)\n')]),
    ("la acción se ejecuta DESPUÉS de pintar la lista",
     AUI, [('    _accion_pendiente(grupo, quien)          # v555 · ACCIÓN DIFERIDA (ver su docstring)\n', ''),
           ('    _kpis_bandeja(pend, fuera_hoy, _sem)\n',
            '    _kpis_bandeja(pend, fuera_hoy, _sem)\n    for r in pend:\n'
            '        _tarjeta_pendiente(grupo, r, quien)\n    _accion_pendiente(grupo, quien)\n')]),
    ("⚠️ lo urgente vuelve a salir el último",
     AUI, [('    pend = sorted([r for r in todas if str(r.get("Status")) == AU.PENDIENTE],\n'
            '                  key=lambda r: str(r.get("From", "")))\n',
            '    pend = [r for r in todas if str(r.get("Status")) == AU.PENDIENTE]\n')]),
    ("vuelven las fechas ISO",
     AUI, [('    a, b = _fdma(desde), _fdma(hasta)\n', '    a, b = str(desde), str(hasta)\n')]),
    ("un solo día vuelve a salir «22 → 22»",
     AUI, [('    return a if a == b else f"{a} → {b}"\n', '    return f"{a} → {b}"\n')]),
    ("⚠️ el saldo vuelve a mirar el de ANTES de la solicitud",
     AUI, [('            _tras = s["restantes"] - _dias\n', '            _tras = s["restantes"]\n')]),
    ("⚠️ el aviso a la persona vuelve al español",
     AUI, [('        _s = "approved" if aprobada else "rejected"\n',
            '        _s = "aprobada" if aprobada else "rechazada"\n')]),
    ("⚠️ la baja por enfermedad deja de llegar al admin",
     AUI, [('    if _bajas:\n', '    if False:\n')]),
    ("⚠️ «Cancel» cancela sin preguntar",
     AUI, [('        st.session_state["_aus_cancelar"] = (donde, aid)\n',
            '        st.session_state["_aus_accion"] = {"aid": aid, "cancelar": True}\n')]),
    ("⚠️ cancelar no libera el tablero",
     AUI, [('            _ok2, _n = AU.aplicar_al_roster(r, quitar=True)\n',
            '            _ok2, _n = True, 0\n')]),
    ("⚠️ la acción vuelve a buscar por ID GLOBAL (otra empresa)",
     AUI, [('    r = _de_grupo(grupo, aid)\n', '    r = AU.get(aid) or {}\n')]),
    ("las tarjetas vuelven a ser pasivas",
     AUI, [('            st.session_state["_aus_kpi"] = "" if _ver == k else k\n', '            pass\n')]),
    ("el histórico pierde su clave (trampa 35)",
     AUI, [('icon=":material/history:", key="exp_aus_hist")', 'icon=":material/history:")')]),
    ("«Cancel» también en lo pendiente",
     AUI, [('    if str(r.get("Status")) != AU.APROBADA:\n        return\n',
            '    if False:\n        return\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           AUI, [("    # v555 · los dos botones solo APUNTAN la acción (ver `render_bandeja`)",
                  "    # v555 · los dos botones solo APUNTAN la acción (ver `render_bandeja`, control)")])


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
