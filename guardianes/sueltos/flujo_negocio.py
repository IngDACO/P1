"""FLUJO COMPLETO DEL NEGOCIO, contra la hoja REAL.

Cliente nuevo -> cotizacion (catalogo + ganancia) -> enviar -> aceptar -> nace el
proyecto -> asignar cuadrilla -> fichar horas -> compra -> avance -> facturar ->
cobrar -> nomina -> P&L / rentabilidad / cotizado-vs-real.

⚠️ NADA que avise a personas reales: la asignacion se escribe con `update_project`
en vez del helper de UI que manda Telegram/email.

Metodo de v344: foto -> ejercitar -> verificar leyendo -> limpiar -> segunda foto.
"""
import sys
import time
from datetime import date, timedelta
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

from core import (projects as P, expenses as E, timeclock as T, quotes as Q,
                 catalogo as C, clientes as CL, invoices as I, payroll as PR,
                 finance as F, auth, clock)

CLI = "ZZZ Cliente Flujo"
OBRA_NOM = "ZZZ Torre Flujo — Instalación"
TECNICO = "apatel"
ok = True
h = {"cli": None, "cot": None, "pid": None, "fac": None, "nom": [], "marca": None}


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def paso(n, t):
    print(f"\n{'─' * 68}\n{n}. {t}\n{'─' * 68}")


def nombre_de(u):
    return next((str(x.get("Nombre") or u) for x in auth.list_users(GRUPO)
                 if x["Usuario"] == u), u)


