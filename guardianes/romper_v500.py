# -*- coding: utf-8 -*-
"""Batería de v500: 10 roturas + CONTROL.

⚠️ Se lee QUÉ comprobación falla en cada una (v492) y se confirma el verde de base ANTES
(v459). NO se lanza en paralelo con la suite: modifica el árbol (v455).
"""
import io
import os
import shutil
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v500.py")
COPIAS = os.path.join(AQUI, "_respaldo_v500")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/plan.py", "core/schedule.py", "core/projects.py", "core/projects_ui.py"]

ROTURAS = [
    ("lo no empezado puede arrancar en el PASADO", "core/plan.py",
     "            ini = max(ini_pred, hoy)", "            ini = ini_pred"),
    ("lo en curso no cuenta desde HOY", "core/plan.py",
     'fin[i] = max(hoy, ini) + dur * (1.0 - av / 100.0)',
     'fin[i] = ini + dur * (1.0 - av / 100.0)'),
    ("lo terminado ignora su fecha REAL", "core/plan.py",
     'fin[i] = num(fin_r) if fin_r is not None else ini + dur',
     'fin[i] = ini + dur'),
    ("el pronóstico resuelve las dependencias por su cuenta", "core/plan.py",
     "    preds, avisos = _preparar(acts)\n    hoy = max(0.0, num(hoy))",
     "    preds, avisos = {i: [] for i in range(len(acts))}, []\n    hoy = max(0.0, num(hoy))"),
    ("vuelve a haber DOS respuestas a «cuándo termina»", "core/schedule.py",
     '        "fecha_cadena": fecha_cadena, "dias_cadena": dias_cadena,',
     '        "fecha_proj": fecha_cadena, "proj_dias": dias_cadena,\n'
     '        "fecha_cadena": fecha_cadena, "dias_cadena": dias_cadena,'),
    ("el GANTT deja de dibujar la proyección", "core/schedule.py",
     '    if proj and proj.get("dias_cadena") is not None:',
     '    if proj and proj.get("proj_dias") is not None:'),
    ("la cartera vuelve al retraso por SPI", "core/projects.py",
     'out[str(p.get("ID", ""))] = pr.get("dias_cadena", 0)',
     'out[str(p.get("ID", ""))] = pr.get("dias_gap", 0)'),
    ("las agrupaciones vuelven a la fecha del SPI", "core/projects.py",
     'out[pid] = {"fecha": pr.get("fecha_cadena"), "spi": pr.get("spi"),\n'
     '                            "gap": pr.get("dias_cadena")}',
     'out[pid] = {"fecha": pr.get("fecha_proj"), "spi": pr.get("spi"),\n'
     '                            "gap": pr.get("dias_gap")}'),
    ("la agrupación cae al respaldo viejo", "core/projects.py",
     '        if fecha is None and "fecha_cadena" in pr:\n            fecha = pr.get("fecha_cadena")',
     '        if fecha is None and "fecha_proj" in pr:\n            fecha = pr.get("fecha_proj")'),
    ("el detalle del proyecto vuelve al SPI", "core/projects_ui.py",
     '    dg   = proj.get("dias_cadena", 0.0)', '    dg   = proj.get("dias_gap", 0.0)'),
]

CONTROL = ("core/plan.py", "SIN_PREDECESORA = \"-\"",
           "SIN_PREDECESORA = \"-\"  # cambio inocuo del CONTROL")


def leer(rel):
    with io.open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return f.read()


def escribir(rel, txt):
    with io.open(os.path.join(RAIZ, rel), "w", encoding="utf-8", newline="") as f:
        f.write(txt)


def correr():
    p = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    fallos = [l.strip() for l in (p.stdout or "").splitlines() if "*** FALLO" in l]
    return p.returncode, fallos, "Traceback" in (p.stderr or "")


os.makedirs(COPIAS, exist_ok=True)
for rel in FICHEROS:
    shutil.copy2(os.path.join(RAIZ, rel), os.path.join(COPIAS, rel.replace("/", "_")))
ORIG = {rel: leer(rel) for rel in FICHEROS}


def restaurar(rel):
    escribir(rel, ORIG[rel])
    if leer(rel) != ORIG[rel]:
        shutil.copy2(os.path.join(COPIAS, rel.replace("/", "_")), os.path.join(RAIZ, rel))
    if leer(rel) != ORIG[rel]:
        print("\n*** NO SE PUDO RESTAURAR %s — SE ABORTA" % rel)
        sys.exit(2)


print("verde de base:")
rc, fallos, rev = correr()
if rc != 0 or rev:
    print("  *** el guardián NO está verde con el código bueno: no se prueba nada")
    print("\n".join(fallos))
    sys.exit(2)
print("  ok\n")

cazadas = 0
for nombre, rel, viejo, nuevo in ROTURAS:
    src = ORIG[rel]
    if src.count(viejo) != 1:
        print("  *** ANCLA no única (%d): %s" % (src.count(viejo), nombre))
        continue
    escribir(rel, src.replace(viejo, nuevo))
    rc, fallos, rev = correr()
    restaurar(rel)
    if rev:
        print("  ?? REVIENTA  %s  (no cuenta)" % nombre)
    elif rc != 0 and fallos:
        cazadas += 1
        print("  CAZADA  %-48s -> %s" % (nombre[:48], fallos[0][12:88]))
    else:
        print("  ESCAPA  %s" % nombre)

rel, viejo, nuevo = CONTROL
escribir(rel, ORIG[rel].replace(viejo, nuevo, 1))
rc, fallos, rev = correr()
restaurar(rel)
print("\n  CONTROL: %s" % ("pasa (correcto)" if rc == 0 and not rev else "*** FALLA"))
for rel in FICHEROS:
    restaurar(rel)
print("\n%d de %d roturas cazadas · árbol restaurado y verificado" % (cazadas, len(ROTURAS)))
