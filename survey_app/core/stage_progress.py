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
cambia no es dónde está el dato: es **quién lo escribe**. Y la escritura se delega en
`projects.save_field_progress`, que ya hace el lote en una sola llamada y pone solas las
fechas reales de inicio y fin (v162) — reusarla es también no duplicar esa lógica.

## ⚠️ Solo para obras con plan sellado

Una obra anterior a v512 no tiene `StagePlanJSON`, así que no hay contra qué catálogo
acreditar. Se dice y no se hace, en vez de inventar un plan por su tipo: adivinarlo
reescribiría el cronograma de una obra en curso sin que nadie lo pidiera.
"""
import logging

import streamlit as st

from core import clock, timeclock
from core.num import col_letter as _col_letter
from core.num import num as _num

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "StageProgress"
HEADERS = ["ID", "Group", "ProjectID", "StageOrder", "Activity", "Pct",
           "Note", "Source", "UpdatedBy", "Updated"]

# De dónde salió el crédito. Por ahora solo a mano; el parte diario en texto añadirá
# el suyo, y entonces poder distinguirlos es lo que permite medir si acierta.
MANUAL = "manual"

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
    out = []
    for i, e in enumerate(plan or [], start=1):
        _acts = [{**a, "pct": (mapa or {}).get((i, a["nombre"]), 0.0)}
                 for a in e["actividades"]]
        out.append({**e, "orden": i, "actividades": _acts, "pct": avance_de(_acts)})
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
def _fila(w, pid, etapa, actividad):
    """(nº de fila, registro) leyendo FRESCO: decidir DÓNDE escribir con una caché es
    como se corrompen los datos (v323)."""
    try:
        from core import columnas, valores
        recs = valores.canonizar(
            columnas.canonizar(w.get_all_records(numericise_ignore=["all"])), SHEET)
    except Exception as e:
        logger.warning("stage_progress._fila: %s", e)
        return None, None
    for i, r in enumerate(recs):
        if (str(r.get("ProjectID", "")) == str(pid)
                and int(_num(r.get("StageOrder"))) == int(_num(etapa))
                and str(r.get("Activity", "")) == str(actividad)):
            return i + 2, r
    return None, None


def acreditar(pid, grupo, prj, creditos_nuevos, quien="", origen=MANUAL) -> tuple:
    """Acredita actividades y **recalcula las etapas que tocan**.

    `creditos_nuevos` = `[{'etapa': orden, 'actividad': nombre, 'pct': 0-100, 'nota': ''}]`

    ⚠️ Solo toca las etapas mencionadas. Recalcular todas escribiría de nuevo filas que
    nadie movió, y cada reescritura es una oportunidad de pisar algo (el criterio del
    guardado parcial de v499/v502).
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
    _malos = [c for c in (creditos_nuevos or [])
              if (int(_num(c.get("etapa"))), str(c.get("actividad", ""))) not in _validas]
    if _malos:
        return False, t("Not in this job's plan: {x}",
                        x=", ".join(str(c.get("actividad", "?")) for c in _malos[:3]))

    _ahora = clock.now(grupo).strftime("%Y-%m-%d %H:%M")
    # ⚠️ El mapa NUEVO se arma en memoria, no releyendo la hoja después de escribir.
    # Releer costaba una lectura extra por acreditación —con el techo de 60/min que ya
    # nos mordió en v511— y ataba la corrección a que la invalidación de caché hubiera
    # funcionado. Lo que se acaba de escribir ya se sabe: no hay que preguntárselo a
    # Google. Lo destapó el guardián, que con la hoja sustituida veía el 0 que la
    # relectura tapaba.
    _despues = dict(_mapa(pid))
    _tocadas, _nuevas = set(), []
    for c in (creditos_nuevos or []):
        _et = int(_num(c.get("etapa")))
        _ac = str(c.get("actividad", ""))
        _pc = max(0.0, min(100.0, _num(c.get("pct"))))
        _tocadas.add(_et)
        _despues[(_et, _ac)] = _pc
        row, _ant = _fila(w, pid, _et, _ac)
        if row is None:
            _nuevas.append(["SP-%s-%d-%d" % (pid, _et, len(_nuevas)), str(grupo),
                            str(pid), str(_et), _ac, str(_pc),
                            str(c.get("nota", "")), str(origen), str(quien), _ahora])
        else:
            try:
                w.batch_update([{"range": "%s%d" % (_col_letter(_COL[k]), row),
                                 "values": [[str(v)]]}
                                for k, v in (("Pct", _pc), ("Note", c.get("nota", "")),
                                             ("Source", origen), ("UpdatedBy", quien),
                                             ("Updated", _ahora))],
                               value_input_option="RAW")
            except Exception as e:
                return False, "%s: %s" % (t("Error saving"), e)
    if _nuevas:
        try:
            w.append_rows(_nuevas, value_input_option="RAW")
        except Exception as e:
            return False, "%s: %s" % (t("Error saving"), e)
    _invalidate()

    # ── y ahora el número que lee todo lo demás ──────────────────────────────
    _det = {e["orden"]: e for e in _sobre(_plan, _despues)}
    _cambios = [{"orden": o, "avance": _det[o]["pct"]} for o in sorted(_tocadas)
                if o in _det]
    if not _cambios:
        return True, t("Saved.")
    from core import projects as P
    ok, msg = P.save_field_progress(pid, _cambios)
    if not ok:
        # ⚠️ Se dice, no se traga: el crédito quedó guardado pero la etapa no se movió,
        # y sin aviso el usuario vería su trabajo registrado y el avance quieto.
        return False, "%s (%s)" % (t("The activity was saved but the stage progress "
                                     "could not be updated"), msg)
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
