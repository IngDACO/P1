# -*- coding: utf-8 -*-
"""QUINTA red: cadenas de UNA sola palabra española, en cualquier posición.

El hueco: `("cred", ":material/badge:", "Credenciales", …)` y
`("alarmas", …, "Alarmas", …)` son etiquetas de display dentro de una TUPLA, de una
sola palabra. No las ve ninguna de las cuatro redes anteriores:

  · la de posición (v440) mira el argumento de `st.*` — aquí el argumento es la tupla;
  · la de frases (v441) pide 3+ palabras;
  · la de cortas (v442) pide 2;
  · la de f-strings (v443) mira f-strings, y estas son cadenas normales.

⚠️ Y no se puede traducir a ciegas: la MISMA cadena de una palabra puede ser un ID de
sub-pestaña, una columna del libro o un valor de `i18n.VALORES`. Se reutiliza el
clasificador de riesgo, que mide qué hace cada cadena en vez de mirar su idioma.
"""
import ast
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

from barre_cortas import _sin                                      # noqa: E402
from barre_fstr_mixto import ES                                    # noqa: E402

WIDGETS = {"radio", "selectbox", "multiselect", "select_slider",
           "segmented_control", "pills"}
UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
REPO = sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"])
ARB = {}
for f in REPO:
    try:
        ARB[f] = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        pass


def _riesgos():
    """Cadenas que NO se pueden traducir solas, y por qué."""
    ident, editor, leidas = set(), set(), set()
    for f, tr in ARB.items():
        for n in ast.walk(tr):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in WIDGETS:
                for a in list(n.args[1:2]) + [k.value for k in n.keywords
                                              if k.arg == "options"]:
                    if isinstance(a, (ast.List, ast.Tuple)):
                        for e in a.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                ident.add(e.value)
                            if isinstance(e, ast.Tuple) and e.elts and \
                               isinstance(e.elts[0], ast.Constant):
                                ident.add(e.elts[0].value)
            if isinstance(n, ast.Compare):
                for x in [n.left] + list(n.comparators):
                    if isinstance(x, ast.Constant) and isinstance(x.value, str):
                        ident.add(x.value)
                    if isinstance(x, (ast.List, ast.Tuple, ast.Set)):
                        for e in x.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                ident.add(e.value)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "data_editor":
                for k in n.keywords:
                    if k.arg == "disabled" and isinstance(k.value, (ast.List, ast.Tuple)):
                        for e in k.value.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                editor.add(e.value)
            if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
               and isinstance(n.slice.value, str):
                leidas.add(n.slice.value)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "get" \
               and n.args and isinstance(n.args[0], ast.Constant) \
               and isinstance(n.args[0].value, str):
                leidas.add(n.args[0].value)
    return ident, editor, leidas


IDENT, EDITOR, LEIDAS = _riesgos()
try:
    from core import i18n
    VALORES = set(i18n.VALORES)
except Exception:
    VALORES = set()

# ⚠️ Nombres de hoja y de columna del libro: son DATO aunque parezcan etiquetas.
HOJAS = {"Proyectos", "Actividades", "Agrupaciones", "Documentos", "Alarmas",
         "Credenciales", "Gastos", "Ordenes", "Auditoria", "Catalogo",
         "Cotizaciones", "Clientes", "Manuales", "Rieles", "Grupos", "Login",
         "Trabajos", "Roster", "PreStarts", "Calculos", "Ausencias", "Facturas",
         "Nominas", "Inventario"}


def una_palabra(ruta):
    """Cadenas de UNA palabra española que se pueden traducir SOLAS."""
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return []
    dentro_t = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d"}:
            dentro_t |= {id(x) for x in ast.walk(n)}
    out = []
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
            continue
        if id(n) in dentro_t:
            continue
        s = n.value.strip()
        pal = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]{3,}", s)
        if len(pal) != 1 or len(s) > 26:
            continue
        if s in IDENT or s in EDITOR or s in LEIDAS or s in VALORES or s in HOJAS:
            continue
        if "_" in s or s.startswith(("%", ":", "<", "#")) or "/" in s:
            continue
        if _sin(pal[0]) not in {_sin(x) for x in ES}:
            continue
        out.append((n.lineno, s))
    return out


if __name__ == "__main__":
    tot = 0
    for f in UI:
        hits = sorted(set(una_palabra(f)))
        if hits:
            print(f"\n── {f.name} ({len(hits)})")
            for ln, s in hits:
                print(f"   {ln}: {s!r}")
            tot += len(hits)
    print(f"\n{tot} cadenas de una palabra traducibles solas")
