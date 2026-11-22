# -*- coding: utf-8 -*-
"""v694 · Ciclo 6 → mejoras 1/3, SEGURIDAD Y CIERRE (22/11), con la decisión D4 del usuario:
- H26 · archivar una obra a medias enseña lo que sigue abierto y pide una casilla; «Project archived.» /
  «Project restored.»; y una alarma de SEGURIDAD abierta sigue en la campana aunque la obra se archive;
- H27 · la campana (el resumen del día, 120 s) se tira al escribir una alarma y al archivar o restaurar;
- D4 / H21 · resolver una de seguridad avisa a quien la levantó, con la nota (Telegram/correo y su campana);
- H15 · lo del parte puede ir a la alarma de seguridad que la obra ya tiene ese día (`alerts.ampliar`);
- H4 · fichar y el Pre-Start dicen la credencial exigida que no se cumple; H5 · «My projects» abre la obra fichada;
- H25 · quien firmó la charla sin fichar sale en la ficha y en el expediente (y sin certificado);
- H6 · «A project alert was opened» sin el icono de error; H8 · «It is installed» desde el checklist;
- H9 · un nombre de fichero que ya existe en la obra sale con « (2)».

Nada sale a la red ni escribe: hojas FALSAS que apuntan lo escrito, sustitutos y AppTest.
"""
import ast
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


