# -*- coding: utf-8 -*-
"""Contador de llamadas a la API de Google (FASE 0.2 de la ruta).

## Por qué existe

El techo de Google Sheets es de **60 lecturas y 60 escrituras por minuto y por cuenta
de servicio**, y la app tiene UNA cuenta para todos los clientes. Decidir entre «más
cuentas de servicio» y «salir de Sheets» es la decisión más cara de la ruta, y hasta
ahora se habría tomado por intuición: nadie sabía cuánto se consume de verdad.

Esto lo mide. No cuesta ni una llamada: se apunta lo que YA se está haciendo.

## Cómo

El enganche va en `timeclock._ConReintento.request`, que es **nuestra** subclase del
cliente HTTP (nació en v290 para el reintento). Es el único punto por el que pasa todo
el tráfico de gspread, así que no hay que instrumentar 90 módulos ni tocar las tripas
de una librería de terceros.

⚠️ **Nunca puede romper una petición.** Un contador que tumba una lectura es peor que
no tener contador, así que `anota` se traga cualquier fallo suyo.

⚠️ **Vive en memoria del PROCESO, no en una hoja.** Escribir las métricas en Sheets
gastaría justo la cuota que se quiere medir. Streamlit Cloud corre un solo proceso para
todos los usuarios, así que este contador mide exactamente lo que el techo limita: el
consumo de la cuenta de servicio. Se pierde al reiniciar, y eso está bien: lo que
interesa es el PICO de un minuto, no el histórico.

⚠️ **Módulo HOJA**: solo stdlib. Si importara `timeclock` habría ciclo, porque es
`timeclock` quien lo llama.
"""
import logging
import re
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

# Tope de eventos guardados. A 60 llamadas/min son ~2,8 h de historia; de sobra para
# ver el pico de una mañana y acotado para que la memoria no crezca sin límite.
_MAX = 10000
_EVENTOS = deque(maxlen=_MAX)
_LOCK = threading.Lock()
_DESDE = time.time()

_RE_LIBRO = re.compile(r"/spreadsheets/([A-Za-z0-9_\-]{20,})")

# ⚠️ Lectura y escritura tienen cuotas SEPARADAS (60/min cada una), así que hay que
# clasificarlas bien. Y no vale mirar el método HTTP: `values:batchGet` —la llamada
# que más usa la app desde v339— es un GET, pero `values:append` y `values:batchUpdate`
# son POST igual que otras lecturas por lote. Manda el ENDPOINT.
_ESCRITURAS = (":batchUpdate", ":append", ":clear", ":batchClear",
               "values:update", "/values/")


def _tipo(method: str, endpoint: str) -> str:
    ep = str(endpoint or "")
    m = str(method or "").upper()
    if m in ("POST", "PUT", "PATCH", "DELETE"):
        # Un POST a `values:batchGet` sigue siendo lectura; lo demás, escritura.
        if ":batchGet" in ep:
            return "lectura"
        return "escritura"
    if any(marca in ep for marca in _ESCRITURAS) and m not in ("GET", "HEAD"):
        return "escritura"
    return "lectura"


def anota(method: str, endpoint: str) -> None:
    """Apunta UNA llamada. Nunca lanza: la petición manda, el contador no."""
    try:
        m = _RE_LIBRO.search(str(endpoint or ""))
        libro = m.group(1) if m else "?"
        ev = (time.time(), libro, _tipo(method, endpoint))
        with _LOCK:
            _EVENTOS.append(ev)
    except Exception:                       # noqa: BLE001 - jamás puede propagar
        pass


def _ventana(eventos, ini, fin):
    return [e for e in eventos if ini <= e[0] < fin]


def resumen(ventana: int = 60) -> dict:
    """Consumo medido. `ventana` en segundos para el «ahora mismo».

    Devuelve el ÚLTIMO minuto, el PICO de un minuto observado y el reparto por libro,
    que es lo que dice si el problema es la carga sostenida o las ráfagas.
    """
    with _LOCK:
        evs = list(_EVENTOS)
    ahora = time.time()
    out = {
        "desde": _DESDE, "minutos_vivo": max(0.0, (ahora - _DESDE) / 60.0),
        "total": len(evs), "truncado": len(evs) >= _MAX,
        "ahora": {"lectura": 0, "escritura": 0},
        "pico": {"lectura": 0, "escritura": 0, "cuando": None},
        "por_libro": {}, "por_minuto": [],
    }
    if not evs:
        return out

    for _t, _lib, _k in _ventana(evs, ahora - ventana, ahora + 1):
        out["ahora"][_k] += 1

    # ⚠️ El pico se busca con ventana DESLIZANTE anclada en cada evento, no partiendo
    # el tiempo en minutos de reloj: una ráfaga a caballo de dos minutos (las 6:59:40
    # a las 7:00:20, que es justo cuando ficha la cuadrilla) se repartiría entre dos
    # cubos y no aparecería en ninguno.
    for i, (t0, _l, _k) in enumerate(evs):
        lec = esc = 0
        for t1, _l2, k2 in evs[i:]:
            if t1 - t0 >= 60:
                break
            if k2 == "lectura":
                lec += 1
            else:
                esc += 1
        if lec > out["pico"]["lectura"]:
            out["pico"]["lectura"] = lec
            out["pico"]["cuando"] = t0
        if esc > out["pico"]["escritura"]:
            out["pico"]["escritura"] = esc

    for _t, lib, k in evs:
        d = out["por_libro"].setdefault(lib, {"lectura": 0, "escritura": 0})
        d[k] += 1

    # serie por minuto de reloj, para ver la forma del consumo
    cubos = {}
    for t, _l, k in evs:
        cubo = int(t // 60) * 60
        d = cubos.setdefault(cubo, {"lectura": 0, "escritura": 0})
        d[k] += 1
    out["por_minuto"] = [(c, v["lectura"], v["escritura"]) for c, v in sorted(cubos.items())]
    return out


def reiniciar() -> None:
    """Vacía el contador (para medir una operación concreta desde cero)."""
    global _DESDE
    with _LOCK:
        _EVENTOS.clear()
    _DESDE = time.time()
