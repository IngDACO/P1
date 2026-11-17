# -*- coding: utf-8 -*-
"""Batería de roturas de v679. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v679"
TOPE_S = 300
CA = "core/chat_agent.py"

# ⚠️ v687 · re-ancladas: el campo tiene ahora la MISMA regla (texto idéntico), así que cada ancla empieza por el
# comentario de v679, que solo va en la oficina.
_P = "        # 2 de 2 comentó la aprobación de una ausencia de un turno anterior al pedirle solo una tarea\n"
_L1 = "        \"- Responde SOLO a lo que te pide ahora. No comentes, repitas ni corrijas por tu cuenta lo que se dijo o se hizo \"\n"
_L2 = "        \"en turnos anteriores, ni lo que la app contestó al confirmar (la persona ya lo ha visto): era cierto con los \"\n"
_L3 = "        \"datos de entonces. Si te lo pregunta, contesta con lo de ahora.\\n\"\n"
ROTURAS = [
    ("⚠️ la oficina pierde la regla", CA,
     [(_P + _L1, _P + "        \"- \"\n")]),
    ("la regla deja fuera lo que la app contestó al confirmar", CA,
     [(_P + _L1 + _L2, _P + _L1 + "        \"en turnos anteriores: era cierto con los \"\n")]),
    ("la regla se queda sin «si te lo pregunta»", CA,
     [(_P + _L1 + _L2 + _L3, _P + _L1 + _L2 + "        \"datos de entonces.\\n\"\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CA,
           [("        # v679 · visto verificando v678:", "        # (control) v679 · visto verificando v678:")])


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
