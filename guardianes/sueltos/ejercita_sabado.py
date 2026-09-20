"""¿De verdad se puede planificar un sábado? — contra la hoja REAL.

Método de v344/v345 (foto en solo lectura → ejercitar → verificar leyendo → devolver
todo → segunda foto). Se usa una semana FUTURA y vacía para no rozar nada existente.

Lo que ninguna prueba local puede contestar:
  · ¿`guardar_persona` acepta la clave 'sab' en el JSON?
  · ¿la lee `get_semana` y la ve `dias_con_datos`?
  · ¿`asignaciones_dia` la devuelve un sábado (antes cortaba por weekday>4)?
  · ¿`copiar_semana` ARRASTRA el sábado, como afirmé?
"""
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrador"}

from core import roster as R          # noqa: E402

G = "cliente1"
USR = "campo1"
SEM = date(2026, 10, 5)              # lunes futuro y VACÍO (medido: hay datos hasta
                                     # el 07/09, así que octubre está limpio)
SEM2 = SEM + timedelta(days=7)
ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


print("== FOTO PREVIA (solo lectura) ==")
_antes = R._roster_records()
_mias = [f for f in _antes if str(f.get("Grupo")) == G
         and str(f.get("Semana")) in (SEM.isoformat(), SEM2.isoformat())]
print(f"   filas del roster en el libro: {len(_antes)}")
print(f"   filas en las 2 semanas de prueba: {len(_mias)}  (debe ser 0)")
if _mias:
    print("   ⚠️ ABORTADO: esas semanas ya tienen datos, no se toca nada.")
    sys.exit(1)

print("\n== 1) guardar una asignación en SÁBADO ==")
_proy = None
try:
    from core import projects as P
    _act = [p for p in P.list_projects(G) if str(p.get("Estado")) != "Archivado"]
    _proy = str(_act[0]["ID"]) if _act else None
except Exception as e:
    print("   (no se pudo leer proyectos:", e, ")")
chk("hay un proyecto real con el que probar", bool(_proy))
sem_data = {"sab": {"items": [{"a": _proy, "i": "07:00", "f": "12:00"}],
                    "nota": "PRUEBA v390 — borrar"}}
_ok, _msg = R.guardar_persona(G, SEM, USR, sem_data)
chk(f"guardar_persona escribe el sábado ({_msg})", _ok)

print("\n== 2) ¿se lee de vuelta? ==")
_leido = R.get_semana(G, SEM)
_items = R.celda_items(_leido, USR, "sab")
chk("get_semana devuelve la asignación del sábado", len(_items), 1)
chk("...con su franja", (_items[0]["ini"], _items[0]["fin"]) if _items else None,
    ("07:00", "12:00"))
chk("...y su proyecto", _items[0]["asig"] if _items else None, _proy)
chk("la nota viaja", R.celda(_leido, USR, "sab").get("nota"), "PRUEBA v390 — borrar")

print("\n== 3) ¿la columna aparece sola, sin haber pulsado el botón? ==")
# ⚠️ ESTA es la garantía de v390: el dato manda sobre el botón.
chk("dias_con_datos abre el sábado SIN pedirlo",
    R.dias_con_datos(_leido), R.DIAS + ["sab"])
chk("dia_tiene_datos dice quién es", R.dia_tiene_datos(_leido, "sab"), [USR])
chk("el domingo sigue cerrado", "dom" in R.dias_con_datos(_leido), False)

print("\n== 4) ¿lo ve el CAMPO en su móvil ese sábado? ==")
# antes de v390 esto devolvía [] por `weekday() > 4`
_sab = R.fecha_de_dia(SEM, "sab")
chk("la fecha del sábado es correcta", _sab, SEM + timedelta(days=5))
chk("...y es sábado de verdad", _sab.weekday(), 5)
_aa = R.asignaciones_dia(G, USR, _sab)
chk("asignaciones_dia lo devuelve (antes daba [])", len(_aa), 1)
chk("...resolviendo la etiqueta del proyecto", bool(_aa and _aa[0].get("etiqueta")))
chk("un domingo sin nada sigue dando []",
    R.asignaciones_dia(G, USR, SEM + timedelta(days=6)), [])

print("\n== 5) ¿`copiar_semana` ARRASTRA el sábado? (lo afirmé, hay que probarlo) ==")
_ok2, _msg2 = R.copiar_semana(G, SEM, SEM2)
chk(f"copiar_semana corre ({_msg2})", _ok2)
_l2 = R.get_semana(G, SEM2)
chk("el sábado llegó a la semana siguiente",
    len(R.celda_items(_l2, USR, "sab")), 1)
chk("...con su franja intacta",
    (R.celda_items(_l2, USR, "sab") or [{}])[0].get("ini"), "07:00")

print("\n== LIMPIEZA: devolver la hoja a como estaba ==")
import gspread                                                   # noqa: E402
from google.oauth2.service_account import Credentials            # noqa: E402
_cred = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"])
_gc = gspread.authorize(_cred)
_sid = R.timeclock.sheet_id_para("Roster", G)
_ws = _gc.open_by_key(_sid).worksheet("Roster")
_vals = _ws.get_all_values()
_borrar = [i for i, row in enumerate(_vals[1:], start=2)
           if len(row) > 2 and row[1] == G and row[2] in (SEM.isoformat(),
                                                          SEM2.isoformat())]
for i in sorted(_borrar, reverse=True):        # de abajo arriba: no desplaza índices
    _ws.delete_rows(i)
print(f"   filas borradas: {len(_borrar)}")
R._invalidate()

print("\n== FOTO FINAL ==")
_desp = R._roster_records()
_quedan = [f for f in _desp if str(f.get("Grupo")) == G
           and str(f.get("Semana")) in (SEM.isoformat(), SEM2.isoformat())]
chk("no queda rastro de la prueba", len(_quedan), 0)
chk("el resto del roster está intacto", len(_desp), len(_antes))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
