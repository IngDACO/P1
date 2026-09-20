"""Ejercita `credentials.notify_expiring` SIN que le llegue nada a nadie.

Se intercepta `notify.notify_user` (el unico punto de salida) y se le hace devolver
EXITO, para que corra tambien el `batch_update` de `UltimoAviso` que v323 escribio y
que nunca se habia ejecutado (el deduplicado de 25 dias siempre lo suprimia).

⚠️ Eso ESCRIBE en la hoja: se guarda el `UltimoAviso` de cada fila antes y se
restaura despues, exactamente. Dejarlo puesto suprimiria el aviso REAL 25 dias.
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os
os.chdir(RAIZ)

import streamlit as st
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "avisos", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "avisos"}

from core import credentials as C, notify

ok = True
enviados_a = []


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def _foto():
    """{ID: UltimoAviso} tal cual está ahora."""
    return {str(r.get("ID")): str(r.get("UltimoAviso", "")) for r in C._records()}


# ── 1. Foto ──────────────────────────────────────────────────────
antes = _foto()
print(f"credenciales: {len(antes)}")
_venc = [(r.get("ID"), r.get("Usuario"), r.get("Tipo"),
          C.dias_para(r.get("Vencimiento")))
         for r in C._records() if str(r.get("Grupo")) == GRUPO]
_avisables = [x for x in _venc if x[3] is not None and x[3] <= 30]
print(f"por vencer/vencidas (<=30 d): {_avisables}")
print(f"UltimoAviso actual: { {k: v for k, v in antes.items() if v} }\n")

# ── 1b. Vaciar el sello para poder ejercitarlo ──────────────────
# ⚠️ Las 4 avisables tienen `UltimoAviso` de hace 4 y 19 días, así que el dedup de 25
# las suprime — CORRECTO, pero entonces no se ejercita nada. Se vacía el sello (la
# restauración del final lo devuelve exacto, y ya está probada).
def _sello(valores: dict):
    import gspread, toml
    from google.oauth2.service_account import Credentials
    from core import timeclock as T
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    ws = gc.open_by_key(T.sheet_id_para("Credenciales", GRUPO)).worksheet("Credenciales")
    v = ws.get_all_values(); cab = v[0]
    ci, cu = cab.index("ID"), cab.index("UltimoAviso")
    col = chr(65 + cu)
    lote = [{"range": f"{col}{n}", "values": [[valores.get(f[ci], "")]]}
            for n, f in enumerate(v[1:], start=2)]
    if lote:
        ws.batch_update(lote, value_input_option="RAW")
    C._invalidate(); time.sleep(1.5)

print("vaciando UltimoAviso para poder ejercitar...")
_sello({})
_s = {k: v for k, v in _foto().items() if v}
print("   sellos ahora:", _s or "ninguno")

# ── 2. Interceptar el envío ─────────────────────────────────────
_orig = notify.notify_user


def _fake(destinatario, subject, lines, **kw):
    enviados_a.append((destinatario, subject))
    return {"email": True, "telegram": False}      # ← simula que SÍ salió


notify.notify_user = _fake
try:
    n = C.notify_expiring(GRUPO)
    print(f"notify_expiring devolvió: {n} aviso(s)\n")
    print("destinatarios que HABRÍA usado (interceptados, nadie recibió nada):")
    for d, s in enviados_a:
        print(f"   → {d:<12} {s}")
    chk("avisó de las credenciales por vencer", n, len(_avisables))
    chk("...a alguien", len(enviados_a) > 0)
    # los destinatarios son admin/propietario del grupo + el dueño
    _dest = {d for d, _ in enviados_a}
    chk("incluye al dueño de la credencial",
        any(u in _dest for _, u, _, _ in _avisables))

    # ── 3. El batch_update de v323 corrió de verdad ─────────────
    C._invalidate(); time.sleep(1.5)
    tras = _foto()
    _sellados = [k for k in tras if tras[k] != antes.get(k, "")]
    print(f"\nfilas selladas con UltimoAviso: {_sellados}")
    chk("v323: el batch_update SÍ escribió el sello", len(_sellados), n)

    # ── 4. El deduplicado de 25 días ────────────────────────────
    enviados_a.clear()
    n2 = C.notify_expiring(GRUPO)
    chk("un segundo aviso el mismo día se SUPRIME (dedup 25 d)", n2, 0)
    chk("...y no se manda nada", len(enviados_a), 0)
finally:
    notify.notify_user = _orig
    # ── Restaurar el UltimoAviso EXACTO ──────────────────────────
    print("\n== restaurando UltimoAviso ==")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    from core import timeclock as T
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    ws = gc.open_by_key(T.sheet_id_para("Credenciales", GRUPO)).worksheet("Credenciales")
    v = ws.get_all_values()
    cab = v[0]
    ci, cu = cab.index("ID"), cab.index("UltimoAviso")
    col = chr(65 + cu)
    batch = []
    for n_, f in enumerate(v[1:], start=2):
        prev = antes.get(f[ci], "")
        actual = f[cu] if cu < len(f) else ""
        if actual != prev:
            batch.append({"range": f"{col}{n_}", "values": [[prev]]})
    if batch:
        ws.batch_update(batch, value_input_option="RAW")
    print(f"   {len(batch)} celda(s) devueltas a su valor original")
    C._invalidate(); time.sleep(1.2)
    final = _foto()
    igual = final == antes
    print(f"   {'OK  ' if igual else 'FALLO'} UltimoAviso idéntico al de antes: {igual}")
    ok = ok and igual

print("\n" + ("AVISOS EJERCITADOS OK — nadie recibió nada" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
