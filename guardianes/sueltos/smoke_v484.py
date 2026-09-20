# -*- coding: utf-8 -*-
"""Ejercita el parte de horas: importar no ejecuta (v378).

La demo tiene 0 ausencias y casi 0 fichajes, así que probar solo contra la hoja real
sería el paso en VACÍO: cada caso que importa va CONSTRUIDO, y además se mira lo que
sale con los datos reales.
"""
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

from core import contable, ausencias as AU, timeclock as TC, auth   # noqa: E402
import csv as _csv                                                 # noqa: E402

G = "cliente1"
L = dt.date(2026, 9, 7)          # lunes
V = L + dt.timedelta(days=11)    # quincena: lun a viernes de la semana siguiente
fallos = []


def ck(que, real, esperado):
    ok = real == esperado
    print(f"  {'ok  ' if ok else '*** FALLO'} {que}: {real!r}"
          + ("" if ok else f"  (esperado {esperado!r})"))
    if not ok:
        fallos.append(que)


print("=" * 78)
print("[1] conceptos: se DERIVAN de ausencias.TIPOS, y solo los PAGADOS")
c = contable.conceptos()
print("  ", c)
ck("ordinarias primero", c[0], contable.ORDINARIAS)
ck("estan los pagados", sorted(c[1:]),
   sorted(k for k, v in AU.TIPOS.items() if v.get("pagado")))
ck("el dia libre (NO pagado) queda fuera", AU.LIBRE in c, False)

print()
print("[2] el mapa trae los nombres de earnings rate y fusiona sin borrar")
m = contable.mapa(G)
print("  ", m["conceptos"])
ck("ordinarias por defecto", m["conceptos"][contable.ORDINARIAS], "Ordinary Hours")
_old = auth.group_text_setting
try:
    auth.group_text_setting = (lambda g, f, d="": '{"conceptos": {"vacaciones": "ZZZ Leave"}}'
                               if f == "AccountingJSON" else d)
    m2 = contable.mapa(G)
    ck("lo guardado sobrescribe el tocado", m2["conceptos"]["vacaciones"], "ZZZ Leave")
    ck("...y CONSERVA los demas", m2["conceptos"][contable.ORDINARIAS], "Ordinary Hours")
    ck("...y no toca las cuentas", m2["cuentas"]["xero"][contable.VENTAS], "200")
finally:
    auth.group_text_setting = _old

