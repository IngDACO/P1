"""Ejercita el cerrojo de v422 CONTRA LA HOJA REAL, con una localizacion de verdad.

⚠️ La comparacion antes/despues con 0 localizaciones NO prueba el cerrojo: un
`incluir_internos` que nunca filtrara daria exactamente el mismo resultado (el paso
en vacio, trampa nº1). Esto crea una localizacion real, le carga un gasto y le ficha
horas, y comprueba las DOS direcciones: donde NO debe salir y donde SI.

Metodo de v344: foto -> ejercitar -> verificar leyendo -> limpiar -> segunda foto.
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
st.session_state["auth"] = {"usuario": "verif_v422", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "verif v422"}

from core import projects as P, expenses as E, finance as F, timeclock as T
from core import invoices as I, roster as R, clock

NOMBRE = "ZZZ Almacen Prueba v422"
ok = True
creado = {"pid": None, "marca": None}   # marca = (usuario, "Clock In") de la jornada


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {t}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def limpiar():
    """Devuelve produccion a su estado. Se llama pase lo que pase."""
    print("\n== limpieza ==")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    sh = gc.open_by_key(T.sheet_id_para("Proyectos", GRUPO))
    # ⚠️ TODO se localiza por el PID, no por ids devueltos: `expenses.add` NO devuelve
    # el ID del gasto sino un MENSAJE («Recibo agregado (500.00).»), así que la primera
    # version de esta limpieza borro 0 gastos y dejo $500 sueltos en produccion. Regla
    # v135 — comprobar la FORMA del retorno, no el nombre que parece logico.
    for hoja, col in (("Sheet1", "ProyectoID"), ("Gastos", "ProyectoID"),
                      ("Proyectos", "ID")):
        if not creado["pid"]:
            continue
        ws = sh.worksheet(hoja)
        v = ws.get_all_values()
        idx = v[0].index(col)
        filas = [i for i, f in enumerate(v[1:], start=2) if f[idx] == creado["pid"]]
        for r in sorted(filas, reverse=True):
            ws.delete_rows(r)
        print(f"   {hoja}: borradas {len(filas)} fila(s)")

    # ⚠️ La fila de JORNADA no tiene ProyectoID —por definicion— asi que el barrido de
    # arriba NO la alcanza: la primera corrida dejo 3 h sueltas en produccion. Se
    # localiza por su firma exacta y se exige que sea UNA, para no borrar a ciegas.
    if creado["marca"]:
        ws = sh.worksheet("Sheet1")
        v = ws.get_all_values()
        ix = {h: v[0].index(h) for h in ("Usuario", "Tipo", "Clock In", "ProyectoID")}
        u, ci = creado["marca"]
        cand = [i for i, f in enumerate(v[1:], start=2)
                if f[ix["Usuario"]] == u and f[ix["Tipo"]] == T.TIPO_GENERAL
                and f[ix["Clock In"]] == ci and not f[ix["ProyectoID"]].strip()]
        assert len(cand) <= 1, f"jornada: esperaba <=1 fila, hay {cand}"
        for r in cand:
            ws.delete_rows(r)
        print(f"   Sheet1 (jornada): borradas {len(cand)} fila(s)")
    P._invalidate()
    E._invalidate()
    T._invalidate_records()


try:
    # ── 1. Crear la localizacion ────────────────────────────────────
    print("== 1. alta ==")
    _ok, pid = P.create_project(GRUPO, NOMBRE, tipo="Almacén",
                                ubicacion="Unit 4, 12 Industrial Dr",
                                creado_por="verif_v422")
    chk("create_project devuelve ok", _ok)
    creado["pid"] = pid if _ok else None
    print(f"         pid={pid}")
    assert _ok, pid
    P._invalidate()
    time.sleep(1.0)

    prj = P.get_project(pid)
    chk("es_interno", P.es_interno(prj))
    chk("Estado = Abierta", str(prj.get("Estado")), P.INTERNO_ABIERTA)
    chk("sin actividades (no tiene cronograma)", len(P.list_activities(pid)), 0)

    # ── 2. Donde NO debe salir ──────────────────────────────────────
    print("\n== 2. NO sale donde hablaria de dinero de cliente ==")
    chk("cartera de obras", pid in [p["ID"] for p in P.list_projects(grupo=GRUPO)], False)
    chk("...ni con archivados",
        pid in [p["ID"] for p in P.list_projects(grupo=GRUPO, incluir_archivados=True)], False)
    time.sleep(1.0)
    chk("pendiente_por_proyecto (facturar)",
        pid in I.pendiente_por_proyecto(GRUPO), False)
    time.sleep(1.0)
    chk("gaps / retraso SPI", pid in P.gaps_by_group(GRUPO), False)
    time.sleep(1.0)
    _res = F.resultado_por_proyecto(GRUPO)
    chk("resultado por proyecto",
        any(str(r.get("id")) == pid for r in _res), False)

    # ── 3. Donde SI debe salir ──────────────────────────────────────
    print("\n== 3. SI sale donde se trabaja ==")
    chk("list_locations", pid in [p["ID"] for p in P.list_locations(GRUPO)])
    chk("list_projects(incluir_internos=True)",
        pid in [p["ID"] for p in P.list_projects(grupo=GRUPO, incluir_internos=True)])
    time.sleep(1.0)
    R._invalidate()
    chk("roster: resuelve nombre y color", str(R.trabajos_idx(GRUPO).get(pid, {}).get("Nombre")),
        NOMBRE)

    # ── 4. Gasto: cuenta como estructura, NO como huerfano ──────────
    print("\n== 4. el gasto ==")
    _ge0 = E.group_expenses(GRUPO)
    _h0 = dict(_ge0["huerfanos"])
    _cg0 = _ge0["compras_grupo"]
    # ⚠️ devuelve (ok, MENSAJE), no (ok, id) — se limpia por ProyectoID.
    _ok2, _msg = E.add(pid, GRUPO, 500.0, categoria="Otros", proveedor="Prueba v422",
                       descripcion="alquiler almacen", creado_por="verif_v422")
    chk("gasto creado", _ok2)
    E._invalidate()
    time.sleep(1.2)
    _ge = E.group_expenses(GRUPO)
    _fila = next((f for f in _ge["proyectos"] if str(f["id"]) == pid), None)
    chk("aparece en group_expenses (es costo del grupo)", _fila is not None)
    chk("...marcada como interna", bool(_fila and _fila.get("interno")))
    chk("compras del grupo suben 500", round(_ge["compras_grupo"] - _cg0, 2), 500.0)
    chk("NO se cuenta como huerfana", _ge["huerfanos"]["n"], _h0["n"])
    time.sleep(1.2)
    _gp = F.group_profitability(GRUPO)
    chk("NO entra en rentabilidad", any(str(r["id"]) == pid for r in _gp["rows"]), False)

    # ── 5. Horas: van a `interno`, no a `proyecto` ──────────────────
    print("\n== 5. las horas ==")
    from core import auth
    _rates = auth.rate_map(GRUPO)
    _u = next((u for u, t in _rates.items() if float(t or 0) > 0), None)
    print(f"         usuario con tarifa: {_u} (${_rates.get(_u)}/h)")
    _hp0 = T.jornada_y_proyecto(GRUPO).get(_u, {})
    _ini = clock.now().replace(hour=8, minute=0, second=0, microsecond=0)
    _fin = _ini.replace(hour=11)
    # fila de JORNADA + fila de PROYECTO (lo que hace `fichar_proyecto`)
    # ⚠️ devuelve (ws, err), no el worksheet suelto — regla v135, otra vez.
    _ws, _err = T._get_worksheet()
    assert _ws is not None, _err
    for _tipo, _pid_col in ((T.TIPO_GENERAL, ""), (T.TIPO_PROYECTO, pid)):
        _ws.append_row([_u, "", NOMBRE if _pid_col else "", "",
                        _ini.strftime(T.FMT), _fin.strftime(T.FMT), "3.0",
                        "Cerrado", GRUPO, _tipo, _u, _pid_col],
                       value_input_option="RAW")
        if _tipo == T.TIPO_GENERAL:
            creado["marca"] = (_u, _ini.strftime(T.FMT))
    T._invalidate_records()
    T._ids_internos.clear()
    time.sleep(1.5)
    _hp = T.jornada_y_proyecto(GRUPO).get(_u, {})
    chk("+3 h de jornada", round(_hp["jornada"] - _hp0.get("jornada", 0), 2), 3.0)
    chk("+3 h INTERNAS", round(_hp.get("interno", 0) - _hp0.get("interno", 0), 2), 3.0)
    chk("+0 h de obra (no se le carga a ningun cliente)",
        round(_hp["proyecto"] - _hp0.get("proyecto", 0), 2), 0.0)
    time.sleep(1.2)
    _c = F.conciliacion_mo(GRUPO)
    chk("conciliacion: `interno` > 0", _c["interno"] > 0)
    print(f"         cargado a obras ${_c['cargado']:,.2f} · interno ${_c['interno']:,.2f}")

except Exception as e:
    ok = False
    import traceback
    traceback.print_exc()
finally:
    try:
        limpiar()
    except Exception:
        import traceback
        traceback.print_exc()
        print("  !! LIMPIEZA FALLIDA — revisar a mano:", creado)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
