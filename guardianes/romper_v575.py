# -*- coding: utf-8 -*-
"""Bateria de roturas de v575 («nada pendiente»). ⚠️ Verde de BASE primero (v459) y NO en
paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v575"
AU = "core/auth_ui.py"
QP = "core/quote_pdf.py"
CU = "core/clientes_ui.py"
TOPE_S = 300

ROTURAS = [
    ("el texto de la identidad fiscal vuelve a nombrar solo la factura", AU,
     [('"These appear on the invoice, quote and payslip PDFs. In Australia a "',
       '"These appear on the invoice PDF. In Australia a "')]),
    ("⚠️ un marcador vacío vuelve al español sin `t()`", AU,
     [('key="tz_g_sel", vacio=t("— choose a company —"))', 'key="tz_g_sel", vacio="— elige un grupo —")')]),
    ("⚠️ la cotización vuelve a «cliente1» (sin el nombre legal)", QP,
     [('    marca = str(_ident.get("legal") or "").strip() or grupo_nombre or _grp\n',
       "    marca = grupo_nombre or _grp\n")]),
    ("⚠️ la fecha de la cotización vuelve al ISO", QP,
     [('[Paragraph(d("Date"), sm), Paragraph(dmy(cot.get("Date")), H)],',
       '[Paragraph(d("Date"), sm), Paragraph(str(cot.get("Date", "")), H)],')]),
    ("el pie de la cotización vuelve al ISO", QP,
     [('v=dmy(cot.get("ValidUntil"))), sm)]', 'v=cot.get("ValidUntil", "")), sm)]')]),
    ("⚠️ las cifras de Contacts dejan de filtrar", CU,
     [('                st.session_state["_clis_filt_pending"] = _fl\n', "")]),
    ("el filtro «With jobs» deja de aplicarse", CU,
     [('    elif _filt == "ConObras":\n        rows = [r for r in rows if r["total"]]\n', "")]),
    ("el filtro deja de recordarse", CU,
     [('horizontal=True, key="cpxseg_clis_filt", label_visibility="collapsed",\n'
       '                     persist_state="session")',
       'horizontal=True, key="cpxseg_clis_filt", label_visibility="collapsed")')]),
    ("⚠️ abrir un cliente vuelve a pedir la casilla", CU,
     [('on_select="rerun", selection_mode="single-cell", key=f"cli_tbl_{_gen}",',
       'on_select="rerun", selection_mode="single-row", key=f"cli_tbl_{_gen}",')]),
    ("al volver, la tabla reabriría el mismo cliente (sin generación)", CU,
     [('        st.session_state["_cli_tbl_gen"] = _gen + 1\n', "")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CU,
           [('_FILTROS_CLI = {"Todos": "All", "ConFicha": "With record", "SinFicha": "No record",\n',
             '_FILTROS_CLI = {"Todos": "All", "ConFicha": "With record", "SinFicha": "No record",  # (control)\n')])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
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
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc))
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
