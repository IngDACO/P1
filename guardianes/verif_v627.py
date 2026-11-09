# -*- coding: utf-8 -*-
"""v627 · RECORRIDO DEL CAMPO: SELF-SERVICE (01/11/2026, «Ok dale con todo incluido lo recomendado»).

  MY ABSENCES
  (1) ⚠️ se podían cancelar días ya disfrutados → su dueño, solo lo pendiente y lo que no ha empezado;
  (2) ⚠️ un toque cancelaba unas vacaciones aprobadas, con correo a todos → pide confirmación;
  (3) ⚠️ sin saldo no dejaba registrar una baja → se registra siempre y la oficina decide cómo se paga;
  (4) ⚠️ lo pendiente no contaba: con 20 días se podían pedir 20 y otros 20 → cuenta, también en el motor;
  (5) el formulario no se vaciaba de verdad (trampa 31) → por generación;
  (6) no decía cuántos días gasta → contador en vivo; (7) título doble, ISO, cifras pasivas, logins…
  MY CREDENTIALS
  (8) las cifras empujaban la tabla a 834 px → 2×2 activas y tarjetas; (9) «expiring» no decía cuándo,
  ISO; (10) los documentos se bajaban en cada pasada → diferidos.
  MY PAYSLIPS
  (11) ⚠️ todos los PDF en cada pasada (411 ms cada uno, medido) → diferidos, y las 10 últimas; (12) título
  doble, fecha de pago, sin el error crudo.
⚠️ Lo aprendido en v620: nada de estado preparado a mano. Sin red ni hoja real; los avisos, sustituidos.
"""
import datetime
import inspect
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
from core import ausencias as AU, clock                           # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def _btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def _todo(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success",
                                              "header", "toast") for x in getattr(a, k, []))


def _src(rel):
    return io.open(os.path.join(RAIZ, "core", rel), encoding="utf-8").read()


HOY = datetime.date(2026, 11, 4)            # un miércoles
clock.today = lambda *a: HOY
clock.now = lambda *a: datetime.datetime(2026, 11, 4, 7, 0)
AU.periodo_saldo = lambda g, u, ref=None: {"desde": datetime.date(2026, 1, 1), "hasta": datetime.date(2026, 12, 31),
                                           "origen": "natural", "ingreso": None}


def fila(aid, tipo, d0, d1, dias, estado, **k):
    return {"ID": aid, "Group": "cliente1", "User": k.pop("User", "installer"), "Name": "installer CI 1", "Type": tipo,
            "From": d0, "To": d1, "Days": str(dias), "Reason": k.pop("Reason", ""), "Status": estado,
            "ResolvedBy": k.pop("ResolvedBy", ""), "ResolvedDate": "", "AdminNote": k.pop("AdminNote", ""),
            "CreatedBy": "installer", "Created": "2026-10-01 07:00", "IncludesWeekends": "NO"}


class Hoja:
    def __init__(self, f):
        self.f, self.altas, self.cambios = f, [], []

    def get_all_records(self, **k):
        return self.f

    def append_row(self, r, **k):
        self.altas.append(dict(zip(AU.HEADERS, r)))
        self.f.append(self.altas[-1])

    def batch_update(self, b, **k):
        self.cambios.append(b)


def monta(f):
    h = Hoja(f)
    AU._ws = lambda: h
    AU._records = lambda: f
    AU._invalidate = lambda: None
    AU._next_id = lambda recs: "AUS-0099"
    return h


V, E, L, P_, A_, R_, C_ = AU.VACACIONES, AU.ENFERMEDAD, AU.LIBRE, AU.PENDIENTE, AU.APROBADA, AU.RECHAZADA, AU.CANCELADA

sec("1. ⚠️ El motor")
monta([fila("A1", V, "2026-03-02", "2026-03-06", 5, A_), fila("A2", V, "2026-12-07", "2026-12-11", 5, P_),
       fila("A3", V, "2026-04-06", "2026-04-07", 2, R_)])
s = AU.saldo("cliente1", "installer", V)
chk("el saldo: 20 · usados 5 · quedan 15, como antes", (s["asignados"], s["usados"], s["restantes"]) == (20, 5, 15), s)
chk("⚠️ lo pendiente se ve, y baja lo disponible", s["pendientes"] == 5 and s["disponibles"] == 10, s)
chk("`exceso`: lo que pasa de lo disponible", AU.exceso("cliente1", "installer", V, 12) == 2
    and AU.exceso("cliente1", "installer", V, 10) == 0)
