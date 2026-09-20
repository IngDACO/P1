"""Ejercita la ESCRITURA de la ganancia fija sobre el caso que la motivó.

«Bespoke — Delivery Chullora» (PRJ-0014): $380 de costo, $5.200 facturados, y la
app estimaba su ingreso en $380 — o sea, ganancia $0. Es el hueco que v370 dejó
abierto: esa obra se creó A MANO, no desde una cotización.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import projects as P, finance as F, invoices as I   # noqa: E402

PID, G = "PRJ-0014", "cliente1"


def foto(t):
    r = F.project_revenue(PID, G)
    fact = P._num(I.facturado_por_proyecto(G).get(PID, 0))
    pend = P._num(I.pendiente_de_facturar(PID, G))
    print(f"\n   {t}")
    print(f"      modelo            {r.get('modelo')}")
    print(f"      costo             ${P._num(r.get('costo')):>10,.2f}")
    print(f"      ganancia fija     ${P._num(r.get('ganancia_fija')):>10,.2f}")
    print(f"      ingreso estimado  ${P._num(r.get('ingreso')):>10,.2f}")
    print(f"      ganancia          ${P._num(r.get('ganancia')):>10,.2f}")
    print(f"      ya facturado      ${fact:>10,.2f}")
    print(f"      pendiente         ${pend:>10,.2f}")
    return r, fact, pend


print("=" * 70)
print("ANTES")
print("=" * 70)
r0, fact, pend0 = foto("PRJ-0014 · Bespoke — Delivery Chullora")
costo = P._num(r0.get("costo"))
print(f"\n   ⚠️ La obra se facturó en ${fact:,.2f} y la app la estimaba en "
      f"${P._num(r0.get('ingreso')):,.2f}.")
print(f"      Si estuviera sin facturar, «por cobrar» diría ${P._num(r0.get('ingreso')):,.2f} "
      f"en vez de ${fact:,.2f}.")

# La ganancia fija que hace que la estimación cuadre con lo que de verdad se cobró.
fija = round(fact - costo, 2)
print(f"\n   ganancia fija = facturado − costo = {fact:,.2f} − {costo:,.2f} = ${fija:,.2f}")

print("\n" + "=" * 70)
print("ESCRIBIR")
print("=" * 70)
ok, msg = P.set_ganancia_fija(PID, fija)
print(f"   set_ganancia_fija → {ok} · {msg}")

P._invalidate()
r1, fact1, pend1 = foto("DESPUÉS")

bien = abs(P._num(r1.get("ingreso")) - fact) < 0.01 and abs(pend1) < 0.01
print(f"\n   {'✓' if bien else '✗'} el ingreso estimado coincide ya con lo facturado, "
      f"y el pendiente baja a ${pend1:,.2f}")

# ── la vuelta atrás tiene que existir (regla v340) ──────────────────
print("\n" + "=" * 70)
print("LA VUELTA ATRÁS (poner 0 la quita)")
print("=" * 70)
P.set_ganancia_fija(PID, 0)
P._invalidate()
r2 = F.project_revenue(PID, G)
vuelve = abs(P._num(r2.get("ingreso")) - P._num(r0.get("ingreso"))) < 0.01
print(f"   ingreso con fija=0 → ${P._num(r2.get('ingreso')):,.2f}  "
      f"{'✓ vuelve EXACTAMENTE al valor de antes' if vuelve else '✗'}")
print(f"   modelo → {r2.get('modelo')}  (sin rastro de la fija)")

# ── se deja puesta: es el número correcto para esta obra ────────────
P.set_ganancia_fija(PID, fija)
P._invalidate()
r3 = F.project_revenue(PID, G)
print(f"\n   se deja en ${P._num(r3.get('ganancia_fija')):,.2f} · "
      f"ingreso ${P._num(r3.get('ingreso')):,.2f} · modelo {r3.get('modelo')}")

# ── el histórico de auditoría lo registró ───────────────────────────
print("\n" + "=" * 70)
print("¿QUEDÓ RASTRO? (la razón de meterlo en CAMPOS_CLAVE)")
print("=" * 70)
try:
    from core import auditoria as AU
    for h in AU.historial("proyecto", PID)[:4]:
        print(f"   {h.get('Fecha')}  {h.get('Usuario')}  {str(h.get('Cambios'))[:96]}")
except Exception as e:
    print(f"   no se pudo leer el histórico: {e}")

sys.exit(0 if bien and vuelve else 1)
