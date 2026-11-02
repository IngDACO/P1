# -*- coding: utf-8 -*-
"""v633 · LO QUE DESTAPÓ EL RECORRIDO DE LA OFICINA (02/11/2026, «Si dale con todo»).

  (1) ⚠️ DINERO: el correo mandaba a decidir la baja sobre el saldo a Planning · Absences, donde solo había «Cancel»,
      y la nómina pagaba todo: 20 días con 10 de saldo (medido en producción). → Lo que pasa del saldo se DERIVA, no
      se paga hasta que la oficina elija «Pay them» o «Leave them unpaid», y Payroll y el parte lo dicen antes.
  (2) ⚠️ SEGURIDAD: «Add credential» aceptaba el formulario vacío y `compliance` daba `cumple: True` con una ficha
      de Forklift sin nada. → Número siempre, vencimiento salvo la White Card, y lo incompleto no cuenta.
  (3) Borrar una credencial se iba de un toque. (4) No se corregían ni el tipo ni la emisión, y «s/n» en español; el
      selector saltaba de credencial al corregir el número. (5) Las cifras no sumaban. (6) Abrir la ficha, una fila de
      Files o el aviso de la campana quedaba fuera de pantalla. (7) Dos Survey por decidir no se distinguían.
Sin red ni hoja: se sustituye lo que escribe, y las pantallas se ejercitan con AppTest (trampa 44).
"""
import datetime as dt
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

st.session_state["auth"] = {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "g"}
from core import ausencias as AU, chat_agent as CA, credentials as C   # noqa: E402

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


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def fila(aid, tipo, d0, d1, estado=AU.APROBADA, paga="", usuario="u1", findes="NO"):
    return {"ID": aid, "Group": "g", "User": usuario, "Name": usuario.upper(), "Type": tipo, "From": d0, "To": d1,
            "Days": "", "Reason": "", "Status": estado, "ResolvedBy": "", "ResolvedDate": "", "AdminNote": "",
            "CreatedBy": usuario, "Created": "", "IncludesWeekends": findes, "OverBalancePay": paga}


E, V = AU.ENFERMEDAD, AU.VACACIONES
_filas = []
AU._records = lambda: _filas
AU.timeclock.horas_por_usuario_dia = lambda *a, **k: {}
_ingreso = {}


class _Auth:
    @staticmethod
    def fecha_ingreso(u):
        return _ingreso.get(u)


sys.modules["core.auth"] = _Auth
import core                                                       # noqa: E402
core.auth = _Auth


def pon(*filas):
    _filas[:] = list(filas)


def pagados(u="u1", d0="2026-01-01", d1="2026-12-31"):
    return (AU.horas_pagadas_dia("g", d0, d1).get(u) or {"dias": {}, "por_tipo": {}, "dias_contados": 0, "recortados": []})


# ─────────────────────────────────────────────────────────────────────────────
sec("1. Lo que pasa del saldo se deriva, y no se paga hasta decidirlo")
BAJA20 = ("2026-11-09", "2026-12-04")                # 20 días hábiles, con 10 de saldo: el caso medido
pon(fila("A", E, *BAJA20))
_dias = AU.dias_del_rango(*BAJA20)
_sob = AU.sobre_saldo("g", "u1", E)
chk("el caso medido: 20 días, 10 sobre el saldo", len(_sob.get("A", [])) == 10, _sob)
chk("⚠️ son los ÚLTIMOS: los primeros gastan saldo", _sob.get("A") == _dias[10:], _sob.get("A"))
_p = pagados()
chk("⚠️⚠️ sin decidir se pagan 10 días, no 20", len(_p["dias"]) == 10 and _p["dias_contados"] == 10, _p)
chk("...que son 80 h", AU.horas_pagadas_grupo("g", "2026-01-01", "2026-12-31")["u1"]["horas"] == 80.0)
chk("el concepto de la colilla dice los pagados", _p["por_tipo"] == {E: 10}, _p["por_tipo"])
chk("saldo: usados 10, no 20", AU.saldo("g", "u1", E, dt.date(2026, 11, 2))["usados"] == 10.0,
    AU.saldo("g", "u1", E, dt.date(2026, 11, 2)))
