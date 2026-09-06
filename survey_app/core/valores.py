# -*- coding: utf-8 -*-
"""VALORES de negocio en INGLES, con respaldo al valor viejo (v469).

⚠️ Modulo HOJA. El mapa vive AQUI y en ningun sitio mas.

## Por que este es el mas delicado de los cuatro renombrados
Una hoja mal nombrada deja la pantalla vacia; una columna mal leida devuelve "". Los
dos se VEN. Un valor que deja de casar **no se ve**: `if estado == "En progreso"`
simplemente no entra, y la rama muere en silencio.

La defensa es la misma que en las columnas —canonizar al LEER— con una diferencia:
aqui solo se traducen las columnas de la LISTA BLANCA. Sin ella, un cliente llamado
«Materiales SA» o una nota que diga «pendiente» acabarian reescritos.

⚠️ `payroll.TIPOS` (devengo/deduccion/aporte) NO esta: vive dentro de
`ConceptsJSON`, no en una columna, asi que la canonizacion al leer no lo alcanza y
renombrarlo en el codigo mataria `neto()` contra las nominas ya emitidas.
⚠️ `m`, `m²` y `kg` tampoco: son simbolos, iguales en los dos idiomas (v464).
⚠️ Ni `OFF`/`LEAVE`/`FORMACION` del roster: son identificadores, no texto.
"""

# valor viejo (español, como esta en la hoja) -> canonico (ingles, el que compara el codigo)
LEGADO = {
    'Abierta': 'Open',
    'Almacén': 'Warehouse',
    'Alquiler': 'Rental',
    'Archivado': 'Archived',
    'Cancelado': 'Cancelled',
    'Cerrada': 'Closed',
    'Combustible': 'Fuel',
    'Completado': 'Completed',
    'Consumible': 'Consumable',
    'EPP': 'PPE',
    'En pausa': 'On hold',
    'En progreso': 'In progress',
    'Equipo': 'Equipment',
    'Equipos': 'Equipment',
    'Herramienta': 'Tool',
    'Herramientas': 'Tools',
    'Ingeniería': 'Engineering',
    'Instalación': 'Installation',
    'Mantenimiento': 'Maintenance',
    'Materiales': 'Materials',
    'Oficina': 'Office',
    'Otro': 'Other',
    'Otros': 'Other',
    'Planificado': 'Planned',
    'Subcontrato': 'Subcontractor',
    'Taller': 'Workshop',
    'Transporte': 'Transport',
    'Vehículo': 'Vehicle',
    'aceptada': 'accepted',
    'administrador': 'administrator',
    'aprobada': 'approved',
    'baja': 'written off',
    'bodega': 'warehouse',
    'borrador': 'draft',
    'bueno': 'good',
    'campo': 'field',
    'cancelada': 'cancelled',
    'dañado': 'damaged',
    'disponible': 'available',
    'en_uso': 'in use',
    'entrada': 'check-in',
    'enviada': 'sent',
    'global': 'lump sum',
    'juego': 'set',
    'malo': 'poor',
    'mantenimiento': 'maintenance',
    'pendiente': 'pending',
    'producto': 'product',
    'propietario': 'owner',
    'proyecto': 'project',
    'otro': 'other',   # destino libre de una salida de inventario
    'rechazada': 'rejected',
    'recibida': 'received',
    'regular': 'fair',
    'reparacion': 'under repair',
    'revertida': 'reverted',
    'salida': 'check-out',
    'servicio': 'service',
    'traslado': 'transfer',
    'unidad': 'unit',
    'usuario': 'user',
}

CANON = {v: k for k, v in LEGADO.items()}

# ⚠️ Lista BLANCA por (HOJA, COLUMNA), no por nombre de columna suelto.
# El nombre solo no basta: `proyecto` es a la vez el tipo de FICHAJE (`Sheet1.Type`)
# y un valor de `UBIC_TIPOS` (`Assets.LocationType`). Con el par, cada columna se
# canoniza con su propio criterio y no se pisan.
#
# ⚠️ `Sheet1.Type` ESTA en la lista, y dejarlo fuera fue un fallo real de v469 que
# no daba ningun error: `TIPO_PROYECTO` paso a `"project"` mientras las ~500 filas del
# historico siguen diciendo `proyecto`, asi que `_tipo_of(r) != TIPO_PROYECTO` era
# cierto para TODAS y **ni una sola hora imputada a una obra contaba como tal**.
# Eso es la nomina, el costo de obra, la conciliacion de v313 y el reparto por
# proyecto, todo a cero, en lo que mas se usa de la app. Probado ejecutando la
# funcion real, no leyendo. `general` no esta en LEGADO, asi que pasa tal cual y
# sigue casando con `TIPO_GENERAL`.
COLUMNAS = {
    ("Sheet1", "Type"),
    ("Projects", "Status"), ("Projects", "ManualStatus"), ("Projects", "Type"),
    ("Assets", "Status"), ("Assets", "Category"), ("Assets", "Condition"),
    ("Assets", "LocationType"),
    ("AssetMovements", "Type"),
    ("AssetCategories", "Name"),
    ("Catalogue", "Type"), ("Catalogue", "Category"), ("Catalogue", "Unit"),
    ("Expenses", "Category"),
    ("Login", "Role"),
    ("Absences", "Status"), ("Absences", "Type"),
    ("TimeCorrections", "Status"),
    ("PurchaseOrders", "Status"),
    ("Quotes", "Status"),
}


def canon(v) -> str:
    """El valor canonico (el nuevo si lo conozco, si no tal cual)."""
    return LEGADO.get(str(v), str(v))


def canonizar(filas, hoja: str = ""):
    """Traduce los valores viejos de las columnas de negocio de ESA hoja.

    ⚠️ Se aplica DESPUES de canonizar las claves (aqui ya vienen en ingles) y solo
    en los pares (hoja, columna) declarados: sin `hoja` no se toca nada, porque
    canonizar a ciegas reescribiria texto libre y el tipo de fichaje.
    """
    if not filas or not hoja:
        return filas
    cols = [c for (h, c) in COLUMNAS if h == hoja]
    if not cols:
        return filas
    for f in filas:
        if not isinstance(f, dict):
            continue
        for c in cols:
            v = f.get(c)
            if isinstance(v, str) and v in LEGADO:
                f[c] = LEGADO[v]
    return filas