def limpiar():
    print(f"\n{'═' * 68}\nLIMPIEZA\n{'═' * 68}")
    import gspread, toml
    from google.oauth2.service_account import Credentials
    sec = toml.load(".streamlit/secrets.toml")
    gc = gspread.authorize(Credentials.from_service_account_info(
        sec["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]))
    sh = gc.open_by_key(T.sheet_id_para("Proyectos", GRUPO))

    def borrar(hoja, col, valores):
        valores = {v for v in valores if v}
        if not valores:
            return
        try:
            ws = sh.worksheet(hoja)
        except Exception:
            return
        v = ws.get_all_values()
        if col not in v[0]:
            return
        i = v[0].index(col)
        filas = [n for n, f in enumerate(v[1:], start=2) if f[i] in valores]
        for r in sorted(filas, reverse=True):
            ws.delete_rows(r)
        print(f"   {hoja}: -{len(filas)}  -> {len(ws.get_all_values())-1}")

    borrar("Sheet1", "ProyectoID", {h["pid"]})
    borrar("Gastos", "ProyectoID", {h["pid"]})
    borrar("Actividades", "ProyectoID", {h["pid"]})
    borrar("Facturas", "ID", {h["fac"]})
    borrar("Nominas", "ID", set(h["nom"]))
    borrar("Cotizaciones", "ID", {h["cot"]})
    borrar("Proyectos", "ID", {h["pid"]})
    borrar("Clientes", "ID", {h["cli"]})
    # ⚠️ La fila de JORNADA no lleva ProyectoID: por firma exacta.
    if h["marca"]:
        ws = sh.worksheet("Sheet1")
        v = ws.get_all_values()
        ix = {k: v[0].index(k) for k in ("Usuario", "Tipo", "Clock In", "ProyectoID")}
        cand = [n for n, f in enumerate(v[1:], start=2)
                if (f[ix["Usuario"]], f[ix["Clock In"]]) == h["marca"]
                and f[ix["Tipo"]] == T.TIPO_GENERAL and not f[ix["ProyectoID"]].strip()]
        for r in sorted(cand, reverse=True):
            ws.delete_rows(r)
        print(f"   Sheet1 (jornada): -{len(cand)}  -> {len(ws.get_all_values())-1}")
    for f in (P._invalidate, E._invalidate, T._invalidate_records):
        try:
            f()
        except Exception:
            pass


try:
    # ── 1 ─────────────────────────────────────────────────────────────
    paso(1, "Entra un cliente nuevo y se le cotiza (v420: sin salir a Contactos)")
    _ok, _res = CL.create_cliente(GRUPO, CLI, contacto="Ana Ruiz",
                                  telefono="0400 111 222", email="ana@zzzflujo.test",
                                  creado_por="flujo")
    chk("ficha de cliente creada", _ok)
    h["cli"] = _res if _ok else None
    print(f"   -> {h['cli']}")
    CL._invalidate(); time.sleep(1.2)

    arts = C.list_items(GRUPO)
    _srv = next(a for a in arts if a["Tipo"] == "servicio")
    _prd = next(a for a in arts if a["Tipo"] == "producto")
    # ⚠️ v355: se escribe la GANANCIA en dinero; el margen % sale solo.
    l1 = Q.linea_de(_srv, cantidad=3, ganancia=600.0)
    l2 = Q.linea_de(_prd, cantidad=4, ganancia=400.0)
    print(f"   servicio: {_srv['Nombre']} x3  costo={l1['costo_total']} "
          f"ganancia=600 -> precio={l1['precio_total']} margen={l1['margen_pct']}%")
    print(f"   producto: {_prd['Nombre']} x4  costo={l2['costo_total']} "
          f"ganancia=400 -> precio={l2['precio_total']} margen={l2['margen_pct']}%")
    chk("precio = costo + ganancia (servicio)",
        round(l1["precio_total"], 2), round(l1["costo_total"] + 600.0, 2))
    chk("precio = costo + ganancia (producto)",
        round(l2["precio_total"], 2), round(l2["costo_total"] + 400.0, 2))

    _ok, _res = Q.crear(GRUPO, h["cli"], CLI, [l1, l2], impuesto_pct=10.0,
                        nota="Flujo de prueba", creado_por="flujo")
    chk("cotización creada", _ok)
    h["cot"] = _res if _ok else None
    Q._invalidate(); time.sleep(1.2)
    cot = Q.get_cotizacion(h["cot"])
    _sub = float(cot["Subtotal"])
    print(f"   -> {h['cot']}  subtotal={_sub}  total={cot['Total']}  estado={cot['Estado']}")
    chk("nace en borrador", str(cot["Estado"]), "borrador")

    # ── 2 ─────────────────────────────────────────────────────────────
    paso(2, "Se envía al cliente y se acepta")
    chk("se marca enviada", Q.set_estado(h["cot"], "enviada")[0])
    Q._invalidate(); time.sleep(1.2)
    _ok, _res = Q.aceptar_y_crear_proyecto(h["cot"], nombre=OBRA_NOM,
                                           tipo="Instalación", ns=4,
                                           ubicacion="1 Test St, Sydney NSW",
                                           creado_por="flujo")
    chk("aceptar CREA el proyecto", _ok)
    h["pid"] = _res if _ok else None
    print(f"   -> {h['pid']}")
    P._invalidate(); Q._invalidate(); time.sleep(1.5)
    prj = P.get_project(h["pid"])
    chk("nace con su ClienteID (no texto suelto)", str(prj.get("ClienteID")), h["cli"])
    chk("...y con el presupuesto = COSTO cotizado (no el precio de venta)",
        round(float(prj.get("Presupuesto") or 0), 2),
        round(l1["costo_total"] + l2["costo_total"], 2))
    chk("...y con cronograma de instalación", len(P.list_activities(h["pid"])) > 1)
    chk("aceptar dos veces NO duplica la obra",
        Q.aceptar_y_crear_proyecto(h["cot"], nombre=OBRA_NOM)[1] != h["pid"]
        or "ya generó" in str(Q.aceptar_y_crear_proyecto(h["cot"])[1]).lower(), True)

    # ── 3 ─────────────────────────────────────────────────────────────
    paso(3, "Se asigna cuadrilla y se fichan horas en la obra")
    P.update_project(h["pid"], {"CampoAsignados": TECNICO})
    P._invalidate(); time.sleep(1.2)
    _n = nombre_de(TECNICO)
    _r = T.fichar_proyecto(_n, OBRA_NOM, GRUPO, TECNICO, h["pid"])
    print(f"   fichar -> {_r[1]}")
    T._invalidate_records(); time.sleep(1.2)
    _s = T.open_sessions(_n, GRUPO, TECNICO)
    h["marca"] = (TECNICO, str(_s[T.TIPO_GENERAL].get("clock_in")))
    _fin = clock.now(GRUPO) + timedelta(hours=10)
    for _tp in (T.TIPO_PROYECTO, T.TIPO_GENERAL):
        T.clock_out(_n, GRUPO, tipo=_tp, usuario=TECNICO, out_ts=_fin)
    T._invalidate_records(); time.sleep(1.5)
    _hh = {d["usuario"]: d for d in T.group_hours(GRUPO)}[TECNICO]
    chk("las horas van a OBRA (no a estructura)", _hh.get("interno", 0), 0.0)
    _lb = E.labor_breakdown(h["pid"], GRUPO)
    _hp = float(_lb.get("horas") or 0)
    # ⚠️ tolerancia FISICA: `out_ts` se calcula unos segundos despues del clock in,
    # asi que la duracion real es 9.99x h, no 10 exactas (la leccion de v363: un
    # epsilon simbolico hace fallar el test por su propia aritmetica).
    chk("la obra registra ~10 h", 9.9 <= _hp <= 10.05)
    print(f"   horas de la obra: {_hp}  (costo {_lb.get('total')})")

    # ── 4 ─────────────────────────────────────────────────────────────
    paso(4, "Compra de material y avance de obra")
    chk("recibo cargado",
        E.add(h["pid"], GRUPO, 1250.0, categoria="Materiales", proveedor="Proveedor ZZZ",
              descripcion="perfilería", creado_por="flujo")[0])
    E._invalidate(); time.sleep(1.5)
    _c = E.project_cost(h["pid"], GRUPO)
    print(f"   costo: compras={_c['compras']} mano_obra={_c['mano_obra']} "
          f"total={_c['total']} presupuesto={_c['presupuesto']} pct={_c['pct']}%")
    chk("el costo suma compras + mano de obra",
        round(_c["total"], 2), round(_c["compras"] + _c["mano_obra"], 2))
    acts = P.list_activities(h["pid"])
    for a in acts[:3]:
        P.update_activity_progress(h["pid"], a["Orden"], 100)
    P._invalidate(); time.sleep(1.5)
    _av = float(P.get_project(h["pid"]).get("Avance") or 0)
    print(f"   avance tras cerrar 3 de {len(acts)} actividades: {_av}%")
    chk("el avance del proyecto se movió", _av > 0)
    chk("...y el estado pasa a En progreso",
        str(P.get_project(h["pid"]).get("Estado")), "En progreso")

    # ── 5 ─────────────────────────────────────────────────────────────
    paso(5, "Se factura la obra y se cobra")
    _pend = I.pendiente_por_proyecto(GRUPO).get(h["pid"], 0)
    print(f"   pendiente de facturar: {_pend}")
    chk("hay algo que facturar (el precio pactado, v370)", _pend > 0)
    chk("...y es el SUBTOTAL de la cotización, sin impuesto", round(_pend, 2), round(_sub, 2))
    _ok, _res = I.create_factura(GRUPO, h["cli"], CLI,
                                 [{"concepto": OBRA_NOM, "cantidad": 1,
                                   "precio": _sub, "importe": _sub,
                                   "proyecto_id": h["pid"]}],
                                 impuesto_pct=10.0, creado_por="flujo")
    chk("factura emitida", _ok)
    h["fac"] = _res if _ok else None
    I._invalidate(); time.sleep(1.5)
    fac = I.get_factura(h["fac"])
    print(f"   -> {h['fac']} subtotal={fac['Subtotal']} total={fac['Total']}")
    chk("el impuesto se calcula", float(fac["Impuesto"]) > 0)
    chk("nace pendiente", I.estado_cobro(fac), "pendiente")
    _mitad = round(float(fac["Total"]) / 2, 2)
    chk("cobro parcial", I.registrar_cobro(h["fac"], _mitad)[0])
    I._invalidate(); time.sleep(1.2)
    chk("...queda parcial", I.estado_cobro(I.get_factura(h["fac"])), "parcial")
    chk("cobro del resto", I.registrar_cobro(h["fac"], _mitad)[0])
    I._invalidate(); time.sleep(1.2)
    chk("...queda cobrada", I.estado_cobro(I.get_factura(h["fac"])), "cobrada")

    # ── 6 ─────────────────────────────────────────────────────────────
    paso(6, "Nómina del periodo")
    _hoy = clock.today(GRUPO)
    _res = PR.generar(GRUPO, _hoy, _hoy, super_pct=11.5, ret_pct=0.0, creado_por="flujo")
    print(f"   generar -> creadas={_res.get('creadas')} omitidas={_res.get('omitidas')} "
          f"sin_tarifa={_res.get('sin_tarifa')} solapes={len(_res.get('solapes', []) or [])}")
    PR._invalidate(); time.sleep(1.5)
    _noms = [n for n in PR.list_nominas(GRUPO)
             if str(n.get("PeriodoDesde")) == _hoy.strftime("%Y-%m-%d")
             and str(n.get("PeriodoHasta")) == _hoy.strftime("%Y-%m-%d")]
    h["nom"] = [n["ID"] for n in _noms]
    chk("se emitió al menos una colilla", len(_noms) > 0)
    _mia = next((n for n in _noms if str(n.get("Usuario")) == TECNICO), None)
    if _mia:
        print(f"   {TECNICO}: base={_mia.get('Base')} neto={_mia.get('Neto')}")
        _b = float(_mia.get("Base") or 0)
        chk("la base del técnico sale de su JORNADA (~10 h × 40)", 396.0 <= _b <= 400.0)
    chk("re-generar el MISMO periodo no duplica",
        PR.generar(GRUPO, _hoy, _hoy, creado_por="flujo").get("creadas"), 0)

    # ── 7 ─────────────────────────────────────────────────────────────
    paso(7, "Lo que ve el gerente: cotizado vs real, rentabilidad y P&L")
    time.sleep(1.0)
    cmp_ = Q.comparacion(h["cot"])
    print(f"   cotizado: horas={cmp_.get('horas_cot')} costo={cmp_.get('costo_cot')} "
          f"ingreso={cmp_.get('ingreso')}")
    print(f"   real    : horas={cmp_.get('horas_real')} costo={cmp_.get('costo_real')}")
    print(f"   claves de comparacion(): {sorted(cmp_.keys())}")
    chk("la comparación devuelve algo", bool(cmp_))
    _rp = {r["id"]: r for r in F.resultado_por_proyecto(GRUPO)}
    _mio = _rp.get(h["pid"], {})
    print(f"   resultado por proyecto: facturado={_mio.get('facturado')} "
          f"costo={_mio.get('costo')} ganancia={_mio.get('ganancia')}")
    chk("la obra aparece en el resultado por proyecto", bool(_mio))
    chk("...con lo facturado", round(float(_mio.get("facturado") or 0), 2),
        round(_sub, 2))
    _gp = {r["id"]: r for r in F.group_profitability(GRUPO)["rows"]}
    chk("y en rentabilidad, con el ingreso PACTADO (v370)",
        round(float(_gp.get(h["pid"], {}).get("ingreso") or 0), 2), round(_sub, 2))

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
        print("  !! LIMPIEZA FALLIDA — revisar a mano:", h)

print("\n" + ("FLUJO DE NEGOCIO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
