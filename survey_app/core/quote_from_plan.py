# -*- coding: utf-8 -*-
"""Cotizar leyendo el PLANO (v509).

Tercera oportunidad del estudio de mercado del 20/09/2026. Simpro y Sage tienen
*estimating*; lo que nadie puede hacer es **presupuestar una instalación a partir del PDF
del plano**, porque hay que extraerlo primero — y eso ya lo hacemos para el survey.

## Cómo funciona

Del plano salen tres cosas que mueven cantidades: **NS** (paradas), el **modelo** y el
**código de riel**. Un ítem del catálogo dice de cuál depende su cantidad:

| Regla | Cantidad |
|---|---|
| `fixed` | 1 — puesta en marcha, movilización |
| `per_stop` | NS — puertas de rellano, botoneras, trabajo por planta |
| `per_stop_minus_1` | NS − 1 — lo que va ENTRE plantas |
| `manual` | no se propone: esa cantidad no sale del plano |

## ⚠️ Lo que NO hace, y es la decisión que más importa

**Si el plano no da el dato, la línea entra con cantidad CERO y marcada**, nunca con un 1
inventado ni omitida en silencio.

Omitirla haría la cotización **más barata** sin que nadie lo note, y sub-cotizar en
silencio es el fallo caro de esta función: se descubre al facturar, cuando ya se firmó.
Un 1 inventado es peor todavía — esconde el error dentro de un número que parece
calculado. Con cantidad 0 y el motivo al lado, alguien tiene que decidir.

Es el mismo criterio que `orders.atrasadas` («sin fecha no se puede decir que llega
tarde») y que el expediente de v506 («un ítem de tercero no pasa por cálculo»).

## Módulo HOJA en su núcleo

`cantidad_de` y `REGLAS` no importan nada: reciben la regla y el plano y devuelven la
cantidad y, si falta, el motivo. `proponer` compone usando `quotes.linea_de`, que es
quien sabe de precios y márgenes — aquí no se calcula ni un importe.
"""

# ── Las reglas ───────────────────────────────────────────────────
FIJA = "fixed"
POR_PARADA = "per_stop"
POR_PARADA_MENOS_1 = "per_stop_minus_1"
MANUAL = "manual"

REGLAS = (MANUAL, FIJA, POR_PARADA, POR_PARADA_MENOS_1)
REGLA_DEFECTO = MANUAL          # ⚠️ por defecto NO se propone: no se adivina

ETIQUETAS = {
    MANUAL: "Manual (not taken from the drawing)",
    FIJA: "Fixed (1 per job)",
    POR_PARADA: "One per stop",
    POR_PARADA_MENOS_1: "One per stop, minus one",
}

_SIN_NS = "the drawing does not state the number of stops"


def _ns(plano) -> int:
    """Las paradas del plano, o 0 si no se pudo leer. No lanza: el plano trae de todo."""
    try:
        v = (plano or {}).get("ns")
        return int(float(str(v))) if v not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def cantidad_de(regla, plano) -> tuple:
    """`(cantidad, motivo_si_falta)` para una regla sobre un plano.

    ⚠️ El motivo NO es un error: es lo que se enseña al lado de una línea que hay que
    decidir a mano. Una cantidad 0 sin motivo sería un silencio, y es justo lo que esta
    función existe para no hacer.
    """
    r = str(regla or REGLA_DEFECTO)
    if r == FIJA:
        return 1, ""
    if r in (POR_PARADA, POR_PARADA_MENOS_1):
        n = _ns(plano)
        if n <= 0:
            return 0, _SIN_NS
        return (n if r == POR_PARADA else max(0, n - 1)), ""
    return 0, ""                       # MANUAL o desconocida: no se propone


def proponer(plano, items, margen_pct=None) -> dict:
    """`{lineas, incompletas, saltadas, plano}` a partir del plano y del catálogo.

    `items` = ítems del catálogo (con su `QtyRule`). Los de regla MANUAL se saltan: su
    cantidad no sale del plano y proponerlos sería inventar.
    """
    from core import quotes as Q          # perezoso (patrón v342): evita ciclos

    lineas, incompletas, saltadas = [], [], []
    for it in (items or []):
        regla = str(it.get("QtyRule", "") or REGLA_DEFECTO)
        if regla == MANUAL or regla not in REGLAS:
            saltadas.append(str(it.get("Name", "")))
            continue
        cant, falta = cantidad_de(regla, plano)
        l = Q.linea_de(it, cant, margen_pct)
        # ⚠️ Las marcas viajan con guion bajo: la pantalla las usa para pintar el aviso
        # y NO se guardan en la cotización (una línea guardada es un precio pactado, no
        # una nota de cómo se propuso).
        l["_regla"] = regla
        l["_falta"] = falta
        lineas.append(l)
        if falta:
            incompletas.append({"nombre": str(it.get("Name", "")), "motivo": falta})
    return {"lineas": lineas, "incompletas": incompletas, "saltadas": saltadas,
            "plano": {"ns": _ns(plano), "modelo": (plano or {}).get("modelo"),
                      "rail": (plano or {}).get("rail")}}


def limpiar(lineas) -> list:
    """Quita las marcas `_*` antes de guardar: en la cotización no viajan."""
    return [{k: v for k, v in (l or {}).items() if not str(k).startswith("_")}
            for l in (lineas or [])]
