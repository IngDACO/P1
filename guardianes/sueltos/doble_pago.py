"""¿Se puede cobrar DOS VECES el mismo día? (ausencia pagada + horas fichadas)

Leer el código no vale: mi chequeo anterior dio «sí lo cruza» porque encontró la
palabra «fichadas» en un comentario mío. Se mide ejecutando, con datos reales.
Crea UNA ausencia y la borra.
"""
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os                                                       # noqa: E402
os.chdir(RAIZ)

import streamlit as st                                          # noqa: E402
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "audit", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "audit"}

from core import ausencias as AU, timeclock as TC, auth, clock  # noqa: E402

creada = None
try:
    # 1 · un día pasado con fichaje real
    hoy = clock.today(GRUPO)
    d = hoy - timedelta(days=1)
    while d.weekday() > 4:
        d -= timedelta(days=1)
    horas = TC.horas_por_usuario_rango(GRUPO, d, d)
    rates = auth.rate_map(GRUPO)
    cand = [(k, v) for k, v in horas.items() if v["horas"] > 1 and rates.get(k, 0) > 0]
    if not cand:
        print("No hay fichajes útiles ese día; probando la semana anterior")
        d = d - timedelta(days=7)
        horas = TC.horas_por_usuario_rango(GRUPO, d, d)
        cand = [(k, v) for k, v in horas.items()
                if v["horas"] > 1 and rates.get(k, 0) > 0]
    usr, info = cand[0]
    tar = float(rates[usr])
    print(f"Día {d} · {usr} fichó {info['horas']:.2f} h a ${tar}/h")

    # 2 · se le aprueba una ausencia PAGADA justo ese día
    ok, creada = AU.solicitar(GRUPO, usr, str(info["nombre"]), AU.ENFERMEDAD, d, d,
                              motivo="AUDITORIA doble pago")
    print(f"ausencia ese mismo día → {ok} {creada}")
    AU._invalidate(); time.sleep(1.5)
    print(f"estado: {AU.get(creada).get('Estado')} (la enfermedad nace aprobada)")

    # 3 · lo que la nómina pagaría por ese día
    hp = AU.horas_pagadas(GRUPO, usr, d, d)
    base = round(info["horas"] * tar, 2)
    dev = round(hp["horas"] * tar, 2)
    print(f"\n   Base (horas FICHADAS)       {info['horas']:>6.2f} h → ${base:>9,.2f}")
    print(f"   Devengo (día de AUSENCIA)   {hp['horas']:>6.2f} h → ${dev:>9,.2f}")
    print(f"   {'-'*52}\n   TOTAL de ese día            "
          f"{info['horas'] + hp['horas']:>6.2f} h → ${base + dev:>9,.2f}")
    if hp["horas"] > 0 and info["horas"] > 0:
        print(f"\n   ⛔ SE PAGA DOS VECES el {d}: {info['horas']:.2f} h trabajadas "
              f"Y {hp['horas']:.0f} h de baja, ${base + dev:,.2f} por UN día.")
        print("   Nada lo comprueba ni lo avisa.")
    else:
        print("\n   OK: no se solapan.")
finally:
    if creada:
        sh = TC._abrir(TC.sheet_id_para(AU.SHEET, GRUPO))
        w = sh.worksheet(AU.SHEET)
        v = w.get_all_values()
        filas = [i for i, f in enumerate(v[1:], start=2) if f and f[0] == creada]
        for r in sorted(filas, reverse=True):
            w.delete_rows(r)
        AU._invalidate()
        print(f"\nLIMPIEZA: -{len(filas)} → {len(w.get_all_values()) - 1} filas")
