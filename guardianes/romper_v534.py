# -*- coding: utf-8 -*-
"""Bateria de roturas de v534. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera rotura devuelve el codigo de v533: `app.py` no conserva las entradas, que es
lo que en produccion dejo el Survey a cero al salir a Rieles y volver. Y hay un bloque para
lo que se vio RELEYENDO el arreglo: conservar sin mirar la obra dejaba el plano de la obra
vieja bajo el nombre de la nueva.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v534"
APPF = "app.py"
EV = "core/estado_vivo.py"
SV = "core/survey_ui.py"
BEL = "core/belting.py"
RC = "core/rail_cut.py"
RCU = "core/rail_cut_ui.py"
PLU = "core/plumb_ui.py"
TCU = "core/timeclock_ui.py"
THE = "core/theme.py"
PLA = "core/plan_ui.py"
TSU = "core/tool_save_ui.py"
PRU = "core/projects_ui.py"
TOPE_S = 420

_LLAMA = "_estado_vivo.pasada()\n"
_REASIGNA = "            st.session_state[k] = st.session_state[k]\n"


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ vuelve el codigo de v533: app.py no conserva las entradas (el Survey a cero al volver)",
     APPF, [(_LLAMA, "pass\n")]),

    ("`mantener()` recorre las claves pero no reasigna ninguna",
     EV, [(_REASIGNA, "            pass\n")]),

    ("⚠️ app.py solo conserva las entradas para un rol (dentro de un `if`)",
     APPF, [(_LLAMA, "if _ROL == \"owner\":\n    _estado_vivo.pasada()\n")]),

    ("⚠️ un BOTON entra en la lista (reasignarlo lanza una excepcion al pintarlo)",
     EV, [('"claves": ("rc_lfkk", "rc_lfgk",', '"claves": ("rc_calc1", "rc_lfkk", "rc_lfgk",')]),

    ("una TABLA editable entra en la lista",
     EV, [('"claves": ("bc_hkp", "bc_n")}', '"claves": ("bc_hkp", "bc_n", "rc_L_editor")}')]),

    ("una entrada de Rieles se cae de la lista (se perderia al salir)",
     EV, [('"rc_n2500", ', "")]),

    ("⚠️ el HGPR por ascensor de Belting se cae de la lista",
     EV, [('"belt": {"prefijos": ("belt_hgpr_",),', '"belt": {"prefijos": (),')]),

    ("los parametros del Survey se caen de la lista",
     EV, [('"sv":   {"prefijos": ("inp_", "cfg_"),', '"sv":   {"prefijos": ("cfg_",),')]),

    ("la solucion activa entra en la lista (v530: tiene que nacer con cada calculo)",
     EV, [('"sv":   {"prefijos": ("inp_", "cfg_"),',
           '"sv":   {"prefijos": ("inp_", "cfg_", "sol_activa_"),')]),

    # ── Lo conservado es de UNA obra ──
    ("⚠️ al volver con OTRA obra no se olvida nada (el plano de la vieja bajo el nombre de la nueva)",
     EV, [("    olvidar(h)\n    return True", "    return True")]),

    ("`olvidar` recorre las entradas de la herramienta pero no borra ninguna",
     EV, [("            del st.session_state[k]\n", "            pass\n")]),

    ("⚠️ `selector_proyecto` deja de avisar con que obra se pinta la herramienta",
     PLA, [('    estado_vivo.al_pintar(key, (prj or {}).get("ID", ""))\n', "")]),

    ("la pasada no se cuenta (nunca se sabe si la herramienta vuelve)",
     EV, [("    st.session_state[_PASADA] = int(st.session_state.get(_PASADA, 0) or 0) + 1",
           "    st.session_state[_PASADA] = int(st.session_state.get(_PASADA, 0) or 0)")]),

    ("⚠️ se olvida tambien al volver con la MISMA obra (el arreglo no arregla nada)",
     EV, [("    if ult_pasada >= n - 1 or ult_obra == obra:", "    if ult_pasada >= n - 1:")]),

    ("se olvida tambien al cambiar de obra SIN salir («Duplicate for the next lift» pierde lo suyo)",
     EV, [("    if ult_pasada >= n - 1 or ult_obra == obra:", "    if ult_obra == obra:")]),

    ("la obra elegida en la herramienta no se conserva (al volver siempre es «otra»)",
     EV, [(" + (_OBRA,)", "")]),

    ("la FASE del Survey se conserva (volveria a Results sin mirar la obra)",
     EV, [('"claves": ("ns",)}', '"claves": ("ns", "survey_fase")}')]),

    ("⚠️ lo cargado a proposito no se respeta (reabrir un calculo con otra obra lo borra)",
     EV, [("    if st.session_state.pop(_RESPETAR + h, False) or not antes:", "    if not antes:")]),

    ("reabrir un calculo no avisa de que lo suyo se respete",
     TSU, [('    estado_vivo.respetar(_PREFIJO.get(herramienta, "").rstrip("_"))\n', "")]),

    ("⚠️ reabrir vuelve a asignar el BOTON guardado (codigo de v533: la pantalla revienta)",
     TSU, [("        if not _restaurable(k):\n            continue\n        try:", "        try:")]),

    ("la foto de las entradas vuelve a incluir el boton (codigo exacto de v533)",
     TSU, [("        if not str(k).startswith(pref) or not _restaurable(k):",
            '        if not str(k).startswith(pref) or str(k).endswith("_editor"):')]),

    ("«Rebuild the project in the Survey» no marca lo que carga",
     PRU, [('                    _ev.respetar("sv")\n', "")]),

    ("⚠️ Belting vuelve a medir lo que sus columnas (198 con 1 ascensor: titulo cortado)",
     BEL, [("    VW = max(470, ML * 2 + n * colw)", "    VW = ML * 2 + n * colw")]),

    ("⚠️ el nombre de la obra vuelve a la linea del titulo de Belting (se pisan)",
     BEL, [("        p.append(f'<text x=\"{VW-18}\" y=\"50\" text-anchor=\"end\" font-size=\"9\" '",
            "        p.append(f'<text x=\"{VW-18}\" y=\"22\" text-anchor=\"end\" font-size=\"9\" '")]),

    ("la columna unica de Belting vuelve pegada a la izquierda",
     BEL, [("        x0 = X0 + i * colw", "        x0 = ML + i * colw")]),

    ("⚠️ la leyenda de Rieles vuelve a una sola linea (pierde el final con 1 ascensor)",
     RC, [("        p.append(f'<text x=\"18\" y=\"{VH-10}\" font-size=\"8\" fill=\"#5b6472\">'",
           "        p.append(f'<text x=\"250\" y=\"{_yl+8}\" font-size=\"8\" fill=\"#5b6472\">'")]),

    ("⚠️ el cronometro vuelve a una sola linea forzada (cortado en columna estrecha)",
     TCU, [("'<div style=\"display:flex;flex-wrap:wrap;align-items:baseline;column-gap:10px;'",
            "'<div style=\"display:flex;align-items:baseline;column-gap:10px;'")]),

    ("el cronometro recupera los margenes del documento (dos lineas ya no caben en 52 px)",
     TCU, [("    incrustar.dibujo('<body style=\"margin:0\">'\n        '<div style=\"display:flex;flex-wrap",
            "    incrustar.dibujo('<body>'\n        '<div style=\"display:flex;flex-wrap")]),

    ("⚠️ el valor de la metrica vuelve a cortarse con «…»",
     THE, [("  text-overflow: clip !important; line-height: 1.2; overflow-wrap: anywhere;",
            "  text-overflow: ellipsis !important; line-height: 1.2; overflow-wrap: anywhere;")]),

    ("⚠️ vuelve «N fuera» al desplegable de soluciones (codigo exacto de v533)",
     SV, [('                        + t("{n} out of limit", n=s["total_off"]) for s in sorted_solutions]',
           "                        + f\"{s['total_off']} fuera\" for s in sorted_solutions]")]),

    ("vuelve «Matriz: N niveles» (codigo exacto de v533)",
     SV, [('            t(":green[:material/check_circle:] Matrix: {n} levels", n=_nsv),',
           '            f":green[:material/check_circle:] Matriz: {_nsv} niveles",')]),

    ("vuelve «Piso N» al selector de pisos (codigo exacto de v533)",
     SV, [('                    format_func=lambda i: t("Floor {n}", n=i + 1),',
           '                    format_func=lambda i: f"Piso {i + 1}",')]),

    ("⚠️ las filas de Rieles vuelven a «Elevador N» (codigo exacto de v533)",
     RCU, [('            base = pd.DataFrame({"Elevador": [t("Lift {n}", n=i + 1) for i in range(n)],',
            '            base = pd.DataFrame({"Elevador": [f"Elevador {i+1}" for i in range(n)],')]),

    ("la cabecera del Caso 2 de Rieles pierde su etiqueta en ingles",
     RCU, [('                                     f"Elevador {i+1}": st.column_config.Column(t("Lift {n}", n=i + 1))',
            '                                     f"Elevador-{i+1}": st.column_config.Column(t("Lift {n}", n=i + 1))')]),

    ("⚠️ el arreglo tentador: renombrar la CLAVE de la columna del Caso 2 (el calculo ya no la lee)",
     RCU, [('        cols_expected = ["Riel"] + [f"Elevador {i+1}" for i in range(n)]',
            '        cols_expected = ["Riel"] + [f"Lift {i+1}" for i in range(n)]'),
           ('                                 **{f"Elevador {i+1}": [0.0] * 4 for i in range(n)}})',
            '                                 **{f"Lift {i+1}": [0.0] * 4 for i in range(n)}})')]),

    ("las filas de la tabla de BSR de Plomada vuelven a «Elevador N»",
     PLU, [('        base = pd.DataFrame({"Elevador": [t("Lift {n}", n=i + 1) for i in range(n)],',
            '        base = pd.DataFrame({"Elevador": [f"Elevador {i+1}" for i in range(n)],')]),

    ("⚠️ la matriz ajustada vuelve a seis decimales (codigo exacto de v533)",
     SV, [("        st.dataframe(survey_adj_df.style.apply(highlight, axis=None).format(precision=1),",
           "        st.dataframe(survey_adj_df.style.apply(highlight, axis=None),")]),

    ("la matriz de cada solucion pierde el formato",
     SV, [("st.dataframe(sol_df.style.apply(sol_highlighter, axis=None).format(precision=1),",
           "st.dataframe(sol_df.style.apply(sol_highlighter, axis=None),")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           EV, [(_REASIGNA, "            # comentario inocuo del control\n" + _REASIGNA)])


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
