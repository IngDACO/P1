# -*- coding: utf-8 -*-
"""v703 · ciclo 7, mejoras 3/4: lo pequeño (D2 y los H de compras, nómina, horas y pantallas).

D2  la cantidad escala la ganancia de la línea (se conserva el %); lo tecleado manda.
H1  tras cambiar la cantidad, la tabla se renueva (enseñaba el costo, el % y el precio de antes).
H3  sin plano, las paradas salen de las líneas «por parada».
H5  la orden de compra: el formulario se vacía al GUARDAR y avisa de una igual de hace minutos.
H6  el estado de la orden con mayúscula · H7 «Order received… ($39,000.00)» con su «$».
H9  la vista previa de la nómina cuenta las ausencias pagadas · H10 el día olvidado antes del inicio de la obra.
H14 reanudar una obra en pausa: «Job restarted.», el aviso a la cuadrilla y «Plan it».
H18 lo marcado sin guardar y «Save all», DEBAJO de la lista de etapas.
H8  barras con anchos flexibles (y la etiqueta escapada) · H15 un aviso de opciones de seguimiento, no dos.
H22 «In Xero since 23/11/2026 17:38» · H24 «-$20,811.60» · H25 un neto por certificación · H26 anular avisa de la
certificación.

Sin red ni escrituras: sustitutos guardados al principio y devueltos al acabar (trampa 48).
"""
import ast
import io
import json
import os
import sys
import tokenize
from datetime import datetime

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def fuente(rel):
    return open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def sin_comentarios(src):
    """El código sin comentarios ni docstrings (trampa 2: un comentario mío no es uso)."""
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            continue
        out.append(tok.string if tok.type != tokenize.STRING or not tok.string.startswith(('"""', "'''")) else '""')
    return " ".join(out)


def funcion(src, nombre):
    return next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


def seg(src, nombre):
    n = funcion(src, nombre)
    return ast.get_source_segment(src, n) if n else ""


import streamlit                                                               # noqa: E402
from streamlit.testing.v1 import AppTest                                      # noqa: E402
from core import (quotes_ui as QU, catalogo as CAT, orders as O, clock, projects_ui as PU, projects as P,  # noqa: E402
                  alerts, notify, auth, contable, claims_ui as CLU, xero as X)

_G = {}


def guarda(mod, *nombres):
    for n in nombres:
        _G[(mod, n)] = getattr(mod, n)


def devuelve():
    for (mod, n), f in _G.items():
        setattr(mod, n, f)


# todo lo que los guiones de AppTest sustituyen (corren en ESTE proceso)
guarda(streamlit, "data_editor")
guarda(CAT, "list_items", "etiqueta_items")
guarda(O, "list_for")
guarda(clock, "now")
guarda(P, "update_project")
guarda(alerts, "notify_change")
guarda(notify, "notify_assignment", "notify_induction")
guarda(auth, "list_users")
guarda(PU, "_autoagenda")
guarda(X, "estado", "url_factura")

L0 = {"catalogo_id": "CAT-1", "tipo": "material", "concepto": "Landing door set (per stop)", "descripcion": "",
      "unidad": "per stop", "cantidad": 1.0, "horas": 0.0, "costo_unit": 1000.0, "costo_total": 1000.0,
      "margen_pct": 25.0, "precio_total": 1250.0}

ED = r'''
import json
import pandas as pd
import streamlit as st
from core import quotes_ui as QU, catalogo as CAT
CAT.list_items = lambda g: [{"ID": "CAT-1", "Name": "Landing door set (per stop)"}]
CAT.etiqueta_items = lambda items: {"CAT-1": "Landing door set (per stop)"}


def _fake(df, **kw):
    st.session_state.setdefault("_KEYS", []).append(kw.get("key"))
    out = df.copy()
    for (i, col, v) in st.session_state.pop("_EDIT", []):
        out.loc[i, col] = v
    return out


st.data_editor = _fake
L = st.session_state.get("new_lineas", [dict(st.session_state["_L0"])])
L = QU._editor_lineas("G", "new", L)
st.session_state["new_lineas"] = L
st.session_state["_RES"] = json.dumps(L)
'''


