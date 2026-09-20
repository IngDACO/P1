# -*- coding: utf-8 -*-
"""¿El agregado de `horas_pagadas_grupo` sigue dando EXACTAMENTE lo mismo?

Lo usa `payroll.generar` para pagar, así que una diferencia aquí es dinero. Y la demo
tiene 0 ausencias, así que compararlo contra la hoja real sería el paso en VACÍO
(trampa nº1): hacen falta casos CONSTRUIDOS.

⚠️ La lógica vieja no se reescribe de memoria: se saca del commit con `git show` y se
ejecuta en el espacio de nombres del módulo bajo otro nombre, para comparar las dos
sobre las MISMAS filas (el método de v363).
"""
import ast
import datetime as dt
import io
import os
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

from core import ausencias as AU                                   # noqa: E402

# ── la version VIEJA, del commit, no de mi memoria ──────────────────────────
_viejo_src = subprocess.run(
    ["git", "show", "HEAD:survey_app/core/ausencias.py"],
    cwd=os.path.dirname(RAIZ), capture_output=True, text=True,
    encoding="utf-8", errors="replace").stdout
if not _viejo_src:
    raise SystemExit("no se pudo leer la version vieja con git show")
_arbol = ast.parse(_viejo_src)
_fn = next((n for n in _arbol.body
            if isinstance(n, ast.FunctionDef) and n.name == "horas_pagadas_grupo"), None)
if _fn is None:
    raise SystemExit("la version vieja no tiene horas_pagadas_grupo")
_fn.name = "_vieja"
_mod = ast.Module(body=[_fn], type_ignores=[])
ast.fix_missing_locations(_mod)
exec(compile(_mod, "<vieja>", "exec"), AU.__dict__)      # noqa: S102 - comparacion
print("version vieja cargada del commit:", AU._vieja.__name__)

G = "cliente1"
L = dt.date(2026, 9, 7)          # lunes
fallos = []


def _fila(usr, tipo, d0, d1, estado=AU.APROBADA, findes="", nombre=None):
    return {"ID": "AUS-x", "Group": G, "User": usr, "Name": nombre or usr.upper(),
            "Type": tipo, "From": d0.isoformat(), "To": d1.isoformat(),
            "Days": "", "Reason": "", "Status": estado, "ResolvedBy": "",
            "ResolvedDate": "", "AdminNote": "", "CreatedBy": "", "Created": "",
            "IncludesWeekends": findes}


CASOS = [
    ("3 dias de vacaciones, sin fichar",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))], {}),

    ("el RECORTE de v432: un dia con 4.68 h fichadas",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))],
     {"u1": {L + dt.timedelta(days=1): 4.68}}),

    ("dia trabajado COMPLETO: paga 0 pero sigue contando como dia",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))],
     {"u1": {L: 8.75}}),

    ("rango con FIN DE SEMANA pedido",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=6), findes="SI")], {}),

    ("rango con fin de semana NO pedido",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=6))], {}),

    ("ausencia a caballo del periodo (solo cuentan los dias dentro)",
     [_fila("u1", AU.VACACIONES, L - dt.timedelta(days=10), L + dt.timedelta(days=1))], {}),

    ("tipo NO pagado (dia libre) queda fuera",
     [_fila("u1", AU.LIBRE, L, L + dt.timedelta(days=2))], {}),

    ("no aprobada queda fuera",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2), estado="pendiente")], {}),

    ("dos tipos, dias distintos, misma persona",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=1)),
      _fila("u1", AU.ENFERMEDAD, L + dt.timedelta(days=2), L + dt.timedelta(days=2))],
     {"u1": {L: 2.0}}),

    ("dos personas",
     [_fila("u1", AU.VACACIONES, L, L),
      _fila("u2", AU.ENFERMEDAD, L, L + dt.timedelta(days=1))],
     {"u2": {L: 8.0}}),

    ("otro grupo queda fuera",
     [dict(_fila("u1", AU.VACACIONES, L, L), Group="otro")], {}),

    ("sin ausencias",
     [], {}),
]

_rec, _hpd = AU._records, None
import core.timeclock as TC                                        # noqa: E402
_tc = TC.horas_por_usuario_dia

print("=" * 78)
for nombre, filas, fichadas in CASOS:
    AU._records = lambda f=filas: list(f)
    TC.horas_por_usuario_dia = lambda g, d0, d1, f=fichadas: {k: dict(v) for k, v in f.items()}
    nuevo = AU.horas_pagadas_grupo(G, L, L + dt.timedelta(days=6))
    viejo = AU._vieja(G, L, L + dt.timedelta(days=6))
    igual = nuevo == viejo
    print(f"  {'ok  ' if igual else '*** DISTINTO'} {nombre}")
    if not igual:
        fallos.append(nombre)
        print("      viejo:", viejo)
        print("      nuevo:", nuevo)
    else:
        for k, v in nuevo.items():
            print(f"        {k}: horas={v['horas']} dias={v['dias']} "
                  f"por_tipo={v['por_tipo']} recortes={len(v['recortados'])}")

# ⚠️ Y la rama del `except`: si no se pueden leer las horas fichadas NO se paga a
# ciegas. Se ejercita de verdad, que es la unica forma de saber que sigue ahi (v370).
def _revienta(*a, **kw):
    raise RuntimeError("boom")


AU._records = lambda: [_fila("u1", AU.VACACIONES, L, L)]
TC.horas_por_usuario_dia = _revienta
nuevo = AU.horas_pagadas_grupo(G, L, L)
viejo = AU._vieja(G, L, L)
igual = nuevo == viejo
print(f"  {'ok  ' if igual else '*** DISTINTO'} con la lectura de fichajes REVENTANDO")
if not igual:
    fallos.append("except de fichajes")
    print("      viejo:", viejo, "\n      nuevo:", nuevo)

# ── y la vista NUEVA, que es la que el parte necesita ───────────────────────
print("-" * 78)
AU._records = lambda: [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))]
TC.horas_por_usuario_dia = lambda g, d0, d1: {"u1": {L + dt.timedelta(days=1): 4.68}}
dia = AU.horas_pagadas_dia(G, L, L + dt.timedelta(days=6))
print("  horas_pagadas_dia:")
for k, v in dia.items():
    for d in sorted(v["dias"]):
        print(f"    {k} {d} -> {v['dias'][d]}")
    print(f"    dias_contados={v['dias_contados']} recortes={v['recortados']}")
_suma = round(sum(h for v in dia.values() for p in v["dias"].values() for h in p.values()), 2)
_agr = AU.horas_pagadas_grupo(G, L, L + dt.timedelta(days=6))["u1"]["horas"]
print(f"  suma del detalle = {_suma} · agregado = {_agr}"
      f"  {'OK' if _suma == _agr else '*** NO CUADRA ***'}")
if _suma != _agr:
    fallos.append("el detalle no suma el agregado")

AU._records, TC.horas_por_usuario_dia = _rec, _tc
print("=" * 78)
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS: {fallos}")
sys.exit(1 if fallos else 0)
