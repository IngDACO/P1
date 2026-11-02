# -*- coding: utf-8 -*-
"""Batería de roturas de v636. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v636"
TOPE_S = 180
M = "core/falsecar.py"
U = "core/falsecar_ui.py"
PDF = "core/falsecar_pdf.py"
TU = "core/timeclock_ui.py"
HU = "core/home_ui.py"
PSU = "core/prestart_ui.py"
PU = "core/projects_ui.py"
HO = "core/handover.py"

ROTURAS = [
    # ── El catálogo y la pregunta ──
    ("⚠️ un Ripout también lo admite", "core/stages.py",
     [('    return PISTA_INSTALL in pistas_de_tipo(tipo)\n', '    return True\n')]),
    ("⚠️ la pregunta nace con «No» marcado", PU,
     [("""        st.radio(t(_S.PREGUNTA_FC), [True, False], index=None, horizontal=True,\n""", """        st.radio(t(_S.PREGUNTA_FC), [True, False], index=1, horizontal=True,\n""")]),
    ("⚠️ sin responder se puede crear", PU,
     [("""        if st.session_state.get(_clave_fc(key)) is None:
            _pend.append({"clave": "false_car", "pregunta": _S.PREGUNTA_FC,
                          "opciones": [True, False], "elegidas": []})
""", "")]),
    ("⚠️ Yes no añade las actividades", PU,
     [("""    return ((v,) if v else ()) + (_S.FALSE_CAR if st.session_state.get(_clave_fc(key)) else ())\n""", """    return (v,) if v else ()\n""")]),
    ("⚠️ se mete en EXCLUYENTES y para las altas por programa", "core/stages.py",
     [("""EXCLUYENTES = {
    "demolicion": {
""", """EXCLUYENTES = {
    "false_car": {"pista": PISTA_INSTALL, "pregunta": "False car?", "opciones": ("Install sky climber", "x")},
    "demolicion": {
""")]),
    # ── El formato ──
    ("⚠️ se retoca el texto de un punto", M,
     [('''    ("fc14", "Whether the manual descent is normal (Brake Release)."),\n''', '''    ("fc14", "Manual descent is normal."),\n''')]),
    ("⚠️ se pierde un punto", M,
     [('''    ("fc13", "Anti-derailment switch function is normal."),\n''', '')]),
    ("la columna nueva no va al final", M,
     [('''HEADERS = ["ID", "ProjectID", "Group", "Date", "Time", "ResultsJSON",''', '''HEADERS = ["ID", "Group", "ProjectID", "Date", "Time", "ResultsJSON",''')]),
    # ── Quién y qué días ──
    ("⚠️ una obra vieja también lo pide", M,
     [("""    return S.FC_MONTAR in (P.plan_etapas(prj or {}).get("condicionales") or ())\n""", """    return True\n""")]),
    ("⚠️ a medio montar ya se exige", M,
     [("""        if _num(r.get("Pct")) < 100:
            continue
""", "")]),
    ("⚠️ el Sky lock cuenta como montado", M,
     [("""        if _a == S.FC_MONTAR:
            desde""", """        if _a in (S.FC_MONTAR, S.FC_LOCK):
            desde""")]),
    ("⚠️ se exige también el día de la retirada", M,
     [("""    return bool(desde) and desde <= dia and not (hasta and hasta <= dia)\n""", """    return bool(desde) and desde <= dia and not (hasta and hasta < dia)\n""")]),
    ("⚠️ retirado sigue exigiéndose", M,
     [("""    return bool(desde) and desde <= dia and not (hasta and hasta <= dia)\n""", """    return bool(desde) and desde <= dia\n""")]),
    ("⚠️ se exige sin estar montado", M,
     [("""    return bool(desde) and desde <= dia and not (hasta and hasta <= dia)\n""", """    return not (hasta and hasta <= dia)\n""")]),
    ("usa la fecha de registro, no la de trabajo", M,
     [("""            desde = _parse_date(SP._fecha_de(r))\n""", """            desde = _parse_date(str(r.get("Updated", ""))[:4] + "-01-01")\n""")]),
    # ── Guardar ──
    ("⚠️ se admite un punto sin responder", M,
     [("""    if _sin:
        return t("Answer every item: {n} still to answer.", n=len(_sin))
""", "")]),
    ("⚠️ X sin observaciones", M,
     [("""    if _nota:
        return t("Write the remarks of the items marked X: {n}.", n=", ".join(_nota))
""", "")]),
    ("⚠️ el motor no valida", M,
     [("""    _err = valida(resultados)
    if _err:
        res["error"] = _err
        return res
""", "")]),
    ("⚠️ el campo registra cualquier día", M,
     [("""    if not data.get("gestor") and dia != _hoy:\n""", """    if False:\n""")]),
    ("⚠️ dos el mismo día", M,
     [("""    if any(str(r.get("ProjectID", "")).strip() == pid and _parse_date(r.get("Date")) == dia
           for r in recs):
        res["error"] = t("This job already has the checklist for that day.")
        return res
""", "")]),
    ("⚠️ con X no se abre alarma", M,
     [("""    if fallos:
        try:
            from core import alerts
""", """    if False:
        try:
            from core import alerts
""")]),
    ("⚠️ la alarma falla en silencio", M,
     [("""            res["alarma"] = bool(ok)\n""", """            res["alarma"] = True\n""")]),
    ("⚠️ la alarma no dice qué puntos", M,
     [("""pid, grupo, "False car check with %d item(s) marked X: %s" % (len(fallos), _txt),\n""", """pid, grupo, "False car check with X",\n""")]),
    ("⚠️ se archiva como Pre-Start", M,
     [("""            projects.add_document(pid, fname, "falsecar", drive_id, usuario)\n""", """            projects.add_document(pid, fname, "prestart", drive_id, usuario)\n""")]),
    ("no queda qué falló", M,
     [("""                      ",".join(str(n) for n in fallos),\n""", """                      "",\n""")]),
    ("sin Drive no se registra", M,
     [("""    except Exception as e:
        logger.warning("falsecar: archivado en Drive falló: %s", e)
""", """    except Exception as e:
        res["error"] = str(e)
        return res
""")]),
    # ── El PDF ──
    ("⚠️ el ✓ con su byte: cuadro negro", PDF,
     [("""<font name="ZapfDingbats" size="13">✓</font>""", """<font name="ZapfDingbats" size="13">3</font>""")]),
    ("⚠️ la X no sale en el PDF", PDF,
     [("""    if res == FC.FALLA:
        return Paragraph('<font name="Helvetica-Bold" size="12">X</font>', _CENT)
""", "")]),
    ("⚠️ las observaciones no salen", PDF,
     [("""                      Paragraph(_esc(_r.get("nota", "")), _CEL)])\n""", """                      Paragraph("", _CEL)])\n""")]),
    ("⚠️ un «&» en las observaciones rompe el PDF", PDF,
     [("""Paragraph(_esc(_r.get("nota", "")), _CEL)""", """Paragraph(str(_r.get("nota", "")) + "<b>", _CEL)""")]),
    ("el PDF no dice de qué obra es", PDF,
     [("""          Paragraph(d("Project: ") + " · ".join(_obra), _OBRA), Spacer(1, 8)]\n""", """          Spacer(1, 8)]\n""")]),
    # ── Firmar ──
    ("⚠️ el nombre manda sobre el login", M,
     [("""    _nombres = reg["firmas_sin_login"] if quien_u else reg["firmas"]\n""", """    _nombres = reg["firmas"]\n""")]),
    ("⚠️ quien ya firmó sigue pendiente", M,
     [("""    if quien_u and quien_u in {u.lower() for u in reg["firmas_usuarios"]}:
        return {}
