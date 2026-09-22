# -*- coding: utf-8 -*-
"""Batería de v514: 14 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v514.py")
COPIAS = os.path.join(AQUI, "_respaldo_v514")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/stage_progress.py", "core/stage_progress_ui.py", "core/hojas.py",
            "core/projects_ui.py", "core/projects.py"]

N = chr(10)
ROTURAS = [
    # ── ⚠️ el fallo que ya mordió DOS veces (v461, v507) ──
    ('⚠️ la hoja se cae del lote (leeria vacio para siempre, sin error)',
     "core/hojas.py", '    "StageProgress",' + N + ')', ')'),

    # ── la aritmetica ──
    ('⚠️ el % cuenta ACTIVIDADES en vez de ponderar por peso',
     "core/stage_progress.py",
     '    tot = sum(_num(a.get("peso_en_etapa")) for a in (actividades or []))',
     '    tot = float(len(actividades or []) * 100)'),
    ('divide por cero con los pesos a 0', "core/stage_progress.py",
     '    if tot <= 0:' + N + '        return 0.0', '    if False:' + N + '        pass'),
    ('el % no se pondera: todas valen igual', "core/stage_progress.py",
     '    acc = sum(_num(a.get("peso_en_etapa")) * _num(a.get("pct")) for a in actividades)',
     '    acc = sum(_num(a.get("pct")) for a in actividades)'),

    # ── ⚠️ el numero que lee todo lo demas ──
    ('⚠️ el avance de la etapa NO llega a Activities', "core/stage_progress.py",
     '    ok, msg = P.save_field_progress(pid, _cambios)',
     '    ok, msg = True, ""'),
    ('⚠️ un fallo al escribir el avance se da por bueno', "core/stage_progress.py",
     '    if not ok:' + N
     + '        # ⚠️ Se dice, no se traga: el crédito quedó guardado pero la etapa no se movió,',
     '    if False:' + N
     + '        # ⚠️ Se dice, no se traga: el crédito quedó guardado pero la etapa no se movió,'),
    ('se recalculan TODAS las etapas, no solo las tocadas',
     "core/stage_progress.py",
     '    _cambios = [{"orden": o, "avance": _det[o]["pct"]} for o in sorted(_tocadas)' + N
     + '                if o in _det]',
     '    _cambios = [{"orden": o, "avance": _det[o]["pct"]} for o in sorted(_det)]'),
    ('⚠️ el recalculo vuelve a depender de releer la hoja', "core/stage_progress.py",
     '        _despues[(_et, _ac)] = _pc', '        pass'),

    # ── lo que no se puede acreditar ──
    ('⚠️ se acredita algo que NO esta en el plan de la obra',
     "core/stage_progress.py",
     '    if _malos:', '    if False:'),
    ('⚠️ se acredita contra un catalogo DISTINTO del que sello la obra',
     "core/stage_progress.py", '    if _vieja:', '    if False:'),
    ('una obra sin plan se acredita igual', "core/stage_progress.py",
     '    if not _plan:', '    if False and not _plan:'),
    ('el pct no se recorta (un 500% entra tal cual)', "core/stage_progress.py",
     '        _pc = max(0.0, min(100.0, _num(c.get("pct"))))',
     '        _pc = _num(c.get("pct"))'),

    # ── la pantalla ──
    ('la version desfasada deja de bloquear la pantalla',
     "core/stage_progress_ui.py", '        editable = False', '        pass'),
    ('⚠️ el campo deja de caer a la rejilla vieja en obras sin plan',
     "core/projects_ui.py",
     '        if not _SPU.render(pid, grupo, prj, key_prefix="fld"):' + N
     + '            _field_activities(pid)',
     '        _SPU.render(pid, grupo, prj, key_prefix="fld")'),
    ('⚠️ borrar una obra deja sus creditos huerfanos', "core/projects.py",
     '        from core import stage_progress as _SP',
     '        from core import num as _SP  # rotura'),
]

# ⚠️ El CONTROL comprueba lo contrario: que un cambio inocuo NO ponga rojo al guardián.
# Sin él, una batería donde «todo se caza» podría ser un guardián que falla con
# cualquier cosa que se toque (v459).
# ⚠️ Y tiene que ser un cambio DE VERDAD: la primera versión ponía el mismo texto a los
# dos lados, o sea que no cambiaba nada y el control pasaba sin probar nada — un control
# vacío es peor que no tenerlo, porque parece cobertura.
CONTROL = ("core/stage_progress.py",
           "def borrar(pid, etapa, actividad, grupo, prj, quien=\"\") -> tuple:",
           "def borrar(pid, etapa, actividad, grupo, prj, quien=\"\") -> tuple:  # CONTROL")


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
if ORIG[rel].count(viejo) != 1:
    print(N + "  *** el ancla del CONTROL no es unica: el control no prueba nada")
    _ctrl_ok = False
else:
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
