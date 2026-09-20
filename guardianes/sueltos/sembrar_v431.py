"""Siembra UNA solicitud pendiente para poder ver la bandeja del admin con contenido.

Verificar una bandeja vacía es el paso en vacío (trampa nº1): lo que hay que ver es la
tarjeta con los choques y los sustitutos. Se elige a quien MÁS obras tenga asignadas
esos días, para que la pantalla enseñe el caso rico. Se borra después.
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os                                                       # noqa: E402
os.chdir(RAIZ)

import streamlit as st                                          # noqa: E402
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "semb", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "semb"}

from core import ausencias as AU, auth, clock                   # noqa: E402

hoy = clock.today(GRUPO)
d0 = hoy + timedelta(days=(7 - hoy.weekday()) % 7 or 7)         # próximo lunes
d1 = d0 + timedelta(days=2)                                     # lun→mié

cands = [u for u in auth.list_users(GRUPO)
         if str(u.get("Rol", "")) == "campo"
         and str(u.get("Activo", "SI")).upper() != "NO"]
mejor, n_max = None, -1
for u in cands:
    ch = AU.choques(GRUPO, str(u.get("Usuario")), d0, d1)
    print(f"   {str(u.get('Usuario')):12} {len(ch)} choque(s): "
          f"{sorted({c['etiqueta'] for c in ch})}")
    if len(ch) > n_max:
        mejor, n_max = u, len(ch)

usr, nom = str(mejor.get("Usuario")), str(mejor.get("Nombre") or mejor.get("Usuario"))
print(f"\nElegido: {usr} ({nom}) con {n_max} choque(s) · {d0} → {d1}")

ok, aid = AU.solicitar(GRUPO, usr, nom, AU.VACACIONES, d0, d1,
                       motivo="Boda de mi hermana")
print(f"solicitar → {ok} {aid}")
if ok:
    print(f"\nSEMBRADO: {aid}   (borrar después con limpiar_v431.py)")
    for c in AU.choques(GRUPO, usr, d0, d1):
        subs = AU.sustitutos(GRUPO, c["fecha"], c.get("proyecto_id"), excluir=usr)
        print(f"   {c['fecha']} {c['etiqueta']:35} → cubren: "
              f"{[s['nombre'] for s in subs if s['cumple']][:3]}")
Path(__file__).with_name("_aus_sembrada.txt").write_text(str(aid), encoding="utf-8")
