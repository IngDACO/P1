# -*- coding: utf-8 -*-
"""Batería de roturas de v645. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v645"
TOPE_S = 120
U = "core/chat_ui.py"
M = "core/chat_memoria.py"
A = "core/chat_agent.py"

ROTURAS = [
    # ── La app marca lo suyo ──
    ("⚠️ Cancel sin marcar", U,
     [("""                      "app": "cancel", "card": a["titulo"]})\n""", """                      })\n""")]),
    ("⚠️ Confirm sin marcar", U,
     [("""    _hist.append({"role": "assistant", "content": ("✅ " if ok else "⚠️ ") + str(msg), "app": "confirm", "card": a["titulo"]})\n""",
       """    _hist.append({"role": "assistant", "content": ("✅ " if ok else "⚠️ ") + str(msg)})\n""")]),
    ("sin decir qué tarjeta", U,
     [(""""app": "confirm", "card": a["titulo"]})""", """"app": "confirm"})""")]),
    # ── La memoria la conserva ──
    ("⚠️ la memoria pierde la marca", M,
     [("""            **({"app": str(m["app"]), "card": str(m.get("card") or "")} if m.get("app") else {})}\n""", """            }\n""")]),
    # ── Lo que le llega al modelo ──
    ("⚠️ el historial vuelve a ir tal cual", A,
     [("""    messages = [_para_el_modelo(m) for m in trimmed]\n""", """    messages = [{"role": m["role"], "content": m["content"]} for m in trimmed]\n""")]),
    ("⚠️ la marca no se mira", A,
     [("""    if m.get("role") == "assistant" and m.get("app"):\n""", """    if False:\n""")]),
    ("⚠️ un Cancel llega como si se hubiera confirmado", A,
     [("""        if m.get("app") == "cancel":\n            return {"role": "user", "content": f"[I pressed Cancel""",
       """        if False:\n            return {"role": "user", "content": f"[I pressed Cancel""")]),
    ("⚠️ no dice que lo hizo la app", A,
     [("""The app, not you, handled it and \"""", """It was handled and \"""")]),
    ("⚠️ la nota sigue siendo un turno del asistente", A,
     [("""        return {"role": "user", "content": f"[I pressed Confirm""", """        return {"role": "assistant", "content": f"[I pressed Confirm""")]),
    ("⚠️ la nota sin lo que contestó la app", A,
     [("""f"replied: {m['content']}]"}""", """f"replied.]"}""")]),
    ("⚠️ la marca llega a la API", A,
     [("""    return {"role": m["role"], "content": m["content"]}\n""", """    return dict(m)\n""")]),
    # ── Lo que se le dice ──
    ("⚠️ el campo no sabe de esas notas", A,
     [("""        "falló, dilo y que decida la persona.\\n"
        "- De los turnos anteriores solo ves el texto, no las herramientas que usaste: eso no significa que no las "
        "usaras, así que no te corrijas por ello.\\n"
        "- Las notas entre corchetes que empiezan por «[I pressed Confirm» o «[I pressed Cancel» las escribe la APP "
        "cuando la persona toca una tarjeta: lo que dicen pasó de verdad. No las niegues ni digas que fueron tuyas; si "
        "dicen que falló, no lo reintentes por tu cuenta.\\n"
""", """        "falló, dilo y que decida la persona.\\n"
        "- De los turnos anteriores solo ves el texto, no las herramientas que usaste: eso no significa que no las "
        "usaras, así que no te corrijas por ello.\\n"
""")]),
    ("⚠️ la oficina no sabe de esas notas", A,
     [("""        "tarifas, ni marcar avance: lo hace la persona, y le dices dónde. Puedes redactarle los mensajes.\\n"
        "- De los turnos anteriores solo ves el texto, no las herramientas que usaste: eso no significa que no las "
        "usaras, así que no te corrijas por ello.\\n"
        "- Las notas entre corchetes que empiezan por «[I pressed Confirm» o «[I pressed Cancel» las escribe la APP "
        "cuando la persona toca una tarjeta: lo que dicen pasó de verdad. No las niegues ni digas que fueron tuyas; si "
        "dicen que falló, no lo reintentes por tu cuenta.\\n"
""", """        "tarifas, ni marcar avance: lo hace la persona, y le dices dónde. Puedes redactarle los mensajes.\\n"
        "- De los turnos anteriores solo ves el texto, no las herramientas que usaste: eso no significa que no las "
        "usaras, así que no te corrijas por ello.\\n"
""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", M,
           [("# v645 · lo que escribió la app al tocar una tarjeta lo sigue siendo mañana", "# v645 · (control) lo de la app sigue siéndolo")])


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
