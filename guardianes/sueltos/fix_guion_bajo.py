"""El parámetro NO puede empezar por `_`: Streamlit lo excluye de la clave.

⚠️ `st.cache_data` trata los argumentos cuyo nombre empieza por guión bajo como
«no hashables» y **los deja fuera de la clave** (es su convención para pasar
conexiones y demás). Al llamarlo `_libro`, el arreglo de aislamiento quedó INERTE:
la firma decía lo correcto y la caché seguía sin distinguir inquilinos.

Solo lo delató instrumentar quién se ejecutaba de verdad.
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

n_tot = 0
for f in sorted(BASE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    if "_libro: str" not in src:
        continue
    nuevo = src.replace("(_libro: str", "(libro: str")
    # el docstring del envoltorio menciona el parámetro; se deja como está.
    if nuevo != src:
        f.write_text(nuevo, encoding="utf-8")
        n = src.count("(_libro: str")
        n_tot += n
        print(f"   {f.name:<18} {n} firma(s) corregida(s)")

print(f"\n   {n_tot} parámetros renombrados `_libro` → `libro`")
print("   (los envoltorios pasan el valor POSICIONALMENTE, así que no cambian)")
