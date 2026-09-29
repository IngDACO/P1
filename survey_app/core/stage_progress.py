# -*- coding: utf-8 -*-
"""Avance por ACTIVIDAD: el nivel de abajo del catálogo de etapas (v514).

## Qué cambia

Hasta v513 el avance de cada etapa se **tecleaba**: el campo movía un porcentaje en una
rejilla. Con el catálogo de v512 eso deja de tener sentido — una etapa no es una cosa,
son entre 3 y 24 actividades concretas, y «¿cuánto va de Car Assembly?» no se contesta
con una intuición sino diciendo **qué se hizo**.

Aquí se guarda eso: qué actividades se han acreditado, y cuánto de cada una.

    avance de la etapa = Σ(peso de la actividad × su %) / Σ(peso de sus actividades)

## ⚠️ La hoja es DISPERSA, y es lo que hace esto viable

Solo hay fila para lo que se ha acreditado. Una obra de instalación tiene **143
actividades**: crearlas todas al dar de alta serían 143 escrituras por obra, un libro
con miles de filas vacías y una pantalla imposible de mirar. La lista completa ya vive
en el catálogo (`stages.plan_de`), que no cuesta nada; la hoja solo lleva lo que pasó.

## ⚠️ El número sigue viviendo en `Activities.Progress`

Lo tentador era calcular el avance de la etapa al vuelo y no guardarlo. Sería un
segundo número diciendo lo mismo que la rejilla, y de los dos saldría una cifra distinta
en cuanto alguien tocara una (regla v361). Peor: **todo lo de abajo lee
`Activities.Progress`** — `compute_avance`, la curva S real, el SPI, la cadena de v500,
la línea base de v501 y, al final del todo, la reclamación que se cobra (v507/v510).

Así que al acreditar una actividad se **recalcula su etapa y se escribe ahí**. Lo que
cambia no es dónde está el dato: es **quién lo escribe**. Las reglas de esa escritura
—las fechas reales de inicio y fin que se ponen solas (v162)— son las de
`projects._lote_avance`, las mismas de la rejilla vieja: no se duplican. ⚠️ v528 · Lo que
ya no se reusa es el camino de `save_field_progress`, que leía y escribía cada hoja por
separado; ver `acreditar`.

## ⚠️ Solo para obras con plan sellado

Una obra anterior a v512 no tiene `StagePlanJSON`, así que no hay contra qué catálogo
acreditar. Se dice y no se hace, en vez de inventar un plan por su tipo: adivinarlo
reescribiría el cronograma de una obra en curso sin que nadie lo pidiera.
"""
import datetime as _dt
import logging
import re

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter
from core.num import num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "StageProgress"
# ⚠️ v525 · `WorkDate` AL FINAL (v363): el DÍA en que se hizo el trabajo, que no es el día
# en que se registró (`Updated`). Un parte del lunes confirmado el jueves se hizo el lunes,
# y de aquí salen las fechas reales de la etapa — la curva S real y el historial.
HEADERS = ["ID", "Group", "ProjectID", "StageOrder", "Activity", "Pct",
           "Note", "Source", "UpdatedBy", "Updated", "WorkDate"]
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# De dónde salió el crédito. Por ahora solo a mano; el parte diario en texto añadirá
# el suyo, y entonces poder distinguirlos es lo que permite medir si acierta.
MANUAL = "manual"
# v523 · Confirmado por el usuario desde las propuestas de un parte (la nota lleva el ID
# del parte). ⚠️ El mismo texto que `parte_propuestas.ORIGEN`: lo vigila `verif_v523`.
PARTE = "log"


def _fecha_trabajo(fecha, grupo) -> str:
    """El DÍA en que se hizo el trabajo, `YYYY-MM-DD` (v525): el del parte, o hoy.

    ⚠️ Una fecha que no se entiende cae en HOY, y una del FUTURO también: una fecha real
    posterior a hoy dibujaría en la curva avance que todavía no ha pasado.
    ⚠️ «Hoy» sale del MISMO `clock.now(grupo).strftime` que el sello `Updated` de
    `acreditar`: dos relojes distintos podrían discrepar justo a medianoche.
    """
    hoy = _dt.date.fromisoformat(clock.now(grupo).strftime("%Y-%m-%d")[:10])
    try:
        if fecha is None or str(fecha).strip() == "":
            return hoy.isoformat()
        s = (fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)).strip()[:10]
        if not _ISO.match(s):
            return hoy.isoformat()
        return min(_dt.date.fromisoformat(s), hoy).isoformat()
    except (TypeError, ValueError):
        return hoy.isoformat()


