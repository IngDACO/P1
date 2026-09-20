"""Tres semanas de planificación: la pasada, la actual (ya sembrada) y la siguiente.

⚠️ La semana PASADA se siembra MIRANDO los fichajes reales, no al azar. Es la única
donde el plan se puede contrastar con la realidad, y de eso vive la pantalla de
Cumplimiento — que necesita sus tres estados para poder probarse:
    🟢 fichó donde tocaba · 🔴 fichó en OTRA obra · ⚠️ no fichó
Sembrar la semana pasada sin mirar los fichajes daría 8 filas rojas y no probaría nada.

La SIGUIENTE es planificación a futuro: sin fichajes que contrastar, así que lo que
aporta es rotación de gente entre obras, franjas y un fin de semana.

En seco por defecto; `--apply` escribe.
"""
import datetime as dt
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador", "nombre": "dmoreno"}

from core import auth, clock, projects as P, roster as R, timeclock as T  # noqa: E402

G = "cliente1"
APLICAR = "--apply" in sys.argv
LUNES = R.lunes_de(clock.today(G))
ANTES, DESPUES = LUNES - dt.timedelta(days=7), LUNES + dt.timedelta(days=7)
T0, T1 = R.TURNO_DEFAULT


def item(a, i="", f=""):
    return {"a": a, "i": i, "f": f}


def dia(*its, nota=""):
    return {"items": list(its), "nota": nota}


# ── lo que se fichó la semana pasada ────────────────────────────────────────
fichado = defaultdict(set)          # (usuario, dia_key) -> {pid}
for r in T._cached_records():
    if str(r.get("Grupo", "")).strip().lower() != G:
        continue
    ci = str(r.get("Clock In", ""))[:10]
    try:
        f = dt.date.fromisoformat(ci)
    except Exception:
        continue
    if ANTES <= f <= ANTES + dt.timedelta(days=6):
        pid = str(r.get("ProyectoID", "")).strip()
        if pid:
            fichado[(str(r.get("Usuario", "")), R.DIAS_TODOS[f.weekday()])].add(pid)

campo = [str(u.get("Usuario")) for u in auth.list_users()
         if str(u.get("Rol")) == "campo" and str(u.get("Grupo")) == G]
activos = [str(p.get("ID")) for p in P.list_projects(G)
           if str(p.get("Estado")) not in ("Archivado", "Cancelado", "Completado")]

# ── SEMANA PASADA: se planifica lo que se fichó, y se introducen los desvíos ──
# Reglas: si fichó → se planifica ESA obra (🟢). Además, a propósito:
#   · a `campo2` el martes se le planifica OTRA obra distinta de la que fichó (🔴)
#   · a `campo1` mié y jue se le planifica trabajo sin fichaje (⚠️)
DESVIO_USR, DESVIO_DIA = "campo2", "mar"
SIN_FICHAR = [("campo1", "mie"), ("campo1", "jue")]

sem_ant = {}
for usr in campo:
    dias = {}
    for d in R.DIAS_TODOS:
        pids = sorted(fichado.get((usr, d), ()))
        if pids:
            if usr == DESVIO_USR and d == DESVIO_DIA:
                otra = next((p for p in activos if p not in pids), activos[0])
                dias[d] = dia(item(otra, T0, T1), nota="plan que NO se cumplió")
            else:
                # varias obras el mismo día se planifican como dos franjas
                if len(pids) == 1:
                    dias[d] = dia(item(pids[0], T0, T1))
                else:
                    dias[d] = dia(item(pids[0], "07:00", "11:00"),
                                  item(pids[1], "11:30", "15:30"))
    for u2, d2 in SIN_FICHAR:
        if u2 == usr and d2 not in dias:
            dias[d2] = dia(item(activos[0], T0, T1), nota="planificado y no fichado")
    if dias:
        sem_ant[usr] = dias