def editor(edits):
    a = AppTest.from_string(ED, default_timeout=60)
    a.session_state["_L0"] = dict(L0)
    a.run()
    a.session_state["_KEYS"] = []
    a.session_state["_EDIT"] = edits
    a.run()
    return a, json.loads(a.session_state["_RES"]), list(a.session_state["_KEYS"])


try:
    print("A. D2 + H1: la cantidad de una línea de cotización")
    a, res, keys = editor([(0, "Cant.", 8.0)])
    chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
    l = res[0] if res else {}
    chk("D2: 1 → 8 puertas con la ganancia sin tocar: 8 × $250 = $2,000 (el 25 % se conserva)",
        l.get("cantidad") == 8.0 and l.get("costo_total") == 8000.0 and l.get("precio_total") == 10000.0
        and abs(float(l.get("margen_pct", 0)) - 25.0) < 0.01, l)
    chk("H1: la tabla se RENUEVA (otra clave: «new_ed_0» → «new_ed_1») y se guarda en «new_lineas»",
        keys[:1] == ["new_ed_0"] and keys[-1:] == ["new_ed_1"] and a.session_state["new_lineas"][0]["cantidad"] == 8.0,
        keys)
    a, res, keys = editor([(0, "Cant.", 8.0), (0, "Ganancia $", 500.0)])
    l = res[0] if res else {}
    chk("D2: con la ganancia TECLEADA a la vez ($500), manda lo tecleado (v355)",
        l.get("cantidad") == 8.0 and l.get("precio_total") == 8500.0, l)
    a, res, keys = editor([(0, "Ganancia $", 300.0)])
    l = res[0] if res else {}
    chk("solo la ganancia ($300): no escala nada ni renueva la tabla", l.get("cantidad") == 1.0
        and l.get("precio_total") == 1300.0 and keys == ["new_ed_0"], (l, keys))
    _ed_src = seg(fuente("core/quotes_ui.py"), "_editor_lineas")
    chk("…y la regla mira la cantidad de ANTES contra la de la tabla (no relanza sin cambio)",
        "abs(cant - _c0) > 1e-9" in _ed_src and "_g0 * cant / _c0" in _ed_src, _ed_src[-900:])

    print("\nB. H3: las paradas de las líneas «por parada»")
    chk("C7: «Landing door set (per stop)» ×8 → 8", QU._ns_por_parada([dict(L0, cantidad=8)]) == 8)
    chk("la unidad «stop» también, y gana la mayor", QU._ns_por_parada(
        [{"unidad": "stop", "cantidad": 5, "concepto": "Door"}, {"unidad": "", "cantidad": 12,
                                                                  "concepto": "Lift — 12 per stop"}]) == 12)
    chk("una línea que no es por parada no cuenta (Delivery ×3 → 0)",
        QU._ns_por_parada([{"unidad": "each", "cantidad": 3, "concepto": "Delivery & transport"}]) == 0)
    _cp = seg(fuente("core/quotes_ui.py"), "_crear_proyecto")
    chk("el alta la usa SOLO sin plano, y lo dice («From the «per stop» lines of the quote.»)",
        "_ns_por_parada(Q.lineas_de(c)) if _ns_pl < 2 else 0" in _cp
        and "From the «per stop» lines of the quote." in _cp, _cp[:400])

    print("\nC. H5: la orden de compra repetida")
    _ahora = datetime(2026, 11, 23, 10, 30)
    clock.now = lambda *a, **k: _ahora
    _ords = [{"ID": "ORD-00005", "Group": "G", "Supplier": "Schindler  Parts", "Amount": "77000",
              "Description": "Guide rails T89", "Status": "pendiente", "Created": "2026-11-23 10:22:10"},
             {"ID": "ORD-00004", "Group": "G", "Supplier": "Bunnings", "Amount": "50", "Description": "Anchors",
              "Status": O.CANCELADA, "Created": "2026-11-23 10:29:00"},
             {"ID": "ORD-00003", "Group": "G", "Supplier": "Bunnings", "Amount": "120", "Description": "Silicone",
              "Status": "pendiente", "Created": "2026-11-23 09:00:00"}]
    O.list_for = lambda pid, estado=None: [dict(x) for x in _ords]
    r = O.igual_reciente("PRJ-1", "schindler parts", 77000, "guide rails  t89")
    chk("igual de hace 8 min (mayúsculas y espacios aparte) → ORD-00005, 8 min", r == {"id": "ORD-00005", "minutos": 8}, r)
    chk("otro importe → nada", O.igual_reciente("PRJ-1", "Schindler Parts", 77001, "Guide rails T89") is None)
    chk("una cancelada no cuenta", O.igual_reciente("PRJ-1", "Bunnings", 50, "Anchors") is None)
    chk("una de hace 90 min no cuenta (15 por defecto)", O.igual_reciente("PRJ-1", "Bunnings", 120, "Silicone") is None)
    _os = seg(fuente("core/projects_ui.py"), "_ordenes_section")
    chk("el formulario cambia de generación al GUARDAR (con lo tecleado si se rechaza), no con «clear_on_submit»",
        'f"{key_prefix}_ordnew_{pid}_{_ogen}"' in _os and "clear_on_submit" not in sin_comentarios(_os)
        and 'st.session_state[f"_{key_prefix}_ordgen_{pid}"] = _ogen + 1' in _os, _os[-1500:])
    # el aviso, SOLO si se creó (con un `st.rerun()` que se ejecuta detrás: trampa 41)
    _fn = funcion(fuente("core/projects_ui.py"), "_ordenes_section")
    _ifs = [n for n in ast.walk(_fn) if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "ok"
            and "igual_reciente" not in ast.unparse(n.test)]
    _con = [n for n in _ifs if "An identical order was recorded" in ast.unparse(n)]
    chk("…y el aviso de la igual va DENTRO de `if ok:`, con su `st.rerun()`", len(_con) == 1
        and "st.rerun()" in ast.unparse(_con[0].body[-1]) and "_igual = O.igual_reciente" in _os
        and _os.index("_igual = O.igual_reciente") < _os.index("ok, msg = O.crear("), [ast.unparse(n)[:200] for n in _ifs])
    # la mecánica que se usa: un formulario con OTRA clave nace vacío (sus campos van sin clave propia)
    MINI = r'''
import streamlit as st
g = st.session_state.get("g", 0)
with st.form(f"f_{g}", enter_to_submit=False):
    v = st.text_input("Supplier")
    if st.form_submit_button("Record order"):
        st.session_state["visto"] = v
'''
    m = AppTest.from_string(MINI, default_timeout=30)
    m.run()
    m.text_input[0].input("Bunnings")
    m.button[0].click()
    m.run()
    _visto = m.session_state["visto"]
    m.session_state["g"] = 1
    m.run()
    chk("(la mecánica) con otra clave de formulario, la caja nace vacía", _visto == "Bunnings"
        and m.text_input[0].value == "", (_visto, m.text_input[0].value))

    print("\nD. H6, H7, H9 y H10")
    chk("H6: el estado de la orden por `i18n.estado` («Pending»)", "{_est_txt(_est)} · ordered" in _os)
    _mr = seg(fuente("core/orders.py"), "marcar_recibida")
    chk("H7: «Order received and charged to the project ($39,000.00).»", "(${valor:,.2f})." in _mr, _mr[-300:])
    _pay = fuente("core/payroll_ui.py")
    chk("H9: la vista previa suma las ausencias pagadas, de la MISMA función que `generar`",
        "_AUP.horas_pagadas_grupo(grupo, desde, hasta)" in _pay and '"LeavePay"' in _pay
        and 'horas.setdefault(_k, {"nombre"' in _pay)
    _gen = fuente("core/payroll.py")
    chk("…(la que usa `generar`)", "horas_pagadas_grupo" in _gen)
    _do = seg(fuente("core/projects_ui.py"), "dia_olvidado_section")
    chk("H10: el día olvidado ANTES del inicio de la obra avisa (no bloquea)",
        "This job starts on {s}: is the day right?" in _do and "if _ini_o and _dia < _ini_o:" in _do)

    print("\nE. H14: reanudar una obra en pausa")
    RE = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, alerts, notify, auth
