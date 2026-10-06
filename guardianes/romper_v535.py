# -*- coding: utf-8 -*-
"""Bateria de roturas de v535. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el codigo de v534: cambiar de obra SIN salir de la herramienta
no olvida nada, y el LFKK de la obra anterior se queda bajo el nombre de la nueva.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v535"
APPF = "app.py"
EV = "core/estado_vivo.py"
PLA = "core/plan_ui.py"
SV = "core/survey_ui.py"
INC = "core/incrustar.py"
TCU = "core/timeclock_ui.py"
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
    ("⚠️ vuelve el codigo de v534: sin salir, de una obra a otra, no se olvida nada",
     EV, [("    if obra and ult_real and ult_real != obra:", "    if False:")]),

    ("⚠️ el Survey tambien olvida lo medido al cambiar de obra («Duplicate» pierde lo suyo)",
     EV, [('        if h != "sv":\n            olvidar(h)\n', "        olvidar(h)\n")]),

    ("las herramientas no olvidan lo tecleado para la obra anterior (solo manda el plano)",
     EV, [('        if h != "sv":\n', "        if False:\n")]),

    ("la pasada no se cuenta: «sin obra» -> obra al volver deja de olvidar (mudada de v534)",
     EV, [("    st.session_state[_PASADA] = int(st.session_state.get(_PASADA, 0) or 0) + 1",
           "    st.session_state[_PASADA] = int(st.session_state.get(_PASADA, 0) or 0)")]),

    ("B -> ninguna -> A deja de contar como cambio (la ultima obra real no se recuerda)",
     EV, [("    st.session_state[_VISTA + h] = (n, obra, obra or ult_real)",
           "    st.session_state[_VISTA + h] = (n, obra, obra)")]),

    ("⚠️ `aplicar` no hace caso del aviso: el plano de la obra nueva no pisa lo de la anterior",
     PLA, [("        if vacio or forzar:", "        if vacio:")]),

    ("`aplicar` no consume el aviso (otra herramienta lo heredaria)",
     PLA, [("    forzar = bool(st.session_state.pop(_FORZAR, False))",
            "    forzar = bool(st.session_state.get(_FORZAR, False))")]),

    ("el nº de paradas forzado pasa a decimal (el widget cambiaria de tipo)",
     PLA, [("isinstance(actual, int)\n", "False\n")]),

    ("⚠️ el NS neutro (2) vuelve a no contar como vacio: el NS del plano no se aplica nunca",
     PLA, [("            vacio = True\n", "            pass\n")]),

    ("el Survey deja de pasar el NS neutro a `aplicar`",
     SV, [(", neutros=_neutro_sv)", ")")]),

    ("el NS neutro cuenta SIEMPRE (quien pone 2 a mano lo ve volver al del plano)",
     SV, [("_neutro_sv = ({\"ns\": 2} if st.session_state.get(\"_sv_ns_obra\") != _pid_sv",
           "_neutro_sv = ({\"ns\": 2} if True")]),

    ("«Start a new survey» no deja que el NS del plano vuelva a mandar",
     SV, [('"_diag_pdf", "_sv_ns_obra"):', '"_diag_pdf"):')]),

    ("⚠️ entra otra cuenta y no se borra nada (ve los resultados y el chat de la anterior)",
     EV, [("            continue\n        del st.session_state[k]\n",
           "            continue\n        pass\n")]),

    ("al cambiar de cuenta se borra tambien la identidad recien puesta",
     EV, [('_INFRA = frozenset({"auth", ', "_INFRA = frozenset({")]),

    ("la primera cuenta de la sesion ya borra (no habia de quien)",
     EV, [("    if antes is None or antes == u:", "    if antes == u:")]),

    ("⚠️ app.py deja de mirar de quien son los datos",
     APPF, [('if _estado_vivo.de_la_cuenta(st.session_state.auth.get("usuario", "")):\n    init_state()\n',
             "")]),

    ("app.py borra pero no vuelve a poner el estado base (lecturas por atributo revientan)",
     APPF, [('if _estado_vivo.de_la_cuenta(st.session_state.auth.get("usuario", "")):\n    init_state()\n',
             'if _estado_vivo.de_la_cuenta(st.session_state.auth.get("usuario", "")):\n    pass\n')]),

    ("⚠️ los dibujos vuelven a un alto fijo (el hueco en blanco en pantalla estrecha)",
     INC, [("        ajustar = not scroll", "        ajustar = False")]),

    ("un cronometro pasa a medir su contenido (el menu lateral cambiaria de alto)",
     TCU, [('"</script>", 44, ajustar=False)', '"</script>", 44)')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           EV, [("    if obra and ult_real and ult_real != obra:",
                 "    # comentario inocuo del control\n    if obra and ult_real and ult_real != obra:")])


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
