# -*- coding: utf-8 -*-
"""Batería v495: cada rotura debe poner rojo verif_v495; el CONTROL debe pasar."""
import io
import os
import shutil
import subprocess
import sys
import time

RAIZ = "C:/Users/diego/P1/survey_app"
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(AQUI, "verif_v495.py")
ULTIMO = []

ROTURAS = [
    # ⚠️ La primera versión de esta rotura quitaba el `continue` del borrador, y la
    # frenaba la guarda siguiente (`est not in _COBRABLES`): el código tiene doble defensa,
    # así que aquello no era un fallo. El fallo REAL es que un borrador cuente como cobrable.
    ("un borrador de Xero cuenta como cobrable (pone a CERO el cobro de aquí)", "core/xero.py",
     '_COBRABLES = {"AUTHORISED", "PAID"}\n_SIN_COBRO = {"DRAFT", "SUBMITTED"}',
     '_COBRABLES = {"AUTHORISED", "PAID", "DRAFT", "SUBMITTED"}\n_SIN_COBRO = set()'),
    ("una anulada en Xero se sincroniza igual", "core/xero.py",
     "                if est in _MUERTAS or est not in _COBRABLES:\n                    res[\"muertas\"].append((f.get(\"ID\"), numero, est))\n                    continue",
     "                if est in _MUERTAS or est not in _COBRABLES:\n                    res[\"muertas\"].append((f.get(\"ID\"), numero, est))"),
    ("el crédito se suma como si fuera cobrado", "core/xero.py",
     'cambios[str(f.get("ID"))] = {"cobrado": pagado, "fecha": fecha.isoformat()}',
     'cambios[str(f.get("ID"))] = {"cobrado": pagado + credito, "fecha": fecha.isoformat()}'),
    ("un fallo de red acusa a las facturas de borradas", "core/xero.py",
     "            if xid not in vistos and not res[\"errores\"]:",
     "            if xid not in vistos:"),
    ("el cobrado se SUMA en vez de fijarse (pulsar dos veces cobra dos veces)",
     "core/invoices.py",
     "        ahora = round(_num(dato.get(\"cobrado\")), 2)",
     "        ahora = round(antes + _num(dato.get(\"cobrado\")), 2)"),
    ("apunta en el historial aunque no cambie nada", "core/invoices.py",
     "        if abs(ahora - antes) < 0.005:\n            res[\"iguales\"].append(fid)\n            continue",
     "        if abs(ahora - antes) < 0.005:\n            res[\"iguales\"].append(fid)"),
    ("escribe factura a factura en vez de por lote", "core/invoices.py",
     "    if not rangos:\n        return True, res\n    try:\n        w.batch_update(rangos, value_input_option=\"RAW\")",
     "    if not rangos:\n        return True, res\n    try:\n        for _r in rangos:\n            w.batch_update([_r], value_input_option=\"RAW\")"),
    ("se consultan también las anuladas de COPEX", "core/xero.py",
     '                        and _norm(f.get("Status")) != "anulada"]',
     "                        ]"),
    ("dos parsers de fecha otra vez", "core/xero_nomina.py",
     "    return X.de_fecha(valor)",
     "    import re as _r, datetime as _d2\n    m = _r.search(r'/Date\\((-?\\d+)', str(valor or ''))\n    return _d2.datetime.fromtimestamp(int(m.group(1)) / 1000, _d2.timezone.utc).date() if m else _parse_date(valor)"),
    ("el resumen se calla los borradores", "core/xero_ui.py",
     '    if res["en_borrador"]:',
     '    if False and res["en_borrador"]:'),
    ("`theme` deja de importarse dentro del resumen", "core/xero_ui.py",
     "    from core import theme as T          # ⚠️ local: en este módulo theme se importa así\n",
     ""),
]
CONTROL = ("CONTROL: comentario inocuo", "core/xero.py",
           "def traer_cobros(grupo: str) -> dict:",
           "# comentario inocuo\ndef traer_cobros(grupo: str) -> dict:")


def correr():
    global ULTIMO
    r = subprocess.run([sys.executable, GUARD], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ULTIMO = [l.strip()[:150] for l in (r.stdout or "").splitlines() if "FALLO" in l][:2] \
        or [l.strip()[:150] for l in (r.stderr or "").splitlines() if "Error" in l][-1:]
    return r.returncode


def probar(nombre, fich, old, new):
    p = os.path.join(RAIZ, fich)
    copia = os.path.join(AQUI, "_r495_" + os.path.basename(fich))
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
