# -*- coding: utf-8 -*-
"""Batería de roturas de v700. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v700"
TOPE_S = 200
PL = "core/plan.py"

ROTURAS = [
    ("la regla vieja: lo que falta de una empezada no espera a sus predecesoras", PL,
     [("            if ini_pred > sigue:             # v700 · empezada fuera de orden: lo que falta espera",
       "            if False:             # v700 · empezada fuera de orden: lo que falta espera")]),
    ("al esperar se tira lo ya hecho (lo ganado fuera de orden no cuenta)", PL,
     [("                sigue = espera[i] = ini_pred",
       "                sigue = espera[i] = ini_pred; av = 0.0")]),
    ("lo que falta de una en curso ya no corre desde hoy (empieza en su inicio real)", PL,
     [("            sigue = max(hoy, ini)",
       "            sigue = ini")]),
    ("el camino crítico no ve a la que retiene lo que falta", PL,
     [("            if abs(_llega - inicio.get(i, 0.0)) < 1e-6 or (i in espera and abs(_llega - espera[i]) < 1e-6):",
       "            if abs(_llega - inicio.get(i, 0.0)) < 1e-6:")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PL,
           [("    espera = {}      # v700 · en curso y RETENIDA por sus predecesoras: desde cuándo sigue lo que falta",
             "    espera = {}      # v700 · en curso y RETENIDA por sus predecesoras: desde cuándo sigue lo que falta · control")])


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
