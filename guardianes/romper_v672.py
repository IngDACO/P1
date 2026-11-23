# -*- coding: utf-8 -*-
"""Batería de roturas de v672. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v672"
TOPE_S = 500
I18 = "core/i18n.py"
IU = "core/invoices_ui.py"
QU = "core/quotes_ui.py"
PI = "core/payroll_ui.py"
CB = "core/contable.py"
IP = "core/invoice_pdf.py"
CP = "core/claim_pdf.py"
QP = "core/quote_pdf.py"
PP = "core/payslip_pdf.py"
AI = "core/auth_ui.py"
AU = "core/auth.py"
CU = "core/claims_ui.py"
CL = "core/claims.py"
XU = "core/xero_ui.py"
PU = "core/projects_ui.py"
AD = "core/auditoria.py"
HU = "core/home_ui.py"

ROTURAS = [
    # ── H5 · estados con mayúscula ──
    ("⚠️ H5 · i18n.estado deja de poner la mayúscula", I18,
     [("    s = etiqueta(valor, defecto)\n    return s[:1].upper() + s[1:] if s else s\n",
       "    s = etiqueta(valor, defecto)\n    return s\n")]),
    ("H5 · el detalle de la factura vuelve a la minúscula", IU,
     [('    return f"{_ic} {_txt[:1].upper() + _txt[1:]}".strip()', '    return f"{_ic} {_txt}".strip()')]),
    ("H5 · la cotización vencida vuelve a «expired»", QU,
     [('    return t("Expired") if str(est) == Q.VENCIDA', '    return t("expired") if str(est) == Q.VENCIDA')]),
    ("H5 · la celda de la colilla, en minúscula", PI,
     [("'')} \" + _estado_txt(_estado(x))", "'')} \" + _estado_txt(_estado(x)).lower()")]),
    # ── H24 · identidad, contacto y banco ──
    ("⚠️ H24 · identidad deja de leer el BSB", CB,
     [('        "bsb": auth.group_text_setting(grupo, "BankBSB", ""),', '        "bsb": "",')]),
    ("H24 · el contacto del emisor pierde el teléfono", CB,
     [(', str(ident.get("telefono") or "").strip()) if x)', ',) if x)')]),
    ("⚠️ H24 · basta el BSB para decir que hay datos de pago", CB,
     [('    return bool(str(ident.get("bsb") or "").strip() and str(ident.get("cuenta") or "").strip())',
       '    return bool(str(ident.get("bsb") or "").strip())')]),
    ("H24 · un BSB de 5 cifras pasa", CB,
     [('    return f"{_d[:3]}-{_d[3:]}" if len(_d) == 6 else ""', '    return f"{_d[:3]}-{_d[3:]}" if len(_d) >= 5 else ""')]),
    ("⚠️ H24 · «How to pay» sin la referencia", IP,
     [('             [Paragraph(d("Account"), H), Paragraph(esc_pdf(ident.get("cuenta")), Hb)],\n'
       '             [Paragraph(d("Reference"), H), Paragraph(esc_pdf(referencia), Hb)]]',
       '             [Paragraph(d("Account"), H), Paragraph(esc_pdf(ident.get("cuenta")), Hb)]]')]),
    ("H24 · «How to pay» también en una cobrada", IP,
     [("    if por_cobrar > 0.005:\n        story += bloque_pago(", "    if True:\n        story += bloque_pago(")]),
    ("H24 · el emisor sin su contacto", IP,
     [("    for _l in contable.contacto_emisor(ident):\n", "    for _l in []:\n")]),
    ("⚠️ el titular sin escapar (v653)", IP,
     [("Paragraph(esc_pdf(_tit), Hb)", "Paragraph(_tit, Hb)")]),
    ("H24 · la factura nueva no avisa sin datos de pago", IU,
     [("    if _sin_pago:\n        st.warning(_CB.aviso_sin_pago(icono=True))",
       "    if False:\n        st.warning(_CB.aviso_sin_pago(icono=True))")]),
    ("H24 · el detalle no avisa junto al PDF", IU,
     [('            if (not _CB.tiene_datos_pago(_idn) and est not in ("cobrada", "anulada")):',
       "            if False:")]),
    ("H24 · avisa también en una cobrada", IU,
     [('            if (not _CB.tiene_datos_pago(_idn) and est not in ("cobrada", "anulada")):',
       "            if (not _CB.tiene_datos_pago(_idn)):")]),
    ("H24 · Accounting no avisa sin datos de pago", CB,
     [("    if not tiene_datos_pago(ident):\n        avisos.append(aviso_sin_pago())",
       "    if False:\n        avisos.append(aviso_sin_pago())")]),
    ("⚠️ H24 · el formulario no valida el BSB", AI,
     [("                    if _bsb.strip() and not _bsb_n:\n", "                    if False:\n")]),
    ("H24 · el formulario acepta el BSB sin la cuenta", AI,
     [("                    elif bool(_bsb.strip()) != bool(_cta.strip()):\n", "                    elif False:\n")]),
    ("H24 · el formulario no valida el email", AI,
     [('                    elif not auth.revisar_email(_mail)["ok"]:\n', "                    elif False:\n")]),
    ("⚠️ H24 · el formulario escribe TODO, cambie o no", AI,
     [("                        _cambian = [c for c, v in _nuevos.items() if _ahora[c] != v]\n",
       "                        _cambian = list(_nuevos)\n")]),
    ("H30 · el plazo vacío (se ve 14) se reescribe al guardar", AI,
     [('                        _ahora["PaymentTermsDays"] = str(int(_num(_gf.get("PaymentTermsDays")) or 14))   # el que se ve\n',
       "")]),
    ("H24 · una columna nueva se mete en medio", AU,
     [('"ContactPhone", "BankAccountName", "BankBSB", "BankAccountNumber"]',
       '"ContactPhone", "BankBSB", "BankAccountName", "BankAccountNumber"]')]),
    # ── H11 · sin estado interno ──
    ("⚠️ H11 · vuelve «Status» a la factura", IP,
     [('        [Paragraph(d("Due"), sm), Paragraph(_dmy(factura.get("ExpiryDate", "")), H)],\n    ], colWidths',
       '        [Paragraph(d("Due"), sm), Paragraph(_dmy(factura.get("ExpiryDate", "")), H)],\n'
       '        [Paragraph(d("Status"), sm), Paragraph(est, H)],\n    ], colWidths')]),
    ("H11 · vuelve «Status» a la cotización", QP,
     [("        # ⚠️ v672 · sin «Status» (H11): «draft» o «sent» es un estado INTERNO, no algo que el cliente deba leer\n",
       '        [Paragraph(d("Status"), sm), Paragraph(str(cot.get("Status", "")), H)],\n')]),
    ("H11 · la colilla sin pagar vuelve a «Status | emitida»", PP,
     [('        _pago_lbl, _pago_txt = d("Payment"), d("Not paid yet")', '        _pago_lbl, _pago_txt = d("Status"), est')]),
    ("H5 · el tipo del concepto en minúscula en la colilla", PP,
     [('Paragraph(esc_pdf(i18n.estado(c.get("tipo", ""))), H)', 'Paragraph(esc_pdf(i18n.etiqueta(c.get("tipo", ""))), H)')]),
    ("⚠️ la certificación pagada pide que se pague", CP,
     [("    elif not _pagada:\n", "    elif True:\n")]),
    ("la certificación anulada sin su sello", CP,
     [("    if _anulada:\n        story += [Paragraph(d(\"VOID — this claim", "    if False:\n        story += [Paragraph(d(\"VOID — this claim")]),
    # ── H14 · certificaciones ──
    ("⚠️ H14 · la fecha de la certificación vuelve a ISO", CP,
     [('Paragraph(esc_pdf(dmy(rec.get("Date", ""))), H)', 'Paragraph(esc_pdf(rec.get("Date", "")), H)')]),
    ("H14 · «-$0.00» vuelve", CP,
     [('    return ("-" + _money(v)) if round(_num(v), 2) > 0 else _money(0)', '    return "-" + _money(v)')]),
    ("H14 · el dinero de los avisos sin miles", CL,
     [('"{:,.2f}".format(round(_num(v), 2))', '"{:.2f}".format(round(_num(v), 2))')]),
    ("H14 · el aviso de emitir sin $", CL,
     # v702 · re-anclada: el aviso de emitir sigue con «· invoice No. N issued.» (D3 del ciclo 7)
     [('t("net payable"), _dinero(d["neto"]),', 't("net payable"), "%.2f" % d["neto"],')]),
    ("⚠️ dos importes en un aviso, sin escapar (LaTeX, v309)", CL,
     [("amount=_dinero(_imp, escapado=True), held=_dinero(_pend, escapado=True))",
       "amount=_dinero(_imp), held=_dinero(_pend))")]),
    ("H14 · la lista vuelve a la fecha ISO", CU,
     [('r.get("Number", "?"), _dmy(r.get("Date", "")), "%g" % _num(r.get("PctComplete", 0)),',
       'r.get("Number", "?"), r.get("Date", ""), "%g" % _num(r.get("PctComplete", 0)),')]),
    ("H5 · la anulada vuelve a «cancelled»", CU,
     [("_estado_txt(CL.ANULADA)))", 't("cancelled")))')]),
    ("H5 · la variación vuelve al código crudo", CU,
     [('v.get("Description", ""), _estado_txt(_e)),', 'v.get("Description", ""), _e),')]),
    # ── H16 · Accounting ──
    ("⚠️ H16 · la conexión vuelve a la fecha ISO", XU,
     [('    _desde = (_dmy(_desde[:10]) + (" " + _desde[11:16] if len(_desde) >= 16 else "")) if _desde else "—"\n',
       '    _desde = _desde or "—"\n')]),
    ("H16 · el login en vez del nombre", XU,
     [('        _por = str((_AU.get_user(str(est["por"] or "")) or {}).get("Name") or est["por"] or "")\n',
       '        _por = str(est["por"] or "")\n')]),
    # ── H28 · la actividad parada ──
    ("⚠️ H28 · vuelve «it was due on … (2 d)» sin t()", PU,
     [('t(":red[:material/cancel:] **{n}** — not started, should have started on {f} · {d}-day activity",',
       '(":red[:material/cancel:] **{n}** — not started, it was due on {f} ({d} d)").format(')]),
    # ── H30 · el rastro ──
    ("⚠️ H30 · el rastro apunta los no-cambios", AD,
     [("    cambios = {k: v for k, v in (cambios or {}).items() if not _igual(v)}\n", "    cambios = dict(cambios or {})\n")]),
    ("H30 · «1 → 1.0» cuenta como cambio", AD,
     [("        return a != \"\" and b != \"\" and abs(float(a) - float(b)) < 1e-9\n", "        return False\n")]),
    ("H30 · el peso sin grupo se reescribe", PU,
     [('                        "WeightInGrouping": peso if ag_id else prj.get("WeightInGrouping", ""),',
       '                        "WeightInGrouping": peso,')]),
    # ── H26 · el buscador ──
    ("⚠️ H26 · el número de factura no se reconoce", HU,
     [('                r = 0 if _es_ese_documento(_doc, "factura", num) else _rank(num, fid, f.get("ClientName"))',
       '                r = _rank(num, fid, f.get("ClientName"))')]),
    ("H26 · con un carácter no se busca nada", HU,
     [("    if len(qn) < 2 and _doc is None:", "    if len(qn) < 2:")]),
    ("H26 · con un carácter, todo coincide", HU,
     [("        if len(qn) < 2:\n            return None\n        mejor = None\n", "        mejor = None\n")]),
    ("H26 · «Invoice 4» trae también la cotización", HU,
     [("    if not doc or (doc[0] and doc[0] != clase):", "    if not doc:")]),
    ("⚠️ H26 · los ceros a la izquierda cuentan («0004» ≠ 4)", HU,
     [("    return bool(_d) and int(_d) == doc[1]", "    return bool(_d) and _d == str(doc[1])")]),
    ("H26 · el resultado de la factura sin estado", HU,
     [('_dmy(f.get("Date", "")), _estado_txt(_est),', '_dmy(f.get("Date", "")),')]),
    ("H26 · el resultado dice el total, no lo que falta", HU,
     [('if _est not in ("cobrada", "anulada") \\', 'if False \\')]),
    # ── lo visto verificando v671 ──
    ("⚠️ la vista previa vuelve a dar base a quien deja fuera", PI,
     [('            "Base": (None if (k in _fuera and k not in _ya) else round(v["horas"] * _num(rates.get(k, 0)), 2)),',
       '            "Base": round(v["horas"] * _num(rates.get(k, 0)), 2),')]),
    ("la vista previa no sabe a quién deja fuera", PI,
     [('        _fuera = {str(j.get("usuario", "")) for j in _lg}\n', "        _fuera = set()\n")]),
    ("la colilla de un administrador manda a Planning → Users", PI,
     [('                if _rol_de in ("administrator", "owner"):', "                if False:")]),
    ("guardar el fondo de super vuelve a «Saved.»", AI,
     [('t("Super fund saved: {f}.", f=_lit(_sf.strip()))', 't("Saved.")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", I18,
           [("def estado(valor, defecto=None) -> str:\n", "def estado(valor, defecto=None) -> str:  # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
