# -*- coding: utf-8 -*-
"""Un libro de Google Sheets de SOLO LECTURA servido desde una FOTO en JSON (v586).

## Por qué existe

Varios guardianes ensayan una pantalla con los datos REALES de una obra, en solo lectura
(v539, v559). El 19/10/2026 el usuario borró todas las obras de prueba de cliente1 y esos
ensayos se quedaron sin obra: verif_v559 pasó a rojo por falta de datos, no por el código.
Atarlos a la hoja viva es atarlos a lo que el usuario haga mañana con sus datos.

La foto es la copia que se hizo ANTES de borrar (`D:\\CopeX\\respaldos`, fuera del repo:
lleva nombres de personas). Con ella el ensayo ve exactamente lo que veía, siempre igual.

## Cómo

Todo libro de cliente se abre por `timeclock._abrir` (no hay otro `open_by_key` en la
app). `instalar` lo sustituye: el libro de la foto sale de la foto, los demás (el maestro:
Login, Groups) siguen siendo los reales. `quitar` lo deja como estaba.

⚠️ SOLO LECTURA de verdad: cualquier método que no sea de lectura se APUNTA en
`intentos` y falla. Un ensayo puede envolver su escritura en un `try` y seguir; por eso
el guardián tiene que comprobar `intentos == []`, no solo que no reventó.
"""
import json

import gspread


class SoloLectura(AttributeError):
    """Subclase de AttributeError a propósito: `hasattr(ws, "algo")` tiene que dar False,
    no reventar (Python solo traga AttributeError en `hasattr`)."""


class _Celda:
    def __init__(self, fila, col, valor):
        self.row, self.col, self.value = fila, col, valor


def _numerico(v, default_blank):
    if v == "":
        return default_blank
    for tipo in (int, float):
        try:
            return tipo(v)
        except ValueError:
            pass
    return v


class _Hoja:
    def __init__(self, libro, titulo, valores, gid):
        self.spreadsheet, self.title, self.id = libro, titulo, gid
        _w = max([len(f) for f in valores] or [0])
        # ⚠️ Como gspread: `get_all_values` devuelve un RECTÁNGULO (la API recorta, gspread
        # rellena con "").
        self._v = [list(f) + [""] * (_w - len(f)) for f in valores]

    @property
    def row_count(self):
        return max(len(self._v), 1000)

    @property
    def col_count(self):
        return max([len(f) for f in self._v] or [0]) or 26

    def get_all_values(self, *a, **k):
        return [list(f) for f in self._v]

    def row_values(self, fila, *a, **k):
        f = list(self._v[fila - 1]) if 0 < fila <= len(self._v) else []
        while f and f[-1] == "":
            f.pop()
        return f

    def col_values(self, col, *a, **k):
        out = [f[col - 1] if len(f) >= col else "" for f in self._v]
        while out and out[-1] == "":
            out.pop()
        return out

    def cell(self, fila, col, *a, **k):
        v = self._v[fila - 1][col - 1] if 0 < fila <= len(self._v) and 0 < col <= len(self._v[fila - 1]) else ""
        return _Celda(fila, col, v)

    def get_all_records(self, head=1, expected_headers=None, value_render_option=None, default_blank="",
                        numericise_ignore=(), allow_underscores_in_numeric_literals=False, empty2zero=False):
        if len(self._v) < head:
            return []
        claves = self._v[head - 1]
        _todo = list(numericise_ignore or ()) == ["all"]
        out = []
        for f in self._v[head:]:
            vals = list(f) if _todo else [_numerico(x, default_blank) for x in f]
            out.append(dict(zip(claves, vals)))
        return out

    def __getattr__(self, n):
        if n.startswith("__"):
            raise AttributeError(n)
        self.spreadsheet.intentos.append("%s.%s" % (self.title, n))
        raise SoloLectura("libro_foto: «%s».%s no está permitido (solo lectura)" % (self.title, n))


class Libro:
    def __init__(self, sheet_id, hojas):
        self.id, self.title, self.intentos = sheet_id, "foto", []
        self._h = {t: _Hoja(self, t, v, i) for i, (t, v) in enumerate(hojas.items())}

    @property
    def sheet1(self):
        return list(self._h.values())[0]

    def worksheets(self, *a, **k):
        return list(self._h.values())

    def worksheet(self, titulo):
        if titulo in self._h:
            return self._h[titulo]
        raise gspread.exceptions.WorksheetNotFound(titulo)

    def values_batch_get(self, ranges, params=None):
        tramos = []
        for r in ranges:
            tit, _, a1 = str(r).partition("!")
            tit = tit[1:-1].replace("''", "'") if tit.startswith("'") else tit
            if tit not in self._h:
                raise ValueError("libro_foto: no existe la hoja %r" % tit)
            vals = self._h[tit].get_all_values()
            if a1 == "1:1":
                vals = vals[:1]
            elif a1:
                raise ValueError("libro_foto: rango no soportado %r" % r)
            vals = [list(f) for f in vals]
            for f in vals:                         # como la API: sin vacíos al final
                while f and f[-1] == "":
                    f.pop()
            tramos.append({"range": "'%s'!A1:ZZ%d" % (tit.replace("'", "''"), max(len(vals), 1)),
                           "values": vals})
        return {"spreadsheetId": self.id, "valueRanges": tramos}

    def __getattr__(self, n):
        if n.startswith("__"):
            raise AttributeError(n)
        self.intentos.append("libro.%s" % n)
        raise SoloLectura("libro_foto: libro.%s no está permitido (solo lectura)" % n)


_ESTADO = {}


def _limpiar_caches(timeclock):
    import streamlit as st
    for fn in (getattr(timeclock._abrir, "clear", None), timeclock._cached_ws.clear,
               timeclock._libro.clear, timeclock.get_sheet.clear):
        if fn:
            try:
                fn()
            except Exception:
                pass
    st.cache_data.clear()


def instalar(ruta_json):
    """Sirve el libro de la foto en lugar del real. Devuelve el `Libro` (con `intentos`)."""
    from core import timeclock
    with open(ruta_json, encoding="utf-8") as f:
        foto = json.load(f)
    libro = Libro(foto["libro"], foto["hojas"])
    real = _ESTADO.get("real") or timeclock._abrir
    _ESTADO["real"] = real

    def _abrir(sheet_id):
        return libro if str(sheet_id) == str(libro.id) else real(sheet_id)

    _limpiar_caches(timeclock)
    timeclock._abrir = _abrir
    return libro


def quitar():
    from core import timeclock
    if "real" in _ESTADO:
        timeclock._abrir = _ESTADO.pop("real")
    _limpiar_caches(timeclock)
