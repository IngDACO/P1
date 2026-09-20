# -*- coding: utf-8 -*-
"""v484 · el PARTE DE HORAS en `contable.py` (fase 2.2-A)."""
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\contable.py"
s = io.open(P, encoding="utf-8").read()

# ── 1 · los conceptos (earnings rates) al mapa de configuración ─────────────
V1 = '''_DEFECTOS = {
    "moneda": "AUD",
    "gastos_incluyen_impuesto": True,   # en AU el recibo viene con el GST dentro
    "categoria_seguimiento": "Project",
    "seguimiento": True,
    "cuentas": _CUENTAS_DEFECTO,
}'''
N1 = '''_DEFECTOS = {
    "moneda": "AUD",
    "gastos_incluyen_impuesto": True,   # en AU el recibo viene con el GST dentro
    "categoria_seguimiento": "Project",
    "seguimiento": True,
    "cuentas": _CUENTAS_DEFECTO,
}

# ── Parte de horas (fase 2.2) ───────────────────────────────────────────────
# El nombre del «earnings rate» con el que cada concepto entra en la nómina. Son los
# nombres de fábrica de Xero Payroll AU; se editan, porque cada organización los tiene
# a su manera y el proveedor casa por NOMBRE.
ORDINARIAS = "ordinarias"
_CONCEPTOS_DEFECTO = {
    ORDINARIAS:   "Ordinary Hours",
    "vacaciones": "Annual Leave",
    "enfermedad": "Personal/Carer's Leave",
}
_MAX_DIAS = 62          # tope de columnas: un año daría 365 y no lo lee nadie


def conceptos() -> tuple:
    """Las claves del parte: ordinarias + los tipos de ausencia **PAGADA**.

    ⚠️ Los tipos se DERIVAN de `ausencias.TIPOS`, no se copian (v433/v434): un tipo
    nuevo aparece solo, y uno que deje de pagarse desaparece. Copiarlos dejaría el
    parte pagando lo que la app ya no paga, sin que nada avise.

    ⚠️ Y es una FUNCIÓN, no una constante de módulo: una constante se evaluaría al
    importar y se quedaría congelada (la familia del `t()` congelado, v445).
    """
    try:
        from core import ausencias as _AU
        pag = tuple(k for k, v in _AU.TIPOS.items() if v.get("pagado"))
    except Exception as e:
        logger.warning("contable: no se pudieron leer los tipos de ausencia: %s", e)
        pag = ()
    return (ORDINARIAS,) + pag'''
if s.count(V1) != 1:
    raise SystemExit("ancla _DEFECTOS no unica: %d" % s.count(V1))
s = s.replace(V1, N1)

# ── 2 · `mapa()` fusiona también los conceptos ──────────────────────────────
V2 = '''    cfg = dict(_DEFECTOS)
    cfg["cuentas"] = {p: dict(c) for p, c in _CUENTAS_DEFECTO.items()}'''
N2 = '''    cfg = dict(_DEFECTOS)
    cfg["cuentas"] = {p: dict(c) for p, c in _CUENTAS_DEFECTO.items()}
    cfg["conceptos"] = dict(_CONCEPTOS_DEFECTO)'''
if s.count(V2) != 1:
    raise SystemExit("ancla mapa/cfg no unica: %d" % s.count(V2))
s = s.replace(V2, N2)

V3 = '''            if k == "cuentas" and isinstance(v, dict):
                for p, c in v.items():
                    cfg["cuentas"].setdefault(p, {}).update(
                        {kk: str(vv) for kk, vv in (c or {}).items()})
            else:
                cfg[k] = v'''
N3 = '''            if k == "cuentas" and isinstance(v, dict):
                for p, c in v.items():
                    cfg["cuentas"].setdefault(p, {}).update(
                        {kk: str(vv) for kk, vv in (c or {}).items()})
            elif k == "conceptos" and isinstance(v, dict):
                # ⚠️ Mismo criterio que las cuentas: SOBRESCRIBE lo tocado y conserva
                # el resto. Sustituir el diccionario dejaría sin nombre un tipo de
                # ausencia añadido despues de guardar, y esa línea saldría en blanco.
                cfg["conceptos"].update({kk: str(vv) for kk, vv in (v or {}).items()})
            else:
                cfg[k] = v'''
if s.count(V3) != 1:
    raise SystemExit("ancla mapa/merge no unica: %d" % s.count(V3))
s = s.replace(V3, N3)

