"""La TERCERA bolsa: claves de dict que son CABECERA DE TABLA visible.

Cuando una tabla se arma como lista de dicts (`st.dataframe(filas)` o el `tool_pdf`),
la CLAVE del dict es lo que se pinta como encabezado — salvo que un `column_config` le
ponga etiqueta. Ni el invariante de posición (no es argumento de display) ni el barrido
de frases (son de 1-3 palabras) las ven.

⚠️ Y no todas se pueden traducir: si otro módulo LEE por esa clave, cambiarla rompe la
lectura en silencio. Se marca cuál se lee fuera.
"""
import ast, re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

PAL = {"de","del","la","el","los","las","por","con","sin","en","y","a","al","que","vs"}


def _es(s):
    n = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn").lower()
    return bool(re.search(r"[áéíóúñ]", s)) or bool(set(re.findall(r"[a-z]+", n)) & PAL)


UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
enc = {}
for m in UI:
    tr = ast.parse((RAIZ / f"core/{m}.py").read_text(encoding="utf-8"))
    for n in ast.walk(tr):
        if not isinstance(n, ast.Dict):
            continue
        for k in n.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                s = k.value.strip()
                if s and any(c.isalpha() for c in s) and _es(s):
                    enc.setdefault(s, []).append(f"{m}:{k.lineno}")

# ¿alguien LEE por esa clave fuera de su módulo?
leidos = {}
for f in RAIZ.rglob("*.py"):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(tr):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
           and n.slice.value in enc:
            leidos.setdefault(n.slice.value, set()).add(f.name)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and n.func.attr == "get" and n.args and isinstance(n.args[0], ast.Constant) \
           and n.args[0].value in enc:
            leidos.setdefault(n.args[0].value, set()).add(f.name)

print(f"{len(enc)} claves de dict en español dentro de los *_ui\n")
for s in sorted(enc):
    ls = sorted(leidos.get(s, []))
    marca = f"   ⚠️ se LEE en {ls}" if ls else ""
    print(f"  {s[:46]:48} {enc[s][0]:26}{marca}")
