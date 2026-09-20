# -*- coding: utf-8 -*-
"""¿El `verif_v430` REANCLADO sigue cazando lo que defendía?

Reanclar un guardián sin probarlo contra su propio fallo es relajarlo diciendo que no.
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUARDIAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v430.py")
_NL = chr(10)

ROTURAS = [
    ("ausencias.py", "el RECORTE de v432 desaparece",
     "            _pag = max(0.0, HORAS_DIA - _ya)",
     "            _pag = HORAS_DIA"),
    ("ausencias.py", "deja de mirar las horas ya fichadas",
     "        fichadas = timeclock.horas_por_usuario_dia(grupo, d0, d1)",
     "        fichadas = {}"),
    # ⚠️ El ancla incluye la linea ANTERIOR: con solo la de `incluye_findes`, los 40
    # espacios eran SUBCADENA de la misma linea con 45 en otra funcion, asi que el
    # replace pegaba en el sitio equivocado y la rotura no probaba nada (leccion v438).
    ("ausencias.py", "lo pagado recuenta el rango por su cuenta (ignora findes)",
     _NL.join(['        _d = [d for d in dias_del_rango(r.get("From"), r.get("To"),',
               "                                        incluye_findes(r))"]),
     _NL.join(['        _d = [d for d in dias_del_rango(r.get("From"), r.get("To"),',
               "                                        False)"])),
    ("ausencias.py", "el agregado deja de delegar (segunda definicion)",
     "    for clave, e in horas_pagadas_dia(grupo, desde, hasta).items():",
     "    for clave, e in dict(_ausencias_dia_copia(grupo, desde, hasta)).items():"),
    ("auth.py", "una columna se cuela DELANTE de las historicas",
     _NL.join(['LOGIN_HEADERS = ["User", "Password", "Role", "Name", "Active", "Group",']),
     _NL.join(['LOGIN_HEADERS = ["ZZZ", "User", "Password", "Role", "Name", "Active", "Group",'])),
    ("auth.py", "_COL vuelve a escribirse A MANO",
     "_COL = {h: i + 1 for i, h in enumerate(LOGIN_HEADERS)}",
     '_COL = {"User": 1, "Password": 2}'),
    # ── CONTROL ──
    ("ausencias.py", "CONTROL: solo un comentario nuevo",
     "logger = logging.getLogger(__name__)",
     _NL.join(["logger = logging.getLogger(__name__)", "# comentario inocuo"])),
]


def _leer(r):
    with io.open(r, encoding="utf-8") as f:
        return f.read()


def _escribir(r, t):
    with io.open(r, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def _restaurar(r, orig, que):
    for i in range(5):
        try:
            _escribir(r, orig)
            if _leer(r) == orig:
                return True
        except OSError as e:
            print(f"       (reintento {i + 1}: {e})")
        time.sleep(1.5)
    print(f"  *** NO SE PUDO RESTAURAR {r} tras «{que}» — se aborta")
    return False


def corre(espera=6):
    time.sleep(espera)
    return subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode


_COPIA = {}
for _f in {f for f, *_ in ROTURAS}:
    _r = os.path.join(RAIZ, "core", _f)
    _c = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_r430_{_f}")
    _escribir(_c, _leer(_r))
    _COPIA[_r] = _c
print("copias:", ", ".join(os.path.basename(v) for v in _COPIA.values()))
print("verde de BASE:", "OK" if corre(0) == 0 else "*** ROJO ***")
print("")

mal = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = _leer(ruta)
    if orig.count(viejo) < 1:
        print("  ??   %-52s ANCLA NO ENCONTRADA" % que[:52])
        mal += 1
        continue
    cod = None
    try:
        _escribir(ruta, orig.replace(viejo, nuevo, 1))
        cod = corre()
    finally:
        if not _restaurar(ruta, orig, que):
            sys.exit(2)
    ctrl = que.startswith("CONTROL")
    bien = (cod == 0) if ctrl else (cod != 0)
    mal += 0 if bien else 1
    print("  %s %-52s (%s)" % ("ok  " if bien else "ESCAPA", que[:52],
                               "pasa" if cod == 0 else "rojo"))

print("")
print("%d mal" % mal)
sys.exit(0 if mal == 0 else 1)
