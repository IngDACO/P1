# -*- coding: utf-8 -*-
"""Siembra en la hoja REAL un caso que HACE VISIBLE el arreglo de v463, y lo limpia.

  python sembrar_v463.py sembrar   -> crea 1 articulo + 1 activo y dice los IDs
  python sembrar_v463.py limpiar   -> borra esas filas y comprueba que no queda rastro

⚠️ La demo esta vacia, asi que sin esto la tabla no tiene filas y mirarla no probaria
nada (trampa n1: verificar una bandeja vacia). Los datos de `cliente1` son de PRUEBA.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

import streamlit as st
# ⚠️ Sin sesion, el cerrojo de aislamiento (v351) bloquea toda lectura y las dos fotos
# saldrian a CERO: comparar dos ceros no prueba nada (leccion de v422).
st.session_state["auth"] = {"usuario": "dacox", "rol": "propietario",
                            "grupo": "cliente1", "nombre": "Diego"}

from core import catalogo as CAT, inventory as INV, timeclock

GRUPO = "cliente1"
MARCA = "ZZZ PRUEBA v463"


def _ws(titulo):
    # get_sheet(title, headers, grupo) -- `_get_worksheet()` NO toma argumentos (v135).
    from core import catalogo as _C, inventory as _I
    cab = {"Catalogo": _C.HEADERS, _I.ACTIVOS_SHEET: _I.ACTIVOS_HEADERS}[titulo]
    return timeclock.get_sheet(titulo, cab, GRUPO)


def foto(donde):
    print("  [%s]" % donde)
    for t in ("Catalogo", INV.ACTIVOS_SHEET):
        try:
            n = len(_ws(t).get_all_values()) - 1
        except Exception as e:
            n = "?(%s)" % e
        print("     %-12s %s fila(s)" % (t, n))


def sembrar():
    foto("antes")
    # ⚠️ categoria «Ingenieria»: una de las CUATRO que no estaban en el mapa
    ok, r = CAT.crear(GRUPO, MARCA, tipo="servicio", horas_est="1", tarifa_hora="10",
                      categoria="Ingeniería", creado_por="verif")
    print("  catalogo.crear ->", ok, r)
    ok2, r2 = INV.create_activo(GRUPO, MARCA, categoria="Herramienta",
                                creado_por="verif")
    print("  inventory.create_activo ->", ok2, r2)
    foto("despues")
    print("")
    print("  MIRAR EN PANTALLA:")
    print("   · Finanzas > Catalogo   -> Type='service'   Category='Engineering'")
    print("   · Inventario            -> Category='Tool'  Status='available'")
    print("   (si sale 'servicio' / 'Ingenieria' / 'disponible', el codigo nuevo NO corre)")


def limpiar():
    foto("antes")
    for titulo in ("Catalogo", INV.ACTIVOS_SHEET):
        try:
            ws = _ws(titulo)
        except Exception as e:
            print("  %s: %s" % (titulo, e)); continue
        vals = ws.get_all_values()
        # de abajo arriba: borrar una fila desplaza las de debajo
        borradas = 0
        for i in range(len(vals) - 1, 0, -1):
            if any(MARCA in str(c) for c in vals[i]):
                ws.delete_rows(i + 1)
                borradas += 1
        print("  %s: %d fila(s) borrada(s)" % (titulo, borradas))
    foto("despues")
    # y comprobar que NO queda rastro
    resto = []
    for titulo in ("Catalogo", INV.ACTIVOS_SHEET):
        try:
            if any(MARCA in str(c) for row in _ws(titulo).get_all_values() for c in row):
                resto.append(titulo)
        except Exception:
            pass
    print("")
    print("  rastro restante:", resto or "ninguno")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo == "sembrar":
        sembrar()
    elif modo == "limpiar":
        limpiar()
    else:
        print(__doc__)
