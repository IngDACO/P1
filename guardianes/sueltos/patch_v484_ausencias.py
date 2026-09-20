# -*- coding: utf-8 -*-
"""v484 · el criterio de «qué día de ausencia se paga» pasa a tener detalle por DÍA.

El parte de horas necesita la ausencia día a día y por tipo (Xero pide un valor por
día del periodo), y `horas_pagadas_grupo` solo da el AGREGADO. Reimplementar el
criterio en el exportador crearía una segunda definición de lo que se paga — la
familia de los cinco `_num` divergentes de v323, y con dinero dentro.

Así que el criterio baja a `horas_pagadas_dia` y el agregado DELEGA. Una definición,
dos vistas. Es el mismo patrón que el módulo ya documenta para `horas_pagadas`.

⚠️ La semántica se preserva EXACTA, incluido lo que parece raro:
  · `por_tipo` y `dias` cuentan TODOS los días del rango, también los que pagan 0
    porque la persona trabajó la jornada entera;
  · si dos ausencias aprobadas cubrieran el mismo día se pagaría dos veces — y NO se
    pone tope, porque `solicitar` **ya impide** los solapes (`solapadas`), así que
    sería inventar un arreglo para un caso que la app no permite (lección v369). El
    tope sería su propio cambio, con su propia prueba.
"""
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\ausencias.py"

# ⚠️ El ancla incluye el `\"\"\"` que CIERRA el docstring: sin él, la nota nueva quedaría
# como prosa suelta detrás de un docstring ya cerrado (y no compila).
VIEJO = '''    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1:
        return {}
    # jornada ya fichada, día a día, para no pagar dos veces el mismo día
    try:
        fichadas = timeclock.horas_por_usuario_dia(grupo, d0, d1)
    except Exception as e:
        # ⚠️ Si esto falla NO se paga a ciegas la jornada completa: se deja el día sin
        # recorte y se dice en `recortados`, para que el aviso de la nómina lo saque.
        logger.warning("ausencias: no se pudieron leer las horas fichadas: %s", e)
        fichadas = {}
    out = {}
    for r in _records():
        if (str(r.get("Group", "")) != str(grupo)
                or str(r.get("Status", "")) != APROBADA):
            continue
        tipo = str(r.get("Type", ""))
        if not TIPOS.get(tipo, {}).get("pagado"):
            continue
        # ⚠️ Los MISMOS días que se descontaron del saldo, no un recuento propio:
        # si el rango se pidió con fin de semana, `Dias` los cuenta y la paga
        # también. Lo contrario le quitaba 12 días de saldo pagándole 8.
        _d = [d for d in dias_del_rango(r.get("From"), r.get("To"),
                                        incluye_findes(r))
              if d0 <= d <= d1]
        if not _d:
            continue
        clave = str(r.get("User", ""))
        e = out.setdefault(clave, {"horas": 0.0, "dias": 0.0, "por_tipo": {},
                                   "nombre": str(r.get("Name") or clave),
                                   "recortados": []})
        _suyas = fichadas.get(clave, {})
        for d in _d:
            _ya = float(_suyas.get(d, 0.0) or 0.0)
            _pag = max(0.0, HORAS_DIA - _ya)
            e["horas"] = round(e["horas"] + _pag, 2)
            if _ya > 0:
                e["recortados"].append({"fecha": d, "fichadas": round(_ya, 2),
                                        "pagadas": round(_pag, 2), "tipo": tipo})
        e["por_tipo"][tipo] = e["por_tipo"].get(tipo, 0) + len(_d)
        e["dias"] += len(_d)
    return out'''

