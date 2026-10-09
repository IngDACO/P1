# -*- coding: utf-8 -*-
"""Bateria de roturas de v554. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Day route en producción.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v554"
RT = "core/route_ui.py"
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
    ("⚠️ un día FUTURO vuelve a decir «not clocked in»",
     RT, [('            if fecha > _hoy:\n                _estado = t("🗓️ planned")\n'
           '            elif pid in _fich_pids:\n',
           '            if pid in _fich_pids:\n')]),
    ("HOY vuelve a decir «not clocked in» sin «yet»",
     RT, [('            elif fecha == _hoy:\n                _estado = t("⚠️ not clocked in yet")\n', '')]),
    ("⚠️ «Planned» vuelve a contar ASIGNACIONES",
     RT, [('t(":material/engineering: Planned") + f"\\n\\n{len(con_obra)}',
           't(":material/engineering: Planned") + f"\\n\\n{len(en_obra)}')]),
    ("«No location» vuelve a contar filas persona→obra",
     RT, [('f"\\n\\n{len(pids_sin_coord)}\\n\\n"', 'f"\\n\\n{len(sin_coord)}\\n\\n"')]),
    ("⚠️ el Panel vuelve a abrir en otra semana",
     RT, [('        st.session_state["ros_lunes"] = roster.lunes_de(fecha).isoformat()\n', '')]),
    ("⚠️ al volver, otra vez a HOY (no se recuerda el día)",
     RT, [('        st.session_state["rutadia_fecha"] = st.session_state.get("_rd_dia") or _hoy\n',
           '        st.session_state["rutadia_fecha"] = _hoy\n')]),
    ("el `date_input` vuelve a llevar `value` (aviso en el log)",
     RT, [('cf.date_input(t("Day"), key="rutadia_fecha",',
           'cf.date_input(t("Day"), value=_hoy, key="rutadia_fecha",')]),
    ("⚠️ el nombre de la obra en su tarjeta no la abre",
     RT, [('                        _abrir_obra(s["pid"])\n', '                        pass\n')]),
    ("«No location» con una obra no la abre",
     RT, [('        if len(pids_sin_coord) == 1:\n            _abrir_obra(pids_sin_coord[0])\n',
           '        if False:\n            pass\n')]),
    ("«Sites» con una obra no la abre",
     RT, [('        if len(sitios) == 1:\n            _abrir_obra(next(iter(sitios)))\n',
           '        if False:\n            pass\n')]),
    ("⚠️ «Today's sites» en cualquier día",
     RT, [('st.markdown(t("**Today\'s sites** — in travel order") if _es_hoy else',
           'st.markdown(t("**Today\'s sites** — in travel order") if True else')]),
    ("el pie de «Sites» dice «today» en cualquier día",
     RT, [('else t("with people that day"))', 'else t("with people today"))')]),
    ("vuelve el «of» calcado del español",
     RT, [('t("{weekday} {day} {month}")', 't("{weekday} {day} of {month}")')]),
    ("el aviso de fin de semana vuelve a minúscula",
     RT, [('.replace("{d}", _DIAS_L[fecha.weekday()]))',
           '.replace("{d}", _DIAS_L[fecha.weekday()].lower()))')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           RT, [("    # v554 · el nombre de la obra la ABRE (nada pasivo)",
                 "    # v554 · el nombre de la obra la ABRE (nada pasivo, control)")])


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