chk("sale en lo que queda por decidir", [x["id"] for x in AU.excesos_por_decidir("g")] == ["A"])
chk("...con sus días", len(AU.excesos_por_decidir("g")[0]["dias"]) == 10)
chk("el rango de la nómina acota el aviso",
    AU.excesos_por_decidir("g", "2026-11-09", "2026-11-20") == [], AU.excesos_por_decidir("g", "2026-11-09", "2026-11-20"))
chk("...y entra si coge alguno", len(AU.excesos_por_decidir("g", "2026-11-23", "2026-11-24")[0]["dias"]) == 2)

pon(fila("A", E, *BAJA20, paga=AU.EXCESO_PAGA))
_p = pagados()
chk("⚠️ «Pay them»: los 20", len(_p["dias"]) == 20 and _p["por_tipo"] == {E: 20}, _p["por_tipo"])
chk("...y gastan saldo", AU.saldo("g", "u1", E, dt.date(2026, 11, 2))["usados"] == 20.0)
chk("...y ya no queda por decidir", AU.excesos_por_decidir("g") == [])
pon(fila("A", E, *BAJA20, paga=AU.EXCESO_NO))
_p = pagados()
chk("⚠️ «Leave them unpaid»: 10", len(_p["dias"]) == 10, _p["por_tipo"])
chk("...y tampoco queda por decidir", AU.excesos_por_decidir("g") == [])

pon(fila("A", E, "2026-11-09", "2026-11-18"), fila("B", E, "2026-11-23", "2026-11-27"),
    fila("C", E, "2026-08-03", "2026-08-03", estado=AU.CANCELADA))
chk("dos bajas (8 + 5): gasta la primera y sobran 3 de la segunda",
    len(AU.sobre_saldo("g", "u1", E).get("B", [])) == 3 and "A" not in AU.sobre_saldo("g", "u1", E), AU.sobre_saldo("g", "u1", E))
pon(fila("A", E, "2026-11-09", "2026-11-18", estado=AU.CANCELADA), fila("B", E, "2026-11-23", "2026-11-27"))
chk("⚠️ cancelar la primera devuelve días: la segunda ya no sobra (por eso se deriva)", AU.sobre_saldo("g", "u1", E) == {})

pon(fila("A", E, "2026-12-14", "2026-12-31"), fila("B", E, "2027-01-04", "2027-01-08"))
_s = AU.sobre_saldo("g", "u1", E)
chk("⚠️ cada periodo tiene su saldo: enero empieza de cero", "B" not in _s and len(_s.get("A", [])) == 4, _s)
_ingreso["u1"] = dt.date(2020, 12, 21)
pon(fila("A", E, "2026-12-07", "2026-12-18"), fila("B", E, "2026-12-21", "2026-12-25"))
chk("...y va por aniversario si tiene fecha de alta", AU.sobre_saldo("g", "u1", E) == {}, AU.sobre_saldo("g", "u1", E))
_ingreso.clear()

pon(fila("A", V, "2026-01-05", "2026-02-27"))
chk("⚠️ a las vacaciones no se les recorta nada: esas se aprueban antes",
    AU.sobre_saldo("g", "u1", V) == {} and pagados()["dias_contados"] == 40, pagados()["dias_contados"])
pon(fila("A", E, *BAJA20), fila("B", E, "2026-08-03", "2026-08-03", usuario="u2"))
chk("cada persona con su saldo", AU.sobre_saldo("g", "u2", E) == {})
pon(fila("A", E, "2026-11-09", "2026-11-20", estado=AU.PENDIENTE))
chk("lo que no está aprobado no gasta nada", AU.sobre_saldo("g", "u1", E) == {} and AU.exceso_de(_filas[0])["dias"] == [])

pon(fila("A", E, *BAJA20))
AU.timeclock.horas_por_usuario_dia = lambda *a, **k: {"u1": {dt.date(2026, 11, 30): 8.0}}
_p = pagados()
chk("un día sobre el saldo con horas fichadas no es un «recorte»: no estaba pagado", _p["recortados"] == [], _p["recortados"])
AU.timeclock.horas_por_usuario_dia = lambda *a, **k: {}
_tramo = AU.horas_pagadas_dia("g", "2026-11-23", "2026-12-04")
chk("⚠️ quien solo tiene días sin pagar no aparece: nada de una colilla de $0", "u1" not in _tramo, _tramo)
_c = leer("core/contable.py")
chk("el parte de horas sale de la misma función", "_AU.horas_pagadas_dia(grupo, d0, d1)" in _c)
chk("y avisa", "_AU2.excesos_por_decidir(grupo, d0, d1)" in _c and "Sick leave over the balance with no decision" in _c)
chk("la nómina también", "AU.horas_pagadas_grupo(grupo, desde, hasta)" in leer("core/payroll.py"))


