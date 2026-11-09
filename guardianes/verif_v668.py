"""v668 · Lo visto verificando v667 en producción.

  H19 de verdad: «Restoring your session…» necesita saber si el componente de cookies CONTESTÓ, y su clave en la
      sesión no lo dice (está desde la primera pasada: en producción el formulario salió a los 4,5 s igual).
      `session_cookie.load` lo pide con `default=None` y `respondio()` lo dice.
  Los resultados del buscador: el estado de un activo y de una cotización con su etiqueta («Available»,
      «Accepted»), y fuera los restos en español («archivado», «nº», «inactivo»).
Todo con sustitutos en memoria: nada sale ni se escribe.
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


def funcion(rel, nombre):
    s = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(s, n) or ""
    return ""


# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. H19 · ¿Contestó el componente de cookies?")
from core import session_cookie as SC                             # noqa: E402


class _MgrFalso:
    """Como el de la librería: devuelve el `default` hasta que el navegador contesta."""
    def __init__(self, valor):
        self.valor, self.pedido = valor, {}

    def _remove_extra_spacing(self):
        pass

    def cookie_manager(self, **k):
        self.pedido = k
        return self.valor if self.valor is not None else k.get("default")


_o = SC._manager
_res = []
try:
    for _v in (None, {}, {"copex_session": "jefa|TOK"}):
        _m = _MgrFalso(_v)
        SC._manager = lambda m=_m: m
        st.session_state.pop("_ck_respondio", None)
        _res.append((SC.load(), SC.respondio(), _m.pedido.get("default", "FALTA"), _m.pedido.get("key")))
finally:
    SC._manager = _o
chk("⚠️ sin respuesta aún: (None, None) y respondio() = False (pide con default=None)",
    _res[0] == ((None, None), False, None, "copex_cookie_get"), _res[0])
chk("…contestó sin nuestra cookie: (None, None) y respondio() = True", _res[1] == ((None, None), True, None, "copex_cookie_get"), _res[1])
chk("…y con ella, la sesión", _res[2][0] == ("jefa", "TOK") and _res[2][1] is True, _res[2])

G2 = r'''
import streamlit as st
from core import auth_ui as AU, auth, session_cookie
session_cookie.load = lambda: (None, None)
auth.is_configured = lambda: True
auth.has_any_user = lambda: True
st.session_state["_R"] = AU.render_login()
'''
at = AppTest.from_string(G2, default_timeout=60).run()
chk("render_login: sin respuesta, «Restoring your session…» y sin formulario",
    not at.exception and any("Restoring your session" in str(i.value) for i in at.info) and not at.text_input,
    [str(i.value) for i in at.info])
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["_ck_respondio"] = True
at.session_state["copex_cookie_get"] = {}
at.run()
chk("…con respuesta (respondio), el formulario", not any("Restoring" in str(i.value) for i in at.info) and len(at.text_input) >= 1)
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["copex_cookie_get"] = {}           # ⚠️ la clave SOLA (lo que hay en producción desde la 1ª pasada)
at.run()
chk("⚠️ …y la clave del componente SOLA ya no cuenta como respuesta (era la sonda equivocada)",
    any("Restoring your session" in str(i.value) for i in at.info), [str(i.value) for i in at.info])

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("2. Los resultados del buscador")
from core import home_ui as H, projects as P, auth as AUTH, roster as R, library as LIB  # noqa: E402
from core import inventory as INV, invoices as IV, quotes as QT  # noqa: E402
_o = (P.list_projects, AUTH.list_users, R.list_trabajos, LIB.list_items, INV.list_activos, IV.list_facturas, QT.list_cotizaciones)
try:
    P.list_projects = lambda *a, **k: [{"ID": "PRJ-9", "Name": "Zeta tower", "Client": "C9", "Status": "Archived",
                                        "ManualStatus": "Archived"}]
    AUTH.list_users = lambda *a, **k: []
    R.list_trabajos = lambda *a, **k: [{"ID": "TRB-1", "Name": "Zeta job", "Number": "3", "Active": "NO"}]
    LIB.list_items = lambda *a, **k: []
    INV.list_activos = lambda g=None, incluir_baja=False: [{"ID": "ACT-0005", "Name": "Zeta hoist", "Category": "Equipment",
                                                           "Status": "available"}]
    IV.list_facturas = lambda g=None, **k: []
    QT.list_cotizaciones = lambda g=None, **k: [{"ID": "COT-6", "Number": "0006", "ClientName": "Zeta client",
                                                 "Status": "accepted", "Version": "1"}]
    _r = {x["tipo"]: x["pie"] for x in H.buscar("zeta", "G")}
finally:
    (P.list_projects, AUTH.list_users, R.list_trabajos, LIB.list_items, INV.list_activos, IV.list_facturas,
     QT.list_cotizaciones) = _o
chk("⚠️ el activo con su estado como etiqueta («Available», era «available»)", _r.get("activo") == "ACT-0005 · Equipment · Available", _r)
chk("…la cotización también («Accepted»)", _r.get("cotizacion") == "Zeta client · Accepted", _r)
chk("⚠️ una obra archivada dice «archived» (era «archivado»)", _r.get("proyecto") == "PRJ-9 · C9 · archived", _r)
chk("…y un trabajo inactivo, «No. 3 · inactive» (eran «nº 3 · inactivo»)", _r.get("trabajo") == "TRB-1 · No. 3 · inactive", _r)

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
