# -*- coding: utf-8 -*-
"""Celdas de un CSV que alguien abrirá en Excel o en una hoja de cálculo (v654).

Una celda que EMPIEZA por «=», «+», «-» o «@» la lee Excel como una FÓRMULA, y lo que exporta la
app lleva texto que escribe la gente (proveedores, conceptos, partes, nombres de obra). Delante
de esas celdas va un apóstrofo, que las deja como texto. Los números y lo que solo PARECE un
número o un teléfono («-120.00», «+61 412 345 678») no se tocan: no pueden llamar a nada.

Módulo HOJA: solo la biblioteca estándar.
"""
import re

_PELIGRO = ("=", "+", "-", "@", "\t", "\r")
# «+» o «-» seguidos SOLO de cifras, espacios y signos de número o teléfono
_NUMERICO = re.compile(r"^[+-][\d\s.,()/\-]*$")


def celda(v):
    """`v` lista para un CSV: un texto que empiece como una fórmula, con «'» delante."""
    if not isinstance(v, str) or not v:
        return v
    if v[0] in _PELIGRO and not (v[0] in "+-" and _NUMERICO.match(v)):
        return "'" + v
    return v


def fila(valores) -> list:
    return [celda(x) for x in valores]


def tabla(df):
    """El mismo DataFrame con cada celda pasada por `celda` (los números, intactos)."""
    return df.map(celda)
