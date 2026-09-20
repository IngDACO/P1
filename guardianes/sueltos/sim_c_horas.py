"""SIMULACIÓN etapa C — ocho semanas de fichajes.

Sin horas no se puede juzgar NADA de lo que importa: costo de mano de obra,
nóminas, rentabilidad, ganancia por rubro, conciliación, cumplimiento del panel.
Con 2 personas y 30 filas, todas esas pantallas son un cero.

⚠️ Las filas se escriben en LOTES (`append_rows`), no con `clock_in`/`clock_out`:
serían ~700 llamadas contra un techo de 60/min (v339). El formato es idéntico,
carácter a carácter, al que escribe `clock_in` (verificado sobre su código:
`[Nombre, "", Proyecto, Ubicacion, ClockIn, ClockOut, Horas, Estado, Grupo,
Tipo, Usuario, ProyectoID]`), así que el camino de LECTURA —que es justo lo que
se está probando— es el real.

CASOS LÍMITE metidos a propósito, cada uno reproduce un fallo ya visto:
  ⚠️ turno que CRUZA MEDIANOCHE  → el reparto por día de v164, que solo se ha
     visto correr una vez con datos reales.
  ⚠️ obra fichada SIN jornada abierta → `sin_asignar_indet` (v320): la app debe
     poner «—», no un 0 que parece bueno.
  ⚠️ jornada SIN imputar a obra (traslados, espera) → el hueco que la
     conciliación de v313 llama «horas pagadas que no se cargan».
  ⚠️ una sesión ABIERTA ahora mismo → cronómetro en vivo y aviso de olvido.
  ⚠️ `nsanchez` trabaja y NO tiene tarifa → su costo sale $0 (aviso de v325/v346).
"""
import random
import sys
from datetime import date, datetime, time, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrador"}

from core import projects as P, timeclock as T                      # noqa: E402

G = "cliente1"
HOY = date(2026, 8, 18)
DESDE = HOY - timedelta(days=56)                 # 8 semanas
random.seed(20260818)                            # reproducible

# quién trabaja en qué (coherente con CampoAsignados de las obras)
PLAN = {
    "jlopez":   [("PRJ-0007", "Meriton Zetland — Torre A", 0.6),
                 ("PRJ-0008", "Meriton Zetland — Torre B", 0.4)],
    "mchen":    [("PRJ-0007", "Meriton Zetland — Torre A", 0.5),
                 ("PRJ-0012", "RNSH Lift 4 — Modernización", 0.5)],
    "mchen2":   [("PRJ-0009", "Meriton Zetland — Torre C", 1.0)],
    "tobrien":  [("PRJ-0008", "Meriton Zetland — Torre B", 0.5),
                 ("PRJ-0010", "Stockland Wetherill Park — Ripout", 0.5)],
    "apatel":   [("PRJ-0012", "RNSH Lift 4 — Modernización", 0.6),
                 ("PRJ-0010", "Stockland Wetherill Park — Ripout", 0.4)],
    "nsanchez": [("PRJ-0009", "Meriton Zetland — Torre C", 1.0)],   # ⚠️ sin tarifa
    "campo1":   [("PRJ-0012", "RNSH Lift 4 — Modernización", 1.0)],
}
NOMBRE = {"jlopez": "Javier López", "mchen": "Mei Chen", "mchen2": "Mei Chen",
          "tobrien": "Tom O'Brien", "apatel": "Anjali Patel",
          "nsanchez": "Nuria Sánchez", "campo1": "lksdfkldsf"}

FMT = "%Y-%m-%d %H:%M:%S"


def fila(usr, ini, fin, tipo, pid="", pnom=""):
    """Una fila EXACTAMENTE como la escribe clock_in + clock_out."""
    if fin is None:                                     # sesión abierta
        return [NOMBRE[usr], "", pnom, "", ini.strftime(FMT), "", "",
                "ABIERTO", G, tipo, usr, pid]
    horas = round((fin - ini).total_seconds() / 3600.0, 2)
    return [NOMBRE[usr], "", pnom, "", ini.strftime(FMT), fin.strftime(FMT),
            str(horas), "CERRADO", G, tipo, usr, pid]


filas = []
dias_trabajados = {u: 0 for u in PLAN}

