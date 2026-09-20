"""Foto de las cifras del grupo, para comparar ANTES/DESPUES del cerrojo de v422.

Vive FUERA del repo a proposito: `git stash` lo borraria, y ademas una exportacion
de datos nunca va dentro del repo (el deploy hace `git add` de todo).

⚠️ Las horas incluyen sesiones ABIERTAS que crecen contra el reloj, asi que la
comparacion lleva tolerancia FISICA (v363: un epsilon simbolico hace fallar el test
por su propia aritmetica). Se guarda tambien el instante para poder medirlo.
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os
os.chdir(RAIZ)                      # v19: los secrets se resuelven contra el CWD

GRUPO = "cliente1"

# ⚠️ SIN SESION TODO SALE A CERO. `_registros_visibles` pasa por el cerrojo de
# aislamiento (v351), que sin `session_state.auth` bloquea, asi que la primera
# corrida dio 0 proyectos / $0 en todo — y comparar dos fotos de ceros no prueba
# NADA (el paso en vacio, trampa nº1). Se simula un admin del grupo.
import streamlit as st
st.session_state["auth"] = {"usuario": "verif_v422", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "verif v422"}

out = {"_t": time.time()}


def paso(nombre, fn):
    """Cada lectura espaciada: 16 guardianes contra un techo de 60/min es un 429."""
    try:
        out[nombre] = fn()
    except Exception as e:
        out[nombre] = f"ERROR: {type(e).__name__}: {e}"
    print(f"  {nombre}: {str(out[nombre])[:110]}")
    time.sleep(1.2)


from core import projects as P, expenses as E, finance as F, timeclock as T, invoices as I

paso("n_proyectos",   lambda: len(P.list_projects(grupo=GRUPO)))
paso("n_con_arch",    lambda: len(P.list_projects(grupo=GRUPO, incluir_archivados=True)))
paso("ids",           lambda: sorted(str(p.get("ID")) for p in
                                     P.list_projects(grupo=GRUPO, incluir_archivados=True)))
paso("horas_bulk",    lambda: round(sum(P.project_hours_bulk(GRUPO).values()), 4))

_ge = E.group_expenses(GRUPO)
out["gasto_total"]   = round(sum(f["total"] for f in _ge["proyectos"]), 2)
out["compras_grupo"] = _ge["compras_grupo"]
out["huerfanos"]     = _ge["huerfanos"]
out["n_filas_gasto"] = len(_ge["proyectos"])
print(f"  gastos: total={out['gasto_total']} compras={out['compras_grupo']} "
      f"huerf={out['huerfanos']} filas={out['n_filas_gasto']}")
time.sleep(1.2)

_gp = F.group_profitability(GRUPO)
out["rent_totales"] = _gp["totales"]
out["rent_filas"]   = len(_gp["rows"])
print(f"  rentabilidad: {out['rent_totales']} filas={out['rent_filas']}")
time.sleep(1.2)

_pnl = F.pnl(GRUPO)
out["pnl"] = {k: _pnl[k] for k in sorted(_pnl) if isinstance(_pnl[k], (int, float))}
print(f"  P&L: {out['pnl']}")
time.sleep(1.2)

_c = F.conciliacion_mo(GRUPO)
out["concil"] = {k: v for k, v in _c.items() if isinstance(v, (int, float))}
print(f"  conciliacion: {out['concil']}")
time.sleep(1.2)

_gh = T.group_hours(GRUPO)
out["horas_grupo"] = {r["usuario"]: [r["general"], r["proyecto"], r["sin_asignar"],
                                     r["costo"]] for r in _gh}
print(f"  horas: {len(_gh)} personas")
time.sleep(1.2)

# ⚠️ `sin_facturar` NO devuelve dicts (mi primera version asumio `x["pendiente"]` y
# reventó): se compara por longitud y por su repr, sin suponer la forma. Regla v135,
# esta vez cometida DENTRO del verificador.
paso("sin_facturar_n",   lambda: len(F.sin_facturar(GRUPO)))
paso("sin_facturar_rep", lambda: sorted(repr(x) for x in F.sin_facturar(GRUPO)))
paso("pendiente_map", lambda: {k: round(v, 2) for k, v in
                               sorted(I.pendiente_por_proyecto(GRUPO).items())})
paso("resultado_n",  lambda: len(F.resultado_por_proyecto(GRUPO)))
paso("gaps",         lambda: {k: v for k, v in sorted(P.gaps_by_group(GRUPO).items())})
paso("over_budget",  lambda: sorted(x["id"] for x in E.over_budget(GRUPO)))

destino = Path(sys.argv[1])
destino.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True),
                   encoding="utf-8")
print(f"\nguardado en {destino}")
