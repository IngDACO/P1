# -*- coding: utf-8 -*-
"""Batería v492: cada rotura debe poner rojo verif_v492; el CONTROL debe pasar."""
import io
import os
import shutil
import subprocess
import sys
import time

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v492.py")

ROTURAS = [
    ("emparejado vuelve a volcar mapa() entero", "core/xero_nomina.py",
     '    return contable.guardar_claves(grupo, {"xero_empleados": {',
     '    cfg = dict(contable.mapa(grupo))\n    return contable.guardar_claves(grupo, cfg) or contable.guardar_claves(grupo, {"xero_empleados": {'),
    ("guardar_claves lee de la CACHÉ", "core/contable.py",
     'crudo = auth.group_text_setting_fresco(grupo, "AccountingJSON", "")',
     'crudo = auth.group_text_setting(grupo, "AccountingJSON", "")'),
    ("un fallo de lectura se trata como vacío y escribe", "core/contable.py",
     "        return False, f\"{t('The accounting settings could not be read; nothing was saved.')} ({e})\"",
     '        crudo = ""'),
    ("sin fusión de un nivel (MYOB se pierde)", "core/contable.py",
     "            guardado[k] = {**guardado[k], **v}",
     "            guardado[k] = v"),
    ("un editor escribe AccountingJSON por su cuenta", "core/contable_ui.py",
     'ok, msg = contable.guardar_claves(grupo, {"conceptos": {',
     'ok, msg = contable.auth.set_group_setting(grupo, "AccountingJSON", {"conceptos": {'),
    ("set_group_setting con su propia búsqueda de fila", "core/auth.py",
     "    fila, _r = _grupo_fresco(gws, grupo)\n    if fila is None:\n        return False, t(\"Company not found.\")",
     "    fila, _r = next(((i + 2, r) for i, r in enumerate(gws.get_all_records()) if r.get('Group') == grupo), (None, None))\n    if fila is None:\n        return False, t(\"Company not found.\")"),
    ("la lectura fresca devuelve vacío al fallar", "core/auth.py",
     "        raise RuntimeError(err)",
     "        return default"),
    ("el estado de envío vuelve a guardar_mapa", "core/xero_ui.py",
     "        ok, msg = contable.guardar_claves(\n            grupo,",
     "        ok, msg = contable.guardar_mapa(\n            grupo,"),
]
CONTROL = ("CONTROL: comentario inocuo", "core/contable.py",
           "def guardar_claves(grupo: str, cambios: dict) -> tuple:",
           "# comentario inocuo\ndef guardar_claves(grupo: str, cambios: dict) -> tuple:")


def correr():
    r = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    global ULTIMO
    ULTIMO = [l.strip() for l in (r.stdout or "").splitlines() if "FALLO" in l or "Traceback" in l][:2]         or ([l for l in (r.stderr or "").splitlines() if "Error" in l][-1:])
    return r.returncode


def probar(nombre, fich, old, new):
    p = os.path.join(RAIZ, fich)
    copia = os.path.join(AQUI, "_romper492_" + os.path.basename(fich))
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
    est = "CAZADA" if rc not in (0,) and not isinstance(rc, str) else ("ESCAPÓ" if rc == 0 else rc)
    if est != "CAZADA":
        escapes += 1
    print(f"  {est:8} {r[0]}   <- {ULTIMO}")
rc = probar(*CONTROL)
print(f"  {'PASA' if rc == 0 else 'FALLA'}     {CONTROL[0]}")
print(f"\n{len(ROTURAS) - escapes}/{len(ROTURAS)} roturas cazadas · control {'verde' if rc == 0 else 'ROJO'}")
