# -*- coding: utf-8 -*-
"""Guardián de v446 — F5b: los mensajes de backend de otros 6 módulos.

`quotes`, `projects`, `ausencias`, `orders`, `catalogo`, `clientes`. Mismo criterio
que v445: se traduce lo que la función DEVUELVE (la UI lo pinta) y **no** los
mensajes de log ni los valores que se guardan en la hoja.

⚠️ Lo que aquí NO se puede tocar, y falla en SILENCIO si se toca:
  · `projects.derive_estado` devuelve `"En progreso"`/`"Planificado"`/`"Completado"`:
    se ESCRIBEN en la hoja y se comparan en 387 sitios;
  · las CLAVES de `ausencias.TIPOS` y sus `estado_roster` (`"LEAVE"`/`"OFF"`), que
    van al tablero;
  · los estados de `quotes` (`borrador`, `enviada`, `aceptada`…).
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


MODS = ("quotes.py", "projects.py", "ausencias.py", "orders.py",
        "catalogo.py", "clientes.py")

# ── 1 ────────────────────────────────────────────────────────────
sec("1. Los mensajes se EJECUTAN y salen en inglés (importar no ejecuta, v378)")
from core import ausencias as AU, catalogo as CAT, clientes as CL   # noqa: E402
from core import orders as OR, projects as P, quotes as Q           # noqa: E402

_o, _m = AU.solicitar("cliente1", "zzz", "ZZZ", "libre", "2026-13-99", "2026-13-99")
chk("ausencias.solicitar (fechas malas)", "could not be read" in str(_m).lower(), str(_m))
_o, _m = Q.crear("cliente1", "CLI-0001", "zzz", [], creado_por="zzz")
chk("quotes.crear (sin líneas)", "at least one line" in str(_m).lower(), str(_m))
_o, _m = Q.set_estado("COT-NO-EXISTE-v446", Q.ACEPTADA)
chk("quotes.set_estado (id inexistente)", "not found" in str(_m).lower(), str(_m))
_o, _m = P.update_project("PRJ-NO-EXISTE-v446", {"Nombre": "x"})
chk("projects.update_project (id inexistente)", "not found" in str(_m).lower(), str(_m))
_o, _m = OR.crear("PRJ-0001", "cliente1", "prov", 0, creado_por="zzz")
chk("orders.crear (valor 0)", "greater than 0" in str(_m).lower(), str(_m))
_o, _m = CAT.crear("cliente1", "", tipo="producto", costo_unit=1)
chk("catalogo.crear (sin nombre)", "a name" in str(_m).lower(), str(_m))
_o, _m = CL.create_cliente("cliente1", "")
chk("clientes.create_cliente (sin nombre)", "required" in str(_m).lower(), str(_m))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. El DATO no se tocó")
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
chk("projects.derive_estado devuelve el estado CANONICO",
    P.derive_estado(50, "", "") == "In progress"
    and P.derive_estado(0, "", "") == "Planned",
    f"{P.derive_estado(50, '', '')} - {P.derive_estado(0, '', '')}")
chk("ausencias: las CLAVES de TIPOS son el dato",
    set(AU.TIPOS) == {"vacaciones", "enfermedad", "libre"}, str(set(AU.TIPOS)))
chk("...y `estado_roster` va al tablero, no a la pantalla",
    AU.TIPOS[AU.VACACIONES]["estado_roster"] == "LEAVE"
    and AU.TIPOS[AU.LIBRE]["estado_roster"] == "OFF")
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
from core import valores as _VAL4                              # noqa: E402
chk("quotes: los estados que se guardan son los canonicos",
    Q.BORRADOR == "draft" and Q.ACEPTADA in Q.ESTADOS, str(Q.ESTADOS))
chk("...y una cotizacion SIN migrar sigue casando",
    _VAL4.canon("aceptada") == Q.ACEPTADA and _VAL4.canon("borrador") == Q.BORRADOR)

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Ningún `t()` se CONGELA al importar")
# ⚠️ Este chequeo cazó mi propio fallo en esta misma versión: había metido `t()`
# dentro de `ausencias.TIPOS`, que se construye a nivel de módulo — la trampa que
# v445 acababa de documentar, repetida veinte minutos después. La constante guarda
# el texto BASE y `nombre_tipo()` traduce al pintarlo.
from barre_t_modulo import congelados, EXCL                        # noqa: E402
_frios = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if f.name in EXCL:
        continue
    _frios += [f"{f.name}:{ln}" for ln, _ in sorted(set(congelados(f)))]
chk("0 llamadas a `t()` congeladas al importar", not _frios, str(_frios))
chk("`ausencias.nombre_tipo` existe y traduce al LLAMARLA",
    AU.nombre_tipo(AU.VACACIONES) == "Annual leave"
    and AU.nombre_tipo("desconocido") == "desconocido")

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Nadie tapa el motor con una variable")
for mod in MODS:
    tr = ast.parse((RAIZ / "core" / mod).read_text(encoding="utf-8"))
    malas = []
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        cuerpo = []
        for h in fn.body:
            pila = [h]
            while pila:
                x = pila.pop()
                cuerpo.append(x)
                for c in ast.iter_child_nodes(x):
                    if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                          ast.AsyncFunctionDef, ast.ClassDef)):
                        pila.append(c)
        comp = {id(nn) for x in cuerpo for g in (getattr(x, "generators", []) or [])
                for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        if any(isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)
               and x.id == "t" and id(x) not in comp for x in cuerpo):
            malas.append(f"{fn.name}:{fn.lineno}")
    chk(f"{mod:14} ninguna función usa `t` como variable", not malas, str(malas))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. No queda ningún mensaje en español")
import medir_f5 as M                                               # noqa: E402


def _es_msg(s):
    return len(s.split()) >= 3 or s.rstrip().endswith((".", ":", "…"))


for mod in MODS:
    c = M.clasifica(RAIZ / "core" / mod)
    resto = sorted({s for _, s in c["RETORNO"] + c["OTRO"] if _es_msg(s)})
    chk(f"{mod:14} 0 mensajes en español", not resto, f"{len(resto)}: {resto[:2]}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
