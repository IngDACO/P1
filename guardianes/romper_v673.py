# -*- coding: utf-8 -*-
"""Batería de roturas de v673. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v673"
TOPE_S = 500
CT = "core/chat_tools.py"
PR = "core/projects.py"
PU = "core/projects_ui.py"
CU = "core/clientes_ui.py"
HU = "core/home_ui.py"

ROTURAS = [
    # ── H1 · get_money ──
    ("⚠️ H1 · la obra deja de decir lo facturado", CT,
     [('                "invoiced_ex_tax": round(_num(INV.facturado_por_proyecto(g).get(pid, 0.0)), 2),\n', "")]),
    ("H1 · las facturas de la obra incluyen las de otras obras", CT,
     [('                  if any(str(ln.get("proyecto_id", "")).strip() == pid for ln in INV.lineas_de(f))]',
       "                  ]")]),
    ("H1 · lo de la obra cuenta la factura entera", CT,
     [('    _esta = sum(_num(ln.get("importe")) for ln in INV.lineas_de(f) if str(ln.get("proyecto_id", "")).strip() == str(pid))',
       '    _esta = sum(_num(ln.get("importe")) for ln in INV.lineas_de(f))')]),
    ("⚠️ H1 · lo cobrado en una anulada cuenta como cobrado", CT,
     [('            c["collected_on_voided_invoices"] += _cob\n            continue\n',
       '            c["collected_on_voided_invoices"] += _cob\n')]),
    # ⚠️ RETIRADA en la 1ª tanda: «una cobrada cuenta como por cobrar» escapaba porque la condición no protegía
    # nada (en una cobrada, total − cobrado ya es 0). Se quitó la condición del código, y con ella la rotura.
    ("H1 · lo vencido no se separa", CT,
     [('        if _est == "vencida":\n            c["overdue"]', '        if False:\n            c["overdue"]')]),
    ("H1 · la empresa sin el desglose por cliente", CT,
     [('            "by_client_all_time": _por_cliente(g),\n', "")]),
    ("H1 · sin la regla de no inventar causas", CT,
     [('                "how_to_read": _COMO_LEER_DINERO}', "                }")]),
    ("H1 · la descripción no lo anuncia (el modelo no lo pediría)", CT,
     [('what was invoiced (and each invoice with "\n                    "its status and what was collected)',
       'estimated profit"\n                    " and')]),
    # ── H2 · Pre-Start ──
    ("⚠️ H2 · una obra terminada vuelve a pedir el Pre-Start", CT,
     [('    if P.es_completada(prj) or str((prj or {}).get("Status", "")) in ("Cancelled", "On hold", "Archived"):',
       '    if str((prj or {}).get("Status", "")) in ("Cancelled", "On hold", "Archived"):')]),
    ("H2 · una cancelada vuelve a pedirlo", CT,
     [('in ("Cancelled", "On hold", "Archived"):', 'in ("On hold", "Archived"):')]),
    ("H2 · no dice por qué", CT,
     [('"false_car_check": "not_required", "why": f"the job is {_por}"}', '"false_car_check": "not_required"}')]),
    # ── H3 · terminada ──
    ("⚠️ H3 · fecha_terminada da la PRIMERA fecha", PR,
     [("    return max(fechas) if fechas else None", "    return min(fechas) if fechas else None")]),
    ("H3 · fecha_terminada no exige el 100 %", PR,
     [("        if _num(a.get(\"Progress\")) < 99.95:\n            return None\n", "")]),
    ("⚠️ H3 · fin_de_obra vuelve al fin estimado", PR,
     [("    if es_completada(p):\n        _f = fecha_terminada(", "    if False:\n        _f = fecha_terminada(")]),
    ("H3 · es_completada olvida el 100 %", PR,
     [('    return _num((p or {}).get("Progress")) >= 99.95 or str((p or {}).get("Status", "")) == "Completed"',
       '    return str((p or {}).get("Status", "")) == "Completed"')]),
    ("H3 · el asistente vuelve al fin estimado en una lista", CT,
     [("         **_fin_de_obra(p), \"assigned\": _asignados(p, nom),",
       "         \"estimated_finish\": dmy(p.get(\"EndDateEst\", \"\")), \"assigned\": _asignados(p, nom),")]),
    ("⚠️ H3 · la ficha de una terminada vuelve a «Projected finish»", PU,
     [("    if _hecha:                     # v673 · H3", "    if False:                     # v673 · H3")]),
    ("H3 · el titular de una terminada vuelve a los puntos", PU,
     [("    if _hecha:\n        _tit_html, _col = ((t(\"The job <b>finished on {f}</b>\")",
       "    if False:\n        _tit_html, _col = ((t(\"The job <b>finished on {f}</b>\")")]),
    ("⚠️ la cancelada vuelve a proyectar", PU,
     [('    _quieta = (not _hecha) and (P.es_cancelada(prj) or str(prj.get("Status", "")) == "On hold")',
       "    _quieta = False")]),
    ("la cancelada vuelve a enseñar la actividad parada", PU,
     [("        d = dict(d, paradas=[], arrastradas=[], en_curso=", "        d = dict(d, arrastradas=[], en_curso=")]),
    ("la pausa cuenta como en marcha", PU,
     [('(P.es_cancelada(prj) or str(prj.get("Status", "")) == "On hold")', "(P.es_cancelada(prj))")]),
    # ── H4 · ficha del cliente ──
    ("⚠️ H4 · la ficha del cliente vuelve a contar pausa y canceladas", CU,
     [("    activos = [x for x in proys if P.es_activa(x)]",
       '    activos = [x for x in proys if str(x.get("Status", "")) not in ("Completed", "Cancelled", "Archived")]')]),
    ("H4 · el pie vuelve a «not completed»", CU,
     [('("act", t("Active"), str(activos), t("planned/ongoing")),', '("act", t("Active"), str(activos), t("not completed")),')]),
    # ── H17 · asignaciones vigentes ──
    ("⚠️ H17 · avisa de una obra que ya acabó", PU,
     [("                if _fe and _fe < _hoy_v673:\n                    continue\n", "")]),
    ("H17 · avisa de una obra en pausa", PU,
     [("                if not P.es_activa(p):\n                    continue\n                _fe =",
       '                if str(p.get("Status", "")) in ("Completed", "Cancelled"):\n                    continue\n                _fe =')]),
    # ── el buscador con una cifra ──
    ("⚠️ «4» vuelve a pararlo la pantalla", HU,
     [("    if len(_norm_busq(qn)) < 2 and _num_documento(_norm_busq(qn)) is None:",
       "    if len(_norm_busq(qn)) < 2:")]),
    ("con una letra se busca todo", HU,
     [("    if len(_norm_busq(qn)) < 2 and _num_documento(_norm_busq(qn)) is None:",
       "    if not _norm_busq(qn):")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PR,
           [("def fecha_terminada(pid: str, acts: list = None):\n", "def fecha_terminada(pid: str, acts: list = None):  # (control)\n")])


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
