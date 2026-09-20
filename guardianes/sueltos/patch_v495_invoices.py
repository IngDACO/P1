# -*- coding: utf-8 -*-
"""v495 · fase 2.3-C: invoices.sincronizar_cobros (lo que Xero dice cobrado, en una escritura)."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")
P = "core/invoices.py"
s = io.open(P, encoding="utf-8").read()

ANCLA = '''def marcar_xero(marcas: dict, cuando: str) -> tuple:'''
assert s.count(ANCLA) == 1

NUEVO = '''def sincronizar_cobros(cobrado_xero: dict, cuando: str) -> tuple:
    """Pone el cobrado que dice Xero: 1 lectura FRESCA + 1 escritura. (ok, resultado).

    `cobrado_xero` = {ID de COPEX: {"cobrado": float, "fecha": "YYYY-MM-DD"}}.
    Devuelve `{"cambiadas": [(fid, antes, ahora)], "iguales": [fid]}` — así la pantalla
    puede decir qué se movió, y una segunda pasada no vuelve a apuntar nada.

    ⚠️ Xero es el que ve el banco, así que MANDA (decisión del usuario): si aquí había
    otra cifra, se sustituye y la pantalla lo avisa. Por eso el llamador solo debe pasar
    facturas que en Xero estén APROBADAS o PAGADAS: una en borrador tiene AmountPaid = 0
    y pondría a cero un cobro real apuntado aquí.

    ⚠️ Lo de antes se lee de la lectura FRESCA de la hoja, no de la caché (v323): decide
    lo que se escribe y el historial al que se añade.
    ⚠️ Una sola escritura para todo el lote: `_find_row` por factura serían N lecturas
    contra el techo de 60/min (v339).
    """
    if not cobrado_xero:
        return True, {"cambiadas": [], "iguales": []}
    w, err = _ws()
    if err:
        return False, err
    try:
        vals = w.get_all_values() or []
    except Exception as e:
        return False, str(e)
    if not vals:
        return False, t("Invoice not found.")
    cab = [columnas.canon(h) for h in vals[0]]
    for col in ("ID", "Collected", "CollectionDate", "CollectionsJSON"):
        if col not in cab:
            return False, t("The invoices sheet has no Xero columns yet.")
    ci, cc = cab.index("ID"), cab.index("Collected")
    cf, cj = cab.index("CollectionDate"), cab.index("CollectionsJSON")
    res = {"cambiadas": [], "iguales": []}
    rangos = []
    for n, fila in enumerate(vals[1:], start=2):
        fid = fila[ci] if ci < len(fila) else ""
        dato = cobrado_xero.get(fid)
        if not dato:
            continue
        antes = _num(fila[cc] if cc < len(fila) else 0)
        ahora = round(_num(dato.get("cobrado")), 2)
        if abs(ahora - antes) < 0.005:
            res["iguales"].append(fid)
            continue
        fch = str(dato.get("fecha") or cuando)[:10]
        try:
            hist = json.loads(fila[cj] if cj < len(fila) and fila[cj] else "[]")
            if not isinstance(hist, list):
                raise ValueError
        except Exception:
            hist = []
        # el historial guarda el MOVIMIENTO (puede ser negativo si en Xero se deshizo un
        # pago), con su origen: así se distingue lo que vino de Xero de lo apuntado a mano.
        hist.append({"fecha": fch, "monto": round(ahora - antes, 2), "origen": "xero"})
        rangos += [
            {"range": f"{_col_letter(cc + 1)}{n}", "values": [[str(ahora)]]},
            {"range": f"{_col_letter(cf + 1)}{n}", "values": [[fch]]},
            {"range": f"{_col_letter(cj + 1)}{n}", "values": [[json.dumps(hist, ensure_ascii=False)]]},
        ]
        res["cambiadas"].append((fid, antes, ahora))
    if not rangos:
        return True, res
    try:
        w.batch_update(rangos, value_input_option="RAW")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, res


'''

io.open(P, "w", encoding="utf-8", newline="").write(s.replace(ANCLA, NUEVO + ANCLA))
print("invoices.sincronizar_cobros añadida")
