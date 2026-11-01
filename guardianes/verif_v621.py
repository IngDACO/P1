# -*- coding: utf-8 -*-
"""v621 · RECORRIDO DEL CAMPO: TIMECLOCK (01/11/2026, «Dale con todo»).

  (1) ⚠️ Un olvido de ayer se cerraba «ahora»: «Close workday and project» apuntó 33,39 h sin avisar
      (medido en producción con datos de prueba) → el motor lo niega y la pantalla solo ofrece
      cerrarlo con la hora real;
  (2) ⚠️ «Management sees the group's hours summary, not each person's detail» era falso;
  (3) ⚠️ «Close forgotten session» decía cerrado aunque fallara, y `cerrar_jornada` cerraba la jornada
      aunque no pudiera cerrar la obra, que seguía sumando sola;
  (4) la baja, solo si no se ha trabajado hoy; (5) el historial cabe en el móvil y la salida lleva su
  día; (6) los avisos dicen dónde; (7) DD/MM/YYYY en el olvido; (8) textos traducibles y el nombre
  de la obra escapado; (9) la pregunta de una sola opción, fuera; (10) las cifras, activas;
  (11) el lateral, con una sola obra, a un toque.
Sin red ni hoja real.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
from core import timeclock as T                                   # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


HOY = "2026-11-01"
T._now = lambda: HOY + " 16:00:00"
T._invalidate_records = lambda: None


class Hoja:
    """La pestaña de fichajes, en memoria. `falla` = qué tipo no se deja cerrar."""

    def __init__(self, filas, falla=None):
        self.filas, self.escrito, self.falla = filas, [], falla

    def get_all_records(self, **k):
        return self.filas

    def append_row(self, fila, **k):
        self.escrito.append(("alta", fila))

    def batch_update(self, cambios, **k):
        n = int(cambios[0]["range"].split(":")[0][1:]) - 2
        if self.falla and self.filas[n].get("Type") == self.falla:
            raise RuntimeError("429")
        self.escrito.append(("cierre", cambios))
        self.filas[n]["Status"] = "CERRADO"


def fila(tipo, ci, proy=""):
    return {"Name": "installer CI 1", "PIN": "", "Project": proy, "Location": "", "Clock In": ci,
            "Clock Out": "", "Hours": "", "Status": "ABIERTO", "Group": "cliente1", "Type": tipo,
            "User": "installer", "ProjectID": "PRJ-1" if proy else ""}


def usa(filas, falla=None):
    h = Hoja(filas, falla)
    T._get_worksheet = lambda: (h, None)
    T._cached_records = lambda: h.filas
    return h


_G, _P = T.TIPO_GENERAL, T.TIPO_PROYECTO
_A = ("installer CI 1", "cliente1")

sec("1. ⚠️ El motor no cierra un olvido «ahora»")
h = usa([fila(_G, "2026-10-31 07:00:00"), fila(_P, "2026-10-31 07:05:00", "Bondi")])
ok, m = T.clock_out(*_A, tipo=_P, usuario="installer")
chk("«Leave the project» sobre una obra de ayer: NEGADO y sin escribir", not ok and not h.escrito, (ok, m))
chk("…y dice qué hacer", "previous day" in m, m)
ok, m = T.cerrar_jornada(*_A, usuario="installer")
chk("⚠️ «Close the workday» (lo que apuntó 33,39 h): NEGADO y sin escribir", not ok and not h.escrito, (ok, m))
ok, m = T.switch_project(*_A, "Otra", usuario="installer", new_pid="PRJ-2")
chk("cambiar de obra, tampoco", not ok and not h.escrito, (ok, m))
ok, m = T.clock_out(*_A, tipo=_P, usuario="installer", out_ts="2026-10-31 15:00:00")
chk("CON la hora real, se cierra", ok and len(h.escrito) == 1, (ok, m))
chk("…con las horas de verdad (7,92)", h.escrito[0][1][0]["values"][0][1] == "7.92", h.escrito)

sec("2. ⚠️ Con un olvido abierto no se ficha")
h = usa([fila(_G, "2026-10-31 07:00:00")])
ok, m = T.clock_in("installer CI 1", "Bondi", "", "cliente1", tipo=_P, usuario="installer", proyecto_id="PRJ-1")
chk("una obra de hoy colgada de la jornada de ayer: NEGADO", not ok and not h.escrito and "previous day" in m, (ok, m))
ok, m, auto = T.fichar_proyecto("installer CI 1", "Bondi", "cliente1", "installer", "PRJ-1")
chk("`fichar_proyecto` tampoco", not ok and not h.escrito and not auto, (ok, m, auto))
h = usa([{**fila(_G, "2026-10-31 07:00:00"), "User": "otro"}])
ok, m = T.clock_in("installer CI 1", "", "", "cliente1", tipo=_G, usuario="installer")
chk("el olvido de OTRA persona no te frena", ok, (ok, m))
h = usa([fila(_G, HOY + " 07:00:00")])
ok, m = T.clock_in("installer CI 1", "Bondi", "", "cliente1", tipo=_P, usuario="installer", proyecto_id="PRJ-1")
chk("con la jornada de HOY abierta sí se ficha", ok, (ok, m))

sec("3. `olvidos`")
_s = {_G: {"clock_in": "2026-10-31 07:00:00"}, _P: {"clock_in": HOY + " 07:00:00"}}
chk("distingue la de ayer de la de hoy", T.olvidos(_s) == {_G: _s[_G]}, T.olvidos(_s))
chk("una hora ilegible no bloquea a nadie", T.olvidos({_G: {"clock_in": "ayer"}}) == {})
chk("sin sesiones, nada", T.olvidos({_G: None, _P: None}) == {})

sec("4. ⚠️ Cerrar la jornada no deja la obra sumando")
h = usa([fila(_G, HOY + " 07:00:00"), fila(_P, HOY + " 07:05:00", "Bondi")], falla=_P)
ok, m = T.cerrar_jornada(*_A, usuario="installer")
chk("si la obra no se pudo cerrar, la jornada TAMPOCO", not ok and h.filas[0]["Status"] == "ABIERTO", (ok, m))
h = usa([fila(_G, HOY + " 07:00:00"), fila(_P, HOY + " 07:05:00", "Bondi")])
ok, m = T.cerrar_jornada(*_A, usuario="installer")
chk("sin fallos, se cierran las dos", ok and {f["Status"] for f in h.filas} == {"CERRADO"}, (ok, m))

sec("5. Los avisos dicen dónde")
h = usa([])
ok, m = T.clock_in("installer CI 1", "", "", "cliente1", tipo=_G, usuario="installer")
chk("abrir la jornada", "Workday opened at" in m and "Clock IN" not in m, m)
ok, m = T.clock_in("installer CI 1", "Bondi *2*", "", "cliente1", tipo=_P, usuario="installer", proyecto_id="PRJ-1")
chk("fichar dice a qué obra, y el nombre va escapado", r"Clocked in to Bondi \*2\* at" in m, m)
h = usa([fila(_P, HOY + " 15:00:00", "Bondi")])
ok, m = T.clock_out(*_A, tipo=_P, usuario="installer")
chk("dejar una obra NO se dice como cerrar el día", "Left Bondi at" in m and "Clock OUT" not in m and "1.0 h" in m, m)
h = usa([fila(_G, HOY + " 15:00:00")])
ok, m = T.clock_out(*_A, tipo=_G, usuario="installer")
chk("cerrar el día", "Workday closed at" in m and "1.0 h" in m, m)

from streamlit.testing.v1 import AppTest                           # noqa: E402

GUION = r'''
import sys
from datetime import date, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import timeclock as T, timeclock_ui as U, flash, prestart, clock, correcciones as C
st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
E = st.session_state["_esc"]
T.is_configured = lambda: True
T._now = lambda: "2026-11-01 16:00:00"
clock.now = lambda *a: datetime(2026, 11, 1, 16, 0)
clock.today = lambda *a: date(2026, 11, 1)
T.open_sessions = lambda *a, **k: E["sess"]
T.resumen_hoy = lambda *a, **k: E["hoy"]
T.resumen_semana = lambda *a, **k: {"general": 8.0, "proyecto": 7.0, "dias": 1}
T.mis_fichajes = lambda *a, **k: E["mios"]
def _out(*a, **k):
    st.session_state.setdefault("_cierres", []).append(k.get("out_ts"))
    return E.get("out", (True, "ok"))
T.clock_out = _out
C.registrar = lambda *a, **k: None
prestart.hecho_hoy = lambda *a, **k: True
prestart.pendiente_de_firma = lambda *a, **k: {}
U._proyectos_para = lambda rol, u, g: (E["proys"], True)
from core import roster
roster.is_configured = lambda: False
flash.mostrar()
with st.sidebar:
    U.render_sidebar_chrono()
U.render_timeclock_tab()
'''

_OBRA = {"ID": "PRJ-1", "Name": "Bondi <b>*2*</b>", "Group": "cliente1"}
_HOY0 = {"general": 0.0, "proyecto": 0.0, "sin_asignar": 0.0, "por_proyecto": {}}
_HOY8 = {"general": 8.0, "proyecto": 7.0, "sin_asignar": 1.0, "por_proyecto": {"Bondi <b>*2*</b>": 7.0}}
_OLV = {_G: {"clock_in": "2026-10-31 07:00:00", "proyecto": "", "proyecto_id": ""},
        _P: {"clock_in": "2026-10-31 07:05:00", "proyecto": "Bondi *2*", "proyecto_id": "PRJ-1"}}
_NADA = {_G: None, _P: None}
_FICHA = {_G: {"clock_in": HOY + " 07:00:00", "proyecto": "", "proyecto_id": ""},
          _P: {"clock_in": HOY + " 07:05:00", "proyecto": "Bondi <b>*2*</b>", "proyecto_id": "PRJ-1"}}
_M1 = {"tipo": _P, "proyecto": "Bondi", "entrada": "2026-10-31 07:05:00", "salida": HOY + " 01:30:00",
       "horas": 18.42, "abierto": False}
_M2 = {"tipo": _G, "proyecto": "", "entrada": HOY + " 07:00:00", "salida": HOY + " 15:00:00",
       "horas": 8.0, "abierto": False}
_M3 = {"tipo": _P, "proyecto": "Bondi", "entrada": HOY + " 15:10:00", "salida": "", "horas": 0.0,
       "abierto": True}


def pinta(sess, hoy=None, mios=None, proys=None, out=None):
    at = AppTest.from_string(GUION, default_timeclock=None) if False else AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_esc"] = {"sess": sess, "hoy": hoy or _HOY0, "mios": mios or [],
                                "proys": [_OBRA] if proys is None else proys, "out": out or (True, "ok")}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def claves(at):
    return {b.key for b in at.button}


def textos(at):
    return " ".join([m.value for m in at.markdown] + [c.value for c in at.caption]
                    + [w.value for w in at.warning])


sec("6. ⚠️ La pantalla con un olvido: solo se puede cerrar con la hora real")
at = pinta(_OLV)
_c = claves(at)
chk("ofrece cerrarlo con la hora", "olv_btn" in _c, sorted(_c))
for k, q in (("tc_gen_out", "«Close the workday»"), ("tc_prj_out", "«Leave the project»"),
             ("sb_tc_gen_out", "el cierre del lateral (el de las 33,39 h)"),
             ("sb_tc_prj_out", "«Leave the project» del lateral")):
    chk("⚠️ %s NO está" % q, k not in _c, sorted(_c))
chk("ni las tarjetas (enseñarían las horas de la noche)", not any(k.startswith("cpxkpi_tc") for k in _c))
chk("el lateral lleva a cerrarlo, sin cronómetro", "sb_tc_olvido" in _c)
_t = textos(at)
chk("⚠️ la fecha en DD/MM/YYYY (salía «2026-10-31 07:00:00»)", "31/10/2026 07:00" in _t and "2026-10-31" not in _t, _t[:300])
chk("el nombre de la obra, escapado", r"Bondi \*2\*" in _t, _t[:300])
chk("el compromiso de privacidad sigue ahí", "Other workers cannot see" in _t)

sec("7. ⚠️ «Close forgotten session» dice la verdad")
at = pinta(_OLV, out=(False, "Error updating the timeclock entry"))
at.button(key="olv_btn").click().run()
chk("el botón llamó con la hora real, no «ahora»", all(at.session_state["_cierres"]), at.session_state["_cierres"])
chk("⚠️ si falla, lo dice", any("Error updating" in e.value for e in at.error), [e.value for e in at.error])
chk("…y no dice que cerró", not any("Session closed" in s.value for s in at.success), [s.value for s in at.success])
at = pinta(_OLV)
at.button(key="olv_btn").click().run()
chk("si va bien, dice que cerró", any("Session closed" in s.value for s in at.success), [s.value for s in at.success])
at = pinta(_OLV)
at.date_input(key="olv_d").set_value(__import__("datetime").date(2026, 10, 31))
at.time_input(key="olv_t").set_value(__import__("datetime").time(7, 2)).run()
chk("⚠️ una hora ANTES de la entrada a la obra no se acepta (daría horas negativas)",
    at.button(key="olv_btn").disabled is True)

sec("8. La pantalla de todos los días")
at = pinta(_NADA)
chk("sin fichar y sin horas hoy, la baja está", "tc_baja" in claves(at))
at = pinta(_NADA, hoy=_HOY8)
chk("⚠️ con la jornada ya trabajada, la baja NO", "tc_baja" not in claves(at))
at = pinta(_FICHA, hoy=_HOY8, mios=[_M3, _M2, _M1])
_c = claves(at)
chk("hoy no hay olvido: los cierres están", {"tc_gen_out", "tc_prj_out", "sb_tc_gen_out"} <= _c, sorted(_c))
_h = " ".join(m.value for m in at.markdown)
chk("⚠️ el nombre, escapado en la franja", "Bondi &lt;b&gt;*2*&lt;/b&gt; · since" in _h, _h[:400])
chk("⚠️ …y en las barras", "text-overflow:ellipsis;\">Bondi &lt;b&gt;" in _h, _h[:400])
from core.maps import literal_md                                   # noqa: E402
_esc = literal_md("Bondi <b>*2*</b>")
chk("«You are on» pasa por `t()` y el nombre va escapado", ("You are on **%s**" % _esc) in _h and r"\*2\*" in _esc,
    (_esc, _h[-300:]))

sec("9. Las cifras llevan a lo que cuentan")
for k in ("jorn", "proy", "sina", "sem"):
    chk("«%s» es un botón" % k, ("cpxkpi_tc_%s" % k) in _c, sorted(_c))
_exp = [e for e in list(at.expander) + list(at.status) if "latest time entries" in e.label]
chk("el historial empieza cerrado", _exp and not _exp[0].proto.expanded, [e.label for e in _exp])
at.button(key="cpxkpi_tc_sem").click().run()
_exp = [e for e in list(at.expander) + list(at.status) if "latest time entries" in e.label]
chk("⚠️ tocar una cifra abre el historial", _exp and _exp[0].proto.expanded, [e.label for e in _exp])

sec("10. El historial cabe en el móvil")
from core import timeclock_ui as U                                 # noqa: E402
f1, f2, f3 = U._fila_hist(_M1), U._fila_hist(_M2), U._fila_hist(_M3)
chk("Día, Hora y Horas van DELANTE de la obra", list(f1) == ["Day", "Time", "Hours", "Entry"], list(f1))
chk("⚠️ una salida de otro día lleva su día", f1["Time"] == "07:05 → 01/11 01:30", f1)
chk("una salida del mismo día, no", f2["Time"] == "07:00 → 15:00", f2)
chk("una abierta dice «in progress» y sus horas no son un 0", f3["Time"] == "15:10 → in progress" and f3["Hours"] == "—", f3)
chk("la jornada se nombra", f2["Entry"] == "Workday", f2)

sec("11. La corrección no pregunta lo que no hay que preguntar")
_cerr = {**_M2, "tipo": _G}


def elegir(at, texto):
    s = at.selectbox(key="cor_sel")
    s.set_value(next(o for o in s.options if texto in o)).run()
    return at


_MIOS_HOY = [_M2, _M3]
at = pinta(_NADA, mios=_MIOS_HOY)
elegir(at, "open")
chk("⚠️ una entrada abierta solo tiene entrada: sin pregunta",
    not any(r.key == "cpxseg_cor_campo" for r in at.radio), [r.key for r in at.radio])
elegir(at, "15:00")
chk("una cerrada tiene dos: pregunta, y con el segmentado de la app",
    any(r.key == "cpxseg_cor_campo" for r in at.radio), [r.key for r in at.radio])

sec("12. El lateral, con una sola obra")
at = pinta(_NADA)
_c = claves(at)
chk("⚠️ un toque (como la pantalla)", "sb_tc_solo" in _c and not any(s.key == "sb_tc_prj_sel" for s in at.selectbox), sorted(_c))
at = pinta(_NADA, proys=[_OBRA, {"ID": "PRJ-2", "Name": "Otra", "Group": "cliente1"}])
chk("con dos, sigue el selector", any(s.key == "sb_tc_prj_sel" for s in at.selectbox), [s.key for s in at.selectbox])

sec("13. ⚠️ Lo que se le promete a quien ficha")
_todo = ""
for f in ("timeclock_ui.py", "chat_agent.py", "home_ui.py"):
    _todo += open(os.path.join(RAIZ, "core", f), encoding="utf-8").read()
chk("ya no dice que la oficina no ve el detalle (era falso)",
    "not each person's detail" not in _todo and "your time entries are private" not in _todo)
chk("el asistente tampoco", "Los fichajes son privados" not in _todo)
_hu = open(os.path.join(RAIZ, "core", "home_ui.py"), encoding="utf-8").read()
chk("la barra de arriba avisa de un olvido", 't("Entry left open") if timeclock.olvidos(_ses)' in _hu)
chk("el banner del Pre-Start no reclama la charla de hoy por una obra de ayer",
    "if not prj or timeclock.olvidos(ses):" in _hu)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
