# -*- coding: utf-8 -*-
"""v546 · LA PANTALLA DE FICHAJE, PROBADA ACCIÓN POR ACCIÓN EN PRODUCCIÓN.

Lo que salió al recorrerla con la cuenta admin (08/10/2026):

1. ⚠️ JORNADAS SOLAPADAS: «abrir la jornada a las 18:00» con una ya cerrada de 18:24 a
   18:26 se aceptaba, y esos minutos contaban DOS veces como tiempo pagado (la tarjeta
   subió a 0,51 h). «Fix the time» tampoco miraba las otras entradas. → `timeclock`
   rechaza una hora que pise otra entrada del MISMO tipo, con un mensaje que dice cuál.
2. El panel «Did you forget…» se cerraba solo tras cada paso (sin clave, Streamlit lo crea
   de nuevo cuando el aviso de arriba aparece o se va). → clave. Igual el de la IA del Home.
3. Fichar desde la pantalla no sacaba el modal del Pre-Start; desde el lateral sí. →
   «deben comportarse igual» (usuario): la pantalla ficha por `_fichar`, y «Switch» avisa.
4. El historial ponía mes/día («10/08» por el 8 de octubre). → día/mes.
5. «— cambiar a… —» en español en «Switch project».
"""
import io
import os
import sys
from datetime import datetime

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
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


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


# ─────────────────────────────────────────────────────────────────────────────
sec("1. ⚠️ Una hora que pisa otra entrada del mismo tipo se rechaza (timeclock)")
from core import timeclock as TC                                  # noqa: E402


def fila(tipo, ci, co="", usuario="u", proyecto="", pid=""):
    return {"Name": "N", "PIN": "", "Project": proyecto, "Location": "", "Clock In": ci,
            "Clock Out": co, "Hours": "", "Status": "CERRADO" if co else "ABIERTO",
            "Group": "g", "Type": tipo, "User": usuario, "ProjectID": pid}


class HojaFalsa:
    def __init__(self, filas):
        self.filas = [dict(f) for f in filas]
        self.altas, self.cambios = [], []

    def get_all_records(self, **k):
        return [dict(f) for f in self.filas]

    def append_row(self, valores, **k):
        self.altas.append(valores)

    def batch_update(self, cambios, **k):
        self.cambios.extend(cambios)


_hoja = {"ws": None}
TC._get_worksheet = lambda: (_hoja["ws"], None)
TC._now = lambda: "2026-10-08 18:30:00"
TC._invalidate_records = lambda: None
G = TC.TIPO_GENERAL
P_ = TC.TIPO_PROYECTO
CERR = fila(G, "2026-10-08 18:24:31", "2026-10-08 18:26:22")
OTRO = fila(G, "2026-10-08 17:00:00", "2026-10-08 19:00:00", usuario="otro")


def abrir(filas, tipo, ts):
    _hoja["ws"] = HojaFalsa(filas)
    r = TC.clock_in("N", "", "", "g", tipo=tipo, usuario="u", in_ts=ts)
    return r, _hoja["ws"]


r, ws = abrir([CERR, OTRO], G, datetime(2026, 10, 8, 18, 0))
chk("⚠️ abrir la jornada a las 18:00 con una cerrada 18:24-18:26 se RECHAZA (el caso de "
    "producción)", r[0] is False and not ws.altas, r)
chk("...y el mensaje dice con qué choca", "18:24" in r[1] and "18:26" in r[1], r[1])
r, ws = abrir([CERR, OTRO], G, datetime(2026, 10, 8, 18, 27))
chk("a las 18:27 (después de la cerrada) se acepta",
    r[0] is True and len(ws.altas) == 1 and ws.altas[0][4] == "2026-10-08 18:27:00", r)
