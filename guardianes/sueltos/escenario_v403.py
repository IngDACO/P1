"""Deja montado el caso de v403: una charla hecha HOY en la que tú NO firmaste.

Así el aviso «Firma el Pre-Start» aparece en cuanto fiches en esa obra, y el bloque de
firma sale en la sección Pre-Start. Sin esto no hay forma de ver ese camino.

⚠️ Todos los checks en YES y near miss en NO **a propósito**: un NO o un near miss
abren alarma, y una alarma manda email/Telegram a personas reales (v373/v395).
⚠️ Desde este script no hay credenciales de Drive, así que el PDF no se archiva. La
firma tardía seguirá funcionando: sin DriveID, `firmar` genera el anexo suelto, que es
un camino previsto — pero el merge original+anexo solo se ve con un Pre-Start creado
desde la app.

En seco por defecto; `--apply` escribe.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import clock, prestart as PS, projects as P             # noqa: E402

G = "cliente1"
PID = "PRJ-0009"
APLICAR = "--apply" in sys.argv
HOY = clock.today(G)

prj = P.get_project(PID) or {}
print(f"obra: {PID} · {prj.get('Nombre')}")
print(f"¿ya hay Pre-Start hoy? {PS.hecho_hoy(PID, G)}")

# quién firma: gente del equipo, NUNCA el admin que va a probar
ASISTENTES = [{"name": "Marcus Chen", "initial": "MC", "sig": None},
              {"name": "Tom O'Brien", "initial": "TO", "sig": None}]

data = {
    "proyecto_id": PID, "grupo": G, "fecha": HOY, "hora": "07:00",
    "location": str(prj.get("Ubicacion", "")) or "Level 3",
    "facilitador": "Marcus Chen",
    "activities_notes": "Montaje de rieles nivel 3. SWMS revisado.",
    "near_miss": "NO", "near_miss_desc": "",
    "s1": {k: "YES" for k, _t in PS.CHECKS_S1},
    "s3": {k: "YES" for k, _t in PS.CHECKS_S3},
    "general_notes": "Charla de prueba sembrada para verificar la firma tardía.",
    "attendees": ASISTENTES, "creado_por": "mchen",
}

for u in ("dmoreno", "asfgjjd"):
    print(f"¿le faltaría firmar a {u}? "
          f"{'(se sabrá tras crearlo)' if not PS.hecho_hoy(PID, G) else bool(PS.pendiente_de_firma(PID, G, u))}")

if not APLICAR:
    print("\n(en seco — repetir con --apply)")
    sys.exit(0)

res = PS.submit(data)
print(f"\nsubmit -> ok={res.get('ok')} id={res.get('id')} "
      f"drive={res.get('drive_id') or '(sin Drive desde aquí)'} err={res.get('error')}")
if not res.get("ok"):
    sys.exit(1)

PS._invalidate()
print(f"hecho_hoy ahora: {PS.hecho_hoy(PID, G)}")
for u in ("dmoreno", "asfgjjd", "Marcus Chen"):
    p = PS.pendiente_de_firma(PID, G, u)
    print(f"  a {u:<14} {'LE FALTA firmar → ' + str(p.get('id')) if p else 'no le falta (ya consta)'}")
