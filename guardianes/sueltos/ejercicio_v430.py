"""Ejercita v430 contra la hoja REAL: ausencia → tablero → NÓMINA → conciliación.

Método de v344: foto → ejercitar → verificar leyendo → limpiar → segunda foto.
Lo que de verdad importa aquí es el dinero: que aprobar unas vacaciones NO signifique
cobrar $0, que quien estuvo fuera el periodo entero reciba colilla igual, y que la
cadena de v313 siga cerrando.
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
import os                                                       # noqa: E402
os.chdir(RAIZ)

import streamlit as st                                          # noqa: E402
GRUPO = "cliente1"
st.session_state["auth"] = {"usuario": "ejv430", "rol": "administrador",
                            "grupo": GRUPO, "nombre": "ejv430"}

from core import ausencias as AU, payroll as PR, finance as F   # noqa: E402
from core import timeclock as TC, auth, roster as R             # noqa: E402

D0, D1 = date(2026, 8, 19), date(2026, 8, 30)      # quincena sin nóminas emitidas
ok = True
aus_creadas, nom_creadas = [], []
roster_backup = {}          # {(usuario, lunes): celdas originales}


def chk(t, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"   {'OK  ' if b else 'FALLO'} {t}: {real!r}")
    if not b:
        print(f"          esperado: {esp!r}")


def paso(n, t):
    print(f"\n{'─' * 70}\n{n}. {t}\n{'─' * 70}")


def _ws_de(hoja):
    sh = TC._abrir(TC.sheet_id_para(hoja, GRUPO))
    return sh.worksheet(hoja)


def limpiar():
    print(f"\n{'═' * 70}\nLIMPIEZA\n{'═' * 70}")
    # 1. nóminas creadas (fila entera: son de prueba, no se anulan y se dejan)
    if nom_creadas:
        w = _ws_de(PR.NOMINAS_SHEET)
        v = w.get_all_values()
        filas = [i for i, f in enumerate(v[1:], start=2) if f and f[0] in set(nom_creadas)]
        for r in sorted(filas, reverse=True):
            w.delete_rows(r)
        print(f"   Nominas: -{len(filas)} → {len(w.get_all_values()) - 1} filas")
        PR._invalidate()
    # 2. el tablero, a como estaba
    for (usr, lunes), celdas in roster_backup.items():
        okr, msg = R.guardar_persona(GRUPO, lunes, usr, celdas)
        print(f"   Roster {usr} {lunes}: {'restaurado' if okr else msg}")
    # 3. las ausencias
    if aus_creadas:
        w = _ws_de(AU.SHEET)
        v = w.get_all_values()
        filas = [i for i, f in enumerate(v[1:], start=2) if f and f[0] in set(aus_creadas)]
        for r in sorted(filas, reverse=True):
            w.delete_rows(r)
        print(f"   Ausencias: -{len(filas)} → {len(w.get_all_values()) - 1} filas")
        AU._invalidate()


try:
    # ── 1 ────────────────────────────────────────────────────────
    paso(1, f"Quién tiene horas fichadas en {D0} → {D1}")
    horas = TC.horas_por_usuario_rango(GRUPO, D0, D1)
    for k, v in sorted(horas.items()):
        print(f"   {k:12} {v['horas']:>7.2f} h")
    rates = auth.rate_map(GRUPO)
    con_horas = sorted(k for k in horas if rates.get(k, 0) > 0)
    chk("hay gente con horas en el periodo", len(con_horas) > 0, True)
    # alguien con TARIFA y SIN horas: el caso que antes se quedaba sin colilla
    sin_horas = [u["Usuario"] for u in auth.list_users(GRUPO)
                 if str(u.get("Rol", "")) == "campo"
                 and str(u.get("Activo", "SI")).upper() != "NO"
                 and rates.get(str(u.get("Usuario")), 0) > 0
                 and str(u.get("Usuario")) not in horas]
    print(f"   con horas y tarifa: {con_horas}")
    print(f"   CON tarifa y SIN horas: {sin_horas}")
    chk("hay alguien con tarifa y sin horas (el caso nuevo)", bool(sin_horas), True)
    U_MIXTO = con_horas[0]
    U_SOLO_AUS = sin_horas[0]

    # ── 2 ────────────────────────────────────────────────────────
    paso(2, f"{U_MIXTO} pide VACACIONES dentro del periodo")
    v0 = date(2026, 8, 24)                     # lunes
    v1 = date(2026, 8, 26)                     # miércoles → 3 días hábiles
    _nom = next((str(u.get("Nombre") or U_MIXTO) for u in auth.list_users(GRUPO)
                 if str(u.get("Usuario")) == U_MIXTO), U_MIXTO)
    _ok, aid = AU.solicitar(GRUPO, U_MIXTO, _nom, AU.VACACIONES, v0, v1,
                            motivo="Prueba v430")
    chk("se crea la solicitud", _ok)
    aus_creadas.append(aid)
    AU._invalidate(); time.sleep(1.2)
    chk("nace PENDIENTE", str(AU.get(aid).get("Estado")), AU.PENDIENTE)
    chk("cuenta 3 días hábiles", str(AU.get(aid).get("Dias")), "3")

    # ── 3 ────────────────────────────────────────────────────────
    paso(3, "El admin ve las obras que quedarían sin esa persona ANTES de decidir")
    ch = AU.choques(GRUPO, U_MIXTO, v0, v1)
    print(f"   choques: {[(str(c['fecha']), c['etiqueta']) for c in ch]}")
    if ch:
        subs = AU.sustitutos(GRUPO, ch[0]["fecha"], ch[0].get("proyecto_id"),
                             excluir=U_MIXTO)
        print(f"   sustitutos para {ch[0]['fecha']}: "
              f"{[(s['nombre'], s['cumple']) for s in subs]}")
    chk("`choques` responde sin reventar", isinstance(ch, list), True)

    # ── 4 ────────────────────────────────────────────────────────
    paso(4, "Aprobar: baja el saldo Y se escribe en el planificador")
    s_antes = AU.saldo(GRUPO, U_MIXTO, AU.VACACIONES)
    chk("antes de aprobar el saldo NO baja", s_antes["usados"], 0.0)
    # respaldo del tablero ANTES de que la ausencia lo pise
    for d in AU.dias_del_rango(v0, v1, True):
        lun = R.lunes_de(d)
        if (U_MIXTO, lun) not in roster_backup:
            roster_backup[(U_MIXTO, lun)] = dict(
                (R.get_semana(GRUPO, lun).get(U_MIXTO, {}) or {}))
    _ok2, _m = AU.resolver(aid, True, "ejv430", nota="Buen viaje")
    chk("se aprueba", _ok2)
    _ok3, n = AU.aplicar_al_roster(AU.get(aid) or {})
    chk("se marca en el tablero", _ok3)
    print(f"   días escritos en el planificador: {n}")
    AU._invalidate(); R._invalidate(); time.sleep(1.5)
    _sem = R.get_semana(GRUPO, R.lunes_de(v0))
    _cel = R._norm_cell((_sem.get(U_MIXTO, {}) or {}).get("lun", {}))
    chk("el lunes queda como LEAVE",
        [i.get("asig") for i in _cel.get("items", [])], ["LEAVE"])
    chk("...con el ID de la ausencia en la nota", aid in str(_cel.get("nota", "")))
    s = AU.saldo(GRUPO, U_MIXTO, AU.VACACIONES)
    chk("ahora sí baja el saldo", s["usados"], 3.0)
    chk("quedan 17 de 20", s["restantes"], 17.0)

    # ── 5 ────────────────────────────────────────────────────────
    paso(5, f"{U_SOLO_AUS} está fuera TODO el periodo (0 h fichadas)")
    _n2 = next((str(u.get("Nombre") or U_SOLO_AUS) for u in auth.list_users(GRUPO)
                if str(u.get("Usuario")) == U_SOLO_AUS), U_SOLO_AUS)
    _ok4, bid = AU.solicitar(GRUPO, U_SOLO_AUS, _n2, AU.ENFERMEDAD, D0, D1,
                             motivo="Prueba v430", incluir_findes=True)
    chk("la baja por enfermedad se registra", _ok4)
    aus_creadas.append(bid)
    AU._invalidate(); time.sleep(1.2)
    chk("nace APROBADA (no espera a nadie)", str(AU.get(bid).get("Estado")), AU.APROBADA)

    # ── 6 ────────────────────────────────────────────────────────
    paso(6, "Horas pagadas del periodo (lo que la nómina va a usar)")
    hp = AU.horas_pagadas_grupo(GRUPO, D0, D1)
    for k, v in sorted(hp.items()):
        print(f"   {k:12} {v['dias']:>4.0f} d → {v['horas']:>6.1f} h   {v['por_tipo']}")
    chk(f"{U_MIXTO}: 3 días × 8 h", hp[U_MIXTO]["horas"], 24.0)
    # ⚠️ LA INVARIANTE: se paga exactamente lo que se descontó del saldo. Sin ella,
    # un rango pedido «con fin de semana» quitaba 12 días y pagaba 8.
    for _a in (AU.get(aid), AU.get(bid)):
        _u = str(_a.get("Usuario"))
        chk(f"lo pagado a {_u} = sus Días × 8 h (rango entero dentro del periodo)",
            hp[_u]["dias"], float(_a.get("Dias")))
    chk(f"{U_SOLO_AUS} pidió el rango con findes",
        AU.incluye_findes(AU.get(bid)), True)

    # ── 7 ────────────────────────────────────────────────────────
    paso(7, "GENERAR la nómina del periodo")
    res = PR.generar(GRUPO, D0, D1, super_pct=11.5, ret_pct=15.0,
                     creado_por="ejv430")
    print(f"   {res}")
    chk("no hay error", "error" not in res)
    chk("no hay solapes con nóminas existentes", res.get("solapadas"), [])
    PR._invalidate(); time.sleep(1.5)
    noms = [n for n in PR.list_nominas(GRUPO)
            if str(n.get("PeriodoDesde")) == str(D0)
            and str(n.get("PeriodoHasta")) == str(D1)]
    nom_creadas = [str(n.get("ID")) for n in noms]
    print(f"   creadas: {nom_creadas}")

    def de(u):
        return next((n for n in noms if str(n.get("Usuario")) == u), None)

    # 7a · el que trabajó Y tuvo vacaciones
    nm = de(U_MIXTO)
    chk(f"{U_MIXTO} tiene colilla", nm is not None)
    tar = float(rates[U_MIXTO])
    _hw = float(horas[U_MIXTO]["horas"])
    print(f"   {U_MIXTO}: {_hw:.2f} h fichadas × ${tar} · vacaciones 24 h")
    chk("la columna Horas sigue siendo lo TRABAJADO",
        round(float(nm["Horas"]), 2), round(_hw, 2))
    chk("la Base sigue siendo lo trabajado × tarifa",
        round(float(nm["Base"]), 2), round(_hw * tar, 2))
    cs = PR.conceptos_de(nm)
    _dev = [c for c in cs if str(c.get("origen")) == "ausencia"]
    chk("hay UN devengo de ausencia", len(_dev), 1)
    chk("...por 24 h × tarifa", round(float(_dev[0]["monto"]), 2), round(24 * tar, 2))
    print(f"   concepto: {_dev[0]['concepto']}")
    _bruto = round(float(nm["Base"]) + float(_dev[0]["monto"]), 2)
    _ret = next(c for c in cs if str(c.get("tipo")) == "deduccion")
    _sup = next(c for c in cs if str(c.get("tipo")) == "aporte")
    chk("la retención se calcula sobre base + ausencia",
        round(float(_ret["monto"]), 2), round(_bruto * 0.15, 2))
    chk("el super también", round(float(_sup["monto"]), 2), round(_bruto * 0.115, 2))
    chk("el neto = base + devengo − deducción (el aporte no resta)",
        round(float(nm["Neto"]), 2),
        round(_bruto - round(_bruto * 0.15, 2), 2))

    # 7b · el que NO fichó nada
    nb = de(U_SOLO_AUS)
    chk(f"{U_SOLO_AUS} RECIBE colilla pese a 0 h fichadas", nb is not None)
    if nb:
        chk("...con Base 0 (no trabajó)", round(float(nb["Base"]), 2), 0.0)
        _d2 = [c for c in PR.conceptos_de(nb) if str(c.get("origen")) == "ausencia"]
        chk("...y toda su paga es la baja", len(_d2), 1)
        print(f"   {U_SOLO_AUS}: neto ${float(nb['Neto']):,.2f} — {_d2[0]['concepto']}")
        chk("...y su neto NO es cero", float(nb["Neto"]) > 0)

    # ── 8 ────────────────────────────────────────────────────────
    paso(8, "La conciliación de v313 sigue cerrando (y ve las ausencias)")
    cc = F.conciliacion_mo(GRUPO, D0, D1)
    for k in ("cargado", "cobrado_no_pagado", "pagado_no_cargado", "base_teorica",
              "base_nomina", "ausencias", "aportes", "costo_real", "sin_explicar"):
        print(f"   {k:20} {cc[k]:>12,.2f}")
    _sum_dev = round(sum(float(c["monto"]) for n in noms
                         for c in PR.conceptos_de(n)
                         if str(c.get("origen")) == "ausencia"), 2)
    chk("`ausencias` = la suma de los devengos emitidos", cc["ausencias"], _sum_dev)
    chk("`costo_real` = base + ausencias + aportes",
        cc["costo_real"], round(cc["base_nomina"] + cc["ausencias"] + cc["aportes"], 2))
    chk("`base_teorica` NO se contamina (sale de la jornada fichada)",
        cc["base_teorica"] == round(cc["cargado"] - cc["cobrado_no_pagado"]
                                    + cc["pagado_no_cargado"], 2))
    print(f"   sin_explicar = {cc['sin_explicar']:,.2f}  "
          f"(base teórica {cc['base_teorica']:,.2f} − nóminas {cc['base_nomina']:,.2f})")

    # ── 9 ────────────────────────────────────────────────────────
    paso(9, "Cancelar devuelve los días y limpia el tablero")
    _ok5, _m5 = AU.cancelar(aid, U_MIXTO)
    chk("se cancela", _ok5)
    _ok6, n2 = AU.aplicar_al_roster(AU.get(aid) or {}, quitar=True)
    chk("se retira del tablero", _ok6)
    print(f"   días retirados: {n2}")
    AU._invalidate(); R._invalidate(); time.sleep(1.5)
    chk("la fila NO se borra, se marca", str(AU.get(aid).get("Estado")), AU.CANCELADA)
    chk("el saldo vuelve a 20", AU.saldo(GRUPO, U_MIXTO, AU.VACACIONES)["restantes"], 20.0)
    # ⚠️ Filtrado por USUARIO: ese día `U_SOLO_AUS` sigue de baja, así que pedir la
    # lista entera vacía daba un FALLO en falso — el código estaba bien.
    chk("ya no cuenta como ausente ese día",
        [a["ID"] for a in AU.ausentes_en(GRUPO, v0)
         if str(a.get("Usuario")) == U_MIXTO], [])
    chk("y sus horas pagadas del periodo desaparecen",
        AU.horas_pagadas(GRUPO, U_MIXTO, D0, D1)["horas"], 0.0)

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
        print("  !! LIMPIEZA FALLIDA:", aus_creadas, nom_creadas, list(roster_backup))

print("\n" + ("v430 EJERCITADA OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
