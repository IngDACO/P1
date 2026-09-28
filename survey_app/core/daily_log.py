# -*- coding: utf-8 -*-
"""El parte diario: el campo escribe lo que hizo, en sus palabras (v516).

## Qué es y qué NO es todavía

Es **texto libre con obra, fecha y autor**. Nada más. No interpreta, no mueve el avance,
no toca ninguna actividad. Eso es lo siguiente (F2), y llega cuando haya con qué medirlo.

## ⚠️ Por qué el texto va ANTES que la IA

Lo que el usuario pidió es que un agente lea el parte y lo cargue en el cronograma. Eso
son dos cosas distintas puestas en fila:

  1. que exista el texto, escrito por quien hizo el trabajo;
  2. que algo lo entienda.

Empezar por (2) obliga a probar la interpretación con frases que me invente yo, y una
frase inventada por quien escribe el intérprete acierta siempre. Es la trampa nº1 en su
forma más cara: un corpus de mentira da una precisión de mentira. Con (1) desplegado,
cada día que pasa el corpus crece **con el vocabulario real de los instaladores**, que
es justo lo que no se puede inventar: las abreviaturas, el orden en que cuentan las
cosas, qué dan por supuesto.

⚠️ Y (1) vale por sí solo aunque (2) no llegara nunca: hoy ese parte se da por WhatsApp o
no se da, y no queda en la obra. Aquí queda pegado al proyecto, con fecha y firma.

## ⚠️ El borrador no se pierde si falla el guardado

Un instalador escribe doscientas palabras en un sótano con mala cobertura. Si el guardado
falla y la caja se vacía, no vuelve a escribirlas — deja de usar la pantalla, y con razón.
Así que el texto **se conserva** y el error dice la verdad: `timeclock.motivo_sin_hoja()`
distingue «no hay configuración» de «la cuota mordió, prueba en un minuto» (v511), que
son dos cosas muy distintas para quien está delante.

Esto NO es trabajar sin conexión —eso sigue pendiente de decidir— pero es lo que impide
que el fallo de hoy cueste el texto de hoy.

## ⚠️ Se AÑADE, no se edita

Cada guardado es una entrada nueva. Si el campo se acuerda de algo más, lo añade; si se
equivocó, borra la suya **del día** y la reescribe. Editar en sitio parece más cómodo y
es peor para lo único que hace especial a estos datos: son **lo que alguien dijo que hizo
ese día**. Un texto reescrito tres semanas después ya no es eso.
"""
import logging

import streamlit as st

from core import clock, columnas, timeclock
from core.num import num as _num

from core.i18n import t

logger = logging.getLogger(__name__)

SHEET = "DailyLogs"
# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL. Lo que traiga F2 —la propuesta del
# intérprete, si se aceptó, contra qué actividades— se añade detrás de `Created`, nunca
# en medio, o toda fila escrita hasta entonces se desplaza una posición.
# ⚠️ v523 · `Reviewed`/`ReviewedBy` AL FINAL (v363): cuándo y quién revisó las PROPUESTAS
# que la app sacó del parte — confirmando lo que era, o diciendo que nada. Sin esta marca
# la pantalla volvería a preguntar lo mismo cada vez que se abre; y qué se acreditó NO se
# guarda aquí: vive en StageProgress con el ID del parte en la nota (una sola verdad).
HEADERS = ["ID", "Group", "ProjectID", "Date", "Author", "Text", "Source", "Created",
           "Reviewed", "ReviewedBy"]

# De dónde salió el parte. Hoy solo escrito a mano; cuando el intérprete proponga y
# alguien acepte, poder distinguirlos es lo que permitirá medir si acierta.
MANUAL = "manual"

# ⚠️ Tope de caracteres. No es paranoia de tamaño de celda (Sheets aguanta 50.000): es
# que un parte diario de veinte mil caracteres no es un parte, es un documento pegado, y
# ensuciaría el corpus que este módulo existe para juntar. Se avisa ANTES de guardar en
# vez de recortar por detrás, que perdería texto sin decirlo.
MAX_TEXTO = 4000

