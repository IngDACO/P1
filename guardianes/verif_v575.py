# -*- coding: utf-8 -*-
"""v575 · NADA PENDIENTE (decisión del usuario: «No me dejes nada pendiente»).

  1. El panel del propietario decía que el nombre legal y el ABN salen «en la factura»: salen
     también en la colilla (v574) y en la cotización (abajo). Y sus selectores llevaban el
     marcador vacío en español y sin `t()` («— elige un grupo —», cinco veces).
  2. La COTIZACIÓN (PDF): fechas ISO y la cabecera con el identificador interno del grupo
     («cliente1») → DD/MM/YYYY y el nombre legal + ABN (lo que la factura lleva desde v483).
  3. La LISTA de Contacts: las cuatro cifras eran `st.metric` que no se podían tocar → botones
     que filtran (con el selector recordado de Invoices/Payroll); abrir era con la casilla →
     un toque en cualquier celda, con generación de clave (trampa 31).
"""
import ast
import io
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUAR = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


# ══════════════════════════════════════════════════════════════════════════════
print("1. El panel del propietario")
_au = ast.parse(io.open(os.path.join(RAIZ, "core", "auth_ui.py"), encoding="utf-8").read())
_vac = [k.value for n in ast.walk(_au) if isinstance(n, ast.Call)
        for k in n.keywords if k.arg == "vacio"]
chk("⚠️ todos los marcadores vacíos pasan por `t()` (había cinco «— elige un grupo —»)",
    len(_vac) >= 8 and all(isinstance(v, ast.Call) and getattr(v.func, "id", "") == "t" for v in _vac),
    [ast.unparse(v)[:40] for v in _vac if not (isinstance(v, ast.Call) and getattr(v.func, "id", "") == "t")])
_txt = [c.value for n in ast.walk(_au) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "t"
        for c in n.args[:1] if isinstance(c, ast.Constant) and isinstance(c.value, str)
        and "TAX INVOICE" in c.value]
chk("el texto de la identidad fiscal nombra la colilla y la cotización (decía solo la factura)",
    _txt and "payslip" in _txt[0] and "quote" in _txt[0], _txt)

# ══════════════════════════════════════════════════════════════════════════════
print("\n2. La cotización (PDF)")
from core import quote_pdf, contable                                       # noqa: E402
from pypdf import PdfReader                                                # noqa: E402
_ct0 = contable.identidad
contable.identidad = lambda g: {"legal": "Acme Lifts Pty Ltd", "abn": "12 345 678 901", "plazo": 14}
try:
    _q = {"ID": "Q1", "Group": "cliente1", "Number": "Q-0001", "Date": "2026-10-13",
          "ValidUntil": "2026-11-12", "Subtotal": "100", "Tax": "10", "TaxPct": "10", "Total": "110",
          "ClientName": "Cliente", "LinesJSON": "[]"}
    _t = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(quote_pdf.generate_quote_pdf(_q, None, "cliente1"))).pages)
    chk("⚠️ el emisor con su nombre legal y su ABN (decía «cliente1»)",
        "Acme Lifts Pty Ltd" in _t and "ABN 12 345 678 901" in _t and "cliente1" not in _t, _t[:200])
    chk("⚠️ fechas DD/MM/YYYY (fecha, validez y el pie que la repite)",
        "13/10/2026" in _t and _t.count("12/11/2026") >= 2 and "2026-10-13" not in _t and "2026-11-12" not in _t,
        re.findall(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}", _t))
    contable.identidad = lambda g: {"legal": "cliente1", "abn": "", "plazo": 14}
    _t = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(quote_pdf.generate_quote_pdf(_q, None, "cliente1"))).pages)
    chk("sin nombre legal configurado, cae al nombre del grupo (y sin línea de ABN)",
        "cliente1" in _t and "ABN" not in _t)
finally:
    contable.identidad = _ct0

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. La lista de Contacts")
from streamlit.testing.v1 import AppTest                                    # noqa: E402

