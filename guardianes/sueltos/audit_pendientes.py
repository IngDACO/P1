"""Auditoría de los 3 pendientes, en SOLO LECTURA.

⚠️ gspread crudo con scope `readonly` (regla v145): `timeclock.get_sheet` y
`projects._get_ws` MIGRAN la cabecera al acceder, así que un "lector" que pase por
los helpers de la app ESCRIBE.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import gspread                                             # noqa: E402
import streamlit as st                                     # noqa: E402
from google.oauth2.service_account import Credentials      # noqa: E402

RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
gc = gspread.authorize(Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=RO))
libro = gc.open_by_key(st.secrets["TIMECLOCK_SHEET_ID"])


def filas(t):
    try:
        return libro.worksheet(t).get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


print("=" * 72)
print("1. GRUPOS — ¿quién tiene libro propio? (v359)")
print("=" * 72)
for g in filas("Grupos"):
    sid = str(g.get("SheetID", "")).strip()
    print(f"   {str(g.get('Grupo')):<16} activo={g.get('Activo'):<4} "
          f"zona={str(g.get('Zona') or '—'):<18} libro propio: {'SÍ' if sid else 'no (maestro)'}")

print("\n" + "=" * 72)
print("2. CUENTAS — cuáles son de prueba y cuál es `admin2`")
print("=" * 72)
for u in filas("Login"):
    usr = str(u.get("Usuario", ""))
    print(f"   {usr:<14} rol={str(u.get('Rol')):<14} grupo={str(u.get('Grupo') or '—'):<10} "
          f"activo={str(u.get('Activo')):<4} nombre={str(u.get('Nombre'))[:18]:<19} "
          f"email={'sí' if str(u.get('Email','')).strip() else 'NO':<3} "
          f"tg={'sí' if str(u.get('TelegramChatID','')).strip() else 'NO'}")

print("\n" + "=" * 72)
print("3. VOLUMEN de datos en el libro maestro")
print("=" * 72)
HOJAS = ["Sheet1", "Proyectos", "Actividades", "Agrupaciones", "Documentos", "Alarmas",
         "Gastos", "Clientes", "Facturas", "Nominas", "Activos", "MovimientosActivo",
         "Roster", "Trabajos", "PreStarts", "Calculos", "Auditoria", "Ordenes",
         "Catalogo", "Cotizaciones", "Credenciales", "Rieles"]
total = 0
for h in HOJAS:
    fs = filas(h)
    if not fs:
        continue
    # ¿cuántas son del grupo cliente1?
    col_g = "Grupo" if any("Grupo" in f for f in fs[:1]) else None
    n1 = sum(1 for f in fs if str(f.get("Grupo", "")) == "cliente1") if col_g else None
    total += len(fs)
    print(f"   {h:<20} {len(fs):>4} filas" + (f"   ({n1} de cliente1)" if n1 is not None else ""))
print(f"   {'TOTAL':<20} {total:>4} filas")

print("\n" + "=" * 72)
print("4. FASE 2 — qué vistas del PROPIETARIO solo cuentan el libro maestro")
print("=" * 72)
print("   (las que leen TODOS los grupos de una vez; con un libro por cliente")
print("    tendrían que abrir N libros)")
import ast
import pathlib
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
for f in sorted(BASE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    try:
        arbol = ast.parse(src)
    except Exception:
        continue
    for n in ast.walk(arbol):
        if not isinstance(n, ast.FunctionDef):
            continue
        cuerpo = ast.unparse(n)
        # llamadas sin filtrar por grupo
        if ("list_projects()" in cuerpo or "list_users()" in cuerpo
                or "owner_digest" in n.name):
            print(f"   {f.name:<18} {n.name}")
