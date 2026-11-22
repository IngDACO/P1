# -*- coding: utf-8 -*-
"""Los días que cuenta el PLAN de una obra (v698, D1 del ciclo 6).

Hasta v697 el plan contaba días NATURALES: NS 8 → «33 days», fin el 25/12, y «should be at», el retraso, el SPI, el fin
previsto y la curva S avanzaban también en fin de semana (la cartera decía «12 behind»). Decisión del usuario (23/11):
«los días laborales de lunes a viernes cuentan siempre, menos en pausa; sábado y domingo no suman aunque estén en el
tablero: si se trabaja, es para recuperar o adelantar. Suma en progreso pero no en tiempo.»

Así que el día N del plan es el N-ésimo día que CUENTA desde el inicio: de lunes a viernes y fuera de una pausa. El
motor (`schedule`, `plan`) sigue trabajando en días de plan; aquí se pasa de día a fecha y de fecha a día, en UN sitio.

Módulo HOJA: solo `datetime` y `math`.
"""
import math
from datetime import date, timedelta

_TOPE = 40000                     # días que se recorren como mucho (≈ 110 años): nunca un bucle sin fin


def laborable(d) -> bool:
    """¿De lunes a viernes?"""
    return d.weekday() < 5


class Calendario:
    """`inicio`: el día de inicio de la obra. `pausas`: `[(desde, hasta)]`, `hasta` EXCLUIDO; `hasta=None` = la pausa
    sigue abierta y para el cálculo termina `hoy` (lo que queda del plan se cuenta desde mañana)."""

    def __init__(self, inicio, pausas=(), hoy=None):
        self.inicio = inicio
        _h = hoy or date.today()
        self.pausas = [(a, b if b is not None else _h + timedelta(days=1)) for a, b in (pausas or ()) if a]

    def cuenta(self, d) -> bool:
        """¿Ese día suma tiempo al plan? De lunes a viernes y fuera de pausa."""
        return laborable(d) and not any(a <= d < b for a, b in self.pausas)

    def fecha(self, dia) -> date:
        """El día `dia` del plan (0 = el primero que cuenta desde el inicio) → su fecha."""
        n = max(0, int(math.floor(float(dia) + 1e-9)))
        d, k = self.inicio, -1
        for _i in range(_TOPE):
            if self.cuenta(d):
                k += 1
                if k == n:
                    return d
            d += timedelta(days=1)
        return d

    def fin(self, x, desde=None) -> date:
        """El ÚLTIMO día de trabajo de un tramo del plan que acaba en `x` (excluido): el fin que se enseña. Nunca antes
        de `desde` (un tramo de duración 0)."""
        f = self.fecha(max(0, math.ceil(float(x) - 1e-9) - 1))
        if desde is not None:
            f0 = self.fecha(desde)
            if f < f0:
                return f0
        return f

    def dia(self, f) -> int:
        """Cuántos días que CUENTAN hay entre el inicio y `f` (excluido): el día del plan de esa fecha. Antes del inicio,
        negativo (un parte del día anterior al inicio)."""
        if f is None:
            return 0
        if f >= self.inicio:
            n, d = 0, self.inicio
            for _i in range(_TOPE):
                if d >= f:
                    break
                if self.cuenta(d):
                    n += 1
                d += timedelta(days=1)
            return n
        n, d = 0, f
        for _i in range(_TOPE):
            if d >= self.inicio:
                break
            if self.cuenta(d):
                n += 1
            d += timedelta(days=1)
        return -n


def pausas_de(historial, estado_actual="", hoy=None) -> list:
    """Las pausas de una obra desde su rastro de cambios (`auditoria.historial`, del más reciente al más antiguo):
    `[(desde, hasta)]`, `hasta=None` si sigue en pausa. Una obra en pausa SIN rastro (de antes de v342) cuenta en pausa
    desde hoy: no se le inventa un pasado."""
    from core.num import parse_date
    ev = []
    for r in reversed(list(historial or [])):
        _c = (r.get("cambios") or {}).get("Status")
        if not (isinstance(_c, (list, tuple)) and len(_c) == 2):
            continue
        _d = parse_date(str(r.get("Date", "") or "").split(" ")[0])
        if _d:
            ev.append((_d, str(_c[0]), str(_c[1])))
    out, abierta = [], None
    for d, antes, despues in ev:
        if despues == "On hold" and antes != "On hold" and abierta is None:
            abierta = d
        elif antes == "On hold" and despues != "On hold" and abierta is not None:
            out.append((abierta, d))
            abierta = None
    if str(estado_actual) == "On hold":
        out.append((abierta or (hoy or date.today()), None))
    return out
