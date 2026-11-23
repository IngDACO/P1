# -*- coding: utf-8 -*-
"""Batería de roturas de v701. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v701"
TOPE_S = 240
EX, FI, QU, CT, PU = "core/expenses.py", "core/finance.py", "core/quotes.py", "core/chat_tools.py", "core/projects_ui.py"

ROTURAS = [
    ("la obra cotizada vuelve a extrapolar TODO (regla de tres)", EX,
     [('        proy = mo_proj + max(compras + comp, _num(desglose.get("material")))',
       '        proy = total * 100.0 / av')]),
    ("sin cotización, las compras vuelven a extrapolarse", EX,
     [('    return {"proyectado": round(mo_proj + compras + comp, 2), "metodo": "sin_cotizacion"}',
       '    return {"proyectado": round(total * 100.0 / av, 2), "metodo": "sin_cotizacion"}')]),
    ("la vista del grupo vuelve a su regla de tres", EX,
     [('        proyectado = costo_al_terminar(c, av, desglose_cotizado(p.get("ID")))["proyectado"]',
       '        proyectado = (round(c["total"] * 100.0 / av, 2) if av > 0 and c["total"] > 0 else None)')]),
    ("el beneficio vuelve a ser precio − lo gastado hasta hoy", FI,
     [("        if _av < 100:", "        if False:")]),
    ("por debajo del 10 % ya no cuenta el costo cotizado", FI,
     [('                elif _num(_c.get("presupuesto")) > _ref:', '                elif False:')]),
    ("el total de Profitability vuelve a ser ingreso − gastado", FI,
     [('                        "ganancia": round(sum(_num(x["ganancia"]) for x in rows), 2)}}',
       '                        "ganancia": round(t_ing - t_costo, 2)}}')]),
    ("la variación vuelve al % sobre una base de $250", FI,
     [("    en_dinero = bool(abs(dif) > 0.005 and (abs(p) < 0.1 * abs(a) or (a * p < 0)))",
       "    en_dinero = False")]),
    ("la tarjeta ignora «en dinero»", PU,
     [('    if var and (var.get("pct") is not None or var.get("en_dinero")):',
       '    if var and var.get("pct") is not None:')]),
    ("el Summary ignora «en dinero»", PU,
     [('        if var and var.get("en_dinero"):\n            # v701 · H12 del ciclo 7: «▲ 13337%» sobre una base de ~$250 no dice nada: la diferencia en dinero\n            _f = "▲" if var["dif"] > 0 else ("▼" if var["dif"] < 0 else "=")\n            return (t("{f} {d} vs previous")',
       '        if False:\n            # v701 · H12 del ciclo 7: «▲ 13337%» sobre una base de ~$250 no dice nada: la diferencia en dinero\n            _f = "▲" if var["dif"] > 0 else ("▼" if var["dif"] < 0 else "=")\n            return (t("{f} {p}% vs previous")')]),
    ("«Quoted vs. actual» proyecta con el 1 % de avance", QU,
     [("                  if av >= _E.AVANCE_MIN_PROYECCION else None)", "                  if av > 0 else None)")]),
    ("el asistente vuelve a dar lo cobrado de la factura entera", CT,
     [('            "this_job_collected": round(_cob * _esta / _sub, 2) if _sub > 0 else 0.0,',
       '            "this_job_collected": round(_cob, 2),')]),
    ("«How much you make» vuelve al ID interno (COT-0018)", PU,
     [('            _qn = str(rev.get("cotizacion_numero", "") or rev.get("cotizacion", ""))',
       '            _qn = str(rev.get("cotizacion", ""))')]),
    ("con precio pactado vuelve a ofrecer la ganancia por hora y la fija", PU,
     [("            # v701 · H4: con precio pactado, ni la ganancia por hora ni la fija cuentan: no se ofrecen\n            return",
       "            # v701 · H4: con precio pactado, ni la ganancia por hora ni la fija cuentan: no se ofrecen\n            pass")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", EX,
           [("# ⚠️ v701 · el mismo umbral que `projects_ui.AVANCE_MIN_PROYECCION` (v697): por debajo, proyectar es ruido",
             "# ⚠️ v701 · el mismo umbral que `projects_ui.AVANCE_MIN_PROYECCION` (v697): por debajo, proyectar es ruido · control")])


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
