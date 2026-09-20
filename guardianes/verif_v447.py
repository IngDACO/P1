# -*- coding: utf-8 -*-
"""Guardián de v447 — F5c: los 14 módulos de backend que quedaban.

`expenses`, `roster`, `inventory`, `credentials`, `payroll`, `prestart`, `rails`,
`plan_data`, `invoices`, `manuals`, `toolruns`, `plan_store`, `tenant`, `excel_io`.

⚠️ Aquí lo más peligroso no fue traducir: fue **renombrar**. `pre_i18n` marcó 25
funciones con `t`/`d` como variable, y al renombrarlas quedaron usos colgando. El
peor, en `payroll.neto`: `elif t == "deduccion"` con `t` ya importado como la función
de idioma **no da error** — la comparación sale siempre False y **las deducciones
dejan de restarse del neto a pagar**. Un fallo de dinero, silencioso, en la función
que calcula lo que cobra cada persona. Por eso este guardián ejecuta `neto()`.

⚠️ Y el `t()` congelado al importar salió DOS veces más (`plan_data.USA`,
`toolruns.HERRAMIENTAS`): son dicts de módulo, así que sus valores van en texto BASE.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


MODS = ("expenses.py", "roster.py", "inventory.py", "credentials.py", "payroll.py",
        "prestart.py", "rails.py", "plan_data.py", "invoices.py", "manuals.py",
        "toolruns.py", "plan_store.py", "tenant.py", "excel_io.py")

# ── 1 ────────────────────────────────────────────────────────────
sec("1. La ARITMÉTICA que el renombrado pudo romper en silencio")
from core import payroll, finance, credentials, inventory           # noqa: E402
from core import manuals, prestart, roster                          # noqa: E402

# ⚠️ El caso exacto: si `_tp` volviera a llamarse `t`, la deducción no restaría.
chk("payroll.neto resta la DEDUCCIÓN y no el aporte",
    payroll.neto(1000, [{"tipo": "devengo", "monto": 100},
                        {"tipo": "deduccion", "monto": 30},
                        {"tipo": "aporte", "monto": 50}]) == 1070,
    str(payroll.neto(1000, [{"tipo": "devengo", "monto": 100},
                            {"tipo": "deduccion", "monto": 30},
                            {"tipo": "aporte", "monto": 50}])))
chk("...y solo con deducción también",
    payroll.neto(500, [{"tipo": "deduccion", "monto": 200}]) == 300)
_c = finance.conciliacion_mo("cliente1")
chk("finance.conciliacion_mo se EJECUTA y cierra la cadena",
    isinstance(_c, dict) and "cargado" in _c and "sin_explicar" in _c)
_ts, _fs = credentials.matrix("cliente1")
# ⚠️ v456: lo que este chequeo prueba es que la función SE EJECUTA tras renombrar su
# `for t` — no cuánta gente hay. Con la demo vacía `_fs` está vacío y exigir filas lo
# convertía en un rojo que no era un fallo. Se comprueba la ESTRUCTURA, y el contenido
# solo si lo hay.
chk("credentials.matrix se EJECUTA (su `for t` se renombró)",
    isinstance(_ts, list) and isinstance(_fs, list)
    and (not _fs or all(x in _fs[0] for x in _ts)),
    f"{len(_ts)} tipos × {len(_fs)} personas")
chk("manuals.search se EJECUTA (⚠️ `_tok` ya era el TOKENIZADOR del módulo)",
    isinstance(manuals.search("rail", 3), list))
chk("prestart._norm_nombre se EJECUTA",
    prestart._norm_nombre("  José  Pérez ") == "jose perez",
    prestart._norm_nombre("  José  Pérez "))
chk("inventory.ubic_str se EJECUTA",
    ":" in inventory.ubic_str({"LocationType": "proyecto",
                               "LocationRef": "PRJ-0001"}))
chk("roster.rango_label se EJECUTA", bool(roster.rango_label(roster.lunes_de())))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. No queda ningún `t` local que tape la función")
for mod in MODS:
    tr = ast.parse((RAIZ / "core" / mod).read_text(encoding="utf-8"))
    restos = sorted({x.lineno for x in ast.walk(tr)
                     if (isinstance(x, ast.Name) and x.id == "t"
                         and isinstance(x.ctx, ast.Store))
                     or (isinstance(x, ast.arg) and x.arg == "t")})
    chk(f"{mod:16} sin `t` como variable ni parámetro", not restos, str(restos))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Ningún `t()` se CONGELA al importar")
from barre_t_modulo import congelados, EXCL                        # noqa: E402
_frios = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if f.name in EXCL:
        continue
    _frios += [f"{f.name}:{ln}" for ln, _ in sorted(set(congelados(f)))]
chk("0 congeladas", not _frios, str(_frios))
# los dos dicts de módulo guardan el texto BASE, sin envolver
_pd = (RAIZ / "core/plan_data.py").read_text(encoding="utf-8")
_tr_ = (RAIZ / "core/toolruns.py").read_text(encoding="utf-8")
chk("plan_data.USA guarda el texto BASE (dict de módulo)",
    '"hkp":     "Buffer cutting",' in _pd)
chk("toolruns.HERRAMIENTAS también, y sus CLAVES no se tocan",
    '"rieles":   "Rail cutting",' in _tr_ and '"belting":  "Belting",' in _tr_)

# ── 3b ───────────────────────────────────────────────────────────
sec("3b. Todo el que usa el motor lo tiene importado")
# ⚠️ Esto vivía en un script aparte y por eso una rotura («roster deja de importar
# el motor») se ESCAPÓ del guardián: un chequeo que no está en la suite no protege
# nada. Es un `NameError` que solo se ve al abrir la pantalla (v423, v445).
MOTOR = {"t", "d", "_d", "_etq"}


def _disponibles(tr):
    out = set()
    for x in tr.body:
        if isinstance(x, ast.ImportFrom) and (x.module or "").endswith("i18n"):
            out |= {a.asname or a.name for a in x.names}
    for x in ast.walk(tr):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name in MOTOR:
            out.add(x.name)
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            out |= {(a.asname or a.name) for a in x.names
                    if (a.asname or a.name) in MOTOR}
    return out


_faltan, _mirados = [], 0
for f in sorted(list((RAIZ / "core").glob("*.py"))) + [RAIZ / "app.py"]:
    tr = ast.parse(f.read_text(encoding="utf-8"))
    usos = {x.func.id: x.lineno for x in ast.walk(tr)
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
            and x.func.id in MOTOR}
    if not usos:
        continue
    _mirados += 1
    disp = _disponibles(tr)
    _faltan += [f"{f.name}:{ln} `{k}`" for k, ln in usos.items() if k not in disp]
chk(f"los {_mirados} módulos que usan el motor lo tienen importado", not _faltan,
    str(_faltan))
chk("...y el chequeo miró algo", _mirados > 40, str(_mirados))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. El DATO no se tocó")
from core import toolruns                                          # noqa: E402
chk("las claves de HERRAMIENTAS son las que se guardan en la hoja",
    set(toolruns.HERRAMIENTAS) == {"survey", "plomada", "rieles", "buffers",
                                   "belting"},
    str(set(toolruns.HERRAMIENTAS)))
_ex = (RAIZ / "core/expenses.py").read_text(encoding="utf-8")
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
from core import expenses as _EXP, valores as _VAL2            # noqa: E402
chk("expenses: las CATEGORIAS que se guardan son las canonicas",
    "Materials" in _EXP.CATEGORIAS and "Fuel" in _EXP.CATEGORIAS, str(_EXP.CATEGORIAS))
chk("...y una fila SIN migrar sigue casando (canon la traduce al leer)",
    _VAL2.canon("Materiales") == "Materials"
    and _VAL2.canonizar([{"Category": "Combustible"}], "Expenses")[0]["Category"] == "Fuel")

# ── 5 ────────────────────────────────────────────────────────────
sec("5. No queda ningún mensaje en español en los 14")
import medir_f5 as M                                               # noqa: E402


def _es_msg(s):
    return len(s.split()) >= 3 or s.rstrip().endswith((".", ":", "…"))


_resto = {}
for mod in MODS:
    c = M.clasifica(RAIZ / "core" / mod)
    r = sorted({s for _, s in c["RETORNO"] + c["OTRO"] if _es_msg(s)})
    if r:
        _resto[mod] = r
chk("0 mensajes en español", not _resto,
    str({k: v[:2] for k, v in _resto.items()}))

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
