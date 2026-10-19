# -*- coding: utf-8 -*-
"""Bateria de roturas de v589 (Tools → Survey). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que
cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v589"
SU = "core/survey_ui.py"
PL = "core/plan_ui.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ los avisos de parámetros vuelven al español", "core/calculations.py",
     [('            issues.append(t("{k} must be greater than 0 (now {v}).", k=k, v=v))\n',
       '            issues.append(f"{k} debe ser > 0 (actual: {v})")\n')]),
    ("el registro del optimizador vuelve a «Apertura tapada»", "core/optimizer.py",
     [('                    "reason":           t("Opening covered: |RL|={rl} > FRAME={f}",\n',
       '                    "reason":           t("Apertura tapada: |RL|={rl} > FRAME={f}",\n')]),
    ("⚠️ el diagrama de plomada vuelve a «componentes»", "core/plumb.py",
     [("""                 f'{_d("components {x}", x=_n(bsc.get("bs_componentes")))}</text>')\n""",
       """                 f'componentes {_n(bsc.get("bs_componentes"))}</text>')\n""")]),
    ("…y a «lado Omega»", "core/plumb.py",
     [("""                 f'{_d("Omega side: {x}", x=_n(disp.get("omega_sacrificio")))}</text>')\n""",
       """                 f'lado Omega: {_n(disp.get("omega_sacrificio"))}</text>')\n""")]),
    ("⚠️ la tabla de plomada vuelve a «Línea»", "core/tabla.py",
     [('    "Línea": "Line",\n', "")]),
    ("el cronograma vuelve a «Peso (%)»", "core/tabla.py",
     [('    "Peso (%)": "Weight (%)",\n', "")]),
    ("⚠️ el PDF técnico vuelve a «Medida» / «Distancia (mm)»", "core/report.py",
     [('for h in [_d("Measurement"), _d("Distance (mm)")]]', 'for h in ["Medida", "Distancia (mm)"]]')]),
    ("los campos medidos vuelven a una fila de seis", SU,
     [("            cols = st.columns(3)\n", "            cols = st.columns(len(USER_ONLY))\n"),
      ("                cols[j % 3].number_input(\n", "                cols[j].number_input(\n")]),
    ("vuelve «Number of stops (NS)» (partía)", SU,
     [('        sc1.number_input(t("Stops (NS)"), min_value=2, max_value=50, step=1, key="ns",\n',
       '        sc1.number_input(t("Number of stops (NS)"), min_value=2, max_value=50, step=1, key="ns",\n')]),
    ("la casilla del Excel vuelve a la larga (se cortaba)", SU,
     [('        _imp_todo = sc2.checkbox(t("Also load its parameters"),\n',
       '        _imp_todo = sc2.checkbox(t("Also restore parameters and configuration from the Excel file"),\n')]),
    ("vuelve «8 warning(s)»", SU,
     [('            with st.expander(t(":material/warning: 1 warning in the parameters") if len(_iss0) == 1 else\n'
       '                             t(":material/warning: {n} warnings in the parameters", n=len(_iss0)),\n',
       '            with st.expander(f":material/warning: {len(_iss0)} warning(s) in the parameters",\n')]),
    ("⚠️ resultados sin cálculo vuelven a pintar las cuatro cabeceras", SU,
     [('                st.session_state["_fase_pending"] = _FASE_DATOS\n                st.rerun()\n            return\n',
       '                st.session_state["_fase_pending"] = _FASE_DATOS\n                st.rerun()\n')]),
    ("⚠️ el selector vuelve a ofrecer todas las obras", PL,
     [("    opciones = [SIN_PROYECTO] + [k for k, p in idmap.items() if es_de_herramientas(p) or k == _ya]\n",
       "    opciones = [SIN_PROYECTO] + list(idmap.keys())\n")]),
    ("…o deja de quitar las completadas", PL,
     [('    return str((prj or {}).get("Status", "")) not in ("Completed", "Cancelled")\n',
       '    return str((prj or {}).get("Status", "")) not in ("Cancelled",)\n')]),
    ("…o la ya elegida desaparece de golpe", PL,
     [("if es_de_herramientas(p) or k == _ya]", "if es_de_herramientas(p)]")]),
    ("⚠️ el aviso sin plano vuelve a «My company»", PL,
     [('                     ":material/attach_file: Files and every tool will use it — or upload the PDF "\n',
       '                     ":material/build: My company → open the project → :material/attach_file: Files and every tool will use it — or upload the PDF "\n')]),
    ("el botón «Open the project's Files» deja de abrir Files", PL,
     [('            st.session_state["_prj_sec_pending"] = "📎 Archivos"\n', "")]),
    ("⚠️ vuelve el «📍» del enlace (dos iconos)", "core/maps.py",
     [('    return f"[{lbl}]({url})"\n', '    return f"[📍 {lbl}]({url})"\n')]),
    ("un sitio pinta el enlace sin su icono", "core/clientes_ui.py",
     [('            st.markdown(":material/place: " + maps.maps_link_md(f.get("Address"), t("See the address on the map")))\n',
       '            st.markdown(maps.maps_link_md(f.get("Address"), t("See the address on the map")))\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PL,
           [("def es_de_herramientas(prj: dict) -> bool:\n", "def es_de_herramientas(prj: dict) -> bool:   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
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
