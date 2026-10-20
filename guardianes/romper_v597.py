# -*- coding: utf-8 -*-
"""Bateria de roturas de v597 (un decimal en las cuatro herramientas; Rails avisa lo que no
encuentra; el PDF de la plomada en inglés; el rótulo HKP con sitio). ⚠️ Verde de BASE primero
(v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas`
solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v597"
RU = "core/rail_cut_ui.py"
RC = "core/rail_cut.py"
BU = "core/buffer_cut_ui.py"
BC = "core/buffer_cut.py"
BE = "core/belting_ui.py"
BL = "core/belting.py"
PL = "core/plumb.py"
PU = "core/plumb_ui.py"
SV = "core/survey_ui.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ Rails: el resumen guardado vuelve a redondear a entero (650.5 → «650»)", RU,
     [("                               d(\"Lift {i}: {c}/{w}\", i=i + 1, c=f\"{x['CutRC']:.1f}\",\n",
       "                               d(\"Lift {i}: {c}/{w}\", i=i + 1, c=f\"{x['CutRC']:.0f}\",\n")]),
    ("Rails: la tabla de cortes vuelve sin formato", RU,
     [('            st.dataframe(mat, width="stretch", column_config=_cfg_mm(_e["n"]))\n'
       '            # v593 · el signo',
       '            st.dataframe(mat, width="stretch", column_config=tabla.cfg())\n'
       '            # v593 · el signo')]),
    ("Rails: el diagrama vuelve a quitar el «.0» del corte", RC,
     [("                             f'font-weight=\"bold\">{_m1(corte)}</text>')\n",
       "                             f'font-weight=\"bold\">{_mm(corte)}</text>')\n")]),
    ("…o de L", RC,
     [("L {_m1(e[\"L\"])}</text>", "L {_mm(e[\"L\"])}</text>")]),
    ("…o del Caso 2", RC,
     [("font-weight=\"bold\">{_m1(v)}</text>", "font-weight=\"bold\">{_mm(v)}</text>")]),
    ("⚠️ Rails: «nada en el PDF» vuelve a salir en VERDE", RU,
     [("            if not found:\n                st.warning(", "            if not found:\n                st.success(")]),
    ("…o deja de decir cuál falta", RU,
     [("            elif _falta:\n", "            elif False:\n")]),
    ("Buffers: el HKPR vuelve sin formato", BU,
     [('"HKPR (mm)": tabla.mm1(t("HKPR (mm)")),', '"HKPR (mm)": st.column_config.Column(t("HKPR (mm)")),')]),
    ("…o el corte", BU,
     [('d("Cut (mm)"): tabla.mm1(t("Cut (mm)"))', 'd("Cut (mm)"): st.column_config.Column(t("Cut (mm)"))')]),
    ("Buffers: el diagrama vuelve a «cut 20»", BC,
     [("f'{_d(\"cut\")} {_m1(corte)}</text>')", "f'{_d(\"cut\")} {_mm(corte)}</text>')")]),
    ("…o a «HKPR 500»", BC,
     [("HKPR {_m1(hkpr)}</text>", "HKPR {_mm(hkpr)}</text>")]),
    ("⚠️ Buffers: el dibujo deja de reservar el sitio del rótulo HKP (con 5, lo pisa)", BC,
     [("             int(_fin_buf + 8 + texto_svg.ancho(_lbl_hkp, 8.5, True) + 20 + 1))\n",
       "             0)\n")]),
    ("Belting: el HGPR vuelve sin formato («120» y «70.5»)", BE,
     [('"HGPR (mm)": tabla.mm1(t("HGPR (mm)")),', '"HGPR (mm)": st.column_config.Column(t("HGPR (mm)")),')]),
    ("…o el diagrama a «HGPR 120»", BL,
     [("HGPR {hgpr:.1f}</text>", "HGPR {hgpr:.0f}</text>")]),
    ("…o el PDF con el valor sin redondear («120.25» junto a «120.2»)", BE,
     [('        "HGPR (mm)": round(float(r["hgpr"]), 1),', '        "HGPR (mm)": float(r["hgpr"]),')]),
    ("Plumb: los dibujos vuelven a quitar el «.0» («DBP 1662»)", PL,
     [('        return f"{float(v):.1f}"\n',
       '        return f"{float(v):.0f}" if abs(float(v) - round(float(v))) < 0.05 else f"{float(v):.1f}"\n')]),
    ("…o el chequeo de BS (cota del plano) con decimal", PL,
     [('x=_n0(bsc.get("dif"))', 'x=_n(bsc.get("dif"))')]),
    # (la 1ª tanda la dejó escapar con razón: la sonda no daba «X final» con dos decimales — ver
    # verif_v597, ahora con BSR 1985.25)
    ("`plumb_table` vuelve a dos decimales (X final)", PL,
     [('            "X final (mm)":   round(d["x"], 1),', '            "X final (mm)":   round(d["x"], 2),')]),
    ("…o en X inicial", PL,
     [('            "X inicial (mm)": round(d["x0"], 1),', '            "X inicial (mm)": round(d["x0"], 2),')]),
    ("⚠️ el PDF de la plomada vuelve a «Línea» (las claves de `plumb_table`)", PL,
     [('    return [{_d("Line"): f["Línea"],', '    return [{"Línea": f["Línea"],')]),
    ("…o la herramienta vuelve a pasarle `plumb_table` al PDF", PU,
     [('(d("Template — line positions"), plumb_table_doc(r0))],',
       '(d("Template — line positions"), plumb_table(r0))],')]),
    ("el Survey: las posiciones de la plomada vuelven sin formato", SV,
     [('"X inicial (mm)": tabla.mm1(t("X start (mm)"))', '"X inicial (mm)": st.column_config.Column(t("X start (mm)"))')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RU,
           [("def _cfg_mm(n):\n", "def _cfg_mm(n):   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
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
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8", newline="").read()
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
