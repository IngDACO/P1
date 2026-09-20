"""Demuestra v426 EN VIVO: una factura ANULADA no mueve el P&L.

Hasta ahora el arreglo estaba probado con un conjunto simulado. Esto lo prueba con
una factura REAL: se emite, se cobra algo, se anula, y el P&L tiene que quedar
EXACTAMENTE igual que antes de crearla. De paso se calcula qué habria dado la logica
VIEJA sobre esos mismos datos, que es la unica forma de ensenar la diferencia.

Uso:  python demo_v426.py crear   |   python demo_v426.py limpiar
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os
os.chdir(RAIZ)

import streamlit as st
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "demo426", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "demo426"}

from core import invoices as I, finance as F, clientes as CL
from core.num import num as _num

MARCA = "ZZZ ANULADA v426"


def _pnl():
    F.pnl.clear() if hasattr(F.pnl, "clear") else None
    I._invalidate()
    time.sleep(1.0)
    p = F.pnl(GRUPO)
    return {k: p[k] for k in ("facturado", "cobrado", "por_cobrar", "ganancia",
                              "vencido")}


def _pnl_viejo():
    """Lo que habria dado la logica de ANTES de v426, sobre los MISMOS datos:
    sumar todas las facturas del rango, anuladas incluidas."""
    facs = I.list_facturas(GRUPO)
    return {"facturado": round(sum(_num(f.get("Total")) for f in facs), 2),
            "cobrado": round(sum(_num(f.get("Cobrado")) for f in facs), 2)}


def crear():
    antes = _pnl()
    antes_v = _pnl_viejo()
    print("P&L ANTES        :", antes)
    print("  (logica vieja) :", antes_v, "\n")

    cli = next((c for c in CL.list_clientes(GRUPO)), None)
    assert cli, "no hay clientes"
    ok, fid = I.create_factura(GRUPO, cli["ID"], cli["Nombre"],
                               [{"concepto": MARCA, "cantidad": 1,
                                 "precio": 5000.0, "importe": 5000.0}],
                               impuesto_pct=10.0, creado_por="demo426")
    assert ok, fid
    print(f"factura creada: {fid}  (total $5.500)")
    I._invalidate(); time.sleep(1.2)
    ok2, _ = I.registrar_cobro(fid, 1500.0)
    print(f"cobro parcial de $1.500: {ok2}")
    I._invalidate(); time.sleep(1.2)
    con = _pnl()
    print("\nP&L con la factura VIVA:", con)
    assert round(con["facturado"] - antes["facturado"], 2) == 5500.0, "no sumo"

    ok3, _ = I.anular(fid)
    print(f"\nfactura ANULADA: {ok3}")
    I._invalidate(); time.sleep(1.5)
    tras = _pnl()
    tras_v = _pnl_viejo()
    print("P&L tras anular  :", tras)
    print("  (logica vieja) :", tras_v)

    print("\n" + "=" * 62)
    igual = all(abs(tras[k] - antes[k]) < 0.01 for k in antes)
    print(f"{'OK  ' if igual else 'FALLO'} el P&L vuelve EXACTAMENTE a como estaba")
    dif_f = round(tras_v["facturado"] - antes_v["facturado"], 2)
    dif_c = round(tras_v["cobrado"] - antes_v["cobrado"], 2)
    print(f"{'OK  ' if dif_f else 'FALLO'} la logica VIEJA habria dejado "
          f"+${dif_f:,.2f} de ingresos y +${dif_c:,.2f} de cobros fantasma")
    print("=" * 62)
    print(f"\nfactura de prueba: {fid}  (anulada, sigue en la hoja para verla en pantalla)")
    return fid


def limpiar():
    import gspread, toml
    from google.oauth2.service_account import Credentials
    from core import timeclock as T
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    ws = gc.open_by_key(T.sheet_id_para("Facturas", GRUPO)).worksheet("Facturas")
    v = ws.get_all_values()
    filas = [n for n, f in enumerate(v[1:], start=2) if MARCA in " ".join(f)]
    for r in sorted(filas, reverse=True):
        ws.delete_rows(r)
    print(f"Facturas: -{len(filas)} -> {len(ws.get_all_values())-1} filas")
    I._invalidate()


if __name__ == "__main__":
    {"crear": crear, "limpiar": limpiar}[sys.argv[1]]()
