"""Siembra la planificación de ESTA semana + credenciales, para poder probar la app.

Medido antes: la semana en curso tenía **0 asignaciones** y el catálogo de trabajos
**0 entradas**, así que Panel, vista Día, Libres, Cumplimiento, Ruta del día y la
agenda de HOME no tenían nada que enseñar. Y de 13 personas solo había 2 credenciales,
con lo que el semáforo y la matriz de cumplimiento tampoco se podían ejercitar.

⚠️ No se siembra ruido: cada fila existe para que una pantalla concreta tenga su caso.
    · dos obras el MISMO día      → la vista del día con carriles (v387)
    · un SOLAPE de franjas        → el radar de choques de turno (v292)
    · OFF y Leave                 → la vista Libres
    · un SÁBADO trabajado         → la columna extra de v390
    · alguien SIN asignar         → la cobertura y el «sin plan» de la Ruta del día
    · credenciales en los 3 estados → semáforo vigente / por vencer / vencida

En seco por defecto; `--apply` escribe.
"""
import datetime as dt
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import auth, clock, credentials as CR, projects as P, roster as R  # noqa: E402

G = "cliente1"
APLICAR = "--apply" in sys.argv
HOY = clock.today(G)
LUNES = R.lunes_de(HOY)
T0, T1 = R.TURNO_DEFAULT                     # ("07:00", "15:30")


def item(asig, ini="", fin=""):
    return {"a": asig, "i": ini, "f": fin}


def dia(*items, nota=""):
    return {"items": list(items), "nota": nota}


# ── a quién y a qué ─────────────────────────────────────────────────────────
campo = [str(u.get("Usuario")) for u in auth.list_users()
         if str(u.get("Rol")) == "campo" and str(u.get("Grupo")) == G]
activos = [p for p in P.list_projects(G)
           if str(p.get("Estado")) not in ("Archivado", "Cancelado", "Completado")]
pids = [str(p.get("ID")) for p in activos]
print(f"{len(campo)} de campo · {len(pids)} obras activas")
if len(campo) < 6 or len(pids) < 4:
    print("no hay material suficiente para sembrar con sentido")
    sys.exit(2)

A, B, C, D = pids[0], pids[1], pids[2], pids[3]
E = pids[4] if len(pids) > 4 else A

# ── catálogo de trabajos que NO son obra ────────────────────────────────────
TRABAJOS = [("90", "Traslado de material", R.PALETA[1][1]),
            ("91", "Curso TAFE", R.PALETA[5][1]),
            ("92", "Entrega en bodega", R.PALETA[3][1]),
            ("93", "Mantenimiento de equipo", R.PALETA[7][1])]

print("\n== catálogo de trabajos ==")
ids_trab = {}
existentes = {str(t.get("Nombre")): str(t.get("ID")) for t in R.list_trabajos(G)}
for num, nom, col in TRABAJOS:
    if nom in existentes:
        ids_trab[nom] = existentes[nom]
        print(f"  ya está   {nom}")
        continue
    if not APLICAR:
        print(f"  (seco)    {nom}")
        continue
    ok, msg = R.add_trabajo(G, num, nom, col, "")
    nuevo = {str(t.get("Nombre")): str(t.get("ID")) for t in R.list_trabajos(G)}
    ids_trab[nom] = nuevo.get(nom, "")
    print(f"  {'ok' if ok else 'FALLO'}       {nom} → {ids_trab.get(nom)} · {msg}")

TAFE = ids_trab.get("Curso TAFE", "FORMACION")
TRAS = ids_trab.get("Traslado de material", "")

