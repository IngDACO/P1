# -*- coding: utf-8 -*-
"""Bateria de roturas de v603 (lo visto verificando v602, en toda la app). ⚠️ Verde de BASE
primero (v459) y NO en paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es
una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo medido en producción o en las mini-apps de v602-v603.
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
G = "verif_v603"
MP = "core/maps.py"
CU = "core/clientes_ui.py"
NT = "core/notify.py"
EN = "core/email_notify.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
FL = "core/flash.py"
IU = "core/invoices_ui.py"
AP = "app.py"
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
    # ── los enlaces ──
    ("⚠️ el texto vuelve a interpretarse como markdown (cursivas, corchetes)", MP,
     [('    return _MD_ESPECIAL.sub(r"\\\\\\1", str(texto or ""))\n', '    return str(texto or "")\n')]),
    ("⚠️ la dirección de Maps vuelve sin escapar («*gate 2*» en cursiva)", MP,
     [('    return f"[{literal_md(lbl)}]({url})"           # v603 · la dirección, TAL CUAL\n',
       '    return f"[{lbl}]({url})"\n')]),
    ("⚠️ el ancla HTML de Maps vuelve sin escapar («<Ground>» tragado)", MP,
     [('    lbl = html.escape(str(label if label is not None else location).strip())\n',
       '    lbl = str(label if label is not None else location).strip()\n')]),
    ("la URL de un enlace vuelve sin codificar (un «)» lo corta)", MP,
     [('    return f"[{literal_md(texto)}]({_u})"\n', '    return f"[{literal_md(texto)}]({url})"\n')]),
    ("⚠️ el email de la ficha vuelve a un <a> (y el enlace VACÍO delante)", CU,
     [('        st.markdown(":material/mail: " + maps.enlace_md(_mail, "mailto:" + _mail))\n',
       """        st.markdown(f':material/mail: <a href="mailto:{_mail}">{_mail}</a>', unsafe_allow_html=True)\n""")]),
    # ── los avisos por correo y Telegram ──
    ("⚠️ los avisos vuelven a mandar el texto SIN escapar", NT,
     [('    text = html_seguro(text)                      # v603 · el texto ajeno, escapado\n', '')]),
    ("el escape se come las etiquetas de la app (<b>, <br>)", NT,
     [('    s = _ETQ_OK.sub(r"<\\1>", s)\n', '')]),
    ("el escape se come los enlaces (<a href>)", NT,
     [("    s = _A_OK.sub(r'<a href=\"\\1\">', s)\n", '')]),
    ("el correo interno vuelve a meter la obra sin escapar", EN,
     [("{_html.escape(proyecto or '(not specified)')}", "{proyecto or '(not specified)'}")]),
    # ── arriba al cambiar de vista ──
    ("⚠️ la shell deja de subir (la ficha nueva, ~190 px abajo)", AP,
     [('_home.subir_si_cambia_la_vista()\n', '')]),
    ("⚠️ abrir una ficha deja de contar como otra vista", HU,
     [('_RE_ABIERTO = re.compile(r"^_[a-z]+_(open(_[a-z]+)?|nuev[oa])$")',
       '_RE_ABIERTO = re.compile(r"^$")')]),
    ("⚠️ otra sección del menú deja de contar (Inventory donde estaba la lista)", HU,
     [('    return (_donde(st.session_state.get("_admin_sec", "")),\n', '    return (None,\n')]),
    ("la búsqueda de arriba deja de contar", HU,
     [('            bool(str(st.session_state.get("topbar_search", "") or "").strip()), _ab)\n',
       '            False, _ab)\n')]),
    ("⚠️ la subida pisa lo que se pidió BAJAR", HU,
     [('    if st.session_state.pop("_bajada_pedida", False):\n        return\n', '')]),
    ("la 1ª pasada de la sesión también sube", HU,
     [('    if ant is not None and ant != v:\n', '    if ant != v:\n')]),
    ("⚠️ un aviso nuevo fuera de la vista deja de verse («1 project linked.» a -488 px)", HU,
     [('    elif _nuevo:\n        _PU._subir_arriba(solo_si_aviso_oculto=True)\n', '')]),
    ("cada pasada deja de empezar sin bajada apuntada", HU,
     [('    st.session_state.pop("_bajada_pedida", None)\n    flash.mostrar()\n', '    flash.mostrar()\n')]),
    ("⚠️ `_bajar_a` deja de apuntar su bajada (la subida la pisa)", PU,
     [('    st.session_state["_bajada_pedida"] = True\n', '')]),
    ("la subida no espera a que acabe la pasada", PU,
     [('''            "if(s==='running'){if(++n<40)setTimeout(ir,100);return;}"\n''', '')]),
    ("⚠️ la subida por un aviso ya no mira si se ve (sube SIEMPRE)", PU,
     [('            "var t=m?m.getBoundingClientRect().top:0;if(f.getBoundingClientRect().top>=t-1)return;}"\n',
       '            "}"\n')]),
    ("la subida ya no mueve la página", PU,
     [('''            "if(m){m.scrollTo({top:0,behavior:SOLO?'smooth':'auto'});}"\n''',
       '''            "if(m){}"\n''')]),
    # ── el aviso ──
    ("⚠️ la marca del aviso vuelve a «_flash_nuevo» (contaba como otra vista y subía SIEMPRE)", FL,
     [('NUEVO = "_flash_recien"', 'NUEVO = "_flash_nuevo"')]),
    ("el aviso sale de su bloque `cpx_flash` (la subida no lo encuentra)", FL,
     [('        with st.container(key=BLOQUE):\n            for tipo, texto in cola:\n'
       '                getattr(st, tipo, st.info)(texto)\n',
       '        for tipo, texto in cola:\n            getattr(st, tipo, st.info)(texto)\n')]),
    ("la repetición de v560 cuenta como aviso nuevo (sube en cada pasada)", FL,
     [('    st.session_state[NUEVO] = bool(cola)\n', '    st.session_state[NUEVO] = True\n')]),
    ("⚠️ «Issue invoice» vuelve a no decir nada", IU,
     [('            flash.exito(t("Invoice No. {n} issued.",\n'
       '                          n=(I.get_factura(res) or {}).get("Number", "")))\n', '')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           MP, [('# signo de puntuación ASCII, así que escapar de más no estropea nada.\n',
                 '# signo de puntuación ASCII, así que escapar de más no estropea nada. (control)\n')])


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
