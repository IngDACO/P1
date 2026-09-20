"""Red SECUNDARIA sobre los trozos de f-string.

⚠️ El invariante de posición no puede exigir `t()` en un trozo de f-string (no es una
cadena entera), así que aquí solo queda mirar. Este barrido por IDIOMA es un AYUDANTE,
no una prueba (trampa nº28): lo que vale es la revisión a mano de los 356, ya hecha.
"""
import re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
from i18n_tool import piezas

PAL = {"el","la","los","las","un","una","unos","unas","del","al","de","que","con","por",
       "para","como","desde","hasta","sin","sobre","entre","cuando","donde","si","no",
       "se","su","sus","es","son","esta","este","estos","estas","ya","hay","tiene",
       "puede","debe","cada","todo","toda","todos","todas","otro","otra","mas","pero",
       "porque","asi","aqui","ahi","ahora","antes","despues","segun","aun","tambien",
       "solo","muy","bien","hacer","poner","ver","dar","ir","fue","han","hasta"}

def _sin(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()

UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
sosp, tot = [], 0
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    for p in piezas(RAIZ / rel):
        if not p["fstr"]:
            continue
        tot += 1
        txt = p["txt"]
        pals = set(re.findall(r"[a-záéíóúñü]+", _sin(txt)))
        if re.search(r"[áéíóúñ¿¡]", txt) or (pals & PAL):
            sosp.append(f"{m}:{p['lin']}  {txt[:88]!r}")

print(f"{tot} trozos de f-string revisados")
print(f"{len(sosp)} con acento o palabra funcional española:")
for s in sosp:
    print("   ", s)
