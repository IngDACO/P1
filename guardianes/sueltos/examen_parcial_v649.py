# -*- coding: utf-8 -*-
"""Examen REAL de v649 (⚠️ GASTA: con permiso): una actividad de varias partes con solo una nombrada ya no sale como hecha.

Con el plan real de PRJ-0034 (cliente1, solo lectura) y el parte que la destapó en producción (v647), más dos de control:
lo que SÍ está entero tiene que seguir saliendo como hecho. Con el arnés (`PYTHONPATH=guardianes/arnes`): nada se escribe.

    py -3.12 examen_parcial_v649.py
"""
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from core import parte_agente as AG, projects as P, stage_progress as SP     # noqa: E402

CASOS = [
    ("el de producción", "Installed the CW guide shoes and the CW buffer. Filled the counterweight with the filler weights. "
     "Pending: the CW safety screen, waiting for the brackets.",
     {"Install CW guide shoes": "done", "Install/trim buffers (car + CW)": "question"}),
    ("las dos partes", "Installed both buffers today, car and CW, and trimmed them.",
     {"Install/trim buffers (car + CW)": "done"}),
    ("control: entera", "Installed the CW guide shoes.", {"Install CW guide shoes": "done"}),
]
_k = AG.clave_api()
if not _k:
    sys.exit("sin clave")
prj = P.get_project("PRJ-0034")
plan = SP.plan_de_obra(prj)
mapa = SP.acreditado("PRJ-0034")
total, bien, malos = 0.0, 0, []
for nombre, texto, espera in CASOS:
    reg, mot = AG.leer(texto, plan, "2026-10-30", mapa, api_key=_k)
    if not reg:
        print("=== %s: FALLÓ (%s)" % (nombre, mot))
        malos.append(nombre)
        continue
    c = AG.coste_usd(reg.get("uso"))
    total += c
    vistas = {}
    for f in reg["fragmentos"]:
        for a in f.get("actividades") or []:
            vistas.setdefault(a, f.get("clase"))
    print("=== %s · $%.4f · %.1f s" % (nombre, c, reg.get("seg") or 0))
    for f in reg["fragmentos"]:
        print("    %-9s %s → %s%s" % (f.get("clase"), f.get("texto"), f.get("actividades"),
                                     ("  ¿" + f.get("pregunta") + "?") if f.get("pregunta") else ""))
    ok = all(vistas.get(a) == cl for a, cl in espera.items())
    bien += ok
    if not ok:
        malos.append(nombre)
    print("    %s (esperado %s)" % ("BIEN" if ok else "MAL", espera))
print("\n%d de %d · $%.3f" % (bien, len(CASOS), total))
