"""SIMULACIÓN etapa B — las obras.

9 obras nuevas de una instaladora de Sídney, con los CASOS LÍMITE que las
pantallas nunca han visto (cada uno señalado con ⚠️ abajo):

  ⚠️ VENCIDA   — fin estimado ya pasado y sin llegar al 100% (la rama que v324
                 descubrió MUERTA: «la fecha de fin ya pasó» era inalcanzable).
  ⚠️ SIN AVANCE— empezó hace semanas y sigue en 0% (la otra rama de v324, la que
                 daba el mensaje MÁS tranquilo al proyecto que peor iba).
  ⚠️ FUTURA    — aún no arranca (no debe salir «en retraso»).
  ⚠️ COMPLETADAS — dos al 100%, para que «ganancia real» deje de ser proyectada.
  ⚠️ 3 torres del mismo edificio → agrupación: la entrega del conjunto la marca
                 la más lenta, no el promedio.
  ⚠️ Mezcla de modelos: unas con ganancia por rubro (v360), otras con margen %,
                 otras SIN margen propio (heredan el 20% del grupo).

Las fechas reales de las actividades se corrigen al final en UN batch: el flujo
normal las pone a HOY (v162), correcto para el campo pero irreal para una obra
que empezó en junio — dejaría la curva S plana.
"""
import sys
import time
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import projects as P, clientes as C, credentials as CR   # noqa: E402

G = "cliente1"
HOY = date(2026, 8, 18)

CLI = {str(c.get("Nombre", "")): str(c.get("ID", ""))
       for c in C.list_clientes(G, incluir_inactivos=True)}

# el catálogo de credenciales manda: no inventar el texto del certificado
_cat = [str(x) for x in (getattr(CR, "CATALOGO", []) or [])]
def cert(*claves):
    out = []
    for k in claves:
        hit = next((c for c in _cat if k.casefold() in c.casefold()), None)
        if hit:
            out.append(hit)
    return ";".join(out)

# nombre, cliente, tipo, ns, inicio, fin, ppto, avance%, equipo, lat, lng, margen, certs
OBRAS = [
    ("Meriton Zetland — Torre A", "Meriton Apartments", "Instalación", 8,
     "2026-06-01", "2026-10-30", 48000, 62, ["jlopez", "mchen", "apatel"],
     -33.9067, 151.2094, "", ""),
    ("Meriton Zetland — Torre B", "Meriton Apartments", "Instalación", 8,
     "2026-06-15", "2026-11-15", 48000, 45, ["jlopez", "tobrien"],
     -33.9071, 151.2101, "", ""),
    ("Meriton Zetland — Torre C", "Meriton Apartments", "Instalación", 8,
     "2026-07-06", "2026-12-04", 48000, 18, ["mchen2", "nsanchez"],
     -33.9075, 151.2088, 22, ""),
    # ⚠️ VENCIDA: el fin estimado pasó hace 4 días y va por el 70%
    ("Stockland Wetherill Park — Ripout", "Stockland Retail", "Ripout", 0,
     "2026-07-20", "2026-08-14", 12000, 70, ["tobrien", "apatel"],
     -33.8489, 150.9047, "", ""),
    # ⚠️ FUTURA: arranca en septiembre, no debe contarse como retrasada
    ("Stockland Wetherill Park — Instalación", "Stockland Retail", "Instalación", 6,
     "2026-09-08", "2027-01-15", 62000, 0, ["jlopez", "mchen", "tobrien"],
     -33.8491, 150.9051, "", ""),
    ("RNSH Lift 4 — Modernización", "NSW Health Infrastructure", "Otro", 0,
     "2026-05-04", "2026-09-30", 38000, 55, ["campo1", "apatel", "mchen"],
     -33.8236, 151.1936, "", cert("White Card", "Heights")),
    # ⚠️ SIN AVANCE: empezó hace 2 semanas y sigue en 0%
    ("RNSH Lift 5 — Modernización", "NSW Health Infrastructure", "Otro", 0,
     "2026-08-03", "2026-12-18", 38000, 0, ["nsanchez"],
     -33.8240, 151.1941, "", cert("White Card")),
    # ⚠️ COMPLETADAS
    ("Bespoke — Delivery Chullora", "Bespoke Lifts Pty Ltd", "Delivery", 0,
     "2026-07-27", "2026-07-31", 4500, 100, ["tobrien"],
     -33.8925, 151.0453, "", ""),
    ("Meriton Rhodes — Survey", "Meriton Apartments", "Otro", 0,
     "2026-08-10", "2026-08-12", 1200, 100, ["dmoreno"],
     -33.8305, 151.0872, "", ""),
]