# ─────────────────────────────────────────────────────────────────────────────
sec("2. Decidir: lo escribe en su sitio, y solo si procede")


class _H:
    def __init__(self, filas):
        self.filas, self.lotes, self.altas = filas, [], []

    def get_all_records(self, **k):
        return list(self.filas)

    def batch_update(self, lote, **k):
        self.lotes.append(lote)

    def append_row(self, f, **k):
        self.altas.append(dict(zip(AU.HEADERS, f)))


_h = _H([fila("A", E, *BAJA20), fila("Z", E, "2026-01-05", "2026-01-05", estado=AU.CANCELADA)])
AU._ws = lambda: _h
AU._invalidate = lambda: None
AU.columnas.canonizar = lambda r: r
AU.valores.canonizar = lambda r, s: r
ok, msg = AU.decidir_exceso("A", AU.EXCESO_NO, "Admin2")
_cel = {x["range"]: x["values"][0][0] for x in (_h.lotes[-1] if _h.lotes else [])}
from core.num import col_letter as _cl                            # noqa: E402
chk("⚠️ en la columna de la decisión y en la fila de esa baja", ok and _cel.get("%s2" % _cl(AU._COL["OverBalancePay"])) == "unpaid", _cel)
chk("y queda quién y cuándo", _cel.get("%s2" % _cl(AU._COL["ResolvedBy"])) == "Admin2" and "%s2" % _cl(AU._COL["ResolvedDate"]) in _cel, _cel)
chk("«OverBalancePay» va la última: la hoja migra sola", AU.HEADERS[-1] == "OverBalancePay")
ok, msg = AU.decidir_exceso("Z", AU.EXCESO_PAGA, "Admin2")
chk("una cancelada no se decide", not ok, msg)
ok, msg = AU.decidir_exceso("NO", AU.EXCESO_PAGA, "Admin2")
chk("una que no existe tampoco", not ok, msg)
_n = len(_h.lotes)
ok, msg = AU.decidir_exceso("A", "quizas", "Admin2")
chk("una decisión desconocida no escribe", not ok and len(_h.lotes) == _n, msg)
ok, msg = AU.decidir_exceso("A", "", "Admin2")
chk("se puede volver a decidir", ok and "not paid until you decide" in msg, msg)

pon()
_h = _H([])
AU._ws = lambda: _h
AU._next_id = lambda recs: "AUS-1"
AU.clock.now = lambda g=None: dt.datetime(2026, 11, 2, 9, 0)
ok, res = AU.solicitar("g", "u1", "U1", E, "2026-11-09", "2026-12-04")
chk("la fila casa con la cabecera", ok and len(_h.altas) == 1, res)
chk("⚠️ ya no se escribe «Over the balance by N»: se desincronizaba", _h.altas and _h.altas[0]["AdminNote"] == "", _h.altas[:1])
chk("nace sin decidir", _h.altas and _h.altas[0]["OverBalancePay"] == "")
chk("con sus fines de semana en su sitio", _h.altas and _h.altas[0]["IncludesWeekends"] == "NO")


# ─────────────────────────────────────────────────────────────────────────────
sec("3. La pantalla de Absences: decidir de verdad (AppTest)")
BANDEJA = r'''
import sys
sys.path.insert(0, r"%s")
import datetime as dt
import streamlit as st
from core import ausencias as AU, ausencias_ui as U, clock, flash
st.session_state.setdefault("auth", {"rol": "administrator", "usuario": "Admin2", "nombre": "Bobo", "grupo": "g"})
F = st.session_state["_F"]
AU.is_configured = lambda: True
AU._records = lambda: F
AU.periodo_saldo = lambda g, u, ref=None: {"desde": dt.date((ref or dt.date(2026, 11, 2)).year, 1, 1),
                                           "hasta": dt.date((ref or dt.date(2026, 11, 2)).year, 12, 31),
                                           "origen": "natural", "ingreso": None}
clock.today = lambda g=None: dt.date(2026, 11, 2)
def _dec(aid, como, quien):
    st.session_state["_dec"] = (aid, como, quien)
    for r in F:
        if r["ID"] == aid:
            r["OverBalancePay"] = como
    return True, "Hecho"
AU.decidir_exceso = _dec
U._avisar_exceso = lambda u, r, c: st.session_state.__setitem__("_av", (u, c))
flash.mostrar()
U.render_bandeja("g")
''' % RAIZ


