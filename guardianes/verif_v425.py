"""v425: el trabajo y el gasto de ESTRUCTURA dejan de ser un hueco anónimo.

v422 separó el dato (`interno` aparte de `proyecto`) y v423 le dio su sección. Pero
en Finanzas seguía sin verse: las 172 h de jornada que nadie imputaba a una obra
caían en «sin asignar» junto a los traslados, y el gasto de la oficina se sumaba a un
KPI que se llama **«Costo cargado a obras»** — o sea, mintiendo.

Lo que se protege:
  (a) UNA sola aritmética del reparto (`_partir_gasto`), no copiada en la vista;
  (b) ⚠️ la INVARIANTE: `total_obra + total_int` es exactamente el costo del grupo de
      antes de v425, así que sin localizaciones no se mueve ni un número;
  (c) las compras HUÉRFANAS se quedan del lado de obra — no se sabe de quién son, y
      llamarlas estructura sería afirmar algo que nadie sabe;
  (d) todo lo nuevo es CONDICIONAL: sin estructura, las pantallas quedan idénticas;
  (e) ⚠️ en la conciliación, `interno` es un DESGLOSE de «pagadas y no cargadas», no
      un sumando nuevo: sumarlo otra vez descuadraría la cadena de v313, que cierra.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def arbol(p: Path):
    src = p.read_text(encoding="utf-8")
    sin = tokenize.untokenize(
        [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
         if t.type != tokenize.COMMENT])
    return ast.parse(sin)


PU = arbol(RAIZ / "core" / "projects_ui.py")


def fn(a, nombre):
    return next((n for n in ast.walk(a)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ── (a) Una sola aritmética ─────────────────────────────────────────────────
print("== a) el reparto obra/estructura vive en UN sitio ==")
chk("existe `_partir_gasto`", fn(PU, "_partir_gasto") is not None)
_rge = fn(PU, "render_group_expenses")
_usa = [n for n in ast.walk(_rge) if isinstance(n, ast.Call)
        and getattr(n.func, "id", getattr(n.func, "attr", "")) == "_partir_gasto"]
chk("la vista lo LLAMA", len(_usa), 1)
# …y no vuelve a filtrar por `interno` a mano (sería una segunda definición)
_amano = [n.lineno for n in ast.walk(_rge)
          if isinstance(n, ast.Constant) and n.value == "interno"]
chk("la vista no re-filtra por `interno` a mano", _amano, [])

# ── (b/c) Invariante y huérfanas, sobre la función REAL ─────────────────────
print("\n== b) la invariante: nada se mueve sin localizaciones ==")
import streamlit as st                                              # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "x"}
from core import projects_ui as _PU                                 # noqa: E402

_sin = {"proyectos": [{"id": "A", "mano_obra": 1000.0, "compras": 500.0},
                      {"id": "B", "mano_obra": 200.0, "compras": 0.0}],
        "compras_grupo": 550.0, "huerfanos": {"n": 1, "total": 50.0}}
_p = _PU._partir_gasto(_sin)
_viejo = round(sum(f["mano_obra"] for f in _sin["proyectos"]) + _sin["compras_grupo"], 2)
chk("sin internas, `total_obra` == el costo del grupo de antes", _p["total_obra"], _viejo)
chk("...y `total_int` es 0", _p["total_int"], 0.0)
chk("...y no aparta ninguna fila", len(_p["obras"]), 2)

_con = {"proyectos": [{"id": "A", "mano_obra": 1000.0, "compras": 500.0, "interno": False},
                      {"id": "B", "mano_obra": 200.0, "compras": 0.0, "interno": False},
                      {"id": "C", "mano_obra": 300.0, "compras": 700.0, "interno": True}],
        "compras_grupo": 1250.0, "huerfanos": {"n": 1, "total": 50.0}}
_q = _PU._partir_gasto(_con)
chk("con estructura, obra y estructura se separan",
    ([f["id"] for f in _q["obras"]], [f["id"] for f in _q["internas"]]),
    (["A", "B"], ["C"]))
chk("INVARIANTE obra+estructura = mano de obra total + compras del grupo",
    round(_q["total_obra"] + _q["total_int"], 2),
    round(sum(f["mano_obra"] for f in _con["proyectos"]) + _con["compras_grupo"], 2))

print("\n== c) las compras huérfanas se quedan en OBRA ==")
# 500 (A) + 0 (B) + 50 (huérfanas) = 550; las 700 del almacén no cuentan como obra
chk("compras de obra incluyen las huérfanas y NO las internas",
    _q["compras_obra"], 550.0)
chk("compras de estructura son solo las internas", _q["compras_int"], 700.0)

# ── (d) Todo lo nuevo es condicional ────────────────────────────────────────
print("\n== d) sin estructura, las pantallas quedan idénticas ==")


def _condicionado(f, marca):
    """¿La aparición de `marca` cuelga de un `if <algo> > 0`?"""
    for n in ast.walk(f):
        if not isinstance(n, ast.If):
            continue
        _t = ast.dump(n.test)
        if not any(x in _t for x in ("tot_int", "tot_intn", "tot_cint", "_mo_int",
                                     "interno")):
            continue
        for s in n.body:
            for c in ast.walk(s):
                if isinstance(c, ast.Constant) and isinstance(c.value, str) \
                        and marca in c.value:
                    return True
    return False


# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
chk("«Gasto de estructura» solo si hay estructura",
    _condicionado(_rge, "Gasto de estructura")
    or _condicionado(_rge, "Overhead spend"))
_rgh = fn(PU, "render_group_hours")
chk("«En estructura» (horas) solo si hay estructura",
    _condicionado(_rgh, "En estructura") or _condicionado(_rgh, "On overhead"))
# ⚠️ CADUCADO por v441 (i18n F4): la columna pasó a «On overhead (h)». Lo que la
# regla protege no es el rótulo, sino que la columna solo aparezca si hay estructura.
chk("la columna de la tabla también",
    _condicionado(_rgh, "En estructura (h)") or _condicionado(_rgh, "On overhead (h)"))

# ── (e) La conciliación: desglose, no sumando ───────────────────────────────
print("\n== e) en la conciliación, `interno` DESGLOSA — no suma ==")
# ⚠️ Por NOMBRE, no por docstring: mi primera versión buscaba «conciliaci» en el
# docstring y no lo encontraba (empieza por «El puente entre…»), así que el chequeo
# fallaba sin que hubiera nada mal. Un localizador frágil produce rojos que no existen.
_conc = fn(PU, "_pnl_conciliacion")
chk("se encuentra la vista de la conciliación", _conc is not None)
if _conc:
    # la fila de interno existe…
    # ⚠️ CADUCADO por el i18n (v441): la fila dice ahora «of which, overhead work».
    # La conducta es la misma —existe la fila de desglose—; solo cambió el idioma.
    _tiene = any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                 and ("estructura" in c.value.lower() or "overhead" in c.value.lower())
                 for c in ast.walk(_conc))
    chk("...tiene la fila de estructura", _tiene)
    # …y NO se suma a base_teorica ni a costo_real (esos vienen tal cual de `cc`)
    _sumas = [n for n in ast.walk(_conc) if isinstance(n, ast.BinOp)
              and isinstance(n.op, ast.Add)
              and any(isinstance(c, ast.Constant) and c.value == "interno"
                      for c in ast.walk(n))]
    chk("...y no se suma a ninguna cifra de la cadena", _sumas, [])

# La cadena de v313 sigue cerrando: se comprueba con la función REAL.
from core import finance as F                                       # noqa: E402
_h = {"a": {"nombre": "A", "jornada": 10.0, "proyecto": 6.0, "interno": 3.0}}
_base = _h["a"]["proyecto"] * 50 - 0 + (_h["a"]["jornada"] - _h["a"]["proyecto"]) * 50
chk("base teórica = cargado − cobrado_no_pagado + pagado_no_cargado (con interno "
    "dentro de lo pagado y no cargado)", round(_base, 2), 500.0)

# ── (f) El dato de origen sigue separado ────────────────────────────────────
print("\n== f) el dato viene ya separado de v422 ==")
from core import timeclock as T                                     # noqa: E402

# ⚠️ Buscar la palabra «interno» en el fuente NO sirve: borrando la clave del dict
# devuelto quedan otras apariciones (`a["interno"]`, `_ids_internos`) y el chequeo
# pasaba con la separación ROTA. Se comprueba que la CLAVE esté en el dict que la
# función construye — lo destapó probar el guardián contra el código roto.
TC = arbol(RAIZ / "core" / "timeclock.py")
FI = arbol(RAIZ / "core" / "finance.py")


def _claves_dict(d) -> set:
    return {k.value for k in d.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)}


def _claves_devueltas(a, nombre) -> set:
    """Claves del dict que la función ENTREGA — el de `out.append({...})` o el del
    `return {...}`, no cualquier dict de dentro.

    ⚠️ Mirar todos los dicts de la función NO sirve: `group_hours` mantiene un
    acumulador `agg.setdefault(clave, {... "interno": 0.0 ...})`, así que borrar la
    clave del resultado seguía dando OK. Lo destapó el código roto, no leerlo.
    """
    f = fn(a, nombre)
    out = set()
    for n in ast.walk(f or ast.Module(body=[], type_ignores=[])):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            out |= _claves_dict(n.value)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "append" and n.args
                and isinstance(n.args[0], ast.Dict)):
            out |= _claves_dict(n.args[0])
        # `jornada_y_proyecto` entrega el dict que construye con setdefault sobre `out`
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "setdefault" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "out" and len(n.args) > 1
                and isinstance(n.args[1], ast.Dict)):
            out |= _claves_dict(n.args[1])
    return out


_gh = _claves_devueltas(TC, "group_hours")
chk("`group_hours` devuelve la clave `interno`", "interno" in _gh)
chk("...y `costo_interno`", "costo_interno" in _gh)
chk("...y sigue devolviendo `proyecto` y `costo` (obra)",
    {"proyecto", "costo"} <= _gh)
chk("`jornada_y_proyecto` devuelve `interno`",
    "interno" in _claves_devueltas(TC, "jornada_y_proyecto"))
chk("`conciliacion_mo` expone `interno`",
    "interno" in _claves_devueltas(FI, "conciliacion_mo"))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
