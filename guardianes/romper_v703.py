# -*- coding: utf-8 -*-
"""Batería de roturas de v703. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v703"
TOPE_S = 300
QU, OR, PU, PY, SP = "core/quotes_ui.py", "core/orders.py", "core/projects_ui.py", "core/payroll_ui.py", "core/stage_progress_ui.py"
CM, CMU, XU, IU, CU = "core/contable.py", "core/contable_ui.py", "core/xero_ui.py", "core/invoices_ui.py", "core/claims_ui.py"

ROTURAS = [
    ("D2: cambiar la cantidad ya no escala la ganancia", QU,
     [("                gan = round(_g0 * cant / _c0, 2)", "                pass")]),
    ("D2: la ganancia tecleada a la vez se pisa con la escalada", QU,
     [("            if abs(gan - _g0) < 0.005 and _c0 > 0:", "            if _c0 > 0:")]),
    ("H1: la tabla no se renueva tras cambiar la cantidad", QU,
     [('        st.session_state[f"{key}_lineas"] = nuevas\n'
       '        st.session_state[f"{key}_edgen"] = st.session_state.get(f"{key}_edgen", 0) + 1\n',
       '        st.session_state[f"{key}_lineas"] = nuevas\n')]),
    ("H3: «per stop» en la unidad ya no cuenta", QU,
     [('        if "per stop" in _u or _uni in ("stop", "stops"):', '        if _uni in ("stop", "stops"):')]),
    ("H3: el alta ignora las líneas por parada", QU,
     [("    _ns_ln = _ns_por_parada(Q.lineas_de(c)) if _ns_pl < 2 else 0", "    _ns_ln = 0")]),
    ("H5: una orden cancelada cuenta como igual", OR,
     [('        if str(r.get("Status", "")) == CANCELADA:\n            continue\n', '')]),
    ("H5: una igual de hace horas también avisa", OR,
     [("        if 0 <= _m <= minutos:", "        if 0 <= _m:")]),
    ("H5: el formulario vuelve a una clave fija con clear_on_submit", PU,
     [('            with st.form(f"{key_prefix}_ordnew_{pid}_{_ogen}", enter_to_submit=False):',
       '            with st.form(f"{key_prefix}_ordnew_{pid}", enter_to_submit=False, clear_on_submit=True):')]),
    ("H5: ya no se busca la orden igual", PU,
     [("                    _igual = O.igual_reciente(pid, _prov, _val, _desc)      # ANTES de crear la nueva",
       "                    _igual = None")]),
    ("H6: el estado de la orden vuelve a minúscula", PU,
     [("{_est_txt(_est)} · ordered", "{_etq(_est)} · ordered")]),
    ("H7: «Order received…» sin «$»", OR,
     [("(${valor:,.2f}).", "({valor:,.2f}).")]),
    ("H9: la vista previa de la nómina sin las ausencias pagadas", PY,
     [("        _aus = _AUP.horas_pagadas_grupo(grupo, desde, hasta) or {}", "        _aus = {}")]),
    ("H10: el día antes del inicio de la obra ya no avisa", PU,
     [("            if _ini_o and _dia < _ini_o:", "            if False:")]),
    ("H14: reanudar ya no se reconoce", PU,
     [("    _reanuda = bool(not cierre and", "    _reanuda = False and bool(not cierre and")]),
    ("H14: a la cuadrilla le vuelve a llegar «The project details were updated.»", PU,
     [('    if _reanuda:\n        _txt = "This job has restarted.', '    if False:\n        _txt = "This job has restarted.')]),
    ("H14: «Plan it» ya no lleva a Planning", PU,
     [('    st.session_state.pop(f"_prj_reanudada_{pid}", None)\n    _planificar_obra(pid)',
       '    st.session_state.pop(f"_prj_reanudada_{pid}", None)')]),
    ("H14: el propietario ve «Plan it» (no tiene Planning)", PU,
     [('        _plan = str((st.session_state.get("auth") or {}).get("rol", "")) == "administrator"',
       '        _plan = True')]),
    ("H14: la ficha no pinta «Job restarted.»", PU,
     [("            _aviso_reanudada(pid, _reanudada)", "            pass")]),
    ("H18: el aviso de lo no guardado vuelve encima de la lista", SP,
     [("    # ⚠️ v703 · H18 del ciclo 7: el aviso y «Save all» iban AQUÍ",
       '    if _pend and editable:\n        st.warning(t("{n} unsaved ticks.", n=len(_pend)))\n'
       "    # ⚠️ v703 · H18 del ciclo 7: el aviso y «Save all» iban AQUÍ")]),
    ("H8: la etiqueta de la barra vuelve a ancho fijo", PU,
     [("f'<div style=\"flex:0 1 118px;min-width:40px;font-size:12px;color:{theme.TXT};'",
       "f'<div style=\"width:118px;flex:none;font-size:12px;color:{theme.TXT};'")]),
    ("H8: la etiqueta de la barra sin escapar", PU,
     [("{_esc(str(et))}</div>", "{et}</div>")]),
    ("H15: el CSV de facturas vuelve a decir el suyo", CM,
     [("    avisos += _avisos_comunes(perfil, cuentas, [VENTAS], cfg, seg, opciones, con_opciones=False)",
       "    avisos += _avisos_comunes(perfil, cuentas, [VENTAS], cfg, seg, opciones)")]),
    ("H15: `con_opciones=False` no hace nada", CM,
     [("    if con_opciones:\n        avisos += aviso_opciones(", "    if True:\n        avisos += aviso_opciones(")]),
    ("H15: Accounting lo dice solo con las opciones de las facturas", CMU,
     [('        sorted(set(ventas["opciones"]) | set(compras["opciones"])))))',
       '        sorted(set(ventas["opciones"])))))')]),
    ("H22: «In Xero since» vuelve a ISO", XU,
     [('d=(_dmy(_xs) + (" " + _xs[11:16] if len(_xs) >= 16 else "")) if _xs else "—"))', 'd=_xs or "—"))')]),
    ("H24: el importe vuelve a «$%,.2f» («$-20,811.60»)", IU,
     [('                t("Amount"), format="dollar",\n', '                t("Amount"), format="$%,.2f",\n')]),
    ("H25: la línea de la certificación pierde el depósito", CU,
     [('    _menos = ("%s %s · " % (t("deposit"), _dinero(deposito))) if deposito > 0.005 else ""', '    _menos = ""')]),
    ("H25: la lista vuelve al neto sin el depósito", CU,
     [("                    _txt = _linea_claim(r, _neto - _dep_l, _dep_l)", "                    _txt = _linea_claim(r, _neto)")]),
    ("H26: anular ya no mira de qué certificación es", IU,
     [('                        _cl_n = ", #".join(str((_CL.es_ultima(c)[1] or {}).get("Number", "?")) for c in _cids)',
       '                        _cl_n = ""')]),
    ("H26: la confirmación con cobros no dice la certificación", IU,
     [('                                     n=str(f.get("Number", "")), m=_T.dinero(cob)) + _y_cl)',
       '                                     n=str(f.get("Number", "")), m=_T.dinero(cob)))')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", QU,
           [("    # ⚠️ v703 · H3 del ciclo 7: sin plano, las paradas de una línea POR PARADA",
             "    # ⚠️ v703 · H3 del ciclo 7: sin plano, las paradas de una línea POR PARADA · control")])


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
