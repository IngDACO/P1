# -*- coding: utf-8 -*-
"""Bateria de roturas de v519. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita. Y ninguna renombra con guion bajo: la
normalizacion lo convierte en espacio y la rotura no rompe nada (la leccion de v518).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v519"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    # ── (a) lo que hace que las informativas NO muevan el avance ──────────────
    ("las informativas se meten DENTRO de `actividades`: `avance_de` las cuenta",
     "core/stage_progress.py",
     '        out.append({**e, "orden": i, "actividades": _acts, "informativas": _info,\n'
     '                    "pct": avance_de(_acts)})',
     '        out.append({**e, "orden": i, "actividades": _acts + [\n'
     '            {**x, "peso_en_etapa": 10.0} for x in _info], "informativas": _info,\n'
     '                    "pct": avance_de(_acts + [{**x, "peso_en_etapa": 10.0}\n'
     '                                              for x in _info])})'),

    ("las informativas desaparecen de la pantalla (entran, decidio el usuario)",
     "core/stage_progress.py",
     '        _info = [{"nombre": n, "pct": (mapa or {}).get((i, n), 0.0)}\n'
     '                 for n in S.informativas(e.get("pista"), e.get("numero"))]',
     '        _info = []'),

    # ── (b) acreditar ─────────────────────────────────────────────────────────
    ("marcar una informativa TOCA su etapa (reescribe el avance con el mismo numero)",
     "core/stage_progress.py",
     "        if (_et, _ac) in _validas:\n            _tocadas.add(_et)",
     "        _tocadas.add(_et)"),

    ("`acreditar` rechaza las informativas (no se podrian marcar)",
     "core/stage_progress.py",
     "              not in (_validas | _info)]",
     "              not in _validas]"),

    ("`acreditar` acepta una informativa en CUALQUIER etapa (se colgaria de otra)",
     "core/stage_progress.py",
     "    _info = {(i, n) for i, e in enumerate(_plan, start=1)\n"
     "             for n in S.informativas(e.get(\"pista\"), e.get(\"numero\"))}",
     "    _info = {(i, n) for i, e in enumerate(_plan, start=1)\n"
     "             for _v in S.INFORMATIVAS.values() for n in _v}"),

    # ── (c) el catalogo ───────────────────────────────────────────────────────
    ("una informativa se llama como una actividad CON peso (marcarla acreditaria la otra)",
     "core/stages.py",
     '    (PISTA_INSTALL, 14): ["Program controller parameters"],',
     '    (PISTA_INSTALL, 14): ["Program controller parameters", "Load test"],'),

    ("`validar` deja de cazar el choque de nombres",
     "core/stages.py",
     "    if _choque:\n        problemas.append",
     "    if False:\n        problemas.append"),

    ("se cae una de las cuatro informativas que decidio el usuario",
     "core/stages.py",
     '    (PISTA_RIPOUT, 2): ["Lighten cabin if too heavy for intended tirak ratio"],\n',
     ""),

    # ── (d) el 50/50 ──────────────────────────────────────────────────────────
    ("el reparto vuelve al 14 heredado (se pierde la decision del usuario)",
     "core/stages.py", "PCT_RIPOUT_DEFECTO = 50.0", "PCT_RIPOUT_DEFECTO = 14.0"),

    ("`plan_nuevo` deja de SELLAR el reparto: las obras viejas cambiarian de avance",
     "core/projects.py",
     '        "pct_ripout": (_S.PCT_RIPOUT_DEFECTO if pct_ripout is None else _num(pct_ripout)),',
     '        "pct_ripout": None,'),

    # ── (e) la huella de los pesos ────────────────────────────────────────────
    ("se cambia UN peso sin subir VERSION (las obras se medirian contra otro juego)",
     "core/stages.py",
     '        ("Tune doors", ',
     '        ("Tune doors", 1 + '),

    # ── (f) la pantalla ───────────────────────────────────────────────────────
    ("se cae el aviso de que las informativas no cuentan",
     "core/stage_progress_ui.py",
     '                st.caption(t(":material/info: For the record only — ticking these does "\n'
     '                             "not change the progress."))',
     "                pass"),

    ("las informativas no entran en lo que se guarda (marcarlas no haria nada)",
     "core/stage_progress_ui.py",
     "                            for a in list(e[\"actividades\"]) + list(_info)",
     "                            for a in e[\"actividades\"]"),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/stages.py", "INFORMATIVAS = {",
           "# comentario inocuo del control\nINFORMATIVAS = {")


def aplica(rel, viejo, nuevo):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    if bak.count(viejo) != 1:
        return None, bak, p, bak.count(viejo)
    io.open(p, "w", encoding="utf-8", newline="").write(bak.replace(viejo, nuevo, 1))
    return True, bak, p, 1


print("0. Verde de base")
if not corre():
    print("   ⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
# ⚠️ Una rotura que NO se puede aplicar ya no desaparece del recuento: pone la
# bateria en ROJO. Antes se contaba solo lo aplicado, asi que un ancla muerta o
# repetida salia como «??» y el total anunciaba «27 de 27» sin haberla probado — paso
# en v517 con un ancla que aparecia DOS veces, y `check_anclas_roturas` no la veia
# porque su regla es «aparece al menos una vez». Lo dije en v516 («una bateria no
# avisa de sus anclas muertas, solo las salta») y lo deje asi: ahora avisa.
saltadas = []
for desc, rel, viejo, nuevo in ROTURAS:
    _ok, bak, p, n = aplica(rel, viejo, nuevo)
    if _ok is None:
        print("  ??      ancla %s -> %s" % ("ausente" if n == 0 else "x%d" % n, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

print("")
print("2. Control (debe seguir VERDE)")
_d, _r, _v, _n = CONTROL
_ok, bak, p, n = aplica(_r, _v, _n)
if _ok is None:
    print("  ??      ancla del control %s" % ("ausente" if n == 0 else "x%d" % n))
else:
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if verde else "MAL    ", _d))

print("")
print("=== %d de %d roturas cazadas ===" % (cazadas, total))
if saltadas:
    print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
          % len(saltadas))
sys.exit(0 if cazadas == total and not saltadas else 1)
