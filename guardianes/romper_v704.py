# -*- coding: utf-8 -*-
"""Batería de roturas de v704. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v704"
TOPE_S = 300
XO, XUI, XN, IN = "core/xero.py", "core/xero_ui.py", "core/xero_nomina.py", "core/invoices.py"
CLs, CU, PU, PY, PYU = "core/claims.py", "core/claims_ui.py", "core/projects_ui.py", "core/payroll.py", "core/payroll_ui.py"

ROTURAS = [
    ("H21: un 401 con el acceso renovado ya no pregunta por la organización", XO,
     [("    if (r.status_code == 401 and refrescado) or r.status_code == 403:",
       "    if False:")]),
    ("H21: con la organización fuera, no se marca «reconnect»", XO,
     [("            _marcar_estado(grupo, RECONECTAR)\n", "")]),
    ("H21: «sigue» aunque /Connections no la liste", XO,
     [("""    return any(str((c or {}).get("tenantId", "")) == str(tok.get("tenant_id", "")) for c in (js or [])
               if isinstance(c, dict))""", "    return True")]),
    ("H21: un 401 en /Connections ya no es «fuera»", XO,
     [("    if r.status_code == 401:\n        return False\n    if r.status_code != 200:",
       "    if r.status_code != 200:")]),
    ("H21: `_token` vuelve a usar una conexión marcada «reconnect»", XO,
     [("""        if str(fila.get("Status", "") or "") == RECONECTAR:
            return False, aviso_reconectar()
""", "")]),
    ("H21: la pantalla no avisa de la causa", XUI,
     [("""            st.warning(":material/link_off: " + X.aviso_reconectar())""", "            pass")]),
    ("H21: el botón vuelve a decir «Connect» con la conexión rechazada", XUI,
     [("""t(":material/link: Reconnect to Xero") if _reconectar else t(":material/link: Connect to Xero")""",
       """t(":material/link: Connect to Xero")""")]),
    ("H21: la nómina vuelve a dar otra causa", XN,
     [("""            if isinstance(js, dict) and js.get("_reconectar"):
                out["error"] = _e
                return out
