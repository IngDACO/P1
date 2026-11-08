# -*- coding: utf-8 -*-
"""v653 · Lo que dejó la auditoría de seguridad del 08/11/2026.

1. Ningún dato de la hoja entra SIN ESCAPAR en el HTML de la pantalla ni en el marcado de un PDF
   (barrido `html_seguro`, validado con casos conocidos; la cartera del propietario y los PDF,
   construidos de verdad con texto trucado).
2. El color de un trabajo del tablero solo puede ser un color.
3. La sesión de la cookie caduca, el token se compara en tiempo constante y la cookie es `Secure`.
4. La entrada: el mismo mensaje si la cuenta no existe o la contraseña no vale, freno por cuenta
   y por proceso, y la pantalla de entrada ya no lee `Login` en cada carga.
5. Telegram se vincula con un código aleatorio y EXACTO, y al vincular se ve de quién es el chat.

Nada sale a la red ni escribe: las hojas, Telegram y la identidad fiscal van sustituidos.
"""
import ast
import io
import os
import re
import sys
import time
import types

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)

FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


import html_seguro as HS                                              # noqa: E402

# ═════════════════════════════════════════════════════════════════════════════
sec("1. El barrido: validado con casos conocidos, y en la app, CERO")
_malo = {"core/x.py": (
    "import streamlit as st\n"
    "def a(p):\n"
    "    st.markdown(f\"<b>{p.get('Name')}</b>\", unsafe_allow_html=True)\n"
    "def b(p):\n"
    "    n = str(p.get('Client', '')).strip()\n"
    "    m = n + ' · x'\n"
    "    st.markdown('<div>' + m + '</div>', unsafe_allow_html=True)\n"
    "def c(rec):\n"
    "    return Paragraph(str(rec.get('Note')), sm)\n"
    "def d(p):\n"
    "    meta = {'cliente': str(p.get('CLIENTE', ''))}\n"
    "    return Paragraph(f\"<b>{meta['cliente']}</b>\", sm)\n")}
_bueno = {"core/x.py": (
    "import streamlit as st\nfrom html import escape as _esc_html\n"
    "def a(p):\n"
    "    st.markdown(f\"<b>{_esc_html(str(p.get('Name')))}</b>\", unsafe_allow_html=True)\n"
    "def b(p, alarmas):\n"
    "    na = alarmas.get(p.get('ID'), 0)\n"
    "    st.markdown(f\"<b>{na}</b> {p.get('BS')} {int(p.get('Hours') or 0)}\", unsafe_allow_html=True)\n"
    "def c(rec):\n"
    "    return Paragraph(esc_pdf(rec.get('Note')), sm)\n")}
_r = HS.barrer(_malo)
chk("la sonda VE un campo en una f-string, uno por cadena de variables, uno en un Paragraph y uno del Survey",
    {x[2] for x in _r} == {"a", "b", "c", "d"}, sorted(_r))
chk("...y no marca lo escapado, un número, un parámetro técnico ni el valor de un mapa",
    HS.barrer(_bueno) == set(), sorted(HS.barrer(_bueno)))
_app = HS.barrer()
chk("en TODA la app: ningún dato de la hoja sin escapar en HTML ni en un PDF", _app == set(), sorted(_app)[:12])
_av = HS.por_aviso_comprobado()
chk("los avisos que se dejan fuera del barrido siguen saliendo por `notify_user` (los 6)",
    len(_av) == 6 and all(_av.values()), _av)
_nu = next(n for n in ast.walk(ast.parse(src("core/notify.py")))
           if isinstance(n, ast.FunctionDef) and n.name == "notify_user")
chk("...y `notify_user` escapa el texto con `html_seguro` (v603)",
    any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "html_seguro" for c in ast.walk(_nu)))

# ═════════════════════════════════════════════════════════════════════════════
sec("2. La cartera del propietario, PINTADA con un nombre trucado")
import streamlit as st                                                 # noqa: E402
from core import projects_ui as PU                                     # noqa: E402

VENENO = "Obra <iframe srcdoc=\"<script>parent.x=1</script>\"></iframe> & <b>Co"
_p = {"ID": "PRJ-9001", "Name": VENENO, "Client": VENENO, "Group": VENENO, "Status": VENENO,
      "Progress": "40", "Location": VENENO}
