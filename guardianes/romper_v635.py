# -*- coding: utf-8 -*-
"""Batería de roturas de v635. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v635"
TOPE_S = 180
M = "core/tareas.py"
U = "core/tareas_ui.py"

ROTURAS = [
    # ── Comentar ──
    ("⚠️ se admite un comentario vacío", M,
     [('    if not _txt:\n        return False, t("Write the comment first.")\n', '')]),
    ("sin límite de largo", M,
     [('    if len(_txt) > MAX_COMENTARIO:\n', '    if False:\n')]),
    ("el límite cambia", M,
     [('MAX_COMENTARIO = 500\n', 'MAX_COMENTARIO = 200\n')]),
    ("se pierden los saltos de línea", M,
     [("""    _txt = re.sub(r"\\n{3,}", "\\n\\n", str(texto or "").replace("\\r\\n", "\\n")).strip()\n""", """    _txt = re.sub(r"\\s+", " ", str(texto or "")).strip()\n""")]),
    ("⚠️ se comenta una tarea borrada", M,
     [("""        _f, r = _fila(_frescos(w), tid, pid)
        if _f is None or not _activa(r):
            return False, t("That task is no longer on the list.")
        wc = _ws_com()
""", """        _f, r = _fila(_frescos(w), tid, pid)
        if _f is None:
            return False, t("That task is no longer on the list.")
        wc = _ws_com()
""")]),
    ("⚠️ se comenta una que no es de esta obra", M,
     [("""        _f, r = _fila(_frescos(w), tid, pid)
        if _f is None or not _activa(r):
            return False, t("That task is no longer on the list.")
        wc = _ws_com()
""", """        wc = _ws_com()
""")]),
    ("⚠️ un doble toque duplica", M,
     [("""        if _ya is not None:
            return True, str(_ya.get("ID", ""))
""", "")]),
    ("otro autor no puede decir lo mismo", M,
     [("""                    and str(c.get("CreatedBy", "")) == str(autor)
                    and normaliza(c.get("Text")) == normaliza(_txt)), None)
""", """                    and normaliza(c.get("Text")) == normaliza(_txt)), None)
""")]),
    ("⚠️ el ID no pasa por el generador común", M,
     [('        return hojas.siguiente_id_libre("TKC-", n, propia=SHEET_COM)\n', '        return "TKC-%04d" % (n + 1)\n')]),
    ("no queda cuándo", M,
     [("""        wc.append_row([cid, str(grupo or ""), str(pid), str(tid), _txt, str(autor or ""), _ahora,
""", """        wc.append_row([cid, str(grupo or ""), str(pid), str(tid), _txt, str(autor or ""), "",
""")]),
    # ── Leer ──
    ("⚠️ se cuelan los de otra obra", M,
     [("""        if (str(c.get("ProjectID", "")) == str(pid) and _activa(c)
                and str(c.get("Text", "")).strip()):
""", """        if (_activa(c)
                and str(c.get("Text", "")).strip()):
""")]),
    ("⚠️ se ven los borrados", M,
     [("""        if (str(c.get("ProjectID", "")) == str(pid) and _activa(c)
                and str(c.get("Text", "")).strip()):
""", """        if (str(c.get("ProjectID", "")) == str(pid)
                and str(c.get("Text", "")).strip()):
""")]),
    ("el orden se invierte", M,
     [("""        lista.sort(key=lambda c: (str(c.get("Created", "")), str(c.get("ID", ""))))
""", """        lista.sort(key=lambda c: (str(c.get("Created", "")), str(c.get("ID", ""))), reverse=True)
""")]),
    # ── Borrar ──
    ("⚠️ cualquiera borra", M,
     [("""        return False, t("That comment is no longer there.")
    if not puede_borrar(r, quien, gestor):
        return False, t("Only the person who wrote it (or the office) can delete it.")
""", """        return False, t("That comment is no longer there.")
""")]),
    ("⚠️ borrar elimina la fila en vez de ocultarla", M,
     [("""            {"range": "%s%d" % (col_letter(_COL_COM["Active"]), fila), "values": [["NO"]]},
            {"range": "%s%d" % (col_letter(_COL_COM["DeletedBy"]), fila), "values": [[str(quien)]]},
            {"range": "%s%d" % (col_letter(_COL_COM["DeletedAt"]), fila), "values": [[_ahora]]},
        ], value_input_option="RAW")
""", """        ], value_input_option="RAW")
        wc.delete_rows(fila)
""")]),
    ("no queda quién lo borró", M,
     [("""            {"range": "%s%d" % (col_letter(_COL_COM["DeletedBy"]), fila), "values": [[str(quien)]]},\n""", "")]),
    ("⚠️ borrar la obra deja los comentarios", M,
     [("    _borrar_comentarios_de_obra(pid)\n    return n\n", "    return n\n")]),
    ("⚠️ borrar se lleva los de otras obras", M,
     [("""        filas = [i + 2 for i, c in enumerate(_frescos(wc)) if str(c.get("ProjectID", "")) == str(pid)]\n""", """        filas = [i + 2 for i, c in enumerate(_frescos(wc))]\n""")]),
    ("⚠️ borrar una obra sin comentarios crea la hoja", M,
     [("""        if not any(str(c.get("ProjectID", "")) == str(pid) for c in _registros_com()):
            return 0
