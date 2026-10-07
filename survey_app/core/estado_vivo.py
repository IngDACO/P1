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

Desde v535 también sin salir de la herramienta (salvo el Survey, por «Duplicate for the
next lift»), y desde v541 con UNA regla: se olvida al pintarse con otra obra REAL; sin obra,
nunca (ver `al_pintar`). Lo que otra pantalla carga A PROPÓSITO (reabrir un cálculo,
reconstruir un survey) se respeta (`respetar`).

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

# ⚠️ v540 · El valor por DEFECTO de cada entrada de las cuatro herramientas de cálculo, el
# mismo con que nace su widget (lo comprueba `verif_v540` pintándolas). Para olvidar una
# entrada que está EN PANTALLA no basta con borrarla: Streamlit identifica estos widgets
# solo por su clave, y el navegador se queda con el valor viejo y lo devuelve en el clic
# siguiente — solo se entera de un valor cuando el código lo ASIGNA (la trampa de v529).
# Visto en producción con el admin: de 88 walker a otra obra sin salir de Belting, el
# servidor borraba y el cálculo salía con el HQ, el HGP y el HGPR de 88 walker.
DEFECTOS = {
    "plb_bks": 0.0, "plb_rail": 0.0, "plb_tksw": 0.0, "plb_lt": 0.0, "plb_sf1": 0.0,
    "plb_sf2": 0.0, "plb_bs": 0.0, "plb_sg": 0.0, "plb_tg": 0.0, "plb_omega": "R",
    "plb_n": 1,
    "rc_lfkk": 0.0, "rc_lfgk": 0.0, "rc_n": 1,
    "rc_caso": "Case 1 — first installed (the bottom one)",
    "rc_n2500": 0, "rc_n5000": 0, "rc_sub": "Above the FFL (subtract)",
    "bc_hkp": 0.0, "bc_n": 1,
    "belt_hq": 0.0, "belt_hgp": 0.0, "belt_ns": 1,
    # v541 · El nº de paradas del Survey (el 2 neutro de `survey_ui.init_state`). Sin él,
    # volver al Survey con otra obra BORRABA `ns` y el plano lo ponía como 5.0: `aplicar`
    # solo lo deja entero si lo que había era entero, y no había nada.
    "ns": 2,
}
_DEFECTO_PREFIJO = (("belt_hgpr_", 0.0),)
# v540 · Las TABLAS de lo medido también son de una obra (HKPR de cada buffer, BSR de cada
# ascensor, L de cada ascensor y la matriz del caso 2): hasta v540 no se olvidaban nunca.
# Su contenido vive en estas claves; la tabla editable lleva una clave con GENERACIÓN
# (`clave_tabla`), porque Streamlit conserva sus ediciones mientras la forma de los datos
# no cambie — ponerla a ceros no bastaría: el navegador volvería a aplicar lo tecleado.
TABLAS = {"plb": ("plb_bsr_df",), "rc": ("rc_L_df", "rc_in_df"), "bc": ("bc_df",)}
_GEN = "_ev_gen_"
_SIN = object()
# v541 · Lo cargado sin obra conocida (`respetar` sin obra): lo adopta la primera obra real.
_ADOPTAR = "\x00adoptar"

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


def _defecto(clave):
    k = str(clave)
    if k in DEFECTOS:
        return DEFECTOS[k]
    for pref, val in _DEFECTO_PREFIJO:
        if k.startswith(pref):
            return val
    return _SIN


def clave_tabla(herramienta, nombre) -> str:
    """La clave de la tabla editable `nombre` de una herramienta: cambia cada vez que la
    herramienta olvida lo suyo, y así el navegador la estrena vacía (v540)."""
    return "%s_%d" % (nombre, int(st.session_state.get(_GEN + str(herramienta), 0) or 0))


def olvidar(herramienta) -> int:
    """Olvida las entradas de UNA herramienta: lo que Streamlit hacía solo al salir de ella.

    ⚠️ v540 · Las que tienen valor por defecto se ASIGNAN a él en vez de borrarse, para que
    el navegador lo reciba aunque la herramienta siga en pantalla (ver `DEFECTOS`). Y sus
    tablas de lo medido se vacían con una tabla editable nueva."""
    h = str(herramienta)
    n = 0
    for k in list(st.session_state.keys()):
        if de_herramienta(h, k):
            d = _defecto(k)
            if d is _SIN:
                del st.session_state[k]
            else:
                st.session_state[k] = d
            n += 1
    for k in TABLAS.get(h, ()):
        st.session_state.pop(k, None)
    st.session_state[_GEN + h] = int(st.session_state.get(_GEN + h, 0) or 0) + 1
    return n