_COL = {h: i + 1 for i, h in enumerate(HEADERS)}


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("daily_log: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja — un lector que
    escribe (regla v145). La crea el primer parte que se guarde."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas
    hojas.invalidar(SHEET)
    try:
        _records_cached.clear()
    except Exception as e:
        logger.warning("daily_log._invalidate: %s", e)


# ═════════════════════════════════════════════════════════════════
# Lecturas
# ═════════════════════════════════════════════════════════════════
def partes(pid, autor=None, dia=None) -> list:
    """Los partes de una obra, del más reciente al más viejo.

    `autor` y `dia` filtran; `dia` es una fecha o su texto `YYYY-MM-DD`.
    """
    out = [r for r in _records() if str(r.get("ProjectID", "")) == str(pid)]
    if autor is not None:
        out = [r for r in out if str(r.get("Author", "")) == str(autor)]
    if dia is not None:
        _d = dia if isinstance(dia, str) else dia.strftime("%Y-%m-%d")
        out = [r for r in out if str(r.get("Date", "")) == _d]
    # ⚠️ Por `Created`, no por `Date`: dos partes del mismo día tienen la misma fecha de
    # trabajo y lo que los ordena es cuándo se escribieron. Y descendente, porque lo que
    # se quiere ver al abrir es lo último.
    #
    # ⚠️ Y el ID desempata. Lo encontró la hoja REAL, no el guardián: dos partes escritos
    # en el MISMO MINUTO tienen el mismo `Created`, y `sorted` es estable, así que el
    # empate los dejaba en el orden en que estuvieran en la hoja — o sea el más VIEJO
    # arriba, justo al revés. Con `%H:%M` no había resolución para distinguirlos; ahora
    # `Created` lleva segundos, y el ID cubre el empate que quede.
    return sorted(out, key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))),
                  reverse=True)


def ultimo(pid, autor=None) -> dict:
    """El parte más reciente de esa obra, o `{}`."""
    _p = partes(pid, autor=autor)
    return _p[0] if _p else {}


def cuenta(pid) -> int:
    """Cuántos partes lleva la obra. Para el badge, sin traerse los textos."""
    return len(partes(pid))


def dias_cubiertos(pid) -> int:
    """Cuántos días DISTINTOS tienen parte. Es la medida del corpus, no el número de
    entradas: tres partes del mismo día son un día contado."""
    return len({str(r.get("Date", "")) for r in partes(pid) if r.get("Date")})


# ═════════════════════════════════════════════════════════════════
# Escrituras
# ═════════════════════════════════════════════════════════════════
def _next_id(recs) -> str:
    n = 0
    for r in recs:
        _v = str(r.get("ID", ""))
        if _v.startswith("LOG-"):
            n = max(n, int(_num(_v[4:]) or 0))
    from core import hojas
    try:
        return hojas.siguiente_id_libre("LOG-", n, propia=SHEET)
    except Exception as e:                       # nunca impedir dar de alta
        logger.warning("daily_log._next_id: %s", e)
        return "LOG-%04d" % (n + 1)


