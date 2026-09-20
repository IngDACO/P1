# -*- coding: utf-8 -*-
"""Cabeceras de tabla que son CLAVE de dict: ¿cuáles se pueden traducir solas?

Una clave de dict y un texto se ven IGUAL en el AST (trampa nº28), así que aquí no
se decide por idioma: se mide el RIESGO de cada una.

  · si la clave se LEE de vuelta (`fila["Situación"]`, `df["Horas"]`, `column_config`,
    `disabled=[...]`) hay que traducir TODAS sus apariciones a la vez, o la lectura
    se queda buscando una columna que ya no existe — sin dar ningún error;
  · si además se PERSISTE (DatosJSON, LineasJSON, una columna de la hoja) es DATO y
    no se toca sin migrar el histórico.
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

from barre_cortas import _sin                                      # noqa: E402
from barre_fstr_mixto import ES                                    # noqa: E402


def _es_esp(s):
    return bool(set(re.findall(r"[a-záéíóúñü]+", _sin(s))) & ES) or \
        bool(re.search(r"[áéíóúñü]", s.lower()))


def claves_dict(ruta):
    """Claves de dict-literal que parecen texto de cabecera (no snake_case)."""
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for n in ast.walk(tr):
        if not isinstance(n, ast.Dict):
            continue
        for k in n.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                s = k.value
                if not s or "_" in s or s.islower() and " " not in s:
                    continue          # snake_case / clave interna → no es cabecera
                if _es_esp(s):
                    out.append((n.lineno, s))
    return out


REPO = sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"])
SRC = {f: f.read_text(encoding="utf-8") for f in REPO}

# ¿dónde se guarda algo que pueda llevar estas claves dentro?
PERSISTEN = ("DatosJSON", "LineasJSON", "ParamsJSON", "MatrizJSON", "InterpJSON",
             "PlanoJSON", "GananciaHoraJSON", "DatosJSON")

todo = {}
for f in REPO:
    for ln, s in claves_dict(f):
        todo.setdefault(s, []).append(f"{f.name}:{ln}")

print(f"{len(todo)} claves candidatas\n")
for s in sorted(todo):
    # ¿se LEE de vuelta en algún sitio? (`[...]` con esa cadena, fuera de su creación)
    lecturas = []
    for f, src in SRC.items():
        for pat in (f'["{s}"]', f"['{s}']", f'get("{s}")', f"get('{s}')"):
            if pat in src:
                lecturas.append(f.name)
                break
    modulos = sorted({x.split(":")[0] for x in todo[s]})
    riesgo = ("PERSISTE" if any(p in "".join(SRC[f] for f in REPO
                                             if f.name in modulos)
                                for p in PERSISTEN) and lecturas
              else ("se LEE" if lecturas else "solo se pinta"))
    print(f"  {riesgo:14} {s!r:34} en {modulos}"
          + (f"  · leída en {sorted(set(lecturas))}" if lecturas else ""))
