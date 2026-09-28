# -*- coding: utf-8 -*-
"""Bateria de roturas de v520. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v520"
IMP = "../guardianes/sueltos/importar_biblioteca.py"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    # ── (a) las catorce de siempre ───────────────────────────────────────────
    ("se RENOMBRA una sección vieja: sus fichas quedan fuera de todo filtro",
     "core/library.py", '    "Car door",\n', '    "Car doors",\n'),

    ("se cae una de las nuevas (la plomada no se podría archivar)",
     "core/library.py", '    "Setting out",\n', ""),

    ("una sección repetida (el desplegable la ofrece dos veces)",
     "core/library.py", '    "Pit",\n', '    "Pit",\n    "Pit",\n'),

    # ── (b) el alta ──────────────────────────────────────────────────────────
    ("el alta deja de validar la sección (entra cualquier texto)",
     "core/library.py", "    if str(seccion) not in SECCIONES:",
     "    if False and str(seccion) not in SECCIONES:"),

    # ── (c) las pantallas ────────────────────────────────────────────────────
    ("el filtro lleva una lista copiada a mano (las nuevas no se pueden elegir)",
     "core/library_ui.py", '[""] + list(LIB.SECCIONES)', '[""] + ["Car", "Pit"]'),

    # ── (d) la carga en lote ─────────────────────────────────────────────────
    ("la carga no comprueba la cabecera real (fila posicional, v363)",
     IMP, "    if cab[:len(LIB.HEADERS)] != LIB.HEADERS:",
     "    if False:"),

    ("la carga no valida la sección (se salta la regla del alta)",
     IMP, "        if sec not in LIB.SECCIONES:", "        if False:"),

    ("la carga no mira lo que ya está en la hoja (duplica al volver a correr)",
     IMP, '    pend = [p for p in plan if p["filename"] not in ya]',
     "    pend = list(plan)"),

    ("la carga olvida lo ya subido a Drive (resube si se cortó)",
     IMP, '        if p["clave"] in estado:\n            continue',
     '        if False:\n            continue'),

    ("la carga reutiliza un ID referenciado en otra hoja (v427)",
     IMP, '        while "LIB-%04d" % n in usados:', "        while False:"),

    ("la carga escribe fila a fila (750 llamadas contra 60/min)",
     IMP, '        ws.append_rows(tanda, value_input_option="RAW")',
     '        [ws.append_row(f, value_input_option="RAW") for f in tanda]'),

    ("la marca nueva no entra al catálogo (el filtro no la ofrece)",
     IMP, '            ok, msg = LIB.add_modelo(marca, "")', '            ok, msg = True, "-"'),
]

# ⚠️ Ancla LARGA a proposito: `check_anclas_roturas` solo mira cadenas de 10 o mas, y
# «TIPOS = [» (9) la dejaba como muerta — el mismo falso positivo que arrastra v472.
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/library.py", 'TIPOS = ["photo", "manual", "datasheet", "diagram", "other"]',
           '# comentario inocuo del control\n'
           'TIPOS = ["photo", "manual", "datasheet", "diagram", "other"]')


def aplica(rel, viejo, nuevo):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
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
sys.exit(0 if cazadas == total and not saltadas and control_ok else 1)