_h = PU._portfolio_html([_p], {}, {}, {}, show_group=True)
chk("ni un <iframe> de verdad en la tarjeta", "<iframe" not in _h, _h[:300])
chk("...el nombre se ve escapado (tal cual lo escribieron)", "Obra &lt;iframe" in _h, _h[:300])
chk("...y la empresa sigue llevando su icono (fuera del texto escapado)",
    _h.count(PU._MI("business")) == 1, _h[:400])
_dp = src("core/projects_ui.py")
for _frag in ('{_esc_html(str(prj.get("Name", "")))}', "{_esc_html(_cli)}", "{_esc_html(_tp)}",
              "{_esc_html(str(pid))}", "{_esc_html(_a)}", "{_esc_html(_d)}", "{_esc_html(str(grupo or ''))}"):
    chk(f"projects_ui escapa {_frag}", _dp.count(_frag) == 1, _dp.count(_frag))

# ═════════════════════════════════════════════════════════════════════════════
sec("3. El color de un trabajo del tablero")
from core import roster as R                                           # noqa: E402

chk("un #hex y un nombre de color pasan", R.color_seguro("#1e8449") == "#1e8449" and R.color_seguro("teal") == "teal")
chk("lo que no es un color, no (cae al de siempre)",
    R.color_seguro('red"><iframe') == R._COLOR_DEFECTO and R.color_seguro("") == R._COLOR_DEFECTO
    and R.color_seguro("#12;x") == R._COLOR_DEFECTO)
chk("`color_de` devuelve el color validado",
    R.color_de("T1", {"T1": {"Color": "x'><b>"}}) == R._COLOR_DEFECTO
    and R.color_de("T1", {"T1": {"Color": "#abcdef"}}) == "#abcdef")
chk("el catálogo pinta su muestra con `color_seguro`",
    "background:{R.color_seguro(r.get('Color'))}" in src("core/roster_ui.py"))

# ═════════════════════════════════════════════════════════════════════════════
sec("4. Los PDF, CONSTRUIDOS con texto trucado en cada campo")
from pypdf import PdfReader                                            # noqa: E402
from core import contable                                              # noqa: E402

TRUCO = "x <b>bold <img src='zz_no_existe.png'/> & <font size=40>BIG"
contable.identidad = lambda g: {"legal": TRUCO, "abn": TRUCO}


def _texto(pdf):
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(pdf)).pages)


def _prueba(nombre, fn):
    try:
        pdf = fn()
        ok = pdf[:4] == b"%PDF"
        txt = _texto(pdf) if ok else ""
    except Exception as e:                                             # noqa: BLE001
        ok, txt = False, f"{type(e).__name__}: {e}"
    chk(f"{nombre}: se genera", ok, txt[:200])
    chk(f"{nombre}: el texto trucado sale TAL CUAL (escapado, no como marcado)",
        "<img src='zz_no_existe.png'/>" in txt.replace("\n", " "), txt[:300])


import json                                                            # noqa: E402
from core import invoice_pdf, claim_pdf, payslip_pdf, quote_pdf, asset_label_pdf, tool_pdf  # noqa: E402

_cli = {"Name": TRUCO, "ContactName": TRUCO, "Address": TRUCO, "Email": TRUCO, "Phone": TRUCO}
_lin = json.dumps([{"concepto": TRUCO, "importe": 10, "descripcion": TRUCO, "cantidad": 1,
                    "unidad": TRUCO, "precio_total": 10}])
_prueba("factura", lambda: invoice_pdf.generate_invoice_pdf(
    {"Group": "g", "Number": TRUCO, "Date": "2026-11-08", "ExpiryDate": "2026-11-20", "Total": 10,
     "ClientName": TRUCO, "LinesJSON": _lin, "Note": TRUCO}, _cli, TRUCO))
_prueba("reclamación", lambda: claim_pdf.generate_claim_pdf(
    {"Group": "g", "Number": TRUCO, "Date": TRUCO, "PeriodTo": TRUCO, "Status": TRUCO, "Note": TRUCO},
    [], _cli, TRUCO, {"Name": TRUCO, "Location": TRUCO, "Client": TRUCO}))
_prueba("nómina", lambda: payslip_pdf.generate_payslip_pdf(
    {"Group": "g", "Name": TRUCO, "Status": "pagada", "PaymentDate": "2026-11-08", "Hours": 8,
     "PeriodFrom": "2026-11-01", "PeriodTo": "2026-11-07",
     "ConceptsJSON": json.dumps([{"concepto": TRUCO, "tipo": "earning", "monto": 5}])}, TRUCO))
