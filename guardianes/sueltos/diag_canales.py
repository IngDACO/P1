"""¿Sigue habiendo gestores a los que una alarma no les llega? (pendiente de v395)

SOLO LECTURA. Comprueba el estado REAL, no lo que decia la nota.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import admin_digest as D                                # noqa: E402
from core import alerts as AL                                     # noqa: E402
from core import auth                                             # noqa: E402

G = "cliente1"
dest = AL._admins_and_owners(G)
print(f"== destinatarios de una alarma de {G}: {len(dest)} ==\n")
for u in dest:
    d = auth.get_user(u) or {}
    em = str(d.get("Email", "")).strip()
    tg = str(d.get("TelegramChatID", "")).strip()
    act = str(d.get("Activo", "")).strip()
    llega = bool(em) or bool(tg)
    print(f"   {'LLEGA ' if llega else 'NO LE LLEGA'}  {u:<12} rol={d.get('Rol','?'):<14} "
          f"activo={act:<3} email={'si' if em else 'NO':<3} telegram={'si' if tg else 'NO'}")

sin = D.group_digest(G).get("avisos_sin_canal", [])
print(f"\n   el digest los cuenta asi: {sin}")
print(f"   -> {'PENDIENTE ABIERTO' if sin else 'CERRADO: a todos les llega'}")
