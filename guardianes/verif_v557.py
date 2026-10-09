# -*- coding: utf-8 -*-
"""v557 · USERS (PLANIFICACIÓN), PROBADA ACCIÓN POR ACCIÓN.

Recorrido en producción (10/10/2026). Lo arreglado («Arregla todo»):
  1. ⚠️ Correos que no lo son («driver 1», «x@hotmai.commomo») se guardaban sin aviso →
     `auth.revisar_email`: lo que no es un correo NO se guarda (motor y pantalla); una
     probable errata de un proveedor frecuente se pregunta («Did you mean…?») y solo se
     guarda confirmándola. La tabla y la ficha los señalan.
  2. ⚠️ El alta borraba TODO al dar un error (`clear_on_submit=True`) → conserva lo
     escrito y solo se vacía al crear (formulario por generación). En los DOS formularios
     (el del admin y el del propietario), y el correo se mira ANTES de crear la cuenta.
  3. ⚠️ Contraseñas de 1 carácter valían → mínimo 8 en altas y cambios (`auth.MIN_PW`);
     el cambio pide repetirla y vacía los campos al guardar.
  4. «ContactName» en bruto → «Contact»; la tarifa con «$».
  5. La línea de salud, ACTIVA: cada problema filtra la tabla (con clave por filtro).
  6. El selector de secciones de la ficha, segmentado (`cpxseg_`).
  7. La fecha de alta en DD/MM/YYYY.

AppTest con una hoja Login de MENTIRA (`_get_login_ws` sustituido): nada toca la real.
"""
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
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


SRC = io.open(os.path.join("core", "auth_ui.py"), encoding="utf-8").read()

print("1. El motor")
from core import auth as A                                          # noqa: E402

for _e, _ok, _sug in (("driver 1", False, ""), ("a@b", False, ""),
                      ("x@hotmai.com", True, "x@hotmail.com"),
                      ("x@hotmai.commomo", True, "x@hotmail.com"),
                      ("x@gmial.com", True, "x@gmail.com"),
                      ("Diego93_aco@hotmail.com", True, ""), ("x@schindler.com", True, ""),
                      ("x@cairn.com.au", True, ""), ("", True, "")):
    _r = A.revisar_email(_e)
    chk("revisar_email(%r) → ok=%s, sugerencia=%r" % (_e, _ok, _sug),
        _r["ok"] == _ok and _r["sugerencia"] == _sug, _r)
chk("el mínimo de contraseña es 8", A.MIN_PW == 8)


class _WS:
    def __init__(self):
        self.escrito = []

    def append_row(self, fila, **k):
        self.escrito.append(("append", fila))

    def update_cell(self, r, c, v):
        self.escrito.append(("cell", r, c, v))


_ws = _WS()
_orig = (A._get_login_ws, A._find_row, A._invalidate_login)
try:
    A._get_login_ws = lambda: (_ws, None)
    A._invalidate_login = lambda: None
    A._find_row = lambda ws, u: (None, None)
    _r = A.add_user("nuevo", "1234567", "field", "N", "G")
    chk("⚠️ add_user con 7 caracteres: rechazado", not _r[0] and "at least 8" in _r[1], _r)
    _r = A.add_user("nuevo", "x", "rol-raro", "N", "G")
    chk("…y el rol inválido se dice ANTES que la longitud (los mensajes de antes no cambian)",
        not _r[0] and _r[1] == "Invalid role.", _r)
    A._find_row = lambda ws, u: (2, {"User": u})
    _r = A.set_password("ana", "corta")
    chk("⚠️ set_password con 5 caracteres: rechazado", not _r[0] and "at least 8" in _r[1], _r)
    _n = len(_ws.escrito)
    _r = A.set_contact("ana", email="driver 1")
    chk("⚠️ set_contact con «driver 1»: rechazado SIN escribir",
        not _r[0] and "not an email" in _r[1] and len(_ws.escrito) == _n, _r)
    _r = A.set_contact("ana", email="")
    chk("…y vaciar el correo sí vale", _r[0] and len(_ws.escrito) == _n + 1, _r)
finally:
    A._get_login_ws, A._find_row, A._invalidate_login = _orig

