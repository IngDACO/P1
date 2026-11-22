# -*- coding: utf-8 -*-
"""v689 · Ciclo 5 → mejoras 1/4, las COTIZACIONES (17/11):
- H3/H3b · un número de cotización es UN trato: las cifras cuentan su versión vigente (`representante`) y las
  anteriores dicen «Superseded»; la 0007 sumaba en la calle sus versiones viejas, la 0008 salía ganada dos veces y
  rechazar la v3 de un trato ganado bajaba la conversión;
- D1 · aceptar una versión de un trato que ya tiene obra es una VARIACIÓN: actualiza esa obra (precio y presupuesto =
  su costo cotizado) y nunca crea otra (la v3 ofrecía «Turn it into a project» con PRJ-0046 viva);
- H16 · «They rejected it» pide el motivo (`RejectReason`), y la lista de perdidas lo cuenta;
- H6 · «Back to quotes» con cambios sin guardar pregunta (Save / Discard / Stay);
- H4 · «New quote» sin cliente preseleccionado;
- H5 · junto al PDF, el aviso de que sale con el identificador interno si la empresa no tiene razón social;
- H21 · la campana avisa de las cotizaciones sin respuesta a punto de vencer o vencidas hace poco.

Nada sale a la red ni escribe: funciones reales con sustitutos (una hoja FALSA que apunta lo escrito) y AppTest.
"""
import json
import os
import sys
from datetime import date

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import quotes as Q                                               # noqa: E402
from core import projects as P                                             # noqa: E402
from core import auditoria                                                 # noqa: E402
from core import clock                                                     # noqa: E402

HOY = date(2026, 11, 17)
_L = [{"catalogo_id": "CAT-1", "tipo": "product", "concepto": "Panel", "cantidad": 12.0, "horas": 0,
       "costo_unit": 320.0, "costo_total": 3840.0, "margen_pct": 20.0, "precio_total": 4608.0}]


def _q(cid, num, ver, st, tot, pid="", valid="2026-12-17", reason="", grupo="G"):
    return {"ID": cid, "Group": grupo, "ClientID": "CLI-1", "ClientName": "C5 — Bayview", "Number": num,
            "Date": "2026-11-10", "ValidUntil": valid, "LinesJSON": json.dumps(_L), "Subtotal": "4608.0",
            "TaxPct": "10", "Tax": "460.8", "Total": str(tot), "MarginPct": "20", "Status": st, "ProjectID": pid,
            "Version": str(ver), "Source": "", "Note": "", "CreatedBy": "x", "Created": "2026-11-10 10:00",
            "DrawingJSON": "", "RejectReason": reason}


DATOS = [
    # 0007: v1 y v2 enviadas, v3 ACEPTADA con obra, v4 enviada después (una variación pendiente)
    _q("C71", "0007", 1, "sent", 64878.0), _q("C72", "0007", 2, "sent", 64878.0),
    _q("C73", "0007", 3, "accepted", 62760.5, pid="PRJ-A"), _q("C74", "0007", 4, "sent", 57055.0),
    # 0008: v1 enviada, v2 ACEPTADA con obra, v3 rechazada (el caso del ciclo 5)
    _q("C81", "0008", 1, "sent", 12170.4), _q("C82", "0008", 2, "accepted", 12170.4, pid="PRJ-B"),
    _q("C83", "0008", 3, "rejected", 12170.4, reason="scope"),
    # 0003: enviada, le quedan 5 días · 0009: rechazada por precio · 0010: v1 enviada + v2 en borrador
    _q("C31", "0003", 1, "sent", 2858.0, valid="2026-11-22"),
    _q("C91", "0009", 1, "rejected", 5000.0, reason="price — their budget was 4000"),
    _q("C101", "0010", 1, "sent", 1000.0, valid="2026-11-14"), _q("C102", "0010", 2, "draft", 1100.0),
    # 0011: la v1 VENCIDA ya sustituida por la v2 enviada · 0012: vencida hace 47 días (fuera de la campana)
    _q("C111", "0011", 1, "sent", 500.0, valid="2026-11-01"), _q("C112", "0011", 2, "sent", 600.0),
    _q("C121", "0012", 1, "sent", 700.0, valid="2026-10-01"),
    # de OTRA empresa: no entra en nada de G
    _q("X1", "0001", 1, "sent", 99999.0, grupo="OTRA"),
]
_OBRAS = {"PRJ-A": {"ID": "PRJ-A", "Name": "C2 — Coastal"}, "PRJ-B": {"ID": "PRJ-B", "Name": "C5 — Bayview — Lift 1"}}