r, ws = abrir([CERR], P_, datetime(2026, 10, 8, 18, 0))
chk("un tramo de OBRA dentro de la jornada no es un choque (otro tipo)", r[0] is True, r)
r, ws = abrir([OTRO], G, datetime(2026, 10, 8, 18, 0))
chk("la jornada de OTRA persona no cuenta", r[0] is True, r)
_hoja["ws"] = HojaFalsa([CERR])
r = TC.clock_in("N", "", "", "g", tipo=G, usuario="u")
chk("fichar AHORA no se toca (solo una hora pasada puede pisar)", r[0] is True, r)


def corrige(filas, campo, actual, nuevo, tipo=G):
    _hoja["ws"] = HojaFalsa(filas)
    r = TC.corregir_fichaje("g", "u", "N", tipo, campo, actual, nuevo)
    return r, _hoja["ws"]


ABIERTA = fila(G, "2026-10-08 18:00:00")
r, ws = corrige([CERR, ABIERTA], "Clock In", "2026-10-08 18:00:00", "2026-10-08 18:27:00")
chk("corregir la entrada a 18:27 (quita el solape) se aplica", r[0] is True and ws.cambios, r)
r, ws = corrige([CERR, ABIERTA], "Clock In", "2026-10-08 18:00:00", "2026-10-08 18:10:00")
chk("⚠️ corregirla a 18:10 (sigue pisando 18:24-18:26) se RECHAZA", r[0] is False
    and not ws.cambios and "18:24" in r[1], r)
SIG = fila(G, "2026-10-08 18:28:00", "2026-10-08 18:29:00")
r, ws = corrige([CERR, SIG], "Clock Out", "2026-10-08 18:26:22", "2026-10-08 18:28:30")
chk("alargar una salida hasta pisar la entrada siguiente se rechaza",
    r[0] is False and "18:28" in r[1], r)
r, ws = corrige([CERR], "Clock Out", "2026-10-08 18:26:22", "2026-10-08 18:25:00")
chk("una entrada no choca CONSIGO MISMA (corregir su propia salida)", r[0] is True, r)

# ─────────────────────────────────────────────────────────────────────────────
sec("2. Fichar desde la pantalla avisa del Pre-Start como el lateral (AppTest)")
from streamlit.testing.v1 import AppTest                          # noqa: E402

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import timeclock as TC, projects as P, roster as R, prestart as PS
from core import timeclock_ui as U
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm",
                            "grupo": "g"}
TC.is_configured = lambda: True
TC.open_sessions = lambda *a, **k: st.session_state.get("_fk_ses", {})
TC.resumen_hoy = lambda *a, **k: {"general": 0.0, "proyecto": 0.0, "sin_asignar": 0.0,
                                  "por_proyecto": {}}
TC.resumen_semana = lambda *a, **k: {"general": 0.0, "proyecto": 0.0, "dias": 0}
TC.mis_fichajes = lambda *a, **k: st.session_state.get("_fk_mios", [])
def _fp(nombre, nom, grupo, usuario, pid):
    st.session_state["_fk_fichado"] = (nom, pid)
    return True, "Clock IN Project", False
TC.fichar_proyecto = _fp
def _sw(nombre, grupo, nom, ubicacion="", usuario="", new_pid=""):
    st.session_state["_fk_switch"] = (nom, new_pid)
    return True, "Switched"
TC.switch_project = _sw
P.list_projects = lambda *a, **k: [{"ID": "PRJ-A", "Name": "Obra A", "Group": "g"},
                                   {"ID": "PRJ-B", "Name": "Obra B", "Group": "g"}]
