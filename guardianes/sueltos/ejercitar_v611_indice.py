# -*- coding: utf-8 -*-
"""v611 · Ejercicio contra el libro REAL (método v344): una pestaña creada por OTRO cliente de la
API —como la siembra de v610, que dejó la memoria invisible en producción— se lee con el índice
de pestañas ya construido, y con el tope de 10 minutos.

    py -3.12 sueltos/ejercitar_v611_indice.py

⚠️ ESCRIBE en el libro MAESTRO: crea UNA pestaña de prueba (`ZZ_v611_indice`) y la BORRA al final
(solo una que se llame exactamente así). No toca ninguna otra.

1. este proceso construye el índice y pide la pestaña: no existe → rehace el índice (el tope
   empieza a contar) → None;
2. OTRO cliente gspread la crea, con cabecera y una fila;
3. dentro de los 10 minutos: None, sin rehacer nada (el tope vale de verdad);
4. pasados (el reloj del tope se adelanta): la lee — rehace el índice y el lote;
5. `ids_referenciados` la ve también (ruta de escritura);
6. se borra.
"""
import os
import sys
import time

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gspread                                                    # noqa: E402
import tomllib                                                    # noqa: E402
from google.oauth2.service_account import Credentials            # noqa: E402

from core import hojas as H                                       # noqa: E402
from core import timeclock as TC                                  # noqa: E402

NOMBRE = "ZZ_v611_indice"
SEC = tomllib.load(open(os.path.join(RAIZ, ".streamlit", "secrets.toml"), "rb"))
fallos = []


def chk(q, cond, det=""):
    print("   %s %s%s" % ("ok   " if cond else "FALLO", q, "" if cond else "  -> %s" % (det,)))
    if not cond:
        fallos.append(q)


SID = TC.sheet_id_para("Sheet1")
chk("el libro es el MAESTRO (sin sesión)", SID == SEC["TIMECLOCK_SHEET_ID"])
otro = gspread.authorize(Credentials.from_service_account_info(
    dict(SEC["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets"]))
ss_otro = otro.open_by_key(SID)
if any(w.title == NOMBRE for w in ss_otro.worksheets()):
    print("⚠️ %s ya existe (¿una vuelta anterior cortada?): se borra antes de empezar" % NOMBRE)
    ss_otro.del_worksheet(ss_otro.worksheet(NOMBRE))

H.HOJAS_LECTURA = H.HOJAS_LECTURA + (NOMBRE,)        # en MEMORIA: la pestaña cuenta como del lote
H._refrescado.clear()
try:
    _hojas, _cab = TC._libro(SID)
    chk("1. el índice de este proceso, construido ANTES (sin la pestaña)", NOMBRE.lower() not in _hojas)
    chk("...pedida sin existir: None", H.registros(NOMBRE) is None)
    chk("...y el tope empieza a contar", SID in H._refrescado)

    w = ss_otro.add_worksheet(title=NOMBRE, rows=10, cols=3)
    w.update(range_name="A1:B2", values=[["ID", "Note"], ["ZZ-0001", "v611"]])
    print("   2. OTRO cliente creó %s con una fila" % NOMBRE)

    chk("3. dentro de los 10 min: None, sin rehacer (el tope)", H.registros(NOMBRE) is None)

    H._refrescado[SID] = time.monotonic() - H._REFRESCO_S - 1
    _r = H.registros(NOMBRE)
    chk("4. ⚠️ pasados los 10 min, SE LEE (antes: None hasta reiniciar la app)",
        _r is not None and [x.get("ID") for x in _r] == ["ZZ-0001"], _r)
    chk("...y ya está en el índice", NOMBRE.lower() in TC._libro(SID)[0])
    chk("...y la siguiente lectura sale del lote", H.registros(NOMBRE) == _r)

    H._refrescado[SID] = time.monotonic() - H._REFRESCO_S - 1
    _ids = H.ids_referenciados("ZZ-", propia="Sheet1", sheet_id=SID)
    chk("5. `ids_referenciados` la ve (ZZ-0001 no se reutilizaría)", "ZZ-0001" in _ids, _ids)
finally:
    try:
        _w = next((x for x in ss_otro.worksheets() if x.title == NOMBRE), None)
        if _w is not None:
            ss_otro.del_worksheet(_w)
        chk("6. la pestaña de prueba, BORRADA", not any(x.title == NOMBRE for x in ss_otro.worksheets()))
    except Exception as e:
        chk("6. la pestaña de prueba, BORRADA", False, e)

print("")
print("FALLOS: %d" % len(fallos) if fallos else "TODO OK")
sys.exit(1 if fallos else 0)
