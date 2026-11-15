# -*- coding: utf-8 -*-
"""Batería de roturas de v676. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v676"
TOPE_S = 500
RO = "core/roster.py"
RU = "core/roster_ui.py"
PR = "core/projects.py"
PU = "core/projects_ui.py"
AU = "core/ausencias.py"
RT = "core/route_ui.py"

ROTURAS = [
    # ── H3 ──
    ("⚠️ H3 · el fin de semana vuelve a la semana que acaba", RO,
     [("    return lunes_de(d) + timedelta(days=7) if d.weekday() >= 5 else lunes_de(d)", "    return lunes_de(d)")]),
    ("H3 · el Panel no usa la semana de trabajo", RU,
     [("        st.session_state[k] = R.semana_de_trabajo().isoformat()", "        st.session_state[k] = R.lunes_de().isoformat()")]),
    ("H3 · la tarjeta vuelve a «today is not in this view»", RU,
     [('    if d is None and clock.today().weekday() >= 5 and lunes == R.semana_de_trabajo():',
       '    if False:')]),
    ("H3 · la ruta del día en domingo vuelve a hoy", RT,
     [("                        _ini = _R.semana_de_trabajo(_hoy)\n", "                        pass\n")]),
    # ── H4 ──
    ("⚠️ H4 · una obra terminada no cuenta como cerrada", PR,
     [('        if es_completada(p) or es_cancelada(p) or str(p.get("Status", "")) == "Archived":',
       '        if es_cancelada(p) or str(p.get("Status", "")) == "Archived":')]),
    ("H4 · una archivada no cuenta como cerrada", PR,
     [('        if es_completada(p) or es_cancelada(p) or str(p.get("Status", "")) == "Archived":',
       '        if es_completada(p) or es_cancelada(p):')]),
    ("⚠️ H4 · copiar la semana vuelve a arrastrar las obras cerradas", RO,
     [("        if cerradas:\n            dias = _sin_cerradas(dias, cerradas, tidx)\n",
       "        if False:\n            dias = _sin_cerradas(dias, cerradas, tidx)\n")]),
    ("H4 · _sin_cerradas deja la obra cerrada", RO,
     [("                 if not ((proyecto_de(it[\"asig\"], tidx) or it[\"asig\"]) in cerradas)]",
       "                 ]")]),
    ("H4 · en_obras_cerradas no ve ninguna", RO,
     [("                if pid and pid in cerradas:\n", "                if False:\n")]),
    ("⚠️ H4 · el Radar no enseña las obras cerradas", RU,
     [("        _radar_cerradas(grupo, _ce)            # v676\n", "")]),
    ("H4 · el Radar no las cuenta", RU,
     [("         + len(_lg) + len({pid for _u, pid, _d in _ce}))", "         + len(_lg))")]),
    ("H4 · el Radar vuelve a buscar certificados en obras cerradas", RU,
     [("                if not pid or pid in _cerradas:", "                if not pid:")]),
    ("H4 · liberar quita también lo de HOY y antes", RU,
     [("    _man = clock.today(grupo) + timedelta(days=1)\n    n = R.limpiar_proyecto(grupo, pid, desde=_man)",
       "    _man = clock.today(grupo) + timedelta(days=1)\n    n = R.limpiar_proyecto(grupo, pid, desde=None)")]),
    ("H4 · «Copy previous week» copia las cerradas", RU,
     [("lunes - timedelta(days=7), lunes, cerradas=_cerradas)", "lunes - timedelta(days=7), lunes)")]),
    ("⚠️ H4 · la lista de cierre no cuenta el tablero", PU,
     [("        if _dd:\n            out.append(t(\"**{n}** day(s) still on the board from tomorrow: {who}.\"",
       "        if False:\n            out.append(t(\"**{n}** day(s) still on the board from tomorrow: {who}.\"")]),
    ("H4 · la lista de cierre sin el botón de liberar", PU,
     [("            if _hay:\n                st.button(t(\":material/event_busy: Free it on the board from tomorrow\"), key=f\"cierre_lib_{pid}\",",
       "            if False:\n                st.button(t(\":material/event_busy: Free it on the board from tomorrow\"), key=f\"cierre_lib_{pid}\",")]),
    # ── H11 ──
    ("⚠️ H11 · Compliance vuelve a comparar un día que no ha llegado", RU,
     [("        if fecha > hoy:\n            _et0 = _etq(staff, grupo)", "        if False:\n            _et0 = _etq(staff, grupo)")]),
    # ── H5 ──
    ("⚠️ H5 · antes de empezar vuelve a «on plan · day -1»", PU,
     [("    _antes = (not _hecha) and (not _quieta) and _ini0 is not None and _ini0 > _hoy0",
       "    _antes = False")]),
    ("H5 · «tomorrow» se pierde", PU,
     [('.replace("{c}", t("tomorrow") if _faltan0 == 1 else t("in {n} days", n=_faltan0))',
       '.replace("{c}", t("in {n} days", n=_faltan0))')]),
    # ── H15 ──
    ("⚠️ H15 · la ausencia vuelve a marcar el fin de semana vacío", AU,
     [("                elif d.weekday() >= 5 and not incluye_findes(a) and not [", "                elif False and not [")]),
    ("H15 · una celda de ausencia vuelve a abrir el fin de semana", RO,
     [('            _it = [i for i in _norm_cell(_c)["items"] if i["asig"] not in ESTADOS]',
       '            _it = _norm_cell(_c)["items"]')]),
    ("H15 · una ausencia con fines de semana deja de marcarlos", AU,
     [("                elif d.weekday() >= 5 and not incluye_findes(a) and not [",
       "                elif d.weekday() >= 5 and not [")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", RO,
           [("def semana_de_trabajo(d=None) -> date:\n", "def semana_de_trabajo(d=None) -> date:  # (control)\n")])


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