def _fuente(rel):
    return open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    """El nodo AST de la función `nombre` del fichero (a cualquier nivel)."""
    arbol = ast.parse(_fuente(rel))
    return next((n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import alerts, admin_digest, credentials, handover, handover_ui   # noqa: E402
from core import projects, falsecar, clock                                 # noqa: E402
from core.num import col_letter                                            # noqa: E402

HOY = date(2026, 11, 22)
# ⚠️ trampa 48: los guiones de AppTest corren en ESTE proceso y lo que sustituyen se queda puesto (el de la campana
# cambia `alerts.resueltas_para`): lo real, guardado antes de ninguno.
_RESUELTAS = alerts.resueltas_para


class _Hoja:
    def __init__(self, cab, filas):
        self.cab, self.filas, self.escrito = list(cab), [dict(x) for x in filas], []

    def get_all_records(self, **k):
        return [dict(x) for x in self.filas]

    def batch_update(self, lote, **k):
        self.escrito += lote
        for it in lote:
            _col = "".join(ch for ch in it["range"] if ch.isalpha())
            _row = int("".join(ch for ch in it["range"] if ch.isdigit()))
            self.filas[_row - 2][next(h for i, h in enumerate(self.cab) if col_letter(i + 1) == _col)] = it["values"][0][0]


def _alr(aid, msg, quien="campo000", estado="abierta", tipo="problema", fecha="2026-11-22 16:55", **kw):
    r = {h: "" for h in alerts.ALERTS_HEADERS}
    r.update({"ID": aid, "ProjectID": "PRJ-47", "Group": "G", "Source": "campo", "Type": tipo, "Message": msg,
              "CreatedBy": quien, "Date": fecha, "Status": estado})
    r.update(kw)
    return r


FC_MSG = "False car check with 1 item(s) marked X: 12 (platform sways)"

# ═════════════════════════════════════════════════════════════════
print("1. H4 · la credencial exigida que no se cumple")
_r = _sustituir(credentials, list_for=lambda u: [{"Type": "Working at Heights", "Number": "1",
                                                  "ExpiryDate": "2026-11-19"}] if u == "campo000" else [],
                is_configured=lambda: True)
_r2 = _sustituir(clock, today=lambda *a, **k: HOY)
chk("requeridos_de parte «;»", credentials.requeridos_de({"RequiredCerts": "Working at Heights; Forklift"})
    == ["Working at Heights", "Forklift"])
_m = credentials.incumplidas("campo000", ["Working at Heights", "Forklift"])
chk("incumplidas: la vencida con su fecha y la que no tiene", _m == [("Working at Heights", "vencido", "2026-11-19"),
                                                                    ("Forklift", "falta", "")], _m)
chk("…y su texto", credentials.texto_incumplidas(_m)
    == "Working at Heights expired on 19/11/2026; Forklift not on file", credentials.texto_incumplidas(_m))
chk("sin nada exigido, nada", credentials.incumplidas("campo000", []) == [])
# lo destapó romper_v694: «por vencer» CUMPLE (decisión del usuario, v219) y nada lo probaba
_rpv = _sustituir(credentials, list_for=lambda u: [{"Type": "Working at Heights", "Number": "1",
                                                    "ExpiryDate": "2026-12-01"}])
chk("una que vence en 9 días («por vencer») cumple: nada que avisar",
    credentials.incumplidas("campo000", ["Working at Heights"]) == [], credentials.incumplidas("campo000", ["Working at Heights"]))
_rpv()
from core import timeclock_ui as TU                                        # noqa: E402
_r3 = _sustituir(TU.projects_data, get_project=lambda pid: {"ID": pid, "RequiredCerts": "Working at Heights"})
_n = TU.nota_credenciales("PRJ-47", "G", "campo000")
chk("al fichar: «This job requires certificates you don't meet: Working at Heights expired on 19/11/2026…»",
    "This job requires certificates you don't meet: Working at Heights expired on 19/11/2026" in _n, _n)
_r3()
_r3 = _sustituir(TU.projects_data, get_project=lambda pid: {"ID": pid, "RequiredCerts": ""})
chk("…en una obra que no exige nada, nada", TU.nota_credenciales("PRJ-47", "G", "campo000") == "")
_r3()
_fi = ast.unparse(_func("core/timeclock_ui.py", "_fichar"))
chk("_fichar avisa de la credencial y deja la obra para «My projects» (H5)",
    "nota_credenciales(pid, grupo, usuario)" in _fi and "_fieldproj_pending" in _fi, _fi[:300])
_sw = _fuente("core/timeclock_ui.py")
chk("…y al cambiar de obra («Switch») también", "_nc = nota_credenciales(_nuevo, grupo, usuario)" in _sw
    and 'st.session_state["_fieldproj_pending"] = str(_nuevo)' in _sw)

# el Pre-Start: lo que no cumple cada asistente, junto a su firma
PS = r'''
import streamlit as st
from core import prestart_ui as PU, credentials
credentials.is_configured = lambda: True
credentials.list_for = lambda u: [{"Type": "Working at Heights", "Number": "1", "ExpiryDate": "2026-11-19"}] if u == "campo000" else []
PU._canvas_disponible = lambda: None
_c = [{"usuario": "campo000", "nombre": "hjg,ujgjg", "etiqueta": "hjg,ujgjg", "ficho": True},
      {"usuario": "helper 1", "nombre": "helper 1", "etiqueta": "helper 1", "ficho": False}]
st.session_state["_OUT"] = PU._asistentes_con_firma("hjg,ujgjg", "campo000", _c, "k",
                                                    requeridos=["Working at Heights"])
'''
at = AppTest.from_string(PS, default_timeout=60)
at.session_state["ps_asist_sel_k"] = ["hjg,ujgjg", "helper 1"]
at.run()
_cap = [str(c.value) for c in at.caption]
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("Pre-Start: «Working at Heights expired on 19/11/2026» junto a hjg,ujgjg",
    any("Working at Heights expired on 19/11/2026" in c for c in _cap), _cap)
chk("…y «Working at Heights not on file» junto a helper 1", any("Working at Heights not on file" in c for c in _cap), _cap)
_ps = _fuente("core/prestart_ui.py")
chk("el formulario le pasa lo que exige la obra", "requeridos=_CR0.requeridos_de(prj)" in _ps)
_r(); _r2()

# ═════════════════════════════════════════════════════════════════
print("2. H5 · «My projects» recoge la obra fichada antes de pintar el desplegable")
_rf = ast.unparse(_func("core/projects_ui.py", "render_field_projects"))
_i_pop, _i_sel = _rf.find("_fieldproj_pending"), _rf.find("st.selectbox(t('Assigned project')")
chk("pop de «_fieldproj_pending» ANTES del selectbox", 0 < _i_pop < _i_sel, (_i_pop, _i_sel))
chk("…y solo si la obra es suya (está en el desplegable)", "if _pend and str(_pend) in idmap:" in _rf)

# ═════════════════════════════════════════════════════════════════
print("3. H6 · «se abrió una alarma» sin el icono de error")
for _f in ("core/prestart_ui.py", "core/falsecar_ui.py"):
    _s = _fuente(_f)
    chk(f"{_f}: ningún «:material/cancel: A project alert was opened»",
        ":material/cancel: A project alert was opened" not in _s and
        ":material/notifications_active: A project alert was opened" in _s)

# ═════════════════════════════════════════════════════════════════
print("4. H8 · «It is installed» desde el checklist")
from core import stage_progress as SP, stages as S                       # noqa: E402
_LL = []
_r = _sustituir(SP, plan_de_obra=lambda prj: [{"actividades": [{"nombre": "Receive toolbox"}]},
                                               {"actividades": [{"nombre": "Clean rails"}]},
                                               ] if prj.get("_sin") else
                [{"actividades": [{"nombre": "Receive toolbox"}, {"nombre": S.FC_MONTAR}]}],
                acreditar=lambda *a, **k: (_LL.append((a, k)), (True, "ok"))[1])
ok, _ = falsecar.montar({"ID": "PRJ-47"}, "G", "campo000", HOY)
chk("montar: acredita «Install sky climber» al 100 % en SU etapa, manual, hoy, con el autor",
    ok and _LL and _LL[-1][0][3] == [{"etapa": 1, "actividad": S.FC_MONTAR, "pct": 100, "nota": ""}]
    and _LL[-1][1] == {"quien": "campo000", "origen": SP.MANUAL, "fecha": HOY}, _LL)
ok, msg = falsecar.montar({"ID": "PRJ-47", "_sin": True}, "G", "campo000", HOY)
chk("…sin esa actividad en el plan, no acredita nada", not ok and len(_LL) == 1, msg)
_r()
FCU = r'''
import datetime as dt
import streamlit as st
from core import falsecar_ui as FU, falsecar as FC, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
clock.now = lambda *a, **k: dt.datetime(2026, 11, 22, 9, 0)
FC.del_dia = lambda pid, dia: None
FC.activo = lambda prj, dia=None: False
FC.periodo = lambda prj: st.session_state.get("_PER", (None, None))
FC.de_obra = lambda pid: []
FC.montar = lambda prj, g, q, dia=None: (st.session_state.setdefault("_M", []).append((prj["ID"], q, dia)), (True, "ok"))[1]
FU.render({"ID": "PRJ-47", "Name": "C6"}, "G", "field", "campo000", "hjg,ujgjg")
'''
at = AppTest.from_string(FCU, default_timeout=60).run()
chk("sin montar: el botón «It is installed: tick «Install sky climber» for today»",
    any(b.key == "fc_montar_PRJ-47" for b in at.button), [b.key for b in at.button])
at.button(key="fc_montar_PRJ-47").click().run()
chk("…tocarlo lo marca (hoy, el autor) y lo dice", at.session_state["_M"] == [("PRJ-47", "campo000", HOY)],
    at.session_state["_M"] if "_M" in at.session_state else None)
at = AppTest.from_string(FCU, default_timeout=60)
at.session_state["_PER"] = (date(2026, 11, 10), date(2026, 11, 20))
at.run()
chk("ya montado y retirado: sin botón (no se rehace desde aquí)", not any(b.key == "fc_montar_PRJ-47" for b in at.button))

# ═════════════════════════════════════════════════════════════════
print("5. H9 · un nombre que ya existe en la obra")
_r = _sustituir(projects, list_documents=lambda pid: [{"Name": "22112026 H H1.pdf"}, {"Name": "22112026 H H1 (2).pdf"}])
chk("«22112026 H H1.pdf» ya está dos veces → «(3)»", projects.nombre_libre("X", "22112026 H H1.pdf") == "22112026 H H1 (3).pdf")
chk("uno libre se queda", projects.nombre_libre("X", "22112026 False Car H.pdf") == "22112026 False Car H.pdf")
_r()
for _f, _fn in (("core/prestart.py", "submit"), ("core/falsecar.py", "submit")):
    chk(f"{_f}.{_fn} pasa el nombre por nombre_libre", "nombre_libre(" in ast.unparse(_func(_f, _fn)))

# ═════════════════════════════════════════════════════════════════
print("6. H26 · archivar a medias")
_LL = []
_r = _sustituir(projects, get_project=lambda pid: {"ID": pid, "Progress": "3", "Type": "Installation"},
                update_project=lambda pid, f: (_LL.append(f), (True, "Project updated."))[1])
_r2 = _sustituir(admin_digest, invalidar=lambda: _LL.append("INV"))
ok, msg = projects.set_archivado("PRJ-47", True)
chk("archivar dice «Project archived.» y tira la campana", ok and msg == "Project archived." and "INV" in _LL, (msg, _LL))
_LL.clear()
ok, msg = projects.set_archivado("PRJ-47", False)
chk("restaurar dice «Project restored.» y tira la campana", ok and msg == "Project restored." and "INV" in _LL
    and _LL[0].get("Status") == "In progress", (msg, _LL))
_r(); _r2()
_dp = ast.unparse(_func("core/projects_ui.py", "_detalle_proyecto"))
_i_lc, _i_bt = _dp.find("_abierto = lista_cierre(pid, grupo, prj)"), _dp.find("key=f'arch_{pid}'")
chk("la ficha arma lo abierto (`lista_cierre`) ANTES del botón «Archive»", 0 < _i_lc < _i_bt, (_i_lc, _i_bt))
chk("…con «The job is at N%: it is not finished.» si no está terminada ni cancelada",
    "not _completada(prj) and (not P.es_cancelada(prj))" in _dp and "The job is at **{p}%**: it is not finished." in _dp)
chk("…y el botón parado hasta la casilla", "disabled=not _ok_arch" in _dp and "key=f'arch_conf_{pid}'" in _dp)

# la campana: una de SEGURIDAD de una obra ARCHIVADA no se va
# (lo destapó romper_v694: la campana sustituía `seguridad_abiertas_por_obra` entera y su filtro no se probaba)
_rs = _sustituir(alerts, _alarmas_visibles=lambda: [
    _alr("A1", FC_MSG, ProjectID="P1"), _alr("A2", "Dropsaw broken", ProjectID="P1"),
    _alr("A3", "Near Miss/Hazard reported in the Pre-Start: x", ProjectID="P2", estado="resuelta"),
    _alr("A4", "Pre-Start with 1 control(s) answered NO: x", ProjectID="P3"),
    _alr("A5", "False car check with x", ProjectID="P4", tipo="cambio")])
chk("seguridad_abiertas_por_obra: solo las de SEGURIDAD abiertas (no un problema cualquiera, una resuelta ni un aviso)",
    alerts.seguridad_abiertas_por_obra() == {"P1": 1, "P3": 1}, alerts.seguridad_abiertas_por_obra())
_rs()
from core import projects as P, prestart, auth                          # noqa: E402
_todas = [{"ID": "PRJ-1", "Name": "Activa", "Status": "In progress"},
          {"ID": "PRJ-47", "Name": "C6 — Harbour", "Status": "Archived"},
          {"ID": "PRJ-9", "Name": "Vieja", "Status": "Archived"}]
_rr = [_sustituir(P, list_projects=lambda grupo=None, agrupacion_id=None, incluir_archivados=False, incluir_internos=False:
                  [dict(p) for p in _todas if incluir_archivados or p["Status"] != "Archived"],
                  delays_for=lambda proys: {}, project_hours_bulk=lambda g: {}),
       _sustituir(alerts, is_configured=lambda: True, open_counts_all=lambda: {"PRJ-1": 1, "PRJ-47": 2, "PRJ-9": 1},
                  seguridad_abiertas_por_obra=lambda: {"PRJ-47": 1}),
       _sustituir(prestart, list_prestarts=lambda pid: []),
       _sustituir(auth, list_users=lambda *a, **k: []),
       _sustituir(clock, today=lambda *a, **k: HOY)]
admin_digest.group_digest.clear()
_al = admin_digest.group_digest("G")["alarmas"]
chk("group_digest: la activa con su alarma, y la ARCHIVADA con la de seguridad (con su estado)",
    {"id": "PRJ-1", "nombre": "Activa", "n": 1} in _al
    and {"id": "PRJ-47", "nombre": "C6 — Harbour", "n": 2, "estado": "Archived"} in _al, _al)
chk("…y no la archivada cuya alarma NO es de seguridad", not [a for a in _al if a["id"] == "PRJ-9"], _al)
# H27: `invalidar` tira la caché de verdad
_cuenta = []
_rb = _sustituir(admin_digest, _base=lambda g: (_cuenta.append(1), {"proys": [], "activos": [], "delays": {},
                                                                    "horas": {}, "alarmas": {}})[1])
admin_digest.group_digest.clear()
admin_digest.group_digest("G2"); admin_digest.group_digest("G2")
_antes = len(_cuenta)
admin_digest.invalidar()
admin_digest.group_digest("G2")
chk("H27 · invalidar() hace que el resumen se vuelva a calcular", _antes == 1 and len(_cuenta) == 2, (_antes, _cuenta))
_rb()
for _x in _rr:
    _x()
admin_digest.group_digest.clear()
_LL = []
from core import hojas                                                    # noqa: E402
_rh = _sustituir(hojas, invalidar=lambda h: _LL.append(("hoja", h)))
_ri = _sustituir(admin_digest, invalidar=lambda: _LL.append("INV"))
alerts._invalidate()
chk("H27 · escribir una alarma tira también el resumen del día", ("hoja", "Alerts") in _LL and "INV" in _LL, _LL)
_rh(); _ri()

BELL = r'''
import datetime as dt
import streamlit as st
from core import home_ui as H, clock, admin_digest, credentials, toolruns, quotes, inventory, alerts, projects
clock.today = lambda *a, **k: dt.date(2026, 11, 22)
_D = {"retrasos": [], "vencidos": [], "alarmas": st.session_state.get("_ALD", [])}
admin_digest.group_digest = lambda g: _D
credentials.is_configured = lambda: False
toolruns.survey_por_decidir = lambda g: []
quotes.seguimiento = lambda g: []
inventory.is_configured = lambda: False
alerts.resueltas_para = lambda u, dias=2: list(st.session_state.get("_RES", []))
projects.get_project = lambda pid: {"ID": pid, "Name": "C6 — Harbour"}
st.session_state.setdefault("auth", {"usuario": st.session_state.get("_U", "admin2"),
                                     "rol": st.session_state.get("_ROL", "administrator"), "grupo": "G", "nombre": "x"})
st.session_state["_IT"] = H._alertas_items("G")
if st.button("ir", key="ir"):
    H._ir_alerta(st.session_state["_IT"][0]["destino"], "G")
'''
at = AppTest.from_string(BELL, default_timeout=60)
at.session_state["_ALD"] = [{"id": "PRJ-47", "nombre": "C6 — Harbour", "n": 1, "estado": "Archived"}]
at.run()
_tx = [x["texto"] for x in at.session_state["_IT"]]
chk("la campana de la oficina: «**C6 — Harbour** (Archived) — 1 open alarm»",
    any("**C6 — Harbour** (Archived)" in x and "1 open alarm" in x for x in _tx), _tx)

# ═════════════════════════════════════════════════════════════════
print("7. D4 · resolver una de seguridad avisa a quien la levantó")
_LL = []
_h = _Hoja(alerts.ALERTS_HEADERS, [_alr("ALR-18", FC_MSG), _alr("ALR-19", "The platform sways"),
                                   _alr("ALR-20", "Near Miss/Hazard reported in the Pre-Start: x", quien="admin2")])
_rr = [_sustituir(alerts, _ws=lambda: (_h, None), _invalidate=lambda: None,
                  _notify=lambda us, sub, lines: _LL.append((list(us), sub, list(lines)))),
       # el aviso al campo va por `notify.notify_user` directamente (lo escapa todo: html_seguro.POR_AVISO)
       _sustituir(alerts.notify, notify_user=lambda u, sub, lines, link=None: _LL.append(([u], sub, list(lines)))),
       _sustituir(auth, get_user=lambda u: {"User": u, "Name": "Bobo" if u == "admin2" else u}),
       _sustituir(projects, get_project=lambda pid: {"ID": pid, "Name": "C6 — Harbour"}),
       _sustituir(clock, now=lambda *a, **k: __import__("datetime").datetime(2026, 11, 22, 17, 25))]
ok, msg = alerts.resolve_alert("ALR-18", "admin2", gestor=True, nota="Guide shoes re-gapped, checked by Bobo")
chk("resuelta con nota", ok and _h.filas[0]["Status"] == "resuelta", (msg, _h.filas[0]))
chk("…y a campo000 le llega «Your alert was resolved: C6 — Harbour» con la nota y quién",
    len(_LL) == 1 and _LL[0][0] == ["campo000"] and "Your alert was resolved" in _LL[0][1] and "C6 — Harbour" in _LL[0][1]
    and "Guide shoes re-gapped, checked by Bobo" in _LL[0][2] and any("Bobo" in x for x in _LL[0][2]), _LL)
_LL.clear()
alerts.resolve_alert("ALR-19", "admin2", gestor=True)
chk("una que NO es de seguridad: sin aviso", _LL == [], _LL)
alerts.resolve_alert("ALR-20", "admin2", gestor=True, nota="ok")
chk("la que levantó quien la resuelve: sin aviso", _LL == [], _LL)
for _x in _rr:
    _x()
_rr = [_sustituir(alerts, _records=lambda: [
    _alr("A1", FC_MSG, estado="resuelta", ResolvedBy="admin2", ResolvedDate="2026-11-22 17:25", Resolution="fixed"),
    _alr("A2", FC_MSG, estado="resuelta", ResolvedBy="admin2", ResolvedDate="2026-11-15 17:25", Resolution="old"),
    _alr("A3", "The platform sways", estado="resuelta", ResolvedBy="admin2", ResolvedDate="2026-11-22 17:20"),
    _alr("A4", FC_MSG, estado="resuelta", ResolvedBy="campo000", ResolvedDate="2026-11-22 17:00"),
    _alr("A5", FC_MSG, quien="otro", estado="resuelta", ResolvedBy="admin2", ResolvedDate="2026-11-22 17:00")]),
       _sustituir(clock, today=lambda *a, **k: HOY)]
chk("resueltas_para: solo la de seguridad, suya, reciente y resuelta por OTRO",
    [a["ID"] for a in _RESUELTAS("CAMPO000")] == ["A1"], [a["ID"] for a in _RESUELTAS("campo000")])
for _x in _rr:
    _x()
at = AppTest.from_string(BELL, default_timeout=60)
at.session_state["_U"], at.session_state["_ROL"] = "campo000", "field"
at.session_state["_RES"] = [_alr("A1", FC_MSG, estado="resuelta", ResolvedBy="admin2", Resolution="Guide shoes re-gapped")]
at.run()
_it = at.session_state["_IT"]
chk("la campana del CAMPO: «C6 — Harbour — the office resolved your alert: Guide shoes re-gapped»",
    any("the office resolved your alert" in x["texto"] and "Guide shoes re" in x["texto"] for x in _it)
    and _it[0]["destino"] == ("obra_campo", "PRJ-47"), _it)
at.button(key="ir").click().run()
chk("…tocarla abre «My projects» → Alerts de esa obra",
    at.session_state["_fieldproj_pending"] == "PRJ-47" and at.session_state["cpxseg_fld_sec"] == "🚨 Avisos"
    and at.session_state["_admin_nav_pending"] == ("misproyectos", None))

# ═════════════════════════════════════════════════════════════════
print("8. H15 · lo del parte, a la alarma que ya hay")
_LL = []
_h = _Hoja(alerts.ALERTS_HEADERS, [_alr("ALR-18", FC_MSG), _alr("ALR-17", "Near Miss/Hazard x", estado="resuelta")])
_rr = [_sustituir(alerts, _ws=lambda: (_h, None), _invalidate=lambda: None,
                  _notify=lambda us, sub, lines: _LL.append((list(us), sub, list(lines))),
                  _admins_and_owners=lambda g: ["admin2"]),
       _sustituir(clock, now=lambda *a, **k: __import__("datetime").datetime(2026, 11, 22, 16, 57))]
ok, res = alerts.ampliar("ALR-18", "The platform sways at the top", "hjg,ujgjg", "C6 — Harbour")
_msg = _h.filas[0]["Message"]
chk("ampliar: se añade al final y conserva el principio (sigue siendo de seguridad)",
    ok and res == "ALR-18" and _msg.startswith(FC_MSG) and _msg.endswith("+ hjg,ujgjg · 22/11 16:57: The platform sways at the top")
    and alerts.es_seguridad(_h.filas[0]), _msg)
chk("…y avisa a la oficina «Alert updated on C6 — Harbour»", _LL and _LL[0][0] == ["admin2"]
    and "Alert updated on C6 — Harbour" in _LL[0][1], _LL)
ok, msg = alerts.ampliar("ALR-17", "x", "y")
chk("a una resuelta, no: «send it as a new one»", not ok and "send it as a new one" in msg, msg)
ok, msg = alerts.ampliar("ALR-18", "  ", "y")
chk("vacío, no", not ok)
for _x in _rr:
    _x()

PB = r'''
import streamlit as st
from core import daily_log_ui as D, alerts
alerts.list_alerts = lambda pid, estado=None: list(st.session_state.get("_AL", []))
_reg = {"fragmentos": [{"clase": "problem", "texto": "The platform sways at the top", "motivo": "defect"}], "avisos": []}
st.session_state.setdefault("k_pb_open", 0)
D._problemas(_reg, {"ID": "LOG-10", "ProjectID": "PRJ-47", "Date": "2026-11-22"}, "k")
'''
at = AppTest.from_string(PB, default_timeout=60)
at.session_state["_AL"] = [_alr("ALR-18", FC_MSG)]
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("con la del false car abierta ese día: lo dice y ofrece «Add it to ALR-18»",
    any("already has an open safety alert" in str(i.value) and "ALR-18" in str(i.value) for i in at.info)
    and any(b.key == "k_pb_add0" for b in at.button)
    and any("Send as a new alert" in str(b.label) for b in at.button), [b.label for b in at.button])
at.button(key="k_pb_add0").click().run()
chk("…«Add it to ALR-18» apunta la petición CON la alarma", at.session_state["_ag_avisar"].get("alerta") == "ALR-18",
    at.session_state["_ag_avisar"])
at = AppTest.from_string(PB, default_timeout=60)
at.session_state["_AL"] = [_alr("ALR-18", FC_MSG, fecha="2026-11-21 10:00"), _alr("ALR-19", "Dropsaw broken")]
at.run()
chk("sin una de seguridad ESE día: como siempre («Send to the office», sin «Add it to»)",
    not any(b.key == "k_pb_add0" for b in at.button) and any("Send to the office" in str(b.label) for b in at.button))

AV = r'''
import streamlit as st
from core import daily_log_ui as D, alerts, projects, daily_log as DL
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "hjg,ujgjg", "rol": "field"})
D._plan_de = lambda pid: [1]
D._lectura = lambda r, plan: {"avisos": []}
DL.revisado = lambda r: False
D._apuntar = lambda a, b: st.session_state.setdefault("_AP", []).append(a)
projects.get_project = lambda pid: {"ID": pid, "Name": "C6 — Harbour"}
alerts.ampliar = lambda aid, txt, quien, nombre="": (st.session_state.setdefault("_AMP", []).append((aid, txt, quien)), (True, aid))[1]
alerts.report_problem = lambda *a, **k: (st.session_state.setdefault("_RP", []).append(a), (True, "ALR-99"))[1]
if "_HECHO" not in st.session_state:
    st.session_state["_HECHO"] = 1
    st.session_state["_ag_avisar"] = {"lid": "LOG-10", "texto": "The platform sways at the top",
                                      "mensaje": "The platform sways at the top", "alerta": st.session_state["_A"]}
    D._avisar("PRJ-47", "G", "campo000", [{"ID": "LOG-10", "Author": "campo000"}])
'''
at = AppTest.from_string(AV, default_timeout=60)
at.session_state["_A"] = "ALR-18"
at.run()
chk("_avisar con alarma: va a `ampliar` (con el NOMBRE), no abre otra",
    at.session_state["_AMP"] == [("ALR-18", "The platform sways at the top", "hjg,ujgjg")] and "_RP" not in at.session_state,
    (at.session_state["_AMP"] if "_AMP" in at.session_state else None))
chk("…lo apunta en el parte con ESA alarma", at.session_state["_AP"][0]["LOG-10"]["avisos"]
    == [{"texto": "The platform sways at the top", "alerta": "ALR-18"}], at.session_state["_AP"])
at = AppTest.from_string(AV, default_timeout=60)
at.session_state["_A"] = ""
at.run()
chk("sin alarma: `report_problem`, como siempre", "_RP" in at.session_state and "_AMP" not in at.session_state)

# ═════════════════════════════════════════════════════════════════
print("9. H25 · quien firmó la charla sin fichar")
CTX = {"prestarts": [{"Date": "2026-11-22", "Attendees": ["campo000", "helper 1"]}],
       "trabajaron": {"campo000": "2026-11-22"}, "dias_fichados": {"campo000": ["2026-11-22"]},
       "credenciales": {"campo000": ["2026-11-19"]}, "nombres": {"campo000": "hjg,ujgjg", "helper 1": "helper 1"},
       "acts": [], "asignados": ["campo000", "helper 1"]}
chk("firmaron_sin_fichar: helper 1, el 22/11", handover.firmaron_sin_fichar(CTX) == [("helper 1", "2026-11-22")],
    handover.firmaron_sin_fichar(CTX))
chk("…sin `dias_fichados` en el contexto, nada (no acusa a todos)",
    handover.firmaron_sin_fichar({k: v for k, v in CTX.items() if k != "dias_fichados"}) == [])
_inc = [x["texto"] for x in handover.incoherencias(CTX)]
chk("expediente: «helper 1 signed the pre-start of 22/11/2026 with no certificate on file»",
    "helper 1 signed the pre-start of 22/11/2026 with no certificate on file" in _inc, _inc)
chk("…«helper 1 signed the pre-start of 22/11/2026 but did not clock in on this job that day»",
    "helper 1 signed the pre-start of 22/11/2026 but did not clock in on this job that day" in _inc, _inc)
chk("…y el de siempre, «hjg,ujgjg signed the pre-start of 22/11/2026, but their certificate expired on 19/11/2026»",
    "hjg,ujgjg signed the pre-start of 22/11/2026, but their certificate expired on 19/11/2026" in _inc, _inc)
_e = handover._ev_installer_certs(CTX)
chk("(l) cuenta a quien firmó: «no certificate: helper 1 · expired before their last day: hjg,ujgjg»",
    _e == ("missing", "no certificate: helper 1 · expired before their last day: hjg,ujgjg"), _e)
from core import prestart as PSm, timeclock as TC                         # noqa: E402
_rr = [_sustituir(PSm, is_configured=lambda: True, list_prestarts=lambda pid: [
           {"Date": "2026-11-22", "Attendees": '[{"usuario": "campo000"}, {"usuario": "helper 1"}, {"usuario": ""}]'}]),
       _sustituir(P, _fichajes_visibles=lambda g: [{"User": "campo000", "Clock In": "2026-11-22 16:48:49", "Project": "C6"},
                                                     {"User": "campo000", "Clock In": "2026-11-20 07:00:00", "Project": "C6"},
                                                     {"User": "otro", "Clock In": "2026-11-22 07:00:00", "Project": "Otra"}]),
       _sustituir(TC, es_del_proyecto=lambda r, pid, nom: r.get("Project") == "C6")]
_as = handover_ui.asistencia("PRJ-47", "G", {"ID": "PRJ-47", "Name": "C6"})
chk("handover_ui.asistencia: las charlas (sin el invitado) y TODOS los días fichados",
    _as["prestarts"] == [{"Date": "2026-11-22", "Attendees": ["campo000", "helper 1"]}]
    and _as["dias_fichados"] == {"campo000": ["2026-11-20", "2026-11-22"]} and _as["trabajaron"] == {"campo000": "2026-11-22"},
    _as)
for _x in _rr:
    _x()
FICHA = r'''
import streamlit as st
from core import projects_ui as PU, handover_ui, projects, expenses
expenses.is_configured = lambda: True
expenses.labor_breakdown = lambda pid, g: {"items": [{"usuario": "campo000", "horas": 0.27}], "horas": 0.27}
projects.get_project = lambda pid: {"ID": pid, "Name": "C6"}
handover_ui.asistencia = lambda pid, g, prj: {"prestarts": [{"Date": "2026-11-22", "Attendees": ["campo000", "helper 1"]}],
                                              "trabajaron": {"campo000": "2026-11-22"},
                                              "dias_fichados": {"campo000": ["2026-11-22"]}}
PU._etq_us = lambda us: {"campo000": "hjg,ujgjg", "helper 1": "helper 1"}
PU._equipo_proyecto("PRJ-47", "G")
'''
at = AppTest.from_string(FICHA, default_timeout=60).run()
_cap = [str(c.value) for c in at.caption]
chk("la ficha: «Signed the Pre-Start but did not clock in here: helper 1 (22/11/2026)»",
    any("Signed the Pre-Start but did not clock in here: helper 1 (22/11/2026)" in c for c in _cap), _cap)

print()
print("verif_v694: %d FALLOS" % len(FALLOS) if FALLOS else "verif_v694: TODO OK")
sys.exit(1 if FALLOS else 0)
