# -*- coding: utf-8 -*-
"""Bateria de roturas de v544. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las primeras devuelven lo que se vio en producción en el Home del admin: tarjetas KPI
en una línea, el mismo pin que no se reabre, «Hours» que abre en «Today», la campana
muda con 4 urgentes y los textos «paradas»/«alarma(s)»/«pendings»/«18.0».
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v544"
TH = "core/theme.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
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
    ("⚠️ las tarjetas KPI vuelven a una línea (sin `white-space:normal`)",
     TH, [("  white-space: normal !important; width: 100%;\n", "  width: 100%;\n")]),

    ("los <p> de la tarjeta vuelven a ser inline",
     TH, [("  display: block !important;\n}}\n/* Tarjeta KPI de TRES",
           "}}\n/* Tarjeta KPI de TRES")]),

    ("⚠️ el mapa sin generación en la clave (el mismo pin no se reabre)",
     HU, [("key=f\"home_map_{st.session_state.get('_home_map_gen', 0)}\"",
           "key=\"home_map\"")]),

    ("«Back to the list» no limpia el mapa",
     HU, [("        st.session_state.pop(\"_home_proj_sel\", None)\n        _mapa_sin_clic()\n"
           "        st.rerun()\n",
           "        st.session_state.pop(\"_home_proj_sel\", None)\n        st.rerun()\n")]),

    ("«See the full project» no limpia el mapa",
     HU, [("        _mapa_sin_clic()\n        st.session_state[\"_prjsel_pending\"] = str(pid)\n",
           "        st.session_state[\"_prjsel_pending\"] = str(pid)\n")]),

    ("un mapa sin clic NO olvida el último pin (volver al Home)",
     HU, [("            if not _clk:\n", "            if False:\n")]),

    ("⚠️ «Hours» vuelve a abrir Horas en «Today»",
     PU, [("        st.session_state[\"_gh_per_pending\"] = \"Todo\"\n", "")]),

    ("Horas no aplica el periodo que pide la tarjeta",
     PU, [("    if _per_pend in _PERH:\n", "    if False:\n")]),

    ("⚠️ la campana vuelve a callarse los urgentes del admin",
     HU, [("    if _rol() == \"administrator\":\n        try:\n            from core import admin_digest\n",
           "    if False:\n        try:\n            from core import admin_digest\n")]),

    ("al CAMPO le entran los urgentes de gestión",
     HU, [("    if _rol() == \"administrator\":\n        try:\n            from core import admin_digest\n",
           "    if _rol() in (\"administrator\", \"field\"):\n        try:\n"
           "            from core import admin_digest\n")]),

    ("las alertas vuelven a ser texto pasivo",
     HU, [("            if not a.get(\"destino\"):\n", "            if True:\n")]),

    ("la credencial abre la ficha con el login, sin el nombre",
     HU, [("        st.session_state[\"gp_fichasel\"] = f\"{_nom} ({_u})\"     # pre-selecciona la persona\n",
           "        st.session_state[\"gp_fichasel\"] = _u\n")]),

    ("⚠️ vuelve «paradas»",
     HU, [("t(\":material/elevator: {n} stops\")", "t(\":material/elevator: {n} paradas\")")]),

    ("vuelve «alarma(s)»",
     HU, [("t(\":material/notifications: 1 alarm\") if al == 1 else\n",
           "t(\":material/notifications: 1 alarma(s)\") if al == 1 else\n")]),

    ("«1 stop» con el plural mal («1 stops»)",
     HU, [("(t(\":material/elevator: 1 stop\") if _ns == 1 else",
           "(t(\":material/elevator: {n} stops\").replace(\"{n}\", \"1\") if _ns == 1 else")]),

    ("vuelve «18.0 d behind»",
     HU, [("str(int(round(dl)))", "str(dl)")]),

    ("vuelve «18.0d» en la lista",
     HU, [("{int(round(_dl))}d\"", "{_dl}d\"")]),

    ("las fechas del resumen de obra vuelven a ISO",
     HU, [("    _fi = _fmt_fecha(prj.get(\"StartDate\")) or \"—\"\n",
           "    _fi = str(prj.get(\"StartDate\", \"\") or \"—\")\n")]),

    ("la cuadrilla vuelve a salir por login",
     HU, [("', '.join(_nom.get(x, x) for x in _asg[:6])", "', '.join(_asg[:6])")]),

    ("⚠️ vuelve «pendings»",
     PU, [("f\":red[{_urg} urgent] · {_tot} pending\")",
           "f\":red[{_urg} urgent] · {_tot} pending{'' if _tot == 1 else 's'}\")")]),

    ("los vencidos del resumen vuelven a ISO",
     PU, [("({_fmt_fecha(v['fin'])})", "({v['fin']})")]),

    ("«No contact details» vuelve a los logins",
     PU, [("_nombres_de(d[\"campo_sin_contacto\"][:15], grupo)", "d[\"campo_sin_contacto\"][:15]")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           HU, [("def _mapa_sin_clic():\n", "# comentario inocuo del control\ndef _mapa_sin_clic():\n")])


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
