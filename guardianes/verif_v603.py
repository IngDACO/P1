"""v603 · LO VISTO VERIFICANDO v602, EN TODA LA APP (decisión del usuario: «Dale no dejes nada pendiente»).

Medido (26/10/2026) en producción y en mini-apps locales (Streamlit 1.64):
  ⚠️ el email de la ficha del cliente salía con un enlace VACÍO delante: el markdown vuelve a
     enlazar el email que es el texto de un `<a>`, y un enlace no cabe dentro de otro;
  ⚠️ Streamlit CONSERVA el desplazamiento al cambiar de vista: la ficha nueva de Contacts se abría
     ~190 px abajo («Client created.» y «Back to clients» fuera), en el móvil un toque en la tabla
     abría la ficha 917 px abajo y «Inventory» desde el menú quedaba donde estaba la lista;
  ⚠️ un aviso al actuar al final de una página larga quedaba por ENCIMA de la vista
     («1 project linked.» a -488 px);
  las direcciones perdían texto («*gate 2*» en cursiva, «<Ground>» tragado); «Issue invoice» no
  decía nada; los avisos por correo/Telegram llevaban SIN ESCAPAR lo que escribió una persona.
Todo con las hojas SUSTITUIDAS en memoria y los envíos interceptados: nada sale ni se escribe.
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


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()


ADMIN = '{"usuario": "jefa", "rol": "administrator", "grupo": "G", "nombre": "Jefa"}'

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("1. Los enlaces: el texto TAL CUAL (markdown y HTML)")
from core import maps                                            # noqa: E402
chk("`literal_md` escapa lo que el markdown interpreta («*», «_», «[», «<», «$»…)",
    maps.literal_md("a*b_c[d]<e>$f") == r"a\*b\_c\[d\]\<e\>\$f", maps.literal_md("a*b_c[d]<e>$f"))
_em = maps.enlace_md("zz_prueba+obra*1@ex-ample.com.au", "mailto:zz_prueba+obra*1@ex-ample.com.au")
chk("`enlace_md`: la etiqueta escapada y la URL entera (el email difícil que el autoenlace partía)",
    _em == r"[zz\_prueba\+obra\*1@ex\-ample.com.au](mailto:zz_prueba+obra*1@ex-ample.com.au)", _em)
chk("…y lo que cortaría el enlace, codificado («)», espacio)",
    maps.enlace_md("x", "mailto:a)b c@d.co") == "[x](mailto:a%29b%20c@d.co)", maps.enlace_md("x", "mailto:a)b c@d.co"))
_md = maps.maps_link_md("12 Smith St *gate 2*")
chk("⚠️ `maps_link_md`: «*gate 2*» ya no sale en cursiva (se escapa la dirección)",
    _md.startswith(r"[12 Smith St \*gate 2\*](https://www.google.com/maps/search/"), _md)
_mh = maps.maps_link_html("Shop 3 <Ground> & 4")
chk("⚠️ `maps_link_html`: «<Ground>» ya no se lo traga el navegador (escapado)",
    "📍 Shop 3 &lt;Ground&gt; &amp; 4</a>" in _mh and 'href="https://www.google.com/maps/search/?api=1&query=Shop' in _mh, _mh)
chk("…y una dirección normal sale igual que antes", maps.maps_link_md("1 Martin Place").startswith("[1 Martin Place]("))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n2. ⚠️ La ficha del cliente: el email, UN solo enlace (markdown, no un <a>)")
G2 = r'''
import streamlit as st
from core import clientes_ui as CU
CU._contactar({"Phone": "02 9000 1099", "Email": st.session_state.get("_MAIL", "zz.prueba@example.com")})
'''
at = AppTest.from_string(G2, default_timeout=60)
at.run()
_mds = [m for m in at.markdown]
_mail = [m for m in _mds if "mail" in str(m.value)]
_tel = [m for m in _mds if "call" in str(m.value)]
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ el email va en MARKDOWN: `[zz.prueba@example.com](mailto:…)`, sin HTML (el <a> dejaba uno VACÍO)",
    len(_mail) == 1 and str(_mail[0].value) == ":material/mail: [zz.prueba@example.com](mailto:zz.prueba@example.com)"
    and not _mail[0].proto.allow_html, [(str(m.value), m.proto.allow_html) for m in _mail])
chk("…el teléfono sigue en HTML (`tel:` no pasa por el markdown de Streamlit)",
    len(_tel) == 1 and 'href="tel:0290001099"' in str(_tel[0].value) and _tel[0].proto.allow_html)
at = AppTest.from_string(G2, default_timeout=60)
at.session_state["_MAIL"] = "zz_prueba+obra*1@ex-ample.com.au"
at.run()
_mail = [m for m in at.markdown if "mail" in str(m.value)]
chk("…y el email difícil, entero en la URL", len(_mail) == 1 and
    "(mailto:zz_prueba+obra*1@ex-ample.com.au)" in str(_mail[0].value), [str(m.value) for m in _mail])
_ui = ast.parse(fuente("core/clientes_ui.py"))
_html_mail = [n for n in ast.walk(_ui) if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "mailto:" in n.value and "<a" in n.value]
chk("⚠️ ningún `<a href=\"mailto:` en la pantalla de Contacts", not _html_mail, [n.value for n in _html_mail])

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n3. ⚠️ Los avisos por correo y Telegram: el texto de las personas, escapado")
from core import notify                                          # noqa: E402
_hs = notify.html_seguro('<b>Obra</b> · hueco < 20 mm & riel <torcido>\n<a href="https://x.y/?a=1&b=2">ver</a><br>')
chk("`html_seguro` escapa «<», «>» y «&» del texto…",
    "hueco &lt; 20 mm &amp; riel &lt;torcido&gt;" in _hs, _hs)
chk("…y deja las etiquetas de la app (<b>, <a href>, <br>), con el «&» de la URL como `&amp;`",
    _hs.startswith("<b>Obra</b>") and '<a href="https://x.y/?a=1&amp;b=2">ver</a><br>' in _hs, _hs)
_env = []
notify.auth.get_user = lambda u: {"User": u, "Email": "prueba@ejemplo.invalid", "TelegramChatID": "0"}
notify.email_configured = lambda: True
notify.telegram_configured = lambda: True
notify.send_email = lambda to, subj, html: _env.append(("email", subj, html)) or True
notify.send_telegram = lambda chat, text: _env.append(("tg", "", text)) or True
_r = notify.notify_assignment("campo000", {"Name": "Smith & Sons <Rear>", "Client": "A & B",
                                           "Location": "Shop 3 <Ground> & 4",
                                           "StartDate": "2026-10-26", "EndDateEst": "2026-11-26",
                                           "InductionLinks": "https://ind.example/?id=1&x=2"})
_tg = next((x[2] for x in _env if x[0] == "tg"), "")
_ml = next((x[2] for x in _env if x[0] == "email"), "")
chk("⚠️ la asignación: el nombre, el cliente y la dirección ESCAPADOS (Telegram rechaza «<»/«&» sueltos)",
    "<b>Smith &amp; Sons &lt;Rear&gt;</b>" in _tg and "A &amp; B" in _tg and ">Shop 3 &lt;Ground&gt; &amp; 4</a>" in _tg, _tg)
chk("…con los enlaces vivos (Maps e inducción)",
    '<a href="https://www.google.com/maps/search/?api=1&amp;query=Shop' in _tg
    and '<a href="https://ind.example/?id=1&amp;x=2">' in _tg, _tg)
chk("…y el correo, el MISMO cuerpo escapado (con <br>)", "Smith &amp; Sons &lt;Rear&gt;" in _ml and "<br>" in _ml, _ml[:200])
chk("…el asunto del correo, en TEXTO (no HTML): sin «&amp;»",
    next((x[1] for x in _env if x[0] == "email"), "").endswith("Smith & Sons <Rear>"), [x[1] for x in _env])
_en = fuente("core/email_notify.py")
chk("el correo interno del Survey escapa la obra y el instalador",
    "{_html.escape(proyecto or '(not specified)')}" in _en and "{_html.escape(ingeniero or '(not specified)')}" in _en)

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n4. ⚠️ Al cambiar de vista, la página empieza ARRIBA (y un aviso nuevo se ve)")
from core import flash, home_ui                                  # noqa: E402
G4 = r'''
import streamlit as st
from core import home_ui as H, incrustar, flash
st.session_state.setdefault("auth", ''' + ADMIN + r''')
LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: LL.append(h)
st.session_state.setdefault("_admin_sec", "contactos")
for _k, _v in (st.session_state.pop("_PASO", None) or {}).items():
    if _v is None:
        st.session_state.pop(_k, None)
    else:
        st.session_state[_k] = _v
st.session_state.pop("_bajada_pedida", None) if st.session_state.pop("_SIN_BAJAR", False) else None
if st.session_state.pop("_FLASH", None):
    flash.exito("Hecho.")
flash.mostrar()
if st.session_state.pop("_BAJAR", None):
    st.session_state["_bajar_x"] = True
    from core import projects_ui as PU
    with st.container(key="x"):
        PU._bajar_a("x", "_bajar_x")
H.subir_si_cambia_la_vista()
'''
at = AppTest.from_string(G4, default_timeout=60)


def paso(**ss):
    at.session_state["_PASO"] = {k: v for k, v in ss.items() if not k.startswith("_F") and k not in ("_BAJAR",)}
    for k in ("_FLASH", "_BAJAR"):
        if k in ss:
            at.session_state[k] = ss[k]
    n0 = len(at.session_state["_LL"]) if "_LL" in at.session_state else 0
    at.run()
    return [s for s in at.session_state["_LL"][n0:] if "scrollTo" in s]


chk("1ª pasada de la sesión: no sube (no hay vista anterior)", paso() == [])
chk("la misma vista: no sube (no mueve a nadie mientras trabaja)", paso() == [])
_s = paso(_cli_open="CLI-1")
chk("⚠️ abrir una ficha (`_cli_open`): SUBE, al terminar la pasada",
    len(_s) == 1 and "SOLO=0" in _s[0] and "scrollTo({top:0" in _s[0] and "'running'" in _s[0], _s)
chk("…y en la pasada siguiente, ya no (una vez por cambio)", paso() == [])
chk("volver a la lista (sin `_cli_open`): sube", len(paso(_cli_open=None)) == 1)
chk("⚠️ otra SECCIÓN desde el menú (Inventory donde estaba la lista): sube", len(paso(_admin_sec="inventario")) == 1)
chk("la búsqueda de arriba (otra pantalla): sube", len(paso(topbar_search="bondi")) == 1)
chk("…y al quitarla: sube", len(paso(topbar_search="")) == 1)
chk("⚠️ si la pasada BAJA a algo pedido (`_bajar_a`), manda la bajada: no sube",
    paso(_inv_open="ACT-1", _BAJAR=True) == [] and any(".st-key-x" in s for s in at.session_state["_LL"][-3:]))
_s = paso(_FLASH=True)
chk("⚠️ un aviso NUEVO sin cambiar de vista: sube SOLO si quedó por encima (`SOLO=1`, busca `.st-key-cpx_flash`)",
    len(_s) == 1 and "SOLO=1" in _s[0] and ".st-key-cpx_flash" in _s[0], _s)
chk("…y la condición está: no sube si el aviso ya se ve (su borde de arriba dentro de la vista)",
    "if(f.getBoundingClientRect().top>=t-1)return;" in _s[0] if _s else False)
chk("…su repetición de v560 (otra pasada enseguida) no vuelve a subir", paso() == [])
chk("el aviso se pinta en su bloque `cpx_flash`",
    flash.BLOQUE == "cpx_flash" and "with st.container(key=BLOQUE):" in fuente("core/flash.py"))
chk("⚠️ la marca de «aviso nuevo» NO casa con «lo abierto» (casaba `_flash_nuevo`: el aviso contaba como cambio de vista y subía SIEMPRE)",
    not home_ui._RE_ABIERTO.match(flash.NUEVO), flash.NUEVO)
_ab = set()
for f in os.listdir(os.path.join(RAIZ, "core")):
    if f.endswith(".py"):
        _arb = ast.parse(fuente("core/" + f))
        # (los trozos de un f-string, como «_open_» de `f"{p}_open_{id}"`, no son claves)
        _trozos = {id(c) for j in ast.walk(_arb) if isinstance(j, ast.JoinedStr) for c in j.values}
        for n in ast.walk(_arb):
            if (isinstance(n, ast.Constant) and id(n) not in _trozos and isinstance(n.value, str) and n.value.startswith("_")
                    and ("_open" in n.value or n.value.endswith(("_nueva", "_nuevo"))) and " " not in n.value):
                _ab.add(n.value)
_fuera = sorted(k for k in _ab if not home_ui._RE_ABIERTO.match(k))
chk("toda clave «lo abierto» de la app (`_…_open…`, `_…_nueva/o`) entra en la firma de la vista (%d)" % len(_ab),
    len(_ab) >= 14 and not _fuera, _fuera)
_app = ast.parse(fuente("app.py"))
_ord = [ast.unparse(n.value.func) for n in _app.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
chk("app.py: la subida va DESPUÉS de la sección y ANTES del fin de pasada de los botones",
    "_home.render_admin_content" in _ord and "_home.subir_si_cambia_la_vista" in _ord and "_botones.fin_de_pasada" in _ord
    and _ord.index("_home.render_admin_content") < _ord.index("_home.subir_si_cambia_la_vista")
    < _ord.index("_botones.fin_de_pasada"), _ord[-4:])
_rac = next(n for n in ast.walk(ast.parse(fuente("core/home_ui.py")))
            if isinstance(n, ast.FunctionDef) and n.name == "render_admin_content")
_src_rac = ast.unparse(_rac)
chk("cada pasada empieza sin «bajada» apuntada (una cortada por `st.rerun()` no bajó)",
    "st.session_state.pop('_bajada_pedida', None)" in _src_rac
    and _src_rac.index("_bajada_pedida") < _src_rac.index("flash.mostrar()"))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n5. ⚠️ El caso visto: «Create client» abre la ficha nueva ARRIBA, con su aviso")
G5 = r'''
import streamlit as st
from core import clientes as C, projects as P, alerts, expenses, invoices as I, incrustar, flash, home_ui as H
from core import clientes_ui as CU
st.session_state.setdefault("auth", ''' + ADMIN + r''')
st.session_state.setdefault("_admin_sec", "contactos")
LL = st.session_state.setdefault("_LL", [])
incrustar.script = lambda h, *a, **k: LL.append(h)
F = st.session_state.setdefault("_F", [{"ID": "CLI-1", "Name": "Meridian", "Group": "G", "Active": "SI",
    "ContactName": "", "Phone": "", "Email": "", "Address": ""}])
C.is_configured = lambda: True
C.list_clientes = lambda g=None, incluir_inactivos=False: [dict(f) for f in F]
C.get_cliente = lambda cid: next((dict(f) for f in F if f["ID"] == cid), {})
def _crear(grupo, nombre, *a, **k):
    F.append({"ID": "CLI-2", "Name": nombre, "Group": "G", "Active": "SI", "ContactName": "",
              "Phone": "", "Email": "", "Address": ""})
    return True, "CLI-2"
C.create_cliente = _crear
P.list_projects = lambda *a, **k: []
P.project_hours_bulk = lambda g: {}
alerts.is_configured = lambda: False
expenses.is_configured = lambda: False
I.is_configured = lambda: False
st.session_state.pop("_bajada_pedida", None)
flash.mostrar()
CU.render_contactos("G")
H.subir_si_cambia_la_vista()
'''
at = AppTest.from_string(G5, default_timeout=120)
at.run()
at.run()
_n0 = len(at.session_state["_LL"])
next(t_ for t_ in at.text_input if str(t_.key).startswith("cli_new_nom_")).set_value("Nuevo SA")
next(b for b in at.button if "Create client" in str(b.label)).click()
at.run()
_s = [s for s in at.session_state["_LL"][_n0:] if "scrollTo" in s]
chk("sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("⚠️ la ficha nueva (CLI-2) se abre con «Client created.» y la página SUBE (en v602, ~190 px abajo)",
    at.session_state["_cli_open"] == "CLI-2" and any("Client created." in str(x.value) for x in at.success)
    and len(_s) == 1 and "SOLO=0" in _s[0], (at.session_state["_cli_open"] if "_cli_open" in at.session_state else None, _s))

# ═══════════════════════════════════════════════════════════════════════════════════════════
print("\n6. «Issue invoice» AVISA (abría la factura sin decir nada)")
G6 = r'''
import datetime as dt
import streamlit as st
from core import invoices_ui as IU, invoices as I, clientes as C, clock, xero_ui, contable, auth, flash
from core import projects as P
st.session_state.setdefault("auth", ''' + ADMIN + r''')
clock.today = lambda *a, **k: dt.date(2026, 10, 26)
I.is_configured = lambda: True
I.list_facturas = lambda g=None, **k: []
_NUEVA = {"ID": "FAC-9", "Number": "0009", "Group": "G", "ClientID": "CLI-1", "ClientName": "Cliente Uno",
          "Date": "2026-10-26", "ExpiryDate": "2026-11-09", "Total": "550", "Subtotal": "500", "TaxPct": "10",
          "Tax": "50", "Collected": "0", "Status": "emitida", "Note": "", "Created": "2026-10-26 10:00:00",
          "LinesJSON": "[]", "CollectionsJSON": "[]"}
I.get_factura = lambda fid: dict(_NUEVA) if fid == "FAC-9" else None
def _crear(**k):
    st.session_state["_CREADA"] = k
    return True, "FAC-9"
I.create_factura = _crear
I.pendiente_de_facturar = lambda *a, **k: 500.0
C.get_cliente = lambda cid: {"ID": cid, "Name": "Cliente Uno"}
C.list_clientes = lambda g=None, **k: [{"ID": "CLI-1", "Name": "Cliente Uno"}]
C.es_del_cliente = lambda p, cid, cn: True
P.list_projects = lambda *a, **k: [] if k.get("incluir_archivados") else [
    {"ID": "PRJ-1", "Name": "Obra Uno", "Group": "G", "ClientID": "CLI-1", "Status": "In progress"}]
contable.identidad = lambda g: {}
auth.group_tax_default = lambda g: 10.0
xero_ui.boton_factura = lambda *a, **k: None
flash.mostrar()
IU.render_facturas("G")
'''
at = AppTest.from_string(G6, default_timeout=120)
at.session_state["_fac_nueva"] = True
at.run()
chk("sin excepción (el alta)", not at.exception, [e.value for e in at.exception][:1])
next(b for b in at.button if b.key == "fac_emit").click()
at.run()
chk("⚠️ emite, abre la factura y AVISA «Invoice No. 0009 issued.»",
    "_CREADA" in at.session_state and at.session_state["_fac_open"] == "FAC-9"
    and any("Invoice No. 0009 issued." in str(x.value) for x in at.success),
    ([str(x.value) for x in at.success], [str(x.value) for x in at.error][:2]))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
for f in fallos:
    print("  - " + f)
sys.exit(1 if fallos else 0)