print("\n2. Estático")
# ⚠️ Sobre ESTAS piezas, no el fichero entero: otros formularios del propietario (grupos,
# rieles) y otras fechas no son de esta pantalla — un chequeo global daba rojos que no son.
chk("la fecha de alta en DD/MM/YYYY", 'key=f"{k}_fing", format="DD/MM/YYYY"' in SRC)
chk("…y las de las credenciales también", 'd = col.date_input(label, value=ini, key=key, format="DD/MM/YYYY"' in SRC)
chk("el selector de la ficha es segmentado (`cpxseg_`)", 'key=f"cpxseg_{k}_sec"' in SRC)
for _form in ('st.form(f"form_campo_{_g}", clear_on_submit=False)',
              'st.form(f"form_user_{_g}", clear_on_submit=False)',
              'st.form(f"{key_prefix}_add_{usuario}_{_cg}", clear_on_submit=False)'):
    chk("⚠️ el formulario conserva lo escrito al dar error: %s" % _form.split('"')[1], _form in SRC)
chk("ya no queda la cabecera «ContactName» en las tablas de usuarios",
    '"ContactName": t(' not in SRC and '"ContactName": _cont' not in SRC)

print("\n3. La pantalla, con clics (AppTest)")
from streamlit.testing.v1 import AppTest                             # noqa: E402

GUION = r'''
import streamlit as st
from core import auth, auth_ui as AUI, credentials as C, timeclock as T
from core import admin_digest

st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
if "_USERS" not in st.session_state:
    def _u(u, n, em, tg, act="SI", rate=""):
        return {"User": u, "Name": n, "Role": "field", "Group": "G", "Email": em,
                "TelegramChatID": tg, "Active": act, "HourlyRate": rate}
    st.session_state["_USERS"] = [
        _u("ana", "Ana", "ana@gmail.com", "111", rate="55"),
        _u("beto", "Beto", "driver 1", ""),
        _u("carl", "Carl", "carl@hotmai.com", "", rate="27.5"),
        _u("dani", "Dani", "", ""),
        _u("eva", "Eva", "eva@cairn.com.au", "222", act="NO"),
    ]
    st.session_state["_LOG"] = []
US, LOG = st.session_state["_USERS"], st.session_state["_LOG"]
auth.list_users = lambda *a, **k: US
auth.get_user = lambda u: next((x for x in US if x["User"] == u), {})
auth.fecha_ingreso = lambda u: None
C.is_configured = lambda: False
T.open_sessions = lambda *a, **k: {}
admin_digest.group_digest = lambda g: {}
class _WS:
    def append_row(self, fila, **k): LOG.append(("append", fila[0]))
    def update_cell(self, r, c, v): LOG.append(("cell", r, c, v))
auth._get_login_ws = lambda: (_WS(), None)
auth._invalidate_login = lambda: None
auth._find_row = lambda ws, u: ((2, {"User": u}) if any(x["User"] == u for x in US) else (None, None))
AUI._grupo_usuarios("G")
'''


def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


def blabel(at, txt):
    x = [y for y in at.button if txt in (y.label or "")]
    return x[0] if x else None


def tabla(at):
    return at.dataframe[0].value.to_dict("records") if at.dataframe else []


def log(at):
    return list(at.session_state["_LOG"])


def textos(at):
    return " | ".join([m.value for m in at.markdown] + [m.value for m in at.error]
                      + [m.value for m in at.warning] + [m.value for m in at.caption])


at = AppTest.from_string(GUION, default_timeout=90)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_t = {r["User"]: r for r in tabla(at)}
chk("la tabla trae a las 5 personas", len(_t) == 5, list(_t))
chk("⚠️ «Contacto»: ana yes · beto invalid email · carl check email · dani missing",
    (_t.get("ana", {}).get("Contacto"), _t.get("beto", {}).get("Contacto"),
     _t.get("carl", {}).get("Contacto"), _t.get("dani", {}).get("Contacto"))
    == ("yes", "invalid email", "check email", "missing"),
    {k: v.get("Contacto") for k, v in _t.items()})
chk("la tarifa con «$» («$55», «$27.50», «—»)",
    (_t["ana"]["Rate/h"], _t["carl"]["Rate/h"], _t["dani"]["Rate/h"]) == ("$55", "$27.50", "—"))

