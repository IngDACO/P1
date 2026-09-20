# -*- coding: utf-8 -*-
"""Las CUATRO pantallas de v486, llamando a las funciones REALES.

No replica la expresion: invoca `_partes_section`, `render_nominas`,
`render_catalogo` y el detalle de inventario tal como los llama la app. Replicar es
justo lo que me hizo dar v485 por bueno.

Cada una entre try/except, para que un fallo de una no oculte a las otras.
"""
import sys
import traceback

sys.path.insert(0, "C:/Users/diego/P1/survey_app")

import streamlit as st

GRUPO = "cliente1"


def bloque(titulo, fn):
    st.markdown("---")
    st.markdown(f"### {titulo}")
    try:
        fn()
    except Exception:
        st.error(f"EXCEPCION en {titulo}")
        st.code(traceback.format_exc())


st.write("SONDA v486 · las cuatro tablas que pintaban None")


def _parte():
    from core import contable_ui
    contable_ui._partes_section(GRUPO)


def _nominas():
    from core import payroll_ui
    payroll_ui.render_nominas(GRUPO)


def _catalogo():
    from core import catalogo_ui
    catalogo_ui.render_catalogo(GRUPO)


def _inventario():
    from core import inventory as INV
    from core import inventory_ui
    activos = INV.list_activos(GRUPO)          # el nombre REAL, comprobado
    st.caption(f"activos en {GRUPO}: {len(activos)}")
    if not activos:
        st.info("sin activos: el historial de movimientos no se puede ejercitar con "
                "datos reales aqui")
        return
    inventory_ui._detalle(GRUPO, str(activos[0].get("ID", "")))


bloque("1 · Parte de horas (contable_ui)", _parte)
bloque("2 · Nominas · Rate/h (payroll_ui)", _nominas)
bloque("3 · Catalogo · Horas (catalogo_ui)", _catalogo)
bloque("4 · Inventario · Costo (inventory_ui)", _inventario)
