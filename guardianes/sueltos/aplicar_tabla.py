# -*- coding: utf-8 -*-
"""Pone `tabla.cfg(...)` en TODAS las tablas de la interfaz (v450).

⚠️ Se aplica a todas, no solo a las que hoy tienen una cabecera española, y es
deliberado: verificado en vivo que `column_config` **ignora las claves que la tabla
no tiene**, así que el mapa entero es inofensivo — y así el arreglo no depende de
que mi atribución estática de «qué dict alimenta qué tabla» sea perfecta, que ya
falló dos veces mientras medía.

⚠️ Los reemplazos van de ATRÁS hacia delante: editar por desplazamiento invalida
todos los que vienen después en el mismo fichero.
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
DESTINOS = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
TABLA = {"dataframe", "data_editor"}
SECO = "--seco" in sys.argv


def _idx(lineas, ln, col):
    """(línea 1-based, columna) → índice absoluto en el texto."""
    return sum(len(x) for x in lineas[:ln - 1]) + col


def procesar(ruta: Path):
    src = ruta.read_text(encoding="utf-8")
    tr = ast.parse(src)
    lineas = src.splitlines(keepends=True)

    ediciones = []          # (ini, fin, texto)
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") in TABLA
                and isinstance(getattr(n.func, "value", None), ast.Name)
                and n.func.value.id == "st"):
            continue
        kw = next((k for k in n.keywords if k.arg == "column_config"), None)
        if kw is not None:
            # ya migrada
            if isinstance(kw.value, ast.Call) \
               and getattr(kw.value.func, "attr", "") == "cfg":
                continue
            ini = _idx(lineas, kw.value.lineno, kw.value.col_offset)
            fin = _idx(lineas, kw.value.end_lineno, kw.value.end_col_offset)
            ediciones.append((ini, fin,
                              "tabla.cfg(None, " + src[ini:fin] + ")"))
        else:
            # insertar el kwarg justo ANTES del paréntesis de cierre
            fin = _idx(lineas, n.end_lineno, n.end_col_offset) - 1
            antes = src[:fin].rstrip()
            coma = "" if antes.endswith(("(", ",")) else ", "
            ediciones.append((fin, fin, coma + "column_config=tabla.cfg()"))

    if not ediciones:
        return 0

    nuevo = src
    for ini, fin, txt in sorted(ediciones, key=lambda e: -e[0]):
        nuevo = nuevo[:ini] + txt + nuevo[fin:]

    # import a nivel de MÓDULO (regla v342: ámbito, no presencia)
    if not any(isinstance(x, ast.ImportFrom) and x.module == "core"
               and any(a.name == "tabla" for a in x.names)
               and x.col_offset == 0
               for x in ast.walk(ast.parse(nuevo))):
        arb = ast.parse(nuevo)
        ancla = None
        for x in arb.body:
            if isinstance(x, (ast.Import, ast.ImportFrom)):
                ancla = x
        if ancla is None:
            raise SystemExit(f"{ruta.name}: sin import donde anclar")
        ln = ancla.end_lineno
        nl = nuevo.splitlines(keepends=True)
        nl.insert(ln, "from core import tabla\n")
        nuevo = "".join(nl)

    ast.parse(nuevo)                       # ⚠️ no se escribe nada que no compile
    if not SECO:
        io.open(ruta, "w", encoding="utf-8", newline="").write(nuevo)
    return len(ediciones)


if __name__ == "__main__":
    tot = 0
    for f in DESTINOS:
        n = procesar(f)
        if n:
            print(f"  {f.name:24} {n} tabla(s)")
            tot += n
    print(f"\n{tot} tablas con column_config{' (SECO)' if SECO else ''}")
