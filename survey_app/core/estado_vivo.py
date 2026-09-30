# -*- coding: utf-8 -*-
"""Lo que se tecleó en una herramienta NO se pierde al salir de ella (v534).

## El fallo, visto en producción (30/09/2026)

Survey con los 23 parámetros y una matriz de 3 pisos tecleados a mano. Un clic en
«Rails» y otro de vuelta en «Survey»: **los 23 parámetros a 0,00, el nº de paradas a 2 y
la matriz cortada a 2 filas**. Los resultados seguían en pantalla con el aviso «You changed
data since the last calculation» — y «Recalculate» habría calculado con ceros.

## Por qué pasa

Streamlit **borra el valor de un widget en cuanto una pasada no lo pinta**. Al cambiar de
sección la herramienta deja de pintarse y sus entradas desaparecen del `session_state`.
La excepción es una clave que el CÓDIGO asignó en esa pasada: esa no se borra.

`survey_ui` ya lo sabía —reasignaba sus claves al entrar, para no perderlas al pasar de
«Survey data» a «Results»—, pero lo hacía DENTRO de `render_survey_tab`: en las pasadas
de otra sección no corría, que es justo cuando hacía falta. Las otras cuatro herramientas
no lo hacían en ningún sitio.

## La cura

`pasada()` se llama desde `app.py` en CADA pasada, antes de pintar nada: reasigna las
entradas de las cinco herramientas que ya existan, y Streamlit las conserva.

⚠️ **Solo ENTRADAS, con lista cerrada.** A un botón, un `file_uploader` o un `data_editor`
no se le puede asignar la clave: Streamlit lanza una excepción al crearlos. Por eso no
se va por prefijos amplios (`rc_` incluiría `rc_calc1`, un botón). Las tablas editables
no hacen falta: su contenido ya vive en una clave propia que no es de widget
(`survey_df`, `rc_L_df`, `plb_bsr_df`, `bc_df`); lo que las vaciaba era perder el NÚMERO
de filas (`ns`, `rc_n`, `plb_n`, `bc_n`), que sí está aquí.

## ⚠️ Lo que ese borrado protegía sin querer: cambiar de OBRA

Releyendo el arreglo antes de desplegarlo: las herramientas rellenan sus datos del plano
con `plan_ui.aplicar`, que **solo escribe si el campo está vacío**. El técnico que calcula
Rieles en la obra A, ficha en la obra B y vuelve, encontraba los campos vacíos —Streamlit
los había borrado— y se rellenaban con el plano de B. Conservándolos sin más, se quedarían
el LFKK de A bajo el nombre de B, en un corte que no se deshace.

Así que lo conservado es **de una obra**: al volver a una herramienta se mira con qué obra
se pintó la última vez (`al_pintar`), y si ahora es OTRA, sus entradas se olvidan — que es
exactamente lo que pasaba antes. Misma obra (o ninguna las dos veces) → se conservan.

⚠️ Solo al VOLVER. Cambiar de obra sin salir de la herramienta no borraba nada antes y no
borra nada ahora: «Duplicate for the next lift» cuenta con eso. Y lo que otra pantalla
carga A PROPÓSITO (reabrir un cálculo, reconstruir un survey) se respeta (`respetar`).

Módulo HOJA: solo importa `streamlit`.
"""
import streamlit as st

# Las entradas de cada herramienta, por la clave con que llama a
# `plan_ui.selector_proyecto`. ⚠️ Solo widgets de ENTRADA (ver arriba).
HERRAMIENTAS = {
    "sv":   {"prefijos": ("inp_", "cfg_"), "claves": ("ns",)},
    "plb":  {"prefijos": (),
             "claves": ("plb_bks", "plb_rail", "plb_tksw", "plb_lt", "plb_sf1", "plb_sf2",
                        "plb_bs", "plb_sg", "plb_tg", "plb_omega", "plb_n")},
    "rc":   {"prefijos": (),
             "claves": ("rc_lfkk", "rc_lfgk", "rc_n", "rc_caso", "rc_n2500", "rc_n5000",
                        "rc_sub")},
    "bc":   {"prefijos": (), "claves": ("bc_hkp", "bc_n")},
    "belt": {"prefijos": ("belt_hgpr_",), "claves": ("belt_hq", "belt_hgp", "belt_ns")},
}

