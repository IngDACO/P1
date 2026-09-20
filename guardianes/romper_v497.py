# -*- coding: utf-8 -*-
"""Batería v497: cada rotura debe poner rojo verif_v497; el CONTROL debe pasar."""
import io
import os
import shutil
import subprocess
import sys
import time

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v497.py")
ULTIMO = []

ROTURAS = [
    ("se adivina con dos empleados del mismo nombre", "core/xero_nomina.py",
     "        if cand2 and len(cand2) == 1:",
     "        if cand2:"),
    ("un correo ambiguo se resuelve al primero", "core/xero_nomina.py",
     "        cand = por_email.get(email) if email else None\n        if cand and len(cand) == 1:",
     "        cand = por_email.get(email) if email else None\n        if cand:"),
    ("dos personas de COPEX pueden caer en el mismo empleado", "core/xero_nomina.py",
     "    for v in out.values():\n        if v[\"id\"] in repetidos:",
     "    for v in out.values():\n        if False and v[\"id\"] in repetidos:"),
    ("`propuesta` vuelve a tener su propia lógica", "core/xero_nomina.py",
     "    return {k: v[\"id\"] for k, v in propuesta_detallada(usuarios, empleados).items() if v[\"id\"]}",
     "    return {str(u.get('User', '')): (empleados[0]['EmployeeID'] if empleados else '')\n            for u in usuarios}"),
    ("la pantalla deja de decir por qué no hay pareja", "core/xero_ui.py",
     '        if _sin:',
     '        if False and _sin:'),
    ("el relleno pisa lo que el administrador ya eligió", "core/xero_ui.py",
     '                if pid and not st.session_state.get(f"xn_emp_{lg}") and pid not in _ya:',
     '                if pid:'),
    ("el relleno se hace al pulsar (y no en la pasada siguiente)", "core/xero_ui.py",
     '        if st.session_state.pop("_xn_aplicar_propuesta", False):',
     '        if False and st.session_state.pop("_xn_aplicar_propuesta", False):'),
    ("desaparece el botón de rellenar", "core/xero_ui.py",
     '        if propuesto and st.button(t(":material/auto_fix_high: Fill in the {n} proposed "',
     '        if False and st.button(t(":material/auto_fix_high: Fill in the {n} proposed "'),
]
CONTROL = ("CONTROL: comentario inocuo", "core/xero_nomina.py",
           "def propuesta_detallada(usuarios: list, empleados: list) -> dict:",
           "# comentario inocuo\ndef propuesta_detallada(usuarios: list, empleados: list) -> dict:")


def correr():
    global ULTIMO
    r = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ULTIMO = [l.strip()[:130] for l in (r.stdout or "").splitlines() if "FALLO" in l][:2] \
        or [l.strip()[:130] for l in (r.stderr or "").splitlines() if "Error" in l][-1:]
    return r.returncode


def probar(nombre, fich, old, new):
    p = os.path.join(RAIZ, fich)
    copia = os.path.join(AQUI, "_r497_" + os.path.basename(fich))
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
