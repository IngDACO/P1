# -*- coding: utf-8 -*-
"""Encadenado de actividades: quién va detrás de quién, y cuándo puede empezar cada una.

Hasta v498 el cronograma era una CADENA rígida: cada actividad empezaba justo cuando
terminaba la anterior (`build_schedule` acumulaba `cur += dur`). Eso no es un plan de obra:
las puertas de rellano y el cableado se solapan, y el atraso de los rieles no arrastraba
nada porque no había nada que arrastrar.

Aquí vive el cálculo, y SOLO el cálculo: funciones puras, sin Streamlit ni Sheets, para
poder ejercitarlo entero (v378: importar no ejecuta).

**Cómo se declara** (columna `Predecessors` de cada actividad):
- **vacío** → va detrás de la ANTERIOR. Es lo que hacía la app hasta v498, así que una obra
  que ya existe se comporta exactamente igual hasta que alguien la edite.
- **`-`** → sin predecesora: empieza el día 0, en paralelo.
- **`3`** → detrás de la actividad nº 3. `3+2` deja 2 días de espera; `3-1` la solapa un día.
- **`3;5-2`** → detrás de varias: manda la que la deje empezar MÁS TARDE.

⚠️ Las predecesoras se refieren al **número de orden** de la actividad, que es como la hoja
identifica cada fila (ProjectID + Order). Por eso reordenar o borrar tiene que REMAPEAR las
referencias: de eso se encarga `remapear`, y `projects.save_activities` la llama.
"""
import logging

from core.num import num

logger = logging.getLogger(__name__)

SIN_PREDECESORA = "-"


def parse(txt) -> list:
    """`"3;5-2"` → `[(3, 0), (5, -2)]`. Lo que no se entiende se ignora, no revienta."""
    out = []
    for trozo in str(txt or "").replace(",", ";").split(";"):
        trozo = trozo.strip()
        if not trozo or trozo == SIN_PREDECESORA:
            continue
        signo, resto = 1, trozo
        for s in ("+", "-"):
            if s in trozo[1:]:
                i = trozo.index(s, 1)
                signo, resto = (1 if s == "+" else -1), trozo[:i]
                desfase = trozo[i + 1:]
                break
        else:
            desfase = "0"
        try:
            out.append((int(float(resto)), signo * int(float(desfase or 0))))
        except Exception:
            logger.warning("plan: predecesora ilegible %r", trozo)
    return out


def formatear(pares) -> str:
    """`[(3, 0), (5, -2)]` → `"3;5-2"`. El inverso de `parse`."""
    trozos = []
    for orden, lag in pares or []:
        lag = int(lag or 0)
        trozos.append(f"{int(orden)}" + (f"+{lag}" if lag > 0 else (f"{lag}" if lag else "")))
    return ";".join(trozos)


def _pred_de(acts: list, i: int) -> list:
    """Las predecesoras EFECTIVAS de la actividad i: lo declarado, o la anterior."""
    crudo = str(acts[i].get("pred", "") or "").strip()
    if crudo == SIN_PREDECESORA:
        return []
    if not crudo:
        return [(int(acts[i - 1]["orden"]), 0)] if i > 0 else []
    return parse(crudo)


def _preparar(acts: list) -> tuple:
    """Las dependencias ya resueltas a índices: `({i: [(j, lag)]}, avisos)`.

    ⚠️ UNA sola definición para `calcular` y `pronostico`: si cada uno resolviera las
    dependencias por su cuenta, el plan y el pronóstico podrían discrepar sobre quién va
    detrás de quién — y eso no da ningún error, solo dos fechas que no cuadran (v323).
    """
    avisos = []
    orden_de = {}
    for i, a in enumerate(acts):
        try:
            orden_de[int(num(a.get("orden")))] = i
        except Exception:
            pass
    preds = {}
    for i, a in enumerate(acts):
        limpio = []
        for orden, lag in _pred_de(acts, i):
            j = orden_de.get(int(orden))
            if j is None:
                avisos.append(("falta", i, orden))
                continue
            if j == i:
                avisos.append(("ella_misma", i, orden))
                continue
            limpio.append((j, lag))
        preds[i] = limpio

    # ⚠️ Ciclos: se rompen ANTES de calcular nada (si no, la recursión no termina).
    for i in range(len(acts)):
        if i in {j for j, _l in preds.get(i, [])} or _hay_ciclo(preds, i):
            avisos.append(("ciclo", i, None))
            preds[i] = [(i - 1, 0)] if i > 0 else []
    return preds, avisos


