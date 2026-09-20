"""v356 — actualizar precios en borrador, pero SOLO si tú lo pides.

Dos cosas, y la segunda es la importante:

1. Se avisa cuando una línea ya no coincide con el catálogo de hoy, y hay un botón para
   traer los precios nuevos conservando la ganancia en dinero (v355).

2. ⚠️ El editor DEJA de refrescar en silencio. Hasta ahora reconstruía cada línea desde
   el catálogo al guardar (`linea_de(base, cant, …)`), así que tocar cualquier celda de
   un borrador cambiaba precios que el usuario no había pedido cambiar: en su cotización
   real, el total habría pasado de $1.927,20 a otro número sin decir nada. Ahora la
   cantidad escala sobre el **costo unitario ya congelado**, y la ÚNICA puerta al
   catálogo es el botón. Un precio no puede moverse a espaldas de quien cotiza.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) core/quotes.py ────────────────────────────────────────────
q = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes.py")
s = q.read_text(encoding="utf-8")

ANCLA = '''def ganancia_de(linea: dict) -> float:'''
NUEVO = '''def escalar(linea: dict, cantidad, ganancia=None) -> dict:
    """Cambia la cantidad usando el costo unitario **YA CONGELADO** (v356).

    ⚠️ NO vuelve al catálogo. Antes el editor reconstruía la línea desde el artículo, así
    que tocar una celda de un borrador adoptaba en silencio los precios nuevos del
    catálogo — el total cambiaba sin que nadie lo pidiera. Adoptar precios nuevos es
    ahora una decisión explícita (`actualizar_precios`).
    """
    l = dict(linea)
    cant_ant = _num(l.get("cantidad")) or 1.0
    horas_unit = _num(l.get("horas")) / cant_ant if cant_ant else 0.0
    cant = _num(cantidad, 0.0)
    l["cantidad"] = cant
    l["costo_total"] = round(_num(l.get("costo_unit")) * cant, 2)
    l["horas"] = round(horas_unit * cant, 2)
    gan = ganancia_de(linea) if ganancia is None else ganancia
    return recalcular(l, ganancia=gan)


def desactualizadas(c: dict) -> list:
    """Líneas cuyo costo ya no coincide con el catálogo de HOY.

    Devuelve [{i, linea, costo_hoy, item, motivo}]. No cambia nada: solo mira, para que
    la pantalla pueda decirlo en vez de que el usuario lo descubra por el total.
    """
    from core import catalogo as CAT
    out = []
    for i, l in enumerate(lineas_de(c)):
        it = CAT.get_item(l.get("catalogo_id"))
        if not it:
            out.append({"i": i, "linea": l, "item": None, "costo_hoy": None,
                        "motivo": "ya no está en el catálogo"})
            continue
        hoy = CAT.costo_de(it, _num(l.get("cantidad")))
        if abs(hoy - _num(l.get("costo_total"))) > 0.005:
            out.append({"i": i, "linea": l, "item": it, "costo_hoy": hoy,
                        "motivo": "cambió en el catálogo"})
    return out


def actualizar_precios(cid) -> tuple:
    """Trae los precios de hoy del catálogo. **Solo en borrador** y bajo petición.

    ⚠️ Conserva la GANANCIA en dinero (v355: es lo que la persona decidió ganar); el
    margen % se recalcula sobre el costo nuevo. Una línea cuyo artículo ya no exista se
    deja intacta y se dice — no se descarta en silencio.
    """
    c = get_cotizacion(cid)
    if not c:
        return False, "Cotización no encontrada."
    if estado_de(c) != BORRADOR:
        return False, ("Solo se pueden actualizar precios en un borrador. Esta ya se "
                       "envió: saca una versión nueva.")
    des = desactualizadas(c)
    if not des:
        return False, "Los precios ya están al día."
    lineas = lineas_de(c)
    n, huerf = 0, []
    for d in des:
        if not d["item"]:
            huerf.append(str(d["linea"].get("concepto", "")))
            continue
        l = lineas[d["i"]]
        lineas[d["i"]] = linea_de(d["item"], _num(l.get("cantidad")),
                                  ganancia=ganancia_de(l))
        n += 1
    ok, msg = guardar_lineas(cid, lineas)
    if not ok:
        return False, msg
    txt = f"{n} línea(s) actualizada(s) con los precios de hoy."
    if huerf:
        txt += (" Sin tocar (ya no están en el catálogo): " + ", ".join(huerf) + ".")
    return True, txt


def ganancia_de(linea: dict) -> float:'''

assert ANCLA in s, "ancla no encontrada en quotes.py"
s = s.replace(ANCLA, NUEVO, 1)
q.write_text(s, encoding="utf-8")
print("✓ quotes.py: escalar / desactualizadas / actualizar_precios")

# ── 2) core/quotes_ui.py: el editor deja de ir al catálogo ───────
u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes_ui.py")
s = u.read_text(encoding="utf-8")

VIEJO = '''        base = CAT.get_item(l.get("catalogo_id"))
        # ⚠️ Al cambiar la CANTIDAD el costo cambia, y la ganancia tecleada se mantiene
        # tal cual (es lo que la persona dijo que quiere ganar); el margen se reajusta.
        nl = (Q.linea_de(base, cant, ganancia=gan) if base
              else Q.recalcular(l, ganancia=gan))
        nuevas.append(nl)'''
NUEVO_ED = '''        # ⚠️ v356: se escala sobre el costo unitario CONGELADO, sin volver al catálogo.
        # Antes se reconstruía desde el artículo, así que tocar una celda adoptaba en
        # silencio los precios nuevos. Adoptarlos es ahora un botón explícito.
        nuevas.append(Q.escalar(l, cant, ganancia=gan))'''
assert VIEJO in s, "ancla del editor no encontrada"
s = s.replace(VIEJO, NUEVO_ED)

# aviso + botón, arriba del editor, solo en borrador
VIEJO2 = '''    if est == Q.BORRADOR:
        nuevas = _editor_lineas(grupo, f"ed{cid}", lineas)'''
NUEVO2 = '''    if est == Q.BORRADOR:
        _des = Q.desactualizadas(c)
        if _des:
            _txt = " · ".join(
                str(d["linea"].get("concepto", "")) + ": "
                + T.dinero(d["linea"].get("costo_total"))
                + (" → " + T.dinero(d["costo_hoy"]) if d["costo_hoy"] is not None
                   else " (" + d["motivo"] + ")")
                for d in _des[:6])
            st.warning(":material/sync_problem: **El catálogo cambió** desde que armaste "
                       "esta cotización: " + _txt + ". Los precios de la cotización NO se "
                       "tocan solos.")
            if st.button(":material/sync: Actualizar precios desde el catálogo",
                         key="cot_upd_" + str(cid),
                         help="Trae los costos de hoy conservando lo que quieres ganar "
                              "en cada línea."):
                ok, msg = Q.actualizar_precios(cid)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        nuevas = _editor_lineas(grupo, f"ed{cid}", lineas)'''
assert VIEJO2 in s, "ancla del detalle no encontrada"
s = s.replace(VIEJO2, NUEVO2)
u.write_text(s, encoding="utf-8")
print("✓ quotes_ui.py: aviso + botón; el editor ya no refresca en silencio")