""", "")]),
    ("⚠️ el anexo dice Pre-Start", M,
     [("""            "location": "", "etiqueta": d("False car"),\n""", """            "location": "",\n""")]),
    ("⚠️ el anexo reemplaza al original", M,
     [("""            for _b in (drive_store.download(drive_id), anexo):\n""", """            for _b in (anexo,):\n""")]),
    ("⚠️ el PDF viejo no se quita", M,
     [("""            projects.delete_document_record(pid, drive_id)
            drive_store.delete(drive_id)
""", """            pass
""")]),
    ("⚠️ el del Pre-Start cambia de texto", "core/prestart_pdf.py",
     [("""    ref = [[Paragraph("<b>" + _esc(info.get("etiqueta") or "Pre-Start") + "</b><br/>"\n""", """    ref = [[Paragraph("<b>" + _esc(info.get("etiqueta") or "Check") + "</b><br/>"\n""")]),
    # ── Los días sin registro ──
    ("⚠️ sale hoy, que aún puede estar por hacer", M,
     [("""    ayer = hoy - _dt.timedelta(days=1)\n""", """    ayer = hoy\n""")]),
    ("⚠️ se exige antes de montarlo", M,
     [("""        if (p, dia) not in con_fc and _dentro(_per[p], dia):\n""", """        if (p, dia) not in con_fc and _per[p] != (None, None):\n""")]),
    ("⚠️ también en obras sin false car", M,
     [("""            _per[p] = periodo(_prj) if tiene(_prj) else (None, None)\n""", """            _per[p] = (_dt.date(2000, 1, 1), None)\n""")]),
    ("⚠️ no mira los Pre-Start", M,
     [("""        falta = [] if (p, dia) in con_ps else ["prestart"]\n""", """        falta = []\n""")]),
    ("el orden no es del más reciente", M,
     [("""    return sorted(out, key=lambda x: (x["fecha"], x["nombre"]), reverse=True)\n""", """    return sorted(out, key=lambda x: (x["fecha"], x["nombre"]))\n""")]),
    ("⚠️ la jornada general cuenta como obra", "core/timeclock.py",
     [("""        if _tipo_of(r) != TIPO_PROYECTO or not pid_of(r):\n            continue\n""", """        if not pid_of(r):\n            continue\n""")]),
    ("⚠️ un turno de noche cuenta un solo día", "core/timeclock.py",
     [("""        for d, hh in _row_segmentos(r):
            if hh <= 0 or (desde and d < desde) or (hasta and d > hasta):
                continue
            e = out.setdefault""", """        for d, hh in _row_segmentos(r)[:1]:
            if hh <= 0 or (desde and d < desde) or (hasta and d > hasta):
                continue
            e = out.setdefault""")]),
    # ── Handover ──
    ("⚠️ se mete en los trece", HO,
     [("""    for it in ITEMS + ([ITEM_FALSE_CAR] if ctx.get("false_car") else []):\n""", """    for it in ITEMS + [ITEM_FALSE_CAR]:\n""")]),
    ("⚠️ el Pre-Start no acusa los días sin él", HO,
     [("""    if n and sin:
        return PARCIAL, "%d pre-start%s on file, %d day%s worked with none" % (
            n, "" if n == 1 else "s", sin, "" if sin == 1 else "s")
""", "")]),
    ("⚠️ el false car no acusa los días sin él", HO,
     [("""    if n and sin:
        return PARCIAL, "%d check%s on file, %d day%s worked with none" % (
            n, "" if n == 1 else "s", sin, "" if sin == 1 else "s")
""", "")]),
    ("⚠️ acusa de falta sin haberlo montado", HO,
     [("""    return PARCIAL, "The false car is not marked as installed yet"\n""", """    return FALTA, "No check recorded"\n""")]),
    # ── La hoja ──
    ("⚠️ fuera del lote", "core/hojas.py",
     [('''    "FalseCarChecks",\n''', '')]),
    ("⚠️ borrar una obra sin checklists crea la hoja", M,
     [("""    if not any(str(r.get("ProjectID", "")).strip() == str(pid) for r in _records()):
        return 0
""", "")]),
    ("⚠️ borrar la obra los deja huérfanos", "core/projects.py",
     [("""        from core import falsecar as _FC
        _FC.borrar_de_obra(pid)
""", """        pass
""")]),
    ("⚠️ el aviso de antes de borrar no los cuenta", "core/projects.py",
     [("""                                    ("False car checks", _FC.SHEET, "ProjectID"),\n""", "")]),
    ("⚠️ el campo no ve el PDF en Files", PU,
     [("""               "prestart", "falsecar", "calculo"}\n""", """               "prestart", "calculo"}\n""")]),
    # ── La pantalla ──
    ("⚠️ las respuestas nacen en ✓", U,
     [("""            _res = c2.radio(t("Inspection results"), [FC.PASA, FC.FALLA], index=None, horizontal=True,\n""", """            _res = c2.radio(t("Inspection results"), [FC.PASA, FC.FALLA], index=0, horizontal=True,\n""")]),
    ("⚠️ se envía sin completar", U,
     [("""                 key=f"fc_submit_{kp}", disabled=bool(_falta)):\n""", """                 key=f"fc_submit_{kp}"):\n""")]),
    ("⚠️ el formulario no lleva la obra en la clave", U,
     [("""    kp = f"{pid}_{dia.isoformat()}_{_gen}"\n""", """    kp = f"{_gen}"\n""")]),
    ("⚠️ el formulario no se vacía al guardar", U,
     [("""            st.session_state[f"_fc_gen_{pid}"] = _gen + 1\n""", "")]),
    ("⚠️ con X no dice que no se use", U,
     [("""    if r.get("fallos"):
        _no_usar([{"n": n} for n in r["fallos"]])
""", """    if r.get("fallos"):
""")]),
    ("⚠️ quien abre la pantalla no se entera de la X", U,
     [("""                   + ", ".join(literal_md(n) for n in d["firmas"]))
        if d["fallos"]:
            _no_usar(d["fallos"])
        _boton_pdf(d, f"fc_hoy_pdf_{pid}", t(":material/download: Download PDF"))
""", """                   + ", ".join(literal_md(n) for n in d["firmas"]))
        _boton_pdf(d, f"fc_hoy_pdf_{pid}", t(":material/download: Download PDF"))
""")]),
    ("⚠️ quien va a firmar no se entera de la X", U,
     [("""                   + ", ".join(literal_md(n) for n in d["firmas"]))
        if d["fallos"]:
            _no_usar(d["fallos"])
        c1, c2 = st.columns([1, 2])
""", """                   + ", ".join(literal_md(n) for n in d["firmas"]))
        c1, c2 = st.columns([1, 2])
