"""Idiomas de la app (v435). **El idioma BASE es el INGLÉS**; el español es opcional.

## Por qué la clave es el propio texto en inglés

`t("Save project")` — no `t("proj.btn.save")`. Tres razones, y las tres pesan:

1. No hay que inventar ni mantener 1.367 claves.
2. El código se sigue **leyendo** (un `t("Nothing to invoice yet")` dice lo que hace;
   un `t("inv.empty.caption")` obliga a ir a buscarlo).
3. ⚠️ Y la que decide: **un diccionario incompleto es válido**. Si falta la
   traducción, sale el texto base, que es correcto — nunca una clave fea en pantalla.
   Eso es exactamente lo que el usuario pidió: traducir al español solo lo barato y
   dejar el resto en inglés, sin que nada se rompa por el camino.

## Las tres clases de texto, que NO se tratan igual

| | qué es | qué hace |
|---|---|---|
| **Etiqueta** | lo que se lee en pantalla, en un PDF o en un correo | `t()` |
| **Dato** | `"En progreso"`, `"aprobada"`, `"campo"`… viven ASÍ en Google Sheets y se comparan por igualdad en 387 sitios | ⚠️ **NO se traducen**: `etiqueta()` solo cambia cómo se MUESTRAN |
| **Histórico** | nombres de obra, notas, motivos que escribió una persona | no se toca nunca |

⚠️ Confundir las dos primeras es el fallo que este módulo existe para evitar, y **no
da error**: traducir el valor `"Completado"` en la hoja no lanza nada — simplemente
deja de encontrarse ningún proyecto completado. Por eso `VALORES` traduce solo de
CARA AFUERA y hay un guardián que impide que un valor de dato pase por `t()`.

## Coste

`t()` es un `dict.get` y una comprobación. Se llama miles de veces por render, así que
no lleva caché de Streamlit (sería más caro que el propio lookup) ni toca la red.

Módulo HOJA: solo importa `streamlit`, así que cualquiera puede importarlo sin ciclos.
"""
import logging

import streamlit as st

logger = logging.getLogger(__name__)

BASE = "en"                      # el idioma en que está escrito el código
IDIOMAS = {"en": "English", "es": "Español"}
_CLAVE = "_lang"                 # dónde vive el idioma activo en la sesión


def idioma() -> str:
    """El idioma activo. Inglés mientras nadie elija otra cosa.

    ⚠️ Lee de `session_state` y NUNCA de un global del módulo: un global se comparte
    por proceso, así que el idioma de una persona se le aplicaría a las demás — es el
    mismo motivo por el que `tenant.como_grupo` vive en la sesión (v379).
    """
    try:
        v = str(st.session_state.get(_CLAVE, "") or "")
        return v if v in IDIOMAS else BASE
    except Exception:
        return BASE


def set_idioma(cod: str) -> None:
    if cod in IDIOMAS:
        st.session_state[_CLAVE] = cod


def t(texto: str, **kw) -> str:
    """El texto en el idioma activo. Si no hay traducción, devuelve el original.

    ⚠️ Las variables van por **placeholder con nombre**, no concatenadas ni en un
    f-string: `t("Saved {n} rows", n=3)`. Un f-string se evalúa ANTES de llegar aquí,
    así que la cadena que llegaría ya lleva el número dentro y jamás casaría con
    ninguna entrada del diccionario — quedaría en inglés para siempre y nadie sabría
    por qué. El guardián de la suite lo comprueba.
    """
    if not texto:
        return texto
    idi = idioma()
    if idi != BASE:
        # ⚠️ Envuelto: un diccionario roto NO puede dejar la pantalla en blanco. El
        # `try` de `_dic` cubre el import, pero cualquier otro fallo (un `TEXTOS` que
        # no sea un dict, un error al leerlo) llegaría hasta aquí y tumbaría el
        # render. Lo cazó el guardián, no la lectura del código.
        try:
            texto = _dic(idi).get(texto, texto)
        except Exception as e:
            logger.warning("i18n: diccionario %s ilegible: %s", idi, e)
    if kw:
        try:
            return texto.format(**kw)
        except Exception as e:
            # ⚠️ Una traducción con un placeholder mal escrito NO puede dejar la
            # pantalla en blanco: se devuelve el texto sin sustituir y se registra.
            logger.warning("i18n: no se pudo formatear %r: %s", texto, e)
            return texto
    return texto


def d(texto: str, **kw) -> str:
    """Texto de DOCUMENTO: **siempre en el idioma base**, pase lo que pase (v436).

    ⚠️ Una factura, una cotización o una colilla salen de la empresa y las lee otra
    persona; su idioma no puede depender de cómo tenga la interfaz quien pulsa el
    botón. Sin esto, el día que alguien traduzca al español un `"Date"` para su
    pantalla, esa misma clave se aplicaría a la factura —el modelo es clave = texto
    inglés, así que un texto se comparte entre pantalla y documento— y saldría una
    factura en español para un cliente australiano. Un fallo caro y silencioso.

    Si algún día hace falta emitir en el idioma del CLIENTE, se cambia aquí y solo
    aquí: es el único punto por el que pasa el texto de los documentos.
    """
    if kw and texto:
        try:
            return texto.format(**kw)
        except Exception as e:
            logger.warning("i18n.d: no se pudo formatear %r: %s", texto, e)
    return texto


def _dic(idi: str) -> dict:
    if idi == "es":
        try:
            from core.lang_es import TEXTOS
            return TEXTOS
        except Exception as e:
            logger.warning("i18n: no se pudo cargar el diccionario es: %s", e)
    return {}