P.update_project = lambda pid, campos: st.session_state.setdefault("_UPD", []).append(dict(campos))
alerts.notify_change = lambda pid, g, txt, quien, dest, nombre: st.session_state.setdefault("_AV", []).append(
    (txt, list(dest)))
notify.notify_assignment = lambda u, info: {"email": True}
notify.notify_induction = lambda *a, **k: None
auth.list_users = lambda g=None: [{"User": "campo000", "Name": "hjg,ujgjg"}, {"User": "helper1", "Name": "helper 1"},
                                  {"User": "nuevo1", "Name": "New One"}]
PU._autoagenda = lambda *a, **k: None
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": st.session_state.get("_ROL", "administrator"),
                                     "grupo": "G", "nombre": "Bobo"})
if st.session_state.get("_GUARDAR"):
    st.session_state["_GUARDAR"] = False
    PU._guardar_datos_obra("PRJ-T", "G", st.session_state["_PRJ"], st.session_state["_CAMPOS"],
                           st.session_state["_CTX"])
_r = st.session_state.get("_prj_reanudada_PRJ-T")
if _r:
    PU._aviso_reanudada("PRJ-T", _r)
'''
    _ctx = {"nombre": "C7 — Lift 1", "cliente": "C7", "ubic": "", "f_ini": "2026-11-23", "f_fin": "2027-01-06",
            "ind": "", "asignados": ["campo000", "helper1", "nuevo1"], "actuales": ["campo000", "helper1"]}

    def reanudar(prev, nuevo, rol="administrator"):
        r = AppTest.from_string(RE, default_timeout=60)
        r.session_state["_GUARDAR"] = True
        r.session_state["_ROL"] = rol
        r.session_state["_PRJ"] = {"ID": "PRJ-T", "ManualStatus": prev, "InductionLinks": ""}
        r.session_state["_CAMPOS"] = {"ManualStatus": nuevo}
        r.session_state["_CTX"] = dict(_ctx)
        r.run()
        return r

    r = reanudar("On hold", "")
    chk("sin excepción", not r.exception, [e.value for e in r.exception][:1])
    _av = list(r.session_state["_AV"]) if "_AV" in r.session_state else []
    chk("la cuadrilla (los que ya estaban) recibe «This job has restarted…», no «The project details were updated.»",
        len(_av) == 1 and "restarted" in _av[0][0] and _av[0][1] == ["campo000", "helper1"], _av)
    _suc = " ".join(str(x.value) for x in r.success)
    chk("«Job restarted.» con a cuántos se avisó (2) — y el nuevo, por su asignación",
        "Job restarted." in _suc and "2 field user(s) told they are back on it." in _suc
        and any("New One" in str(c.value) for c in r.caption), (_suc, [c.value for c in r.caption]))
    _btn = {str(b.key): str(b.label) for b in r.button}
    chk("…con «Plan it» y «Not now»", "reanudada_plan_PRJ-T" in _btn and "Plan it" in _btn["reanudada_plan_PRJ-T"]
        and "Not now" in _btn.get("reanudada_no_PRJ-T", ""), _btn)
    _fq = [x for x in (r.session_state["_flash_cola"] if "_flash_cola" in r.session_state else [])]
    chk("…y NO el «Changes saved.» suelto", not any("Changes saved" in x[1] for x in _fq), _fq)
    r.button(key="reanudada_plan_PRJ-T").click()
    r.run()
    chk("«Plan it» → Planning → Assign con la obra, y el aviso se va",
        r.session_state["_admin_nav_pending"] == ("planificacion", "🎛 Panel")
        and r.session_state["ai_prj"] == "PRJ-T" and r.session_state["_panel_tool"] == "asignar"
        and "_prj_reanudada_PRJ-T" not in r.session_state, "")
    r = reanudar("Cancelled", "")
    chk("una cancelada que vuelve, también («restarted»)", "_prj_reanudada_PRJ-T" in r.session_state
        and "restarted" in r.session_state["_AV"][0][0])
    r = reanudar("", "")
    chk("guardar sin cambiar el estado: «Changes saved.» y el aviso de siempre", "_prj_reanudada_PRJ-T" not in r.session_state
        and any("Changes saved" in x[1] for x in r.session_state["_flash_cola"])
        and r.session_state["_AV"][0][0] == "The project details were updated.")
    r = reanudar("On hold", "On hold")
    chk("seguir en pausa no es reanudar", "_prj_reanudada_PRJ-T" not in r.session_state)
    r = reanudar("On hold", "", rol="owner")
    _btn = {str(b.key): str(b.label) for b in r.button}
    chk("el propietario (sin Planning): «Job restarted.» sin «Plan it»", "reanudada_plan_PRJ-T" not in _btn
        and "reanudada_no_PRJ-T" in _btn and "Job restarted." in " ".join(str(x.value) for x in r.success), _btn)
    _dp = seg(fuente("core/projects_ui.py"), "_detalle_proyecto")
    chk("la ficha lo pinta encima del formulario de datos (y no a la vez que la pausa)",
        "_aviso_reanudada(pid, _reanudada)" in _dp and "if _reanudada and not _cierre_pend:" in _dp
        and _dp.index("_aviso_reanudada(pid, _reanudada)") < _dp.index('with st.form(f"edit_{pid}"'))

    print("\nF. H18: lo marcado sin guardar, debajo de la lista")
    _sp = fuente("core/stage_progress_ui.py")
    _fr = funcion(_sp, "render")
    _loop = next((n for n in ast.walk(_fr) if isinstance(n, ast.For) and ast.unparse(n.target) == "e"
                  and ast.unparse(n.iter) == "_det"), None)
    _sa = [n.lineno for n in ast.walk(_fr) if isinstance(n, ast.Call) and "_save_all_" in ast.unparse(n)]
    _uns = [n.lineno for n in ast.walk(_fr) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and "unsaved ticks" in n.value]
    chk("«Save all» y el aviso, DESPUÉS del bucle de etapas (aparecer no mueve ninguna casilla)",
        _loop is not None and _sa and _uns and min(_sa + _uns) > _loop.end_lineno, (_sa, _uns, getattr(_loop, "end_lineno", None)))

    print("\nG. H8: las barras")
    _b = PU._barras_html([("Smith <b>& Co</b>", 300.0), ("Labour", 700.0)], 1000.0)
    chk("sin anchos fijos (118/96/42 px con flex:none)", "width:118px" not in _b and "width:96px" not in _b
        and "width:42px" not in _b and "flex:none" not in _b, _b[:400])
    chk("la etiqueta cede y la barra guarda un mínimo", "flex:0 1 118px;min-width:40px" in _b
        and "flex:1 1 40px;min-width:28px" in _b)
    chk("la etiqueta, ESCAPADA (llegan nombres de la hoja)", "Smith &lt;b&gt;&amp; Co&lt;/b&gt;" in _b
        and "<b>&" not in _b)
    chk("…y las cifras de siempre", "$300" in _b and "30%" in _b and "70%" in _b)

    print("\nH. H15: un aviso de opciones de seguimiento")
    _cfg = {"categoria_seguimiento": "Project"}
    chk("los CSV ya no lo dicen (`con_opciones=False`)", not contable._avisos_comunes(
        "xero", {}, [], _cfg, True, ["A", "B"], con_opciones=False))
    chk("…por defecto sí (verif_v584 lo llama así)", any("these 2 options" in x for x in contable._avisos_comunes(
        "xero", {}, [], _cfg, True, ["A", "B"])))
    _uno = contable.aviso_opciones("xero", _cfg, True, sorted({"A", "B"} | {"B", "C", "D", "E", "F"}))
    chk("la pantalla: UNO, con las de los dos ficheros (2 y 5, con una en común → 6)",
        len(_uno) == 1 and "these 6 options" in _uno[0], _uno)
    _cm = fuente("core/contable.py")
    chk("csv_ventas y csv_compras lo piden sin opciones", _cm.count("cfg, seg, opciones, con_opciones=False)") == 2)
    # la llamada MISMA (la unión sale también en la cifra y en la lista de obras: buscar el texto pasaría en vacío)
    _ao = [n for n in ast.walk(ast.parse(fuente("core/contable_ui.py"))) if isinstance(n, ast.Call)
           and ast.unparse(n.func) == "contable.aviso_opciones"]
    _arg = ast.unparse(_ao[0].args[3]) if _ao and len(_ao[0].args) >= 4 else ""
    chk("Accounting lo dice UNA vez, con la UNIÓN de las opciones de los dos ficheros", len(_ao) == 1
        and "ventas['opciones']" in _arg and "compras['opciones']" in _arg and "|" in _arg, _arg)

    print("\nI. H22: «In Xero since» en DD/MM/YYYY HH:MM")
    XS = r'''
