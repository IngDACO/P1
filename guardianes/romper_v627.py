# -*- coding: utf-8 -*-
"""Batería de roturas de v627. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v627"
TOPE_S = 240
M = "core/ausencias.py"
U = "core/ausencias_ui.py"
AI = "core/auth_ui.py"
PY = "core/payroll_ui.py"

ROTURAS = [
    # ── El motor ──
    ("⚠️ lo pendiente deja de contar en lo disponible", M,
     [('            "disponibles": round(asignados - usados - pend, 1),\n', '            "disponibles": round(asignados - usados, 1),\n')]),
    ("⚠️ el motor deja pedir más de lo disponible", M,
     [('    if _ex and cfg["aprobacion"]:\n        return t("You are asking for {n}', '    if False:\n        return t("You are asking for {n}')]),
    ("⚠️⚠️ el motor tampoco deja registrar una baja sin saldo", M,
     [('    if _ex and cfg["aprobacion"]:\n        return t("You are asking for {n}', '    if _ex:\n        return t("You are asking for {n}')]),
    ("⚠️ vuelve a escribirse el exceso, que se desincroniza", M,
     [('            "", str(usuario), hoy,\n', '            (f"Over the balance by {_ex}" if _ex else ""), str(usuario), hoy,\n')]),
    ("lo que no tiene tope excede", M,
     [('    return 0 if s["ilimitado"] else max(0, int(dias - max(s["disponibles"], 0)))\n',
       '    return max(0, int(dias - max(s["disponibles"], 0)))\n')]),
    ("el choque, otra vez en ISO", M,
     [("""{dmy(_r.get('From'))} → {dmy(_r.get('To'))}, {t(str(_r.get('Status')))}).")""",
       """{_r.get('From')} → {_r.get('To')}, {t(str(_r.get('Status')))}).")""")]),
    ("⚠️ el motor deja cancelar lo ya disfrutado", M,
     [('    if not gestor and not cancelable_por_el_campo(recs[fila - 2]):\n', '    if False:\n')]),
    ("⚠️ la oficina tampoco puede cancelar", M,
     [('    if not gestor and not cancelable_por_el_campo(recs[fila - 2]):\n', '    if not cancelable_por_el_campo(recs[fila - 2]):\n')]),
    ("⚠️ se puede cancelar lo que empieza hoy", M,
     [('    return _e == APROBADA and bool(d0) and d0 > (hoy or clock.today(r.get("Group")))\n',
       '    return _e == APROBADA and bool(d0) and d0 >= (hoy or clock.today(r.get("Group")))\n')]),
    ("una pendiente pasada ya no se puede retirar", M,
     [('    _e = str(r.get("Status", ""))\n    if _e == PENDIENTE:\n        return True\n', '    _e = str(r.get("Status", ""))\n')]),
    ("⚠️ la bandeja deja de identificarse como oficina", U,
     [('        ok, msg = AU.cancelar(aid, quien, gestor=True)\n', '        ok, msg = AU.cancelar(aid, quien)\n')]),
    # ── My absences ──
    ("⚠️ vuelve el título doble", U,
     [('    _accion_mia(grupo, usuario, nombre)      # v627 · ACCIÓN DIFERIDA (v555)\n',
       '    st.markdown(t("## :material/event_busy: My absences"))\n    _accion_mia(grupo, usuario, nombre)      # v627 · ACCIÓN DIFERIDA (v555)\n')]),
    ("⚠️ la cifra deja de filtrar", U,
     [('                st.session_state["_aus_mia_filtro"] = "" if _f == _tp else _tp\n', '')]),
    ("la cifra no se quita al tocarla otra vez", U,
     [('                st.session_state["_aus_mia_filtro"] = "" if _f == _tp else _tp\n', '                st.session_state["_aus_mia_filtro"] = _tp\n')]),
    ("la lista no se filtra", U,
     [("""    _lista = [r for r in mias if not _f or str(r.get("Type")) == _f]\n""", """    _lista = list(mias)\n""")]),
    ("⚠️ la cifra enseña lo que queda, sin lo pendiente", U,
     [("""            _v = f"{max(s['disponibles'], 0):.0f}"\n""", """            _v = f"{max(s['restantes'], 0):.0f}"\n""")]),
    ("lo pendiente no se ve en la tarjeta", U,
     [("""            if s["pendientes"]:\n""", """            if False:\n""")]),
    ("⚠️ el periodo vuelve a ISO", U,
     [('''"balance will count from your anniversary.", a=_fdma(_per["desde"]),\n                     b=_fdma(_per["hasta"])))''',
       '''"balance will count from your anniversary.", a=_per["desde"],\n                     b=_per["hasta"]))''')]),
    ("⚠️ el formulario no nace vacío", U,
     [('                st.session_state["_aus_gen"] = _g + 1\n', '')]),
    ("⚠️ desaparece el contador", U,
     [('            st.caption(_txt)\n', '')]),
    ("el contador no resta", U,
     [("""                _txt += " · " + t("{n} left after this", n=f"{_s['disponibles'] - _n:.0f}")\n""",
       """                _txt += " · " + t("{n} left after this", n=f"{_s['disponibles']:.0f}")\n""")]),
    ("⚠️ el botón deja enviar lo imposible", U,
     [('type="primary", width="stretch", key="aus_enviar", disabled=bool(_no)):', 'type="primary", width="stretch", key="aus_enviar"):')]),
    ("⚠️ la pantalla bloquea la baja sin saldo", U,
     [('        elif _ex and cfg["aprobacion"]:\n            _no = t(', '        elif _ex:\n            _no = t(')]),
    ("no avisa de que la baja pasa del saldo", U,
     [('        elif _ex:\n            st.warning(t(":material/warning: This goes', '        elif False:\n            st.warning(t(":material/warning: This goes')]),
    ("⚠️ la oficina no se entera del exceso", U,
     [('    _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg, _ex)\n', '    _avisar_admins(grupo, nombre, tipo, desde, hasta, cfg)\n')]),
    ("⚠️ un toque vuelve a cancelar", U,
     [('                st.session_state["_aus_mia_cancelar"] = aid\n                st.rerun()\n            return\n',
       '                st.session_state["_aus_mia_accion"] = aid\n                st.rerun()\n            return\n')]),
    ("⚠️ confirmar no cancela", U,
     [('            st.session_state["_aus_mia_accion"] = aid\n            st.rerun()\n        if b2.button', '            st.rerun()\n        if b2.button')]),
    ("«Keep it» no cierra la pregunta", U,
     [('        if b2.button(t("Keep it"), key=f"auscanno_{aid}", width="stretch"):\n            st.session_state.pop("_aus_mia_cancelar", None)\n',
       '        if b2.button(t("Keep it"), key=f"auscanno_{aid}", width="stretch"):\n')]),
    ("⚠️ se ofrece cancelar lo ya disfrutado", U,
     [('        if not AU.cancelable_por_el_campo(r):\n            st.caption(', '        if False:\n            st.caption(')]),
    ("⚠️ se puede tocar lo de otra persona", U,
     [('    if str(r.get("User", "")) != str(usuario):\n        flash.error(t("Request not found."))\n        st.rerun()\n', '')]),
    ("⚠️ cancelar no quita del tablero", U,
     [('            AU.aplicar_al_roster(r, quitar=True)\n            # ⚠️ v432', '            # ⚠️ v432')]),
    ("⚠️ retirar una pendiente avisa a todos", U,
     [('    ok, msg = AU.cancelar(aid, usuario)\n    if ok:\n        flash.exito(msg)\n        if _estaba:\n',
       '    ok, msg = AU.cancelar(aid, usuario)\n    if ok:\n        flash.exito(msg)\n        if True:\n')]),
    ("⚠️ quien resolvió, otra vez por su login", U,
     [("""_pie.append(t("resolved by {x}", x=literal_md(_etq_us([_por]).get(_por, _por))))""", """_pie.append(t("resolved by {x}", x=_por))""")]),
    ("«(automatic)» vuelve a parecer una persona", U,
     [("""        if _por and _por != str(usuario) and not _por.startswith("("):\n""", """        if _por and _por != str(usuario):\n""")]),
    ("«nota:» vuelve al español", U,
     [("""_pie.append(t("Note: {x}", x=literal_md(r.get("AdminNote"))))""", """_pie.append(f"nota: {literal_md(r.get('AdminNote'))}")""")]),
    ("el motivo sin escapar", U,
     [("""            _pie.append(literal_md(r.get("Reason")))\n""", """            _pie.append(str(r.get("Reason")))\n""")]),
    ("⚠️ la lista se corta sin decirlo", U,
     [('''    if len(_vis) < len(_lista) and st.button(t("Show all ({n})", n=len(_lista)), key="aus_ver_todas"):\n        st.session_state["_aus_mia_todas"] = True\n        st.rerun()\n''', '')]),
    ("«1 day(s)» otra vez", U,
     [('''    return t("1 day") if n == 1 else t("{n} days", n=n)\n''', '''    return t("{n} day(s)", n=n)\n''')]),
    ("el aviso de cancelación, en ISO", U,
     [('''f"from {_fdma(r.get('From'))} to {_fdma(r.get('To'))}.",''', '''f"from {r.get('From')} to {r.get('To')}.",''')]),
    ("el aviso de la solicitud, en ISO", U,
     [('''f"From {_fdma(desde)} to {_fdma(hasta)}.",''', '''f"From {desde} to {hasta}.",''')]),
    # ── My credentials ──
    ("⚠️ el campo vuelve a la tabla", AI,
     [('        if not editable:\n            _tarjetas_cred(C, _vis, key_prefix)\n        elif _vis:\n', '        if _vis:\n')]),
    ("⚠️ la oficina pierde la tabla", AI,
     [('        if not editable:\n            _tarjetas_cred(C, _vis, key_prefix)\n        elif _vis:\n', '        if True:\n            _tarjetas_cred(C, _vis, key_prefix)\n        elif _vis:\n')]),
    ("⚠️ el documento se baja al pintar", AI,
     [('data=lambda: drive_store.download(_did),\n                       file_name=r.get("File")', 'data=drive_store.download(_did),\n                       file_name=r.get("File")')]),
    ("⚠️ v628 · el número de credenciales, otra vez como un pie", AI,
     [("""if _col.button(f"{_l}\\n\\n{_v}\\n\\n{_pie}", key=f"cpxkpi_cred_{_s or 'todas'}",""",
       """if _col.button(f"{_l}\\n\\n{_v}", key=f"cpxkpi_cred_{_s or 'todas'}",""")]),
    ("⚠️ la cifra de credenciales deja de filtrar", AI,
     [('                    st.session_state[_kf] = "" if _f == _s else _s\n', '')]),
    ("el filtro de credenciales no se quita", AI,
     [('                    st.session_state[_kf] = "" if _f == _s else _s\n', '                    st.session_state[_kf] = _s\n')]),
    ("⚠️ lo vencido ya no va primero", AI,
     [('    _orden = {"vencido": 0, "por_vencer": 1, "vigente": 2}\n', '    _orden = {"vencido": 2, "por_vencer": 1, "vigente": 0}\n')]),
    ("⚠️ dentro del mismo estado, sin orden", AI,
     [("""                                          C.dias_para(x.get("ExpiryDate")) or 0)):\n""", """                                          0)):\n""")]),
    ("⚠️ la vencida sin fecha", AI,
     [('        return t(":red[:material/cancel:] **Expired** on {f}", f=_f)\n', '        return t(":red[:material/cancel:] **Expired**")\n')]),
    ("⚠️ «Expires» sin decir cuándo", AI,
     [('t(":orange[:material/schedule:] **Expires in {n} days** · {f}", n=_n, f=_f))', 't(":orange[:material/schedule:] **Expiring**"))')]),
    ("«No expiry» se pierde en la oficina", AI,
     [('''"Estado": (_etq(C.estado(r)).capitalize() if r.get("ExpiryDate") or not C.completa(r)
                           else t("No expiry")),''', '''"Estado": _etq(C.estado(r)).capitalize(),''')]),
    ("⚠️ la tabla de la oficina, otra vez en ISO", AI,
     [('"Vence": _dmy(r.get("ExpiryDate")), "Number": r.get("Number"),', '"Vence": r.get("ExpiryDate") or "—", "Number": r.get("Number"),')]),
    ("el número sin escapar", AI,
     [('_d.append(t("No. {x}", x=_lit(r.get("Number"))))', '_d.append(t("No. {x}", x=r.get("Number")))')]),
    ("vuelve el título de My credentials", AI,
     [('''    a = st.session_state.get("auth", {})\n    st.caption(t("Your tickets''', '''    a = st.session_state.get("auth", {})\n    st.markdown(t("### :material/badge: My credentials"))\n    st.caption(t("Your tickets''')]),
    # ── My payslips ──
    ("⚠️⚠️ los PDF se generan al pintar", PY,
     [('data=lambda f=f: _pdf_colilla(f, grupo),\n', 'data=_pdf_colilla(f, grupo),\n')]),
    ("⚠️ se enseñan todas de entrada", PY,
     [('    _vis = _orden if st.session_state.get("_mis_colillas_todas") else _orden[:_MAX_COLILLAS]\n', '    _vis = _orden\n')]),
    ("«Show all» no enseña todas", PY,
     [('        st.session_state["_mis_colillas_todas"] = True\n', '')]),
    ("vuelve el título de My payslips", PY,
     [('''    """⚠️ Sin título propio (v627): `_sub_header` ya pinta «Self-service · My payslips»."""\n''',
       '''    st.markdown(t("## :material/payments: My payslips"))\n''')]),
    ("⚠️ se pierde la fecha de pago", PY,
     [('''t("paid on {d}", d=_dmy(_pago)) if _est == "pagada" and _pago else _etq(_est)''', '''_etq(_est)''')]),
    ("la fecha de pago, en ISO", PY,
     [('''t("paid on {d}", d=_dmy(_pago))''', '''t("paid on {d}", d=_pago)''')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", M,
           [("""    """ + '"""v627 · Cuántos de esos `dias` pasan del saldo disponible (0 si el tipo no tiene tope)."""' + """""",
             """    """ + '"""v627 · (control) Cuántos de esos `dias` pasan del saldo disponible."""' + """""")])


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
