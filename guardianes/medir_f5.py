# -*- coding: utf-8 -*-
"""¿Cuánto es F5 de verdad, y qué parte de ello se VE?

En los módulos internos no vale la red de POSICIÓN (v440): aquí no hay llamadas a
`st.*`. Lo que decide es el DESTINO de la cadena:

  RETORNO   la función la devuelve → la UI la pinta con `flash`/`st.error`  → se traduce
  LOG       `logger.warning(...)` → nunca se ve                            → NO se toca
  OTRO      el resto: claves internas, columnas del libro, docstrings…     → hay que mirar

⚠️ `logger.warning` y `st.warning` comparten NOMBRE de atributo: filtrar por atributo
metió 92 mensajes de log en la primera pasada de v439. Se filtra por RECEPTOR.
⚠️ Y el barrido va bajo `__main__`: si corre al IMPORTAR, ensucia la salida de
cualquier guardián que reutilice estos helpers (pasó con `barre_frases` en v441).
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

from barre_cortas import _sin                                      # noqa: E402
from barre_fstr_mixto import ES                                    # noqa: E402

INTERNOS = [f for f in sorted((RAIZ / "core").glob("*.py"))
            if not f.name.endswith("_ui.py")]


def esp(s):
    return bool(set(re.findall(r"[a-záéíóúñü]+", _sin(s))) & ES) \
        or bool(re.search(r"[áéíóúñü]", s.lower()))


def texto(n):
    """El texto literal de una cadena o de una f-string."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.JoinedStr):
        return " ".join(p.value for p in n.values
                        if isinstance(p, ast.Constant) and isinstance(p.value, str))
    return ""


def clasifica(ruta):
    """{RETORNO|LOG|OTRO: [(linea, texto)]} de un módulo."""
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return {"RETORNO": [], "LOG": [], "OTRO": []}
    en_log, en_ret = set(), set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and isinstance(n.func.value, ast.Name) \
           and n.func.value.id in ("logger", "log", "_log", "logging"):
            en_log |= {id(x) for x in ast.walk(n)}
        if isinstance(n, ast.Return) and n.value is not None:
            en_ret |= {id(x) for x in ast.walk(n.value)}
    # docstrings: primer nodo del cuerpo de módulo/función/clase
    docs = set()
    for n in ast.walk(tr):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)) and n.body:
            h = n.body[0]
            if isinstance(h, ast.Expr) and isinstance(h.value, ast.Constant) \
               and isinstance(h.value.value, str):
                docs.add(id(h.value))
    out = {"RETORNO": [], "LOG": [], "OTRO": []}
    for n in ast.walk(tr):
        if not isinstance(n, (ast.Constant, ast.JoinedStr)) or id(n) in docs:
            continue
        s = texto(n).strip()
        if not s or len(s) < 4 or not esp(s):
            continue
        if s.lstrip().startswith(("<", "#", "%")) or "font-family" in s:
            continue
        k = "LOG" if id(n) in en_log else ("RETORNO" if id(n) in en_ret else "OTRO")
        out[k].append((n.lineno, s))
    return out


if __name__ == "__main__":
    solo = sys.argv[1] if len(sys.argv) > 1 else None
    tot = {"RETORNO": 0, "LOG": 0, "OTRO": 0}
    for f in INTERNOS:
        c = clasifica(f)
        if solo and f.name != solo:
            for k in tot:
                tot[k] += len(c[k])
            continue
        if solo:
            for k in ("RETORNO", "OTRO"):
                print(f"\n── {k} ({len(c[k])})")
                for ln, s in sorted(set(c[k])):
                    print(f"   {ln}: {s[:78]!r}")
        elif any(c.values()):
            print(f"  {f.name:22} RETORNO {len(c['RETORNO']):3}  ·  "
                  f"LOG {len(c['LOG']):3}  ·  OTRO {len(c['OTRO']):3}")
        for k in tot:
            tot[k] += len(c[k])
    if not solo:
        print(f"\n  {'TOTAL':22} RETORNO {tot['RETORNO']:3}  ·  LOG {tot['LOG']:3}"
              f"  ·  OTRO {tot['OTRO']:3}")
