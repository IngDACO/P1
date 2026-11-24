# -*- coding: utf-8 -*-
"""v707 · el marco de la app (repaso de diseño con el usuario, 24/11/2026; maqueta vista y aprobada en el panel).

1. Menú lateral, de arriba abajo: el logo («Lift installation management», sin la versión), el usuario (nombre, rol
   con mayúscula y la empresa), el MENÚ, el fichaje (selector y botón en una fila) y «Sign out» al pie. El menú iba
   después del fichaje: en una ventana de 622 px de alto empezaba en el píxel 583.
2. El asistente sale del menú lateral: una burbuja flotante lo abre en un panel a la derecha (`st.dialog`,
   `position="right"`); la conversación en una caja con su scroll que baja sola, y el cuadro de escribir debajo.
   Con un chat largo, el menú lateral pasaba de 1184 a 3159 px (2 mensajes).
3. Fuera «Fork», GitHub y el ⋮ de Streamlit Cloud; la barra sube 40 px con el menú lateral abierto (con él cerrado
   no: en la cabecera va «>>»); la cabecera ya no tapa los clics; abajo 6rem para la insignia de Streamlit Cloud.
4. La pestaña del navegador «COPEX vNNN» y el buscador «Search jobs, people…» (en el móvil se cortaba).

Sin red ni escrituras: AppTest con el asistente y la memoria sustituidos (guardados y devueltos, trampa 48).
"""
import ast
import os
import re
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def funcion(src, nombre):
    f = next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)
    return ast.get_source_segment(src, f) if f else ""


from streamlit.testing.v1 import AppTest                                      # noqa: E402
from core import chat_ui, contable                                            # noqa: E402
import core.chat_agent as CA                                                  # noqa: E402

print("1. El menú lateral, en su orden")
APP = leer("app.py")
_sb = APP[APP.index("with st.sidebar:"):APP.index("_chat_ui.burbuja(_ROL, _GRUPO)")]
_orden = ["Lift installation management", "render_user_info()", "_home.sidebar_menu()", "render_sidebar_chrono()",
          "render_sign_out()"]
_pos = [_sb.find(x) for x in _orden]
chk("logo → usuario → MENÚ → fichaje → «Sign out»", all(p >= 0 for p in _pos) and _pos == sorted(_pos), _pos)
_marca = _sb[:_sb.index("render_user_info()")]
chk("el logo dice «Lift installation management» y ya no la versión", "{APP_VERSION}" not in _marca
    and "Elevator Survey Analyzer" not in re.sub(r"#.*", "", _marca), _marca[-400:])
chk("…y en el menú lateral ya no hay asistente (ni desplegable ni cuadro de escribir)",
    "chat_input" not in _sb and "st.expander" not in _sb)
chk("la pestaña del navegador: «COPEX vNNN»", 'st.set_page_config(page_title=f"COPEX {APP_VERSION}",' in APP)
_t = ast.parse(APP)
_bur = [n for n in _t.body if isinstance(n, ast.Expr) and "burbuja" in ast.unparse(n)]
chk("la burbuja, al nivel del guion (fuera del menú lateral) y ANTES del contenido",
    len(_bur) == 1 and APP.index("_chat_ui.burbuja(_ROL, _GRUPO)") < APP.index("_home.render_topbar(_GRUPO)"),
    [ast.unparse(n) for n in _bur])

print("\n2. El usuario arriba y «Sign out» al pie (auth_ui)")
_G = {}
from core import chat_memoria as _CM                                        # noqa: E402
for m, n in ((contable, "identidad"), (CA, "get_chat_response"), (chat_ui, "recordar"), (chat_ui, "memorizar"),
             (_CM, "borrar")):
    _G[(m, n)] = getattr(m, n)
