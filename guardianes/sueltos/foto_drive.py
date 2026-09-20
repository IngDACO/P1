"""Foto del estado ANTES de ejercitar las 4 escrituras de Drive.

⚠️ SOLO LECTURA y por gspread CRUDO con scope readonly: los helpers de la app
(`timeclock.get_sheet`, `projects._get_ws`…) MIGRAN LA CABECERA en cualquier acceso, así
que una "lectura" por ahí escribe (regla v145, aprendida a base de hacerlo mal).

Sin foto previa no se puede afirmar después que algo se creó: se estaría comparando
contra un recuerdo.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import gspread                                                    # noqa: E402
from google.oauth2.service_account import Credentials             # noqa: E402
import tomllib                                                    # noqa: E402

with open(RAIZ / ".streamlit" / "secrets.toml", "rb") as fh:
    sec = tomllib.load(fh)

cred = Credentials.from_service_account_info(
    sec["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
gc = gspread.authorize(cred)

# ⚠️ El libro del grupo `cliente1` NO es el maestro desde la mudanza de v377.
LIBRO_DEMO = "1WHGCrZndwdmqrR3RehLh7jocOIVkRvjAbigifvfSe1Y"
sh = gc.open_by_key(LIBRO_DEMO)

print(f"libro: {sh.title}\n")
for hoja in ("Documentos", "Gastos", "Manuales", "Credenciales"):
    try:
        w = sh.worksheet(hoja)
        vals = w.get_all_values()
    except Exception as e:                                        # noqa: BLE001
        print(f"  {hoja:14} — no existe todavía ({type(e).__name__})")
        continue
    cab = vals[0] if vals else []
    filas = vals[1:] if len(vals) > 1 else []
    print(f"  {hoja:14} {len(filas):3} filas")
    if hoja == "Documentos":
        _i = {c: i for i, c in enumerate(cab)}
        con_drive = [f for f in filas
                     if _i.get("DriveID") is not None
                     and len(f) > _i["DriveID"] and f[_i["DriveID"]].strip()]
        print(f"                   {len(con_drive)} con DriveID")
        for f in filas[-3:]:
            print("                   ...", " | ".join(f[:4]))
    if hoja == "Gastos":
        _i = {c: i for i, c in enumerate(cab)}
        col = _i.get("Archivo") or _i.get("DriveID")
        if col is not None:
            con = [f for f in filas if len(f) > col and f[col].strip()]
            print(f"                   {len(con)} con recibo adjunto "
                  f"(columna {cab[col]})")
    print()

print("Cabeceras (para saber dónde mirar después):")
for hoja in ("Documentos", "Gastos", "Manuales"):
    try:
        print(f"  {hoja:12} {sh.worksheet(hoja).row_values(1)}")
    except Exception:
        pass
