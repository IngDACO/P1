# -*- coding: utf-8 -*-
"""Bateria de roturas de v522. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita: casi todas deshacen un arreglo que salio de los
1070 partes reales, o aflojan una regla hasta el punto en que volveria a fallar alli.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v522"
VOC = "core/vocabulario.py"


# ⚠️ Con TOPE de tiempo. La primera version de la rotura de las etapas dejaba el bucle
# buscando la misma frase para siempre: el guardian se COLGO 18 minutos y la bateria con
# el. Un cuelgue no es una rotura cazada —el guardian no detecto nada, no llego a
# terminar—, asi que se cuenta aparte y pone la bateria en rojo.
TOPE_S = 420


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── (a) rope / roping ────────────────────────────────────────────────────
    ("«roping» vuelve a recortarse: cualquier cuerda acredita belting",
     VOC, '_SIN_RAIZ = frozenset(("roping", "reverses"))', '_SIN_RAIZ = frozenset(("reverses",))'),
    ("«reverses» vuelve a recortarse: «reverse rotation» monta paredes",
     VOC, '_SIN_RAIZ = frozenset(("roping", "reverses"))', '_SIN_RAIZ = frozenset(("roping",))'),

    # ── (b) quitar no es montar ──────────────────────────────────────────────
    ("la oracion de QUITAR deja de convertirse (Remove cable trays → Install cable tray)",
     VOC, '        if "retirada" in ctx:', '        if False and "retirada" in ctx:'),
    ("«rip-out» vuelve a leerse como verbo (el kit se convierte en desmontaje)",
     VOC, r'rip(?:ped|ping)\s*-?\s*out\b"', r'rip(?:ped|ping|s)?\s*-?\s*out\b"'),
    ("«take off» a secas vuelve a ser quitar («so the driver could take off»)",
     VOC, r'(?!(?:and|then|to|at|from|for|so|early|home|work|with)\b)\w+"', r'\w+"'),
    ("sin desmontaje en el plan, se propone igual en vez de preguntar",
     VOC, "        if con_desmontaje:", "        if True:"),
    # ⚠️ Las DOS a la vez: con una sola, la otra seguía dando «Pack up» y el usuario vería
    # lo mismo — la primera versión de esta rotura no imitaba ningún fallo visible.
    ("las vallas quitadas dejan de ser «Pack up» (se pregunta sin necesidad)",
     VOC, '    "Hoardings & protection": ["Pack up"],\n    "Compound/Hoardings": ["Pack up"],', ""),

    # ── (c) pendiente y logistica ────────────────────────────────────────────
    ("lo PENDIENTE vuelve a acreditarse (Issues/Pendings, «still needs…»)",
     VOC, "if en_pendiente or _PENDIENTE.search(t):", "if False:"),
    ("lo que se LLEVA vuelve a montarse («hoardings onto the hilux»)",
     VOC, "if _LOGISTICA.search(t):", "if False:"),
    ("la excepcion de las entregas desaparece (se pierde «Picked up delivery»)",
     VOC, "_log = [a for a in acts if a in LOGISTICAS]", "_log = []"),

    # ── (d) etapas ───────────────────────────────────────────────────────────
    # ⚠️ Con SU PROPIA mascara (se tapa a si misma y termina), no con una mascara vacia
    # en cada vuelta: esa version no imitaba ningun fallo, colgaba el guardian para siempre.
    ("la etapa compite con las actividades (le roba «Prep all landing doors»)",
     VOC, "        palabras = normaliza(term).split()\n        while True:\n"
          "            pos = _casa(toks, palabras, tapado)\n            if pos is None:\n"
          "                break\n            for _j in pos:\n                tapado[_j] = True",
     "        palabras = normaliza(term).split()\n        _t2 = [False] * len(toks)\n"
     "        while True:\n            pos = _casa(toks, palabras, _t2)\n"
     "            if pos is None:\n                break\n            for _j in pos:\n"
     "                _t2[_j] = True"),
    ("la misma etapa se propone dos veces en una nota",
     VOC, "elif (p, n) in _et_idx:", "elif False:"),
    ("se propone una etapa que la obra NO tiene",
     VOC, "if en_plan is None or a[0] in en_plan]", "if True]"),

    # ── (e) luces, aviso, alias ──────────────────────────────────────────────
    ("«lights» a secas vuelve a ser Shaft Wiring en vez de preguntar",
     VOC, '    "lights": {', '    "lights-x": {'),
    ("un «(not finished yet)» deja de avisar sobre la oracion anterior",
     VOC, 'prev["aviso"] = "incompleto"', "pass"),
    ("se pierde el alias car = cabin («car doors» no encuentra «cabin doors»)",
     VOC, '"cwt": "cw", "car": "cabin", "cars": "cabin",', '"cwt": "cw",'),

    # ── (f) ascensores ───────────────────────────────────────────────────────
    ("«L3» pasa a ser un ascensor seguro (y puede ser un NIVEL)",
     VOC, r'r"\blifts?\s*(?:#|no', r'r"\b(?:lifts?|L)\s*(?:#|no'),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           VOC, '_SIN_RAIZ = frozenset(("roping", "reverses"))',
           '# comentario inocuo del control\n_SIN_RAIZ = frozenset(("roping", "reverses"))')


def aplica(rel, viejo, nuevo):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    if bak.count(viejo) != 1:
        return None, bak, p, bak.count(viejo)
    io.open(p, "w", encoding="utf-8", newline="").write(bak.replace(viejo, nuevo, 1))
    return True, bak, p, 1


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
    if verde is None:
        colgadas.append(desc)
        print("  COLGADA  %s" % desc)
        continue
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

print("")
print("2. Control (debe seguir VERDE)")
_d, _r, _v, _n = CONTROL
_ok, bak, p, n = aplica(_r, _v, _n)
control_ok = False
if _ok is None:
    print("  ??      ancla del control %s" % ("ausente" if n == 0 else "x%d" % n))
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
