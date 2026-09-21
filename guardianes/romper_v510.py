# -*- coding: utf-8 -*-
"""Batería de v510: 12 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v510.py")
COPIAS = os.path.join(AQUI, "_respaldo_v510")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/claims.py", "core/claim_pdf.py", "core/claims_ui.py",
            "core/catalogo.py", "core/timeclock.py"]

N = chr(10)
ROTURAS = [
    # ── ⚠️ las que cuestan dinero de verdad ──
    ('⚠️ se libera MAS de lo retenido (eso es una factura, no una liberacion)',
     "core/claims.py", '    if _imp > _pend:', '    if False:'),
    ('⚠️ se libera con la obra a medias', "core/claims.py",
     '    if _av < 100:', '    if _av < 0:'),
    ('⚠️ no poder leer el avance se trata como «esta terminada»', "core/claims.py",
     '        return False, t("The job progress could not be read, so the release is on hold.")',
     '        return True, ""'),
    ('⚠️ la liberacion RETIENE un 5% (se cobraria de menos)', "core/claims.py",
     '                      "0", "0",                   # una liberación no retiene nada',
     '                      "5", "100",'),
    ('⚠️ la liberacion mueve la base de trabajo ejecutado', "core/claims.py",
     '                      str(_num(_prev.get("VariationsValue"))),' + N
     + '                      str(_num(_prev.get("WorkDone"))),',
     '                      str(_num(_prev.get("VariationsValue"))),' + N
     + '                      "0",'),

    # ── la aritmetica de lo retenido ──
    ('las liberaciones cuentan como retencion (el pendiente no baja)',
     "core/claims.py",
     '    _ret = round(sum(_num(r.get("Retention")) for r in _rs if not es_liberacion(r)), 2)',
     '    _ret = round(sum(_num(r.get("Retention")) for r in _rs), 2)'),
    ('el pendiente puede salir NEGATIVO («te deben» al reves)', "core/claims.py",
     '            "pendiente": round(max(0.0, _ret - _lib), 2)}',
     '            "pendiente": round(_ret - _lib, 2)}'),
    ('una liberacion deja de reconocerse como tal', "core/claims.py",
     '    return str((r or {}).get("Type", "")) == LIBERACION',
     '    return False'),

    # ── la hoja (v363) ──
    ('«Type» deja de ser la ULTIMA columna', "core/claims.py",
     '             "Type"]', '             "Type", "Zzz"]'),
    ('falta el valor en la fila posicional de la reclamacion', "core/claims.py",
     '                      PROGRESO],                  # v510: clase de documento',
     '                      ],'),

    # ── el documento ──
    ('⚠️ el PDF detalla variaciones PROPUESTAS (no son dinero)', "core/claim_pdf.py",
     '                  if str(v.get("Status", "")) == "approved"]',
     '                  if True]'),
    ('la liberacion se titula igual que una reclamacion de avance',
     "core/claim_pdf.py",
     '    _titulo = d("RETENTION RELEASE") if _lib else d("PROGRESS CLAIM")',
     '    _titulo = d("PROGRESS CLAIM")'),

    # ── el mensaje que mentia sobre la causa (lo encontro la cadena, no un test) ──
    ('⚠️ un 429 vuelve a culpar a la configuracion', "core/catalogo.py",
     '        return False, timeclock.motivo_sin_hoja()   # v510: no mientas, puede ser un 429'
     + N + '    if not str(nombre).strip():',
     '        return False, t("Google Sheets is not configured.")'
     + N + '    if not str(nombre).strip():'),
    ('⚠️ los dos motivos dan el MISMO mensaje (el arreglo no hace nada)',
     "core/timeclock.py",
     '    return t("The sheet could not be opened right now — this is usually a temporary "'
     + N + '             "limit. Try again in a minute.")',
     '    return t("Google Sheets is not configured.")'),
]

# El CONTROL comprueba lo contrario: que un cambio que NO rompe nada deje el guardián
# en verde. Sin él, una batería en la que «todo se caza» podría ser un guardián que
# falla con cualquier cosa (v459).
CONTROL = ("core/claims.py", "def es_liberacion(r) -> bool:",
           "def es_liberacion(r) -> bool:  # cambio inocuo del CONTROL")


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
        # ⚠️ Un guardián que REVIENTA no denuncia: no cuenta como cazada. Fue el patrón
        # que se repitió cinco veces en v505-v509.
        print("  ?? REVIENTA  %s  (no cuenta)" % nombre)
        escapadas.append(nombre)
    elif rc != 0 and fallos:
        cazadas += 1
        print("  CAZADA  %-52s -> %s" % (nombre[:52], fallos[0][12:78]))
    else:
        print("  ESCAPA  %s" % nombre)
        escapadas.append(nombre)

rel, viejo, nuevo = CONTROL
escribir(rel, ORIG[rel].replace(viejo, nuevo, 1))
rc, fallos, rev = correr()
restaurar(rel)
_ctrl_ok = (rc == 0 and not rev)
print(N + "  CONTROL (cambio inocuo): %s" % ("sigue VERDE, bien" if _ctrl_ok
                                             else "se puso ROJO — el guardián acusa de más"))

print(N + "=" * 70)
print("%d/%d roturas cazadas · CONTROL %s"
      % (cazadas, len(ROTURAS), "ok" if _ctrl_ok else "MAL"))
for e in escapadas:
    print("  - ESCAPA: " + e)
sys.exit(0 if (cazadas == len(ROTURAS) and _ctrl_ok) else 1)
