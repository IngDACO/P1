# -*- coding: utf-8 -*-
"""Cabeceras de tabla en el idioma de la pantalla, SIN tocar la clave (v450).

## El problema que resuelve

`st.dataframe(pd.DataFrame(filas))` pinta como cabecera la **CLAVE del dict**. En esta
app las filas se construyen a mano (`{"Cliente": …, "Horas": …}`), así que la cabecera
salía en español aunque todo lo demás estuviera traducido — y **mezclada** dentro de la
misma tabla con las que sí se habían tocado (`Alerts` y `Status` al lado de `Elevador`
y `Costo`), que se nota más que si estuviera todo en español.

⚠️ **La clave NO se puede renombrar a la ligera.** Muchas se leen de vuelta
(`r["Elevador"]`, `r["Peso"]`, `x["Estado"]`) y varias viajan a `DatosJSON` en la hoja
(v148). Renombrar es dos pasos y el segundo falla en silencio (v447).

## La solución: etiqueta, no clave

`column_config` cambia lo que se MUESTRA y deja intacto el nombre de la columna que
devuelve el widget. ⚠️ No es una suposición: es lo que la propia app ya hace desde
v353 — `invoices_ui` etiqueta `"Concepto"` como *Item* y después lee `r.get("Concepto")`.

## Lo que se midió antes de aplicarlo a 66 tablas

⚠️ `st.dataframe` pinta en un `<canvas>`, así que el DOM no responde: hubo que
interceptar `fillText` y forzar un repintado real (trampa nº18).

| | Medido |
|---|---|
| ¿cambia la cabecera? | `Cliente · Horas · Costo` → **`Client · Hours · Cost`** |
| ¿cambia cómo se pinta una celda numérica? | **NO**: `41.13 · 27882.67 · 46`, idénticas |
| ¿qué devuelve el `data_editor`? | **las claves ORIGINALES** (`Cliente \| Horas \| …`) |
| ¿tolera claves que la tabla no tiene? | **sí**, 0 excepciones |
| ¿reactiva una columna de `disabled=[…]`? | **NO**: sigue `aria-readonly="true"` |

La última importaba de verdad: `_miembros_editor` y la tabla de avance del campo
bloquean columnas por nombre, y volverlas editables habría dejado escribir donde no
se debe, en silencio.

## Por qué un mapa explícito y no `t()` sobre la clave

`t()` busca por el TEXTO BASE, que es el inglés. `t("Cliente")` no encuentra nada y
devuelve «Cliente». Así que hace falta decir una vez qué inglés le toca a cada clave;
de ahí en adelante, el que traduzca al español traduce el texto inglés como todo lo
demás.

Módulo HOJA: solo `streamlit` + `i18n`, así que cualquier `_ui` puede importarlo.
"""
import streamlit as st

from core.i18n import t

# Clave tal como vive en el dict de la fila → texto BASE (inglés).
# ⚠️ Es un mapa de PRESENTACIÓN. Que una clave esté aquí no la convierte en etiqueta:
# la clave sigue siendo el dato con el que el código lee la tabla de vuelta.
CABECERAS = {
    # identidad y personas
    "Usuario": "User",
    "Nombre": "Name",
    "Persona": "Person",
    "Rol": "Role",
    "Grupo": "Company",
    "Contacto": "Contact",
    "Activo": "Active",
    # proyectos
    "Proyecto": "Project",
    "Cliente": "Client",
    "Elevador": "Lift",
    "Estado": "Status",
    "Tipo": "Type",
    "Avance %": "Progress %",
    "Peso": "Weight",
    "Inicio": "Start",
    "Fin": "End",
    "Entrega prev.": "Est. delivery",
    "Horas": "Hours",
    # dinero
    "Costo": "Cost",
    "Presupuesto": "Budget",
    "Ppto": "Budget",
    "Comprometido": "Committed",
    "Facturado": "Invoiced",
    "Resultado": "Result",
    "Margen %": "Margin %",
    "Sobre pres.": "Over budget",
    "Concepto": "Item",
    "Cant.": "Qty",
    "Quitar": "Remove",
    "vs media h": "vs avg h",
    "vs media $": "vs avg $",
    # documentos, fechas y notas
    "Archivo": "File",
    "Fecha": "Date",
    "Nota": "Note",
    "Valor": "Value",
    "Numero": "Number",
    "Clase": "Class",
    "Vence": "Expires",
    "Vencimiento": "Expiry",
    "ActualizadoPor": "Updated by",
    "Fragmentos": "Fragments",
    # inventario y ruta
    "Desde": "From",
    "Hacia": "To",
    "Horario": "Schedule",
    # rieles
    "Referencia": "Reference",
    "Ancho diente": "Tooth width",
    "Altura diente desde espalda (RAIL)": "Tooth height from back (RAIL)",
    # survey
    "Columna": "Column",
    "Niveles": "Levels",
    "Niveles incumplidos": "Levels out of limit",
    "Diferencia (mm)": "Difference (mm)",
    "Mínimo (mm)": "Minimum (mm)",
    "Máximo (mm)": "Maximum (mm)",
    "FB aplic.": "FB applied",
    "Fuera": "Out",
}


def _claves(filas):
    """Las columnas, venga un DataFrame o la lista de dicts con que se construyó."""
    cols = getattr(filas, "columns", None)
    if cols is not None:
        return [str(c) for c in cols]
    out, vistos = [], set()
    for f in (filas or []):
        if isinstance(f, dict):
            for k in f:
                k = str(k)
                if k not in vistos:
                    vistos.add(k)
                    out.append(k)
    return out


def cfg(filas=None, extra=None):
    """`column_config` con la etiqueta inglesa de cada cabecera conocida.

    Sin `filas` devuelve el mapa ENTERO. ⚠️ Verificado en vivo que Streamlit **ignora
    las claves que la tabla no tiene** (4 tablas, 0 excepciones), así que una tabla
    puede pedirlo completo sin enumerar sus columnas — que es justo lo que evita el
    fallo de origen: una lista escrita a mano en paralelo a las filas se desincroniza
    en cuanto alguien añade una columna, y nadie se entera (v363, v433, v434).

    `extra` son las configuraciones propias de la tabla (formato de dinero, anchos,
    `pinned`, `LinkColumn`…) y **manda**: se aplica encima.

    ⚠️ Una cabecera que no esté en `CABECERAS` se deja como está: este helper no
    adivina idiomas — lo que no se ha decidido, no se toca.
    """
    claves = _claves(filas) if filas is not None else list(CABECERAS)
    out = {}
    for c in claves:
        base = CABECERAS.get(c)
        if base:
            # ⚠️ `Column` genérica a propósito: medido interceptando `fillText` que
            # cambia la CABECERA y deja las celdas numéricas pintándose IDÉNTICAS
            # (41.13 · 27882.67 · 46 antes y después). Poner `TextColumn` sí las
            # cambiaría.
            out[c] = st.column_config.Column(t(base))
    if extra:
        out.update(extra)
    return out
