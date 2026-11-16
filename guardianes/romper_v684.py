# -*- coding: utf-8 -*-
"""Batería de roturas de v684. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v684"
TOPE_S = 300
INT, CT, TS = "core/interpretation.py", "core/chat_tools.py", "core/tool_save_ui.py"

ROTURAS = [
    ("⚠️ el muro vuelve a «within_its_limit»", INT,
     [("                \"how_it_is_handled\": _como, \"needs_attention\": False,", "                \"within_its_limit\": not _ev,")]),
    ("el muro esquivado empujando, sin decir con qué", INT,
     [("    _como = (\"cleared by the %.1f mm shift towards the REAR (it includes %.1f mm of extra push for the wall)\"",
       "    _como = (\"pushed %.1f mm towards the REAR (it includes %.1f mm of extra push for the wall)\"")]),
    ("el muro ya esquivado, sin decirlo", INT,
     [("\"already clear: at that floor the car is far enough towards the REAR\" if _ev else", "\"\" if _ev else")]),
    ("cómo leerlo, sin el muro ni los buffers", CT,
     [("        \"limiting_wall: how_it_is_handled says how the solution clears it; needs_attention false = nothing to check \"\n",
       "        \"\"\n")]),
    ("⚠️ lo archivado sin la hora", TS, [("usuario=usuario, pdf=pdf_bytes, filename=_arch)", "usuario=usuario, pdf=pdf_bytes, filename=nombre_archivo)")]),
    ("la hora con otro formato (sin el «_»)", TS, [("_ck.now().strftime(\"_%H%M\")", "_ck.now().strftime(\"%H%M\")")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", TS,
           [("        # ⚠️ v684 · Lo ARCHIVADO lleva también la hora", "        # (control) ⚠️ v684 · Lo ARCHIVADO lleva también la hora")])


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