print("   a) el filtro de salud")
_pi = [p for p in at.get("button_group") if getattr(p, "key", None) == "gu_filtro"]
chk("⚠️ la línea de salud es un filtro (pills)", bool(_pi))
if _pi:
    _ops = list(_pi[0].proto.options) if hasattr(_pi[0].proto, "options") else []
    chk("…con «sin contacto» (3), «correo» (2) e «inactivos» (1)",
        len(_ops) == 3, [str(o)[:60] for o in _ops])
    at.session_state["gu_filtro"] = "correo"
    at.run()
    chk("⚠️ elegir «invalid or suspicious email» deja SOLO a beto y carl",
        sorted(r["User"] for r in tabla(at)) == ["beto", "carl"], [r["User"] for r in tabla(at)])
    # ⚠️ La selección es un NÚMERO de fila: con la misma tabla para todos los filtros, la
    # fila 1 de «correo» abriría a quien sea la fila 1 de «todos».
    chk("…y la tabla filtrada tiene SU clave (la selección no se cruza entre filtros)",
        at.dataframe and at.dataframe[0].key == "gu_tbl_correo",
        at.dataframe[0].key if at.dataframe else None)
    at.session_state["gu_filtro"] = None
    at.run()

print("   b) la ficha y el correo")
at.session_state["_gu_open"] = "beto"
at.run()
chk("la ficha de beto avisa «Invalid email»", "Invalid email" in textos(at))
_sec = [r for r in at.radio if r.key == "cpxseg_fu_beto_sec"]
chk("su selector de secciones es segmentado (clave `cpxseg_`)", bool(_sec))
_sec[0].set_value("📇 Contacto")
at.run()
chk("⚠️ el «driver 1» guardado se señala al abrir Contact",
    any("«driver 1» is not an email address." in e.value for e in at.error))
at.session_state["_gu_open"] = "carl"
at.run()
[r for r in at.radio if r.key == "cpxseg_fu_carl_sec"][0].set_value("📇 Contacto")
at.run()
chk("⚠️ la errata de carl se pregunta: «Did you mean carl@hotmail.com?»",
    any("carl@hotmail.com" in w.value for w in at.warning))
_n = len(log(at))
b(at, "fu_carl_cc_emb").click()
at.run()
chk("…«Save email» sin confirmar NO guarda", len(log(at)) == _n
    and any("Check the address" in e.value for e in at.error))
[c for c in at.checkbox if c.key == "fu_carl_cc_emok"][0].check()
at.run()
b(at, "fu_carl_cc_emb").click()
at.run()
chk("…confirmando, sí guarda", len(log(at)) > _n, log(at)[-1:])

print("   c) el alta conserva lo escrito")
at.session_state["_gu_open"] = None
at.run()
at.text_input(key="fc_u_0").input("nuevo")
at.text_input(key="fc_n_0").input("Nuevo Uno")
at.text_input(key="fc_p_0").input("corta")
_crear = blabel(at, "Create")
_crear.click()
at.run()
chk("sin correo: «Email is required…»", any("Email is required" in e.value for e in at.error))
chk("⚠️ …y lo escrito SE CONSERVA", (at.text_input(key="fc_u_0").value,
                                     at.text_input(key="fc_n_0").value) == ("nuevo", "Nuevo Uno"))
at.text_input(key="fc_e_0").input("nuevo@hotmai.com")
blabel(at, "Create").click()
at.run()
chk("una errata en el correo se pregunta antes de crear", any("nuevo@hotmail.com" in e.value for e in at.error)
    and not any(x[0] == "append" for x in log(at)))
[c for c in at.checkbox if c.key == "fc_eok_0"][0].check()
blabel(at, "Create").click()
at.run()
chk("⚠️ contraseña de 5 caracteres: rechazada y nada creado",
    any("at least 8" in e.value for e in at.error) and not any(x[0] == "append" for x in log(at)))
at.text_input(key="fc_p_0").input("larga1234")
blabel(at, "Create").click()
at.run()
chk("con todo bien, se crea", ("append", "nuevo") in log(at), log(at)[-3:])
chk("…y el formulario se vacía (uno nuevo)", at.session_state["_fc_gen"] == 1
    and at.text_input(key="fc_u_1").value == "")

print("   d) cambiar la contraseña")
at.session_state["_gu_open"] = "ana"
at.run()
at.text_input(key="fu_ana_np_0").input("abcd1234")
at.text_input(key="fu_ana_np2_0").input("abcd9999")
_n = len(log(at))
b(at, "fu_ana_chp").click()
at.run()
chk("⚠️ si no coinciden, no cambia", len(log(at)) == _n
    and any("do not match" in e.value for e in at.error))
at.text_input(key="fu_ana_np2_0").input("abcd1234")
b(at, "fu_ana_chp").click()
at.run()
chk("coinciden: cambia", len(log(at)) > _n)
chk("…y los campos se vacían (generación nueva)", at.session_state["fu_ana_pwgen"] == 1
    and at.text_input(key="fu_ana_np_1").value == "")
chk("sin excepción en todo el recorrido", not at.exception, [e.value for e in at.exception][:1])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