# ── VALORES DE NEGOCIO ────────────────────────────────────────────
# ⚠️ La clave es el valor **tal y como está escrito en Google Sheets** (en español,
# porque así se escribió desde v65) y el valor es cómo se MUESTRA en inglés. Nada de
# esto cambia lo que hay en la hoja: el dato sigue siendo el mismo y las 387
# comparaciones del código siguen funcionando. Solo cambia lo que lee la persona.
#
# ⚠️ NO se migran los datos a inglés, y no es pereza: son claves internas que el
# usuario no ve nunca si se traducen aquí, están repartidas por el libro de CADA
# cliente y por todo el histórico, y migrarlas obligaría a tocar esas 387
# comparaciones a la vez. Riesgo alto a cambio de nada visible.
VALORES = {
    # estado del proyecto (derive_estado + ESTADOS_MANUAL)
    "Planificado": "Planned", "En progreso": "In progress", "Completado": "Completed",
    "En pausa": "On hold", "Cancelado": "Cancelled", "Archivado": "Archived",
    "Abierta": "Open", "Cerrada": "Closed",
    # tipo de proyecto / localización interna
    "Instalación": "Installation", "Delivery": "Delivery", "Ripout": "Ripout",
    "Otro": "Other", "Oficina": "Office", "Almacén": "Warehouse", "Taller": "Workshop",
    # roles
    "propietario": "owner", "administrador": "administrator", "campo": "field",
    # ausencias
    "vacaciones": "annual leave", "enfermedad": "sick leave", "libre": "day off",
    "pendiente": "pending", "aprobada": "approved", "rechazada": "rejected",
    # v461 · estado propio de las correcciones de fichaje. Los otros dos ya
    # estaban (los usa `ausencias`, de donde se tomo el vocabulario); sin este,
    # la tabla del historial mostraba «revertida» en una fila por lo demas en
    # ingles — traduccion a medias, el peor caso (v443/v450).
    "revertida": "reverted",
    "cancelada": "cancelled",
    # v463 · estado de una ORDEN de compra (orders.ESTADOS). `pendiente` y
    # `cancelada` ya estaban, asi que una orden recibida salia en español
    # entre dos que si se traducian.
    "recibida": "received",
    # v464 · inventario: condicion, tipo de ubicacion y tipo de movimiento.
    # ⚠️ `mantenimiento` y `baja` ya estaban arriba (son estado Y movimiento).
    "bueno": "good", "regular": "fair", "malo": "poor",
    "bodega": "warehouse", "usuario": "user", "reparacion": "under repair",
    "salida": "check-out", "entrada": "check-in", "traslado": "transfer",
    # v464 · unidades del catalogo. ⚠️ m/m²/kg NO se mapean: son simbolos, iguales
    # en los dos idiomas, y un mapa espejo es lo que v450 mando borrar.
    "unidad": "unit", "juego": "set", "global": "lump sum",
    # facturas / nóminas / cotizaciones
    "emitida": "issued", "pagada": "paid", "anulada": "voided", "cobrada": "collected",
    "parcial": "partial", "vencida": "overdue",
    "borrador": "draft", "enviada": "sent", "aceptada": "accepted",
    # credenciales
    "vigente": "valid", "por_vencer": "expiring", "vencido": "expired", "falta": "missing",
    # fichaje
    "general": "workday", "proyecto": "project", "interno": "overhead",
    # categorías de gasto (expenses.CATEGORIAS)
    "Materiales": "Materials", "Herramientas": "Tools", "Transporte": "Transport",
    "Combustible": "Fuel", "Subcontrato": "Subcontractor", "Alquiler": "Rental",
    "Otros": "Other",
    # inventario (inventory.CAT_DEFAULT)
    "Herramienta": "Tool", "Equipo": "Equipment", "Vehículo": "Vehicle",
    "EPP": "PPE", "Consumible": "Consumable",
    # v463 · estado del ACTIVO (inventory.ESTADOS). ⚠️ El TEXTO vive aquí y el COLOR
    # se queda en `inventory_ui._EST_LBL`: hasta v462 el texto vivía SOLO allí, así que
    # la ficha del activo decía «available» y su tabla «disponible» — el mismo activo en
    # dos idiomas a dos clics. Una definición del texto, el color aparte (v450).
    "disponible": "available", "en_uso": "in use", "mantenimiento": "maintenance",
    "dañado": "damaged", "baja": "written off",
    # catálogo (Tipo + catalogo.CAT_DEFAULT)
    "producto": "product", "servicio": "service",
    "Equipos": "Equipment", "Ingeniería": "Engineering", "Mantenimiento": "Maintenance",
    # conceptos de nómina (payroll: `tipo`)
    "devengo": "earning", "deduccion": "deduction", "aporte": "contribution",
}


def etiqueta(valor, defecto=None) -> str:
    """Cómo se MUESTRA un valor de negocio. El dato guardado no cambia jamás.

    Un valor que no esté en el mapa se devuelve tal cual: es lo correcto para lo que
    escribió una persona (el nombre de una obra, una nota) y para cualquier valor
    nuevo que aún no se haya mapeado — sale en español, pero sale.
    """
    v = str(valor if valor is not None else (defecto or ""))
    if not v:
        return v
    if idioma() == BASE:
        return VALORES.get(v, v)
    return v                      # en español el dato ya está en español


def selector(label="Language", key="i18n_sel"):
    """Selector de idioma. ⚠️ Aún NO se pinta en ninguna pantalla: el diccionario
    español está vacío a propósito (decisión del usuario), así que ofrecerlo hoy sería
    ofrecer un botón que no cambia nada. Se cablea cuando haya algo que traducir."""
    _op = list(IDIOMAS)
    _i = _op.index(idioma()) if idioma() in _op else 0
    _n = st.selectbox(label, _op, index=_i, key=key,
                      format_func=lambda c: IDIOMAS[c])
    if _n != idioma():
        set_idioma(_n)
        st.rerun()
