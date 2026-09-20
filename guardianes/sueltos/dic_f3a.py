"""F3-A · Contactos (CRM) y Catálogo — diccionario ES→EN.

⚠️ NO entra aquí (y por eso no está en el dict): nada que sea CLAVE o COLUMNA. Las
claves de widget ya las excluye el extractor (`st.form(key)`); los nombres de columna
de las hojas `Clientes` y `Catalogo` (`Nombre`, `Tipo`, `Unidad`, `Categoria`,
`CostoUnit`, `Activo`…) se leen por su nombre y traducirlos rompería la lectura SIN dar
ningún error. Cuando un texto coincide con un nombre de columna se traduce solo la
ETIQUETA que se pinta, nunca el subíndice.
"""
TRAD = {
    # ── clientes_ui ────────────────────────────────────────────────
    "## :material/contacts: Clientes": "## :material/contacts: Clients",
    ":material/info: Configura Google Sheets para gestionar clientes.":
        ":material/info: Configure Google Sheets to manage clients.",
    "Aún no hay clientes. Crea el primero, o crea proyectos con un cliente.":
        "No clients yet. Create the first one, or create projects with a client.",
    "Clientes": "Clients",
    "Con ficha": "With record",
    "Sin ficha": "No record",
    ":material/search: Buscar cliente, contacto, teléfono o email":
        ":material/search: Search client, contact, phone or email",
    "escribe para filtrar…": "type to filter…",
    "Toca un cliente para ver su ficha, su resumen y sus proyectos. (":
        "Tap a client to see its record, summary and projects. (",
    " cliente(s))": " client(s))",
    ":material/search_off: Ningún cliente coincide con la búsqueda.":
        ":material/search_off: No client matches the search.",
    ":material/archive: Ver también los archivados":
        ":material/archive: Show archived ones too",
    " cliente(s) archivado(s) oculto(s).": " archived client(s) hidden.",
    "Los archivados dejan de listarse, pero no se borran: sus proyectos, horas y "
    "facturas siguen intactos.":
        "Archived ones stop being listed, but are not deleted: their projects, hours "
        "and invoices stay intact.",
    ":material/arrow_back: Volver a clientes": ":material/arrow_back: Back to clients",
    "## :material/apartment: ": "## :material/apartment: ",
    ":material/info: Este cliente aún **no tiene ficha** — sale de sus proyectos. "
    "Completa el contacto abajo y guarda para crear su ficha (y poder vincular "
    "proyectos).":
        ":material/info: This client **has no record yet** — it comes from its "
        "projects. Fill in the contact below and save to create the record (and be "
        "able to link projects).",
    "#### :material/contact_page: Ficha de contacto":
        "#### :material/contact_page: Contact record",
    ":material/save: Guardar ficha": ":material/save: Save record",
    "Ficha guardada.": "Record saved.",
    "#### :material/insights: Resumen": "#### :material/insights: Summary",
    "Proyectos": "Projects",
    "Activos": "Active",
    "Avance prom.": "Avg. progress",
    "Horas": "Hours",
    "Costo total": "Total cost",
    "** alarma(s) abierta(s)": "** open alert(s)",
    ":material/archive: Esta ficha está **archivada**: no aparece en la lista salvo "
    "que marques «Ver también los archivados».":
        ":material/archive: This record is **archived**: it does not show in the list "
        "unless you tick «Show archived ones too».",
    ":material/restore: Restaurar esta ficha": ":material/restore: Restore this record",
    ":material/archive: Archivar cliente": ":material/archive: Archive client",
    "Deja de listarse; sus proyectos no se tocan. Para volver a verlo, marca «Ver "
    "también los archivados» en la lista.":
        "It stops being listed; its projects are untouched. To see it again, tick "
        "«Show archived ones too» in the list.",
    "Archivar esta ficha": "Archive this record",
    "#### :material/folder: Proyectos de este cliente":
        "#### :material/folder: Projects for this client",
    "Aún no tiene proyectos vinculados.": "No linked projects yet.",
    ":material/link: Vincular otros proyectos a este cliente":
        ":material/link: Link other projects to this client",
    "Útil si el proyecto tiene otro texto en «Cliente» o quedó sin vincular.":
        "Useful if the project has different text in «Client» or was left unlinked.",
    "Proyectos a vincular": "Projects to link",
    ":material/link: Vincular seleccionados": ":material/link: Link selected",
    " proyecto(s) vinculado(s).": " project(s) linked.",
    "Elige al menos un proyecto.": "Choose at least one project.",
    "#### :material/receipt: Facturación": "#### :material/receipt: Invoicing",
    "Facturado": "Invoiced",
    "Cobrado": "Collected",
    "Pendiente": "Outstanding",
    "Vencido": "Overdue",
    "Sin facturas todavía.": "No invoices yet.",
    ":material/add_circle: Nueva factura para este cliente":
        ":material/add_circle: New invoice for this client",
    ":material/add_circle: Nuevo cliente": ":material/add_circle: New client",
    "Nombre del cliente *": "Client name *",
    "Persona de contacto": "Contact person",
    "Teléfono": "Phone",
    "Email": "Email",
    "Dirección": "Address",
    "Notas": "Notes",
    ":material/add: Crear cliente": ":material/add: Create client",
    "Cliente creado.": "Client created.",

    # ── catalogo_ui ────────────────────────────────────────────────
    ":material/info: Configura Google Sheets para usar el catálogo.":
        ":material/info: Configure Google Sheets to use the catalogue.",
    ":material/archive: Ver también los desactivados":
        ":material/archive: Show deactivated ones too",
    "Hay ": "There are ",
    " desactivado(s). No se borran: las cotizaciones viejas deben seguir mostrando su "
    "nombre.":
        " deactivated. They are not deleted: old quotes must keep showing their name.",
    "Buscar": "Search",
    "nombre, categoría…": "name, category…",
    "Toca un artículo para editarlo. **Costo** es lo que te cuesta a ti; el margen se "
    "pone al cotizar, línea por línea.":
        "Tap an item to edit it. **Cost** is what it costs you; the margin is set when "
        "quoting, line by line.",
    " artículo(s)": " item(s)",
    "Todavía no hay artículos. Crea el primero abajo.":
        "No items yet. Create the first one below.",
    ":material/add_circle: Nuevo artículo": ":material/add_circle: New item",
    "Tipo": "Type",
    "p. ej. Riel T75-3/B": "e.g. Rail T75-3/B",
    "Lo que se compara luego contra las horas fichadas.":
        "This is what gets compared later against the hours clocked.",
    "Descripción (opcional)": "Description (optional)",
    "lo que verá el cliente en la cotización": "what the client will see on the quote",
    ":material/save: Guardar artículo": ":material/save: Save item",
    "Artículo ": "Item ",
    " creado.": " created.",
    ":material/arrow_back: Volver al catálogo": ":material/arrow_back: Back to catalogue",
    "Artículo no encontrado.": "Item not found.",
    "## :material/sell: ": "## :material/sell: ",
    "Nombre": "Name",
    "Categoría": "Category",
    "Horas estimadas": "Estimated hours",
    "Tarifa/hora (costo)": "Rate/hour (cost)",
    "Costo unitario": "Unit cost",
    "Unidad": "Unit",
    "Descripción": "Description",
    ":material/save: Guardar cambios": ":material/save: Save changes",
    "Cambiar el costo **no altera** las cotizaciones ya emitidas: cada línea guarda su "
    "propia copia del precio pactado.":
        "Changing the cost **does not alter** quotes already issued: each line keeps "
        "its own copy of the agreed price.",
    ":material/archive: Desactivar artículo": ":material/archive: Deactivate item",
    "Deja de ofrecerse al cotizar, pero no se borra: las cotizaciones que ya lo usan "
    "siguen mostrándolo.":
        "It stops being offered when quoting, but is not deleted: quotes already using "
        "it keep showing it.",
    ":material/archive: Desactivar": ":material/archive: Deactivate",
    ":material/block: Este artículo está **desactivado**: no aparece al cotizar salvo "
    "que marques «Ver también los desactivados».":
        ":material/block: This item is **deactivated**: it does not appear when quoting "
        "unless you tick «Show deactivated ones too».",
    ":material/restore: Reactivar": ":material/restore: Reactivate",
}