def respetar(herramienta, obra="") -> None:
    """Otra pantalla acaba de CARGAR valores en esta herramienta (reabrir un cálculo,
    reconstruir un survey): la próxima vez que se pinte, no se olvidan aunque la obra sea
    otra. Y el selector de obra vuelve a «no project», como ocurría antes al llegar.

    ⚠️ v539 · `obra` = el ID de la obra de la que SON esos valores (el cálculo reabierto
    lleva su ProjectID; el survey reconstruido, su proyecto). Sin ella, la herramienta
    seguía creyendo que lo suyo era de la última obra con que se usó: el admin usaba
    Belting con la obra A, reabría un cálculo de B, elegía B en el selector —lo natural
    para volver a guardarlo— y v535 lo tomaba por «de A a B sin salir» y borraba lo
    medido (HGPR 1547 → 0 con los cálculos reales de 88 walker). Elegir después ESA obra
    ya no es un cambio; elegir otra sí."""
    st.session_state[_RESPETAR + str(herramienta)] = str(obra or "") or True
    st.session_state.pop(_OBRA + str(herramienta), None)


# ── De quién son los datos de trabajo (v535) ─────────────────────────────────
# ⚠️ Al cerrar sesión solo se quitaba la identidad (`auth`): los resultados del Survey, el
# historial del asistente y lo tecleado se quedaban en la pestaña, y OTRA cuenta que
# entrara en ella sin recargar —otra empresa cliente, incluso— los veía. Ahora los datos
# de trabajo son de UNA cuenta: si entra otra, la sesión empieza limpia. La misma cuenta
# que vuelve (tras salir, o tras una expulsión de la sesión única) encuentra lo suyo.
_CUENTA = "_ev_cuenta"
# Lo que NO es trabajo de nadie y hay que conservar: la identidad recién puesta por el
# login, el idioma, el gestor de la cookie (único por sesión, v188) y sus componentes, y
# los mensajes pendientes de pintar (`flash`).
_INFRA = frozenset({"auth", "_hb_last", "_remember_session", "_no_cookie_restore",
                    "_lang", "_cookie_mgr", "_flash_cola", _CUENTA})
_INFRA_PREF = ("copex_cookie",)


def de_la_cuenta(usuario) -> bool:
    """Marca de quién son los datos de la sesión. Si entra OTRA cuenta, los borra todos
    (menos la infraestructura) y devuelve True. Va justo después del login y antes de
    pintar nada: quien llama vuelve a inicializar el estado base (`init_state`)."""
    u = str(usuario or "")
    antes = st.session_state.get(_CUENTA)
    st.session_state[_CUENTA] = u
    if antes is None or antes == u:
        return False
    for k in list(st.session_state.keys()):
        if k in _INFRA or str(k).startswith(_INFRA_PREF):
            continue
        del st.session_state[k]
    return True


def al_pintar(herramienta, obra) -> bool:
    """La herramienta se está pintando con `obra` (su ID, o "" si no hay).

    Devuelve True si lo que tenía era de OTRA obra — y entonces el plano de la obra actual
    tiene que MANDAR sobre lo que haya (`plan_ui.aplicar` lo pisa en esa pasada). Va ANTES
    de crear los widgets de la herramienta.

    ⚠️ v541 · UNA regla: lo tecleado es de la última obra REAL con que se pintó la
    herramienta, y se olvida solo cuando se pinta con OTRA obra real (también la primera
    tras usarla sin obra: manda el plano de esa obra). **Sin obra no se olvida nunca.**
    Hasta v541 había dos casos según la herramienta se hubiera pintado o no en la pasada
    anterior, y «volver» olvidaba también al pasar a «sin obra». Pero los botones del
    fichaje del menú lateral terminan en `st.rerun()`, que corta la pasada ANTES de pintar
    la herramienta: cerrar la jornada desde Rieles contaba como «volver» y borraba lo
    tecleado sin cambiar de obra (visto en producción con la cuenta de campo: LFKK 1234 → 0
    al cerrar la jornada; y al volver a fichar en la MISMA obra, perdido). Hasta v540 no
    se notaba porque el borrado no llegaba al navegador.

    ⚠️ v535 · El Survey, sin salir, NO olvida: «Duplicate for the next lift» conserva A
    PROPÓSITO lo medido para el siguiente ascensor; ahí solo manda el plano de la obra nueva
    sobre lo que el plano trae. Al VOLVER a él con otra obra real sí se olvida (lo de antes).

    Lo cargado a propósito (`respetar`) no se olvida al pintarse y es de la obra que dijo
    quien lo cargó (v539); si no lo dijo, es de la primera obra real con que se pinte.
    """
    h, obra = str(herramienta), str(obra or "")
    n = int(st.session_state.get(_PASADA, 0) or 0)
    antes = st.session_state.get(_VISTA + h)
    ult_real = (antes[2] if antes and len(antes) > 2 else "") if antes else ""
    resp = st.session_state.pop(_RESPETAR + h, False)
    if resp:
        # v539 · La última obra REAL de la herramienta es ahora la de lo cargado, no la
        # de antes de cargarlo (ver `respetar`). Sin obra conocida: la adopta la primera.
        ult_real = resp if isinstance(resp, str) else _ADOPTAR
    if obra and ult_real == _ADOPTAR:
        ult_real = obra
    st.session_state[_VISTA + h] = (n, obra, obra or ult_real)
    if resp or not antes:
        return False
    if obra and ult_real != obra:                       # llega a OTRA obra real
        volvio = antes[0] < n - 1                       # no se pintó en la pasada anterior
        if h != "sv" or volvio:
            olvidar(h)
        return True
    return False