def bandeja(*filas):
    a = AppTest.from_string(BANDEJA, default_timeout=60)
    a.session_state["_F"] = list(filas)
    a.run()
    return a


def btn(a, k):
    return next((b for b in a.button if b.key == k), None)


def txt(a):
    return " | ".join(str(x.value) for k in ("markdown", "caption", "info", "warning", "error", "success") for x in getattr(a, k, []))


a = bandeja(fila("AUS-1", E, *BAJA20))
chk("abre", not a.exception, [e.value for e in a.exception][:1])
_t = txt(a)
chk("⚠️ dice cuántos, cuáles y que no se pagan", "10 days over the balance" in _t and "23/11/2026" in _t and "not paid until you decide" in _t, _t[:400])
chk("los dos botones", btn(a, "ausexp_baja_AUS-1") is not None and btn(a, "ausexn_baja_AUS-1") is not None)
chk("el histórico no repite los botones", btn(a, "ausexp_hist_AUS-1") is None)
btn(a, "ausexn_baja_AUS-1").click()
a.run()
chk("⚠️ «Leave them unpaid» decide, con quién", a.session_state["_dec"] == ("AUS-1", AU.EXCESO_NO, "Admin2"), a.session_state["_dec"])
chk("⚠️ y se le avisa a la persona", a.session_state["_av"] == ("u1", AU.EXCESO_NO))
_t = txt(a)
chk("queda dicho, y ya no hay botones de decidir", "10 days over the balance (23/11/2026 → 04/12/2026): unpaid" in _t and btn(a, "ausexp_baja_AUS-1") is None, _t[:400])
btn(a, "ausexc_baja_AUS-1").click()
a.run()
chk("«Change» vuelve a decidir", a.session_state["_dec"] == ("AUS-1", "", "Admin2") and btn(a, "ausexp_baja_AUS-1") is not None)
btn(a, "ausexp_baja_AUS-1").click()
a.run()
chk("«Pay them» decide", a.session_state["_dec"] == ("AUS-1", AU.EXCESO_PAGA, "Admin2"))
chk("⚠️ y recuerda la colilla ya emitida", "void it and generate it again" in txt(a), txt(a)[:300])
VIEJA = fila("AUS-2", E, "2026-05-04", "2026-05-29")
a = bandeja(VIEJA)
chk("⚠️ una vieja sin decidir sigue en la bandeja", btn(a, "ausexp_baja_AUS-2") is not None, txt(a)[:300])
a = bandeja(fila("AUS-2", E, "2026-05-04", "2026-05-29", paga=AU.EXCESO_NO))
chk("...y decidida se va al histórico", btn(a, "ausexc_baja_AUS-2") is None and "unpaid" in txt(a))
a = bandeja(fila("AUS-3", E, "2026-11-09", "2026-11-10"))
chk("sin exceso, nada de esto", btn(a, "ausexp_baja_AUS-3") is None and "over the balance" not in txt(a), txt(a)[:300])

MIAS = r'''
import sys
sys.path.insert(0, r"%s")
import datetime as dt
import streamlit as st
from core import ausencias as AU, ausencias_ui as U
AU._records = lambda: st.session_state["_F"]
AU.periodo_saldo = lambda g, u, ref=None: {"desde": dt.date(2026, 1, 1), "hasta": dt.date(2026, 12, 31), "origen": "natural", "ingreso": None}
for r in st.session_state["_F"]:
    U._tarjeta_mia(r, "u1")
''' % RAIZ
for paga, esperado in (("", "10 days over your balance: the office decides how they are paid"),
                       (AU.EXCESO_PAGA, "10 days over your balance: paid"), (AU.EXCESO_NO, "10 days over your balance: unpaid")):
    a = AppTest.from_string(MIAS, default_timeout=60)
    a.session_state["_F"] = [fila("AUS-1", E, *BAJA20, paga=paga)]
    a.run()
    chk("el campo lo ve: «%s»" % esperado[:44], not a.exception and esperado in txt(a), [e.value for e in a.exception][:1] or txt(a)[:200])


