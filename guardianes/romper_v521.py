# -*- coding: utf-8 -*-
"""Bateria de roturas de v521. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v521"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    ("se vuelve a contar FILAS del catálogo (la tarjeta diría 2 con cero modelos)",
     "core/library.py", '"modelos": _num_modelos()}', '"modelos": len(list_modelos())}'),

    ("se cuentan los modelos DESACTIVADOS (el desplegable no los ofrece)",
     "core/library.py",
     "    return sum(len(modelos_de(b)) for b in marcas())",
     "    return sum(len(modelos_de(b, True)) for b in marcas(True))"),

    ("se cuentan filas con modelo, repetidas incluidas",
     "core/library.py",
     "    return sum(len(modelos_de(b)) for b in marcas())",
     '    return len([r for r in list_modelos() if str(r.get("Model", "")).strip()])'),

    ("la tarjeta «Models» pinta otro número (el arreglo no se vería)",
     "core/library_ui.py", 'str(r["modelos"])', 'str(r["marcas"])'),
]

# ⚠️ Ancla de 10 o más caracteres: `check_anclas_roturas` ignora las más cortas (v520).
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/library.py", "def _num_modelos() -> int:",
           "# comentario inocuo del control\ndef _num_modelos() -> int:")


def aplica(rel, viejo, nuevo):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    if bak.count(viejo) != 1:
        return None, bak, p, bak.count(viejo)
    io.open(p, "w", encoding="utf-8", newline="").write(bak.replace(viejo, nuevo, 1))
    return True, bak, p, 1


print("0. Verde de base")
if not corre():
    print("   ⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
saltadas = []
for desc, rel, viejo, nuevo in ROTURAS:
    _ok, bak, p, n = aplica(rel, viejo, nuevo)
    if _ok is None:
        print("  ??      ancla %s -> %s" % ("ausente" if n == 0 else "x%d" % n, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

print("")
print("2. Control (debe seguir VERDE)")
_d, _r, _v, _n = CONTROL
_ok, bak, p, n = aplica(_r, _v, _n)
control_ok = False
if _ok is None:
    print("  ??      ancla del control %s" % ("ausente" if n == 0 else "x%d" % n))
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
sys.exit(0 if cazadas == total and not saltadas and control_ok else 1)
