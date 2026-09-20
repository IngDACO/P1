"""GUARDIÁN v364 — no se pagan dos veces las mismas horas.

El fallo salió con datos REALES: dos personas generaron nóminas a la vez (quincenas
20/07-02/08 y 03/08-16/08 contra un 21/07-19/08) y `generar` no dijo nada, porque su
salto de duplicados compara la TERNA EXACTA `(Usuario, Desde, Hasta)`. Resultado: a
`campo1` se le pagaron 567 h habiendo trabajado 354.

⚠️ Se prueba sobre la función REAL con un worksheet simulado, no sobre una copia de su
lógica: replicar el `if` en el test es lo que produjo el «OK en falso» de v324.
"""
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrator"}

from core import payroll as PR, timeclock as T, auth      # noqa: E402

G = "cliente1"
ok = True

# ── worksheet y entorno simulados: nada toca la hoja real ───────
class FakeWS:
    def __init__(self):
        self.escritas = []

    def append_rows(self, rows, **kw):
        self.escritas.extend(rows)

    def append_row(self, row, **kw):
        self.escritas.append(row)


NOMINAS = []          # lo que "ya existe"


def escenario(existentes, desde, hasta):
    """Corre la generar() REAL contra unas nóminas existentes dadas."""
    global NOMINAS
    NOMINAS = existentes
    ws = FakeWS()
    PR._ws = lambda: (ws, None)
    PR.list_nominas = lambda g, incluir_anuladas=False: [
        n for n in NOMINAS if incluir_anuladas or str(n.get("Status", "")).lower() != "anulada"]
    PR._max_num = lambda: 100
    T.horas_por_usuario_rango = lambda g, d, h: {
        "campo1": {"nombre": "lksdfkldsf", "horas": 80.0},
        "jlopez": {"nombre": "Javier López", "horas": 76.0}}
    auth.rate_map = lambda g: {"campo1": 40.0, "jlopez": 42.0}
    r = PR.generar(G, desde, hasta, super_pct=11.5, ret_pct=20.0, creado_por="test")
    return r, ws


print("== 1. sin nada previo → se generan las dos ==")
r, ws = escenario([], "2026-08-03", "2026-08-16")
print(f"   {r}")
ok &= r["creadas"] == 2 and not r.get("solapadas")

print("\n== 2. duplicado EXACTO → se omite (comportamiento de siempre, intacto) ==")
prev = [{"ID": "NOM-0001", "User": "campo1", "Name": "lksdfkldsf",
         "PeriodFrom": "2026-08-03", "PeriodTo": "2026-08-16", "Status": "emitida"}]
r, ws = escenario(prev, "2026-08-03", "2026-08-16")
print(f"   creadas {r['creadas']} · omitidas {r['omitidas']} · solapadas {len(r.get('solapadas') or [])}")
ok &= r["creadas"] == 1 and r["omitidas"] == 1 and not r.get("solapadas")

print("\n== 3. ⚠️ EL FALLO: periodo que SOLAPA → se bloquea y se nombra ==")
prev = [{"ID": "NOM-0009", "User": "campo1", "Name": "lksdfkldsf",
         "PeriodFrom": "2026-07-21", "PeriodTo": "2026-08-19", "Status": "emitida"}]
r, ws = escenario(prev, "2026-08-03", "2026-08-16")     # dentro del rango de arriba
print(f"   creadas {r['creadas']} (solo jlopez) · solapadas: {r.get('solapadas')}")
ok &= r["creadas"] == 1 and len(r.get("solapadas") or []) == 1
ok &= r["solapadas"][0]["id"] == "NOM-0009"
ok &= not any("lksdfkldsf" in str(f) for f in ws.escritas)   # campo1 NO se escribió
print(f"   ✓ campo1 NO recibió colilla; jlopez sí ({len(ws.escritas)} fila escrita)")

print("\n== 4. solape PARCIAL por un solo día (los bordes cuentan) ==")
for prev_d, prev_h, txt in (("2026-07-01", "2026-08-03", "termina el 1er día del nuevo"),
                            ("2026-08-16", "2026-09-01", "empieza el último día del nuevo")):
    prev = [{"ID": "NOM-X", "User": "campo1", "Name": "lksdfkldsf",
             "PeriodFrom": prev_d, "PeriodTo": prev_h, "Status": "emitida"}]
    r, _ = escenario(prev, "2026-08-03", "2026-08-16")
    bloq = bool(r.get("solapadas"))
    ok &= bloq
    print(f"   {'✓' if bloq else '✗'} {txt} ({prev_d}→{prev_h}) → bloqueado")

print("\n== 5. periodos CONTIGUOS que NO se tocan → se generan ==")
prev = [{"ID": "NOM-Y", "User": "campo1", "Name": "lksdfkldsf",
         "PeriodFrom": "2026-07-20", "PeriodTo": "2026-08-02", "Status": "emitida"}]
r, _ = escenario(prev, "2026-08-03", "2026-08-16")      # empieza justo al día siguiente
print(f"   creadas {r['creadas']} · solapadas {len(r.get('solapadas') or [])}")
ok &= r["creadas"] == 2 and not r.get("solapadas")
print("   ✓ una quincena pegada a la anterior NO se bloquea (si no, sería inservible)")

print("\n== 6. una nómina ANULADA no bloquea (principio de v347) ==")
prev = [{"ID": "NOM-Z", "User": "campo1", "Name": "lksdfkldsf",
         "PeriodFrom": "2026-07-21", "PeriodTo": "2026-08-19", "Status": "anulada"}]
r, _ = escenario(prev, "2026-08-03", "2026-08-16")
print(f"   creadas {r['creadas']} · solapadas {len(r.get('solapadas') or [])}")
ok &= r["creadas"] == 2 and not r.get("solapadas")
print("   ✓ se puede corregir: anular la solapada y volver a emitir")

print("\n== 7. fechas ilegibles → NO se afirma que solapan ==")
prev = [{"ID": "NOM-W", "User": "campo1", "Name": "lksdfkldsf",
         "PeriodFrom": "", "PeriodTo": "basura", "Status": "emitida"}]
r, _ = escenario(prev, "2026-08-03", "2026-08-16")
print(f"   creadas {r['creadas']} · solapadas {len(r.get('solapadas') or [])}")
ok &= r["creadas"] == 2
print("   ✓ sin fechas legibles no se puede afirmar un cruce → no se bloquea a ciegas")

print("\n" + ("✅ v364 OK: bloquea el solape, respeta el duplicado exacto, deja pasar "
              "quincenas contiguas y se puede deshacer anulando" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
