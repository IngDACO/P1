# -*- coding: utf-8 -*-
"""Bateria de roturas de v585 (lo visto verificando v584: las cifras de Accounting abrían lo
suyo pero la vista no bajaba). ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite
(v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v585"
CU = "core/contable_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ la lista de obras vuelve a quedar FUERA del bloque al que baja (v584)", CU,
     [('            _PU._bajar_a("cpx_cont_jobs", "_cont_bajar_jobs")\n',
       '            _PU._bajar_a("cpx_cont_jobs", "_cont_bajar_jobs")\n        if True:\n')]),
    ("⚠️ la tabla del parte vuelve a quedar FUERA del bloque al que baja (v584)", CU,
     [('            _PU._bajar_a("cpx_cont_ptabla", "_cont_bajar_p")\n',
       '            _PU._bajar_a("cpx_cont_ptabla", "_cont_bajar_p")\n        if True:\n')]),
    ("la marca de Quotes se queda sola en su bloque (otra pantalla, el mismo fallo)", "core/quotes_ui.py",
     [('        _PU._bajar_a("cpx_cot_tabla", "_cot_bajar")\n',
       '        _PU._bajar_a("cpx_cot_tabla", "_cot_bajar")\n    if True:\n')]),
    ("la marca de Hours baja a un bloque que no es el suyo", "core/projects_ui.py",
     [('    with st.container(key="cpx_gh_tabla"):\n', '    with st.container(key="cpx_gh_tablas"):\n')]),
    ("la vista vuelve a bajar en CADA pasada (no una vez)", "core/projects_ui.py",
     [("    if not st.session_state.pop(marca, False):\n", "    if not st.session_state.get(marca, False):\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CU,
           [("def _parte_csv(grupo, desde, hasta):\n", "def _parte_csv(grupo, desde, hasta):   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
