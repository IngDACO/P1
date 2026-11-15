# -*- coding: utf-8 -*-
"""Batería de roturas de v677. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v677"
TOPE_S = 500
TC = "core/timeclock.py"
CO = "core/correcciones.py"
CU = "core/correcciones_ui.py"
PU = "core/projects_ui.py"
AU = "core/ausencias.py"
AI = "core/ausencias_ui.py"
AT = "core/auth_ui.py"
TU = "core/timeclock_ui.py"
RO = "core/roster.py"
RUI = "core/roster_ui.py"

ROTURAS = [
    # ── H9 · el motor ──
    ("⚠️ H9 · un día añadido vuelve a poder pisar otra jornada", TC,
     [("    for _tipo in ((TIPO_GENERAL, TIPO_PROYECTO) if con_obra else (TIPO_GENERAL,)):",
       "    for _tipo in ():")]),
    ("H9 · …o una entrada de obra", TC,
     [("    for _tipo in ((TIPO_GENERAL, TIPO_PROYECTO) if con_obra else (TIPO_GENERAL,)):",
       "    for _tipo in (TIPO_GENERAL,):")]),
    ("H9 · se puede añadir lo que aún no ha pasado", TC,
     [("    if salida > datetime.strptime(_now(), FMT):\n", "    if False:\n")]),
    ("H9 · una jornada de más de 16 h", TC,
     [("    if _h > JORNADA_MAX_H:\n        return t(\"That is {h} h", "    if False:\n        return t(\"That is {h} h")]),
    ("⚠️ H9 · sin la entrada de obra (el coste de la obra no la ve)", TC,
     [("    if _con:\n        filas.append(", "    if False:\n        filas.append(")]),
    ("H9 · las horas no se escriben (la nómina las recalcula mal)", TC,
     [('    filas = [[nombre, "", "", "", _e, _s, str(_h), "CERRADO"', '    filas = [[nombre, "", "", "", _e, _s, "", "CERRADO"')]),
    ("H9 · la jornada queda ABIERTA (acumula contra el reloj)", TC,
     [('    filas = [[nombre, "", "", "", _e, _s, str(_h), "CERRADO"', '    filas = [[nombre, "", "", "", _e, _s, str(_h), "ABIERTO"')]),
    ("H9 · escribe sin mirar lo leído fresco", TC,
     [("    _no = problema_jornada(registros, usuario, nombre, grupo, entrada, salida, con_obra=_con)\n",
       "    _no = \"\"\n")]),
    ("⚠️ H9 · sin motivo también se añade", CO,
     [("    if not _mot:\n        return False, t(\"Say why the day is added", "    if False:\n        return False, t(\"Say why the day is added")]),
    ("⚠️ H9 · la corrección queda sin aprobar (rastro a medias)", CO,
     [("    if okr:\n        aprobar(cid, revisor, nota=_mot)\n", "    if okr:\n        pass\n")]),
    ("H9 · la corrección se apunta como una salida corregida", CO,
     [("proyecto, CAMPO_DIA, \"\", _v, motivo=_mot)", "proyecto, CAMPO_OUT, \"\", _v, motivo=_mot)")]),
    ("H9 · no dice la colilla que ya cubre ese día", CO,
     [("    return True, _txt, nomina_que_cubre(grupo, usuario, entrada)", "    return True, _txt, \"\"")]),
    # ── H9 · la pantalla ──
    ("⚠️ H9 · la vista previa no mira el solape", PU,
     [("                _no = _TC.problema_jornada(_TC._cached_records(), _usr, _nom_de.get(_usr, \"\"), grupo, _ent, _sal,\n"
       "                                           con_obra=True)\n", "                _no = \"\"\n")]),
    ("H9 · el botón se puede pulsar con un problema delante", PU,
     [("disabled=bool(_no or not _usr or not _pid or not str(_mot or \"\").strip())):",
       "disabled=bool(not _usr or not _pid or not str(_mot or \"\").strip())):")]),
    ("H9 · no avisa de la colilla", PU,
     [("            if _nom:\n                st.warning(t(\":material/receipt_long: That day is already in payslip",
       "            if False:\n                st.warning(t(\":material/receipt_long: That day is already in payslip")]),
    ("H9 · no se le dice a la persona", PU,
     [("                correcciones_ui.avisar_dia_anadido(_usr, _ent, _sal, _nom_p.get(_pid, \"\"), _mot)\n", "")]),
    ("H9 · las personas inactivas también salen", PU,
     [("                   if str(u.get(\"Active\", \"SI\")).strip().upper() in auth._ACTIVE_OK\n                   and str(u.get(\"Role\", \"\")).lower() in (\"field\", \"administrator\")]",
       "                   if str(u.get(\"Role\", \"\")).lower() in (\"field\", \"administrator\")]")]),
    ("H9 · el día propuesto vuelve a ser hoy", PU,
     [("value=_ultimo_laborable(_hoy), max_value=_hoy", "value=_hoy, max_value=_hoy")]),
    ("H9 · no está en Finance → Hours", PU,
     [("    dia_olvidado_section(grupo)         # v677 · H9 del ciclo 3: un día que no se fichó del todo\n", "")]),
    # ── H9 · Time fixes ──
    ("H9 · Time fixes da «—» de horas para un día añadido", CU,
     [("    if str(r.get(\"Field\", \"\")) == C.CAMPO_DIA:          # v677 · un día añadido: suma la jornada entera",
       "    if False:          # v677 · un día añadido: suma la jornada entera")]),
    ("H9 · «Revert» de un día añadido habla de una sesión abierta", CU,
     [("    if accion == \"revertir\" and str(r.get(\"Field\", \"\")) == C.CAMPO_DIA:", "    if False:")]),
    ("H9 · el historial pinta «— → 07:00»", CU,
     [("    if str(r.get(\"Field\", \"\")) == C.CAMPO_DIA:\n        _a, _b = C.ventana(r)\n        return f\"{_hhmm(_a)} → {_hhmm(_b)}\"",
       "    if False:\n        _a, _b = C.ventana(r)\n        return f\"{_hhmm(_a)} → {_hhmm(_b)}\"")]),
    ("H1 · el historial de Time fixes vuelve a minúscula", CU,
     [("                \"Estado\": i18n.estado(str(r.get(\"Status\", \"\"))),", "                \"Estado\": i18n.etiqueta(str(r.get(\"Status\", \"\"))),")]),
    # ── H2 ──
    ("⚠️ H2 · la de la oficina nace pendiente", AU,
     [("    estado = PENDIENTE if (cfg[\"aprobacion\"] and not por_oficina) else APROBADA",
       "    estado = PENDIENTE if cfg[\"aprobacion\"] else APROBADA")]),
    ("H2 · sin quién la registró", AU,
     [("            \"\", str(por_oficina or usuario), hoy,", "            \"\", str(usuario), hoy,")]),
    ("H2 · …ni quién la aprobó", AU,
     [("            (str(por_oficina) if por_oficina else t(\"(automatic)\") if estado == APROBADA else \"\"),",
       "            (t(\"(automatic)\") if estado == APROBADA else \"\"),")]),
    ("⚠️ H2 · no va al tablero", AI,
     [("    _ok2, _n = AU.aplicar_al_roster(_r)\n    _avisar_registrada(", "    _ok2, _n = False, \"\"\n    _avisar_registrada(")]),
    ("⚠️ H2 · la recién creada se lee por un ID global (sin el grupo)", AI,
     [("    _r = _de_grupo(grupo, res)\n", "    _r = AU.get(res) or {}\n")]),
    ("H2 · no se le dice a la persona", AI,
     [("    _avisar_registrada(usuario, _r, motivo)\n", "")]),
    ("H2 · sin la oficina en `solicitar` (nace pendiente)", AI,
     [("incluir_findes=incluir_findes,\n                           por_oficina=quien)", "incluir_findes=incluir_findes)")]),
    ("⚠️ H2 · el formulario no mira las reglas antes", AI,
     [("            _no = AU.problema_solicitud(grupo, _usr, tipo, desde, hasta, findes)\n", "            _no = \"\"\n")]),
    ("H2 · viniendo de la ficha, la persona no está elegida", AI,
     [("            st.session_state[_kp] = next(k for k, v in _opc.items() if v == _pre)", "            pass")]),
    ("H2 · el formulario no está en la bandeja", AI,
     [("    _registrar_oficina_form(grupo, quien)    # v677 · H2 del ciclo 3\n", "")]),
    ("⚠️ H2 · la ficha sin el saldo", AT,
     [("        _saldo_ausencias(grupo, sel, k)        # v677 · H2 del ciclo 3\n", "")]),
    ("H2 · el saldo sin lo pendiente", AT,
     [("                      + (\" \" + t(\"({n} pending)\", n=f\"{s['pendientes']:.0f}\") if s[\"pendientes\"] else \"\"))",
       "                      )")]),
    ("H2 · el botón de la ficha no lleva a la bandeja", AT,
     [("        st.session_state[\"_admin_nav_pending\"] = (\"planificacion\", \"🌴 Ausencias\")\n        st.rerun()\n\n\ndef _error_email_alta",
       "        st.rerun()\n\n\ndef _error_email_alta")]),
    # ── H12 ──
    ("⚠️ H12 · la vista previa vuelve a prometer con un solape", AI,
     [("        elif AU.msg_solape(grupo, usuario, desde, hasta):\n", "        elif False:\n")]),
    ("H12 · el motor y la vista previa con dos mensajes distintos", AU,
     [("    _sol = msg_solape(grupo, usuario, desde, hasta)\n    if _sol:\n        return _sol\n",
       "    _sol = msg_solape(grupo, usuario, desde, hasta)\n    if _sol:\n        return _sol.replace(\"overlapping\", \"over\")\n")]),
    # ── H1 ──
    ("⚠️ H1 · los estados de las ausencias vuelven a minúscula", AI,
     [("AU.CANCELADA: \"⚪ \"}.get(e, \"\") + _estado(e)", "AU.CANCELADA: \"⚪ \"}.get(e, \"\") + e")]),
    # ── H7 ──
    ("⚠️ H7 · fichar en una obra que no ha empezado no dice nada", TU,
     [("    _nota = nota_obra(pid, grupo)            # v677 · H7 del ciclo 3\n    if _nota:\n        flash.aviso(_nota)\n", "")]),
    ("H7 · …ni en pausa", TU,
     [("    if str(p.get(\"Status\", \"\")) == \"On hold\":\n        return t(\":material/pause_circle:",
       "    if False:\n        return t(\":material/pause_circle:")]),
    ("H7 · avisa también de la que empieza HOY", TU,
     [("    if _ini and _ini > clock.today(grupo):", "    if _ini and _ini >= clock.today(grupo):")]),
    ("H7 · al cambiar de obra no dice nada", TU,
     [("                        if nota_obra(_nuevo, grupo):                # v677 · H7: también al cambiar de obra\n"
       "                            flash.aviso(nota_obra(_nuevo, grupo))\n", "")]),
    # ── H8 ──
    ("⚠️ H8 · la barra lateral vuelve a no decir dónde", TU,
     [("    if prj:\n        st.caption(t(\":material/apartment: {p} · since {h}\"", "    if False:\n        st.caption(t(\":material/apartment: {p} · since {h}\"")]),
    ("H8 · …ni desde cuándo, con solo la jornada", TU,
     [("    elif gen:\n        st.caption(t(\":material/schedule: Workday, no project · since {h}\"",
       "    elif False:\n        st.caption(t(\":material/schedule: Workday, no project · since {h}\"")]),
    # ── lo visto verificando v676 ──
    ("⚠️ v676 · la NOTA de una ausencia vuelve a abrir el fin de semana", RO,
     [("    return bool(str(n[\"nota\"]).strip()) and not n[\"items\"]", "    return bool(str(n[\"nota\"]).strip())")]),
    ("v676 · el tablero vuelve a su regla vieja (sin `celda_con_trabajo`)", RO,
     [("            if _d in DIAS_EXTRA and celda_con_trabajo(_c):",
       "            if _d in DIAS_EXTRA and (_norm_cell(_c)[\"items\"] or _norm_cell(_c)[\"nota\"].strip()):")]),
    ("v676 · una columna con solo ausencias no se deja cerrar", RO,
     [("    return [u for u, _sem in (datos or {}).items() if celda_con_trabajo((_sem or {}).get(dia, {}))]",
       "    return [u for u, _sem in (datos or {}).items() if _norm_cell((_sem or {}).get(dia, {}))[\"items\"]]")]),
    ("v676 · liberar desde el Radar vuelve a decir solo el ID", RUI,
     [("p=f\"{_nom} ({pid})\" if _nom else pid, n=n,\n                  f=_dmy(", "p=pid, n=n,\n                  f=_dmy(")]),
    ("v676 · «Not copied» vuelve a decir solo el ID", RUI,
     [("{_np.get(pid) or pid} ({pid})", "{pid}")]),
    ("v676 · la lista de cierre vuelve a decir solo el ID", PU,
     [("p=f\"{_nom} ({pid})\" if _nom else pid, n=n,\n                  f=_fmt_fecha(", "p=pid, n=n,\n                  f=_fmt_fecha(")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", TC,
           [("def problema_jornada(registros, usuario, nombre, grupo, entrada, salida, con_obra=True) -> str:\n",
             "def problema_jornada(registros, usuario, nombre, grupo, entrada, salida, con_obra=True) -> str:  # (control)\n")])


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
