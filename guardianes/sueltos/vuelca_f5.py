import re, sys, unicodedata, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))
from barre_frases import frases
from barre_frases_es import PAL, _sin
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
todo = []
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    for ln, s in sorted(set(frases(RAIZ / rel))):
        pals = set(re.findall(r"[a-záéíóúñü]+", _sin(s)))
        if re.search(r"[áéíóúñ¿¡]", s) or len(pals & PAL) >= 2:
            # ⚠️ Un bloque <style> es CÓDIGO CSS con comentarios míos, no pantalla.
            css = s.lstrip().startswith("<style>") or "/*" in s
            todo.append({"mod": m, "lin": ln, "txt": s, "css": css})
Path("f5_pendientes.json").write_text(json.dumps(todo, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
print(f"{len(todo)} totales · {sum(1 for x in todo if x['css'])} son CSS (se saltan) · "
      f"{sum(1 for x in todo if not x['css'])} a traducir")
