# -*- coding: utf-8 -*-
"""Batería de v505: 12 roturas + CONTROL.

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
GUARD = os.path.join(AQUI, "verif_v505.py")
COPIAS = os.path.join(AQUI, "_respaldo_v505")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/orders.py", "core/projects_ui.py"]

N = chr(10)
ROTURAS = [
    # ── la hoja ──
    ('«ActivityOrder» deja de ser la ULTIMA columna', "core/orders.py",
     '           "ActivityOrder"]', '           "ActivityOrder", "Zzz"]'),
    ('falta el valor en la fila posicional de crear()', "core/orders.py",
     '                      str(actividad or "")],          # v505: actividad que la espera',
     '                      ],'),

    # ── que bloquea y que no ──
    ('bloquea tambien lo RECIBIDO y lo CANCELADO', "core/orders.py",
     '    for r in list_for(pid, PENDIENTE):' + N + '        _a = str(r.get("ActivityOrder", "") or "").strip()',
     '    for r in list_for(pid):' + N + '        _a = str(r.get("ActivityOrder", "") or "").strip()'),
    # ⚠️ Poner `if False` aqui NO sirve de rotura: el parseo estricto de abajo tambien
    # tira la cadena vacia, asi que quitar esta guarda no cambia nada observable (son
    # dos redes sobre lo mismo). La rotura de verdad es la que INVENTA a quien bloquea:
    # una orden sin actividad reclamando la 1.
    ('⚠️ una orden SIN actividad se cuelga de la actividad 1', "core/orders.py",
     '        if not _a:' + N + '            continue',
     '        if not _a:' + N + '            _a = "1"'),
    ('⚠️ vuelve `_num`: la basura se liga a una actividad FANTASMA 0', "core/orders.py",
     '            k = int(float(_a.replace(",", ".")))' + N +
     '        except (TypeError, ValueError):' + N + '            continue' + N +
     '        if k <= 0:' + N + '            continue',
     '            k = int(_num(_a))' + N +
     '        except (TypeError, ValueError):' + N + '            continue' + N +
     '        if False:' + N + '            continue'),
    ('⚠️ sin fecha esperada se declara ATRASADA (no se puede afirmar)', "core/orders.py",
     '"tarde": bool(f and f < hoy),', '"tarde": bool(not f or f < hoy),'),

    # ── el viaje hasta la pantalla ──
    ('_diagnostico deja de llevar el nº de Orden a las paradas', "core/projects_ui.py",
     '            tocaban.append({"nombre": a["nombre"], "avance": pct, "owner": _ow,' + N +
     '                            "orden": _or, "desde": f_i, "dur": a["duracion"]})',
     '            tocaban.append({"nombre": a["nombre"], "avance": pct, "owner": _ow,' + N +
     '                            "desde": f_i, "dur": a["duracion"]})'),
    ('la causa deja de pintarse en la ARRASTRADA', "core/projects_ui.py",
     't(" _(carried over)_") + _dueno(x) + _espera(x)',
     't(" _(carried over)_") + _dueno(x)'),
    ('las ordenes dejan de ser OPCIONALES (tumban la pantalla de estado)',
     "core/projects_ui.py",
     '    try:' + N + '        from core import orders as _Ord' + N +
     '        if not _Ord.is_configured():' + N + '            return {}' + N +
     '        return _Ord.bloqueos(pid, grupo)' + N + '    except Exception:' + N +
     '        return {}',
     '    from core import orders as _Ord' + N + '    return _Ord.bloqueos(pid, grupo)'),

    # ── el campo ──
    ('⚠️ el campo deja de ver que espera material', "core/projects_ui.py",
     '    _blq = _bloqueos_de(pid, st.session_state.get("auth", {}).get("grupo", ""))',
     '    _blq = {}'),

    # ── el vacio con nombre (leccion de v504) ──
    ('la opcion «sin actividad» vuelve a ser "" (pinta None)', "core/projects_ui.py",
     '_op_act = [_SIN_ACT] + ["%d · %s"', '_op_act = [""] + ["%d · %s"'),
    ('se guarda la ETIQUETA en vez del nº de Orden', "core/projects_ui.py",
     'actividad=("" if _act == _SIN_ACT else _act.split(" · ", 1)[0]),',
     'actividad=("" if _act == _SIN_ACT else _act),'),
]

CONTROL = ("core/orders.py", "def bloqueos(pid, grupo=None) -> dict:",
           "def bloqueos(pid, grupo=None) -> dict:  # cambio inocuo del CONTROL")


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
        print("  CAZADA  %-52s -> %s" % (nombre[:52], fallos[0][12:84]))
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
