# -*- coding: utf-8 -*-
"""Batería de v512: 12 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v512.py")
COPIAS = os.path.join(AQUI, "_respaldo_v512")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/stages.py", "core/schedule.py", "core/projects.py",
            "core/quotes.py", "core/projects_ui.py"]

N = chr(10)
ROTURAS = [
    # ── ⚠️ el fallo que traia el documento ──
    ('⚠️ la Stage 2 vuelve a sumar 106 (avance inflado)', "core/stages.py",
     '        ("Fire services access & assist", 5.7, False),',
     '        ("Fire services access & assist", 11.7, False),'),
    ('⚠️ Prepping vuelve a pesar 4 (las etapas suman 101)', "core/stages.py",
     '    (PISTA_INSTALL, 2, "Prepping", 3),',
     '    (PISTA_INSTALL, 2, "Prepping", 4),'),
    ('otra etapa descuadrada (Commissioning)', "core/stages.py",
     '        ("Load test", 6, False),', '        ("Load test", 16, False),'),
    ('una actividad con peso CERO', "core/stages.py",
     '        ("Install oilers", 7, False),', '        ("Install oilers", 0, False),'),

    # ── ⚠️ el 85% eterno ──
    ('⚠️ traccion deja de ser condicional (el R3 no llegaria a 100)',
     "core/stages.py",
     '        ("Rip out mechanical components - traction", 25, True),',
     '        ("Rip out mechanical components - traction", 25, False),'),

    # ── la renormalizacion ──
    ('⚠️ el plan deja de renormalizar (una obra suma 97,48)', "core/stages.py",
     '    k = {pista: (cuota[pista] / total[pista] if total.get(pista, 0) > 0 else 0.0)'
     + N + '         for pista in _pistas}',
     '    k = {pista: 1.0 for pista in _pistas}'),
    ('⚠️ se renormaliza sobre el TOTAL: el reparto declarado se mueve solo',
     "core/stages.py",
     '    cuota = {pista: (100.0 if len(_pistas) < 2' + N
     + '                     else (p if pista == PISTA_RIPOUT else 100.0 - p))' + N
     + '             for pista in _pistas}',
     '    cuota = {pista: 100.0 * total[pista] / sum(total.values())' + N
     + '             for pista in _pistas}'),
    ('el pct no se recorta (un 500% pasa tal cual)', "core/stages.py",
     '    p = PCT_RIPOUT_DEFECTO if pct_ripout is None else float(pct_ripout)' + N
     + '    p = max(0.0, min(100.0, p))' + N + N + '    bruto, total = [], {}',
     '    p = PCT_RIPOUT_DEFECTO if pct_ripout is None else float(pct_ripout)' + N + N
     + '    bruto, total = [], {}'),

    # ── los nombres ──
    ('⚠️ los dos altavoces vuelven a llamarse igual', "core/stages.py",
     '        ("Speaker (under cabin)", 5, False),',
     '        ("Speaker (top of cabin)", 5, False),'),

    # ── el validador ──
    ('⚠️ el validador se queda ciego (tolerancia enorme)', "core/stages.py",
     'TOLERANCIA = 0.05', 'TOLERANCIA = 40.0'),
    ('una etapa fantasma sin actividades', "core/stages.py",
     '    (PISTA_INSTALL, 14, "Commissioning & Tuning", 9),',
     '    (PISTA_INSTALL, 14, "Commissioning & Tuning", 9),' + N
     + '    (PISTA_INSTALL, 15, "Fantasma", 0),'),

    # ── el modulo hoja ──
    ('core/stages.py deja de ser modulo HOJA', "core/stages.py",
     'VERSION = "2026-09-22"',
     'from core import num  # rotura' + N + 'VERSION = "2026-09-22"'),

    # ── el puente al cronograma ──
    ('⚠️ se deja de repartir el resto (la entrega se mueve)', "core/schedule.py",
     '        if resto > 0:', '        if False:'),
    ('⚠️ una etapa puede durar CERO dias (la red la trata como instantanea)',
     "core/schedule.py",
     '        dias = [max(1, int(x)) for x in exactos]',
     '        dias = [int(x) for x in exactos]'),
    ('las predecesoras dejan de nacer vacias', "core/schedule.py",
     '                "pred": "",      # vacío = detrás de la anterior (v499): no mueve nada',
     '                "pred": "1",'),
    ('⚠️ los dias se reparten sobre el TOTAL, no por pista', "core/schedule.py",
     '        exactos = [objetivo * float(plan_obra[i]["peso"]) / por_pista[pista] for i in idx]',
     '        exactos = [objetivo * float(plan_obra[i]["peso"]) / 100.0 for i in idx]'),

    # ── el alta ──
    ('⚠️ la columna nueva se queda SIN su valor en la fila (v363)', "core/projects.py",
     '        str(stage_plan or ""),              # v512: el plan de etapas con el que nace.',
     '        # (valor quitado)'),
    ('«Ripout» vuelve a quedarse sin cronograma (0% eterno)', "core/projects.py",
     '    return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST, TIPO_RIPOUT)',
     '    return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST)'),
    ('⚠️ un plan ilegible revienta en vez de degradar', "core/projects.py",
     '        d = json.loads(crudo)' + N + '        return d if isinstance(d, dict) else {}',
     '        d = json.loads(crudo)' + N + '        return d'),
    ('⚠️ aceptar una cotizacion vuelve al cronograma VIEJO', "core/quotes.py",
     '        _filas = S.filas_de_etapas(tipo, int(_num(ns)), condicionales)' + N
     + '        sch = S.build_schedule(int(_num(ns)), ini, {}, custom_rows=_filas)',
     '        sch = S.build_schedule(int(_num(ns)), ini, {}, ripout=P.con_ripout(tipo))'),
    ('el alta a mano deja de preguntar lo que falta decidir', "core/projects_ui.py",
     '        _pendientes = _pregunta_etapas(_tipo, key)',
     '        _pendientes = []'),
]

# ⚠️ El CONTROL comprueba lo contrario: que un cambio inocuo NO ponga rojo al guardián.
# Sin él, una batería donde «todo se caza» podría ser un guardián que falla con
# cualquier cosa que se toque (v459).
CONTROL = ("core/stages.py", "def condicionales(pista=None) -> list:",
           "def condicionales(pista=None) -> list:  # cambio inocuo del CONTROL")


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
        # ⚠️ Un guardián que REVIENTA no denuncia: no cuenta como cazada.
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
