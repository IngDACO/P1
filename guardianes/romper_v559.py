# -*- coding: utf-8 -*-
"""Bateria de roturas de v559. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de la ficha de una obra en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v559"
PU = "core/projects_ui.py"
EX = "core/expenses.py"
DL = "core/daily_log_ui.py"
HO = "core/handover.py"
HU = "core/handover_ui.py"
TOPE_S = 600


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ «Delete» vuelve a borrar de un clic (sin preguntar)", PU,
     [("                st.session_state[_kc] = _id\n",
       '                st.session_state[f"_arch_borrar_{pid}"] = {"did": did, "nombre": e["nombre"]}\n')]),
    ("el borrado confirmado deja de ejecutarse", PU,
     [("    _pend = st.session_state.pop(_kb, None)\n    if _pend:\n",
       "    _pend = st.session_state.pop(_kb, None)\n    if False:\n")]),
    ("la tabla de archivos pierde la generación (la selección se cruzaría)", PU,
     [("key=f\"arch_tbl_{pid}_{st.session_state.get(f'_arch_gen_{pid}', 0)}\",",
       'key=f"arch_tbl_{pid}",')]),
    ("el selector de archivo deja de vaciarse al subir", PU,
     [('                    st.session_state[f"_updoc_gen_{pid}"] = _ug + 1\n', '')]),
    ("⚠️ Data: cambiar la gente deja de avisar «Not saved yet»", PU,
     [("        if set(asignados) != set(_actuales) or set(_ecerts) != set(_certs_act):\n",
       "        if False:\n")]),
    ("Data: los asignados vuelven a salir por login", PU,
     [("                                   format_func=lambda u: _nm_asig.get(u, u))",
       "                                   format_func=lambda u: u)")]),
    ("Data: la fecha de inicio vuelve al ISO", PU,
     [('            f_ini    = e1.date_input(t("Start date"), value=_a_fecha(prj.get("StartDate")),\n'
       '                                     format="DD/MM/YYYY")',
       '            f_ini    = e1.date_input(t("Start date"), value=_a_fecha(prj.get("StartDate")),\n'
       '                                     format="YYYY-MM-DD")')]),
    ("Data: el fin vuelve a la izquierda", PU,
     [("            f_ini    = e1.date_input(", "            f_ini    = e2.date_input("),
      ("            f_fin    = e2.date_input(", "            f_fin    = e1.date_input(")]),
    ("Data: el estado manual vacío vuelve a «Choose an option»", PU,
     [('                                   format_func=lambda v: _etq(v) if str(v or "").strip()\n'
       '                                   else t("— automatic (from the progress) —"), index=_emi)',
       '                                   format_func=_etq, index=_emi)')]),
    ("Data: el aviso de contacto vuelve a dar el login", PU,
     [("                sin_contacto.append(_nm.get(u, u))\n",
       "                sin_contacto.append(u)\n")]),
    ("Data: «until» vuelve al ISO", PU,
     [("{t('until')} {_fmt_fecha(_fin)}", "{t('until')} {_fin}")]),
    ("⚠️ Status: el cronograma vuelve a UN lienzo de 1280", PU,
     [('    _lienzos = ((700, "(max-width:819px)"), (1000, "(min-width:820px) and (max-width:1159px)"),\n'
       '                (1280, "(min-width:1160px)"))',
       '    _lienzos = ((1280, "all"),)')]),
    ("⚠️ Status: la cifra larga vuelve a partirse (sin tamaño propio)", PU,
     [("    if _lv >= 11:\n", "    if False:\n"), ("    elif _lv >= 7:\n", "    elif False:\n")]),
    ("Status: «Who has worked here» vuelve a dar logins", PU,
     [('    st.dataframe(pd.DataFrame([{"Persona": _nm.get(x["usuario"], x["usuario"]),',
       '    st.dataframe(pd.DataFrame([{"Persona": x["usuario"],')]),
    ("historial: quién vuelve a ser el login", PU,
     [('            _quien = _nm.get(_u, _u) or "—"\n', '            _quien = _u or "—"\n')]),
    ("⚠️ historial: el avance 0 vuelve a «(empty)»", PU,
     [('        if v is None or str(v).strip() == "":\n',
       '        if not v or str(v).strip() == "":\n')]),
    ("ganancia: el login deja de ir oculto", PU,
     [('                "Usuario": None,\n', '')]),
    ("ganancia: se guarda por el NOMBRE (lo que puede repetirse)", PU,
     [("    _nuevo = {str(_ed.iloc[i][\"Usuario\"]): ", "    _nuevo = {str(_ed.iloc[i][\"Persona\"]): ")]),
    ("vuelve «(decision from v360)»", PU,
     [('                 "Materials are invoiced at cost.")',
       '                 "Materials are invoiced at cost (decision from v360).")')]),
    ("⚠️ Costs: vuelve el «Everything invoiced» con algo pendiente", PU,
     [("    if pend > 0:\n        return\n", "    if False:\n        return\n")]),
    ("Costs: la 5ª tarjeta vuelve a caer sola", PU,
     [("<style>.cpx-kpis-cst .cpx-kpi{flex:1 1 110px}</style>", "")]),
    ("Costs: «Set the budget in Data» deja de llevar a Data", PU,
     [('            st.session_state["_prj_sec_pending"] = "✏️ Datos"\n', '            pass\n')]),
    ("la ficha deja de atender el cambio de pestaña pedido", PU,
     [('        st.session_state["cpxseg_prj_sec"] = _psp\n', '        pass\n')]),
    ("Costs: «Go to Users» deja de llevar a Users", PU,
     [('                                        key=f"cst_ir_users_{pid}", type="tertiary"):\n'
       '                _ir_a("planificacion", "👷 Usuarios")\n',
       '                                        key=f"cst_ir_users_{pid}", type="tertiary"):\n'
       '                pass\n')]),
    ("Costs: la tarifa vuelve sin «$»", PU,
     [('                "Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f"),\n', '')]),
    ("pedidos: vuelve «llega»", PU,
     [("_lin += f\" · due {_fesp.strftime('%d/%m')}\"", "_lin += f\" · llega {_fesp.strftime('%d/%m')}\"")]),
    ("Files: vuelve «Matriz survey»", PU,
     [('"matriz_survey": "Survey matrix"', '"matriz_survey": "Matriz survey"')]),
    ("⚠️ gasto: las marcas del eje vuelven a repetirse", EX,
     [("fill=\"#667080\">{_money(v, _dec)}</text>')", "fill=\"#667080\">{_money(v)}</text>')")]),
    ("gasto: el subtítulo vuelve al ISO", EX,
     [("{_dmy(fechas[0])} → {_dmy(fechas[-1])}", "{fechas[0]} → {fechas[-1]}")]),
    ("gasto: vuelve «Presup.»", EX,
     [('font-weight="bold">{t("Budget")} {_money(pres)}</text>', 'font-weight="bold">Presup. {_money(pres)}</text>')]),
    ("⚠️ partes: el autor vuelve a ser el login", DL,
     [("theme.chip(f\"{_dmy(_dia)} · {_nombre(_autor) if _autor != '—' else _autor}\"",
       "theme.chip(f\"{_dmy(_dia)} · {_autor}\"")]),
    ("partes: la fecha vuelve al ISO", DL,
     [("theme.chip(f\"{_dmy(_dia)} · ", "theme.chip(f\"{_dia} · ")]),
    ("partes: vuelve «1 logs»", DL,
     [('    _a = t("1 log") if n == 1 else t("{n} logs", n=n)\n', '    _a = t("{n} logs", n=n)\n')]),
    ("⚠️ expediente: vuelve el login («no certificate: admin2»)", HO,
     [('            _p.append("no certificate: %s" % ", ".join(sorted(_nom(ctx, u) for u in sin)))\n',
       '            _p.append("no certificate: %s" % ", ".join(sorted(sin)))\n')]),
    ("expediente: la pantalla deja de pasar los nombres", HU,
     [('        "nombres": nombres,\n', '')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [("    # v559 · por su NOMBRE: salían «Admin2» y «campo000» (Admin2 es «Bobo»).",
                 "    # v559 · por su NOMBRE: salían «Admin2» y «campo000» (Admin2 es «Bobo»). (control)")])


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


# Opcional: `romper_v559.py <texto> …` repite SOLO las roturas cuyo nombre contenga alguno
# de esos textos (para re-correr las que escaparon tras reforzar el guardián: añadir
# comprobaciones no puede hacer que escape una que ya se cazaba).
if len(sys.argv) > 1:
    ROTURAS = [r for r in ROTURAS if any(a in r[0] for a in sys.argv[1:])]
    print("SOLO %d rotura(s): %s" % (len(ROTURAS), "; ".join(r[0] for r in ROTURAS)))

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
for desc, rel, cambios in ROTURAS:
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
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc), flush=True)

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
