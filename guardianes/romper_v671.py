# -*- coding: utf-8 -*-
"""Batería de roturas de v671. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v671"
TOPE_S = 500
TC = "core/timeclock.py"
CO = "core/correcciones.py"
PU = "core/projects_ui.py"
RU = "core/roster_ui.py"
PR = "core/payroll.py"
PI = "core/payroll_ui.py"
PP = "core/payslip_pdf.py"
AU = "core/auth.py"
AI = "core/auth_ui.py"

ROTURAS = [
    ("⚠️ H27 · jornadas_largas deja de ver las imposibles", TC,
     [("        if h <= umbral and (co.date() - ci.date()).days < 2:\n            continue\n",
       "        if True:\n            continue\n")]),
    ("⚠️ recortar_jornada no corrige las entradas de obra", TC,
     [("    for proy, vieja in obras:\n", "    for proy, vieja in []:\n")]),
    ("recortar_jornada no avisa de una entrada que empieza después", TC,
     [("        if p0 >= _cn:\n            return False, t(\"The entry on {p} starts at",
       "        if False:\n            return False, t(\"The entry on {p} starts at")]),
    ("recortar_jornada acepta una salida posterior a la registrada", TC,
     [("    if not (_ci < _cn < _co):\n", "    if not (_ci < _cn):\n")]),
    ("la oficina no apunta las correcciones", CO,
     [("        okr, cid = registrar(grupo, usuario, nombre, tipo, proy, CAMPO_OUT, vieja, nueva, motivo=_nota)\n",
       '        okr, cid = False, ""\n')]),
    ("la oficina no las deja aprobadas", CO,
     [("            aprobar(cid, revisor, nota=_nota)\n", "            pass\n")]),
    ("⚠️ Hours deja de enseñar las jornadas imposibles", PU,
     [("    jornadas_largas_section(grupo)\n\n    if not data:", "\n    if not data:")]),
    ("«Fix it» propone la misma hora de entrada", PU,
     [("            _sug = _ci + timedelta(hours=8)\n", "            _sug = _ci\n")]),
    ("⚠️ «Apply» ignora la hora puesta", PU,
     [('j["entrada"], j["salida"],\n                    _dt.combine(_dia, _hora)',
       'j["entrada"], j["salida"],\n                    _dt.combine(_dia, _ci.time())')]),
    ("el Radar no las cuenta", RU,
     [("\n         + len(_lg))", ")")]),
    ("el Radar no lleva a Hours", RU,
     [('            st.session_state["_admin_nav_pending"] = ("finanzas", "⏱ Horas")\n            st.rerun()',
       "            pass\n            st.rerun()")]),
    ("⚠️ H27 · la nómina paga la jornada imposible", PR,
     [("        if clave in largas:\n", "        if False:\n")]),
    ("la nómina no mira las jornadas largas", PR,
     [('            largas.setdefault(_j["usuario"], _j)\n', "            pass\n")]),
    ("H15 · ultimo_hasta devuelve la más antigua", PR,
     [("    return max(_f) if _f else None\n", "    return min(_f) if _f else None\n")]),
    ("H15 · horas_sin_pagar no suma las colillas de ajuste", PR,
     [('        en = round(sum(_num(n.get("Hours")) for n in ns), 2)\n',
       '        en = round(_num(ns[0].get("Hours")), 2)\n')]),
    ("H15 · al saldar no se recalcula el super", PR,
     [("                c[\"monto\"] = round(bruto * sup_pct / 100.0, 2)\n", "                pass\n")]),
    ("⚠️ H15 · se suman horas a una colilla YA pagada", PR,
     [('    if str(n.get("Status", "")).lower() != "pagada":\n        con = conceptos_de(n)\n',
       "    if True:\n        con = conceptos_de(n)\n")]),
    ("⚠️ H15 · «Generate» vuelve a proponer el periodo ya generado", PI,
     [("        _d0 = _ult + timedelta(days=1)\n", "        _d0 = _d0\n")]),
    ("H15 · la vista previa deja de decir «already on»", PI,
    # v672 · re-anclada: detrás de «already on» va «Left out» de quien deja fuera una jornada larga (v672). La misma rotura
     [("                     if k in _ya else t(\"Left out: fix the workday of more than 16 h first\") if k in _fuera\n",
       "                     if False else t(\"Left out: fix the workday of more than 16 h first\") if k in _fuera\n")]),
    ("H15 · la lista de nóminas deja de avisar de las horas sin pagar", PI,
     [('    horas_sin_pagar_section(grupo, "nom_lst")\n', "")]),
    ("H15 · «Settle» no hace nada", PI,
     [('    elif _acc.get("accion") == "saldar":', "    elif False:")]),
    ("H27 · la vista previa no avisa de la jornada imposible", PI,
     [("    if _lg:\n        st.error(t(\":material/error: **Workday of more than 16 h to fix first:**",
       "    if False:\n        st.error(t(\":material/error: **Workday of more than 16 h to fix first:**")]),
    ("⚠️ H25 · la colilla deja de decir el fondo", PP,
     [('        story += [Paragraph(d("Super fund") + ": " + esc_pdf(fondo_super(nomina) or d("not set")), sm)]\n', "")]),
    ("H25 · fondo_super lee otra columna", PP,
     [('.get("SuperFund", "")', '.get("PayrollID", "")')]),
    ("H25 · el detalle deja de avisar de lo que falta", PI,
     [("            if _faltan:\n                st.caption(", "            if False:\n                st.caption(")]),
    ("H25 · Login sin la columna", AU,
     [('                 "SuperFund"]', "                 ]")]),
    ("H25 · la ficha no guarda el fondo", AI,
     [('ok, msg = auth.set_login_setting(sel, "SuperFund", _sf)', 'ok, msg = True, ""')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PR,
           [("def ultimo_hasta(grupo: str):\n", "def ultimo_hasta(grupo: str):  # (control)\n")])


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