R.is_configured = lambda: False
PS.hecho_hoy = lambda pid, g="": st.session_state.get("_fk_hecho", False)
U.render_timeclock_tab()
''' % RAIZ


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def ss(at, k, defecto=None):
    try:
        return at.session_state[k]
    except KeyError:
        return defecto


def pantalla(**kw):
    at = AppTest.from_string(GUION, default_timeout=120)
    for k, v in kw.items():
        at.session_state[k] = v
    return corre(at)


at = pantalla()
at.selectbox(key="tc_prj_sel").select("Obra A")
corre(at)
at.button(key="tc_prj_in").click()
corre(at)
chk("fichar desde el selector de la pantalla ficha con el NOMBRE de la obra",
    ss(at, "_fk_fichado") == ("Obra A", "PRJ-A"), ss(at, "_fk_fichado"))
chk("⚠️ ...y deja el aviso del Pre-Start de ESA obra (antes solo lo hacía el lateral)",
    (ss(at, "_ps_aviso") or {}).get("pid") == "PRJ-A", ss(at, "_ps_aviso"))

at = pantalla(**{"_ps_visto_PRJ-A": True})
at.selectbox(key="tc_prj_sel").select("Obra A")
corre(at)
at.button(key="tc_prj_in").click()
corre(at)
chk("si lo habías descartado antes, volver a fichar lo re-arma (igual que el lateral)",
    ss(at, "_ps_visto_PRJ-A") is None and (ss(at, "_ps_aviso") or {}).get("pid") == "PRJ-A")

at = pantalla(_fk_hecho=True)
at.selectbox(key="tc_prj_sel").select("Obra A")
corre(at)
at.button(key="tc_prj_in").click()
corre(at)
chk("con el Pre-Start ya hecho hoy no hay nada que avisar", ss(at, "_ps_aviso") is None)

_SES = {TC.TIPO_GENERAL: {"proyecto": "", "proyecto_id": "", "clock_in": "2026-10-08 18:24:31"},
        TC.TIPO_PROYECTO: {"proyecto": "Obra A", "proyecto_id": "PRJ-A",
                           "clock_in": "2026-10-08 18:25:01"}}
at = pantalla(_fk_ses=_SES)
_sel = at.selectbox(key="tc_switch")
chk("⚠️ «Switch project» en inglés (decía «— cambiar a… —»)",
    _sel.options[0] == "— switch to… —" and all("cambiar" not in o for o in _sel.options),
    _sel.options)
chk("...y no ofrece la obra en la que ya estás", "Obra A" not in _sel.options, _sel.options)
_sel.select("Obra B")
corre(at)
at.button(key="tc_switch_btn").click()
corre(at)
chk("«Switch» a otra obra avisa del Pre-Start de la NUEVA",
    ss(at, "_fk_switch") == ("Obra B", "PRJ-B")
    and (ss(at, "_ps_aviso") or {}).get("pid") == "PRJ-B", (ss(at, "_fk_switch"), ss(at, "_ps_aviso")))

# ─────────────────────────────────────────────────────────────────────────────
sec("3. El historial pone la fecha como día/mes")
_MIOS = [{"tipo": "general", "proyecto": "", "entrada": "2026-10-08 16:20:05",
          "salida": "2026-10-08 16:21:00", "horas": 0.01, "abierto": False},
         {"tipo": "general", "proyecto": "", "entrada": "2026-09-07 17:06:00",
          "salida": "2026-09-07 17:06:30", "horas": 0.0, "abierto": False}]
at = pantalla(_fk_mios=_MIOS)
_df = at.dataframe[0].value
_col = next(c for c in _df.columns if str(c) == "In")
chk("⚠️ 8 de octubre a las 16:20 → «08/10 16:20» (decía «10/08»)",
    list(_df[_col]) == ["08/10 16:20", "07/09 17:06"], list(_df[_col]))

# ─────────────────────────────────────────────────────────────────────────────
sec("4. Los desplegables con controles llevan clave (no se cierran solos)")
_tu = _fuente("core/timeclock_ui.py")
chk("«Did you forget…» con clave",
    'icon=":material/schedule_send:", key="tc_corregir")' in _tu)
chk("la lectura de la IA del Home con clave",
    "t(\":material/forum: The assistant's read (AI)\"), key=\"cpx_lectura_ia\")"
    in _fuente("core/projects_ui.py"))
chk("ningún botón de fichar de la pantalla llama a `fichar_proyecto` por su cuenta "
    "(todos por `_fichar`)", _tu.count("timeclock.fichar_proyecto(") == 1)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
