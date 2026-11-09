# -*- coding: utf-8 -*-
"""v618 · LO VISTO VERIFICANDO v617 EN PRODUCCIÓN (01/11/2026, «Dale»): «Tap a receipt to see the
photo.» salía también cuando ningún recibo tenía foto, y un recibo sin foto no se puede tocar.
Sin red ni hoja real.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


from streamlit.testing.v1 import AppTest                          # noqa: E402

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import projects_ui as PU, expenses as E
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"items": [
    {"ID": "G-1", "Date": "2026-10-28", "Category": "Materials", "Amount": "12.5", "Supplier": "S1",
     "Description": "", "DriveID": "__D1__", "File": "", "CreatedBy": "campo000"},
    {"ID": "G-2", "Date": "2026-10-27", "Category": "Fuel", "Amount": "120", "Supplier": "S2",
     "Description": "", "DriveID": "__D2__", "File": "", "CreatedBy": "campo000"}]}
PU.render_expenses("PRJ-1", "cliente1", can_delete=False, key_prefix="fld", solo_de="campo000")
'''
_TXT = "Tap a receipt to see the photo."


def caps(d1, d2):
    at = AppTest.from_string(APP.replace("__D1__", d1).replace("__D2__", d2), default_timeout=60).run()
    chk("se pinta sin excepción (%r, %r)" % (d1, d2), not at.exception, [e.value for e in at.exception][:1])
    return [c.value for c in at.caption]


print("1. La frase, solo si hay algo que tocar")
_c = caps("", "")
chk("⚠️ ningún recibo con foto: la frase NO sale", _TXT not in _c, _c)
# ⚠️ v665 · CADUCADO a propósito: un recibo sin comprobante se marca «no receipt» en naranja (era «no file» en gris)
chk("…y los recibos sí, con su «no receipt» (el barrido no vació la lista)",
    sum("no receipt" in c for c in _c) == 2, _c)
_c = caps("abc", "")
chk("uno con foto y otro sin ella: la frase SALE", _TXT in _c, _c)
_c = caps("abc", "def")
chk("todos con foto: la frase SALE", _TXT in _c, _c)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
