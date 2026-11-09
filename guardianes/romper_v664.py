# -*- coding: utf-8 -*-
"""Batería de roturas de v664. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v664"
TOPE_S = 240
QU = "core/quotes_ui.py"
Q = "core/quotes.py"
QPDF = "core/quote_pdf.py"
I = "core/invoices.py"
IU = "core/invoices_ui.py"
O = "core/orders.py"
PU = "core/projects_ui.py"

ROTURAS = [
    ("⚠️ las líneas del plano vuelven a entrar a coste (sin margen)", QU,
     [("_QP.proponer(_plano, _items, _A.group_margin_default(grupo))", "_QP.proponer(_plano, _items)")]),
    ("«The drawing says» vuelve a pintarse antes del rerun (se pierde)", QU,
     [('flash.info(t("**The drawing says:**', 'st.info(t("**The drawing says:**')]),
    ("«Not proposed» vuelve a perderse con el rerun", QU,
     [('flash.aviso(t(":material/info: Not proposed', 'st.caption(t(":material/info: Not proposed')]),
    ("⚠️ un artículo repetido vuelve a entrar en silencio", QU,
     [("for _nuevo, _viejo in _dobles:", "for _nuevo, _viejo in []:")]),
    ("el plano no se guarda para la cotización", QU,
     [('_st["new_plano"] = _plano', '_st["otro_plano"] = _plano')]),
    ("⚠️ crear la cotización ya no lleva el plano", QU,
     [('creado_por=_creado_por(),\n                              plano=st.session_state.get("new_plano"))',
       "creado_por=_creado_por())")]),
    ("el plano de una cotización anterior se queda en la sesión", QU,
     [('"new_lineas", "new_plano", "cot_new_cli"', '"new_lineas", "cot_new_cli"')]),
    ("Turn it into a project vuelve a nacer con NS = 2", QU,
     [("value=min(50, _ns_pl) if _ns_pl >= 2 else 2,", "value=2,")]),
    ("la ubicación vuelve a nacer vacía", QU,
     [('ubic = st.text_input(t("Location (optional)"), value=_dir0,',
       'ubic = st.text_input(t("Location (optional)"), value="",')]),
    ("⚠️ la fila de la cotización ya no guarda el plano", Q,
     [("_plano_json(plano)],", '""],')]),
    ("una versión nueva pierde el plano", Q,
     [('plano=str(c.get("DrawingJSON") or ""))', 'plano=""))')]),
    ("⚠️ la obra vuelve a nacer sin modelo", Q,
     [('modelo=str(_pl.get("modelo") or ""),', 'modelo="",')]),
    ("⚠️ el plano no pasa a la obra al aceptar", Q,
     [("            _PD.guardar(res, _pl)\n", "            pass\n")]),
    ("plano_de deja pasar lo que no es un dict", Q,
     [("return d if isinstance(d, dict) else {}", "return d")]),
    ("⚠️ el PDF vuelve a decir «1» por 160 h de montaje", QPDF,
     [('if str(l.get("tipo", "")) == "service" and _num(l.get("horas")) > 0:', "if False:")]),
    ("lo ganado ya no depende del avance", I,
     [("ganado = round(ingreso * avance / 100.0, 2)", "ganado = round(ingreso, 2)")]),
    ("⚠️ lo certificable vuelve a ser todo el contrato", I,
     [("certificable = round(min(pendiente, max(0.0, ganado - ya)), 2)",
       "certificable = round(min(pendiente, max(0.0, ingreso - ya)), 2)")]),
    ("el pendiente vuelve a tener una segunda definición", I,
     [("pendiente = round(_num(pendiente_de_facturar(pid, grupo, p)), 2)",
       'pendiente = round(max(0.0, _num(F.project_revenue(pid, grupo, p)["ingreso"]) '
       '- _num(facturado_por_proyecto(grupo).get(str(pid), 0.0))), 2)')]),
    ("⚠️ crear vuelve a abrir (y migrar) la hoja antes de validar", Q,
     [("    if not lineas:\n        return False, t(\"Add at least one line to the quote.\")\n",
       "    _ws()\n    if not lineas:\n        return False, t(\"Add at least one line to the quote.\")\n")]),
    ("⚠️ la factura vuelve a proponer el 100 % con la obra a medias", IU,
     [('            imp = _c["certificable"]\n', "            imp = pend\n")]),
    ("sin avance, ya no avisa de que es por adelantado", IU,
     [('if _c["avance"] <= 0:', "if False:")]),
    ("las notas de la precarga no se pintan", IU,
     [("    for _n in _notas:\n        st.markdown(_n)\n", "")]),
    ("el importe vuelve a ir detrás de Project", IU,
     [('"Importe": imp, "Project": _lbl.get(str(p.get("ID", "")), "")})',
       '"Project": _lbl.get(str(p.get("ID", "")), ""), "Importe": imp})')]),
    ("⚠️ sin ABN ya no avisa antes de emitir", IU,
     [("    if _sin_abn:\n        st.warning(", "    if False:\n        st.warning(")]),
    ("el aviso de ABN no mira el ABN", IU,
     [('_sin_abn = not str(_CB.identidad(grupo).get("abn") or "").strip()', "_sin_abn = False")]),
    ("el detalle de la factura deja de avisar junto al PDF", IU,
     [('            if not str(_CB.identidad(grupo).get("abn") or "").strip():\n                st.caption(',
       "            if False:\n                st.caption(")]),
    ("⚠️ lo recibido vuelve a ser lo pedido", O,
     [('return _num(g.get("Amount"))', 'return _num(o.get("Amount"))')]),
    ("la diferencia de lo recibido no se dice", PU,
     [('if _rv is not None and abs(_rv - _n(o.get("Amount"))) > 0.005:', "if False:")]),
    ("una orden recibida no mira lo recibido", PU,
     [("                if _est == O.RECIBIDA:\n                    _rv = O.valor_recibido(o)",
       "                if False:\n                    _rv = O.valor_recibido(o)")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", Q,
           [("# v664: el plano con que se cotizó", "# v664 (control): el plano con que se cotizó")])


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
