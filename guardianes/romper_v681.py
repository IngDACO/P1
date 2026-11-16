# -*- coding: utf-8 -*-
"""Batería de roturas de v681. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v681"
TOPE_S = 600
UR, OPT, INT, DG = "core/user_report.py", "core/optimizer.py", "core/interpretation.py", "core/diagrams.py"
RP, CAL, SCA, PU, SU = "core/report.py", "core/calculations.py", "core/survey_calc.py", "core/projects_ui.py", "core/survey_ui.py"

ROTURAS = [
    # ── H1 · el sentido lateral del PDF del cliente
    ("⚠️ Main action vuelve a «right si rl >= 0»", UR,
     [('dir_lat=_SENT.get(_sentido_lateral(rl), d("right")),',
       'dir_lat=d("right") if rl >= 0 else d("left"),')]),
    # ── H3 · el optimizador
    ("⚠️ el empuje solo yendo HACIA el muro (paso 2)", OPT,
     [("            if wall_active and 0 <= wall_stop_idx < len(modified):\n",
       "            if wall_active and toward_wall and 0 <= wall_stop_idx < len(modified):\n")]),
    ("⚠️ el descarte solo yendo HACIA el muro (paso 4)", OPT,
     [("            if wall_active and not wall_evaded and 0 <= wall_stop_idx < len(modified):",
       "            if wall_active and toward_wall and not wall_evaded and 0 <= wall_stop_idx < len(modified):")]),
    ("⚠️ esquivado solo si se empuja (con empuje 0 no cuenta)", OPT,
     [("                            wall_evaded = True\n                            if objetivo > fb_applied + 1e-3:\n",
       "                            if objetivo > fb_applied + 1e-3:\n                                wall_evaded = True\n")]),
    ("⚠️ se acepta el empuje que no cabe detrás", OPT,
     [("                        if objetivo <= fb_max_back + 1e-3:", "                        if True:")]),
    ("el muro esquivado sin empujar sigue contando como fuera", OPT,
     [("if wall_evaded and row_idx == wall_stop_idx and col == wall_check_col:",
       "if fb_extra_applied and row_idx == wall_stop_idx and col == wall_check_col:")]),
    ("la apertura tapada solo si se empujó", OPT,
     [("if wall_evaded and toward_wall and frame > 0 and abs(rl) > frame:",
       "if fb_extra_applied and toward_wall and frame > 0 and abs(rl) > frame:")]),
    # ── H3 · los cortes y los textos
    ("⚠️ el muro vuelve a ser un corte", INT,
     [('        if muro and i + 1 == muro["stop"]:', "        if False:")]),
    ("el último piso del controlador contra el límite normal", INT,
     [('c_or = round(float(row.get("OR", 0) or 0) - (lim_or - (70 if _ult and ctrl == "R" else 0)), 1)',
       'c_or = round(float(row.get("OR", 0) or 0) - lim_or, 1)')]),
    ("«still out of limit» repite las aperturas", INT,
     [("            if c in _MAXIMO:\n                continue\n            if int(_num(por_col.get(c))) <= 0:",
       "            if int(_num(por_col.get(c))) <= 0:")]),
    ("los hechos sin el muro", INT, [("        _m = muro_de(p)\n        if _m:", "        _m = None\n        if _m:")]),
    ("el empuje sin decir que el muro no se corta", INT,
     [('"• The front-back shift includes %.1f mm of extra push towards the REAR to clear the limiting wall "',
       '"• The front-back shift includes %.1f mm of extra push towards the REAR to clear the wall "')]),
    ("esquivado sin empujar, sin decirlo", INT,
     [('    elif _w and _w.get("already_clear_without_extra_push"):', "    elif False:")]),
    ("el prompt: WR/WL vuelven al bloque", INT,
     [("- WR/WL: distance from the right/left wall to the rail line (where the plumb line hangs). Out of limit when BELOW its",
       "- WR/WL: side clearance between the car block (BKS + 2×RAIL) and the right/left wall. Out of limit when BELOW its")]),
    # ── H3 · el PDF del cliente
    ("la nota del muro bajo la matriz", UR,
     [('            story += [_sp(2), Paragraph(esc_pdf(texto_muro(_muro, best)), styles["USmall"])]', "            pass")]),
    # ── H11 · los dibujos y el glosario
    ("⚠️ el hueco de la planta con el bloque", DG,
     [("    ancho_int = wl + sep_rieles + wr               # v681 · entre líneas de riel, no el bloque",
       "    ancho_int = wl + cab_w + wr")]),
    ("la apertura desde el borde del bloque", DG,
     [("    dx0, dx1 = x_rl + ol * esc, x_rr - orr * esc", "    dx0, dx1 = cx0 + ol * esc, cx0 + (cab_w - orr) * esc")]),
    ("la isométrica con el bloque", DG, [("    W  = wl + (bks + rail) + wr", "    W  = wl + cab_w + wr")]),
    ("el glosario vuelve al bloque", UR,
     [('("WR / WL", d("Distance from the right / left wall to the rail line (where the plumb line hangs).")),',
       '("WR / WL", d("Clearance between the car block and the right / left wall.")),')]),
    # ── el informe interno
    ("CUT OR solo sin muro (informe interno)", RP,
     [('            sol_df.insert(3, "CUT OR", [', '            if not wall_limiting: sol_df.insert(3, "CUT OR", ['),
      ('            sol_df.insert(7, "CUT OL", [', '            if not wall_limiting: sol_df.insert(7, "CUT OL", [')]),
    ("una etiqueta en español otra vez", RP,
     [('Paragraph(_d("Limiting wall?"),            styles["Normal2"]),',
       'Paragraph("Pared limitante?",              styles["Normal2"]),')]),
    # ── H4
    ("⚠️ la parada imposible no para el cálculo", CAL, [("        if _n and not 1 <= _s <= _n:", "        if False:")]),
    ("…ni se dice junto al campo", SU,
     [('            if int(st.session_state.get("cfg_wall_stop", 1) or 1) > _ns_ws:', "            if False:")]),
    # ── H13 / H12
    ("la equivalencia olvida el muro", SCA,
     [('        out["cfg_wall_yn"] = "Y" if _si(cfg["WALL_LIMITING"]) else "N"', "        pass")]),
    ("⚠️ reabrir no deja la configuración", PU,
     [('    st.session_state["_cfg_pendiente_sv"] = cfg_de_params(params)', "    pass")]),
    ("reabrir no elige la obra", PU, [("    st.session_state[\"pl_prj_sv\"] = f\"{prj.get('Name')} ({pid})\"", "    pass")]),
    ("reabrir no lleva al Survey", PU,
     [('                    st.session_state["_admin_nav_pending"] = ("herramientas", "📐 Survey")\n                    st.rerun()',
       '                    st.success("Loaded.")')]),
    ("⚠️ el Survey no aplica la configuración pendiente", SU,
     [('    for _k, _v in (st.session_state.pop("_cfg_pendiente_sv", None) or {}).items():\n        st.session_state[_k] = _v',
       '    st.session_state.pop("_cfg_pendiente_sv", None)')]),
    # ── H5
    ("las filas vuelven a 0…NS−1", SU, [('        _df_ed.index = pd.RangeIndex(1, len(_df_ed) + 1, name=t("Stop"))', "        pass")]),
    ("la matriz guardada se queda con el índice 1…NS", SU,
     [("        st.session_state.survey_df = edited_df.reset_index(drop=True)",
       "        st.session_state.survey_df = edited_df.copy()")]),
    # ── H12b / H2 / H16 / la tabla de la solución
    ("el cálculo sin MODELO", SU, [('        all_params["MODELO"]        = st.session_state.get("modelo", "")', "        pass")]),
    ("la obra elegida no da el modelo", SU, [('            st.session_state["modelo"]    = str(_prj_sv.get("Model", ""))      # v681 · H12b', "            pass")]),
    ("⚠️ al guardar, sin la identidad de la obra de destino", SU,
     [('                        ap.update({"PROYECTO": str(_prj.get("Name", "")), "CLIENTE": str(_prj.get("Client", "")),',
       '                        dict({"PROYECTO": str(_prj.get("Name", "")), "CLIENTE": str(_prj.get("Client", "")),')]),
    ("el historial con el FB del barrido", SU,
     [('                                           "fb": _best.get("fb_applied", _best.get("fb")),',
       '                                           "fb": _best.get("fb"),')]),
    ("la tabla de la solución sin los parámetros (el muro como corte)", SU,
     [('_cps = {c["piso"]: c for c in _cpp(limits, sol, all_params)}', '_cps = {c["piso"]: c for c in _cpp(limits, sol)}')]),
    ("la tabla de la solución sin la nota del muro", SU,
     [('st.caption(t(":material/block: {x}", x=_txm(_mdf(all_params), sol)))', "pass")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", DG,
           [("# línea del riel izquierdo (WL llega aquí)", "# (control) línea del riel izquierdo (WL llega aquí)")])


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