print()
print("[3] el parte, con datos CONSTRUIDOS")
_jd, _au, _lu = TC.horas_por_usuario_dia, AU.horas_pagadas_dia, auth.list_users
try:
    TC.horas_por_usuario_dia = lambda g, d0, d1: {
        "u1": {L: 8.0, L + dt.timedelta(days=1): 4.68, L + dt.timedelta(days=2): 7.5},
        "u2": {L: 8.0},
        "fantasma": {L: 6.0},                      # con horas y SIN ficha en Login
    }
    AU.horas_pagadas_dia = lambda g, d0, d1: {
        "u1": {"nombre": "Mei Chen", "dias": {L + dt.timedelta(days=1): {"vacaciones": 3.32}},
               "por_tipo": {"vacaciones": 1}, "dias_contados": 1.0,
               "recortados": [{"fecha": L + dt.timedelta(days=1), "fichadas": 4.68,
                               "pagadas": 3.32, "tipo": "vacaciones"}]},
        "u2": {"nombre": "Mei Chen", "dias": {L + dt.timedelta(days=3): {"enfermedad": 8.0}},
               "por_tipo": {"enfermedad": 1}, "dias_contados": 1.0, "recortados": []},
    }
    # ⚠️ Dos HOMONIMOS: uno con codigo de nomina y otro sin.
    auth.list_users = lambda grupo=None: [
        {"User": "u1", "Name": "Mei Chen", "PayrollID": "EMP-001", "Group": G},
        {"User": "u2", "Name": "Mei Chen", "PayrollID": "", "Group": G},
        {"User": "u3", "Name": "Solo Uno", "PayrollID": "", "Group": G},
    ]
    r = contable.partes(G, L, V)
    print("  dias:", len(r["dias"]), "· filas:", len(r["filas"]),
          "· personas:", r["personas"], "· total:", r["total"])
    for f in r["filas"]:
        print(f"    {f['nombre']:<10} {f['payroll_id']:<8} {f['etiqueta']:<24}"
              f" total={f['total']:<6} {sorted(f['horas'].items())}")
    ck("12 dias en la quincena", len(r["dias"]), 12)
    ck("4 lineas (ordinarias u1/u2/fantasma + 2 ausencias)", len(r["filas"]), 5)
    # ⚠️ La suma: 8+4.68+7.5 (u1) + 8 (u2) + 6 (fantasma) + 3.32 + 8 = 45.5
    ck("el total cuadra", r["total"], 45.5)
    _ord = [f for f in r["filas"] if f["concepto"] == contable.ORDINARIAS
            and f["usuario"] == "u1"][0]
    ck("las ordinarias de u1 son la JORNADA, no las de obra", _ord["total"], 20.18)
    _vac = [f for f in r["filas"] if f["concepto"] == "vacaciones"][0]
    ck("la vacacion trae el RECORTE de v432 (3.32, no 8)", _vac["total"], 3.32)
    ck("y su etiqueta es el earnings rate", _vac["etiqueta"], "Annual Leave")

    print("  avisos:")
    for a in r["avisos"]:
        print("    ·", a)
    _txt = " | ".join(r["avisos"])
    ck("avisa del que NO esta en Login", "fantasma" in _txt, True)
    ck("avisa del HOMONIMO sin codigo", "Mei Chen" in _txt, True)
    ck("avisa del recorte", "3.32" in _txt, True)
    ck("NO avisa del que tiene nombre unico", "Solo Uno" in _txt, False)

    print()
    print("[4] el CSV, ancho: una columna por dia")
    cv = contable.csv_partes(G, L, V)
    lineas = cv["csv"].splitlines()
    cab = next(_csv.reader([lineas[0]]))
    print("   cabecera:", cab)
    ck("cabecera = 3 + dias + total", len(cab), 3 + 12 + 1)
    ck("empieza por Employee/Payroll ID/Earnings rate", cab[:3],
       ["Employee", "Payroll ID", "Earnings rate"])
    ck("los dias van en DD/MM/YYYY", cab[3], "07/09/2026")
    ck("acaba en Total", cab[-1], "Total")
    for ln in lineas[1:]:
        print("   |", ln)
    _f = list(_csv.reader(lineas[1:]))
    ck("cada fila tiene el ancho de la cabecera",
       sorted({len(x) for x in _f}), [len(cab)])
    # ⚠️ El orden de las columnas ES el orden de NumberOfUnits de la API (2.3).
    _u1o = next(x for x in _f if x[1] == "EMP-001" and x[2] == "Ordinary Hours")
    ck("dia 1 = 8.00", _u1o[3], "8.00")
    ck("dia 2 = 4.68 (la jornada, no 8)", _u1o[4], "4.68")
    ck("un dia sin horas queda VACIO, no en 0", _u1o[6], "")
finally:
    TC.horas_por_usuario_dia, AU.horas_pagadas_dia, auth.list_users = _jd, _au, _lu

print()
print("[5] bordes")
ck("fechas ilegibles no revientan", contable.partes(G, "x", "y")["filas"], [])
ck("hasta < desde no revienta", contable.partes(G, V, L)["filas"], [])
_larga = contable.partes(G, L, L + dt.timedelta(days=400))
ck("el periodo se topa en 62 dias", len(_larga["dias"]), 62)
ck("y lo DICE", any("62" in a for a in _larga["avisos"]), True)

print()
print("[6] contra los datos REALES del grupo")
r = contable.csv_partes(G, dt.date(2026, 8, 1), dt.date(2026, 9, 30))
print("   filas:", r["filas"], "· personas:", r["personas"], "· total:", r["total"], "h")
for a in r["avisos"]:
    print("   aviso:", a)
for ln in r["csv"].splitlines()[:4]:
    print("   |", ln[:160])

print("=" * 78)
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS: {fallos}")
sys.exit(1 if fallos else 0)
