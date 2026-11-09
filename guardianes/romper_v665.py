# -*- coding: utf-8 -*-
"""Batería de roturas de v665. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v665"
TOPE_S = 400
AL = "core/alerts.py"
PU = "core/projects_ui.py"
PS = "core/prestart.py"
PSU = "core/prestart_ui.py"
TU = "core/timeclock_ui.py"
CT = "core/chat_tools.py"
CU = "core/claims_ui.py"

ROTURAS = [
    # ── H21 · el motor ──
    ("⚠️ ninguna alarma es de seguridad", AL,
     [('    return (str((al or {}).get("Type", "")) == "problema"\n',
       '    return False and (str((al or {}).get("Type", "")) == "problema"\n')]),
    ("el near miss deja de ser de seguridad", AL,
     [('"Near Miss/Hazard", "Pre-Start with", "False car check with")', '"Pre-Start with", "False car check with")')]),
    ("⚠️ el motor cierra una de seguridad sin nota", AL,
     [("            if es_seguridad(r) and not nota:\n                return False, _d(NOTA_SEGURIDAD)\n",
       "            if False:\n                return False, _d(NOTA_SEGURIDAD)\n")]),
    ("la nota no se guarda en Resolution", AL,
     [("            if nota:\n                lote.append(", "            if False:\n                lote.append(")]),
    ("la nota se guarda con sus espacios", AL,
     [('    nota = str(nota or "").strip()\n', '    nota = str(nota or "")\n')]),
    # ── H21 · la pantalla ──
    ("⚠️ el ✓ de una de seguridad la vuelve a cerrar de un clic", PU,
     [("                if _seg:\n                    c[1].button(", "                if False:\n                    c[1].button(")]),
    ("«Resolve with this note» no lleva la nota", PU,
     [('on_click=_pedir_resolver, args=(pid, _aid, f"alr_nota_{_aid}"))', "on_click=_pedir_resolver, args=(pid, _aid))")]),
    ("la petición pierde la nota", PU,
     [('"nota": str(st.session_state.get(clave_nota, "") or "") if clave_nota else ""}', '"nota": ""}')]),
    ("la acción diferida no pasa la nota al motor", PU,
     [('gestor=gestor, nota=_pet.get("nota", ""))', "gestor=gestor)")]),
    ("sin el rastro de las resueltas", PU,
     [('    if _res:\n        with st.expander(t(":material/history: Resolved safety alerts',
       '    if False:\n        with st.expander(t(":material/history: Resolved safety alerts')]),
    # ── H21 · el asistente ──
    ("⚠️ el asistente prepara el cierre de una de seguridad sin nota", CT,
     [("    if AL.es_seguridad(r) and not nota:\n        raise _Negado(", "    if False:\n        raise _Negado(")]),
    ("Confirm no pasa la nota", CT,
     [('gestor=True, nota=d.get("note", ""))', "gestor=True)")]),
    ("la tarjeta no lleva la nota", CT,
     [('{"alert_id": str(r.get("ID", "")), "note": nota})', '{"alert_id": str(r.get("ID", ""))})')]),
    # ── H39 · el hito ──
    ("⚠️ vuelve el hito de una actividad ya hecha", PU,
     [('if proximo is None and a["inicio"] > hoy and pct < 100:', 'if proximo is None and a["inicio"] > hoy:')]),
    # ── H40 · la lista de cierre ──
    ("⚠️ la pestaña Status no enseña la lista de cierre", PU,
     [("    _cierre_section(pid, grupo, prj)                 # v665", "    pass                 # v665")]),
    ("la lista olvida las alarmas abiertas", PU,
     [('            if _n:\n                out.append(t("**{n}** open alert(s)',
       '            if False:\n                out.append(t("**{n}** open alert(s)')]),
    ("la lista olvida el To-do", PU,
     [('            if _n:\n                out.append(t("**{n}** To-do item(s)',
       '            if False:\n                out.append(t("**{n}** To-do item(s)')]),
    ("la lista cuenta los activos de OTRAS obras", PU,
     [('                  and str(a.get("LocationRef", "")).strip() == str(pid)]', "                  ]")]),
    ("la lista olvida lo que falta por facturar", PU,
     [('            if _p > 0.5:\n                out.append(t("**{x}** of the price',
       '            if False:\n                out.append(t("**{x}** of the price')]),
    ("una fuente que falla se calla (y parece «nada abierto»)", PU,
     [('        out.append(t("The To-do list could not be checked."))', "        pass")]),
    # ── H33 · el recibo ──
    ("⚠️ un recibo sin foto se guarda sin decir nada", PU,
     [("                elif f is None and not _sin:\n", "                elif False:\n")]),
    ("la lista vuelve a decir «no file» en gris", PU,
     [("cc[0].caption(f\"{_lbl} · :orange[**{t('no receipt')}**]\")", "cc[0].caption(f\"{_lbl} · {t('no file')}\")")]),
    # ── H32 · firmar sabiendo qué ──
    ("pendiente_de_firma no trae el near miss", PS,
     [('"near_miss": bool(d.get("near_miss")), ', '"near_miss": False, ')]),
    ("pendiente_de_firma no trae los controles", PS,
     [('"hora": str(d.get("hora", "") or ""), "checks": d.get("checks", []),',
       '"hora": str(d.get("hora", "") or ""), "checks": [],')]),
    ("⚠️ se firma sin el resumen", PSU,
     [("        _resumen_para_firmar(info)\n", "")]),
    ("el resumen no enseña el near miss", PSU,
     [('    if info.get("near_miss"):\n        st.error(', '    if False:\n        st.error(')]),
    ("el resumen no dice los NO", PSU,
     [('_no = [c.get("label", "") for c in _checks if str(c.get("estado", "")).upper() == "NO"]', "_no = []")]),
    # ── H20 · la ventana dentro del Pre-Start ──
    ("⚠️ en_prestart nunca sabe que está en el Pre-Start", TU,
     [('    return sec == "prestart" or (sec == "herramientas" and sub == "🦺 Pre-Start")', "    return False")]),
    ("la ventana de «falta» vuelve a salir dentro del Pre-Start", TU,
     [("    if en_prestart():                           # v665 · ídem\n        return True\n", "")]),
    ("la ventana de «fírmalo» vuelve a salir dentro del Pre-Start", TU,
     [("        if en_prestart():\n            return True\n        _dialogo_firmar(", "        _dialogo_firmar(")]),
    # ── H43 · certificaciones ──
    ("⚠️ las certificaciones vuelven a callarse lo ya facturado", CU,
     [('    _tit = (t("Progress claims ({n} issued · {m} claimable now · {f} already invoiced)",',
       '    _fact = 0.0\n    _tit = (t("Progress claims ({n} issued · {m} claimable now · {f} already invoiced)",')]),
    ("sin el aviso del doble cobro", CU,
     # v670 · re-anclada: la vista previa sigue al % escrito (`dv`, H13 del ciclo 2)
     [('            if _fact > 0.5 and dv["bruto"] > 0:\n                st.warning(', '            if False:\n                st.warning(')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", AL,
           [("# ⚠️ v665 · qué se hizo al cerrarla", "# ⚠️ v665 (control) · qué se hizo al cerrarla")])


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
