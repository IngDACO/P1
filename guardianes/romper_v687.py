# -*- coding: utf-8 -*-
"""Batería de roturas de v687. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v687"
TOPE_S = 300
PU, CA, AUI = "core/projects_ui.py", "core/chat_agent.py", "core/ausencias_ui.py"

ROTURAS = [
    # ── «My route»: el mapa solo con el desplegable abierto ──
    ("⚠️ la ruta (y su mapa) se pinta con el desplegable cerrado", PU,
     [("            if _exp_ruta.open:", "            if True:")]),
    ("el desplegable sin `on_change` (no sabe si está abierto)", PU,
     [("                                on_change=\"rerun\")", "                                )")]),
    # ── el Field assistant responde solo a lo pedido ──
    ("⚠️ el campo no recibe el recordatorio", CA,
     [("    _mas = _SOLO_LO_PEDIDO if rol in (\"administrator\", \"field\") else \"\"",
       "    _mas = _SOLO_LO_PEDIDO if rol == \"administrator\" else \"\"")]),
    ("la guía del campo sin la regla", CA,
     [("        # de v679 en la oficina, que no llegó al campo.\n"
       "        \"- Responde SOLO a lo que te pide ahora. No comentes, repitas ni corrijas por tu cuenta lo que se dijo o se hizo \"\n",
       "        # de v679 en la oficina, que no llegó al campo.\n"
       "        \"- Responde a lo que te pide ahora. \"\n")]),
    # ── ausencias: «From» arrastra «To» ──
    ("⚠️ «From» no arrastra «To»", AUI,
     [("        if _d and _h and _h < _d:\n            st.session_state[clave_hasta] = _d",
       "        if False:\n            st.session_state[clave_hasta] = _d")]),
    ("«To» se mueve también cuando ya iba después", AUI,
     [("        if _d and _h and _h < _d:", "        if _d and _h and _h != _d:")]),
    ("My absences sin el arrastre", AUI,
     [("                                  on_change=_hasta_no_antes, args=(f\"aus_desde_{_g}\", f\"aus_hasta_{_g}\"))",
       "                                  )")]),
    ("el formulario de la oficina sin el arrastre", AUI,
     [("                              on_change=_hasta_no_antes, args=(f\"aus_of_d_{_g}\", f\"aus_of_h_{_g}\"))",
       "                              )")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", AUI,
           [("    (trampa 31). Llevar «To» hacia atrás sigue dando el aviso, que es lo que toca.\"\"\"",
             "    (trampa 31). (control) Llevar «To» hacia atrás sigue dando el aviso, que es lo que toca.\"\"\"")])


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
