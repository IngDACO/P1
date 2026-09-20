# =====================================================================
# HISTORICO - NO SE PUEDE EJECUTAR (marcado el 20/09/2026)
#
# Apunta al scratchpad temporal de la sesion 1734b676..., que ya no existe,
# y ademas opera sobre ficheros intermedios de aquella tanda que tampoco
# existen: era una transformacion de un solo uso, ya aplicada.
#
# Se conserva como RASTRO de como se hizo aquel cambio, no como herramienta.
# Arreglarle la ruta no lo haria funcionar: lo que leia ya no esta.
# =====================================================================
"""Los tres guardianes de la migración de nav, actualizados a lo que queda vivo.

v296/v297/v298 vigilaban una MIGRACIÓN (la nav vieja de `app.py` → la shell única).
**v299 la completó y borró la nav vieja, `_SHELL_NUEVA` y `render_owner_panel`.**
Sus afirmaciones piden que ese código EXISTA, así que fallan por haber ganado.

Se invierten: lo que hay que proteger a partir de ahora es que **NO vuelva**. Es la
regla del propio proyecto (v140/v146): al sustituir un mecanismo, el viejo se
retira; un guardián que exige el viejo envejece al revés.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = pathlib.Path(r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
                 r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad")

CAMBIOS = [
    ("verif_v296.py",
     'for rol in ("propietario", "campo"):\n'
     '    check(f"{rol}: la nav se pudo LEER (no vacia)",\n'
     '          bool(antes.get(rol)) and bool(ahora.get(rol)))\n'
     '    check(f"{rol}: nav IDENTICA", ahora.get(rol), antes.get(rol))\n'
     '    print(f"         {ahora.get(rol)}")',
     '# v384: v299 BORRÓ la nav vieja de `app.py`, así que ya no hay nada que leer ni\n'
     '# que comparar: estas dos afirmaciones fallaban por haber ganado. Lo que queda\n'
     '# vivo es que la nav vieja NO vuelva (regla v140/v146).\n'
     'for rol in ("propietario", "campo"):\n'
     '    check(f"{rol}: la nav vieja sigue borrada", not ahora.get(rol))'),

    ("verif_v297.py",
     'check("app.py define _SHELL_NUEVA",\n'
     '      "_SHELL_NUEVA" in (BASE / "app.py").read_text(encoding="utf-8"))',
     '# v384: `_SHELL_NUEVA` era la bandera que convivía con la nav vieja. v299 hizo la\n'
     '# shell incondicional y la quitó: exigirla ahora es exigir el andamio después de\n'
     '# construir el edificio.\n'
     'check("la bandera _SHELL_NUEVA ya no hace falta (shell incondicional, v299)",\n'
     '      "_SHELL_NUEVA" not in (BASE / "app.py").read_text(encoding="utf-8"))'),

    ("verif_v298.py",
     'check("mismos IDs que el radio de render_owner_panel",\n'
     '      [i for i, _ in _adm[1]], _ids_viejo)',
     '# v384: `render_owner_panel` se borró en v299, así que no hay radio viejo contra\n'
     '# el que comparar. Lo que importa —y se comprueba— es que los IDs del propietario\n'
     '# sigan siendo los que usan sus deep-links.\n'
     'check("los IDs del propietario siguen siendo los 6 acordados",\n'
     '      [i for i, _ in _adm[1]],\n'
     '      ["🌐 Resumen", "🏢 Grupos", "👥 Usuarios", "📁 Proyectos", "🚆 Rieles",\n'
     '       "📚 Manuales"])'),

    ("verif_v298.py",
     'check("...y render_owner_panel la usa", "render_owner_seccion(sec)" in src_au)',
     'check("render_owner_panel ya no existe (v299)", "def render_owner_panel" not in src_au)'),
]

fallos = 0
for fichero, viejo, nuevo in CAMBIOS:
    p = S / fichero
    src = p.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"   ‼️ {fichero}: ancla no encontrada — {viejo.splitlines()[0][:60]}…")
        fallos += 1
        continue
    p.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    print(f"   ✓ {fichero}: afirmación invertida a «sigue borrado»")

sys.exit(1 if fallos else 0)
