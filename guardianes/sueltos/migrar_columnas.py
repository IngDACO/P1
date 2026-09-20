# -*- coding: utf-8 -*-
"""Renombra las COLUMNAS al ingles en el codigo, por AST y por posicion.

  python migrar_columnas.py seco      -> cuenta y muestra, sin escribir
  python migrar_columnas.py aplicar   -> escribe (y se niega si algo no compila)

⚠️ Lo que NO se toca, y es lo que hace segura la migracion:
  · las CLAVES de un dict que va dentro de un `pd.DataFrame(...)`: son etiquetas de
    display, no columnas de la hoja (y `tabla.CABECERAS` ya las traduce);
  · cualquier literal en los modulos EXENTOS, donde la misma palabra es otra cosa.
"""
import ast
import io
import sys
from pathlib import Path

# ⚠️ El mapa se lee del MODULO de la app, no de una copia: dos copias divergen y
# eso ya dejo aqui 4 entradas espejo que alla se habian quitado.
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
from core.columnas import LEGADO as COLUMNAS

RAIZ = Path(r"C:\Users\diego\P1\survey_app")
MODO = sys.argv[1] if len(sys.argv) > 1 else "seco"

# ⚠️ Modulos donde estas palabras NO son columnas de hoja.
EXENTOS = {"columnas.py", "i18n.py", "theme.py", "tabla.py", "diagrams.py", "plumb.py",
           "schedule.py", "calculations.py", "optimizer.py", "highlighting.py",
           "bs_logic.py", "rail_cut.py", "buffer_cut.py", "belting.py",
           "excel_io.py", "report.py", "user_report.py", "interpretation.py",
           "chat_agent.py", "survey_calc.py", "num.py"}


def dentro_de_dataframe(arbol):
    """Offsets de las CLAVES de dicts que alimentan un pd.DataFrame (no tocar)."""
    fuera = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "DataFrame":
            for d in ast.walk(n):
                if isinstance(d, ast.Dict):
                    for k in d.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            fuera.add((k.lineno, k.col_offset))
    return fuera


def objetivos(src):
    arbol = ast.parse(src)
    fuera = dentro_de_dataframe(arbol)
    out = []
    for n in ast.walk(arbol):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
            continue
        if n.value not in COLUMNAS:
            continue
        if (n.lineno, n.col_offset) in fuera:
            continue
        out.append(n)
    return out


tot, ficheros = 0, 0
for p in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if p.name in EXENTOS:
        continue
    src = p.read_text(encoding="utf-8")
    objs = objetivos(src)
    if not objs:
        continue
    lineas = src.split("\n")
    # de atras hacia delante: reemplazar desplaza las columnas de la misma linea
    for n in sorted(objs, key=lambda x: (x.lineno, x.col_offset), reverse=True):
        i = n.lineno - 1
        if n.end_lineno != n.lineno:
            continue                      # literal multilinea: no deberia haber
        # ⚠️ `col_offset` es un offset en BYTES UTF-8, no en caracteres. Cortando el
        # `str` directamente, cualquier linea con «·», tilde o emoji ANTES del literal
        # sale desplazada: el trozo empieza por la letra y no por la comilla. La guarda
        # de abajo lo saltaba (nunca corrompio nada) pero dejaba el renombrado A MEDIAS,
        # y una lectura a medias devuelve "" en silencio.
        crudo = lineas[i].encode("utf-8")
        trozo = crudo[n.col_offset:n.end_col_offset].decode("utf-8", "replace")
        if len(trozo) < 2 or trozo[0] not in "\"'":
            continue
        q = trozo[0]
        nuevo = (q + COLUMNAS[n.value] + q).encode("utf-8")
        lineas[i] = (crudo[:n.col_offset] + nuevo + crudo[n.end_col_offset:]).decode("utf-8")
        tot += 1
    texto = "\n".join(lineas)
    ast.parse(texto)                      # nunca escribir algo que no compile
    if MODO == "aplicar":
        io.open(p, "w", encoding="utf-8", newline="").write(texto)
    ficheros += 1

print("%s: %d literales de columna en %d ficheros"
      % ("APLICADO" if MODO == "aplicar" else "en seco", tot, ficheros))
