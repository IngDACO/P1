# -*- coding: utf-8 -*-
"""Guardián de v450: las CABECERAS DE TABLA y los mapas de estado hechos a mano.

## Qué protege

1. **Ninguna cabecera de tabla se pinta en español.** Streamlit pinta la CLAVE del
   dict salvo que `column_config` le dé etiqueta, y las filas de esta app se
   construyen a mano — así que la cabecera se escapó de las cinco redes anteriores,
   que miran POSICIÓN o IDIOMA pero nunca claves.
2. **La clave NO se renombra.** El arreglo es la etiqueta; renombrar rompería las
   lecturas (`r["Elevador"]`, `r["Peso"]`) y lo que viaja a `DatosJSON`.
3. **No vuelve a haber un mapa de estado hecho a mano** que traduzca un valor a sí
   mismo (`{"vigente": "vigente"}`). Aparecieron TRES el mismo día
   (`_cumplimiento_equipo`, `auth_ui._ico`, `credentials.status_label`): los tres son
   anteriores a `i18n.VALORES` y los tres dejaban celdas en español bajo una leyenda
   ya traducida.
4. **Ningún `t()` a nivel de módulo**, que se congela al importar (van seis).

⚠️ Se EJECUTA lo que se puede: importar no ejecuta (v378), y de los tres fallos de
esta versión dos solo se ven llamando a la función.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

from medir_cabeceras import analiza                                # noqa: E402
from core.tabla import CABECERAS, cfg                              # noqa: E402
from core import i18n                                             # noqa: E402
import subprocess                                                  # noqa: E402

UI = sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"])
TODOS = sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"])
fallos = []


def ck(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        fallos.append(msg)


print("== 1. Ninguna cabecera de tabla en español ==")
_pend = []
for f in UI:
    for fname, ln, cab in analiza(f):
        _pend += [f"{f.name}:{ln} {fname}() {c}" for _l, c in cab]
ck(not _pend, f"cabeceras españolas sin traducir: {len(_pend)} {_pend[:4]}")

print("\n== 2. `tabla.cfg` traduce la ETIQUETA y NO toca la clave ==")
_c = cfg([{"Cliente": 1, "Horas": 2, "Zzz": 3}])
ck(set(_c) == {"Cliente", "Horas"}, "solo configura las cabeceras conocidas")
ck("Zzz" not in _c, "lo que no está en el mapa se deja como está")
_lbl = {k: getattr(v, "label", None) or getattr(v, "_label", None) for k, v in _c.items()}
ck(all(isinstance(k, str) for k in _c), "las CLAVES siguen siendo las originales")
_full = cfg()
ck(len(_full) == len(CABECERAS),
   f"sin argumentos devuelve el mapa entero ({len(_full)} columnas)")

print("\n== 3. Ningún mapa de estado que traduzca un valor a sí mismo ==")
_espejo = []
for f in TODOS:
    # ⚠️ `i18n.py` ES el diccionario: ahí «Delivery»→«Delivery» y «Ripout»→«Ripout»
    # son correctos (la palabra es la misma en los dos idiomas), no un mapa espejo.
    if f.name == "i18n.py":
        continue
    tr = ast.parse(f.read_text(encoding="utf-8"))
    for n in ast.walk(tr):
        if not isinstance(n, ast.Dict):
            continue
        for k, v in zip(n.keys, n.values):
            if (isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
                    and isinstance(k.value, str) and isinstance(v.value, str)
                    and k.value in i18n.VALORES and k.value == v.value):
                _espejo.append(f"{f.name}:{k.lineno} {k.value!r}")
ck(not _espejo, f"mapas espejo (valor→sí mismo): {_espejo}")

print("\n== 4. `credentials.status_label` devuelve el estado TRADUCIDO ==")
from core import credentials as C                                  # noqa: E402
from datetime import date, timedelta                               # noqa: E402
_hoy = date.today()
_lab_vig = C.status_label((_hoy + timedelta(days=200)).isoformat())
_lab_pv = C.status_label((_hoy + timedelta(days=10)).isoformat())
_lab_ven = C.status_label((_hoy - timedelta(days=10)).isoformat())
print(f"    vigente={_lab_vig!r}  por_vencer={_lab_pv!r}  vencido={_lab_ven!r}")
ck("vigente" not in _lab_vig, "«vigente» ya no sale en crudo")
ck("por vencer" not in _lab_pv, "«por vencer» ya no sale en crudo")
ck("vencido" not in _lab_ven, "«vencido» ya no sale en crudo")
# ⚠️ el DATO no cambia: `status()` sigue devolviendo el valor español que se compara
ck(C.status((_hoy + timedelta(days=200)).isoformat()) == "vigente",
   "el DATO (`status`) sigue en español, que es lo que se compara")

print("\n== 5. Ningún `t()` que se congele al importar ==")
# ⚠️ Se REUSA el barrido de v445 en vez de reescribirlo: mi primera versión hacía
# `ast.walk` sobre `tr.body` y por tanto DESCENDÍA dentro de los `def` — el mismo
# autoengaño de v342 —, así que denunciaba 3.000 llamadas perfectamente normales.
_r = subprocess.run([sys.executable, str(AQUI / "barre_t_modulo.py")],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", cwd=str(RAIZ))
_sal = (_r.stdout or "") + (_r.stderr or "")
ck("0 llamadas al motor que se CONGELAN" in _sal,
   f"t() a nivel de módulo: {_sal.strip().splitlines()[-1] if _sal.strip() else 'sin salida'}")

print("\n== 6. Ninguna rama muerta por traducir una opción que se compara ==")
# ⚠️ Mi primera versión miraba «el literal sigue en el fichero» y ESCAPABA: sigue
# estando… en la comparación. Es exactamente el fallo que v449 ya había cometido con
# los IDs de sub-pestaña. El invariante correcto es el de v442 —lo comparado tiene
# que salir de las OPCIONES de ese widget—, así que se reusa su guardián en vez de
# escribir uno flojo al lado.
_r6 = subprocess.run([sys.executable, str(AQUI / "verif_ramas_muertas.py")],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace", cwd=str(RAIZ))
print("    " + ((_r6.stdout or "").strip().splitlines() or ["sin salida"])[-1])
ck(_r6.returncode == 0, "sin ramas muertas")

print("\n== 7. `_est_lbl` / `_est_fmt` traducen al PINTAR, no al importar ==")
from core import inventory_ui as IU                                # noqa: E402
from core import quotes_ui as QU                                   # noqa: E402
ck("disponible" not in IU._est_lbl("disponible"),
   f"inventario: {IU._est_lbl('disponible')!r} sin español")
ck("borrador" not in QU._est_fmt("borrador"),
   f"cotización: {QU._est_fmt('borrador')!r} sin español")

print("\n" + ("TODO OK" if not fallos else f"{len(fallos)} FALLO(S)"))
sys.exit(1 if fallos else 0)
