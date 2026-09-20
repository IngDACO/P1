"""EJECUTA las pantallas que ahora pasan los VALORES por `i18n.etiqueta`.

⚠️ Por qué hace falta: al enrutar los valores metí `_etq(...)` en `render_nominas`, donde
`_etq` YA era una variable local (el dict de `auth.etiqueta_usuarios`). Python marca el
nombre local en el ámbito ENTERO, así que esa pantalla habría reventado con
«'dict' object is not callable» — el fallo de v437/v439/v440 por CUARTA vez. Ni
`compileall` ni importar el módulo lo ven: hay que LLAMAR a la función (v378).

⚠️ Firmas LEÍDAS del código, no supuestas (regla v135).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "smoke", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "smoke"}

pintado = []


def _cap(*a, **k):
    if a and isinstance(a[0], str):
        pintado.append(a[0])
    return None


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getattr__(self, _n):
        return _cap


for _n in ("warning", "info", "success", "error", "markdown", "caption", "write",
           "subheader", "header", "title", "divider", "toast", "metric"):
    setattr(st, _n, _cap)

ok = True


def chk(t_, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


# ── 1 · `etiqueta` traduce sin tocar el dato ──────────────────────
from core import i18n                                             # noqa: E402
chk("etiqueta('En progreso') = 'In progress'",
    i18n.etiqueta("En progreso") == "In progress", i18n.etiqueta("En progreso"))
chk("etiqueta deja pasar lo que no conoce (no inventa)",
    i18n.etiqueta("PRJ-0007") == "PRJ-0007")
chk("etiqueta('') no revienta", i18n.etiqueta("") == "")

# ── 2 · `_etq` es la FUNCIÓN en cada módulo que la usa ────────────
import importlib                                                  # noqa: E402
for m in ("projects_ui", "home_ui", "auth_ui", "payroll_ui",
          "catalogo_ui", "inventory_ui"):
    mod = importlib.import_module("core." + m)
    f = getattr(mod, "_etq", None)
    chk(f"{m:14} `_etq` es la función de i18n", callable(f) and f("En pausa") == "On hold",
        repr(f))

# ── 3 · la pantalla que habría reventado, EJECUTADA ───────────────
# ⚠️ Se sustituyen las lecturas de Sheets: el smoke prueba el CÓDIGO, no la hoja.
from core import payroll, timeclock, auth                         # noqa: E402
import pandas as pd                                               # noqa: E402

_FILAS = [{"ID": "NOM-0001", "Usuario": "u1", "Nombre": "Ana",
           "PeriodoDesde": "2026-08-01", "PeriodoHasta": "2026-08-15",
           "Horas": "38", "TarifaHora": "40", "Base": "1520", "Neto": "1300",
           "Estado": "emitida"},
          {"ID": "NOM-0002", "Usuario": "u2", "Nombre": "Beto",
           "PeriodoDesde": "2026-08-01", "PeriodoHasta": "2026-08-15",
           "Horas": "10", "TarifaHora": "0", "Base": "0", "Neto": "0",
           "Estado": "pagada"}]
payroll.is_configured = lambda: True
payroll.list_nominas = lambda *a, **k: _FILAS
payroll.resumen = lambda *a, **k: {"a_pagar": 1300.0, "pagado": 0.0, "n": 2}
auth.list_users = lambda *a, **k: [{"Usuario": "u1", "Nombre": "Ana"},
                                   {"Usuario": "u2", "Nombre": "Beto"}]
timeclock.jornada_y_proyecto = lambda *a, **k: {}
st.columns = lambda spec, **k: [_Ctx() for _ in
                                (range(spec) if isinstance(spec, int) else spec)]
st.button = lambda *a, **k: False
st.selectbox = lambda label, opts, **k: list(opts)[0]
st.dataframe = lambda *a, **k: type("S", (), {"selection": type("X", (), {"rows": []})()})()

from core import payroll_ui                                       # noqa: E402
try:
    payroll_ui.render_nominas("cliente1")
    _err = ""
except Exception as e:                                            # noqa: BLE001
    _err = f"{type(e).__name__}: {e}"
chk("render_nominas SE EJECUTA (no 'dict object is not callable')", not _err, _err)

# ── 4 · y lo que pinta está en inglés ─────────────────────────────
_txt = " ".join(pintado)
chk("...y la pantalla no pinta el estado crudo en español",
    "emitida" not in _txt and "pagada" not in _txt,
    [p for p in pintado if "emitida" in p or "pagada" in p][:2])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
