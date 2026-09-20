# -*- coding: utf-8 -*-
"""Smoke de v469: EJECUTA el viaje completo de un valor de negocio.

⚠️ «Compila e importa» no verifica nada de una migración de valores: importar no
ejecuta (v378), y el fallo de esta capa —una comparación que deja de casar— vive
dentro de la función, no en su firma. Aquí se recorre:

    fila de la hoja (vieja o nueva)  ->  canonizar  ->  la comparacion REAL del
    codigo  ->  lo que se muestra en pantalla

en las siete familias de valor que v469 toca, mas las dos que se dejan a proposito.
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))

fallos = []
n_ok = 0


def chk(msg, cond, detalle=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % msg)
    else:
        fallos.append(msg)
        print("   FALLO %s  %s" % (msg, ("-> " + str(detalle)) if detalle else ""))


def sec(t):
    print("\n%s" % t)


from core import valores as VAL, i18n            # noqa: E402


def viaje(hoja, col, viejo, canonico):
    """La fila vieja y la nueva tienen que acabar las dos en el canonico."""
    a = VAL.canonizar([{col: viejo}], hoja)[0][col]
    b = VAL.canonizar([{col: canonico}], hoja)[0][col]
    return a == canonico and b == canonico


sec("1. Una fila SIN migrar y una migrada acaban en el mismo valor")
CASOS = [
    ("Projects", "Status", "En progreso", "In progress"),
    ("Projects", "ManualStatus", "En pausa", "On hold"),
    ("Projects", "Type", "Instalación", "Installation"),
    ("Sheet1", "Type", "proyecto", "project"),
    ("Assets", "Status", "en_uso", "in use"),
    ("Assets", "Condition", "bueno", "good"),
    ("Assets", "LocationType", "bodega", "warehouse"),
    ("AssetMovements", "Type", "traslado", "transfer"),
    ("Catalogue", "Type", "servicio", "service"),
    ("Catalogue", "Unit", "unidad", "unit"),
    ("Expenses", "Category", "Materiales", "Materials"),
    ("Login", "Role", "administrador", "administrator"),
    ("Absences", "Status", "aprobada", "approved"),
    ("TimeCorrections", "Status", "revertida", "reverted"),
    ("PurchaseOrders", "Status", "recibida", "received"),
    ("Quotes", "Status", "aceptada", "accepted"),
]
for h, c, v, k in CASOS:
    chk("%-16s %-14s %-14r -> %r" % (h, c, v, k), viaje(h, c, v, k))

sec("2. La comparacion REAL del codigo casa con la fila vieja")
from core import timeclock as TC                 # noqa: E402
_f = VAL.canonizar([{"Type": "proyecto"}], "Sheet1")[0]
chk("timeclock: un segmento de proyecto del historico cuenta como tal",
    TC._tipo_of(_f) == TC.TIPO_PROYECTO, TC._tipo_of(_f))
_g = VAL.canonizar([{"Type": "general"}], "Sheet1")[0]
chk("timeclock: la jornada sigue siendo jornada",
    TC._tipo_of(_g) == TC.TIPO_GENERAL, TC._tipo_of(_g))

from core import projects as P                   # noqa: E402
chk("projects: el estado derivado es canonico",
    P.derive_estado(50, "", "") == "In progress"
    and P.derive_estado(100, "", "") == "Completed",
    "%s / %s" % (P.derive_estado(50, "", ""), P.derive_estado(100, "", "")))
chk("projects: un override VIEJO sigue mandando",
    P.derive_estado(50, VAL.canon("En pausa"), "") == "On hold",
    P.derive_estado(50, VAL.canon("En pausa"), ""))

from core import inventory as INV                # noqa: E402
chk("inventory: un activo del historico sigue contando como en uso",
    VAL.canonizar([{"Status": "en_uso"}], "Assets")[0]["Status"] == "in use")
chk("inventory: `alertas` compara contra el canonico",
    '"in use"' in open("core/inventory.py", encoding="utf-8").read())

sec("3. Lo que ve la persona")
import core.inventory_ui as IU                   # noqa: E402
chk("la ficha del activo pinta el estado con su color",
    IU._est_lbl("available") == ":green[available]", IU._est_lbl("available"))
import core.invoices_ui as VU                    # noqa: E402
from core import invoices as I                   # noqa: E402
_est = I.estado_cobro({"Total": "100", "Collected": "0",
                       "Status": "emitida", "ExpiryDate": "2099-01-01"})
chk("el chip de la factura encuentra su icono (no sale el texto crudo)",
    _est in VU._EST_FMT, "%r no esta en %s" % (_est, list(VU._EST_FMT)))
chk("...y se muestra traducido", i18n.etiqueta(_est) == "pending", i18n.etiqueta(_est))

sec("4. Lo que se deja en espanol A PROPOSITO, sigue coherente")
from core import payroll as PR                   # noqa: E402
chk("payroll.TIPOS sigue en espanol (vive en ConceptsJSON, no en una columna)",
    set(PR.TIPOS) == {"devengo", "deduccion", "aporte"}, str(PR.TIPOS))
_neto = PR.neto(1000.0, [{"tipo": "devengo", "monto": 100.0},
                         {"tipo": "deduccion", "monto": 200.0},
                         {"tipo": "aporte", "monto": 50.0}])
chk("...y la DEDUCCION se sigue restando del neto (1000+100-200 = 900)",
    abs(_neto - 900.0) < 0.01, _neto)
chk("facturas: la columna Status NO se canoniza (coherente de punta a punta)",
    ("Invoices", "Status") not in VAL.COLUMNAS)
chk("...asi que una factura anulada del historico sigue detectandose",
    VAL.canonizar([{"Status": "anulada"}], "Invoices")[0]["Status"] == "anulada")

print("")
if fallos:
    print("HAY FALLOS: %d de %d" % (len(fallos), len(fallos) + n_ok))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
