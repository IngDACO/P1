# -*- coding: utf-8 -*-
"""Batería de roturas de v632. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v632"
TOPE_S = 120
C = "core/chat_agent.py"

ROTURAS = [
    # ── Lo que se le pide a la API ──
    ("⚠️ vuelve Haiku", C,
     [('MODEL       = "claude-sonnet-5-5"\n', 'MODEL       = "claude-haiku-4-5"\n')]),
    ("el esfuerzo deja de decirse", C,
     [('            output_config = {"effort": ESFUERZO},\n', '')]),
    ("⚠️ `max_tokens` vuelve a 1024: el razonamiento se come la respuesta", C,
     [('MAX_TOKENS  = 4096 ', 'MAX_TOKENS  = 1024 ')]),
    ("sin respaldo del servidor", C,
     [('            fallbacks     = "default",\n', '')]),
    ("sin su beta", C,
     [('            betas         = [_BETA_RESPALDO],\n', '')]),
    ("⚠️ una temperatura, que Sonnet 5.5 rechaza", C,
     [('            max_tokens    = MAX_TOKENS,\n', '            max_tokens    = MAX_TOKENS,\n            temperature   = 0.2,\n')]),
    ("el resumen de la oficina se mueve sin que nadie lo pidiera", C,
     [('MODEL_RESUMEN = "claude-haiku-4-5"', 'MODEL_RESUMEN = "claude-sonnet-5-5"')]),
    # ── Lo que vuelve ──
    ("⚠️ vuelve `content[0].text`", C,
     [('            return _texto_de(r)\n', '            return r.content[0].text\n')]),
    ("⚠️ el rechazo deja de mirarse", C,
     [("""    if r.stop_reason == "refusal":\n        return "⚠️ I can't answer that one. Try asking it another way, or ask the office."\n""", "")]),
    ("cortada por tokens y sin decirlo", C,
     [('    if txt and r.stop_reason == "max_tokens":\n        txt += "\\n\\n⚠️ That answer was cut short: ask me to continue."\n', '')]),
    ("⚠️ el chat en blanco", C,
     [('    return txt or "⚠️ I could not get an answer this time. Try again."\n', '    return txt\n')]),
    # ── La receta de la baja ──
    ("⚠️ el atajo vuelve a My absences", C,
     [("es un botón de **Timeclock**, NO de My\n  absences:", "es un botón de **My absences**:")]),
    ("⚠️ vuelve la cuadrilla", C,
     [("la oficina recibe el aviso.", "la cuadrilla recibe el aviso.")]),
    ("el paso 2 cita un selector que no existe", C,
     [("2. En **What do you need?** elige", "2. En **Type** elige")]),
    # ── ⚠️ Lo importante: cambia la APP y la receta se queda atrás ──
    ("⚠️ cambia el selector de la pantalla", "core/ausencias_ui.py",
     [('t("What do you need?")', 't("Type of absence")')]),
    ("las fechas dejan de venir con hoy", "core/ausencias_ui.py",
     [('t("From"), value=hoy', 't("From"), value=None')]),
    ("⚠️ la baja deja de avisar a la oficina", "core/ausencias_ui.py",
     [("    _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg, _ex)\n", "")]),
    ("⚠️ la baja deja de entrar en la planificación", "core/ausencias_ui.py",
     [("_ok2, _nd = AU.aplicar_al_roster(AU.get(res) or {})", "_ok2, _nd = True, 0")]),
    ("⚠️ la baja pasa a necesitar aprobación", "core/ausencias.py",
     [("""                 "aprobacion": False, "pagado": True,  "dias_anio": 10,\n""", """                 "aprobacion": True, "pagado": True,  "dias_anio": 10,\n""")]),
    ("el atajo sale en otros casos", "core/timeclock_ui.py",
     [('if rol == "field" and not gen and not prj and hoy["general"] <= 0 and hoy["proyecto"] <= 0:', 'if rol == "field" and not gen and not prj:')]),
    # ── La regla ──
    ("⚠️ se quita «no añadas pasos»", C,
     [(" No añadas pasos\n  ni digas quién se entera o qué pasa después si no está aquí.", "")]),
    ("⚠️ se quita «no inventes dónde está»", C,
     [(" No inventes en qué sección o página está un dato.", "")]),
    # ── striker ──
    ("⚠️ vuelve «sticker» en Buffers", "core/buffer_cut_ui.py",
     [("car striker ↔ buffer serving", "car sticker ↔ buffer serving")]),
    ("⚠️ vuelve «sticker» en el diagrama", "core/buffer_cut.py",
     [('_d("CAR STRIKER")', '_d("CAR STICKER")')]),
    ("vuelve «sticker» en la leyenda", "core/buffer_cut.py",
     [('widens the striker")', 'widens the sticker")')]),
    ("la guía se queda en «sticker»", C,
     [("- **HKP:** car striker ↔ buffer", "- **HKP:** car sticker ↔ buffer")]),
    # ── El informe ──
    ("⚠️ vuelve «SI»", "core/report.py",
     [('def _yn(b):   return "YES" if b else "NO"', 'def _yn(b):   return "SI" if b else "NO"')]),
    ("⚠️ vuelve «Valor»", "core/report.py",
     [("""Paragraph(f"<b>{_d('Value')}</b>",        styles["Normal2"])],""", """Paragraph("<b>Valor</b>",                 styles["Normal2"])],""")]),
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