def crear(pid, grupo, texto, autor, dia=None) -> tuple:
    """Guarda un parte. Devuelve `(ok, mensaje_o_id)`.

    ⚠️ El texto se valida ANTES de tocar la hoja: un parte vacío no es un parte, y uno
    de veinte mil caracteres no cabe en la idea de parte (ver `MAX_TEXTO`). Decirlo
    antes es lo que permite a quien escribe arreglarlo sin perder lo escrito.
    """
    _txt = str(texto or "").strip()
    if not _txt:
        return False, t("Write what you did before saving.")
    if len(_txt) > MAX_TEXTO:
        return False, t("That is too long for a daily log ({n} of {max} characters). "
                        "Split it or shorten it.", n=len(_txt), max=MAX_TEXTO)
    if not str(pid or "").strip():
        return False, t("The daily log has to belong to a job.")

    w = _ws()
    if w is None:
        # ⚠️ El motivo REAL, no «no está configurado»: con la cuota agotada eso es
        # falso y manda a tocar los secretos en vez de esperar un minuto (v511).
        return False, timeclock.motivo_sin_hoja()

    try:
        _hoy = clock.now(grupo)
        _dia = (dia.strftime("%Y-%m-%d") if dia is not None and not isinstance(dia, str)
                else (dia or _hoy.strftime("%Y-%m-%d")))
        lid = _next_id(columnas.canonizar(
            w.get_all_records(numericise_ignore=["all"])))
        # ⚠️ Con SEGUNDOS, y no con el `%Y-%m-%d %H:%M` del resto de la app: dos partes
        # escritos en el mismo minuto empataban y salían en el orden equivocado. Es una
        # hoja nueva, así que no hay histórico que migrar por cambiar el formato — en
        # cualquier otra columna de fecha esto no sería gratis.
        # ⚠️ La fila es POSICIONAL: `Reviewed` y `ReviewedBy` nacen vacías, pero tienen que
        # ir, o la fila queda más corta que la cabecera (el fallo de v363).
        w.append_row([lid, str(grupo), str(pid), _dia, str(autor), _txt, MANUAL,
                      _hoy.strftime("%Y-%m-%d %H:%M:%S"), "", ""],
                     value_input_option="RAW")
    except Exception as e:
        logger.warning("daily_log.crear(%s): %s", pid, e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, lid


def borrar(log_id, quien) -> tuple:
    """Borra un parte. Solo puede borrarlo **su autor**, y solo el MISMO día.

    ⚠️ El límite no es burocracia: lo que hace valioso a esto es que sea lo que alguien
    dijo que hizo ese día. Borrar el parte de la semana pasada es reescribir el registro
    de la obra, que es justo lo que un parte firmado no debe permitir. El mismo día sí:
    ahí todavía se está escribiendo.
    """
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        recs = columnas.canonizar(
            w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        logger.warning("daily_log.borrar(%s): %s", log_id, e)
        return False, timeclock.motivo_sin_hoja()

    for i, r in enumerate(recs):
        if str(r.get("ID", "")) != str(log_id):
            continue
        if str(r.get("Author", "")) != str(quien):
            return False, t("Only the person who wrote it can delete it.")
        _hoy = clock.now(r.get("Group")).strftime("%Y-%m-%d")
        if str(r.get("Date", "")) != _hoy:
            return False, t("A log from another day can no longer be deleted. "
                            "Add a new one correcting it instead.")
        try:
            w.delete_rows(i + 2)
        except Exception as e:
            logger.warning("daily_log.borrar(%s): %s", log_id, e)
            return False, timeclock.motivo_sin_hoja()
        _invalidate()
        return True, t("Daily log deleted.")
    return False, t("Daily log not found.")


def revisado(r) -> bool:
    """¿Ya revisó su autor las propuestas de este parte?"""
    return bool(str((r or {}).get("Reviewed", "") or "").strip())


def marcar_revisado(log_id, quien) -> tuple:
    """El autor revisó las propuestas de su parte (confirmó lo que era, o que nada).

    ⚠️ Solo el AUTOR: el parte es de quien lo escribió (v516), y las propuestas salen de
    SUS palabras — quien no estuvo no sabe si «installed headers» fue en este ascensor.
    ⚠️ La fila se busca leyendo FRESCO: decidir dónde escribir con una caché es como se
    corrompen los datos (v323).
    """
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        logger.warning("daily_log.marcar_revisado(%s): %s", log_id, e)
        return False, timeclock.motivo_sin_hoja()
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) != str(log_id):
            continue
        if str(r.get("Author", "")) != str(quien):
            return False, t("Only the person who wrote it can review its proposals.")
        from core.num import col_letter
        _ahora = clock.now(r.get("Group")).strftime("%Y-%m-%d %H:%M:%S")
        try:
            w.batch_update([
                {"range": "%s%d" % (col_letter(_COL["Reviewed"]), i + 2), "values": [[_ahora]]},
                {"range": "%s%d" % (col_letter(_COL["ReviewedBy"]), i + 2),
                 "values": [[str(quien)]]},
            ], value_input_option="RAW")
        except Exception as e:
            logger.warning("daily_log.marcar_revisado(%s): %s", log_id, e)
            return False, timeclock.motivo_sin_hoja()
        _invalidate()
        return True, t("Reviewed.")
    return False, t("Daily log not found.")


def borrar_de_obra(pid) -> int:
    """Todos los partes de una obra, de una vez. Devuelve cuántos se fueron.

    ⚠️ Existe para `projects.delete_project`: los partes viven en OTRA hoja, así que
    borrar la obra sin esto los dejaría apuntando a algo inexistente — no da error y
    ensucia el libro para siempre. Es literalmente el fallo que v514 encontró con los
    créditos de etapa, y se escribe aquí para no volver a encontrarlo.
    """
    w = _ws()
    if w is None:
        return 0
    try:
        recs = columnas.canonizar(
            w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        logger.warning("daily_log.borrar_de_obra(%s): %s", pid, e)
        return 0
    # ⚠️ De abajo arriba: borrar por índice desplaza todo lo que va debajo.
    filas = [i + 2 for i, r in enumerate(recs)
             if str(r.get("ProjectID", "")) == str(pid)]
    n = 0
    for fila in sorted(filas, reverse=True):
        try:
            w.delete_rows(fila)
            n += 1
        except Exception as e:
            logger.warning("daily_log.borrar_de_obra(%s) fila %s: %s", pid, fila, e)
    if n:
        _invalidate()
    return n
