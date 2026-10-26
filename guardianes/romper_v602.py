# -*- coding: utf-8 -*-
"""Bateria de roturas de v602 (Contacts → la lista). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en producción probando la lista de Contacts.
⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v602"
CL = "core/clientes.py"
CU = "core/clientes_ui.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el motor ──
    ("⚠️ el email vuelve a aceptar cualquier cosa («abc»)", CL,
     [('    e = str(email or "").strip()\n    return not e or bool(',
       '    e = str(email or "").strip()\n    return True or bool(')]),
    ("⚠️ el alta deja de validar el email", CL,
     [('    if not email_valido(email):\n', '    if False:\n')]),
    ("la edición deja de validar el email", CL,
     [('    if "Email" in fields and not email_valido(fields.get("Email")):\n', '    if False:\n')]),
    ("⚠️ archivar/restaurar vuelve a responder «Client updated.»", CL,
     [('    return True, t("Client restored.") if activo else t("Client archived.")\n',
       '    return True, msg\n')]),
    ("⚠️ los dígitos del teléfono conservan los espacios", CL,
     [('    return "".join(ch for ch in str(s or "") if ch.isdigit())\n', '    return str(s or "")\n')]),
    ("⚠️ la ficha vuelve a buscar solo entre las ACTIVAS", CL,
     [('    fichas = list_clientes(grupo, incluir_inactivos=True)\n',
       '    fichas = list_clientes(grupo, incluir_inactivos=False)\n')]),
    ("la ficha deja de encontrarse por su ID", CL,
     [('    for f in fichas:\n        if str(f.get("ID", "")) == clave:\n            return f\n', '')]),
    ("la ficha deja de encontrarse por el NOMBRE (lo que llega de Invoices)", CL,
     [('    for f in fichas:\n        if _norm(f.get("Name")) == _norm(clave):\n            return f\n', '')]),
    # ── la ficha ──
    ("⚠️ la ficha vuelve a buscarse por nombre entre las activas (la archivada, sin «Restore»)", CU,
     [('    f = C.ficha_de(grupo, key)\n',
       '    f = next((x for x in C.list_clientes(grupo) if _norm(x.get("Name")) == key), {})\n')]),
    ("restaurar deja de avisar", CU,
     [('                    (flash.exito if ok else st.error)(msg)\n',
       '                    (st.error if not ok else (lambda m: None))(msg)\n')]),
    ("⚠️ archivar vuelve a la lista sin decir nada", CU,
     [('                            flash.exito(msg)          # v602 · avisa (volvía a la lista sin decir nada)\n', '')]),
    ("⚠️ el teléfono vuelve a ser texto (sin `tel:`)", CU,
     [("""        st.markdown(f':material/call: <a href="tel:{_num_tel}">{_h.escape(_tel)}</a>',""",
       """        st.markdown(f':material/call: {_h.escape(_tel)}',""")]),
    # (v603 · re-anclada: el email va en markdown, `maps.enlace_md`; el <a> dejaba uno VACÍO)
    ("el email vuelve a ser texto (sin `mailto:`)", CU,
     [('        st.markdown(":material/mail: " + maps.enlace_md(_mail, "mailto:" + _mail))\n',
       '        st.markdown(":material/mail: " + maps.literal_md(_mail))\n')]),
    ("⚠️ la ficha vuelve a enviarse con Enter", CU,
     [('with st.form(f"cli_form_{key}", enter_to_submit=False):', 'with st.form(f"cli_form_{key}"):')]),
    # ── la lista ──
    ("⚠️ la búsqueda vuelve a perderse al abrir una ficha", CU,
     [('                       key="cli_q", persist_state="session",\n', '                       key="cli_q",\n')]),
    ("la casilla de archivados vuelve a perderse", CU,
     [('                            key="cli_ver_arch", persist_state="session",\n',
       '                            key="cli_ver_arch",\n')]),
    ("⚠️ el aviso de archivados vuelve a ser MUDO (no enseña nada)", CU,
     [('key="cli_ver_arch_btn", type="tertiary", on_click=_ver_archivados)',
       'key="cli_ver_arch_btn", type="tertiary", on_click=None)')]),
    ("los plurales vuelven a «(s)» (siempre la forma de varios)", CU,
     [('    return t(uno, n=n) if n == 1 else t(varios, n=n)\n', '    return t(varios, n=n)\n')]),
    ("el pie de la tabla vuelve a «client(s)»", CU,
     [('_plural(len(rows), "({n} client)", "({n} clients)")', 't("({n} client(s))", n=len(rows))')]),
    ("⚠️ el teléfono sin espacios vuelve a no encontrarse", CU,
     [('\n            or (len(_qd) >= 3 and _qd in C.solo_digitos(r["Phone"]))]', ']')]),
    ("⚠️ «nada coincide» vuelve a quedarse sin salida", CU,
     [('            st.button(t(":material/filter_alt_off: Show all"), key="cli_ver_todos", on_click=_ver_todos)\n', '')]),
    ("«Show all» deja la búsqueda puesta", CU,
     [('    st.session_state["cli_q"] = ""\n    st.session_state["cpxseg_clis_filt"] = "Todos"\n',
       '    st.session_state["cpxseg_clis_filt"] = "Todos"\n')]),
    ("⚠️ una cifra vuelve a no bajar a la tabla", CU,
     [('                st.session_state["_bajar_cpx_clis_tabla"] = True   # v602 · y baja a ella\n', '')]),
    ("una cifra deja la búsqueda puesta (cuenta una cosa y enseña otra)", CU,
     [('                st.session_state["cli_q"] = ""       # v602 · la cifra cuenta la lista ENTERA\n', '')]),
    ("la tabla sale del bloque al que se baja", CU,
     [('    with st.container(key="cpx_clis_tabla"):           # v602 · destino de las cifras\n',
       '    with st.container():\n')]),
    ("⚠️ un toque vuelve a abrir la ficha por el NOMBRE (no por su ID)", CU,
     [('st.session_state["_cli_open"] = rows[_sel]["cid"] or rows[_sel]["key"]',
       'st.session_state["_cli_open"] = rows[_sel]["key"]')]),
    ("⚠️ el avance medio vuelve a contar las canceladas", CU,
     [('    _cuentan = [x for x in proys if str(x.get("Status", "")) not in ("Cancelled", "Archived")]\n',
       '    _cuentan = list(proys)\n')]),
    ("⚠️ «Record» vuelve a la 2ª columna (las obras, fuera de la vista)", CU,
     [('        "Ficha":     (t("Archived") if r.get("archivado") else t("Yes")) if r["ficha"] else "—",\n', ''),
      ('        "Cliente":   r["disp"],\n',
       '        "Cliente":   r["disp"],\n'
       '        "Ficha":     (t("Archived") if r.get("archivado") else t("Yes")) if r["ficha"] else "—",\n')]),
    ("las horas vuelven sin unidad", CU,
     [('        # nombre que esa columna tiene en la ficha y en el resto de la app (decía «Alarms»)\n'
       '        "Horas": st.column_config.NumberColumn(t("Hours"), format="%.1f h"),',
       '        # nombre que esa columna tiene en la ficha y en el resto de la app (decía «Alarms»)\n'
       '        "Horas": st.column_config.NumberColumn(t("Hours"), format="%.1f"),')]),
    ("la columna vuelve a llamarse «Alarms»", CU,
     [('        "Alarms": st.column_config.TextColumn(t("Open alerts")),',
       '        "Alarms": st.column_config.TextColumn(t("Alarms")),')]),
    ("«Yes» vuelve a «yes»", CU,
     [('else t("Yes")) if r["ficha"]', 'else t("yes")) if r["ficha"]')]),
    ("⚠️ el archivado vuelve a no distinguirse en la tabla", CU,
     [('(t("Archived") if r.get("archivado") else t("Yes")) if r["ficha"]', 't("Yes") if r["ficha"]')]),
    # ── el alta ──
    ("⚠️ el alta vuelve a enviarse con Enter", CU,
     [('with st.form(f"cli_nuevo_{_g}", enter_to_submit=False):', 'with st.form(f"cli_nuevo_{_g}"):')]),
    ("⚠️ el alta vuelve a quedarse con lo tecleado (sin generación nueva)", CU,
     [('                st.session_state["_cli_new_gen"] = _g + 1\n', '')]),
    ("los campos del alta vuelven a una clave fija", CU,
     [('key=f"cli_new_nom_{_g}"', 'key="cli_new_nom"')]),
    ("el alta nueva abre la ficha por el NOMBRE", CU,
     [('                st.session_state["_cli_open"] = msg          # v602 · por su ID\n',
       '                st.session_state["_cli_open"] = _norm(_nom)\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           CL, [('    """v602 · Los dígitos de un teléfono, para buscarlo con o sin espacios («02 9000 1003»)."""',
                 '    """v602 · Los dígitos de un teléfono, para buscarlo con o sin espacios («02 9000 1003»). (control)"""')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
