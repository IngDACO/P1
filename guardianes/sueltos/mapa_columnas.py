# -*- coding: utf-8 -*-
"""Mapa de columnas: nombre viejo (español) -> nombre canonico (ingles).

⚠️ Solo entran las que CAMBIAN. Las que ya estan en ingles o son identificadores
(ID, NS, PIN, Lat, Lng, Email, Password, Base, Neto, *JSON, *ID) no aparecen.
"""
COLUMNAS = {
    # identidad y comunes
    "Nombre": "Name", "Fecha": "Date", "Estado": "Status", "Tipo": "Type",
    "Grupo": "Group", "Usuario": "User", "Nota": "Note", "Notas": "Notes",
    "Cliente": "Client", "Activo": "Active", "Creado": "Created",
    "CreadoPor": "CreatedBy", "ActualizadoPor": "UpdatedBy", "Orden": "Order",
    "Numero": "Number", "Color": "Color", "Descripcion": "Description",
    "Hora": "Time", "Accion": "Action", "Origen": "Source", "Motivo": "Reason",
    "Mensaje": "Message", "Resumen": "Summary", "Archivo": "File",
    "Referencia": "Reference", "Version": "Version", "Zona": "TimeZone",
    "Clase": "Class", "Marca": "Brand", "Modelo": "Model", "Serie": "Serial",
    "Proveedor": "Supplier", "Direccion": "Address", "Telefono": "Phone",
    "Contacto": "ContactName", "Instrucciones": "Instructions",
    "Facilitador": "FacilitatedBy", "Asistentes": "Attendees",
    "Herramienta": "Tool", "SubidoPor": "UploadedBy", "Emision": "IssueDate",
    "Vencimiento": "ExpiryDate", "Validez": "ValidUntil", "Semana": "Week",
    "Dias": "Days", "Findes": "IncludesWeekends", "Desde": "From", "Hasta": "To",
    "Campo": "Field", "Entidad": "Entity", "ValorAnterior": "OldValue",
    "ValorNuevo": "NewValue", "Rol": "Role",
    # proyecto
    "Proyecto": "Project", "Avance": "Progress", "Ingeniero": "HeadInstallers",
    "Presupuesto": "Budget", "DuracionDias": "DurationDays", "Peso": "Weight",
    "PesoEnAgrupacion": "WeightInGrouping", "Ubicacion": "Location",
    # dinero
    "Costo": "Cost", "CostoUnit": "UnitCost", "Total": "Total",
    "Subtotal": "Subtotal", "Impuesto": "Tax", "Cobrado": "Collected",
    "Valor": "Amount", "ValorCompra": "PurchaseValue", "Horas": "Hours",
    "Categoria": "Category", "Unidad": "Unit", 
    # inventario
    "Condicion": "Condition", "UbicacionTipo": "LocationType",
    "UbicacionRef": "LocationRef", "VidaUtilAnios": "UsefulLifeYears",
    "ProximoMant": "NextService", "AsignadoA": "AssignedTo",
    # rieles
    "AnchoDiente": "ToothWidth", "AlturaDiente": "ToothHeight",
    # alarmas / resolucion
    "ResueltoPor": "ResolvedBy", "ResueltaPor": "ResolvedBy",
    "ResueltaFecha": "ResolvedDate", "FechaResuelta": "ResolvedDate",
    "RevisadoPor": "ReviewedBy", "RevisadoFecha": "ReviewedDate",
    "NotaAdmin": "AdminNote",
    # fechas compuestas
    "FechaInicio": "StartDate", "FechaFinEst": "EndDateEst",
    "FechaInicioReal": "ActualStartDate", "FechaFinReal": "ActualEndDate",
    "FechaCompra": "PurchaseDate", "FechaCobro": "CollectionDate",
    "FechaPago": "PaymentDate", "FechaEsperada": "ExpectedDate",
    "FechaDevolucion": "ReturnDate", "FechaIngreso": "StartedOn",
    "RecibidaFecha": "ReceivedDate", "PeriodoDesde": "PeriodFrom",
    "PeriodoHasta": "PeriodTo", "UltimoAviso": "LastNotice",
    # varios
    "TarifaHora": "HourlyRate", "HorasEst": "EstHours",
    "CampoAsignados": "FieldAssigned", "InduccionLinks": "InductionLinks",
    "ActividadesNotas": "ActivityNotes", "NotasGenerales": "GeneralNotes",
    "NumFrags": "NumChunks", "NominaCubre": "PayslipCovers",
    "FotoDriveID": "PhotoDriveID", "ClienteNombre": "ClientName",
    "MargenMO": "LabourMargin", "MargenPct": "MarginPct",
    "MargenDefault": "DefaultMargin", "ImpuestoDefault": "DefaultTax",
    "RetencionDefault": "DefaultWithholding", "SuperDefault": "DefaultSuper",
    "GananciaFija": "FixedProfit", "CertsReq": "RequiredCerts",
    "DesdeUbic": "FromLocation", "HaciaUbic": "ToLocation",
    # IDs de relacion. ⚠️ El VALOR (PRJ-0001) no cambia: solo el nombre de la columna.
    "ProyectoID": "ProjectID", "AgrupacionID": "GroupingID",
    "ActivoID": "AssetID", "ClienteID": "ClientID", "GastoID": "ExpenseID",
    "EntidadID": "EntityID",
    # columnas que guardan JSON. ⚠️ Cambia el nombre de la COLUMNA, nunca las claves
    # de dentro: esas son DATO y romperlas descasa lo ya guardado sin dar error.
    "DatosJSON": "DataJSON", "LineasJSON": "LinesJSON",
    "ConceptosJSON": "ConceptsJSON", "CobrosJSON": "CollectionsJSON",
    "CambiosJSON": "ChangesJSON", "MatrizJSON": "MatrixJSON",
    "PlanoJSON": "DrawingJSON", "GananciaHoraJSON": "HourlyProfitJSON",
    # resto
    "EstadoManual": "ManualStatus", "ImpuestoPct": "TaxPct", "Neto": "Net",
}
