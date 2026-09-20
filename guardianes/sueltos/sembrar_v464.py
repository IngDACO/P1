# -*- coding: utf-8 -*-
"""Siembra en la hoja REAL un caso que hace visibles las CUATRO listas de v464.

  python sembrar_v464.py sembrar | limpiar

⚠️ La demo esta vacia: sin esto, mirar la tabla no probaria nada (trampa n1).
Los datos de `cliente1` son de PRUEBA (autorizado por el usuario).
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

import streamlit as st
# Sin sesion, el cerrojo de aislamiento (v351) bloquea toda lectura (leccion v422).
st.session_state["auth"] = {"usuario": "dacox", "rol": "propietario",
                            "grupo": "cliente1", "nombre": "Diego"}

from core import catalogo as CAT, inventory as INV, timeclock

GRUPO = "cliente1"
MARCA = "ZZZ PRUEBA v464"


def _ws(titulo):
    cab = {"Catalogo": CAT.HEADERS, INV.ACTIVOS_SHEET: INV.ACTIVOS_HEADERS}[titulo]
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
    # PRODUCTO con unidad `juego` -> la columna Unidad debe decir «set»
    ok, r = CAT.crear(GRUPO, MARCA, tipo="producto", costo_unit="120",
                      unidad="juego", categoria="Equipos", creado_por="verif")
    print("  catalogo.crear ->", ok, r)
    # ACTIVO en `bodega`, condicion `regular` -> «warehouse: …» y «fair»
    ok2, r2 = INV.create_activo(GRUPO, MARCA, categoria="Herramienta",
                                condicion="regular", ubicacion_tipo="bodega",
                                ubicacion_ref="Bodega central", creado_por="verif")
    print("  inventory.create_activo ->", ok2, r2)
    foto("despues")
    print("")
    print("  MIRAR EN PANTALLA (si sale lo de la derecha, el codigo nuevo NO corre):")
    print("   Catalogo   Unit      = 'set'        (no 'juego')")
    print("   Inventario Location  = 'warehouse: Bodega central'  (no 'bodega: ...')")
    print("   Inventario Condition = 'fair'       (no 'regular')")


def limpiar():
    foto("antes de limpiar")
    for titulo in ("Catalogo", INV.ACTIVOS_SHEET):
        ws = _ws(titulo)
        filas = ws.get_all_values()
        # de abajo arriba: borrar desplaza los indices
        borradas = 0
        for i in range(len(filas) - 1, 0, -1):
            if any(MARCA in str(c) for c in filas[i]):
                ws.delete_rows(i + 1)
                borradas += 1
        print("  %-12s borradas %s" % (titulo, borradas))
    # ⚠️ comprobar que NO queda rastro, no dar por hecho que el borrado fue bien
    resto = []
    for titulo in ("Catalogo", INV.ACTIVOS_SHEET, "MovimientosActivo"):
        try:
            ws = timeclock.get_sheet(titulo, None, GRUPO) if titulo == "MovimientosActivo" else _ws(titulo)
            for f in ws.get_all_values():
                if any(MARCA in str(c) for c in f):
                    resto.append(titulo)
        except Exception:
            pass
    print("  rastro restante:", sorted(set(resto)) or "NINGUNO")
    foto("despues de limpiar")


if __name__ == "__main__":
    {"sembrar": sembrar, "limpiar": limpiar}[sys.argv[1]]()
