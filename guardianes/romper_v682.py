# -*- coding: utf-8 -*-
"""Batería de roturas de v682. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v682"
TOPE_S = 600
RC, SU, PD, PL, BC, HU = ("core/rail_cut_ui.py", "core/survey_ui.py", "core/plan_data.py", "core/plumb_ui.py",
                          "core/buffer_cut_ui.py", "core/home_ui.py")

ROTURAS = [
    ("⚠️ Rieles: el negativo sin aviso en pantalla", RC,
     [("            if _neg:\n                st.warning(t(\":material/warning: A negative value", "            if False:\n                st.warning(t(\":material/warning: A negative value")]),
    ("…ni en el PDF", RC, [("it. Check the measurement on site, and the sub-case (above or below the FFL).\")] if _neg else []))",
                           "it. Check the measurement on site, and the sub-case (above or below the FFL).\")] if False else []))")]),
    ("…ni en lo guardado", RC, [("d(\"lift {i} {r}\", i=i, r=r) for i, r, _v in _neg)) if _neg else \"\"),",
                                "d(\"lift {i} {r}\", i=i, r=r) for i, r, _v in _neg)) if False else \"\"),")]),
    ("⚠️ el plano vuelve a «drawing.pdf»", SU, [("_n_pl = f\"Drawing_{_nom_f}.pdf\"", "_n_pl = \"drawing.pdf\"")]),
    ("la matriz vuelve a «survey_matrix.csv»", SU, [("_n_mx = f\"Survey_matrix_{_nom_f}_{_marca_f}.csv\"", "_n_mx = \"survey_matrix.csv\"")]),
    ("el informe vuelve a «client_report.pdf»", SU, [("_n_ic = f\"Client_report_{_nom_f}_{_marca_f}.pdf\"", "_n_ic = \"client_report.pdf\"")]),
    ("⚠️ el plano se vuelve a archivar aunque la obra ya tenga uno", SU, [("if pb and not _ya_plano:", "if pb:")]),
    ("la oficina no sabe que sustituye el Survey", SU,
     [("if not _es_campo and _prj is not None and projects_data.tiene_survey(_prj):", "if False:")]),
    ("vaciar el Survey vuelve a callar", SU,
     [("            flash.info(t(\":material/cleaning_services: Survey cleared:", "            (t(\":material/cleaning_services: Survey cleared:")]),
    ("«Riel» otra vez", PD, [("(t(\"Car guide rail\"), riel)", "(\"Riel\", riel)")]),
    ("«RAIL (altura)» otra vez", PD, [("(t(\"RAIL (tooth height)\"), ralt_txt)", "(\"RAIL (altura)\", ralt_txt)")]),
    ("⚠️ la Plomada sin la plantilla del Survey", PL,
     [("            st.session_state[\"plb_lt\"] = float(_sv_prj[\"LengthTemplate\"])", "            pass")]),
    ("la Plomada pisa lo tecleado", PL,
     [("if float(st.session_state.get(\"plb_lt\") or 0) <= 0 and float(_sv_prj.get(\"LengthTemplate\") or 0) > 0:",
       "if float(_sv_prj.get(\"LengthTemplate\") or 0) > 0:")]),
    ("la Plomada sin el BSR del Survey", PL,
     [("            st.session_state[\"_plb_bsr_sv\"] = float(_sv_prj[\"BSR\"])", "            st.session_state[\"_plb_bsr_sv\"] = 0.0")]),
    ("la tabla de BSR no usa el BSR pendiente del Survey", PL,
     [("        if not _prev and st.session_state.get(\"_plb_bsr_sv\"):", "        if False:")]),
    ("la Plomada no lo dice", PL,
     [("if float(_sv_prj.get(\"LengthTemplate\") or 0) > 0 or float(_sv_prj.get(\"BSR\") or 0) > 0:", "if False:")]),
    ("Buffers «check» en minúscula", BC, [("d(\"Check\") if b[\"warn\"]", "d(\"check\") if b[\"warn\"]")]),
    ("⚠️ «Last used» sin el ID", HU, [("_p = f\"{_nm_u} ({_pid_u})\" if _nm_u else _pid_u", "_p = _nm_u or _pid_u")]),
    ("⚠️ las soluciones equivalentes sin agrupar", "core/optimizer.py",
     [("    best_solutions = [s for s in best_solutions if _una[(round(s[\"rl\"], 3), round(s[\"fb_applied\"], 3))] is s]\n", "")]),
    ("de las equivalentes, la de MENOR fb del barrido", "core/optimizer.py",
     [("        if k not in _una or s[\"fb\"] > _una[k][\"fb\"]:", "        if k not in _una or s[\"fb\"] < _una[k][\"fb\"]:")]),
    ("la nota del muro vuelve a la parte «extra»", "core/interpretation.py",
     [("% (muro[\"stop\"], lado, abs(_num(b.get(\"fb_applied\", b.get(\"fb\"))))))", "% (muro[\"stop\"], lado, empuje_extra(b)))")]),
    ("la matriz ajustada vuelve a 0…NS−1", SU,
     [("st.dataframe(_por_paradas(survey_adj_df).style", "st.dataframe(survey_adj_df.style")]),
    ("las soluciones vuelven a 0…NS−1", SU,
     [("st.dataframe(_por_paradas(sol_df).style", "st.dataframe(sol_df.style")]),
    ("_por_paradas sin numerar", SU,
     [("    v.index = pd.RangeIndex(1, len(v) + 1, name=t(\"Stop\"))\n", "")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PL,
           [("    # ⚠️ v682 · Lo que el Survey de la obra ya midió", "    # (control) ⚠️ v682 · Lo que el Survey de la obra ya midió")])


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
