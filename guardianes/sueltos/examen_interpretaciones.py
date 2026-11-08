# -*- coding: utf-8 -*-
"""Examen REAL de las interpretaciones del survey (v652; ⚠️ GASTA: solo con permiso del usuario).

Con los dos surveys reales de cliente1 (PRJ-0026, PRJ-0034; recalculados con el cálculo determinista de la app, solo
lectura) y un Caso 1 (pared limitante) armado sobre el de PRJ-0026. Con el arnés (`PYTHONPATH=guardianes/arnes`): nada se
escribe. Apunta las llamadas (intentos), lo que no pasó la revisión, el coste y el tiempo, y guarda los textos.

    py -3.12 examen_interpretaciones.py SALIDA.json
"""
import json
import os
import sys
import time

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd                                               # noqa: E402
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from core import interpretation as I, projects as P               # noqa: E402
from core.bs_logic import find_bs_step                            # noqa: E402
from core.calculations import analyze_matrix, apply_offsets, calculate_limits   # noqa: E402
from core.optimizer import optimize                               # noqa: E402

SALIDA = sys.argv[1]
USO = []
_Real = I.anthropic.Anthropic


class _Apunta:
    """El cliente de verdad, apuntando lo que gasta cada llamada."""

    def __init__(self, **k):
        self._c = _Real(**k)
        self.beta = self

    @property
    def messages(self):
        return self

    def create(self, **k):
        t0 = time.time()
        r = self._c.beta.messages.create(**k)
        u = r.usage
        USO.append({"in": u.input_tokens, "out": u.output_tokens, "s": round(time.time() - t0, 1), "stop": r.stop_reason})
        return r


I.anthropic.Anthropic = _Apunta


def calc_de(pj, mj):
    ap = dict(pj)
    last = pd.DataFrame(mj).iloc[-1]
    for col in ("WR", "FR", "OR", "WL", "FL", "OL"):
        ap[f"{col[0]}{col[1]}T"] = float(last[col])
    lim = calculate_limits(ap)
    ap.update(lim)
    adj = apply_offsets(mj, lim)
    ana = analyze_matrix(adj, lim, wall_limiting=bool(ap.get("WALL_LIMITING")))
    ap.update(ana)
    lim.update(ana)
    opt = optimize(adj, lim, ap)
    bs = find_bs_step(pj["BSR"], pj["BS"], lim["LIMIT_ZB"], lim["LIMIT_OB"])
    return {"limits": lim, "analysis": ana, "optimizer_result": opt, "bs_result": bs, "survey_adj": pd.DataFrame(adj)}, ap


CASOS = []
for pid in ("PRJ-0026", "PRJ-0034"):
    prj = P.get_project(pid)
    CASOS.append((pid, json.loads(prj["ParamsJSON"]), json.loads(prj["MatrixJSON"])))
_p26 = json.loads(P.get_project("PRJ-0026")["ParamsJSON"])
CASOS.append(("Caso 1 sobre PRJ-0026", {**_p26, "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "L"},
              json.loads(P.get_project("PRJ-0026")["MatrixJSON"])))

informe = []
for nombre, pj, mj in CASOS:
    calc, ap = calc_de(pj, mj)
    f = I.hechos(calc, ap)
    print("=" * 100, "\n%s · %s · %s · %s" % (nombre, f["solution"]["lateral_shift"] if f["solution"] else "sin solución",
                                               f["solution"]["front_back_shift"] if f["solution"] else "",
                                               "sigue fuera: %s" % [(q["column"], q["floors"]) for q in (f["solution"] or {}).get("still_out_of_limit", [])]))
    for tipo, fn in (("interno", I.generate_interpretation), ("cliente", I.generate_user_interpretation)):
        n0, t0 = len(USO), time.time()
        res = fn(calc, ap)
        llam = USO[n0:]
        c = sum((u["in"] * 2 + u["out"] * 10) / 1e6 for u in llam)
        textos = {k: v for k, v in res.items() if not k.startswith("_")}
        print("\n--- %s · %d llamada(s) · %.1f s · $%.4f · ok=%s" % (tipo, len(llam), time.time() - t0, c, res.get("_ok")))
        for a in res.get("_avisos") or []:
            print("   AVISO:", a)
        if tipo == "cliente":
            for k in ("resumen", "implementacion", "verificacion"):
                print("   [%s] %s" % (k, textos.get(k)))
        else:
            for k in ("desplazamientos", "solucion_optima", "consideraciones"):
                print("   [%s] %s" % (k, textos.get(k)))
        # ⚠️ y la revisión, OTRA VEZ sobre lo publicado: lo que salió tiene que pasar limpio
        _pub = {k: v for k, v in textos.items() if v and v != I.NO_INCLUIDO and k not in ("desplazamientos", "cortes") or
                (tipo == "interno" and v and v != I.NO_INCLUIDO)}
        print("   revisión de lo publicado:", I.revisar(_pub, f) or "limpio")
        informe.append({"caso": nombre, "tipo": tipo, "llamadas": llam, "coste": c, "ok": res.get("_ok"),
                        "avisos": res.get("_avisos"), "textos": textos})
total = sum(x["coste"] for x in informe)
print("\nTOTAL: %d llamadas · $%.3f · tiempos %s" % (len(USO), total, [u["s"] for u in USO]))
with open(SALIDA, "w", encoding="utf-8") as fh:
    json.dump(informe, fh, ensure_ascii=False, indent=1, default=str)