_t5 = ast.parse(io.open(os.path.join(GUAR, "verif_v571.py"), encoding="utf-8").read())
CAB = next(n.value.value for n in _t5.body if isinstance(n, ast.Assign)
           and getattr(n.targets[0], "id", "") == "CAB")
# «Otro» tiene ficha y ninguna obra; «Cliente Uno», ficha y tres obras: los dos filtros se ven
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_LISTA"] = True
at.run()
chk("la lista se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_kb = {b.key: b.label for b in at.button if str(b.key).startswith("cpxkpi_clis_")}
chk("⚠️ cuatro cifras-BOTÓN (eran `st.metric`)",
    list(_kb) == ["cpxkpi_clis_tot", "cpxkpi_clis_con", "cpxkpi_clis_sin", "cpxkpi_clis_prj"]
    and not at.metric, list(_kb))
chk("…con sus valores: 2 clientes, 2 con ficha, 0 sin ficha, 3 obras",
    [v.split("\n\n")[1] for v in _kb.values()] == ["2", "2", "0", "3"], list(_kb.values()))
[b for b in at.button if b.key == "cpxkpi_clis_prj"][0].click()
at.run()
_v = at.dataframe[0].value
chk("⚠️ «Projects» filtra: solo el cliente CON obras", list(_v["Cliente"]) == ["Cliente Uno"]
    and at.session_state["cpxseg_clis_filt"] == "ConObras", list(_v["Cliente"]))
[b for b in at.button if b.key == "cpxkpi_clis_sin"][0].click()
at.run()
chk("«No record» sin ninguno: lo dice", any("No client matches the search or the filter." in i.value
                                            for i in at.info) and not at.dataframe)
_rd = [r for r in at.radio if r.key == "cpxseg_clis_filt"]
# ⚠️ v602 · «persist_state» EN EL FICHERO ya no prueba nada: la búsqueda y la casilla también
# lo llevan, y quitarlo del filtro escapaba (trampa 2, grep ≠ uso) → el `key=` de ESA llamada
_radio_pers = [n for n in ast.walk(ast.parse(io.open(os.path.join(RAIZ, "core", "clientes_ui.py"),
                                                       encoding="utf-8").read()))
               if isinstance(n, ast.Call) and ast.unparse(n.func) == "st.radio"
               and any(k.arg == "key" and ast.unparse(k.value) == "'cpxseg_clis_filt'" for k in n.keywords)]
chk("…con el selector All · With record · No record · With jobs, RECORDADO",
    _rd and list(_rd[0].options) == ["All", "With record", "No record", "With jobs"]
    and len(_radio_pers) == 1 and any(k.arg == "persist_state" for k in _radio_pers[0].keywords),
    _rd[0].options if _rd else None)
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_LISTA"] = True
at.run()
_df = at.dataframe[0]
_cj = json.loads(_df.proto.columns)
_enum = _df.proto.DESCRIPTOR.fields_by_name["selection_mode"].enum_type
chk("⚠️ un toque en cualquier celda (era la casilla) y el cliente FIJADO",
    [_enum.values_by_number[x].name for x in _df.proto.selection_mode] == ["SINGLE_CELL"]
    and _cj.get("Cliente", {}).get("pinned") is True, _cj.get("Cliente"))
at = AppTest.from_string(CAB, default_timeout=90)
at.session_state["_LISTA"] = True
at.session_state["_PRE"] = {}
at.run()
at.session_state["cli_tbl_0"] = {"selection": {"rows": [], "columns": [], "cells": [(0, "Phone")]}}
at.run()
chk("⚠️ tocar la 1ª fila abre ESA ficha, con otra generación de clave",
    # (v602 · se abre por su ID: el nombre solo es el respaldo de lo que no tiene ficha)
    at.session_state["_cli_open"] == "CLI-1" and at.session_state["_cli_tbl_gen"] == 1
    if "_cli_open" in at.session_state else False)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
