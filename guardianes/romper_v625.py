# -*- coding: utf-8 -*-
"""Batería de roturas de v625. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v625"
TOPE_S = 300
PL = "core/plan_ui.py"
TS = "core/tool_save_ui.py"
TR = "core/toolruns.py"
HU = "core/home_ui.py"
SU = "core/survey_ui.py"
PR = "core/projects.py"
PU = "core/projects_ui.py"
BC = "core/buffer_cut_ui.py"
BE = "core/belting_ui.py"
PB = "core/plumb_ui.py"
RC = "core/rail_cut_ui.py"

ROTURAS = [
    ("⚠️ el fichaje vuelve a ir por el nombre aunque haya ID", PL,
     [('    if pid:\n        return next((p for p in proys if str(p.get("ID", "")).strip() == pid), None)\n', "")]),
    ("⚠️ con dos obras del mismo nombre se queda con la primera", PL,
     [("    return casan[0] if len(casan) == 1 else None\n", "    return casan[0] if casan else None\n")]),
    ("⚠️ el guardado tiene su propia búsqueda por nombre", TS,
     [('            _fich = plan_ui.obra_del_fichaje(_ses.get(timeclock.TIPO_PROYECTO)\n'
       '                                             or _ses.get(timeclock.TIPO_GENERAL) or {}, proys)\n',
       '            _fich = next(iter(proys), None)\n')]),
    ("⚠️ sin fichar vuelve el «Clock in first»", PL,
     [('        if len(suyas) == 1:\n            prj = suyas[0]\n        else:\n',
       '        if len(suyas) == 1:\n            return None, {}\n        else:\n')]),
    ("⚠️ el selector ofrece obras que no son de herramientas", PL,
     [('                                                      grupo=auth.get("grupo", "") or None)\n'
       '                 if es_de_herramientas(p)]\n',
       '                                                      grupo=auth.get("grupo", "") or None)]\n')]),
    ("sin obra elegida, usa la primera", PL,
     [('            if prj is None:\n                return None, {}\n',
       '            if prj is None:\n                prj = suyas[0]\n')]),
    ("sin fichar dice que fichó", PL,
     [('        datos = plan_data.del_proyecto(str(prj.get("ID", "")))\n        _cabecera(prj, datos, fichado=False)\n'
       '        return prj, datos\n\n    # ── Admin',
       '        datos = plan_data.del_proyecto(str(prj.get("ID", "")))\n        _cabecera(prj, datos, fichado=True)\n'
       '        return prj, datos\n\n    # ── Admin')]),
    ("⚠️ el nombre sin escapar en la cabecera", PL, [('    _n = literal_md(prj.get("Name"))\n', '    _n = prj.get("Name")\n')]),
    ("⚠️ «It will be saved» vuelve bajo «Saved as…»", TS,
     [("            if not _ya(_fich):\n                st.caption(t(\":material/save: It will be saved",
       "            if True:\n                st.caption(t(\":material/save: It will be saved")]),
    ("⚠️ «You have not clocked in» con la obra ya elegida", TS,
     [('            if rol == "field" and not obra_id:\n', '            if rol == "field":\n')]),
    ("el nombre sin escapar al guardar", TS, [('x=literal_md(_fich.get(\'Name\'))', "x=_fich.get('Name')")]),
    ("⚠️ la portada le enseña al campo las obras ajenas", HU,
     [('        ult = TR.ultimos_por_herramienta(grupo, pids=pids)\n', '        ult = TR.ultimos_por_herramienta(grupo)\n')]),
    ("el filtro por obras se ignora en el motor", TR,
     [('        if pids is None or str(r.get("ProjectID", "")) in pids:\n', "        if True:\n")]),
    ("`pids` vacío vale por «todas»", TR,
     [('        if pids is None or str(r.get("ProjectID", "")) in pids:\n',
       '        if not pids or str(r.get("ProjectID", "")) in pids:\n')]),
    ("⚠️ el Pre-Start de hoy vuelve a contar los del grupo", HU,
     [('                     if pids is None or str(r.get("ProjectID", "")) in pids])\n',
       '                     if True])\n')]),
    ("⚠️ Buffers no baja", BC, [('            st.session_state["_bajar_cpx_bc_kpis"] = True     # v625 · al resultado, solo si lo hay\n', "")]),
    ("⚠️ Buffers baja aunque no calcule", BC,
     [('        if _faltan:\n            st.session_state.pop(_K, None)\n',
       '        st.session_state["_bajar_cpx_bc_kpis"] = True\n        if _faltan:\n            st.session_state.pop(_K, None)\n')]),
    ("⚠️ Belting no baja", BE, [('            st.session_state["_bajar_cpx_belt_kpis"] = True   # v625 · al resultado, solo si lo hay\n', "")]),
    ("⚠️ Plomada no baja", PB, [('        st.session_state["_bajar_cpx_plb_res"] = True         # v625 · al resultado, solo si lo hay\n', "")]),
    ("⚠️ Plomada baja aunque no calcule", PB,
     [('    if st.button(t(":material/straighten: Calculate plumb lines"), type="primary", width="stretch",\n'
       '                 key="plb_calc") and _se_puede(bks, rail, tksw, lt, bs, bsr_list):\n',
       '    if st.button(t(":material/straighten: Calculate plumb lines"), type="primary", width="stretch",\n'
       '                 key="plb_calc"):\n        st.session_state["_bajar_cpx_plb_res"] = True\n'
       '    if _se_puede(bks, rail, tksw, lt, bs, bsr_list) and False:\n')]),
    ("⚠️ Rieles caso 1 no baja", RC,
     [('                    "n2500": int(n2500), "n5000": int(n5000), "n": int(n),\n'
       '                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}\n'
       '                st.session_state["_bajar_cpx_rc_res"] = True  # v625 · al resultado, solo si lo hay\n',
       '                    "n2500": int(n2500), "n5000": int(n5000), "n": int(n),\n'
       '                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}\n')]),
    ("⚠️ Rieles caso 2 no baja", RC,
     [('                    "subcaso": subcaso, "sub": sub, "n": int(n),\n'
       '                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}\n'
       '                st.session_state["_bajar_cpx_rc_res"] = True  # v625 · al resultado, solo si lo hay\n',
       '                    "subcaso": subcaso, "sub": sub, "n": int(n),\n'
       '                    "lfkk": float(lfkk), "lfgk": float(lfgk), "firma": _ahora}\n')]),
    ("⚠️ «Client report» vuelve al campo", SU,
     [('        if can_reports(_ROL):\n            st.header(t(":material/description: Client report"))\n',
       '        st.header(t(":material/description: Client report"))\n        if can_reports(_ROL):\n')]),
    ("⚠️ el campo vuelve a no poder guardar", SU,
     [('        if _ROL in ("administrator", "owner", "field"):\n', '        if _ROL in ("administrator", "owner"):\n')]),
    ("⚠️⚠️ el campo pisa el survey guardado (sin la pregunta)", SU,
     [('                        _a_oficina = _es_campo and not projects_data.survey_libre(_pid)\n',
       '                        _a_oficina = False\n')]),
    ("⚠️⚠️ la pregunta sale de la caché", SU,
     [('                        _a_oficina = _es_campo and not projects_data.survey_libre(_pid)\n',
       '                        _a_oficina = _ya_hay\n')]),
    ("⚠️ la oficina también pasa por el camino del campo", SU,
     [('                        _a_oficina = _es_campo and not projects_data.survey_libre(_pid)\n',
       '                        _a_oficina = not projects_data.survey_libre(_pid)\n')]),
    ("⚠️ el aviso de que ya hay uno desaparece", SU,
     [('                    if _ya_hay:\n                        st.info(', '                    if False:\n                        st.info(')]),
    ("el botón no dice lo que va a hacer", SU,
     [('t(":material/save: Save as a new calculation") if _ya_hay else\n                                 ', "")]),
    ("⚠️ el campo vuelve a elegir de una lista la obra del cálculo", SU,
     [('                    if _es_campo and _lbl_dest:\n', '                    if False:\n')]),
    ("⚠️ el botón «Open project» vuelve al campo", SU,
     [('                            if not _es_campo:\n                                st.session_state["_prj_creado"] = {',
       '                            if True:\n                                st.session_state["_prj_creado"] = {')]),
    ("⚠️ sin obras, le manda a la pantalla de la oficina", SU,
     [('                if not _proys and _es_campo:\n', '                if False:\n')]),
    ("⚠️ el campo ve las obras de todo el grupo", SU,
     [('                          else projects_data.list_projects_for_field(_usr, grupo=_GRUPO)\n'
       '                          if _es_campo else projects_data.list_projects(_GRUPO))\n',
       '                          else projects_data.list_projects(_GRUPO))\n')]),
    ("el aviso del campo vuelve a prometer el informe", SU,
     [('Calculate and see the results**: the solutions, the schedule and saving "\n'
       '                      "to the project appear here.") if _ROL == "field" else\n',
       'Calculate and see the results**: the solutions, the schedule and the client report "\n'
       '                      "appear here.") if _ROL == "field" else\n')]),
    ("⚠️ sin Drive deja una fila sin archivo", SU,
     [('    if not (drive_store.is_configured() and drive_store.is_available()):\n'
       '        st.error(t("It could not be saved: Drive is not connected',
       '    if False:\n        st.error(t("It could not be saved: Drive is not connected')]),
    ("⚠️ el archivo no lleva la matriz", SU,
     [('pdf=_json.dumps({"params": params, "matriz": matriz}, ensure_ascii=False,',
       'pdf=_json.dumps({"params": params}, ensure_ascii=False,')]),
    ("⚠️ el archivo no lleva los parámetros", SU,
     [('pdf=_json.dumps({"params": params, "matriz": matriz}, ensure_ascii=False,',
       'pdf=_json.dumps({"matriz": matriz}, ensure_ascii=False,')]),
    ("⚠️ el JSON se archiva como PDF", SU, [(', mime="application/json")', ")")]),
    ("⚠️ `registrar` ignora el tipo", TR,
     [("drive_id = drive_store.upload(pid, filename, pdf, mime)", 'drive_id = drive_store.upload(pid, filename, pdf, "application/pdf")')]),
    ("⚠️ no se marca «por decidir»", SU,
     [('datos={"por_decidir": True, "ns": params.get("NS")}', 'datos={"ns": params.get("NS")}')]),
    ("⚠️ la matriz va a la fila (se cortaría a 4800)", SU,
     [('datos={"por_decidir": True, "ns": params.get("NS")}', 'datos={"por_decidir": True, "ns": params.get("NS"), "m": matriz}')]),
    ("⚠️ `tiene_survey` da por bueno «{}»", PR,
     [('not in ("", "{}", "[]")', 'not in ("",)')]),
    ("⚠️ `survey_libre` da «libre» si no se puede leer", PR,
     [('        logger.warning("projects.survey_libre(%s): %s", pid, e)\n    return False\n',
       '        logger.warning("projects.survey_libre(%s): %s", pid, e)\n    return True\n')]),
    ("⚠️ `survey_libre` da «libre» sin hoja", PR,
     [('    pws, err = _projects_ws()\n    if err:\n        return False\n    try:\n        for r in valores',
       '    pws, err = _projects_ws()\n    if err:\n        return True\n    try:\n        for r in valores')]),
    ("⚠️ la campana no filtra lo ya decidido", TR,
     [('            and str(r.get("DriveID", "")).strip() and datos_de(r).get("por_decidir")]\n',
       '            and str(r.get("DriveID", "")).strip()]\n')]),
    ("la campana cuenta filas sin archivo", TR,
     [('            and str(r.get("DriveID", "")).strip() and datos_de(r).get("por_decidir")]\n',
       '            and datos_de(r).get("por_decidir")]\n')]),
    ("la campana mezcla grupos", TR,
     [('            if str(r.get("Group", "")).strip().lower() == g and es_survey_a_decidir(r)\n',
       '            if es_survey_a_decidir(r)\n')]),
    ("⚠️ decidir escribe en otra columna", TR,
     [('w.update_cell(cel.row, HEADERS.index("DataJSON") + 1,', 'w.update_cell(cel.row, HEADERS.index("Summary") + 1,')]),
    ("⚠️ decidir no apaga la campana (caché)", TR,
     [('                      json.dumps(d, ensure_ascii=False, default=str)[:4800])\n        _invalidate()\n',
       '                      json.dumps(d, ensure_ascii=False, default=str)[:4800])\n')]),
    ("⚠️ borrar no cierra la decisión", TR,
     [('            decidir_survey(r, "deleted", usuario)\n', "            pass\n")]),
    ("⚠️ «Load» no carga", PU,
     [('        _cargar_en_survey(pid, _prj, str(_prj.get("Group", "")), _params, _matriz)\n', "")]),
    ("⚠️ «Load» no deja la obra elegida", PU,
     [('        st.session_state["pl_prj_sv"] = f"{_prj.get(\'Name\')} ({pid})"\n', "")]),
    ("⚠️ «Load» no lleva al Survey", PU,
     [('        st.session_state["_admin_nav_pending"] = ("herramientas", "📐 Survey")\n        st.rerun()\n    if pendiente and',
       '        st.rerun()\n    if pendiente and')]),
    ("⚠️ «Load» no cierra la decisión", PU, [('            toolruns.decidir_survey(run, "loaded", _usr)\n', "            pass\n")]),
    ("⚠️ un archivo ilegible cierra la decisión", PU,
     [('            st.error(t("It could not be read: {e}", e=ex))\n            return\n',
       '            st.error(t("It could not be read: {e}", e=ex))\n            toolruns.decidir_survey(run, "loaded", _usr)\n            return\n')]),
    ("⚠️ «Keep» sale también con lo ya decidido", PU,
     [('    if pendiente and _c2.button(t(":material/check: Keep', '    if _c2.button(t(":material/check: Keep')]),
    ("⚠️ el campo también decide", PU,
     [("    if puede_borrar and did and bool(run) and toolruns.es_survey_a_decidir(run):\n",
       "    if did and bool(run) and toolruns.es_survey_a_decidir(run):\n")]),
    ("⚠️ borrar el archivo no avisa al motor", PU,
     [('                    toolruns.decidir_por_drive(_pend["did"],\n'
       '                                               st.session_state.get("auth", {}).get("usuario", ""))\n',
       "                    pass\n")]),
    ("⚠️ «Rebuild» pierde su carga", PU,
     [('                    _cargar_en_survey(pid, prj, grupo, params, matriz)\n', "                    pass\n")]),
    ("⚠️ lo cargado lo pisa el plano", PU, [('    _ev.respetar("sv", pid)\n', "")]),
    ("⚠️ la campana no avisa", HU,
     [('            for r in TR.survey_por_decidir(grupo):\n', "            for r in []:\n")]),
    ("⚠️ la campana lleva a la ficha, no a los archivos", HU,
     [('out.append({"texto": _txt, "destino": ("archivos", _pid)})\n', 'out.append({"texto": _txt, "destino": ("obra", _pid)})\n')]),
    ("⚠️ tocar la campana no abre Files", HU,
     [('        st.session_state["_prj_sec_pending"] = "📎 Archivos"\n        navegar("proyectos", "📊 Proyectos")\n',
       '        navegar("proyectos", "📊 Proyectos")\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", TR,
           [('    """v625 · Los surveys del campo que la oficina aún no ha resuelto (la campana los cuenta)."""',
             '    """v625 · (control) Los surveys del campo que la oficina aún no ha resuelto."""')])


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
