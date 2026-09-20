"""Smoke de v452: EJECUTA los `format_func` nuevos.

⚠️ Importar no ejecuta (v378). Un lambda dentro de un `st.radio` no corre hasta que
Streamlit pinta el widget, así que un `NameError` o un `TypeError` ahí vive escondido
hasta que alguien abre esa pantalla — es el fallo de v437/v439/v440/v442, cinco veces.

Aquí se extraen los lambdas por AST, se compilan con `t` y `_etq` REALES en su ámbito,
y se llaman con TODAS las opciones de su widget.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

from core.i18n import t, etiqueta as _etq  # noqa: E402

fallos = []
WID = {"radio", "selectbox", "segmented_control", "pills", "multiselect"}
total = 0

for f in sorted(CORE.glob("*_ui.py")):
    arb = ast.parse(f.read_text(encoding="utf-8"))
    for c in ast.walk(arb):
        if not isinstance(c, ast.Call) or getattr(c.func, "attr", None) not in WID:
            continue
        lam = next((k.value for k in c.keywords
                    if k.arg == "format_func" and isinstance(k.value, ast.Lambda)), None)
        if lam is None:
            continue
        # las opciones del widget (segundo posicional)
        ops = []
        for a in list(c.args)[1:2]:
            if isinstance(a, ast.List):
                ops = [e.value for e in a.elts
                       if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if not ops:
            continue
        try:
            fn = eval(compile(ast.Expression(lam), "<lam>", "eval"),
                      {"t": t, "_etq": _etq, "str": str})
        except Exception as e:
            fallos.append(f"{f.name}:{c.lineno} no compila: {e}")
            continue
        for o in ops:
            total += 1
            try:
                r = fn(o)
                if not isinstance(r, str):
                    fallos.append(f"{f.name}:{c.lineno} format_func({o!r}) -> {type(r).__name__}")
            except Exception as e:
                fallos.append(f"{f.name}:{c.lineno} format_func({o!r}) revienta: {e}")

print(f"format_func ejecutados: {total} llamadas")
for x in fallos:
    print("  FALLO  " + x)

# Y los valores de negocio que ahora pasan por etiqueta() en las celdas.
print("\nvalores de negocio por etiqueta():")
for v in ("pendiente", "parcial", "cobrada", "vencida", "anulada",
          "borrador", "enviada", "aceptada", "rechazada",
          "Instalación", "Delivery", "Ripout", "Otro"):
    r = _etq(v)
    ok = isinstance(r, str) and r
    print(f"  {'OK ' if ok else 'FALLO'}  {v!r:15} -> {r!r}")
    if not ok:
        fallos.append(f"etiqueta({v!r}) -> {r!r}")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