""")]),
    ("⚠️ la alarma que falla no se dice", U,
     [("""        else:
            st.error(t(":material/error: The alert could NOT be opened. Tell your administrator now."))
""", "")]),
    ("⚠️ el campo elige la fecha", U,
     [("""                         key=f"fc_fecha_{pid}_{_fg}", format="DD/MM/YYYY") if gestor else hoy)\n""", """                         key=f"fc_fecha_{pid}_{_fg}", format="DD/MM/YYYY"))\n""")]),
    ("⚠️ se puede elegir mañana", U,
     [("""    dia = (st.date_input(t("Date"), value=st.session_state.get(f"_fc_dia_{pid}_{_fg}", hoy), max_value=hoy,\n""", """    dia = (st.date_input(t("Date"), value=st.session_state.get(f"_fc_dia_{pid}_{_fg}", hoy),\n""")]),
    ("⚠️ sin montar sale el formulario", U,
     [("""    elif FC.activo(prj, dia):\n""", """    elif True:\n""")]),
    ("⚠️ se rehace lo de otro en vez de firmarlo", U,
     [("""        if _pf:
            _bloque_firmar(_pf, pid, grupo, nombre, usuario)
        elif not _r:
""", """        if not _r:
""")]),
    ("⚠️ el día pedido no llega", U,
     [("""    if dia_pedido:
        st.session_state[f"_fc_dia_{pid}_{_fg}"] = dia_pedido
""", "")]),
    ("⚠️ tocar la fila no deja el día", U,
     [("""            st.session_state["_ps_dia_pending"] = _x["fecha"]\n""", "")]),
    ("⚠️ la tabla no cambia de clave", U,
     [("""            key=f"ps_faltantes_{st.session_state.get(_gk, 0)}", column_config=tabla.cfg())\n""", """            key="ps_faltantes", column_config=tabla.cfg())\n""")]),
    # ── La sección Pre-Start ──
    ("⚠️ sale en obras sin false car", PSU,
     [("""    if FC.tiene(prj):\n        _kdoc = f"cpxseg_ps_doc_{pid}"\n""", """    if True:\n        _kdoc = f"cpxseg_ps_doc_{pid}"\n""")]),
    ("⚠️ empieza por el checklist", PSU,
     [("""        _etq_doc = {"prestart": t("Pre-Start"), "falsecar": t("False car")}\n""", """        _etq_doc = {"falsecar": t("False car"), "prestart": t("Pre-Start")}\n""")]),
    ("⚠️ el atajo no llega al checklist", PSU,
     [("""        if _ps_doc:
            st.session_state[_kdoc] = _ps_doc
""", "")]),
    ("⚠️ el encargo se queda en la sesión", PSU,
     [("""    _ps_doc = st.session_state.pop("_ps_doc_pending", None)\n""", """    _ps_doc = st.session_state.get("_ps_doc_pending", None)\n""")]),
    ("⚠️ el campo ve la lista de la oficina", PSU,
     [("""    if rol == "administrator":\n        from core import falsecar_ui\n""", """    if True:\n        from core import falsecar_ui\n""")]),
    ("⚠️ el Pre-Start de hoy tapa el día pedido", PSU,
     [("""    if _ya_hoy and not _pf and not st.session_state.get(f"_ps_dia_{kp}"):\n""", """    if _ya_hoy and not _pf:\n""")]),
    ("⚠️ el día pedido no llega al Pre-Start", PSU,
     [("""        f_fecha = c1.date_input(t("Date"), value=st.session_state.get(f"_ps_dia_{kp}", hoy),\n""", """        f_fecha = c1.date_input(t("Date"), value=hoy,\n""")]),
    # ── v637 ──
    ("⚠️ tocar la fila no baja", U,
     [("""            st.session_state["_bajar_cpx_ps_obra"] = True\n""", "")]),
    ("⚠️ el bloque de la obra no baja", PSU,
     [("""        _PU._bajar_a("cpx_ps_obra", "_bajar_cpx_ps_obra", bloque="start")\n""", "")]),
    ("⚠️ la regla no se pinta", U,
     [("""    st.markdown(_CSS_PUNTOS, unsafe_allow_html=True)\n""", "")]),
    ("⚠️ el bloque de los puntos cambia de nombre", U,
     [("""    with st.container(key="cpx_fc_puntos"):\n""", """    with st.container(key="cpx_fc_otro"):\n""")]),
    ("en estrecho vuelven a apilarse", U,
     [("""               "{flex:0 0 96px!important;min-width:96px!important;width:96px!important}"\n""", "")]),
    ("⚠️ la firma sigue diminuta en el checklist", PDF,
     [("""st,
                               ancho=60 * mm, alto=18 * mm)],
""", """st)],
""")]),
    ("⚠️ se ignora la caja de la firma", "core/prestart_pdf.py",
     [("""            return RLImage(io.BytesIO(sig), width=ancho, height=alto, kind="proportional")\n""", """            return RLImage(io.BytesIO(sig), width=25 * mm, height=8 * mm, kind="proportional")\n""")]),
    ("⚠️ la firma del Pre-Start cambia de medida", "core/prestart_pdf.py",
     [("""def _celda_firma(a, st, ancho=25 * mm, alto=8 * mm):\n""", """def _celda_firma(a, st, ancho=60 * mm, alto=18 * mm):\n""")]),
    ("⚠️ un doble toque firma dos veces", M,
     [("""    if ya_firmo(asist, nombre, usuario):
        res["ok"], res["archivado"] = True, True
        return res
