# -*- coding: utf-8 -*-
"""Batería de roturas de v685. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v685"
TOPE_S = 300
CA, SU, EN, RP = "core/calculations.py", "core/survey_ui.py", "core/email_notify.py", "core/report.py"

ROTURAS = [
    # ── la matriz sin medir ──
    ("⚠️ un nivel a 0 cuenta como medido", CA,
     [("        if all(abs(_v) < 1e-9 for _v in _vals):", "        if False and all(abs(_v) < 1e-9 for _v in _vals):")]),
    ("una celda vacía (NaN) cuenta como medida", CA,
     [("            _vals.append(0.0 if _v != _v else _v)          # NaN (celda vacía) = sin medir",
       "            _vals.append(_v)")]),
    ("los tramos sin agrupar", CA,
     [("            _t.append(str(_ini) if _ini == _ant else \"%d–%d\" % (_ini, _ant))",
       "            _t.append(str(_ini) if _ini == _ant else \"%d, %d\" % (_ini, _ant))")]),
    ("⚠️ «Calculate» sin mirar la matriz (correo e interpretaciones sobre ceros)", SU,
     [("        issues = validate_inputs(all_params) + aviso_matriz(survey_original_input, SURVEY_COLS)",
       "        issues = validate_inputs(all_params)")]),
    ("el aviso temprano sin la matriz", SU,
     [("            _iss0 = validate_inputs(_ap0) + aviso_matriz(st.session_state.survey_df, SURVEY_COLS)   # v685",
       "            _iss0 = validate_inputs(_ap0)")]),
    ("⚠️ el chip vuelve a verde con la matriz a ceros", SU,
     [("        if _sin_med or _a_medias:\n            _falta = (", "        if False:\n            _falta = (")]),
    # ── B: medido a medias (lo destapó esta batería: el guardián se COLGABA) ──
    ("⚠️ una medida a 0 en un nivel medido pasa", CA, [("            out.append((i, _c0))", "            pass")]),
    ("OR/OL a 0 cuentan como medida que falta", CA,
     [("SIN_CERO = (\"WR\", \"WL\", \"FR\", \"FL\")", "SIN_CERO = (\"WR\", \"WL\", \"FR\", \"FL\", \"OR\", \"OL\")")]),
    ("⚠️ el aviso sin los niveles a medias", CA, [("    _med = celdas_a_cero(_filas, cols)", "    _med = []")]),
    ("el chip sin los niveles a medias", SU,
     [("                + ([t(\"{k} incomplete\", k=len(_a_medias))] if _a_medias else [])", "                + []")]),
    # ── B: el informe de gestión ──
    ("⚠️ H11 · WL/WR vuelven a la cara del bloque en el diagrama", RP,
     [("        \"    |<----- WL ----->@<-------- BKS + RAIL -------->@<----- WR ----->|\",",
       "        \"    |<-- WL -->|<-RAIL-|<---- BKS ---->|-RAIL->|<-- WR -->|\",")]),
    ("la sección transversal, en español", RP,
     [("        \"  Cross-section (top view, not to scale):\",", "        \"  Seccion transversal (vista superior, no proporcional):\",")]),
    ("el bloque del perfil, en español", RP,
     [("        \"    |        CAR BLOCK = TL                           |  |\",",
       "        \"    |        BLOQUE CABINA = TL                       |  |\",")]),
    ("⚠️ la cabecera de la tabla de la solución, en español", RP,
     [("                    _d(\"Column\"):       col,", "                    \"Columna\":       col,")]),
    ("el rango 1 del BSR vs BS, en español", RP,
     [("            _calc_block(_d(\"Range 1 — Zone ZB\"),", "            _calc_block(\"Rango 1 — Zona ZB\",")]),
    # ── «Rewrite the interpretation» ──
    ("⚠️ reescribe sin preguntar con cajas cambiadas", SU,
     [("                _edit_iu = _cajas_editadas(r) if interp_usr.get(\"_ok\") else []", "                _edit_iu = []")]),
    ("todas las cajas cuentan como cambiadas (pregunta siempre)", SU,
     [("        if v is not None and str(v).strip() != str(iu.get(k) or \"\").strip():", "        if v is not None:")]),
    ("reescribe en silencio", SU,
     [("                            flash.exito(t(\":material/smart_toy: Interpretation rewritten for the active solution: \"",
       "                            str(t(\":material/smart_toy: Interpretation rewritten for the active solution: \"")]),
    ("⚠️ «Keep my changes» reescribe igual", SU,
     [("                    if _rw2.button(t(\":material/undo: Keep my changes\"), key=\"sv_rw_no\", width=\"stretch\"):\n"
       "                        st.session_state.pop(\"_sv_rw_pide\", None)\n",
       "                    if _rw2.button(t(\":material/undo: Keep my changes\"), key=\"sv_rw_no\", width=\"stretch\"):\n"
       "                        st.session_state.pop(\"_sv_rw_pide\", None)\n"
       "                        st.session_state[\"_sv_rw_hacer\"] = r.get(\"_n\", 0)\n")]),
    ("la pregunta sin decir qué cajas", SU, [("                                 cajas=\", \".join(_edit_iu)))",
                                              "                                 cajas=\"\"))")]),
    # ── el correo interno ──
    ("⚠️ el correo vuelve a «Notificación de uso»", EN,
     [("Elevator Survey Analyzer — Usage notification</div>", "Elevator Survey Analyzer — Notificación de uso</div>")]),
    ("«Paso / Zona» otra vez", EN,
     [("f\"Step: {bs_result['step']} mm — Zone: {bs_result.get('range_name')} ⚠️\", True)",
       "f\"Paso: {bs_result['step']} mm — Zona: {bs_result.get('range_name')} ⚠️\", True)")]),
    ("la matriz del correo, en español", EN,
     [("SURVEY matrix entered (mm)</h3>", "Matriz SURVEY ingresada (mm)</h3>")]),
    ("el pie, en español", EN,
     [("        Automatic notification from COPEX Survey Analyzer.<br>",
       "        Notificación automática generada por COPEX Survey Analyzer.<br>")]),
    ("⚠️ «OFF per column» vuelve a ser el dict de Python", EN,
     [("          {row(\"OFF per column\",             _off_col)}",
       "          {row(\"OFF per column\",             str(best.get('off_by_col', {})))}")]),
    ("RL sin su sentido", EN,
     [("        rl_str = f\"{best['rl']:+.1f} mm\" + (f\" (to the {_sl.upper()})\" if _sl != \"none\" else \"\")",
       "        rl_str = f\"{best['rl']:+.1f} mm\"")]),
    ("FB sin su sentido", EN,
     [("(f\" (towards the {_sf.upper()})\" if _sf != \"none\" else \"\")", "(\"\")")]),
    ("el pie sin los adjuntos", EN, [("        {_adjuntos}\n", "        Survey matrix included above.\n")]),
    ("⚠️ el CSV vuelve a «Stop» 0…", EN, [("                _tab.index = range(1, len(_tab) + 1)", "                pass")]),
    ("el CSV vuelve a «survey_matrix.csv»", EN,
     [("                    filename=f\"Survey_matrix_{nombre_archivo(proyecto, 'project')}_\"\n"
       "                             f\"{clock.now().strftime('%Y-%m-%d_%H%M')}.csv\"\n",
       "                    filename=\"survey_matrix.csv\"\n")]),
    ("el plano vuelve a «drawing.pdf»", EN,
     [("filename=pdf_name or f\"Drawing_{nombre_archivo(proyecto, 'project')}.pdf\"   # v685 · era «drawing.pdf»",
       "filename=pdf_name or \"drawing.pdf\"")]),
    ("un correo personal vuelve al código (repositorio público)", EN,
     [("Envía el resumen técnico a la dirección de `NOTIFY_TO` (secrets) via Gmail SMTP.",
       "Envía resumen técnico a alguien@gmail.com via Gmail SMTP.")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CA,
           [("    \"\"\"[1, 2, 3, 5, 7, 8] → «1–3, 5, 7–8».\"\"\"", "    \"\"\"(control) [1, 2, 3, 5, 7, 8] → «1–3, 5, 7–8».\"\"\"")])


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
