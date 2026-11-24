# -*- coding: utf-8 -*-
"""Batería de roturas de v707. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v707"
TOPE_S = 300
APP, AU, TC, CH, TH, HO = ("app.py", "core/auth_ui.py", "core/timeclock_ui.py", "core/chat_ui.py", "core/theme.py",
                           "core/home_ui.py")

ROTURAS = [
    ("el logo vuelve a «Elevator Survey Analyzer»", APP,
     [("            Lift installation management\n", "            Elevator Survey Analyzer\n")]),
    ("el menú vuelve debajo del fichaje", APP,
     [("""    from core import home_ui as _home
    st.session_state["_admin_sec"] = _home.sidebar_menu()
    st.markdown("---")

    # ── Fichaje (v202/v374): admin y campo, debajo del menú ──
    if _ROL in ("administrator", "field"):
        from core.timeclock_ui import render_sidebar_chrono
        render_sidebar_chrono()
""", """    # ── Fichaje (v202/v374): admin y campo, debajo del menú ──
    if _ROL in ("administrator", "field"):
        from core.timeclock_ui import render_sidebar_chrono
        render_sidebar_chrono()
    from core import home_ui as _home
    st.session_state["_admin_sec"] = _home.sidebar_menu()
    st.markdown("---")
""")]),
    ("«Sign out» vuelve arriba, con el usuario", APP,
     [("    render_user_info()\n", "    render_user_info()\n    render_sign_out()\n"),
      ("    # ── Salir, al pie ──\n    render_sign_out()\n", "")]),
    ("la pestaña vuelve a «COPEX Survey Analyzer»", APP,
     [('st.set_page_config(page_title=f"COPEX {APP_VERSION}",', 'st.set_page_config(page_title=f"COPEX Survey Analyzer {APP_VERSION}",')]),
    ("el rol vuelve en minúscula", AU,
     [('rol_lbl = f"{_ico_rol} {str(_etq(_rol))[:1].upper()}{str(_etq(_rol))[1:]}".strip() if _rol else ""',
       'rol_lbl = f"{_ico_rol} {_etq(_rol)}".strip() if _rol else ""')]),
    ("la empresa vuelve a ser siempre el grupo", AU,
     [('grupo = (_empresa(a.get("grupo")) if a.get("grupo")', 'grupo = (a.get("grupo") if a.get("grupo")')]),
    ("el fichaje vuelve a tres alturas (con su etiqueta)", TC,
     [('vacio=t("— pick the site —"),\n                         label_visibility="collapsed")', 'vacio=t("— pick the site —"))')]),
    ("la burbuja no abre nada", CH,
     [('st.button(":material/smart_toy:", key="cpx_chat_burbuja", type="primary", on_click=_abrir_chat,',
       'st.button(":material/smart_toy:", key="cpx_chat_burbuja", type="primary",')]),
    ("el panel sale en el centro", CH,
     [('width="small", position="right"', 'width="small", position="center"')]),
    ("el panel se cierra solo en la pasada siguiente", CH,
     [("    if st.session_state.get(_ABIERTO):\n", "    if st.session_state.pop(_ABIERTO, False):\n")]),
    ("lo nuevo vuelve a pintarse debajo del cuadro de escribir", CH,
     [('        with _caja, st.chat_message("user", avatar="🧑‍🔧"):', '        with st.chat_message("user", avatar="🧑‍🔧"):')]),
    ("«Clear the conversation» no la vacía", CH,
     [("            st.session_state.chat_history = []\n            olvidar()", "            olvidar()")]),
    ("la marca se llama `_chat_open` (cambio de vista)", CH,
     [('_ABIERTO = "_chat_abierto"', '_ABIERTO = "_chat_open"')]),
    ("vuelven «Fork», GitHub y el ⋮", TH,
     [('[data-testid="stToolbarActions"], [data-testid="stMainMenu"] {{ display: none !important; }}\n', '')]),
    ("la barra sube también con «>>» en la cabecera", TH,
     [('[data-testid="stApp"]:not(:has([data-testid="stExpandSidebarButton"])) div.block-container {{ margin-top: -40px; }}',
       'div.block-container {{ margin-top: -40px; }}')]),
    ("la barra de herramientas vuelve a tapar los clics", TH,
     [('[data-testid="stHeader"], [data-testid="stHeader"] div {{ pointer-events: none !important; }}',
       '[data-testid="stHeader"] {{ pointer-events: none !important; }}')]),
    ("abajo vuelve a 3rem (la insignia tapa lo último)", TH,
     [("padding-top: 2.2rem; padding-bottom: 6rem;", "padding-top: 2.2rem; padding-bottom: 3rem;")]),
    ("la caja de la conversación vuelve a 440 px fijos", TH,
     [("  flex: 0 0 max(220px, calc(100vh - 290px)) !important; ", "  ")]),
    ("el buscador vuelve al texto largo", HO,
     [('placeholder=t("Search jobs, people…")', 'placeholder=t("Search projects, people, assets, invoices…")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CH,
           [("# v707 · La burbuja: el asistente en su propio panel, fuera del menú lateral",
             "# v707 · La burbuja: el asistente en su propio panel, fuera del menú lateral · control")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
