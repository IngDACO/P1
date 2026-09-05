# -*- coding: utf-8 -*-
"""Columnas en INGLES, con respaldo al nombre viejo (v468).

⚠️ Modulo HOJA: solo importa lo imprescindible, asi que cualquiera puede usarlo sin
crear un ciclo. El mapa vive AQUI y en ningun sitio mas — dos copias divergen, y de
eso ya hubo cinco `_num` distintos (v323).

## Por que hace falta un respaldo
Renombrar la cabecera de una hoja **no da ningun error**: `fila.get("Status")` sobre
una fila cuya cabecera dice `Estado` devuelve `""`, y la pantalla sale con la columna
vacia. Por eso el codigo pide el nombre nuevo y el LECTOR canoniza: mientras el libro
no se haya renombrado, las claves viejas se traducen al vuelo.

⚠️ Solo se canoniza al LEER. Las escrituras van por posicion (`_COL` se deriva de
`*_HEADERS`), y renombrar una cabecera **no mueve la columna**, asi que siguen
cayendo donde deben con el libro en cualquiera de los dos estados.
"""

# viejo (español, como esta hoy en la hoja) -> canonico (ingles, como lo pide el codigo)
LEGADO = {
    'Accion': 'Action',
    'ActividadesNotas': 'ActivityNotes',
    'Activo': 'Active',
    'ActivoID': 'AssetID',
    'ActualizadoPor': 'UpdatedBy',
    'AgrupacionID': 'GroupingID',
    'AlturaDiente': 'ToothHeight',
    'AnchoDiente': 'ToothWidth',
    'Archivo': 'File',
    'AsignadoA': 'AssignedTo',
    'Asistentes': 'Attendees',
    'Avance': 'Progress',
    'CambiosJSON': 'ChangesJSON',
    'Campo': 'Field',
    'CampoAsignados': 'FieldAssigned',
    'Categoria': 'Category',
    'CertsReq': 'RequiredCerts',
    'Clase': 'Class',
    'Cliente': 'Client',
    'ClienteID': 'ClientID',
    'ClienteNombre': 'ClientName',
    'Cobrado': 'Collected',
    'CobrosJSON': 'CollectionsJSON',
    'ConceptosJSON': 'ConceptsJSON',
    'Condicion': 'Condition',
    'Contacto': 'ContactName',
    'Costo': 'Cost',
    'CostoUnit': 'UnitCost',
    'Creado': 'Created',
    'CreadoPor': 'CreatedBy',
    'DatosJSON': 'DataJSON',
    'Descripcion': 'Description',
    'Desde': 'From',
    'DesdeUbic': 'FromLocation',
    'Dias': 'Days',
    'Direccion': 'Address',
    'DuracionDias': 'DurationDays',
    'Emision': 'IssueDate',
    'Entidad': 'Entity',
    'EntidadID': 'EntityID',
    'Estado': 'Status',
    'EstadoManual': 'ManualStatus',
    'Facilitador': 'FacilitatedBy',
    'Fecha': 'Date',
    'FechaCobro': 'CollectionDate',
    'FechaCompra': 'PurchaseDate',
    'FechaDevolucion': 'ReturnDate',
    'FechaEsperada': 'ExpectedDate',
    'FechaFinEst': 'EndDateEst',
    'FechaFinReal': 'ActualEndDate',
    'FechaIngreso': 'StartedOn',
    'FechaInicio': 'StartDate',
    'FechaInicioReal': 'ActualStartDate',
    'FechaPago': 'PaymentDate',
    'FechaResuelta': 'ResolvedDate',
    'Findes': 'IncludesWeekends',
    'FotoDriveID': 'PhotoDriveID',
    'GananciaFija': 'FixedProfit',
    'GananciaHoraJSON': 'HourlyProfitJSON',
    'GastoID': 'ExpenseID',
    'Grupo': 'Group',
    'HaciaUbic': 'ToLocation',
    'Hasta': 'To',
    'Herramienta': 'Tool',
    'Hora': 'Time',
    'Horas': 'Hours',
    'HorasEst': 'EstHours',
    'Impuesto': 'Tax',
    'ImpuestoDefault': 'DefaultTax',
    'ImpuestoPct': 'TaxPct',
    'InduccionLinks': 'InductionLinks',
    'Ingeniero': 'HeadInstallers',
    'Instrucciones': 'Instructions',
    'LineasJSON': 'LinesJSON',
    'Marca': 'Brand',
    'MargenDefault': 'DefaultMargin',
    'MargenMO': 'LabourMargin',
    'MargenPct': 'MarginPct',
    'MatrizJSON': 'MatrixJSON',
    'Mensaje': 'Message',
    'Modelo': 'Model',
    'Motivo': 'Reason',
    'Neto': 'Net',
    'Nombre': 'Name',
    'NominaCubre': 'PayslipCovers',
    'Nota': 'Note',
    'NotaAdmin': 'AdminNote',
    'Notas': 'Notes',
    'NotasGenerales': 'GeneralNotes',
    'NumFrags': 'NumChunks',
    'Numero': 'Number',
    'Orden': 'Order',
    'Origen': 'Source',
    'PeriodoDesde': 'PeriodFrom',
    'PeriodoHasta': 'PeriodTo',
    'Peso': 'Weight',
    'PesoEnAgrupacion': 'WeightInGrouping',
    'PlanoJSON': 'DrawingJSON',
    'Presupuesto': 'Budget',
    'Proveedor': 'Supplier',
    'ProximoMant': 'NextService',
    'Proyecto': 'Project',
    'ProyectoID': 'ProjectID',
    'RecibidaFecha': 'ReceivedDate',
    'Referencia': 'Reference',
    'ResueltaFecha': 'ResolvedDate',
    'ResueltaPor': 'ResolvedBy',
    'ResueltoPor': 'ResolvedBy',
    'Resumen': 'Summary',
    'RetencionDefault': 'DefaultWithholding',
    'RevisadoFecha': 'ReviewedDate',
    'RevisadoPor': 'ReviewedBy',
    'Rol': 'Role',
    'Semana': 'Week',
    'Serie': 'Serial',
    'SubidoPor': 'UploadedBy',
    'SuperDefault': 'DefaultSuper',
    'TarifaHora': 'HourlyRate',
    'Telefono': 'Phone',
    'Tipo': 'Type',
    'Ubicacion': 'Location',
    'UbicacionRef': 'LocationRef',
    'UbicacionTipo': 'LocationType',
    'UltimoAviso': 'LastNotice',
    'Unidad': 'Unit',
    'Usuario': 'User',
    'Validez': 'ValidUntil',
    'Valor': 'Amount',
    'ValorAnterior': 'OldValue',
    'ValorCompra': 'PurchaseValue',
    'ValorNuevo': 'NewValue',
    'Vencimiento': 'ExpiryDate',
    'VidaUtilAnios': 'UsefulLifeYears',
    'Zona': 'TimeZone',
}

CANON = {v: k for k, v in LEGADO.items()}


def canon(nombre) -> str:
    """El nombre canonico de una columna (el nuevo si la conozco, si no tal cual)."""
    return LEGADO.get(str(nombre), str(nombre))


def canonizar(filas):
    """Renombra las claves VIEJAS de cada fila al nombre canonico.

    ⚠️ Si la fila ya trae la clave canonica **no se pisa**: en una hoja a medio
    migrar podrian convivir las dos, y la buena es la que el codigo escribe hoy.
    """
    if not filas:
        return filas
    out = []
    for f in filas:
        if not isinstance(f, dict):
            out.append(f)
            continue
        d = {}
        for k, v in f.items():
            nk = LEGADO.get(k, k)
            if nk in d and k != nk:
                continue                  # ya venia la canonica: manda esa
            d[nk] = v
        out.append(d)
    return out