_prueba("presupuesto", lambda: quote_pdf.generate_quote_pdf(
    {"Group": "g", "Number": TRUCO, "Date": "2026-11-08", "ValidUntil": "2026-12-08", "ClientName": TRUCO,
     "LinesJSON": _lin, "Note": TRUCO, "Subtotal": 10, "Total": 10}, _cli, TRUCO))
import segno                                                           # noqa: E402

_qr = io.BytesIO()
segno.make("x").save(_qr, kind="png")
_prueba("etiqueta de activo", lambda: asset_label_pdf.generate_label_pdf(
    {"ID": TRUCO, "Name": TRUCO, "Category": TRUCO, "Brand": TRUCO, "Model": TRUCO, "Serial": TRUCO},
    _qr.getvalue(), TRUCO))
_prueba("PDF de herramienta", lambda: tool_pdf.tool_pdf(
    "Belting", meta={"Project": TRUCO}, tablas=[("Tabla", [{"Col": TRUCO}])], notas=["nota"]))

from reportlab.platypus import SimpleDocTemplate                       # noqa: E402
from core import user_report as UR, report as RP                       # noqa: E402


def _doc(flows):
    b = io.BytesIO()
    SimpleDocTemplate(b).build(list(flows))
    return b.getvalue()


_prueba("informe del cliente: los textos editables (`_ia_text`)", lambda: _doc(UR._ia_text(TRUCO, UR._styles())))
_prueba("informe interno: la interpretación (`_ia_block`)",
        lambda: _doc([RP._ia_block(TRUCO, RP._styles() if hasattr(RP, "_styles") else RP.get_styles())]))
_ur = src("core/user_report.py")
chk("informe del cliente: el instalador y el cliente de la firma, escapados",
    "{esc_pdf(meta['ingeniero'])}" in _ur and "{esc_pdf(meta['cliente'])}" in _ur)
for _f in ("claim_pdf", "invoice_pdf", "payslip_pdf", "quote_pdf", "asset_label_pdf", "tool_pdf", "user_report", "report"):
    _s = src(f"core/{_f}.py")
    chk(f"{_f}: ningún `Paragraph(str(…))` (todo dato pasa por `esc_pdf`)", "Paragraph(str(" not in _s,
        _s.count("Paragraph(str("))

# ═════════════════════════════════════════════════════════════════════════════
sec("5. La sesión de la cookie")
from core import auth as A                                              # noqa: E402
from core import session_cookie as SC                                   # noqa: E402

chk("SESION_DIAS de la hoja = los días de la cookie", A.SESION_DIAS == SC._DIAS, (A.SESION_DIAS, SC._DIAS))
_capt = []
_o_scr = SC.incrustar.script
SC.incrustar.script = lambda js: _capt.append(js)
try:
    SC.save("u1", "tok")
finally:
    SC.incrustar.script = _o_scr
chk("la cookie se escribe con `Secure`", bool(_capt) and "SameSite=Lax; Secure" in _capt[0], _capt[:1])

_ahora = int(time.time())
_REC = {"User": "u1", "Role": "field", "Name": "U", "Group": "g", "Active": "SI",
        "SessionToken": "TOKBUENO", "SessionTime": str(_ahora - 600)}
_lect = []
_o = (A._get_login_ws, A._find_row)
A._get_login_ws = lambda: (object(), "")


def _fila(rec):
    def f(_ws, _u):
        _lect.append(1)
        return (2, dict(rec)) if rec else (None, None)
    return f


def _vs(rec, tok):
    A._FALLOS_RESTAURAR.clear()
    A._find_row = _fila(rec)
    return A.validate_session("u1", tok)


chk("token bueno y usado hace 10 min → restaura", _vs(_REC, "TOKBUENO").get("usuario") == "u1")
chk("token malo → no", _vs(_REC, "TOKMALO") == {})
chk("token bueno, pero sin usar en 8 días → NO (caduca)",
    _vs(dict(_REC, SessionTime=str(_ahora - 8 * 86400)), "TOKBUENO") == {})
chk("token bueno con SessionTime vacío o 0 → no", _vs(dict(_REC, SessionTime=""), "TOKBUENO") == {}
    and _vs(dict(_REC, SessionTime="0"), "TOKBUENO") == {})
chk("token vacío en la hoja (sesión cerrada) → no, aunque el dado esté vacío también",
    _vs(dict(_REC, SessionToken=""), " ") == {})
