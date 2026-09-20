# -*- coding: utf-8 -*-
"""Batería v498: cada rotura debe poner rojo verif_v498; el CONTROL debe pasar."""
import io
import os
import shutil
import subprocess
import sys
import time

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v498.py")
ULTIMO = []

ROTURAS = [
    # el fallo REAL que reportó el usuario, reconstruido
    ("vuelve a pasar la función `t` como tipo", "core/auth_ui.py",
     "                ok, msg = C.add(usuario, grupo, _tp, num, clase, emi, ven, did, fname,",
     "                ok, msg = C.add(usuario, grupo, t, num, clase, emi, ven, did, fname,"),
    ("manda «Other» en vez de lo que se escribió", "core/auth_ui.py",
     '                _tp = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo',
     '                _tp = tipo'),
    ("el backend acepta cualquier cosa como tipo", "core/credentials.py",
     "    if not isinstance(tipo, str) or not tipo.strip():",
     "    if not str(tipo).strip():"),
    ("el aviso vuelve a escribir «falta» a mano", "core/projects_ui.py",
     '''                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{_c} ({_etq(comp['por_tipo'][_c])})" for _c in faltan))''',
     '''                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{_c} (falta)" for _c in faltan))'''),
]
CONTROL = ("CONTROL: comentario inocuo", "core/credentials.py",
           "def add(usuario, grupo, tipo, numero=\"\", clase=\"\", emision=\"\", vencimiento=\"\",",
           "# comentario inocuo\ndef add(usuario, grupo, tipo, numero=\"\", clase=\"\", emision=\"\", vencimiento=\"\",")


def correr():
    global ULTIMO
    r = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ULTIMO = [l.strip()[:120] for l in (r.stdout or "").splitlines() if "FALLO" in l][:2] \
        or [l.strip()[:120] for l in (r.stderr or "").splitlines() if "Error" in l][-1:]
    return r.returncode


def probar(nombre, fich, old, new):
    p = os.path.join(RAIZ, fich)
    copia = os.path.join(AQUI, "_r498_" + os.path.basename(fich))
    shutil.copyfile(p, copia)
    with io.open(p, encoding="utf-8") as fh:
        s = fh.read()
    if s.count(old) != 1:
        return "ANCLA MAL (%d)" % s.count(old)
    try:
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(s.replace(old, new))
        rc = correr()
    finally:
        for _ in range(5):
            try:
                shutil.copyfile(copia, p)
                with io.open(p, encoding="utf-8") as fh:
                    if fh.read() == s:
                        break
            except OSError:
                time.sleep(1)
        else:
            print("!!! NO SE PUDO RESTAURAR", fich)
            sys.exit(3)
    return rc


if correr() != 0:
    print("!!! el guardián NO está verde de base: la batería no probaría nada")
    sys.exit(2)
print("verde de base: ok")
escapes = 0
for r in ROTURAS:
    rc = probar(*r)
    cazada = isinstance(rc, int) and rc != 0
    if not cazada:
        escapes += 1
    print(f"  {'CAZADA' if cazada else 'ESCAPÓ/' + str(rc):10} {r[0]}   <- {ULTIMO}")
rc = probar(*CONTROL)
print(f"  {'PASA' if rc == 0 else 'FALLA':10} {CONTROL[0]}")
print(f"\n{len(ROTURAS) - escapes}/{len(ROTURAS)} roturas cazadas · control {'verde' if rc == 0 else 'ROJO'}")
