# -*- coding: utf-8 -*-
"""Bateria de roturas de v579 (Finance → Profitability, probada acción por acción). ⚠️ Verde
de BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales
(v570). `--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v579"
PU = "core/projects_ui.py"
FI = "core/finance.py"
TB = "core/tabla.py"
TOPE_S = 300

ROTURAS = [
    ("⚠️ «sin ganancia» vuelve a decidirse por el % de mano de obra (cuenta la fija)", FI,
     [('                     "a_costo": _mod == "a_costo",\n',
       '                     "a_costo": rev["margen_pct"] <= 0,\n')]),
    ("⚠️ el Resumen vuelve a contar «No margin» por el %", PU,
     [('                   if r.get("a_costo")]\n', '                   if P._num(r.get("margen")) <= 0]\n')]),
    ("el margen se calcula sobre el costo", FI,
     [('                     "margen_ing": (round(100.0 * rev["ganancia"] / ingreso, 1)\n',
       '                     "margen_ing": (round(100.0 * rev["ganancia"] / max(costo, 1), 1)\n')]),
    ("⚠️ la tabla vuelve al % de mano de obra (la fija a 0.0 %)", PU,
     [("""                "Margin":     (f"{r['margen_ing']:.1f}%" if r.get("margen_ing") is not None else "—"),\n""",
       """                "Margin":     f"{r['margen']:.1f}%",\n""")]),
    ("⚠️ quien va a costo con ganancia por hora deja de saberse", FI,
     [('                                          if str(_mod).startswith("rubro") else [])})\n',
       '                                          if False else [])})\n')]),
    ("…o la pantalla no lo avisa", PU,
     [("    if _parc:\n        try:\n            from core import auth as _A\n",
       "    if False:\n        try:\n            from core import auth as _A\n")]),
    ("…o lo avisa con los logins", PU,
     [('                         + ", ".join(_nom.get(u, u) for u in r["a_costo_personas"]))\n',
       '                         + ", ".join(u for u in r["a_costo_personas"]))\n')]),
    ("los avisos vuelven a ser texto (sin botón a la obra)", PU,
     [('        _botones_obras([(r["id"], _rot(r)) for r in _m0], "rentmar", "💰 Costos")\n', "")]),
    ("⚠️ `tabla.cfg` vuelve a pisar la etiqueta traducida (cabeceras en español)", TB,
     [('            if _b and isinstance(_v, dict) and _v.get("label") is None:\n',
       "            if False:\n")]),
    ("una cabecera de Profitability vuelve sin etiqueta", PU,
     [('                    "Revenue":    st.column_config.NumberColumn(t("Est. revenue"), format="dollar"),\n',
       '                    "Revenue":    st.column_config.NumberColumn(format="dollar"),\n')]),
    ("⚠️ el dinero vuelve sin céntimos", PU,
     [('                    "Cost":       st.column_config.NumberColumn(t("Cost"), format="dollar"),\n',
       '                    "Cost":       st.column_config.NumberColumn(t("Cost"), format="$%,d"),\n')]),
    ("el proyecto deja de ir fijado", PU,
     [('                    "Proyecto":   st.column_config.TextColumn(t("Project"), pinned=True),\n',
       '                    "Proyecto":   st.column_config.TextColumn(t("Project")),\n')]),
    ("una obra con nombre repetido pierde su ID", PU,
     [("""        return f"{r['nombre']} ({r['id']})" if _rep[r["nombre"]] > 1 else r["nombre"]\n""",
       """        return r["nombre"]\n""")]),
    ("las cifras vuelven a no hacer nada", PU,
     [('                    st.session_state["_rent_orden"] = _ir\n', "                    pass\n")]),
    ("…o el orden pedido no se aplica", PU,
     [('    if _campo not in ("costo", "ingreso", "ganancia", "facturado"):\n', "    if True:\n")]),
    ("⚠️ «To invoice» deja de abrir lo pendiente", PU,
     [('                    st.session_state["_rent_vista"] = "pdt" if _abre else None\n',
       '                    st.session_state["_rent_vista"] = "pdt"\n')]),
    ("…o lo pendiente ya no prepara la factura", PU,
     [('                        _ir_a_facturar(r["id"], grupo)\n', "")]),
    ("la ganancia negativa no se pone roja", PU,
     [('        _cg = T.ROJO if _tot["ganancia"] < 0 else T.VERDE\n', "        _cg = T.VERDE\n")]),
    ("las cifras vuelven a partirse fila a fila", PU,
     [('    st.markdown(T.por_fila("cpx_rent_kpis", 3), unsafe_allow_html=True)\n',
       '    st.markdown(T.dos_por_fila("cpx_rent_kpis"), unsafe_allow_html=True)\n')]),
    ("⚠️ un toque en la tabla no abre la obra", PU,
     [("        if _fs and 0 <= _fs[0] < len(_orden):\n", "        if False:\n")]),
    ("…o la tabla no cambia de clave (reabriría la misma)", PU,
     [('            st.session_state["_rent_tbl_gen"] = _gen + 1\n', "")]),
    ("el desplegable vuelve sin clave", PU,
     [('"no invoicing)", n=len(_sin)), key="exp_rent_sin"):\n', '"no invoicing)", n=len(_sin))):\n')]),
    ("la vacía vuelve sin salida", PU,
     [('        if st.button(t(":material/folder: Go to Projects"), key="rent_ir_proy"):\n'
       '            _ir_a("proyectos", "📊 Proyectos")\n', "")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("def render_group_profitability(grupo: str):\n",
             "def render_group_profitability(grupo: str):   # (control)\n")])


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
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc))
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
