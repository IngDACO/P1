# -*- coding: utf-8 -*-
"""Batería de roturas de v705. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v705"
TOPE_S = 120
XN, CU = "core/xero_nomina.py", "core/contable_ui.py"

ROTURAS = [
    ("vuelve «can still go by file»", XN,
     [("""Payroll stays in COPEX; its "
                                 "timesheet is in «Timesheet for payroll», just above, to key into Xero.\"""",
       """Payroll stays in COPEX, and "
                                 "its timesheet can still go by file (Accounting → «Timesheet for payroll»).\"""")]),
    ("el bloque de Xero Payroll se pinta antes del fichero del parte («just above» deja de ser verdad)", CU,
     [("""        _parte_csv(grupo, desde, hasta)

    # v490 · el envío a Xero Payroll: parte + permisos, con el periodo de SU calendario.
    from core import xero_ui
    xero_ui.render_partes_xero(grupo)
""", """        pass

    # v490 · el envío a Xero Payroll: parte + permisos, con el periodo de SU calendario.
    from core import xero_ui
    xero_ui.render_partes_xero(grupo)
    _parte_csv(grupo, desde, hasta)
""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", XN,
           [("                # v705 · decía que el parte «can still go by file»",
             "                # v705 · decía que el parte «can still go by file» · control")])


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
