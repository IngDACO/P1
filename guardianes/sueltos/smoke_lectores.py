"""Llamar de VERDAD a los 18 envoltorios nuevos.

⚠️ Importar un módulo NO ejecuta el cuerpo de sus funciones, así que un nombre mal
escrito dentro del envoltorio (p. ej. `TRABAJOS_SHEET` cuando la constante es
`TRAB_SHEET`) pasa el import, pasa el compileall, pasa el guardián de AST… y
revienta la primera vez que alguien abre esa pantalla. La única forma de cazarlo
es llamarlos.
"""
import importlib
import inspect
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1", "rol": "administrador"}

# módulo → [(envoltorio, argumentos)]
CASOS = [
    ("alerts", "_records", ()),
    ("auditoria", "_records", ()),
    ("catalogo", "_records", ()),
    ("clientes", "_records", ()),
    ("credentials", "_records", ()),
    ("expenses", "_records", ()),
    ("invoices", "_records", ()),
    ("orders", "_records", ()),
    ("payroll", "_records", ()),
    ("prestart", "_records", ()),
    ("quotes", "_records", ()),
    ("toolruns", "_records", ()),
    ("roster", "_trab_records", ()),
    ("roster", "_roster_records", ()),
    ("projects", "_records", ("Proyectos",)),
    ("projects", "_fichaje_records", ()),
    ("timeclock", "_cached_records", ()),
    ("inventory", "_records", None),           # el título se resuelve abajo
]

ok = True
print("== llamando a cada envoltorio ==")
for mod, fn_name, args in CASOS:
    m = importlib.import_module(f"core.{mod}")
    fn = getattr(m, fn_name, None)
    if fn is None:
        print(f"   ‼️ {mod}.{fn_name} no existe")
        ok = False
        continue
    if args is None:                            # inventory: buscar su constante de hoja
        cand = next((getattr(m, c) for c in ("SHEET", "ACTIVOS_SHEET", "INV_SHEET")
                     if isinstance(getattr(m, c, None), str)), None)
        args = (cand,) if cand else ()
        if not args:
            params = list(inspect.signature(fn).parameters)
            print(f"   ⚠️ {mod}.{fn_name}: no se encontró su constante de hoja "
                  f"(params: {params}) — revisar a mano")
            continue
    try:
        r = fn(*args)
        n = len(r) if hasattr(r, "__len__") else "?"
        print(f"   ✓ {mod}.{fn_name}{args if args else '()'} → {n} filas")
    except Exception as e:
        ok = False
        print(f"   ‼️ {mod}.{fn_name}{args}: {type(e).__name__}: {e}")

print("\n== y que las invalidaciones se puedan ejecutar sin romper ==")
for mod in ("alerts", "auditoria", "catalogo", "clientes", "credentials", "expenses",
            "invoices", "orders", "payroll", "prestart", "quotes", "toolruns",
            "roster", "projects", "inventory"):
    m = importlib.import_module(f"core.{mod}")
    inv = getattr(m, "_invalidate", None)
    if inv is None:
        continue
    try:
        inv()
        print(f"   ✓ {mod}._invalidate()")
    except Exception as e:
        ok = False
        print(f"   ‼️ {mod}._invalidate(): {type(e).__name__}: {e}")

print("\n" + ("✅ los 18 envoltorios responden y las invalidaciones corren"
              if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