""", "")]),
    ("⚠️ un doble toque firma dos veces en el Pre-Start", "core/prestart.py",
     [("""    if ya_firmo(_ya, nombre, usuario):
        res.update(ok=True, archivado=True, drive_id=str(fila.get("DriveID", "") or ""))
        return res
""", "")]),
    ("⚠️ un homónimo con otro login no puede firmar", "core/prestart.py",
     [("""    _sin = [x for x in _a if not str(x.get("usuario", "") or "").strip()] if quien_u else _a\n""", """    _sin = _a\n""")]),
    ("⚠️ el aviso sale sobre otro día", U,
     [("""    if _r and (_r.get("dia") != hoy.isoformat() or _r.get("fecha") != dia.isoformat()):\n""", """    if _r and _r.get("dia") != hoy.isoformat():\n""")]),
    # ── v638 ──
    ("⚠️ el botón no marca nada", U,
     [("""            st.session_state[f"fc_res_{kp}_{k}"] = FC.PASA\n""", """            pass\n""")]),
    ("⚠️ el botón pisa una X", U,
     [("""        if st.session_state.get(f"fc_res_{kp}_{k}") is None:
            st.session_state[f"fc_res_{kp}_{k}"] = FC.PASA
""", """        st.session_state[f"fc_res_{kp}_{k}"] = FC.PASA
""")]),
    ("⚠️ el botón marca X", U,
     [("""            st.session_state[f"fc_res_{kp}_{k}"] = FC.PASA\n""", """            st.session_state[f"fc_res_{kp}_{k}"] = FC.FALLA\n""")]),
    ("el botón no se apaga", U,
     [("""              on_click=_marcar_todo, args=(kp,),
              disabled=not any(st.session_state.get(f"fc_res_{kp}_{k}") is None for k, _x in FC.CHECKS))
