"""FLUJO COMPLETO de una localizacion interna, contra la hoja REAL.

Alta -> acceso (las DOS vias) -> fichaje -> pre-start -> gasto -> asignacion puntual
por Planificacion -> seguimiento del admin -> cierre y reapertura.

⚠️ NO se ejercita nada que mande correo/Telegram a personas reales: los checks van
todos en YES y `near_miss=NO` (un check en NO abre alarma y notifica, v373), y la
asignacion se escribe con `update_project` en vez de con el helper de UI que notifica.

Metodo de v344: foto -> ejercitar -> verificar leyendo -> limpiar -> segunda foto.
"""
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os
os.chdir(RAIZ)

import streamlit as st
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "flujo", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "flujo"}

from core import projects as P, expenses as E, timeclock as T, roster as R
from core import prestart, auth, clock, finance as F
from core import timeclock_ui as TU, prestart_ui as PSU

NOMBRE = "ZZZ Almacen Flujo"
OFICINA = "apatel"      # perfil de oficina: asignado PERMANENTE
OBRA    = "tobrien"     # gente de obra: asignado un dia suelto por Planificacion
AJENO   = "jlopez"      # no tiene nada que ver: NO debe verla

ok = True
creado = {"pid": None, "ps": None, "marcas": []}


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def paso(n, t):
    print(f"\n{'─' * 66}\n{n}. {t}\n{'─' * 66}")


def nombre_de(u):
    for x in auth.list_users(GRUPO):
        if x["Usuario"] == u:
            return str(x.get("Nombre") or u)
    return u


def limpiar():
    print(f"\n{'═' * 66}\nLIMPIEZA\n{'═' * 66}")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    sh = gc.open_by_key(T.sheet_id_para("Proyectos", GRUPO))
    pid = creado["pid"]
    if pid:
        for hoja, col in (("Sheet1", "ProyectoID"), ("Gastos", "ProyectoID"),
                          ("PreStarts", "ProyectoID"), ("Proyectos", "ID")):
            try:
                ws = sh.worksheet(hoja)
            except Exception:
                continue
            v = ws.get_all_values()
            if col not in v[0]:
                continue
            i = v[0].index(col)
            filas = [n for n, f in enumerate(v[1:], start=2) if f[i] == pid]
            for r in sorted(filas, reverse=True):
                ws.delete_rows(r)
            print(f"   {hoja}: -{len(filas)}  -> {len(ws.get_all_values())-1}")
    # ⚠️ Las filas de JORNADA no llevan ProyectoID: por firma exacta (lo que se me
    # escapo en v422 y dejo 3 h sueltas en produccion).
    if creado["marcas"]:
        ws = sh.worksheet("Sheet1")
        v = ws.get_all_values()
        ix = {h: v[0].index(h) for h in ("Usuario", "Tipo", "Clock In", "ProyectoID")}
        cand = [n for n, f in enumerate(v[1:], start=2)
                if (f[ix["Usuario"]], f[ix["Clock In"]]) in creado["marcas"]
                and f[ix["Tipo"]] == T.TIPO_GENERAL and not f[ix["ProyectoID"]].strip()]
        for r in sorted(cand, reverse=True):
            ws.delete_rows(r)
        print(f"   Sheet1 (jornada): -{len(cand)}  -> {len(ws.get_all_values())-1}")
    # La semana del roster: se deja al usuario SIN ese dia (no se borra la fila:
    # puede tener otras asignaciones legitimas).
    try:
        _l = R.lunes_de(clock.today(GRUPO))
        _sem = R.get_semana(GRUPO, _l)
        _d = dict(_sem.get(OBRA, {}) or {})
        _dia = R.DIAS_TODOS[clock.today(GRUPO).weekday()]
        if _dia in _d:
            _d.pop(_dia, None)
            R.guardar_persona(GRUPO, _l, OBRA, _d)
            print(f"   Roster: quitada la asignacion de {OBRA} el {_dia}")
    except Exception as e:
        print(f"   !! roster: {e}")
    for f in (P._invalidate, E._invalidate, T._invalidate_records, R._invalidate):
        try:
            f()
        except Exception:
            pass
    try:
        T._ids_internos.clear()
    except Exception:
        pass


