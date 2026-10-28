# -*- coding: utf-8 -*-
"""v616 · RECORRIDO DE «MY PROJECTS» (la obra del CAMPO) — decisión del usuario (28/10/2026):
«Dale con todo incluido lo recomendado».

Visto en producción como installer CI 1 (PRJ-0027) y en el código:
  (1) cabecera: en el móvil «Client» quedaba sola en una 2ª fila → 2 tarjetas y el cliente en la
      línea de la dirección;
  (2) ⚠️ lo marcado en «Progress» SIN GUARDAR se perdía en silencio al cambiar de pestaña (medido)
      → se conserva, cada etapa dice cuántos cambios, «Save all», y el aviso en las demás pestañas
      con la vuelta a un toque; (3) el «?» de cada casilla acreditada: quién, cuándo, de qué parte;
  (4-8) alarmas: fecha DD/MM/YYYY HH:MM, NOMBRE, texto escapado, la caja se vacía tras enviar (un
      2º toque mandaba OTRA alarma), «Alert sent…» traducible, «resolver» diferido;
  (9) el campo resuelve solo los avisos de la oficina y lo que reportó él (decisión B);
  (10-11) recibos: el campo ve SOLO los suyos (decisión C), fecha DD/MM/YYYY, texto escapado;
  (12-14) archivos: el campo sube solo imágenes, sin el selector «foto», el error traducible;
  (15) «My route» con clave.
Todo sin red ni hoja real: la pantalla REAL con sus datos sustituidos.
"""
import ast
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

from core import alerts as AL                                     # noqa: E402
# ⚠️ Los guiones de AppTest corren en ESTE proceso y sustituyen `alerts.resolve_alert`: la real se
# guarda AHORA, antes de lanzar ninguno (si no, la prueba de unidad de abajo probaba el sustituto).
_RESOLVER_REAL = AL.resolve_alert

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": ss.get("_u", "campo000"), "nombre": "X",
                                     "rol": ss.get("_rol", "field"), "grupo": "cliente1"})
from core import projects as P, projects_ui as PU, timeclock, roster, route_ui, auth, alerts
from core import stage_progress as SP, daily_log_ui as DLU, expenses as E
ss.setdefault("_hecho", {"1|A1": 100.0})
ss.setdefault("_acr", [])
ss.setdefault("_res", [])
ss.setdefault("_rep", [])
ss.setdefault("_alertas", [
    {"ID": "ALR-1", "ProjectID": "PRJ-1", "Type": "problema", "CreatedBy": "campo000",
     "Date": "2026-10-28 08:05", "Status": "abierta", "Message": "Pit *light* broken $5"},
    {"ID": "ALR-2", "ProjectID": "PRJ-1", "Type": "problema", "CreatedBy": "helper 1",
     "Date": "2026-10-27 16:40", "Status": "abierta", "Message": "Door frames missing"},
    {"ID": "ALR-3", "ProjectID": "PRJ-1", "Type": "cambio", "CreatedBy": "Admin2",
     "Date": "2026-10-26 09:00", "Status": "abierta", "Message": "The project details were updated."}])


def _prj(pid):
    return {"ID": pid, "Name": "Job A", "Status": "In progress", "Progress": "40",
            "Client": "Meridian *Property* Group", "Type": "Installation",
            "Location": "500 Oxford Street"}


P.is_configured = lambda: True
P.list_projects_for_field = lambda u, grupo=None, incluir_internos=False: [_prj("PRJ-1")]
P.get_project = lambda pid: _prj(pid)
P.es_interno = lambda prj: False
timeclock.open_sessions = lambda n, g, u: {}
roster.is_configured = lambda: False
route_ui.render_mi_ruta = lambda u, g: None
PU._induccion_section = lambda *a, **k: None
auth.list_users = lambda grupo=None: [{"User": "campo000", "Name": "Carlos Campo"},
                                      {"User": "helper 1", "Name": "Helena Uno"},
                                      {"User": "Admin2", "Name": "Bobo"}]
# ── Progress: el plan, lo acreditado y `acreditar`, en memoria ──
_PLAN = [(1, "Set Up", ["A1", "A2"]), (2, "Prepping", ["B1", "B2"])]
SP.is_configured = lambda: True
SP.version_desfasada = lambda prj: ""
def _detalle(pid, prj):
    out = []
    for o, n, acts in _PLAN:
        _a = [{"nombre": x, "peso_en_etapa": 50.0, "pct": ss["_hecho"].get("%d|%s" % (o, x), 0.0)} for x in acts]
        out.append({"orden": o, "nombre": n, "actividades": _a, "informativas": [],
                    "pct": sum(a["pct"] for a in _a) / len(_a)})
    return out