_d = [_sustituir(Q, _records=lambda: [dict(x) for x in DATOS]),
      _sustituir(P, get_project=lambda pid: dict(_OBRAS[pid]) if pid in _OBRAS else {}),
      _sustituir(clock, today=lambda *a, **k: HOY)]
try:
    print("1. Las versiones de un trato: el estado que se ENSEÑA (H3)")
    _vis = Q.vistas([x for x in DATOS if x["Group"] == "G"])
    chk("0007 v1 y v2 «superseded», v3 accepted, v4 —la variación posterior— sigue «sent»",
        [_vis[k] for k in ("C71", "C72", "C73", "C74")] == [Q.SUSTITUIDA, Q.SUSTITUIDA, "accepted", "sent"], _vis)
    chk("0008 v1 «superseded», v2 accepted, v3 rechazada (la variación rechazada dice lo suyo)",
        [_vis[k] for k in ("C81", "C82", "C83")] == [Q.SUSTITUIDA, "accepted", "rejected"], _vis)
    chk("0010: la v1 enviada (vencida) habla por el trato; la v2 es un borrador",
        _vis["C101"] == Q.VENCIDA and _vis["C102"] == "draft", _vis)
    chk("0011: la v1 vencida pero sustituida dice «superseded», no «expired»; la v2 «sent»",
        _vis["C111"] == Q.SUSTITUIDA and _vis["C112"] == "sent", _vis)
    chk("vista() de una sola mira a sus hermanas: C81 superseded, C31 sent",
        Q.vista(dict(DATOS[4])) == Q.SUSTITUIDA and Q.vista(dict(DATOS[7])) == "sent")

    print("2. Las cifras, por TRATO (H3)")
    Q.resumen.clear()
    _r = Q.resumen("G")
    chk("«Out with clients» = 0003 + 0010 v1 + 0011 v2 + 0012 = 5.158 (contaba además 0007 v1, v2, v4, la 0008 v1 y "
        "la 0011 v1: 203.340 más)", abs(_r["en_calle"] - 5158.0) < 0.01, _r)
    chk("«Won» = 0007 v3 + 0008 v2 = 74.930,9 (una vez cada trato)", abs(_r["ganado"] - 74930.9) < 0.01, _r)
    chk("aceptados 2, rechazados 1 (la 0009; la v3 rechazada de la 0008 NO cuenta como trato perdido)",
        _r["por_estado"].get("accepted") == 2 and _r["por_estado"].get("rejected") == 1, _r["por_estado"])
    chk("conversión 66,7 % (2 de 3 tratos decididos; por versión salía 2 de 4)", _r["conversion"] == 66.7, _r)
    chk("n = 14 cotizaciones de la lista, 4 sustituidas, nada de la otra empresa",
        _r["n"] == 14 and _r["sustituidas"] == 4, _r)

    print("3. La obra del trato y el precio que vale (D1)")
    chk("la 0008 v3 sabe que la v2 creó PRJ-B", Q.obra_del_trato(dict(DATOS[6]))[0] == "PRJ-B")
    chk("…y la 0003, sin otra versión, no tiene obra del trato", Q.obra_del_trato(dict(DATOS[7])) == ("", {}))
    _o = _sustituir(P, get_project=lambda pid: {})
    chk("una obra que ya no existe no cuenta como obra del trato", Q.obra_del_trato(dict(DATOS[6]))[0] == "")
    _o()
    _extra = _q("C84", "0008", 4, "accepted", 13000.0, pid="PRJ-B")
    _o = _sustituir(Q, _records=lambda: [dict(x) for x in DATOS + [_extra]])
    chk("con una variación aceptada, la obra vale la versión MÁS ALTA (cotizacion_de_proyecto → C84)",
        Q.cotizacion_de_proyecto("PRJ-B").get("ID") == "C84", Q.cotizacion_de_proyecto("PRJ-B").get("ID"))
    chk("…y la v2 pasa a «superseded»", Q.vista(dict(DATOS[5]), [dict(x) for x in DATOS + [_extra]]) == Q.SUSTITUIDA)
    _o()

    print("4. El seguimiento de la campana (H21) y los motivos (H16)")
    _s = Q.seguimiento("G")
    chk("la 0010 (vencida hace 3 días) primero y la 0003 (quedan 5) después; ni la 0012 (vencida hace 47), ni la "
        "0011 (30 días), ni versiones viejas, ni OTRA",
        [(x["id"], x.get("vencida"), x.get("quedan")) for x in _s] == [("C101", 3, None), ("C31", None, 5)], _s)
    chk("con «0010 v1»… no: la v1 se dice sin «v1»; el número de la 0003 es «0003»",
        [x["numero"] for x in _s] == ["0010", "0003"], [x["numero"] for x in _s])
    chk("motivo_de separa clave y nota", Q.motivo_de(DATOS[8]) == ("price", "their budget was 4000"))
    chk("los TRATOS perdidos por motivo: {price: 1} (la 0008 v3 no es un trato perdido)",
        Q.rechazos_por_motivo("G") == {"price": 1}, Q.rechazos_por_motivo("G"))
