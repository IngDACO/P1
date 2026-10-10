# -*- coding: utf-8 -*-
"""Bateria de roturas de v558. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Projects en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v558"
PU = "core/projects_ui.py"
IU = "core/invoices_ui.py"
LU = "core/location_ui.py"
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
    ("⚠️ el ritmo vuelve a llamarse «Status» (y lo pisa el estado)", PU,
     [('            "Pace": _sit,\n', '            "Status": _sit,\n')]),
    ("⚠️ la comparativa de Agrupaciones vuelve a la «Status» repetida", PU,
     [('            "Pace": (f"{delays[pid]:.0f} d behind" if pid in delays',
       '            "Status": (f"{delays[pid]:.0f} d behind" if pid in delays')]),
    ("⚠️ la casilla del nombre repetido deja de valer (homónima imposible)", PU,
     [("            if dups and not st.session_state.get(_k_dup(_nn)):\n",
       "            if dups:\n")]),
    # ⚠️ La 1ª versión solo cambiaba el 1er argumento y ESCAPÓ sin ser un hueco: la
    # duración sale de `custom_rows=_filas_etapas(…, ns, …)`, así que la vista previa
    # seguía al NS. Rota de verdad = la vista previa deja de leer el NS (las dos cosas).
    ("⚠️ la fecha estimada deja de seguir al NS", PU,
     [("                _sch_prev = build_schedule(int(ns), f_ini, {},\n"
       "                                           custom_rows=_filas_etapas(_tipo, ns, key))\n",
       "                _sch_prev = build_schedule(2, f_ini, {},\n"
       "                                           custom_rows=_filas_etapas(_tipo, 2, key))\n")]),
    ("⚠️ un Delivery vuelve a leer `sched` (revienta tras escribir)", PU,
     [('            _fin = _fin_d.strftime("%Y-%m-%d") if _fin_d else ""\n',
       '            _fin = sched.get("fecha_fin").strftime("%Y-%m-%d")\n')]),
    ("tras crear ya no se abre la obra nueva", PU,
     [('                st.session_state["_admin_open_proj"] = str(res)\n',
       '                pass\n')]),
    ("⚠️ el alta deja de vaciarse tras crear", PU,
     [("            st.session_state[_kgen] = _gen + 1\n", "            pass\n")]),
    ("el éxito vuelve a `st.success` (se pierde en el rerun)", PU,
     [('            flash.exito((t(":material/check_circle: Project **{p}** created',
       '            st.success((t(":material/check_circle: Project **{p}** created')]),
    ("el alta vuelve a `st.stop()`", PU,
     [("                    # cortaba también todo lo que la pantalla pinta después.\n"
       "                    return\n",
       "                    # cortaba también todo lo que la pantalla pinta después.\n"
       "                    st.stop()\n")]),
    ("la fecha de inicio vuelve al ISO", PU,
     [('key=f"np_ini_{key}",\n                              format="DD/MM/YYYY")',
       'key=f"np_ini_{key}",\n                              format="YYYY/MM/DD")')]),
    ("⚠️ las tarjetas vuelven a «\\$133»", PU,
     [("{theme.dinero_html(_pf, 0)}</b>", "{theme.dinero(_pf, 0)}</b>")]),
    ("⚠️ las tarjetas vuelven a «33.0d»", PU,
     [("{_MI('cancel','#d64541')} {int(round(_dl))} d", "{_MI('cancel','#d64541')} {_dl}d")]),
    ("las tarjetas vuelven a «s/ppto»", PU,
     [('                _ppto = t("no budget")\n', '                _ppto = "s/ppto"\n')]),
    ("⚠️ el filtro vuelve a las bolitas", PU,
     [('key="cpxseg_cart_filt", label_visibility="collapsed",',
       'key="cart_filt", label_visibility="collapsed",')]),
    ("⚠️ la vista se olvida al salir", PU,
     [('key="cpxseg_cart_view", label_visibility="collapsed",\n'
       '                       persist_state="session")',
       'key="cpxseg_cart_view", label_visibility="collapsed")')]),
    ("el tipo vuelve a decir «Todos»", PU,
     [('                             format_func=lambda o: t("All types") if o == "Todos" else o,\n',
       '')]),
    ("⚠️ el contador vuelve a contar el grupo entero", PU,
     [('    _nr = sum(1 for p in _base_f if delays.get(str(p.get("ID", ""))))\n',
       '    _nr = sum(1 for p in proys if delays.get(str(p.get("ID", ""))))\n')]),
    ("⚠️ el contador vuelve a ser pasivo", PU,
     [('                st.session_state["_cart_filt_pending"] = "Todos" if _activo else _val\n',
       '                pass\n')]),
    ("sin coincidencias, sin «Clear filters»", PU,
     [('                st.session_state["_cart_pending"] = {}\n', '                pass\n')]),
    ("⚠️ el Home vuelve a abrir la cartera en «All»", PU,
     [('                        st.session_state["_cart_pending"] = {"filtro": "🔴 Retraso"}\n',
       '                        pass\n')]),
    ("el Home deja de pasar las obras del indicador", PU,
     [('"motivo": lbl, "ids": [str(x.get("id", "")) for x in _solo_ids]}}',
       '"motivo": lbl, "ids": []}}')]),
    ("⚠️ «Invoice» sin fichas vuelve a ser un callejón", IU,
     [('                st.session_state["_cli_open"] = C._norm(_cli_obra)\n', '')]),
    ("el nombre del cliente se pierde al pulsar", IU,
     [('            st.session_state["_fac_cli_sin_ficha"] = _av0\n', '')]),
    ("⚠️ el buscador del mapa vuelve al icono literal", LU,
     [('label_visibility="collapsed", icon=":material/search:",\n'
       '                      placeholder=t("Search address…"))',
       'label_visibility="collapsed",\n'
       '                      placeholder=t(":material/search: Search address…"))')]),
    ("el mapa vuelve a 500 px fijos", LU,
     [("height=360, use_container_width=True,", "height=360,")]),
    ("«no encuentro la dirección» vuelve a perderse", LU,
     [("            flash.aviso(t(\"I could not find that address.",
       "            st.warning(t(\"I could not find that address.")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [("    # v558 · lo que llegó del Home (un indicador): solo esas obras, hasta quitarlo.",
                 "    # v558 · lo que llegó del Home (un indicador): solo esas obras, hasta quitarlo. (control)")])


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
