# -*- coding: utf-8 -*-
"""Batería de roturas de v663. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v663"
TOPE_S = 240
FI = "core/finance.py"
PU = "core/projects_ui.py"
CT = "core/chat_tools.py"
TC = "core/timeclock.py"
PR = "core/payroll.py"
PRU = "core/payroll_ui.py"
TU = "core/timeclock_ui.py"
CU = "core/correcciones_ui.py"
AU = "core/auth_ui.py"

ROTURAS = [
    ("⚠️ la ganancia vuelve a salir con el GST", FI,
     [("ganancia = round(ingresos - costo_total, 2)", "ganancia = round(facturado - costo_total, 2)")]),
    ("⚠️ los ingresos vuelven a ser el total con impuesto", FI,
     [("ingresos  = round(sum(_sin_impuesto(f) for f in facs), 2)",
       'ingresos  = round(sum(_num(f.get("Total")) for f in facs), 2)')]),
    ("fila vieja sin Subtotal: deja de restar el Tax", FI,
     [('        return round(tot - _num(f.get("Tax")), 2)\n', "        return tot\n")]),
    ("pnl_comparado deja de comparar los ingresos", FI,
     [('campos = ("facturado", "ingresos", "cobrado",', 'campos = ("facturado", "cobrado",')]),
    ("⚠️ Summary enseña el total con GST como ingreso", PU,
     [('T.dinero(d.get("ingresos", d["facturado"]), 0),', 'T.dinero(d["facturado"], 0),')]),
    ("el margen vuelve a salir del total con GST", PU,
     [('_mrg = (100 * d["ganancia"] / _ing)', '_mrg = (100 * d["ganancia"] / d["facturado"])')]),
    ("el asistente recibe el beneficio sin decir que es sin impuesto", CT,
     [('"profit_ex_tax": p["ganancia"]', '"profit": p["ganancia"]')]),
    ("⚠️ la jornada abierta vuelve a contar en la nómina", TC,
     [('        if solo_cerradas and str(r.get("Status", "")).strip().upper() == "ABIERTO":\n            continue\n', "")]),
    ("⚠️ generar paga también lo abierto", PR,
     [("horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta, solo_cerradas=True)",
       "horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)")]),
    ("⚠️ el periodo por defecto vuelve a acabar hoy", PRU,
     [("    _h0 = hoy - timedelta(days=1)\n", "    _h0 = hoy\n")]),
    ("la vista previa no avisa de la jornada abierta", PRU,
     [("    if _abiertas:\n", "    if False:\n")]),
    ("⚠️ el motor deja empezar la obra antes que la jornada", TC,
     [("            if n0 < a0:\n", "            if False:\n")]),
    ("la jornada puede dejar fuera sus obras", TC,
     [('            if a0 < n0 or (str(co or "").strip() and a1 > n1):', "            if False:")]),
    ("⚠️ corregir_fichaje no lo comprueba", TC,
     [("    if _fuera:\n        return False, _fuera\n", "    if False:\n        return False, _fuera\n")]),
    ("el campo no ofrece mover la jornada", TU,
     [("        if campo == correcciones.CAMPO_IN and nuevo < g0:\n            return g\n",
       "        if False:\n            return g\n")]),
    ("la casilla de mover la jornada nace desmarcada", TU,
     [('value=True, key="cor_mover_jornada")', 'value=False, key="cor_mover_jornada")')]),
    ("⚠️ la revisión vuelve a dar el signo de la marca, no del trabajo", CU,
     [('        if str(r.get("Field", "")) == C.CAMPO_IN:\n            d = -d\n', "")]),
    ("las colillas vuelven a un decimal", PRU,
     [("h=f\"{_num(f.get('Hours')):.2f}\", r=_T.dinero", "h=f\"{_num(f.get('Hours')):.1f}\", r=_T.dinero")]),
    ("Costs vuelve a decir «No costs» con coste", PU,
     [('    elif cp["total"] > 0:\n        # ⚠️ v663', '    elif False:\n        # ⚠️ v663')]),
    ("«Save rate» activo sin cambio", AU,
     [("disabled=abs(float(tar) - _tar0) < 0.005", "disabled=False")]),
    ("«Save start date» activo con la fecha vacía", AU,
     [("disabled=(_nf or None) == (_fi or None)", "disabled=False")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", FI,
           [("# v663: sin el GST", "# v663 (control): sin el GST")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
