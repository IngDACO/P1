"""Cierra la fuga de caché entre inquilinos: el LIBRO entra en la clave.

Transformación, por módulo:
  1. la función cacheada `X()` pasa a llamarse `X_cached(_libro)`  →  el id del
     libro entra en la CLAVE de `st.cache_data`;
  2. se deja un envoltorio `X()` con el nombre de siempre, que resuelve el libro
     y llama al cacheado  →  **ningún call-site cambia**;
  3. en `_invalidate`, `X.clear()` pasa a `X_cached.clear()`.

⚠️ El paso 3 no es cosmético: si se queda `X.clear()`, X ya no es la función
cacheada, `.clear()` lanza AttributeError y el `except` lo traga → la caché deja
de limpiarse y nadie se entera. Es LITERALMENTE la regresión de v344, que vivió
4 versiones. Por eso hay un guardián aparte que lo comprueba.

Solo toca módulos de INQUILINO: los que leen hojas globales (Login, Grupos,
Rieles, Manuales) no tienen fuga — su libro es siempre el maestro.
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

# módulo → [(función cacheada, expresión de la hoja para resolver el libro)]
OBJETIVOS = {
    "alerts.py":      [("_records", '"Alarmas"')],
    "auditoria.py":   [("_records", "SHEET")],
    "catalogo.py":    [("_records", "SHEET")],
    "clientes.py":    [("_records", "CLIENTES_SHEET")],
    "credentials.py": [("_records", "SHEET")],
    "expenses.py":    [("_records", "SHEET")],
    "invoices.py":    [("_records", "SHEET")],
    "orders.py":      [("_records", "SHEET")],
    "payroll.py":     [("_records", "SHEET")],
    "prestart.py":    [("_records", "SHEET")],
    "quotes.py":      [("_records", "SHEET")],
    "toolruns.py":    [("_records", "SHEET")],
    "roster.py":      [("_trab_records", "TRABAJOS_SHEET"), ("_roster_records", "ROSTER_SHEET")],
    "inventory.py":   [("_records", "title")],
    "projects.py":    [("_records", "title"), ("_fichaje_records", '"Sheet1"')],
    "timeclock.py":   [("_cached_records", '"Sheet1"')],
}

DEC = re.compile(r"^@st\.cache_data\([^)]*\)\s*$")


def transforma(ruta: pathlib.Path, nombre: str, hoja_expr: str, informe: list) -> bool:
    src = ruta.read_text(encoding="utf-8")
    lineas = src.splitlines()

    # localizar el decorador + def
    i_def = None
    for i, l in enumerate(lineas):
        if re.match(rf"^def {re.escape(nombre)}\(", l) and i and DEC.match(lineas[i - 1].strip()):
            i_def = i
            break
    if i_def is None:
        informe.append(f"      ‼️ no se encontró `{nombre}` decorada")
        return False

    firma = lineas[i_def]
    params = firma[firma.index("(") + 1:firma.rindex(")")]
    nuevo = f"{nombre}_cached"

    # 1) renombrar la def y meter `_libro` como PRIMER parámetro
    p_nuevos = "_libro: str" + (f", {params}" if params.strip() else "")
    resto = firma[firma.rindex(")") + 1:]              # conserva el `-> list:` si lo hay
    lineas[i_def] = f"def {nuevo}({p_nuevos}){resto}"

    # 2) fin de la función (primera línea a nivel 0 que no sea vacía/comentario)
    j = i_def + 1
    while j < len(lineas):
        l = lineas[j]
        if l.strip() and not l[0].isspace() and not l.startswith(("#", ")")):
            break
        j += 1

    # el argumento con el que el envoltorio resuelve el libro
    arg = "title" if hoja_expr == "title" else hoja_expr
    llamada = f"_libro_de({arg})" if hoja_expr == "title" else f"_libro_de({hoja_expr})"
    pase = f"{nuevo}({llamada}" + (f", {params}" if params.strip() else "") + ")"
    envoltorio = [
        "",
        "",
        f"def {nombre}({params}):",
        f'    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).',
        "",
        "    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se",
        "    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el",
        "    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.",
        '    """',
        f"    return {pase}",
    ]
    lineas[j:j] = envoltorio

    # 3) `X.clear()` → `X_cached.clear()`
    txt = "\n".join(lineas)
    n_clear = txt.count(f"{nombre}.clear()")
    txt = txt.replace(f"{nombre}.clear()", f"{nuevo}.clear()")
    # y la variante `for fn in (_records,)`
    txt = re.sub(rf"\(\s*{re.escape(nombre)}\s*,", f"({nuevo},", txt)

    ruta.write_text(txt + ("\n" if src.endswith("\n") else ""), encoding="utf-8")
    informe.append(f"      ✓ {nombre} → {nuevo}(_libro)   ·   .clear() reescritos: {n_clear}")
    return True


# helper compartido: se inyecta en cada módulo tocado
HELPER = '''

def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""
'''

print("== cerrando la fuga ==")
for mod, funcs in OBJETIVOS.items():
    ruta = BASE / mod
    if not ruta.exists():
        print(f"   ‼️ falta {mod}")
        continue
    print(f"   {mod}")
    informe = []
    src = ruta.read_text(encoding="utf-8")
    if "_libro_de" not in src:
        # el helper va tras los imports, antes de la primera def
        m = re.search(r"^(?:from|import)\s.*$", src, re.M)
        pos = src.index("\ndef ") if "\ndef " in src else len(src)
        src = src[:pos] + HELPER + src[pos:]
        ruta.write_text(src, encoding="utf-8")
    for nombre, hoja in funcs:
        transforma(ruta, nombre, hoja, informe)
    print("\n".join(informe))