# ─────────────────────────────────────────────────────────────────────────────
sec("4. Payroll lo dice ANTES de generar (AppTest)")
NOMINA = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import auth, ausencias as AU, payroll_ui as U, timeclock
timeclock.horas_por_usuario_rango = lambda *a, **k: {"u1": {"horas": 8.0, "nombre": "U1"}}
auth.rate_map = lambda g: {"u1": 30.0}
auth.group_num_setting = lambda g, k, d: d
AU.excesos_por_decidir = lambda g, d0, d1: st.session_state.get("_X", [])
U._generar("g")
''' % RAIZ


def nomina(x):
    a = AppTest.from_string(NOMINA, default_timeout=60)
    a.session_state["_X"] = x
    a.run()
    return a


a = nomina([{"id": "AUS-1", "usuario": "u1", "nombre": "Ana *Pi*", "dias": [1, 2, 3]}])
chk("⚠️ abre (usa `literal_md`, que hay que importar)", not a.exception, [e.value for e in a.exception][:1])
chk("⚠️ avisa con nombre y días", "Sick leave over the balance with no decision" in txt(a) and "(3 d)" in txt(a), txt(a)[:300])
chk("el nombre va escapado", "Ana \\*Pi\\*" in txt(a), txt(a)[:300])
chk("y lleva a decidirlo", btn(a, "nom_gen_ir_aus") is not None)
a = nomina([])
chk("sin nada, ni aviso ni botón", not a.exception and btn(a, "nom_gen_ir_aus") is None and "with no decision" not in txt(a))


# ─────────────────────────────────────────────────────────────────────────────
sec("5. Una credencial vale si está completa")
chk("⚠️ sin número no vale", C.falta_dato("Forklift (LF)", "", "2029-01-01") != "")
chk("⚠️ sin vencimiento no vale", C.falta_dato("Forklift (LF)", "F1", "") != "")
chk("la White Card no vence", C.falta_dato("White Card", "W1", "") == "" and C.SIN_VENCIMIENTO == ("White Card",))
chk("...pero lleva número", C.falta_dato("White Card", "  ", "") != "")
chk("«Other» también lleva fecha", C.falta_dato("Other", "O1", "") != "")
for tipo in C.CATALOGO:
    if tipo != "White Card":
        chk("%s lleva fecha" % tipo, C.falta_dato(tipo, "1", "") != "")


class _Ws:
    def __init__(self, filas=()):
        self.filas, self.altas, self.lotes = list(filas), [], []

    def get_all_records(self, **k):
        return list(self.filas)

    def append_row(self, f, **k):
        self.altas.append(f)

    def batch_update(self, b, **k):
        self.lotes.append(b)


_w = _Ws()
C._ws = lambda: _w
C._invalidate = lambda: None
C._next_id = lambda r: "CR-1"
C.columnas.canonizar = lambda r: r
ok, msg = C.add("u1", "g", "")
chk("⚠️ el motor rechaza un alta sin tipo", not ok and not _w.altas, msg)
ok, msg = C.add("u1", "g", "White Card")
chk("⚠️⚠️ y el formulario vacío, que es lo que pasaba", not ok and not _w.altas and "number is required" in msg, msg)
ok, msg = C.add("u1", "g", "Forklift (LF)", "F1")
chk("⚠️ Forklift sin fecha", not ok and not _w.altas and "expiry date is required" in msg, msg)
ok, msg = C.add("u1", "g", "White Card", "W1")
chk("una White Card con número entra", ok and len(_w.altas) == 1, msg)
ok, msg = C.add("u1", "g", "Forklift (LF)", "F1", vencimiento="2029-01-01")
chk("y un Forklift completo", ok and len(_w.altas) == 2, msg)

FILA_C = {"ID": "CR-1", "User": "u1", "Group": "g", "Type": "Forklift (LF)", "Number": "F1", "ExpiryDate": "2029-01-01"}
_w = _Ws([FILA_C])
ok, msg = C.update("CR-1", {"Number": ""})
chk("⚠️ editar no puede vaciar el número", not ok and not _w.lotes, msg)
ok, msg = C.update("CR-1", {"ExpiryDate": ""})
chk("⚠️ ni la fecha", not ok and not _w.lotes, msg)
ok, msg = C.update("CR-1", {"Type": "White Card", "ExpiryDate": ""})
chk("cambiar a White Card sí la deja sin fecha", ok, msg)
_w = _Ws([dict(FILA_C, Number="")])
ok, msg = C.update("CR-1", {"LastNotice": "2026-11-02"})
chk("⚠️ el aviso de vencimiento sigue pudiendo apuntar en una incompleta", ok, msg)

_lista = []
C.list_for = lambda u: _lista
_lista[:] = [{"Type": "Forklift (LF)", "Number": "", "ExpiryDate": ""}]
chk("⚠️⚠️ la ficha vacía de Forklift ya no hace apto a nadie (daba cumple: True)",
    C.compliance("u", ["Forklift (LF)"]) == {"por_tipo": {"Forklift (LF)": "falta"}, "cumple": False}, C.compliance("u", ["Forklift (LF)"]))
_lista[:] = [{"Type": "Forklift (LF)", "Number": "F1", "ExpiryDate": ""}]
chk("⚠️ con número y sin fecha, tampoco", C.compliance("u", ["Forklift (LF)"])["cumple"] is False)
_lista[:] = [{"Type": "White Card", "Number": "W1", "ExpiryDate": ""}]
chk("la White Card sin fecha cumple", C.compliance("u", ["White Card"]) == {"por_tipo": {"White Card": "vigente"}, "cumple": True})
_lista[:] = [{"Type": "White Card", "Number": "", "ExpiryDate": ""}]
chk("...sin número no", C.compliance("u", ["White Card"])["cumple"] is False)
_lista[:] = [{"Type": "Forklift (LF)", "Number": "", "ExpiryDate": ""},
             {"Type": "Forklift (LF)", "Number": "F2", "ExpiryDate": "2029-01-01"}]
chk("si tiene otra buena, manda la buena", C.compliance("u", ["Forklift (LF)"])["cumple"] is True)
chk("estado: incompleta", C.estado({"Type": "EWP / Boom (WP)", "Number": "", "ExpiryDate": "2029-01-01"}) == "incompleta")
chk("estado: lo que no vence está vigente", C.estado({"Type": "White Card", "Number": "W", "ExpiryDate": ""}) == "vigente")
chk("estado: vencida", C.estado({"Type": "First Aid", "Number": "1", "ExpiryDate": "2020-01-01"}) == "vencido")

C.list_group = lambda g: [{"User": "u1", "Type": "First Aid", "Number": "1", "ExpiryDate": "2020-01-01"},
                          {"User": "u2", "Type": "First Aid", "Number": "", "ExpiryDate": ""}]
_Auth.list_users = staticmethod(lambda g: [{"User": "u1", "Name": "U1"}, {"User": "u2", "Name": "U2"}])
_ts, _fs = C.matrix("g")
chk("⚠️ la matriz en inglés (decía «vencido» bajo un título en inglés)", [f["First Aid"] for f in _fs] == ["expired", "incomplete"], _fs)


# ─────────────────────────────────────────────────────────────────────────────
sec("6. La pantalla de credenciales (AppTest)")
CRED = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import auth_ui as U, credentials as C
st.session_state.setdefault("auth", {"rol": "administrator", "usuario": "Admin2", "nombre": "Bobo", "grupo": "g"})
F = st.session_state["_F"]
C.is_configured = lambda: True
C.list_for = lambda u: F
def _upd(i, c):
    st.session_state["_upd"] = (i, c)
    falta = C.falta_dato(c.get("Type"), c.get("Number"), c.get("ExpiryDate"))
    if falta:
        return False, falta
    for r in F:
        if r["ID"] == i:
            r.update(c)
    return True, "ok"
C.update = _upd
def _del(i):
    st.session_state["_del"] = i
    F[:] = [r for r in F if r["ID"] != i]
    return True, "ok"
C.delete = _del
from core import flash
flash.mostrar()
U.render_credenciales("u1", "g", editable=True, key_prefix="zz")
''' % RAIZ
_FC = lambda: [{"ID": "CR-1", "Type": "White Card", "Number": "W1", "IssueDate": "2024-02-01", "ExpiryDate": "", "Note": "", "DriveID": ""},
               {"ID": "CR-2", "Type": "Working at Heights", "Number": "H1", "IssueDate": "2024-02-01", "ExpiryDate": (dt.date.today() + dt.timedelta(days=9)).isoformat(), "Note": "", "DriveID": ""},
               {"ID": "CR-3", "Type": "First Aid", "Number": "A1", "IssueDate": "2023-02-01", "ExpiryDate": "2024-09-30", "Note": "", "DriveID": ""},
               {"ID": "CR-4", "Type": "Forklift (LF)", "Number": "F1", "IssueDate": "2025-03-10", "ExpiryDate": "2029-03-10", "Note": "", "DriveID": ""}]


