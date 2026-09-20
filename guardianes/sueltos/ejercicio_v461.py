"""Ejercita v461 CONTRA LA HOJA REAL (método v344).

foto en solo lectura -> ejercitar -> verificar LEYENDO -> devolver todo -> foto.
⚠️ Escribe en el grupo de demo `cliente1`, que el usuario autorizó como entorno de
pruebas. Todo lo que crea se borra al final y se comprueba que no queda rastro.
"""
import os
import sys
from datetime import timedelta

# ⚠️ CWD = survey_app SIEMPRE: Streamlit busca `.streamlit/secrets.toml` relativo
# al directorio de trabajo, así que lanzarlo desde otro sitio lo tumba por el
# entorno y no por el código (trampa nº19).
RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

import streamlit as st

GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "zzzv461", "nombre": "ZZZ PRUEBA v461",
                            "rol": "administrador", "grupo": GRUPO}

from core import clock, correcciones as C, hojas, timeclock

USUARIO, NOMBRE = "zzzv461", "ZZZ PRUEBA v461"
fallos = []


def comprueba(cond, msg):
    print(("  OK   " if cond else "  FALLO ") + msg)
    if not cond:
        fallos.append(msg)


def filas_fichaje():
    hojas.invalidar()
    ws, err = timeclock._get_worksheet()
    if err:
        raise SystemExit("no se pudo abrir el fichaje: " + str(err))
    return [r for r in ws.get_all_records(numericise_ignore=["all"])
            if str(r.get("Usuario", "")).strip() == USUARIO]


def correcciones_mias():
    C._invalidate()
    return [r for r in C.list_group(GRUPO) if str(r.get("Usuario", "")) == USUARIO]


print("=== FOTO ANTES ===")
_f0, _c0 = len(filas_fichaje()), len(correcciones_mias())
ws_all, _ = timeclock._get_worksheet()
_tot0 = len(ws_all.get_all_records(numericise_ignore=["all"]))
print("  fichajes míos: %d · correcciones mías: %d · filas totales de fichaje: %d"
      % (_f0, _c0, _tot0))

hoy = clock.today(GRUPO)
t7 = timeclock.datetime.combine(hoy, timeclock.datetime.min.time()) + timedelta(hours=7)
t9 = t7 + timedelta(hours=2)
t17 = t7 + timedelta(hours=10)

print("")
print("=== 1 · Fichar con hora RETROACTIVA (el olvido de entrada) ===")
ok1, msg1 = timeclock.clock_in(NOMBRE, "PRUEBA v461", "", GRUPO,
                               tipo=timeclock.TIPO_GENERAL, usuario=USUARIO, in_ts=t7)
print("  " + str(msg1))
_mias = filas_fichaje()
comprueba(ok1 and len(_mias) == 1, "se creó UNA fila")
_ci = str(_mias[0].get("Clock In", "")) if _mias else ""
comprueba(_ci == t7.strftime(timeclock.FMT),
          "la hoja guarda la hora que dijo la persona (%s), no «ahora»" % _ci[11:16])

print("")
print("=== 2 · Cerrar y corregir la ENTRADA (07:00 -> 09:00) ===")
timeclock.clock_out(NOMBRE, GRUPO, tipo=timeclock.TIPO_GENERAL, usuario=USUARIO,
                    out_ts=t17)
_h_antes = float(filas_fichaje()[0].get("Horas") or 0)
comprueba(abs(_h_antes - 10.0) < 0.02, "cerrada con 10.0 h (leído: %.2f)" % _h_antes)

okc, msgc = timeclock.corregir_fichaje(
    grupo=GRUPO, usuario=USUARIO, nombre=NOMBRE, tipo=timeclock.TIPO_GENERAL,
    campo=C.CAMPO_IN, valor_actual=t7.strftime(timeclock.FMT),
    valor_nuevo=t9.strftime(timeclock.FMT))
_r = filas_fichaje()[0]
comprueba(okc and str(_r.get("Clock In"))[11:16] == "09:00",
          "la entrada quedó en 09:00 (%s)" % str(_r.get("Clock In"))[11:16])