A._FALLOS_RESTAURAR.clear()
A._find_row = _fila(_REC)
for _ in range(A.RESTAURAR_MAX_FALLOS):
    A.validate_session("u1", "TOKMALO")
_lect.clear()
_r = A.validate_session("u1", "TOKBUENO")
chk(f"con {A.RESTAURAR_MAX_FALLOS} cookies malas en un minuto ya NO se lee la hoja (ni para la buena)",
    _r == {} and _lect == [], (_r, len(_lect)))
A._FALLOS_RESTAURAR.clear()
chk("...y pasado el minuto vuelve a valer", A.validate_session("u1", "TOKBUENO").get("usuario") == "u1")
A._get_login_ws, A._find_row = _o
_t = ast.parse(src("core/auth.py"))
_ti = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == "_token_igual")
chk("`_token_igual` compara con `hmac.compare_digest`",
    any(isinstance(c, ast.Attribute) and c.attr == "compare_digest" for c in ast.walk(_ti)))
for _fn in ("validate_session", "_heartbeat_con", "end_session"):
    _f = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef) and n.name == _fn)
    _cmp = [ast.unparse(c) for c in ast.walk(_f) if isinstance(c, ast.Compare) and "SessionToken" in ast.unparse(c)]
    _usa = any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_token_igual" for c in ast.walk(_f))
    chk(f"{_fn}: el token, con `_token_igual` (ningún ==/!= sobre SessionToken)", _usa and not _cmp, _cmp)

# ═════════════════════════════════════════════════════════════════════════════
sec("6. La entrada (login)")
_HASH = A.hash_password("clave-buena-1")
_USUARIOS = [{"User": "ana", "Password": _HASH, "Role": "field", "Name": "Ana", "Active": "SI", "Group": "g"},
             {"User": "baja", "Password": _HASH, "Role": "field", "Name": "B", "Active": "NO", "Group": "g"}]
_lotes = []
_o2 = A._login_records_cached


def _cache():
    _lotes.append(1)
    return [dict(x) for x in _USUARIOS]


A._login_records_cached = _cache


def _limpiar():
    A._FALLOS.clear()
    A._FALLOS_PROCESO.clear()


_limpiar()
_e1 = A.verify_login("nadie-v653", "x").get("error")
_e2 = A.verify_login("ana", "mala").get("error")
chk("«no existe» y «contraseña mal» dan el MISMO mensaje", _e1 == _e2 == "Wrong username or password.", (_e1, _e2))
chk("cuenta de baja + contraseña buena → «Inactive user.»",
    A.verify_login("baja", "clave-buena-1").get("error") == "Inactive user.")
chk("cuenta de baja + contraseña mala → el mensaje de siempre (no delata que existe)",
    A.verify_login("baja", "mala").get("error") == "Wrong username or password.")
_ok = A.verify_login("ANA ", "clave-buena-1")
chk("la buena entra (sin distinguir mayúsculas ni espacios)", _ok.get("ok") and _ok.get("usuario") == "ana", _ok)
_limpiar()
for _ in range(A.LOGIN_MAX_FALLOS):
    A.verify_login("ana", "mala")
_lotes.clear()
_b = A.verify_login("ana", "clave-buena-1")
chk(f"tras {A.LOGIN_MAX_FALLOS} fallos, ni la contraseña buena entra: hay que esperar",
    not _b.get("ok") and "Too many failed attempts" in str(_b.get("error")), _b)
chk("...y ese intento NI lee la hoja", _lotes == [], len(_lotes))
chk("...pero otra cuenta sí puede", A.verify_login("baja", "clave-buena-1").get("error") == "Inactive user.")
_o_time = A.time.time
A.time.time = lambda: _o_time() + A.LOGIN_ESPERA + 1
try:
    chk(f"pasados {A.LOGIN_ESPERA} s, vuelve a poder (y la buena entra)", A.verify_login("ana", "clave-buena-1").get("ok"))
    A.verify_login("ana", "mala")
    chk("...y entrar borra los fallos: uno nuevo no la vuelve a frenar", A.espera_login("ana") == 0,
        A.espera_login("ana"))
finally:
    A.time.time = _o_time
_limpiar()
for i in range(A.LOGIN_MAX_PROCESO):
    A._anotar_fallo_login(f"spray{i}")
chk(f"con {A.LOGIN_MAX_PROCESO} fallos en un minuto en TODA la app, espera todo el mundo",
    "Too many failed attempts" in str(A.verify_login("otra-cuenta", "x").get("error")))