d = DESDE
while d <= HOY:
    if d.weekday() > 4:                                  # Lun–Vie
        d += timedelta(days=1)
        continue
    for usr, obras in PLAN.items():
        if random.random() < 0.12:                       # ausencias, permisos
            continue
        # las obras solo se fichan dentro de su ventana real
        activas = []
        for pid, pnom, peso in obras:
            prj = P.get_project(pid) or {}
            try:
                ini_p = date.fromisoformat(str(prj.get("FechaInicio"))[:10])
            except Exception:
                ini_p = DESDE
            if d >= ini_p:
                activas.append((pid, pnom, peso))
        if not activas:
            continue

        entrada = datetime.combine(d, time(random.choice([6, 7, 7, 7, 8]),
                                           random.choice([0, 15, 30, 45])))
        jornada = timedelta(hours=random.choice([7.5, 8, 8, 8, 8.5, 9, 9.5]))
        salida = entrada + jornada
        dias_trabajados[usr] += 1

        # ── la jornada general
        filas.append(fila(usr, entrada, salida, T.TIPO_GENERAL))

        # ── el tiempo imputado a obra: SIEMPRE algo menos que la jornada
        #    (traslados, montaje, espera). Ese hueco es el que la conciliación
        #    de v313 llama «horas pagadas que no se cargan» y es real.
        imputable = jornada - timedelta(minutes=random.choice([15, 30, 30, 45, 60]))
        cursor = entrada + timedelta(minutes=random.choice([10, 15, 20]))
        for k, (pid, pnom, peso) in enumerate(activas):
            trozo = imputable * (peso / sum(p for _, _, p in activas))
            if k == len(activas) - 1:
                trozo = max(timedelta(hours=1), (entrada + imputable) - cursor)
            fin_t = cursor + trozo
            filas.append(fila(usr, cursor, fin_t, T.TIPO_PROYECTO, pid, pnom))
            cursor = fin_t
    d += timedelta(days=1)

# ── los casos límite, añadidos aparte para que sean inequívocos ──
extra = []

# 1) turno nocturno que CRUZA MEDIANOCHE (v164)
n_ini = datetime.combine(HOY - timedelta(days=9), time(21, 30))
n_fin = n_ini + timedelta(hours=8, minutes=15)
extra.append(fila("tobrien", n_ini, n_fin, T.TIPO_GENERAL))
extra.append(fila("tobrien", n_ini + timedelta(minutes=20),
                  n_fin - timedelta(minutes=25), T.TIPO_PROYECTO,
                  "PRJ-0010", "Stockland Wetherill Park — Ripout"))

# 2) obra fichada SIN jornada abierta (v320 → sin_asignar indeterminado)
s_ini = datetime.combine(HOY - timedelta(days=5), time(8, 0))
extra.append(fila("apatel", s_ini, s_ini + timedelta(hours=6),
                  T.TIPO_PROYECTO, "PRJ-0012", "RNSH Lift 4 — Modernización"))

# 3) jornada SIN imputar nada a obra (día de traslados)
t_ini = datetime.combine(HOY - timedelta(days=3), time(7, 0))
extra.append(fila("jlopez", t_ini, t_ini + timedelta(hours=7, minutes=30), T.TIPO_GENERAL))

# 4) sesión ABIERTA ahora mismo (cronómetro en vivo)
a_ini = datetime.combine(HOY, time(7, 15))
extra.append(fila("mchen", a_ini, None, T.TIPO_GENERAL))
extra.append(fila("mchen", a_ini + timedelta(minutes=20), None,
                  T.TIPO_PROYECTO, "PRJ-0007", "Meriton Zetland — Torre A"))

filas += extra

print(f"== C. {len(filas)} filas de fichaje ({len(extra)} son casos límite) ==")
for u, n in sorted(dias_trabajados.items()):
    print(f"   {u:<10} {n:>3} días trabajados")

ws = T.get_sheet("Sheet1", tuple(T.HEADERS))
LOTE = 120
for i in range(0, len(filas), LOTE):
    ws.append_rows(filas[i:i + LOTE], value_input_option="RAW")
    print(f"   escritas {min(i + LOTE, len(filas))}/{len(filas)}")
T._invalidate_records()

print("\n== verificación: se lee lo que se escribió ==")
recs = [r for r in T._cached_records() if str(r.get("Grupo")) == G]
abiertas = [r for r in recs if str(r.get("Estado", "")).upper() == "ABIERTO"]
print(f"   filas del grupo en la hoja : {len(recs)}")
print(f"   sesiones abiertas          : {len(abiertas)} "
      f"({[r.get('Usuario') for r in abiertas]})")

# el reparto por medianoche (v164) es la comprobación que más vale: una fila de
# 8,25 h que cruza las 00:00 tiene que salir partida en DOS días
cruce = [r for r in recs if str(r.get("Clock In", ""))[:10] != str(r.get("Clock Out", ""))[:10]
         and str(r.get("Clock Out", ""))]
print(f"   filas que cruzan medianoche: {len(cruce)}")
for r in cruce[:3]:
    segs = T._row_segmentos(r)
    print(f"      {r.get('Usuario')} {r.get('Clock In')} → {r.get('Clock Out')} "
          f"({r.get('Horas')} h) se reparte en {[(str(d), round(h, 2)) for d, h in segs]}")