_h = float(_r.get("Horas") or 0)
# ⚠️ Lo que de verdad importa: si las Horas no se recalculan, `_row_segmentos`
# respeta el valor guardado y la corrección NO mueve ni nómina ni costo (v164).
comprueba(abs(_h - 8.0) < 0.02, "las Horas se recalcularon 10 -> 8 (leído: %.2f)" % _h)

print("")
print("=== 3 · La corrección llega a la bandeja del admin ===")
okr, cid = C.registrar(GRUPO, USUARIO, NOMBRE, timeclock.TIPO_GENERAL, "PRUEBA v461",
                       C.CAMPO_IN, t7.strftime(timeclock.FMT),
                       t9.strftime(timeclock.FMT), motivo="prueba v461")
comprueba(okr, "registrada: %s" % cid)
_pend = [r for r in C.pendientes(GRUPO) if str(r.get("Usuario")) == USUARIO]
comprueba(len(_pend) == 1, "aparece en pendientes del grupo")
if _pend:
    comprueba(str(_pend[0].get("ValorAnterior"))[11:16] == "07:00"
              and str(_pend[0].get("ValorNuevo"))[11:16] == "09:00",
              "la tarjeta puede enseñar las DOS horas (07:00 -> 09:00)")

print("")
print("=== 4 · REVERTIR devuelve la hora original ===")
okv, msgv = C.revertir(cid, "admin_prueba", "no cuadra")
print("  " + str(msgv))
_r = filas_fichaje()[0]
comprueba(okv and str(_r.get("Clock In"))[11:16] == "07:00",
          "el fichaje volvió a 07:00 (%s)" % str(_r.get("Clock In"))[11:16])
comprueba(abs(float(_r.get("Horas") or 0) - 10.0) < 0.02,
          "y las Horas volvieron a 10.0 (%.2f)" % float(_r.get("Horas") or 0))
_g = C.get(cid)
comprueba(str(_g.get("Estado")) == C.REVERTIDA, "la corrección queda REVERTIDA")
ok2, _ = C.revertir(cid, "admin_prueba", "")
comprueba(not ok2, "no se puede revisar dos veces la misma corrección")

print("")
print("=== 5 · APROBAR: el fichaje NO se toca (ya llevaba la hora) ===")
okc2, _ = timeclock.corregir_fichaje(
    grupo=GRUPO, usuario=USUARIO, nombre=NOMBRE, tipo=timeclock.TIPO_GENERAL,
    campo=C.CAMPO_IN, valor_actual=t7.strftime(timeclock.FMT),
    valor_nuevo=t9.strftime(timeclock.FMT))
_ok, cid2 = C.registrar(GRUPO, USUARIO, NOMBRE, timeclock.TIPO_GENERAL, "PRUEBA v461",
                        C.CAMPO_IN, t7.strftime(timeclock.FMT),
                        t9.strftime(timeclock.FMT))
oka, msga = C.aprobar(cid2, "admin_prueba", "correcto")
_r = filas_fichaje()[0]
comprueba(oka and str(_r.get("Clock In"))[11:16] == "09:00",
          "aprobar deja la hora corregida donde estaba")
comprueba(str(C.get(cid2).get("Estado")) == C.APROBADA, "queda APROBADA")

print("")
print("=== 6 · AJUSTAR: el caso que revertir NO puede resolver ===")
_ok, cid3 = C.registrar(GRUPO, USUARIO, NOMBRE, timeclock.TIPO_GENERAL, "PRUEBA v461",
                        C.CAMPO_OUT, "", t17.strftime(timeclock.FMT),
                        motivo="olvidó cerrar")
_g3 = C.get(cid3)
comprueba(not str(_g3.get("ValorAnterior", "")).strip(),
          "un cierre olvidado NO tiene hora anterior (por eso no se revierte)")
