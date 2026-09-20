# -*- coding: utf-8 -*-
"""Traduce cabeceras de tabla que son CLAVE de dict, por AST y por POSICIÓN.

⚠️ NO por texto. `"Credenciales"` es también el nombre de una hoja
(`credentials.SHEET`) y `"Horas"`/`"Estado"` son columnas reales del libro: un
`str.replace` sobre el fuente arrastraría eso y rompería la lectura de Sheets sin
dar ningún error. Aquí solo se reescriben los nodos que el árbol confirma como
CLAVE de un dict literal, usando sus offsets de byte.

⚠️ Y se reescribe de atrás hacia adelante, porque sustituir por offset invalida los
offsets posteriores.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

# clave española → inglés. Solo las que el clasificador da por TRADUCIBLES SOLAS
# (no identificador, no columna de editor, no valor de i18n, no leída por índice).
DIC = {
    "% consumido":   "% used",
    "Activos":       "Active",
    "Adelanto":      "Ahead",
    "Agrupación":    "Grouping",
    "Alarmas":       "Alarms",
    "Alertas":       "Alerts",
    "Artículo":      "Item",
    "Asignado a":    "Assigned to",
    "Categoría":     "Category",
    "Compras":       "Purchases",
    "Credenciales":  "Credentials",
    "Cumple":        "Compliant",
    "Emisión":       "Issued",
    "Fuera límite":  "Out of limit",
    "Jornada (h)":   "Shift (h)",
    "Límite (mm)":   "Limit (mm)",
    "Margen":        "Margin",
    "Número":        "Number",
    "Parámetro":     "Parameter",
    "Pendiente":     "Outstanding",
    "Por":           "By",
    "Proyección":    "Forecast",
    "Proyectos":     "Projects",
    "Retraso":       "Behind",
    "Situación":     "Status",
    "Tarifa/h":      "Rate/h",
    "Teléfono":      "Phone",
    "Ubicación":     "Location",
    "Usuarios":      "Users",
    "Vencidos":      "Overdue",
}

# ⚠️ `report.py` y `excel_io.py` quedan FUERA: el informe admin es F5 y la cabecera
# del Excel es un documento que sale, con su propia tanda. Cada dict es
# independiente, así que traducir el de `survey_ui` no rompe el de `report`.
DESTINOS = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])

tot = 0
for f in DESTINOS:
    src = f.read_text(encoding="utf-8")
    try:
        tr = ast.parse(src)
    except Exception as e:
        print(f"  ⚠️ {f.name} no parsea: {e}")
        continue
    b = src.encode("utf-8")
    puntos = []
    for n in ast.walk(tr):
        if not isinstance(n, ast.Dict):
            continue
        for k in n.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str) \
               and k.value in DIC:
                seg = ast.get_source_segment(src, k)
                if seg is None:
                    continue
                # offset de byte del literal completo (con sus comillas)
                lineas = b.split(b"\n")
                ini = sum(len(x) + 1 for x in lineas[:k.lineno - 1]) + k.col_offset
                fin = sum(len(x) + 1 for x in lineas[:k.end_lineno - 1]) + k.end_col_offset
                trozo = b[ini:fin].decode("utf-8")
                # solo literales simples de una línea: nada de f-strings ni concatenación
                if k.lineno != k.end_lineno or not (
                        trozo.startswith(('"', "'")) and trozo.endswith(('"', "'"))):
                    print(f"  ⚠️ salto {f.name}:{k.lineno} {k.value!r} (no es literal simple)")
                    continue
                q = trozo[0]
                nuevo = q + DIC[k.value] + q
                puntos.append((ini, fin, nuevo, k.value))
    if not puntos:
        continue
    for ini, fin, nuevo, _ in sorted(puntos, reverse=True):   # ⚠️ de atrás adelante
        b = b[:ini] + nuevo.encode("utf-8") + b[fin:]
    nueva = b.decode("utf-8")
    try:
        ast.parse(nueva)
    except SyntaxError as e:
        print(f"  ✗ {f.name}: el resultado NO parsea, no se escribe ({e})")
        continue
    f.write_text(nueva, encoding="utf-8")
    hechas = {p[3] for p in puntos}
    print(f"  OK  {f.name}: {len(puntos)} claves ({len(hechas)} distintas)")
    tot += len(puntos)

print(f"\n{tot} claves traducidas")
