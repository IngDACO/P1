# -*- coding: utf-8 -*-
"""Batería de v499: 12 roturas + CONTROL.

⚠️ Se lee QUÉ comprobación falla en cada una (v492): un guardián que REVIENTA también
devuelve código ≠ 0, así que un «12/12 cazadas» sin el motivo a la vista no vale nada
(v459/v463). Y ⚠️ NO se lanza en paralelo con la suite: modifica el árbol (v455).
"""
import io
import os
import shutil
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v499.py")
COPIAS = os.path.join(AQUI, "_respaldo_v499")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/plan.py", "core/projects.py", "core/schedule.py", "core/projects_ui.py"]

# (nombre, fichero, viejo, nuevo)
ROTURAS = [
    ("parse ignora el desfase", "core/plan.py",
     "out.append((int(float(resto)), signo * int(float(desfase or 0))))",
     "out.append((int(float(resto)), 0))"),
    ("vacío deja de ser «detrás de la anterior»", "core/plan.py",
     'return [(int(acts[i - 1]["orden"]), 0)] if i > 0 else []',
     "return []"),
    ("no se detecta el ciclo", "core/plan.py",
     "if i in {j for j, _l in preds.get(i, [])} or _hay_ciclo(preds, i):",
     "if False:"),
    ("remapear conserva la referencia que ya no existe", "core/plan.py",
     "nuevos = [(mapa[o], lag) for o, lag in parse(crudo) if o in mapa]",
     "nuevos = [(mapa.get(o, o), lag) for o, lag in parse(crudo)]"),
    ("el mapa sale SOLO de los edits (el fallo real)", "core/projects.py",
     "    mapa = {}\n    for r in recs:",
     "    mapa = {}\n    for r in []:"),
    ("limpiar_predecesoras no hace nada", "core/projects.py",
     "        if batch:\n            aws.batch_update(batch, value_input_option=\"RAW\")\n            _invalidate()",
     "        if False:\n            aws.batch_update(batch, value_input_option=\"RAW\")\n            _invalidate()"),
    ("la columna nueva se cuela en MEDIO de la cabecera", "core/projects.py",
     '"ActualStartDate", "ActualEndDate", "Note",',
     '"ActualStartDate", "Predecessors", "ActualEndDate", "Note",'),
    ("create_project no escribe la columna nueva", "core/projects.py",
     '"0", "", "", "", str(a.get("pred", a.get("Predecessors", ""))),',
     '"0", "", "", "",'),
    ("el Gantt deja de marcar las críticas", "core/schedule.py",
     '_cri = bool(a.get("critica"))', "_cri = False"),
    ("build_schedule no pasa las predecesoras", "core/schedule.py",
     '"pred": r.get("pred", "")} for i, r in enumerate(custom_rows)]',
     '"pred": ""} for i, r in enumerate(custom_rows)]'),
    ("la tabla vuelve a leer «Weight» (KeyError de v471)", "core/projects_ui.py",
     '"Weight": float(r["Peso"]),', '"Weight": float(r["Weight"]),'),
    ("el avance del campo vuelve a leer «Note»", "core/projects_ui.py",
     '_av, _nt = r["Avance %"], r["Nota"]', '_av, _nt = r["Avance %"], r["Note"]'),
    # ⚠️ Los avisos no saldrían NUNCA y nada lo diría: el fallo no da error, solo silencio.
    ("la pantalla pide los avisos sobre la raíz, no sobre «sched»", "core/projects_ui.py",
     '(P.project_schedule(pid) or {}).get("sched", {}).get("avisos_plan")',
     '(P.project_schedule(pid) or {}).get("avisos_plan")'),
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
    p = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    fallos = [l.strip() for l in (p.stdout or "").splitlines() if "*** FALLO" in l]
    reventado = "Traceback" in (p.stderr or "")
    return p.returncode, fallos, reventado


# ── respaldo EN DISCO antes de tocar nada (v484) ──
os.makedirs(COPIAS, exist_ok=True)
for rel in FICHEROS:
    shutil.copy2(os.path.join(RAIZ, rel), os.path.join(COPIAS, rel.replace("/", "_")))
ORIG = {rel: leer(rel) for rel in FICHEROS}


def restaurar(rel):
    escribir(rel, ORIG[rel])
    if leer(rel) != ORIG[rel]:                    # ⚠️ se VERIFICA leyendo
        shutil.copy2(os.path.join(COPIAS, rel.replace("/", "_")),
                     os.path.join(RAIZ, rel))
    if leer(rel) != ORIG[rel]:
        print("\n*** NO SE PUDO RESTAURAR %s — SE ABORTA" % rel)
        sys.exit(2)


print("verde de base (el paso que v459 se saltó):")
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
        print("  *** ANCLA no única (%d) en %s: %s" % (src.count(viejo), rel, nombre))
        continue
    escribir(rel, src.replace(viejo, nuevo))
    rc, fallos, rev = correr()
    restaurar(rel)
    if rev:
        print("  ?? REVIENTA  %s  (no cuenta: un guardián roto «caza» todo)" % nombre)
    elif rc != 0 and fallos:
        cazadas += 1
        print("  CAZADA  %-52s -> %s" % (nombre[:52], fallos[0][12:90]))
    else:
        print("  ESCAPA  %s" % nombre)

rel, viejo, nuevo = CONTROL
escribir(rel, ORIG[rel].replace(viejo, nuevo, 1))
rc, fallos, rev = correr()
restaurar(rel)
print("\n  CONTROL (cambio inocuo): %s" % ("pasa (correcto)" if rc == 0 and not rev
                                           else "*** FALLA"))

for rel in FICHEROS:
    restaurar(rel)
print("\n%d de %d roturas cazadas · árbol restaurado y verificado" % (cazadas, len(ROTURAS)))