chk("…lo que no tiene tope, nunca excede", AU.exceso("cliente1", "installer", L, 300) == 0)
h = monta([fila("A2", V, "2026-06-01", "2026-06-26", 20, P_)])
ok, res = AU.solicitar("cliente1", "installer", "i", V, "2026-08-03", "2026-08-03")
chk("⚠️ con 20 días pedidos y esperando, otro día NO: también en el motor", not ok and not h.altas
    and "waiting for approval" in res, res)
h = monta([fila("A1", E, "2026-02-02", "2026-02-13", 10, A_)])
ok, res = AU.solicitar("cliente1", "installer", "i", E, "2026-11-04", "2026-11-05")
chk("⚠️⚠️ sin saldo, la baja se registra igual (aprobada: no se pide permiso para estar enfermo)",
    ok and h.altas and h.altas[0]["Status"] == A_, res)
# v633 · Ya no se escribe: «Over the balance by 2» se desincronizaba al cancelar otra baja (verif_v633)
chk("⚠️ …y nace sin decidir: lo que pasa del saldo se deriva, y lo decide la oficina",
    h.altas and h.altas[0]["AdminNote"] == "" and h.altas[0]["OverBalancePay"] == "", h.altas[:1])
h = monta([])
ok, res = AU.solicitar("cliente1", "installer", "i", E, "2026-11-04", "2026-11-04")
chk("con saldo, sin nota", ok and h.altas[0]["AdminNote"] == "", h.altas[:1])
h = monta([fila("A1", V, "2026-11-09", "2026-11-10", 2, P_)])
ok, res = AU.solicitar("cliente1", "installer", "i", V, "2026-11-10", "2026-11-11")
chk("⚠️ el choque, con fechas DD/MM/YYYY", not ok and "09/11/2026 → 10/11/2026" in res and "pending" in res, res)
_d = lambda n: (HOY + datetime.timedelta(days=n)).isoformat()   # noqa: E731
chk("su dueño: lo pendiente, siempre, también si ya pasó", AU.cancelable_por_el_campo(fila("x", V, _d(-9), _d(-8), 2, P_)))
chk("…lo aprobado que no ha empezado, sí", AU.cancelable_por_el_campo(fila("x", V, _d(1), _d(2), 2, A_)))
chk("⚠️ …lo aprobado que empieza HOY, no", not AU.cancelable_por_el_campo(fila("x", V, _d(0), _d(2), 2, A_)))
chk("⚠️ …lo aprobado ya disfrutado, no", not AU.cancelable_por_el_campo(fila("x", V, _d(-9), _d(-8), 2, A_)))
chk("…lo cancelado o rechazado, no", not AU.cancelable_por_el_campo(fila("x", V, _d(1), _d(2), 2, C_))
    and not AU.cancelable_por_el_campo(fila("x", V, _d(1), _d(2), 2, R_)))
h = monta([fila("A1", V, _d(-9), _d(-8), 2, A_)])
ok, msg = AU.cancelar("A1", "installer")
chk("⚠️ el motor niega al campo cancelar lo ya disfrutado, aunque la pantalla se equivoque",
    not ok and "already started" in msg and not h.cambios, msg)
ok, msg = AU.cancelar("A1", "Admin2", gestor=True)
chk("…la oficina sí puede", ok and h.cambios, msg)
_b = inspect.getsource(__import__("core.ausencias_ui", fromlist=["x"])._ejecutar)
chk("⚠️ …y la bandeja se identifica como oficina (si no, dejaría de poder)",
    "AU.cancelar(aid, quien, gestor=True)" in _b)

