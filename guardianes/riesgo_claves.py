# -*- coding: utf-8 -*-
"""¿Qué cabecera de tabla se puede traducir SOLA, y cuál no?

Una clave de dict y una etiqueta se ven IGUAL en el AST, así que la decisión no se
toma por idioma sino midiendo qué hace cada cadena en el repo. Tres motivos para NO
tocarla, y cada uno falla EN SILENCIO si se ignora:

  IDENTIFICADOR  la cadena es opción de un widget o se compara con `==`/`in`
                 → traducirla deja la rama MUERTA (el fallo de v441 en rieles)
  SE LEE         se indexa por ella (`fila["Horas"]`, `.get("Estado")`)
                 → traducir solo la escritura deja la lectura buscando una columna
                   que ya no existe
  VALOR i18n     está en `i18n.VALORES` → es el DATO en español de la hoja, y el
                 mapa lo traduce solo al MOSTRARLO

⚠️ El clasificador anterior daba «solo se pinta» a `📊 Estado` y `🚨 Avisos`, que son
IDs de sub-pestaña comparados por `sub ==` (v232). Un clasificador flojo es peor que
ninguno: invita a traducir justo lo que no se puede.
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
REPO = sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"])
ARB = {}
for f in REPO:
    try:
        ARB[f] = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        pass

# ── 1 · cadenas que son IDENTIFICADOR ────────────────────────────────────────
ident = set()
for f, tr in ARB.items():
    for n in ast.walk(tr):
        # opciones de un widget de selección
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in WIDGETS:
            cand = list(n.args[1:2]) + [k.value for k in n.keywords
                                        if k.arg in ("options",)]
            for a in cand:
                if isinstance(a, (ast.List, ast.Tuple)):
                    for e in a.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            ident.add(e.value)
                        # sub-pestañas = (ID, display): manda el ID
                        if isinstance(e, ast.Tuple) and e.elts \
                           and isinstance(e.elts[0], ast.Constant):
                            ident.add(e.elts[0].value)
        # comparada con == / in
        if isinstance(n, ast.Compare):
            for x in [n.left] + list(n.comparators):
                if isinstance(x, ast.Constant) and isinstance(x.value, str):
                    ident.add(x.value)
                if isinstance(x, (ast.List, ast.Tuple, ast.Set)):
                    for e in x.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            ident.add(e.value)

# ── 1b · columnas de un `st.data_editor` ─────────────────────────────────────
# ⚠️ Son DATO por dos motivos a la vez: el código LEE la tabla editada por esos
# nombres, y en las herramientas el `_snapshot` de v148 las guarda en `DatosJSON`
# (en la hoja real, `CAL-0002` ya tiene una). La primera versión de este
# clasificador daba `'Riel'` por «traducible» porque `["Riel"]` dentro de una lista
# no es un `Subscript` — un falso «se puede» es peor que no clasificar.
editor = set()
for f, tr in ARB.items():
    for n in ast.walk(tr):
        # `disabled=[...]` de un data_editor
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "data_editor":
            for k in n.keywords:
                if k.arg == "disabled" and isinstance(k.value, (ast.List, ast.Tuple)):
                    for e in k.value.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            editor.add(e.value)
        # listas de columnas esperadas (`cols_expected = ["Riel"] + ...`)
        if isinstance(n, ast.Assign) and any(
                isinstance(t_, ast.Name) and "col" in t_.id.lower() for t_ in n.targets):
            for e in ast.walk(n.value):
                if isinstance(e, ast.Constant) and isinstance(e.value, str) \
                   and e.value and not e.value.startswith(("%", "{")):
                    editor.add(e.value)

# ── 2 · cadenas que se LEEN por índice ───────────────────────────────────────
leidas = {}
for f, tr in ARB.items():
    for n in ast.walk(tr):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
           and isinstance(n.slice.value, str):
            leidas.setdefault(n.slice.value, set()).add(f.name)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "get" \
           and n.args and isinstance(n.args[0], ast.Constant) \
           and isinstance(n.args[0].value, str):
            leidas.setdefault(n.args[0].value, set()).add(f.name)

# ── 3 · valores que el mapa de i18n ya traduce al mostrar ────────────────────
from core import i18n                                              # noqa: E402
valores = set(i18n.VALORES)


def _es_esp(s):
    return bool(set(re.findall(r"[a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc]+",
                               _sin(s))) & ES) \
        or bool(re.search(r"[\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc]", s.lower()))


# ── 4 · las claves de dict que parecen cabecera ──────────────────────────────
cab = {}
for f, tr in ARB.items():
    for n in ast.walk(tr):
        if not isinstance(n, ast.Dict):
            continue
        for k in n.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                s = k.value
                if not s or "_" in s or (s.islower() and " " not in s):
                    continue
                if _es_esp(s):
                    cab.setdefault(s, set()).add(f.name)

SEG = {"IDENTIFICADOR": [], "COLUMNA DE EDITOR": [], "SE LEE": [],
       "VALOR i18n": [], "TRADUCIBLE": []}
for s, mods in sorted(cab.items()):
    if s in ident:
        SEG["IDENTIFICADOR"].append((s, mods))
    elif s in editor:
        SEG["COLUMNA DE EDITOR"].append((s, mods))
    elif s in valores:
        SEG["VALOR i18n"].append((s, mods))
    elif s in leidas:
        SEG["SE LEE"].append((s, mods, leidas[s]))
    else:
        SEG["TRADUCIBLE"].append((s, mods))

for k in ("IDENTIFICADOR", "COLUMNA DE EDITOR", "VALOR i18n", "SE LEE", "TRADUCIBLE"):
    print(f"\n{'=' * 70}\n{k}  ({len(SEG[k])})\n{'=' * 70}")
    for row in SEG[k]:
        s, mods = row[0], row[1]
        extra = f"  · leída en {sorted(row[2])}" if len(row) > 2 else ""
        print(f"  {s!r:34} {sorted(mods)}{extra}")

print(f"\n{sum(len(v) for v in SEG.values())} claves candidatas · "
      f"{len(SEG['TRADUCIBLE'])} traducibles solas")
