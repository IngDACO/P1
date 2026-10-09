# -*- coding: utf-8 -*-
"""v552 · LA FICHA ABIERTA DESDE EL RADAR SE VE DONDE SE TOCÓ.

Verificando v551 en producción: tocar una línea del Radar abría la ficha rápida ARRIBA del
Panel. Con la vista bajada hasta el Radar (que es donde se toca), la ficha quedaba 373 px
por encima de la pantalla y el clic parecía no hacer nada. Ahora:
  - abierta desde una línea → se pinta DEBAJO de esa línea (`_panel_ficha_en` = su key);
  - la misma línea otra vez → se cierra;
  - si su línea ya no está (la lista cambió) → al final del Radar, nunca en ninguna parte;
  - si se cierra el Radar, o se toca un nombre del tablero → arriba, como siempre.

AppTest con la ficha REAL (su ✕ y su «See full record» son botones con key) y datos
inventados; ninguna hoja se toca. La POSICIÓN se mide recorriendo el árbol en orden.
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
_i = RU_SRC.find('if cB.button("✕", key="fp_close"):')
chk("se encontró el ✕ de la ficha (no es un paso en vacío)", _i > 0)
chk("el ✕ olvida también de dónde se abrió (`_panel_ficha_en`)",
    'st.session_state.pop("_panel_ficha_en", None)' in RU_SRC[_i:_i + 300])

print("\n2. Con clics reales (AppTest)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import json, datetime
import streamlit as st
from core import roster as R, roster_ui as RU, auth, projects as P, credentials as C
from core import timeclock as TC

LUNES = R.lunes_de()
def _c(*asigs):
    return {"items": [{"a": a, "i": "07:00", "f": "15:30"} for a in asigs], "nota": ""}
ESTA = {"ana": {"mar": _c("PRJ-1", "PRJ-2")}, "beto": {"jue": _c("PRJ-9")}}
FILAS = [{"Group": "G", "Week": LUNES.isoformat(), "User": u, "DataJSON": json.dumps(d)}
         for u, d in ESTA.items()]
if st.session_state.get("_VACIO"):                  # una semana sin choques ni certificados
    FILAS = []
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


def orden(at):
    """Botones (B:key) y nombres de ficha (F:texto) en el orden en que se pintan."""
    out = []

    def _rec(nodo):
        for h in getattr(nodo, "children", {}).values():
            tipo = getattr(h, "type", "")
            if tipo == "button":
                out.append("B:" + (h.key or ""))
            elif tipo == "markdown" and str(h.value).startswith("**") and " · field" in str(h.value):
                out.append("F:" + str(h.value).split("**")[1])
            _rec(h)
    _rec(at.main)
    return out


def tras(sec, clave):
    """Lo primero que se pinta después del botón `clave` (sin contar el propio botón)."""
    try:
        i = sec.index(clave)
    except ValueError:
        return None
    return sec[i + 1] if i + 1 < len(sec) else None


def boton(at, k):
    b = [x for x in at.button if x.key == k]
    return b[0] if b else None


def fichas(sec):
    return [x for x in sec if x.startswith("F:")]


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("el Panel se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
boton(at, "ptool_radar").click()
at.run()
s = orden(at)
chk("el Radar está abierto con sus 2 líneas (no es un paso en vacío)",
    "B:radar_ch_0" in s and "B:radar_ce_0" in s, [x for x in s if "radar" in x])
chk("la sonda VE una ficha cuando la hay: todavía ninguna", fichas(s) == [], fichas(s))

boton(at, "radar_ce_0").click()
at.run()
s = orden(at)
chk("sin excepción (la ficha no se pinta dos veces: claves únicas)", not at.exception,
    [e.value for e in at.exception][:1])
chk("⚠️ la ficha de BETO sale justo DEBAJO de su línea", tras(s, "B:radar_ce_0") == "F:Beto",
    s[s.index("B:radar_ce_0"):][:4] if "B:radar_ce_0" in s else s)
chk("…y solo una vez (no también arriba del Panel)", fichas(s) == ["F:Beto"], fichas(s))
chk("…arriba del Panel no hay ficha (antes de «Copy previous week»)",
    "B:ros_copy" in s and not any(x.startswith("F:") for x in s[:s.index("B:ros_copy")]))

boton(at, "radar_ch_0").click()
at.run()
s = orden(at)
chk("otra línea: la ficha de ANA bajo la suya, la de Beto se va",
    tras(s, "B:radar_ch_0") == "F:Ana" and fichas(s) == ["F:Ana"], fichas(s))

boton(at, "radar_ch_0").click()
at.run()
s = orden(at)
chk("⚠️ la MISMA línea otra vez cierra la ficha", fichas(s) == [] and
    "_panel_ficha" not in at.session_state, fichas(s))

boton(at, "radar_ce_0").click()
at.run()
boton(at, "fp_close").click()
at.run()
s = orden(at)
chk("el ✕ de la ficha la cierra y olvida de dónde venía",
    fichas(s) == [] and "_panel_ficha_en" not in at.session_state, fichas(s))

boton(at, "radar_ce_0").click()
at.run()
boton(at, "ptool_radar").click()                    # cerrar el Radar con la ficha abierta
at.run()
s = orden(at)
chk("con el Radar cerrado, la ficha vuelve ARRIBA (no se pierde)",
    fichas(s) == ["F:Beto"] and s.index("F:Beto") < s.index("B:ros_copy"), fichas(s))

boton(at, "ptool_radar").click()
at.run()
_pnm = [b for b in at.button if (b.key or "").startswith("pnm_")]
chk("hay nombres en el tablero", len(_pnm) == 2)
_pnm[0].click()                                     # el nombre de Ana en el tablero
at.run()
s = orden(at)
chk("⚠️ un nombre del TABLERO abre la ficha arriba aunque el Radar esté abierto",
    fichas(s) == ["F:Ana"] and s.index("F:Ana") < s.index("B:ros_copy"), fichas(s))

# La lista cambió entre pasadas: la key de la línea ya es de OTRA persona, o ya no existe.
# ⚠️ Con una línea que NO sea la última: bajo la última, «debajo» y «al final» coinciden.
at.session_state["_panel_ficha"] = "beto"
at.session_state["_panel_ficha_en"] = "radar_ch_0"   # la línea ch_0 es de ANA
at.run()
s = orden(at)
_ult = max(i for i, x in enumerate(s) if x.startswith("B:radar_"))
chk("⚠️ si la línea ya es de otra persona, NO se pinta bajo ella",
    tras(s, "B:radar_ch_0") != "F:Beto", s[s.index("B:radar_ch_0"):][:3])
chk("…sino al final del Radar (nunca en ninguna parte)",
    fichas(s) == ["F:Beto"] and s.index("F:Beto") > _ult, fichas(s))
at.session_state["_panel_ficha"] = "beto"
at.session_state["_panel_ficha_en"] = "radar_ce_9"   # una línea que ya no existe
at.run()
s = orden(at)
chk("si la línea ya no existe, también al final del Radar",
    fichas(s) == ["F:Beto"] and s.index("F:Beto") > _ult, fichas(s))
at.session_state["_VACIO"] = True                   # el Radar se queda SIN líneas
at.run()
s = orden(at)
chk("con el Radar vacío («No shift clashes…») no hay líneas (no es un paso en vacío)",
    not any(x.startswith("B:radar_") for x in s)
    and any("No shift clashes" in m.value for m in at.success), [x for x in s if "radar" in x])
chk("⚠️ …y la ficha abierta sigue viéndose (no se queda en ninguna parte)",
    fichas(s) == ["F:Beto"], fichas(s))
at.session_state["_VACIO"] = False
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
