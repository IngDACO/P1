# -*- coding: utf-8 -*-
"""Batería de roturas de v669. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v669"
TOPE_S = 400
FI = "core/finance.py"
IN = "core/invoices.py"
IU = "core/invoices_ui.py"
PU = "core/projects_ui.py"
PR = "core/projects.py"

ROTURAS = [
    ("⚠️ las variaciones aprobadas vuelven a quedar fuera del ingreso", FI,
     [('_ing = round(_num(_cot.get("Subtotal")) + _var, 2)', '_ing = round(_num(_cot.get("Subtotal")), 2)')]),
    ("⚠️ la cancelada vuelve a valer su cotización", FI,
     [("    if P.es_cancelada(_p_est):\n", "    if False and P.es_cancelada(_p_est):\n")]),
    ("es_cancelada también con Archived", PR,
     [('return str((p or {}).get("Status", "")) == "Cancelled"',
       'return str((p or {}).get("Status", "")) in ("Cancelled", "Archived")')]),
    ("⚠️ por horas vuelve a ganarse con el avance (el adelanto de $0.45)", IN,
     [('        if modelo == "cotizado":\n', '        if True:\n')]),
    ("la ganancia fija por horas deja de ir por avance", IN,
     [("ganado = round(ingreso - _fija * (1 - avance / 100.0), 2)", "ganado = round(ingreso, 2)")]),
    ("⚠️ «sin facturar» vuelve a ser el contrato entero", FI,
     [('    return _por_obra(grupo, "certificable")', '    return _por_obra(grupo, "pendiente")')]),
    ("el Resumen deja de listar el contrato por delante", PU,
     [("        if _sfc:\n            st.caption(t(\"Contract still ahead", "        if False:\n            st.caption(t(\"Contract still ahead")]),
    ("facturado_de_mas vuelve a esconder el exceso", IN,
     [("return round(max(0.0, ya - ingreso), 2)", "return 0.0")]),
    ("⚠️ el aviso de facturar de más no suma (compara línea a línea)", IU,
     [("_por[pid] = round(_por.get(pid, 0.0) + _num(ln.get(\"importe\")), 2)",
       "_por[pid] = round(_num(ln.get(\"importe\")), 2)")]),
    ("⚠️ el aviso de facturar de más deja de pintarse", IU,
     [("    for _av in avisos_de_mas(_lineas, grupo, _pend_de, prjs):\n        st.warning(_av)\n", "")]),
    ("H23 · el aviso de adelanto vuelve a mirar el avance", IU,
     [('        if _c["certificable"] <= 0.005:\n', '        if _c["avance"] <= 0:\n')]),
    ("⚠️ anular con cobros vuelve a hacerlo sin preguntar", IN,
     [("        if not destino_cobros:\n            return False, t(\"This invoice has {m} collected",
       "        if False:\n            return False, t(\"This invoice has {m} collected")]),
    ("devolver no apunta el movimiento en el historial", IN,
     [('            cobros.append({"fecha": hoy, "monto": -cob, "origen": DEVUELTO, "por": str(quien or "")})\n', "")]),
    ("⚠️ pasar a otra factura no sube su cobrado", IN,
     [('"values": [[str(round(prev_g + cob, 2))]]}', '"values": [[str(prev_g)]]}')]),
    ("⚠️ se puede pasar el dinero a una factura de OTRO cliente", IN,
     [('                and str(g.get("ClientID", "")) == str(f.get("ClientID", "")) \\\n', "")]),
    ("destinos acepta facturas sin saldo", IN,
     [("        if round(_num(g.get(\"Total\")) - _num(g.get(\"Collected\")), 2) + 0.005 >= cob:\n            out.append(g)",
       "        out.append(g)")]),
    ("sacar_cobros deja hacerlo en una factura viva", IN,
     [('    if not anular_tambien and estado_cobro(f) != "anulada":\n', '    if False:\n')]),
    ("⚠️ quitar el cobro deja el cobrado igual", IN,
     [("    nuevo = round(max(0.0, prev - monto), 2)\n", "    nuevo = prev\n")]),
    ("quitar el cobro no lo apunta en el historial", IN,
     [('    cobros = cobros_de(f) + [{"fecha": _hoy_iso(), "monto": -monto, "origen": QUITADO, "quita": i,\n'
       '                               "por": str(quien or "")}]\n', "    cobros = cobros_de(f)\n")]),
    ("quitar un cobro de Xero", IN,
     [('        if _num(c.get("monto")) > 0 and not c.get("origen"):\n',
       '        if _num(c.get("monto")) > 0:\n')]),
    ("quitar el cobro sin rastro", IN,
     [('    _rastro(fid, f, {"Collected": [prev, nuevo]}, "quitar_cobro")\n', "")]),
    ("⚠️ el detalle deja de ofrecer «Remove the last payment»", IU,
     [("        if _iq is not None:\n            if st.session_state.get(\"_fac_quitar_conf\") == fid:",
       "        if False:\n            if st.session_state.get(\"_fac_quitar_conf\") == fid:")]),
    ("la anulada con cobros deja de avisar", IU,
     [("        if _anulada and cob > 0.005:\n            st.warning(", "        if False:\n            st.warning(")]),
    ("el desplegable de anular deja de preguntar adónde va el dinero", IU,
     [('                    _dest = _destino_cobros(f, f"fac_anul_dest_{fid}")\n', "")]),
    ("la ficha deja de decir lo facturado de más", PU,
     [("        if _demas_cab > 0.5:\n", "        if False:\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", IN,
           [('DEVOLVER = "devolver"', 'DEVOLVER = "devolver"  # (control)')])


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
