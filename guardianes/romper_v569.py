# -*- coding: utf-8 -*-
"""Bateria de roturas de v569. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Finance → Invoices en producción.
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
G = "verif_v569"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"
FI = "core/finance.py"
TH = "core/theme.py"
EX = "core/expenses.py"
IU = "core/invoices_ui.py"
IP = "core/invoice_pdf.py"
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
    # ── anular ──
    ("⚠️ «Void this invoice» vuelve a anular SIN preguntar", IU,
     [('                elif st.button(t("Void this invoice"), key=f"fac_anul_{fid}"):\n'
       '                    st.session_state["_fac_anular_conf"] = fid\n',
       '                elif st.button(t("Void this invoice"), key=f"fac_anul_{fid}"):\n'
       '                    st.session_state["_fac_anular"] = fid\n')]),
    ("⚠️ anular vuelve a no AVISAR", IU,
     [("        (flash.exito if _ok else flash.error)(_msg)\n", "        pass\n")]),
    ("⚠️ la anulada vuelve a «deber» en pantalla", IU,
     [("        if _anulada:\n            # ⚠️ v569 · una anulada NO debe nada",
       "        if False:\n            # ⚠️ v569 · una anulada NO debe nada")]),
    ("⚠️ el PDF de una anulada vuelve a pedir el saldo", IP,
     [("        por_cobrar = 0.0\n", "")]),
    # ── fechas ──
    ("las fechas del PDF vuelven al ISO", IP,
     [('Paragraph(_dmy(factura.get("Date", "")), H)', 'Paragraph(str(factura.get("Date", "")), H)')]),
    ("⚠️ el detalle vuelve a no decir cuándo se emitió ni vence", IU,
     [('    st.caption(" · ".join(_fecha))\n', "")]),
    ("las fechas de la lista vuelven al ISO", IU,
     [('"Vence":     _dmy(f.get("ExpiryDate")),', '"Vence":     str(f.get("ExpiryDate", "")),')]),
    ("los cobros vuelven al ISO", IU,
     [("st.markdown(f\"- {_dmy(cb.get('fecha', ''))}: **{_T.dinero(_num(cb.get('monto')))}**\")",
       "st.markdown(f\"- {cb.get('fecha', '')}: **{_T.dinero(_num(cb.get('monto')))}**\")")]),
    ("un selector de fecha vuelve al formato ISO", IU,
     [('_fecha = c1.date_input(t("Date"), value=clock.today(), key="fac_fecha", format="DD/MM/YYYY")',
       '_fecha = c1.date_input(t("Date"), value=clock.today(), key="fac_fecha")')]),
    # ── estado y textos ──
    ("el detalle vuelve a «paid» (la tabla dice «collected»)", IU,
     [('"cobrada":   (":green[:material/check_circle:]", "collected"),',
       '"cobrada":   (":green[:material/check_circle:]", "paid"),')]),
    ("un aviso vuelve sin `t()`", IU,
     [('st.caption(t(":material/info: This client has no jobs: the invoice lines are free text."))',
       'st.caption(":material/info: This client has no jobs: the invoice lines are free text.")')]),
    ("el PDF vuelve a «Factura_…»", IU,
     [("file_name=f\"Invoice_{f.get('Number', '')}.pdf\"", "file_name=f\"Factura_{f.get('Number', '')}.pdf\"")]),
    # ── activos y lista ──
    ("⚠️ las cifras dejan de filtrar la lista", IU,
     [('                st.session_state["_fac_filt_pending"] = _fl\n', "")]),
    ("el filtro deja de recordarse", IU,
     [('horizontal=True, key="cpxseg_fac_filt", label_visibility="collapsed",\n'
       '                     persist_state="session")',
       'horizontal=True, key="cpxseg_fac_filt", label_visibility="collapsed")')]),
    ("⚠️ abrir una factura vuelve a pedir la casilla", IU,
     [('on_select="rerun", selection_mode="single-cell", key=f"fac_tbl_{_gen}",',
       'on_select="rerun", selection_mode="single-row", key=f"fac_tbl_{_gen}",')]),
    ("el cliente deja de llevar a su ficha", IU,
     [('        st.session_state["_cli_open"] = C._norm(_cn)\n', "")]),
    ("el Nº deja de ir fijado", IU,
     [('"Nº":        st.column_config.TextColumn(t("No."), pinned=True),',
       '"Nº":        st.column_config.TextColumn(t("No.")),')]),
    ("vuelve el «Scope» de UNA opción", IU,
     [("    if prj_names:\n        _scope = st.radio(", "    if True:\n        _scope = st.radio(")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           IU, [('    """El estado en una CELDA de tabla: punto de color + la etiqueta traducida (v569).',
                 '    """El estado en una CELDA de tabla: punto de color + la etiqueta traducida (v569). (control)')])

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