def _fecha_de(r) -> str:
    """El día de trabajo de un crédito GUARDADO: su `WorkDate`; si es anterior a v525 y no
    lo tiene, el día en que se registró (`Updated`) — que es lo que valía entonces."""
    for k in ("WorkDate", "Updated"):
        s = str((r or {}).get(k, "") or "").strip()[:10]
        if _ISO.match(s):
            return s
    return ""


def acreditado(pid) -> dict:
    """`{(orden, actividad): pct}` de lo acreditado en la obra — para quien tenga que
    cruzar propuestas con lo ya hecho (`parte_propuestas`) sin volver a pedirlo."""
    return _mapa(pid)


def de_parte(pid, log_id) -> list:
    """Lo que se acreditó desde ESE parte (y sigue acreditado)."""
    return [r for r in creditos(pid)
            if str(r.get("Source", "")) == PARTE and str(r.get("Note", "")) == str(log_id)
            and _num(r.get("Pct")) > 0]

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
        logger.warning("stage_progress: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: con ellas cae a `get_sheet`, que CREA la hoja — un lector que
    escribe (regla v145). La crea la primera acreditación."""
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
        logger.warning("stage_progress._invalidate: %s", e)


# ═════════════════════════════════════════════════════════════════
# Lecturas
# ═════════════════════════════════════════════════════════════════
def creditos(pid, etapa=None) -> list:
    """Lo acreditado en esa obra (o solo en esa etapa)."""
    out = [r for r in _records() if str(r.get("ProjectID", "")) == str(pid)]
    if etapa is not None:
        out = [r for r in out if int(_num(r.get("StageOrder"))) == int(_num(etapa))]
    return out


def _mapa(pid) -> dict:
    """`{(orden, actividad): pct}` de lo acreditado. Un índice para no recorrer N veces."""
    return {(int(_num(r.get("StageOrder"))), str(r.get("Activity", ""))):
            max(0.0, min(100.0, _num(r.get("Pct")))) for r in creditos(pid)}


def plan_de_obra(prj) -> list:
    """El menú de etapas y actividades de ESTA obra, según su plan sellado.

    ⚠️ Lista vacía si la obra no tiene plan (anterior a v512). No se deduce del tipo:
    inventarlo reescribiría el cronograma de una obra en curso.
    """
    from core import projects as P
    from core import stages as S
    pl = P.plan_etapas(prj)
    if not pl:
        return []
    return S.plan_de(pl.get("tipo") or str((prj or {}).get("Type", "")),
                     pl.get("condicionales") or (),
                     pl.get("pct_ripout"))


def _ver_actual() -> str:
    """La versión del catálogo de hoy. Import perezoso: `stages` es hoja y no hay
    ninguna razón para atarlo al import de este módulo."""
    from core import stages as S
    return S.VERSION


def version_desfasada(prj) -> str:
    """La versión del plan de la obra si NO es la del catálogo de hoy, o `""`.

    ⚠️ Esto tapa un hueco real de v512. El plan sella la **versión** del juego de pesos,
    pero hoy el catálogo vive en el código y solo hay UNA versión: nada impide añadir
    una etapa mañana y que `plan_de_obra` devuelva, para una obra creada ayer, un menú
    distinto del que tenía. Los créditos se colgarían de la etapa equivocada —los
    órdenes se desplazan— y el avance saldría mal **sin un solo error**.

    Hasta que existan juegos de pesos guardados de verdad, lo honesto es **detectarlo y
    negarse a escribir**, no calcular sobre un menú que no es el suyo. Leer y mostrar sí
    se permite: esconder la obra sería peor que enseñarla con un aviso.
    """
    from core import projects as P
    from core import stages as S
    _v = str(P.plan_etapas(prj).get("version", "") or "")
    return _v if (_v and _v != S.VERSION) else ""


def _sobre(plan, mapa) -> list:
    """El plan con lo acreditado superpuesto. **La única forma de cruzarlos.**

    ⚠️ Existe para que la pantalla y el recálculo de `acreditar` usen exactamente el
    mismo cruce. Dos maneras de mezclar catálogo y créditos acabarían enseñando un
    porcentaje y guardando otro (regla v361).
    """
    from core import stages as S
    out = []
    for i, e in enumerate(plan or [], start=1):
        _acts = [{**a, "pct": (mapa or {}).get((i, a["nombre"]), 0.0)}
                 for a in e["actividades"]]
        # ⚠️ v519 · Las INFORMATIVAS van en su PROPIA clave, nunca dentro de
        # `actividades`. Esa es toda la garantía de que no mueven el avance: `avance_de`
        # recibe `_acts` y nada más, así que aunque estén marcadas no llegan a la fórmula
        # — ni a la curva S, ni al SPI, ni a la reclamación, que leen lo que de aquí sale.
        _info = [{"nombre": n, "pct": (mapa or {}).get((i, n), 0.0)}
                 for n in S.informativas(e.get("pista"), e.get("numero"))]
        out.append({**e, "orden": i, "actividades": _acts, "informativas": _info,
                    "pct": avance_de(_acts)})
    return out


def detalle(pid, prj) -> list:
    """Las etapas de la obra con sus actividades y lo acreditado en cada una.

    Es lo que pinta la pantalla: la lista COMPLETA sale del catálogo (no cuesta nada) y
    encima se superpone lo poco que hay en la hoja.
    """
    return _sobre(plan_de_obra(prj), _mapa(pid))


def avance_de(actividades) -> float:
    """El % de una etapa a partir de sus actividades. **La única fórmula.**

    ⚠️ Pondera por el peso de cada actividad, no por cuántas hay: terminar «Install
    motor bedplate» (17% de su etapa) no vale lo mismo que «Seal penetrations» (12%).
    Y divide por la suma de los pesos PRESENTES, así que es escala-invariante igual que
    `projects.compute_avance` — si un día se añade una actividad, el % se recalcula solo
    en vez de bajar de golpe.
    """
    tot = sum(_num(a.get("peso_en_etapa")) for a in (actividades or []))
    if tot <= 0:
        return 0.0
    acc = sum(_num(a.get("peso_en_etapa")) * _num(a.get("pct")) for a in actividades)
    return round(acc / tot, 1)


# ═════════════════════════════════════════════════════════════════
# Escritura
# ═════════════════════════════════════════════════════════════════
def _indice(recs, pid) -> tuple:
    """De la hoja leída FRESCA: `({clave: fila}, {clave: pct}, {clave: día de trabajo})`
    de lo acreditado en la obra, con `clave = (orden, actividad)`.

    ⚠️ Decidir DÓNDE escribir con una caché es como se corrompen los datos (v323). Y el
    avance que se recalcula sale de aquí también, no de la caché de la pantalla: con dos
    personas acreditando la misma obra en menos de 120 s, la caché no vería lo del otro y
    la etapa se reescribiría con un % MENOR del que tiene.
    ⚠️ Con filas repetidas —no debería haberlas—, la fila es la PRIMERA (donde escribía
    `_fila` hasta v527) y el % y el día, la ÚLTIMA (lo que enseña `_mapa`).
    """
    filas, pct, dias = {}, {}, {}
    for i, r in enumerate(recs or []):
        if str(r.get("ProjectID", "")) != str(pid):
            continue
        k = (int(_num(r.get("StageOrder"))), str(r.get("Activity", "")))
        filas.setdefault(k, i + 2)
        pct[k] = max(0.0, min(100.0, _num(r.get("Pct"))))
        dias[k] = _fecha_de(r)
    return filas, pct, dias


def acreditar(pid, grupo, prj, creditos_nuevos, quien="", origen=MANUAL, fecha=None) -> tuple:
    """Acredita actividades y **recalcula las etapas que tocan**.

    `creditos_nuevos` = `[{'etapa': orden, 'actividad': nombre, 'pct': 0-100, 'nota': ''}]`
    `fecha` (v525) = el día en que se HIZO el trabajo (el del parte); sin ella, hoy.

    ⚠️ Solo toca las etapas mencionadas. Recalcular todas escribiría de nuevo filas que
    nadie movió, y cada reescritura es una oportunidad de pisar algo (el criterio del
    guardado parcial de v499/v502).

    ## ⚠️ v528 · Tres hojas, una lectura y una escritura
    Guardar tocaba `StageProgress`, `Activities` y `Projects` por separado: ~9 llamadas a
    Google y 7-8 s en producción (~1 s cada una desde el Cloud). Las tres viven en el
    mismo libro, así que se leen FRESCAS en UNA llamada y se escribe todo en OTRA; solo
    las filas NUEVAS van aparte, con `append_rows`, porque es lo único que hace sitio al
    final de la hoja sin pisar a nadie. Las reglas de fechas de `Activities` siguen
    siendo UNA sola (`projects._lote_avance`, la misma que usa la rejilla vieja).
    """
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    _plan = plan_de_obra(prj)
    if not _plan:
        return False, t("This job has no stage plan, so there is nothing to credit "
                        "against. It was created before the stage catalogue existed.")
    # ⚠️ Si el catálogo cambió desde que nació la obra, su menú de hoy NO es el suyo:
    # los órdenes se desplazan y el crédito se colgaría de otra etapa, sin error.
    _vieja = version_desfasada(prj)
    if _vieja:
        return False, t("This job was planned with stage catalogue {a}, and the current "
                        "one is {b}. Crediting against a different catalogue would put "
                        "the work on the wrong stage.", a=_vieja, b=_ver_actual())
    # ⚠️ Lo que no está en el catálogo de ESTA obra no se acredita: sería avance que no
    # cuenta para ningún denominador, o sea un número que no se puede explicar.
    _validas = {(i, a["nombre"]) for i, e in enumerate(_plan, start=1)
                for a in e["actividades"]}
    # ⚠️ v519 · Las INFORMATIVAS de esta obra también se pueden marcar —«entran», decidió
    # el usuario—, pero van en su propio conjunto: ver abajo por qué importa separarlas.
    from core import stages as S
    _info = {(i, n) for i, e in enumerate(_plan, start=1)
             for n in S.informativas(e.get("pista"), e.get("numero"))}
    _malos = [c for c in (creditos_nuevos or [])
              if (int(_num(c.get("etapa"))), str(c.get("actividad", "")))
              not in (_validas | _info)]
    if _malos:
        return False, t("Not in this job's plan: {x}",
                        x=", ".join(str(c.get("actividad", "?")) for c in _malos[:3]))

    from core import hojas
    from core import projects as P
    aws, _e_act = P._activities_ws()
    pws, _e_prj = P._projects_ws()
    if _e_act or _e_prj:
        return False, _e_act or _e_prj
    try:
        _leido = hojas.frescas({SHEET: w, P.ACTIVITIES_SHEET: aws, P.PROJECTS_SHEET: pws})
    except Exception as e:
        # Sin lectura no se sabe dónde escribir: no se escribe NADA.
        return False, "%s: %s" % (t("Error saving"), e)

    _ahora = clock.now(grupo).strftime("%Y-%m-%d %H:%M")
    _hoy = clock.now(grupo).strftime("%Y-%m-%d")[:10]
    _dia = _fecha_trabajo(fecha, grupo)
    # ⚠️ El mapa NUEVO se arma en memoria, no releyendo la hoja después de escribir.
    # Releer costaba una lectura extra por acreditación —con el techo de 60/min que ya
    # nos mordió en v511— y ataba la corrección a que la invalidación de caché hubiera
    # funcionado. Lo que se acaba de escribir ya se sabe: no hay que preguntárselo a
    # Google. Lo destapó el guardián, que con la hoja sustituida veía el 0 que la
    # relectura tapaba.
    # ⚠️ v525 · Y por lo mismo las fechas de trabajo de lo YA acreditado se toman de la
    # lectura de ANTES de escribir. v528 · Esa lectura es la fresca, no la caché.
    _filas, _despues, _fechas = _indice(_leido.get(SHEET), pid)
    _tocadas, _nuevas, _lote_sp = set(), [], []
    for c in (creditos_nuevos or []):
        _et = int(_num(c.get("etapa")))
        _ac = str(c.get("actividad", ""))
        _pc = max(0.0, min(100.0, _num(c.get("pct"))))
        # ⚠️ Solo una actividad CON PESO toca su etapa. Marcar una informativa guarda el
        # hecho y nada más: sin esto, su etapa se recalculaba y se reescribía en
        # `Activities.Progress` con el MISMO número — una escritura inútil contra la
        # cuota y, peor, una que haría creer que la informativa movió algo.
        if (_et, _ac) in _validas:
            _tocadas.add(_et)
        _despues[(_et, _ac)] = _pc
        _fechas[(_et, _ac)] = _dia
        row = _filas.get((_et, _ac))
        if row is None:
            _nuevas.append(["SP-%s-%d-%d" % (pid, _et, len(_nuevas)), str(grupo),
                            str(pid), str(_et), _ac, str(_pc),
                            str(c.get("nota", "")), str(origen), str(quien), _ahora, _dia])
        else:
            _lote_sp += [{"range": "%s%d" % (_col_letter(_COL[k]), row), "values": [[str(v)]]}
                         for k, v in (("Pct", _pc), ("Note", c.get("nota", "")),
                                      ("Source", origen), ("UpdatedBy", quien),
                                      ("Updated", _ahora), ("WorkDate", _dia))]

    # ── y ahora el número que lee todo lo demás ──────────────────────────────
    _det = {e["orden"]: e for e in _sobre(_plan, _despues)}
    _cambios = []
    for o in sorted(_tocadas):
        if o not in _det:
            continue
        # ⚠️ v525 · Las fechas REALES de la etapa salen de TODOS sus créditos con peso, no
        # del de ahora: el inicio es el primer día en que se hizo algo de ella y el fin el
        # último. Un parte del lunes confirmado el jueves no fecha la etapa el jueves.
        _ds = sorted(f for f in (_fechas.get((o, a["nombre"])) for a in _det[o]["actividades"]
                                 if _despues.get((o, a["nombre"]), 0) > 0) if f)
        _cambios.append({"orden": o, "avance": _det[o]["pct"],
                         "inicio": _ds[0] if _ds else "",
                         "fin": _ds[-1] if (_ds and _det[o]["pct"] >= 100) else ""})
    _lote_act, _acts = P._lote_avance(_leido.get(P.ACTIVITIES_SHEET), pid, _cambios, _hoy)
    _lote_prj, _antes, _escritos = [], {}, {}
    if _lote_act:
        # ⚠️ Es el `_recompute_project_avance` de siempre, sin sus dos lecturas: la obra se
        # recalcula con las actividades que se van a escribir, no releyéndolas después.
        _lote_prj, _antes, _escritos = P._lote_obra(_leido.get(P.PROJECTS_SHEET), pid, _acts)
        if _lote_prj is None:
            # ⚠️ ANTES de escribir nada: hasta v527 los créditos quedaban guardados y la
            # obra sin recalcular, porque el fallo de `update_project` no se miraba.
            return False, t("Project not found.")

    if _nuevas:
        try:
            w.append_rows(_nuevas, value_input_option="RAW")
        except Exception as e:
            return False, "%s: %s" % (t("Error saving"), e)
    try:
        hojas.escribir([(w, _lote_sp), (aws, _lote_act), (pws, _lote_prj)])
    except Exception as e:
        _invalidate()
        P._invalidate()
        if _nuevas and _cambios:
            # ⚠️ Se dice, no se traga: el crédito nuevo quedó guardado pero la etapa no se
            # movió, y sin aviso el usuario vería su trabajo registrado y el avance quieto.
            return False, "%s (%s)" % (t("The activity was saved but the stage progress "
                                         "could not be updated"), e)
        # Sin filas nuevas, lo que falló era TODO lo que había que escribir.
        return False, "%s: %s" % (t("Error saving"), e)
    _invalidate()
    if not _cambios:
        return True, t("Saved.")
    P._invalidate()
    if _escritos:
        # ⚠️ El rastro de cambios del avance y el estado, como hacía `update_project`,
        # con el «antes» de la lectura fresca en vez del de la caché. Fuera del guardado:
        # si la anotación falla, el cambio del usuario ya está hecho (v342).
        try:
            from core import auditoria
            auditoria.registrar("proyecto", pid, auditoria.diff(_antes, _escritos),
                                grupo=str(_antes.get("Group", "")))
        except Exception as e:
            logger.warning("stage_progress: no se pudo auditar %s: %s", pid, e)
    return True, "%s: %s" % (t("Stages updated"),
                             ", ".join("#%d %.1f%%" % (c["orden"], c["avance"])
                                       for c in _cambios))


def borrar(pid, etapa, actividad, grupo, prj, quien="") -> tuple:
    """Quita un crédito (se marcó por error) y recalcula su etapa.

    ⚠️ Pone el % a CERO en vez de borrar la fila: así queda constancia de que alguien lo
    tocó y de cuándo. Una fila que desaparece no deja rastro de haber existido.
    """
    return acreditar(pid, grupo, prj,
                     [{"etapa": etapa, "actividad": actividad, "pct": 0.0,
                       "nota": t("cleared")}], quien=quien)
