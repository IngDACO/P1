# -*- coding: utf-8 -*-
"""Batería de roturas de v702. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v702"
TOPE_S = 240
CLs, CU, IN, IU, PD = "core/claims.py", "core/claims_ui.py", "core/invoices.py", "core/invoices_ui.py", "core/claim_pdf.py"

ROTURAS = [
    ("la certificación ya no recupera el depósito", CLs,
     [('    _menos_dep = round(max(0.0, min(_dp["pendiente"], _dp["deposito"] * pct / 100.0 - _dp["recuperado"])), 2)',
       '    _menos_dep = 0.0')]),
    ("el neto no resta el depósito", CLs,
     [('"neto": round(_bruto - _ret - _menos_dep, 2),', '"neto": round(_bruto - _ret, 2),')]),
    ("una factura anulada cuenta como depósito", CLs,
     [('        return [f for f in _I.list_facturas(grupo) if str(f.get("Status", "")).lower() != "anulada"]',
       '        return [f for f in _I.list_facturas(grupo)]')]),
    ("emitir la certificación ya no emite su factura", CLs,
     [('    ok_f, num_f = _emitir_factura(pid, grupo, _ls, prj, creado_por, nota)',
       '    ok_f, num_f = True, "—"')]),
    ("si la factura falla, la certificación se queda", CLs,
     [('            _set(w, _CCOL, _f, {"Status": ANULADA})\n        _invalidate()\n        return False, t("The claim could not',
       '            pass\n        _invalidate()\n        return False, t("The claim could not')]),
    ("anular con cobros en su factura no se para", CLs,
     [('        if round(_num(_fac.get("Collected")), 2) > 0:', '        if False:')]),
    ("anular la certificación deja viva su factura", CLs,
     [('        ok_v, msg_v = _I.anular(str(_fac.get("ID", "")), _desde_reclamacion=True)',
       '        ok_v, msg_v = True, ""')]),
    ("Invoices anula la factura de una certificación que no es la última", IN,
     [('            if _r and not _ok_u and str(_r.get("Status", "")) != _CL.ANULADA:', '            if False:')]),
    ("anular en Invoices no cancela su certificación", IN,
     [('            _CL.anular(_c, _con_factura=False)', '            pass')]),
    ("el PDF pierde «Less deposit recovered»", PD,
     [('        if _mdep > 0:\n            _filas_c.append', '        if False:\n            _filas_c.append')]),
    ("el neto del PDF no resta el depósito", PD,
     [('[d("NET AMOUNT PAYABLE"), _money(_bruto - _mdep - _ret)]', '[d("NET AMOUNT PAYABLE"), _money(_bruto - _ret)]')]),
    ("vuelve «Mark paid» aunque haya factura", CU,
     [('                    elif b1.button(t("Mark paid"), key=f"{key_prefix}_pay_{r.get(\'ID\')}"):',
       '                    if b1.button(t("Mark paid"), key=f"{key_prefix}_pay_{r.get(\'ID\')}"):')]),
    ("New invoice ya no resta el depósito de las líneas de la cotización", IU,
     [('            if _num((_dep1 or {}).get("pendiente")) > 0:', '            if False:')]),
    ("tras un depósito, «Invoice it as» vuelve a desaparecer", IU,
     [('            if I.es_cotizada(_pid1) and _solo_dep:',
       '            if I.es_cotizada(_pid1) and _num(I.facturado_por_proyecto(grupo).get(_pid1, 0)) <= 0.005:')]),
    ("«Amount» vuelve a no admitir negativos", IU,
     [('                t("Amount"), format="$%,.2f",\n', '                t("Amount"), format="$%,.2f", min_value=0.0,\n')]),
    ("una factura de total ≤ 0 se emite", IU,
     [("        if _sub <= 0:", "        if False:")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CLs,
           [("# v702 · D3 del ciclo 7 («como se hace normalmente»): la certificación ES la factura",
             "# v702 · D3 del ciclo 7 («como se hace normalmente»): la certificación ES la factura · control")])


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
