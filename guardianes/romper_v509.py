# -*- coding: utf-8 -*-
"""Batería de v509: 12 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v509.py")
COPIAS = os.path.join(AQUI, "_respaldo_v509")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/quote_from_plan.py", "core/catalogo.py", "core/quotes_ui.py"]

N = chr(10)
ROTURAS = [
    # ── ⚠️ el fallo caro: sub-cotizar en silencio ──
    ('⚠️ la linea sin dato se OMITE (abarata sin que nadie lo note)',
     "core/quote_from_plan.py",
     '        l["_falta"] = falta' + N + '        lineas.append(l)',
     '        l["_falta"] = falta' + N + '        if not falta:' + N + '            lineas.append(l)'),
    ('⚠️ sin dato se INVENTA un 1', "core/quote_from_plan.py",
     '        if n <= 0:' + N + '            return 0, _SIN_NS',
     '        if n <= 0:' + N + '            return 1, ""'),
    ('⚠️ la cantidad es 0 pero SIN motivo (un silencio)', "core/quote_from_plan.py",
     '            return 0, _SIN_NS', '            return 0, ""'),

    # ── las reglas ──
    ('«por parada menos 1» devuelve NS', "core/quote_from_plan.py",
     'return (n if r == POR_PARADA else max(0, n - 1)), ""',
     'return n, ""'),
    ('la regla FIJA deja de dar 1', "core/quote_from_plan.py",
     '    if r == FIJA:' + N + '        return 1, ""',
     '    if r == FIJA:' + N + '        return 0, ""'),
    ('⚠️ un item MANUAL se propone igual', "core/quote_from_plan.py",
     '        if regla == MANUAL or regla not in REGLAS:',
     '        if False:'),
    ('el defecto pasa a ser «por parada» (se adivina)', "core/quote_from_plan.py",
     'REGLA_DEFECTO = MANUAL', 'REGLA_DEFECTO = POR_PARADA'),

    # ── la basura ──
    ('una cantidad negativa del plano se acepta', "core/quote_from_plan.py",
     '        if n <= 0:', '        if n < -99:'),

    # ── lo que se guarda ──
    ('⚠️ las marcas internas viajan a la cotizacion guardada',
     "core/quote_from_plan.py",
     'return [{k: v for k, v in (l or {}).items() if not str(k).startswith("_")}',
     'return [{k: v for k, v in (l or {}).items()}'),

    # ── la hoja ──
    ('«QtyRule» deja de ser la ULTIMA columna', "core/catalogo.py",
     '           "QtyRule"]', '           "QtyRule", "Zzz"]'),
    ('falta el valor en la fila posicional del catalogo', "core/catalogo.py",
     '                      str(qty_rule or "")],    # v509: de dónde sale su cantidad',
     '                      ],'),

    # ── la pantalla ──
    ('⚠️ la pantalla REEMPLAZA lo ya escrito en vez de añadir',
     "core/quotes_ui.py",
     '_st["new_lineas"] = list(_st.get("new_lineas") or []) + _QP.limpiar(_r["lineas"])',
     '_st["new_lineas"] = _QP.limpiar(_r["lineas"])'),
]

CONTROL = ("core/quote_from_plan.py", "def limpiar(lineas) -> list:",
           "def limpiar(lineas) -> list:  # cambio inocuo del CONTROL")


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
        print("  CAZADA  %-52s -> %s" % (nombre[:52], fallos[0][12:78]))
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
