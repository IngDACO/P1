"""v584 · FINANCE → ACCOUNTING, PROBADA ACCIÓN POR ACCIÓN (decisión del usuario: «ok dale»).

  1. ⚠️ Dos avisos de ABN, y el de la pantalla mandaba a «Administration → Companies», que
     no existe (es «Groups») y que el administrador —quien ve esta pantalla— no tiene → UNO,
     el del motor, con el sitio de verdad y quién lo pone (el propietario).
  2. ⚠️ El error de Xero Payroll daba una sola causa («needs Payroll AU set up») cuando Xero
     contesta igual si quien conectó no tiene permiso de nómina → las dos, y qué hacer.
  3. Con «All», los ficheros se llamaban `…_todo_todo.csv` → `…_all.csv`.
  4. «From» después de «To» en el parte salía vacío sin decir nada → aviso, y lo de Xero
     Payroll de debajo sigue.
  5. Las seis cifras, ACTIVAS.   6. Plurales («1 rows», «these 1 options», «the 1 jobs»).
  7. Periodo y formato, recordados.   8. «Saved.» → lo que cambia.
  9. «Bring payments from Xero» sin nada enviado → se dice sin hacer pulsar.
 10. «Payroll ID» en pantalla solo si alguien lo tiene (el CSV la conserva).
 11. TODO `st.date_input` de la app en DD/MM/YYYY (eran 10 sin él).

AppTest y el motor con sus fuentes sustituidas: ninguna hoja ni Xero se tocan.
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
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


import streamlit as st                                                      # noqa: E402
st.session_state["auth"] = {"usuario": "adm", "rol": "administrator", "grupo": "G"}
from core import contable, xero_nomina as XN, xero as X                    # noqa: E402

# ═════════════════════════════════════════════════════════════════
print("1. ⚠️ UN aviso de ABN, con el sitio de verdad (motor, EJECUTADO)")
_o = {n: getattr(contable, n) for n in ("mapa", "identidad", "_etiquetas", "fichas_clientes")}
_ol = contable.invoices.list_facturas
try:
    contable.mapa = lambda g: {}
    contable.identidad = lambda g: {"abn": "", "legal": "x", "plazo": 14}
    contable._etiquetas = lambda g: {}
    contable.fichas_clientes = lambda g: {}
    contable.invoices.list_facturas = lambda g: []
    _av = contable.csv_ventas("G", "xero")["avisos"]
    _abn = [a for a in _av if "ABN" in a]
    chk("un solo aviso de ABN en el motor", len(_abn) == 1, _av)
    chk("⚠️ …con el sitio REAL y quién lo pone (antes «Administration → Companies»)",
        _abn and "Administration → Groups → «Tax identity and payment terms»" in _abn[0]
        and "owner" in _abn[0], _abn)
finally:
    for _n, _v in _o.items():
        setattr(contable, _n, _v)
    contable.invoices.list_facturas = _ol
_cu = _src("core/contable_ui.py")
_lits_cu = [n.value for n in ast.walk(ast.parse(_cu)) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)]
chk("⚠️ la pantalla ya NO pinta su propio aviso (el segundo, el de la ruta inexistente)",
    not any("Administration → Companies" in x or "no ABN" in x for x in _lits_cu)
    and "identidad(" not in _cu)

print("\n6. Plurales")
_c = {k: "1" for k in contable.claves_de("xero")} if hasattr(contable, "claves_de") else None
_av1 = contable._avisos_comunes("xero", {}, [], {"categoria_seguimiento": "Project"}, True, ["A"])
_av2 = contable._avisos_comunes("xero", {}, [], {"categoria_seguimiento": "Project"}, True, ["A", "B"])
chk("Xero, UNA opción: «with this option» (salía «with these 1 options»)",
    any("with this option" in a for a in _av1) and not any("these 1" in a for a in _av1), _av1)
chk("…y con dos, «these 2 options»", any("these 2 options" in a for a in _av2), _av2)
_m1 = contable._avisos_comunes("myob", {}, [], {}, True, ["A"])
chk("MYOB, UNA obra: «the job must already exist» (salía «the 1 jobs»)",
    any("the job must already exist" in a for a in _m1), _m1)

print("\n2. ⚠️ Xero Payroll: las causas de verdad")
_oa = X._api
try:
    X._api = lambda *a, **k: (401, {"Title": "Unauthorized", "Detail": "AuthenticationUnsuccessful"}, {})
    _e = XN.datos("G")["error"]
    chk("con 401 dice las DOS causas (sin Payroll AU, o quien conectó no tiene permiso)",
        "no Payroll AU" in _e and "no payroll access" in _e and "connect again" in _e, _e)
    chk("…y ya no afirma una sola («needs Payroll AU set up»)", "needs Payroll AU set up" not in _e)
    X._api = lambda *a, **k: (500, {}, {})
    _e = XN.datos("G")["error"]
    chk("otro error (500) no culpa a los permisos", "could not be read" in _e and "payroll access" not in _e, _e)
finally:
    X._api = _oa

print("\n3, 7, 11. Lo que se mira en el código")
chk("«All» → `…_all.csv` (era «todo_todo»)", "'todo'" not in _cu and '"all"' in _cu)
_rad = [n for n in ast.walk(ast.parse(_cu)) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "radio"]
chk("periodo y formato se RECUERDAN (`persist_state`)",
    len(_rad) >= 2 and all(any(k.arg == "persist_state" for k in r.keywords) for r in _rad))
_sin = []
for _f in sorted(os.listdir(os.path.join(RAIZ, "core"))):
    if _f.endswith(".py"):
        for n in ast.walk(ast.parse(_src("core/" + _f))):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "date_input":
                _fm = next((ast.unparse(k.value) for k in n.keywords if k.arg == "format"), None)
                if _fm != "'DD/MM/YYYY'":
                    _sin.append("%s:%d %s" % (_f, n.lineno, _fm))
chk("⚠️ TODO `st.date_input` de la app en DD/MM/YYYY (eran 10 sin él)", not _sin, _sin)

# ═════════════════════════════════════════════════════════════════
from streamlit.testing.v1 import AppTest                                    # noqa: E402

CAB = r'''
import sys, datetime as dt
sys.path.insert(0, r"%s")
import streamlit as st
from core import contable_ui as CU, contable, xero_ui
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
st.session_state.setdefault("_LL", [])
_LL = st.session_state["_LL"]
_ABN = "This company has no ABN: … Administration → Groups → «Tax identity and payment terms»."
contable.csv_ventas = lambda g, p, d=None, h=None: {"csv": "a", "filas": 1, "documentos": 1,
    "avisos": [_ABN], "opciones": ["Job A"]}
contable.csv_compras = lambda g, p, d=None, h=None: {"csv": "b", "filas": 3, "documentos": 2,
    "avisos": [], "opciones": ["Job A"]}
contable.identidad = lambda g: {"abn": "", "legal": "x", "plazo": 14}
contable.mapa = lambda g: {}
_PID = st.session_state.get("_PID", "")
_D = [dt.date(2026, 10, 6), dt.date(2026, 10, 7)]
contable.csv_partes = lambda g, d, h: {"csv": "x", "filas": 1, "personas": 1, "total": 3.5,
    "avisos": [], "dias": _D}
contable.partes = lambda g, d, h: {"dias": _D, "filas": [{"nombre": "Ana", "payroll_id": _PID,
    "etiqueta": "Ordinary Hours", "horas": {_D[0]: 3.5}, "total": 3.5}], "avisos": []}
xero_ui.render_conexion = lambda g, d=None, h=None: _LL.append("conexion")
xero_ui.render_partes_xero = lambda g: _LL.append("partes_xero")
if "_INI" not in st.session_state:
    st.session_state["_INI"] = 1
    for _k, _v in (st.session_state.get("_PRE") or {}).items():
        st.session_state[_k] = _v
CU.render_contable("G")
''' % RAIZ


def _app(pre=None, pid=""):
    a = AppTest.from_string(CAB, default_timeout=90)
    if pre:
        a.session_state["_PRE"] = pre
    a.session_state["_PID"] = pid
    a.run()
    return a


def _ss(a, k, d=None):
    try:
        return a.session_state[k]
    except KeyError:
        return d


def _kb(a):
    return {b.key: b.label for b in a.button}


def _desplegado(a, texto):
    """¿Abierto? ⚠️ Un `st.expander` con `icon=` AppTest lo clasifica como «Status»."""
    return any(e.proto.expanded for e in list(a.expander) + list(a.status)
               if texto in str(e.label))


def _tabla_parte(a):
    return next((d.value for d in a.dataframe if "Employee" in list(d.value.columns)), None)


def _textos(a):
    return " | ".join([str(x.value) for x in list(a.info) + list(a.error) + list(a.warning)
                       + list(a.success) + list(a.caption) + list(a.markdown)])


print("\n1, 5, 6. La pantalla: el aviso, y las cifras ACTIVAS")
at = _app()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ el ABN, UNA vez", _textos(at).count("no ABN") == 1, _textos(at).count("no ABN"))
_b = _kb(at)
chk("las 3 cifras de arriba son botones", all(k in _b for k in ("cpxkpi_cont_fac", "cpxkpi_cont_gas",
    "cpxkpi_cont_seg")), [k for k in _b if "cpxkpi_cont" in str(k)])
chk("«1 row» en singular (salía «1 rows») y «3 rows»",
    _b.get("cpxkpi_cont_fac") == "Invoices\n\n1\n\n1 row" and _b.get("cpxkpi_cont_gas") == "Expenses\n\n2\n\n3 rows",
    (_b.get("cpxkpi_cont_fac"), _b.get("cpxkpi_cont_gas")))
chk("«1 job involved»", "1 job involved" in _b.get("cpxkpi_cont_seg", ""), _b.get("cpxkpi_cont_seg"))
at.button(key="cpxkpi_cont_fac").click()
at.run()
chk("Invoices lleva a Finance → Invoices", tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "🧾 Facturas"),
    _ss(at, "_admin_nav_pending"))
at = _app()
at.button(key="cpxkpi_cont_gas").click()
at.run()
chk("Expenses, a Finance → Expenses", tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "💰 Gastos"),
    _ss(at, "_admin_nav_pending"))
at = _app()
at.button(key="cpxkpi_cont_seg").click()
at.run()
chk("Tracking options ABRE la lista de obras (y baja a ella)",
    _ss(at, "_cont_ver_jobs") is True and _desplegado(at, "Jobs that must")
    and ".st-key-ir_cpx_cont_jobs" in _textos(at), [str(e.label) for e in at.status])
at.button(key="cpxkpi_cont_seg").click()
at.run()
chk("…y otro toque la cierra", not _ss(at, "_cont_ver_jobs") and not _desplegado(at, "Jobs that must")
    and any("Jobs that must" in str(e.label) for e in at.status))

print("\n4, 5, 10. El parte")
at = _app()
_b = _kb(at)
chk("las 3 cifras del parte son botones", all(k in _b for k in ("cpxkpi_contp_pers", "cpxkpi_contp_horas",
    "cpxkpi_contp_lin")), [k for k in _b if "cpxkpi_contp" in str(k)])
chk("«2 days in the period»", "2 days in the period" in _b.get("cpxkpi_contp_horas", ""))
at.button(key="cpxkpi_contp_pers").click()
at.run()
chk("People lleva a Finance → Hours", tuple(_ss(at, "_admin_nav_pending") or ()) == ("finanzas", "⏱ Horas"))
at = _app()
at.button(key="cpxkpi_contp_lin").click()
at.run()
chk("Lines baja a la tabla", ".st-key-ir_cpx_cont_ptabla" in _textos(at))
_df = _tabla_parte(at)
chk("⚠️ sin Payroll ID de nadie, la columna NO sale (era una columna vacía)",
    _df is not None and "Payroll ID" not in _df.columns, list(_df.columns) if _df is not None else None)
at = _app(pid="E-17")
_df = _tabla_parte(at)
chk("…con uno, sí", _df is not None and "Payroll ID" in _df.columns)
at = _app(pre={"cont_p_d": dt.date(2026, 10, 19), "cont_p_h": dt.date(2026, 10, 6)})
chk("⚠️ «From» después de «To» lo DICE (salía vacío sin decir nada)",
    "«From» is after «To»" in _textos(at), _textos(at)[:200])
chk("…y lo de Xero Payroll de debajo SIGUE", "partes_xero" in (_ss(at, "_LL") or []), _ss(at, "_LL"))

print("\n8, 9. Xero: lo que cambia, y «Bring payments» solo con algo enviado")
CAB2 = r'''
import sys
sys.path.insert(0, r"%s")
import importlib
import streamlit as st
from core import xero_ui, xero as X, contable, invoices
importlib.reload(xero_ui)   # ⚠️ la prueba de la pantalla la dejó sustituida (mismo proceso)
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "grupo": "G"}
X.configuracion = lambda: {"ok": True, "faltan": [], "problemas": [], "redirect": ""}
X.estado = lambda g: {"conectada": True, "estado": "connected", "tenant": "Demo", "desde": "x",
                      "por": "adm", "tenant_id": "T"}
X.estado_envio = lambda g: st.session_state.get("_EST", "DRAFT")
contable.mapa = lambda g: {"cuentas": {"xero": {contable.VENTAS: "200"}}}
def _gc(g, c):
    st.session_state["_EST"] = c.get("xero_estado")
    return True, "ok"
contable.guardar_claves = _gc
xero_ui._pendientes = lambda g, d, h: {"pendientes": [], "enviables": 0}
_F = [{"ID": "FAC-1", "XeroInvoiceID": st.session_state.get("_XID", "")}]
invoices.list_facturas = lambda g: _F
from core import flash
flash.mostrar()
xero_ui.render_conexion("G")
''' % RAIZ
at = AppTest.from_string(CAB2, default_timeout=60)
at.run()
chk("sin ninguna factura enviada, NO hay botón «Bring payments» y se dice por qué",
    "xero_traer_cobros" not in _kb(at) and "No invoice has been sent to Xero yet" in _textos(at),
    list(_kb(at)))
at.radio(key="cpxseg_xero_estado").set_value("AUTHORISED")
at.run()
chk("⚠️ cambiar a «Approved» dice lo que cambia (decía «Saved.»)",
    "Invoices will now arrive in Xero approved." in _textos(at), _textos(at)[:200])
at = AppTest.from_string(CAB2, default_timeout=60)
at.session_state["_XID"] = "abc"
at.run()
chk("…con una enviada, el botón está", "xero_traer_cobros" in _kb(at))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
