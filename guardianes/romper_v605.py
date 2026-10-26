# -*- coding: utf-8 -*-
"""Bateria de roturas de v605 (Library: el número de página aparte y las secciones en una fila).
⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455). Con TOPE de tiempo (v522).
Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo medido en producción verificando v604.
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
G = "verif_v605"
LU = "core/library_ui.py"
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
    # ── la página, aparte ──
    ("⚠️ la tabla pierde la columna «Page»", LU,
     [('            **({"Page": _pagina(it, pags)} if _con_pagina else {}),\n', '')]),
    ("«Page» deja de ser la primera columna", LU,
     [('            **({"Page": _pagina(it, pags)} if _con_pagina else {}),\n', ''),
      ('            "Title": str(it.get("Title", "")).strip(),\n',
       '            "Title": str(it.get("Title", "")).strip(),\n'
       '            **({"Page": _pagina(it, pags)} if _con_pagina else {}),\n')]),
    ("⚠️ el título de la tabla vuelve con el número pegado (y cortado)", LU,
     [('            "Title": str(it.get("Title", "")).strip(),\n', '            "Title": _titulo(it, pags),\n')]),
    ("la columna «Page» deja de ser estrecha", LU,
     [('"Page": st.column_config.TextColumn(t("Page"), width=56)', '"Page": st.column_config.TextColumn(t("Page"), width=200)')]),
    ("⚠️ la miniatura pierde su insignia", LU,
     [('                    if _pg:\n', '                    if False:\n')]),
    ("el título de la miniatura vuelve con el número (cortado en el móvil)", LU,
     [('                        _h.escape(str(it.get("Title", "")).strip()),\n',
       '                        _h.escape(_titulo(it, pags)),\n')]),
    ("la insignia vuelve al flujo (sube la foto)", LU,
     [("""[data-testid='stElementContainer']:has(.lib-pag){position:absolute!important;""",
       """[data-testid='stElementContainer']:has(.lib-pag){""")]),
    # ── las secciones, en una fila ──
    ("⚠️ el CSS de las secciones deja de ponerse (vuelven a ocupar ~320 px en el móvil)", LU,
     [('    st.markdown(_CSS_SECCIONES, unsafe_allow_html=True)\n', '')]),
    ("las secciones vuelven a saltar de línea", LU,
     [("""[data-testid='stButtonGroup']>div{flex-wrap:nowrap!important;""",
       """[data-testid='stButtonGroup']>div{flex-wrap:wrap!important;""")]),
    ("la elegida deja de ir la primera (escondida al final de la fila)", LU,
     [("""button[aria-checked='true']{order:-1}}</style>")""", """button[aria-checked='true']{order:0}}</style>")""")]),
    ("la regla deja de mirar el ancho del bloque", LU,
     [(""""@container (max-width:700px){\"\n    ".st-key-lib_secs""", """"@media (max-width:0px){\"\n    ".st-key-lib_secs""")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           LU, [('    """«3/30» si la pieza comparte título con otras (si no, nada)."""\n',
                 '    """«3/30» si la pieza comparte título con otras (si no, nada). (control)"""\n')])


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
