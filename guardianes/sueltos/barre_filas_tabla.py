# -*- coding: utf-8 -*-
"""SEXTA red: las FILAS de una tabla construidas como dict literal.

El hueco que la destapó (v450): en `_cumplimiento_equipo` la tabla se arma como
`fila = {"Usuario": u, "Compliant": ...}` y sus valores salen de
`_ico = {"vigente": "vigente", "por_vencer": "por vencer", ...}`.

Ninguna de las cinco redes lo ve:
  · posición  → el argumento de `st.dataframe` es un `pd.DataFrame(filas)`, no cadenas;
  · frases    → son de 1-2 palabras;
  · cortas    → mira tuplas y f-strings, no claves de dict;
  · f-strings → no hay f-string;
  · una palabra → ⚠️ las EXCLUYE a propósito, porque `"Usuario"` se lee con `.get()`
    y `"vigente"` se compara en `credentials` → caen en LEIDAS / IDENT.

⚠️ Y ese es justo el punto: la MISMA cadena es dato en un módulo y etiqueta en otro.
Una exclusión global es cómoda y miente (lección v444). Esta red no excluye por
riesgo: recoge todo dict literal que acabe en una tabla y lo deja para mirar a mano.
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

UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
_ES = {_sin(x) for x in ES}


def _espanol(s: str) -> bool:
    pal = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]+", s)
    return any(_sin(p) in _ES for p in pal)


def _vars_de_tabla(tr):
    """Nombres que acaban dentro de un `pd.DataFrame(...)` o de un `st.table/dataframe`."""
    out = set()
    for n in ast.walk(tr):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        es_df = (getattr(f, "attr", "") in {"DataFrame", "dataframe", "table", "data_editor"})
        if not es_df:
            continue
        for a in n.args:
            for x in ast.walk(a):
                if isinstance(x, ast.Name):
                    out.add(x.id)
    return out


def filas_tabla(ruta):
    """Cadenas españolas dentro de dicts literales que alimentan una tabla."""
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return []
    destinos = _vars_de_tabla(tr)
    if not destinos:
        return []

    # dicts que se asignan a una var, o que se .append()an a una lista de la tabla
    sospechosos = []
    for n in ast.walk(tr):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    sospechosos.append((t.id, n.value))
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "append" \
           and isinstance(getattr(n.func, "value", None), ast.Name) \
           and n.func.value.id in destinos:
            for a in n.args:
                if isinstance(a, ast.Dict):
                    sospechosos.append((n.func.value.id, a))
                if isinstance(a, ast.Name):
                    # `filas.append(fila)` → el dict de `fila` ya está recogido arriba
                    destinos.add(a.id)

    dentro_t = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d"}:
            dentro_t |= {id(x) for x in ast.walk(n)}

    out = []
    for var, dic in sospechosos:
        if var not in destinos:
            continue
        for k, v in zip(dic.keys, dic.values):
            for nodo, papel in ((k, "clave"), (v, "valor")):
                if not (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)):
                    continue
                if id(nodo) in dentro_t:
                    continue
                s = nodo.value.strip()
                if not s or len(s) > 40 or not _espanol(s):
                    continue
                out.append((nodo.lineno, papel, s))
    return sorted(set(out))


if __name__ == "__main__":
    tot = 0
    for f in UI:
        hits = filas_tabla(f)
        if hits:
            print(f"\n── {f.name} ({len(hits)})")
            for ln, papel, s in hits:
                print(f"   {ln}: {papel:6} {s!r}")
            tot += len(hits)
    print(f"\n{tot} cadenas españolas en filas de tabla")
