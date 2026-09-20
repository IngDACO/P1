# -*- coding: utf-8 -*-
"""v471 · el tercer sitio que v468 no reviso: el cuerpo que LEE la tabla editada.

v468 documento dos formas del fallo (claves de `column_config` renombradas sin la fila
y al reves) pero no miro las LECTURAS ni los `disabled`. Y ahi no se pierde el formato:
`_ed.iloc[i]["Hours"]` sobre una fila cuya clave es "Horas" lanza **KeyError** y la
pantalla revienta.
"""
import io
import os

RAIZ = r"C:\Users\diego\P1\survey_app"
hechos, fallos = [], []


def parche(rel, viejo, nuevo, etq):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(viejo)
    if n != 1:
        fallos.append("%s · %s: ancla %s (%d)"
                      % (rel, etq, "ausente" if not n else "ambigua", n))
        return
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(viejo, nuevo))
    hechos.append("%s · %s" % (rel, etq))


# ── 1 · EL KeyError. La pantalla «Cuanto ganas con cada persona» (💰 Costos)
#        revienta en cuanto alguien tiene horas fichadas en esa obra.
parche(
    "core/projects_ui.py",
    '    _tot = sum(P._num(_ed.iloc[i]["Hours"]) * P._num(_ed.iloc[i]["Ganancia/h"])',
    '    # ⚠️ La clave de la fila es "Horas" (v360). v468 renombro ESTA LECTURA a\n'
    '    # "Hours" y no la clave, asi que `_ed.iloc[i]["Hours"]` lanzaba KeyError y el\n'
    '    # bloque reventaba en cuanto alguien tuviera horas fichadas en la obra. Llevaba\n'
    '    # dos versiones asi, invisible solo porque la demo esta vacia.\n'
    '    _tot = sum(P._num(_ed.iloc[i]["Horas"]) * P._num(_ed.iloc[i]["Ganancia/h"])',
    "KeyError en el total de ganancia")

# ── 2 · el mismo renombrado a medias en el `disabled`: la columna de HORAS, que
#        viene del fichaje, quedaba editable.
parche(
    "core/projects_ui.py",
    'disabled=["Persona", "Hours", "Costo/h", "Precio/h", "Ganas"],',
    'disabled=["Persona", "Horas", "Costo/h", "Precio/h", "Ganas"],',
    "horas editables por error")

# ── 3 · igual en cotizaciones: el COSTO viene del catalogo y esta congelado a
#        proposito (v355/v356). Con `disabled` apuntando a una columna que no
#        existe, quedaba editable y el precio se recalcularia sobre un costo tecleado.
parche(
    "core/quotes_ui.py",
    'disabled=["Concepto", "Cost", "Margen %", "Precio"],',
    'disabled=["Concepto", "Costo", "Margen %", "Precio"],',
    "costo de la cotizacion editable por error")

print("APLICADO:")
for h in hechos:
    print("   ok  " + h)
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   !!  " + f)
    raise SystemExit(1)