import streamlit as st
from core import xero_ui, xero as X
X.estado = lambda g: {"short_code": "!abc"}
X.url_factura = lambda sc, xid: "https://go.xero.com/x"
xero_ui.boton_factura("G", {"ID": "FAC-0007", "XeroInvoiceID": "xid-1", "XeroSentAt": "2026-11-23 17:38:31"})
'''
    x = AppTest.from_string(XS, default_timeout=30)
    x.run()
    _c = " ".join(str(c.value) for c in x.caption)
    chk("«In Xero since 23/11/2026 17:38» (era «2026-11-23 17:38:31»)", "In Xero since 23/11/2026 17:38" in _c
        and "2026-11-23" not in _c, _c)

    print("\nJ. H24, H25 y H26: facturas y certificaciones")
    _iu = fuente("core/invoices_ui.py")
    _im = _iu[_iu.index('"Importe":  st.column_config.NumberColumn('):][:200]
    chk("H24: el importe de las líneas con «dollar» («-$20,811.60», no «$-20,811.60»)", 'format="dollar"' in _im, _im)
    _ln = CLU._linea_claim({"Number": "2", "Date": "2026-11-23", "PctComplete": "10.6", "Retention": "390.57"},
                           5214.75, 2206.03).replace("\\", "")
    chk("H25: un solo neto, el de su factura, con el depósito al lado",
        _ln.count("net ") == 1 and "net $5,214.75" in _ln and "deposit $2,206.03" in _ln
        and "retention $390.57" in _ln and "23/11/2026" in _ln and "10.6%" in _ln, _ln)
    _ln0 = CLU._linea_claim({"Number": "1", "Date": "2026-10-01", "PctComplete": "10", "Retention": "100"},
                            1900.0).replace("\\", "")
    chk("…sin depósito, como siempre (sin «deposit»)", "deposit" not in _ln0 and "net $1,900.00" in _ln0, _ln0)
    _cl = sin_comentarios(fuente("core/claims_ui.py"))
    chk("…y ya no hay «net after deposit» (el segundo neto)", "net after deposit" not in _cl)
    _ren = seg(fuente("core/claims_ui.py"), "render")
    chk("…el neto de la línea y el de «Cancel claim» salen de la factura (`_neto - _dep_l`)",
        "_linea_claim(r, _neto - _dep_l, _dep_l)" in _ren and "m=_dinero(_neto - _dep_l)" in _ren)
    chk("H26: la caja «Void invoice» dice que cancela su certificación, y la confirmación también",
        "voiding it cancels that claim" in _iu and "Claim #{n} is cancelled too." in _iu
        and "_CL.es_ultima(c)" in _iu and _iu.count('+ _y_cl)') == 2, _iu.count('+ _y_cl)'))
finally:
    devuelve()

print("\nK. Compila y sin nombres sueltos")
import py_compile                                                              # noqa: E402
for f in ("core/quotes_ui.py", "core/orders.py", "core/projects_ui.py", "core/payroll_ui.py", "core/stage_progress_ui.py",
          "core/contable.py", "core/contable_ui.py", "core/xero_ui.py", "core/invoices_ui.py", "core/claims_ui.py"):
    try:
        py_compile.compile(os.path.join(RAIZ, f), doraise=True)
        ok = True
    except Exception as e:
        ok = False
        print(e)
    chk("compila " + f, ok)

print()
print("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}")
sys.exit(1 if FALLOS else 0)