# La obra elegida en cada herramienta (admin y propietario). Sin esto, al volver el
# selector estaría en «no project», la obra habría «cambiado» y se olvidaría todo.
_OBRA = "pl_prj_"
# La identidad del informe del Survey. No son widgets; venían en el bucle de `survey_ui`.
_IDENTIDAD = ("proyecto", "cliente", "ubicacion", "ingeniero")

PREFIJOS = tuple(p for h in HERRAMIENTAS.values() for p in h["prefijos"]) + (_OBRA,)
CLAVES = frozenset(k for h in HERRAMIENTAS.values() for k in h["claves"]) | frozenset(_IDENTIDAD)

_PASADA = "_ev_pasada"          # nº de pasada (lo cuenta `pasada`, desde app.py)
_VISTA = "_ev_vista_"           # + herramienta → (pasada, obra) de la última vez que se pintó
_RESPETAR = "_ev_respetar_"     # + herramienta → la próxima vez que se pinte, no olvidar


def es_entrada(clave) -> bool:
    k = str(clave)
    return k in CLAVES or k.startswith(PREFIJOS)


def de_herramienta(herramienta, clave) -> bool:
    """¿Es `clave` una entrada de ESA herramienta?"""
    h = HERRAMIENTAS.get(herramienta)
    k = str(clave)
    return bool(h) and (k in h["claves"] or (bool(h["prefijos"]) and k.startswith(h["prefijos"])))


def mantener() -> int:
    """Reasigna las entradas que ya existen, para que sobrevivan a una pasada que no las
    pinta. Devuelve cuántas. Va ANTES de crear cualquier widget."""
    n = 0
    for k in list(st.session_state.keys()):
        if es_entrada(k):
            st.session_state[k] = st.session_state[k]
            n += 1
    return n


def pasada() -> int:
    """Lo que `app.py` llama UNA vez por pasada: cuenta la pasada y conserva las entradas.

    ⚠️ El contador es lo que permite saber si una herramienta «vuelve» (no se pintó en la
    pasada anterior) o sigue en pantalla. Solo lo mueve esta función: quien pinte una
    herramienta sin pasar por `app.py` no lo mueve, y entonces nunca se olvida nada.
    """
    st.session_state[_PASADA] = int(st.session_state.get(_PASADA, 0) or 0) + 1
    return mantener()


def olvidar(herramienta) -> int:
    """Borra las entradas de UNA herramienta: lo que Streamlit hacía solo al salir de ella."""
    n = 0
    for k in list(st.session_state.keys()):
        if de_herramienta(herramienta, k):
            del st.session_state[k]
            n += 1
    return n


def respetar(herramienta) -> None:
    """Otra pantalla acaba de CARGAR valores en esta herramienta (reabrir un cálculo,
    reconstruir un survey): la próxima vez que se pinte, no se olvidan aunque la obra sea
    otra. Y el selector de obra vuelve a «no project», como ocurría antes al llegar."""
    st.session_state[_RESPETAR + str(herramienta)] = True
    st.session_state.pop(_OBRA + str(herramienta), None)


def al_pintar(herramienta, obra) -> bool:
    """La herramienta se está pintando con `obra` (su ID, o "" si no hay).

    Si VUELVE (no se pintó en la pasada anterior) y la obra es OTRA, olvida sus entradas y
    devuelve True. Va ANTES de crear los widgets de la herramienta.
    """
    h, obra = str(herramienta), str(obra or "")
    n = int(st.session_state.get(_PASADA, 0) or 0)
    antes = st.session_state.get(_VISTA + h)
    st.session_state[_VISTA + h] = (n, obra)
    if st.session_state.pop(_RESPETAR + h, False) or not antes:
        return False
    ult_pasada, ult_obra = antes
    if ult_pasada >= n - 1 or ult_obra == obra:
        return False
    olvidar(h)
    return True
