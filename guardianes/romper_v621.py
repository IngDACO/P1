# -*- coding: utf-8 -*-
"""Batería de roturas de v621. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v621"
TOPE_S = 240
TC = "core/timeclock.py"
TU = "core/timeclock_ui.py"
HU = "core/home_ui.py"
CA = "core/chat_agent.py"

ROTURAS = [
    ("⚠️ las 33,39 h: el motor vuelve a cerrar un olvido «ahora»", TC,
     [("    if out_ts is None and _de_otro_dia(target_in):\n        return False, _msg_olvido()\n", "")]),
    ("⚠️ se ficha con un olvido abierto", TC,
     [('           and _de_otro_dia(r.get("Clock In")) for r in records):\n        return False, _msg_olvido()\n',
       '           and _de_otro_dia(r.get("Clock In")) for r in records):\n        pass\n')]),
    ("una entrada de hoy cuenta como olvido", TC,
     [("            < datetime.strptime(_now(), FMT).date()\n", "            <= datetime.strptime(_now(), FMT).date()\n")]),
    ("⚠️ la jornada se cierra aunque la obra no se pueda cerrar", TC,
     [("        if not ok:\n            return False, msg\n    return clock_out(nombre, grupo, tipo=TIPO_GENERAL",
       "    return clock_out(nombre, grupo, tipo=TIPO_GENERAL")]),
    ("dejar una obra vuelve a no decir cuál", TC,
     [('t("Left {p} at {h} · {n} h.", p=_nombre_md(target_prj),', 't("Left {p} at {h} · {n} h.", p="the project",')]),
    ("el nombre en el aviso, sin escapar", TC,
     [("    return literal_md(proyecto) or t(\"the project\")\n", "    return str(proyecto or \"\") or t(\"the project\")\n")]),
    ("⚠️ la pantalla vuelve a ofrecer los cierres con un olvido", TU,
     [("    if _aviso_olvido(nombre, grupo, usuario, sess):\n        _privacidad()\n        return\n",
       "    _aviso_olvido(nombre, grupo, usuario, sess)\n")]),
    ("⚠️ el lateral vuelve a ofrecer cerrar con un olvido", TU,
     [("    if timeclock.olvidos(sess):\n        _sidebar_olvido()\n    elif gen or prj:\n", "    if gen or prj:\n")]),
    ("⚠️ el olvido dice cerrado aunque falle", TU,
     [("        if _mal:\n            flash.error(_mal[0])\n        else:\n            flash.exito(t(\"Session closed at the time given. Your supervisor will review it.\"))\n",
       "        flash.exito(t(\"Session closed at the time given. Your supervisor will review it.\"))\n")]),
    ("⚠️ un cierre antes de la entrada a la obra (horas negativas)", TU,
     [("    ok_rango = ci_max is not None and ci_max < fin <= clock.now()\n",
       "    ok_rango = ci_min is not None and ci_min < fin <= clock.now()\n")]),
    ("la fecha del olvido vuelve a ISO", TU,
     [("**{timeclock._ts_legible(s['clock_in'])}**", "**{s['clock_in']}**")]),
    ("⚠️ la baja vuelve a salir tras trabajar", TU,
     [('if rol == "field" and not gen and not prj and hoy["general"] <= 0 and hoy["proyecto"] <= 0:',
       'if rol == "field" and not gen and not prj:')]),
    ("⚠️ la franja sin escapar", TU,
     [("""f"{html.escape(prj['proyecto'] or '—')} · {t('since')}""", """f"{prj['proyecto'] or '—'} · {t('since')}""")]),
    ("⚠️ las barras sin escapar", TU, [("{html.escape(nom)}</div>", "{nom}</div>")]),
    ("«You are on» sin escapar", TU,
     [("""t("You are on **{p}**", p=literal_md(prj['proyecto'] or '—'))""",
       """t("You are on **{p}**", p=prj['proyecto'] or '—')""")]),
    ("⚠️ tocar una cifra deja de abrir el historial", TU,
     [('''st.session_state["_tc_hist_gen"] = int(st.session_state.get("_tc_hist_gen", 0)) + 1\n''', "pass\n")]),
    ("⚠️ el historial vuelve a la salida sin día", TU,
     [("""    _h = _s[11:16] if _s[:10] == _e[:10] else f"{_s[8:10]}/{_s[5:7]} {_s[11:16]}"\n""",
       "    _h = _s[11:16]\n")]),
    ("una entrada abierta enseña 0 horas", TU,
     [("""t("Hours"): f"{f['horas']:.2f}" if _s else "—",""", """t("Hours"): f"{f['horas']:.2f}",""")]),
    ("⚠️ pregunta aunque solo haya una opción", TU, [("if len(_campos) > 1 else _campos[0])", "if len(_campos) > 0 else _campos[0])")]),
    ("⚠️ el lateral vuelve a pedir elegir de una lista de uno", TU,
     [("    if _propios and len(idmap) == 1 and not _hechos:\n", "    if False:\n")]),
    ("⚠️ vuelve el compromiso falso", TU,
     [('st.caption(t(":material/lock: Other workers cannot see your time entries. The office sees "\n'
       '                 "your hours and the sites you clock in to."))',
       """st.caption(t(":material/lock: Management sees the group's hours summary, not each person's detail."))""")]),
    ("el asistente vuelve a decir lo falso", CA,
     [("  Los demás trabajadores no ven los fichajes; la oficina ve las horas de cada persona y sus obras.\n",
       "  Los fichajes son privados; solo el admin ve el reporte de horas del grupo.\n")]),
    ("la barra deja de avisar del olvido", HU,
     [('_txt = (t("Entry left open") if timeclock.olvidos(_ses) else t("On a project") if _prj else',
       '_txt = (t("On a project") if _prj else')]),
    ("el banner reclama el Pre-Start de hoy por una obra de ayer", HU,
     [("        if not prj or timeclock.olvidos(ses):\n", "        if not prj:\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", TU,
           [('    """v621 · Una entrada de un día anterior abierta: ni cronómetro', '    """(control) v621 · Una entrada de un día anterior abierta: ni cronómetro')])


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
