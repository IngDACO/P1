# -*- coding: utf-8 -*-
"""SEXTA red: qué CABECERA se pinta de verdad en cada tabla.

Streamlit pinta la CLAVE del dict salvo que su `column_config` le dé una etiqueta.
Una cabecera sale en español si su clave lo es y además:
  · no tiene entrada en `column_config`, o
  · la tiene pero SIN etiqueta (`NumberColumn(min_value=…)` → cae a la clave), o
  · la etiqueta es un literal español.

⚠️ CUATRO correcciones, cada una destapada por un recuento que no cuadraba. Las
apunto porque las cuatro son formas de que este chequeo apruebe o acuse en falso:
  1. El mapa de dicts iba por NOMBRE de variable en todo el MÓDULO, así que el
     `rows` de una función heredaba las cabeceras del `rows` de otra.
  2. Contaba como «valor de celda» el argumento de `p.get("Nombre")`, que es una
     LECTURA de la hoja, no un texto que se pinte.
  3. Bastaba con estar en `column_config` para darla por traducida — y una entrada
     SIN etiqueta sigue pintando la clave.
  4. No veía el dict INLINE (`pd.DataFrame([{…} for r in xs])`, que es la mitad de
     las tablas) y en cambio atribuía a esa llamada cualquier dict de la función
     que compartiera nombre con la variable del bucle. Ahora las claves salen del
     PRIMER argumento de la tabla, y los nombres ligados por una comprensión se
     excluyen de la búsqueda por variable.

⚠️ El filtro por idioma es un SUELO, no un total (trampa nº28): «Rol», «Grupo» o
«Costo» no llevan acento ni palabra funcional. Con `--todas` se listan todas.
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

sys.path.insert(0, str(RAIZ))
from core.tabla import CABECERAS                                   # noqa: E402

UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
_ES = {_sin(x) for x in ES}
TABLA = {"dataframe", "data_editor", "table"}
TODAS = "--todas" in sys.argv


def _esp(s):
    return any(_sin(p) in _ES for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]+", s))


def _claves(d):
    return [k.value for k in d.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)]


def _traducida(valor):
    """¿La entrada de `column_config` da una etiqueta ya traducida?

    La etiqueta es el PRIMER posicional de `st.column_config.XxxColumn(...)`.
    Sin posicionales no hay etiqueta → Streamlit cae a la clave.
    """
    if not isinstance(valor, ast.Call) or not valor.args:
        return False
    lab = valor.args[0]
    if isinstance(lab, ast.Call) and isinstance(lab.func, ast.Name) \
       and lab.func.id in {"t", "d", "_d"}:
        return True
    if isinstance(lab, ast.Constant) and isinstance(lab.value, str):
        return not _esp(lab.value)          # una etiqueta inglesa literal vale
    return True                              # expresión: no se puede afirmar que falle


def _ligados(nodo):
    """Nombres que liga una comprensión dentro de `nodo` (no son variables de fila)."""
    out = set()
    for n in ast.walk(nodo):
        if isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for g in n.generators:
                for x in ast.walk(g.target):
                    if isinstance(x, ast.Name):
                        out.add(x.id)
    return out


def analiza(ruta):
    tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    out = []
    for fn in [n for n in ast.walk(tr)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        dicts = {}
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
                for tg in n.targets:
                    if isinstance(tg, ast.Name):
                        dicts.setdefault(tg.id, []).append(n.value)
            if isinstance(n, ast.Call) \
               and getattr(n.func, "attr", "") in {"append", "update"} \
               and isinstance(getattr(n.func, "value", None), ast.Name):
                for a in n.args:
                    if isinstance(a, ast.Dict):
                        dicts.setdefault(n.func.value.id, []).append(a)
                    elif isinstance(a, ast.Name) and a.id in dicts:
                        dicts.setdefault(n.func.value.id, []).extend(dicts[a.id])

        for n in ast.walk(fn):
            if not (isinstance(n, ast.Call)
                    and getattr(n.func, "attr", "") in TABLA and n.args):
                continue
            arg = n.args[0]
            # (a) dicts escritos INLINE dentro del propio argumento
            filas = [x for x in ast.walk(arg) if isinstance(x, ast.Dict) and x.keys]
            # (b) por variable, excluyendo lo que liga una comprensión
            excl = _ligados(arg)
            for x in ast.walk(arg):
                if isinstance(x, ast.Name) and x.id not in excl:
                    filas += dicts.get(x.id, [])
            if not filas:
                continue
            cubiertas = set()
            for k in n.keywords:
                if k.arg != "column_config":
                    continue
                v = k.value
                # `tabla.cfg(None, {...})` → cubre TODO el mapa real + los extras.
                # ⚠️ El mapa se IMPORTA del módulo, no se copia aquí: un chequeo que
                # reproduce lo que audita sigue en verde con el código roto (v412).
                if isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "cfg":
                    cubiertas |= set(CABECERAS)
                    v = v.args[1] if len(v.args) > 1 else None
                if isinstance(v, ast.Dict):
                    for ck, cv in zip(v.keys, v.values):
                        if isinstance(ck, ast.Constant) and _traducida(cv):
                            cubiertas.add(ck.value)
            cab = set()
            for d in filas:
                for k in d.keys:
                    if not (isinstance(k, ast.Constant)
                            and isinstance(k.value, str)):
                        continue
                    c = k.value
                    if c not in cubiertas and (TODAS or _esp(c)):
                        cab.add((k.lineno, c))       # ⚠️ con la línea de ORIGEN:
                        # sin ella no se distingue la clave de ESTA tabla de la de
                        # un dict vecino atribuido por error (me pasó dos veces).
            if cab:
                out.append((fn.name, n.lineno, sorted(cab)))
    return out


if __name__ == "__main__":
    tot = 0
    for f in UI:
        res = analiza(f)
        if not res:
            continue
        print(f"\n── {f.name}")
        for fname, ln, cab in res:
            print(f"   {fname}()  tabla en línea {ln}")
            for kln, c in cab:
                print(f"      L{kln:<5} {c!r}")
            tot += len(cab)
    print(f"\n{tot} cabeceras que se pintan sin traducir")
