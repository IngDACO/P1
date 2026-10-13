# -*- coding: utf-8 -*-
"""Bateria de roturas de v576 (2 cifras por fila en estrecho). ⚠️ Verde de BASE primero
(v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
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
G = "verif_v576"
CU = "core/clientes_ui.py"
PU = "core/payroll_ui.py"
TH = "core/theme.py"
TOPE_S = 300

ROTURAS = [
    ("⚠️ la lista de Contacts vuelve a apilar sus cifras", CU,
     [('    st.markdown(_T.dos_por_fila("cpx_clis_kpis"), unsafe_allow_html=True)   # v576 · 2 por fila en estrecho\n', "")]),
    ("el resumen del cliente vuelve a apilarlas", CU,
     [('    st.markdown(_T.dos_por_fila("cpx_cls_kpis"), unsafe_allow_html=True)\n', "")]),
    ("…o sus columnas salen FUERA del contenedor medido", CU,
     [("zip(_box.columns(2), _K[_i:_i + 2])", "zip(st.columns(2), _K[_i:_i + 2])")]),
    ("las cifras de Payroll vuelven a apilarse", PU,
     [('    st.markdown(T.dos_por_fila("cpx_nom_kpis"), unsafe_allow_html=True)   # v576 · 2 por fila en estrecho\n', "")]),
    ("el helper pierde el corte de 700 px", TH,
     [('            f"@container (max-width:700px){{{_c} [data-testid=\'stHorizontalBlock\']"',
       '            f"@container (max-width:300px){{{_c} [data-testid=\'stHorizontalBlock\']"')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", TH,
           [('def dos_por_fila(clave: str) -> str:\n', 'def dos_por_fila(clave: str) -> str:   # (control)\n')])


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
