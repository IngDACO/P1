# -*- coding: utf-8 -*-
"""Bateria de roturas de v542. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el «empezar de cero» de v541, que BORRABA los campos con la
pantalla delante (el navegador no se enteraba y los devolvia); la segunda, la matriz con
clave fija (Streamlit re-aplicaba lo tecleado sobre la matriz «limpia»).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v542"
EV = "core/estado_vivo.py"
SV = "core/survey_ui.py"
PRU = "core/projects_ui.py"
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
    # ── A. Lo que reemplaza, limpia de verdad ──
    ("⚠️ vuelve el «empezar de cero» de v541: BORRA los campos (el navegador no se entera)",
     SV, [("        if _k in _inicial:\n            st.session_state[_k] = _inicial[_k]\n"
           "        else:\n            st.session_state.pop(_k, None)\n"
           "    for _k, _v in _inicial.items():\n        st.session_state.setdefault(_k, _v)\n",
           "        st.session_state.pop(_k, None)\n")]),

    ("⚠️ la matriz vuelve a una clave FIJA (Streamlit re-aplica lo tecleado)",
     SV, [('key=estado_vivo.clave_tabla("sv", "survey_editor")', 'key="survey_editor"')]),

    ("empezar de cero no estrena matriz",
     SV, [('    estado_vivo.tabla_nueva("sv")       # la matriz, nueva también para el navegador\n',
           "")]),

    ("Duplicate no estrena matriz",
     SV, [('        estado_vivo.tabla_nueva("sv")       # v542 · si no, las celdas tecleadas reaparecen\n',
           "")]),

    ("importar un Excel no estrena matriz (lo tecleado pisa lo importado)",
     SV, [('            estado_vivo.tabla_nueva("sv")   # v542 · si no, lo tecleado pisa lo importado\n',
           "")]),

    ("«Rebuild the project in the Survey» no estrena matriz",
     PRU, [('                            _ev.tabla_nueva("sv")\n', "")]),

    # ── B. No se mezcla información de proyectos ──
    ("⚠️ de una obra a OTRA el Survey ya no empieza de cero (lo de A pasa a B)",
     SV, [('        if estado_vivo.cambio_de_obra("sv"):\n            _limpiar_survey()\n',
           '        if estado_vivo.cambio_de_obra("sv"):\n            pass\n')]),

    ("`estado_vivo` no avisa del cambio de una obra real a otra",
     EV, [("            st.session_state[_CAMBIO + h] = True", "            pass")]),

    ("de «sin obra» a una obra tambien empieza de cero (se pierde lo tecleado antes de fichar)",
     EV, [("        elif ult_real:                                  # de una obra real a otra",
           "        else:")]),

    # v543 · RETIRADA «el aviso vuelve a `st.info`»: por `flash` llegaba una pasada tarde;
    # desde v543 va por una marca que dura hasta pasar el corte de la matriz — lo vigila
    # romper_v543.

    ("⚠️ Duplicate no deja lo suyo para la siguiente obra (al elegirla, se borra)",
     SV, [('        estado_vivo.adoptar_siguiente("sv")\n', "")]),

    ("lo duplicado lo adopta la MISMA obra de partida (la siguiente lo borra)",
     EV, [("        if obra and obra != salvo:", "        if obra:")]),

    ("al adoptar lo duplicado, el plano de la obra nueva no manda",
     EV, [('            adopta = "|" in ult_real                    # el duplicado: su plano manda',
           "            adopta = False")]),

    ("Duplicate no pone el selector del admin en «sin proyecto»",
     SV, [('        if "pl_prj_sv" in st.session_state:\n'
           '            st.session_state["pl_prj_sv"] = plan_ui.SIN_PROYECTO\n', "")]),

    ("⚠️ guardar el survey en su proyecto ya no lo limpia (el siguiente arrastra este)",
     SV, [('                            st.session_state["_reset_survey"] = True\n', "")]),

    ("el «guardado» vuelve a `st.success` (se pierde con el `st.rerun()`)",
     SV, [('flash.exito(t(":material/check_circle: Survey saved to **{x}**.",',
           'st.success(t(":material/check_circle: Survey saved to **{x}**.",')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           SV, [("    estado_vivo.tabla_nueva(\"sv\")       # la matriz, nueva también para el navegador\n",
                 "    # comentario inocuo del control\n"
                 "    estado_vivo.tabla_nueva(\"sv\")       # la matriz, nueva también para el navegador\n")])


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