def cred(filas=None):
    a = AppTest.from_string(CRED, default_timeout=60)
    a.session_state["_F"] = filas if filas is not None else _FC()
    a.run()
    return a


a = cred()
chk("abre", not a.exception, [e.value for e in a.exception][:1])


def cifra(a, k):
    b = btn(a, "cpxkpi_cred_%s" % k)
    return int(re.search(r"\n\n(\d+)\n\n", b.label).group(1)) if b else None


_v = {k: cifra(a, k) for k in ("todas", "vigente", "por_vencer", "vencido")}
chk("⚠️ las cifras suman: 4 = 2 + 1 + 1 (la White Card cuenta como válida)", _v == {"todas": 4, "vigente": 2, "por_vencer": 1, "vencido": 1}, _v)
btn(a, "cpxkpi_cred_vigente").click()
a.run()
_tb = a.dataframe[0].value if a.dataframe else None
chk("⚠️ y «Valid» enseña las dos, también la que no vence", _tb is not None and sorted(_tb.iloc[:, 0]) == ["Forklift (LF)", "White Card"], None if _tb is None else list(_tb.iloc[:, 0]))
chk("el estado con mayúscula, como «No expiry»", _tb is not None and set(_tb.iloc[:, 1]) == {"Valid", "No expiry"}, None if _tb is None else list(_tb.iloc[:, 1]))
a = cred(_FC() + [{"ID": "CR-9", "Type": "First Aid", "Number": "", "ExpiryDate": "", "Note": "", "DriveID": ""}])
chk("una vieja incompleta sale con su cifra: 5 = 2 + 1 + 1 + 1", cifra(a, "incompleta") == 1 and cifra(a, "todas") == 5, cifra(a, "incompleta"))
chk("⚠️ el selector no dice «s/n» en español", any("no number" in str(o) for o in a.selectbox(key="zz_eselid").options)
    and not any("s/n" in str(o) for o in a.selectbox(key="zz_eselid").options), a.selectbox(key="zz_eselid").options)
