# -*- coding: utf-8 -*-
"""Bateria de roturas de v526. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522).

⚠️ La primera rotura NO es una variante: devuelve el selector EXACTAMENTE al codigo de
v525 (cuatro trozos a la vez). Es la prueba de que el guardian caza el fallo que se vio
en produccion, y no solo algo parecido. Por eso cada rotura es una LISTA de cambios.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v526"
PUI = "core/projects_ui.py"
DUI = "core/daily_log_ui.py"
APPF = "app.py"
TOPE_S = 420


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ el selector vuelve al codigo de v525 (guarda la ETIQUETA: el fallo de produccion)",
     PUI, [
         ('    idmap = {str(p.get("ID")): f"{p.get(\'Name\')} ({p.get(\'ID\')}) — {p.get(\'Status\')}"\n'
          '             for p in proys}',
          '    idmap = {f"{p.get(\'Name\')} ({p.get(\'ID\')}) — {p.get(\'Status\')}": p.get("ID")\n'
          '             for p in proys}'),
         ("    if _prev is not None and _prev != _VACIO and _prev not in idmap:",
          "    if False:"),
         ('_m = next((i for i, lab in idmap.items() if lab.startswith(_fich + " (")), None)',
          '_m = next((k for k in idmap if k.startswith(_fich + " (")), None)'),
         ("format_func=lambda i: idmap.get(i, i))", "format_func=lambda i: i)"),
         ("    pid = sel\n", "    pid = idmap[sel]\n"),
     ]),

    ("un valor viejo ya no se rescata: se queda FANTASMA en el desplegable",
     PUI, [("    if _prev is not None and _prev != _VACIO and _prev not in idmap:",
            "    if False:")]),

    ("un valor viejo se tira en vez de rescatar su ID",
     PUI, [('(i for i in idmap if f"({i})" in str(_prev)), _VACIO)',
            "(i for i in ()), _VACIO)")]),

    ("el desplegable enseña el ID pelado (sin nombre ni estado)",
     PUI, [("format_func=lambda i: idmap.get(i, i))", "format_func=lambda i: i)")]),

    ("el fichaje abierto deja de elegir su obra",
     PUI, [('lab.startswith(_fich + " (")', 'lab.startswith(_fich + " [")')]),

    ("una sola obra deja de abrirse sola (v480)",
     PUI, [('if "fieldproj_sel" not in st.session_state and len(idmap) == 1:',
            'if "fieldproj_sel" not in st.session_state and len(idmap) == 0:')]),

    ("un parte de otro dia vuelve a ensenar los SEGUNDOS",
     DUI, [("and len(_creado) >= 16 else _creado[:16]", "and len(_creado) >= 16 else _creado")]),

    ("la caja del asistente vuelve al espanol y sin `t()`",
     APPF, [('st.chat_input(t("Ask your question…"), key=',
             'st.chat_input("Escribe tu pregunta…", key=')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PUI, [('_VACIO = "— choose a project —"',
                  '# comentario inocuo del control\n_VACIO = "— choose a project —"')])


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
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

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