# ── SEMANA SIGUIENTE: rotación, franjas y fin de semana ─────────────────────
A, B, C, D = activos[0], activos[1], activos[2], activos[3]
sem_sig = {
    campo[0]: {"lun": dia(item(B, T0, T1)), "mar": dia(item(B, T0, T1)),
               "mie": dia(item(B, T0, T1)), "jue": dia(item(C, T0, T1)),
               "vie": dia(item(C, T0, T1), nota="rota a otra torre")},
    campo[1]: {"lun": dia(item(C, T0, T1)), "mar": dia(item(C, T0, T1)),
               "mie": dia(item("OFF")), "jue": dia(item(C, T0, T1)),
               "vie": dia(item(C, T0, T1))},
    campo[2]: {"lun": dia(item(D, T0, T1)), "mar": dia(item(D, "07:00", "12:00"),
                                                       item(A, "12:30", "16:30")),
               "mie": dia(item(D, T0, T1)), "jue": dia(item(D, T0, T1)),
               "vie": dia(item(D, T0, T1))},
    campo[3]: {d: dia(item(A, T0, T1)) for d in ("lun", "mar", "mie", "jue", "vie")},
    campo[4]: {"lun": dia(item(A, T0, T1)), "mar": dia(item(A, T0, T1)),
               "mie": dia(item(A, T0, T1)), "jue": dia(item(A, T0, T1)),
               "vie": dia(item(A, T0, T1)),
               "dom": dia(item(A, "09:00", "14:00"), nota="entrega de material")},
    campo[5]: {"lun": dia(item(B, T0, T1)), "mar": dia(item("LEAVE")),
               "mie": dia(item("LEAVE")), "jue": dia(item(B, T0, T1)),
               "vie": dia(item(B, T0, T1))},
    campo[6]: {d: dia(item(C, T0, T1)) for d in ("lun", "mar", "mie", "jue", "vie")},
}
if len(campo) > 7:
    sem_sig[campo[7]] = {d: dia(item(D, T0, T1)) for d in ("lun", "mar", "mie")}


def sembrar(lunes, plan, etiqueta):
    print(f"\n== semana del {lunes} ({etiqueta}) ==")
    for usr, dias in plan.items():
        n = sum(len(d["items"]) for d in dias.values())
        print(f"  {usr:<12} {len(dias)} días · {n} asignaciones"
              + ("" if APLICAR else "   (seco)"))
        if APLICAR:
            ok, msg = R.guardar_persona(G, lunes, usr, dias)
            if not ok:
                print(f"     FALLO: {msg}")


sembrar(ANTES, sem_ant, "pasada · calcada de lo fichado, con 2 desvíos a propósito")
sembrar(DESPUES, sem_sig, "siguiente · rotación y fin de semana")

if not APLICAR:
    print("\n(en seco: no se ha escrito nada — repetir con --apply)")
    sys.exit(0)

# ── verificación: ¿salen los TRES estados de Cumplimiento? ──────────────────
print("\n== Cumplimiento de la semana pasada, contra los fichajes reales ==")
R._invalidate()
datos = R.get_semana(G, ANTES)
verde = rojo = ambar = 0
for k in range(7):
    f = ANTES + dt.timedelta(days=k)
    real = T.proyectos_por_usuario_dia(G, f)
    for usr in datos:
        plan = [i["asig"] for i in R.celda_items(datos, usr, R.DIAS_TODOS[k])
                if not i["asig"].startswith(("OFF", "LEAVE", "FORMACION"))]
        if not plan:
            continue
        pids_real = {str(x.get("pid", "")) for x in (real.get(usr) or [])}
        if not pids_real:
            ambar += 1
        elif pids_real & set(plan):
            verde += 1
        else:
            rojo += 1
            print(f"     🔴 {usr} {f}: plan {plan} · fichó {sorted(pids_real)}")
print(f"  🟢 donde tocaba {verde} · 🔴 en otra obra {rojo} · ⚠️ sin fichar {ambar}")

print("\n== resumen de las tres semanas ==")
for lu, et in ((ANTES, "pasada"), (LUNES, "actual"), (DESPUES, "siguiente")):
    d = R.get_semana(G, lu)
    n = sum(len(R.celda_items(d, u, x)) for u in d for x in R.DIAS_TODOS)
    ch = sum(1 for u in d for x in R.DIAS_TODOS
             for i in R.celda_items(d, u, x) if i["ini"])
    print(f"  {lu} ({et:<9}) {len(d)} personas · {n} asignaciones · {ch} con franja "
          f"· días con datos: {R.dias_con_datos(d)}")
