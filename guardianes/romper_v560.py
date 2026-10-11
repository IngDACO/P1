# -*- coding: utf-8 -*-
"""Bateria de roturas de v560. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Projects y del Home en producción.
Un argumento filtra por subcadena de la descripción (re-correr solo algunas).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v560"
PU = "core/projects_ui.py"
SC = "core/schedule.py"
EX = "core/expenses.py"
IN = "core/incrustar.py"
HU = "core/home_ui.py"
FL = "core/flash.py"
TC = "core/timeclock.py"
TB = "core/tabla.py"
AU = "core/auth_ui.py"
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
    ("⚠️ «TODAY» vuelve a pisar el subtítulo", SC,
     [('y="{gantt_top-8:.1f}" text-anchor="middle" ', 'y="{gantt_top-11:.1f}" text-anchor="middle" '),
      ("f'<text x=\"18\" y=\"35\" font-size=\"8.5\" fill=\"#5b6472\">'",
       "f'<text x=\"18\" y=\"39\" font-size=\"8.5\" fill=\"#5b6472\">'")]),
    ("⚠️ el recibo vuelve a borrar lo escrito al dar error", PU,
     [('        with st.form(f"{key_prefix}_add_{pid}{_sf}", clear_on_submit=False):\n',
       '        with st.form(f"{key_prefix}_add_{pid}{_sf}", clear_on_submit=True):\n')]),
    ("el recibo ya no se vacía al guardar", PU,
     [('                        st.session_state[f"_rec_gen_{key_prefix}_{pid}"] = _rg + 1\n', '')]),
    ("⚠️ «Add activity» vuelve a borrar lo escrito", PU,
     [('clear_on_submit=False):\n                st.markdown(t("**:material/add: Add activity**"))',
       'clear_on_submit=True):\n                st.markdown(t("**:material/add: Add activity**"))')]),
    ("«Add activity» ya no se vacía al añadir", PU,
     [('                            st.session_state[f"_addact_gen_{pid}"] = _ag + 1\n', '')]),
    ("⚠️ la empresa vuelve a borrar lo escrito", AU,
     [('    with st.form(f"form_grupo_{_fg}", clear_on_submit=False):\n',
       '    with st.form(f"form_grupo_{_fg}", clear_on_submit=True):\n')]),
    ("la empresa ya no se vacía al crear", AU,
     [('                st.session_state["_form_grupo_gen"] = _fg + 1\n', '')]),
    ("⚠️ el riel vuelve a borrar lo escrito", AU,
     [('        with st.form(f"form_riel_{_fr}", clear_on_submit=False):\n',
       '        with st.form(f"form_riel_{_fr}", clear_on_submit=True):\n')]),
    ("el riel ya no se vacía al añadir", AU,
     [('                        st.session_state["_form_riel_gen"] = _fr + 1\n', '')]),
    ("⚠️ el gasto vuelve al eje por posición", EX,
     [("    def sx(i):   return ML + (_dia[i] / _span) * pw\n",
       "    def sx(i):   return ML + (i / max(1, n - 1)) * pw\n")]),
    ("las fechas del gasto se vuelven a montar", EX,
     [("        if not _et or sx(i) - sx(_et[-1]) >= _MIN:\n",
       "        if True:\n")]),
    ("⚠️ la última fecha se monta sobre la anterior", EX,
     [("        if sx(n - 1) - sx(_et[-1]) < _MIN and len(_et) > 1:\n            _et.pop()\n", "")]),
    ("⚠️ el filtro de ritmo vuelve a una columna estrecha", PU,
     [("    _filt = st.radio(t(\"Filter\"), [\"Todos\", \"🔴 Retraso\", \"🟢 Adelanto\", \"⏸ En pausa\"],\n",
       "    _filt = _fc1.radio(t(\"Filter\"), [\"Todos\", \"🔴 Retraso\", \"🟢 Adelanto\", \"⏸ En pausa\"],\n")]),
    ("⚠️ el recuadro deja de volver a medirse", IN,
     [("        h = (h[:_f] + _REMEDIR + h[_f:]) if _f >= 0 else (h + _REMEDIR)\n", "")]),
    ("el re-medido se sale del <body>", IN,
     [("        h = (h[:_f] + _REMEDIR + h[_f:]) if _f >= 0 else (h + _REMEDIR)\n",
       "        h = h + _REMEDIR\n")]),
    ("⚠️ la campana vuelve a 33 px en escritorio", HU,
     [("        \".st-key-cpxtop [data-testid='stColumn']:nth-child(1){flex:0 0 44px !important;\"\n"
       "        \"min-width:44px !important;}\"\n"
       "        \".st-key-cpxtop [data-testid='stColumn']:nth-child(4){flex:0 0 64px !important;\"\n"
       "        \"min-width:64px !important;}\"\n",
       "        \".st-key-cpxtop [data-testid='stColumn']:nth-child(1){flex:0 0 44px !important;\"\n"
       "        \"min-width:44px !important;}\"\n")]),
    ("⚠️ la fila de la barra vuelve a saltar de línea", HU,
     [("        \".st-key-cpxtop [data-testid='stHorizontalBlock']{flex-wrap:nowrap !important;}\"\n", "")]),
    ("la campana del móvil vuelve a 44 px", HU,
     [("        # v560 · en el móvil la campana tampoco cabía en 44 px («🔔·»): 64.\n"
       "        \".st-key-cpxtop [data-testid='stColumn']:nth-child(4){flex:0 0 64px !important;\"\n"
       "        \"min-width:64px !important;}\"\n", "")]),
    ("⚠️ «Refresh» vuelve a solo borrar la lectura", PU,
     [("                            pass\n"
       "                        st.session_state[key] = chat_agent.admin_briefing(grupo)\n",
       "                            pass\n"
       "                        st.session_state.pop(key, None)\n")]),
    ("«Refresh» redacta con los datos de antes (caché)", PU,
     [("                            admin_digest.group_digest.clear()     # los hechos, de ahora\n",
       "                            pass\n")]),
    ("⚠️ la URL vuelve a quedarse sin `&p=`", HU,
     [('        prj = (st.session_state.get("_prjsel_pending")\n'
       '               or st.session_state.get("_admin_open_proj"))\n',
       '        prj = st.session_state.get("_admin_open_proj")\n')]),
    ("⚠️ el aviso vuelve a perderse en el relanzamiento", FL,
     [("        if _prev and ahora - _prev[1] <= _GRACIA_S:\n            cola = list(_prev[0])\n",
       "        if False:\n            pass\n")]),
    ("el aviso se queda pegado para siempre", FL,
     [("        if _prev and ahora - _prev[1] <= _GRACIA_S:\n",
       "        if _prev:\n")]),
    ("Contacts vuelve a «Ficha»", TB,
     [('    "Ficha": "Record",', '    "Ficha_": "Record",')]),
    ("⚠️ el fichaje vuelve a «2026-10-11 16:36:14»", TC,
     [("    return d.strftime(\"%H:%M\") if d.date() == hoy else d.strftime(\"%d/%m/%Y %H:%M\")\n",
       "    return str(ts)\n")]),
    ("el aviso de salida vuelve a la marca de la hoja", TC,
     [("Clock OUT {t('at')} {_ts_legible(out_ts)}", "Clock OUT {t('at')} {out_ts}")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           FL, [("    `_GRACIA_S` segundos siguientes, si no hay mensajes nuevos.",
                 "    `_GRACIA_S` segundos siguientes, si no hay mensajes nuevos. (control)")])


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
        # Solo comprobar que cada ancla casa UNA vez (sin tocar nada).
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
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
    for desc, rel, cambios in _rot:
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