SP.detalle = _detalle
SP.creditos = lambda pid, etapa=None: [
    {"StageOrder": "1", "Activity": "A1", "Pct": "100", "UpdatedBy": "campo000",
     "WorkDate": "2026-10-22", "Updated": "2026-10-23 10:00", "Source": "log", "Note": "LOG-0005"}]
def _acreditar(pid, grupo, prj, cambios, quien="", **k):
    ss["_acr"].append([(c["etapa"], c["actividad"], c["pct"]) for c in cambios])
    for c in cambios:
        ss["_hecho"]["%d|%s" % (c["etapa"], c["actividad"])] = c["pct"]
    return True, "Saved."
SP.acreditar = _acreditar
DLU.render_campo = lambda *a, **k: st.caption("PARTE")
# ── alarmas ──
alerts.is_configured = lambda: True
alerts.list_alerts = lambda pid, estado=None: [a for a in ss["_alertas"] if a["Status"] == "abierta"]
def _resolver(aid, quien, gestor=True):
    ss["_res"].append((aid, quien, gestor))
    return True, "Alert resolved."
alerts.resolve_alert = _resolver
alerts.report_problem = lambda pid, g, msg, u, n="": (ss["_rep"].append(msg) or (True, "ALR-9"))
# ── recibos ──
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"items": [
    {"ID": "G-1", "Date": "2026-10-22", "Category": "Materials", "Amount": "120", "Supplier": "Bunnings *A*",
     "Description": "", "DriveID": "", "File": "", "CreatedBy": "campo000"},
    {"ID": "G-2", "Date": "2026-10-20", "Category": "Rental", "Amount": "5000", "Supplier": "Crane hire",
     "Description": "", "DriveID": "", "File": "", "CreatedBy": "Admin2"}]}
