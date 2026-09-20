"""Los trozos de f-string que el invariante NO puede exigir envueltos: hay que MIRARLOS."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
from i18n_tool import piezas

UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
n = 0
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    fs = [p for p in piezas(RAIZ / rel) if p["fstr"]]
    if fs:
        print(f"\n=== {m}  ({len(fs)}) ===")
        for p in fs:
            print(f"  {p['lin']:5}  {p['txt'][:95]!r}")
        n += len(fs)
print(f"\nTOTAL trozos de f-string: {n}")
