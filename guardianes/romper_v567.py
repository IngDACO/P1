# -*- coding: utf-8 -*-
"""Bateria de roturas de v567. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto verificando v566 en producción.
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
G = "verif_v567"
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
    ("⚠️ las tarjetas con texto corto vuelven a salir CENTRADAS (envoltorio)", TH,
     [('[class*="st-key-cpxkpi_"] button > div {{\n  width: 100%; justify-content: flex-start !important;\n}}\n', "")]),
    ("…o el `<span>` que encoge vuelve", TH,
     [('[class*="st-key-cpxkpi_"] button > div > span {{\n  flex: 1 1 auto; width: 100%; justify-content: flex-start !important;\n}}\n', "")]),
    ("⚠️ la tarjeta deja de llevar la vista a la herramienta", PU,
     [('            st.session_state["_pnl_tool_ir"] = True\n', "")]),
    ("⚠️ la vista se movería en CADA pasada", PU,
     [('            if st.session_state.pop("_pnl_tool_ir", False):\n', "            if True:\n")]),
    ("el recuadro pierde la clave que busca el script", PU,
     [('with st.container(border=True, key="cpx_pnl_panel"):', "with st.container(border=True):")]),
    ("⚠️ vuelve el «None» del margen", PU,
     [('"Margen %": (f"{r[\'margen\']:.1f}%" if r["margen"] is not None else "—"),',
       '"Margen %": r["margen"],')]),
    ("el margen deja de ir a la derecha", PU,
     [('st.column_config.TextColumn(t("Margin %"), alignment="right")', 'st.column_config.TextColumn(t("Margin %"))')]),
    ("⚠️ vuelve «single-row» (solo con la casilla)", PU,
     [('selection_mode="single-cell", key=f"pnl_prj_tbl_{_gen}",', 'selection_mode="single-row", key=f"pnl_prj_tbl_{_gen}",')]),
    ("⚠️ la celda elegida se ignora", PU,
     [('[c[0] for c in (getattr(_sel, "cells", None) or [])]', "[]")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [("            # v567 · la herramienta se pinta debajo de la rejilla: desde la tarjeta quedaba",
                 "            # v567 · la herramienta se pinta debajo de la rejilla: desde la tarjeta quedaba (control)")])

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
