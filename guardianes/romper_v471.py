# -*- coding: utf-8 -*-
"""Roturas de v471: se reintroducen los fallos REALES que traia el codigo.

⚠️ Verde de base primero (v459) y NO en paralelo con la suite (v455).
"""
import io
import os
import subprocess
import sys

SCRW = os.environ["SCRW"]
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def corre(g):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    ("la LECTURA vuelve a 'Hours' (KeyError: la pantalla revienta)",
     "core/projects_ui.py", '_ed.iloc[i]["Horas"]', '_ed.iloc[i]["Hours"]', "verif_v471"),
    ("las HORAS vuelven a quedar editables",
     "core/projects_ui.py", 'disabled=["Persona", "Horas", "Costo/h"',
     'disabled=["Persona", "Hours", "Costo/h"', "verif_v471"),
    ("el COSTO de la cotizacion vuelve a quedar editable",
     "core/quotes_ui.py", 'disabled=["Concepto", "Costo"', 'disabled=["Concepto", "Cost"',
     "verif_v471"),
    ("una cabecera vuelve a pintarse cruda en español",
     "core/tabla.py", '    "Actividad": "Activity",\n', "", "verif_v471"),
    ("el column_config de clientes vuelve a ser huerfano (perdia el $ y la barra)",
     "core/clientes_ui.py", '_colcfg = {"Avance":', '_colcfg = {"Progress":', "verif_v444"),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/tabla.py", 'CABECERAS = {', '# comentario inocuo del control\nCABECERAS = {',
           "verif_v471")


def prueba(desc, fich, viejo, nuevo, g, espera_rojo=True):
    p = os.path.join(RAIZ, fich.replace("/", os.sep))
    orig = io.open(p, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        return "  ??      ancla ausente en %s -> %s" % (fich, desc)
    try:
        io.open(p, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        verde = corre(g)
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(orig)
    if espera_rojo:
        return "  %s %-58s (%s)" % ("CAZADA " if not verde else "ESCAPADA", desc, g)
    return "  %s %-58s (%s)" % ("ok     " if verde else "FALSO+ ", desc, g)


print("0. Verde de base")
base = {g: corre(g) for g in ("verif_v471", "verif_v444")}
for g, v in base.items():
    print("   %-14s %s" % (g, "verde" if v else "ROJO -> la tanda no valdria"))
if not all(base.values()):
    sys.exit(2)

print("\n1. Roturas (cada una debe ponerse ROJA)")
res = [prueba(*r) for r in ROTURAS]
for r in res:
    print(r)

print("\n2. Control (debe seguir VERDE)")
print(prueba(*CONTROL, espera_rojo=False))

cz = sum(1 for r in res if "CAZADA" in r)
print("\n=== %d de %d roturas cazadas ===" % (cz, len(ROTURAS)))
sys.exit(0 if cz == len(ROTURAS) else 1)
