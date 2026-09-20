"""Guardián de v440 — F3: la interfaz de GESTIÓN, en inglés.

Lo que protege, y por qué cada cosa (todas salieron de un fallo real de esta tanda):

 1. **0 etiquetas sin `t()`** en los 15 módulos, medido por POSICIÓN. ⚠️ NO por idioma:
    el detector de español no ve «Fichar», «Firma», «Pendientes» ni «Mis ausencias», y
    con él di F2 por terminada con 47 etiquetas dentro (v439).
 2. ⚠️ Las **CLAVES de widget** siguen en su sitio. `st.form("cli_nuevo")` recibe la key
    como primer posicional: envolverla en `t()` la haría depender del idioma y el
    formulario perdería su estado al cambiarlo. Igual `ui.confirmar_borrado(key, texto)`.
 3. ⚠️ Las **CLAVES de `column_config`** siguen en español. Son el nombre de la columna
    que `st.data_editor` DEVUELVE; traducirlas deja la lectura buscando una columna que
    ya no existe, sin ningún error. La ETIQUETA de la columna sí va traducida.
 4. ⚠️ **Nadie tapa `t`.** Si `t` ya es variable en una función y la traducción le mete
    `t("…")`, Python la marca local en el ámbito ENTERO y revienta. Pasó en v437, v439 y
    otra vez en `quotes_ui` (3 funciones: «Nueva cotización» no habría abierto).
 5. Los 15 módulos importan el motor a nivel de MÓDULO y **se ejecutan** al importarse.
"""

def _cc_dict(v):
    """El dict de `column_config`, venga literal o por `tabla.cfg(None, {...})`.

    ⚠️ v450 movió la configuración a `tabla.cfg`, que traduce la CABECERA sin tocar la
    clave. Sin resolverlo, un chequeo que solo entiende `ast.Dict` deja de mirar todas
    las tablas y devuelve 0 — que parece un aprobado y no lo es.
    """
    import ast as _a
    if isinstance(v, _a.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    return v if isinstance(v, _a.Dict) else None

import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

MODS = ["projects_ui", "auth_ui", "home_ui", "roster_ui", "inventory_ui", "clientes_ui",
        "catalogo_ui", "invoices_ui", "payroll_ui", "quotes_ui", "location_ui",
        "plan_ui", "tool_save_ui"]
ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def _src(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. 0 etiquetas sin t(), medido por POSICIÓN (no por idioma)")
from i18n_tool import piezas                                      # noqa: E402

ES = re.compile(r"[áéíóúÁÉÍÓÚñÑ¿¡]|\b(de|del|la|el|los|las|con|para|por|que|una|un|su|"
                r"al|es|son|se|lo|guardar|eliminar|crear|nuevo|nueva|elige|añadir|"
                r"proyecto|obra|cliente|usuario|grupo|hora|horas|dia|dias|fecha|"
                r"nombre|todos|todas|aún|más|sin|ver|hay|esta|este)\b", re.I)
restos = []
for m in MODS + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    for p in piezas(RAIZ / rel):
        if ES.search(p["txt"]):
            restos.append(f"{m}:{p['lin']} {p['txt'][:44]!r}")
chk("0 etiquetas en español en los 14 módulos", not restos, str(restos[:5]))

# ⚠️ EL CHEQUEO QUE DE VERDAD MIDE. El de arriba filtra por IDIOMA y eso ya falló tres
# veces: «Neto a pagar» no lleva acento ni palabra funcional, así que una etiqueta
# devuelta al español pasa por delante (lo comprobé rompiéndolo: no la veía).
# El invariante correcto no habla de idioma: **toda cadena SUELTA que llegue a una
# función de display tiene que estar envuelta en `t()`**. Las que no se pueden envolver
# son los trozos de f-string, y esos se marcan aparte.
_sueltos = []
for m in MODS:
    _sueltos += [f"{m}:{p['lin']} {p['txt'][:40]!r}"
                 for p in piezas(RAIZ / f"core/{m}.py") if not p["fstr"]]
chk("0 cadenas sueltas sin envolver en t()", not _sueltos, str(_sueltos[:5]))
_tot = sum(len(piezas(RAIZ / ("app.py" if m == "app" else f"core/{m}.py")))
           for m in MODS + ["app"])
# ⚠️ El barrido ve lo que NO está envuelto (una vez envuelto, el argumento es una Call y
# deja de ser un Constant), así que un número BAJO aquí es lo normal y no prueba nada por
# sí solo. Lo que demuestra que la traducción ocurrió es contar las llamadas a `t(`.
_llam = 0
for m in MODS + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    _llam += sum(1 for x in ast.walk(ast.parse(_src(rel)))
                 if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                 and x.func.id == "t")
chk("...y el barrido no corre en vacío", _tot >= 100, f"{_tot} literales sin envolver")
chk("la traducción REALMENTE se aplicó (llamadas a t())", _llam >= 900, f"{_llam} llamadas")

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Las CLAVES de widget NO se tradujeron")
# `st.form(key)` y `ui.confirmar_borrado(key, texto)` — verbatim, medidas en el código
KEYS = {
    "core/clientes_ui.py": ['st.form("cli_nuevo")'],
    "core/catalogo_ui.py": ['st.form("cat_new")'],
    "core/auth_ui.py": ['confirmar_borrado("del_g_ok"', 'confirmar_borrado("man_del_ok"',
                        '_delok"'],
}
for rel, ks in KEYS.items():
    falta = [k for k in ks if k not in _src(rel)]
    chk(f"{Path(rel).name:18} conserva sus keys", not falta, str(falta))

# ⚠️ Y la REGLA, no solo los casos: ningún `st.form(...)` puede recibir `t(...)`.
malos = []
for m in MODS:
    tr = ast.parse(_src(f"core/{m}.py"))
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)):
            continue
        if x.func.attr not in ("form",):
            continue
        if x.args and isinstance(x.args[0], ast.Call) and \
                isinstance(x.args[0].func, ast.Name) and x.args[0].func.id == "t":
            malos.append(f"{m}:{x.lineno}")
