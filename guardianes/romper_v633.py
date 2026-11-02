# -*- coding: utf-8 -*-
"""Batería de roturas de v633. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v633"
TOPE_S = 180
M = "core/ausencias.py"
U = "core/ausencias_ui.py"
C = "core/credentials.py"
A = "core/auth_ui.py"
P = "core/projects_ui.py"

ROTURAS = [
    # ── El dinero ──
    ("⚠️⚠️ la nómina vuelve a pagar lo que pasa del saldo", M,
     [("              if d0 <= d <= d1 and d not in _no]\n        if not _d:\n", "              if d0 <= d <= d1]\n        if not _d:\n")]),
    ("⚠️ sin decidir se paga", M,
     [('    return {a: set(d) for a, d in m.items() if a not in pagados}\n', '    return {}\n')]),
    ("«Pay them» no paga", M,
     [('               if str(r.get("OverBalancePay", "")).strip() == EXCESO_PAGA}\n', '               if False}\n')]),
    ("⚠️ el exceso son los primeros días, no los últimos", M,
     [("    gastados, p, out = {}, None, {}\n    for r in filas:\n        for d in dias_del_rango(r.get(\"From\"), r.get(\"To\"), incluye_findes(r)):\n",
       "    gastados, p, out = {}, None, {}\n    for r in filas:\n        for d in reversed(dias_del_rango(r.get(\"From\"), r.get(\"To\"), incluye_findes(r))):\n")]),
    ("⚠️ el saldo no se reinicia por periodo", M,
     [('            if gastados.get(p["desde"], 0) < tope:\n                gastados[p["desde"]] = gastados.get(p["desde"], 0) + 1\n',
       '            if gastados.get(0, 0) < tope:\n                gastados[0] = gastados.get(0, 0) + 1\n')]),
    ("⚠️ también se recortan las vacaciones", M,
     [('    if tope <= 0 or cfg.get("aprobacion", True):\n        return {}\n', '    if tope <= 0:\n        return {}\n')]),
    ("cuenta lo que no está aprobado", M,
     [("""                    and str(r.get("Type", "")) == str(tipo)
                    and str(r.get("Status", "")) == APROBADA),
""", """                    and str(r.get("Type", "")) == str(tipo)),
""")]),
    ("⚠️ los días sin pagar gastan saldo", M,
     [("    _fuera = sin_pagar(grupo, usuario, tipo) if estado == APROBADA else {}\n", "    _fuera = {}\n")]),
    ("el aviso de Payroll no acota al periodo", M,
     [('        _d = [d for d in ex["dias"] if not (d0 and d1) or d0 <= d <= d1]\n', '        _d = list(ex["dias"])\n')]),
    ("una ya decidida sigue saliendo por decidir", M,
     [('        if _d and not ex["decision"]:\n', '        if _d:\n')]),
    ("⚠️ se decide una cancelada", M,
     [('    if str(recs[fila - 2].get("Status", "")) != APROBADA:\n        return False, t("That absence is no longer approved.")\n', '')]),
    ("⚠️ la decisión cae en otra columna", M,
     [("""{"range": f"{_cl(_COL['OverBalancePay'])}{fila}", "values": [[como]]},""", """{"range": f"{_cl(_COL['AdminNote'])}{fila}", "values": [[como]]},""")]),
    ("no queda quién decidió", M,
     [("""            {"range": f"{_cl(_COL['OverBalancePay'])}{fila}", "values": [[como]]},
            {"range": f"{_cl(_COL['ResolvedBy'])}{fila}", "values": [[str(quien)]]},
