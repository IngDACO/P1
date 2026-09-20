

# ── IDs que NO se reciclan (v427) ────────────────────────────────────────────
_RE_ID = None


def ids_referenciados(prefijo: str, propia: str = "", sheet_id: str = "") -> set:
    """IDs con ese `prefijo` que aparecen en CUALQUIER hoja menos la suya.

    ## Por qué existe

    Los 13 generadores de la app hacen `max(los que existen) + 1`, así que **borrar
    la fila con el ID más alto libera ese número** y el siguiente alta lo reutiliza.
    Todo lo que hubiera quedado apuntando al ID viejo —una factura, un gasto, un
    fichaje— **se pega a la entidad nueva**.

    ⚠️ No es teórico: pasó en el ejercicio del ciclo de negocio de v426. Dos facturas
    de una prueba vieja apuntaban a `PRJ-0017`; al recrear ese ID, la obra nueva
    **heredó $1.000 de facturación ajena** y su pendiente de facturar bajó de $4.000
    a $3.000. Fue lo que destapó, tirando del hilo, que el P&L contaba las facturas
    anuladas.

    ## Qué se considera «referenciado»

    Que el ID aparezca **en cualquier celda de cualquier otra hoja**, incluidos los
    JSON incrustados (líneas de factura, `DatosJSON` del roster). Se busca por texto a
    propósito: saber en qué columna vive cada referencia obligaría a mantener un mapa
    de 12 hojas que envejecería al añadir la siguiente.

    ⚠️ **La hoja `Auditoria` cuenta también.** Ahí quedan registrados cambios de
    objetos que ya no existen, y eso es justo la señal que interesa: ese ID *se usó*.
    Reutilizarlo mezclaría dos historiales en el mismo identificador.

    ⚠️ **La hoja propia se EXCLUYE**: ahí el ID vive legítimamente, y contarla haría
    que ningún ID vivo pudiera existir.

    ## Coste

    Una llamada `values:batchGet` — la misma mecánica del lote de v339, pero **FRESCA**:
    esto es una ruta de ESCRITURA (decide qué ID se emite) y usar una caché para eso
    es como se corrompen los datos (regla v323). Crear algo es una acción humana y
    rara; una lectura de más ahí es barata.

    Si algo falla devuelve **vacío**, o sea el comportamiento de siempre: un fallo de
    lectura no puede impedir dar de alta.
    """
    import re
    pref = str(prefijo or "").strip()
    if not pref:
        return set()
    rx = re.compile(re.escape(pref) + r"\d+")
    propia_l = str(propia or "").strip().lower()
    try:
        sheet_id = sheet_id or timeclock.sheet_id_para("Sheet1")
        lib = _libro(sheet_id)
        if lib is None:
            return set()
        hay = _existentes(sheet_id)
        # Todas las del lote MÁS `Auditoria`, que no está en HOJAS_LECTURA (su lector
        # va aparte) y es justamente donde queda constancia de lo borrado.
        titulos = [h for h in tuple(HOJAS_LECTURA) + ("Auditoria",)
                   if h.strip().lower() in hay and h.strip().lower() != propia_l]
        if not titulos:
            return set()
        r = lib.values_batch_get([f"'{h}'" for h in titulos])
        out = set()
        for tramo in (r.get("valueRanges") or []):
            for fila in (tramo.get("values") or []):
                for celda in fila:
                    if pref in celda:
                        out.update(rx.findall(celda))
        return out
    except Exception as e:
        logger.warning("hojas.ids_referenciados(%s): %s", prefijo, e)
        return set()


def siguiente_id_libre(prefijo: str, maximo: int, propia: str = "",
                       ancho: int = 4, tope: int = 200) -> str:
    """El siguiente ID que NO esté ya referenciado en otra hoja (v427).

    `maximo` es el mayor número en uso HOY (lo que cada `_next_id` ya calcula leyendo
    fresco su propia hoja). Desde ahí se avanza saltando los que alguien referencia.

    ⚠️ `tope` acota el barrido: si algo va mal y todo pareciera ocupado, se devuelve
    el siguiente sin más en vez de colgarse. Fallar hacia el comportamiento de
    siempre es mejor que no poder crear nada.
    """
    usados = ids_referenciados(prefijo, propia)
    n = int(maximo) + 1
    saltados = []
    for _ in range(tope):
        if f"{prefijo}{n:0{ancho}d}" not in usados:
            break
        saltados.append(n)
        n += 1
    if saltados:
        logger.info("hojas: %s salta %s (referenciados en otras hojas)",
                    prefijo, saltados)
    return f"{prefijo}{n:0{ancho}d}"
