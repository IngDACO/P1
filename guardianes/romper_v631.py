# -*- coding: utf-8 -*-
"""Batería de roturas de v631. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v631"
TOPE_S = 120
C = "core/chat_agent.py"
T = "core/timeclock_ui.py"
R = "core/rail_cut.py"
A = "core/prestart_pdf.py"

ROTURAS = [
    # ── Las siglas en la guía ──
    ("⚠️ RZ y RO pasan a ser de contrapeso", C,
     [("- **RZ, RO:** rieles de cabina,", "- **RZ, RO:** rieles de contrapeso,")]),
    ("⚠️ LFKK vuelve a ser «el del primer riel»", C,
     [("Rails usa LFKK para los rieles de cabina y LFGK para\n  los de contrapeso, en Case 1 y en Case 2.",
       "Rails usa LFKK para el primer riel y LFGK para\n  el último.")]),
    ("⚠️ le ponen una definición sin glosario", C,
     [("- **LFKK** y **LFGK** son dos valores del plano.", "- **LFKK** es la longitud del riel de cabina.")]),
    ("⚠️ deja de decir que no tiene la definición", C,
     [("**De estas dos NO tienes la definición:** no sabes qué\n  miden ni qué significan sus letras. ", "")]),
    ("⚠️ ya no descarta lo del primer riel", C,
     [(" ⚠️ Ninguna es «la del\n  primer riel» ni «la del último»: Case 1 y Case 2 usan las dos.", "")]),
    ("⚠️ el bloque deja de mandar parar", C,
     [("responde\ncon esto y para: no añadas qué miden, cómo se miden ni qué significan sus letras. ", "responde\ncon esto. ")]),
    ("⚠️ vuelve la línea vieja de Rails", C,
     [("- **Rails:** el corte de riel de cada elevador, con LFKK y LFGK del plano. **Case 1:** el corte va",
       "- **Rails:** lee LFKK (primer riel) y LFGK (último riel) del plano. **Case 1:** el corte va")]),
    ("«qué representa cada parámetro» vuelve a invitar a inventar", C,
     [("qué es TKSW, etc.), si está definido en esta guía\n", "qué es TKSW, etc.)\n")]),
    # ── ⚠️ Lo importante: cambia la APP y la guía se queda atrás ──
    ("⚠️ cambia el texto de RZ/RO en su pantalla", "core/rail_cut_ui.py",
     [("RZ, RO = car rails · RF, RB = counterweight rails", "RZ, RO = counterweight rails · RF, RB = car rails")]),
    ("⚠️ cambia HGP en Belting", "core/belting_ui.py",
     [("HGP — design striker↔buffer (mm)", "HGP — design distance (mm)")]),
    ("⚠️ cambia HKP en Buffers", "core/buffer_cut_ui.py",
     [("HKP (mm) — car striker ↔ buffer serving the 1st level", "HKP (mm) — car plate ↔ buffer serving the 1st level")]),
    ("⚠️ el plano aporta una sigla que el bloque no explica", "core/plan_data.py",
     [("""("HQ", _v("hq")), ("HGP", _v("hgp"))]},""", """("HQ", _v("hq")), ("HGP", _v("hgp")), ("HXY", _v("hq"))]},""")]),
    # ── El motor deja de hacer lo que dice la guía ──
    ("⚠️ Case 1: LFKK pasa al contrapeso", R,
     [("        rc  = L + float(lfkk)\n", "        rc  = L + float(lfgk)\n")]),
    ("⚠️ Case 2: RZ pasa a usar LFGK", R,
     [("""            "CutRZ": float(lfkk) + sign * rz,\n""", """            "CutRZ": float(lfgk) + sign * rz,\n""")]),
    # ── La baja ──
    ("⚠️ la guía vuelve a callarse que el atajo no registra", C,
     [("no registra nada y solo lo lleva a My\n  absences, donde sigue por el paso 2.\n", "y registra la baja.\n")]),
    ("⚠️ el botón pasa a registrar y la guía no lo sabe", T,
     [("""            navegar("autogestion", "🌴 Ausencias")\n""", """            navegar("autogestion", "🌴 Ausencias")\n            ausencias.registrar_baja(usuario, grupo)\n""")]),
    ("⚠️ el botón lleva a otra pantalla", T,
     [("""            navegar("autogestion", "🌴 Ausencias")\n""", """            navegar("autogestion", "💰 Colillas")\n""")]),
    # ── «Switch project» ──
    ("⚠️ el selector vuelve a media columna", T,
     [("""                _nuevo = ui.elegir(t("Switch project"), _otros, key="tc_switch",\n                                   vacio=t("— switch to… —"))\n""",
       """                with st.columns(2)[1]:\n                    _nuevo = ui.elegir(t("Switch project"), _otros, key="tc_switch",\n                                       vacio=t("— switch to… —"))\n""")]),
    ("⚠️ «Leave the project» vuelve a media columna", T,
     [("""            if st.button(t(":material/cancel: Leave the project"), width="stretch", key="tc_prj_out"):\n""",
       """            if st.columns(2)[0].button(t(":material/cancel: Leave the project"), width="stretch", key="tc_prj_out"):\n""")]),
    # ── El anexo ──
    ("⚠️ vuelve «Proyecto»", A,
     [("""Paragraph(f"<b>{d('Project')}</b><br/>" +""", """Paragraph("<b>Proyecto</b><br/>" +""")]),
    ("⚠️ vuelve la fecha ISO", A,
     [("""_esc(dmy(info.get("fecha", "")))""", """_esc(info.get("fecha", ""))""")]),
    ("«Location» deja de pasar por d()", A,
     [("""Paragraph(f"<b>{d('Location')}</b><br/>" +""", """Paragraph("<b>Location</b><br/>" +""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", C,
           [("# máximo de mensajes guardados en memoria (evita tokens infinitos)", "# (control) máximo de mensajes guardados en memoria")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for a, b in cambios:
        if txt.count(a) != 1:
            return False, bak, p, "ancla x%d: %s" % (txt.count(a), a[:60])
        txt = txt.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if not ok:
            print("  ESCAPA %s (%s)" % (desc, msg))
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
