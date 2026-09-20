# -*- coding: utf-8 -*-
"""Batería de v506: 12 roturas + CONTROL.

⚠️ Verde de base ANTES (v459), motivo de cada rotura a la vista (v492), respaldo en
disco + restauración VERIFICADA + abortar (v484). NO en paralelo con la suite (v455).
"""
import io
import os
import shutil
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v506.py")
COPIAS = os.path.join(AQUI, "_respaldo_v506")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/handover.py", "core/handover_ui.py", "core/projects.py"]

N = chr(10)
ROTURAS = [
    # ── lo que la app NO puede afirmar ──
    ('⚠️ un item de TERCERO pasa por calculo (afirma lo que no sabe)',
     "core/handover.py",
     '            _e = (OK, "Uploaded: %s" % _doc) if _doc else (FALTA, "Not uploaded yet")',
     '            _e = (OK, "Uploaded: %s" % _doc) if _doc else (OK, "Assumed present")'),

    # ── la hoja ──
    ('«HandoverItem» deja de ser la ULTIMA columna', "core/projects.py",
     '                     "HandoverItem"]', '                     "HandoverItem", "Zzz"]'),
    ('falta el valor en la fila posicional de add_document', "core/projects.py",
     '                    str(handover_item or "")],     # v506: qué acredita en la entrega',
     '                    ],'),

    # ── los estados, y los falsos rojos ──
    ('⚠️ un certificado SIN vencimiento se cuenta como vencido (falso rojo)',
     "core/handover.py",
     'if _d and all((_v is not None and _f(_v) and _f(_v) < _d) for _v in mios):',
     'if _d and all((_v is None or not _f(_v) or _f(_v) < _d) for _v in mios):'),
    ('commissioning dice OK con actividades abiertas', "core/handover.py",
     '    if len(cerradas) == len(acts):', '    if True:'),
    ('as_built dice OK sin verificacion de plomada', "core/handover.py",
     '    if ctx.get("plumb_ok"):' + N + '        return OK, "Matrix and plumb verification present"',
     '    if True:' + N + '        return OK, "Matrix and plumb verification present"'),
    ('check_sheets no distingue PARCIAL de FALTA', "core/handover.py",
     '        return PARCIAL, "Parameters recorded, no solution matrix"',
     '        return FALTA, "Parameters recorded, no solution matrix"'),

    # ── los cruces ──
    ('⚠️ el cruce del ticket vencido deja de cazar', "core/handover.py",
     '            if _d and _v and max(_v) < _d:', '            if False:'),
    ('⚠️ se cae la guarda del INVITADO (falso rojo a todo el mundo)', "core/handover.py",
     '            if not str(u).strip():' + N + '                continue',
     '            if False:' + N + '                continue'),
    ('el cruce de la obra cerrada sin plomada deja de cazar', "core/handover.py",
     '    if acts and all(_f(a.get("ActualEndDate")) for a in acts) and not ctx.get("plumb_ok"):',
     '    if False:'),

    # ── modulo hoja ──
    ('handover deja de ser modulo HOJA (ciclo posible)', "core/handover.py",
     'from datetime import date', 'from datetime import date' + N + 'from core import projects'),

    # ── ⚠️ el riesgo de PRODUCTO: prometer cumplimiento ──
    ('⚠️ la pantalla promete un certificado de cumplimiento', "core/handover_ui.py",
     'st.caption(t("What this company has to keep for five years',
     'st.caption(t("This certifies compliance. What this company has to keep for five years'),
]

CONTROL = ("core/handover.py", "def resumen(filas) -> dict:",
           "def resumen(filas) -> dict:  # cambio inocuo del CONTROL")


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

cazadas, escapadas = 0, []
for nombre, rel, viejo, nuevo in ROTURAS:
    src = ORIG[rel]
    if src.count(viejo) != 1:
        print("  *** ANCLA no única (%d): %s" % (src.count(viejo), nombre))
        escapadas.append(nombre)
        continue
    escribir(rel, src.replace(viejo, nuevo))
    rc, fallos, rev = correr()
    restaurar(rel)
    if rev:
        print("  ?? REVIENTA  %s  (no cuenta)" % nombre)
        escapadas.append(nombre)
    elif rc != 0 and fallos:
        cazadas += 1
        print("  CAZADA  %-54s -> %s" % (nombre[:54], fallos[0][12:80]))
    else:
        print("  ESCAPA  %s" % nombre)
        escapadas.append(nombre)

rel, viejo, nuevo = CONTROL
escribir(rel, ORIG[rel].replace(viejo, nuevo, 1))
rc, fallos, rev = correr()
restaurar(rel)
print(N + "  CONTROL (cambio inocuo): %s"
      % ("pasa, correcto" if rc == 0 and not rev else "*** FALLA"))

for rel in FICHEROS:
    restaurar(rel)
print(N + "%d de %d roturas cazadas · árbol restaurado y verificado"
      % (cazadas, len(ROTURAS)))
if escapadas:
    print("ESCAPARON:" + N + N.join("  - " + e for e in escapadas))
sys.exit(0 if cazadas == len(ROTURAS) else 1)