def pronostico(acts: list, hoy: float = 0.0) -> dict:
    """Cuándo termina la obra DE VERDAD, partiendo de lo que ya pasó.

    `calcular` responde «cuándo debería»; esta responde «cuándo va a ser», que es la
    pregunta del cliente. Hasta v499 el fin previsto salía del **ritmo** (SPI: una regla
    de tres sobre el % de avance), así que una obra podía ir «al 50% en la mitad del
    plazo» con la actividad que bloquea a todas las demás sin empezar.

    `acts`: [{orden, duracion, pred, avance, ini_real, fin_real}] — `ini_real`/`fin_real`
    en días desde el inicio (None si no se saben). `hoy` = día actual.

    Las tres reglas, que es donde está el dominio:
    - **terminada** → su fecha es la REAL: ya no se mueve ni la mueve nadie;
    - **en curso**  → le queda `duración × (1 − avance)`, y eso corre **desde HOY**;
    - **sin empezar** → empieza cuando sus predecesoras la dejen, ⚠️ **nunca antes de
      HOY**: lo que tocaba el martes y no se hizo no se puede hacer el martes.
    Por eso el retraso se PROPAGA por la cadena en vez de diluirse en un promedio.
    """
    preds, avisos = _preparar(acts)
    hoy = max(0.0, num(hoy))
    inicio, fin = {}, {}
    for i in _en_orden(preds, len(acts)):
        a = acts[i]
        dur = max(0.0, num(a.get("duracion")))
        av = max(0.0, min(100.0, num(a.get("avance"))))
        ini_r, fin_r = a.get("ini_real"), a.get("fin_real")
        ini_pred = 0.0
        for j, lag in preds[i]:
            ini_pred = max(ini_pred, fin.get(j, 0.0) + lag)

        if av >= 100.0:                      # terminada: manda lo que PASÓ
            ini = num(ini_r) if ini_r is not None else max(0.0, ini_pred)
            fin[i] = num(fin_r) if fin_r is not None else ini + dur
        elif av > 0.0:                       # en curso: le queda el resto, desde hoy
            ini = num(ini_r) if ini_r is not None else max(0.0, ini_pred)
            fin[i] = max(hoy, ini) + dur * (1.0 - av / 100.0)
        else:                                # sin empezar: no puede arrancar en el pasado
            ini = max(ini_pred, hoy)
            fin[i] = ini + dur
        inicio[i] = ini

    total = max(fin.values()) if fin else 0.0
    criticas = set()
    pila = [i for i in range(len(acts)) if abs(fin.get(i, 0.0) - total) < 1e-6]
    while pila:
        i = pila.pop()
        if i in criticas:
            continue
        criticas.add(i)
        for j, lag in preds.get(i, []):
            if abs(fin.get(j, 0.0) + lag - inicio.get(i, 0.0)) < 1e-6:
                pila.append(j)

    return {"por_orden": {int(num(acts[i].get("orden"))): {
                "inicio": inicio.get(i, 0.0), "fin": fin.get(i, 0.0), "critica": i in criticas}
                for i in range(len(acts))},
            "total_dias": total,
            "avisos": avisos}


def calcular(acts: list) -> dict:
    """Cuándo empieza y termina cada actividad, y cuáles están en la ruta crítica.

    `acts`: [{orden, duracion, pred}] en el orden de la hoja. Devuelve
    `{"por_orden": {orden: {inicio, fin, critica}}, "total_dias", "avisos"}` — días desde
    el inicio del proyecto, como los usaba `build_schedule`.

    ⚠️ Un ciclo (A detrás de B y B detrás de A) colgaría el cálculo, así que se detecta y
    esa actividad pasa a ir detrás de la anterior, con aviso. Una obra mal encadenada tiene
    que seguir dibujándose: es lo que permite verla para arreglarla.
    ⚠️ Una predecesora que no existe (se borró) se ignora con aviso, en vez de dar por
    bueno un plan que empieza el día 0 sin que nadie se entere.
    """
    preds, avisos = _preparar(acts)
    inicio, fin = {}, {}
    for i in _en_orden(preds, len(acts)):
        dur = max(0.0, num(acts[i].get("duracion")))
        ini = 0.0
        for j, lag in preds[i]:
            ini = max(ini, fin.get(j, 0.0) + lag)
        inicio[i] = max(0.0, ini)
        fin[i] = inicio[i] + dur
    total = max(fin.values()) if fin else 0.0

    # ── ruta crítica: hacia atrás desde el final, por las que no tienen holgura ──
    criticas = set()
    pila = [i for i in range(len(acts)) if abs(fin.get(i, 0.0) - total) < 1e-6]
    while pila:
        i = pila.pop()
        if i in criticas:
            continue
        criticas.add(i)
        for j, lag in preds.get(i, []):
            if abs(fin.get(j, 0.0) + lag - inicio.get(i, 0.0)) < 1e-6:
                pila.append(j)

    return {"por_orden": {int(num(acts[i].get("orden"))): {
                "inicio": inicio.get(i, 0.0), "fin": fin.get(i, 0.0), "critica": i in criticas}
                for i in range(len(acts))},
            "total_dias": total,
            "avisos": avisos}


def _hay_ciclo(preds: dict, i: int, visitando=None) -> bool:
    visitando = visitando or set()
    if i in visitando:
        return True
    visitando = visitando | {i}
    return any(_hay_ciclo(preds, j, visitando) for j, _l in preds.get(i, []))


def _en_orden(preds: dict, n: int) -> list:
    """Índices en orden topológico (cada uno después de sus predecesoras)."""
    hecho, salida = set(), []
    while len(salida) < n:
        movido = False
        for i in range(n):
            if i in hecho:
                continue
            if all(j in hecho for j, _l in preds.get(i, [])):
                hecho.add(i)
                salida.append(i)
                movido = True
        if not movido:                      # no debería pasar (los ciclos ya se rompieron)
            salida += [i for i in range(n) if i not in hecho]
            break
    return salida


def remapear(pred_txt: str, mapa: dict) -> str:
    """Reescribe las referencias cuando cambian los números de orden.

    `mapa` = {orden viejo: orden nuevo}; un orden que desaparece (actividad borrada) se
    quita de la lista. ⚠️ Sin esto, reordenar el cronograma haría que «detrás de la 3»
    pasara a apuntar a otra actividad **sin que nada avise**, que es la peor forma de
    equivocar un plan.
    """
    crudo = str(pred_txt or "").strip()
    if not crudo or crudo == SIN_PREDECESORA:
        return crudo
    nuevos = [(mapa[o], lag) for o, lag in parse(crudo) if o in mapa]
    return formatear(nuevos) if nuevos else SIN_PREDECESORA
