# -*- coding: utf-8 -*-
"""¿Las redes de v487 CAZAN sus fallos? Cada rotura contra los TRES guardianes.

Verde de BASE primero (sin el, una tanda entera sale «cazada» sin probar nada, v459) y
un CONTROL que debe pasar. Copia a disco, restore VERIFICADO y ABORTO si falla (v484).
Espaciado: verif_v469 lee la hoja real y el techo es 60/min (trampa n19).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARDIANES = ["check_v487_smoke.py", "verif_v487.py", "verif_v469.py"]
NL = chr(10)

ROTURAS = [
    ("inventory_ui.py", "KPI vuelve a buscar «disponible»",
     "c[1].metric(t(\"Available\"), est.get(INV.DISPONIBLE, 0))",
     "c[1].metric(t(\"Available\"), est.get(\"disponible\", 0))"),
    ("inventory.py", "el alta vuelve a escribir «disponible»",
     "           DISPONIBLE, str(condicion or CONDICIONES[0]), str(ubicacion_tipo or UBIC_TIPOS[0]),",
     "           \"disponible\", str(condicion or CONDICIONES[0]), str(ubicacion_tipo or UBIC_TIPOS[0]),"),
    ("inventory.py", "mantenimiento vuelve a escribir «mantenimiento»",
     "        campos[\"Status\"] = MANTENIMIENTO",
     "        campos[\"Status\"] = \"mantenimiento\""),
    ("inventory_ui.py", "Category vuelve al patron index-o-0",
     "        _cats, _ci = ui.opciones_con_actual(cats, a.get(\"Category\"))",
     "        _cats, _ci = cats, (cats.index(a.get(\"Category\")) if a.get(\"Category\") in cats else 0)"),
    ("catalogo_ui.py", "Unit vuelve al patron index-o-0",
     "            _unis, _uni = ui.opciones_con_actual(CAT.UNIDADES, it.get(\"Unit\", \"\"))",
     "            _unis, _uni = list(CAT.UNIDADES), (list(CAT.UNIDADES).index(it.get(\"Unit\", \"\")) if it.get(\"Unit\", \"\") in CAT.UNIDADES else 0)"),
    ("auth_ui.py", "el rol por defecto vuelve a «campo»",
     "            _rcur = str(u.get(\"Role\", \"\") or \"field\")",
     "            _rcur = str(u.get(\"Role\", \"\") or \"campo\")"),
    ("roster_ui.py", "el guardado del color vuelve a `_colmap[_cn]`",
     "\"Color\": _colmap.get(_cn, _cn)})",
     "\"Color\": _colmap[_cn]})"),
    ("expenses.py", "la compra sin categoria vuelve a «Otros»",
     "        c = str(r.get(\"Category\", \"\")) or SIN_CATEGORIA",
     "        c = str(r.get(\"Category\", \"\")) or \"Otros\""),
    ("ui_common.py", "el helper deja de CONSERVAR el valor",
     "        return [act] + ops, 0",
     "        return ops, 0"),
    ("projects_ui.py", "estado manual vuelve al patron index-o-0",
     "            _ems, _emi = ui.opciones_con_actual(P.ESTADOS_MANUAL, prj.get(\"ManualStatus\", \"\"))",
     "            _ems, _emi = P.ESTADOS_MANUAL, (P.ESTADOS_MANUAL.index(prj.get(\"ManualStatus\", \"\")) if prj.get(\"ManualStatus\", \"\") in P.ESTADOS_MANUAL else 0)"),
    ("ui_common.py", "CONTROL: solo un comentario nuevo",
     "def opciones_con_actual(opciones, actual):",
     "# comentario inocuo" + NL + "def opciones_con_actual(opciones, actual):"),
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
    """Codigo != 0 si ALGUNO de los tres guardianes falla."""
    peor = 0
    for g in GUARDIANES:
        rc = subprocess.run([sys.executable, os.path.join(AQUI, g)], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode
        peor = peor or rc
    return peor


_COPIA = {}
for _f in {f for f, *_ in ROTURAS}:
    _r = os.path.join(RAIZ, "core", _f)
    _c = os.path.join(AQUI, "_v487r_" + _f)
    _escribir(_c, _leer(_r))
    _COPIA[_r] = _c

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
        print("  ??   %-50s ANCLA aparece %d veces" % (que[:50], orig.count(viejo)))
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
    print("  %s %-50s (%s)" % ("ok  " if bien else "ESCAPA", que[:50],
                               "pasa" if cod == 0 else "rojo"))
    time.sleep(4)

print("")
print("%d mal" % mal)
sys.exit(0 if mal == 0 else 1)
