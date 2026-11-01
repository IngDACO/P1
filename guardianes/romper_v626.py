# -*- coding: utf-8 -*-
"""Batería de roturas de v626. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v626"
TOPE_S = 240
HU = "core/home_ui.py"
SU = "core/survey_ui.py"
PU = "core/projects_ui.py"

ROTURAS = [
    ("⚠️ la bajada vuelve a quedar debajo de la barra", PU,
     [("""            "if(c&&s!=='running'){c.style.scrollMarginTop='68px';"\n""",
       """            "if(c&&s!=='running'){"\n""")]),
    ("⚠️ el margen no llega a los 60 px de la barra", PU,
     [("c.style.scrollMarginTop='68px';", "c.style.scrollMarginTop='40px';")]),
    ("⚠️ la campana vuelve a repetir la línea", HU,
     [('                _esperan[_pid] = _esperan.get(_pid, 0) + 1\n', '                _esperan[_pid + "x" * len(_esperan)] = 1\n')]),
    ("la campana no dice cuántos", HU,
     [("                        if _n == 1 else\n", "                        if _n >= 1 else\n")]),
    ("el número de la campana no se pone", HU,
     [(""".replace("{n}", str(_n)).replace("{p}", _nom))\n""", """.replace("{p}", _nom))\n""")]),
    ("⚠️ Files no dice cuál", PU,
     [('    if puede_borrar and _esperan:\n', '    if False:\n')]),
    ("⚠️ Files se lo dice también al campo", PU,
     [('    if puede_borrar and _esperan:\n', '    if _esperan:\n')]),
    ("Files sigue diciéndolo con la decisión tomada", PU,
     [('                if toolruns.datos_de(r).get("por_decidir") and str(r.get("DriveID", "")).strip()]\n',
       '                if "por_decidir" in toolruns.datos_de(r) and str(r.get("DriveID", "")).strip()]\n')]),
    ("Files pide tocar una fila que no existe", PU,
     [('                if toolruns.datos_de(r).get("por_decidir") and str(r.get("DriveID", "")).strip()]\n',
       '                if toolruns.datos_de(r).get("por_decidir")]\n')]),
    ("el nombre del archivo sin escapar", PU,
     [('    _esperan = [maps.literal_md(r.get("File")) for r in runs\n', '    _esperan = [str(r.get("File")) for r in runs\n')]),
    ("⚠️ el texto de la oficina vuelve al campo", SU,
     [('                    if not _es_campo:\n                        st.caption(t("The parameters, the matrix',
       '                    if True:\n                        st.caption(t("The parameters, the matrix')]),
    ("⚠️ la oficina pierde su texto", SU,
     [('                    if not _es_campo:\n                        st.caption(t("The parameters, the matrix',
       '                    if False:\n                        st.caption(t("The parameters, the matrix')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", HU,
           [("# v626 · Una línea por OBRA: dos en la misma salían", "# v626 · (control) Una línea por OBRA: dos en la misma salían")])


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