""", "")]),
    ("H21: el 404 de Payroll vuelve a «Try in a minute»", XN,
     [("            if st_ == 404:\n", "            if False:\n")]),
    ("D4: con Xero a 0, un solo pago en vez de uno por cobro", XO,
     [("    if (pagado <= 0.005 and hist\n", "    if (False and hist\n")]),
    ("D4: lo que vino DE Xero vuelve a Xero", XO,
     [("""    hist = [c for c in invoices.cobros_de(f) if isinstance(c, dict) and str(c.get("origen", "")) != "xero"]""",
       """    hist = [c for c in invoices.cobros_de(f) if isinstance(c, dict)]""")]),
    ("D4: se manda TODO lo cobrado aunque Xero ya tenga una parte", XO,
     [("    falta = round(copex - pagado, 2)\n", "    falta = copex\n")]),
    ("D4: se manda un pago a una factura en borrador", XO,
     [("""            if est != "AUTHORISED":
                res["errores"].append((fid, numero, [t("It is {e} in Xero: a payment can only go to an approved \"""",
       """            if False:
                res["errores"].append((fid, numero, [t("It is {e} in Xero: a payment can only go to an approved \"""")]),
    ("D4: el pago va a otra cuenta", XO,
     [("""                pagos.append({"Invoice": {"InvoiceID": xid}, "Account": {"AccountID": cb["id"]},""",
       """                pagos.append({"Invoice": {"InvoiceID": xid}, "Account": {"Code": "200"},""")]),
    ("D4: un pago rechazado por Xero se da por mandado", XO,
     [("""                if errs or not pid or pid == "00000000-0000-0000-0000-000000000000":
                    res["errores"].append((fid, numero, errs or [t("Xero rejected the payment.")]))""",
       """                if False:
                    res["errores"].append((fid, numero, errs or [t("Xero rejected the payment.")]))""")]),
    ("D4: sin cuenta del banco, se llama a Xero igual", XO,
     [("""    cb = cuenta_banco(grupo)
    if not cb:
        res["avisos"].append(t("Choose the Xero bank account for COPEX payments first""",
       """    cb = cuenta_banco(grupo) or {"id": ""}
    if not cb:
        res["avisos"].append(t("Choose the Xero bank account for COPEX payments first""")]),
    ("D4: al enviar, los cobros ya no van", XO,
     [("            _cobros_al_enviar(grupo, marcas, estado_xero, res)\n", "")]),
    ("D4: en borrador ya no se avisa", XO,
     [("""    if estado_xero != APROBADA:
        for _fid, f in con_cobro:""", """    if estado_xero != APROBADA:
        for _fid, f in []:""")]),
    ("D4: traer cobros vuelve a bajar lo de COPEX", XO,
     [("""                if pagado < _copex - 0.005:
                    res["por_mandar"].append((f.get("ID"), numero, _copex, pagado))
                    continue
""", "")]),
    ("D4: sincronizar_cobros baja sin confirmar", IN,
     [("        if ahora < antes and fid not in _bajar:", "        if False:")]),
    ("D4: lo no bajado de la lectura fresca se pierde", XO,
     [("""                res["por_mandar"] += [(fid, num.get(fid, fid), antes, ahora)
                                      for fid, antes, ahora in r.get("no_bajadas", [])]""", "                pass")]),
    ("D4: «Use Xero's figure» no puede bajar (sin `bajar`)", XO,
     [("""                                        clock.today().isoformat(), bajar={str(fid)})""",
       """                                        clock.today().isoformat())""")]),
    ("D4: «Use Xero's figure» baja sin preguntar", XUI,
     [("""            elif st.button(t("Use Xero's figure for invoice {n}", n=_md(n)), key=f"xero_pm_x_{fid}",
                           type="tertiary"):
                st.session_state["_xero_pm_conf"] = str(fid)""",
       """            elif st.button(t("Use Xero's figure for invoice {n}", n=_md(n)), key=f"xero_pm_x_{fid}",
                           type="tertiary"):
                X.aceptar_cifra_xero(grupo, str(fid))""")]),
    ("D4: «Send these payments» activo sin cuenta del banco", XUI,
     [("""                     type="primary", disabled=not cb):""", """                     type="primary", disabled=False):""")]),
    ("D4: la cuenta elegida no se guarda", XUI,
     [("""        ok, msg = contable.guardar_claves(grupo, {"xero_cuenta_banco": {"id": x["id"], "codigo": x["codigo"],
                                                                         "nombre": x["nombre"]}})""",
       """        ok, msg = True, \"\"""")]),
    ("D4: «Bring payments» ya no guarda lo que falta en Xero", XUI,
     [("""        st.session_state["_xero_por_mandar"] = list(res.get("por_mandar") or [])   # v704 · D4""",
       """        pass""")]),
    ("V1: «Job restarted.» vuelve a decir siempre que la pausa quitó el tablero", PU,
     [("""            st.caption(t("Nobody is on the board for it from today: plan their days.") if _tab == 0""",
       """            st.caption(t("The pause took the crew off the board: plan their days again.") if True""")]),
    ("V1: el aviso no lee el tablero", PU,
     [("""                    _tab = sum(_R.dias_desde(grupo, pid, clock.today(grupo)).values())""",
       """                    _tab = None""")]),
    ("V2: factura_de ignora `incluir_anuladas`", CLs,
     [("    if incluir_anuladas:\n        _todas = _I.list_facturas(grupo) if grupo else _I.list_facturas()",
       "    if False:\n        _todas = _I.list_facturas(grupo) if grupo else _I.list_facturas()")]),
    ("V2: la anulada vuelve al neto sin el depósito", CU,
     [("                        _txt = _linea_claim(r, _neto - _dep_a, _dep_a)",
       "                        _txt = _linea_claim(r, _neto)")]),
    ("V3: la del MISMO periodo cuenta como solape", PY,
     [("""            if str(f.get("PeriodFrom", "")) == d_iso and str(f.get("PeriodTo", "")) == h_iso:
                continue                          # el duplicado EXACTO ya lo trata `existentes`
            if fd <= _h and _d <= fh:""", """            if fd <= _h and _d <= fh:""")]),
    ("V3: generar vuelve a su copia (no usa solapes_de)", PY,
     [("    solapes = solapes_de(grupo, d_iso, h_iso)      # v704 · una definición, la usa también la vista previa",
       "    solapes = {}")]),
    ("V3: la vista previa no dice el solape", PYU,
     [("        _sol = payroll.solapes_de(grupo, desde.isoformat(), hasta.isoformat())", "        _sol = {}")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", XO,
           [("# v704 · D4 del ciclo 7: los cobros de COPEX van a Xero, y COPEX nunca baja uno sin preguntar",
             "# v704 · D4 del ciclo 7: los cobros de COPEX van a Xero, y COPEX nunca baja uno sin preguntar · control")])


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
