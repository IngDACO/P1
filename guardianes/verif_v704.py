# -*- coding: utf-8 -*-
"""v704 · ciclo 7, mejoras 4/4: Xero (H21 y D4) y lo visto midiendo v703 (V1–V3).

H21 cuando Xero ya no acepta la organización (la demo se reinicia cada 28 días): la conexión queda «reconnect», con
    la causa en palabras y «Reconnect to Xero»; la nómina dice la MISMA causa, y un 404 de Payroll dice que no hay
    Payroll AU (antes, «Try in a minute»).
D4 «Mandar los cobros también»: la cuenta del banco de Xero se elige una vez; al enviar una factura APROBADA van sus
    cobros (en borrador se dice, y van después); al traer, Xero con menos NO baja un cobro de COPEX: se ofrece mandarlo
    o, confirmado, quedarse la cifra de Xero.
V1 «Job restarted.» dice los días que HAY en el tablero · V2 el neto de una certificación anulada con su depósito ·
V3 la vista previa de la nómina avisa del solape con una colilla ya emitida.

Sin red ni escrituras: Xero, la hoja y lo demás, sustituidos; lo sustituido se guarda al principio y se devuelve
(trampa 48).
"""
import ast
import io
import json
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def fuente(rel):
    return open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(src, nombre):
    return next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


import streamlit                                                               # noqa: E402
from streamlit.testing.v1 import AppTest                                      # noqa: E402
from core import (xero as X, xero_nomina as XN, xero_ui as XU, invoices as I, contable, claims as CL,  # noqa: E402
                  payroll, roster, clock)

_G = {}


def guarda(mod, *nombres):
    for n in nombres:
        _G[(mod, n)] = getattr(mod, n)


def devuelve():
    for (mod, n), f in _G.items():
        setattr(mod, n, f)


guarda(X, "_http", "_token", "_marcar_estado", "_ws", "_leer", "_estados_cached", "configuracion", "_api",
       "cuenta_banco", "cuentas_banco", "mandar_cobros", "aceptar_cifra_xero", "url_autorizacion", "estado",
       "_espera_cupo", "_invalida", "_leer_facturas_xero")
guarda(I, "list_facturas", "get_factura", "sincronizar_cobros", "_ws", "_invalidate")
guarda(contable, "mapa", "guardar_claves")
guarda(CL, "_facturas_vivas")
guarda(payroll, "list_nominas")
guarda(roster, "dias_desde")


class R:
    def __init__(self, status, js=None):
        self.status_code, self._js, self.headers = status, js, {}

    def json(self):
        if self._js is None:
            raise ValueError("sin json")
        return self._js


