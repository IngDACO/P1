"""Guardián v333 — la escala tipográfica se respeta.

Había 31 tamaños distintos para 102 usos. Que ahora sean 9 no sirve de nada si el
siguiente que alguien escriba vuelve a ser 12.48. Este guardián falla si aparece
un `font-size:` fuera de la escala.

⚠️ NO mira los `font-size="7.5"` de los SVG: son atributos sin unidad que `svglib`
lee para generar el PDF, con su propia escala de dibujo técnico. Meterlos en la
escala de la interfaz rompería las cotas de los planos.
"""
import importlib
import pathlib
import py_compile
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(BASE))
OK = True

from core import theme as T                                    # noqa: E402

print("== 1) compila e importa ==")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)
fallos = []
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        fallos.append((p.stem, repr(e)[:90]))
print(f"   {len(mods) - len(fallos)}/{len(mods)} módulos + app.py")
for f in fallos:
    print("    FALLO", f)
OK &= not fallos

print(f"\n== 2) todo `font-size:` está en la escala {T.ESCALA_FS} ==")
fuera = []
for p in sorted(BASE.rglob("*.py")):
    if "scratchpad" in str(p):
        continue
    for m in re.finditer(r"font-size:\s*([0-9.]+)(rem|px|em)", p.read_text(encoding="utf-8")):
        v, u = float(m.group(1)), m.group(2)
        px = v * 16 if u in ("rem", "em") else v
        if px not in T.ESCALA_FS:
            fuera.append(f"{p.name}: {m.group(0)}  ({px}px)")
print(f"   declaraciones fuera de la escala: {len(fuera)}")
for f in fuera[:10]:
    print("    ", f)
OK &= not fuera

print("\n== 3) el guardián CAZA una regresión (no solo aprueba lo sano) ==")
ROTO = 'st.markdown("<div style=\'font-size:12.48px\'>x</div>")'
m = re.search(r"font-size:\s*([0-9.]+)(rem|px|em)", ROTO)
caza = m and float(m.group(1)) not in T.ESCALA_FS
print(f"   'font-size:12.48px' se detecta como fuera de escala: {bool(caza)}")
OK &= bool(caza)

print("\n== 4) los SVG conservan su propia escala (no se tocan) ==")
n_svg = sum(len(re.findall(r'font-size="[0-9.]+"', p.read_text(encoding="utf-8")))
            for p in (BASE / "core").glob("*.py"))
print(f"   atributos font-size= en SVG: {n_svg}")
OK &= (n_svg > 100)

print("\n== 5) los diagramas siguen generándose ==")
from core import schedule                                      # noqa: E402
import datetime                                                # noqa: E402
svg = schedule.schedule_svg(schedule.build_schedule(6, datetime.date(2026, 8, 1), {}))
print(f"   schedule_svg: {len(svg)} chars · <text>={svg.count('<text')} · "
      f"sin defs/marker: {'<defs' not in svg and '<marker' not in svg}")
OK &= (len(svg) > 2000 and "<defs" not in svg)

print("\n== 6) la paleta de texto sigue pasando WCAG ==")


def _lum(h):
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def _ratio(a, b):
    l1, l2 = _lum(a), _lum(b)
    return round((max(l1, l2) + .05) / (min(l1, l2) + .05), 2)


for nom, c, bg in [("GRIS_TXT", T.GRIS_TXT, "#ffffff"),
                   ("GRIS_SUAVE", T.GRIS_SUAVE, "#f4f6f9"),
                   ("AMBAR_TXT", T.AMBAR_TXT, "#fff4e0"),
                   ("ROJO", T.ROJO, "#fdecec")]:
    r = _ratio(c, bg)
    print(f"   {nom:<11} {c} → {r}:1  {'ok' if r >= 4.5 else 'FALLA'}")
    OK &= (r >= 4.5)

print("\n" + ("TODO OK" if OK else "HAY FALLOS"))
sys.exit(0 if OK else 1)
