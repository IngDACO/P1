# -*- coding: utf-8 -*-
r"""Cabeceras de tabla en el idioma de la pantalla, SIN tocar la clave (v450).

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
from core.num import num as _num

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
    # ⚠️ v471 · estas se pintaban con su CLAVE cruda, en español, dentro de tablas por
    # lo demas inglesas — la sexta red de v450 con lo que se le escapo. No se puede
    # renombrar la clave: `Riel` y `Actividad` las LEE el codigo de vuelta y `Riel`
    # ademas viaja a `DatosJSON` (v443), asi que reabrir un calculo dejaria de casar.
    # La etiqueta es justo lo que se cambia sin tocar el dato.
    "Riel": "Rail",
    "Actividad": "Activity",
    "Avance": "Progress",
    "Inicio real": "Actual start",
    "Fin real": "Actual finish",
    "Ganancia": "Profit",
    "Orden": "Order",
    "Días": "Days",
    "Estado": "Status",
    "Tipo": "Type", "Unidad": "Unit",
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
    # v461 · bandeja de correcciones de fichaje. ⚠️ Van AQUI y no envueltas en
    # `t()` en su modulo: la CLAVE es el nombre de columna que el codigo lee de
    # vuelta, y solo la ETIQUETA cambia (v450). Tres de estas cuatro se le
    # escaparon al detector por idioma —«Campo», «Antes», «Ahora» no llevan
    # acento ni palabra funcional—, la ceguera de la trampa nº28.
    "Campo": "Field",
    "Antes": "Before",
    "Ahora": "Now",
    "Revisor": "Reviewed by",
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


def derecha(label):
    """Columna de TEXTO alineada a la derecha, para importes y horas ya formateados.

    ⚠️ `alignment` es un parámetro RECIENTE y `requirements.txt` admite Streamlit
    desde 1.39: si no está, se degrada a la columna genérica en vez de romper la
    tabla entera. Una alineación perdida es un detalle; una tabla que no pinta, no.
    """
    try:
        return st.column_config.Column(label, alignment="right")
    except TypeError:                                     # Streamlit sin `alignment`
        return st.column_config.Column(label)


def celda(valor, dec: int = 2, simbolo: str = "", vacio: str = "") -> str:
    r"""Número YA FORMATEADO para una celda, o `vacio` cuando NO hay dato (v486).

    ## Por qué existe: Streamlit NO sabe pintar una celda numérica vacía

    ⚠️ Un nulo en `st.dataframe` se pinta como el literal **«None»** en gris, y no
    hay forma de configurarlo. Medido en 1.57 con una tabla por caso, interceptando
    `fillText`, y con el control que discrimina:

    | Valor de la celda | `column_config` de esa columna | Se pinta |
    |---|---|---|
    | `nan` · `None` · `pd.NA` | ninguno · `{}` · `Column()` · `NumberColumn` · `+format` · `TextColumn` | **«None»** |
    | `nan` + `Styler(na_rep="")` | — | **«None»** |
    | **`""`** | **ninguno o `Column()`** | **vacío** |
    | `""` | `NumberColumn` | **«None»** |

    O sea: **una columna TIPADA convierte incluso `""` en nulo**, así que la única
    celda que sale vacía es una CADENA en una columna sin tipar. De ahí las dos
    piezas: el importe se formatea aquí y la columna se declara con `derecha()`.

    ⚠️ Historia, porque el error se escribió DOS veces: v467 documentó «con `NaN`
    sale vacía — medido» y con esa frase se arreglaron cuatro tablas (catálogo,
    inventario, nómina y el parte de v485) que seguían pintando «None» en
    producción. La frase era falsa. Una afirmación equivocada que se documenta como
    medida no se queda quieta: se copia.

    ⚠️ **No usa `theme.dinero`, a propósito.** Ese escapa el `$` como `\$` porque
    Streamlit lee LaTeX en markdown (v309); una celda de `st.dataframe` no es
    markdown y ahí el escape se ve literal. Medido: `$12.50` en una celda sale tal
    cual. Son dos sitios porque son dos destinos distintos, no por descuido.

    El cero es un DATO (`"$0"`), no una ausencia: solo `None`, la cadena vacía y
    `NaN` dan `vacio`.
    """
    if valor is None:
        return vacio
    if isinstance(valor, str) and not valor.strip():
        return vacio
    # ⚠️ `num`, NO `float()`: un importe con separador de miles («1,234.56», que es
    # como Sheets formatea el dinero en AU/US) revienta con `float` — es el fallo que
    # documentó v323, donde CINCO implementaciones lo leían como 0,00 en silencio.
    # Aquí sería peor: saldría VACÍO, o sea «no hay dato» en vez de «hay $1.234,56».
    # `default=None` para poder distinguir un cero legítimo de algo ilegible.
    v = _num(valor, None)
    if v is None or v != v:                               # ilegible, pd.NA o NaN
        return vacio
    return f"{simbolo}{v:,.{dec}f}"
