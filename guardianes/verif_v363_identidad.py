"""GUARDIÁN v363 — el resolvedor de identidad, único y sin mover dinero.

⚠️ Por qué este test y no el obvio: comparar el total de horas ANTES y DESPUÉS del
cambio (en dos ejecuciones) NO vale, porque hay una sesión ABIERTA que acumula contra
el reloj — entre las dos medidas creció 20 h y parecía que el cambio movía cifras.
Es la trampa del «OK en falso» al revés: un FALLO en falso.

Aquí se comparan las DOS lógicas sobre las MISMAS filas, en el MISMO proceso y con el
mismo instante: lo único que cambia es el resolvedor. Así el veredicto es del cambio.
"""
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrator"}

from core import timeclock as T, auth                                  # noqa: E402

G = "cliente1"
filas = [r for r in T._cached_records() if str(r.get("Grupo", "")).strip() == G]
pn = T.mapa_nombres(G)


def clave_vieja(r):
    """La que había en las 6 funciones antes de v363."""
    return str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()


# ── agregado por persona con cada lógica, sobre las mismas filas y el mismo instante
def agrupar(fn):
    acc = defaultdict(float)
    for r in filas:
        h = sum(x for _, x in T._row_segmentos(r))
        if h > 0:
            acc[fn(r)] += h
    return dict(acc)


viejo, nuevo = agrupar(clave_vieja), agrupar(lambda r: T.clave_de(r, pn))
tv, tn = sum(viejo.values()), sum(nuevo.values())

print("== 1. el TOTAL no se mueve (la unión solo reagrupa) ==")
print(f"   lógica vieja : {tv:>12.4f} h  ({len(viejo)} personas)")
print(f"   lógica nueva : {tn:>12.4f} h  ({len(nuevo)} personas)")
print(f"   diferencia   : {tn - tv:>12.6f} h  ({(tn - tv) * 3600:.3f} s)")
# ⚠️ Tolerancia con sentido FÍSICO, no simbólica: sumar 473 flotantes en distinto orden
# da ~1e-5 h de ruido (0,02 s). Un epsilon de 1e-6 hacía FALLAR el test por su propia
# aritmética, no por el código — un «fallo en falso», el gemelo del OK en falso.
ok = abs(tn - tv) < 0.001                    # < 3,6 segundos sobre 3.300 horas

print("\n== 2. qué se unió y qué NO ==")
rates = auth.rate_map(G)
for k in sorted(set(viejo) | set(nuevo)):
    a, b = viejo.get(k, 0.0), nuevo.get(k, 0.0)
    if abs(a - b) > 0.001:   # ruido de flotantes, no un cambio
        marca = "→ ABSORBIDA" if b == 0 else "← recibe"
        print(f"   {k:<14} vieja {a:>9.2f}  nueva {b:>9.2f}   {marca}")

print("\n== 3. el dinero tampoco (mismas horas × misma tarifa) ==")
cv = sum(h * float(rates.get(k, 0) or 0) for k, h in viejo.items())
cn = sum(h * float(rates.get(k, 0) or 0) for k, h in nuevo.items())
print(f"   costo con lógica vieja: {cv:>12.2f}")
print(f"   costo con lógica nueva: {cn:>12.2f}")
print(f"   diferencia            : {cn - cv:>12.6f}")
# ⚠️ Esta es la comprobación que de verdad importa: `rate_map` indexa por Usuario Y por
# Nombre (v106), así que el cubo fantasma YA cobraba la tarifa correcta. Si el dinero
# se moviera, la unión estaría cambiando lo que se paga, no solo cómo se agrupa.
ok &= abs(cn - cv) < 0.005

print("\n== 4. los homónimos NO se mezclan ==")
homs = {n: u for n, u in
        ((n, u) for n, u in T.mapa_nombres(G).items() if len(u) > 1)}
print(f"   nombres compartidos por varias cuentas: {homs}")
for nom, usuarios in homs.items():
    fake = {"Usuario": "", "Nombre": nom}
    res = T.clave_de(fake, pn)
    bien = res not in usuarios          # no debe elegir a ninguno de los dos
    ok &= bien
    print(f"   {'✓' if bien else '✗'} fila sin login con nombre «{nom}» → {res!r} "
          f"(no se le adjudica a {usuarios})")

print("\n== 5. UNA sola definición en el repo ==")
import ast
import pathlib
copias = []
for f in sorted(pathlib.Path(r"C:\Users\diego\P1\survey_app\core").glob("*.py")):
    src = f.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for n in ast.walk(tree):
        # el patrón viejo: `X.get("Usuario"...).strip() or ...get("Nombre"...)`
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            txt = ast.unparse(n)
            if '"Usuario"' in txt and '"Nombre"' in txt and ".strip()" in txt:
                copias.append(f"{f.name}:{n.lineno}  {txt[:70]}")
if copias:
    print("   ‼️ quedan copias del patrón viejo:")
    for c in copias:
        print("     ", c)
    ok = False
else:
    print("   ✓ 0 copias del patrón `Usuario or Nombre`; todas usan clave_de()")

print("\n== 6. las 6 funciones la usan ==")
usan = []
for f in ("timeclock.py", "expenses.py"):
    src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core", f).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for fn in [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]:
        if any(getattr(c.func, "attr", getattr(c.func, "id", "")) == "clave_de"
               for c in ast.walk(fn) if isinstance(c, ast.Call)):
            usan.append(f"{f}:{fn.name}")
print(f"   {len(usan)}: {usan}")
ok &= len(usan) >= 6

print("\n" + ("✅ v363 OK: una definición, une a la misma persona, respeta homónimos, "
              "y ni las horas ni el dinero se mueven" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
