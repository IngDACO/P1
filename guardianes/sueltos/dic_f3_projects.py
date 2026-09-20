"""F3 · projects_ui — une los cuatro bloques del diccionario en uno solo.

Se parte en cuatro ficheros porque son 479 literales y revisarlos de golpe es como se
cuelan los errores; se aplica de una sola vez porque `aplicar.py` recorre el fichero
entero por posición y hacerlo cuatro veces movería los offsets entre pasadas.

⚠️ Si dos bloques tradujeran la MISMA cadena de forma distinta, uno pisaría al otro sin
avisar. Se comprueba antes de unir.
"""
import importlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TRAD = {}
_conflictos = []
for _m in ("dic_f3j", "dic_f3k", "dic_f3l", "dic_f3m"):
    _d = importlib.import_module(_m).TRAD
    for _k, _v in _d.items():
        if _k in TRAD and TRAD[_k] != _v:
            _conflictos.append(f"{_k[:44]!r}: {TRAD[_k][:30]!r} vs {_v[:30]!r}")
        TRAD[_k] = _v

if _conflictos:
    print(f"⚠️ {len(_conflictos)} cadenas traducidas de DOS formas distintas:")
    for _c in _conflictos:
        print("   ", _c)
    raise SystemExit(1)

if __name__ == "__main__":
    print(f"{len(TRAD)} entradas, sin conflictos")
