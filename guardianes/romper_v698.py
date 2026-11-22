# -*- coding: utf-8 -*-
"""Batería de roturas de v698. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v698"
TOPE_S = 300
CA = "core/calendario.py"
SC = "core/schedule.py"
PR = "core/projects.py"
PU = "core/projects_ui.py"
TH = "core/theme.py"
DLU = "core/daily_log_ui.py"

ROTURAS = [
    ("⚠️ D1 · el sábado y el domingo vuelven a contar", CA,
     [("    return d.weekday() < 5\n", "    return True\n")]),
    ("⚠️ D1 · la pausa deja de parar el plan", CA,
     [("        return laborable(d) and not any(a <= d < b for a, b in self.pausas)\n",
       "        return laborable(d)\n")]),
    ("D1 · una pausa abierta no se cierra para el cálculo (todo lo que queda, en pausa)", CA,
     [("        self.pausas = [(a, b if b is not None else _h + timedelta(days=1)) for a, b in (pausas or ()) if a]\n",
       "        self.pausas = [(a, b if b is not None else _h + timedelta(days=400)) for a, b in (pausas or ()) if a]\n")]),
    ("D1 · antes del inicio da 0 (no negativo)", CA,
     [("        return -n\n", "        return 0\n")]),
    ("D1 · `pausas_de` no cierra la pausa al volver", CA,
     [('        elif antes == "On hold" and despues != "On hold" and abierta is not None:\n'
       "            out.append((abierta, d))\n            abierta = None\n", "")]),
    ("D1 · `pausas_de` se inventa el pasado de una pausa sin rastro", CA,
     [("        out.append((abierta or (hoy or date.today()), None))\n",
       "        out.append((abierta or date(2000, 1, 1), None))\n")]),
    ("⚠️ D1 · el fin del plan vuelve a ser natural", SC,
     [('        "fecha_fin":   cal.fin(total_dias),        # v698 · el último día de trabajo (de lunes a viernes)\n',
       '        "fecha_fin":   start_date,\n')]),
    ("D1 · las actividades, con fecha natural", SC,
     [('            "fecha_inicio": cal.fecha(_r["inicio"]),\n', '            "fecha_inicio": start_date,\n')]),
    ("D1 · el fin previsto sin calendario", SC,
     [('    fecha_cadena = (sched.get("cal") or Calendario(start)).fin(fin_cadena)      # v698 · en días que cuentan\n',
       "    fecha_cadena = start\n")]),
    ("D1 · el eje del Gantt vuelve a días naturales", SC,
     [("                 f'{_cal_eje.fecha(d).strftime(\"%d/%m\")}</text>')\n",
       "                 f'{start.strftime(\"%d/%m\")}</text>')\n")]),
    ("⚠️ D1 · «hoy» vuelve a contar días naturales", PR,
     [("    today_day = cal.dia(_hoy)\n", "    today_day = (_hoy - start).days\n")]),
    ("D1 · las ventanas reales en días naturales", PR,
     [("            return cal.dia(date(int(y), int(m), int(dd)))\n",
       "            return (date(int(y), int(m), int(dd)) - start).days\n")]),
    ("D1 · la obra no lee sus pausas", PR,
     [('    cal = Calendario(start, pausas_de(_hist, prj.get("Status", ""), _hoy), _hoy)\n',
       "    cal = Calendario(start, (), _hoy)\n")]),
    ("D1 · la agrupación con días naturales", PR,
     [('            off = s["cal"].dia(d) if s.get("cal") else (d - s["inicio"]).days\n',
       '            off = (d - s["inicio"]).days\n')]),
    ("D1 · el hito con días naturales", PU,
     [('        f_i  = sched["cal"].fecha(a["inicio"]) if sched.get("cal") else ini + timedelta(days=int(a["inicio"]))\n',
       '        f_i  = ini + timedelta(days=int(a["inicio"]))\n')]),
    ("D1 · «working day N of M» vuelve a «day»", PU,
     [('    _dia_txt  = (f"working day {_hoy_real} of {_tot}" if _hoy_real <= _tot\n',
       '    _dia_txt  = (f"day {_hoy_real} of {_tot}" if _hoy_real <= _tot\n')]),
    ("el aviso flotante con «reducir movimiento», sin duración propia (los .001 ms globales)", TH,
     [("                      animation-duration: 9s !important; }}\n", "                      }}\n")]),
    ("la doble puntuación vuelve al aviso de lo no enviado", DLU,
     [('literal_md(str(x).rstrip(" ."))', "literal_md(x)")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CA,
           [('    """¿De lunes a viernes?"""', '    """¿De lunes a viernes? · control"""')])


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