""", "")]),
    # ── Lo que lo rodea ──
    ("⚠️ la hoja se sale del lote: leería vacío para siempre", "core/hojas.py",
     [('    "TaskComments",\n', '')]),
    ("⚠️ el lector crea la hoja", M,
     [('    return hojas.registros(SHEET_COM) or []\n', '    return hojas.registros(SHEET_COM, HEADERS_COM) or []\n')]),
    ("la guía no lo sabe", "core/chat_agent.py",
     [("Cada tarea tiene\n    **Comments**:", "Cada tarea tiene\n    notas:")]),
    # ── La pantalla ──
    ("⚠️ el comentario sale sin escapar", U,
     [("""            st.markdown(literal_md(c.get("Text", "")).replace("\\n", "  \\n"))\n""", """            st.markdown(str(c.get("Text", "")).replace("\\n", "  \\n"))\n""")]),
    ("se pierden los saltos al pintar", U,
     [("""            st.markdown(literal_md(c.get("Text", "")).replace("\\n", "  \\n"))\n""", """            st.markdown(literal_md(c.get("Text", "")))\n""")]),
    ("⚠️ el número no se ve", U,
     [("""    with st.expander(t("Comments ({n})", n=_n) if _n else t("Add a comment"),\n""", """    with st.expander(t("Add a comment"),\n""")]),
    ("⚠️ el desplegable sale abierto", U,
     [("""                     icon=":material/chat_bubble:", key=f"{kp}_td_exp_com_{pid}_{tid}"):\n""", """                     icon=":material/chat_bubble:", expanded=True, key=f"{kp}_td_exp_com_{pid}_{tid}"):\n""")]),
    ("⚠️ Enter envía", U,
     [("""border=False, enter_to_submit=False):\n""", """border=False):\n""")]),
    ("⚠️ se le ofrece borrar lo de otro", U,
     [("""            if not T.puede_borrar(c, usuario, gestor):
                continue
            if st.session_state.get(_CBORRA) != _cid:
""", """            if st.session_state.get(_CBORRA) != _cid:
""")]),
    ("⚠️ borrar se va de un toque", U,
     [("""                          type="tertiary", on_click=_confirmar_borrar_com, args=(_cid,))\n""", """                          type="tertiary", on_click=_pedir_borrar_com, args=(pid, _cid))\n""")]),
    ("«Keep it» borra", U,
     [("""            b2.button(t("Keep it"), key=f"{kp}_td_cdelno_{pid}_{_cid}", width="stretch",
                      on_click=_no_borrar_com)
""", """            b2.button(t("Keep it"), key=f"{kp}_td_cdelno_{pid}_{_cid}", width="stretch",
                      on_click=_pedir_borrar_com, args=(pid, _cid))
""")]),
    ("⚠️ la caja no se vacía", U,
     [("""                st.session_state[_k] = int(st.session_state.get(_k, 0)) + 1   # la caja nace vacía
            else:
                flash.error(r)                    # lo escrito SE QUEDA, como en el alta
""", """                pass
            else:
                flash.error(r)                    # lo escrito SE QUEDA, como en el alta
""")]),
    ("⚠️ el fallo se calla", U,
     [("""            else:
                flash.error(r)                    # lo escrito SE QUEDA, como en el alta
""", "")]),
    ("⚠️ se pierde lo escrito si falla", U,
     [("""            ok, r = T.comentar(pet.get("tid"), pid, grupo, pet.get("texto"), usuario)
            if ok:
                _k = _clave_cgen(pet.get("kp"), pid, pet.get("tid"))
""", """            ok, r = T.comentar(pet.get("tid"), pid, grupo, pet.get("texto"), usuario)
            if True:
                _k = _clave_cgen(pet.get("kp"), pid, pet.get("tid"))
""")]),
    ("⚠️ las hechas no se pueden comentar", U,
     [("""                             d=_dmy(_da) + (" " + _da[11:16] if len(_da) >= 16 else "")))
                _comentarios(kp, pid, _tid, _com.get(_tid, []), usuario, gestor)
""", """                             d=_dmy(_da) + (" " + _da[11:16] if len(_da) >= 16 else "")))
""")]),
    ("el comentario se pega a otra tarea", U,
     [("""            st.form_submit_button(t(":material/send: Comment"), key=f"{kp}_td_csend_{pid}_{tid}",
                                  on_click=_pedir_comentario, args=(kp, pid, tid))
""", """            st.form_submit_button(t(":material/send: Comment"), key=f"{kp}_td_csend_{pid}_{tid}",
                                  on_click=_pedir_comentario, args=(kp, pid, "TSK-1"))
""")]),
    ("el autor sale por su login", U,
     [("""            st.caption(t("{q} · {d}", q=_nombre(c.get("CreatedBy")),\n""", """            st.caption(t("{q} · {d}", q=c.get("CreatedBy"),\n""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", M,
           [("# una tarea es una línea («Pick up the landing door keys»), no un parte", "# (control) una tarea es una línea, no un parte")])


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
