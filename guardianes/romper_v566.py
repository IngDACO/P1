# -*- coding: utf-8 -*-
"""Bateria de roturas de v566. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Finance → Summary en producción.
Una rotura puede nombrar OTRO guardián (4º elemento): la clave de un desplegable con
condición la vigila verif_v547, no AppTest (que respeta `expanded` en la 1ª pasada).
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
G = "verif_v566"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"
FI = "core/finance.py"
TH = "core/theme.py"
RU = "core/roster_ui.py"
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
    ("⚠️ lo pendiente vuelve a ser solo lo emitido en el periodo", PU,
     [("    _dt = d if _desde is None else F.pnl(grupo)          # v566 · saldos a hoy\n",
       "    _dt = d\n")]),
    ("⚠️ un periodo vacío vuelve a dejar la pantalla en blanco", PU,
     [("    else:\n        _pnl_kpis(grupo, d, _desde, _hasta, _modo, F, T)\n",
       "        return\n    else:\n        _pnl_kpis(grupo, d, _desde, _hasta, _modo, F, T)\n")]),
    ("«See All» deja de cambiar el periodo", PU,
     [('            st.session_state["_pnl_per_pending"] = "Todo"\n', "")]),
    ("⚠️ el periodo deja de recordarse", PU,
     [('horizontal=True, key="cpxseg_pnl_per", label_visibility="collapsed",\n'
       '                    persist_state="session")',
       'horizontal=True, key="cpxseg_pnl_per", label_visibility="collapsed")')]),
    ("⚠️ vuelve la comparación con «los mismos días hacia atrás»", FI,
     [("    d0, h0 = periodo_comparable(desde, hasta, modo)          # v566\n",
       "    d0, h0 = periodo_anterior(desde, hasta)\n")]),
    ("las fechas de la comparación pierden el año", PU,
     [('_pie.append(t("compared with {a} → {b}").replace("{a}", _d0.strftime("%d/%m/%Y"))',
       '_pie.append(t("compared with {a} → {b}").replace("{a}", _d0.strftime("%d/%m"))')]),
    ("⚠️ «No rate» vuelve a contar solo el periodo", PU,
     [("            _ccp = F.conciliacion_mo(grupo) or {}\n", "            _ccp = _cc\n")]),
    ("vuelve «Hours with no payslip»", PU,
     [('t("Charged with no workday"),', 't("Hours with no payslip"),')]),
    ("«No margin» vuelve a decir «Invoiced at cost»", PU,
     [('st.caption(t("No profit set: they would be invoiced at cost (estimated profit $0). "',
       'st.caption(t("Invoiced at cost (estimated profit $0). "')]),
    ("⚠️ el signo vuelve DENTRO del importe («$-128»)", TH,
     [('    return ("-" if _neg else "") + ("\\\\" if escapar else "") + simbolo + _cifra\n',
       '    return ("\\\\" if escapar else "") + simbolo + ("-" if _neg else "") + _cifra\n')]),
    ("⚠️ «Income» deja de llevar a Invoices", PU,
     [('            if _s == "ing":\n                _ir_a("finanzas", "🧾 Facturas")\n', "")]),
    ("«What you pay» deja de abrir el desglose", PU,
     [('"comp" if _s == "cos" else "prj"', '"prj"')]),
    ("⚠️ la obra sin facturar deja de preparar SU factura", PU,
     [("                _ir_a_facturar(_pid, grupo)\n                st.rerun()\n\n    def _det_pagar():",
       "                st.rerun()\n\n    def _det_pagar():")]),
    ("⚠️ la persona sin tarifa deja de abrir su ficha", PU,
     [('                        st.session_state["gp_fichasel"] = f"{_nom} ({_cl[_nom]})"\n', "")]),
    ("la obra sin margen deja de abrir sus Costs", PU,
     [('_obras_botones(_sinmar, "pnlmar", "💰 Costos")', '_obras_botones(_sinmar, "pnlmar", None)')]),
    ("⚠️ vuelve «→ Ir a Facturas»", PU,
     [('if st.button(t("→ Go to {x}").replace("{x}", t(_dsub)), key=f"pnlgo_{_it[0]}",',
       'if st.button(f"→ Ir a {_it[7].split(chr(32), 1)[-1]}", key=f"pnlgo_{_it[0]}",')]),
    ("vuelve «Sobre ppto.»", PU,
     [('t("Over budget"), _n_obras(len(_over))', '"Sobre ppto.", _n_obras(len(_over))')]),
    ("⚠️ la cifra vuelve a la misma línea que la etiqueta", PU,
     [('_col.button(f"{_x[1]} {_x[2]}\\n\\n{_x[3]}", key=f"pnlind_{_x[0]}",',
       '_col.button(f"{_x[1]} {_x[2]} · {_x[3]}", key=f"pnlind_{_x[0]}",')]),
    ("desaparecen los 2 por fila en estrecho", PU,
     [('"@container (max-width:760px){"', '"@container (max-width:1px){"')]),
    ("una cabecera de By project vuelve a la clave en español", PU,
     [('"Facturado": st.column_config.NumberColumn(t("Invoiced"), format="dollar"),',
       '"Facturado": st.column_config.NumberColumn(format="dollar"),')]),
    ("el resultado vuelve al formato con el signo dentro", PU,
     [('"Resultado": st.column_config.NumberColumn(t("Result"), format="dollar"),',
       '"Resultado": st.column_config.NumberColumn(t("Result"), format="$%,.0f"),')]),
    # v568 · Gastos usa el mismo patrón en dos tablas: anclas con el contexto de By project
    ("la obra deja de ir fijada", PU,
     [('"Proyecto":  st.column_config.TextColumn(t("Project"), pinned=True)',
       '"Proyecto":  st.column_config.TextColumn(t("Project"))')]),
    ("las filas de By project dejan de abrir la obra", PU,
     [('} for r in rows]), hide_index=True, width="stretch", on_select="rerun",',
       '} for r in rows]), hide_index=True, width="stretch", on_select="ignore",')]),
    ("la tarjeta KPI vuelve a «vs. periodo anterior»", PU,
     [('+ t("{f} {p}% vs previous").replace("{f}", _f)', '+ t("{f} {p}% vs. periodo anterior").replace("{f}", _f)')]),
    ("una etiqueta de la conciliación pierde su `t()` (va por una tupla)", PU,
     [('(t("Charged to jobs (hours booked × rate)"), cc["cargado"], ""),',
       '("Charged to jobs (hours booked × rate)", cc["cargado"], ""),')]),
    ("las descripciones de Tools pierden su `t()`", HU,
     [('st.caption(t(_desc.get(_id, "")))', 'st.caption(_desc.get(_id, ""))')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [("    pantalla en blanco: lo pendiente sigue ahí (visto en el recorrido de Summary).",
                 "    pantalla en blanco: lo pendiente sigue ahí (visto en el recorrido de Summary). (control)")])


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
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

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
