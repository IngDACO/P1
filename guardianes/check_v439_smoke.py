"""EJECUTA las dos funciones que estaban rotas. Importar NO ejecuta (v378).

`_aviso_olvido` y `render_mis_ausencias` daban `UnboundLocalError` y `'str' object is
not callable`, y ni `compileall` ni importar el módulo los ven: hay que LLAMARLOS. Mi
verificación de F2 fue «los cuatro compilan e importan» y por eso no vio nada.

⚠️ Firmas LEÍDAS del código, no supuestas (regla v135, que ya falló seis veces):
    _aviso_olvido(nombre, grupo, usuario, sess)
    render_mis_ausencias()          # lee la identidad de session_state
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "smoke", "rol": "field",
                            "grupo": "cliente1", "nombre": "smoke"}

pintado = []


def _cap(*a, **k):
    if a and isinstance(a[0], str):
        pintado.append(a[0])
    return None


for _n in ("warning", "info", "success", "error", "markdown", "caption", "write",
           "subheader", "metric", "divider", "toast"):
    setattr(st, _n, _cap)

ok = True
import inspect                                                    # noqa: E402

# ── 1 · timeclock_ui._aviso_olvido ────────────────────────────────
from core import timeclock_ui, timeclock                          # noqa: E402
print(f"  firma real: _aviso_olvido{inspect.signature(timeclock_ui._aviso_olvido)}")
# Sesión abierta de un día ANTERIOR: es la rama que recorre el bucle y llama a t()
# ANTES del strptime — exactamente donde reventaba.
_sess = {timeclock.TIPO_GENERAL: {"proyecto": "", "clock_in": "2026-08-29 07:00:00"},
         timeclock.TIPO_PROYECTO: {"proyecto": "Torre A", "clock_in": "2026-08-29 08:30:00"}}
try:
    timeclock_ui._aviso_olvido("smoke", "cliente1", "smoke", _sess)
    print("  OK    _aviso_olvido ejecuta el bucle sin excepción")
except (UnboundLocalError, TypeError) as e:
    print(f"  FALLO EL BUG SIGUE VIVO → {type(e).__name__}: {e}")
    ok = False
except Exception as e:                                            # noqa: BLE001
    print(f"  (dependencia no simulada, no es el bug) {type(e).__name__}: {e}")

# ── 2 · ausencias_ui.render_mis_ausencias ─────────────────────────
from core import ausencias_ui                                     # noqa: E402
from core import ausencias as AU                                  # noqa: E402
print(f"  firma real: render_mis_ausencias{inspect.signature(ausencias_ui.render_mis_ausencias)}")
# ⚠️ `periodo` es un DICT con `origen`/`desde`/`hasta`/`ingreso` (v433), no una tupla:
# con la forma equivocada la función revienta a mitad y el smoke deja de probar el resto.
AU.saldo = lambda g, u, tp: {"ilimitado": False, "usados": 3.0, "restantes": 17.0,
                             "asignados": 20.0,
                             "periodo": {"origen": "aniversario", "desde": "2026-06-23",
                                         "hasta": "2027-06-22", "ingreso": "2026-06-23"}}
for _c in ("mis_ausencias", "listar", "list_ausencias", "de_usuario"):
    if hasattr(AU, _c):
        setattr(AU, _c, lambda *a, **k: [])
try:
    ausencias_ui.render_mis_ausencias()
    print("  OK    render_mis_ausencias ejecuta el bucle de saldo sin excepción")
except (UnboundLocalError,) as e:
    print(f"  FALLO EL BUG SIGUE VIVO → UnboundLocalError: {e}")
    ok = False
except TypeError as e:
    if "not callable" in str(e):
        print(f"  FALLO EL BUG SIGUE VIVO → {e}")
        ok = False
    else:
        print(f"  (dependencia no simulada, no es el bug) TypeError: {e}")
except Exception as e:                                            # noqa: BLE001
    print(f"  (dependencia no simulada, no es el bug) {type(e).__name__}: {e}")

# ── 3 · lo que se pintó, en inglés ────────────────────────────────
_txt = " || ".join(p for p in pintado if p and p.strip())
print(f"\n  {len(pintado)} textos pintados; muestra:")
for p in [x for x in pintado if x and x.strip()][:5]:
    print(f"    {p[:76]!r}")
_es = [w for w in ("Jornada", "abierta", "Tienes fichajes", "Mis ausencias",
                   "vacaciones", "Te quedan") if w in _txt]
if _txt:
    print(f"  español en lo pintado: {_es or 'ninguno'}")
    ok = ok and not _es

print("\n" + ("SMOKE OK" if ok else "SMOKE CON FALLOS"))
sys.exit(0 if ok else 1)