finally:
    for x in _d:
        x()


class _Hoja:
    """Una hoja FALSA de Quotes: lee los datos y apunta lo que se escribiría."""
    def __init__(self, filas):
        self.filas = [dict(x) for x in filas]
        self.escrito = []

    def get_all_records(self, **k):
        return [dict(x) for x in self.filas]

    def batch_update(self, lote, **k):
        self.escrito += lote
        for it in lote:
            _col = "".join(ch for ch in it["range"] if ch.isalpha())
            _row = int("".join(ch for ch in it["range"] if ch.isdigit()))
            _k = next(h for h, i in Q._COL.items() if Q._col_letter(i) == _col)
            self.filas[_row - 2][_k] = it["values"][0][0]


def _escrito(h, cid, campo):
    _row = next(i + 2 for i, x in enumerate(h.filas) if x["ID"] == cid)
    _rg = f"{Q._col_letter(Q._COL[campo])}{_row}"
    return [it["values"][0][0] for it in h.escrito if it["range"] == _rg]


print("5. Aceptar una VARIACIÓN y rechazar con motivo, contra una hoja falsa")
_H = _Hoja([x for x in DATOS if x["Group"] == "G"])
_AUD, _UPD = [], []
_d = [_sustituir(Q, _records=lambda: [dict(x) for x in _H.filas], _ws=lambda: _H, _invalidate=lambda: None),
      _sustituir(P, get_project=lambda pid: dict(_OBRAS[pid]) if pid in _OBRAS else {},
                 update_project=lambda pid, f: (_UPD.append((pid, dict(f))), (True, "ok"))[1]),
      _sustituir(auditoria, registrar=lambda *a, **k: _AUD.append((a, k))),
      _sustituir(clock, today=lambda *a, **k: HOY)]
try:
    # la 0008 v3 vuelve a «sent» para aceptarla como variación (su motivo se borra al volver)
    _ok, _m = Q.set_estado("C83", Q.ENVIADA)
    chk("volver a «sent» una rechazada BORRA su motivo", _ok and _escrito(_H, "C83", "RejectReason") == [""],
        (_ok, _m, _escrito(_H, "C83", "RejectReason")))
    _ok, _m = Q.set_estado("C83", Q.ACEPTADA)
    chk("aceptarla (set_estado) la ENLAZA a PRJ-B: Status accepted + ProjectID PRJ-B, sin crear obra",
        _ok and _escrito(_H, "C83", "Status")[-1:] == ["accepted"] and _escrito(_H, "C83", "ProjectID") == ["PRJ-B"],
        (_ok, _m, _H.escrito[-3:]))
    chk("…y la obra pasa a tener de presupuesto el COSTO cotizado de esta versión (3840)",
        _UPD == [("PRJ-B", {"Budget": "3840.0"})], _UPD)
    chk("…y lo dice: «accepted as a variation of v2 … goes by its price»",
        "as a variation of v2" in _m and "C5 — Bayview — Lift 1" in _m, _m)
    chk("…con su apunte en la auditoría", any(a[1] == "C83" and a[2].get("ProjectID") == ["", "PRJ-B"] for a, k in _AUD),
        _AUD[-1:])
    _ok2, _m2 = Q.aceptar_variacion("C83")
    chk("un 2º toque no hace nada", not _ok2, _m2)
    _ok3, _m3 = Q.aceptar_y_crear_proyecto("C74", nombre="x", ns=12)
    chk("crear obra desde la 0007 v4 (su trato ya tiene PRJ-A) se NIEGA: «This job already exists: PRJ-A»",
        not _ok3 and "PRJ-A" in _m3, _m3)
    _ok4, _m4 = Q.set_estado("C31", Q.RECHAZADA, motivo="price", nota_motivo="  too   high ")
    chk("rechazar con motivo guarda «price — too high»",
        _ok4 and _escrito(_H, "C31", "RejectReason") == ["price — too high"], _escrito(_H, "C31", "RejectReason"))
    _ok5, _m5 = Q.set_estado("C101", Q.RECHAZADA, motivo="because")
    chk("un motivo que no está en la lista se rechaza", not _ok5 and "because" in _m5, _m5)
