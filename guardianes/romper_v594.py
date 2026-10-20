# -*- coding: utf-8 -*-
"""Bateria de roturas de v594 (Tools → Buffers + la validación de la plomada). ⚠️ Verde de BASE
primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v594"
BU = "core/buffer_cut_ui.py"
PL = "core/plumb_ui.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ un buffer SIN MEDIR vuelve a dar «cortar el HKP entero»", BU,
     [("        _sin = [str(i + 1) for i, x in enumerate(hkpr_list) if x <= 0]\n",
       "        _sin = []\n")]),
    ("…o sin HKP vuelve a calcular", BU,
     [("        if hkp <= 0:\n", "        if False:\n")]),
    ("⚠️ los resultados viejos vuelven a pasar por buenos", BU,
     [('    _vig = res.get("firma") == _ahora\n', "    _vig = True\n")]),
    ("⚠️ cambiar el nº de buffers vuelve a BORRAR los HKPR", BU,
     [('                             "HKPR (mm)": (_prev + [0.0] * n)[:n]})\n',
       '                             "HKPR (mm)": [0.0] * n})\n')]),
    ("el aviso del plano vuelve a ser de UNA pasada (o desaparece)", BU,
     [('        if _plano.get("hkp"):\n', "        if False:\n")]),
    ("«To check» deja de llevar a la tabla", BU,
     [('           ("rev", t("To check"), str(_n_warn), "cpx_bc_tabla")]\n',
       '           ("rev", t("To check"), str(_n_warn), "cpx_bc_nada")]\n')]),
    ("vuelve «B1:» al resumen guardado", BU,
     [('                       d("Buffer {i}: {c}", i=b["n"], c=f"{b[\'CutBuffer\']:.1f}")\n',
       '                       f"B{b[\'n\']}: {b[\'CutBuffer\']}"\n')]),
    ("vuelve «corte_buffers.pdf»", BU,
     [('                   nombre_archivo=f"Buffer_cutting_{_archivo(_pr, \'shaft\')}_"\n',
       '                   nombre_archivo="corte_buffers.pdf" if True else f"Buffer_cutting_{_archivo(_pr, \'shaft\')}_"\n')]),
    ("la huella interna se cuela en lo guardado", BU,
     [('                   datos={k: v for k, v in res.items() if k != "firma"},\n',
       "                   datos=res,\n")]),
    ("⚠️ el nombre vuelve sin medir ni escapar en el diagrama", "core/buffer_cut.py",
     [("                 f'fill=\"{INK}\" font-weight=\"bold\">{texto_svg.cabe(proyecto, _libre, 9, True)}</text>')\n",
       "                 f'fill=\"{INK}\" font-weight=\"bold\">{proyecto}</text>')\n")]),
    ("⚠️ la plomada vuelve a calcular con un BSR en 0", PL,
     [("    _sin = [str(i + 1) for i, x in enumerate(bsr_list) if float(x or 0) <= 0]\n",
       "    _sin = []\n")]),
    ("…o sin LengthTemplate", PL,
     [('                              ("LengthTemplate", lt), ("BS", bs)) if float(v or 0) <= 0]\n',
       '                              ("BS", bs)) if float(v or 0) <= 0]\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", BU,
           [("def _firma(hkp, n, hkpr_list) -> tuple:\n", "def _firma(hkp, n, hkpr_list) -> tuple:   # (control)\n")])


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
