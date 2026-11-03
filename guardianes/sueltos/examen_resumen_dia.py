# -*- coding: utf-8 -*-
"""Examen REAL del resumen del día (v647; ⚠️ GASTA: solo con permiso del usuario).

Con los datos reales de cliente1 y la cuenta de oficina, en local. Va con el arnés (`PYTHONPATH=guardianes/arnes`):
toda escritura en Sheets o Drive, Telegram y correo, PARADA; los datos solo se leen. Lo que recibió el modelo se guarda
aparte, para comparar cada cifra del resumen con la de la app.

    py -3.12 examen_resumen_dia.py SALIDA.json
"""
import json
import os
import sys
import time

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from core import parte_agente as AG, resumen_dia as RD            # noqa: E402

SALIDA = sys.argv[1]
_k = AG.clave_api()
if not _k:
    sys.exit("sin clave")
datos = RD.hechos("cliente1", "Admin2")
with open(SALIDA, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=1, default=str)
print("datos: %d caracteres · %s" % (len(json.dumps(datos, ensure_ascii=False, default=str)),
                                     {k: ("error" if "error" in v else "ok") for k, v in datos.items()}))
total, seg = 0.0, []
for i, idi in enumerate(["en", "en", "es", "en", "es"], start=1):
    t0 = time.time()
    res, mot = RD.generar("cliente1", "Admin2", idi, api_key=_k)
    d = time.time() - t0
    seg.append(d)
    if not res:
        print("\n=== %d (%s) · FALLÓ: %s · %.1f s" % (i, idi, mot, d))
        continue
    c = (res["uso"]["in"] * 2 + res["uso"]["out"] * 10) / 1e6
    total += c
    print("\n=== %d (%s) · %.1f s · $%.4f · ent %d sal %d" % (i, idi, d, c, res["uso"]["in"], res["uso"]["out"]))
    print("    " + res["titular"])
    for p in res["puntos"]:
        print("    %s %s  →  %s%s" % ("!!" if p["urgente"] else "··", p["texto"], p["ir"], (" " + p["obra"]) if p["obra"] else ""))
print("\nTOTAL $%.3f · por resumen $%.4f · mediana %.1f s · máx %.1f s" % (total, total / 5, sorted(seg)[2], max(seg)))
