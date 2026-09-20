"""Cierra el fichaje olvidado de `campo1`, abierto desde el 21/08.

El usuario: «ponle cualquier hora, ahora no es importante» (es la empresa simulada).
Se elige **15:30 del 21/08**, una hora de fin de jornada plausible, y se DICE cuál —
inventar una hora es aceptable aquí sólo porque el dato es de prueba; en producción la
pone la persona (v164: cerrar con «ahora» registra horas que nadie trabajó).
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import timeclock as T                                   # noqa: E402

G = "cliente1"
abiertas = [r for r in T._cached_records()
            if str(r.get("Grupo", "")).strip().lower() == G
            and not str(r.get("Clock Out", "")).strip()]
print(f"{len(abiertas)} sesiones abiertas:")
for r in abiertas:
    print(f"   Usuario={r.get('Usuario')!r} Nombre={r.get('Nombre')!r} "
          f"Tipo={r.get('Tipo')!r} Proyecto={r.get('Proyecto')!r} In={r.get('Clock In')!r}")

if "--apply" not in sys.argv:
    print("\n(en seco — repetir con --apply)")
    sys.exit(0)

HORA = "2026-08-21 15:30:00"
for r in abiertas:
    nom = str(r.get("Nombre", ""))
    usr = str(r.get("Usuario", ""))
    tipo = str(r.get("Tipo", "")) or T.TIPO_PROYECTO
    ok, msg = T.clock_out(nom, G, tipo=tipo, usuario=usr, out_ts=HORA)
    print(f"   clock_out({nom!r}, tipo={tipo!r}) -> {ok} · {msg}")

T._invalidate_records()
quedan = [r for r in T._cached_records()
          if str(r.get("Grupo", "")).strip().lower() == G
          and not str(r.get("Clock Out", "")).strip()]
print(f"\nsesiones abiertas después: {len(quedan)}")
