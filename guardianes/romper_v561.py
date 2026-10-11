# -*- coding: utf-8 -*-
"""Bateria de roturas de v561. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto verificando v560 en producción.
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
G = "verif_v561"
SC = "core/schedule.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
AD = "core/admin_digest.py"
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
    ("⚠️ el subtítulo vuelve a quedar pegado a «TODAY» (y=35)", SC,
     [("f'<text x=\"18\" y=\"31\" font-size=\"8.5\" fill=\"#5b6472\">'",
       "f'<text x=\"18\" y=\"35\" font-size=\"8.5\" fill=\"#5b6472\">'")]),
    ("el título se sale por arriba", SC,
     [("f'<text x=\"18\" y=\"19\" font-size=\"13\" fill=\"#1a3a5c\" font-weight=\"bold\">'",
       "f'<text x=\"18\" y=\"8\" font-size=\"13\" fill=\"#1a3a5c\" font-weight=\"bold\">'")]),
    ("⚠️ la fila del Home pierde su clave (la regla no la encuentra)", HU,
     [('    with st.container(key="cpx_home_fila"):\n', '    with st.container(key="cpx_home_x"):\n')]),
    ("⚠️ el umbral vuelve a uno que deja 3 columnas a 1280 con menú", HU,
     [('"@container (max-width:1140px){"', '"@container (max-width:900px){"')]),
    ("⚠️ KPI + mapa ya no van a todo el ancho", HU,
     [(':nth-child(1)"\n            "{flex:1 1 100% !important;}"',
       ':nth-child(1)"\n            "{flex:1 1 40% !important;}"')]),
    ("Projects | agenda ya no van a medias", HU,
     [('"{flex:1 1 calc(50% - 1rem) !important;}}"', '"{flex:1 1 30% !important;}}"')]),
    ("la regla alcanza también las tarjetas KPI de dentro", HU,
     [('            ".st-key-cpx_home_fila [data-testid=\'stHorizontalBlock\']"\n'
       '            ":not([data-testid=\'stColumn\'] *){column-gap:2rem !important;"',
       '            ".st-key-cpx_home_fila [data-testid=\'stHorizontalBlock\']"\n'
       '            "{column-gap:2rem !important;"')]),
    ("el estilo vuelve a `st.markdown` (ocupa un hueco)", HU,
     [('    st.html("<style>"\n            ".st-key-cpx_home_fila{container-type:inline-size;}"',
       '    st.markdown("<style>"\n            ".st-key-cpx_home_fila{container-type:inline-size;}"')]),
    ("⚠️ los indicadores vuelven a partir palabras («Credenti als»)", PU,
     [("'>[data-testid=\"stColumn\"]{flex:1 1 calc(33.3% - 1rem) !important;}}']",
       "'>[data-testid=\"stColumn\"]{flex:1 1 auto !important;}}']")]),
    ("⚠️ la IA vuelve a leer «end 2026-10-02»", AD,
     [("{t('end')} {_dmy(x['fin'])})", "{t('end')} {x['fin']})")]),
    ("la fecha del near miss vuelve a ISO", AD,
     [("({_dmy(x['fecha'])}: ", "({x['fecha']}: ")]),
    ("⚠️ el campo sin contacto vuelve a salir por login", AD,
     [("+ \", \".join(_nom.get(str(u), str(u)) for u in d[\"campo_sin_contacto\"]))",
       "+ \", \".join(d[\"campo_sin_contacto\"]))")]),
    ("⚠️ las credenciales vuelven a «VENCIDA»", AD,
     [('        return t("expired {n} d ago").replace("{n}", str(-n))\n',
       '        return "VENCIDA"\n')]),
    ("el near miss sin descripción vuelve a «s/d»", AD,
     [("{x['desc'] or t('no description')}", "{x['desc'] or 's/d'}")]),
    ("⚠️ el Home vuelve a «tipo·login (-3d)»", PU,
     [("lambda: \", \".join(f\"{c['tipo']} · {_n} ({admin_digest.plazo_credencial(c['dias'])})\"",
       "lambda: \", \".join(f\"{c['tipo']}·{c['usuario']} ({c['dias']}d)\"")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           AD, [("    identidad; la IA y el texto de respaldo escribían «appretince» donde la ficha dice",
                 "    identidad; la IA y el texto de respaldo escribían «appretince» donde la ficha dice (control)")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
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
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    _base = corre()
    if not _base:
        print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
              % ("COLGADO" if _base is None else "rojo"))
        sys.exit(1)
    print("   verde")

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for desc, rel, cambios in _rot:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

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
