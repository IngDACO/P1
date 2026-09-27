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
    # ⚠️ REESCRITA tras la prueba contra el corpus de frases reales: la busqueda paso de
    # cadenas a PALABRAS (hueco, fronteras de oracion, una sola pasada para los cuatro
    # tipos) y cinco anclas murieron. Cuatro las denuncio `check_anclas_roturas`; la
    # quinta NO la vio — la de la consonante doblada, cuyo texto de REEMPLAZO paso a ser
    # el codigo bueno, asi que «alguna de sus cadenas esta en el fichero» y la daba por
    # viva. Punto ciego real de ese guardian: no distingue un ancla viva de una rotura
    # que se convirtio en la norma. Lo cazo correr la bateria, que es por lo que se corre.

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
     "                (fuera if en_plan is not None and a not in en_plan else dentro).append(fila)",
     "                dentro.append(fila)"),

    ("el plan se lee en la clave equivocada y el filtro queda VACIO (no filtra nada)",
     "core/vocabulario.py",
     'en_plan = {str(a.get("nombre") if isinstance(a, dict) else a)\n'
     '                   for e in plan for a in (e.get("actividades") or [])}',
     'en_plan = {str(e.get("nombre")) for e in plan\n'
     '                   for a in (e.get("actividades") or [])}'),

    ("lo que queda fuera del plan se TIRA en silencio en vez de decirse",
     "core/vocabulario.py",
     "                (fuera if en_plan is not None and a not in en_plan else dentro).append(fila)",
     "                if not (en_plan is not None and a not in en_plan): dentro.append(fila)"),

    # ── (c) la raiz ───────────────────────────────────────────────────────────
    ("la raiz deja de unir las formas del verbo (los partes van en prosa)",
     "core/vocabulario.py", "    for suf in (\"ing\", \"ed\", \"es\", \"s\"):",
     "    for suf in ():"),

    ("vuelve la «e» muda sin quitar: «tuned» y «tune» dejan de casar",
     "core/vocabulario.py",
     '    if len(p) > 3 and p.endswith("e"):\n        p = p[:-1]',
     '    if False:\n        p = p[:-1]'),

    # ⚠️ INVERTIDA respecto a la de antes: la consonante doblada se recorta SIEMPRE, que
    # es lo que hace que install/installed/installing caigan en la misma raiz. La rotura
    # de hoy es quitar el recorte, que devuelve el fallo que el corpus destapo.
    ("la consonante doblada deja de recortarse: «installed» ya no casa con «Install»",
     "core/vocabulario.py",
     '    if len(p) > 3 and p[-1] == p[-2] and p[-1] not in "aeiou":\n        p = p[:-1]',
     '    if False:\n        p = p[:-1]'),

    ("las palabras de relleno dejan de quitarse: el articulo rompe la frase",
     "core/vocabulario.py", "    _p = [_raiz(p) for p in s.split() if p not in RELLENO]",
     "    _p = [_raiz(p) for p in s.split()]"),

    # ── (c2) el hueco y las oraciones ─────────────────────────────────────────
    ("el hueco CRUZA una coma: «cleaned the pit, rails arriving» acredita Clean rails",
     "core/vocabulario.py",
     "                if toks[j] == SEP:          # fin de oración: aquí no sigue el término",
     "                if False:"),

    ("el hueco se ESTIRA: palabras sueltas de media frase se juntan en un termino",
     "core/vocabulario.py", "HUECO = 2\n", "HUECO = 6\n"),

    ("el hueco desaparece: «Cleaned 4 car rails» deja de encontrar Clean rails",
     "core/vocabulario.py", "HUECO = 2\n", "HUECO = 0\n"),

    ("una raya DENTRO de una palabra parte la frase («rip-out», «3-phase»)",
     "core/vocabulario.py",
     '_LIMITE = re.compile(r"[,.;:!?()\\n]|',
     '_LIMITE = re.compile(r"[,.;:!?()\\n-]|'),

    # ── (c3) una sola pasada ──────────────────────────────────────────────────
    ("en empate gana la actividad y no lo marcado: «flex cable» sin zona se cuela a una",
     "core/vocabulario.py",
     'PRIO = {"amb": 0, "noav": 0, "sin": 0, "act": 1}',
     'PRIO = {"amb": 1, "noav": 1, "sin": 1, "act": 0}'),

    ("el nombre sin su parentesis deja de ser termino: «installed belts» no encuentra nada",
     "core/vocabulario.py",
     "            if _base and _base != a[0]:",
     "            if False:"),

    ("lo que el documento manda «por defecto» deja de proponerse (Pit doors sin puntuar)",
     "core/vocabulario.py",
     '            if len(dato["alternativas"]) == 1 and "default" in dato["regla"].lower():',
     "            if False:"),

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

    # ⚠️ v519 · Caducada por DECISION del usuario, no por descuido: «roping» era una
    # contradiccion MARCADA y ahora es sinonimo de belting (su opcion A). La rotura pasa a
    # ser que la decision se pierda. «roping zz» y no «roping_»: el guion bajo se
    # normaliza a espacio y la rotura no rompia nada (la leccion de v518).
    ("«roping» deja de proponer belting: la decision del usuario se pierde",
     "core/vocabulario.py",
     '    "roping": ["Install belts (motor, CW, cabin)"],',
     '    "roping zz": ["Install belts (motor, CW, cabin)"],'),

    # ── (e) lo que no es avance ───────────────────────────────────────────────
    ("la induccion deja de reconocerse (un dia de solo induccion se leeria como ilegible)",
     "core/vocabulario.py",
     '    "induction": "Site induction — happens once, does not carry progress.",\n'
     '    "inductions": "Site induction — happens once, does not carry progress.",\n',
     ""),

    ("un texto ilegible se disfraza de «no avance»",
     "core/vocabulario.py",
     '    return {"candidatos": dentro, "ambiguos": amb, "no_avance": nop,',
     '    return {"candidatos": dentro, "ambiguos": amb, "no_avance": nop or [\n'
     '        {"termino": k, "motivo": v} for k, v in NO_AVANCE.items()],'),

    # ── (f) lo informativo (v519) ─────────────────────────────────────────────
    # ⚠️ Caducadas por DECISION: el «chaser job» ya no esta «sin actividad», entra como
    # INFORMATIVA. Lo que hay que romper ahora es lo que la hace segura: que diga que NO
    # cuenta, y que no salga «fuera del plan» cuando su etapa si es de la obra.
    # ⚠️ Con el «"fuente": tipo,» delante: el ancla sola aparecia DOS veces (tambien en la
    # fila de «por defecto»), la bateria la salto con «??» y anuncio 27 de 27 contando
    # solo las que aplico. `check_anclas_roturas` no lo vio: su regla es «aparece al menos
    # una vez», y aparecia dos.
    ("una informativa se propone como si CONTARA (un chaser job subiria la etapa)",
     "core/vocabulario.py",
     '"fuente": tipo,\n                        "cuenta": a not in _info}',
     '"fuente": tipo,\n                        "cuenta": True}'),

    ("las informativas salen «fuera del plan» aunque su etapa sea de la obra",
     "core/vocabulario.py",
     "        en_plan |= {n for e in plan for n in S.informativas(e.get(\"pista\"), e.get(\"numero\"))}",
     "        pass"),

    # ── (g) el orden de los terminos ──────────────────────────────────────────
    ("el termino CORTO gana al largo (la luz generica tapa a «work lighting»)",
     "core/vocabulario.py",
     "    pats.sort(key=lambda p: (-len(p[0]), -sum(len(w) for w in p[0]), PRIO[p[1]]))",
     "    pats.sort(key=lambda p: (len(p[0]), sum(len(w) for w in p[0]), PRIO[p[1]]))"),

    # ── (g2) vocabulario que el corpus exige ──────────────────────────────────
    # ⚠️ Si alguien «limpia» un termino que solo el corpus usa, el trinquete lo caza.
    # ⚠️ ESCAPADA la primera vez, y por culpa de la ROTURA: renombraba «yemny wheel» a
    # «yemny_wheel», y la normalizacion convierte el guion bajo en espacio — o sea que el
    # termino seguia siendo EXACTAMENTE el mismo. Una rotura que no rompe nada, como el
    # CONTROL que nacio vacio en v514. Ahora se BORRA la linea.
    ("se pierde un termino documentado (la mala escucha «yemny wheel»)",
     "core/vocabulario.py",
     '    "yemny wheel": ["Install governor tension device"],   # «was a mishearing/typo»\n',
     ""),

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
