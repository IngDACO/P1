"""¿A quién NO le llegan las alarmas? — estado real de los canales de aviso.

`alerts.report_problem` avisa a los admins del grupo y a los propietarios. Si una
cuenta no tiene email ni Telegram, la alarma se escribe en la hoja pero **no llega
a nadie**: se ve solo si esa persona entra a mirar. Con el check en NO abriendo
alarma (v373), eso pasa a importar más.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "", "rol": "propietario"}

from core import auth                                            # noqa: E402
from core import notify                                          # noqa: E402

print("== Canales configurados en el ENTORNO ==")
print(f"   Telegram (bot en secrets): {notify.telegram_configured()}")
print("   ⚠️ medido en LOCAL — el Cloud tiene sus propios secrets (lección v368)")

print("\n== Quién recibe las alarmas (admins y propietarios) ==")
print(f"   {'cuenta':<14}{'rol':<15}{'grupo':<14}{'email':<8}{'telegram':<10}llega?")
sin_canal = []
for u in auth.list_users():
    rol = str(u.get("Rol", ""))
    if rol not in ("propietario", "administrador"):
        continue
    em = bool(str(u.get("Email", "")).strip())
    tg = bool(str(u.get("TelegramChatID", "")).strip())
    activo = str(u.get("Activo", "SI")).strip().upper() in auth._ACTIVE_OK
    llega = "SÍ" if (em or tg) else "NO ⚠️"
    if not (em or tg) and activo:
        sin_canal.append(str(u.get("Usuario")))
    print(f"   {str(u.get('Usuario')):<14}{rol:<15}"
          f"{str(u.get('Grupo', '')) or '(sin grupo)':<14}"
          f"{'sí' if em else '—':<8}{'sí' if tg else '—':<10}{llega}"
          f"{'' if activo else '  (inactivo)'}")

print("\n== Veredicto ==")
if sin_canal:
    print(f"   ⚠️ {len(sin_canal)} cuenta(s) ACTIVAS sin ningún canal: "
          f"{', '.join(sin_canal)}")
    print("      Una alarma dirigida a ellas queda escrita en la hoja y no")
    print("      llega a ninguna parte: solo se ve entrando a la app.")
else:
    print("   ✓ todas las cuentas que reciben alarmas tienen al menos un canal")

# ¿A quién avisaría realmente una alarma del grupo de la demo?
print("\n== Simulación: destinatarios de una alarma de 'cliente1' ==")
try:
    from core import alerts
    dest = alerts._admins_and_owners("cliente1")
    print(f"   {len(dest)} destinatario(s):")
    for d in dest:
        u = d if isinstance(d, str) else str(d.get("Usuario", d))
        fila = next((x for x in auth.list_users() if str(x.get("Usuario")) == u), {})
        _em = bool(str(fila.get("Email", "")).strip())
        _tg = bool(str(fila.get("TelegramChatID", "")).strip())
        print(f"      {u:<14} email:{'sí' if _em else '—':<4} "
              f"telegram:{'sí' if _tg else '—':<4} "
              f"{'→ le llega' if (_em or _tg) else '→ ⚠️ NO le llega'}")
except Exception as e:
    print(f"   (no se pudo simular: {type(e).__name__}: {e})")
