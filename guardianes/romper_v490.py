# -*- coding: utf-8 -*-
"""¿verif_v490 CAZA sus fallos? Cada rotura contra el guardián, con verde de BASE primero
y un CONTROL que debe pasar. Copia a disco, restore VERIFICADO y ABORTO si falla (v484).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARDIANES = ["verif_v490.py"]
NL = chr(10)

ROTURAS = [
    ("core/xero_nomina.py", "a_ms usa la hora LOCAL (corre el dia)", [
        ("    base = _dt.datetime(d.year, d.month, d.day, tzinfo=_dt.timezone.utc)",
         "    base = _dt.datetime(d.year, d.month, d.day) + _dt.timedelta(hours=10)")]),
    ("core/xero_nomina.py", "NumberOfUnits sin el orden del periodo", [
        ("    unidades = [round(_num((horas_por_dia or {}).get(d)), 2) for d in dias_del_periodo(inicio, fin)]",
         "    unidades = [round(_num(h), 2) for h in (horas_por_dia or {}).values()]")]),
    ("core/xero_nomina.py", "el periodo mensual acaba un dia tarde", [
        ("        return inicio, _suma_meses(inicio, 1) - _dt.timedelta(days=1)",
         "        return inicio, _suma_meses(inicio, 1)")]),
    ("core/xero_nomina.py", "se propone pareja aunque el nombre se repita", [
        ("        if cand and len(cand) == 1:", "        if cand:")]),
    ("core/xero_nomina.py", "un parte APROBADO se sobrescribe", [
        ('                elif existe is not None and str(existe.get("Status", "")).upper() != BORRADOR:',
         '                elif False:')]),
    ("core/xero_nomina.py", "sin poder comprobar se crea igual", [
        ("                if err:" + NL + "                    # ⚠️ Sin poder comprobar si ya hay parte NO se crea otro (duplicado).",
         "                if False:" + NL + "                    # ⚠️ Sin poder comprobar si ya hay parte NO se crea otro (duplicado).")]),
    ("core/xero_nomina.py", "solo se mira la primera pagina", [
        ("        if len(lote) < 100:" + NL + "            return out, \"\"",
         "        if True:" + NL + "            return out, \"\"")]),
    ("core/xero_nomina.py", "un permiso que ya esta se reenvia", [
        ("                if ya:" + NL + "                    res[\"omitidos\"]",
         "                if False:" + NL + "                    res[\"omitidos\"]")]),
    ("core/xero_nomina.py", "otro calendario se manda igual", [
        ('        if emp.get("PayrollCalendarID") != calendario_id:',
         '        if False:')]),
    ("core/xero_nomina.py", "fechas fuera de periodo se aceptan", [
        ('    if not any(p["inicio"] == inicio and p["fin"] == fin for p in periodos(cal)):',
         '    if False:')]),
    ("core/xero_nomina.py", "tramos no corta en un hueco", [
        ("        if out and d == out[-1][1] + _dt.timedelta(days=1):",
         "        if out:")]),
    ("core/xero.py", "sin ritmo: nunca espera", [
        ("        if len(marcas) >= _CUPO_MIN:", "        if False:")]),
    ("core/xero.py", "un 429 corto no se reintenta", [
        ("            if 0 < segundos <= _ESPERA_429:", "            if False:")]),
    ("core/xero.py", "no se leen los errores dentro de cada objeto", [
        ("        for v in js.values():" + NL + "            if isinstance(v, list):",
         "        for v in []:" + NL + "            if isinstance(v, list):")]),
    ("core/xero_ui.py", "entran los usuarios INACTIVOS", [
        ('                if str(u.get("Active", "")).strip().upper() in auth._ACTIVE_OK]',
         '                ]')]),
    ("core/xero_nomina.py", "CONTROL: solo un comentario nuevo", [
        ("def _cf(s) -> str:", "# comentario inocuo" + NL + "def _cf(s) -> str:")]),
]


def _leer(r):
    with io.open(r, encoding="utf-8") as f:
        return f.read()


def _escribir(r, txt):
    with io.open(r, "w", encoding="utf-8", newline="") as f:
        f.write(txt)


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
    peor = 0
    for g in GUARDIANES:
        rc = subprocess.run([sys.executable, os.path.join(AQUI, g)], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode
        peor = peor or rc
    return peor


for _f in {f for f, *_ in ROTURAS}:
    _escribir(os.path.join(AQUI, "_v490r_" + _f.replace("/", "_")), _leer(os.path.join(RAIZ, _f)))

base = corre()
print("verde de BASE: %s" % ("OK" if base == 0 else "*** ROJO: la tanda no valdria nada ***"))
if base != 0:
    sys.exit(2)
print("")

mal = 0
for fich, que, pares in ROTURAS:
    ruta = os.path.join(RAIZ, fich)
    orig = _leer(ruta)
    nuevo = orig
    ancla_mal = False
    for viejo, reemplazo in pares:
        if nuevo.count(viejo) != 1:
            print("  ??   %-55s ANCLA aparece %d veces: %r" % (que[:55], nuevo.count(viejo), viejo[:50]))
            ancla_mal = True
            break
        nuevo = nuevo.replace(viejo, reemplazo, 1)
    if ancla_mal:
        mal += 1
        continue
    cod = None
    try:
        _escribir(ruta, nuevo)
        cod = corre()
    finally:
        if not _restaurar(ruta, orig, que):
            sys.exit(2)
    ctrl = que.startswith("CONTROL")
    bien = (cod == 0) if ctrl else (cod != 0)
    mal += 0 if bien else 1
    print("  %s %-55s (%s)" % ("ok  " if bien else "ESCAPA", que[:55], "pasa" if cod == 0 else "rojo"))
    time.sleep(3)

print("")
print("%d mal" % mal)
sys.exit(0 if mal == 0 else 1)
