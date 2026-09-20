"""GUARDIÁN v370 — el ingreso de una obra cotizada es el PRECIO PACTADO.

Una obra cuyo valor no está en las horas valía exactamente lo que costó: los materiales
van a costo en los DOS modelos, así que un delivery o un suministro salían con ganancia
$0. Y la app **ya tenía** el número bueno: la cotización aceptada guarda su `ProyectoID`.

⚠️ La base es el **Subtotal** (sin impuesto), porque `facturado_por_proyecto` suma los
importes de línea, también sin impuesto. Mezclarlas rompería `pendiente_de_facturar`.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrator"}

from core import finance as F, quotes as Q, invoices as I, projects as P, expenses as E  # noqa: E402

G = "cliente1"
ok = True

print("== 1. el enlace proyecto → cotización aceptada ==")
pares = [(str(c.get("ProyectoID")), str(c.get("ID")), _s := c) for c in Q.list_cotizaciones(G)
         if str(c.get("ProyectoID", "")).strip()]
for pid, cid, c in pares:
    hallado = Q.cotizacion_de_proyecto(pid)
    bien = str(hallado.get("ID", "")) == cid
    ok &= bien
    print(f"   {pid} → {cid}  {'✓' if bien else '✗'}  (subtotal ${float(c.get('Subtotal') or 0):,.2f})")
print(f"   proyecto SIN cotización → {Q.cotizacion_de_proyecto('PRJ-0001') or '{} ✓'}")
ok &= not Q.cotizacion_de_proyecto("PRJ-0001")
print(f"   pid vacío → {Q.cotizacion_de_proyecto('') or '{} ✓'}")

print("\n== 2. el ingreso pasa a ser el pactado ==")
for pid, cid, c in pares:
    r = F.project_revenue(pid, G)
    sub = float(c.get("Subtotal") or 0)
    bien = r.get("modelo") == "cotizado" and abs(float(r.get("ingreso") or 0) - sub) < 0.01
    ok &= bien
    print(f"   {pid}  modelo={r.get('modelo'):<9} ingreso ${float(r.get('ingreso') or 0):>9,.2f} "
          f"(pactado ${sub:,.2f})  costo ${float(r.get('costo') or 0):>8,.2f}  "
          f"ganancia ${float(r.get('ganancia') or 0):>9,.2f}  {'✓' if bien else '✗'}")
    print(f"      cotización citada: {r.get('cotizacion')}")

print("\n== 3. ⚠️ MISMA BASE que lo facturado (sin impuesto) ==")
# Si se hubiera usado el Total con GST, `pendiente` saldría inflado justo en el impuesto.
for pid, cid, c in pares:
    r = F.project_revenue(pid, G)
    fact = float(I.facturado_por_proyecto(G).get(pid, 0) or 0)
    pend = float(I.pendiente_de_facturar(pid, G) or 0)
    esperado = max(0.0, float(r.get("ingreso") or 0) - fact)
    bien = abs(pend - esperado) < 0.02
    ok &= bien
    print(f"   {pid}  ingreso ${float(r.get('ingreso') or 0):,.2f} − facturado ${fact:,.2f} "
          f"= pendiente ${pend:,.2f}  {'✓' if bien else '✗ esperaba ' + format(esperado, ',.2f')}")
    print(f"      (si se hubiera usado el Total con GST: ${float(c.get('Total') or 0):,.2f} → "
          f"pendiente inflado en ${float(c.get('Impuesto') or 0):,.2f})")

print("\n== 4. las obras SIN cotización no cambian ==")
for pid in ("PRJ-0001", "PRJ-0007", "PRJ-0010", "PRJ-0014"):
    r = F.project_revenue(pid, G)
    m = str(r.get("modelo") or "")
    # ⚠️ v373 añadió las variantes «+fija». Lo que este caso protege es que una obra
    #    SIN cotización no use el modelo cotizado, no la lista literal de modelos:
    #    fijar los nombres exactos convertiría cada modelo nuevo en un falso fallo.
    # ⚠️ v455: «margen» desapareció; una obra sin cotización usa rubro, fija o a_costo.
    bien = m.startswith("rubro") or m in ("fija", "a_costo")
    ok &= bien
    print(f"   {pid}  modelo={m:<9} ingreso ${float(r.get('ingreso') or 0):>9,.2f}  "
          f"{'✓ intacto' if bien else '✗'}")

print("\n== 5. el `except` NO revienta si las cotizaciones fallan ==")
# ⚠️ Ahí dentro había un `logger` que no existía en el módulo: un NameError escondido
#    justo donde nadie mira. Se fuerza el fallo para ejercitar esa rama de verdad.
_orig = Q.cotizacion_de_proyecto
Q.cotizacion_de_proyecto = lambda pid: (_ for _ in ()).throw(RuntimeError("Sheets caído"))
try:
    r = F.project_revenue("PRJ-0016", G)
    print(f"   con las cotizaciones caídas → modelo={r.get('modelo')} "
          f"ingreso ${float(r.get('ingreso') or 0):,.2f}  ✓ degrada sin romper")
except Exception as e:
    print(f"   ‼️ REVIENTA: {type(e).__name__}: {e}")
    ok = False
finally:
    Q.cotizacion_de_proyecto = _orig

print("\n" + ("✅ v370 OK: el precio pactado manda, misma base sin impuesto, el resto "
              "intacto y degrada si falla" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
