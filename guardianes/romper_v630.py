# -*- coding: utf-8 -*-
"""Batería de roturas de v630. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v630"
TOPE_S = 120
C = "core/chat_agent.py"
H = "core/home_ui.py"

ROTURAS = [
    # ── El menú de la guía ──
    ("⚠️ vuelve «Mis colillas»", C,
     [("My credentials · My payslips) · Library.\n", "My credentials · Mis colillas) · Library.\n")]),
    ("⚠️ el campo deja de tener Library", C,
     [("My credentials · My payslips) · Library.\n", "My credentials · My payslips).\n")]),
    ("a la oficina le falta Accounting", C,
     [("· Quotes · Catalogue · Accounting) · Inventory", "· Quotes · Catalogue) · Inventory")]),
    ("al propietario le falta API quota", C,
     [("· Rails · Manuals · API quota) · Pre-Start", "· Rails · Manuals) · Pre-Start")]),
    ("las herramientas en español", C,
     [("**Tools**: Survey · Plumb line · Rails", "**Tools**: Survey · Plomada · Rails")]),
    # ── ⚠️ Lo importante: cambia la APP y la guía se queda atrás ──
    ("⚠️ cambia un menú de la app y la guía no", H,
     [("""("💰 Colillas", ":material/payments: My payslips")""", """("💰 Colillas", ":material/payments: Payslips")""")]),
    ("⚠️ una sección nueva en el campo que la guía no conoce", H,
     [("""    ("biblioteca",   ":material/menu_book: Library"),\n]\n# Sus Herramientas""",
       """    ("biblioteca",   ":material/menu_book: Library"),\n    ("nueva",        ":material/star: Something new"),\n]\n# Sus Herramientas""")]),
    ("⚠️ cambia una pestaña de la obra y la guía no", "core/projects_ui.py",
     [(""""✅ Tareas": t(":material/checklist: To-do"),\n""", """"✅ Tareas": t(":material/checklist: Tasks"),\n""")]),
    ("⚠️ un botón cambia de nombre y la guía lo sigue citando", "core/timeclock_ui.py",
     [("""t(":material/cancel: Close forgotten session")""", """t(":material/cancel: Close the session")""")]),
    ("⚠️ la baja pasa a necesitar aprobación", "core/ausencias.py",
     [("""                 "aprobacion": False, "pagado": True,  "dias_anio": 10,\n""", """                 "aprobacion": True, "pagado": True,  "dias_anio": 10,\n""")]),
    ("el campo deja de poder guardar el Survey", "core/survey_ui.py",
     [("""        if _ROL in ("administrator", "owner", "field"):\n""", """        if _ROL in ("administrator", "owner"):\n""")]),
    ("cambia cuántas nóminas salen", "core/payroll_ui.py",
     [("_MAX_COLILLAS = 10", "_MAX_COLILLAS = 20")]),
    # ── Lo que era falso ──
    ("⚠️ vuelve «si no ha fichado, se lo pide»", C,
     [("  - El **usuario de campo** trabaja sobre la obra en la que **fichó** (Timeclock). Si no ha fichado\n",
       "  - El **usuario de campo** no elige nada: usa la obra en la que **fichó** (Timeclock). Si no ha fichado\n")]),
    ("⚠️ la baja espera aprobación en la guía", C,
     [("**Sick leave** no: se registra al momento", "**Sick leave** también: se registra al aprobarse")]),
    ("la guía olvida el To-do del campo", C,
     [("  - **To-do:** la lista de pendientes de la obra, compartida", "  - La lista de pendientes de la obra, compartida")]),
    ("la guía olvida cómo reportar un problema", C,
     [("con **Report a problem to the administrator**, el\n", "con un botón, el\n")]),
    ("vuelve una pantalla en español", C,
     [("""**Files** (una lista ÚNICA""", """**Archivos** (una lista ÚNICA""")]),
    ("se cuela una versión interna", C,
     [("- ⚠️ **El survey NO crea proyectos:**", "- ⚠️ **El survey NO crea proyectos (v135):**")]),
    ("se cuela un nombre de código (confidencialidad)", C,
     [("- **Ubicaciones:** cada dirección enlaza a Google Maps.\n", "- **Ubicaciones:** cada dirección enlaza a Google Maps (maps.py).\n")]),
    # ── No inventar ──
    ("⚠️ desaparece la regla de no inventar", C,
     [("## LO QUE NO SABES, NO LO INVENTES\n", "## NOTAS\n")]),
    ("⚠️ la regla ya no cubre las siglas", C,
     [("NUNCA deduzcas\n  el significado por las letras del nombre, aunque parezca obvio. ", "")]),
    ("⚠️ puede dar cifras que no tiene", C,
     [("dile en qué pantalla verlos, sin dar ninguna cifra.", "dile en qué pantalla verlos.")]),
    ("⚠️ a LFKK le ponen una definición sin glosario", C,
     [("- **Rails:** el corte de riel de cada elevador, con LFKK y LFGK del plano.", "- **Rails:** LFKK es la longitud del riel de cabina; el corte de riel de cada elevador.")]),
    # ── Lo que llega al modelo ──
    ("⚠️ la persona del campo vuelve a lo de antes", C,
     [("""marcar el avance, escribir el parte del día, la lista de pendientes, reportar "\n""", """actualizar el % de avance, reportar "\n""")]),
    ("⚠️ la persona no llega al modelo", C,
     [("""    system = SYSTEM_PROMPT + "\\n\\n" + persona + context_block\n""", """    system = SYSTEM_PROMPT + context_block\n""")]),
    ("⚠️ el campo recibe el estado del grupo", C,
     [("""    if rol == "administrator" and grupo:\n""", """    if grupo:\n""")]),
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
