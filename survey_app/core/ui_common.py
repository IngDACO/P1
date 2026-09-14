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

def opciones_con_actual(opciones, actual):
    """(opciones, indice) para un desplegable que EDITA un valor ya guardado (v487).

    ⚠️ El patron `L.index(v) if v in L else 0` SOBRESCRIBE EN SILENCIO: si el valor
    guardado no esta entre las opciones —una categoria que se borro, un rol mal
    tecleado en la hoja, un color que no es de la paleta— el desplegable muestra la
    PRIMERA opcion y al pulsar «Guardar» esa primera opcion se escribe encima del dato
    de verdad, sin que nadie lo haya elegido. En Usuarios era peor: un usuario sin rol
    salia con **owner** preseleccionado.

    Aqui el valor actual se ANTEPONE a las opciones y queda seleccionado, asi que
    guardar sin tocar ese campo conserva lo que habia. Un valor vacio no se antepone:
    no hay dato que proteger y la primera opcion es un defecto legitimo.
    """
    ops = list(opciones)
    act = "" if actual is None else str(actual)
    if act in ops:
        return ops, ops.index(act)
    if act.strip():
        return [act] + ops, 0
    return ops, 0
