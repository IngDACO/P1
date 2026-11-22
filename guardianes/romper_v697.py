# -*- coding: utf-8 -*-
"""Batería de roturas de v697. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v697"
TOPE_S = 400
TH = "core/theme.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
SPU = "core/stage_progress_ui.py"
RU = "core/roster_ui.py"

ROTURAS = [
    ("el aviso flotante vuelve a 560 px (cortado por el menú)", TH,
     [("  width: min(480px, calc(100vw - 32px)) !important; z-index: 1000000;\n",
       "  width: min(560px, calc(100vw - 32px)) !important; z-index: 1000000;\n")]),
    ("⚠️ el aviso flotante, debajo del menú lateral", TH,
     [("  width: min(480px, calc(100vw - 32px)) !important; z-index: 1000000;\n",
       "  width: min(480px, calc(100vw - 32px)) !important; z-index: 999990;\n")]),
    ("⚠️ H18 · «2d» adelantada dice lo mismo que retrasada", HU,
     [('            _extra += " · " + t(":material/schedule: {n}d ahead", n=int(round(_ah)))\n',
       '            _extra += f" · :material/schedule: {int(round(_ah))}d"\n')]),
    ("H18 · retrasada sin «behind»", HU,
     [('            _extra += " · " + t(":material/schedule: {n}d behind", n=int(round(_dl)))\n',
       '            _extra += f" · :material/schedule: {int(round(_dl))}d"\n')]),
    ("⚠️ H18 · «N behind» cuenta obras que no están activas", PU,
     [('        "riesgo":  len({str(p.get("ID", "")) for p in activos} & set(P.delays_of_group(grupo))),\n',
       '        "riesgo":  len(P.delays_of_group(grupo)),\n')]),
    ("H19 · una etapa empezada vuelve a ser el próximo hito", PU,
     [('        if proximo is None and a["inicio"] > hoy and pct <= 0:\n',
       '        if proximo is None and a["inicio"] > hoy and pct < 100:\n')]),
    ("⚠️ H23 · se proyecta con un 3 % de avance", PU,
     [('    elif proy and _av_obra < AVANCE_MIN_PROYECCION and not (pres > 0 and cp["total"] > pres):\n',
       "    elif False:\n")]),
    ("⚠️ H23 · «demasiado pronto» esconde un gasto que ya pasa del presupuesto", PU,
     [('    elif proy and _av_obra < AVANCE_MIN_PROYECCION and not (pres > 0 and cp["total"] > pres):\n',
       "    elif proy and _av_obra < AVANCE_MIN_PROYECCION:\n")]),
    ("H7 · Progress vuelve a los pesos de la plantilla (suman 94)", SPU,
     [('                    "%s  ·  %.1f%%" % (a["nombre"], 100.0 * _num(a["peso_en_etapa"]) / _tot_e)\n',
       '                    "%s  ·  %.1f%%" % (a["nombre"], _num(a["peso_en_etapa"]))\n')]),
    ("H20 · el cumplimiento vuelve a la cuenta", PU,
     [('        fila = {"User": _nm_c.get(u, u), "Compliant":', '        fila = {"User": u, "Compliant":')]),
    ("H24 · el recibo sin quién lo cargó", PU,
     [('                    _lbl += " · " + t("by {x}", x=maps.literal_md(_etq_us([_por]).get(_por, _por)))\n',
       "                    pass\n")]),
    ("H2 · el head installer sin la cuadrilla primero", PU,
     [("            _hi = [u for u in campos if u in (asg or [])] + [u for u in campos if u not in (asg or [])]\n",
       "            _hi = list(campos)\n")]),
    ("H3 · Assign sin la cuadrilla primero", RU,
     [('        libres.sort(key=lambda f: (0 if f["usr"] in _crew else 1, 0 if f["cumple"] else 1, f["nom"]))\n',
       '        libres.sort(key=lambda f: (0 if f["cumple"] else 1, f["nom"]))\n')]),
    ("⚠️ H3 · «nadie tiene X» no se dice", RU,
     [('        _nadie = [c for c in certs if not any(credentials.compliance(u["User"], [c])["cumple"] for u in staff)]\n',
       "        _nadie = []\n")]),
    ("H3 · asignar a quien no cumple, sin aviso", RU,
     [('                if _sin and certs:\n'
       '                    flash.aviso(t("Assigned without {c}: {who}.", c=" · ".join(certs), who=", ".join(_sin)))\n',
       "")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("# v697 · H23 del ciclo 6: por debajo de este avance (%) no se proyecta el coste al terminar\n",
             "# v697 · H23 del ciclo 6: por debajo de este avance (%) no se proyecta el coste al terminar · control\n")])


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
