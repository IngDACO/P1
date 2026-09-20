def _partir_gasto(ge: dict) -> dict:
    """Separa el gasto del grupo en OBRA y ESTRUCTURA (v425).

    ⚠️ `group_expenses` incluye las localizaciones internas desde v422, y con razón:
    su gasto es costo REAL del grupo, y excluirlo repetiría el fallo de v310 con los
    archivados (KPI a $0 mientras la torta mostraba $1.500). Pero el KPI de esa
    pantalla se llama **«Costo cargado a obras»**, así que meterle la oficina lo haría
    MENTIR — el mismo problema que v422 resolvió en las horas. Se parten las dos
    cifras: la de obra conserva su significado y la de estructura se nombra.

    ⚠️ Las compras HUÉRFANAS (sin proyecto, o de uno borrado) se quedan del lado de
    obra: no se sabe de quién son, y moverlas a estructura sería afirmar algo que
    nadie sabe. Por eso `compras_obra` se calcula RESTANDO las internas al total del
    grupo, en vez de sumando las de obra — así se conserva la invariante de v310
    (`compras_grupo == Σ compras por proyecto + huérfanas`) y ninguna compra se pierde.

    Invariante que el guardián comprueba: `total_obra + total_int` es exactamente el
    costo del grupo de antes de v425, así que sin localizaciones NADA se mueve.

    Es una función APARTE, y no aritmética suelta dentro de la vista, para que el
    guardián pueda ejercitar la de verdad en vez de reproducirla (el error de v412).
    """
    filas = ge.get("proyectos") or []
    internas = [f for f in filas if f.get("interno")]
    obras = [f for f in filas if not f.get("interno")]
    mo_int = round(sum(f.get("mano_obra", 0) for f in internas), 2)
    cmp_int = round(sum(f.get("compras", 0) for f in internas), 2)
    mo_obra = round(sum(f.get("mano_obra", 0) for f in obras), 2)
    cmp_grupo = ge.get("compras_grupo", sum(f.get("compras", 0) for f in filas))
    cmp_obra = round(cmp_grupo - cmp_int, 2)
    return {
        "obras": obras, "internas": internas,
        "mo_obra": mo_obra, "compras_obra": cmp_obra,
        "total_obra": round(mo_obra + cmp_obra, 2),
        "mo_int": mo_int, "compras_int": cmp_int,
        "total_int": round(mo_int + cmp_int, 2),
        "huerfanos": ge.get("huerfanos", {"n": 0, "total": 0.0}),
    }


