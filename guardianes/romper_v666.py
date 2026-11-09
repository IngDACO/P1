# -*- coding: utf-8 -*-
"""Batería de roturas de v666. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v666"
TOPE_S = 400
R = "core/roster.py"
RU = "core/roster_ui.py"
PU = "core/projects_ui.py"
AUI = "core/ausencias_ui.py"
CO = "core/correcciones.py"
CUI = "core/correcciones_ui.py"
CT = "core/chat_tools.py"
CA = "core/chat_agent.py"
O = "core/orders.py"

ROTURAS = [
    # ── H14 · el cálculo ──
    ("⚠️ cuenta también las obras terminadas o en pausa", R,
     [('        if not pid or str(p.get("Status", "")) not in ACTIVAS_PLAN:\n', "        if not pid:\n")]),
    ("cuenta las obras que empiezan más adelante", R,
     [("        if not ini or ini > dom or (fin and fin < lunes):\n", "        if not ini or (fin and fin < lunes):\n")]),
    ("cuenta las obras ya acabadas", R,
     [("        if not ini or ini > dom or (fin and fin < lunes):\n", "        if not ini or ini > dom:\n")]),
    ("⚠️ todo jefe sale aunque tenga su día", R,
     [("            if (u, pid) not in hay:\n                jefes.append", "            if True:\n                jefes.append")]),
    ("⚠️ ninguna obra sale sin gente", R,
     [("        if pid not in con_gente:\n            obras.append(pid)", "        if False:\n            obras.append(pid)")]),
    ("una fecha a mitad de semana pide otra semana", R,
     [("    lunes = lunes_de(lunes)                       # cualquier día", "    pass                       # cualquier día")]),
    # ── H14 · el Radar ──
    ("⚠️ el Radar no lo enseña", RU,
     [("        _radar_sin_gente(grupo, sp)            # v666", "        pass            # v666")]),
    ("la línea no abre Assign", RU,
     [('    st.session_state["_panel_tool"] = "asignar"\n', "")]),
    ("el jefe de una obra ya listada se repite", RU,
     [('if pid not in set(sp.get("obras", []))]', "]")]),
    ("«Radar (n)» no lo cuenta", RU,
     [('_n_rad = len(_scan[0]) + len(_scan[1]) + len(_sp["obras"]) + len(_sp["jefes"])', "_n_rad = len(_scan[0]) + len(_scan[1])")]),
    # ── H14 · la ficha y el alta ──
    ("⚠️ la ficha no avisa", PU,
     [("    _plan_semana_section(pid, grupo, prj)            # v666", "    pass            # v666")]),
    ("el aviso de la ficha le sale al campo", PU,
     [('    if str((st.session_state.get("auth") or {}).get("rol", "")) != "administrator":\n        return\n    try:\n        from core import roster as R',
       "    try:\n        from core import roster as R")]),
    ("el aviso sale en una obra completada", PU,
     [('        if str(prj.get("Status", "")) not in R.ACTIVAS_PLAN:\n            return\n', "")]),
    ("«Plan it» no lleva a Planning", PU,
     [('    st.session_state["_admin_nav_pending"] = ("planificacion", "🎛 Panel")\n', "")]),
    ("el alta vuelve a callarse que la obra queda sin nadie", PU,
     [('"overwritten, so **nobody is planned on this job yet**. Use «Plan it» in its Status tab "', '"overwritten. "')]),
    # ── H37 ──
    ("⚠️ vuelve «(2 day(s))» para 1 día con 2 obras", AUI,
     [('_nd = len({c["fecha"] for c in ch})', "_nd = len(ch)")]),
    # ── H31 ──
    ("⚠️ la nómina generada después no se ve", CO,
     [('    return nomina_que_cubre(grupo, str((r or {}).get("User", "")), str((r or {}).get("NewValue", "")))', '    return ""')]),
    ("la pantalla vuelve a leer solo lo anotado", CUI,
     [("_nom_id = C.nomina_de(r, grupo)", '_nom_id = str(r.get("PayslipCovers", "")).strip()')]),
    ("la bandeja del asistente vuelve a leer solo lo anotado", CT,
     [('"already_on_payslip": CO.nomina_de(r, g),', '"already_on_payslip": r.get("PayslipCovers", ""),')]),
    ("el asistente no sabe que no ve las nóminas", CT,
     [('        "payslips": "You cannot see payslips.', '        "payslips_note": "You cannot see payslips.')]),
    # ── H30 ──
    ("⚠️ el equipo vuelve a ser de un solo día", CT,
     [("dias = [dia + _td(days=i) for i in range((hasta - dia).days + 1)]", "dias = [dia]")]),
    ("una ausencia de varios días sale repetida", CT,
     [('_por_id = {str(r.get("ID", "")): r for d in dias', '_por_id = {str(r.get("ID", "")) + str(d): r for d in dias')]),
    ("sin lo que a la semana le falta", CT,
     [('"absent": _aus, "the_week_on_the_board": _hueco,', '"absent": _aus, "the_week_on_the_board": {},')]),
    ("el rango no tiene tope", CT,
     [("(hasta - dia).days > 6:", "(hasta - dia).days > 60:")]),
    # ── H34 ──
    ("⚠️ toda obra del día sale como planificada", CT,
     [('"planned_for_you_today": pid in _plan,', '"planned_for_you_today": True,')]),
    # ── H29 ──
    ("⚠️ idioma_de nunca sabe el idioma", CA,
     [('    if es >= 2 and es > en:\n        return "Spanish"\n    if en >= 2 and en > es:\n        return "English"\n', "")]),
    ("el recordatorio no nombra el idioma", CA,
     [("    _l = idioma_de(pregunta)\n", '    _l = ""\n')]),
    # ── H45 ──
    ("⚠️ vuelve «Orden» al gasto", O,
     [("descripcion=f\"Order {r.get('ID','')}", "descripcion=f\"Orden {r.get('ID','')}")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", R,
           [("(la clave del tablero)\n    dom = lunes", "(la clave del tablero, control)\n    dom = lunes")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
