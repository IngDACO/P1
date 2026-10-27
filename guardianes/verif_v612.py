# -*- coding: utf-8 -*-
"""v612 · LO VISTO VERIFICANDO v611 EN PRODUCCIÓN (27/10/2026, «no dejes nada pendiente»).

  (a) dos lecciones olvidadas IGUALES salían en «Restore these» con el MISMO texto (y una lección y
      una regla iguales saldrían igual en «Forget these»): no había forma de saber cuál se elegía →
      la etiqueta lleva si es regla o aprendida (y cuántas veces), y al recuperar, la HORA del olvido;
  (b) el aviso del duplicado decía «learned again» también de una REGLA re-enseñada, y
      «1 … left as they are» → vale para las dos y para cualquier número.
Sin red y sin la hoja real (todo sustituido).
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin1", "nombre": "Admin Test", "rol": "administrator",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import daily_log_ui as DLU                              # noqa: E402

# ═════════════════════════════════════════════════════════════════
sec("1. La etiqueta de una lección")
_R = {"Phrase": "installed motor", "Activity": "Install motor (machine)", "Kind": "rule",
      "Confirmed": "0", "Rejected": "0", "Updated": "2026-10-27 17:53"}
_A = {"Phrase": "installed motor", "Activity": "Install motor (machine)", "Kind": "learned",
      "Confirmed": "2", "Rejected": "0", "Updated": "2026-10-27 10:00"}
chk("una regla dice que es regla", DLU._etq_leccion(_R) == "«installed motor» → Install motor (machine) · rule",
    DLU._etq_leccion(_R))
chk("una aprendida, cuántas veces (de la hoja llegan como TEXTO)",
    DLU._etq_leccion(_A) == "«installed motor» → Install motor (machine) · learned 2×", DLU._etq_leccion(_A))
chk("...y las veces que se rechazó, si las hay (una «no es»: 0 sí, 2 no)",
    DLU._etq_leccion(dict(_A, Confirmed=0, Rejected=2)).endswith("· learned 0× · rejected 2×"),
    DLU._etq_leccion(dict(_A, Confirmed=0, Rejected=2)))
chk("⚠️ una lección y una regla IGUALES ya no se confunden", DLU._etq_leccion(_A) != DLU._etq_leccion(_R))
chk("olvidada: con el día y la HORA del olvido (DD/MM/YYYY HH:MM)",
    DLU._etq_leccion(_R, olvidada=True).endswith("· rule · forgotten 27/10/2026 17:53"),
    DLU._etq_leccion(_R, olvidada=True))
chk("⚠️ dos olvidadas iguales el MISMO día ya no se confunden (visto en producción)",
    DLU._etq_leccion(_R, olvidada=True) != DLU._etq_leccion(dict(_R, Updated="2026-10-27 14:45"), olvidada=True))
chk("sin fecha, un guion (no un texto roto)", DLU._etq_leccion(dict(_R, Updated=""), olvidada=True).endswith("forgotten —"))
chk("un número raro en la hoja no revienta", DLU._etq_leccion(dict(_A, Confirmed="", Rejected="x")).endswith("learned 0×"))

# ═════════════════════════════════════════════════════════════════
sec("2. El panel (AppTest)")
APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": "admin1", "nombre": "X", "rol": "administrator",
                                     "grupo": "cliente1"})
from core import agente_memoria as MEM, daily_log as DL, daily_log_ui as DLU, flash
ss.setdefault("_rest", [])
MEM.lecciones = lambda grupo=None: [
    {"ID": "MEM-1", "Phrase": "zz", "Activity": "Spin motor", "Kind": "learned", "Confirmed": 1,
     "Rejected": 0, "Group": "cliente1", "Updated": "2026-10-27 10:00"},
    {"ID": "MEM-2", "Phrase": "zz", "Activity": "Spin motor", "Kind": "rule", "Confirmed": 0,
     "Rejected": 0, "Group": "cliente1", "Updated": "2026-10-27 11:00"}]
MEM.olvidadas = lambda grupo=None: [
    {"ID": "MEM-8", "Phrase": "zz prueba", "Activity": "Spin motor", "Kind": "rule", "Confirmed": "0",
     "Rejected": "0", "Group": "cliente1", "Active": "NO", "Updated": "2026-10-27 14:45"},
    {"ID": "MEM-9", "Phrase": "zz prueba", "Activity": "Spin motor", "Kind": "rule", "Confirmed": "0",
     "Rejected": "0", "Group": "cliente1", "Active": "NO", "Updated": "2026-10-27 17:53"}]
MEM.restaurar = lambda ids, g, dueno: (ss["_rest"].append(list(ids)) or ss.get("_res", (True, 0, 1)))
DL.partes = lambda pid, autor=None, dia=None: []
flash.mostrar()
DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
'''


def _w(lista, key):
    return next((x for x in lista if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


at = AppTest.from_string(APP, default_timeout=90).run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_fo = _w(at.multiselect, "adm_mem_olv")
_op = list(_fo.options) if _fo else []          # AppTest ya las da formateadas (como verif_v610)
chk("⚠️ «Forget these»: una lección y una regla iguales, con textos DISTINTOS",
    len(_op) == 2 and len(set(_op)) == 2 and any("· rule" in x for x in _op) and any("learned 1×" in x for x in _op), _op)
_w(at.checkbox, "adm_mem_ver_olv").check()
at.run()
_mr = _w(at.multiselect, "adm_mem_rest")
_or = list(_mr.options) if _mr else []
chk("⚠️ «Restore these»: dos olvidadas iguales, con textos DISTINTOS (la hora del olvido)",
    len(_or) == 2 and len(set(_or)) == 2 and any("14:45" in x for x in _or) and any("17:53" in x for x in _or), _or)
_mr.select("MEM-9")
at.run()
next(b for b in at.button if b.key == "adm_mem_restaurar").click()
at.run()
_msg = [x for x in _todo(at) if "Already back" in x]
chk("el aviso del duplicado vale para una regla re-enseñada y para cualquier número",
    _msg == ["Already back in the memory (learned or taught again after it was forgotten), so left as is: 1."], _msg)
chk("...y ya no dice «learned again» ni «they are»",
    not any("learned again since" in x or "they are" in x for x in _todo(at)))
at2 = AppTest.from_string(APP, default_timeout=90)
at2.session_state["_res"] = (True, 1, 1)
at2.run()
_w(at2.checkbox, "adm_mem_ver_olv").check()
at2.run()
_w(at2.multiselect, "adm_mem_rest").select("MEM-8").select("MEM-9")
at2.run()
next(b for b in at2.button if b.key == "adm_mem_restaurar").click()
at2.run()
chk("una recuperada y otra repetida: las dos cosas, en una frase",
    any(x == "Restored: 1. Already back in the memory (learned or taught again after it was forgotten), "
             "so left as is: 1." for x in _todo(at2)), [x for x in _todo(at2) if "Restored" in x])

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