_limpiar()
for i in range(2100):
    A._FALLOS[f"vieja{i}"] = [time.time() - 10 * A.LOGIN_VENTANA]
A._anotar_fallo_login("nueva")
chk("el registro de fallos no crece sin fin (se poda lo que ya no cuenta)", len(A._FALLOS) < 50, len(A._FALLOS))
_limpiar()
# la pantalla de entrada: `has_any_user` ya no lee `Login` en cada carga
A._HAY_USUARIOS = False
_lotes.clear()
_l1 = A.has_any_user()
A._login_records_cached = lambda: (_lotes.append(1) or [])
_lotes.clear()
_l2 = A.has_any_user()
chk("`has_any_user`: con cuentas → True, y la siguiente vez NI pregunta", _l1 and _l2 and _lotes == [], (_l1, _l2, _lotes))
A._login_records_cached = _o2

# ═════════════════════════════════════════════════════════════════════════════
sec("7. Vincular Telegram")
from core import notify as N                                           # noqa: E402

_cods = {N.codigo_vinculo() for _ in range(200)}
chk("el código es aleatorio (200 distintos) y vale en `?start=`",
    len(_cods) == 200 and all(re.fullmatch(r"c[0-9a-f]{10}", c) for c in _cods), sorted(_cods)[:3])
chk("`telegram_find_chat_by_code` ya no existe (no tenía ningún uso)", not hasattr(N, "telegram_find_chat_by_code"))


class _Resp:
    def __init__(self, msgs):
        self._j = {"ok": True, "result": [{"message": m} for m in msgs]}

    def json(self):
        return self._j


_o3 = (N.telegram_configured, N.requests.get)
N.telegram_configured = lambda: True
try:
    def _diag(msgs, code):
        N.requests.get = lambda *a, **k: _Resp(msgs)
        return N.telegram_diagnostico(code)
    _m = lambda txt, cid, **k: {"text": txt, "chat": dict({"id": cid}, **k)}   # noqa: E731
    chk("un mensaje que solo CONTIENE el código no vale («/start cab12» para «cab»)",
        _diag([_m("/start cab12", 1), _m("hola cab", 2)], "cab").get("chat_id") is None)
    _d = _diag([_m("/start cab", 7, first_name="Ana", last_name="Pérez", username="anap")], "cab")
    chk("«/start código» exacto vale, y dice de quién es el chat",
        _d.get("chat_id") == "7" and _d.get("nombre") == "Ana Pérez (@anap)", _d)
    chk("el código a secas también vale", _diag([_m("  cab ", 9)], "cab").get("chat_id") == "9")
    chk("sin código no casa nada", _diag([_m("/start ", 3)], "").get("chat_id") is None)
finally:
    N.telegram_configured, N.requests.get = _o3

from streamlit.testing.v1 import AppTest                                # noqa: E402

APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import auth, auth_ui, notify
auth.get_user = lambda u: {"User": u, "Email": "a@b.co", "TelegramChatID": ""}
notify.telegram_configured = lambda: True
notify.bot_username = lambda: "copex_bot"
auth_ui._contacto_uno("helper 1", key_prefix="cc")
'''


def _enlace(at):
    return [str(c.value) for c in at.code if "t.me/" in str(c.value)]


at = AppTest.from_string(APP, default_timeout=60).run()
_e1 = _enlace(at)
at.run()
_e2 = _enlace(at)
at2 = AppTest.from_string(APP, default_timeout=60).run()
chk("la ficha pinta el enlace sin excepción", not at.exception and len(_e1) == 1, (at.exception, _e1))
chk("...con un código aleatorio, no el usuario", _e1 and "helper" not in _e1[0]
    and re.search(r"\?start=c[0-9a-f]{10}$", _e1[0]), _e1)
chk("...el MISMO al volver a pintar (la persona ya puede tenerlo)", _e1 == _e2, (_e1, _e2))
chk("...y otro en otra sesión", _enlace(at2) and _enlace(at2) != _e1, (_e1, _enlace(at2)))
_au = src("core/auth_ui.py")
chk("al vincular, el aviso dice de quién es el chat, y el código se tira (un solo uso)",
    "Telegram linked: {n}." in _au and "st.session_state.pop(_kcod, None)" in _au)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLOS: " + " | ".join(FALLOS)))
sys.exit(1 if FALLOS else 0)
