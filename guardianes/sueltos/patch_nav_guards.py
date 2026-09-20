# -*- coding: utf-8 -*-
"""Las tres afirmaciones de IGUALDAD EXACTA sobre la nav, actualizadas — no relajadas.

⚠️ Fallaban **por haber ganado algo**: v472 añade la seccion Biblioteca a los tres
roles a proposito. Es la trampa nº16 (un guardian atado a la FORMA caduca cuando la
forma cambia adrede) y la misma correccion que v430 ya le hizo al bloque del CAMPO en
este mismo fichero. El PRINCIPIO no cambia y se afirma entero:
   · no se PIERDE ninguna seccion de las que ese rol ya tenia (contencion), y
   · las que se añadan van DESPUES (prefijo), asi no se le reordena la nav a nadie.
La lista vieja se conserva escrita, que es lo que hace la afirmacion comprobable.
"""
import ast
import io

VIEJAS_ADMIN = ('["home", "fichaje", "planificacion", "proyectos", "finanzas",\n'
                '       "inventario", "herramientas", "contactos"]')

# ── v297 ─────────────────────────────────────────────────────────────────────
P = "verif_v297.py"
s = io.open(P, encoding="utf-8").read()
VIEJO = ('check("secciones = las de siempre", [k for k, _ in H._secciones()],\n'
         '      ["home", "fichaje", "planificacion", "proyectos", "finanzas",\n'
         '       "inventario", "herramientas", "contactos"])\n')
NUEVO = ('# ⚠️ CADUCADO en v472 y ACTUALIZADO (regla v385, trampa nº16): exigia la lista\n'
         '# EXACTA, asi que se puso rojo al añadir «biblioteca» a proposito — fallaba por\n'
         '# haber ganado. Es la misma correccion que v430 le hizo al bloque del campo, unas\n'
         '# lineas mas abajo. Lo que protege: al admin no se le pierde nada Y lo nuevo va\n'
         '# DESPUES (si se colara en medio, se le reordena la nav a quien ya la usaba).\n'
         '_ADMIN_VIEJAS = ["home", "fichaje", "planificacion", "proyectos", "finanzas",\n'
         '                 "inventario", "herramientas", "contactos"]\n'
         '_adm_secs = [k for k, _ in H._secciones()]\n'
         'check("no se pierde ninguna seccion del admin",\n'
         '      [x for x in _ADMIN_VIEJAS if x not in _adm_secs], [])\n'
         'check("...y las que se anadan van DESPUES (no reordenan su nav)",\n'
         '      _adm_secs[:len(_ADMIN_VIEJAS)], _ADMIN_VIEJAS)\n')
if s.count(VIEJO) != 1:
    raise SystemExit("v297: ancla no unica (%d)" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v297.py actualizado")

# ── v298 ─────────────────────────────────────────────────────────────────────
P = "verif_v298.py"
s = io.open(P, encoding="utf-8").read()

VIEJO1 = ('check("admin: secciones intactas", [k for k, _ in H._secciones()],\n'
          '      ["home", "fichaje", "planificacion", "proyectos", "finanzas",\n'
          '       "inventario", "herramientas", "contactos"])\n')
NUEVO1 = ('# ⚠️ CADUCADO en v472 y ACTUALIZADO (regla v385): «intactas» era igualdad\n'
          '# EXACTA y v472 le añade la Biblioteca a los tres roles a proposito. Lo que\n'
          '# este guardian vino a proteger en la migracion de v298 es que a los otros dos\n'
          '# roles no se les PIERDA nada, no que no puedan ganar una seccion nunca.\n'
          '_ADMIN_VIEJAS = ["home", "fichaje", "planificacion", "proyectos", "finanzas",\n'
          '                 "inventario", "herramientas", "contactos"]\n'
          '_adm_secs = [k for k, _ in H._secciones()]\n'
          'check("admin: no pierde ninguna seccion",\n'
          '      [x for x in _ADMIN_VIEJAS if x not in _adm_secs], [])\n'
          'check("admin: lo nuevo va DESPUES (no le reordena la nav)",\n'
          '      _adm_secs[:len(_ADMIN_VIEJAS)], _ADMIN_VIEJAS)\n')

VIEJO2 = ('check("3 secciones (Administracion · Pre-Start · Herramientas)", _secs,\n'
          '      ["administracion", "prestart", "herramientas"])\n')
NUEVO2 = ('# ⚠️ CADUCADO en v472 y ACTUALIZADO por la misma razon: el propietario gana la\n'
          '# Biblioteca (decision del usuario: la sube el, y todos consultan). Se afirma\n'
          '# el principio —no pierde ninguna de sus 3 y lo nuevo va detras— y de paso\n'
          '# sigue vigilada la de al lado: SIN fichaje (no ficha, v93).\n'
          '_OWNER_VIEJAS = ["administracion", "prestart", "herramientas"]\n'
          'check("propietario: no pierde ninguna de sus 3 secciones",\n'
          '      [x for x in _OWNER_VIEJAS if x not in _secs], [])\n'
          'check("propietario: lo nuevo va DESPUES", _secs[:len(_OWNER_VIEJAS)],\n'
          '      _OWNER_VIEJAS)\n')

for viejo, nuevo, etq in ((VIEJO1, NUEVO1, "admin"), (VIEJO2, NUEVO2, "owner")):
    if s.count(viejo) != 1:
        raise SystemExit("v298/%s: ancla no unica (%d)" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v298.py actualizado")
