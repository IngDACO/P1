# -*- coding: utf-8 -*-
"""La MEMORIA del agente del parte (v610): lo que las cuadrillas ya confirmaron.

Decisión del usuario (27/10/2026): «El agente de logs debe tener la capacidad de aprender, debe
tener una memoria» — GLOBAL (una para todos los clientes) y AUTOMÁTICA.

## Qué guarda

Lecciones «frase del parte → actividad del catálogo», con cuántas veces se CONFIRMARON (el autor
marcó esa casilla) y cuántas se RECHAZARON (la dejó sin marcar al confirmar el parte), y las REGLAS
que pone la oficina. Antes de cada lectura el agente recibe las lecciones firmes
(`para_el_agente`). La memoria cambia lo que el agente propone y pregunta; acreditar sigue siendo
el clic del autor (la regla «proponer, no asumir»).

## ⚠️ Global, sin llevar lo de un cliente a otro

Solo viajan frases CORTAS de trabajo (las palabras del trozo, ≤ `MAX_FRASE`) y el NOMBRE de una
actividad del catálogo. Las respuestas libres del autor («What did you mean?») NO entran: se
vuelven lección cuando, releído el parte, marca la casilla. Y cada lección recuerda de qué GRUPO
salió: en el panel, un admin ve y borra las de su grupo (y las reglas); el propietario, todas.

## De dónde aprende

Solo de lo que leyó el AGENTE (`termino` = las palabras del trozo). Lo del vocabulario no: sus
términos son raíces normalizadas («instal sil»), no frases que el modelo pueda reconocer.
«Nothing to credit» no enseña nada (no dice qué estaba mal).

Hoja `AgentMemory`, GLOBAL (`timeclock.SHEETS_GLOBALES`): vive en el libro maestro.
"""
import datetime as _dt
import logging
import re
import sys

import streamlit as st

from core import hojas, timeclock
from core.i18n import t
from core.num import col_letter as _col_letter
from core.num import num as _num

logger = logging.getLogger(__name__)

SHEET = "AgentMemory"
# ⚠️ Columnas nuevas, siempre AL FINAL (v363).
HEADERS = ["ID", "Phrase", "Activity", "Kind", "Confirmed", "Rejected", "Group", "CreatedBy",
           "LogID", "Created", "Updated", "Active"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}
REGLA, APRENDIDA = "rule", "learned"
MAX_FRASE = 80
MAX_LECCIONES = 150       # las que van al agente: ≈ 2.000 tokens, en la caché
MIN_RECHAZOS = 2          # «no es eso»: dos rechazos y ninguna confirmación


def normaliza(frase) -> str:
    """La forma con que se guarda y se compara una frase: minúsculas, espacios simples, sin
    signos en los bordes, recortada. «Isntalled the motor.» → «isntalled the motor»."""
    s = re.sub(r"\s+", " ", str(frase or "")).strip().lower()
    s = re.sub(r"^[\W_]+|[\W_]+$", "", s)
    return s[:MAX_FRASE].strip()