a = cred()
chk("se corrige el tipo", a.selectbox(key="zz_etipo_CR-1").value == "White Card")
chk("⚠️ y la emisión", any(d.key == "zz_eemi_CR-1" for d in a.date_input))
chk("una licencia pide su clase", not any(s.key == "zz_eclase_CR-1" for s in a.selectbox))
a.selectbox(key="zz_etipo_CR-1").select("Driver License").run()
chk("...y sale al elegirla", any(s.key == "zz_eclase_CR-1" for s in a.selectbox))
a = cred()
a.selectbox(key="zz_eselid").select("CR-3").run()
a.text_input(key="zz_enum_CR-3").input("A2").run()
btn(a, "zz_eupd").click()
a.run()
chk("guarda todo lo editable", a.session_state["_upd"][1]["Number"] == "A2" and set(a.session_state["_upd"][1]) >= {"Type", "Class", "Number", "IssueDate", "ExpiryDate", "Note"}, a.session_state["_upd"])
chk("⚠️ corregir el número no salta a otra credencial", a.selectbox(key="zz_eselid").value == "CR-3", a.selectbox(key="zz_eselid").value)
a.text_input(key="zz_enum_CR-3").input("").run()
btn(a, "zz_eupd").click()
a.run()
chk("⚠️ vaciar el número se rechaza en pantalla", any("number is required" in str(e.value) for e in a.error), [e.value for e in a.error])
a = cred()
btn(a, "zz_edel").click()
a.run()
chk("⚠️ borrar pregunta", "_del" not in a.session_state and any("Delete this credential?" in str(w.value) for w in a.warning), [w.value for w in a.warning])
btn(a, "zz_edelno").click()
a.run()
chk("«Keep it» no borra", "_del" not in a.session_state and btn(a, "zz_edelok") is None)
btn(a, "zz_edel").click()
a.run()
btn(a, "zz_edelok").click()
a.run()
chk("«Yes, delete it» borra esa", a.session_state["_del"] == "CR-1", a.session_state["_del"] if "_del" in a.session_state else None)
_au = leer("core/auth_ui.py")
chk("⚠️ el texto ya no dice que se puede dejar en blanco", "blank if it does not expire" not in _au)


