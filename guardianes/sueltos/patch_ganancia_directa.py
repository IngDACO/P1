"""v355 — se escribe la GANANCIA en dinero y el margen % se calcula solo.

Petición del usuario: «el admin pone el valor que desea ganar sobre el costo base y el
% de margen se calcula de forma automática». Es invertir la entrada: antes se tecleaba
el % y salía el precio; ahora se teclea lo que quieres ganar y sale el %.

Se conserva `margen_pct` en la línea (lo consumen el `MargenMO` del proyecto al aceptar
y la columna Margen de la lista): sigue siendo la misma línea, solo cambia por dónde
entra el dato.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) core/quotes.py ────────────────────────────────────────────
q = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes.py")
s = q.read_text(encoding="utf-8")

VIEJO = '''def linea_de(item: dict, cantidad=1, margen_pct=None) -> dict:
    """Una línea de cotización a partir de un artículo del catálogo.

    ⚠️ SNAPSHOT: se copian el costo y el margen, no una referencia. Ver el módulo.
    """
    from core import catalogo as CAT
    cant = _num(cantidad, 0.0)
    costo = CAT.costo_de(item, cant)
    m = _num(margen_pct, 0.0)
    precio = round(costo * (1.0 + m / 100.0), 2)'''

NUEVO = '''def margen_de(costo, ganancia) -> float:
    """% de margen que representa ganar `ganancia` sobre `costo`. **La única fórmula.**

    ⚠️ Con costo 0 el margen no existe (no se puede dividir): se devuelve 0 y el precio
    acaba siendo la ganancia a secas. El catálogo ya impide artículos sin costo, así que
    esto solo se da con cantidad 0 — que la pantalla descarta.
    """
    c = _num(costo)
    return round(100.0 * _num(ganancia) / c, 2) if c > 0.005 else 0.0


def linea_de(item: dict, cantidad=1, margen_pct=None, ganancia=None) -> dict:
    """Una línea de cotización a partir de un artículo del catálogo.

    Se puede fijar el precio por **margen %** o por **ganancia en dinero** (v355, que es
    como el usuario lo pide: «pongo lo que quiero ganar y el % sale solo»). Si llegan
    los dos, manda la ganancia — es el dato que la persona escribió.

    ⚠️ SNAPSHOT: se copian el costo y el margen, no una referencia. Ver el módulo.
    """
    from core import catalogo as CAT
    cant = _num(cantidad, 0.0)
    costo = CAT.costo_de(item, cant)
    if ganancia is not None:
        m = margen_de(costo, ganancia)
        precio = round(costo + _num(ganancia), 2)
    else:
        m = _num(margen_pct, 0.0)
        precio = round(costo * (1.0 + m / 100.0), 2)'''

assert VIEJO in s, "ancla 1 no encontrada"
s = s.replace(VIEJO, NUEVO)

VIEJO2 = '''def recalcular(linea: dict) -> dict:
    """Reaplica el margen sobre el costo YA CONGELADO (no vuelve al catálogo)."""
    l = dict(linea)
    l["precio_total"] = round(_num(l.get("costo_total")) * (1.0 + _num(l.get("margen_pct")) / 100.0), 2)
    return l'''

NUEVO2 = '''def recalcular(linea: dict, ganancia=None) -> dict:
    """Reaplica el precio sobre el costo YA CONGELADO (no vuelve al catálogo).

    Con `ganancia` fija el precio por dinero y deriva el % (v355); sin ella, aplica el
    `margen_pct` que la línea ya lleva.
    """
    l = dict(linea)
    costo = _num(l.get("costo_total"))
    if ganancia is not None:
        l["margen_pct"] = margen_de(costo, ganancia)
        l["precio_total"] = round(costo + _num(ganancia), 2)
    else:
        l["precio_total"] = round(costo * (1.0 + _num(l.get("margen_pct")) / 100.0), 2)
    return l


def ganancia_de(linea: dict) -> float:
    """Lo que se gana en esa línea, en dinero. Derivado: no se guarda aparte para que
    no pueda desacompasarse del precio (la lección de los helpers divergentes de v323)."""
    return round(_num(linea.get("precio_total")) - _num(linea.get("costo_total")), 2)'''

assert VIEJO2 in s, "ancla 2 no encontrada"
s = s.replace(VIEJO2, NUEVO2)
q.write_text(s, encoding="utf-8")
print("✓ quotes.py: margen_de / linea_de(ganancia=) / recalcular(ganancia=) / ganancia_de")

# ── 2) core/quotes_ui.py: la columna que se edita ────────────────
u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes_ui.py")
s = u.read_text(encoding="utf-8")

VIEJO_UI = '''    st.markdown("**Líneas** — ajusta cantidad y el margen que quieres cobrar en cada una")
    ed = st.data_editor(
        pd.DataFrame([{
            "Concepto": l.get("concepto", ""),
            "Cant.": _num(l.get("cantidad")),
            "Costo": _num(l.get("costo_total")),
            "Margen %": _num(l.get("margen_pct")),
            "Precio": _num(l.get("precio_total")),
            "Quitar": False,
        } for l in lineas]),
        hide_index=True, use_container_width=True, key=f"{key}_ed",
        disabled=["Concepto", "Costo", "Precio"],
        column_config={
            "Costo": st.column_config.NumberColumn("Costo", format="$%.2f",
                                                   help="Lo que te cuesta a ti. No lo ve el cliente."),
            "Precio": st.column_config.NumberColumn("Precio", format="$%.2f",
                                                    help="Se recalcula al guardar."),
            "Margen %": st.column_config.NumberColumn("Margen %", format="%.1f%%", min_value=0.0),
            "Cant.": st.column_config.NumberColumn("Cant.", min_value=0.0)})

    # ⚠️ La cantidad se reaplica sobre el artículo del catálogo (el costo depende de
    # ella); el margen, sobre el costo ya congelado.
    nuevas = []
    for i, l in enumerate(lineas):
        if i >= len(ed) or bool(ed.iloc[i]["Quitar"]):
            continue
        cant, marg = _num(ed.iloc[i]["Cant."]), _num(ed.iloc[i]["Margen %"])
        if cant <= 0:
            continue
        base = CAT.get_item(l.get("catalogo_id"))
        nl = Q.linea_de(base, cant, marg) if base else Q.recalcular(dict(l, margen_pct=marg))
        nuevas.append(nl)
    return nuevas'''

NUEVO_UI = '''    st.markdown("**Líneas** — pon **cuánto quieres ganar** en cada rubro; "
                "el margen % y el precio salen solos")
    ed = st.data_editor(
        pd.DataFrame([{
            "Concepto": l.get("concepto", ""),
            "Cant.": _num(l.get("cantidad")),
            "Costo": _num(l.get("costo_total")),
            "Ganancia $": Q.ganancia_de(l),
            "Margen %": _num(l.get("margen_pct")),
            "Precio": _num(l.get("precio_total")),
            "Quitar": False,
        } for l in lineas]),
        hide_index=True, use_container_width=True, key=f"{key}_ed",
        # ⚠️ v355: lo único que se teclea del precio es la GANANCIA. El margen y el
        # precio son consecuencia, y se muestran bloqueados para que quede claro.
        disabled=["Concepto", "Costo", "Margen %", "Precio"],
        column_config={
            "Costo": st.column_config.NumberColumn("Costo", format="$%.2f",
                                                   help="Lo que te cuesta a ti. No lo ve el cliente."),
            "Ganancia $": st.column_config.NumberColumn(
                "Ganancia $", format="$%.2f", min_value=0.0,
                help="Lo que quieres ganar en este rubro. El margen % se calcula solo."),
            "Margen %": st.column_config.NumberColumn("Margen %", format="%.1f%%",
                                                      help="Se calcula: ganancia ÷ costo."),
            "Precio": st.column_config.NumberColumn("Precio", format="$%.2f",
                                                    help="Costo + ganancia. Es lo que ve el cliente."),
            "Cant.": st.column_config.NumberColumn("Cant.", min_value=0.0)})

    # ⚠️ La cantidad se reaplica sobre el artículo del catálogo (el costo depende de
    # ella); la ganancia, sobre el costo ya congelado.
    nuevas = []
    for i, l in enumerate(lineas):
        if i >= len(ed) or bool(ed.iloc[i]["Quitar"]):
            continue
        cant, gan = _num(ed.iloc[i]["Cant."]), _num(ed.iloc[i]["Ganancia $"])
        if cant <= 0:
            continue
        base = CAT.get_item(l.get("catalogo_id"))
        # ⚠️ Al cambiar la CANTIDAD el costo cambia, y la ganancia tecleada se mantiene
        # tal cual (es lo que la persona dijo que quiere ganar); el margen se reajusta.
        nl = (Q.linea_de(base, cant, ganancia=gan) if base
              else Q.recalcular(l, ganancia=gan))
        nuevas.append(nl)
    return nuevas'''

assert VIEJO_UI in s, "ancla UI no encontrada"
s = s.replace(VIEJO_UI, NUEVO_UI)
u.write_text(s, encoding="utf-8")
print("✓ quotes_ui.py: se edita «Ganancia $»; margen y precio bloqueados")