# ── la hoja ──────────────────────────────────────────────────────────────────
def _ws():
    """⚠️ `get_sheet` (resuelve el libro como el lector: global → maestro) y CREA la hoja si
    falta: solo lo usan las escrituras.
    ⚠️ Bajo AppTest, NINGUNA: el guardián de v607 confirma un parte leído por el agente, y
    aprender escribiría en el libro maestro REAL (y lo crearía). Quien la quiera, la sustituye."""
    if "streamlit.testing.v1.local_script_runner" in sys.modules:
        return None
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("agente_memoria: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _records_cached() -> list:
    """⚠️ SIN cabeceras: con ellas se crearía la hoja al LEER (un lector que escribe, v145)."""
    return hojas.registros(SHEET) or []


def _records() -> list:
    # ⚠️ Bajo AppTest (los guardianes), nada de la hoja REAL: los de la tarjeta del parte
    # (v607, v608…) leerían el libro maestro en cada suite. Un guardián que quiera memoria
    # sustituye `_records` (la misma regla que `parte_agente.clave_api`, trampa 44).
    if "streamlit.testing.v1.local_script_runner" in sys.modules:
        return []
    try:
        return _records_cached()
    except Exception as e:
        logger.warning("agente_memoria: no se pudo leer %s: %s", SHEET, e)
        return []


def _invalidate():
    hojas.invalidar(SHEET)
    try:
        _records_cached.clear()
    except Exception:
        pass


def _ahora() -> str:
    try:
        from core import clock
        return clock.now().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return _dt.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── leer ─────────────────────────────────────────────────────────────────────
def lecciones(grupo=None) -> list:
    """Las lecciones ACTIVAS. `grupo` filtra a las de ese grupo y las reglas sin grupo (lo que
    ve un admin); `None`, todas (el propietario y el agente)."""
    out = []
    for r in _records():
        if str(r.get("Active", "")).strip().upper() == "NO":
            continue
        if not str(r.get("Phrase", "")).strip() or not str(r.get("Activity", "")).strip():
            continue
        if grupo is not None and str(r.get("Group", "")) not in (str(grupo), ""):
            continue
        out.append(dict(r, Confirmed=int(_num(r.get("Confirmed"))), Rejected=int(_num(r.get("Rejected")))))
    return out


def firmes(filas) -> list:
    """Las que el agente recibe: `[(tipo, frase, actividad, veces)]`, las reglas primero.
    · «rule»  → la puso la oficina: manda;
    · «means» → confirmada más veces que rechazada;
    · «not»   → rechazada `MIN_RECHAZOS` veces o más y nunca confirmada."""
    out = []
    for r in filas or []:
        f, a = str(r["Phrase"]), str(r["Activity"])
        c, x = int(r.get("Confirmed", 0)), int(r.get("Rejected", 0))
        if str(r.get("Kind")) == REGLA:
            out.append(("rule", f, a, 0, str(r.get("Updated", ""))))
        elif c >= 1 and c > x:
            out.append(("means", f, a, c, str(r.get("Updated", ""))))
        elif c == 0 and x >= MIN_RECHAZOS:
            out.append(("not", f, a, x, str(r.get("Updated", ""))))
    _rango = {"rule": 0, "means": 1, "not": 2}
    out.sort(key=lambda z: (_rango[z[0]], -z[3], z[1]))
    return [z[:4] for z in out[:MAX_LECCIONES]]


def para_el_agente() -> str:
    """El bloque CREW MEMORY para el agente, o "" sin lecciones. ⚠️ Ordenado de forma
    DETERMINISTA: va en la caché del prompt y cualquier byte distinto la invalida."""
    _l = firmes(lecciones())
    if not _l:
        return ""
    _txt = []
    for tipo, f, a, n in _l:
        if tipo == "rule":
            _txt.append("- «%s» → %s (rule set by the office)" % (f, a))
        elif tipo == "means":
            _txt.append("- «%s» → %s (confirmed %d×)" % (f, a, n))
        else:
            _txt.append("- «%s» is NOT %s (rejected %d×)" % (f, a, n))
    return ("CREW MEMORY — what crews confirmed before, from their own ticks. Prefer these "
            "readings when a fragment says the same thing, unless the log clearly says "
            "otherwise. Use only activities that are in the JOB PLAN.\n" + "\n".join(_txt))


# ── aprender ─────────────────────────────────────────────────────────────────
def observaciones(destinos) -> list:
    """De la revisión de un parte (lo OFRECIDO y lo MARCADO por destino, la forma de
    `parte_propuestas.registro`) a `[(frase, actividad, confirmada, rechazada)]`.

    · una casilla propuesta suelta («a») marcada → confirmada; sin marcar → rechazada;
    · una opción de pregunta («q») marcada → confirmada; sin marcar → rechazada SOLO si se
      marcó otra opción de la MISMA pregunta (si no marcó ninguna, no dijo nada de ellas);
    · las de la lista de una etapa («e») y lo ya acreditado, nada.
    """
    out = {}
    for x in (destinos or {}).values():
        if not isinstance(x, dict):
            continue
        marc = {(int(_num(o)), str(a)) for o, a in (x.get("marcadas") or [])}
        _ofr = [o for o in (x.get("ofrecidas") or []) if isinstance(o, (list, tuple)) and len(o) >= 4]
        _q_con = {str(o[3]) for o in _ofr if o[0] == "q" and (int(_num(o[1])), str(o[2])) in marc}
        for tipo, orden, act, term in (o[:4] for o in _ofr):
            f = normaliza(term)
            if tipo not in ("a", "q") or not f:
                continue
            ok = (int(_num(orden)), str(act)) in marc
            if not ok and tipo == "q" and str(term) not in _q_con:
                continue
            k = (f, str(act))
            c, r = out.get(k, (0, 0))
            out[k] = (c + ok, r + (not ok))
    return [(f, a, c, r) for (f, a), (c, r) in sorted(out.items())]


def aprender(obs, grupo, autor, log_id) -> tuple:
    """Suma las observaciones a la memoria: `(ok, cuántas lecciones tocadas)`. Lee FRESCO (v323)
    y escribe en UN lote; las lecciones nuevas, con `append_rows`. ⚠️ Una regla de la oficina
    no se mueve con lo que se marque: se suma igual, pero manda."""
    if not obs:
        return True, 0
    w = _ws()
    if w is None:
        return False, 0
    try:
        from core import columnas
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        logger.warning("agente_memoria.aprender: %s", e)
        return False, 0
    idx = {}
    for i, r in enumerate(recs):
        if str(r.get("Active", "")).strip().upper() != "NO":
            idx.setdefault((normaliza(r.get("Phrase")), str(r.get("Activity", ""))), (i + 2, r))
    _n = max([int(_num(str(r.get("ID", ""))[4:])) for r in recs if str(r.get("ID", "")).startswith("MEM-")] or [0])
    lote, nuevas, ahora = [], [], _ahora()
    for f, a, c, x in obs:
        hit = idx.get((f, a))
        if hit:
            fila, r = hit
            lote += [{"range": "%s%d" % (_col_letter(_COL["Confirmed"]), fila),
                      "values": [[str(int(_num(r.get("Confirmed"))) + c)]]},
                     {"range": "%s%d" % (_col_letter(_COL["Rejected"]), fila),
                      "values": [[str(int(_num(r.get("Rejected"))) + x)]]},
                     {"range": "%s%d" % (_col_letter(_COL["Updated"]), fila), "values": [[ahora]]}]
        else:
            _n += 1
            nuevas.append(["MEM-%04d" % _n, f, a, APRENDIDA, str(c), str(x), str(grupo or ""),
                           str(autor or ""), str(log_id or ""), ahora, ahora, ""])
    try:
        if lote:
            w.batch_update(lote, value_input_option="RAW")
        if nuevas:
            w.append_rows(nuevas, value_input_option="RAW")
    except Exception as e:
        logger.warning("agente_memoria.aprender: %s", e)
        return False, 0
    _invalidate()
    return True, len(obs)


def poner_regla(frase, actividad, grupo, autor) -> tuple:
    """La oficina enseña algo a mano: «frase → actividad», que MANDA sobre lo aprendido."""
    f, a = normaliza(frase), str(actividad or "").strip()
    if not f or not a:
        return False, t("Write the phrase and choose the activity.")
    w = _ws()
    if w is None:
        return False, timeclock.motivo_sin_hoja()
    try:
        from core import columnas
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
        if any(normaliza(r.get("Phrase")) == f and str(r.get("Activity")) == a
               and str(r.get("Kind")) == REGLA and str(r.get("Active", "")).upper() != "NO" for r in recs):
            return False, t("That rule already exists.")
        _n = max([int(_num(str(r.get("ID", ""))[4:])) for r in recs if str(r.get("ID", "")).startswith("MEM-")] or [0])
        ahora = _ahora()
        w.append_row(["MEM-%04d" % (_n + 1), f, a, REGLA, "0", "0", str(grupo or ""), str(autor or ""),
                      "", ahora, ahora, ""], value_input_option="RAW")
    except Exception as e:
        logger.warning("agente_memoria.poner_regla: %s", e)
        return False, timeclock.motivo_sin_hoja()
    _invalidate()
    return True, t("Rule saved: «{f}» → {a}.", f=f, a=a)


def olvidar(ids, grupo, es_propietario) -> tuple:
    """Desactiva lecciones (`Active=NO`, no se borra la fila: queda rastro). ⚠️ Un admin solo
    las de SU grupo —las reglas del propietario (sin grupo) las ve, pero no las quita—; el
    propietario, cualquiera."""
    ids = {str(i) for i in ids or ()}
    if not ids:
        return True, 0
    w = _ws()
    if w is None:
        return False, 0
    try:
        from core import columnas
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        logger.warning("agente_memoria.olvidar: %s", e)
        return False, 0
    lote = []
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) not in ids:
            continue
        if not es_propietario and str(r.get("Group", "")) != str(grupo):
            continue
        lote.append({"range": "%s%d" % (_col_letter(_COL["Active"]), i + 2), "values": [["NO"]]})
    if not lote:
        return False, 0
    try:
        w.batch_update(lote, value_input_option="RAW")
    except Exception as e:
        logger.warning("agente_memoria.olvidar: %s", e)
        return False, 0
    _invalidate()
    return True, len(lote)
