# -*- coding: utf-8 -*-
"""Bateria de roturas de v590 (lo visto verificando v589). ⚠️ Verde de BASE primero (v459) y
NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo
comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v590"
SU = "core/survey_ui.py"
PR = "core/projects.py"
TOPE_S = 900

ROTURAS = [
    ("⚠️ el recuento antes de borrar vuelve a pedir «Gastos»", PR,
     [('        for etiqueta, hoja, col in (("Expenses", _EX.SHEET, "ProjectID"),\n',
       '        for etiqueta, hoja, col in (("Expenses", "Gastos", "ProjectID"),\n')]),
    ("…o «Calculos»", PR,
     [('                                    ("Calculations", _TR.SHEET, "ProjectID"),\n',
       '                                    ("Calculations", "Calculos", "ProjectID"),\n')]),
    ("⚠️ una lectura vuelve a CREAR la pestaña que no conoce (cabecera `[]`)", PR,
     [("    return hojas.registros(title, _HEADERS_BY_TITLE.get(title)) or []\n",
       "    return hojas.registros(title, _HEADERS_BY_TITLE.get(title, [])) or []\n")]),
    ("la pantalla vuelve a pintar la clave en minúscula («documentos»)", "core/projects_ui.py",
     [("                                             + _ETQ_ASO.get(k, (k, k))[0 if v == 1 else 1]\n",
       "                                             + k.lower()\n")]),
    ("un nombre viejo de pestaña vuelve al código («Alarmas»)", "core/alerts.py",
     [("    return _records_cached(_libro_de(ALERTS_SHEET))",
       '    return _records_cached(_libro_de("Alarmas"))')]),
    ("⚠️ el aviso del cálculo vuelve a `st.success` (lo borra el `st.rerun()`)", SU,
     [('            flash.exito(t(":material/check_circle: Calculation and interpretation completed."))\n',
       '            st.success(t(":material/check_circle: Calculation and interpretation completed."))\n')]),
    ("⚠️ «sent by email» aunque el correo no salga", SU,
     [("        if _enviado:\n", "        if True:\n")]),
    ("⚠️ el destino de guardar deja de venir elegido", SU,
     [('                        st.session_state["sv_prj_sel"] = _lbl_dest\n', "")]),
    ("…o la obra del cálculo deja de guardarse", SU,
     [('            "prj_id":              str(st.session_state.get("_sv_prj_id", "") or ""),\n',
       '            "prj_id":              "",\n')]),
    ("⚠️ el destino vuelve a ofrecer obras cerradas", SU,
     [('                          if plan_ui.es_de_herramientas(p) or str(p.get("ID", "")) == _dest]\n',
       "                          if True]\n")]),
    ("sin obras abiertas, sin botón a Projects", SU,
     [('                    if st.button(t(":material/folder: Open Projects"), key="sv_ir_proyectos"):\n',
       "                    if False:\n")]),
    ("«Out of limit» deja de poner los pisos con problemas", SU,
     [('                            st.session_state["diag_modo"] = "With issues"\n', "")]),
    ("⚠️ el plano por piso vuelve a «nearest» (el título fuera de la vista)", SU,
     [('            _PU._bajar_a("cpx_sv_planta", "_bajar_cpx_sv_planta", bloque="start")\n',
       '            _PU._bajar_a("cpx_sv_planta", "_bajar_cpx_sv_planta")\n')]),
    ("`_bajar_a` ignora el bloque pedido", "core/projects_ui.py",
     [("            \"block:'\" + bloque + \"'});return;}\"",
       "            \"block:'nearest'});return;}\"")]),
    ("⚠️ vuelve «optimal solution(s)»", SU,
     [('                   else t("Found **{n} optimal solutions**", n=len(all_solutions)))\n',
       '                   else t("Found **{n} optimal solution(s)**", n=len(all_solutions)))\n')]),
    ("vuelve «activa»", SU,
     [('                            "": t("active") if k == _idx_act else "",',
       '                            "": "activa" if k == _idx_act else "",')]),
    ("⚠️ vuelve «EJES»", "core/diagrams.py",
     [('                        _d("AXIS OFFSET {x}→{s}", x=_mm(abs(d_ejes)), s=_lado),\n',
       '                        f"EJES {_mm(abs(d_ejes))}→{_lado}",\n')]),
    ("⚠️ el cajetín vuelve a cortar el nombre a 24", "core/diagrams.py",
     [("""             f'{texto_svg.cabe(proyecto or "COPEX", tw - 12, 7.5)}</text>')\n""",
       """             f'{(proyecto or "COPEX")[:24]}</text>')\n""")]),
    ("⚠️ el nombre deja de escaparse («&» rompe el SVG)", "core/texto_svg.py",
     [("    return escape(s)\n", "    return s\n")]),
    ("⚠️ el chip vuelve a «No drawing» con el plano de la obra", SU,
     [('             t(":green[:material/check_circle:] Drawing from the project") if _plano_sv else\n',
       '             t(":green[:material/check_circle:] Drawing from the project") if False else\n')]),
    ("⚠️ el riel fuera del catálogo vuelve a salir como `info`", SU,
     [('            (st.success if _m.startswith(":green[") else\n',
       '            (st.success if _m.startswith(":material/check_circle:") else\n'),
      ('             st.warning if _m.startswith(":orange[") else st.info)(_m)\n',
       '             st.warning if _m.startswith(":material/warning:") else st.info)(_m)\n')]),
    ("vuelve «(now 0.0)»", "core/calculations.py",
     [("            v = _mm(v)\n", "")]),
    ("el Excel vuelve a «Parada»", "core/excel_io.py",
     [('    headers = ["Stop"] + SURVEY_COLS\n', '    headers = ["Parada"] + SURVEY_COLS\n')]),
    ("⚠️ el PDF del CLIENTE vuelve a «value(s)»", "core/user_report.py",
     [('                d("The solution leaves {n} values out of limit that need attention "\n',
       '                d("The solution leaves {n} value(s) out of limit that need attention "\n')]),
    ("el PDF técnico vuelve a «value(s)»", "core/report.py",
     [('               else _d("{n} values out of limit", n=off_c)),\n',
       '               else _d("{n} value(s) out of limit", n=off_c)),\n')]),
    ("vuelve «matriz_survey.csv» en Files", SU,
     [('                                        fid = drive_store.upload(_pid, "survey_matrix.csv", csv,\n',
       '                                        fid = drive_store.upload(_pid, "matriz_survey.csv", csv,\n')]),
    ("vuelve «— see the sidebar»", SU,
     [('            st.info(t(":material/description: Data from: **{f}**.", f=pdf_file.name))\n',
       '            st.info(t(":material/description: Data from: **{f}** — see the sidebar.", f=pdf_file.name))\n')]),
    ("la franja de después de guardar vuelve a REPETIR el guardado", SU,
     [('        _c1.caption(t(":material/cleaning_services: This survey was cleared so the next one "\n',
       '        _c1.caption(t(":material/cleaning_services: Project updated with the survey. This survey was cleared so the next one "\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", "core/texto_svg.py",
           [("def cabe(texto, ancho_px: float, tam: float, negrita: bool = False) -> str:\n",
             "def cabe(texto, ancho_px: float, tam: float, negrita: bool = False) -> str:   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def _eol(txt, s):
    """⚠️ projects.py, diagrams.py, user_report.py y email_notify.py son CRLF (también en git):
    las anclas se escriben con «\\n» (como las lee check_anclas_roturas) y aquí se pasan a CRLF.
    Así la batería no reescribe el fichero entero con LF (el ruido de solo-CR de otras tandas)."""
    return s.replace("\n", "\r\n") if "\r\n" in txt else s


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        viejo, nuevo = _eol(txt, viejo), _eol(txt, nuevo)
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                viejo = _eol(txt, viejo)
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
