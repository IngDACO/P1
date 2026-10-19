# -*- coding: utf-8 -*-
"""Bateria de roturas de v584 (Finance → Accounting, probada acción por acción). ⚠️ Verde de
BASE primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.

La condición del desplegable en su clave (`exp_cont_jobs_{_ver}`) NO va aquí: AppTest no
guarda el estado de un desplegable como el navegador, así que la vigila verif_v547 (estático).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v584"
CM = "core/contable.py"
CU = "core/contable_ui.py"
XU = "core/xero_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ el aviso del ABN vuelve sin el sitio de verdad", CM,
     [('"and Australia requires it above $82.50. The account owner sets it "\n'
       '                        "in Administration → Groups → «Tax identity and payment terms»."))',
       '"and Australia requires it above $82.50."))')]),
    ("⚠️ vuelve el SEGUNDO aviso, con la ruta que no existe", CU,
     [("    # ⚠️ v584 · el aviso del ABN es UNO,",
       '    st.warning(t("This company has no ABN. Set it in Administration → Companies."))\n'
       "    # ⚠️ v584 · el aviso del ABN es UNO,")]),
    ("vuelve «with these 1 options»", CM,
     [('                        "BEFORE importing, or the file is rejected.", c=_c)\n'
       "                      if len(opciones) == 1 else\n",
       '                        "BEFORE importing, or the file is rejected.", c=_c)\n'
       "                      if False else\n")]),
    ("vuelve «the 1 jobs»", CM,
     [('        avisos.append(t("In MYOB, the job must already exist in the file.")\n'
       "                      if len(opciones) == 1 else\n",
       '        avisos.append(t("In MYOB, the job must already exist in the file.")\n'
       "                      if False else\n")]),
    ("⚠️ el error de Xero Payroll vuelve a dar una sola causa", "core/xero_nomina.py",
     [('            if st_ in (401, 403) or "authentication" in _e.lower():\n', "            if False:\n")]),
    ("vuelve el «todo_todo» en el nombre del fichero", CU,
     [('    _suf = f"{desde}_{hasta}" if desde and hasta else "all"\n',
       "    _suf = f\"{desde or 'todo'}_{hasta or 'todo'}\"\n")]),
    ("⚠️ «From» después de «To» vuelve a salir vacío sin decir nada", CU,
     [("    if desde and hasta and desde > hasta:\n", "    if False:\n")]),
    ("las cifras de arriba dejan de llevar a su pantalla", CU,
     [("                _PU._ir_a(*_dest)\n", "                pass\n")]),
    ("«Tracking options» deja de abrir la lista", CU,
     [('                    st.session_state["_cont_ver_jobs"] = not st.session_state.get("_cont_ver_jobs")\n',
       '                    st.session_state["_cont_ver_jobs"] = False\n')]),
    ("las cifras del parte dejan de llevar a Hours", CU,
     [('                _PU._ir_a("finanzas", "⏱ Horas")\n', "                pass\n")]),
    ("«Lines» deja de bajar a la tabla", CU,
     [('                    st.session_state["_cont_bajar_p"] = True\n', "")]),
    ("⚠️ «Payroll ID» vuelve a salir vacía", CU,
     [('        if not any(str(f["payroll_id"] or "").strip() for f in det["filas"]):\n',
       "        if False:\n")]),
    ("…o se quita también cuando alguien la tiene", CU,
     [('        if not any(str(f["payroll_id"] or "").strip() for f in det["filas"]):\n',
       "        if True:\n")]),
    ("el periodo deja de recordarse", CU,
     [('                   horizontal=True, key="cpxseg_cont_per", label_visibility="collapsed",\n'
       '                   persist_state="session")\n',
       '                   horizontal=True, key="cpxseg_cont_per", label_visibility="collapsed")\n')]),
    ("⚠️ «Approved» vuelve a decir «Saved.»", XU,
     [('             else t("Invoices will now arrive in Xero approved.")) if ok else msg)\n',
       '             else t("Saved.")) if ok else msg)\n')]),
    ("⚠️ «Bring payments» vuelve a ofrecerse sin nada enviado", XU,
     [('    if not any(str(f.get("XeroInvoiceID", "") or "").strip()\n'
       "               for f in _INV.list_facturas(grupo)):\n", "    if False:\n")]),
    ("una fecha vuelve sin DD/MM/YYYY", "core/timeclock_ui.py",
     [('key="olv_d", format="DD/MM/YYYY")', 'key="olv_d")')]),
    ("vuelve «1 rows»", CU,
     [('        return t("1 row") if n == 1 else t("{n} rows", n=n)\n', '        return t("{n} rows", n=n)\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", CU,
           [("def _parte_csv(grupo, desde, hasta):\n", "def _parte_csv(grupo, desde, hasta):   # (control)\n")])


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
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
