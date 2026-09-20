"""La OTRA dirección de `hecho_hoy`: que diga True cuando el Pre-Start SÍ está.

⚠️ Comprobar solo que devuelve False es el «paso en vacío» (trampa nº1): un
`return False` fijo pasaría ese test y el recordatorio saldría para siempre, aun con
el Pre-Start hecho.

⚠️ v474 · Se CONSTRUYE el caso en vez de depender de lo que haya en la demo. Antes
salía «SIN DATOS» desde que v456 la vació, o sea que la afirmación llevaba versiones
sin comprobarse. El caso construido ejercita la función REAL (`hecho_hoy` lee
`_records()`, que es lo único que se sustituye), y la prueba se valida en las DOS
direcciones contra implementaciones rotas antes de creerse su verde.

⚠️ Y de paso arregla un desajuste que el «SIN DATOS» estaba tapando: este guardián
listaba las filas por `ProyectoID`/`Fecha` y **v468 renombró esas columnas** a
`ProjectID`/`Date`, que es lo que lee `hecho_hoy`. Con datos delante habría dicho «no
hay pre-starts» igualmente — la lista de columnas a mano que se queda vieja (v433/v434).
"""
import datetime as dt
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "field"}

from core import prestart as PS, clock          # noqa: E402

ok = True
HOY = dt.date(2026, 3, 10)

# ⚠️ Las claves son las CANÓNICAS (v468). Si alguien vuelve a renombrar la columna,
# `hecho_hoy` dejará de casar y este guardián lo dirá, que es justo lo que no pasaba.
FIXTURE = [
    {"ID": "PS-T1", "ProjectID": "PRJ-T-A", "Date": "2026-03-10", "Facilitator": "jlopez"},
    {"ID": "PS-T2", "ProjectID": "PRJ-T-B", "Date": "2026-03-05", "Facilitator": "jlopez"},
    # fila con la fecha en formato VIEJO: `hecho_hoy` la PARSEA, no la compara como
    # texto (v323), así que debe casar igual. Sin este caso, esa rama no se prueba.
    {"ID": "PS-T3", "ProjectID": "PRJ-T-C", "Date": "10/03/2026", "Facilitator": "jlopez"},
]

_rec_orig, _hoy_orig = PS._records, clock.today
PS._records = lambda: FIXTURE
clock.today = lambda grupo=None: HOY


def escenario(fn=None):
    """Las 4 afirmaciones contra la implementación que se le pase (o la real)."""
    f = fn or PS.hecho_hoy
    return {
        "obra con pre-start de HOY": f("PRJ-T-A", "cliente1") is True,
        "la MISMA obra otro día": f("PRJ-T-B", "cliente1") is False,
        "otra obra el mismo día": f("PRJ-T-Z", "cliente1") is False,
        "fecha en formato viejo": f("PRJ-T-C", "cliente1") is True,
    }


try:
    print("== 1. la funcion REAL, con el caso construido ==")
    res = escenario()
    for k, v in res.items():
        print("   %s %s" % ("✓" if v else "‼️", k))
    ok &= all(res.values())

    # ⚠️ 2. La prueba, validada contra DOS rotos: si no cazara ninguno, su verde de
    # arriba no significaría nada (trampa nº12, y es la razón de ser de este guardián).
    print("\n== 2. ¿la prueba CAZA una implementacion rota? ==")
    _siempre_no = escenario(lambda *a, **k: False)
    _siempre_si = escenario(lambda *a, **k: True)
    caza_no = not all(_siempre_no.values())
    caza_si = not all(_siempre_si.values())
    print("   %s un `return False` fijo (el fallo que este guardian existe para ver)"
          % ("✓ cazado" if caza_no else "‼️ SE ESCAPA"))
    print("   %s un `return True` fijo (avisaria como hecho lo que falta)"
          % ("✓ cazado" if caza_si else "‼️ SE ESCAPA"))
    ok &= caza_no and caza_si

    # 3. Y que sigue leyendo la hoja de verdad cuando la hay.
    print("\n== 3. con los datos REALES de la demo (informativo) ==")
    PS._records = _rec_orig
    clock.today = _hoy_orig
    reales = [r for r in PS._records() if str(r.get("Date", "")).strip()]
    print("   %d pre-start(s) en la hoja" % len(reales))
    if reales:
        r0 = reales[0]
        print("   %s → hecho_hoy=%s" % (r0.get("ID"),
                                        PS.hecho_hoy(r0.get("ProjectID"), "cliente1")))
    else:
        print("   (la demo está vacía: no afecta, el caso construido ya afirmó)")
finally:
    PS._records, clock.today = _rec_orig, _hoy_orig

print("\n" + ("✅ las dos direcciones probadas Y la prueba caza los dos rotos"
              if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
