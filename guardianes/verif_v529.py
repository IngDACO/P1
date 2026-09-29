# -*- coding: utf-8 -*-
"""v529 · LA CAJA DEL PARTE SE VACÍA DE VERDAD (en el navegador) AL GUARDAR.

Visto en producción el 29/09/2026 con la sesión de campo: el parte se guardaba y salía en
la lista, pero el TEXTO SEGUÍA EN LA CAJA, invitando a guardarlo otra vez. Desde v516 se
vaciaba con `st.session_state.pop(clave)`: el servidor quedaba en "" pero el navegador no se
enteraba, porque Streamlit solo le manda el valor nuevo (`set_value`) cuando el código lo
ASIGNA. AppTest lo daba por bueno porque lee el valor del SERVIDOR (`.value == ""`).

Lo que protege, EJECUTANDO la pantalla con AppTest y mirando el `set_value` del proto —el
contrato con el navegador—, no solo el valor:
  (a) ⚠️ tras un guardado confirmado, la caja llega al navegador VACÍA (`set_value` True);
  (b) ⚠️ si la hoja falla, el texto se queda — también en la pasada siguiente (la marca de
      vaciar no puede quedarse encendida esperando);
  (c) la marca se consume UNA vez: lo que se escribe después no se borra solo;
  (d) se guarda una sola vez;
  (e) la sonda está validada: con el patrón viejo (`pop`) el mismo chequeo da False.
"""
import datetime
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


def sec(x):
    print("\n%s" % x)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import clock                                            # noqa: E402
from core import daily_log as DL                                  # noqa: E402

K = "t_dl_txt_PRJ-T"
_orig = (DL.crear, DL.partes, clock.today)
LLAMADAS, RESP = [], [(True, "LOG-9")]
DL.crear = lambda pid, grupo, txt, usuario, dia=None: (LLAMADAS.append(txt) or RESP[0])
DL.partes = lambda pid: []
clock.today = lambda g=None: datetime.date(2026, 9, 30)

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import daily_log_ui as DLU
st.session_state.setdefault("auth", {"usuario": "campo000", "rol": "field", "grupo": "cliente1"})
DLU.render_campo("PRJ-T", "cliente1", "campo000", key_prefix="t")
''' % RAIZ


def _caja(at):
    ta = at.text_area(key=K)
    return ta.value, ta.proto.set_value


def _guardar(at):
    next(b for b in at.button if "Save the daily log" in str(b.proto.label)).click()
    at.run()


try:
    # ═════════════════════════════════════════════════════════════════
    sec("1. ⚠️ Guardado confirmado: la caja llega VACÍA al navegador")
    at = AppTest.from_string(GUION, default_timeout=60)
    at.run()
    chk("la pantalla pinta sin errores", not at.exception, [e.value for e in at.exception][:1])
    at.text_area(key=K).input("Installed headers on all landings").run()
    chk("escrito: el texto está en la caja", _caja(at)[0] == "Installed headers on all landings",
        _caja(at))
    _guardar(at)
    chk("sin errores al guardar", not at.exception, [e.value for e in at.exception][:1])
    chk("se guarda UNA vez, con el texto escrito",
        LLAMADAS == ["Installed headers on all landings"], LLAMADAS)
    _v, _sv = _caja(at)
    chk("en el servidor la caja queda vacía", _v == "", _v)
    chk("⚠️ ...y el navegador RECIBE el vacío (`set_value`): el fallo de producción",
        _sv is True, _sv)

    sec("2. La marca se consume una sola vez")
    at.text_area(key=K).input("second log").run()
    chk("lo que se escribe DESPUÉS no se borra solo", _caja(at)[0] == "second log", _caja(at))
    at.run()
    chk("...ni en la pasada siguiente", _caja(at)[0] == "second log", _caja(at))

    # ═════════════════════════════════════════════════════════════════
    sec("3. ⚠️ Si la hoja falla, el texto SE QUEDA (control)")
    LLAMADAS.clear()
    RESP[0] = (False, "The sheet did not respond")
    at = AppTest.from_string(GUION, default_timeout=60)
    at.run()
    at.text_area(key=K).input("Two hundred words written in a basement").run()
    _guardar(at)
    chk("se intentó guardar", LLAMADAS == ["Two hundred words written in a basement"], LLAMADAS)
    chk("se dice que falló", any("did not respond" in str(e.value) for e in at.error),
        [e.value for e in at.error])
    chk("⚠️ el texto sigue en la caja", _caja(at)[0] == "Two hundred words written in a basement",
        _caja(at))
    at.run()
    chk("⚠️ ...y sigue en la pasada SIGUIENTE (ninguna marca de vaciar quedó encendida)",
        _caja(at)[0] == "Two hundred words written in a basement", _caja(at))

    # ═════════════════════════════════════════════════════════════════
    sec("4. La sonda está validada (trampa nº12)")
    VIEJO = r'''
import streamlit as st
st.text_area("x", key="k")
if st.button("guardar", key="b"):
    st.session_state.pop("k", None)
    st.rerun()
'''
    at = AppTest.from_string(VIEJO)
    at.run()
    at.text_area(key="k").input("hola").run()
    at.button(key="b").click().run()
    chk("con el patrón de v516-v528 (`pop`), el servidor dice «vacía»…",
        at.text_area(key="k").value == "", at.text_area(key="k").value)
    chk("⚠️ …pero `set_value` es False: el navegador se queda con el texto — y este chequeo "
        "lo VE (por eso sirve el de la sección 1)",
        at.text_area(key="k").proto.set_value is False, at.text_area(key="k").proto.set_value)
finally:
    (DL.crear, DL.partes, clock.today) = _orig

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
