# -*- coding: utf-8 -*-
"""v495 · fase 2.3-C: xero.traer_cobros — lo cobrado en Xero entra en COPEX."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")
P = "core/xero.py"
s = io.open(P, encoding="utf-8").read()

# 1 · constantes: qué estados de Xero admiten (o no) un cobro
ANCLA_C = '_VIVAS = {"DRAFT", "SUBMITTED", "AUTHORISED", "PAID"}   # DELETED/VOIDED no cuentan\n'
assert s.count(ANCLA_C) == 1
NUEVAS_C = ANCLA_C + '''# ⚠️ Un pago en Xero solo se aplica a una factura APROBADA (o ya pagada). Una en
# borrador tiene AmountPaid = 0, así que sincronizar desde ella pondría a cero un cobro
# real apuntado en COPEX: por eso el cobrado solo se lee de estas dos.
_COBRABLES = {"AUTHORISED", "PAID"}
_SIN_COBRO = {"DRAFT", "SUBMITTED"}                     # todavía no pueden recibir pagos
_MUERTAS = {"VOIDED", "DELETED"}                        # ya no existen para Xero
_POR_CONSULTA = 40                  # IDs por GET: 40 × 37 caracteres cabe de sobra en la URL
'''
s = s.replace(ANCLA_C, NUEVAS_C)

# 3 · una sola definición del parser de fechas de Xero (v323): vivía en xero_nomina,
#     y ahora la necesitan las dos (el parte y el cobrado de una factura).
ANCLA_F = """def url_factura(short_code: str, invoice_id: str) -> str:"""
assert s.count(ANCLA_F) == 1
PARSER = '''def de_fecha(valor):
    """`/Date(ms+0000)/` o `YYYY-MM-DD` → date (o None). Xero devuelve el primero.

    ⚠️ Una sola definición: nació en `xero_nomina` (v490) para las fechas del parte y la
    necesita también el cobrado de una factura. Dos parsers de la misma fecha es como
    empiezan las divergencias de v323.
    """
    import re as _re
    m = _re.search(r"/Date\((-?\d+)", str(valor or ""))
    if m:
        return _dt.datetime.fromtimestamp(int(m.group(1)) / 1000, _dt.timezone.utc).date()
    return _parse_date(valor)


'''
s = s.replace(ANCLA_F, PARSER + ANCLA_F)

# 2 · la función, al final del módulo
NUEVO = '''

def traer_cobros(grupo: str) -> dict:
    """Trae de Xero lo cobrado de las facturas ya enviadas. Dirección Xero → COPEX.

    {actualizadas, iguales, en_borrador, muertas, con_credito, no_encontradas, errores, avisos}

    Decisiones del usuario (fase 2.3-C): el cobro lo registra el contable EN XERO, se trae
    con un BOTÓN, las facturas siguen saliendo en borrador (y se avisa de las que por eso
    no pueden recibir pagos), y si el importe no cuadra **manda Xero** y se avisa.

    ⚠️ El cobrado se lee de `AmountPaid` de la propia factura, no de `GET /Payments`: la
    lista de invoices lo trae en el resumen (una llamada por lote de 40) y es la cifra que
    Xero mantiene al conciliar. `AmountCredited` —notas de crédito, anticipos— NO se suma:
    no es dinero recibido, así que se AVISA aparte; si se sumara, COPEX diría «cobrado»
    de algo que nadie pagó.
    ⚠️ Idempotente: pone el valor (no lo suma), así que pulsar dos veces no cobra dos veces.
    """
    from core import invoices

    res = {"actualizadas": [], "iguales": [], "en_borrador": [], "muertas": [],
           "con_credito": [], "no_encontradas": [], "errores": [], "avisos": []}
    with _cerrojo(grupo):
        try:
            facturas = [f for f in invoices.list_facturas(grupo)
                        if str(f.get("XeroInvoiceID", "") or "").strip()
                        and _norm(f.get("Status")) != "anulada"]
        except Exception as e:
            res["errores"].append(str(e))
            return res
        if not facturas:
            return res
        por_xid = {}
        for f in facturas:
            por_xid.setdefault(str(f.get("XeroInvoiceID")).strip(), f)
        ids = sorted(por_xid)
        vistos, cambios = {}, {}
        for i in range(0, len(ids), _POR_CONSULTA):
            trozo = ids[i:i + _POR_CONSULTA]
            status, js, _h = _api(grupo, "GET", "/Invoices", params={"IDs": ",".join(trozo)})
            if status != 200:
                res["errores"].append("; ".join(mensajes_error(js)) or f"HTTP {status}")
                continue
            for inv in (js or {}).get("Invoices") or []:
                xid = str(inv.get("InvoiceID", "") or "")
                f = por_xid.get(xid)
                if not f:
                    continue
                vistos[xid] = True
                numero = str(f.get("Number", ""))
                est = str(inv.get("Status", "")).upper()
                if est in _SIN_COBRO:
                    res["en_borrador"].append((f.get("ID"), numero))
                    continue
                if est in _MUERTAS or est not in _COBRABLES:
                    res["muertas"].append((f.get("ID"), numero, est))
                    continue
                pagado = round(_num(inv.get("AmountPaid")), 2)
                credito = round(_num(inv.get("AmountCredited")), 2)
                if credito > 0:
                    res["con_credito"].append((f.get("ID"), numero, credito))
                fecha = de_fecha(inv.get("FullyPaidOnDate")) or clock.today()
                cambios[str(f.get("ID"))] = {"cobrado": pagado, "fecha": fecha.isoformat()}
        for xid, f in por_xid.items():
            if xid not in vistos and not res["errores"]:
                res["no_encontradas"].append((f.get("ID"), str(f.get("Number", ""))))
        if cambios:
            ok, r = invoices.sincronizar_cobros(cambios, clock.today().isoformat())
            if not ok:
                res["errores"].append(str(r))
            else:
                num = {str(f.get("ID")): str(f.get("Number", "")) for f in facturas}
                res["actualizadas"] = [(fid, num.get(fid, fid), antes, ahora)
                                       for fid, antes, ahora in r["cambiadas"]]
                res["iguales"] = [(fid, num.get(fid, fid)) for fid in r["iguales"]]
    return res
'''
assert "def traer_cobros" not in s
s = s.rstrip("\n") + "\n" + NUEVO
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("xero.traer_cobros añadida")

# ── xero_nomina delega en el parser de xero (una sola definición) ──
Q = "core/xero_nomina.py"
sn = io.open(Q, encoding="utf-8").read()
VIEJO = '''def de_ms(valor):
    """`/Date(ms+0000)/` o `YYYY-MM-DD` → date (o None). Xero devuelve el primero."""
    m = _RE_MS.search(str(valor or ""))
    if m:
        return _dt.datetime.fromtimestamp(int(m.group(1)) / 1000, _dt.timezone.utc).date()
    return _parse_date(valor)
'''
assert sn.count(VIEJO) == 1
NUEVODE = '''def de_ms(valor):
    """`/Date(ms+0000)/` o `YYYY-MM-DD` → date (o None).

    ⚠️ Delega en `xero.de_fecha`: al traer el cobrado de una factura (v495) hacía falta
    el mismo parser, y dos copias de la misma fecha divergen (v323).
    """
    return X.de_fecha(valor)
'''
sn = sn.replace(VIEJO, NUEVODE)
io.open(Q, "w", encoding="utf-8", newline="").write(sn)
print("xero_nomina.de_ms delega en xero.de_fecha")
