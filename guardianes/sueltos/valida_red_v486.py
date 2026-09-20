# -*- coding: utf-8 -*-
"""¿La red de `verif_v467` CAZA el NaN, o su «0» no significa nada?

Un guardian verde con el codigo bueno no prueba nada (trampa n12): hay que ensenarle
el fallo y ver que salta. Se prueban las TRES formas de escribir el nulo, en las dos
posiciones (valor directo y rama `else` de un ternario), y un CONTROL que debe pasar.

Copia a disco ANTES de tocar, VERIFICA el restore y ABORTA si no puede (leccion v484:
una bateria cuyo `finally` falla deja codigo roto en el arbol).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARDIAN = os.path.join(AQUI, "verif_v467.py")
NL = chr(10)

ROTURAS = [
    ("contable_ui.py", 'float("nan") como valor directo',
     '**{_etq_dia[d]: tabla.celda(f["horas"].get(d), 2)',
     '**{_etq_dia[d]: f["horas"].get(d, float("nan"))'),
    ("payroll_ui.py", 'float("nan") en la rama else de un ternario',
     '"Rate/h": (tabla.celda(x.get("HourlyRate"), 2, "$")' + NL +
     '                     if _num(x.get("HourlyRate")) > 0 else ""),',
     '"Rate/h": (round(_num(x.get("HourlyRate")), 2)' + NL +
     '                     if _num(x.get("HourlyRate")) > 0 else float("nan")),'),
    ("catalogo_ui.py", "np.nan (otra forma de escribirlo)",
     '"Horas": (tabla.celda(i.get("EstHours"), 2)' + NL +
     '                      if str(i.get("Type", "")) == CAT.SERVICIO else ""),',
     '"Horas": (round(_num(i.get("EstHours")), 2)' + NL +
     '                      if str(i.get("Type", "")) == CAT.SERVICIO else np.nan),'),
    ("inventory_ui.py", "pd.NA (la tercera forma)",
     '"Costo":   (tabla.celda(m.get("Cost"), 0, "$")' + NL +
     '                        if str(m.get("Cost", "")).strip() else ""),',
     '"Costo":   (round(_num(m.get("Cost")), 0)' + NL +
     '                        if str(m.get("Cost", "")).strip() else pd.NA),'),
    ("contable_ui.py", "None pelado (lo que ya cazaba antes)",
     '**{_etq_dia[d]: tabla.celda(f["horas"].get(d), 2)',
     '**{_etq_dia[d]: f["horas"].get(d)'),
    # ── CONTROL: un cambio inocuo NO debe hacerla saltar ──
    ("contable_ui.py", "CONTROL: solo un comentario nuevo",
     "def _partes_section(grupo):",
     "def _partes_section(grupo):" + NL + "    # comentario inocuo"),
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
            print("       (reintento %d: %s)" % (i + 1, e))
        time.sleep(1.0)
    print("  *** NO SE PUDO RESTAURAR %s tras «%s» — SE ABORTA" % (r, que))
    return False


def corre():
    return subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode


# copias en disco ANTES de tocar nada
_COPIA = {}
for _f in {f for f, *_ in ROTURAS}:
    _r = os.path.join(RAIZ, "core", _f)
    _c = os.path.join(AQUI, "_v486_" + _f)
    _escribir(_c, _leer(_r))
    _COPIA[_r] = _c
print("copias: %s" % ", ".join(os.path.basename(v) for v in _COPIA.values()))

base = corre()
print("verde de BASE: %s" % ("OK" if base == 0 else "*** ROJO: la tanda no valdria nada ***"))
if base != 0:
    sys.exit(2)
print("")

mal = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = _leer(ruta)
    if orig.count(viejo) != 1:
        print("  ??   %-52s ANCLA aparece %d veces" % (que[:52], orig.count(viejo)))
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
