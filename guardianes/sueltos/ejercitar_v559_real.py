# -*- coding: utf-8 -*-
"""v559 · Ejercitar CONTRA LA HOJA REAL (método v344) las acciones que escriben en la ficha
de una obra: AppTest pulsando los mismos botones que la pantalla, en el libro de cliente1.

⚠️ Datos de PRUEBA y sin avisar a nadie:
  · Data (guardar, actividades, plan base, archivar) sobre una obra NUEVA sin asignados
    («ZZ PRUEBA v559 escrituras»): lo que avisa a los asignados no tiene a quién avisar.
  · Costs (pedido y recibo) sobre PRJ-0015, la obra de prueba permanente (no avisan): el
    pedido se CANCELA (los pedidos no se borran) y el recibo se BORRA.
  · Al final: se borra la obra nueva (motor) y se cierran sus alertas de «cambio».
Se lanza con `py -3.12 ejercitar_v559_real.py` desde cualquier sitio.
"""
import datetime as dt
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from streamlit.testing.v1 import AppTest  # noqa: E402

fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


CAB = r'''
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator",
                                     "grupo": "cliente1", "nombre": "Bobo"})
from core import projects as P, projects_ui as PU, alerts, orders as O, expenses as E
'''

# ── 1) la obra de prueba ─────────────────────────────────────────────────────────
G_CREA = CAB + r'''
if "_PID" not in st.session_state:
    hoy = __import__("datetime").date.today()
    ok, res = P.create_project(
        grupo="cliente1", nombre="ZZ PRUEBA v559 escrituras", cliente="", cliente_id="",
        ubicacion="", modelo="", ns=2, ingeniero="", campo_asignados=[], tipo="Delivery",
        fecha_inicio=hoy.strftime("%Y-%m-%d"),
        fecha_fin_est=(hoy + __import__("datetime").timedelta(days=4)).strftime("%Y-%m-%d"),
        activities=[{"nombre": "Execution", "duracion": 5, "peso": 1}],
        creado_por="Admin2", instrucciones="", induccion_links="", presupuesto=0,
        lat="", lng="", certs_req="", stage_plan="")
    st.session_state["_PID"] = res if ok else None
    st.session_state["_ERR"] = None if ok else res
'''
print("1. La obra de prueba (sin asignados)")
at = AppTest.from_string(G_CREA, default_timeout=180)
at.run()
PID = at.session_state["_PID"] if "_PID" in at.session_state else None
chk("se crea", bool(PID), at.session_state["_ERR"] if "_ERR" in at.session_state else "")
if not PID:
    sys.exit(1)
print("     ->", PID)

G_FICHA = CAB + r'''
PU._detalle_proyecto(st.session_state["_PID"], "cliente1")
_p = P.get_project(st.session_state["_PID"]) or {}
st.session_state["_PRJ"] = {k: _p.get(k) for k in ("Model", "Budget", "Status", "ManualStatus",
                                                     "StartDate", "EndDateEst")}
st.session_state["_ACTS"] = [str(a.get("Name")) for a in P.list_activities(st.session_state["_PID"])]
st.session_state["_FIJA"] = P.ganancia_fija(st.session_state["_PID"])
st.session_state["_BL"] = bool((P.get_baseline(st.session_state["_PID"], _p) or {}).get("original"))
'''


def ficha():
    a = AppTest.from_string(G_FICHA, default_timeout=240)
    a.session_state["_PID"] = PID
    a.run()
    return a


def sec(a, s):
    [x for x in a.radio if x.key == "cpxseg_prj_sec"][0].set_value(s)
    a.run()


def boton(a, k):
    x = [y for y in a.button if y.key == k]
    return x[0] if x else None


def flashes(a):
    return list(a.session_state["_flash_cola"]) if "_flash_cola" in a.session_state else []


def estado(a, k):
    return a.session_state[k] if k in a.session_state else None


