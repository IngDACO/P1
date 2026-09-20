# -*- coding: utf-8 -*-
"""Foto de las cifras del grupo, para comparar ANTES/DESPUÉS de un cambio.

⚠️ Los renombrados de F5c tocaron funciones que mueven DINERO (`payroll.neto`,
`finance.conciliacion_mo`, `finance.pnl`). Un `t` colgante ahí no da error: la
comparación sale siempre falsa y **las deducciones dejan de restarse del neto**.
Compilar y pasar los guardianes no lo detecta; lo detecta comparar los números.

⚠️ Se compara con el código VIEJO de verdad (`git stash`), no de memoria (v422).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import credentials, expenses, finance, inventory          # noqa: E402
from core import payroll, roster, timeclock                         # noqa: E402

G = "cliente1"
out = {}

# ── payroll: la función que el renombrado casi rompe en silencio ──
_cs = [{"tipo": "devengo", "monto": 100}, {"tipo": "deduccion", "monto": 30},
       {"tipo": "aporte", "monto": 50}]
out["neto_1000"] = payroll.neto(1000, _cs)
out["neto_solo_ded"] = payroll.neto(500, [{"tipo": "deduccion", "monto": 200}])
out["resumen_nominas"] = payroll.resumen(G)

# ── finance ──
_p = finance.pnl(G)
out["pnl"] = {k: _p[k] for k in ("facturado", "cobrado", "costo_nomina",
                                 "compras", "costo_total", "ganancia",
                                 "por_cobrar", "por_pagar", "vencido")}
_c = finance.conciliacion_mo(G)
out["concil"] = {k: _c.get(k) for k in ("cargado", "interno", "cobrado_no_pagado",
                                        "pagado_no_cargado", "base", "aportes",
                                        "costo_real", "sin_explicar")}
_rp = finance.group_profitability(G)
out["rentab"] = {"n": len(_rp.get("rows") or _rp.get("filas") or []),
                 "totales": {k: v for k, v in (_rp.get("totales") or {}).items()
                             if isinstance(v, (int, float))}}

# ── expenses / horas ──
out["gastos"] = {k: v for k, v in expenses.group_expenses(G).items()
                 if isinstance(v, (int, float))}
# ⚠️ `group_hours` devuelve una LISTA por persona, no un dict (regla v135).
_h = timeclock.group_hours(G)
out["horas"] = sorted(
    [{k: round(v, 4) for k, v in r.items() if isinstance(v, (int, float))}
     | {"usuario": r.get("usuario")} for r in _h],
    key=lambda r: str(r.get("usuario")))

# ── credentials / inventory / roster: lo que NO es dinero pero se renombró ──
_ts, _fs = credentials.matrix(G)
out["cred_matrix"] = [len(_ts), len(_fs), sorted(_ts)]
out["ubic"] = inventory.ubic_str({"UbicacionTipo": "proyecto",
                                  "UbicacionRef": "PRJ-0001"})
_iv = inventory.reporte_valor(G)
out["inv_valor"] = {k: (sorted(v.items()) if isinstance(v, dict) else v)
                    for k, v in _iv.items()}
out["roster_rango"] = roster.rango_label(roster.lunes_de())

print(json.dumps(out, ensure_ascii=False, sort_keys=True, default=str, indent=1))
