"""¿Se puede convertir `use_container_width` a `width=` sin romper nada?

No se convierte a ciegas. Antes hay que saber:
  1. qué ELEMENTO recibe el parámetro en cada uno de los ~200 sitios;
  2. cuáles NO son de Streamlit (⚠️ `st_folium` tiene su propio parámetro con ese
     nombre: convertirlo revienta el mapa, y es el arreglo de v307);
  3. y si cada elemento de Streamlit acepta de verdad `width=` en la versión instalada.
"""
import ast
import inspect
import io
import pathlib
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")

sitios = defaultdict(list)          # nombre del elemento -> [(fichero, línea, valor)]
for p in sorted(BASE.glob("core/*.py")) + [BASE / "app.py"]:
    src = io.open(p, encoding="utf-8").read()
    arb = ast.parse(src)
    for n in ast.walk(arb):
        if not isinstance(n, ast.Call):
            continue
        for kw in n.keywords:
            if kw.arg != "use_container_width":
                continue
            f = n.func
            nom = getattr(f, "attr", "") or getattr(f, "id", "")
            val = getattr(kw.value, "value", "?")
            sitios[nom].append((p.name, n.lineno, val))

tot = sum(len(v) for v in sitios.values())
print(f"{tot} usos en {len({f for v in sitios.values() for f, _l, _x in v})} ficheros\n")

import streamlit as st                                            # noqa: E402
print(f"streamlit {st.__version__}\n")
print(f"{'elemento':<22}{'usos':>5}  ¿acepta width=?   valores")
print("-" * 74)
NO_ST = set()
for nom, us in sorted(sitios.items(), key=lambda kv: -len(kv[1])):
    fn = getattr(st, nom, None)
    if fn is None:
        estado = "NO ES DE STREAMLIT"
        NO_ST.add(nom)
    else:
        try:
            acepta = "width" in inspect.signature(fn).parameters
        except (TypeError, ValueError):
            acepta = None
        estado = "sí" if acepta else ("NO ACEPTA" if acepta is False else "no se pudo mirar")
    vals = Counter(v for _f, _l, v in us)
    print(f"  {nom:<20}{len(us):>5}  {estado:<17} {dict(vals)}")

print("\n== ⚠️ los que NO son de Streamlit (no se tocan) ==")
for nom in sorted(NO_ST):
    for f, l, v in sitios[nom]:
        print(f"  {f}:{l}  {nom}(use_container_width={v})")
