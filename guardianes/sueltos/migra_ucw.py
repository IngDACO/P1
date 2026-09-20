"""v405 · `use_container_width=True` → `width="stretch"`.

Por qué ahora: el runtime lo dice al arrancar — «use_container_width will be removed
after 2025-12-31». Hay FECHA y ya pasó, así que puede desaparecer en cualquier versión.

⚠️ NO es un reemplazo a ciegas. Medido antes: 203 usos, todos con `True`; 201 son de
Streamlit y los 8 elementos implicados aceptan `width` (tipo `Width`, que admite
"stretch"/"content"); y **2 son de `st_folium`**, que tiene su PROPIO parámetro con ese
nombre — convertirlos rompe el mapa, y es justo el arreglo de v307 que llenó el hueco
blanco de la Ruta del día. Esos dos se localizan por AST y se saltan.

En seco por defecto; `--apply` escribe.
"""
import ast
import io
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
APLICAR = "--apply" in sys.argv
VIEJO, NUEVO = "use_container_width=True", 'width="stretch"'

ficheros = sorted(BASE.glob("core/*.py")) + [BASE / "app.py"]
total, saltados, tocados = 0, [], 0

for p in ficheros:
    src = io.open(p, encoding="utf-8").read()
    if VIEJO not in src:
        continue
    arb = ast.parse(src)
    # ⚠️ la LÍNEA DEL PARÁMETRO, no la de la llamada: en `route_ui` el `st_folium(...)`
    # abre en una línea y el `use_container_width` está en la siguiente.
    # ⚠️ Lista BLANCA por AST, no lista negra: hay un COMENTARIO en `route_ui` que
    # contiene el literal (el de v307, explicando por qué `st_folium` lo lleva). Un
    # reemplazo por texto lo reescribiría y el comentario pasaría a decir una mentira
    # sobre un parámetro que a propósito NO se toca. grep ≠ uso, otra vez.
    reales, excluir = set(), set()
    for n in ast.walk(arb):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
        for kw in n.keywords:
            if kw.arg != "use_container_width":
                continue
            reales.add(kw.value.lineno)
            if nom == "st_folium":
                excluir.add(kw.value.lineno)

    lineas = src.splitlines(keepends=True)
    cambios = 0
    for i, ln in enumerate(lineas):
        if VIEJO not in ln:
            continue
        n_ln = i + 1
        if n_ln not in reales:
            saltados.append(f"{p.name}:{n_ln}  (no es un argumento: comentario o texto)")
            continue
        total += ln.count(VIEJO)
        if n_ln in excluir:
            saltados.append(f"{p.name}:{n_ln}  (st_folium — su propio parámetro)")
            continue
        lineas[i] = ln.replace(VIEJO, NUEVO)
        cambios += ln.count(VIEJO)
    if cambios:
        tocados += 1
        print(f"  {p.name:<20} {cambios:>3}")
        if APLICAR:
            io.open(p, "w", encoding="utf-8", newline="").write("".join(lineas))

print(f"\n{total} encontrados · {total - len(saltados)} convertidos · "
      f"{len(saltados)} saltados · {tocados} ficheros")
for s in saltados:
    print(f"  SALTADO {s}")

if APLICAR:
    # comprobación DESPUÉS de escribir: solo deben quedar los de st_folium
    quedan = []
    for p in ficheros:
        s = io.open(p, encoding="utf-8").read()
        for i, ln in enumerate(s.splitlines(), start=1):
            if VIEJO in ln:
                quedan.append(f"{p.name}:{i}")
    print(f"\nquedan {len(quedan)} `use_container_width=True`: {quedan}")
    print("OK" if len(quedan) == len(saltados) else "⚠️ REVISAR: no cuadra con lo saltado")
    # ⚠️ y que todo lo escrito siga compilando: un reemplazo por líneas puede
    # descuadrar un paréntesis si algo no era lo que parecía
    import py_compile
    malos = []
    for p in ficheros:
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:                                    # noqa: BLE001
            malos.append(f"{p.name}: {e}")
    print(f"compilan: {'todos' if not malos else malos}")
else:
    print("\n(en seco: no se ha escrito nada — repetir con --apply)")
