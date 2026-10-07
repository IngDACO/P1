# -*- coding: utf-8 -*-
"""Bateria de roturas de v540. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el `olvidar` de v539 (BORRA): el servidor olvida pero el
navegador se queda con lo viejo y lo devuelve en el clic siguiente — lo visto en produccion.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v540"
EV = "core/estado_vivo.py"
BCU = "core/buffer_cut_ui.py"
PRU = "core/projects_ui.py"
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
    ("⚠️ vuelve el `olvidar` de v539: BORRA (el navegador se queda con lo de la otra obra)",
     EV, [("            d = _defecto(k)\n            if d is _SIN:\n"
           "                del st.session_state[k]\n            else:\n"
           "                st.session_state[k] = d\n",
           "            del st.session_state[k]\n")]),

    ("un valor por defecto con el TIPO cambiado (1.0 donde el widget es entero)",
     EV, [('"bc_hkp": 0.0, "bc_n": 1,', '"bc_hkp": 0.0, "bc_n": 1.0,')]),

    ("un valor por defecto distinto del del widget (lado Omega)",
     EV, [('"plb_omega": "R",', '"plb_omega": "L",')]),

    ("una entrada sin valor por defecto (se borraria y el navegador no se enteraria)",
     EV, [('    "rc_n2500": 0, "rc_n5000": 0,', '    "rc_n5000": 0,')]),

    ("el HGPR de cada ascensor sin valor por defecto",
     EV, [('_DEFECTO_PREFIJO = (("belt_hgpr_", 0.0),)', "_DEFECTO_PREFIJO = ()")]),

    ("⚠️ las tablas de lo medido no se olvidan (lo de antes de v540)",
     EV, [("    for k in TABLAS.get(h, ()):\n        st.session_state.pop(k, None)\n", "")]),

    ("⚠️ la tabla editable no cambia de identidad (el navegador re-aplicaria lo tecleado)",
     EV, [("    st.session_state[_GEN + h] = int(st.session_state.get(_GEN + h, 0) or 0) + 1\n",
           "")]),

    ("`clave_tabla` no lleva la generacion",
     EV, [('    return "%s_%d" % (nombre, int(st.session_state.get(_GEN + str(herramienta), 0) or 0))',
           "    return nombre")]),

    ("una tabla que escribe Rieles falta en `TABLAS`",
     EV, [('"rc": ("rc_L_df", "rc_in_df")', '"rc": ("rc_L_df",)')]),

    ("la tabla de Buffers vuelve a una clave fija",
     BCU, [('key=estado_vivo.clave_tabla("bc", "bc_editor")', 'key="bc_editor"')]),

    ("vuelve «Descargar» en Files (codigo exacto de v539)",
     PRU, [('t(":material/download: Download {x}", x=e["nombre"] or t("file"))',
            '":material/download: Descargar " + (e["nombre"] or "archivo")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           EV, [("    for k in TABLAS.get(h, ()):\n",
                 "    # comentario inocuo del control\n    for k in TABLAS.get(h, ()):\n")])


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