finally:
    for x in _d:
        x()

print("6. La pantalla de Quotes (AppTest)")
PANTALLA = r'''
import json
import datetime as dt
import streamlit as st
from core import quotes as Q, quotes_ui as QU, projects as P, clientes as C, clock, contable, catalogo as CAT, auth
from core import quote_pdf
_D = st.session_state["_DATOS"]
Q._records = lambda: [dict(x) for x in _D]
Q.desactualizadas = lambda c: []
Q.comparacion = lambda cid: {}
_LLAM = st.session_state.setdefault("_LLAM", [])
def _set(cid, est, motivo="", nota_motivo=""):
    _LLAM.append((cid, est, motivo, nota_motivo))
    return True, "ok"
Q.set_estado = _set
Q.guardar_lineas = lambda *a, **k: (_LLAM.append(("guardar",) + a), (True, "Quote updated."))[1]
P.get_project = lambda pid: {"ID": pid, "Name": "Obra " + pid} if pid in ("PRJ-A", "PRJ-B") else {}
C.list_clientes = lambda *a, **k: [{"ID": "CLI-1", "Name": "C5 — Bayview", "Group": "G"},
                                   {"ID": "CLI-2", "Name": "Meridian", "Group": "G"}]
contable.identidad = lambda g: {"legal": st.session_state.get("_LEGAL", "") or g, "abn": ""}
# ⚠️ v691 · CADUCADO el sustituto de `identidad` con «legal» vacío: la de verdad cae al nombre del grupo, y por eso el
# aviso no salió nunca en producción (este guardián lo daba por bueno). La pantalla pregunta a `tiene_razon_social`.
contable.tiene_razon_social = lambda g: bool(st.session_state.get("_LEGAL", ""))
quote_pdf.generate_quote_pdf = lambda *a, **k: b"%PDF-1.4"
CAT.list_items = lambda *a, **k: []
auth.group_tax_default = lambda g: 10.0
auth.group_margin_default = lambda g: 20.0
clock.today = lambda *a, **k: dt.date(2026, 11, 17)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
QU.render_cotizaciones("G")
'''


def _at(**ss):
    a = AppTest.from_string(PANTALLA, default_timeout=90)
    a.session_state["_DATOS"] = [x for x in DATOS if x["Group"] == "G"]
    for k, v in ss.items():
        a.session_state[k] = v
    a.run()
    return a


def _txt(a):
    # sin los escapes de `literal_md` («PRJ\-A» se ve «PRJ-A»)
    return " ¦ ".join(str(x.value) for x in list(a.markdown) + list(a.caption) + list(a.info) + list(a.warning)
                      + list(a.error)).replace("\\", "")


at = _at()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kp = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_cot_")}
chk("«Out with clients» $5,158 y «4 sent · 2 expired» (por trato)",
    "$5,158" in _kp.get("cpxkpi_cot_calle", "") and "4 sent · 2 expired" in _kp.get("cpxkpi_cot_calle", ""), _kp)
chk("«Won» $74,931 · 2 accepted", "$74,931" in _kp.get("cpxkpi_cot_gan", "") and "2 accepted" in _kp["cpxkpi_cot_gan"], _kp)
chk("«Conversion» 67 %", "67%" in _kp.get("cpxkpi_cot_conv", ""), _kp)
chk("«Quotes» 14 · «2 expired · 4 superseded»", "14" in _kp.get("cpxkpi_cot_n", "")
    and "2 expired · 4 superseded" in _kp["cpxkpi_cot_n"], _kp)