TOK = {"access": "acc-1", "tenant_id": "TEN-1", "short_code": "!x"}
AV = X.aviso_reconectar()
try:
    print("A. H21: cuando Xero ya no acepta la organización")
    X._espera_cupo = lambda *a, **k: 0
    for (st_, js), esperado in (((200, [{"tenantId": "TEN-1"}]), True), ((200, [{"tenantId": "OTRA"}]), False),
                                ((401, {}), False), ((500, {}), None)):
        X._http = lambda m, u, _s=st_, _j=js, **k: R(_s, _j)
        chk(f"¿sigue la organización? /Connections {st_} {js} → {esperado}", X._organizacion_sigue(TOK) is esperado)

    _marcas, _llam = [], []

    def _monta(respuestas, conexiones):
        _marcas.clear()
        _llam.clear()
        seq = list(respuestas)
        X._token = lambda g, forzar=False: (True, dict(TOK))
        X._marcar_estado = lambda g, e: _marcas.append((g, e))

        def _h(m, u, **k):
            _llam.append((m, u))
            if u == X.CONNECTIONS_URL:
                return R(200, conexiones)
            return seq.pop(0)
        X._http = _h

    _monta([R(401, {"Title": "Unauthorized"}), R(401, {"Detail": "AuthenticationUnsuccessful"})], [])
    st_, js, _h = X._api("cliente1", "GET", "/Invoices")
    chk("401 con el acceso RENOVADO y la organización fuera → «reconnect» y el aviso en palabras",
        st_ == 0 and js.get("_reconectar") is True and js.get("Message") == AV
        and _marcas == [("cliente1", X.RECONECTAR)], (st_, js, _marcas))
    chk("…y el aviso dice la causa (demo cada 28 días) y qué hacer", "28 days" in AV and "Reconnect" in AV, AV)
    _monta([R(401, {}), R(401, {"Detail": "AuthenticationUnsuccessful"})], [{"tenantId": "TEN-1"}])
    st_, js, _h = X._api("cliente1", "GET", "/Invoices")
    chk("401 pero la organización SIGUE conectada: no se marca (es otra cosa), vuelve lo de Xero",
        st_ == 401 and not _marcas and js.get("Detail") == "AuthenticationUnsuccessful", (st_, js, _marcas))
    _monta([R(401, {}), R(200, {"Invoices": []})], [])
    st_, js, _h = X._api("cliente1", "GET", "/Invoices")
    chk("un 401 que se arregla renovando: nada que marcar", st_ == 200 and not _marcas and
        X.CONNECTIONS_URL not in [u for _m, u in _llam], (st_, _llam))
    _monta([R(403, {"Title": "Forbidden"})], [])
    st_, js, _h = X._api("cliente1", "GET", "/Employees", base=X.PAYROLL_URL)
    chk("403 y la organización fuera → «reconnect» también", st_ == 0 and _marcas == [("cliente1", X.RECONECTAR)])
    _monta([R(403, {"Title": "Forbidden"})], [{"tenantId": "TEN-1"}])
    st_, js, _h = X._api("cliente1", "GET", "/Employees", base=X.PAYROLL_URL)
    chk("403 con la organización conectada (un permiso, p. ej. la nómina): no se marca", st_ == 403 and not _marcas)

    devuelve()
    X._ws = lambda crear=True: object()
    X._leer = lambda ws: (["Group"], [(2, {"Group": "cliente1", "TokenEnc": "x", "TenantID": "TEN-1",
                                           "Status": X.RECONECTAR})])
    X._VIVOS.pop("cliente1", None)
    ok_t, m_t = X._token("cliente1")
    chk("marcada «reconnect», `_token` no la usa (renovar la volvería a poner «connected»)", not ok_t and m_t == AV,
        (ok_t, m_t))
    X.configuracion = lambda: {"ok": True, "faltan": [], "problemas": [], "redirect": "https://x/"}
    X._estados_cached = lambda libro: [{"Group": "cliente1", "Status": X.RECONECTAR, "TenantName": "Demo",
                                        "_con_token": True}]
    import core.timeclock as _TC
    _sid = _TC.sheet_id_para
    _TC.sheet_id_para = lambda h: "LIBRO"
    try:
        e_ = X.estado("cliente1")
    finally:
        _TC.sheet_id_para = _sid
    chk("estado(): «reconnect» no está conectada", e_["conectada"] is False and e_["estado"] == X.RECONECTAR, e_)

    PANT = r'''
import streamlit as st
from core import xero_ui as XU, xero as X
X.configuracion = lambda: {"ok": True, "faltan": [], "problemas": [], "redirect": "https://x/"}
X.estado = lambda g: {"conectada": False, "estado": st.session_state["_EST"], "tenant": "Demo", "tenant_id": "",
                      "short_code": "", "por": "", "desde": ""}
X.url_autorizacion = lambda g, u: "https://login.xero.com/x"
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G"})
XU.render_conexion("G")
'''
    for est_, lab in ((X.RECONECTAR, "Reconnect to Xero"), (X.CADUCADA, "Connect to Xero"), ("", "Connect to Xero")):
        a = AppTest.from_string(PANT, default_timeout=60)
        a.session_state["_EST"] = est_
        a.run()
        _w = " ".join(str(w.value) for w in a.warning)
        _lb = [str(getattr(b, "label", "")) for b in a.get("link_button")]
        chk(f"pantalla con estado «{est_ or 'sin conectar'}»: botón «{lab}»"
            + (" y la causa en el aviso" if est_ == X.RECONECTAR else ""),
            not a.exception and any(lab in x for x in _lb)
            and (("no longer accepts" in _w) if est_ == X.RECONECTAR else ("no longer accepts" not in _w)),
            (_lb, _w, [e.value for e in a.exception][:1]))
    devuelve()

    print("\nB. H21: la nómina de Xero dice la misma causa, y el 404")
    X._api = lambda g, m, r, **k: (0, {"Message": AV, "_reconectar": True}, {})
    d = XN.datos("cliente1")
    chk("organización fuera: la nómina dice LO MISMO que el resto", d["error"] == AV, d["error"])
    X._api = lambda g, m, r, **k: (404, {}, {})
    d = XN.datos("cliente1")
    chk("404: «no Payroll AU… waiting does not change that» (era «Try… in a minute»)",
        "no Payroll AU" in d["error"] and "waiting does not change that" in d["error"] and "in a minute" not in d["error"],
        d["error"])
    X._api = lambda g, m, r, **k: (401, {"Detail": "AuthenticationUnsuccessful"}, {})
    d = XN.datos("cliente1")
    chk("401 con la organización conectada: el aviso de siempre (permiso de nómina)", "Payroll AU" in d["error"]
        and "whoever connected" in d["error"], d["error"])
    devuelve()

    print("\nC. D4: qué pagos manda COPEX (cobros_para_xero)")
    f1 = {"ID": "FAC-0007", "Number": "0007", "Collected": "10050", "CollectionDate": "2026-11-23",
          "CollectionsJSON": json.dumps([{"fecha": "2026-11-23", "monto": 10050}])}
    chk("Xero a 0: su cobro con SU fecha", X.cobros_para_xero(f1, 0) == [{"fecha": "2026-11-23", "monto": 10050.0}],
        X.cobros_para_xero(f1, 0))
    f2 = dict(f1, CollectionsJSON=json.dumps([{"fecha": "2026-11-20", "monto": 5000}, {"fecha": "2026-11-23",
                                                                                         "monto": 5050}]))
    chk("dos cobros, dos pagos (el contable los casa con el banco)", X.cobros_para_xero(f2, 0) == [
        {"fecha": "2026-11-20", "monto": 5000.0}, {"fecha": "2026-11-23", "monto": 5050.0}], X.cobros_para_xero(f2, 0))
    chk("Xero ya tiene $3,000: UNO por la diferencia ($7,050), con la fecha del último",
        X.cobros_para_xero(f2, 3000) == [{"fecha": "2026-11-23", "monto": 7050.0}], X.cobros_para_xero(f2, 3000))
    # un historial que SUMA lo cobrado contando un movimiento que vino de Xero: ese no se reenvía con su fecha
    # (romper_v704 escapó con un caso donde daba igual: aquí, con el filtro, uno por la diferencia; sin él, dos)
    f3 = dict(f1, Collected="1300", CollectionDate="2026-11-21",
              CollectionsJSON=json.dumps([{"fecha": "2026-11-20", "monto": 900, "origen": "xero"},
                                          {"fecha": "2026-11-21", "monto": 400}]))
    chk("lo que vino DE Xero no vuelve con su fecha: uno por la diferencia ($1,300 el 21/11)",
        X.cobros_para_xero(f3, 0) == [{"fecha": "2026-11-21", "monto": 1300.0}], X.cobros_para_xero(f3, 0))
    chk("Xero con lo mismo o más: nada", X.cobros_para_xero(f1, 10050) == [] and X.cobros_para_xero(f1, 11000) == [])

    print("\nD. D4: mandar los cobros (mandar_cobros)")
    _put = []
    _xinv = {"X7": {"InvoiceID": "X7", "Status": "AUTHORISED", "AmountPaid": 0}}

    def _api_pagos(g, m, ruta, *, params=None, cuerpo=None, cabeceras=None, base=None):
        if m == "GET" and ruta == "/Invoices":
            ids = set((params or {}).get("IDs", "").split(","))
            return 200, {"Invoices": [v for k, v in _xinv.items() if k in ids]}, {}
        if m == "PUT" and ruta == "/Payments":
            _put.append(cuerpo)
            return 200, {"Payments": [{"PaymentID": f"P{i}"} for i, _p in enumerate(cuerpo["Payments"])]}, {}
        return 500, {}, {}

    X._api = _api_pagos
    I.list_facturas = lambda g=None, cliente_id=None: [dict(f1, Group="cliente1", XeroInvoiceID="X7",
                                                            Status="emitida")]
    X.cuenta_banco = lambda g: {"id": "BANK-1", "codigo": "090", "nombre": "Business Bank Account"}
    rc = X.mandar_cobros("cliente1", ["FAC-0007"])
    _p = (_put[0]["Payments"] if _put else [{}])[0]
    chk("la 0007 aprobada en Xero: un PUT /Payments con su factura, la cuenta elegida, la fecha y el importe",
        rc["mandados"] == [("FAC-0007", "0007", 10050.0)] and _p.get("Invoice") == {"InvoiceID": "X7"}
        and _p.get("Account") == {"AccountID": "BANK-1"} and _p.get("Date") == "2026-11-23"
        and _p.get("Amount") == 10050.0 and _p.get("Reference") == "COPEX 0007", (rc, _put))
    _put.clear()
    _xinv["X7"]["AmountPaid"] = 10050
    rc = X.mandar_cobros("cliente1", ["FAC-0007"])
    chk("…otra vez, con Xero ya al día: no manda nada (no cobra dos veces) y lo dice", not _put
        and not rc["mandados"] and rc["avisos"], rc)
    _xinv["X7"].update(Status="DRAFT", AmountPaid=0)
    rc = X.mandar_cobros("cliente1", ["FAC-0007"])
    chk("en BORRADOR en Xero: no se manda («only to an approved invoice»)", not _put and rc["errores"]
        and "approved" in rc["errores"][0][2][0], rc)
    _xinv["X7"].update(Status="AUTHORISED")

    def _api_rechaza(g, m, ruta, *, params=None, cuerpo=None, cabeceras=None, base=None):
        if m == "PUT":
            return 400, {"Payments": [{"PaymentID": "00000000-0000-0000-0000-000000000000",
                                       "ValidationErrors": [{"Message": "Payment amount exceeds the amount due"}]}]}, {}
        return _api_pagos(g, m, ruta, params=params, cuerpo=cuerpo)
    X._api = _api_rechaza
    rc = X.mandar_cobros("cliente1", ["FAC-0007"])
    chk("Xero lo rechaza: el error de Xero, sin darlo por mandado", not rc["mandados"]
        and "exceeds" in " ".join(rc["errores"][0][2]), rc)
    X._api = _api_pagos
    X.cuenta_banco = lambda g: {}
    _llamo = []
    X._api = lambda *a, **k: (_llamo.append(a), (500, {}, {}))[1]
    rc = X.mandar_cobros("cliente1", ["FAC-0007"])
    chk("sin la cuenta del banco elegida: no llama a Xero y dice dónde elegirla", not _llamo and rc["avisos"]
        and "bank account" in rc["avisos"][0], rc)

    print("\nE. D4: al enviar la factura (_cobros_al_enviar)")
    I.get_factura = lambda fid: dict(f1)
    res = {"avisos": [], "errores": [], "cobros": []}
    X._cobros_al_enviar("cliente1", {"FAC-0007": "X7"}, X.BORRADOR, res)
    chk("en borrador: se dice (con lo cobrado) que irá desde «Bring payments»", len(res["avisos"]) == 1
        and "draft" in res["avisos"][0] and "10,050.00" in res["avisos"][0] and "Bring payments" in res["avisos"][0],
        res)
    res = {"avisos": [], "errores": [], "cobros": []}
    X.cuenta_banco = lambda g: {}
    X._cobros_al_enviar("cliente1", {"FAC-0007": "X7"}, X.APROBADA, res)
    chk("aprobada sin cuenta del banco: se dice dónde elegirla", res["avisos"] and "bank account" in res["avisos"][0],
        res)
    res = {"avisos": [], "errores": [], "cobros": []}
    X.cuenta_banco = lambda g: {"id": "BANK-1"}
    X.mandar_cobros = lambda g, fids: {"mandados": [(fids[0], "0007", 10050.0)], "errores": [], "avisos": []}
    X._cobros_al_enviar("cliente1", {"FAC-0007": "X7"}, X.APROBADA, res)
    chk("aprobada con cuenta: manda los cobros", res["cobros"] == [("FAC-0007", "0007", 10050.0)], res)
    res = {"avisos": [], "errores": [], "cobros": []}
    I.get_factura = lambda fid: dict(f1, Collected="0")
    X._cobros_al_enviar("cliente1", {"FAC-0007": "X7"}, X.APROBADA, res)
    chk("sin nada cobrado: ni aviso ni envío", res == {"avisos": [], "errores": [], "cobros": []}, res)
    _ef = funcion(fuente("core/xero.py"), "enviar_facturas")
    chk("enviar_facturas lo llama tras marcar las facturas", "_cobros_al_enviar(grupo, marcas, estado_xero, res)"
        in ast.unparse(_ef))
    devuelve()

    print("\nF. D4: traer cobros NO baja sin confirmar")
    CAB = ["ID", "Group", "ClientID", "ClientName", "Number", "Date", "ExpiryDate", "LinesJSON", "Subtotal", "TaxPct",
           "Tax", "Total", "Collected", "CollectionDate", "Status", "Note", "CreatedBy", "Created", "CollectionsJSON",
           "XeroInvoiceID", "XeroSentAt"]

    class WS:
        def __init__(self, filas):
            self.filas = [list(CAB)] + [[f.get(c, "") for c in CAB] for f in filas]
            self.escrituras = []

        def get_all_values(self):
            return [list(r) for r in self.filas]

        def batch_update(self, rangos, value_input_option=None):
            import re as _re
            self.escrituras.append(rangos)
            for r_ in rangos:
                m_ = _re.match(r"([A-Z]+)(\d+)", r_["range"])
                col = 0
                for ch in m_.group(1):
                    col = col * 26 + (ord(ch) - 64)
                self.filas[int(m_.group(2)) - 1][col - 1] = r_["values"][0][0]

    ws = WS([{"ID": "FAC-0007", "Group": "cliente1", "Number": "0007", "Total": "22892.76", "Collected": "10050",
              "XeroInvoiceID": "X7", "Status": "emitida", "CollectionsJSON": "[]"}])
    I._ws = lambda: (ws, "")
    I._invalidate = lambda: None
    # la caché dice 0 (vieja); la hoja fresca, 10050: la lectura FRESCA manda
    I.list_facturas = lambda g=None, cliente_id=None: [{"ID": "FAC-0007", "Group": "cliente1", "Number": "0007",
                                                        "Collected": "0", "XeroInvoiceID": "X7", "Status": "emitida"}]
    X._api = lambda g, m, r, *, params=None, **k: (200, {"Invoices": [{"InvoiceID": "X7", "Status": "AUTHORISED",
                                                                       "AmountPaid": 2000, "AmountCredited": 0}]}, {})
    r = X.traer_cobros("cliente1")
    chk("Xero $2,000 y COPEX $10,050 (aunque la caché diga 0): no se baja, va a «por_mandar»",
        r["por_mandar"] == [("FAC-0007", "0007", 10050.0, 2000.0)] and not ws.escrituras and not r["actualizadas"],
        (r, ws.escrituras))
    # ⚠️ la protección de `traer_cobros`, por el camino donde es la ÚNICA (trampa 55): con la caché al día, la bajada
    # ni siquiera se le pasa a `sincronizar_cobros` (romper_v704 escapó: la de `sincronizar_cobros` la tapaba)
    I.list_facturas = lambda g=None, cliente_id=None: [{"ID": "FAC-0007", "Group": "cliente1", "Number": "0007",
                                                        "Collected": "10050", "XeroInvoiceID": "X7",
                                                        "Status": "emitida"}]
    _pasado = []
    I.sincronizar_cobros = lambda c, cuando, bajar=None: (_pasado.append(dict(c)),
                                                          (True, {"cambiadas": [], "iguales": [], "no_bajadas": []}))[1]
    r = X.traer_cobros("cliente1")
    chk("…y con la caché al día, `traer_cobros` NO le pasa la bajada a `sincronizar_cobros`",
        r["por_mandar"] == [("FAC-0007", "0007", 10050.0, 2000.0)] and not any("FAC-0007" in c for c in _pasado),
        (r["por_mandar"], _pasado))
    I.sincronizar_cobros = _G[(I, "sincronizar_cobros")]
    _ok, _r = I.sincronizar_cobros({"FAC-0007": {"cobrado": 2000, "fecha": "2026-11-23"}}, "2026-11-23")
    chk("sincronizar_cobros sin `bajar`: tampoco baja", _ok and _r["no_bajadas"] == [("FAC-0007", 10050.0, 2000.0)]
        and not ws.escrituras, _r)
    I.get_factura = lambda fid: {"ID": "FAC-0007", "Group": "cliente1", "Number": "0007", "XeroInvoiceID": "X7"}
    _bajadas = []
    _sinc = _G[(I, "sincronizar_cobros")]
    I.sincronizar_cobros = lambda c, cuando, bajar=None: (_bajadas.append((c, bajar)), _sinc(c, cuando, bajar=bajar))[1]
    ok_a, m_a = X.aceptar_cifra_xero("cliente1", "FAC-0007")
    chk("«Use Xero's figure» (confirmado): baja SOLO esa factura, con `bajar`", ok_a and _bajadas
        and _bajadas[0][1] == {"FAC-0007"} and ws.filas[1][CAB.index("Collected")] == "2000.0" and "2,000.00" in m_a,
        (ok_a, m_a, _bajadas))
    devuelve()

    print("\nG. D4: la pantalla (cuenta del banco y lo que falta en Xero)")
    PM = r'''
import streamlit as st
from core import xero_ui as XU, xero as X, contable
X.cuenta_banco = lambda g: st.session_state.get("_CB") or {}
X.cuentas_banco = lambda g: ([{"id": "BANK-1", "codigo": "090", "nombre": "Business Bank Account"}], "")
X.mandar_cobros = lambda g, fids: (st.session_state.setdefault("_MANDA", []).append(list(fids)),
                                   {"mandados": [("FAC-0007", "0007", 10050.0)], "errores": [], "avisos": []})[1]
X.aceptar_cifra_xero = lambda g, fid: (st.session_state.setdefault("_ACEPTA", []).append(fid), (True, "ok"))[1]
contable.guardar_claves = lambda g, c: (st.session_state.setdefault("_GUARDA", []).append(c), (True, "ok"))[1]
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G"})
XU._cuenta_banco_section("G")
XU._por_mandar_section("G")
'''
    a = AppTest.from_string(PM, default_timeout=60)
    a.session_state["_xero_por_mandar"] = [("FAC-0007", "0007", 10050.0, 0.0)]
    a.run()
    _w = " ".join(str(w.value) for w in a.warning).replace("\\", "")
    _b = {str(b.key): b for b in a.button}
    chk("lo que falta en Xero: «Collected in COPEX but not in Xero» con las dos cifras",
        "Collected in COPEX but not in Xero" in _w and "Invoice 0007: COPEX $10,050.00 · Xero $0.00" in _w, _w)
    chk("…sin cuenta del banco, «Send these payments» parado y dice por qué",
        _b["xero_pm_mandar"].disabled and any("bank account above" in str(c.value) for c in a.caption))
    a.button(key="xero_cb_leer").click()
    a.run()
    a.selectbox(key="xero_cb_sel").set_value("BANK-1")
    a.run()
    a.button(key="xero_cb_ok").click()
    a.run()
    _gu = a.session_state["_GUARDA"] if "_GUARDA" in a.session_state else []
    chk("elegir la cuenta: se lee de Xero y se guarda UNA vez en los ajustes contables",
        _gu == [{"xero_cuenta_banco": {"id": "BANK-1", "codigo": "090", "nombre": "Business Bank Account"}}], _gu)
    a.session_state["_CB"] = {"id": "BANK-1", "codigo": "090", "nombre": "Business Bank Account"}
    a.run()
    chk("…y dice adónde van («go to «Business Bank Account» in Xero»)",
        any("Business Bank Account" in str(c.value) for c in a.caption))
    a.button(key="xero_pm_mandar").click()
    a.run()
    chk("con cuenta, «Send these payments to Xero (1)» los manda y el bloque se va",
        (a.session_state["_MANDA"] if "_MANDA" in a.session_state else []) == [["FAC-0007"]]
        and "_xero_por_mandar" not in a.session_state)
    a.session_state["_xero_por_mandar"] = [("FAC-0007", "0007", 10050.0, 0.0)]
    a.run()
    a.button(key="xero_pm_x_FAC-0007").click()
    a.run()
    _w2 = " ".join(str(w.value) for w in a.warning).replace("\\", "")
    chk("«Use Xero's figure» PREGUNTA antes («Set invoice 0007 to $0.00 collected…»)",
        "Set invoice 0007 to $0.00 collected, as in Xero?" in _w2
        and not (a.session_state["_ACEPTA"] if "_ACEPTA" in a.session_state else []), _w2)
    a.button(key="xero_pm_si_FAC-0007").click()
    a.run()
    chk("…y solo con «Yes» la baja", (a.session_state["_ACEPTA"] if "_ACEPTA" in a.session_state else [])
        == ["FAC-0007"])
    _rc = ast.unparse(funcion(fuente("core/xero_ui.py"), "render_conexion"))
    chk("Accounting pinta la cuenta del banco y lo que falta, y guarda lo que trajo «Bring payments»",
        "_cuenta_banco_section(grupo)" in _rc and "_por_mandar_section(grupo)" in _rc
        and "st.session_state['_xero_por_mandar'] = list(res.get('por_mandar') or [])" in _rc)
    chk("al enviar, «… collected in COPEX sent to Xero.»", "collected in COPEX sent to Xero" in
        fuente("core/xero_ui.py"))

    print("\nH. V1: «Job restarted.» con los días del tablero de verdad")
    V1 = r'''
import streamlit as st
from core import projects_ui as PU, roster
roster.dias_desde = lambda g, pid, desde: st.session_state["_TAB"]
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G"})
PU._aviso_reanudada("PRJ-T", {"n": 1, "nuevos": 0, "avisados": ""}, "G")
'''
    for tab, txt in (({"campo000": 8}, "8 day(s) on the board for it from today"),
                     ({}, "Nobody is on the board for it from today")):
        a = AppTest.from_string(V1, default_timeout=60)
        a.session_state["_TAB"] = tab
        a.run()
        _c = " ".join(str(c.value) for c in a.caption)
        chk(f"tablero {tab or 'vacío'} → «{txt}» (y nunca «took the crew off the board»)",
            txt in _c and "took the crew off" not in _c, _c)

    print("\nI. V2: una certificación anulada, con su depósito")
    _anul = {"ID": "FAC-0009", "Number": "0009", "Status": "anulada", "Subtotal": "5214.75",
             "LinesJSON": json.dumps([{"concepto": "Progress claim #2", "importe": 7811.35,
                                       "reclamacion": "CLM-PRJ-0048-002"}])}
    I.list_facturas = lambda g=None, cliente_id=None: [_anul]
    CL._facturas_vivas = lambda g: []
    chk("factura_de: sin `incluir_anuladas`, la anulada no sale", CL.factura_de("CLM-PRJ-0048-002", "cliente1") == {})
    chk("…con él, sí", CL.factura_de("CLM-PRJ-0048-002", "cliente1", incluir_anuladas=True).get("Number") == "0009")
    _cu = ast.unparse(funcion(fuente("core/claims_ui.py"), "render"))
    chk("la lista la usa en las ANULADAS y resta el depósito («_linea_claim(r, _neto - _dep_a, _dep_a)»)",
        "factura_de(r.get('ID'), grupo, incluir_anuladas=True)" in _cu and "_linea_claim(r, _neto - _dep_a, _dep_a)"
        in _cu, "")
    devuelve()

    print("\nJ. V3: la vista previa de la nómina y el solape")
    payroll.list_nominas = lambda g=None, usuario=None, incluir_anuladas=False: [
        {"ID": "NOM-0006", "User": "campo000", "Name": "hjg,ujgjg", "PeriodFrom": "2026-11-17", "PeriodTo": "2026-11-22"},
        {"ID": "NOM-0009", "User": "otro", "Name": "Otro", "PeriodFrom": "2026-11-16", "PeriodTo": "2026-11-22"}]
    s_ = payroll.solapes_de("cliente1", "2026-11-16", "2026-11-22")
    chk("16/11–22/11 solapa con la NOM-0006 (17/11–22/11); la del MISMO periodo no es solape",
        list(s_) == ["campo000"] and s_["campo000"][0]["id"] == "NOM-0006", s_)
    chk("…y 23/11–29/11 no solapa con nada", payroll.solapes_de("cliente1", "2026-11-23", "2026-11-29") == {})
    chk("generar usa la MISMA función", "solapes_de(grupo, d_iso, h_iso)" in ast.unparse(
        funcion(fuente("core/payroll.py"), "generar")))
    _pu = fuente("core/payroll_ui.py")
    chk("la vista previa lo dice en la nota («Overlaps {n} ({d} → {a}): it will be skipped»)",
        "payroll.solapes_de(grupo, desde.isoformat(), hasta.isoformat())" in _pu
        and "Overlaps {n} ({d} → {a}): it will be skipped" in _pu)
finally:
    devuelve()
    streamlit.cache_data.clear()

print("\nK. Compila")
import py_compile                                                              # noqa: E402
for f in ("core/xero.py", "core/xero_ui.py", "core/xero_nomina.py", "core/invoices.py", "core/claims.py",
          "core/claims_ui.py", "core/projects_ui.py", "core/payroll.py", "core/payroll_ui.py"):
    try:
        py_compile.compile(os.path.join(RAIZ, f), doraise=True)
        ok = True
    except Exception as e:
        ok = False
        print(e)
    chk("compila " + f, ok)

print()
print("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}")
sys.exit(1 if FALLOS else 0)
