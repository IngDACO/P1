# -*- coding: utf-8 -*-
"""Batería de v507: 12 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v507.py")
COPIAS = os.path.join(AQUI, "_respaldo_v507")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/claims.py"]

N = chr(10)
ROTURAS = [
    # ── qué es dinero y qué no ──
    ('⚠️ una variacion PROPUESTA cuenta como valor de contrato', "core/claims.py",
     'return round(sum(_num(v.get("Amount")) for v in variaciones(pid, APROBADA)), 2)',
     'return round(sum(_num(v.get("Amount")) for v in variaciones(pid)), 2)'),

    # ── el avance que retrocede ──
    ('⚠️ el bruto puede ser NEGATIVO (devolucion en silencio)', "core/claims.py",
     '_bruto = round(max(0.0, _hecho - _antes), 2)',
     '_bruto = round(_hecho - _antes, 2)'),

    # ── lo acumulado ──
    ('⚠️ lo acumulado se suma de los NETOS y la obra no llega al 100%', "core/claims.py",
     '_antes = round(max([_num(r.get("WorkDone")) for r in reclamaciones(pid)], default=0.0), 2)',
     '_antes = round(sum(_num(r.get("ThisClaim")) - _num(r.get("Retention"))'
     ' for r in reclamaciones(pid)), 2)'),

    # ── la base de comparacion ──
    ('⚠️ el contrato lee el Total (con impuesto) en vez del Subtotal', "core/claims.py",
     'return (round(_num(c.get("Subtotal")), 2), str(c.get("ID", ""))) if c else (0.0, "")',
     'return (round(_num(c.get("Total")), 2), str(c.get("ID", ""))) if c else (0.0, "")'),

    # ── la obra sin contrato ──
    ('sin cotizacion aceptada se deja emitir igual', "core/claims.py",
     '    if not d["hay_contrato"]:', '    if False:'),

    # ── las decisiones ──
    ('⚠️ una variacion ya decidida se puede re-decidir', "core/claims.py",
     '    if str(r.get("Status", "")) != PROPUESTA:', '    if False:'),
    ('⚠️ se puede anular cualquier reclamacion, no solo la ultima', "core/claims.py",
     '    if _num(r.get("Number")) != _ultima:', '    if False:'),

    # ── los limites ──
    ('el porcentaje no se recorta a 100', "core/claims.py",
     'pct = max(0.0, min(100.0, _num(pct)))', 'pct = _num(pct)'),

    # ── las filas posicionales (v363) ──
    ('falta un valor en la fila de crear_variacion', "core/claims.py",
     'str(_num(importe)), PROPUESTA, "", "", str(nota), str(creado_por),',
     'str(_num(importe)), PROPUESTA, "", str(nota), str(creado_por),'),
    ('falta un valor en la fila de crear_reclamacion', "core/claims.py",
     'str(d["retencion"]), str(d["bruto"]), EMITIDA, str(nota),',
     'str(d["bruto"]), EMITIDA, str(nota),'),

    # ── la anulada ──
    ('⚠️ una reclamacion ANULADA vuelve a contar como reclamada', "core/claims.py",
     '        out = [r for r in out if str(r.get("Status", "")) != ANULADA]',
     '        out = [r for r in out if True]'),

    # ── la retencion ──
    ('⚠️ la retencion se descuenta del TRABAJO HECHO, no del pago', "core/claims.py",
     '_hecho = round(_valor * pct / 100.0, 2)',
     '_hecho = round(_valor * pct / 100.0 * 0.95, 2)'),
]

CONTROL = ("core/claims.py", "def retencion_pct(grupo) -> float:",
           "def retencion_pct(grupo) -> float:  # cambio inocuo del CONTROL")


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
        print("  CAZADA  %-54s -> %s" % (nombre[:54], fallos[0][12:78]))
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