USR = r'''
import streamlit as st
from core import auth_ui, contable
contable.identidad = lambda g: {"legal": st.session_state["_LEGAL"] or g, "abn": "", "plazo": 14}
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": st.session_state["_ROL"],
                                     "grupo": st.session_state["_GRUPO"]})
auth_ui.render_user_info()
st.write("---SEPARA---")
auth_ui.render_sign_out()
'''
try:
    for rol, grupo, legal, esperado in (("administrator", "cliente1", "", ("Administrator", "cliente1")),
                                        ("administrator", "cliente1", "Northshore Lifts Pty Ltd",
                                         ("Administrator", "Northshore Lifts Pty Ltd")),
                                        ("field", "cliente1", "", ("Field", "cliente1"))):
        a = AppTest.from_string(USR, default_timeout=60)
        a.session_state["_ROL"], a.session_state["_GRUPO"], a.session_state["_LEGAL"] = rol, grupo, legal
        a.run()
        _md = " ".join(str(m.value) for m in a.markdown)
        _b = [str(b.key) for b in a.button]
        chk(f"{rol} · {legal or 'sin razón social'}: «{esperado[0]}» con mayúscula y la empresa «{esperado[1]}»",
            not a.exception and esperado[0] in _md and esperado[1] in _md and "Bobo" in _md, (_md, a.exception))
        chk("…y «Sign out» va aparte (su propia función)", _b == ["logout_btn"], _b)
    _ui = leer("core/auth_ui.py")
    chk("render_user_bar sigue (otros guiones la llaman): pinta las dos", "    render_user_info()\n    render_sign_out()"
        in funcion(_ui, "render_user_bar"))

    print("\n3. El fichaje compacto")
    _sf = funcion(leer("core/timeclock_ui.py"), "_sidebar_sin_fichar")
    chk("el selector y «Clock in» en UNA fila (columnas), el selector sin su etiqueta",
        'st.columns([3, 2], vertical_alignment="bottom"' in _sf and 'label_visibility="collapsed"' in _sf
        and '_c_bot.button(t(":material/check_circle: Clock in")' in _sf)

    print("\n4. La burbuja y el panel (AppTest, con clics)")
    BUR = r'''
import streamlit as st
from core import chat_ui
import core.chat_agent as CA
CA.get_chat_response = lambda **k: (st.session_state.setdefault("_LLAM", []).append(k["user_message"]),
                                    "Answer to " + k["user_message"])[1]
chat_ui.recordar = lambda: None
chat_ui.memorizar = lambda: None
# ⚠️ «Clear the conversation» llama a `olvidar`, que BORRA la memoria en la hoja (el arnés lo paró): sustituida
from core import chat_memoria as CM
CM.borrar = lambda *a, **k: st.session_state.setdefault("_BORRA", []).append(a)
st.session_state.setdefault("auth", {"usuario": "Admin2", "nombre": "Bobo", "rol": "administrator", "grupo": "G"})
st.session_state.setdefault("chat_history", [])
chat_ui.burbuja(st.session_state.get("_ROL", "administrator"), "G")
'''
    a = AppTest.from_string(BUR, default_timeout=60)
    a.run()
    _bb = [b for b in a.button if str(b.key) == "cpx_chat_burbuja"]
    chk("cerrado: solo la burbuja (sin panel, sin cuadro de escribir)", len(_bb) == 1 and len(a.chat_input) == 0
        and not a.exception, (len(_bb), len(a.chat_input)))
    a.button(key="cpx_chat_burbuja").click()
    a.run()
    _dl = a.get("dialog")
    chk("la burbuja abre el panel con el cuadro de escribir", len(_dl) == 1 and len(a.chat_input) == 1, len(_dl))
    # (la posición y el título van DENTRO de `proto.dialog`: se lee del volcado del proto)
    _pd = str(_dl[0].proto)
    chk("…a la DERECHA, como panel, con su título", "position: RIGHT" in _pd
        and 'title: "Management assistant COPEX"' in _pd, _pd[:300])
    a.chat_input[0].set_value("How much on C7?").run()
    _msg = [str(m.value) for m in a.markdown]
    chk("una pregunta: la contesta, y queda la conversación", "How much on C7?" in _msg
        and "Answer to How much on C7?" in _msg and a.session_state["_LLAM"] == ["How much on C7?"], _msg)
    a.run()
    chk("…y el panel sigue abierto en la pasada siguiente (se reabre mientras `_chat_abierto`)",
        len(a.get("dialog")) == 1 and a.session_state["_chat_abierto"] is True)
    a.button(key="clear_chat_sb").click()
    a.run()
    chk("«Clear the conversation» la vacía (y pide borrar la memoria)", a.session_state["chat_history"] == []
        and a.session_state["_BORRA"] == [("Admin2", "G")], a.session_state["_BORRA"] if "_BORRA" in a.session_state else None)
    a2 = AppTest.from_string(BUR, default_timeout=60)
    a2.session_state["_ROL"] = "field"
    a2.run()
    a2.button(key="cpx_chat_burbuja").click()
    a2.run()
    chk("el campo: «Field assistant COPEX»", 'title: "Field assistant COPEX"' in str(a2.get("dialog")[0].proto))
