"""Auditoría de v430/v431: qué queda ABIERTO. Con evidencia, no con un OK.

No comprueba lo que ya salió verde: busca los huecos que nadie ha mirado —los que
tocan dinero primero— y las integraciones con las pantallas que dependen del roster.
Todo LECTURA salvo lo que se dice; nada se deja escrito.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os                                                       # noqa: E402
os.chdir(RAIZ)

import streamlit as st                                          # noqa: E402
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "audit", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "audit"}

from core import ausencias as AU                                # noqa: E402
import ast                                                      # noqa: E402

hallazgos = []


def h(grave, titulo, detalle):
    hallazgos.append((grave, titulo, detalle))
    print(f"\n{'⛔' if grave else '⚠️ '} {titulo}\n   {detalle}")


def paso(t):
    print(f"\n{'─' * 70}\n{t}\n{'─' * 70}")


# ── 1 · ¿Se puede cobrar DOS VECES el mismo día? ─────────────────
paso("1. ¿Ausencia pagada + horas fichadas EL MISMO DÍA = doble pago?")
# `payroll.generar`: base = horas fichadas × tarifa · devengo = días de ausencia × 8 h
# Nada comprueba que ese día la persona además fichara.
src = (RAIZ / "core" / "payroll.py").read_text(encoding="utf-8")
tree = ast.parse(src)
gen = next(n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == "generar")
cuerpo = ast.unparse(gen)
solapa = ("horas_pagadas" in cuerpo and "aus" in cuerpo
          and "solap" not in cuerpo.lower() and "fich" not in cuerpo.lower())
print(f"   `generar` cruza ausencia contra días fichados: {not solapa}")
if solapa:
    h(True, "SE PUEDE PAGAR DOS VECES EL MISMO DÍA",
      "Si alguien tiene vacaciones aprobadas el lunes y además FICHA ese lunes, la "
      "nómina suma sus horas fichadas (Base) Y 8 h de ausencia (devengo). Nada lo "
      "comprueba ni lo avisa.")

# ── 2 · Asignar a alguien que está de vacaciones ─────────────────
paso("2. ¿Avisa al asignar personal a una obra en días que ya tiene ausencia?")
pu = (RAIZ / "core" / "projects_ui.py").read_text(encoding="utf-8")
t2 = ast.parse(pu)
av = next((n for n in ast.walk(t2) if isinstance(n, ast.FunctionDef)
           and n.name == "_avisar_asignados"), None)
usa = "ausencias" in ast.unparse(av).lower() if av else False
print(f"   `_avisar_asignados` mira las ausencias: {usa}")
if not usa:
    h(False, "Asignar personal NO avisa de las ausencias ya aprobadas",
      "Avisa de otras obras y de certificados (v219), pero se puede asignar a alguien "
      "a una obra justo en su semana de vacaciones sin que nada lo diga. El tablero "
      "sí lo respeta (auto-poblar solo llena celdas VACÍAS y la ausencia no lo está).")

# ── 3 · Integración con las vistas que leen el roster ────────────
paso("3. ¿El LEAVE de una ausencia se comporta como cualquier LEAVE?")
from core import roster as R                                    # noqa: E402
print(f"   roster.ESTADOS = {R.ESTADOS}")
ok_estados = all(c["estado_roster"] in R.ESTADOS for c in AU.TIPOS.values())
print(f"   los estados que escribe ausencias existen en el roster: {ok_estados}")
if not ok_estados:
    h(True, "Ausencias escribe un estado que el tablero no conoce", "")

# ── 4 · Rutas de ESCRITURA sin ejercitar ────────────────────────
paso("4. Rutas de escritura de v430: ¿cuáles se han ejercitado?")
ejercitadas = {"solicitar", "resolver(aprobar=True)", "cancelar",
               "aplicar_al_roster", "aplicar_al_roster(quitar=True)"}
todas = {"solicitar", "resolver(aprobar=True)", "resolver(aprobar=False)",
         "cancelar", "aplicar_al_roster", "aplicar_al_roster(quitar=True)"}
faltan = sorted(todas - ejercitadas)
for f in sorted(todas):
    print(f"   {'OK  ' if f in ejercitadas else 'SIN '} {f}")
if faltan:
    h(False, "Rutas de escritura sin ejercitar", ", ".join(faltan))

# ── 5 · Los avisos por correo/Telegram ──────────────────────────
paso("5. Los avisos (correo/Telegram) al pedir y al resolver")
from core.alerts import _admins_and_owners                      # noqa: E402
from core import auth, notify                                   # noqa: E402
dest = _admins_and_owners(GRUPO)
sin_canal = []
for d in dest:
    u = auth.get_user(d) or {}
    if not str(u.get("Email", "")).strip() and not str(u.get("TelegramChatID", "")).strip():
        sin_canal.append(d)
print(f"   destinatarios de una solicitud: {dest}")
print(f"   SIN ningún canal (solo la verán entrando a la app): {sin_canal}")
if sin_canal:
    h(False, "Hay administradores que NO recibirán el aviso de una solicitud",
      f"{', '.join(sin_canal)} — sin email ni Telegram. La bandeja los muestra igual, "
      "pero el aviso no sale de la app. Es el pendiente de v395.")

# ── 6 · Limitaciones del modelo (no son fallos: son alcance) ────
paso("6. Límites del modelo, para que consten")
print(f"   HORAS_DIA = {AU.HORAS_DIA} h fijas para todos")
h(False, "Un día de ausencia vale 8 h para TODO EL MUNDO",
  "No hay jornada por persona en el modelo, así que alguien a media jornada cobraría "
  "8 h por día de vacaciones. Hoy no afecta (nadie está a media jornada), pero el "
  "número está fijo en el código, no configurado por grupo.")

_d = AU.dias_del_rango(date(2026, 12, 28), date(2027, 1, 3))
print(f"   una ausencia 28/12 → 03/01 tiene {len(_d)} días hábiles")
h(False, "El saldo cuenta por el año en que EMPIEZA la ausencia",
  "Una ausencia a caballo de dos años se descuenta entera del año de inicio "
  "(`dias_usados` filtra por el año de `Desde`).")

# ── 7 · ¿La cancelación avisa a alguien? ────────────────────────
paso("7. Si el campo cancela unas vacaciones ya aprobadas, ¿se entera el admin?")
ui = (RAIZ / "core" / "ausencias_ui.py").read_text(encoding="utf-8")
t7 = ast.parse(ui)
rma = next(n for n in ast.walk(t7) if isinstance(n, ast.FunctionDef)
           and n.name == "render_mis_ausencias")
_c = ast.unparse(rma)
avisa_cancel = "_avisar_admins" in _c.split("Cancelar")[-1] if "Cancelar" in _c else False
print(f"   la cancelación avisa a los administradores: {avisa_cancel}")
if not avisa_cancel:
    h(False, "Cancelar una ausencia aprobada NO avisa al administrador",
      "La solicitud sí le llega; la cancelación no. El tablero se limpia solo (esos "
      "días quedan libres) pero nadie se lo dice — y quizá ya había reorganizado la "
      "cuadrilla contando con esa ausencia.")

# ── Resumen ─────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
graves = [x for x in hallazgos if x[0]]
print(f"{len(hallazgos)} hallazgo(s): {len(graves)} grave(s), "
      f"{len(hallazgos) - len(graves)} anotación(es)")
for g, t, _ in hallazgos:
    print(f"  {'⛔' if g else '· '} {t}")
