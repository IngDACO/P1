"""TERCERA pasada: etiquetas CORTAS sin envolver (2 palabras) que parecen españolas.

⚠️ Ni la red 1 (argumento de display) ni la red 2 (frases de 3+ palabras) las ven: viven
dentro de listas de tuplas (`_fil.append(("+ ausencias pagadas …", v))`) y son cortas.
Aquí se baja el listón a DOS palabras y se acepta un léxico español más amplio, a costa
de más falsos positivos — que se miran a mano, que para eso son pocos.
"""
import re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))
from barre_frases import frases
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

# palabras que SOLO existen en español (no son siglas ni inglés)
ES = {"de","del","la","el","los","las","por","con","sin","en","y","al","que","obra",
      "obras","mano","costo","costos","horas","hora","dia","día","días","semana",
      "proyecto","proyectos","usuario","usuarios","fecha","estado","nombre","tarifa",
      "ausencias","ausencia","pagadas","pagado","estructura","jornada","cliente",
      "elevador","elevadores","riel","rieles","corte","cortes","plano","planos",
      "presupuesto","ganancia","margen","nomina","nómina","nominas","nóminas",
      "asignado","asignados","trabajo","trabajos","personal","credencial","credenciales"}


def _sin(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


if __name__ == "__main__":
    UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
    tot = 0
    for m in UI + ["app"]:
        rel = "app.py" if m == "app" else f"core/{m}.py"
        sos = []
        for ln, s in sorted(set(frases(RAIZ / rel, minimo=2))):
            if s.lstrip().startswith("<style>") or "/*" in s:
                continue
            pals = set(re.findall(r"[a-záéíóúñü]+", _sin(s)))
            if pals & ES:
                sos.append((ln, s))
        if sos:
            print(f"\n=== {m} ({len(sos)}) ===")
            for ln, s in sos:
                print(f"  {ln:5} {s[:88]!r}")
            tot += len(sos)
    print(f"\nTOTAL: {tot}")