chk("ningún st.form() recibe una key traducida", not malos, str(malos))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Las CLAVES de column_config siguen en español (la etiqueta sí se traduce)")
# ⚠️ `st.data_editor` devuelve las columnas con el nombre de la CLAVE, y el código las
# lee después por ese nombre. La etiqueta es lo único que se ve.
# ⚠️ Se comprueba la REGLA, no una lista de claves escrita a mano: mi primera versión
# afirmaba que `clientes_ui` tenía la clave `"Pendiente"` y NO existe (ahí es una
# etiqueta de `st.metric`), así que daba FALLO con el código correcto — el test fallando
# por su propia aritmética (v363/v372/v423).
_claves_mal, _n_cols = [], 0
for m in MODS:
    tr = ast.parse(_src(f"core/{m}.py"))
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)):
            continue
        for kw in x.keywords:
            if kw.arg != "column_config" or _cc_dict(kw.value) is None:
                continue
            for k in _cc_dict(kw.value).keys:
                _n_cols += 1
                if isinstance(k, ast.Call) and isinstance(k.func, ast.Name) \
                        and k.func.id == "t":
                    _claves_mal.append(f"{m}:{k.lineno}")
chk("ninguna CLAVE de column_config está traducida", not _claves_mal, str(_claves_mal))
chk("...y hay claves de column_config que vigilar", _n_cols >= 8, f"{_n_cols}")
# y la etiqueta SÍ va traducida (si no, el chequeo de arriba pasaría sin traducir nada)
_inv = _src("core/invoices_ui.py")
chk("...y la ETIQUETA de la columna sí va traducida",
    'NumberColumn(t("Amount")' in _inv, "no se encontró t(\"Amount\") en invoices_ui")

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Nadie tapa `t` (v437 · v439 · quotes_ui: tres veces el mismo fallo)")


def _mismo_ambito(fn):
    """⚠️ Sin descender a lambdas, funciones anidadas ni comprensiones: todas tienen su
    propio ámbito y contarlas daba FALSOS POSITIVOS sobre código correcto (trampa nº3)."""
    out = []
    for h in fn.body:
        pila = [h]
        while pila:
            x = pila.pop()
            out.append(x)
            for c in ast.iter_child_nodes(x):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return out


tapan = []
for m in MODS + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    tr = ast.parse(_src(rel))
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nod = _mismo_ambito(fn)
        comp = {id(nn) for x in nod for g in (getattr(x, "generators", []) or [])
                for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        _st = [x.lineno for x in nod if isinstance(x, ast.Name)
               and isinstance(x.ctx, ast.Store) and x.id == "t" and id(x) not in comp]
        if "t" in {a.arg for a in fn.args.args + fn.args.kwonlyargs}:
            _st.append(fn.lineno)
        _ld = [x for x in nod if isinstance(x, ast.Call)
               and isinstance(x.func, ast.Name) and x.func.id == "t"]
        if _st and _ld:
            tapan.append(f"{m}:{fn.lineno} {fn.name}")
chk("ninguna función tapa `t`", not tapan, str(tapan[:4]))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. El motor se importa a nivel de MÓDULO y los módulos EJECUTAN al importarse")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}
import importlib                                                  # noqa: E402







for m in MODS:
    tr = ast.parse(_src(f"core/{m}.py"))
    imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
              and any(a.name == "t" for a in x.names) for x in tr.body)
    try:
        importlib.import_module("core." + m)
        _imp_ok, _err = True, ""
    except Exception as e:                                        # noqa: BLE001
        _imp_ok, _err = False, f"{type(e).__name__}: {e}"
    chk(f"{m:16} importa `t` arriba y el módulo carga", imp and _imp_ok,
        f"import_t={imp} {_err}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
