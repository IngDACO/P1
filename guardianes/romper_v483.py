# -*- coding: utf-8 -*-
"""Prueba el guardián de v483 contra código ROTO.

Un guardián que solo aprueba no demuestra nada, y hace falta un CONTROL (un cambio
inocuo que debe seguir pasando) o uno que grite con cualquier edición tampoco distingue.

⚠️ NUNCA en paralelo con la suite: modifica ficheros del árbol de trabajo (la trampa
que fabricó 7 rojos falsos en v455).

⚠️ Y espaciado: cada corrida hace lecturas reales de Sheets y el techo son 60/min
(trampa nº19, que ya se cometió en v482 dentro del script que venía a verificar).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUARDIAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v483.py")

_NL = chr(10)   # ⚠️ nunca "\n" literal por heredoc: se convierte en un salto real

ROTURAS = [
    ("contable.py", "la 4a columna de MYOB vuelve a llevar el proyecto",
     _NL.join(['    return [c["contacto"], c["numero"], c["fecha"], "", c["descripcion"],']),
     '    return [c["contacto"], c["numero"], c["fecha"], c["referencia"], c["descripcion"],'),

    ("contable.py", "el impuesto se redondea linea a linea (no cuadra)",
     _NL.join(["    partes = [round(total * x / base, 2) for x in importes]",
               "    resto = round(total - sum(partes), 2)"]),
     _NL.join(["    partes = [round(total * x / base, 2) for x in importes]",
               "    resto = 0.0"])),

    ("contable.py", "el mapa SUSTITUYE en vez de fusionar",
     _NL.join(['            if k == "cuentas" and isinstance(v, dict):',
               "                for p, c in v.items():",
               '                    cfg["cuentas"].setdefault(p, {}).update(',
               '                        {kk: str(vv) for kk, vv in (c or {}).items()})']),
     _NL.join(['            if k == "cuentas" and isinstance(v, dict):',
               '                cfg["cuentas"] = {p: dict(c) for p, c in v.items()}'])),

    ("contable.py", "un solo mapa de cuentas para los dos perfiles",
     '    "myob": {VENTAS: "4-1000", "Materials": "5-1000", "Tools": "6-1000",',
     '    "myob": {VENTAS: "200", "Materials": "5-1000", "Tools": "6-1000",'),

    ("contable.py", "Xero pierde la columna obligatoria de vencimiento",
     '"*InvoiceDate", "*DueDate",',
     '"*InvoiceDate",'),

    ("contable.py", "el impuesto de venta pasa al CODIGO en vez del nombre",
     'cod, nombre = IMPUESTOS_XERO["venta_con" if pct else "venta_sin"]',
     _NL.join(['nombre, cod = IMPUESTOS_XERO["venta_con" if pct else "venta_sin"]'])),

    ("contable.py", "la opcion de seguimiento RECORTA en vez de usar el ID",
     _NL.join(["    if not etq or len(etq) > _MAX_OPCION:",
               '        return str(pid or "")',
               "    return etq"]),
     _NL.join(["    if not etq:",
               '        return str(pid or "")',
               "    return etq[:_MAX_OPCION]"])),

    ("contable.py", "una fila sin fecha se cuela en el periodo",
     _NL.join(["    d = _parse_date(f)", "    if not d:", "        return False"]),
     _NL.join(["    d = _parse_date(f)", "    if not d:", "        return True"])),

    ("contable.py", "vuelve a alcanzar el lector PRIVADO de expenses",
     "    gastos = [g for g in (expenses.list_group(grupo) or [])",
     "    gastos = [g for g in (expenses._records() or [])"),

    ("invoice_pdf.py", "el PDF deja de llevar el ABN",
     _NL.join(['    if str(_ident.get("abn") or "").strip():',
               "        _emisor.append(Paragraph(f\"{d('ABN')} {_ident['abn']}\", sm))"]),
     '    if False:' + _NL + "        pass"),

    ("invoices_ui.py", "el vencimiento vuelve a ser HOY",
     _NL.join(['    _venc = c2.date_input(t("Due date"),',
               "                          value=clock.today() + _timedelta(days=_plazo),",
               '                          key="fac_venc")']),
     '    _venc = c2.date_input(t("Due date"), value=clock.today(), key="fac_venc")'),

    ("home_ui.py", "la sub-seccion nueva se cuela la PRIMERA",
     _NL.join(['        ("📊 Resumen", ":material/insights: Summary"),']),
     _NL.join(['        ("📤 Contable", ":material/sync_alt: Accounting"),',
               '        ("📊 Resumen", ":material/insights: Summary"),'])),

    ("home_ui.py", "el despacho de la sub-seccion desaparece (cae al else)",
     _NL.join(['    elif sub == "📤 Contable":',
               "        from core.contable_ui import render_contable",
               "        render_contable(grupo)", ""]),
     ""),

    ("auth.py", "una columna nueva se mete en MEDIO de la cabecera",
     '                  "ABN", "LegalName", "PaymentTermsDays", "AccountingJSON"]',
     '                  "ABN", "LegalName", "AccountingJSON", "PaymentTermsDays"]'),

    # ── CONTROL: un cambio inocuo que DEBE seguir pasando ──
    ("contable.py", "CONTROL: solo un comentario nuevo",
     "logger = logging.getLogger(__name__)",
     _NL.join(["logger = logging.getLogger(__name__)",
               "# comentario inocuo del control"])),
]


def corre(espera=6):
    time.sleep(espera)
    r = subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


print("verde de BASE antes de romper nada:", "OK" if corre(0) == 0 else "*** ROJO ***")
print("(si esto sale rojo, la tanda de abajo no prueba NADA — leccion v459)")
print("")

cazadas = escapadas = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = io.open(ruta, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        print("  ??   %-58s ANCLA NO ENCONTRADA" % que[:58])
        escapadas += 1
        continue
    try:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        cod = corre()
    finally:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig)
    es_control = que.startswith("CONTROL")
    bien = (cod == 0) if es_control else (cod != 0)
    cazadas += 1 if bien else 0
    escapadas += 0 if bien else 1
    print("  %s %-58s (%s)" % ("ok  " if bien else "ESCAPA", que[:58],
                               "pasa" if cod == 0 else "rojo"))

print("")
print("%d correctas · %d mal" % (cazadas, escapadas))
sys.exit(0 if escapadas == 0 else 1)
