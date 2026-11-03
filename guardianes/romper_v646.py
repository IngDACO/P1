# -*- coding: utf-8 -*-
"""Batería de roturas de v646. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v646"
TOPE_S = 240
DL = "core/daily_log.py"
PP = "core/parte_propuestas.py"
U = "core/daily_log_ui.py"
AD = "core/admin_digest.py"
PU = "core/projects_ui.py"
T = "core/chat_tools.py"
CU = "core/chat_ui.py"
A = "core/chat_agent.py"

ROTURAS = [
    # ── Cuándo pasa a la oficina, y quién lo revisa ──
    ("⚠️ a la oficina al día siguiente", DL, [("""DIAS_OFICINA = 2\n""", """DIAS_OFICINA = 1\n""")]),
    ("⚠️ cuenta el día del parte, no cuándo se guardó", DL,
     [("""    d = parse_date(str((r or {}).get("Created", "") or "")[:10]) or parse_date((r or {}).get("Date"))\n""",
       """    d = parse_date((r or {}).get("Date"))\n""")]),
    ("⚠️ también lo ya revisado", DL,
     [("""    return (not revisado(r) and bool(str((r or {}).get("Text", "") or "").strip())\n""",
       """    return (bool(str((r or {}).get("Text", "") or "").strip())\n""")]),
    ("también lo vacío", DL,
     [("""bool(str((r or {}).get("Text", "") or "").strip())\n            and dias_sin_revisar(r, hoy) >= DIAS_OFICINA)""",
       """True\n            and dias_sin_revisar(r, hoy) >= DIAS_OFICINA)""")]),
    ("⚠️ los que esperan, de todas las empresas", DL,
     [("""    out = [r for r in _records() if str(r.get("Group", "")) == str(grupo) and para_la_oficina(r, hoy)]\n""",
       """    out = [r for r in _records() if para_la_oficina(r, hoy)]\n""")]),
    ("⚠️ se pisa un parte ya revisado", DL,
     [("""        if revisado(r):\n            # v646 · ya lo revisó otro (su autor o la oficina): no se pisa quién ni lo acreditado\n            return False, t("This log was already reviewed.")\n""", "")]),
    ("⚠️ la oficina de otra empresa", DL,
     [("""                oficina and str(r.get("Group", "")) == str(oficina)\n""", """                oficina\n""")]),
    ("⚠️ la oficina sin esperar los 2 días", DL,
     [("""                and para_la_oficina(r, clock.today(r.get("Group")))):\n""", """                and True):\n""")]),
    ("⚠️ sin poder leer, se da por sin revisar", DL,
     [("""    w = _ws()\n    if w is None:\n        return False\n    try:\n        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))\n    except Exception as e:\n        logger.warning("daily_log.sin_revisar_aun(""",
       """    w = _ws()\n    if w is None:\n        return True\n    try:\n        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))\n    except Exception as e:\n        logger.warning("daily_log.sin_revisar_aun(""")]),
    ("⚠️ lo revisado se da por sin revisar", DL, [("""    return bool(r) and not revisado(r)\n""", """    return bool(r)\n""")]),
    # ── El registro ──
    ("⚠️ el registro no dice qué venía marcado", PP, [("""        if x.get("premarcadas"):\n""", """        if False:\n""")]),
    ("el registro no dice por quién confirmó la oficina", PP, [("""    if en_nombre_de:\n""", """    if False:\n""")]),
    # ── Premarcado ──
    ("⚠️ nada viene marcado", U, [("""                _seg = f.get("fuente") == "agente" and not f.get("aviso")\n""", """                _seg = False\n""")]),
    ("⚠️ también lo que va bajo «Issues»", U, [("""                _seg = f.get("fuente") == "agente" and not f.get("aviso")\n""", """                _seg = f.get("fuente") == "agente"\n""")]),
    ("⚠️ también lo de la lista de palabras", U, [("""                _seg = f.get("fuente") == "agente" and not f.get("aviso")\n""", """                _seg = not f.get("aviso")\n""")]),
    ("la pantalla no devuelve lo premarcado", U, [(""""premarcadas": list(dict.fromkeys(pre))}""", """"premarcadas": []}""")]),
    ("no dice que viene marcado", U, [(""""The assistant ticked what it is sure of: untick anything that is not right. Nothing is \"""",
                                       """"Tick only what is true. Nothing is \"""")]),
    # ── «Add to To-do» ──
    ("⚠️ lo pendiente, sin «Add to To-do»", U, [("""                if todo:\n                    _boton_tarea(""", """                if False:\n                    _boton_tarea(""")]),
    ("la tarea lleva la cabecera «Pending:»", U, [(""""", tx, flags=re.I).strip()\n""", """"", "", flags=re.I).strip() or tx\n""")]),
    ("⚠️ se ofrece dos veces", U, [("""    if any(TA.normaliza(r.get("Text")) == TA.normaliza(tx) for r in TA.pendientes(pid)):\n""", """    if False:\n""")]),
    ("⚠️ apunta en una obra ajena", U, [("""    if not pet or pet.get("pid") not in mias:\n""", """    if not pet:\n""")]),
    ("⚠️ apunta con otro autor", U, [("""        ok, r = TA.crear(pet["pid"], grupo, pet["texto"], usuario)\n""", """        ok, r = TA.crear(pet["pid"], grupo, pet["texto"], "x")\n""")]),
    ("⚠️ el botón no hace nada", U, [("""    _apuntar_tarea(grupo, usuario, set(_asignables(usuario, grupo, pid)))      # v646 · «Add to To-do»\n""", "")]),
    ("sin tarjeta, lo pendiente sin botón", U, [("""        _pendientes_a_todo(_prev, (lid, str(pid)), kp)        # v646\n""", "")]),
    # ── La oficina confirma por el autor ──
    ("⚠️ la oficina no ve los que le esperan", U, [("""               if DL.para_la_oficina(r, _hoy) else (lambda r=r: _estado_revision(r, pid)))\n""",
                                                    """               if False else (lambda r=r: _estado_revision(r, pid)))\n""")]),
    ("⚠️ la oficina confirma sin esperar los 2 días", U, [("""               if DL.para_la_oficina(r, _hoy) else (lambda r=r: _estado_revision(r, pid)))\n""",
                                                          """               if not DL.revisado(r) else (lambda r=r: _estado_revision(r, pid)))\n""")]),
    ("⚠️ acredita con el nombre del autor", U, [("""                                           quien=usuario, origen=SP.PARTE,\n""",
                                                 """                                           quien=_autor, origen=SP.PARTE,\n""")]),
    ("⚠️ revisa sin decir que es la oficina", U, [("""                    ok, msg = DL.marcar_revisado(lid, usuario, propuestas=_registro(False),\n                                                 **({"oficina": grupo} if oficina else {}))\n""",
                                                   """                    ok, msg = DL.marcar_revisado(lid, usuario, propuestas=_registro(False))\n""")]),
    ("⚠️ la memoria aprende de la oficina", U, [("""                    if ok and not oficina:\n""", """                    if ok:\n""")]),
    ("el registro sin por quién", U, [("""if reg else "", en_nombre_de=_autor if oficina else "")""", """if reg else "")""")]),
    ("⚠️ sin mirar si su autor acaba de revisarlo", U, [("""            if oficina and not DL.sin_revisar_aun(lid):\n                errores.append(t("This log was already reviewed."))\n""", "")]),
    ("⚠️ con el error, acredita igual", U, [("""                for d, res in ({} if errores else por_destino).items():\n""", """                for d, res in por_destino.items():\n""")]),
    ("⚠️ la oficina con «Tell the office» y «Read it again»", U, [("""        if reg and not oficina:\n            _problemas(reg, r, kp)\n""", """        if reg:\n            _problemas(reg, r, kp)\n""")]),
    ("no dice de quién es ni cuánto espera", U, [("""st.markdown(t("##### :material/rate_review: {who}'s log, {n} days without review", who=_nombre(_autor),""",
                                                  """st.markdown(t("##### :material/rate_review: A log without review", who=_nombre(_autor),""")]),
    ("⚠️ sin nada que acreditar, la oficina no lo puede cerrar", U, [("""        if oficina:\n            # v646 · Sin nada que acreditar, la oficina lo cierra""",
                                                                      """        if False:\n            # v646 · Sin nada que acreditar, la oficina lo cierra""")]),
    ("lo cierra sin decir que es la oficina", U, [("""en_nombre_de=_autor),\n                                                 oficina=grupo)\n""", """en_nombre_de=_autor))\n""")]),
    ("no dice que fue por su autor", U, [("""            if _q and _q != str(r.get("Author", "")) else "")\n""", """            if False else "")\n""")]),
    ("⚠️ la oficina no lee los que le esperan", U, [("""             if (DL.para_la_oficina(r, _hoy) if oficina\n""", """             if (False if oficina\n""")]),
    ("la oficina no lee", U, [("""    _leer_pendientes(pid, _u, _p[:25], oficina=True)\n""", "")]),
    ("⚠️ a la oficina, también los de obras sin plan", U, [("""        if _con_plan[pid]:\n            out.append(r)\n""", """        out.append(r)\n""")]),
    # ── Lo pendiente de la oficina y Home ──
    ("⚠️ no cuenta como pendiente", AD, [("""                 "sobre_presupuesto", "partes_por_revisar")\n""", """                 "sobre_presupuesto")\n""")]),
    ("⚠️ el resumen no los busca", AD, [("""        for r in _DLU.partes_para_la_oficina(grupo):\n""", """        for r in []:\n""")]),
    ("la IA no los ve", AD, [("""    if d.get("partes_por_revisar"):\n        L.append(""", """    if False:\n        L.append(""")]),
    ("⚠️ Home sin el indicador", PU, [("""        ("partes", ":material/rate_review:", "Logs to review", False,""", """        ("partes2", ":material/rate_review:", "Logs to review", False,""")]),
    ("Home no lleva a esas obras", PU, [("""                                 "partes": d.get("partes_por_revisar", [])}.get(slug)\n""", """                                 }.get(slug)\n""")]),
    ("⚠️ el Management assistant no los ve", T, [("""        "daily_logs_waiting_review": {"count": len(_partes),""", """        "daily_logs": {"count": len(_partes),""")]),
    ("con el login, no el nombre", T, [(""""author": nom.get(str(r.get("Author", "")), r.get("Author", "")),""", """"author": r.get("Author", ""),""")]),
    # ── Acreditar desde el chat ──
    ("⚠️ guardar el parte no ofrece acreditar", T, [("""            _mas = _ofrecer_credito(str(r), prj, str(d.get("text") or ""), str(d.get("date") or ""), ctx)\n""", """            _mas = ""\n""")]),
    ("⚠️ con dos ascensores, ofrece igual", T, [("""        if _a.get("separar") or _a.get("dudosos"):\n""", """        if False:\n""")]),
    ("⚠️ la lectura no se guarda (se pagaría otra vez)", T, [("""        DLU._apuntar({str(lid): reg}, {})\n""", "")]),
    ("⚠️ la tarjeta lleva también lo que tiene aviso", T, [("""            if not f["hecha"] and f.get("fuente") == "agente" and not f.get("aviso")]\n""", """            if not f["hecha"]]\n""")]),
    ("⚠️ el parte se da por revisado aunque quede algo", T, [("""    return bool(p["preguntas"] or p["pendientes"] or p.get("problemas")""",
                                                              """    return False and bool(p["preguntas"] or p["pendientes"] or p.get("problemas")""")]),
    ("⚠️ acredita el parte de otro", T, [("""    if r is None or str(r.get("Author", "")) != str(ctx["usuario"]):\n        return False, t("That daily log is not yours.")\n""",
                                          """    if r is None:\n        return False, t("That daily log is not yours.")\n""")]),
    ("⚠️ acredita un parte ya revisado", T, [("""    if not DL.sin_revisar_aun(lid):\n        return False, t("That daily log was already reviewed.")\n""", "")]),
    ("⚠️ una tarjeta tocada acredita", T, [("""    elegidas = [_vale[(int(o), str(a))] for o, a in d.get("creditos") or [] if (int(o), str(a)) in _vale]\n""",
                                            """    elegidas = list(_vale.values())\n""")]),
    ("⚠️ sin la fecha del parte", T, [("""quien=ctx["usuario"], origen=SP.PARTE,\n                           fecha=str(r.get("Date", "") or ""))""",
                                       """quien=ctx["usuario"], origen=SP.PARTE,\n                           fecha=None)""")]),
    ("la memoria no aprende del chat", T, [("""    if ok2:\n        DLU._aprender(""", """    if False:\n        DLU._aprender(""")]),
    ("⚠️ la oficina confirma la tarjeta de acreditar", T, [(""""administrator": tuple(_CONFIRMAR_OFICINA)}\n""", """"administrator": tuple(_CONFIRMAR_OFICINA) + ("credito",)}\n""")]),
    ("⚠️ la tarjeta nueva no llega a la lista", CU, [("""        ok, msg = CT.confirmar(a, {**_contexto(), "acciones": lista})\n""", """        ok, msg = CT.confirmar(a, _contexto())\n""")]),
    ("⚠️ el Field assistant no sabe que la tarjeta es de la app", A,
     [("""        "- Al guardar un parte, la app lo lee y puede dejar una tarjeta para acreditar lo que dice con seguridad: esa "
        "tarjeta la pone la APP, no tú, y solo acredita si la persona pulsa **Confirm**. Lo demás del parte (dudas, "
        "pendientes, problemas) lo revisa en **Daily log**.\\n"
""", "")]),
    ("el Management assistant no sabe dónde se confirman", A,
     [("""        "- Un parte que su autor no revisa en 2 días pasa a la oficina: sale en lo pendiente y en **Home** («Logs to "
        "review»), y se confirma en su nombre en **Projects** → la obra → **Status**, abajo del todo. Tú no lo confirmas.\\n"
""", "")]),
    ("la herramienta del parte no lo dice", T, [(""""saved, the app reads it and may offer a second card to credit what it clearly says.\"""", """"saved.\"""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", DL,
           [("# v646 · Decisión del usuario: el parte que su autor no revisa en tantos días pasa a la OFICINA",
             "# v646 · (control) el parte que su autor no revisa en tantos días pasa a la OFICINA")])


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
