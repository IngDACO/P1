# -*- coding: utf-8 -*-
"""v492: los ajustes contables se guardan por CLAVES, no volcando mapa() entero."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")


def rep(p, old, new):
    s = io.open(p, encoding="utf-8").read()
    assert s.count(old) == 1, (p, s.count(old), old[:70])
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))


# ── auth: lectura FRESCA de un ajuste, compartiendo la búsqueda de la fila ──
rep("core/auth.py",
    '''    for i, r in enumerate(valores.canonizar(columnas.canonizar(gws.get_all_records(numericise_ignore=["all"])), LOGIN_SHEET)):
        if str(r.get("Group", "")).strip().lower() == (grupo or "").strip().lower():
            try:
                gws.update_cell(i + 2, col, str(val))
                _invalidate_groups()
                return True, f"{field} actualizado."
            except Exception as e:
                return False, f"Error: {e}"
    return False, t("Company not found.")
''',
    '''    fila, _r = _grupo_fresco(gws, grupo)
    if fila is None:
        return False, t("Company not found.")
    try:
        gws.update_cell(fila, col, str(val))
        _invalidate_groups()
        return True, f"{field} actualizado."
    except Exception as e:
        return False, f"Error: {e}"


def _grupo_fresco(gws, grupo: str):
    """(fila de la hoja, registro) del grupo leídos FRESCOS, o (None, None).

    Una sola búsqueda para quien escribe (`set_group_setting`) y quien lee para
    escribir después (`group_text_setting_fresco`): si divergieran, uno podría leer
    una fila y el otro escribir en otra.
    """
    g = (grupo or "").strip().lower()
    for i, r in enumerate(valores.canonizar(columnas.canonizar(gws.get_all_records(numericise_ignore=["all"])), LOGIN_SHEET)):
        if str(r.get("Group", "")).strip().lower() == g:
            return i + 2, r
    return None, None


def group_text_setting_fresco(grupo: str, field: str, default: str = "") -> str:
    """Como `group_text_setting`, pero SIN caché. Para leer-fusionar-escribir (v492).

    ⚠️ LANZA si no puede leer, en vez de devolver `default`: quien fusiona sobre lo
    leído escribiría el resultado, y tratar un fallo de lectura como «no había nada»
    borraría lo que sí había guardado.
    """
    gws, err = _get_groups_ws()
    if err:
        raise RuntimeError(err)
    _f, r = _grupo_fresco(gws, grupo)
    if r is None:
        raise LookupError(t("Company not found."))
    v = r.get(field, "")
    return str(v) if v not in (None, "") else default
''')

# ── contable: guardar SOLO las claves que se tocan ──
rep("core/contable.py",
    '''def guardar_mapa(grupo: str, cfg: dict) -> tuple:
    """Guarda los ajustes contables del grupo (una escritura)."""
    try:
        crudo = json.dumps(cfg or {}, ensure_ascii=False)
    except Exception as e:
        return False, f"Error: {e}"
    return auth.set_group_setting(grupo, "AccountingJSON", crudo)
''',
    '''def guardar_claves(grupo: str, cambios: dict) -> tuple:
    """Guarda SOLO estas claves de los ajustes contables; lo demás guardado se conserva.

    ⚠️ v492 — antes cada guardado escribía `mapa()` ENTERO, que es lo guardado ya
    FUSIONADO con los valores de fábrica: guardar un emparejado con Xero congelaba en
    el grupo todos los valores por defecto (cuentas, nombres de nómina, moneda…) y un
    cambio futuro de un valor de fábrica en el código dejaba de llegarle, sin avisar.
    Visto al limpiar la prueba de v490: `AccountingJSON` estaba vacío y salió lleno.

    Una clave cuyo valor es un dict se fusiona UN nivel (así guardar las cuentas de
    Xero no borra las de MYOB); el resto sustituye.

    ⚠️ Lee lo guardado FRESCO: decide qué se escribe, y fusionar sobre la caché de
    120 s perdería la clave que otra sesión acaba de guardar (v323). Si no se puede
    leer, NO se escribe: escribir solo lo nuevo borraría lo que había.
    """
    try:
        crudo = auth.group_text_setting_fresco(grupo, "AccountingJSON", "")
    except Exception as e:
        return False, f"{t('The accounting settings could not be read; nothing was saved.')} ({e})"
    try:
        guardado = json.loads(crudo) if crudo else {}
        if not isinstance(guardado, dict):
            raise ValueError("no es un objeto JSON")
    except Exception as e:
        # Ilegible = ya nadie podía leerlo (`mapa()` lo trata como vacío): no hay nada
        # legible que perder, y queda rastro en vez de sobrescribir en silencio.
        logger.warning("contable: AccountingJSON ilegible en %s, se reemplaza: %s", grupo, e)
        guardado = {}
    for k, v in (cambios or {}).items():
        if isinstance(v, dict) and isinstance(guardado.get(k), dict):
            guardado[k] = {**guardado[k], **v}
        else:
            guardado[k] = v
    try:
        nuevo = json.dumps(guardado, ensure_ascii=False)
    except Exception as e:
        return False, f"Error: {e}"
    return auth.set_group_setting(grupo, "AccountingJSON", nuevo)
''')

# ── los cuatro escritores ──
rep("core/xero_nomina.py",
    '''    cfg = dict(contable.mapa(grupo))
    cfg["xero_empleados"] = {"tenant": tenant_id,
                             "map": {str(k): str(v) for k, v in (mapa_nuevo or {}).items() if v}}
    return contable.guardar_mapa(grupo, cfg)
''',
    '''    # ⚠️ Solo esta clave (v492): antes se escribía `mapa()` entero y se congelaban en
    # el grupo todos los valores contables de fábrica.
    return contable.guardar_claves(grupo, {"xero_empleados": {
        "tenant": tenant_id,
        "map": {str(k): str(v) for k, v in (mapa_nuevo or {}).items() if v}}})
''')

rep("core/xero_ui.py",
    '''        nuevo = dict(contable.mapa(grupo))
        nuevo["xero_estado"] = st.session_state.get("cpxseg_xero_estado", actual)
        ok, msg = contable.guardar_mapa(grupo, nuevo)
''',
    '''        ok, msg = contable.guardar_claves(
            grupo, {"xero_estado": st.session_state.get("cpxseg_xero_estado", actual)})
''')

rep("core/contable_ui.py",
    '''        nuevo = dict(cfg)
        # ⚠️ Solo se toca el perfil que se está editando: `mapa()` fusiona sobre los de
        # fábrica, así que escribir el diccionario entero borraría lo del otro perfil.
        nuevo.setdefault("cuentas", {})
        nuevo["cuentas"] = {p: dict(c) for p, c in cfg.get("cuentas", {}).items()}
        nuevo["cuentas"][perfil] = {
            filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
            for i in range(len(filas))}
        nuevo["categoria_seguimiento"] = seg.strip() or "Project"
        nuevo["gastos_incluyen_impuesto"] = bool(dentro)
        ok, msg = contable.guardar_mapa(grupo, nuevo)
''',
    '''        # ⚠️ Solo lo de esta pantalla, y de las cuentas solo el perfil que se edita:
        # `guardar_claves` fusiona un nivel, así que las de MYOB sobreviven a guardar las
        # de Xero. Antes se escribía `mapa()` entero y se congelaba lo de fábrica (v492).
        ok, msg = contable.guardar_claves(grupo, {
            "cuentas": {perfil: {filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
                                 for i in range(len(filas))}},
            "categoria_seguimiento": seg.strip() or "Project",
            "gastos_incluyen_impuesto": bool(dentro)})
''')

rep("core/contable_ui.py",
    '''        nuevo = dict(cfg)
        nuevo["conceptos"] = {filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip()
                              or filas[i]["_k"] for i in range(len(filas))}
        ok, msg = contable.guardar_mapa(grupo, nuevo)
''',
    '''        ok, msg = contable.guardar_claves(grupo, {"conceptos": {
            filas[i]["_k"]: str(ed.iloc[i]["Cuenta"] or "").strip() or filas[i]["_k"]
            for i in range(len(filas))}})
''')
print("parcheado")
