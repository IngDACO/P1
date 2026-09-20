"""PRE-VUELO: renombra las variables `t` que taparían el motor de idioma.

⚠️ Se hace ANTES de traducir. Si `t` ya es una variable en una función y la traducción
le mete `t("…")`, Python marca el nombre local en el ÁMBITO ENTERO y la función revienta
con UnboundLocalError (o `'str'/'dict' object is not callable` si es un parámetro o la
variable de un `for`). No lo ven `compileall` ni importar el módulo.
Pasó en v437, v439 y `quotes_ui` — las tres veces por comprobarlo DESPUÉS.

Nada de esto cambia comportamiento: son renombrados de variables locales.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
    "core/auth_ui.py": [
        # `t` = el tipo de credencial resuelto («Otro» → texto libre)
        ('                t = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo',
         '                _tp = tipo_otro.strip() if (_es_otro and tipo_otro.strip()) else tipo'),
        ('did = C.upload_file(usuario, t, arch.name, arch.getvalue(),',
         'did = C.upload_file(usuario, _tp, arch.name, arch.getvalue(),'),
    ],
    "core/home_ui.py": [
        # `_slug`: `t` es la cadena normalizada
        ('    t = unicodedata.normalize("NFD", str(sub_id or "").lower())\n'
         '    t = "".join(c for c in t if unicodedata.category(c) not in ("Mn", "So", "Cn"))\n'
         '    return "-".join("".join(ch if ch.isalnum() else " " for ch in t).split())',
         '    _s = unicodedata.normalize("NFD", str(sub_id or "").lower())\n'
         '    _s = "".join(c for c in _s if unicodedata.category(c) not in ("Mn", "So", "Cn"))\n'
         '    return "-".join("".join(ch if ch.isalnum() else " " for ch in _s).split())'),
        # `_norm_busq`: idem
        ('    t = unicodedata.normalize("NFD", str(s or "").strip().lower())\n'
         '    return "".join(c for c in t if unicodedata.category(c) != "Mn")',
         '    _s = unicodedata.normalize("NFD", str(s or "").strip().lower())\n'
         '    return "".join(c for c in _s if unicodedata.category(c) != "Mn")'),
        # `buscar`: `t` es cada TRABAJO del catálogo
        ('        for t in R.list_trabajos(grupo, incluir_inactivos=True):\n'
         '            tid = str(t.get("ID", ""))\n'
         '            r = _rank(tid, t.get("Nombre"), t.get("Numero"))',
         '        for _trb in R.list_trabajos(grupo, incluir_inactivos=True):\n'
         '            tid = str(_trb.get("ID", ""))\n'
         '            r = _rank(tid, _trb.get("Nombre"), _trb.get("Numero"))'),
    ],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, n in reps:
        if s.count(n) >= 1 and s.count(o) == 0:
            continue
        if s.count(o) < 1:
            fallos.append(f"{rel}: {o.splitlines()[0][:72]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", f)
    sys.exit(1)

for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o):
            s = s.replace(o, nv, 1)
            n += 1
    ast.parse(s)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} renombrados")
print("OK")