_df = at.dataframe[0].value if at.dataframe else None
_est = dict(zip(_df["Nº"], _df["Estado"])) if _df is not None else {}
chk("la tabla dice «◻️ Superseded» en la 0008 (v1) y «🟢 Accepted» en la 0008 v2",
    _est.get("0008") == "◻️ Superseded" and _est.get("0008 v2") == "🟢 Accepted", _est)
_bv = {str(b.key) for b in at.button if str(b.key).startswith("cotvenc_")}
chk("el aviso de vencidas: la 0010 y la 0012, NO la 0011 v1 (sustituida)",
    "2 expired quote(s)" in _txt(at) and _bv == {"cotvenc_C101", "cotvenc_C121"}, (_bv, _txt(at)[:400]))

at = _at(cpxseg_cot_filt="Rechazadas")
chk("el filtro «Rejected» dice las perdidas por motivo: «Lost, by reason: Price 1»", "Lost, by reason: Price 1" in _txt(at),
    _txt(at)[:500])

print("7. La ficha: superseded, variación, ya con obra del trato, motivo, emisor (H3, D1, H16, H5)")
at = _at(_cot_open="C81")
chk("0008 (v1): «Superseded by v2 (Accepted)» y un botón que abre la v2",
    "Superseded** by v2 (Accepted)" in _txt(at) and any(str(b.key) == "cot_rep_C81" for b in at.button), _txt(at)[:500])
chk("…y el aviso del emisor: la empresa sin razón social → «This PDF shows «G» as the issuer»",
    "This PDF shows «G» as the issuer" in _txt(at), _txt(at)[-500:])
at = _at(_cot_open="C81", _LEGAL="Acme Lifts Pty Ltd")
chk("…que no sale con razón social", "as the issuer" not in _txt(at))
at = _at(_cot_open="C74")
chk("0007 v4 (enviada, su trato tiene PRJ-A): «This is a variation of the accepted v3, which created Obra PRJ-A»",
    "variation** of the accepted v3, which created **Obra PRJ-A**" in _txt(at), _txt(at)[:600])
_d4 = [dict(x) for x in DATOS if x["Group"] == "G"]
for x in _d4:
    if x["ID"] == "C83":
        x["Status"] = "accepted"                          # aceptada SIN obra y con la v2 ya con obra
at = AppTest.from_string(PANTALLA, default_timeout=90)
at.session_state["_DATOS"] = _d4
at.session_state["_cot_open"] = "C83"
at.run()
chk("0008 v3 aceptada sin obra (su trato ya tiene PRJ-B): «Another version … already created» y SIN el formulario",
    "already created **Obra PRJ-B**" in _txt(at) and "Turn it into a project" not in _txt(at), _txt(at)[-700:])
at = _at(_cot_open="C91")
chk("0009 rechazada: «Reason: Price — their budget was 4000»", "Reason: Price — their budget was 4000" in _txt(at),
    _txt(at)[:500])
at = _at(_cot_open="C82")
_nv = next((b for b in at.button if str(b.key) == "cot_v2_C82"), None)
chk("«New version» de una aceptada con obra explica que es una VARIACIÓN de su obra",
    _nv is not None and "a variation of Obra PRJ-B" in str(_nv.help), getattr(_nv, "help", None))

print("8. Rechazar pide el motivo (H16)")
at = _at(_cot_open="C31")
at.button(key="cot_no_C31").click().run()
chk("tras «They rejected it» sale «Why did they reject it?» y «Record the rejection» PARADO hasta elegir",
    "Why did they reject it?" in _txt(at) and at.button(key="cot_rech_ok_C31").disabled, _txt(at)[-400:])
chk("…y todavía no se ha rechazado nada", not at.session_state["_LLAM"], at.session_state["_LLAM"])
at.selectbox(key="cot_rech_mot_C31").set_value("competitor")
at.text_input(key="cot_rech_nota_C31").set_value("Kone was cheaper")
at.run()
at.button(key="cot_rech_ok_C31").click().run()
chk("con el motivo, se rechaza con él: (C31, rejected, competitor, «Kone was cheaper»)",
    ("C31", "rejected", "competitor", "Kone was cheaper") in at.session_state["_LLAM"], at.session_state["_LLAM"])

