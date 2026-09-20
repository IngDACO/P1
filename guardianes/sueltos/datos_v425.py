"""Crea una localizacion con horas y gasto para VER v425 con datos, y la limpia.

Uso:  python datos_v425.py crear   |   python datos_v425.py limpiar

Datos de prueba en la empresa simulada (cliente1), autorizado por el usuario.
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
st.session_state["auth"] = {"usuario": "verif_v425", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "verif v425"}

from core import projects as P, expenses as E, timeclock as T, auth, clock

NOMBRE = "ZZZ Almacen Chullora"
MARCA = "v425-prueba"          # va en la descripcion del gasto y en la nota, para limpiar


def _libro():
    import gspread, toml
    from google.oauth2.service_account import Credentials
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    return gc.open_by_key(T.sheet_id_para("Proyectos", GRUPO))


def crear():
    ok, pid = P.create_project(GRUPO, NOMBRE, tipo="Almacén",
                               ubicacion="12 Distribution Dr, Chullora NSW",
                               ingeniero="Bobo", creado_por="verif_v425")
    assert ok, pid
    print(f"localizacion: {pid}")
    P._invalidate()
    time.sleep(1.0)

    ok2, msg = E.add(pid, GRUPO, 820.0, categoria="Otros", proveedor="Arriendo Chullora",
                     descripcion=f"alquiler mensual {MARCA}", creado_por="verif_v425")
    print(f"gasto: {ok2} · {msg}")
    E._invalidate()
    time.sleep(1.0)

    # Horas: dos personas CON tarifa, jornada + segmento interno (lo que hace
    # `fichar_proyecto`: abre la jornada sola y luego imputa).
    rates = auth.rate_map(GRUPO)
    quien = [u for u, t in rates.items() if float(t or 0) > 0][:2]
    print(f"personas con tarifa: {quien}")
    ws, err = T._get_worksheet()
    assert ws is not None, err
    filas = []
    for i, u in enumerate(quien):
        horas = 12.0 if i == 0 else 7.5
        ini = clock.now().replace(hour=7, minute=0, second=0, microsecond=0)
        fin = ini + __import__("datetime").timedelta(hours=horas)
        for tipo, pcol, pnom in ((T.TIPO_GENERAL, "", ""), (T.TIPO_PROYECTO, pid, NOMBRE)):
            filas.append([u, "", pnom, "", ini.strftime(T.FMT), fin.strftime(T.FMT),
                          str(horas), "Cerrado", GRUPO, tipo, u, pcol])
    ws.append_rows(filas, value_input_option="RAW")
    print(f"fichajes: {len(filas)} filas ({quien[0]} 12 h · {quien[1]} 7.5 h)")
    T._invalidate_records()
    try:
        T._ids_internos.clear()
    except Exception:
        pass
    print("\nCREADO. Ahora mirar Finanzas · Horas / Gastos / Resumen→Conciliacion.")


def limpiar():
    sh = _libro()
    # el pid se resuelve por NOMBRE, que es unico en esta prueba
    ws_p = sh.worksheet("Proyectos")
    v = ws_p.get_all_values()
    ic, inom = v[0].index("ID"), v[0].index("Nombre")
    pids = {f[ic] for f in v[1:] if f[inom] == NOMBRE}
    print(f"pids de la prueba: {sorted(pids) or '(ninguno)'}")
    total = 0
    for hoja, col in (("Sheet1", "ProyectoID"), ("Gastos", "ProyectoID"),
                      ("Proyectos", "ID")):
        ws = sh.worksheet(hoja)
        vv = ws.get_all_values()
        ix = vv[0].index(col)
        filas = [n for n, f in enumerate(vv[1:], start=2) if f[ix] in pids]
        for r in sorted(filas, reverse=True):
            ws.delete_rows(r)
        total += len(filas)
        print(f"   {hoja}: -{len(filas)}  -> {len(ws.get_all_values())-1} filas")

    # ⚠️ Las filas de JORNADA no tienen ProyectoID (por definicion): se localizan por
    # su firma exacta. Es lo que se me escapo en v422 y dejo 3 h sueltas.
    ws = sh.worksheet("Sheet1")
    vv = ws.get_all_values()
    ix = {h: vv[0].index(h) for h in ("Usuario", "Tipo", "Clock In", "ProyectoID", "Horas")}
    hoy = clock.today().strftime("%Y-%m-%d")
    cand = [n for n, f in enumerate(vv[1:], start=2)
            if f[ix["Tipo"]] == T.TIPO_GENERAL and not f[ix["ProyectoID"]].strip()
            and f[ix["Clock In"]].startswith(hoy)
            and f[ix["Clock In"]].endswith("07:00:00")
            and f[ix["Horas"]] in ("12.0", "7.5")]
    assert len(cand) <= 2, f"jornada: esperaba <=2, hay {cand}"
    for r in sorted(cand, reverse=True):
        ws.delete_rows(r)
    total += len(cand)
    print(f"   Sheet1 (jornada): -{len(cand)}  -> {len(ws.get_all_values())-1} filas")

    print(f"\nborradas {total} filas. Rastro:")
    for hoja in ("Proyectos", "Gastos", "Sheet1"):
        vv = sh.worksheet(hoja).get_all_values()
        n = sum(1 for f in vv[1:] if NOMBRE in " ".join(f) or MARCA in " ".join(f)
                or (pids and any(p in f for p in pids)))
        print(f"   {hoja}: {n}")


if __name__ == "__main__":
    {"crear": crear, "limpiar": limpiar}[sys.argv[1]]()
