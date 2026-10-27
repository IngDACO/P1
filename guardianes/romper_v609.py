# -*- coding: utf-8 -*-
"""Bateria de roturas de v609 (el motor en el catálogo y la migración a propósito). ⚠️ Verde de BASE primero (v459)
y NO en paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de
cambios (v526).

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
G = "verif_v609"
STG = "core/stages.py"
SPR = "core/stage_progress.py"
AUD = "core/auditoria.py"
TOPE_S = 600


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ⚠️ `stages.py` va en CRLF: sus anclas, sin el salto de línea.
    ("el bedplate vuelve al 17 (la etapa suma 105)", STG,
     [('        ("Install motor bedplate", 12, False),       # v609: 17 → 12 (5 al motor)',
       '        ("Install motor bedplate", 17, False),       # v609: 17 → 12 (5 al motor)')]),
    ("se pierde «Install motor (machine)»", STG,
     [('        ("Install motor (machine)", 5, False),       # v609: nueva (decisión del usuario)', '')]),
    ("⚠️ se cambian los pesos SIN subir la versión", STG,
     [('VERSION = "2026-10-27"          # juego de pesos; ver el aviso de arriba',
       'VERSION = "2026-09-22"          # juego de pesos; ver el aviso de arriba')]),
    ("la etapa sin renombrar", STG,
     [('    (PISTA_INSTALL, 6, "Shaft Climb, Bedplate & Motor", 13),      # v609: era «… & Bedplates»',
       '    (PISTA_INSTALL, 6, "Shaft Climb & Bedplates", 13),      # v609: era «… & Bedplates»')]),
    ("⚠️ MIGRABLES no dice qué etapa cambia de pesos (la obra no se recalcula)", STG,
     [('        "etapas": [(PISTA_INSTALL, 6)],', '        "etapas": [],')]),
    ("⚠️ se migra con un crédito que el juego de hoy no tiene", SPR,
     [('    if _huerfanos:\n', '    if False:\n')]),
    ("la etapa no se renombra en el cronograma de la obra", SPR,
     [('                    and str(r.get("Name", "")) == viejo):\n', '                    and False):\n')]),
    ("⚠️ el plan de la obra no pasa a la versión de hoy (sigue en solo lectura)", SPR,
     [('    _nuevo_plan = _json.dumps(dict(_pl, version=S.VERSION), ensure_ascii=False)\n',
       '    _nuevo_plan = _json.dumps(dict(_pl), ensure_ascii=False)\n')]),
    ("⚠️ en una obra combinada se toca la etapa 6 de la lista, no la suya", SPR,
     [('        o = _orden.get(k)\n        if o is None or o not in _det:\n',
       '        o = k[1]\n        if o is None or o not in _det:\n')]),
    ("una obra ya al día se vuelve a «migrar»", SPR,
     [('    if _v == S.VERSION:\n        return True, t("Already on the current catalogue.")\n', '')]),
    ("⚠️ el plan de la obra vuelve a cambiar SIN rastro en la auditoría", AUD,
     [('    "StagePlanJSON",\n', '')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           SPR, [('def migrar_catalogo(pid, grupo, prj, quien="") -> tuple:\n',
                  'def migrar_catalogo(pid, grupo, prj, quien="") -> tuple:   # (control)\n')])


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
                             "" if _g == G else "  [%s]" % _g), flush=True)

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
