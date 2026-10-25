# -*- coding: utf-8 -*-
"""v600 · Los movimientos de inventario escritos en ESPAÑOL pasan al dato canónico (inglés).

Hasta v599 la devolución escribía «bodega: <sitio>» y la baja/reactivación «baja» en
AssetMovements (From/To). La pantalla los traducía al pintarlos, pero el dato es inglés desde
v453: «bodega…» → «warehouse…» y «baja» → «written off».

Uso (desde survey_app, como los guardianes):
    py -3.12 ..\\guardianes\\sueltos\\migrar_v600_movimientos.py            → solo enseña
    py -3.12 ..\\guardianes\\sueltos\\migrar_v600_movimientos.py --aplicar  → copia y escribe

⚠️ Antes de escribir guarda una COPIA de cada hoja tocada en D:\\CopeX\\respaldos (FUERA del
repo: son datos reales, y el despliegue hace `git add` de todo).
"""
import datetime
import io
import json
import os
import sys

import gspread
import tomllib
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APLICAR = "--aplicar" in sys.argv
SEC = tomllib.load(open(os.path.join(".streamlit", "secrets.toml"), "rb"))
_SC = ["https://www.googleapis.com/auth/spreadsheets"] if APLICAR else \
      ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(dict(SEC["gcp_service_account"]), scopes=_SC))
RESP = r"D:\CopeX\respaldos"


def nuevo(v: str):
    """El valor canónico, o None si no hay que tocarlo."""
    s = str(v or "")
    pre, sep, resto = s.partition(":")
    if pre.strip().lower() == "bodega":
        return "warehouse" + (sep + resto if sep else "")
    if s.strip().lower() == "baja":
        return "written off"
    return None


m = gc.open_by_key(SEC["TIMECLOCK_SHEET_ID"])
libros = {"(maestro)": SEC["TIMECLOCK_SHEET_ID"]}
for r in m.worksheet("Groups").get_all_records():
    if str(r.get("SheetID", "")).strip():
        libros[str(r.get("Group", ""))] = str(r.get("SheetID")).strip()

total = 0
for g, sid in libros.items():
    L = gc.open_by_key(sid)
    if "AssetMovements" not in {w.title for w in L.worksheets()}:
        continue
    w = L.worksheet("AssetMovements")
    vals = w.get_all_values()
    if not vals:
        continue
    cab = vals[0]
    cols = [cab.index(c) for c in ("FromLocation", "ToLocation") if c in cab]
    cambios = []
    for i, fila in enumerate(vals[1:], start=2):
        for c in cols:
            v = fila[c] if c < len(fila) else ""
            n = nuevo(v)
            if n is not None:
                cambios.append((i, c, v, n))
    for i, c, v, n in cambios:
        print("%s · fila %d · %s: %r → %r" % (g, i, cab[c], v, n))
    total += len(cambios)
    if APLICAR and cambios:
        os.makedirs(RESP, exist_ok=True)
        _f = os.path.join(RESP, "AssetMovements_%s_antes_de_v600_%s.json" % (
            g.strip("()"), datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")))
        io.open(_f, "w", encoding="utf-8").write(json.dumps(vals, ensure_ascii=False))
        print("copia:", _f)
        w.batch_update([{"range": gspread.utils.rowcol_to_a1(i, c + 1), "values": [[n]]}
                        for i, c, v, n in cambios], value_input_option="RAW")
        print("%s: %d celdas escritas" % (g, len(cambios)))
print("total:", total, "(escrito)" if APLICAR else "(solo enseñado: --aplicar para escribir)")