print("== B1. crear obras ==")
ya = {str(p.get("Nombre", "")) for p in P.list_projects(G, incluir_archivados=True)}
# ⚠️ el equipo se valida contra quien existe de VERDAD: asignar a un usuario
# inventado dejaría la obra con un fantasma en CampoAsignados (el caso `de_baja`
# de v325, que no se puede resolver desde ninguna pantalla)
from core import auth as _auth                                    # noqa: E402
_reales = {str(u.get("Usuario", "")) for u in _auth.list_users(G)}
creados = {}
for (nom, cliente, tipo, ns, ini, fin, ppto, av, equipo, lat, lng, margen, certs) in OBRAS:
    if nom in ya:
        pid = next(str(p.get("ID")) for p in P.list_projects(G, incluir_archivados=True)
                   if str(p.get("Nombre")) == nom)
        creados[nom] = (pid, av)
        print(f"   {nom[:38]:<39} ya existe ({pid})")
        continue
    _falsos = [u for u in equipo if u not in _reales]
    if _falsos:
        print(f"      ⚠️ se descartan (no existen): {_falsos}")
        equipo = [u for u in equipo if u in _reales]
    ok, res = P.create_project(
        G, nom, cliente=cliente, ubicacion="Sydney NSW", modelo="Schindler 5500",
        ns=ns, ingeniero="Diego Moreno", campo_asignados=equipo,
        fecha_inicio=ini, fecha_fin_est=fin, creado_por="dmoreno",
        presupuesto=ppto, lat=lat, lng=lng, certs_req=certs,
        cliente_id=CLI.get(cliente, ""), margen_mo=margen, tipo=tipo)
    print(f"   {nom[:38]:<39} {tipo:<12} {'OK ' + str(res) if ok else '⚠️ ' + str(res)}")
    if ok:
        creados[nom] = (str(res), av)
    time.sleep(0.6)

# ── B2. avance por actividad (1 escritura por obra) ─────────────
print("\n== B2. avance ==")
for nom, (pid, objetivo) in creados.items():
    acts = P.list_activities(pid)
    if not acts or objetivo <= 0:
        print(f"   {nom[:38]:<39} {objetivo:>3}%  (sin tocar)")
        continue
    # se llenan las actividades EN ORDEN hasta alcanzar el % objetivo: es como
    # avanza una obra de verdad (no todas al mismo porcentaje a la vez)
    pesos = [float(str(a.get("Peso", 0) or 0)) for a in acts]
    total = sum(pesos) or 1.0
    restante = objetivo * total / 100.0
    cambios = []
    for a, w in zip(acts, pesos):
        if restante <= 0:
            av = 0
        elif restante >= w:
            av = 100
            restante -= w
        else:
            av = int(round(restante / w * 100)) if w else 0
            restante = 0
        cambios.append({"orden": a.get("Orden"), "avance": av})
    ok, msg = P.save_field_progress(pid, cambios)
    P._invalidate()
    real = P.get_project(pid).get("Avance")
    print(f"   {nom[:38]:<39} objetivo {objetivo:>3}% → real {real}%  {'OK' if ok else msg}")
    time.sleep(0.6)

print("\n== B3. estado final ==")
for p in P.list_projects(G, incluir_archivados=True):
    pid = str(p.get("ID"))
    print(f"   {pid:<9} {str(p.get('Nombre'))[:36]:<37} {str(p.get('Estado')):<12} "
          f"{str(p.get('Avance')):>5}%  {str(p.get('Tipo') or '—'):<12} fin={p.get('FechaFinEst')}")