# ── la semana ───────────────────────────────────────────────────────────────
# ⚠️ Cada persona cubre un caso distinto a propósito (ver el docstring).
SEMANA = {
    campo[0]: {                                   # dos obras el MISMO martes
        "lun": dia(item(A, T0, T1)),
        "mar": dia(item(A, "07:00", "11:00"), item(B, "11:30", "15:30"),
                   nota="cambia de obra a media mañana"),
        "mie": dia(item(A, T0, T1)),
        "jue": dia(item(A, T0, T1)),
        "vie": dia(item(A, T0, T1)),
    },
    campo[1]: {                                   # SOLAPE el miércoles
        "lun": dia(item(B, T0, T1)),
        "mar": dia(item(B, T0, T1)),
        "mie": dia(item(B, T0, T1), item(C, "13:00", "17:00"),
                   nota="⚠️ se pisa: dos obras a la vez"),
        "jue": dia(item(B, T0, T1)),
        "vie": dia(item(B, T0, T1)),
    },
    campo[2]: {                                   # un día OFF
        "lun": dia(item(C, T0, T1)),
        "mar": dia(item(C, T0, T1)),
        "mie": dia(item("OFF")),
        "jue": dia(item(D, T0, T1)),
        "vie": dia(item(D, T0, T1)),
    },
    campo[3]: {                                   # de baja toda la semana
        d: dia(item("LEAVE")) for d in ("lun", "mar", "mie", "jue", "vie")
    },
    campo[4]: {                                   # trabaja el SÁBADO
        "lun": dia(item(D, T0, T1)),
        "mar": dia(item(D, T0, T1)),
        "mie": dia(item(D, T0, T1)),
        "jue": dia(item(D, T0, T1)),
        "sab": dia(item(D, "08:00", "13:00"), nota="refuerzo de fin de semana"),
    },
    campo[5]: {                                   # curso + obra
        "lun": dia(item(E, T0, T1)),
        "mar": dia(item(TAFE, "08:00", "16:00")) if TAFE else dia(item("FORMACION")),
        "mie": dia(item(E, T0, T1)),
        "jue": dia(item(TAFE, "08:00", "16:00")) if TAFE else dia(item("FORMACION")),
        "vie": dia(item(TRAS, "07:00", "12:00")) if TRAS else dia(item(E, T0, T1)),
    },
}
if len(campo) > 7:
    SEMANA[campo[7]] = {d: dia(item(E, T0, T1))
                        for d in ("lun", "mar", "mie", "jue", "vie")}
# campo[6] se queda SIN asignar a propósito → cobertura y «sin plan» de la Ruta

print(f"\n== semana del {LUNES} ==")
for usr, dias in SEMANA.items():
    n = sum(len(d["items"]) for d in dias.values())
    print(f"  {usr:<12} {len(dias)} días · {n} asignaciones"
          + ("" if APLICAR else "   (seco)"))
    if APLICAR:
        ok, msg = R.guardar_persona(G, LUNES, usr, dias)
        if not ok:
            print(f"     FALLO: {msg}")
if len(campo) > 6:
    print(f"  {campo[6]:<12} SIN asignar (a propósito)")

# ── credenciales con los tres estados ───────────────────────────────────────
print("\n== credenciales ==")
CREDS = [(campo[0], "White Card", HOY + dt.timedelta(days=400)),      # vigente
         (campo[1], "Working at Heights", HOY + dt.timedelta(days=15)),  # por vencer
         (campo[2], "EWP / Boom (WP)", HOY - dt.timedelta(days=20)),  # VENCIDA
         (campo[3], "First Aid", HOY + dt.timedelta(days=90)),
         (campo[4], "Forklift (LF)", HOY + dt.timedelta(days=25))]    # por vencer
for usr, tipo, venc in CREDS:
    ya = [c for c in CR.list_for(usr) if str(c.get("Tipo")) == tipo]
    estado = CR.status(venc.isoformat())
    if ya:
        print(f"  ya está   {usr:<10} {tipo:<20} ({estado})")
        continue
    if not APLICAR:
        print(f"  (seco)    {usr:<10} {tipo:<20} vence {venc} → {estado}")
        continue
    ok, msg = CR.add(usr, G, tipo, numero=f"SIM-{usr[:4].upper()}",
                     emision=(venc - dt.timedelta(days=365)).isoformat(),
                     vencimiento=venc.isoformat(), actualizado_por="dmoreno")
    print(f"  {'ok' if ok else 'FALLO'}       {usr:<10} {tipo:<20} → {estado} · {msg}")

if not APLICAR:
    print("\n(en seco: no se ha escrito nada — repetir con --apply)")
    sys.exit(0)

# ── verificación: se LEE de vuelta ──────────────────────────────────────────
print("\n== verificación ==")
datos = R.get_semana(G, LUNES)
tot = conhora = solapes = 0
for usr in datos:
    for d in R.DIAS_TODOS:
        for it in R.celda_items(datos, usr, d):
            tot += 1
            if it.get("ini"):
                conhora += 1
print(f"  {len(datos)} personas con fila · {tot} asignaciones · {conhora} con franja")
print(f"  trabajos del catálogo: {len(R.list_trabajos(G))}")
_est = {}
for usr in campo:
    for c in CR.list_for(usr):
        _est[CR.status(str(c.get("Vencimiento", "")))] = \
            _est.get(CR.status(str(c.get("Vencimiento", ""))), 0) + 1
print(f"  credenciales por estado: {_est}")
