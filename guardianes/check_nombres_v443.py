# -*- coding: utf-8 -*-
"""¿Uso `t`/`d`/`_etq` en algún módulo que NO lo importe?

⚠️ Es el fallo de v423 (`theme` usado sin importar): compilar lo pasa, importar el
módulo lo pasa —el cuerpo de la función no se ejecuta— y solo revienta al abrir la
pantalla. Y ⚠️ hay que mirar el ÁMBITO DE MÓDULO, sin descender a los `def`: ahí es
donde el chequeo se autoengaña (v342/v366).
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
MOTOR = {"t", "d", "_d", "_etq"}


def importados(tr):
    """Nombres del motor DISPONIBLES: import de módulo, def propio o import local.

    ⚠️ Las tres formas cuentan, o el chequeo grita en falso: `roster_ui` define su
    propio `_etq(staff, grupo)` (v413) y hace `from datetime import date as _d`
    dentro de una función. Acusar a esos dos me habría llevado a «arreglar» código
    sano — la regla v385 (mirar el código acusado) aplicada al propio chequeo.
    """
    out = set()
    for n in tr.body:                      # ⚠️ tr.body, NO ast.walk: el import de
        if isinstance(n, ast.ImportFrom) \
           and (n.module or "").endswith("i18n"):   # OTRA función no vale (v342)
            for a in n.names:
                out.add(a.asname or a.name)
    # def propio a nivel de módulo, y cualquier import local con ese nombre
    for n in ast.walk(tr):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in MOTOR:
            out.add(n.name)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                if (a.asname or a.name) in MOTOR:
                    out.add(a.asname or a.name)
    return out


def usados(tr):
    """Nombres del motor LLAMADOS en el módulo."""
    out = {}
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in MOTOR:
            out.setdefault(n.func.id, n.lineno)
    return out


malos = 0
mirados = 0
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    imp, uso = importados(tr), usados(tr)
    if not uso:
        continue
    mirados += 1
    faltan = {k: v for k, v in uso.items() if k not in imp}
    if faltan:
        malos += 1
        for k, ln in sorted(faltan.items()):
            print(f"  FALTA  {f.name}:{ln}  usa `{k}()` y NO lo importa")

print(f"\n{mirados} módulos usan el motor · {malos} con importes que faltan")
if not mirados:
    print("⚠️ el chequeo no miró nada: eso NO es un aprobado")
sys.exit(1 if (malos or not mirados) else 0)
