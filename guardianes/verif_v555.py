# -*- coding: utf-8 -*-
"""v555 · ABSENCES (BANDEJA DEL ADMIN), PROBADA ACCIÓN POR ACCIÓN.

Recorrido en producción (09/10/2026) con 3 solicitudes de prueba. Lo arreglado («Dale»):
  1. ⚠️ Tras «Reject», la tarjeta seguía en pantalla —atenuada, con sus botones— aunque ya
     no se pintara: Streamlit 1.64 + tarjetas con clave + una acción LENTA (hoja + aviso)
     dentro de la tarjeta. Reproducido en una mini-app. → ACCIÓN DIFERIDA: el botón solo
     apunta y relanza; la acción se ejecuta antes de pintar la lista.
  2. ⚠️ La baja por enfermedad nace aprobada y «el admin la confirma después», pero la
     bandeja solo enseñaba lo pendiente → sección «Sick leave recorded».
  3. ⚠️ El admin no podía deshacer nada aprobado → «Cancel» (con confirmación) en lo
     aprobado: libera el tablero y avisa a la persona.
  4. El aviso a la persona decía «aprobada / rechazada» en un correo en inglés.
  5. Lo pendiente, de lo más próximo a lo más lejano (lo urgente salía el último).
  6. Fechas dd/mm/aaaa, y un solo día sin «→».
  7. Las 3 tarjetas, activas: cada una abre su lista.
  8. El saldo dice cómo queda TRAS la solicitud, y «se pasa del saldo» mira eso.
  + aislamiento: la acción busca la ausencia SOLO en el grupo (`AU.get` es global).

AppTest con datos inventados; ninguna hoja se toca (resolver/cancelar/roster/avisos
sustituidos y apuntados). «Hoy» = viernes 09/10/2026.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


print("0. Estático: los botones de las tarjetas solo APUNTAN (el fantasma no lo ve AppTest)")
# ⚠️ El fantasma lo pinta el NAVEGADOR: con la acción otra vez dentro de la tarjeta, el
# recorrido de AppTest seguiría verde (el servidor ya no la pinta). Por eso el principio
# se afirma sobre el código: ni la tarjeta ni la fila hacen nada lento, y `_ejecutar`
# solo se llama desde la acción diferida, antes de pintar la lista.
import ast                                                          # noqa: E402
import io                                                           # noqa: E402
_src = io.open(os.path.join("core", "ausencias_ui.py"), encoding="utf-8").read()
_fns = {n.name: n for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.FunctionDef)}
_LENTO = {"resolver", "cancelar", "aplicar_al_roster", "_ejecutar", "notify_user",
          "_avisar_persona", "_avisar_persona_cancelada"}
for _f in ("_tarjeta_pendiente", "_fila_con_cancelar", "_kpis_bandeja", "render_bandeja"):
    _n = _fns.get(_f)
    _ll = sorted({(c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", ""))
                  for c in ast.walk(_n) if isinstance(c, ast.Call)} & _LENTO) if _n else ["(no existe)"]
    chk("⚠️ `%s` no ejecuta nada lento (solo apunta)" % _f, not _ll, _ll)
_quien_llama = sorted(f for f, n in _fns.items()
                      if any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_ejecutar"
                             for c in ast.walk(n)))
chk("`_ejecutar` solo se llama desde `_accion_pendiente`", _quien_llama == ["_accion_pendiente"],
    _quien_llama)
_rb = ast.unparse(_fns["render_bandeja"]) if "render_bandeja" in _fns else ""
chk("…y la acción se ejecuta ANTES de pintar la lista",
    0 <= _rb.find("_accion_pendiente(") < _rb.find("_tarjeta_pendiente(") if _rb else False)

from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import datetime as dt
import streamlit as st
from core import ausencias as AU, ausencias_ui as AUI, clock, notify

HOY = dt.date(2026, 10, 9)
if not hasattr(clock, "_v555_today"):
    clock._v555_today = clock.today
clock.today = lambda *a, **k: HOY
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})

def _r(i, g, u, n, tipo, d0, d1, dias, est):
    return {"ID": i, "Group": g, "User": u, "Name": n, "Type": tipo, "From": d0, "To": d1,
            "Days": str(dias), "Reason": "", "Status": est, "AdminNote": ""}
if "_RECS" not in st.session_state:
    st.session_state["_RECS"] = [
        _r("AUS-1", "G", "ana", "Ana", AU.VACACIONES, "2026-10-19", "2026-10-20", 2, AU.PENDIENTE),
        _r("AUS-2", "G", "beto", "Beto", AU.LIBRE, "2026-10-22", "2026-10-22", 1, AU.PENDIENTE),
        _r("AUS-3", "G", "carl", "Carl", AU.VACACIONES, "2026-10-13", "2026-10-14", 2, AU.PENDIENTE),
        _r("AUS-4", "G", "dani", "Dani", AU.ENFERMEDAD, "2026-10-07", "2026-10-08", 2, AU.APROBADA),
        _r("AUS-5", "G", "eva", "Eva", AU.VACACIONES, "2026-10-12", "2026-10-12", 1, AU.APROBADA),
        _r("AUS-6", "OTRA", "zed", "Zed", AU.VACACIONES, "2026-10-15", "2026-10-15", 1, AU.PENDIENTE),
        _r("AUS-7", "G", "ana", "Ana", AU.VACACIONES, "2026-10-09", "2026-10-09", 1, AU.APROBADA),
        _r("AUS-8", "G", "fede", "Fede", AU.VACACIONES, "2026-11-02", "2026-12-04", 25, AU.PENDIENTE),
    ]
    st.session_state["_LOG"] = []
RECS, LOG = st.session_state["_RECS"], st.session_state["_LOG"]
AU.is_configured = lambda: True
AU._records = lambda: RECS
def _resolver(aid, aprobar, quien, nota=""):
    LOG.append(("resolver", aid, aprobar, nota))
    for r in RECS:
        if r["ID"] == aid:
            r["Status"] = AU.APROBADA if aprobar else AU.RECHAZADA
    return True, ("Absence approved." if aprobar else "Request rejected.")
def _cancelar(aid, quien):
    LOG.append(("cancelar", aid))
    for r in RECS:
        if r["ID"] == aid:
            r["Status"] = AU.CANCELADA
    return True, "Absence cancelled."
AU.resolver, AU.cancelar = _resolver, _cancelar
AU.aplicar_al_roster = lambda a, quitar=False: (LOG.append(("roster", a.get("ID"), quitar)) or (True, 2))
AU.choques = lambda g, u, d0, d1: ([{"fecha": dt.date(2026, 10, 13), "dia": "mar", "asig": "PRJ-1",
                                     "etiqueta": "Torre", "proyecto_id": "PRJ-1"}] if u == "carl" else [])
AU.sustitutos = lambda *a, **k: [{"nombre": "Gil", "cumple": True}]
notify.notify_user = lambda u, subj, lines: LOG.append(("aviso", u, subj, " ".join(lines)))
AUI.render_bandeja("G")
'''


def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


def log(at):
    return list(at.session_state["_LOG"])


def bloques(at, prefijo):
    """Las claves de los bloques que empiezan por `prefijo`, en el orden en que se pintan."""
    out = []

    def _rec(n):
        for h in getattr(n, "children", {}).values():
            k = getattr(h, "key", None)
            if isinstance(k, str) and k.startswith(prefijo):
                out.append(k)
            _rec(h)
    _rec(at.main)
    return out


def texto(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.caption]
                      + [m.value for m in at.error] + [m.value for m in at.warning])


def flashes(at):
    return list(at.session_state["_flash_cola"]) if "_flash_cola" in at.session_state else []


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])

print("1. Orden, fechas y saldo")
_ord = bloques(at, "auspend_")
chk("⚠️ lo pendiente, del más PRÓXIMO al más lejano (13/10, 19/10, 22/10, 02/11)",
    _ord == ["auspend_AUS-3", "auspend_AUS-1", "auspend_AUS-2", "auspend_AUS-8"], _ord)
chk("la de otra empresa (AUS-6) no sale", "auspend_AUS-6" not in _ord and "Zed" not in texto(at))
_t = texto(at)
chk("fechas dd/mm/aaaa: «13/10/2026 → 14/10/2026»", "13/10/2026 → 14/10/2026" in _t)
chk("un solo día, sin flecha: «22/10/2026 ·»", "22/10/2026 ·" in _t and "22/10/2026 → 22/10/2026" not in _t)
chk("ya no queda la fecha ISO en las tarjetas", "2026-10-19" not in _t)
chk("⚠️ el saldo dice cómo queda: Ana «19 of 20 … → 17 after this request»",
    "They have **19** of 20 days of annual leave this year → **17** after this request." in _t, _t[:400])
chk("⚠️ «se pasa del saldo» mira lo que queda TRAS la solicitud (Fede: 20 − 25)",
    any("→ **-5** after this request" in e.value and "over the balance" in e.value for e in at.error),
    [e.value for e in at.error])
chk("las fechas de «Who could cover it» también en dd/mm/aaaa", "**13/10/2026** · Torre" in _t)

print("\n2. Tarjetas activas")
for k in ("pend", "today", "week"):
    chk("la tarjeta %s es un botón" % k, b(at, "cpxkpi_aus_%s" % k) is not None)
chk("Pending = 4 (sin la de otra empresa)", "\n\n4\n\n" in b(at, "cpxkpi_aus_pend").label,
    b(at, "cpxkpi_aus_pend").label)
b(at, "cpxkpi_aus_today").click()
at.run()
chk("«Away today» abre la lista: Ana (hoy, 09/10/2026)",
    "**Ana** — **Annual leave** · 09/10/2026" in texto(at))
b(at, "cpxkpi_aus_week").click()
at.run()
_t = texto(at)
# ⚠️ La línea de Eva sale TAMBIÉN en el histórico: abierta, 2 veces; cerrada, 1
_EVA = "**Eva** — **Annual leave** · 12/10/2026"
chk("«Next 7 days» abre la suya (Eva, 12/10): la línea sale 2 veces (lista + histórico)",
    _t.count(_EVA) == 2, _t.count(_EVA))
b(at, "cpxkpi_aus_week").click()
at.run()
chk("…y otro toque la cierra (1 vez: solo el histórico)", texto(at).count(_EVA) == 1,
    texto(at).count(_EVA))

print("\n3. Aprobar y rechazar, DIFERIDOS")
at.text_input(key="ausnota_AUS-3").input("PRUEBA nota")
b(at, "ausok_AUS-3").click()
at.run()
_l = log(at)
chk("⚠️ aprobar llama a `resolver` con la nota", ("resolver", "AUS-3", True, "PRUEBA nota") in _l, _l)
chk("…escribe el tablero", ("roster", "AUS-3", False) in _l, _l)
_av = [x for x in _l if x[0] == "aviso" and x[1] == "carl"]
chk("⚠️ el aviso, en inglés: «has been <b>approved</b>»", bool(_av) and "has been <b>approved</b>" in _av[0][3]
    and "aprobada" not in _av[0][3] and _av[0][2].startswith("Absence approved:"), _av)
chk("…con las fechas en dd/mm/aaaa", bool(_av) and "13/10/2026 → 14/10/2026" in _av[0][2], _av)
chk("⚠️ la tarjeta aprobada YA no se pinta en esa pasada (acción antes de la lista)",
    "auspend_AUS-3" not in bloques(at, "auspend_"), bloques(at, "auspend_"))
chk("…y deja su aviso para arriba", any("Absence approved" in m for _t2, m in flashes(at)), flashes(at))
b(at, "ausno_AUS-2").click()
at.run()
_av = [x for x in log(at) if x[0] == "aviso" and x[1] == "beto"]
chk("rechazar: aviso «rejected», en inglés", bool(_av) and "<b>rejected</b>" in _av[0][3]
    and "rechazada" not in _av[0][3], _av)
chk("…y la tarjeta se va", "auspend_AUS-2" not in bloques(at, "auspend_"))

print("\n4. La baja por enfermedad llega al admin, y lo aprobado se puede deshacer")
_t = texto(at)
chk("⚠️ sección «Sick leave recorded» con la baja de Dani",
    "#### :material/sick: Sick leave recorded" in _t and "**Dani** — **Sick leave**" in _t)
chk("…con «Cancel»", b(at, "auscx_baja_AUS-4") is not None)
b(at, "auscx_baja_AUS-4").click()
at.run()
chk("«Cancel» primero PREGUNTA (no cancela)", ("cancelar", "AUS-4") not in log(at)
    and any("Cancel this absence?" in w.value for w in at.warning))
b(at, "auscxno_baja_AUS-4").click()
at.run()
chk("«Keep it» no cancela y cierra la pregunta", ("cancelar", "AUS-4") not in log(at)
    and not any("Cancel this absence?" in w.value for w in at.warning))
b(at, "auscx_baja_AUS-4").click()
at.run()
b(at, "auscxok_baja_AUS-4").click()
at.run()
_l = log(at)
chk("⚠️ «Yes, cancel it» cancela y LIBERA el tablero", ("cancelar", "AUS-4") in _l
    and ("roster", "AUS-4", True) in _l, _l[-4:])
_av = [x for x in _l if x[0] == "aviso" and x[1] == "dani"]
chk("…y avisa a la persona («cancelled by the administrator»)", bool(_av)
    and "cancelled</b> by the administrator" in _av[0][3], _av)
chk("…y la baja sale de la sección", b(at, "auscx_baja_AUS-4") is None)

print("\n5. Histórico")
chk("el histórico tiene clave (lleva controles: trampa 35)", "exp_aus_hist" in bloques(at, "exp_aus"))
chk("«Cancel» solo en lo APROBADO (Eva sí; Fede, pendiente, no)",
    b(at, "auscx_hist_AUS-5") is not None and b(at, "auscx_hist_AUS-8") is None)

print("\n6. Aislamiento")
_n = len([x for x in log(at) if x[0] == "resolver"])
at.session_state["_aus_accion"] = {"aid": "AUS-6", "aprobar": True}
at.run()
chk("⚠️ una acción apuntada a la de OTRA empresa no llega a `resolver`",
    len([x for x in log(at) if x[0] == "resolver"]) == _n, log(at)[-2:])
chk("…y se dice", any("Request not found" in m for _t2, m in flashes(at)), flashes(at))
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