sec("2. ⚠️ My absences (AppTest, clics reales)")
G = r'''
import datetime
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "installer CI 1", "rol": "field", "grupo": "cliente1"})
from core import ausencias as AU, ausencias_ui as AUI, clock, flash, notify, alerts, auth
_F = st.session_state["_F"]
_L = st.session_state.setdefault("_LOG", [])
class H:
    def get_all_records(self, **k): return _F
    def append_row(self, r, **k):
        _F.append(dict(zip(AU.HEADERS, r))); _L.append(("alta", _F[-1]))
    def batch_update(self, b, **k):
        for x in b:
            _c = "".join(c for c in x["range"] if c.isalpha())
            _n = int("".join(c for c in x["range"] if c.isdigit()))
            _i = 0
            for ch in _c: _i = _i * 26 + ord(ch) - 64
            _F[_n - 2][AU.HEADERS[_i - 1]] = x["values"][0][0]
        _L.append(("cambio", [x["values"][0][0] for x in b]))
AU._ws = lambda: H()
AU._records = lambda: _F
AU._invalidate = lambda: None
AU._next_id = lambda recs: "AUS-%04d" % (len(recs) + 1)
AU.aplicar_al_roster = lambda a, quitar=False: (_L.append(("tablero", a.get("ID"), quitar)) or (True, 1))
AU.get = lambda aid: next((x for x in _F if x["ID"] == aid), {})
notify.notify_user = lambda d, s, l, link=None: (_L.append(("aviso", d, s, list(l))) or {})
alerts._admins_and_owners = lambda g: ["Admin2"]
auth.list_users = lambda *a: [{"User": "dmoreno", "Name": "Diana Moreno", "Group": "cliente1"}, {"User": "installer", "Name": "installer CI 1", "Group": "cliente1"}]
flash.mostrar()
AUI.render_mis_ausencias()
'''


def ap(f):
    a = AppTest.from_string(G, default_timeout=60)
    a.session_state["_F"] = f
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


def log(a, q):
    return [x for x in a.session_state["_LOG"] if x[0] == q]


a = ap([fila("A1", V, "2026-03-02", "2026-03-06", 5, A_), fila("A2", V, "2026-12-07", "2026-12-11", 5, P_)])
_md = [str(x.value) for x in a.markdown]
chk("⚠️ sin título propio (salía dos veces, con la raya en medio)", not [x for x in _md if x.startswith("## ")], _md[:3])
_k = {b.key: str(b.label) for b in a.button if str(b.key or "").startswith("cpxkpi_mia_")}
chk("⚠️ las cifras son BOTONES (eran HTML): una por tipo", sorted(_k) == sorted("cpxkpi_mia_" + x for x in AU.TIPOS), _k)
chk("⚠️ la cifra es lo que aún se puede pedir, y lo pendiente se ve",
    "\n\n10\n\n" in _k.get("cpxkpi_mia_" + V, "") and "of 20 · used 5 · 5 pending" in _k.get("cpxkpi_mia_" + V, ""), _k)
chk("⚠️ el periodo en DD/MM/YYYY (iba en ISO)", "**01/01/2026** → **31/12/2026**" in _todo(a), _todo(a)[:300])
chk("«1 day», no «1 day(s)»", "1 day(s)" not in _todo(a) and "**1 day**" in _todo(a), _todo(a)[:300])
chk("⚠️ cuenta lo que gasta ANTES de enviar", "This takes **1 day** · 9 left after this" in _todo(a), _todo(a))
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 9)).run()
chk("⚠️ en vivo y sin el fin de semana (mié → lun: 4 días)", "This takes **4 days** · 6 left after this" in _todo(a), _todo(a))
a.checkbox(key="aus_findes_0").check().run()
chk("…con el fin de semana marcado, 6", "This takes **6 days** · 4 left after this" in _todo(a), _todo(a))
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 3)).run()
chk("⚠️ el fin antes del inicio: lo dice y no deja enviar",
    "The end date cannot be earlier" in _todo(a) and _btn(a, "aus_enviar").disabled, _todo(a))
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 12, 4)).run()
chk("⚠️ pide más de lo disponible: lo dice y no deja enviar",
    "and you have **10** available" in _todo(a) and _btn(a, "aus_enviar").disabled, _todo(a))
a.checkbox(key="aus_findes_0").uncheck().run()
a.date_input(key="aus_desde_0").set_value(datetime.date(2026, 11, 7)).run()
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 8)).run()
chk("solo fin de semana: lo dice y no deja enviar",
    "only covers the weekend" in _todo(a) and _btn(a, "aus_enviar").disabled, _todo(a))

