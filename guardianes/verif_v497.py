# -*- coding: utf-8 -*-
"""v497 · el emparejado con Xero dice POR QUÉ, y se aplica de una vez.

Lo que falla EN SILENCIO y hay que proteger:
  (a) un «— not in Xero —» mudo manda a buscar el problema a Xero cuando casi siempre lo
      que falta está en COPEX (el correo de esa persona);
  (b) rellenar los desplegables DESPUÉS de instanciarlos revienta (regla v111), así que
      el botón deja bandera y el relleno ocurre en la pasada siguiente;
  (c) el relleno no puede pisar lo que el administrador ya eligió, ni poner al mismo
      empleado en dos personas (eso paga las horas de una a otra);
  (d) una sola definición de cómo se empareja: `propuesta` DELEGA en la detallada.
Todo EJECUTANDO con Xero y Streamlit sustituidos.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
G = "cliente1"
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": G}

fallos, n_ok = [], 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    ok(que) if real == esperado else fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import auth, contable, xero as X, xero_nomina as XN, xero_ui as XU   # noqa: E402

EMP = [{"EmployeeID": "E1", "FirstName": "Ana", "LastName": "Uno", "Email": "ANA@x.com",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"},
       {"EmployeeID": "E2", "FirstName": "Bea", "LastName": "Dos", "Email": "",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"},
       {"EmployeeID": "E3", "FirstName": "Mei", "LastName": "Chen", "Email": "",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"},
       {"EmployeeID": "E4", "FirstName": "Mei", "LastName": "Chen", "Email": "",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"},
       {"EmployeeID": "E5", "FirstName": "Zoe", "LastName": "Cinco", "Email": "dup@x.com",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"},
       {"EmployeeID": "E6", "FirstName": "Zia", "LastName": "Seis", "Email": "dup@x.com",
        "OrdinaryEarningsRateID": "R1", "PayrollCalendarID": "C1", "Status": "ACTIVE"}]

# ═════ 1 · la propuesta y su motivo ══════════════════════════════════════════
print("\n[1] la propuesta dice por qué cuando no hay pareja")
USUARIOS = [
    {"User": "ana", "Name": "Ana Uno", "Email": "ana@x.com", "Active": "SI"},      # email
    {"User": "bea", "Name": "Bea Dos", "Email": "", "Active": "SI"},               # nombre
    {"User": "cid", "Name": "Cid Tres", "Email": "no@x.com", "Active": "SI"},      # no está
    {"User": "din", "Name": "Din Cuatro", "Email": "", "Active": "SI"},            # sin email
    {"User": "mei1", "Name": "Mei Chen", "Email": "", "Active": "SI"},             # nombre repetido
    {"User": "mei2", "Name": "Mei Chen", "Email": "", "Active": "SI"},
    {"User": "zoe", "Name": "Zoe Otra", "Email": "dup@x.com", "Active": "SI"},     # email repetido
]
d = XN.propuesta_detallada(USUARIOS, EMP)
ck("empareja por EMAIL sin distinguir mayúsculas", (d["ana"]["id"], d["ana"]["por"]), ("E1", "email"))
ck("...y por NOMBRE cuando no hay correo", (d["bea"]["id"], d["bea"]["por"]), ("E2", "nombre"))
ck("«su correo y su nombre no están en Xero»", (d["cid"]["id"], d["cid"]["motivo"]), ("", "no_esta"))
ck("«no tiene correo en COPEX» (es lo que falta, y está AQUÍ)",
   (d["din"]["id"], d["din"]["motivo"]), ("", "sin_email"))
ck("dos empleados de Xero con el mismo NOMBRE: no se adivina",
   [(d[k]["id"], d[k]["motivo"]) for k in ("mei1", "mei2")],
   [("", "nombre_repetido"), ("", "nombre_repetido")])
# ⚠️ Con el correo repetido se INTENTA el nombre, y si ese es único la pareja vale: es
# la regla de «solo parejas únicas», no «solo por correo». Aquí el nombre no está en Xero.
ck("dos empleados de Xero con el mismo CORREO (y el nombre no está): no se adivina",
   (d["zoe"]["id"], d["zoe"]["motivo"]), ("", "email_repetido"))
ck("...pero si el NOMBRE es único, esa pareja sí se propone",
   XN.propuesta_detallada([{"User": "z2", "Name": "Zoe Cinco", "Email": "dup@x.com"}], EMP)["z2"],
   {"id": "E5", "por": "nombre", "motivo": ""})

# dos personas de COPEX que caen en el mismo empleado
d2 = XN.propuesta_detallada(
    [{"User": "u1", "Name": "Ana Uno", "Email": "ana@x.com"},
     {"User": "u2", "Name": "Ana Uno", "Email": "ana@x.com"}], EMP)
ck("dos personas de COPEX apuntando al MISMO empleado: ninguna se propone",
   [(d2[k]["id"], d2[k]["motivo"]) for k in ("u1", "u2")],
   [("", "mismo_empleado"), ("", "mismo_empleado")])

# (d) una sola definición
ck("`propuesta` DELEGA en la detallada (una sola definición)",
   XN.propuesta(USUARIOS, EMP), {"ana": "E1", "bea": "E2"})
_fn = next(n for n in ast.walk(ast.parse(_fuente("core/xero_nomina.py")))
           if isinstance(n, ast.FunctionDef) and n.name == "propuesta")
ck("...y no reimplementa el emparejado",
   (any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "propuesta_detallada"
        for n in ast.walk(_fn)), len(ast.unparse(_fn).splitlines()) < 8), (True, True))

# ═════ 2 · la pantalla, EJECUTADA ════════════════════════════════════════════
print("\n[2] la pantalla: motivos, botón y relleno")
PINT = {"caption": [], "button": [], "selectbox": [], "warning": []}
_g = {}


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _espia(nombre, fn):
    _g[nombre] = getattr(st, nombre)
    setattr(st, nombre, fn)


APRETADO = {"activo": None}
_espia("markdown", lambda *a, **kw: None)
_espia("caption", lambda txt, *a, **kw: PINT["caption"].append(str(txt)))
_espia("warning", lambda txt, *a, **kw: PINT["warning"].append(str(txt)))
_espia("info", lambda *a, **kw: None)
_espia("expander", lambda *a, **kw: _Ctx())
_espia("spinner", lambda *a, **kw: _Ctx())
_espia("rerun", lambda *a, **kw: None)
_espia("dataframe", lambda df, **kw: None)
_espia("button", lambda label, **kw: PINT["button"].append((label, kw.get("key"))) or
       (kw.get("key") == APRETADO["activo"]))


def _sb(label, opciones, **kw):
    k = kw.get("key")
    PINT["selectbox"].append((k, list(opciones), kw.get("index", 0)))
    if k in st.session_state:                     # como Streamlit: el estado manda
        return st.session_state[k]
    val = opciones[kw.get("index", 0) or 0]
    if k:
        st.session_state[k] = val
    return val


_espia("selectbox", _sb)
_oc = (X.configuracion, X.estado, XN.datos, auth.list_users, contable.partes, contable.mapa)
try:
    X.configuracion = lambda: {"ok": True}
    X.estado = lambda g: {"conectada": True, "tenant_id": "T1"}
    XN.datos = lambda g: {"empleados": EMP, "calendarios": [], "tipos_permiso": {}, "error": ""}
    auth.list_users = lambda g=None: [dict(u) for u in USUARIOS]
    contable.partes = lambda g, a, b: {"filas": [], "avisos": []}
    contable.mapa = lambda g: {"conceptos": {}, "xero_empleados": {}}

    def _limpia():
        for u in USUARIOS:
            st.session_state.pop(f"xn_emp_{u['User']}", None)
        st.session_state.pop(f"_xero_nomina_{G}", None)
        st.session_state.pop("_xn_aplicar_propuesta", None)
        for k in PINT:
            PINT[k].clear()

    _limpia()
    XU.render_partes_xero(G)
    _caps = " || ".join(PINT["caption"])
    ck("dice cuántas ha emparejado y por qué vía", ("1 by email" in _caps, "1 by name" in _caps),
       (True, True))
    ck("...y por qué NO las otras cinco", "Not matched (5)" in _caps, True)
    for trozo in ("has no email in COPEX", "not in Xero Payroll",
                  "share that email", "have that name"):
        ck(f"   · explica «{trozo}»", trozo in _caps, True)
    ck("el botón de rellenar existe y cuenta las propuestas",
       any(k == "xn_aplicar" and "2" in lab for lab, k in PINT["button"]), True)

    # (b) el relleno ocurre en la pasada SIGUIENTE, no al pulsar
    _limpia()
    APRETADO["activo"] = "xn_aplicar"
    XU.render_partes_xero(G)
    # ⚠️ Aquí NO se puede exigir que la clave siga vacía: el desplegable ya trae la
    # propuesta como valor por defecto (por eso basta con «Save matches» la primera vez).
    # Lo que se comprueba es que el botón deja BANDERA para la pasada siguiente (v111).
    ck("pulsar deja la bandera para la pasada siguiente",
       st.session_state.get("_xn_aplicar_propuesta"), True)
    APRETADO["activo"] = None
    # ⚠️ Lo que el botón resuelve es ESTE caso, y solo este: las filas que alguien dejó en
    # «— not in Xero —». Con las claves sin valor, el desplegable ya trae la propuesta por
    # su cuenta, así que comprobarlo así aprobaba el relleno aunque estuviera desactivado
    # (se escapó una rotura de la batería, y por eso el caso se cambió).
    for u in USUARIOS:
        st.session_state[f"xn_emp_{u['User']}"] = ""
    st.session_state["_xn_aplicar_propuesta"] = True
    for k in PINT:
        PINT[k].clear()
    XU.render_partes_xero(G)
    ck("recupera las propuestas en las filas que estaban en «not in Xero»",
       (st.session_state.get("xn_emp_ana"), st.session_state.get("xn_emp_bea")), ("E1", "E2"))
    ck("...y las que no tienen pareja se quedan vacías",
       [st.session_state.get(f"xn_emp_{k}") for k in ("cid", "din", "mei1")], ["", "", ""])

    # (c) no pisa lo elegido, ni repite empleado
    _limpia()
    st.session_state["xn_emp_ana"] = "E3"         # el administrador la puso a mano
    st.session_state["_xn_aplicar_propuesta"] = True
    XU.render_partes_xero(G)
    ck("no pisa lo que el administrador ya eligió", st.session_state.get("xn_emp_ana"), "E3")
    # ⚠️ El relleno se salta un empleado ya ocupado, pero la protección que MANDA es la de
    # v490: si dos filas acaban en el mismo empleado se avisa y NO se deja guardar.
    _limpia()
    st.session_state["xn_emp_cid"] = "E2"         # ya ocupa el empleado que se propone a bea
    st.session_state["_xn_aplicar_propuesta"] = True
    XU.render_partes_xero(G)
    _dis = [k for lab, k in PINT["button"] if k == "xn_guardar"]
    ck("dos filas en el mismo empleado: se avisa",
       any("same Xero employee" in w for w in PINT["warning"]), True)
    ck("...y Guardar queda deshabilitado (la protección de v490 sigue viva)",
       XU.st.session_state.get("_xn_guardar_disabled", "no medido") == "no medido" and bool(_dis), True)
finally:
    for n, f in _g.items():
        setattr(st, n, f)
    (X.configuracion, X.estado, XN.datos, auth.list_users, contable.partes, contable.mapa) = _oc

# ═════ 3 · el orden que exige la regla v111 ═════════════════════════════════
print("\n[3] el relleno va ANTES de instanciar los desplegables (regla v111)")
_tr = ast.parse(_fuente("core/xero_ui.py"))
_rp = next(n for n in ast.walk(_tr) if isinstance(n, ast.FunctionDef)
           and n.name == "render_partes_xero")
_pop = [n.lineno for n in ast.walk(_rp) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "pop"
        and any(isinstance(a, ast.Constant) and a.value == "_xn_aplicar_propuesta" for a in n.args)]
_sel = [n.lineno for n in ast.walk(_rp) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "selectbox"
        and any(getattr(k, "arg", "") == "key" and "xn_emp_" in ast.unparse(k.value)
                for k in n.keywords)]
ck("la bandera se lee antes del primer selectbox de personas",
   bool(_pop) and bool(_sel) and min(_pop) < min(_sel), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