""", """              on_click=_marcar_todo, args=(kp,))
""")]),
    ("⚠️ el botón no sabe qué formulario es", U,
     [("""              on_click=_marcar_todo, args=(kp,),\n""", """              on_click=_marcar_todo, args=(pid,),\n""")]),
    ("⚠️ el formulario nace marcado", U,
     [("""    st.button(t(":material/done_all: Mark all as passed"), key=f"fc_todo_{kp}", width="stretch",\n""", """    _marcar_todo(kp)
    st.button(t(":material/done_all: Mark all as passed"), key=f"fc_todo_{kp}", width="stretch",\n""")]),
    ("el botón desaparece", U,
     [("""    st.button(t(":material/done_all: Mark all as passed"), key=f"fc_todo_{kp}", width="stretch",
              on_click=_marcar_todo, args=(kp,),
              disabled=not any(st.session_state.get(f"fc_res_{kp}_{k}") is None for k, _x in FC.CHECKS))
""", "")]),
    ("el asistente no lo conoce", "core/chat_agent.py",
     [("""**Mark all as passed**\n""", """\n""")]),
    # ── Los avisos ──
    ("⚠️ dos diálogos en la misma pasada", "app.py",
     [("""    if not aviso_prestart_pendiente(_GRUPO):\n        aviso_falsecar_pendiente(_GRUPO)\n""", """    aviso_prestart_pendiente(_GRUPO)\n    aviso_falsecar_pendiente(_GRUPO)\n""")]),
    ("⚠️ el del checklist no espera a la charla", TU,
     [("""    try:
        if not prestart.hecho_hoy(pid, _g) or _pend_firma_de(pid, _g):
            return
    except Exception:
        return
    _toca = _falsecar_toca(pid, _g)
""", """    _toca = _falsecar_toca(pid, _g)
""")]),
    ("⚠️ no espera a mi firma de la charla", TU,
     [("""        if not prestart.hecho_hoy(pid, _g) or _pend_firma_de(pid, _g):\n""", """        if not prestart.hecho_hoy(pid, _g):\n""")]),
    ("⚠️ «Not now» vuelve a salir", TU,
     [("""    if pid:
        st.session_state[f"_fc_visto_{pid}"] = True
""", "")]),
    ("⚠️ no se arma al fichar", TU,
     [("""    if _falsecar_toca(pid, grupo):
        st.session_state["_fc_aviso"] = {"pid": pid, "nombre": nom_obra, "grupo": grupo}
        st.session_state.pop(f"_fc_visto_{pid}", None)
""", "")]),
    ("⚠️ el atajo lleva al Pre-Start", TU,
     [("""    st.session_state["_ps_doc_pending"] = "falsecar"\n""", "")]),
    ("⚠️ el menú lateral no lo recuerda", TU,
     [("""    elif _toca:
        st.warning(t(":material/warning: Today's **false car check** is missing."))
""", """    elif False:
        st.warning(t(":material/warning: Today's **false car check** is missing."))
""")]),
    ("⚠️ la banda sale junto a la del Pre-Start", HU,
     [("""            from core.timeclock_ui import _ir_a_prestart
            _ir_a_prestart(pid)
    return True
""", """            from core.timeclock_ui import _ir_a_prestart
            _ir_a_prestart(pid)
    return False
""")]),
    ("⚠️ el nombre de la obra sin escapar", HU,
     [("""    _obra = _html.escape(str(prj.get("proyecto", "") or t("this job")))
""", """    _obra = str(prj.get("proyecto", "") or t("this job"))
""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", M,
           [("# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL.", "# (control) columnas nuevas al final.")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for a, b in cambios:
        if txt.count(a) != 1:
            return False, bak, p, "ancla x%d: %s" % (txt.count(a), a[:60])
        txt = txt.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if not ok:
            print("  ESCAPA %s (%s)" % (desc, msg))
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
