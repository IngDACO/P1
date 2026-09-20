"""AUDITORIA: ¿está de verdad cerrado y funcionando?

⚠️ Los guardianes prueban LOGICA. v427 tocó tres rutas de ESCRITURA
(`_next_project_id`, `clientes._next_id`, `expenses._next_id`) y ninguna se ha
ejercitado con ese código: crear de verdad es lo unico que lo demuestra.

Ejercita las tres, comprueba que el ID emitido SALTA el que sigue referenciado, y
limpia. Metodo de v344.
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
st.session_state["auth"] = {"usuario": "audit", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "audit"}

from core import projects as P, clientes as CL, expenses as E, hojas, timeclock as T

ok = True
creado = {"pid": None, "cli": None, "gasto_pid": None}


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def limpiar():
    print("\n== limpieza ==")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    sh = gc.open_by_key(T.sheet_id_para("Proyectos", GRUPO))
    for hoja, col, val in (("Gastos", "ProyectoID", creado["gasto_pid"]),
                           ("Proyectos", "ID", creado["pid"]),
                           ("Clientes", "ID", creado["cli"])):
        if not val:
            continue
        ws = sh.worksheet(hoja)
        v = ws.get_all_values()
        i = v[0].index(col)
        filas = [n for n, f in enumerate(v[1:], start=2) if f[i] == val]
        for r in sorted(filas, reverse=True):
            ws.delete_rows(r)
        print(f"   {hoja}: -{len(filas)} -> {len(ws.get_all_values())-1} filas")
    for f in (P._invalidate, E._invalidate, CL._invalidate):
        try:
            f()
        except Exception:
            pass


try:
    print("=" * 66)
    print("1. ¿Qué IDs están referenciados pero YA NO existen?")
    print("=" * 66)
    ref = hojas.ids_referenciados("PRJ-", propia="Proyectos")
    vivos = {p["ID"] for p in P.list_projects(incluir_archivados=True,
                                              incluir_internos=True)}
    fantasmas = sorted(ref - vivos)
    mx = max(int(p.split("-")[1]) for p in vivos)
    print(f"   proyectos vivos: {len(vivos)} (máximo PRJ-{mx:04d})")
    print(f"   referenciados que ya no existen: {fantasmas}")
    print(f"   -> sin v427 el siguiente sería PRJ-{mx+1:04d}")

    print("\n" + "=" * 66)
    print("2. CREAR UN PROYECTO DE VERDAD (la escritura que v427 tocó)")
    print("=" * 66)
    _ok, pid = P.create_project(GRUPO, "ZZZ Auditoria v427", tipo="Instalación",
                                creado_por="audit")
    chk("create_project funciona", _ok)
    creado["pid"] = pid if _ok else None
    print(f"   ID emitido: {pid}")
    if fantasmas and f"PRJ-{mx+1:04d}" in fantasmas:
        chk("SALTA el ID que sigue referenciado", pid != f"PRJ-{mx+1:04d}")
    else:
        chk("emite el siguiente (no había nada que saltar)", pid, f"PRJ-{mx+1:04d}")
    chk("...y el ID emitido NO estaba referenciado", pid in ref, False)
    P._invalidate(); time.sleep(1.2)
    chk("el proyecto existe y es suyo",
        str(P.get_project(pid).get("Nombre")), "ZZZ Auditoria v427")

    print("\n" + "=" * 66)
    print("3. CREAR UN CLIENTE DE VERDAD")
    print("=" * 66)
    _refc = hojas.ids_referenciados("CLI-", propia="Clientes")
    _ok, cid = CL.create_cliente(GRUPO, "ZZZ Auditoria Cliente", creado_por="audit")
    chk("create_cliente funciona", _ok)
    creado["cli"] = cid if _ok else None
    print(f"   ID emitido: {cid}  (referenciados: {sorted(_refc)})")
    chk("el ID emitido NO estaba referenciado", cid in _refc, False)

    print("\n" + "=" * 66)
    print("4. CREAR UN GASTO DE VERDAD")
    print("=" * 66)
    _refg = hojas.ids_referenciados("G-", propia="Gastos")
    _ok, _msg = E.add(pid, GRUPO, 12.34, categoria="Otros",
                      descripcion="auditoria v427", creado_por="audit")
    chk("expenses.add funciona", _ok)
    creado["gasto_pid"] = pid if _ok else None
    E._invalidate(); time.sleep(1.2)
    _g = [r for r in E._records() if str(r.get("ProyectoID")) == pid]
    chk("el gasto se guardó", len(_g), 1)
    if _g:
        print(f"   ID emitido: {_g[0]['ID']}  (referenciados: {sorted(_refg) or 'ninguno'})")
        chk("el ID emitido NO estaba referenciado", _g[0]["ID"] in _refg, False)

except Exception:
    ok = False
    import traceback
    traceback.print_exc()
finally:
    try:
        limpiar()
    except Exception:
        import traceback
        traceback.print_exc()
        print("  !! LIMPIEZA FALLIDA:", creado)

print("\n" + ("ESCRITURAS DE v427 EJERCITADAS OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
