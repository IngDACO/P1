# -*- coding: utf-8 -*-
"""Batería de roturas de v670. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v670"
TOPE_S = 500
QU = "core/quotes_ui.py"
OR = "core/orders.py"
EX = "core/expenses.py"
PU = "core/projects_ui.py"
CU = "core/claims_ui.py"
CL = "core/claims.py"
RO = "core/roster.py"
IN = "core/invoices.py"
IU = "core/invoices_ui.py"

ROTURAS = [
    ("⚠️ H6 · «Mark as sent» vuelve a no guardar antes", QU,
     [('            ok, msg = True, ""\n            if _cambia:\n', '            ok, msg = True, ""\n            if False:\n')]),
    ("H6 · el botón deja de decir «Save and mark as sent»", QU,
     [('_lbl_env = (t(":material/send: Save and mark as sent") if _cambia',
       '_lbl_env = (t(":material/send: Save and mark as sent") if False')]),
    ("H7 · reabrir deja la orden cancelada", OR,
     [('    ok, err = _set(w, row, {"Status": PENDIENTE})\n', '    ok, err = _set(w, row, {"Status": CANCELADA})\n')]),
    ("⚠️ H9 · deshacer la recepción no quita el gasto", OR,
     [("        ok_e, msg_e = E.delete(gid, de_orden=True)\n", '        ok_e, msg_e = True, ""\n')]),
    ("H9 · deshacer la recepción deja el gasto apuntado en la orden", OR,
     [('{"Status": PENDIENTE, "ExpenseID": "", "ReceivedDate": ""}', '{"Status": PENDIENTE, "ReceivedDate": ""}')]),
    ("⚠️ H9 · el gasto de una orden se puede borrar suelto", EX,
     [("    if not de_orden:\n        try:\n            from core import orders as _O\n",
       "    if False:\n        try:\n            from core import orders as _O\n")]),
    ("H8 · adjuntar no escribe el fichero", EX,
     [("                    {\"range\": f\"{_col_letter(_ECOL['DriveID'])}{i + 2}\", \"values\": [[str(drive_id)]]},\n", "")]),
    ("⚠️ H7 · «Cancel» vuelve a cancelar sin preguntar", PU,
     [('                        st.session_state[f"_{key_prefix}_ordconf"] = ("cancelar", _oid)\n',
       '                        O.cancelar(_oid)\n')]),
    ("H7 · desaparece «Reopen»", PU,
     [("                if editable and _est == O.CANCELADA:\n", "                if False:\n")]),
    ("H9 · desaparece «Undo the receipt»", PU,
     [('                if editable and _est == O.RECIBIDA and str(o.get("ExpenseID", "")).strip():\n'
       '                    if st.button(t(":material/undo: Undo the receipt")',
       '                if False:\n'
       '                    if st.button(t(":material/undo: Undo the receipt")')]),
    ("⚠️ H9 · el gasto de una orden vuelve a tener papelera", PU,
     [("if can_delete and not _ord and cc[1].button(", "if can_delete and cc[1].button(")]),
    ("⚠️ H9 · la papelera vuelve a borrar sin preguntar", PU,
     [('                    st.session_state[f"_{key_prefix}_delconf"] = _rid\n', "                    E.delete(_rid)\n")]),
    ("H8 · el gasto de una orden vuelve a «no receipt»", PU,
     [("                elif _ord:\n                    cc[0].caption(", "                elif False:\n                    cc[0].caption(")]),
    ("H8 · desaparece «Attach the supplier invoice»", PU,
     [("                if can_delete and _ord and not _did:\n", "                if False:\n")]),
    ("⚠️ H13 · la vista previa ignora el % escrito", CU,
     [('            dv = d if abs(_pct - float(d["pct"])) < 1e-9 else CL.calcular(pid, grupo, _pct, prj)\n',
       "            dv = d\n")]),
    ("⚠️ H13 · certificar más de lo hecho deja de avisar", CU,
     [('            if _pct > float(d["pct"]) + 1e-9 and dv["bruto"] > 0:\n', "            if False:\n")]),
    ("H21 · una obra cancelada vuelve a certificar", CU,
     [("        if _cancelada:\n            # ⚠️ v670 · una obra CANCELADA ya no certifica",
       "        if False:\n            # ⚠️ v670 · una obra CANCELADA ya no certifica")]),
    ("⚠️ H21 · «Cancel» de una certificación vuelve a anular sin preguntar", CU,
     [('                        st.session_state[f"_{key_prefix}_clmconf"] = r.get("ID")\n',
       '                        CL.anular(r.get("ID"))\n')]),
    ("H21 · las anuladas vuelven a desaparecer", CU,
     [("        _todas = CL.reclamaciones(pid, incluir_anuladas=True)\n", "        _todas = CL.reclamaciones(pid)\n")]),
    ("H21 · la retención de una cancelada vuelve a esperar al 100 %", CL,
     [("    if P.es_cancelada(_prj):\n", "    if False:\n")]),
    ("dias_desde cuenta también el pasado", RO,
     [("if _f is not None and _f >= desde and str(pid)", "if _f is not None and str(pid)")]),
    ("⚠️ limpiar_proyecto(desde) borra también el pasado", RO,
     [("                if _f is None or _f < desde:\n                    continue\n",
       "                if False:\n                    continue\n")]),
    ("H18 · la lista de lo abierto olvida las facturas", PU,
     [('                if any(str(ln.get("proyecto_id", "")) == str(pid) for ln in _I.lineas_de(f)):\n',
       "                if False:\n")]),
    ("H18 · la lista de lo abierto olvida el tablero", PU,
     [("        _d = _R.dias_desde(grupo, pid, clock.today(grupo))\n        if _d:\n",
       "        _d = {}\n        if _d:\n")]),
    ("⚠️ H18 · cancelar vuelve a guardarse sin preguntar", PU,
     [('if est_man in ("Cancelled", "On hold") and est_man != str(prj.get("ManualStatus", "") or ""):',
       'if False:')]),
    ("⚠️ H18 · el aviso de cancelar vuelve al genérico", PU,
     [('    _txt = {"Cancelled": "This job has been cancelled. You are off it from today.",',
       '    _txt = {"Cancelled": "The project details were updated.",')]),
    ("H18 · «Yes, cancel it» no libera el tablero", PU,
     [('cierre=pend["est"], liberar=_lib)', 'cierre=pend["est"], liberar=False)')]),
    ("los avisos de cobros vuelven sin miles", IN,
     [('    return "${:,.2f}".format(round(_num(v), 2))\n', '    return "$%.2f" % round(_num(v), 2)\n')]),
    ("el historial vuelve al login", IU,
     [('        _por = _nombre_de(str(cb.get("por", "") or ""))\n', '        _por = str(cb.get("por", "") or "")\n')]),
    ("⚠️ obra sin cotización: el aviso vuelve a sugerir una variación", IU,
     [("        elif I.es_cotizada(pid):\n", "        elif True:\n")]),
    ("la ficha vuelve a sugerir una variación sin cotización", PU,
     [("            if _INV.es_cotizada(pid):\n", "            if True:\n")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", OR,
           [("def reabrir(oid) -> tuple:\n", "def reabrir(oid) -> tuple:  # (control)\n")])


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
