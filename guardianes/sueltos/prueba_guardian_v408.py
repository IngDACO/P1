"""¿El guardián de v408 caza el código de ANTES? Si solo aprueba lo que ya funciona,
no demuestra nada (regla v322/v306)."""
import re, shutil, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
G = Path(__file__).with_name("verif_v408.py")

CASOS = {
  "cartera: contexto delante de las señales (el orden de v407)": (
     "core/projects_ui.py",
     lambda s: s.replace('"Situación": _sit,\n            "Alertas": str(_al) if _al else "",',
                         '', 1).replace('"Ppto": _ppto,\n        })',
                         '"Ppto": _ppto,\n            "Situación": _sit,\n'
                         '            "Alertas": str(_al) if _al else "",\n        })', 1)),
  "cartera: sin pinned en ID": (
     "core/projects_ui.py",
     lambda s: s.replace('"ID", width=76, pinned=True', '"ID", width=76', 1)),
  "pre-start: el aviso vuelve a colgar de `_ya_hoy`": (
     "core/prestart_ui.py",
     lambda s: s.replace("        if _pf:\n            st.warning(\":material/warning: **Esta obra ya tiene el Pre-Start de hoy.** \"\n                       \"Si solo faltas tú por constar, fírmalo arriba en vez de crear otro.\")",
                         "        if True:\n            st.warning(\":material/warning: **Esta obra ya tiene el Pre-Start de hoy.** \"\n                       \"Si solo faltas tú por constar, fírmalo arriba en vez de crear otro.\")", 1)),
}

for nombre, (rel, romper) in CASOS.items():
    f = RAIZ / rel
    bak = f.read_text(encoding="utf-8")
    nuevo = romper(bak)
    if nuevo == bak:
        print(f"  ??  {nombre}: el parche NO cambió nada -> el caso no se probó")
        continue
    f.write_text(nuevo, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(G)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(RAIZ))
        caza = r.returncode != 0
        print(f"  {'OK  ' if caza else 'FALLO'}  lo caza: {nombre}")
    finally:
        f.write_text(bak, encoding="utf-8")

r = subprocess.run([sys.executable, str(G)], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", cwd=str(RAIZ))
print(f"\n  restaurado y en verde: {r.returncode == 0}")
