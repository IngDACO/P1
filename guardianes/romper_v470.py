# -*- coding: utf-8 -*-
"""Bateria de roturas de v470. ⚠️ Verde de BASE primero: sin ese paso una tanda
entera sale «cazada» sin probar nada (v459). Y NO se lanza en paralelo con la suite,
que modifica los mismos ficheros (v455)."""
import io
import os
import subprocess
import sys

SCRW = os.environ["SCRW"]
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v470"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    ("el tipo se cae de P.TIPOS",
     "core/projects.py", 'TIPOS = [TIPO_INSTALACION, TIPO_RIPOUT_INST,',
     'TIPOS = [TIPO_INSTALACION,'),
    ("se queda sin icono (se veria como una localizacion interna)",
     "core/projects.py", '              TIPO_RIPOUT_INST: ":material/autorenew:",\n', ""),
    ("quotes vuelve a comparar el LITERAL (el fallo de v454)",
     "core/quotes.py", "if P.genera_cronograma(tipo) and _num(ns) > 0:",
     'if str(tipo) == "Installation" and _num(ns) > 0:'),
    ("el alta deja de pasar `ripout` al cronograma",
     "core/projects_ui.py", "sched = build_schedule(int(ns), f_ini, {},\n"
                            "                                       ripout=P.con_ripout(_tipo))",
     "sched = build_schedule(int(ns), f_ini, {})"),
    ("la cotizacion deja de pasarlo",
     "core/quotes.py", "sch = S.build_schedule(int(_num(ns)), ini, {}, ripout=P.con_ripout(tipo))",
     "sch = S.build_schedule(int(_num(ns)), ini, {})"),
    ("genera_cronograma se abre al «Ripout» a secas",
     "core/projects.py", 'return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST)',
     'return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST, "Ripout")'),
    ("el desmontaje deja de ser el PRIMERO",
     "core/schedule.py", "([FASE_RIPOUT] + PHASES if ripout else PHASES)",
     "(PHASES + [FASE_RIPOUT] if ripout else PHASES)"),
    ("su duracion deja de escalar con el NS",
     "core/schedule.py", 'FASE_RIPOUT = ("Ripout of existing lift", 3, 0.5, 15, None)',
     'FASE_RIPOUT = ("Ripout of existing lift", 3, 0.0, 15, None)'),
    ("`custom_rows` vuelve a insertar la fase (la duplicaria en cada guardado)",
     "core/schedule.py", 'base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]',
     'base = ([(FASE_RIPOUT[0], 3.0, 15.0)] if ripout else []) + '
     '[(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]'),
    ("el default de quotes se desincroniza de la constante",
     "core/quotes.py", 'tipo="Installation"', 'tipo="Instalacion"'),
    ("un texto vuelve a decir «Only Installation» (pasaria a mentir)",
     "core/projects_ui.py",
     '«Installation» and «Ripout + Installation» generate the standard job',
     'Only «Installation» generates the standard job'),
    ("se cae el aviso de que el plan no tiene el desmontaje",
     "core/projects_ui.py", 'has no strip-out activity', 'has every activity'),
    ("el marcador {act} deja de casar (se pintaria literal, v453)",
     "core/projects_ui.py", 'so add it below: «{act}».", act=_FR[0]))',
     'so add it below: «{actividad}».", act=_FR[0]))'),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/projects.py", "TIPO_INSTALACION = \"Installation\"",
           "# comentario inocuo del control\nTIPO_INSTALACION = \"Installation\"")


def prueba(desc, fich, viejo, nuevo, espera_rojo=True):
    p = os.path.join(RAIZ, fich.replace("/", os.sep))
    orig = io.open(p, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        return "  ??      ancla ausente en %s -> %s" % (fich, desc)
    try:
        io.open(p, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(orig)
    if espera_rojo:
        return "  %s %s" % ("CAZADA " if not verde else "ESCAPADA", desc)
    return "  %s %s" % ("ok     " if verde else "FALSO+ ", desc)


print("0. Verde de base")
if not corre():
    print("   ROJO de base: la tanda no valdria nada. ABORTADO.")
    sys.exit(2)
print("   verde\n")

print("1. Roturas (cada una debe ponerse ROJA)")
res = [prueba(*r) for r in ROTURAS]
for r in res:
    print(r)

print("\n2. Control (debe seguir VERDE)")
print(prueba(*CONTROL, espera_rojo=False))

cz = sum(1 for r in res if "CAZADA" in r)
print("\n=== %d de %d roturas cazadas ===" % (cz, len(ROTURAS)))
sys.exit(0 if cz == len(ROTURAS) else 1)
