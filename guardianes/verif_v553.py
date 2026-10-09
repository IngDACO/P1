# -*- coding: utf-8 -*-
"""v553 · LA PÁGINA BAJA (O SUBE) HASTA LA FICHA RECIÉN ABIERTA, Y EL RADAR SE LEE A LA IZQUIERDA.

Visto verificando v552 en producción:
  1. Con la línea del Radar al fondo de la página, la ficha salía bajo ella pero cortada
     (114 px fuera). En una mini-app 1.64 con 10 personas salía ENTERA por debajo de la
     pantalla (777-1000 con 768 de alto). Y con un NOMBRE del tablero pasaba lo mismo hacia
     arriba: la ficha se pintaba en -472..-259, invisible.
     → Al ABRIR una ficha (una línea del Radar o un nombre del tablero) se encola UNA vez
     (`_fp_ir`) un script que, cuando la pasada termina, la trae a la vista con
     `scrollIntoView({block:'nearest'})`: lo justo, y nada si ya se ve. Medido en la
     mini-app: 381 → 603 (Radar) y 667 → 195 (tablero), la ficha entera; otra pasada no mueve.
  2. El texto de las líneas del Radar salía CENTRADO: en 1.64 lo centran el `div` y el
     `span` interiores del botón. Con `flex-start` en los dos: 13 px del borde (antes 84-99).

El recuadro del script va FUERA del flujo, él y su `stLayoutWrapper` (medido: con solo el
contenedor fuera, la ficha medía 223 px en vez de 213: el envoltorio de 0 px seguía
recibiendo el hueco de 9,6 px).

AppTest no ejecuta JavaScript: aquí se comprueba que el script ESTÁ cuando debe (y solo
entonces) y qué hace; que se mueve la vista se midió en el navegador.
"""
import io
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


RU_SRC = io.open(os.path.join("core", "roster_ui.py"), encoding="utf-8").read()

print("1. Estático")
_i = RU_SRC.find("def _radar_personal(")
_rad = RU_SRC[_i:RU_SRC.find("\ndef ", _i + 10)]
chk("se encontró `_radar_personal` (no es un paso en vacío)", "radar_" in _rad)
chk("⚠️ el texto del Radar se alinea también en el `div` y el `span` interiores",
    "button > div," in _rad and "button > div > span" in _rad
    and "justify-content:flex-start!important" in _rad)
_j = RU_SRC.find("def _ficha_rapida(")
_fic = RU_SRC[_j:RU_SRC.find("\ndef ", _j + 10)]
chk("se encontró `_ficha_rapida`", "fp_close" in _fic)
chk("la ficha lleva la clave que busca el script (`fp_card`)",
    'st.container(border=True, key="fp_card")' in _fic)
chk("el script se consume UNA vez (`pop` de `_fp_ir`)", 'st.session_state.pop("_fp_ir", False)' in _fic)
chk("…y va FUERA del flujo, él y su envoltorio (`stLayoutWrapper:has(> .st-key-fp_ir)`)",
    '.st-key-fp_ir,[data-testid=\\"stLayoutWrapper\\"]:has(> ' in _fic
    and "position:absolute!important" in _fic)

print("\n2. Con clics reales (AppTest)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import json
import streamlit as st
from core import roster as R, roster_ui as RU, auth, projects as P, credentials as C
from core import timeclock as TC

LUNES = R.lunes_de()
def _c(*asigs):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": ""}
ESTA = {"ana": {"mar": _c("PRJ-1", "PRJ-2")}, "beto": {"jue": _c("PRJ-9")}}
FILAS = [{"Group": "G", "Week": LUNES.isoformat(), "User": u, "DataJSON": json.dumps(d)}
         for u, d in ESTA.items()]
R._roster_records = lambda: FILAS
R._trab_records = lambda: []
R.is_configured = lambda: True
R._ws_roster = lambda: None
R.guardar_persona = lambda *a, **k: (True, "ok")
R.asignaciones_dia = lambda g, u: []
TC.is_configured = lambda: False
USERS = [{"User": u, "Name": n, "Role": "field", "Group": "G", "Email": u + "@x.test"}
         for u, n in (("ana", "Ana"), ("beto", "Beto"))]
auth.list_users = lambda *a, **k: USERS
auth.get_user = lambda u: next((x for x in USERS if x["User"] == u), None)
PRJ = [{"ID": "PRJ-1", "Name": "Torre", "Group": "G", "Status": "In progress"},
       {"ID": "PRJ-2", "Name": "Redfen", "Group": "G", "Status": "In progress"},
       {"ID": "PRJ-9", "Name": "Agecare", "Group": "G", "Status": "In progress"}]
P.list_projects = lambda *a, **k: PRJ
P.get_project = lambda pid: dict(next((p for p in PRJ if p["ID"] == pid), {}),
                                 RequiredCerts=("White Card" if pid == "PRJ-9" else ""))
P.add_field_user = lambda *a, **k: None
C.compliance = lambda usr, certs: {"cumple": False, "por_tipo": {"White Card": "vencido"}}
C.list_for = lambda u: []
C.status = lambda d: "vigente"
RU.render_planificacion("G")
'''


def scripts(at):
    """Los `srcdoc` de los recuadros que hay DENTRO del contenedor `fp_ir`."""
    out = []

    def _rec(nodo, dentro):
        for h in getattr(nodo, "children", {}).values():
            _d = dentro or (getattr(h, "key", None) == "fp_ir")
            if getattr(h, "type", "") == "iframe" and _d:
                out.append(str(h.proto.srcdoc))
            _rec(h, _d)
    _rec(at.main, False)
    return out


def boton(at, k):
    b = [x for x in at.button if x.key == k]
    return b[0] if b else None


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("el Panel se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
boton(at, "ptool_radar").click()
at.run()
chk("con el Radar abierto y sin ficha, no hay script", scripts(at) == [], len(scripts(at)))

boton(at, "radar_ce_0").click()
at.run()
_s = scripts(at)
chk("⚠️ abrir la ficha desde el Radar pinta el script UNA vez", len(_s) == 1, len(_s))
_js = _s[0] if _s else ""
chk("…que busca la ficha por su clave", ".st-key-fp_card" in _js, _js[:120])
chk("…la trae con `scrollIntoView` y `block:'nearest'` (lo justo, nada si ya se ve)",
    "scrollIntoView" in _js and "block:'nearest'" in _js, _js[:200])
chk("…y espera a que la pasada termine (`data-test-script-state`)",
    "data-test-script-state" in _js and "running" in _js, _js[:200])
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])

at.run()                                            # otra pasada, sin abrir nada
chk("⚠️ en la pasada siguiente el script YA no está (una vez por apertura)", scripts(at) == [],
    len(scripts(at)))
chk("…pero la ficha sigue abierta", boton(at, "fp_close") is not None)

boton(at, "radar_ce_0").click()                     # la misma línea: CIERRA
at.run()
chk("cerrar la ficha no pinta script (ni ficha)", scripts(at) == [] and boton(at, "fp_close") is None)

_pnm = [b for b in at.button if (b.key or "").startswith("pnm_")]
chk("hay nombres en el tablero (no es un paso en vacío)", len(_pnm) == 2)
_pnm[1].click()                                     # el nombre de Beto en el tablero
at.run()
chk("⚠️ abrir la ficha desde un NOMBRE del tablero también pinta el script",
    len(scripts(at)) == 1, len(scripts(at)))
at.run()
chk("…y tampoco se repite", scripts(at) == [])

boton(at, "fp_close").click()
at.run()
chk("el ✕ cierra sin script", scripts(at) == [] and boton(at, "fp_close") is None)
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
