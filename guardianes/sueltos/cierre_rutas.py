"""Cierra las dos rutas de v430 sin ejercitar: RECHAZAR y los AVISOS.

⚠️ Los avisos se ejercitan con `notify.notify_user` INTERCEPTADO: mandan correo y
Telegram a personas reales (mismo criterio que `notify_expiring` en v417). Lo que se
comprueba es que se construyen y se dirigen bien, no que lleguen.
"""
import sys
import time
from datetime import timedelta
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

from core import ausencias as AU, timeclock as TC, clock, notify  # noqa: E402
from core import ausencias_ui as AUI                            # noqa: E402

# ⚠️ INTERCEPTADO: nada sale de aquí.
enviados = []
notify.notify_user = lambda u, s, l, link=None: (
    enviados.append({"a": u, "asunto": s, "lineas": l}) or {"email": True})
AUI.notify = notify

creada = None
ok = True


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")


try:
    print("─" * 70 + "\n1. RECHAZAR una solicitud pendiente\n" + "─" * 70)
    d0 = clock.today(GRUPO) + timedelta(days=45)
    while d0.weekday() > 4:
        d0 += timedelta(days=1)
    _ok, creada = AU.solicitar(GRUPO, "campo1", "lksdfkldsf", AU.LIBRE, d0, d0,
                               motivo="AUDITORIA rechazo")
    chk("se crea", _ok)
    AU._invalidate(); time.sleep(1.2)
    chk("nace pendiente", str(AU.get(creada).get("Estado")), AU.PENDIENTE)

    _r = AU.resolver(creada, False, "audit", nota="Esa semana hay entrega")
    chk("se rechaza", _r[0])
    print(f"   mensaje: {_r[1]!r}")
    AU._invalidate(); time.sleep(1.5)
    a = AU.get(creada)
    chk("queda RECHAZADA", str(a.get("Estado")), AU.RECHAZADA)
    chk("con la nota del admin", str(a.get("NotaAdmin")), "Esa semana hay entrega")
    chk("y quién la resolvió", str(a.get("ResueltaPor")), "audit")
    chk("NO se puede volver a resolver", AU.resolver(creada, True, "audit")[0], False)
    chk("una rechazada NO cuenta como ausente",
        [x["ID"] for x in AU.ausentes_en(GRUPO, d0)], [])
    chk("...ni bloquea pedir esas fechas otra vez",
        AU.solapadas(GRUPO, "campo1", d0, d0), [])
    chk("...ni gasta saldo", AU.saldo(GRUPO, "campo1", AU.LIBRE)["usados"], 0.0)

    print("\n" + "─" * 70 + "\n2. Los AVISOS (envío interceptado)\n" + "─" * 70)
    enviados.clear()
    AUI._avisar_admins(GRUPO, "lksdfkldsf", AU.VACACIONES, d0, d0 + timedelta(days=4),
                       AU.TIPOS[AU.VACACIONES])
    print(f"   avisados al PEDIR: {[e['a'] for e in enviados]}")
    chk("se avisa a alguien", len(enviados) > 0)
    if enviados:
        print(f"   asunto: {enviados[0]['asunto']!r}")
        print(f"   cuerpo: {enviados[0]['lineas']}")
        chk("el asunto nombra a la persona y las fechas",
            "lksdfkldsf" in enviados[0]["asunto"] and str(d0) in enviados[0]["asunto"])
        chk("dice que está PENDIENTE de aprobación",
            any("PENDIENTE" in x for x in enviados[0]["lineas"]))

    enviados.clear()
    AUI._avisar_admins(GRUPO, "lksdfkldsf", AU.ENFERMEDAD, d0, d0,
                       AU.TIPOS[AU.ENFERMEDAD])
    chk("una BAJA dice que ya se registró (no que espera aprobación)",
        any("no requiere aprobación" in x for x in enviados[0]["lineas"]))

    enviados.clear()
    AUI._avisar_persona("campo1", AU.get(creada), False, "Esa semana hay entrega")
    print(f"   avisado al RESOLVER: {[e['a'] for e in enviados]}")
    chk("se avisa a quien la pidió", [e["a"] for e in enviados], ["campo1"])
    chk("...diciendo que fue rechazada",
        "rechazada" in enviados[0]["asunto"] or
        any("rechazada" in x for x in enviados[0]["lineas"]))
    chk("...con la nota del admin",
        any("Esa semana hay entrega" in x for x in enviados[0]["lineas"]))

    print("\n" + "─" * 70 + "\n3. Un aviso que falla NO puede tumbar el registro\n" + "─" * 70)
    def _boom(*a, **k):
        raise RuntimeError("SMTP caído")
    notify.notify_user = _boom
    try:
        AUI._avisar_admins(GRUPO, "x", AU.LIBRE, d0, d0, AU.TIPOS[AU.LIBRE])
        chk("con el correo caído, no revienta", True)
    except Exception as e:
        chk("con el correo caído, no revienta", f"REVENTÓ: {e}", True)

except Exception:
    ok = False
    import traceback
    traceback.print_exc()
finally:
    if creada:
        sh = TC._abrir(TC.sheet_id_para(AU.SHEET, GRUPO))
        w = sh.worksheet(AU.SHEET)
        v = w.get_all_values()
        filas = [i for i, f in enumerate(v[1:], start=2) if f and f[0] == creada]
        for r in sorted(filas, reverse=True):
            w.delete_rows(r)
        AU._invalidate()
        print(f"\nLIMPIEZA: -{len(filas)} → {len(w.get_all_values()) - 1} filas")

print("\n" + ("RUTAS CERRADAS OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