okj, msgj = C.ajustar(cid3, "admin_prueba", (t17 - timedelta(hours=2)).time(), "salió antes")
print("  " + str(msgj))
_r = filas_fichaje()[0]
comprueba(okj and str(_r.get("Clock Out"))[11:16] == "15:00",
          "el admin fijó la salida en 15:00 (%s)" % str(_r.get("Clock Out"))[11:16])
comprueba(abs(float(_r.get("Horas") or 0) - 6.0) < 0.02,
          "las Horas siguen al ajuste: 6.0 (%.2f)" % float(_r.get("Horas") or 0))
comprueba(str(C.get(cid3).get("ValorNuevo"))[11:16] == "15:00",
          "el rastro dice la hora REAL, no la que se pidió")
comprueba(str(C.get(cid3).get("ValorNuevo"))[:10] == t17.strftime("%Y-%m-%d"),
          "el ajuste NO movió el fichaje de día")

print("")
print("=== 7 · El aviso «ese día ya se pagó» (las DOS direcciones) ===")
# ⚠️ La demo no tiene nóminas, así que comprobar solo el "" sería el paso en VACÍO
# (trampa nº1): un `return ""` fijo lo pasaría. Se prueba con casos construidos.
from core import payroll
_real = payroll.list_nominas
_dia = t9.strftime(timeclock.FMT)
payroll.list_nominas = lambda g, **k: [
    {"ID": "NOM-TEST", "Usuario": USUARIO, "PeriodoDesde": str(hoy - timedelta(days=3)),
     "PeriodoHasta": str(hoy + timedelta(days=3))}]
comprueba(C.nomina_que_cubre(GRUPO, USUARIO, _dia) == "NOM-TEST",
          "detecta la nómina que cubre ese día")
payroll.list_nominas = lambda g, **k: [
    {"ID": "NOM-OTRA", "Usuario": USUARIO, "PeriodoDesde": str(hoy - timedelta(days=30)),
     "PeriodoHasta": str(hoy - timedelta(days=20))}]
comprueba(C.nomina_que_cubre(GRUPO, USUARIO, _dia) == "",
          "una nómina de otro periodo NO dispara el aviso")
payroll.list_nominas = lambda g, **k: [
    {"ID": "NOM-OTRO-USR", "Usuario": "otra_persona",
     "PeriodoDesde": str(hoy - timedelta(days=3)),
     "PeriodoHasta": str(hoy + timedelta(days=3))}]
comprueba(C.nomina_que_cubre(GRUPO, USUARIO, _dia) == "",
          "la nómina de OTRA persona tampoco")
payroll.list_nominas = _real

print("")
print("=== LIMPIEZA ===")
ws, _ = timeclock._get_worksheet()
_todas = ws.get_all_records(numericise_ignore=["all"])
_borrar = [i + 2 for i, r in enumerate(_todas)
           if str(r.get("Usuario", "")).strip() == USUARIO]
for fila in sorted(_borrar, reverse=True):
    ws.delete_rows(fila)
wsc = C._ws()
_todasc = wsc.get_all_values()
_borrarc = [i + 1 for i, r in enumerate(_todasc)
            if len(r) > 2 and str(r[2]).strip() == USUARIO]
for fila in sorted(_borrarc, reverse=True):
    wsc.delete_rows(fila)
timeclock._invalidate_records()
C._invalidate()
hojas.invalidar()

print("")
print("=== FOTO DESPUÉS ===")
_f1, _c1 = len(filas_fichaje()), len(correcciones_mias())
_tot1 = len(ws.get_all_records(numericise_ignore=["all"]))
print("  fichajes míos: %d · correcciones mías: %d · filas totales de fichaje: %d"
      % (_f1, _c1, _tot1))
comprueba(_f1 == 0 and _c1 == 0, "no queda ni una fila de la prueba")
comprueba(_tot1 == _tot0, "el fichaje vuelve a %d filas (antes %d)" % (_tot1, _tot0))

print("")
if fallos:
    print("FALLOS: %d" % len(fallos))
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("EJERCICIO COMPLETO - sin fallos y sin rastro")