print("9. «Back to quotes» con cambios sin guardar (H6)")
at = _at(_cot_open="C102")
chk("el borrador se pinta", not at.exception and any(n.key == "cot_imp_C102" for n in at.number_input),
    [e.value for e in at.exception][:1])
at.button(key="cot_back").click().run()
chk("sin cambios, «Back» vuelve a la lista", "_cot_open" not in at.session_state)
at = _at(_cot_open="C102")
at.number_input(key="cot_imp_C102").set_value(0.0).run()
at.button(key="cot_back").click().run()
chk("con el impuesto cambiado, «Back» NO sale: pregunta «changes that are not saved»",
    at.session_state["_cot_open"] == "C102" and "changes that are not saved" in _txt(at), _txt(at)[:500])
at.button(key="cot_salir_q_C102").click().run()
chk("«Stay» se queda con el cambio", at.session_state["_cot_open"] == "C102"
    and at.number_input(key="cot_imp_C102").value == 0.0 and "changes that are not saved" not in _txt(at))
at.button(key="cot_back").click().run()
at.button(key="cot_salir_g_C102").click().run()
chk("«Save and go back» GUARDA (impuesto 0) y vuelve a la lista",
    any(x[0] == "guardar" and x[1] == "C102" for x in at.session_state["_LLAM"]) and "_cot_open" not in at.session_state,
    at.session_state["_LLAM"])
at = _at(_cot_open="C102")
at.number_input(key="cot_imp_C102").set_value(0.0).run()
at.button(key="cot_back").click().run()
at.button(key="cot_salir_d_C102").click().run()
chk("«Discard and go back» vuelve SIN guardar", "_cot_open" not in at.session_state
    and not any(x[0] == "guardar" for x in at.session_state["_LLAM"]), at.session_state["_LLAM"])

print("10. «New quote» sin cliente elegido (H4)")
at = _at(_cot_nueva=True, new_lineas=list(_L))
chk("el cliente nace SIN elegir", at.selectbox(key="cot_new_cli").value is None, at.selectbox(key="cot_new_cli").value)
at.button(key="cot_new_save").click().run()
chk("«Create quote» sin cliente dice «Choose who the quote is for.» y no crea",
    "Choose who the quote is for." in _txt(at) and at.session_state["_cot_nueva"], _txt(at)[-300:])

print("11. La campana (H21)")
CAMPANA = r'''
import datetime as dt
import streamlit as st
from core import home_ui as H, quotes as Q, clock, admin_digest, toolruns, credentials, inventory
clock.today = lambda *a, **k: dt.date(2026, 11, 17)
Q._records = lambda: [dict(x) for x in st.session_state["_DATOS"]]
admin_digest.group_digest = lambda g: {}
toolruns.survey_por_decidir = lambda g: []
credentials.is_configured = lambda: False
inventory.is_configured = lambda: False
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_it = H._alertas_items("G")
st.session_state["_IT"] = _it
if st.button("ir", key="ir"):
    H._ir_alerta(_it[0]["destino"], "G")
'''
at = AppTest.from_string(CAMPANA, default_timeout=90)
at.session_state["_DATOS"] = [x for x in DATOS if x["Group"] == "G"]
at.run()
_it = at.session_state["_IT"] if "_IT" in at.session_state else []
_tx = [x["texto"] for x in _it]
chk("la campana trae la 0010 «expired 3 d ago with no reply» y la 0003 «no reply yet, valid 5 more day(s)»",
    any("Quote No. 0010" in x and "expired 3 d ago" in x for x in _tx)
    and any("Quote No. 0003" in x and "valid 5 more day(s)" in x for x in _tx), _tx)
chk("…con el cliente escapado y llevando a ESA cotización", any("C5 — Bayview" in x for x in _tx)
    and ("cotizacion", "C101") in [x["destino"] for x in _it], _it)
at.button(key="ir").click().run()
chk("tocarla abre la cotización en Finance → Quotes",
    at.session_state["_cot_open"] == "C101" and at.session_state["_admin_nav_pending"] == ("finanzas", "📄 Cotizaciones"),
    (at.session_state["_cot_open"] if "_cot_open" in at.session_state else None,))

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
