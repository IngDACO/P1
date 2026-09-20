# -*- coding: utf-8 -*-
"""Batería de v502: 13 roturas + CONTROL.

⚠️ Se confirma el verde de base ANTES (v459) y se lee QUÉ comprobación falla en cada
rotura (v492). Respaldo en disco + restauración VERIFICADA + abortar si no se puede
devolver el árbol (v484). NO se lanza en paralelo con la suite: modifica el árbol (v455).
"""
import io
import os
import shutil
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v502.py")
COPIAS = os.path.join(AQUI, "_respaldo_v502")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FICHEROS = ["core/projects.py", "core/projects_ui.py", "core/tabla.py", "core/auth.py"]

N = chr(10)
ROTURAS = [
    # ── la hoja: la columna nueva y la fila posicional (v363) ──
    ('«Owner» deja de ser la ULTIMA columna', "core/projects.py",
     '    "Owner",' + N + ']',
     '    "Owner",' + N + '    "Zzz",' + N + ']'),
    ('falta el valor en la fila posicional de create_project', "core/projects.py",
     'str(a.get("owner", a.get("Owner", ""))),',
     '# v502 sin valor en la fila:'),

    # ── el guardado: lo que no viaja, no se toca ──
    ('⚠️ el responsable se escribe SIEMPRE (un guardado parcial lo BORRA)',
     "core/projects.py",
     'if field in e and field in _ACOL:' + N +
     '                batch.append({"range": f"{_col_letter(_ACOL[field])}{row}",' + N +
     '                              "values": [[str(e[field])]]})',
     'if field in _ACOL:' + N +
     '                batch.append({"range": f"{_col_letter(_ACOL[field])}{row}",' + N +
     '                              "values": [[str(e.get(field, ""))]]})'),
    ('«Owner» se cae del bucle de guardado (no se guarda nunca)', "core/projects.py",
     '("Name", "DurationDays", "Weight", "Order", "Owner")',
     '("Name", "DurationDays", "Weight", "Order")'),

    # ── el viaje hasta la pantalla ──
    ('project_schedule deja de llevar los responsables', "core/projects.py",
     '"avances": avances, "proj": proj, "owners": owners}',
     '"avances": avances, "proj": proj}'),
    ('la lista de responsables va DESORDENADA (miente en paralelo)', "core/projects.py",
     'owners = [str(a.get("Owner", "") or "").strip() for a in acts]',
     'owners = [str(a.get("Owner", "") or "").strip() for a in acts][::-1]'),
    ('_diagnostico deja de pasar el dueño a las paradas', "core/projects_ui.py",
     'tocaban.append({"nombre": a["nombre"], "avance": pct, "owner": _ow,',
     'tocaban.append({"nombre": a["nombre"], "avance": pct,'),
    ('la pantalla deja de pintar el dueño en la ARRASTRADA', "core/projects_ui.py",
     't(" _(carried over)_") + _dueno(x) if x["tarde"] else ""',
     't(" _(carried over)_") if x["tarde"] else ""'),

    # ── la identidad: login dentro, nombre fuera (v306/v413) ──
    ('la relectura guarda la ETIQUETA en vez del login', "core/projects_ui.py",
     '"Owner": _login_de.get(' + N +
     '                                      str(r["Responsable"] or "").strip(), "")})',
     '"Owner": str(r["Responsable"] or "").strip()})'),
    ('etiqueta_usuarios deja de desambiguar homonimos', "core/auth.py",
     'if _n.get(str(u.get("Name") or ""), 0) > 1 else _nom',
     'if False else _nom'),

    # ── el borrado silencioso que motivo el diseño ──
    ('⚠️ los dueños ya guardados se caen de las OPCIONES (los borraria)',
     "core/projects_ui.py",
     '+ [o for o in _due0 if o]', '+ []'),

    # ── el fallo REAL que se fue a produccion (trampa nº29) ──
    ('⚠️ se liga un nombre que YA es funcion del modulo (UnboundLocalError)',
     "core/projects_ui.py",
     '            _lbl_de = _etq_us(_op_us)',
     '            _etq_us = {}' + N + '            _lbl_de = _etq_us'),

    # ── el «None» que se pinta en cada celda vacia (visto en el canvas) ──
    ('⚠️ el «sin responsable» vuelve a ser "" (pinta None en cada fila)',
     "core/projects_ui.py",
     '            _op_lbl = [_SIN] + [_lbl_de[u] for u in _op_us]',
     '            _op_lbl = [""] + [_lbl_de[u] for u in _op_us]'),

    # ── pantalla y permisos ──
    ('la cabecera desaparece de tabla.CABECERAS (se pintaria en español)',
     "core/tabla.py", '    "Responsable": "Owner",' + N, ''),
    ('⚠️ el CAMPO empieza a editar responsables', "core/projects_ui.py",
     'ok, msg = P.save_field_progress(pid, cambios)',
     '_ = "Responsable"' + N + '            ok, msg = P.save_field_progress(pid, cambios)'),
]

CONTROL = ("core/projects.py",
           "def save_activities(pid, edits) -> tuple:",
           "def save_activities(pid, edits) -> tuple:  # cambio inocuo del CONTROL")


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
      % ("pasa, correcto" if rc == 0 and not rev else "*** FALLA — el guardián acusa a código sano"))

for rel in FICHEROS:
    restaurar(rel)
print(N + "%d de %d roturas cazadas · árbol restaurado y verificado"
      % (cazadas, len(ROTURAS)))
if escapadas:
    print("ESCAPARON:" + N + N.join("  - " + e for e in escapadas))
sys.exit(0 if cazadas == len(ROTURAS) else 1)
