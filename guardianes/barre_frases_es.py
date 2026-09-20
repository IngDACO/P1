"""Las FRASES sin envolver que además parecen españolas.

⚠️ Por qué aquí sí vale el detector de idioma (trampa nº28 dice que no vale en general):
su ceguera es con etiquetas CORTAS sin acento ni palabra funcional («Fichar», «Firma»,
«Pendientes») — y ESAS ya las cubre el invariante de posición, que hoy da 0. Lo que el
invariante NO puede ver son los trozos de f-string y las cadenas armadas en una variable
(el hueco de v349), y ahí casi todo es una FRASE: 3+ palabras en español llevan acento o
artículo. Las dos redes juntas cubren lo que cada una se deja.
"""
import re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))
from barre_frases import frases            # noqa: E402

RAIZ = Path(r"C:\Users\diego\P1\survey_app")
PAL = {"el","la","los","las","un","una","unos","unas","del","al","de","que","con","por",
       "para","como","desde","hasta","sin","sobre","entre","cuando","donde","si","se",
       "su","sus","es","son","esta","este","estos","estas","ya","hay","tiene","puede",
       "debe","cada","todo","toda","todos","todas","otro","otra","pero","porque","asi",
       "aqui","ahora","antes","despues","segun","tambien","solo","muy","bien","hacer",
       "poner","ver","dar","fue","han","tu","tus","te","le","lo","les","nos","mi","mis",
       "aun","cual","cuales","quien","quienes","yo","ellos","ella"}


def _sin(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


if __name__ == "__main__":
    UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
    tot = 0
    for m in UI + ["app"]:
        rel = "app.py" if m == "app" else f"core/{m}.py"
        sos = []
        for ln, s in sorted(set(frases(RAIZ / rel))):
            pals = set(re.findall(r"[a-záéíóúñü]+", _sin(s)))
            if re.search(r"[áéíóúñ¿¡]", s) or len(pals & PAL) >= 2:
                sos.append((ln, s))
        if sos:
            print(f"\n=== {m}  ({len(sos)}) ===")
            for ln, s in sos:
                print(f"  {ln:5}  {s[:96]!r}")
            tot += len(sos)
    print(f"\nTOTAL frases que parecen españolas: {tot}")
