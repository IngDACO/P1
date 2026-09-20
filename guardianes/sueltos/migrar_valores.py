# -*- coding: utf-8 -*-
"""Migra los VALORES guardados en las hojas al canonico ingles (capa 4 de v469).

Orden obligatorio, y no es ceremonia:
  1. desplegar v469  (el codigo canoniza al LEER, asi que aguanta las dos formas)
  2. ver el CAMBIO en produccion  (no la version: v334 corregido por v408/v452)
  3. este script

⚠️ Se puede correr DESPUES del deploy sin prisa, porque `valores.canonizar` traduce
la fila vieja al leerla. Lo que NO se puede es correrlo ANTES: el codigo viejo compara
contra el valor espanol y no encontraria nada.

Metodo de v344/v377: foto en SOLO LECTURA -> plan -> escribir -> verificar leyendo ->
segunda foto. El respaldo va FUERA del repo (v377/v422/v453: el deploy hace `git add`
de todo, y ya se ha colado tres veces).

⚠️ La lectura va por gspread CRUDO con scope `spreadsheets`, nunca por los helpers de
la app: `get_sheet` MIGRA la cabecera al acceder, o sea que una «lectura» escribe
(regla v145).
"""
import datetime
import io
import json
import os
import sys

import gspread
from google.oauth2.service_account import Credentials

sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
from core import valores as VAL  # noqa: E402

RESPALDO = r"C:\Users\diego\respaldo_sheets"     # ⚠️ FUERA del repo
SECRETS = r"C:\Users\diego\P1\survey_app\.streamlit\secrets.toml"
APLICAR = "--aplicar" in sys.argv


def _cliente():
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    with open(SECRETS, "rb") as f:
        sec = tomllib.load(f)
    cred = Credentials.from_service_account_info(
        sec["gcp_service_account"],
        # ⚠️ En modo PLAN el scope es de SOLO LECTURA: asi la auditoria no puede
        # escribir ni por accidente (regla v145).
        scopes=["https://www.googleapis.com/auth/spreadsheets" if APLICAR
                else "https://www.googleapis.com/auth/spreadsheets.readonly"])
    return gspread.authorize(cred), sec


def main():
    gc, sec = _cliente()
    maestro_id = sec["TIMECLOCK_SHEET_ID"]

    # los libros: el maestro y el de cada grupo con SheetID propio
    libros = {"MAESTRO": maestro_id}
    try:
        mg = gc.open_by_key(maestro_id).worksheet("Groups")
        filas = mg.get_all_values()
        cab = filas[0] if filas else []
        i_g = cab.index("Group") if "Group" in cab else 0
        i_s = cab.index("SheetID") if "SheetID" in cab else -1
        for r in filas[1:]:
            if i_s >= 0 and len(r) > i_s and r[i_s].strip():
                libros[r[i_g]] = r[i_s].strip()
    except Exception as e:
        print("!! no se pudo leer Groups: %s" % e)

    print("libros: %s\n" % {k: v[:12] + "..." for k, v in libros.items()})

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(RESPALDO, exist_ok=True)
    foto, plan_total, tocadas = {}, 0, 0

    for etq, sid in libros.items():
        try:
            libro = gc.open_by_key(sid)
        except Exception as e:
            print("!! %s: %s" % (etq, e))
            continue
        titulos = {w.title: w for w in libro.worksheets()}
        for hoja, col in sorted(VAL.COLUMNAS):
            ws = titulos.get(hoja)
            if ws is None:
                continue
            vals = ws.get_all_values()
            if len(vals) < 2:
                continue
            cab = vals[0]
            if col not in cab:
                continue
            ci = cab.index(col)
            foto["%s/%s/%s" % (etq, hoja, col)] = [
                r[ci] if len(r) > ci else "" for r in vals[1:]]
            cambios = []
            for n, r in enumerate(vals[1:], start=2):
                v = r[ci] if len(r) > ci else ""
                c = VAL.canon(v)
                if v and c != v:
                    cambios.append((n, v, c))
            if not cambios:
                continue
            plan_total += len(cambios)
            tocadas += 1
            muestra = ", ".join("%s->%s" % (a, b) for _f, a, b in cambios[:3])
            print("  %-9s %-18s %-14s %3d celda(s)  %s"
                  % (etq, hoja, col, len(cambios), muestra))
            if APLICAR:
                letra = gspread.utils.rowcol_to_a1(1, ci + 1).rstrip("1")
                cuerpo = [{"range": "%s%d" % (letra, f), "values": [[c]]}
                          for f, _v, c in cambios]
                ws.batch_update(cuerpo, value_input_option="RAW")

    p = os.path.join(RESPALDO, "valores_v469_%s.json" % ts)
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(foto, ensure_ascii=False, indent=1))
    print("\nfoto previa: %s  (%d columnas)" % (p, len(foto)))
    print("=== %d celdas en %d columnas · %s ==="
          % (plan_total, tocadas, "APLICADO" if APLICAR else "SOLO PLAN (usa --aplicar)"))


if __name__ == "__main__":
    main()
