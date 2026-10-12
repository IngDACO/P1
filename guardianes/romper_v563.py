# -*- coding: utf-8 -*-
"""Bateria de roturas de v563. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Groupings en producción.
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v563"
PR = "core/projects.py"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ borrar vuelve a NO desagrupar (huérfanos en la hoja)", PR,
     [("    if n:\n        ok, msg = set_grouping_members(gid, {}, grupo)\n        if not ok:\n"
       "            return False, msg\n", "")]),
    ("⚠️ se borra aunque desagrupar falle", PR,
     [("        ok, msg = set_grouping_members(gid, {}, grupo)\n        if not ok:\n"
       "            return False, msg\n",
       "        ok, msg = set_grouping_members(gid, {}, grupo)\n")]),
    ("la pantalla borra sin pasar el grupo", PU,
     [('ok, msg = P.delete_grouping(_ag["ID"], grupo)', 'ok, msg = P.delete_grouping(_ag["ID"])')]),
    ("⚠️ el alta vuelve a quedarse con el nombre y las obras marcadas", PU,
     [('                    st.session_state["_agr_new_gen"] = _ng + 1\n', '')]),
    ("⚠️ la cabecera vuelve a «:material/warning:» literal", PU,
     [('t("Already in another group")', 't(":material/warning: Already in another")')]),
    ("la casilla vuelve a «In the grou…»", PU,
     [("st.column_config.CheckboxColumn(t(\"In group\"), width=\"small\")",
       "st.column_config.CheckboxColumn(width=\"small\")")]),
    ("⚠️ «HOURS 0» otra vez", PU,
     [('    _h = f"{tot_h:.1f} h" if tot_h < 10 else f"{tot_h:.0f} h"\n',
       '    _h = f"{tot_h:.0f}"\n')]),
    ("⚠️ las tarjetas vuelven a flex (la última se estira)", PU,
     [("st.markdown('<div style=\"display:grid;grid-template-columns:repeat(auto-fill,'",
       "st.markdown('<div style=\"display:flex;flex-wrap:wrap;'")]),
    ("la entrega vuelve sin año", PU,
     [('"Entrega prev.": _pf.strftime("%d/%m/%Y") if _pf else "—",',
       '"Entrega prev.": _pf.strftime("%d/%m") if _pf else "—",')]),
    ("⚠️ el ascensor deja de estar fijado", PU,
     [('"Elevador": st.column_config.Column(t("Lift"), pinned=True),',
       '"Elevador": st.column_config.Column(t("Lift")),')]),
    ("el coste vuelve sin $", PU,
     [('"Cost": st.column_config.NumberColumn(t("Cost"), format="$%,.2f"',
       '"Cost": st.column_config.NumberColumn(t("Cost"), format="%.2f"')]),
    ("⚠️ vuelve la gráfica de barras vacía", PU,
     [('    _out = [r["Elevador"] for r in rows if r["vs media h"].startswith("+")]\n',
       '    st.bar_chart(pd.DataFrame({"x": [0, 0]}))\n'
       '    _out = [r["Elevador"] for r in rows if r["vs media h"].startswith("+")]\n')]),
    ("⚠️ la curva vuelve a los dos azules", PU,
     [('range=["#BA7517", "#1e8449"]', 'range=["#2e6da4", "#9ec5ea"]')]),
    ("la curva pierde la línea de HOY", PU,
     [('    if cur.get("hoy"):\n        _h = pd.DataFrame', '    if False:\n        _h = pd.DataFrame')]),
    ("la leyenda de la curva vuelve al español", PU,
     [('    _pl, _re = t("Planned"), t("Actual")\n', '    _pl, _re = "Planificado", "Real"\n')]),
    ("⚠️ la tarjeta vuelve a «2 elev»", PU,
     [('_nl = (t("1 lift") if r["n"] == 1 else t("{n} lifts").replace("{n}", str(r["n"])))',
       '_nl = f"{r[\'n\']} elev"')]),
    ("la fecha de la tarjeta vuelve sin año", PU,
     [("{r['fecha'].strftime('%d/%m/%Y')}", "{r['fecha'].strftime('%d/%m')}")]),
    ("una sola agrupación vuelve a media fila", PU,
     [('    _por_fila = 1 if len(rows) == 1 else 2\n', '    _por_fila = 2\n')]),
    ("⚠️ guardar sin cambios vuelve a escribir (y en verde)", PU,
     [("                if set(_sel) == set(_act) and", "                if False and set(_sel) == set(_act) and")]),
    ("sin agrupaciones, el alta vuelve a nacer plegada", PU,
     [('expanded=not ags, key=f"exp_agr_new_{not ags}"):', 'key="exp_agr_new"):')]),
    ("un texto de Groupings vuelve sin `t()`", PU,
     [('st.markdown(t("**Groups of lifts — {n}**").replace("{n}", str(len(ags))))',
       'st.markdown(f"**Groups of lifts — {len(ags)}**")')]),
    ("⚠️ la URL vuelve a perder la agrupación", HU,
     [('            quiero["g"] = str(agr)\n', '            pass\n')]),
    ("un enlace con `&g=` deja de abrirla", HU,
     [('            st.session_state["_admin_open_agr"] = str(qp.get("g"))\n', '            pass\n')]),
    ("⚠️ el menú vuelve a no cerrar lo abierto", HU,
     [('                            st.session_state.pop(_abierto, None)\n',
       '                            pass\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PR, [("    pantalla prometía «they are only ungrouped». Primero se desagrupan;",
                 "    pantalla prometía «they are only ungrouped». Primero se desagrupan; (control)")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    _base = corre()
    if not _base:
        print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
              % ("COLGADO" if _base is None else "rojo"))
        sys.exit(1)
    print("   verde")

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for desc, rel, cambios in _rot:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
