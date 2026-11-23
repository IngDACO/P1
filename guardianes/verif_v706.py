# -*- coding: utf-8 -*-
"""v706 · lo visto con la sesión de campo al cerrar el ciclo 7 (decisión del usuario, 24/11: «Sí, los dos»).

V4  al reanudar, al campo le llegaba «the office will put your days on the board» aunque la pausa dejó sus días en
    el tablero (C7: 8 días). Ahora a quien sigue en él desde hoy: «your days on the board stay as they were»; a quien
    no, lo de antes.
V5  «1 unsaved ticks» → «1 unsaved tick» (en la lista de etapas y en el aviso de otra pestaña).

Sin red ni escrituras: AppTest con los sustitutos guardados y devueltos (trampa 48).
"""
import ast
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


from streamlit.testing.v1 import AppTest                                      # noqa: E402
from core import projects_ui as PU, projects as P, alerts, notify, auth, roster   # noqa: E402

_G = {(m, n): getattr(m, n) for m, n in ((P, "update_project"), (alerts, "notify_change"),
                                          (notify, "notify_assignment"), (notify, "notify_induction"),
                                          (auth, "list_users"), (PU, "_autoagenda"), (roster, "dias_desde"))}

RE = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, alerts, notify, auth, roster
P.update_project = lambda pid, campos: None
alerts.notify_change = lambda pid, g, txt, quien, dest, nombre: st.session_state.setdefault("_AV", []).append(
    (txt, list(dest)))
notify.notify_assignment = lambda u, info: {}
notify.notify_induction = lambda *a, **k: None
auth.list_users = lambda g=None: [{"User": "campo000", "Name": "hjg,ujgjg"}, {"User": "helper1", "Name": "helper 1"}]
PU._autoagenda = lambda *a, **k: None
roster.dias_desde = lambda g, pid, desde: dict(st.session_state["_TAB"])
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G"})
if st.session_state.get("_GUARDAR"):
    st.session_state["_GUARDAR"] = False
    PU._guardar_datos_obra("PRJ-T", "G", {"ID": "PRJ-T", "ManualStatus": st.session_state["_PREV"]},
                           {"ManualStatus": ""}, {"nombre": "C7", "cliente": "", "ubic": "", "f_ini": "2026-11-23",
                                                   "f_fin": "2027-01-06", "ind": "",
                                                   "asignados": ["campo000", "helper1"],
                                                   "actuales": ["campo000", "helper1"]})
'''


def reanuda(tab, prev="On hold"):
    a = AppTest.from_string(RE, default_timeout=60)
    a.session_state["_GUARDAR"] = True
    a.session_state["_TAB"] = tab
    a.session_state["_PREV"] = prev
    a.run()
    return a, (list(a.session_state["_AV"]) if "_AV" in a.session_state else [])


QUEDAN = "This job has restarted. You are back on it: your days on the board stay as they were."
PONDRA = "This job has restarted. You are back on it: the office will put your days on the board."
try:
    print("A. V4: lo que le llega al campo al reanudar")
    a, av = reanuda({"campo000": 8})
    chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
    chk("campo000, con 8 días en el tablero: «your days on the board stay as they were»",
        (QUEDAN, ["campo000"]) in av, av)
    chk("helper1, sin días: «the office will put your days on the board»", (PONDRA, ["helper1"]) in av, av)
    chk("…y nadie recibe los dos", len(av) == 2, av)
    a, av = reanuda({})
    chk("tablero vacío: uno solo, a los dos, «the office will put…»", av == [(PONDRA, ["campo000", "helper1"])], av)
    a, av = reanuda({"campo000": 8, "helper1": 3})
    chk("los dos en el tablero: uno solo, «stay as they were»", av == [(QUEDAN, ["campo000", "helper1"])], av)
    a, av = reanuda({"campo000": 8}, prev="")
    chk("guardar sin reanudar: el aviso de siempre, sin mirar el tablero",
        av == [("The project details were updated.", ["campo000", "helper1"])], av)
finally:
    for (m, n), f in _G.items():
        setattr(m, n, f)

print("\nB. V5: «1 unsaved tick», en singular")
for rel, fn, cond, sing in (("core/stage_progress_ui.py", "render", "len(_pend) == 1", "**1 unsaved tick.**"),
                            ("core/projects_ui.py", "_mis_proyectos_obra", "_npend == 1",
                             "**1 unsaved tick in «Progress».**")):
    src = open(os.path.join(RAIZ, rel), encoding="utf-8").read()
    ifs = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.IfExp) and ast.unparse(n.test) == cond]
    _ok = bool(ifs) and sing in ast.unparse(ifs[0].body) and "{n} unsaved ticks" in ast.unparse(ifs[0].orelse)
    chk(f"{rel}: con una, «{sing.strip('*')}»; con más, «{{n}} unsaved ticks»", _ok,
        [ast.unparse(x)[:200] for x in ifs])

print()
print("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}")
sys.exit(1 if FALLOS else 0)