finally:
    for (m, n), f in _G.items():
        setattr(m, n, f)

_cu = leer("core/chat_ui.py")
_bs = funcion(_cu, "burbuja")
chk("el panel: `st.dialog(..., position=\"right\", on_dismiss=_cerrar_chat)`, solo si `_chat_abierto`",
    'position="right"' in _bs and "on_dismiss=_cerrar_chat" in _bs and "if st.session_state.get(_ABIERTO):" in _bs, _bs)
chk("⚠️ la marca no se llama `_…_open…` (contaría como cambio de vista, v603)", '_ABIERTO = "_chat_abierto"' in _cu)
_cv = funcion(_cu, "conversacion")
chk("la conversación en una caja con su scroll que baja sola, y lo nuevo se pinta DENTRO",
    'st.container(height=440, autoscroll=True, border=False, key="cpx_chat_hist")' in _cv
    and _cv.count("with _caja") == 3 and _cv.index("with _caja:") < _cv.index("st.chat_input("), "")
chk("⚠️ volver a pintar solo el panel, con salida si la pasada es entera", "st.rerun(scope=\"fragment\")"
    in funcion(_cu, "_rerun_panel") and "except st.errors.StreamlitAPIException:" in funcion(_cu, "_rerun_panel"))

print("\n5. El CSS del marco (theme)")
from core import theme                                                        # noqa: E402
C = theme._CSS
chk("fuera «Fork», GitHub y el ⋮", '[data-testid="stToolbarActions"], [data-testid="stMainMenu"] { display: none !important; }' in C)
chk("la barra sube 40 px SOLO con el menú lateral abierto (con «>>» en la cabecera, no)",
    '[data-testid="stApp"]:not(:has([data-testid="stExpandSidebarButton"])) div.block-container { margin-top: -40px; }' in C)
chk("⚠️ la cabecera (y sus DIV, la barra de herramientas) no tapan los clics; sus botones sí los reciben",
    '[data-testid="stHeader"], [data-testid="stHeader"] div { pointer-events: none !important; }' in C
    and '[data-testid="stHeader"] button, [data-testid="stHeader"] a { pointer-events: auto !important; }' in C)
chk("abajo 6rem (la insignia de Streamlit Cloud no tapa lo último)", "padding-bottom: 6rem" in C
    and "padding-bottom: 3rem" not in C)
chk("la burbuja: fija, abajo a la derecha, por encima de la insignia", ".st-key-cpx_chat_burbuja { position: fixed !important; right: 20px; bottom: 76px;" in C)
chk("⚠️ la caja de la conversación: se fija la BASE de su envoltorio (`flex: 0 0 440px` mandaba)",
    '[data-testid="stLayoutWrapper"]:has(> .st-key-cpx_chat_hist)' in C and "flex: 0 0 max(220px, calc(100vh - 290px)) !important" in C)
chk("el buscador, corto: «Search jobs, people…»", 'placeholder=t("Search jobs, people…")' in leer("core/home_ui.py"))

print()
print("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}")
sys.exit(1 if FALLOS else 0)
