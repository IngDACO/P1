"""Ejercita las escrituras de `core.ausencias` contra la hoja REAL.

Metodo de v344: foto -> ejercitar -> verificar leyendo -> limpiar -> segunda foto.
La hoja `Ausencias` no existe todavia: la crea la primera escritura (regla v145).
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os
os.chdir(RAIZ)

import streamlit as st
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "ejaus", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "ejaus"}

from core import ausencias as AU, clock

U = "campo1"
NOM = "lksdfkldsf"
ok = True
creados = []


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def paso(n, t):
    print(f"\n{'─' * 66}\n{n}. {t}\n{'─' * 66}")


def limpiar():
    print(f"\n{'═' * 66}\nLIMPIEZA\n{'═' * 66}")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    from core import timeclock as T
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    sh = gc.open_by_key(T.sheet_id_para(AU.SHEET, GRUPO))
    try:
        ws = sh.worksheet(AU.SHEET)
    except Exception as e:
        print(f"   (la hoja no existe: {e})")
        return
    v = ws.get_all_values()
    filas = [n for n, f in enumerate(v[1:], start=2) if f and f[0] in set(creados)]
    for r in sorted(filas, reverse=True):
        ws.delete_rows(r)
    print(f"   Ausencias: -{len(filas)} -> {len(ws.get_all_values())-1} filas")
    AU._invalidate()


try:
    # ── 1 ──────────────────────────────────────────────────────────
    paso(1, "El usuario pide VACACIONES (aprobación previa)")
    hoy = clock.today(GRUPO)
    from datetime import timedelta
    d0 = hoy + timedelta(days=30)
    while d0.weekday() > 4:            # empezar en lunes-viernes
        d0 += timedelta(days=1)
    d1 = d0 + timedelta(days=4)
    _ok, aid = AU.solicitar(GRUPO, U, NOM, AU.VACACIONES, d0, d1,
                            motivo="Viaje familiar")
    chk("se crea la solicitud", _ok)
    creados.append(aid if _ok else None)
    print(f"   -> {aid}  ({d0} → {d1})")
    AU._invalidate(); time.sleep(1.5)
    r = AU.get(aid)
    chk("nace PENDIENTE (necesita aprobación)", str(r.get("Estado")), AU.PENDIENTE)
    chk("cuenta los días hábiles del rango", str(r.get("Dias")),
        str(len(AU.dias_del_rango(d0, d1))))

    # ── 2 ──────────────────────────────────────────────────────────
    paso(2, "El saldo aún NO baja (solo cuentan las aprobadas)")
    s = AU.saldo(GRUPO, U, AU.VACACIONES)
    print(f"   saldo: {s}")
    chk("una PENDIENTE no descuenta días", s["usados"], 0.0)

    # ── 3 ──────────────────────────────────────────────────────────
    paso(3, "Pedir las MISMAS fechas otra vez se bloquea (criterio v364)")
    _ok2, _msg = AU.solicitar(GRUPO, U, NOM, AU.LIBRE, d0 + timedelta(days=2),
                              d1 + timedelta(days=2))
    chk("un rango que SOLAPA se rechaza", _ok2, False)
    print(f"   -> {_msg}")
    chk("...y dice cuál estorba", aid in str(_msg))

    # ── 4 ──────────────────────────────────────────────────────────
    paso(4, "El administrador la APRUEBA")
    _ok3, _m3 = AU.resolver(aid, True, "Bobo", nota="Buen viaje")
    chk("se aprueba", _ok3)
    AU._invalidate(); time.sleep(1.5)
    r = AU.get(aid)
    chk("queda APROBADA", str(r.get("Estado")), AU.APROBADA)
    chk("con quién la resolvió", str(r.get("ResueltaPor")), "Bobo")
    chk("resolver dos veces se bloquea", AU.resolver(aid, True, "Bobo")[0], False)
    # ⚠️ y el caso grave: RECHAZAR una ya aprobada desde el mismo botón
    _rr = AU.resolver(aid, False, "Bobo")
    chk("no se puede RECHAZAR una ya aprobada", _rr[0], False)
    print(f"   -> {_rr[1]}")

    # ── 5 ──────────────────────────────────────────────────────────
    paso(5, "AHORA sí baja el saldo, y las horas cuentan para la nómina")
    s = AU.saldo(GRUPO, U, AU.VACACIONES)
    print(f"   saldo: {s}")
    chk("descuenta los 5 días", s["usados"], 5.0)
    chk("y quedan 15 de 20", s["restantes"], 15.0)
    hp = AU.horas_pagadas(GRUPO, U, d0, d1)
    print(f"   horas pagadas en el periodo: {hp}")
    chk("5 días × 8 h = 40 h pagadas", hp["horas"], 40.0)
    # ⚠️ una ausencia a caballo de dos nóminas se reparte
    hp2 = AU.horas_pagadas(GRUPO, U, d0, d0 + timedelta(days=1))
    chk("...y solo cuenta los días DENTRO del periodo pedido", hp2["horas"], 16.0)

    # ── 6 ──────────────────────────────────────────────────────────
    paso(6, "Quién está ausente ese día")
    _aus = AU.ausentes_en(GRUPO, d0)
    chk("aparece en el día de la ausencia", [a["ID"] for a in _aus], [aid])
    chk("...y no el día anterior",
        [a["ID"] for a in AU.ausentes_en(GRUPO, d0 - timedelta(days=1))], [])

    # ── 7 ──────────────────────────────────────────────────────────
    paso(7, "Una baja por ENFERMEDAD se registra YA, sin esperar")
    # ⚠️ `hoy` puede ser SÁBADO (lo fue al probar): una baja de fin de semana no
    # puede rechazarse con un mensaje falso sobre las fechas.
    if hoy.weekday() > 4:
        _r0 = AU.solicitar(GRUPO, U, NOM, AU.ENFERMEDAD, hoy, hoy)
        chk("un rango solo-findes se rechaza con el motivo CORRECTO",
            "fin de semana" in str(_r0[1]))
        _ok4, bid = AU.solicitar(GRUPO, U, NOM, AU.ENFERMEDAD, hoy, hoy,
                                 motivo="Gripe", incluir_findes=True)
    else:
        _ok4, bid = AU.solicitar(GRUPO, U, NOM, AU.ENFERMEDAD, hoy, hoy,
                                 motivo="Gripe")
    # y el rango de verdad invertido sigue dando SU mensaje
    from datetime import timedelta as _td
    chk("un rango invertido dice lo suyo",
        "anterior a la de inicio" in str(
            AU.solicitar(GRUPO, U, NOM, AU.LIBRE, hoy, hoy - _td(days=3))[1]))
    chk("se registra", _ok4)
    creados.append(bid if _ok4 else None)
    AU._invalidate(); time.sleep(1.5)
    rb = AU.get(bid)
    chk("nace APROBADA (no espera a nadie)", str(rb.get("Estado")), AU.APROBADA)
    print(f"   -> {bid} · resuelta por {rb.get('ResueltaPor')!r}")
    chk("el tablero la pintará como LEAVE",
        AU.TIPOS[AU.ENFERMEDAD]["estado_roster"], "LEAVE")

    # ── 8 ──────────────────────────────────────────────────────────
    paso(8, "Cancelar devuelve los días")
    _ok5, _m5 = AU.cancelar(aid, U)
    chk("se cancela", _ok5)
    AU._invalidate(); time.sleep(1.5)
    chk("la fila NO se borra, se marca", bool(AU.get(aid)))
    chk("...como cancelada", str(AU.get(aid).get("Estado")), AU.CANCELADA)
    s = AU.saldo(GRUPO, U, AU.VACACIONES)
    chk("el saldo vuelve a 20", s["restantes"], 20.0)
    chk("y ya no cuenta como ausente ese día",
        [a["ID"] for a in AU.ausentes_en(GRUPO, d0)], [])

except Exception:
    ok = False
    import traceback
    traceback.print_exc()
finally:
    try:
        limpiar()
    except Exception:
        import traceback
        traceback.print_exc()
        print("  !! LIMPIEZA FALLIDA:", creados)

print("\n" + ("AUSENCIAS EJERCITADAS OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
