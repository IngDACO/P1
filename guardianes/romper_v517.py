# -*- coding: utf-8 -*-
"""Bateria de roturas de v517. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita. Y el CONTROL es un cambio de verdad: uno que
ponga el mismo texto a los dos lados no prueba nada y parece cobertura (v514).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v517"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    # ── (a) el invariante: nada apunta a una actividad que no existe ──────────
    ("un sinonimo apunta a una actividad FANTASMA (no propondria nunca, sin error)",
     "core/vocabulario.py", '"okr": ["OKR box (top of cabin)"],',
     '"okr": ["OKR box on top of the cabin"],'),

    ("una tarea se cuelga de una actividad que no existe",
     "core/vocabulario.py", "    'Install motor bedplate': [",
     "    'Install the motor bedplate': ["),

    ("una alternativa de lo ambiguo apunta a algo inexistente",
     "core/vocabulario.py", '"alternativas": ["Install ladder", "Stop button box"],',
     '"alternativas": ["Install pit ladder", "Stop button box"],'),

    # ── (b) la barandilla ─────────────────────────────────────────────────────
    ("se cae el filtro por PLAN: una instalacion recibiria propuestas de desmontaje",
     "core/vocabulario.py",
     "            if en_plan is not None and a not in en_plan:",
     "            if False:"),

    ("el plan se lee en la clave equivocada y el filtro queda VACIO (no filtra nada)",
     "core/vocabulario.py",
     'en_plan = {str(a.get("nombre") if isinstance(a, dict) else a)\n'
     '                   for e in plan for a in (e.get("actividades") or [])}',
     'en_plan = {str(e.get("nombre")) for e in plan\n'
     '                   for a in (e.get("actividades") or [])}'),

    ("lo que queda fuera del plan se TIRA en silencio en vez de decirse",
     "core/vocabulario.py", "                fuera.append(fila)", "                pass"),

    # ── (c) la raiz ───────────────────────────────────────────────────────────
    ("la raiz deja de unir las formas del verbo (los partes van en prosa)",
     "core/vocabulario.py", "    for suf in (\"ing\", \"ed\", \"es\", \"s\"):",
     "    for suf in ():"),

    ("vuelve la «e» muda sin quitar: «tuned» y «tune» dejan de casar",
     "core/vocabulario.py",
     '    if len(p) > 3 and p.endswith("e"):\n        p = p[:-1]',
     '    if False:\n        p = p[:-1]'),

    ("la consonante doblada se recorta SIEMPRE: «install» pasa a «instal»",
     "core/vocabulario.py",
     "    if cortado and len(p) > 3 and p[-1] == p[-2] and p[-1] not in \"aeiou\":",
     "    if len(p) > 3 and p[-1] == p[-2] and p[-1] not in \"aeiou\":"),

    ("las palabras de relleno dejan de quitarse: el articulo rompe la frase",
     "core/vocabulario.py", "    _p = [_raiz(p) for p in s.split() if p not in RELLENO]",
     "    _p = [_raiz(p) for p in s.split()]"),

    # ── (d) lo ambiguo ────────────────────────────────────────────────────────
    ("lo ambiguo se RESUELVE a dedo en vez de marcarse",
     "core/vocabulario.py",
     '    "under the cabin work": {\n'
     '        "alternativas": ["Install platform (cradle)", "Traveller/flat/flex cables (under cabin)"],',
     '    "under the cabin work": {\n'
     '        "alternativas": ["Install platform (cradle)"],'),

    ("lo ambiguo se queda sin su REGLA (nadie sabria como decidir)",
     "core/vocabulario.py",
     '        "regla": "Mechanical if the car rails are not up yet; electrical once the shaft "\n'
     '                 "climb has progressed.",',
     '        "regla": "",'),

    # ── (e) lo que no es avance ───────────────────────────────────────────────
    # ⚠️ ESCAPADA la primera vez: cambiaba UNA de las dos claves («induction») y la
    # otra («inductions», el plural) seguia reconociendo el concepto, asi que la rotura
    # no rompia nada. Se quita el reconocimiento ENTERO, que es el fallo de verdad.
    ("la induccion deja de reconocerse (un dia de solo induccion se leeria como ilegible)",
     "core/vocabulario.py",
     '    "induction": "Site induction — happens once, does not carry progress.",\n'
     '    "inductions": "Site induction — happens once, does not carry progress.",\n',
     ""),

    ("un texto ilegible se disfraza de «no avance»",
     "core/vocabulario.py",
     '    nop = [{"termino": k, "motivo": v} for k, v in NO_AVANCE.items()\n'
     '           if (" " + normaliza(k).strip() + " ") in t]',
     '    nop = [{"termino": k, "motivo": v} for k, v in NO_AVANCE.items()]'),

    # ── (f) lo que no tiene actividad ─────────────────────────────────────────
    # ⚠️ Esta ancla murio a la hora de nacer: el texto estaba en español, `verif_v448` lo
    # cazo (es descripcion de trabajo, o sea pantalla) y al traducirlo el ancla se quedo
    # apuntando a lo viejo. La bateria no avisa de eso — solo la salta. Lo vio
    # `check_anclas_roturas`, por segunda vez en dos versiones y sobre mi propia bateria.
    ("un termino sin actividad se cuelga de la mas parecida (inventaria trabajo)",
     "core/vocabulario.py",
     '    "chaser job": "Cutting/expanding a door opening that came in too small",',
     '    "chaser job_": "Cutting/expanding a door opening that came in too small",'),

    # ── (g) el orden de los terminos ──────────────────────────────────────────
    ("el termino CORTO gana al largo («doors» tapa a «landing doors»)",
     "core/vocabulario.py",
     "sorted(_terminos().items(), key=lambda kv: -len(kv[0]))",
     "sorted(_terminos().items(), key=lambda kv: len(kv[0]))"),

    # ── (h) modulo hoja ───────────────────────────────────────────────────────
    ("el modulo pasa a importar Streamlit (deja de ser hoja y de ser testeable)",
     "core/vocabulario.py", "import re\nimport unicodedata",
     "import re\nimport unicodedata\nimport streamlit"),

    ("el vocabulario se congela en una constante (segunda definicion, v361)",
     "core/vocabulario.py", "    from core import stages as S\n    out = {}",
     "    S = type('x', (), {'ACTIVIDADES': {}})\n    out = {}"),
]

# ⚠️ El CONTROL tiene que ser un cambio REAL que NO pueda poner nada rojo.
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/vocabulario.py", "SINONIMOS = {",
           "# comentario inocuo del control\nSINONIMOS = {")


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
for desc, rel, viejo, nuevo in ROTURAS:
    _ok, bak, p, n = aplica(rel, viejo, nuevo)
    if _ok is None:
        print("  ??      ancla %s -> %s" % ("ausente" if n == 0 else "x%d" % n, desc))
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
sys.exit(0 if cazadas == total else 1)
