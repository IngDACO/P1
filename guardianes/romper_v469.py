# -*- coding: utf-8 -*-
"""Bateria de roturas de v469: comprueba que los guardianes invertidos CAZAN lo que
dicen cazar, y que un cambio inocuo NO los pone rojos (caso de CONTROL).

⚠️ Un guardian verde no prueba nada hasta esto (v459: seis roturas salieron
«cazadas» con el guardian rojo de base, asi que ninguna probaba nada). Por eso lo
primero que hace este script es exigir VERDE de base.

⚠️ NO se lanza en paralelo con la suite: modifica ficheros del repo (v455).
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

SCRW = os.environ["SCRW"]
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def corre(g):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


# fichero -> (viejo, nuevo) ; guardian que debe cazarlo
ROTURAS = [
    ("Sheet1.Type fuera de la lista blanca (EL FALLO REAL de v469)",
     "core/valores.py", '    ("Sheet1", "Type"),\n', "", "verif_v445"),
    ("TIPO_PROYECTO revertido sin tocar el resto",
     "core/timeclock.py", 'TIPO_PROYECTO = "project"', 'TIPO_PROYECTO = "proyecto"',
     "verif_v445"),
    ("una categoria de gasto vuelve al espanol",
     "core/expenses.py", '"Materials"', '"Materiales"', "verif_v447"),
    ("derive_estado vuelve a devolver el espanol",
     "core/projects.py", '"In progress"', '"En progreso"', "verif_v442"),
    ("un estado de correccion vuelve al espanol",
     "core/correcciones.py",
     'PENDIENTE, APROBADA, REVERTIDA = "pending", "approved", "reverted"',
     'PENDIENTE, APROBADA, REVERTIDA = "pending", "approved", "revertida"',
     "verif_v461"),
    ("estado_cobro mezcla migrado y sin migrar",
     "core/invoices.py", '    return "pendiente"', '    return "pending"', "verif_v463"),
    ("queda una comparacion contra el literal VIEJO (rama muerta)",
     "core/inventory_ui.py", '_est == "available"', '_est == "disponible"', "verif_v463"),
    ("se cae una entrada de valores.LEGADO",
     "core/valores.py", "'En pausa': 'On hold',", "", "verif_v449"),
    # ⚠️ La misma rotura contra `verif_v469`, que hasta ahora afirmaba lo CONTRARIO
    # (exigia que `Sheet1.Type` quedase FUERA) y por tanto PROTEGIA el fallo: hacerle
    # caso al rojo sin mirar el codigo acusado lo habria reintroducido (regla v385).
    ("Sheet1.Type fuera — contra el guardian que antes lo exigia",
     "core/valores.py", '    ("Sheet1", "Type"),\n', "", "verif_v469"),
]

CONTROL = ("CONTROL: un comentario nuevo no puede poner nada rojo",
           "core/valores.py", "CANON = {v: k for k, v in LEGADO.items()}",
           "# comentario inocuo del caso de control\nCANON = {v: k for k, v in LEGADO.items()}",
           "verif_v445")


def prueba(desc, fich, viejo, nuevo, guardian, espera_rojo):
    p = os.path.join(RAIZ, fich.replace("/", os.sep))
    orig = io.open(p, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        return "  ?? ancla ausente en %s -> %s" % (fich, desc)
    try:
        io.open(p, "w", encoding="utf-8", newline="").write(
            orig.replace(viejo, nuevo, 1))
        verde = corre(guardian)
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(orig)
    if espera_rojo:
        return ("  %s %-58s (%s)"
                % ("CAZADA " if not verde else "ESCAPADA", desc, guardian))
    return ("  %s %-58s (%s)"
            % ("ok     " if verde else "FALSO+ ", desc, guardian))


# ⚠️ Verde de BASE primero: si no, toda la tanda sale «cazada» sin probar nada.
print("0. Verde de base (sin este paso, las roturas no significan nada)")
base = {}
for g in sorted({r[4] for r in ROTURAS} | {CONTROL[4]}):
    base[g] = corre(g)
    print("   %-16s %s" % (g, "verde" if base[g] else "ROJO -> la tanda no valdria"))
if not all(base.values()):
    print("\nABORTADO: hay guardianes rojos de base.")
    sys.exit(2)

print("\n1. Roturas (cada una debe ponerse ROJA)")
res = [prueba(d, f, v, n, g, True) for d, f, v, n, g in ROTURAS]
for r in res:
    print(r)

print("\n2. Control (debe seguir VERDE)")
print(prueba(*CONTROL, espera_rojo=False))

cz = sum(1 for r in res if "CAZADA" in r)
print("\n=== %d de %d roturas cazadas ===" % (cz, len(ROTURAS)))
sys.exit(0 if cz == len(ROTURAS) else 1)
