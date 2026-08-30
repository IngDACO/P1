"""
Piezas de UI compartidas.

⚠️ `st.selectbox` **siempre devuelve su primer elemento**: no existe el estado
"todavía no he elegido". Eso convertía en trampa a dos tipos de desplegable:

- los que **borran** (grupo, actividad, manual, agrupación): venían con un
  destino ya elegido y el botón de eliminar justo al lado, sin confirmación;
- los que **escriben en un proyecto** (fichaje, pre-start, recibos, guardar un
  cálculo): un descuido mandaba horas o costos al elevador equivocado, en
  silencio.

`elegir()` antepone una opción neutra para que "no he elegido" sea un estado
real. NO se usa en los desplegables de CONFIGURACIÓN (Marca, Tipo, Categoría,
Rol…), donde el valor por defecto sí ayuda y no dispara ninguna acción.
"""
import streamlit as st

# ⚠️ NO se envuelve en `t()`: es una CONSTANTE de módulo, evaluada al importar, y el
# idioma se resuelve por sesión. `elegir()` la traduce al pintarla.
SIN_SELECCION = "— choose an option —"


def elegir(label: str, opciones, key: str, vacio: str = None, **kw):
    """Selectbox con opción neutra al principio. Devuelve la elección o None.

    `opciones` puede ser una lista o un dict {etiqueta: valor}; con dict se
    devuelve el VALOR, no la etiqueta.
    """
    vacio = vacio or SIN_SELECCION
    es_dict = isinstance(opciones, dict)
    etiquetas = list(opciones.keys()) if es_dict else list(opciones)
    sel = st.selectbox(label, [vacio] + etiquetas, key=key, **kw)
    if not sel or sel == vacio:
        return None
    return opciones[sel] if es_dict else sel


def confirmar_borrado(key: str, texto: str = "I confirm I want to delete it") -> bool:
    """Casilla de confirmación para acciones irreversibles.

    El desplegable neutro evita apuntar al destino equivocado, pero no el clic
    accidental: esto es lo segundo. Mismo criterio que ya usaba "Eliminar
    proyecto", que sí avisaba.
    """
    return st.checkbox(texto, key=key, value=False)
