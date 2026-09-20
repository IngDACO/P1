"""Actualiza los guardianes cuya AFIRMACIÓN envejeció por cambios deliberados.

⚠️ No se relajan: se les cambia la afirmación por la que corresponde HOY, con la
razón escrita al lado. Relajar un guardián porque molesta es taparse los ojos;
actualizarlo cuando la funcionalidad cambió a propósito es mantenerlo vivo.

⚠️ Cada reemplazo comprueba que su ancla EXISTE. Un patch que no aplica y no avisa
es lo que dejó inerte el arreglo de v360 (lo contó v361).
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = pathlib.Path(r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
                 r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad")

CAMBIOS = [
    # v306: exigía que `Tipo` fuera la ÚLTIMA columna. v360 y v373 añadieron
    # `GananciaHoraJSON` y `GananciaFija` DESPUÉS — también al final, que es lo que
    # la regla protege de verdad (columna nueva = migración segura).
    ("verif_v306.py",
     'check("Tipo va al FINAL (columna nueva = migracion segura)",\n'
     '      P.PROJECTS_HEADERS[-1], "Tipo")',
     '# v384: la regla es «las columnas NUEVAS van al final», no «Tipo es la última»:\n'
     '# v360 y v373 añadieron GananciaHoraJSON y GananciaFija después, y también al\n'
     '# final. Se comprueba el ORDEN relativo, que es lo que hace segura la migración.\n'
     'check("Tipo va DESPUES de las columnas previas a v306",\n'
     '      P.PROJECTS_HEADERS.index("Tipo") > P.PROJECTS_HEADERS.index("MargenMO"))\n'
     'check("las columnas de ganancia son las ULTIMAS (v360/v373)",\n'
     '      P.PROJECTS_HEADERS[-2:], ["GananciaHoraJSON", "GananciaFija"])'),

    # v317: exigía 3 herramientas. v318 convirtió la composición en la cuarta, a
    # petición del usuario tras verla fija.
    ("verif_v317.py",
     'check("3 herramientas (composición NO es una)", len(_tools.value.elts), 3)\n'
     'check("...y son las acordadas",\n'
     '      [e.elts[0].value for e in _tools.value.elts], ["conc", "cli", "prj"])',
     '# v384: eran 3 y v318 hizo la composición la CUARTA — decisión del usuario tras\n'
     '# verla fija («que sea una herramienta más»). La regla viva es que estén las\n'
     '# acordadas, no cuántas son.\n'
     'check("4 herramientas (v318 sumó la composición)", len(_tools.value.elts), 4)\n'
     'check("...y son las acordadas",\n'
     '      [e.elts[0].value for e in _tools.value.elts], ["conc", "cli", "comp", "prj"])'),

    # v301: exigía 13.5px en la cabecera del tablero. v333 normalizó TODA la app a
    # una escala de 9 pasos y 13.5 no es uno de ellos.
    ("verif_v301.py",
     'check("mas grande que 12px", "13.5px" in _cab)',
     '# v384: era 13.5px y v333 normalizó la app a 9 pasos (11,12,13,14,16,18,21,26,34).\n'
     '# Lo que v301 protegía es que la cabecera fuera MÁS GRANDE que el texto de las\n'
     '# celdas, no ese número concreto.\n'
     'check("mas grande que el texto de celda", "14px" in _cab or "16px" in _cab)'),
]

for fichero, viejo, nuevo in CAMBIOS:
    p = S / fichero
    src = p.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"   ‼️ {fichero}: el ancla NO existe — revisar a mano (no se tocó)")
        continue
    p.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"   ✓ {fichero}: afirmación actualizada")
