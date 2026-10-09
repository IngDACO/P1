# -*- coding: utf-8 -*-
"""Bateria de roturas de v551. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

Las marcadas ⚠️ devuelven lo visto en el recorrido del Panel en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v551"
RU = "core/roster_ui.py"
HU = "core/home_ui.py"
TH = "core/theme.py"
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
    ("⚠️ «Copy previous week» vuelve a pisar sin preguntar",
     RU, [('            st.session_state["_ros_copiar"] = lunes.isoformat()\n            st.rerun()',
           '            R.copiar_semana(grupo, lunes - timedelta(days=7), lunes)\n            st.rerun()')]),
    ("una semana con SOLO notas no sale en el aviso de copiar",
     RU, [('        return any(R._norm_cell((sem or {}).get(d, {}))["items"]\n'
           '                   or str(R._norm_cell((sem or {}).get(d, {}))["nota"]).strip()\n',
           '        return any(R._norm_cell((sem or {}).get(d, {}))["items"]\n')]),
    ("⚠️ «Select all» vuelve al editor de la celda",
     RU, [('key=f"pva_{_wk}_{idx}",\n                                      select_all=False)',
           'key=f"pva_{_wk}_{idx}")')]),
    ("⚠️ el popover de la celda sin generación (se queda abierto)",
     RU, [('key=f"roscel_{_wk}_{_gp}_{idx}", width="stretch"):',
           'key=f"roscel_{_wk}_{idx}", width="stretch"):')]),
    ("el CSS del color de la celda sin generación (la celda pierde su color)",
     RU, [('key = f"roscel_{_wk}_{_gp}_{idx}"      # ⚠️ = la key del popover (v551)',
           'key = f"roscel_{_wk}_{idx}"')]),
    ("«View the day» no sube la generación",
     RU, [('"wk": lunes.isoformat()}\n'
           '                    st.session_state["_ros_pop_gen"] = _gp + 1     # v551 · se cierra\n',
           '"wk": lunes.isoformat()}\n')]),
    ("«Save» no sube la generación",
     RU, [('                                    pass\n'
           '                        st.session_state["_ros_pop_gen"] = _gp + 1     # v551 · se cierra\n',
           '                                    pass\n')]),
    ("⚠️ las tarjetas KPI vuelven a ser pasivas (el clic no lleva a ningún sitio)",
     RU, [('            st.session_state["_pnl_ir"] = accion\n', '            pass\n')]),
    ("«Shift clashes» lleva a Compliance en vez de al Radar",
     RU, [('t("overlapping time slots"), theme.ROJO if choques else theme.GRIS_TXT,\n'
           '            {"tool": "radar"}),',
           't("overlapping time slots"), theme.ROJO if choques else theme.GRIS_TXT,\n'
           '            {"tool": "cumpl"}),')]),
    ("«Free today» no cambia de vista",
     RU, [('theme.AZUL, {"vista": "👀 Disponibilidad", "dia": d}),',
           'theme.AZUL, {"tool": "cumpl"}),')]),
    ("⚠️ las líneas del Radar no abren la ficha",
     RU, [('                    st.session_state["_panel_ficha"] = _u\n',
           '                    pass\n')]),
    ("el Radar vuelve al español (« y »)",
     RU, [('_lbls = " and ".join(', '_lbls = " y ".join(')]),
    ("⚠️ Compliance vuelve a decir «not clocked in yet» de un día pasado",
     RU, [('                    elif fecha < hoy:\n', '                    elif False:\n')]),
    ("⚠️ «Free» y «Assign» vuelven a abrir en el lunes",
     RU, [('    return dias.index(_hk) if _hk in dias else 0\n', '    return 0\n')]),
    ("el catálogo vuelve al español («Activar»)",
     RU, [('t("Activate") if not _act else t("Deactivate")',
           '"Activar" if not _act else t("Deactivate")')]),
    ("⚠️ «←» vuelve a apilar solo la sección",
     HU, [('    cur = _donde(cur)\n', '    cur = (cur, None)\n')]),
    ("`_donde` sin normalizar (primera visita = falso cambio, Atrás que no hace nada)",
     HU, [('    return (cur, sub if sub in _ids else (_ids[0] if _ids else None))',
           '    return (cur, sub)')]),
    ("«←» ignora la sub-pestaña al volver",
     HU, [('        navegar(_sec, _sub)', '        navegar(_sec)')]),
    ("una sesión de antes de v551 apila un falso cambio al desplegar",
     HU, [('        prev = (prev, cur[1] if prev == cur[0] else None)',
           '        prev = (prev, None)')]),
    ("⚠️ el selector segmentado pierde el resaltado (`data-selected`)",
     TH, [('[class*="st-key-cpxseg_"] [data-testid="stRadioOption"][data-selected="true"] {{\n'
           '  background: #e8eef6 !important;',
           '[class*="st-key-cpxseg_"] [data-testid="stRadioOption"][data-selected="false"] {{\n'
           '  background: #e8eef6 !important;')]),
    ("⚠️ vuelven las bolitas del selector segmentado",
     TH, [(':not([data-testid]) {{\n  display: none !important;',
           ':not([data-testid]) {{\n  display: flex !important;')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           RU, [("    # v551 · «Asignar» salía en español y sin `t()`",
                 "    # v551 · «Asignar» salía en español y sin `t()` (control)")])


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