""", """            {"range": f"{_cl(_COL['OverBalancePay'])}{fila}", "values": [[como]]},
""")]),
    ("una decisión desconocida se escribe", M,
     [('    if como not in (EXCESO_PAGA, EXCESO_NO, ""):\n        return False, t("Unknown decision.")\n', '')]),
    ("⚠️ la fila del alta no casa con la cabecera", M,
     [('            ("SI" if incluir_findes else "NO"), ""]\n', '            ("SI" if incluir_findes else "NO")]\n')]),
    # ── La pantalla de la oficina ──
    ("⚠️ la baja vieja sin decidir se sale de la bandeja", U,
     [('              and ((_pd(r.get("To")) or hoy) >= hoy - timedelta(days=14)\n                   or str(r.get("ID")) in _sin_decidir)]\n',
       '              and (_pd(r.get("To")) or hoy) >= hoy - timedelta(days=14)]\n')]),
    ("⚠️ desaparecen los botones de decidir", U,
     [("    _decidir_exceso(r, donde)\n", "")]),
    ("el histórico repite los botones", U,
     [('    if donde == "hist":\n        return\n    b1, b2 = st.columns(2)\n', '    b1, b2 = st.columns(2)\n')]),
    ("«Pay them» apunta lo contrario", U,
     [("""key=f"ausexp_{donde}_{aid}", width="stretch"):
        st.session_state["_aus_accion"] = {"aid": aid, "exceso": AU.EXCESO_PAGA}""", """key=f"ausexp_{donde}_{aid}", width="stretch"):
        st.session_state["_aus_accion"] = {"aid": aid, "exceso": AU.EXCESO_NO}""")]),
    ("⚠️ no se avisa a la persona", U,
     [("        if _como:\n            _avisar_exceso(usuario, r, _como)\n", "")]),
    ("no se recuerda la colilla ya emitida", U,
     [('        if _como == AU.EXCESO_PAGA:\n            flash.info(t("If a payslip for those dates is already issued, void it and generate it "\n                         "again so they are included."))\n', '')]),
    ("el campo no ve cómo quedó", U,
     [('        if _ex["dias"]:\n            _n = _dias(len(_ex["dias"]))\n            _pie.append({AU.EXCESO_PAGA:', '        if False:\n            _n = _dias(len(_ex["dias"]))\n            _pie.append({AU.EXCESO_PAGA:')]),
    # ── Payroll ──
    ("⚠️ se quita el aviso de Payroll", "core/payroll_ui.py",
     [("    if _exc:\n        st.warning(t(\":material/rule: **Sick leave over the balance with no decision:**", "    if False:\n        st.warning(t(\":material/rule: **Sick leave over the balance with no decision:**")]),
    ("⚠️ falta importar `literal_md`", "core/payroll_ui.py",
     [("from core.maps import literal_md\n", "")]),
    ("el nombre va sin escapar", "core/payroll_ui.py",
     [("""f"{literal_md(x['nombre'])} ({len(x['dias'])} d)\"""", """f"{x['nombre']} ({len(x['dias'])} d)\"""")]),
    ("el parte de horas no avisa", "core/contable.py",
     [("        _exc = _AU2.excesos_por_decidir(grupo, d0, d1)\n", "        _exc = []\n")]),
    # ── Credenciales: el motor ──
    ("⚠️⚠️ vuelve el alta vacía", C,
     [("    _falta = falta_dato(tipo, numero, vencimiento)\n    if _falta:\n        return False, _falta\n    w = _ws()\n", "    w = _ws()\n")]),
    ("⚠️ el número deja de ser obligatorio", C,
     [('    if not str(numero or "").strip():\n        return t("The credential number is required.")\n', '')]),
    ("⚠️ el vencimiento deja de ser obligatorio", C,
     [('    if str(tipo or "").strip() not in SIN_VENCIMIENTO and not str(vencimiento or "").strip():\n', '    if False:\n')]),
    ("otro ticket se libra del vencimiento", C,
     [('SIN_VENCIMIENTO = ("White Card",)\n', 'SIN_VENCIMIENTO = ("White Card", "First Aid")\n')]),
    ("⚠️⚠️ una ficha vacía vuelve a hacer apto", C,
     [("""        matching = [c for c in creds if str(c.get("Type", "")).strip() == str(tipo).strip()
                    and completa(c)]
""", """        matching = [c for c in creds if str(c.get("Type", "")).strip() == str(tipo).strip()]
""")]),
    ("⚠️ editar deja vaciar los datos", C,
     [('            if {"Type", "Number", "ExpiryDate"} & set(fields):\n', '            if False:\n')]),
    ("⚠️ el aviso de vencimiento no puede apuntar en una incompleta", C,
     [('            if {"Type", "Number", "ExpiryDate"} & set(fields):\n', '            if True:\n')]),
    ("la matriz vuelve al español", C,
     [("""                fila[_tp] = _etq(next((e for e in ("vencido", "por_vencer", "vigente") if e in sts),
                                      "incompleta"))
""", """                fila[_tp] = next((e for e in ("vencido", "por_vencer", "vigente") if e in sts), "incompleta")
""")]),
    ("lo que no vence no está vigente", C,
     [('    return status(r.get("ExpiryDate")) or "vigente"\n', '    return status(r.get("ExpiryDate"))\n')]),
    # ── Credenciales: la pantalla ──
    ("⚠️ las cifras dejan de sumar", A,
     [('        _sts = [C.estado(r) for r in creds]\n', '        _sts = [C.status(r.get("ExpiryDate")) for r in creds]\n')]),
    ("⚠️ «Valid» no enseña lo que no vence", A,
     [('        _vis = [r for r in creds if not _f or C.estado(r) == _f]\n', '        _vis = [r for r in creds if not _f or C.status(r.get("ExpiryDate")) == _f]\n')]),
    ("no se cuentan las incompletas", A,
     [('        if _sts.count("incompleta"):\n            _kp.append(', '        if False:\n            _kp.append(')]),
    ("vuelve «s/n»", A,
     [("""f"{idmap[k].get('Number') or t('no number')} ({k})")""", """f"{idmap[k].get('Number') or 's/n'} ({k})")""")]),
    ("⚠️ el selector vuelve a ir por etiqueta: salta al corregir", A,
     [("""            idmap = {str(r.get("ID")): r for r in creds}
""", """            idmap = {f"{r.get('Number')}|{r.get('ID')}": r for r in creds}
""")]),
    ("no se corrige la emisión", A,
     [("""                                                 "IssueDate": eemi, "ExpiryDate": even,
""", """                                                 "ExpiryDate": even,
""")]),
    ("⚠️ borrar vuelve a ser de un toque", A,
     [("""                st.session_state[_kb] = _kid
                st.rerun()
""", """                C.delete(r.get("ID"))
                st.rerun()
""")]),
    ("⚠️ la ficha de Users no baja", A,
     [("""            _PU._bajar_a("cpx_gu_ficha", "_bajar_cpx_gu_ficha", bloque="start")\n""", "")]),
    ("la ficha baja en cada pasada", A,
     [("""        if st.session_state.get("_gu_tocado") != vista[_sr[0]]["User"]:
            st.session_state["_gu_tocado"] = vista[_sr[0]]["User"]
            st.session_state["_bajar_cpx_gu_ficha"] = True
""", """        st.session_state["_bajar_cpx_gu_ficha"] = True
""")]),
    ("⚠️ v634 · la persona ya abierta no baja", A,
     [("""    else:
        st.session_state.pop("_gu_tocado", None)
""", "")]),
    ("⚠️ v634 · la fila ya elegida no baja", P,
     [("""        else:
            st.session_state.pop("_arch_sel", None)        # v634 · como `_gu_tocado`
""", "")]),
    ("⚠️ v634 · vuelve la franja blanca", "core/theme.py",
     [("""[data-testid="stAppViewContainer"] {{ overflow: clip !important; }}\n""", "")]),
    ("v634 · vuelve el saldo negativo", U,
     [("""            _v = f"{max(s['disponibles'], 0):.0f}"\n""", """            _v = f"{s['disponibles']:.0f}"\n""")]),
    # ── Files y la campana ──
    ("⚠️ las acciones de Files no bajan", P,
     [("""                _bajar_a("cpx_arch_acc", "_bajar_cpx_arch_acc")\n""", "")]),
    ("⚠️ la campana no baja al aviso", "core/home_ui.py",
     [("""        st.session_state["_bajar_cpx_arch_espera"] = True    # v633 · al aviso, no arriba de la obra\n""", "")]),
    ("⚠️ se pierde la marca de la tabla", P,
     [("""            "Archivo": ("⏳ " if _espera(e) else "") + e["nombre"], "Tipo": e["label"],\n""", """            "Archivo": e["nombre"], "Tipo": e["label"],\n""")]),
    ("el campo ve la marca", P,
     [("""        return (puede_borrar and bool(e.get("run")) and bool(e.get("did"))\n""", """        return (bool(e.get("run")) and bool(e.get("did"))\n""")]),
    # ── La guía ──
    ("la guía no sabe de la decisión", "core/chat_agent.py",
     [("o **Leave them unpaid** en\n", "o déjalos sin pagar en\n")]),
    ("⚠️ cambia un botón y la guía no", U,
     [('t(":material/payments: Pay them")', 't(":material/payments: Pay")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", "core/chat_agent.py",
           [("# máximo de mensajes guardados en memoria (evita tokens infinitos)", "# (control) máximo de mensajes guardados en memoria")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for a, b in cambios:
        if txt.count(a) != 1:
            return False, bak, p, "ancla x%d: %s" % (txt.count(a), a[:60])
        txt = txt.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if not ok:
            print("  ESCAPA %s (%s)" % (desc, msg))
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