try:
    # ── 1 ────────────────────────────────────────────────────────────
    paso(1, f"El admin da de alta el almacén y asigna a {OFICINA} (perfil de oficina)")
    _ok, pid = P.create_project(GRUPO, NOMBRE, tipo="Almacén",
                                ubicacion="12 Distribution Dr, Chullora NSW",
                                ingeniero="Bobo", campo_asignados=[OFICINA],
                                creado_por="flujo")
    assert _ok, pid
    creado["pid"] = pid
    print(f"   -> {pid}")
    P._invalidate(); T._ids_internos.clear(); time.sleep(1.2)
    prj = P.get_project(pid)
    chk("es interna", P.es_interno(prj))
    chk("nace Abierta", str(prj.get("Estado")), P.INTERNO_ABIERTA)
    chk("sin cronograma", len(P.list_activities(pid)), 0)
    chk(f"{OFICINA} queda asignado", OFICINA in str(prj.get("CampoAsignados")))

    # ── 2 ────────────────────────────────────────────────────────────
    paso(2, "Quién la ve en el fichaje (las DOS vías, y quien no tiene ninguna)")
    def ve(u):
        lst, _ = TU._proyectos_para("campo", u, GRUPO)
        return pid in [str(p.get("ID")) for p in lst]
    chk(f"{OFICINA} (asignado permanente) la ve", ve(OFICINA))
    chk(f"{AJENO} (sin vía) NO la ve", ve(AJENO), False)
    chk(f"{OBRA} (aún sin asignar) NO la ve", ve(OBRA), False)
    chk("el ADMIN la ve", pid in [str(p.get("ID")) for p in
                                  TU._proyectos_para("administrador", "Bobo", GRUPO)[0]])

    # ── 3 ────────────────────────────────────────────────────────────
    paso(3, f"{OFICINA} ficha en el almacén y cierra la jornada")
    _n = nombre_de(OFICINA)
    _r = T.fichar_proyecto(_n, NOMBRE, GRUPO, OFICINA, pid)
    print(f"   fichar_proyecto -> {_r}")
    T._invalidate_records(); time.sleep(1.5)
    _s = T.open_sessions(_n, GRUPO, OFICINA)
    chk("abre jornada Y segmento de proyecto", sorted(_s.keys()),
        sorted([T.TIPO_GENERAL, T.TIPO_PROYECTO]))
    chk("el segmento apunta al almacén", str(_s[T.TIPO_PROYECTO].get("proyecto_id")), pid)
    _ci = _s[T.TIPO_GENERAL].get("clock_in") or _s[T.TIPO_GENERAL].get("Clock In")
    creado["marcas"].append((OFICINA, str(_ci)))
    time.sleep(1.0)
    # ⚠️ Se cierra con hora EXPLÍCITA (`out_ts`, el arreglo de v164). Mi primera versión
    # llamaba a `cerrar_jornada` sin más y la sesión duraba 4 segundos → la fila quedaba
    # con **0.0 h**, así que mano de obra, `interno`, la conciliación y el desglose de la
    # ficha salían todos a cero y yo lo leí como cinco fallos del código. Eran de la
    # prueba: una jornada de 4 segundos no tiene horas que repartir.
    _fin = clock.now(GRUPO) + timedelta(hours=6)
    for _tp in (T.TIPO_PROYECTO, T.TIPO_GENERAL):
        _rc = T.clock_out(_n, GRUPO, tipo=_tp, usuario=OFICINA, out_ts=_fin)
        print(f"   clock_out {_tp:<9} -> {_rc}")
    T._invalidate_records(); T._ids_internos.clear(); time.sleep(1.5)
    # ⚠️ `open_sessions` devuelve SIEMPRE las dos claves, con None cuando no hay nada
    # abierto (lo dice su docstring) — no un dict vacío, como yo había supuesto.
    _s2 = T.open_sessions(_n, GRUPO, OFICINA)
    chk("no queda nada abierto", [k for k, v in _s2.items() if v], [])
    _hh = {d["usuario"]: d for d in T.group_hours(GRUPO)}.get(OFICINA, {})
    chk("la jornada registra ~6 h", 5.9 <= _hh.get("interno", 0) <= 6.1)

    # ── 4 ────────────────────────────────────────────────────────────
    paso(4, "Pre-Start del almacén (todo YES: no dispara avisos a nadie)")
    chk(f"el almacén sale en el selector de Pre-Start de {OFICINA}",
        pid in [str(p.get("ID")) for p in PSU._projects_for("campo", OFICINA, GRUPO)])
    data = {"proyecto_id": pid, "proyecto_nombre": NOMBRE, "grupo": GRUPO,
            "fecha": clock.today(GRUPO), "hora": "07:30",
            "location": "12 Distribution Dr, Chullora NSW",
            "facilitador": _n, "creado_por": OFICINA,
            "near_miss": "NO", "near_miss_desc": "",
            "s1": {k: "YES" for k, _ in prestart.CHECKS_S1},
            "s3": {k: "YES" for k, _ in prestart.CHECKS_S3},
            "activities_notes": "Recepción y despacho de material.",
            "general_notes": "Montacargas revisado.",
            "attendees": [{"name": _n, "initial": "AP", "usuario": OFICINA}]}
    res = prestart.submit(data)
    print(f"   submit -> ok={res['ok']} id={res['id']} alarma={res['alarma']} "
          f"checks_no={res['checks_no']}")
    chk("se registra", res["ok"])
    chk("NO abre alarma (todo en YES)", res["alarma"] or res["alarma_checks"], False)
    creado["ps"] = res["id"]
    time.sleep(1.2)
    _r3 = prestart.submit(dict(data))
    chk("un SEGUNDO pre-start el mismo día se bloquea (v407)", bool(_r3.get("ya_hay")))
    chk("...y dice cuál es", _r3.get("ya_hay"), res["id"])
    chk("la charla de hoy consta hecha", prestart.hecho_hoy(pid, GRUPO))

    # ── 5 ────────────────────────────────────────────────────────────
    paso(5, "Gasto de administración")
    _ok5, _m5 = E.add(pid, GRUPO, 640.0, categoria="Otros", proveedor="Arriendo Chullora",
                      descripcion="alquiler mensual", creado_por="flujo")
    chk("recibo cargado", _ok5)
    E._invalidate(); time.sleep(1.5)
    _c = E.project_cost(pid, GRUPO)
    chk("el costo del almacén incluye compras y mano de obra",
        _c["compras"] > 0 and _c["mano_obra"] > 0)
    print(f"   compras={_c['compras']} mano_obra={_c['mano_obra']} total={_c['total']}")

    # ── 6 ────────────────────────────────────────────────────────────
    paso(6, f"El admin asigna a {OBRA} al almacén HOY, desde Planificación")
    _hoy = clock.today(GRUPO)
    _lun = R.lunes_de(_hoy)
    _dia = R.DIAS_TODOS[_hoy.weekday()]
    _sem = R.get_semana(GRUPO, _lun)
    _dst = dict(_sem.get(OBRA, {}) or {})
    _dst[_dia] = {"asig": pid, "nota": "apoyo en almacén"}
    _r6 = R.guardar_persona(GRUPO, _lun, OBRA, _dst)
    print(f"   guardar_persona -> {_r6}")
    R._invalidate(); time.sleep(1.5)
    _as = R.asignaciones_dia(GRUPO, OBRA, _hoy)
    chk("el roster se lo asigna hoy", [a["proyecto_id"] for a in _as], [pid])
    chk("...con su nombre resuelto (celda no muda)",
        _as[0]["etiqueta"] if _as else "", NOMBRE)
    chk(f"AHORA {OBRA} SÍ la ve en el fichaje (2ª vía)", ve(OBRA))
    chk(f"...y {AJENO} sigue sin verla", ve(AJENO), False)

    # ── 7 ────────────────────────────────────────────────────────────
    paso(7, "El admin ve el seguimiento — y NADA se cuela en el dinero de obra")
    time.sleep(1.0)
    chk("NO está en la cartera de obras",
        pid in [p["ID"] for p in P.list_projects(grupo=GRUPO)], False)
    chk("SÍ está en Localizaciones",
        pid in [p["ID"] for p in P.list_locations(GRUPO)])
    _gh = {d["usuario"]: d for d in T.group_hours(GRUPO)}
    _o = _gh.get(OFICINA, {})
    chk(f"las horas de {OFICINA} van a `interno`, no a `proyecto`",
        _o.get("interno", 0) > 0)
    print(f"   {OFICINA}: jornada={_o.get('general')} obra={_o.get('proyecto')} "
          f"interno={_o.get('interno')} costo_obra=${_o.get('costo')} "
          f"costo_interno=${_o.get('costo_interno')}")
    _cc = F.conciliacion_mo(GRUPO)
    chk("la conciliación lo cuenta como estructura", _cc["interno"] > 0)
    _lb = E.labor_breakdown(pid, GRUPO)
    chk("la ficha sabe quién trabajó aquí",
        OFICINA in [i["usuario"] for i in _lb.get("items", [])])

    # ── 8 ────────────────────────────────────────────────────────────
    paso(8, "Se cierra el almacén — el histórico se conserva y se puede reabrir")
    _ok8, _m8 = P.update_project(pid, {"EstadoManual": P.INTERNO_CERRADA,
                                       "Estado": P.derive_estado(0, P.INTERNO_CERRADA,
                                                                 "Almacén")})
    chk("se cierra", _ok8)
    P._invalidate(); time.sleep(1.5)
    chk("sale de la lista por defecto",
        pid in [p["ID"] for p in P.list_locations(GRUPO)], False)
    chk("...pero se ve pidiéndolas", pid in [p["ID"] for p in
                                             P.list_locations(GRUPO, incluir_cerradas=True)])
    chk("su gasto SIGUE contando en el grupo",
        pid in [str(f["id"]) for f in E.group_expenses(GRUPO)["proyectos"]])
    T._ids_internos.clear(); time.sleep(1.0)
    chk("sus horas SIGUEN siendo estructura (no pasan a obra)",
        T.group_hours(GRUPO) and
        {d["usuario"]: d for d in T.group_hours(GRUPO)}.get(OFICINA, {}).get("interno", 0) > 0)
    _ok8b, _ = P.update_project(pid, {"EstadoManual": "",
                                      "Estado": P.derive_estado(0, "", "Almacén")})
    P._invalidate(); time.sleep(1.5)
    chk("se REABRE y vuelve a Abierta",
        str(P.get_project(pid).get("Estado")), P.INTERNO_ABIERTA)

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
        print("  !! LIMPIEZA FALLIDA — revisar a mano:", creado)

print("\n" + ("FLUJO COMPLETO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
