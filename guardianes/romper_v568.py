# -*- coding: utf-8 -*-
"""Bateria de roturas de v568. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Finance → Expenses en producción.
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
G = "verif_v568"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"
FI = "core/finance.py"
TH = "core/theme.py"
EX = "core/expenses.py"
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
    # ── el motor ──
    ("⚠️ la compra de la OFICINA sale como «sin obra»", EX,
     [('incluir_internos=True)}\n    out = [dict(r) for r in _records()',
       'incluir_internos=False)}\n    out = [dict(r) for r in _records()')]),
    ("⚠️ se puede asignar a una obra de OTRA empresa", EX,
     [('    if not prj or str(prj.get("Group", "")) != str(grupo):\n'
       '        return False, t("That job is not in this company.")\n', "")]),
    ("⚠️ se mueve una compra que YA era de una obra", EX,
     [('        if str(r.get("ProjectID", "")) in _ids:\n'
       '            return False, t("That purchase already belongs to a job.")\n', "")]),
    ("vuelve «Recibo agregado»", EX,
     [('return True, t("Receipt added ({x}).").replace("{x}", f"{_num(valor):,.2f}")',
       'return True, f"Recibo agregado ({_num(valor):.2f})."')]),
    # ── las cifras ──
    ("⚠️ «Forecast» vuelve a sumar el coste de HOY de obras sin avance", PU,
     [('    _con_prev = [f for f in filas if f["proyectado"] is not None]\n',
       '    _con_prev = [dict(f, proyectado=f["proyectado"] or f["total"]) for f in filas]\n')]),
    ("«% used» vuelve a «0%»", PU,
     [('        return "—" if p is None else (f"{p:.1f}%" if p < 10 else f"{p:.0f}%")\n',
       '        return "—" if p is None else f"{p:.0f}%"\n')]),
    # ── las compras sin obra ──
    ("⚠️ las compras sin obra dejan de listarse", PU,
     [("            _orf = E.huerfanos(grupo)\n", "            _orf = []\n")]),
    ("⚠️ «Assign» deja de escribir", PU,
     [("        _ok, _msg = E.asignar_proyecto(_pend[0], _pend[1], grupo)\n",
       '        _ok, _msg = True, ""\n')]),
    ("«Assign» activo sin obra elegida", PU,
     [('key=f"ge_huerf_asg_{_gid}", disabled=not _dest)', 'key=f"ge_huerf_asg_{_gid}", disabled=False)')]),
    # ── tablas ──
    ("⚠️ el estado vuelve al español", PU,
     [('                return "🔴 " + t("over")\n', '                return "sobre"\n')]),
    ("el coste vuelve sin $", PU,
     [('"Costo":        st.column_config.NumberColumn(t("Cost"), format="$%,.2f"),',
       '"Costo":        st.column_config.NumberColumn(t("Cost")),')]),
    ("⚠️ la tabla vuelve a pedir casilla + «Open»", PU,
     [('selection_mode="single-cell", key=f"ge_tbl_{_gen}",', 'selection_mode="single-row", key=f"ge_tbl_{_gen}",')]),
    ("la obra vuelve a abrirse en Status (no en Costs)", PU,
     [('_tabla_abre_obra(_gev, con_pres, "_ge_tbl_gen", "💰 Costos")',
       '_tabla_abre_obra(_gev, con_pres, "_ge_tbl_gen", "📊 Estado")')]),
    ("la obra sin presupuesto no se abre en Data", PU,
     [('_tabla_abre_obra(_ev2, sin_pres, "_ge_sin_gen", "✏️ Datos")',
       '_tabla_abre_obra(_ev2, sin_pres, "_ge_sin_gen", "💰 Costos")')]),
    # ── tarjetas y avisos activos ──
    ("⚠️ «Over budget» deja de abrir su lista", PU,
     [('                if _s in ("sobrep", "comp"):\n'
       '                    st.session_state["_ge_kpi"] = None if _sel == _s else _s\n',
       '                if False:\n                    pass\n')]),
    ("«Overhead spend» deja de llevar a Locations", PU,
     [('                if _s == "int":\n                    _ir_a("proyectos", "🏢 Localizaciones")\n', "")]),
    ("las cifras de la tabla dejan de bajar la vista a ella", PU,
     [('                    st.session_state["_ge_ir_tabla"] = True\n', "                    pass\n")]),
    ("⚠️ el aviso de obras pasadas pierde sus botones", PU,
     [('        _botones_obras([(f["id"], f["nombre"]) for f in filas if f["over"]], "geerr")\n', "")]),
    # ── CSV, disposición y textos ──
    ("el CSV vuelve a cabeceras en español", PU,
     [('        "Project": f["nombre"], "Purchases": f["compras"], "Labour": f["mano_obra"],',
       '        "Proyecto": f["nombre"], "Purchases": f["compras"], "Labour": f["mano_obra"],')]),
    ("el CSV vuelve a «gastos_…»", PU,
     [('file_name=f"expenses_{grupo}.csv"', 'file_name=f"gastos_{grupo}.csv"')]),
    ("desaparecen los 2 por fila en estrecho", PU,
     [('"@container (max-width:700px){.st-key-cpx_ge_kpis', '"@container (max-width:1px){.st-key-cpx_ge_kpis')]),
    ("vuelven las tarjetas en UNA fila (la última se estira)", PU,
     [("for c, k in zip(st.columns(4), _K[_i0:_i0 + 4])]:",
       "for c, k in zip(st.columns(len(_K)), _K[_i0:_i0 + len(_K)])]:")]),
    ("un aviso vuelve a una f-string sin `t()`", PU,
     [('st.error(t(":material/block: **{n} project(s) already over budget:**").replace("{n}", str(n_over)))',
       'st.error(f":material/block: **{n_over} project(s) already over budget:**")')]),
    # ── la sonda de verif_v313, ARREGLADA: ahora ve un nombre libre en `render_pnl` ──
    ("⚠️ un nombre libre en render_pnl (antes verif_v313 no miraba esa función)", PU,
     [('t("No margin"), _n_obras(len(_sinmar))', 't("No margin"), _n_obrass(len(_sinmar))')],
     "verif_v313"),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [('    """💰 Gastos del grupo (v568, probada acción por acción).',
                 '    """💰 Gastos del grupo (v568, probada acción por acción). (control)')])

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
