# -*- coding: utf-8 -*-
"""Bateria de roturas de v574 (Finance → Payroll). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de
cambios (v526). Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).

⚠️ Las marcadas devuelven lo visto en producción con las colillas de prueba.
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v574"
PU = "core/payroll_ui.py"
PR = "core/payroll.py"
PP = "core/payslip_pdf.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── la lista ──
    ("⚠️ las cifras dejan de filtrar", PU,
     [('                st.session_state["_nom_filt_pending"] = _fl\n', "")]),
    ("⚠️ las anuladas vuelven a desaparecer", PU,
     [("    noms = payroll.list_nominas(grupo, incluir_anuladas=True)\n",
       "    noms = payroll.list_nominas(grupo)\n")]),
    ("⚠️ vuelve el homónimo FALSO (una entrada por colilla)", PU,
     [('    _et = _A.etiqueta_usuarios(list({str(x.get("User", "")): {"User": x.get("User"), "Name": x.get("Name")}\n'
       '                                     for x in noms}.values()))\n',
       '    _et = _A.etiqueta_usuarios([{"User": x.get("User"), "Name": x.get("Name")} for x in noms])\n')]),
    ("⚠️ el neto vuelve sin céntimos (valor)", PU,
     [('        "Neto":     round(_num(x.get("Net")), 2),', '        "Neto":     round(_num(x.get("Net")), 0),')]),
    ("…y el formato vuelve a `$%,d`", PU,
     [('"Neto": st.column_config.NumberColumn(t("Net"), format="$%,.2f"),',
       '"Neto": st.column_config.NumberColumn(t("Net"), format="$%,d"),')]),
    ("⚠️ el periodo vuelve al ISO", PU,
     [("    return f\"{_dmy(x.get('PeriodFrom'))} → {_dmy(x.get('PeriodTo'))}\"\n",
       "    return f\"{x.get('PeriodFrom', '')} → {x.get('PeriodTo', '')}\"\n")]),
    ("abrir una colilla vuelve a pedir la casilla", PU,
     [('on_select="rerun", selection_mode="single-cell", key=f"nom_tbl_{_gen}",',
       'on_select="rerun", selection_mode="single-row", key=f"nom_tbl_{_gen}",')]),
    # ── anular y pagar ──
    ("⚠️ «Void this payslip» vuelve a anular SIN preguntar", PU,
     [('                elif st.button(t("Void this payslip"), key=f"nom_anul_{nid}"):\n'
       '                    st.session_state["_nom_conf"] = ("anular", nid)\n',
       '                elif st.button(t("Void this payslip"), key=f"nom_anul_{nid}"):\n'
       '                    st.session_state["_nom_accion"] = {"accion": "anular", "nid": nid}\n')]),
    ("⚠️ anular vuelve a NO avisar", PU,
     [("    (flash.exito if _ok else flash.error)(_msg)\n    st.rerun()\n", "    st.rerun()\n")]),
    ("⚠️ …o avisa un clic TARDE (sin relanzar)", PU,
     [("    (flash.exito if _ok else flash.error)(_msg)\n    st.rerun()\n",
       "    (flash.exito if _ok else flash.error)(_msg)\n")]),
    ("⚠️ el motor vuelve a anular una PAGADA", PR,
     [('    if str((get_nomina(nid) or {}).get("Status", "")).lower() == "pagada":\n',
       "    if False:\n")]),
    ("deshacer el pago deja la fecha puesta", PR,
     [("""            {"range": f"{_col_letter(_NCOL['PaymentDate'])}{row}", "values": [[""]]},""",
       """            {"range": f"{_col_letter(_NCOL['PaymentDate'])}{row}", "values": [["2026-10-13"]]},""")]),
    # ── el detalle ──
    ("⚠️ el estado vuelve CRUDO en la línea del periodo («emitida»)", PU,
     [("e=f\"{_EST_ICONO.get(est, '')} {_etq(est)}\".strip()))", "e=est))")]),
    ("⚠️ el editor vuelve a enseñar el tipo interno («deduccion»)", PU,
     [('             "Type": _TL.get(str(c.get("tipo", "deduccion")), str(c.get("tipo", ""))),',
       '             "Type": str(c.get("tipo", "")),')]),
    ("el concepto vuelve a comerse el ancho (tipo e importe fuera)", PU,
     [('            "Concepto": st.column_config.TextColumn(t("Item")),',
       '            "Concepto": st.column_config.TextColumn(t("Item"), width="large"),')]),
    # ── la colilla ──
    ("⚠️ la colilla vuelve a «cliente1» (sin el nombre legal)", PP,
     [('    marca = str(_ident.get("legal") or "").strip() or grupo_nombre or _grp\n',
       "    marca = grupo_nombre or _grp\n")]),
    ("⚠️ la colilla vuelve a «pagada (2026-…)»", PP,
     [("        _est_txt += f\" ({dmy(nomina.get('PaymentDate'))})\"\n",
       "        _est_txt = f\"pagada ({nomina.get('PaymentDate')})\"\n")]),
    ("el archivo vuelve a «Colilla_…»", PU,
     [("file_name=f\"Payslip_{f.get('Name', '')}_{f.get('PeriodTo', '')}.pdf\",",
       "file_name=f\"Colilla_{f.get('Name', '')}_{f.get('PeriodTo', '')}.pdf\",")]),
    # ── generar ──
    ("⚠️ la tarifa de la vista previa vuelve a TRUNCAR (`$%,d`)", PU,
     [('"Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f"),',
       '"Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,d"),')]),
    ("⚠️ quien no tiene tarifa vuelve a descubrirse DESPUÉS", PU,
     [("        if _sin:\n            st.warning(", "        if False:\n            st.warning(")]),
    ("un texto de generar vuelve sin `t()`", PU,
     [('st.markdown(t("**{n} user(s)** with workday hours in the period:", n=len(horas)))',
       'st.markdown(f"**{len(horas)} user(s)** with workday hours in the period:")')]),
    ("una fecha de generar vuelve al formato por defecto", PU,
     [('desde = c1.date_input(t("From"), value=_d0, key=f"nom_desde_{per}", format="DD/MM/YYYY")',
       'desde = c1.date_input(t("From"), value=_d0, key=f"nom_desde_{per}")')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("    return t(\"no rate — will be skipped\") if _num(r) <= 0 else \"\"\n",
             "    return t(\"no rate — will be skipped\") if _num(r) <= 0 else \"\"   # (control)\n")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