NUEVO = '''    ⚠️ v484 — AGREGA desde `horas_pagadas_dia`, que es donde vive el criterio. Antes
    lo calculaba aquí, y el parte de horas necesita el mismo dato día a día: dos
    implementaciones del mismo «qué se paga» acaban pagando días distintos (v323).
    """
    out = {}
    for clave, e in horas_pagadas_dia(grupo, desde, hasta).items():
        horas = 0.0
        for _porh in e["dias"].values():
            for _h in _porh.values():
                horas = round(horas + _h, 2)
        out[clave] = {"horas": horas, "dias": e["dias_contados"],
                      "por_tipo": dict(e["por_tipo"]), "nombre": e["nombre"],
                      "recortados": list(e["recortados"])}
    return out


def horas_pagadas_dia(grupo, desde, hasta) -> dict:
    """La ausencia PAGADA día a día y por tipo, que es la forma que pide un parte.

    `{usuario: {nombre, dias: {date: {tipo: horas}}, por_tipo: {tipo: n_dias},
      dias_contados: n, recortados: [...]}}`

    ⚠️ **Aquí vive el criterio de v432** —«un día vale UNA jornada, nunca dos»— y
    `horas_pagadas_grupo` agrega desde aquí. Si cada una lo calculara por su cuenta,
    la nómina y el parte de horas podrían pagar días distintos, y eso no lo delata
    ninguna línea de la colilla: solo el total del día.

    ⚠️ `por_tipo` y `dias_contados` cuentan TODOS los días del rango, incluidos los
    que pagan 0 porque esa persona trabajó la jornada entera. Es la semántica de
    siempre y se conserva a propósito: son días de ausencia CONCEDIDOS, que es lo que
    descuenta del saldo, y no horas pagadas.

    ⚠️ Y no lleva tope por día: dos ausencias aprobadas sobre el mismo día pagarían
    dos veces, pero `solicitar` **ya impide** los solapes (`solapadas`), así que poner
    el tope aquí sería arreglar un caso que la app no permite — y cambiaría el agregado
    que la nómina ya usa. Si algún día se edita la hoja a mano, ese tope es su propio
    cambio con su propia prueba.
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1:
        return {}
    # jornada ya fichada, día a día, para no pagar dos veces el mismo día
    try:
        fichadas = timeclock.horas_por_usuario_dia(grupo, d0, d1)
    except Exception as e:
        # ⚠️ Si esto falla NO se paga a ciegas la jornada completa: se deja el día sin
        # recorte y se dice en `recortados`, para que el aviso de la nómina lo saque.
        logger.warning("ausencias: no se pudieron leer las horas fichadas: %s", e)
        fichadas = {}
    out = {}
    for r in _records():
        if (str(r.get("Group", "")) != str(grupo)
                or str(r.get("Status", "")) != APROBADA):
            continue
        tipo = str(r.get("Type", ""))
        if not TIPOS.get(tipo, {}).get("pagado"):
            continue
        # ⚠️ Los MISMOS días que se descontaron del saldo, no un recuento propio:
        # si el rango se pidió con fin de semana, `Dias` los cuenta y la paga
        # también. Lo contrario le quitaba 12 días de saldo pagándole 8.
        _d = [d for d in dias_del_rango(r.get("From"), r.get("To"),
                                        incluye_findes(r))
              if d0 <= d <= d1]
        if not _d:
            continue
        clave = str(r.get("User", ""))
        e = out.setdefault(clave, {"nombre": str(r.get("Name") or clave),
                                   "dias": {}, "por_tipo": {},
                                   "dias_contados": 0.0, "recortados": []})
        _suyas = fichadas.get(clave, {})
        for d in _d:
            _ya = float(_suyas.get(d, 0.0) or 0.0)
            _pag = max(0.0, HORAS_DIA - _ya)
            # ⚠️ Se guarda incluso el 0: ese día EXISTE como ausencia concedida, y el
            # parte tiene que poder decir «no pagó nada porque trabajó la jornada».
            _pd = e["dias"].setdefault(d, {})
            _pd[tipo] = round(_pd.get(tipo, 0.0) + _pag, 2)
            if _ya > 0:
                e["recortados"].append({"fecha": d, "fichadas": round(_ya, 2),
                                        "pagadas": round(_pag, 2), "tipo": tipo})
        e["por_tipo"][tipo] = e["por_tipo"].get(tipo, 0) + len(_d)
        e["dias_contados"] += len(_d)
    return out'''

s = io.open(P, encoding="utf-8").read()
if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("ausencias: horas_pagadas_dia (criterio) + horas_pagadas_grupo agrega")