# ── 3 · el parte, al final del módulo ───────────────────────────────────────
s = s.rstrip() + '''


# ─────────────────────────────────────────────────────────────────────────────
# Parte de horas para la nómina (fase 2.2-A)
# ─────────────────────────────────────────────────────────────────────────────
def partes(grupo: str, desde, hasta) -> dict:
    """Las horas PAGADAS del periodo, persona × concepto × día.

    `{dias: [date...], filas: [{usuario, nombre, payroll_id, concepto, etiqueta,
      horas: {date: h}, total}], avisos: [...], total: h, personas: n}`

    ⚠️ **Formato ANCHO (una columna por día) a propósito.** Un parte de Xero Payroll es
    `TimesheetLines[] = {EarningsRateID, NumberOfUnits[]}`, y `NumberOfUnits` es un
    ARRAY con una entrada por día del periodo — verificado en su documentación, no
    supuesto. Construirlo largo (una fila por día) obligaría a pivotarlo cuando exista
    OAuth; así, 2.3 es un mapeo: cada fila de aquí ES una línea de allí y el orden de
    las columnas ES el orden del array.

    ⚠️ **Son las horas que se PAGAN, no las que se cargan a obra.** La base es la
    JORNADA fichada (lo mismo que usa `payroll.generar`), más las ausencias pagadas.
    Las horas de proyecto son otra cosa —lo que se le cobra al cliente— y meterlas
    aquí pagaría de más: la app ya mide que pueden superar la jornada (v320/v422). Por
    eso el desvío se AVISA en vez de sumarse.

    ⚠️ El día de ausencia sale de `ausencias.horas_pagadas_dia`, que es donde vive el
    criterio de v432 («un día vale UNA jornada, nunca dos»). Recalcularlo aquí sería
    una segunda definición de lo que se paga.
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1 or d1 < d0:
        return {"dias": [], "filas": [], "avisos": [t("The dates could not be read.")],
                "total": 0.0, "personas": 0}

    avisos = []
    dias = []
    d = d0
    while d <= d1 and len(dias) < _MAX_DIAS:
        dias.append(d)
        d += _dt.timedelta(days=1)
    if d <= d1:
        avisos.append(t("The period is longer than {n} days: only the first {n} are "
                        "exported. A timesheet goes per pay period.", n=_MAX_DIAS))
        d1 = dias[-1]

    cfg = mapa(grupo)
    nombres_concepto = cfg.get("conceptos", {})

    # ── de dónde salen las horas ──
    try:
        from core import timeclock as _TC
        jornada = _TC.horas_por_usuario_dia(grupo, d0, d1) or {}
    except Exception as e:
        logger.warning("contable: no se pudo leer la jornada de %s: %s", grupo, e)
        jornada, _ = {}, avisos.append(
            t("The clocked hours could not be read: the timesheet is incomplete."))
    try:
        from core import ausencias as _AU
        aus = _AU.horas_pagadas_dia(grupo, d0, d1) or {}
    except Exception as e:
        logger.warning("contable: no se pudieron leer las ausencias de %s: %s", grupo, e)
        aus, _ = {}, avisos.append(
            t("The paid absences could not be read: the timesheet is incomplete."))

    # ── quién es quién ──
    try:
        usuarios = auth.list_users(grupo) or []
    except Exception as e:
        logger.warning("contable: no se pudieron leer los usuarios de %s: %s", grupo, e)
        usuarios = []
    por_login = {str(u.get("User", "")): u for u in usuarios}
    _cuenta_nombre = {}
    for u in usuarios:
        _n = str(u.get("Name", "") or u.get("User", "")).strip().lower()
        _cuenta_nombre[_n] = _cuenta_nombre.get(_n, 0) + 1

    filas, sin_id, de_baja = [], [], []
    claves = sorted(set(jornada) | set(aus))
    for clave in claves:
        u = por_login.get(clave) or {}
        nombre = str(u.get("Name", "") or aus.get(clave, {}).get("nombre") or clave)
        pid = str(u.get("PayrollID", "") or "").strip()
        if not u:
            # ⚠️ Tiene horas y NO está en Login: una cuenta dada de baja con fichajes
            # históricos (el caso de v325). El proveedor no la conoce, así que se dice
            # en vez de exportar una línea que su nómina va a rechazar.
            de_baja.append(nombre)
        elif not pid and _cuenta_nombre.get(nombre.strip().lower(), 0) > 1:
            # ⚠️ Sin código y con el nombre REPETIDO: el proveedor casa por nombre y
            # no puede distinguirlos. Con el nombre único, no tener código es normal.
            sin_id.append(nombre)

        porc = {}
        for f, h in (jornada.get(clave) or {}).items():
            if _num(h):
                porc.setdefault(ORDINARIAS, {})[f] = round(_num(h), 2)
        for f, portipo in ((aus.get(clave) or {}).get("dias") or {}).items():
            for tipo, h in (portipo or {}).items():
                if _num(h):
                    porc.setdefault(tipo, {})[f] = round(_num(h), 2)

        for concepto in conceptos():
            horas = porc.get(concepto)
            if not horas:
                continue
            filas.append({
                "usuario": clave, "nombre": nombre, "payroll_id": pid,
                "concepto": concepto,
                "etiqueta": nombres_concepto.get(concepto, concepto),
                "horas": horas,
                "total": round(sum(horas.values()), 2)})

    # ── lo que hay que saber ANTES de mandarlo a la nómina ──
    if de_baja:
        avisos.append(t("These people have paid hours and are no longer in the app, so "
                        "the payroll provider does not know them: {q}",
                        q=", ".join(sorted(set(de_baja)))))
    if sin_id:
        avisos.append(t("Same name, no payroll ID — the provider matches by name and "
                        "cannot tell them apart: {q}",
                        q=", ".join(sorted(set(sin_id)))))
    recortes = [(aus[k].get("nombre") or k, r) for k in aus
                for r in (aus[k].get("recortados") or [])]
    if recortes:
        avisos.append(t("Days with BOTH an absence and clocked hours — one day pays one "
                        "shift, so the absence only pays the remainder: {q}",
                        q=" · ".join(f"{n} {r['fecha']}: {r['pagadas']} h"
                                     for n, r in recortes[:6])))
    # ⚠️ Horas de obra por encima de la jornada = alguien fichó a una obra sin abrir
    # jornada (v320). Sus horas PAGADAS salen de la jornada, así que ese parte va corto
    # y hay que decirlo: es el hueco que el resumen financiero llama «horas sin nómina».
    try:
        from core import timeclock as _TC2
        jp = _TC2.jornada_y_proyecto(grupo, d0, d1) or {}
        _desc = [str(v.get("nombre") or k) for k, v in jp.items()
                 if _num(v.get("proyecto")) > _num(v.get("jornada")) + 0.05]
        if _desc:
            avisos.append(t("More job hours than workday hours, so they clocked onto a "
                            "job without opening their workday and these paid hours "
                            "fall short: {q}", q=", ".join(sorted(set(_desc)))))
    except Exception as e:
        logger.warning("contable: no se pudo contrastar jornada y obra: %s", e)

    return {"dias": dias, "filas": filas, "avisos": avisos,
            "total": round(sum(f["total"] for f in filas), 2),
            "personas": len({f["usuario"] for f in filas})}


def csv_partes(grupo: str, desde, hasta) -> dict:
    """El parte en CSV ancho. {csv, filas, personas, total, avisos, dias}.

    ⚠️ **Xero Payroll AU no importa partes por CSV** —comprobado en su documentación,
    en sus Product Ideas (la petición sigue abierta) y en sus foros—, así que este
    fichero es para que lo lea una persona y lo teclee, y sirve para cualquier
    proveedor. El camino que SÍ conecta con Xero es la API (`POST /timesheets`), que
    necesita OAuth y los GUID de empleado y de earnings rate: eso es la fase 2.3, y
    esta forma ancha es exactamente la que esa API pide.
    """
    r = partes(grupo, desde, hasta)
    cab = ([t("Employee"), t("Payroll ID"), t("Earnings rate")]
           + [d.strftime(_FECHA) for d in r["dias"]] + [t("Total")])
    filas = [[f["nombre"], f["payroll_id"], f["etiqueta"]]
             + [(_dinero(f["horas"][d]) if d in f["horas"] else "") for d in r["dias"]]
             + [_dinero(f["total"])]
             for f in r["filas"]]
    return {"csv": _escribe(cab, filas), "filas": len(filas),
            "personas": r["personas"], "total": r["total"],
            "avisos": r["avisos"], "dias": r["dias"]}
'''

if "import datetime as _dt" not in s:
    s = s.replace("import csv\nimport io\n", "import csv\nimport datetime as _dt\nimport io\n", 1)

compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("contable: partes() + csv_partes() + conceptos en el mapa")
