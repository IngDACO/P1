# -*- coding: utf-8 -*-
"""Bateria de roturas de v593 (Tools → Rails). ⚠️ Verde de BASE primero (v459) y NO en paralelo
con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba que cada ancla
casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v593"
RU = "core/rail_cut_ui.py"
RC = "core/rail_cut.py"
TOPE_S = 600

ROTURAS = [
    ("⚠️ el Caso 1 vuelve a calcular sin tramos (A = 0)", RU,
     [("            if A <= 0:\n", "            if False:\n")]),
    ("⚠️ los resultados viejos del Caso 1 vuelven a pasar por buenos", RU,
     [('            _vig = _e.get("firma") == _ahora\n            if not _vig:\n                _aviso_viejo()\n'
       '            _lk, _lg = _e.get("lfkk", lfkk), _e.get("lfgk", lfgk)\n            _cifras([("a"',
       '            _vig = True\n            if not _vig:\n                _aviso_viejo()\n'
       '            _lk, _lg = _e.get("lfkk", lfkk), _e.get("lfgk", lfgk)\n            _cifras([("a"')]),
    ("⚠️ las cifras vuelven a tomar LFKK/LFGK de AHORA", RU,
     [('            _lk, _lg = _e.get("lfkk", lfkk), _e.get("lfgk", lfgk)\n            _cifras([("a"',
       '            _lk, _lg = lfkk, lfgk\n            _cifras([("a"')]),
    ("⚠️ cambiar el nº de ascensores vuelve a BORRAR las L", RU,
     [('                                 "L (mm)": (_prev + [0.0] * n)[:n]})\n',
       '                                 "L (mm)": [0.0] * n})\n')]),
    ("⚠️ el Caso 2 vuelve a decidir por el TEXTO de la opción", RU,
     [('        subcaso = "encima" if sub == _S1 else "debajo"      # código del motor (`compute_case2`)\n',
       '        subcaso = "encima" if str(sub).startswith("Arriba") else "debajo"\n')]),
    ("⚠️ el Caso 2 vuelve a calcular con un ascensor en 0", RU,
     [("            if _vacios:\n", "            if False:\n")]),
    ("el Caso 2 vuelve a borrar las columnas al cambiar el nº de ascensores", RU,
     [("            for _c, _v in _prev.items():\n", "            for _c, _v in {}.items():\n")]),
    ("cambiar el sub-caso deja de dejar viejo el resultado", RU,
     [("        _ahora = _firma(2, lfkk, lfgk, n, subcaso,\n", "        _ahora = _firma(2, lfkk, lfgk, n,\n")]),
    ("⚠️ vuelve «Caso 1 · …» al resumen guardado", RU,
     [('                           resumen=d("Case 1 · A {a} · {x}", a=f"{res[\'A\']:.0f}", x=", ".join(\n',
       '                           resumen=d("Caso 1 · A {a} · {x}", a=f"{res[\'A\']:.0f}", x=", ".join(\n')]),
    ("vuelve «corte_rieles_caso1.pdf»", RU,
     [("                           nombre_archivo=f\"Rail_cutting_case1_{_archivo(_pr, 'shaft')}_{_hoy}.pdf\",\n",
       '                           nombre_archivo="corte_rieles_caso1.pdf",\n')]),
    ("vuelve «(debajo) · N lift(s)»", RU,
     [('                                    else d("Case 2 ({s}) · {n} lifts", s=_sub_doc, n=len(res))),\n',
       "                                    else f\"Case 2 ({_e['subcaso']}) · {len(res)} lift(s)\"),\n")]),
    ("el signo de los cortes deja de decirse junto a la tabla", RU,
     [('            st.caption(t("The cut goes on the 1st rail (the bottom one, first installed). "\n',
       '            (t("The cut goes on the 1st rail (the bottom one, first installed). "\n')]),
    ("⚠️ el aviso del plano vuelve a ser de UNA pasada (o desaparece)", RU,
     [('        if _plano.get("lfkk") or _plano.get("lfgk"):\n', "        if False:\n")]),
    ("las cifras dejan de llevar al diagrama", RU,
     [('                st.session_state["_bajar_cpx_rc_dibujo"] = True\n', "")]),
    ("⚠️ vuelve «Elev.» al diagrama", RC,
     [("{_d(\"Lift {n}\", n=i + 1)}</text>')   # v593 · era «Elev.»",
       "{_d(\"Elev.\")} {i+1}</text>')")]),
    ("⚠️ el nombre vuelve sin medir ni escapar («&» rompe el SVG)", RC,
     [("                f'font-weight=\"bold\">{texto_svg.cabe(proyecto, _libre, 9, True)}</text>')\n",
       "                f'font-weight=\"bold\">{proyecto}</text>')\n")]),
    ("la cifra vuelve DENTRO de la banda fina", RC,
     [("                    _yt = (yc + h / 2 + 3) if h >= 12 else (yc - 3)\n",
       "                    _yt = yc + h / 2 + 3\n")]),
    ("⚠️ la plomada vuelve a BORRAR los BSR al cambiar el nº de ascensores", "core/plumb_ui.py",
     [('                             "BSR (mm)": (_prev + [0.0] * n)[:n]})\n',
       '                             "BSR (mm)": [0.0] * n})\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RU,
           [("def _aviso_viejo():\n", "def _aviso_viejo():   # (control)\n")])


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
