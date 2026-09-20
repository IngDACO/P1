"""BARRIDO — llamar a lo que llama cada pantalla, con el escenario completo.

No es un test de unidad: es recorrer las funciones que alimentan cada vista con
16 obras, 11 personas, 480 fichajes y dinero de verdad, y mirar qué sale mal.
Todo lo que no cuadre se marca ⚠️ para revisarlo, no se corrige aquí.
"""
import sys
import traceback
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import (projects as P, timeclock as T, expenses as E, finance as F,   # noqa: E402
                  invoices as I, payroll as PR, orders as O, quotes as Q,
                  inventory as INV, admin_digest as AD, alerts as AL)

G = "cliente1"
avisos = []


def probar(nombre, fn):
    """Llama y reporta; un crash aquí es un crash de pantalla."""
    try:
        return fn()
    except Exception as e:
        avisos.append(f"💥 {nombre}: {type(e).__name__}: {e}")
        print(f"   💥 {nombre} REVIENTA: {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)
        return None


print("=" * 78)
print("1. RESUMEN FINANCIERO — los 8 indicadores")
print("=" * 78)
pnl = probar("finance.pnl", lambda: F.pnl(G, None, None))
if pnl:
    for k in ("facturado", "cobrado", "por_cobrar", "vencido", "costo_nomina",
              "costo_compras", "costo_total", "ganancia"):
        v = pnl.get(k)
        print(f"   {k:<16} {v:>14,.2f}" if isinstance(v, (int, float)) else f"   {k:<16} {v}")

sf = probar("finance.sin_facturar", lambda: F.sin_facturar(G))
if sf is not None:
    print(f"\n   sin facturar: {len(sf)} obras")
    for x in sf[:6]:
        print(f"      {x}")

print("\n" + "=" * 78)
print("2. CONCILIACIÓN DE MANO DE OBRA (la cadena de v313)")
print("=" * 78)
c = probar("conciliacion_mo", lambda: F.conciliacion_mo(G, None, None))
if c:
    for k, v in c.items():
        if isinstance(v, (int, float)):
            print(f"   {k:<22} {v:>14,.2f}")
        elif v:
            print(f"   {k:<22} {v}")
    se = abs(float(c.get("sin_explicar") or 0))
    if se > 1:
        avisos.append(f"conciliación: ${se:,.2f} sin explicar (esperable: hay días "
                      "trabajados sin nómina a propósito)")

print("\n" + "=" * 78)
print("3. RENTABILIDAD por obra — los DOS modelos conviviendo")
print("=" * 78)
gp = probar("group_profitability", lambda: F.group_profitability(G))
if gp:
    filas = gp if isinstance(gp, list) else gp.get("filas", [])
    print(f"   {'OBRA':<34}{'MODELO':<9}{'COSTO':>11}{'INGRESO':>11}{'GANA':>10}{'MARGEN':>8}")
    for f in filas:
        nom = str(f.get("nombre", ""))[:32]
        print(f"   {nom:<34}{str(f.get('modelo', '—')):<9}"
              f"{float(f.get('costo') or 0):>11,.0f}{float(f.get('ingreso') or 0):>11,.0f}"
              f"{float(f.get('ganancia') or 0):>10,.0f}{float(f.get('margen') or 0):>7.1f}%")
        if f.get("sin_ganancia"):
            print(f"      ⚠️ sin ganancia puesta (se factura a costo): {f['sin_ganancia']}")

print("\n" + "=" * 78)
print("4. PRESUPUESTOS: gastado vs comprometido")
print("=" * 78)
ge = probar("group_expenses", lambda: E.group_expenses(G))
comp = probar("comprometido_por_proyecto", lambda: O.comprometido_por_proyecto(G))
if ge:
    filas = ge.get("filas", ge if isinstance(ge, list) else [])
    for f in filas:
        p = str(f.get("id", ""))
        cm = float((comp or {}).get(p, 0) or 0)
        pres = float(f.get("presupuesto") or 0)
        tot = float(f.get("total") or 0)
        if not (pres or tot or cm):
            continue
        marca = ""
        if pres and tot > pres:
            marca = "⛔ SOBRE"
        elif pres and (tot + cm) > pres:
            marca = "⚠️ con lo pedido se pasa"
        print(f"   {str(f.get('nombre'))[:30]:<31} gastado {tot:>10,.0f} + comprometido "
              f"{cm:>9,.0f} de {pres:>9,.0f}  {marca}")

print("\n" + "=" * 78)
print("5. NÓMINAS y horas sin pagar")
print("=" * 78)
res = probar("payroll.resumen", lambda: PR.resumen(G))
print(f"   resumen: {res}")
noms = probar("list_nominas", lambda: PR.list_nominas(G)) or []
print(f"   colillas: {len(noms)}")
cero = [n for n in noms if float(n.get("Base") or 0) == 0]
if cero:
    avisos.append(f"⚠️ {len(cero)} colillas con base $0")
    print(f"   ⚠️ colillas con base $0: {[n.get('ID') for n in cero]}")
else:
    print("   ✓ ninguna colilla de $0")

print("\n" + "=" * 78)
print("6. HORAS del grupo")
print("=" * 78)
gh = probar("group_hours", lambda: T.group_hours(G, days=0)) or []
indet = [r for r in gh if r.get("sin_asignar_indet")]
sin_t = [r for r in gh if not float(r.get("tarifa") or 0) and float(r.get("proyecto") or 0) > 0]
print(f"   personas con horas: {sum(1 for r in gh if float(r.get('proyecto') or 0) > 0)}")
print(f"   con «sin asignar» indeterminado: {[r['usuario'] for r in indet]}")
print(f"   con horas y SIN tarifa: {[(r['usuario'], r.get('existe')) for r in sin_t]}")
dup = {}
for r in gh:
    dup.setdefault(str(r.get("nombre")), []).append(str(r.get("usuario")))
part = {n: u for n, u in dup.items() if len(u) > 1}
print(f"   nombres en más de una fila: {part}")
for n, us in part.items():
    reales = {str(x.get('Usuario')) for x in __import__('core.auth', fromlist=['x']).list_users(G)}
    fantasma = [u for u in us if u not in reales]
    if fantasma:
        avisos.append(f"⚠️ «{n}» sigue partida: {us} (fantasma {fantasma})")

print("\n" + "=" * 78)
print("7. RADAR DEL DÍA (los 9 indicadores del admin)")
print("=" * 78)
d = probar("group_digest", lambda: AD.group_digest(G))
if d:
    for k in ("retrasos", "vencidos", "por_vencer", "sin_asignar", "campo_sin_contacto",
              "cred_venc", "alarmas", "near_miss", "sobre_presupuesto"):
        v = d.get(k)
        n = len(v) if isinstance(v, list) else v
        muestra = ""
        if isinstance(v, list) and v:
            muestra = str(v[0])[:60]
        print(f"   {k:<20} {n}   {muestra}")

print("\n" + "=" * 78)
print("8. COTIZACIONES e INVENTARIO")
print("=" * 78)
qr = probar("quotes.resumen", lambda: Q.resumen(G))
print(f"   cotizaciones: {qr}")
for c_ in (probar("list_cotizaciones", lambda: Q.list_cotizaciones(G)) or []):
    print(f"      {c_.get('ID')} {str(c_.get('ClienteNombre'))[:22]:<23} "
          f"${float(c_.get('Total') or 0):>10,.2f}  guardado «{c_.get('Estado')}» "
          f"→ derivado «{Q.estado_de(c_)}»")
ir = probar("inventory.resumen", lambda: INV.resumen(G))
print(f"\n   inventario: {ir}")
al = probar("inventory.alertas", lambda: INV.alertas(G))
print(f"   alertas de inventario: {al}")

print("\n" + "=" * 78)
print("RESULTADO")
print("=" * 78)
if avisos:
    for a in avisos:
        print("  ", a)
else:
    print("   sin incidencias")