a = ap([])
a.date_input(key="aus_desde_0").set_value(datetime.date(2026, 11, 9)).run()
a.date_input(key="aus_hasta_0").set_value(datetime.date(2026, 11, 10)).run()
a.text_input(key="aus_motivo_0").input("Boda").run()
_btn(a, "aus_enviar").click()
a.run()
chk("sin excepción al enviar", not a.exception, [e.value for e in a.exception][:1])
_al = log(a, "alta")
chk("se registra, pendiente, con su motivo", len(_al) == 1 and _al[0][1]["Status"] == P_ and _al[0][1]["Reason"] == "Boda", _al)
_av = log(a, "aviso")
chk("⚠️ el aviso a la oficina, con fechas DD/MM/YYYY", _av and "09/11/2026" in _av[0][2] and "2026-11" not in str(_av[0]), _av[:1])
chk("…lo dice", "Request sent (AUS-0001)" in _todo(a), _todo(a)[:200])
chk("⚠️ el formulario NACE vacío: los campos son otros (trampa 31: vaciar no llega al navegador)",
    a.text_input(key="aus_motivo_1").value == "" and a.date_input(key="aus_desde_1").value == HOY
    and not a.checkbox(key="aus_findes_1").value, [x.key for x in a.text_input])
a.date_input(key="aus_desde_1").set_value(datetime.date(2026, 11, 16)).run()
a.date_input(key="aus_hasta_1").set_value(datetime.date(2026, 11, 16)).run()
_btn(a, "aus_enviar").click()
a.run()
chk("⚠️ …y la segunda no arrastra el motivo de la primera", not a.exception and len(log(a, "alta")) == 2
    and log(a, "alta")[-1][1]["Reason"] == "", log(a, "alta")[-1])

a = ap([fila("A1", E, "2026-02-02", "2026-02-13", 10, A_)])
a.selectbox(key="aus_tipo").select(E).run()
chk("sin saldo de baja, ningún «no puedes»", "You have no days left" not in _todo(a), _todo(a))
chk("⚠️ dice que pasa del saldo y que se registra igual", "1 day** over your sick leave balance" in _todo(a)
    and "recorded anyway" in _todo(a), _todo(a))
chk("⚠️ …y DEJA enviar", not _btn(a, "aus_enviar").disabled)
_btn(a, "aus_enviar").click()
a.run()
_al = log(a, "alta")
chk("⚠️⚠️ queda registrada, aprobada", _al and _al[0][1]["Status"] == A_, _al)
chk("…va al tablero", log(a, "tablero") == [("tablero", "AUS-0002", False)], log(a, "tablero"))
chk("⚠️ …y la oficina sabe que pasa del saldo", log(a, "aviso") and "1 day(s) over the balance" in str(log(a, "aviso")[0]), log(a, "aviso"))

a = ap([fila("A1", V, _d(5), _d(6), 2, A_), fila("A2", V, _d(9), _d(9), 1, P_),
        fila("A3", V, _d(-9), _d(-8), 2, A_, Reason="*Boda*", ResolvedBy="dmoreno", AdminNote="Ok _ya_"),
        fila("A4", E, _d(-1), _d(-1), 1, A_, ResolvedBy="(automatic)"),
        fila("A5", V, _d(20), _d(20), 1, C_, ResolvedBy="installer")])
_t = _todo(a)
chk("⚠️ quien resolvió, por su NOMBRE (salía «dmoreno»)", "resolved by Diana Moreno" in _t and "dmoreno" not in _t, _t)
# ⚠️ «automatic», sin paréntesis: el texto va escapado y con ellos esta red no veía nada (lo destapó la rotura)
chk("«(automatic)» no es nadie, y lo que cancela uno mismo tampoco", "automatic" not in _t and "resolved by installer" not in _t, _t)
chk("⚠️ «Note:» en inglés (decía «nota:»), y el texto tal cual", "Note: Ok \\_ya\\_" in _t and "nota:" not in _t
    and "\\*Boda\\*" in _t, _t)
chk("⚠️ lo aprobado que no ha empezado y lo pendiente se pueden cancelar",
    _btn(a, "auscan_A1") is not None and _btn(a, "auscan_A2") is not None)
chk("⚠️ lo ya disfrutado NO, y lo dice", _btn(a, "auscan_A3") is None and _btn(a, "auscan_A4") is None
    and _t.count("It has already started") == 2, _t)
