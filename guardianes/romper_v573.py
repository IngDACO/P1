# -*- coding: utf-8 -*-
"""Bateria de roturas de v573 (la suite no toca el código de la app). Rompe GUARDIANES,
no la app: reintroduce las escrituras en disco que había y quita la huella del runner.
⚠️ Ninguna rotura se EJECUTA: verif_v573 lee los guardianes, no los corre.
⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455).
Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v573"
TOPE_S = 120

ROTURAS = [
    ("⚠️ verif_v471 vuelve a escribir la rotura EN DISCO (por la variable del bucle)", "verif_v471.py",
     [("            _SUPLE[fich] = roto\n",
       '            io.open(fich, "w", encoding="utf-8", newline="").write(roto)\n')]),
    ("verif_v463 vuelve a escribir en core/invoices.py", "verif_v463.py",
     [("    _SUPLE[_pinv] = _orig.replace('    return \"pendiente\"', '    return \"pending\"', 1)\n",
       "    io.open(_pinv, \"w\", encoding=\"utf-8\").write(_orig.replace('    return \"pendiente\"', "
       "'    return \"pending\"', 1))\n")]),
    ("verif_v498 vuelve a crear un fichero dentro de core/", "verif_v498.py",
     [("    _SUPLE.clear()\n\n",
       "    _SUPLE.clear()\n    io.open(os.path.join(RAIZ, \"core\", \"_zz.py\"), \"w\").write(\"\")\n\n")]),
    ("⚠️ el runner deja de tomar la huella DESPUÉS de cada guardián", "run_suite.py",
     [("        _h1 = _huella()\n", "        _h1 = _h0\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", "verif_v471.py",
           [("_SUPLE = {}\n", "_SUPLE = {}   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(SCRW, rel)
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.replace("\r\n", "\n").count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace("\r\n", "\n").replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(SCRW, rel), encoding="utf-8").read()
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
    cazadas = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE, byte a byte
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc))
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == len(ROTURAS) and control_ok else 1)