PU._archivos_section = lambda pid: st.caption("ARCHIVOS")
# ⚠️ El ORDEN de la shell (trampa 41): los avisos de `flash`, ANTES de la sección
from core import flash
flash.mostrar()
PU.render_field_projects(ss["auth"]["usuario"], "cliente1")
'''


def _w(lista, key):
    return next((x for x in lista if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


def _app(**estado):
    at = AppTest.from_string(APP, default_timeout=90)
    for k, v in estado.items():
        at.session_state[k] = v
    return at.run()


def _exps(at):
    return list(at.expander) + list(at.status)


def _tit(at, txt):
    return next((str(e.label) for e in _exps(at) if txt in str(e.label)), "")


# ═════════════════════════════════════════════════════════════════
sec("1. La cabecera")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kp = " ".join(m.value for m in at.markdown if "cpx-kpis" in m.value)
chk("⚠️ DOS tarjetas: Status y Project progress (sin «Client», que quedaba sola en el móvil)",
    "Status" in _kp and "Project progress" in _kp and "Client" not in _kp, _kp[:200])
_cap = next((c.value for c in at.caption if "Oxford" in c.value), "")
chk("...el cliente, en la línea de la dirección, ESCAPADO", r"Meridian \*Property\* Group" in _cap
    and "500 Oxford Street" in _cap, _cap)

# ═════════════════════════════════════════════════════════════════
sec("2-3. Progress: lo marcado sin guardar, «Save all» y el «?» de cada casilla")
_c11 = _w(at.checkbox, "fld_PRJ-1_1_0")
chk("el «?» de una acreditada: quién (su NOMBRE), el DÍA del trabajo y de qué parte",
    _c11 is not None and _c11.proto.help == "Credited by Carlos Campo · 22/10/2026 — from daily log LOG-0005",
    _c11 and _c11.proto.help)
chk("...y una sin acreditar, sin «?»", _w(at.checkbox, "fld_PRJ-1_1_1").proto.help == "")
_w(at.checkbox, "fld_PRJ-1_1_1").check()
at.run()
chk("marcar sin guardar: la etapa dice «1 unsaved»", "1 unsaved" in _tit(at, "Set Up"), _tit(at, "Set Up"))
chk("...arriba, el aviso y «Save all (1)»", any("1 unsaved ticks" in x for x in _todo(at))
    and _w(at.button, "fld_save_all_PRJ-1") is not None)
_bs = _w(at.button, "fld_save_PRJ-1_1")
chk("...y el botón de la etapa lo dice y se resalta", _bs is not None and "(1 changes)" in _bs.label
    and _bs.proto.type == "primary", _bs and (_bs.label, _bs.proto.type))
chk("nada escrito todavía", at.session_state["_acr"] == [])
at.session_state["cpxseg_fld_sec"] = "📝 Parte"
at.run()
chk("⚠️ en OTRA pestaña: «1 unsaved ticks in «Progress»» y la vuelta a un toque",
    any("unsaved ticks in «Progress»" in x for x in _todo(at)) and _w(at.button, "fld_ir_pend_PRJ-1") is not None,
    _todo(at)[-4:])
_w(at.button, "fld_ir_pend_PRJ-1").click()
at.run()
_c12 = _w(at.checkbox, "fld_PRJ-1_1_1")
chk("⚠️ de vuelta en «Progress», la casilla SIGUE marcada (antes se perdía en silencio)",
    at.session_state["cpxseg_fld_sec"] == "🏗 Avance" and _c12 is not None and _c12.value is True,
    (at.session_state["cpxseg_fld_sec"], _c12 and _c12.value))
_w(at.checkbox, "fld_PRJ-1_2_0").check()
at.run()
chk("dos etapas con cambios: «Save all (2)»", _w(at.button, "fld_save_all_PRJ-1").label.endswith("Save all (2)"),
    _w(at.button, "fld_save_all_PRJ-1").label)
_w(at.button, "fld_save_PRJ-1_1").click()
at.run()
chk("guardar UNA etapa: solo lo suyo, y lo de la otra sigue pendiente",
    at.session_state["_acr"] == [[(1, "A2", 100.0)]] and "1 unsaved" in _tit(at, "Prepping")
    and "unsaved" not in _tit(at, "Set Up"), (at.session_state["_acr"], _tit(at, "Prepping")))
_w(at.button, "fld_save_all_PRJ-1").click()
at.run()
chk("«Save all»: lo que quedaba, en UNA escritura, y sin avisos después",
    at.session_state["_acr"][-1] == [(2, "B1", 100.0)] and len(at.session_state["_acr"]) == 2
    and not any("unsaved" in x for x in _todo(at)), at.session_state["_acr"])
at2 = _app()
_w(at2.checkbox, "fld_PRJ-1_1_1").check()
at2.run()
_w(at2.checkbox, "fld_PRJ-1_1_1").uncheck()
at2.run()
chk("marcar y DESMARCAR (vuelve a lo guardado): nada pendiente", not any("unsaved" in x for x in _todo(at2)))
at2b = _app(**{"_sp_pend_fld_PRJ-1": {"1|A1": True}})
chk("un pendiente que YA es verdad en la hoja (lo guardó otro) deja de contarse",
    not any("unsaved" in x for x in _todo(at2b)) and at2b.session_state["_sp_pend_fld_PRJ-1"] == {})

# ═════════════════════════════════════════════════════════════════
sec("4-9. Alarmas")
at3 = _app(cpxseg_fld_sec="🚨 Avisos")
_md = " | ".join(m.value for m in at3.markdown)
chk("⚠️ fecha DD/MM/YYYY HH:MM y la persona por su NOMBRE", "_28/10/2026 08:05_" in _md
    and "**Carlos Campo**" in _md and "campo000" not in _md, _md[:300])
chk("...y su texto ESCAPADO (ni cursiva ni fórmula)", r"Pit \*light\* broken \$5" in _md)
_rb = sorted(b.key for b in at3.button if b.key and b.key.startswith("resolv_"))
chk("⚠️ el campo resuelve el problema QUE REPORTÓ y el aviso de la oficina — no el de Helena",
    _rb == ["resolv_ALR-1", "resolv_ALR-3"], _rb)
_w(at3.button, "resolv_ALR-1").click()
at3.run()
chk("resolver: diferido, y el módulo recibe que NO es la oficina (lo vuelve a mirar)",
    at3.session_state["_res"] == [("ALR-1", "campo000", False)] and not at3.exception, at3.session_state["_res"])
at3b = _app(cpxseg_fld_sec="🚨 Avisos", _alr_pet={"pid": "PRJ-OTRA", "id": "ALR-1"})
chk("una petición de «resolver» de OTRA obra no se aplica (y se tira)",
    at3b.session_state["_res"] == [] and "_alr_pet" not in at3b.session_state)
at4 = _app(cpxseg_fld_sec="🚨 Avisos", _u="Admin2", _rol="administrator")
chk("la oficina resuelve cualquiera", sorted(b.key for b in at4.button if b.key and b.key.startswith("resolv_"))
    == ["resolv_ALR-1", "resolv_ALR-2", "resolv_ALR-3"])
at5 = _app(cpxseg_fld_sec="🚨 Avisos")
_w(at5.text_area, "rep_PRJ-1").input("The car top is wet")
at5.run()
_w(at5.button, "repb_PRJ-1").click()
at5.run()
chk("enviar: la alarma sale y «Alert sent to the administrator.»", at5.session_state["_rep"] == ["The car top is wet"]
    and any("Alert sent to the administrator." in x for x in _todo(at5)), _todo(at5)[-3:])
_ta = _w(at5.text_area, "rep_PRJ-1_1")
chk("⚠️ ...y la caja nace VACÍA (un 2º toque mandaba OTRA alarma igual)", _ta is not None and _ta.value == "",
    _ta and _ta.value)

# unidad: la regla y el módulo
_AL = [{"ID": "A1", "Type": "problema", "CreatedBy": "yo"}, {"ID": "A2", "Type": "problema", "CreatedBy": "otro"},
       {"ID": "A3", "Type": "cambio", "CreatedBy": "Admin2"}]
chk("`puede_resolver`: el campo, lo suyo y los avisos; la oficina, todo",
    [AL.puede_resolver(a, "yo", False) for a in _AL] == [True, False, True]
    and all(AL.puede_resolver(a, "yo", True) for a in _AL))


class _WS:
    def __init__(self):
        self.lotes = []

    def get_all_records(self, **k):
        return [{"ID": "A2", "Type": "problema", "CreatedBy": "otro", "Status": "abierta"}]

    def batch_update(self, lote, value_input_option=None):
        self.lotes.append(lote)


_ws, _o = _WS(), (AL._ws, AL._invalidate)
AL._ws, AL._invalidate = (lambda: (_ws, None)), (lambda: None)
try:
    okr, mr = _RESOLVER_REAL("A2", "yo", gestor=False)
    chk("⚠️ el MÓDULO tampoco deja al campo resolver el problema de otro (fila fresca)",
        okr is False and not _ws.lotes, mr)
    chk("...la oficina, sí", _RESOLVER_REAL("A2", "Admin2")[0] and len(_ws.lotes) == 1)
finally:
    AL._ws, AL._invalidate = _o

# ═════════════════════════════════════════════════════════════════
sec("10-11. Recibos")
at6 = _app(cpxseg_fld_sec="💰 Recibos")
_tr = _tit(at6, "receipts")
_rec = " | ".join(c.value for c in at6.caption)
chk("⚠️ el campo ve SOLO los suyos: «Your receipts (1)», sin la grúa de la oficina",
    "Your receipts (1)" in _tr and "Crane hire" not in _rec and "5,000" not in _rec, (_tr, _rec[:200]))
chk("...la fecha DD/MM/YYYY, el «$» y el proveedor escapados",
    r"22/10/2026 · Materials · \$120 · Bunnings \*A\*" in _rec, _rec[:300])

# ═════════════════════════════════════════════════════════════════
sec("12-15. Archivos y lo demás")
APP2 = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import projects_ui as PU
if st.session_state.get("_campo", True):
    PU._subir_documento("PRJ-1", True, PU._CAMPO_SUBE, "campo000")
else:
    PU._subir_documento("PRJ-1", False, PU._DOC_SUBIR, "Admin2")
'''
at7 = AppTest.from_string(APP2, default_timeout=60).run()
_fu = at7.get("file_uploader")
chk("⚠️ el campo sube SOLO imágenes (decía «solo fotos» y aceptaba cualquier archivo)",
    _fu and sorted(_fu[0].proto.type) == sorted([".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]),
    _fu and list(_fu[0].proto.type))
chk("...y sin el selector «Type» de una sola opción en español", len(at7.selectbox) == 0, [s.label for s in at7.selectbox])
at8 = AppTest.from_string(APP2, default_timeout=60)
at8.session_state["_campo"] = False
at8.run()
chk("la oficina: cualquier archivo y el tipo por su ETIQUETA («Client report», no «informe_cliente»)",
    at8.get("file_uploader") and list(at8.get("file_uploader")[0].proto.type) == []
    and at8.selectbox and "Client report" in list(at8.selectbox[0].options)
    and "informe_cliente" not in list(at8.selectbox[0].options), at8.selectbox and list(at8.selectbox[0].options))
_pu = open(os.path.join(RAIZ, "core", "projects_ui.py"), encoding="utf-8").read()
_apu = ast.parse(_pu)
_fs = [ast.unparse(n) for n in ast.walk(_apu) if isinstance(n, ast.JoinedStr) and "could not be uploaded" in ast.unparse(n)]
chk("el error de subida, traducible (no un f-string suelto)", not _fs
    and 't("It could not be uploaded: {e}", e=ex)' in _pu, _fs)
chk("«My route» con clave (trampa 35)", 'key="exp_mi_ruta"' in _pu)
# (el texto en inglés sale IGUAL con o sin `t()`: AppTest no lo distingue, se mira el código)
chk("«Alert sent to the administrator.» dentro de `t()` (traducible)",
    't("Alert sent to the administrator.")' in _pu)

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
