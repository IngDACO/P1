"""v665 · Ciclo 1 → mejoras 3/5: SEGURIDAD Y CIERRE (y lo visto verificando v664).

  H21 una alarma de SEGURIDAD (near miss, Pre-Start con NO, false car con X) no se cierra sin nota
      — en la pantalla, en `alerts.resolve_alert` y en el Management assistant —, y queda el rastro;
  H40 una obra al 100 % enseña lo que sigue abierto (alarmas, To-do, activos en obra, por facturar);
  H39 el «Next milestone» es lo que QUEDA (no una actividad ya al 100 %);
  H33 un recibo sin foto ni PDF hay que marcarlo «no receipt» a propósito;
  H32 antes de firmar un Pre-Start ajeno se lee lo que se respondió;
  H20 las ventanas del Pre-Start no saltan DENTRO del Pre-Start;
  H43 las certificaciones dicen lo ya facturado aparte y avisan del doble cobro.
Todo con las hojas SUSTITUIDAS en memoria: nada sale ni se escribe.
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "jefa", "rol": "administrator", "grupo": "G"}
from streamlit.testing.v1 import AppTest                         # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   " + q)
    else:
        fallos.append(q)
        print("   FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


def funcion(rel, nombre):
    s = fuente(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(s, n) or ""
    return ""


ADMIN = '{"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"}'
SEG = {"ID": "ALR-1", "ProjectID": "PRJ-1", "Group": "G", "Source": "campo", "Type": "problema",
       "Message": "Near Miss/Hazard reported in the Pre-Start: loose guard", "CreatedBy": "f1",
       "Date": "2026-11-09 08:00", "Status": "abierta", "ResolvedBy": "", "ResolvedDate": "", "Resolution": ""}
NORMAL = dict(SEG, ID="ALR-2", Message="Missing bolts on level 3")

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. H21 · Las alarmas de seguridad, en el motor")
from core import alerts                                           # noqa: E402
chk("Alerts tiene la columna Resolution, al FINAL (migra sola)", alerts.ALERTS_HEADERS[-1] == "Resolution")
_casos = [("Near Miss/Hazard reported in the Pre-Start: x", True), ("Pre-Start with 2 control(s) marked NO: a · b", True),
          ("False car check with 1 item(s) marked X: 3 (gate)", True), ("Missing bolts", False)]
chk("es_seguridad: near miss, Pre-Start con NO y false car con X sí; un problema cualquiera no",
    all(alerts.es_seguridad(dict(SEG, Message=m)) == v for m, v in _casos)
    and not alerts.es_seguridad(dict(SEG, Type="cambio")), [(m, alerts.es_seguridad(dict(SEG, Message=m))) for m, _ in _casos])
# ⚠️ los prefijos son el texto que escriben sus TRES orígenes: si uno cambia, se deja de exigir la nota
_ps, _fc = fuente("core/prestart.py"), fuente("core/falsecar.py")
chk("…y los prefijos casan con lo que escriben prestart (×2) y falsecar",
    'msg = "Near Miss/Hazard reported in the Pre-Start"' in _ps
    and 'msg = (f"Pre-Start with {len(no_ok)} control(s) marked NO: "' in _ps
    and '"False car check with %d item(s) marked X: %s"' in _fc)


class _WSA:
    def __init__(self, recs):
        self.recs, self.lotes = recs, []

    def get_all_records(self, **k):
        return [dict(r) for r in self.recs]

    def batch_update(self, lote, **k):
        self.lotes.append(lote)


_o = (alerts._ws, alerts._invalidate)
try:
    alerts._invalidate = lambda: None
    w = _WSA([SEG, NORMAL])
    alerts._ws = lambda: (w, None)
    _r0 = alerts.resolve_alert("ALR-1", "jefa", gestor=True)
    _l0 = list(w.lotes)
    _r1 = alerts.resolve_alert("ALR-1", "jefa", gestor=True, nota="  Guard fixed, checked by Sam  ")
    _l1 = w.lotes[-1] if w.lotes else []
    _r2 = alerts.resolve_alert("ALR-2", "jefa", gestor=True)
    _l2 = w.lotes[-1] if len(w.lotes) > 1 else []
    _r3 = alerts.resolve_alert("ALR-1", "f1", gestor=False, nota="I put the guard back")
finally:
    alerts._ws, alerts._invalidate = _o
chk("⚠️ una de seguridad SIN nota no se cierra (y no se escribe nada)",
    _r0[0] is False and "needs a note" in _r0[1] and _l0 == [], (_r0, _l0))
chk("…con nota se cierra y la nota va a Resolution (columna L), sin los espacios",
    _r1[0] is True and {"range": "L2", "values": [["Guard fixed, checked by Sam"]]} in _l1, (_r1, _l1))
chk("…una normal se cierra sin nota, como antes (sin tocar Resolution)",
    _r2[0] is True and not any(x["range"].startswith("L") for x in _l2), (_r2, _l2))
chk("…y el campo cierra la que reportó él, con su nota", _r3[0] is True, _r3)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("2. H21 · En la pantalla: la caja de la nota y el rastro")
G1 = r'''
import streamlit as st
from core import projects_ui as PU, alerts, flash
st.session_state.setdefault("auth", ''' + ADMIN + r''')
alerts.is_configured = lambda: True
_AL = [''' + repr(SEG) + ", " + repr(NORMAL) + r''']
_RES = [dict(_AL[0], ID="ALR-0", Message="False car check with 1 item(s) marked X: 3 (gate)", Status="resuelta",
             ResolvedBy="jefa", ResolvedDate="2026-11-08 10:00", Resolution="Gate replaced, checked by Sam"),
        dict(_AL[1], ID="ALR-9", Status="resuelta", ResolvedBy="jefa", ResolvedDate="2026-11-08 11:00")]
alerts.list_alerts = lambda pid, estado=None: [dict(x) for x in (_AL if estado == "abierta" else _RES)]
def _res(aid, quien, gestor=True, nota=""):
    st.session_state.setdefault("_LL", []).append((aid, nota))
    return True, "Alert resolved."
alerts.resolve_alert = _res
PU._nombres_de = lambda us, g: [str(u) for u in us]
flash.mostrar()
PU._alerts_section("PRJ-1", "G", "Obra")
'''
at = AppTest.from_string(G1, default_timeout=120).run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("la caja de la nota NO está de entrada", not [x for x in at.text_area if x.key == "alr_nota_ALR-1"])
at.button(key="resolv_ALR-1").click().run()
_ll = at.session_state["_LL"] if "_LL" in at.session_state else []
chk("⚠️ el ✓ de una de seguridad ABRE la caja y no cierra nada",
    [x for x in at.text_area if x.key == "alr_nota_ALR-1"] and not _ll, (_ll, [x.key for x in at.text_area]))
at.text_area(key="alr_nota_ALR-1").set_value("Guard fixed, checked by Sam")
at.button(key="alr_ok_ALR-1").click().run()
_ll = at.session_state["_LL"] if "_LL" in at.session_state else []
chk("…«Resolve with this note» la cierra CON la nota, y la caja se va",
    _ll == [("ALR-1", "Guard fixed, checked by Sam")] and not [x for x in at.text_area if x.key == "alr_nota_ALR-1"], _ll)
at.button(key="resolv_ALR-2").click().run()
_ll = at.session_state["_LL"] if "_LL" in at.session_state else []
chk("…una normal se cierra de un toque, como antes", _ll[-1:] == [("ALR-2", "")], _ll)
_exp = [x for x in list(at.expander) + list(at.status) if "Resolved safety alerts" in str(x.label)]
_md = " ".join(str(m.value) for m in at.markdown)
chk("el rastro: «Resolved safety alerts (1)» (solo las de seguridad) con la nota",
    _exp and "(1)" in str(_exp[0].label) and "Gate replaced, checked by Sam" in _md, ([str(x.label) for x in _exp], _md[-300:]))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("3. H21 · El Management assistant")
from core import chat_tools as CT, admin_digest as AD           # noqa: E402
ctx = {"usuario": "jefa", "grupo": "G", "rol": "administrator"}
_o = (CT._aviso_abierto, CT._mis_obras, CT._tarjeta, AD.nombres_usuarios, alerts.resolve_alert)
_cap = {}
try:
    CT._aviso_abierto = lambda e, c: dict(SEG)
    CT._mis_obras = lambda c: [{"ID": "PRJ-1", "Name": "Obra"}]
    CT._tarjeta = lambda c, tipo, tit, cuerpo, datos, *a, **k: {"tipo": tipo, "cuerpo": cuerpo, "datos": datos}
    AD.nombres_usuarios = lambda: {}
    try:
        CT._preparar_cierre_aviso({"alert_id": "ALR-1"}, ctx)
        _neg = None
    except CT._Negado as e:
        _neg = str(e)
    _card = CT._preparar_cierre_aviso({"alert_id": "ALR-1", "note": "Guard fixed"}, ctx)
    CT._aviso_abierto = lambda e, c: dict(NORMAL)
    _card2 = CT._preparar_cierre_aviso({"alert_id": "ALR-2"}, ctx)
    alerts.resolve_alert = lambda aid, u, gestor=True, nota="": (_cap.setdefault("r", (aid, nota)), (True, "ok"))[1]
    CT._confirmar_cierre({"alert_id": "ALR-1", "note": "Guard fixed"}, ctx)
finally:
    CT._aviso_abierto, CT._mis_obras, CT._tarjeta, AD.nombres_usuarios, alerts.resolve_alert = _o
chk("⚠️ sin nota, una de seguridad se NIEGA y le dice que pregunte", bool(_neg) and "Ask them" in _neg, _neg)
chk("…con nota, la tarjeta la enseña y la lleva", _card["datos"].get("note") == "Guard fixed" and "Guard fixed" in _card["cuerpo"], _card)
chk("…una normal sigue sin pedirla", _card2["datos"].get("note") == "", _card2)
chk("…y Confirm pasa la nota a resolve_alert", _cap.get("r") == ("ALR-1", "Guard fixed"), _cap)
_h = next(h for h in CT.HERRAMIENTAS if h["name"] == "prepare_close_alert") if hasattr(CT, "HERRAMIENTAS") else None
_esq = str(_h["input_schema"]) if _h else fuente("core/chat_tools.py")
chk("la herramienta prepare_close_alert acepta «note» (y dice que no se invente)",
    "'note'" in _esq or '"note": {"type": "string", "description": "What was done and who checked it' in _esq)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("4. H39 · El próximo hito es lo que QUEDA")
from core import projects_ui as PU                               # noqa: E402
ps = {"sched": {"activities": [{"nombre": "A", "inicio": 0, "duracion": 2, "orden": 1},
                               {"nombre": "Prepping", "inicio": 5, "duracion": 2, "orden": 2}],
                "total_dias": 7, "start_date": dt.date(2026, 11, 1)},
      "avances": [100, 100], "owners": ["", ""], "proj": {"ev": 100}, "today_day": 3}
_d1 = PU._diagnostico(ps)
ps["avances"] = [100, 0]
_d2 = PU._diagnostico(ps)
chk("⚠️ todo al 100 %: sin «Next milestone»", _d1["proximo"] is None, _d1["proximo"])
chk("…con «Prepping» sin hacer, ese es el hito", (_d2["proximo"] or {}).get("nombre") == "Prepping", _d2["proximo"])

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("5. H40 · La lista de cierre")
from core import tareas, inventory, invoices                     # noqa: E402
_o = (alerts.is_configured, alerts.list_alerts, tareas.is_configured, tareas.pendientes,
      inventory.is_configured, inventory.list_activos, invoices.is_configured, invoices.pendiente_de_facturar)
try:
    alerts.is_configured = lambda: True
    alerts.list_alerts = lambda pid, estado=None: [dict(SEG)] if pid == "PRJ-1" else []
    tareas.is_configured = lambda: True
    tareas.pendientes = lambda pid: [{"ID": "T1"}, {"ID": "T2"}] if pid == "PRJ-1" else []
    inventory.is_configured = lambda: True
    inventory.list_activos = lambda g=None, incluir_baja=False: [
        {"ID": "ACT-5", "Name": "Hoist 500kg", "LocationType": "project", "LocationRef": "PRJ-1"},
        {"ID": "ACT-6", "Name": "Drill", "LocationType": "warehouse", "LocationRef": "Store"},
        {"ID": "ACT-7", "Name": "Ladder", "LocationType": "project", "LocationRef": "PRJ-2"}]
    invoices.is_configured = lambda: True
    invoices.pendiente_de_facturar = lambda pid, g, p=None: 5000.0 if pid == "PRJ-1" else 0.0
    _l1 = PU.lista_cierre("PRJ-1", "G", {"ID": "PRJ-1", "Progress": "100"})
    _l2 = PU.lista_cierre("PRJ-3", "G", {"ID": "PRJ-3", "Progress": "100"})
    tareas.pendientes = lambda pid: 1 / 0
    _l3 = PU.lista_cierre("PRJ-3", "G", {"ID": "PRJ-3", "Progress": "100"})
finally:
    (alerts.is_configured, alerts.list_alerts, tareas.is_configured, tareas.pendientes,
     inventory.is_configured, inventory.list_activos, invoices.is_configured, invoices.pendiente_de_facturar) = _o
_j = " | ".join(_l1)
chk("⚠️ con todo abierto: alarmas, To-do, activo EN ESA obra y lo que falta por facturar",
    len(_l1) == 4 and "**1** open alert" in _j and "**2** To-do" in _j and "Hoist 500kg" in _j
    and "Drill" not in _j and "Ladder" not in _j and "5,000" in _j, _l1)
chk("…con nada abierto, la lista vacía", _l2 == [], _l2)
chk("…y una fuente que falla se DICE (no «nada abierto» de lo que no se miró)",
    any("could not be checked" in x for x in _l3), _l3)
chk("completada = 100 % o «Completed»",
    PU._completada({"Progress": "100"}) and PU._completada({"Progress": "50", "Status": "Completed"})
    and not PU._completada({"Progress": "99"}))
_es = funcion("core/projects_ui.py", "_estado_section")
chk("la pestaña Status la enseña ARRIBA, antes de todo",
    _es.find("_cierre_section(pid, grupo, prj)") >= 0
    and _es.find("_cierre_section(pid, grupo, prj)") < _es.find("ps = P.project_schedule(pid)"))
_cs = funcion("core/projects_ui.py", "_cierre_section")
chk("…en amarillo con la lista, o en verde si no queda nada",
    "if not _completada(prj):\n        return" in _cs and "st.warning(" in _cs and "st.success(" in _cs
    and '"\\n".join(f"- {x}" for x in _l)' in _cs)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("6. H33 · El recibo sin comprobante")
G6 = r'''
import streamlit as st
from core import projects_ui as PU, expenses as E, flash
st.session_state.setdefault("auth", ''' + ADMIN + r''')
E.is_configured = lambda: True
E.project_expenses = lambda pid: {"total": 37.8, "por_categoria": {}, "items": [
    {"ID": "GAS-1", "Date": "2026-11-09", "Category": "Fuel", "Amount": "37.80", "Supplier": "Shell",
     "Description": "", "DriveID": "", "CreatedBy": "jefa"}]}
def _add(*a, **k):
    st.session_state.setdefault("_ADD", []).append(a)
    return True, "Receipt added (37.80)."
E.add = _add
E.upload_receipt = lambda *a, **k: ""
flash.mostrar()
PU.render_expenses("PRJ-1", "G", key_prefix="ex")
'''
at = AppTest.from_string(G6, default_timeout=120).run()
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
_cap_ = " ".join(str(c.value) for c in at.caption)
chk("la lista lo marca «no receipt» (era «no file» en gris)", ":orange[**no receipt**]" in _cap_, _cap_[-200:])
_sub = next(b for b in at.button if "Save receipt" in str(b.label))
at.number_input(key="ex_val").set_value(37.8)
_sub.click().run()
chk("⚠️ sin foto ni la casilla NO se guarda, y dice por qué",
    "_ADD" not in at.session_state and any("proof for the accounts" in str(e.value) for e in at.error),
    [str(e.value) for e in at.error])
at.number_input(key="ex_val").set_value(37.8)
at.checkbox(key="ex_sinrec").check()
next(b for b in at.button if "Save receipt" in str(b.label)).click().run()
chk("…con «I have no receipt for this» marcada, se guarda (sin archivo)",
    "_ADD" in at.session_state and len(at.session_state["_ADD"]) == 1 and at.session_state["_ADD"][0][6] == "",
    at.session_state["_ADD"] if "_ADD" in at.session_state else None)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("7. H32 · Lo que se respondió, antes de firmar")
from core import prestart as PS                                  # noqa: E402
from core import clock                                           # noqa: E402
_row = {"ID": "PS-0003", "ProjectID": "PRJ-1", "Group": "G", "Date": "2026-11-09", "Time": "07:10",
        "Location": "Site", "FacilitatedBy": "Bobo", "ActivityNotes": "Install rails L1-L3",
        "NearMiss": "YES", "NearMissDesc": "loose guard", "S1JSON": '{"permisos": "YES"}',
        "S3JSON": '{"barreras": "NO"}', "GeneralNotes": "", "Attendees": '[{"name": "Bobo", "usuario": "jefa"}]',
        "File": "", "DriveID": "", "CreatedBy": "jefa", "Created": ""}
_o = (PS._records, clock.today)
try:
    PS._records = lambda *a, **k: [dict(_row)]
    clock.today = lambda *a, **k: dt.date(2026, 11, 9)
    _pf = PS.pendiente_de_firma("PRJ-1", "G", "Field One", usuario="f1")
finally:
    PS._records, clock.today = _o
chk("pendiente_de_firma trae el near miss, los controles y las notas",
    _pf.get("near_miss") is True and _pf.get("near_miss_desc") == "loose guard"
    and any(c.get("estado") == "NO" for c in _pf.get("checks", [])) and _pf.get("act_notes") == "Install rails L1-L3",
    {k: _pf.get(k) for k in ("near_miss", "near_miss_desc", "checks", "act_notes")})
G7 = r'''
import streamlit as st
from core import prestart_ui as PSU
PSU._resumen_para_firmar(st.session_state["_INFO"])
'''
at = AppTest.from_string(G7, default_timeout=60)
at.session_state["_INFO"] = {"checks": [{"label": "SWMS reviewed", "estado": "YES"},
                                        {"label": "Barriers in place", "estado": "NO"}],
                             "near_miss": True, "near_miss_desc": "loose guard", "act_notes": "Install rails", "gen_notes": ""}
at.run()
chk("⚠️ el resumen: el near miss en rojo, los NO en amarillo y las notas",
    not at.exception and any("loose guard" in str(e.value) for e in at.error)
    and any("Barriers in place" in str(w.value) for w in at.warning)
    and any("Install rails" in str(m.value) for m in at.markdown),
    ([str(e.value) for e in at.error], [str(w.value) for w in at.warning]))
at = AppTest.from_string(G7, default_timeout=60)
at.session_state["_INFO"] = {"checks": [{"label": "a", "estado": "YES"}, {"label": "b", "estado": "N/A"}],
                             "near_miss": False, "act_notes": "", "gen_notes": ""}
at.run()
chk("…y sin nada malo, lo dice («All 2 controls answered YES or N/A»)",
    not at.error and not at.warning and any("All 2 controls" in str(c.value) for c in at.caption))
_bf = funcion("core/prestart_ui.py", "_bloque_firmar")
chk("…ENCIMA del lienzo de la firma", 0 <= _bf.find("_resumen_para_firmar(info)") < _bf.find("st_canvas(key="))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("8. H20 · Las ventanas del Pre-Start, no dentro del Pre-Start")
G8 = r'''
import streamlit as st
from core import timeclock_ui as TU, home_ui as H, prestart
st.session_state.setdefault("auth", st.session_state["_AUTH"])
if st.session_state.get("_SUB"):
    st.session_state[H._subkey()["herramientas"]] = st.session_state["_SUB"]
st.session_state["_ps_aviso"] = {"pid": "PRJ-1", "nombre": "Obra", "grupo": "G"}
prestart.hecho_hoy = lambda pid, g: bool(st.session_state.get("_HECHO"))
TU._pend_firma_de = lambda pid, g: {"facilitador": "Bobo"} if st.session_state.get("_HECHO") else {}
TU._dialogo_prestart = lambda obra: st.session_state.__setitem__("_DLG", "falta")
TU._dialogo_firmar = lambda obra, q="": st.session_state.__setitem__("_DLG", "firmar")
st.session_state["_EN"] = TU.en_prestart()
st.session_state["_RET"] = TU.aviso_prestart_pendiente("G")
'''
CAMPO = {"usuario": "f1", "rol": "field", "grupo": "G", "nombre": "F1"}
OFI = {"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"}


def _g8(auth, sec, sub=None, hecho=False):
    a = AppTest.from_string(G8, default_timeout=60)
    a.session_state["_AUTH"] = auth
    a.session_state["_admin_sec"] = sec
    if sub:
        a.session_state["_SUB"] = sub
    if hecho:
        a.session_state["_HECHO"] = True
    a.run()
    g = lambda k: a.session_state[k] if k in a.session_state else None
    return (not a.exception, g("_EN"), g("_RET"), g("_DLG"))


_c1 = _g8(CAMPO, "prestart")
_c2 = _g8(CAMPO, "misproyectos")
_c3 = _g8(OFI, "herramientas", "🦺 Pre-Start")
_c4 = _g8(OFI, "herramientas", "📐 Survey")
_c5 = _g8(CAMPO, "prestart", hecho=True)
_c6 = _g8(CAMPO, "fichaje", hecho=True)
chk("⚠️ el campo, DENTRO del Pre-Start: ninguna ventana (y True: tampoco la del false car)",
    _c1 == (True, True, True, None), _c1)
chk("…fuera, la de «falta» sale como antes", _c2 == (True, False, True, "falta"), _c2)
chk("la oficina en Herramientas → Pre-Start: ninguna; en otra herramienta, sí",
    _c3 == (True, True, True, None) and _c4 == (True, False, True, "falta"), (_c3, _c4))
chk("«fírmalo» tampoco dentro del Pre-Start, y fuera sí", _c5 == (True, True, True, None)
    and _c6 == (True, False, True, "firmar"), (_c5, _c6))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("9. H43 · Certificaciones y lo ya facturado")
G9 = r'''
import streamlit as st
from core import claims_ui as CLU, claims as CL, invoices as I
st.session_state.setdefault("auth", ''' + ADMIN + r''')
CL.is_configured = lambda: True
CL.contrato = lambda pid: (12780.0, "COT-1")
CL.valor_variaciones = lambda pid: 0.0
CL.reclamaciones = lambda pid, incluir_anuladas=False: []
CL.variaciones = lambda pid, estado=None: []
CL.retencion_pct = lambda g: 5.0
I.is_configured = lambda: True
I.facturado_por_proyecto = lambda g: {"PRJ-1": float(st.session_state.get("_FACT", 0.0))}
CLU.render("PRJ-1", "G", {"ID": "PRJ-1", "Progress": "100"}, editable=False)
'''
at = AppTest.from_string(G9, default_timeout=60)
at.session_state["_FACT"] = 12780.0
at.run()
_lab = [str(x.label) for x in list(at.expander) + list(at.status)]
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ facturada aparte: el título lo dice junto a lo «claimable now»",
    any("12,141.00 claimable now" in x and "12,780.00 already invoiced" in x for x in _lab), _lab)
chk("…y dentro avisa del doble cobro", any("charge it twice" in str(w.value) for w in at.warning),
    [str(w.value) for w in at.warning])
at = AppTest.from_string(G9, default_timeout=60).run()
_lab = [str(x.label) for x in list(at.expander) + list(at.status)]
chk("…sin facturas aparte, como antes (sin aviso ni «already invoiced»)",
    any("claimable now)" in x and "already invoiced" not in x for x in _lab)
    and not any("charge it twice" in str(w.value) for w in at.warning), _lab)
_cr = funcion("core/claims.py", "calcular")
chk("…y la cuenta de la reclamación NO cambia (restar las facturas la descontaría dos veces)",
    "_bruto = round(max(0.0, _hecho - _antes), 2)" in _cr and "facturado" not in _cr)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
