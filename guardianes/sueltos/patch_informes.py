# -*- coding: utf-8 -*-
"""Los tres guardianes de informes dejan de depender de que la demo tenga un survey.

Si la demo tiene un proyecto con survey, se usa ESE (mejor: datos reales). Si no, se
cae al caso construido de `fixture_survey`, que se auto-comprueba antes de servir.
Asi la afirmacion —que los dos informes se GENERAN y no llevan español— se comprueba
siempre, que es lo que dejo de pasar cuando v456 vacio la demo.
"""
import ast
import io

FALLBACK = '''
# ⚠️ v474 · Si la demo no tiene ningún proyecto con survey (v456 la vació), se cae a un
# caso CONSTRUIDO en vez de salir SIN DATOS: la afirmación de este guardián llevaba
# versiones sin comprobarse. Se prefieren los datos REALES cuando los hay.
if _prj is None:
    import fixture_survey as _FIX
    if not _FIX.valido():
        print("‼️ el fixture no lo digiere el cálculo: no se puede afirmar nada")
        sys.exit(1)
    _prj = _FIX.proyecto()
    print("   (demo sin survey: se usa el caso construido `fixture_survey`)")
'''

CASOS = [
    ("check_report_smoke.py",
     'if _prj is None:\n'
     '    print("⚠️ no hay proyecto con survey: el chequeo NO puede afirmar nada")\n'
     '    # ⚠️ Código 2 = SIN DATOS, no 1: no hay nada roto, es que no hay qué comprobar.\n'
     '    # Salir en rojo aquí acumularía un rojo permanente en cuanto la demo se vacíe, y\n'
     '    # una suite con rojos crónicos se acaba ignorando entera (v385).\n'
     '    sys.exit(2)\n',
     FALLBACK.lstrip("\n")),
    ("verif_v448.py",
     '# ⚠️ v456: la demo se vació, así que este chequeo ya no tiene DATOS que mirar.\n'
     '# Sale con código 2 (SIN DATOS): ni verde —sería un OK que no comprobó nada,\n'
     '# trampa nº1— ni rojo, porque no hay nada roto. El runner lo lista aparte y\n'
     '# avisa de que esa afirmación dejó de comprobarse.\n'
     'if _prj is None:\n'
     '    print("⚠️ no hay proyecto con survey: el informe ADMIN no se puede generar")\n'
     '    sys.exit(2)\n',
     FALLBACK.lstrip("\n")),
    ("verif_v437.py",
     '    if _prj is None:\n'
     '        # ⚠️ v456: sin datos no se puede generar el informe. Ver la nota de v448:\n'
     '        # código 2 = SIN DATOS, que el runner cuenta aparte.\n'
     '        print("⚠️ no hay proyecto con survey: el informe de cliente no se puede generar")\n'
     '        sys.exit(2)\n'
     '    else:\n',
     '    # ⚠️ v474 · caso CONSTRUIDO si la demo no tiene survey (ver `fixture_survey`).\n'
     '    if _prj is None:\n'
     '        import fixture_survey as _FIX\n'
     '        if not _FIX.valido():\n'
     '            print("‼️ el fixture no lo digiere el cálculo")\n'
     '            sys.exit(1)\n'
     '        _prj = _FIX.proyecto()\n'
     '        print("   (demo sin survey: se usa el caso construido)")\n'
     '    if True:\n'),
]

for fichero, viejo, nuevo in CASOS:
    s = io.open(fichero, encoding="utf-8").read()
    if s.count(viejo) != 1:
        raise SystemExit("%s: ancla %d veces" % (fichero, s.count(viejo)))
    s = s.replace(viejo, nuevo)
    ast.parse(s)
    io.open(fichero, "w", encoding="utf-8", newline="").write(s)
    print("   %s -> con caso construido" % fichero)