# ─────────────────────────────────────────────────────────────────────────────
sec("7. La vista baja a lo que se abre, y los Survey se distinguen")
_pu, _hu = leer("core/projects_ui.py"), leer("core/home_ui.py")
chk("⚠️ la ficha de Users", 'with st.container(key="cpx_gu_ficha"):\n            _PU._bajar_a("cpx_gu_ficha", "_bajar_cpx_gu_ficha", bloque="start")\n            _ficha_usuario(gente[_oi], grupo)' in _au)
chk("...solo al CAMBIAR de persona, no en cada pasada",
    'if st.session_state.get("_gu_tocado") != vista[_sr[0]]["User"]:\n            st.session_state["_gu_tocado"] = vista[_sr[0]]["User"]\n            st.session_state["_bajar_cpx_gu_ficha"] = True' in _au)
chk("⚠️ v634 · y baja también con la persona que ya estaba abierta: al no haber fila, se olvida",
    'else:\n        st.session_state.pop("_gu_tocado", None)' in _au)
chk("...y también desde otra pantalla", 'st.session_state["_gu_open"] = _du\n        st.session_state["_bajar_cpx_gu_ficha"] = True' in _au)
chk("⚠️ las acciones de una fila de Files", 'with st.container(key="cpx_arch_acc"):\n                _bajar_a("cpx_arch_acc", "_bajar_cpx_arch_acc")\n                _acciones_archivo(pid, _e, puede_borrar)' in _pu)
chk("...una vez por fila elegida", 'if st.session_state.get("_arch_sel") != _sel:' in _pu)
chk("⚠️ v634 · lo mismo en Files", 'else:\n            st.session_state.pop("_arch_sel", None)' in _pu)
_tm = leer("core/theme.py")
chk("⚠️ v634 · el contenedor no se mueve: ni menú subido ni franja blanca",
    '[data-testid="stAppViewContainer"] {{ overflow: clip !important; }}' in _tm)
chk("⚠️ v634 · el campo no ve un saldo negativo", """_v = f"{max(s['disponibles'], 0):.0f}\"""" in leer("core/ausencias_ui.py"))
chk("⚠️ el aviso de la campana", 'st.session_state["_bajar_cpx_arch_espera"] = True' in _hu and '_bajar_a("cpx_arch_espera", "_bajar_cpx_arch_espera", bloque="start")' in _pu)
chk("⚠️ marcados en la tabla", '"Archivo": ("⏳ " if _espera(e) else "") + e["nombre"]' in _pu)
chk("...y el aviso ya no lista nombres iguales", "Tap its row below" not in _pu and "the rows marked ⏳" in _pu)
chk("solo la oficina los ve marcados", "return (puede_borrar and bool(e.get(\"run\"))" in _pu)


# ─────────────────────────────────────────────────────────────────────────────
sec("8. La guía del asistente lo sabe")
G = re.sub(r"\s+", " ", CA.SYSTEM_PROMPT)
_u = leer("core/ausencias_ui.py")
for b in ("Pay them", "Leave them unpaid", "Sick leave recorded"):
    chk("cita «%s», que existe" % b, "**%s**" % b in G and b in _u, b)

print("\n=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
for x in fallos:
    print("  FALLO: %s" % x)
sys.exit(1 if fallos else 0)
