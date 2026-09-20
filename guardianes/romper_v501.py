# -*- coding: utf-8 -*-
"""Batería de v501: 11 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v501.py")
COPIAS = os.path.join(AQUI, "_respaldo_v501")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/baseline.py", "core/projects.py", "core/projects_ui.py"]

N = chr(10)
ROTURAS = [
    ("re-fijar PISA la original (lo que lo arruina todo)", "core/baseline.py",
     '    if not bl.get("original"):', "    if True:"),
    ("re-fijar no deja rastro en el historial", "core/baseline.py",
     '    bl["historial"].append({', "    [].append({"),
    ("comparar casa las actividades por POSICIÓN", "core/baseline.py",
     'hoy = {int(a.get("orden", 0) or 0): a for a in (sched or {}).get("activities", []) or []}',
     'hoy = {i + 1: a for i, a in enumerate((sched or {}).get("activities", []) or [])}'),
    ("se compara contra la VIGENTE, no contra la acordada", "core/baseline.py",
     '    base = (bl or {}).get("original") or {}',
     '    base = (bl or {}).get("vigente") or (bl or {}).get("original") or {}'),
    ("una actividad ELIMINADA deja de reportarse", "core/baseline.py",
     "    for o, b in sorted(por_orden.items()):" + N + "        if o not in hoy:",
     "    for o, b in sorted(por_orden.items()):" + N + "        if False:"),
    ("se escribe aunque NO se pueda leer (borra la original)", "core/projects.py",
     "        return False, f\"{t('Could not read the current baseline, so nothing was changed')}: {e}\"",
     "        bl_actual = {}"),
    ("se fija la línea base de una obra sin cronograma", "core/projects.py",
     '    if not sched or not sched.get("activities"):', "    if False:"),
    ("la columna se cuela en MEDIO de la cabecera", "core/projects.py",
     '    "FixedProfit",' + N, '    "BaselineJSON",' + N + '    "FixedProfit",' + N),
    ("falta el valor en la fila posicional", "core/projects.py",
     '        "",                                 # v501: BaselineJSON',
     "        # v501 sin valor:"),
    ("el CAMPO puede fijar líneas base", "core/projects_ui.py",
     'key=f"blset_{pid}"', 'key=f"bl_otro_{pid}"'),
    ("baseline deja de ser módulo hoja (ciclo posible)", "core/baseline.py",
     "import logging", "import logging" + N + "from core import projects"),
]

CONTROL = ("core/baseline.py", "logger = logging.getLogger(__name__)",
           "logger = logging.getLogger(__name__)  # cambio inocuo del CONTROL")


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
        print(N + "*** NO SE PUDO RESTAURAR %s — SE ABORTA" % rel)
        sys.exit(2)


print("verde de base:")
rc, fallos, rev = correr()
if rc != 0 or rev:
    print("  *** el guardián NO está verde con el código bueno: no se prueba nada")
    print(N.join(fallos))
    sys.exit(2)
print("  ok" + N)

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
        print("  CAZADA  %-50s -> %s" % (nombre[:50], fallos[0][12:86]))
    else:
        print("  ESCAPA  %s" % nombre)

rel, viejo, nuevo = CONTROL
escribir(rel, ORIG[rel].replace(viejo, nuevo, 1))
rc, fallos, rev = correr()
restaurar(rel)
print(N + "  CONTROL: %s" % ("pasa (correcto)" if rc == 0 and not rev else "*** FALLA"))
for rel in FICHEROS:
    restaurar(rel)
print(N + "%d de %d roturas cazadas · árbol restaurado y verificado" % (cazadas, len(ROTURAS)))
