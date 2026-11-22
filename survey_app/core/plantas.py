# -*- coding: utf-8 -*-
"""Las PLANTAS que nombra un parte (v695, D2 del ciclo 6).

«Installed the landing door panels on levels 5 and 6», en una obra de 8 paradas, acreditaba «Install door panels»
ENTERA: un 16 % de la etapa por un 25 % del trabajo. Las puertas se montan planta a planta y en días distintos, así que
cada parte acredita SUS plantas y la actividad va subiendo (2 de 8 = 25 %) hasta tenerlas todas (decisión del usuario).

Lo lee la APP, no el modelo: se prueba sin gastar y no depende de cómo redacte el agente.
⚠️ Solo con las palabras de planta (level, floor, stop, landing): «L2» puede ser el ascensor 2 (`vocabulario.ascensores`).
Módulo HOJA: solo `re`.
"""
import re

_PAL = r"(?:levels?|lvls?|floors?|stops?|landings?)"
_NUM = r"\d{1,3}"
_SEP = r"\s*(?:,|&|\+|and|to|-|–|—|through|thru)\s*"
# «levels 3 and 4», «level 3 and level 4», «floors 2-5», «stops 1, 2 & 4», «landing no. 6»
_LISTA = re.compile(r"\b%s\s*(?:no\.?\s*)?(%s(?:%s(?:%s\s*)?%s)*)" % (_PAL, _NUM, _SEP, _PAL, _NUM), re.I)
_TODAS = re.compile(r"\b(?:all|every)\s+(?:the\s+)?%s\b" % _PAL, re.I)
_RANGO = re.compile(r"-|–|—|\bto\b|through|thru", re.I)


def de_texto(texto, ns) -> list:
    """Las plantas 1..`ns` que nombra `texto`, ordenadas: `[]` si no nombra ninguna; todas con «all levels».
    Un rango («levels 3-5», «3 to 5») cuenta entero. Lo que cae fuera de 1..ns no cuenta."""
    try:
        ns = int(ns)
    except (TypeError, ValueError):
        return []
    if ns <= 0:
        return []
    s = str(texto or "")
    if _TODAS.search(s):
        return list(range(1, ns + 1))
    out = set()
    for m in _LISTA.finditer(s):
        partes = re.split(r"(\d{1,3})", m.group(1))
        prev = None
        for i in range(1, len(partes), 2):
            n = int(partes[i])
            sep = partes[i - 1] if i > 1 else ""
            if prev is not None and _RANGO.search(sep) and n >= prev:
                out.update(range(prev, n + 1))
            else:
                out.add(n)
            prev = n
    return sorted(x for x in out if 1 <= x <= ns)


def leer(valor) -> set:
    """De la columna `Levels` de StageProgress («3,4,5») a {3, 4, 5}."""
    return {int(x) for x in re.findall(r"\d+", str(valor or ""))}


def texto(plantas) -> str:
    """{5, 3, 4} → «3, 4, 5»."""
    return ", ".join(str(x) for x in sorted(plantas or []))