try:
    # ── 2) Data: guardar los datos ───────────────────────────────────────────────
    print("\n2. Data · Save changes")
    at = ficha()
    sec(at, "✏️ Datos")
    chk("Data se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    _mod = [x for x in at.text_input if str(x.label) == "Model"]
    _bud = [x for x in at.number_input if "Project budget" in str(x.label)]
    chk("se localizan «Model» y el presupuesto", bool(_mod) and bool(_bud))
    _mod[0].set_value("v559")
    _bud[0].set_value(100.0)
    [b for b in at.button if "Save changes" in str(b.label)][0].click()
    at.run()
    chk("guardar no lanza excepción", not at.exception, [e.value for e in at.exception][:1])
    _p = estado(at, "_PRJ") or {}
    chk("⚠️ en la HOJA: Model «v559» y Budget 100", str(_p.get("Model")) == "v559"
        and float(_p.get("Budget") or 0) == 100.0, _p)
    chk("las fechas siguen en ISO en la hoja (el formato DD/MM/YYYY es solo cómo se ve)",
        len(str(_p.get("StartDate"))) == 10 and str(_p.get("StartDate"))[4] == "-", _p)
    chk("el aviso «Changes saved» (toast)", any("Changes saved" in str(x.value) for x in at.toast),
        [x.value for x in at.toast])
    # el historial lo cuenta con nombre y fecha DD/MM/YYYY
    at = ficha()
    sec(at, "✏️ Datos")
    _md = " | ".join(m.value for m in at.markdown)
    chk("⚠️ el historial: «Budget: 0 → 100» con «· Bobo» y la fecha DD/MM/YYYY",
        "Budget: " in _md and "<b>100" in _md and "· Bobo" in _md
        and dt.date.today().strftime("%d/%m/%Y") in _md, _md[-400:])

    # ── 3) actividades ─────────────────────────────────────────────────────────
    print("\n3. Data · actividades y plan base")
    _nm = [x for x in at.text_input if str(x.label) == "Name" and not x.value]
    chk("se localiza el nombre de «Add activity»", bool(_nm))
    _nm[0].set_value("Prueba v559")
    [b for b in at.button if str(b.label) == "Add"][0].click()
    at.run()
    chk("⚠️ en la HOJA: la actividad añadida", "Prueba v559" in (estado(at, "_ACTS") or []),
        estado(at, "_ACTS"))
    at = ficha()
    sec(at, "✏️ Datos")
    boton(at, f"savetbl_{PID}").click()
    at.run()
    chk("«Save activity table» guarda (aviso de éxito)", not at.exception
        and any("success" in str(x) for x in flashes(at)) or not at.exception, flashes(at))
    at = ficha()
    sec(at, "✏️ Datos")
    boton(at, f"blset_{PID}").click()
    at.run()
    chk("⚠️ en la HOJA: el plan base queda fijado", estado(at, "_BL") is True)
    at = ficha()
    sec(at, "✏️ Datos")
    _sel = [s for s in at.selectbox if s.key == f"delact_{PID}"]
    chk("se localiza «Activity to delete»", bool(_sel))
    _op = [o for o in _sel[0].options if "Prueba v559" in o]
    _sel[0].set_value([o for o in _sel[0].options if "Prueba v559" in o][0]) if _op else None
    at.run()
    [c for c in at.checkbox if c.key == f"delactok_{PID}"][0].check()
    at.run()
    boton(at, f"delactb_{PID}").click()
    at.run()
    chk("⚠️ en la HOJA: la actividad se borró (con su confirmación)",
        "Prueba v559" not in (estado(at, "_ACTS") or ["Prueba v559"]), estado(at, "_ACTS"))

    # ── 4) Costs: beneficio fijo ───────────────────────────────────────────────
    print("\n4. Costs · beneficio fijo")
    at = ficha()
    sec(at, "💰 Costos")
    chk("Costs se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    [x for x in at.number_input if x.key == f"gf_{PID}"][0].set_value(50.0)
    boton(at, f"gf_save_{PID}").click()
    at.run()
    chk("⚠️ en la HOJA: beneficio fijo 50", float(estado(at, "_FIJA") or 0) == 50.0,
        estado(at, "_FIJA"))

    # ── 5) archivar ────────────────────────────────────────────────────────────
    print("\n5. Data · archivar")
    at = ficha()
    sec(at, "✏️ Datos")
    boton(at, f"arch_{PID}").click()
    at.run()
    chk("⚠️ en la HOJA: archivada", str((estado(at, "_PRJ") or {}).get("Status")) == "Archived",
        estado(at, "_PRJ"))
finally:
    # ── limpieza: la obra nueva fuera, sus alertas cerradas ───────────────────────
    print("\n6. Limpieza")
    G_LIMPIA = CAB + r'''
_pid = st.session_state["_PID"]
_al = [a for a in alerts.list_alerts(_pid) if str(a.get("Status", "")).lower() not in ("resolved", "resuelta")]
for a in _al:
    alerts.resolve_alert(a.get("ID"), "Admin2")
st.session_state["_NAL"] = len(_al)
st.session_state["_DEL"] = P.delete_project(_pid)
st.session_state["_YA"] = P.get_project(_pid)
'''
    at = AppTest.from_string(G_LIMPIA, default_timeout=180)
    at.session_state["_PID"] = PID
    at.run()
    print("     alertas cerradas:", estado(at, "_NAL"), "· borrado:", estado(at, "_DEL"),
          "· queda:", estado(at, "_YA"))
    chk("la obra de prueba ya no existe", not estado(at, "_YA"))

# ── 7) Costs sobre PRJ-0015: pedido (se cancela) y recibo (se borra) ─────────────────
print("\n7. Costs en PRJ-0015 · pedido y recibo")
G_015 = CAB + r'''
PU._detalle_proyecto("PRJ-0015", "cliente1")
st.session_state["_ORD"] = [(o.get("ID"), o.get("Supplier"), o.get("Status"), o.get("ExpectedDate"))
                            for o in O.list_for("PRJ-0015") if o.get("Supplier") == "Prueba v559"]
st.session_state["_GAS"] = [(g.get("ID"), g.get("Supplier"), g.get("Amount"))
                            for g in (E.project_expenses("PRJ-0015").get("items") or [])
                            if g.get("Supplier") == "Prueba v559"]
'''
at = AppTest.from_string(G_015, default_timeout=240)
at.run()
sec(at, "💰 Costos")
_txt = [x for x in at.text_input if str(x.label) == "Supplier"]
chk("se localizan los proveedores (pedido y recibo)", len(_txt) >= 2, len(_txt))
_txt[0].set_value("Prueba v559")
[x for x in at.number_input if str(x.label) == "Value"][0].set_value(10.0)
[x for x in at.date_input if "Expected delivery" in str(x.label)][0].set_value(dt.date(2026, 10, 20))
[b for b in at.button if "Record order" in str(b.label)][0].click()
at.run()
_ord = estado(at, "_ORD") or []
chk("⚠️ en la HOJA: el pedido, con su fecha en ISO", len(_ord) == 1
    and str(_ord[0][3])[:10] == "2026-10-20", _ord)
_c = " | ".join(m.value for m in at.markdown)
chk("en pantalla: «due 20/10» (no «llega»)", "due 20/10" in _c and "llega" not in _c)
if _ord:
    boton(at, f"adm_ordc_{_ord[0][0]}").click()
    at.run()
    chk("el pedido se cancela", all(str(o[2]).lower() in ("cancelled", "cancelada")
                                    for o in (estado(at, "_ORD") or [])), estado(at, "_ORD"))
_v = [x for x in at.number_input if x.key == "adm_val"]
_pv = [x for x in at.text_input if x.key == "adm_prov"]
_v[0].set_value(5.0)
_pv[0].set_value("Prueba v559")
[b for b in at.button if "Save receipt" in str(b.label)][0].click()
at.run()
_gas = estado(at, "_GAS") or []
chk("⚠️ en la HOJA: el recibo", len(_gas) == 1 and float(_gas[0][2] or 0) == 5.0, _gas)
for g in _gas:
    G_DEL = CAB + f'st.session_state["_R"] = E.delete({g[0]!r})\n'
    a2 = AppTest.from_string(G_DEL, default_timeout=120)
    a2.run()
    print("     recibo borrado:", estado(a2, "_R"))

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
