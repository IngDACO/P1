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
    # ⚠️ v515 · OCHO anclas de esta bateria apuntaban a texto que ya no existe, y la
    # bateria las contaba como «??» mientras anunciaba «5 de 13 cazadas». CINCO llevaban
    # muertas desde v512 (comprobado contra el HEAD anterior): el modelo viejo se cambio
    # y nadie volvio aqui. Una bateria con anclas muertas es peor que no tenerla —
    # parece cobertura y no prueba nada—, y como las `romper_*` NO estan en la suite
    # (modifican el arbol, v455), se pudren en silencio. De ahi sale `check_anclas_roturas`.
    ("el alta deja de armar el plan con el catalogo",
     "core/projects_ui.py", "sched = build_schedule(int(ns), f_ini, {},\n"
                            "                                       custom_rows=_filas_etapas(_tipo, ns, key))",
     "sched = build_schedule(int(ns), f_ini, {})"),
    ("la cotizacion deja de armarlo",
     "core/quotes.py", "sch = S.build_schedule(int(_num(ns)), ini, {}, custom_rows=_filas)",
     "sch = S.build_schedule(int(_num(ns)), ini, {})"),
    ("genera_cronograma se cierra al «Ripout» a secas (la decision de v512)",
     "core/projects.py",
     'return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST, TIPO_RIPOUT)',
     'return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST)'),
    ("el desmontaje deja de ir DELANTE",
     "core/schedule.py", '_tipo = "Ripout + Installation" if ripout else "Installation"',
     '_tipo = "Installation"'),
    ("sus dias dejan de escalar con el NS",
     "core/schedule.py", 'DIAS_POR_PISTA = {"install": (17.0, 2.0), "ripout": (3.0, 0.5)}',
     'DIAS_POR_PISTA = {"install": (17.0, 2.0), "ripout": (3.0, 0.0)}'),
    ("`custom_rows` vuelve a insertar el desmontaje (lo duplicaria en cada guardado)",
     "core/schedule.py", 'base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]',
     'base = ([("Set Up (rip-out)", 3.0, 15.0)] if ripout else []) + '
     '[(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]'),
    ("el default de quotes se desincroniza de la constante",
     "core/quotes.py", 'tipo="Installation"', 'tipo="Instalacion"'),
    ("el help del tipo vuelve a decir que solo la instalacion lleva cronograma",
     "core/projects_ui.py",
     '«Installation», «Ripout» and the combined type generate the job schedule',
     'Only «Installation» generates the standard job'),
    ("se cae el aviso de que el plan no tiene el desmontaje",
     "core/projects_ui.py", 'has no strip-out stages', 'has every stage'),
    ("el marcador {act} deja de casar (se pintaria literal, v453)",
     "core/projects_ui.py", 'so add them below: «{act}».",',
     'so add them below: «{actividad}».",'),
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