_btn(a, "auscan_A1").click()
a.run()
chk("⚠️ un toque NO cancela: nada escrito, nadie avisado", not log(a, "cambio") and not log(a, "aviso"))
chk("…pregunta, con lo que pasará", "Its days go back to your balance and the office is told" in _todo(a), _todo(a))
chk("…y solo en ESA", _btn(a, "auscanok_A1") is not None and _btn(a, "auscanok_A2") is None)
_btn(a, "auscanno_A1").click()
a.run()
chk("«Keep it» no toca nada", not log(a, "cambio") and _btn(a, "auscan_A1") is not None and _btn(a, "auscanok_A1") is None)
_btn(a, "auscan_A1").click()
a.run()
_btn(a, "auscanok_A1").click()
a.run()
chk("sin excepción al confirmar", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ al confirmar: cancelada", log(a, "cambio") and log(a, "cambio")[0][1][0] == C_, log(a, "cambio"))
chk("…fuera del tablero", ("tablero", "A1", True) in log(a, "tablero"), log(a, "tablero"))
chk("⚠️ …y avisa, con fechas DD/MM/YYYY", log(a, "aviso") and "2026-" not in str(log(a, "aviso")[0]), log(a, "aviso"))
chk("…y ya no ofrece cancelarla", _btn(a, "auscan_A1") is None and "Absence cancelled." in _todo(a), _todo(a)[:200])
_btn(a, "auscan_A2").click()
a.run()
chk("una pendiente: «Withdraw», sin hablar de la oficina", "Withdraw this request?" in _todo(a), _todo(a))
_btn(a, "auscanok_A2").click()
a.run()
chk("⚠️ retirar una pendiente no molesta a nadie ni toca el tablero",
    len(log(a, "aviso")) == 1 and not [x for x in log(a, "tablero") if x[1] == "A2"], log(a, "tablero"))

a = ap([fila("A1", V, _d(5), _d(6), 2, P_)])
a.session_state["_aus_mia_accion"] = "A9"
a.run()
chk("⚠️ una acción sobre lo que no es suyo no se ejecuta", not log(a, "cambio") and "Request not found" in _todo(a), _todo(a)[:120])
_de_otro = fila("A2", V, _d(5), _d(6), 2, P_, User="otro")
a = ap([_de_otro])
a.session_state["_aus_mia_accion"] = "A2"
a.run()
chk("⚠️ …ni aunque exista: es de otra persona", not log(a, "cambio"), log(a, "cambio"))

_mias = [fila(f"A{i:02d}", V, f"2026-0{i // 10 + 1}-{i % 10 + 10}", f"2026-0{i // 10 + 1}-{i % 10 + 10}", 1, C_) for i in range(12)]
_mias.append(fila("B1", E, "2026-08-03", "2026-08-03", 1, C_))
a = ap(_mias)
_c = _todo(a).count("cancelled")
chk("⚠️ se ven 10, no se corta en silencio", _c == 10 and "Show all (13)" in str(_btn(a, "aus_ver_todas").label), _c)
_btn(a, "aus_ver_todas").click()
a.run()
chk("…y el botón enseña todas", _todo(a).count("cancelled") == 13)
a = ap(_mias)
_btn(a, "cpxkpi_mia_" + E).click()
a.run()
chk("sin excepción al filtrar", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ la cifra filtra: solo las bajas", _todo(a).count("cancelled") == 1 and "Showing only: Sick leave" in _todo(a), _todo(a)[:300])
_btn(a, "aus_filtro_fuera").click()
a.run()
chk("…y se quita", _todo(a).count("cancelled") == 10 and "Showing only" not in _todo(a))
_btn(a, "cpxkpi_mia_" + L).click()
a.run()
chk("un tipo sin solicitudes lo dice", "None of this type." in _todo(a), _todo(a)[-200:])
_btn(a, "cpxkpi_mia_" + L).click()
a.run()
chk("tocar otra vez la misma quita el filtro", "Showing only" not in _todo(a))
_s = _src("ausencias_ui.py")
chk("⚠️ la cifra baja a la lista (bloque que envuelve el título, verif_v585)",
    'with st.container(key="cpx_aus_lista"):' in _s and '_PU._bajar_a("cpx_aus_lista", "_bajar_cpx_aus_lista", bloque="start")' in _s
    and 'st.session_state["_bajar_cpx_aus_lista"] = True' in _s)
chk("⚠️ sin `st.form`: dentro de un formulario no reacciona", 'with st.form("aus_form"' not in _s)
chk("las fechas, de dos en dos también en el móvil", 'T.por_fila("cpx_aus_fechas", 2)' in _s)

sec("3. ⚠️ My credentials")
GC = r'''
import datetime
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "i", "rol": "field", "grupo": "cliente1"})
from core import auth_ui as AI, credentials as C, drive_store as DS, clock
clock.today = lambda *a: datetime.date(2026, 11, 4)
_L = st.session_state.setdefault("_LOG", [])
C.is_configured = lambda: True
C.list_for = lambda u: st.session_state["_CR"]
DS.download = lambda did: (_L.append(did) or b"x")
if st.session_state.get("_ED"):
    AI.render_credenciales("installer", "cliente1", editable=True, key_prefix="p_cr")
else:
    AI.render_my_credentials()
'''
CR = [{"ID": "CR-1", "Type": "White Card", "Number": "WC-*123456789*", "IssueDate": "2024-02-01", "ExpiryDate": "", "DriveID": "D1", "File": "wc.pdf"},
      {"ID": "CR-2", "Type": "Forklift (LF)", "Number": "F2", "IssueDate": "2025-03-10", "ExpiryDate": "2029-03-10"},
      {"ID": "CR-3", "Type": "First Aid", "Number": "F3", "IssueDate": "2023-09-30", "ExpiryDate": "2026-09-30"},
      {"ID": "CR-4", "Type": "Working at Heights", "Number": "F4", "IssueDate": "", "ExpiryDate": "2026-11-18"},
      {"ID": "CR-5", "Type": "Driver License", "Number": "F5", "Class": "HR", "IssueDate": "", "ExpiryDate": "2026-11-05"}]


def cr(ed=False, f=CR):
    a = AppTest.from_string(GC, default_timeout=60)
    a.session_state["_CR"], a.session_state["_ED"] = f, ed
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = cr()
_md = [str(x.value) for x in a.markdown]
chk("⚠️ sin título propio", not [x for x in _md if x.startswith("#")], _md[:3])
chk("⚠️ sin tabla: una tarjeta por credencial", not list(a.dataframe) and len(a.get("expandable")) == 0)
chk("⚠️ v628 · cada cifra con su pie: el tema solo agranda el número en tarjetas de TRES líneas",
    all(str(b.label).count("\n\n") == 2 for b in a.button if str(b.key).startswith("cpxkpi_cred_")),
    [str(b.label) for b in a.button if str(b.key).startswith("cpxkpi_cred_")])
chk("sin `st.metric`: cifras que se pueden tocar", not list(a.metric)
    and sorted(b.key for b in a.button if str(b.key).startswith("cpxkpi_cred_"))
    == ["cpxkpi_cred_por_vencer", "cpxkpi_cred_todas", "cpxkpi_cred_vencido", "cpxkpi_cred_vigente"])
_o = [x for x in _md if x.startswith("**") and "Expire" not in x]
chk("⚠️ lo vencido primero, luego lo que vence antes, lo vigente y lo que no vence",
    _o == ["**First Aid**", "**Driver License**", "**Working at Heights**", "**Forklift \\(LF\\)**", "**White Card**"], _o)
_t = _todo(a)
chk("⚠️ vencida: desde cuándo, DD/MM/YYYY", ":red[:material/cancel:] **Expired** on 30/09/2026" in _t, _t)
chk("⚠️ por vencer: cuándo", "**Expires in 14 days** · 18/11/2026" in _t and "**Expires tomorrow**" in _t, _t)
chk("vigente: hasta cuándo", "Valid until 10/03/2029" in _t, _t)
chk("sin vencimiento, dicho", "No expiry" in _t, _t)
chk("⚠️ el número entero y tal cual, la clase y la fecha de emisión en DD/MM/YYYY",
    "\\*123456789\\*" in _t and "No. WC" in _t and "Class HR" in _t and "Issued 01/02/2024" in _t, _t)
chk("⚠️ el documento NO se baja al pintar (se bajaban todos en cada pasada)", a.session_state["_LOG"] == [], a.session_state["_LOG"])
chk("…y el botón está", [d for d in a.get("download_button") if "document" in str(d.label)])
_btn(a, "cpxkpi_cred_vencido").click()
a.run()
_md = [str(x.value) for x in a.markdown]
chk("⚠️ la cifra filtra", "**First Aid**" in _md and "**Driver License**" not in _md, _md)
_btn(a, "cpxkpi_cred_vencido").click()
a.run()
chk("…y otra vez, la quita", "**Driver License**" in [str(x.value) for x in a.markdown])
a = cr(f=CR[:2])
_btn(a, "cpxkpi_cred_vencido").click()
a.run()
chk("un filtro vacío lo dice", "None in this state." in _todo(a), _todo(a))
a = cr(ed=True)
chk("⚠️ la oficina conserva su tabla", len(list(a.dataframe)) == 1)
_v = a.dataframe[0].value
chk("⚠️ …en DD/MM/YYYY", list(_v["Vence"])[:3] == ["—", "10/03/2029", "30/09/2026"] and list(_v["Issued"])[0] == "01/02/2024", _v.to_dict())
chk("…y «No expiry» donde no vence", list(_v["Estado"])[0] == "No expiry", list(_v["Estado"]))
chk("⚠️ …sin bajar nada al pintar", a.session_state["_LOG"] == [], a.session_state["_LOG"])
chk("…con sus cifras activas también", _btn(a, "cpxkpi_cred_vigente") is not None)

sec("4. ⚠️ My payslips")
GN = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "installer", "nombre": "i", "rol": "field", "grupo": "cliente1"})
from core import payroll_ui as PU, payroll as N, payslip_pdf as PP
_L = st.session_state.setdefault("_LOG", [])
N.is_configured = lambda: True
N.list_nominas = lambda g, usuario=None: st.session_state["_N"]
PP.generate_payslip_pdf = lambda f, g: (_L.append(f.get("ID")) or b"%PDF")
PU.render_mis_colillas("installer", "cliente1")
'''


def nom(i, est="pagada", pago="2026-10-22"):
    return {"ID": f"NOM-{i:03d}", "PeriodFrom": f"2026-{i % 9 + 1:02d}-01", "PeriodTo": f"2026-{i % 9 + 1:02d}-{i % 20 + 7:02d}",
            "Hours": "38", "Net": "1340", "Status": est, "PaymentDate": pago}


def pag(f):
    a = AppTest.from_string(GN, default_timeout=60)
    a.session_state["_N"] = f
    a.run()
    chk("   (sin excepción)", not a.exception, [e.value for e in a.exception][:1])
    return a


a = pag([nom(i) for i in range(12)])
_md = [str(x.value) for x in a.markdown]
chk("⚠️ sin título propio", not [x for x in _md if x.startswith("#")], _md[:2])
chk("⚠️⚠️ NINGÚN PDF se genera al pintar (eran 411 ms cada uno, en cada pasada)", a.session_state["_LOG"] == [], a.session_state["_LOG"])
chk("⚠️ se ven 10 y el resto con un botón", len(a.get("download_button")) == 10 and "Show all (12)" in str(_btn(a, "myp_todas").label))
_btn(a, "myp_todas").click()
a.run()
chk("…que las enseña todas, sin generar nada", len(a.get("download_button")) == 12 and a.session_state["_LOG"] == [])
a = pag([nom(1), nom(2, "emitida", "")])
_t = _todo(a)
# ⚠️ v663 · CADUCADO a propósito: las horas de la colilla con DOS decimales («8.0 h × 55 = 439.45» no cuadraba)
chk("⚠️ lo importante en su línea: «Net $1,340.00 · 38.00 h»", "Net **$1,340.00** · 38.00 h" in _t, _t)
chk("⚠️ la fecha de pago, DD/MM/YYYY", "paid on 22/10/2026" in _t, _t)
chk("emitida, sin fecha", "issued" in _t, _t)
a = pag([])
chk("sin nóminas, lo dice", "You have no payslips yet." in _todo(a))
_u = _src("payroll_ui.py")
chk("⚠️ el error crudo ya no se pinta", "st.caption(str(e))" not in _u.split("def render_mis_colillas")[1])
from core import payroll_ui as PYU, payslip_pdf as PP            # noqa: E402
_pp = PP.generate_payslip_pdf
PP.generate_payslip_pdf = lambda f, g: b"%PDF-ok"
chk("⚠️ la descarga diferida genera el de ESA nómina", PYU._pdf_colilla({"ID": "N"}, "g") == b"%PDF-ok")
PP.generate_payslip_pdf = _pp

print("\n%d ok, %d fallos" % (n_ok, len(fallos)))
for x in fallos:
    print("  FALLO:", x)
sys.exit(1 if fallos else 0)
