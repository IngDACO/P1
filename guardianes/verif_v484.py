# -*- coding: utf-8 -*-
"""v484 · Parte de horas para la nómina (fase 2.2-A).

Lo que hay que proteger, y por qué cada cosa falla EN SILENCIO:

  (a) que «qué día de ausencia se paga» tenga UNA definición: `horas_pagadas_grupo`
      agrega desde `horas_pagadas_dia`. Si cada una lo calculara, la nómina y el parte
      pagarían días distintos y no lo delata ninguna línea, solo el total;
  (b) que el agregado siga dando EXACTAMENTE lo de siempre — lo usa `payroll.generar`
      para pagar. ⚠️ El oráculo va ESCRITO aquí y no sacado de `git show HEAD:`: en
      cuanto se commitea, HEAD tendría el código nuevo y el chequeo se quedaría vacío;
  (c) que el parte exporte la JORNADA (lo que se paga) y no las horas de obra (lo que
      se cobra), que pueden ser más — y el desvío se AVISA en vez de sumarse;
  (d) que el formato sea ANCHO y en ORDEN, porque el array `NumberOfUnits` de la API
      de Xero es una entrada por día: si se pierde el orden, 2.3 paga días cruzados;
  (e) que un día sin horas vaya VACÍO y no en 0 (un 0 afirma «trabajó cero»);
  (f) que los homónimos sin código de nómina se avisen: el proveedor casa por nombre.
"""
import ast
import datetime as dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": "cliente1"}

fallos = []
n_ok = 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    if real == esperado:
        ok(que)
    else:
        fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


def _func(mod, nombre):
    for n in ast.walk(ast.parse(_fuente(mod))):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre:
            return n
    return None


import csv as _csv                                                 # noqa: E402
import pandas as pd                                                # noqa: E402
from core import auditoria, ausencias as AU, auth, contable        # noqa: E402
from core import contable_ui, theme as T, timeclock as TC          # noqa: E402

G = "cliente1"
L = dt.date(2026, 9, 7)          # lunes

# ═════ 1 · UNA definición de qué día de ausencia se paga ════════════════════
print("\n[1] el criterio vive en un solo sitio")
ck("existe la vista por día", hasattr(AU, "horas_pagadas_dia"), True)
# ⚠️ El agregado tiene que DELEGAR, no recalcular: por AST, su cuerpo llama a la
# función de día y NO vuelve a recorrer las filas por su cuenta.
_agr = _func("core/ausencias.py", "horas_pagadas_grupo")
_llama = [n for n in ast.walk(_agr) if isinstance(n, ast.Call)
          and getattr(n.func, "id", "") == "horas_pagadas_dia"]
ck("el agregado delega en la vista por día", len(_llama), 1)
_recorre = [n for n in ast.walk(_agr) if isinstance(n, ast.Call)
            and getattr(n.func, "id", "") == "_records"]
ck("...y ya NO recorre las filas por su cuenta", _recorre, [])
_hd = _func("core/ausencias.py", "horas_pagadas_dia")
ck("y el criterio de v432 está en la vista por día",
   any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "max"
       for n in ast.walk(_hd)), True)

# ═════ 2 · el agregado da EXACTAMENTE lo de siempre ═════════════════════════
print("\n[2] el agregado no se movió (oráculo fijo, lo paga la nómina)")


def _fila(usr, tipo, d0, d1, estado=AU.APROBADA, findes=""):
    return {"ID": "AUS-x", "Group": G, "User": usr, "Name": usr.upper(),
            "Type": tipo, "From": d0.isoformat(), "To": d1.isoformat(),
            "Days": "", "Reason": "", "Status": estado, "ResolvedBy": "",
            "ResolvedDate": "", "AdminNote": "", "CreatedBy": "", "Created": "",
            "IncludesWeekends": findes}


# (nombre, filas, fichadas, esperado) — los números salieron de comparar contra la
# implementación ANTERIOR sobre las mismas filas, y quedan clavados aquí.
CASOS = [
    ("3 días de vacaciones, sin fichar",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))], {},
     {"horas": 24.0, "dias": 3.0, "por_tipo": {"vacaciones": 3}, "recortes": 0}),
    ("el RECORTE de v432 (4.68 h fichadas ese día)",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))],
     {"u1": {L + dt.timedelta(days=1): 4.68}},
     {"horas": 19.32, "dias": 3.0, "por_tipo": {"vacaciones": 3}, "recortes": 1}),
    ("día trabajado COMPLETO: paga 0 y sigue contando como día",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=2))], {"u1": {L: 8.75}},
     {"horas": 16.0, "dias": 3.0, "por_tipo": {"vacaciones": 3}, "recortes": 1}),
    ("rango CON fin de semana pedido",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=6), findes="SI")], {},
     {"horas": 56.0, "dias": 7.0, "por_tipo": {"vacaciones": 7}, "recortes": 0}),
    ("rango SIN fin de semana",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=6))], {},
     {"horas": 40.0, "dias": 5.0, "por_tipo": {"vacaciones": 5}, "recortes": 0}),
    ("a caballo del periodo: solo los días dentro",
     [_fila("u1", AU.VACACIONES, L - dt.timedelta(days=10), L + dt.timedelta(days=1))],
     {}, {"horas": 16.0, "dias": 2.0, "por_tipo": {"vacaciones": 2}, "recortes": 0}),
    ("dos tipos, días distintos",
     [_fila("u1", AU.VACACIONES, L, L + dt.timedelta(days=1)),
      _fila("u1", AU.ENFERMEDAD, L + dt.timedelta(days=2), L + dt.timedelta(days=2))],
     {"u1": {L: 2.0}},
     {"horas": 22.0, "dias": 3.0, "por_tipo": {"vacaciones": 2, "enfermedad": 1},
      "recortes": 1}),
]
FUERA = [
    ("tipo NO pagado (día libre)", [_fila("u1", AU.LIBRE, L, L + dt.timedelta(days=2))]),
    ("no aprobada", [_fila("u1", AU.VACACIONES, L, L, estado="pendiente")]),
    ("de otro grupo", [dict(_fila("u1", AU.VACACIONES, L, L), Group="otro")]),
    ("sin ausencias", []),
]

_rec, _tc = AU._records, TC.horas_por_usuario_dia
try:
    for nombre, filas, fich, esp in CASOS:
        AU._records = lambda f=filas: list(f)
        TC.horas_por_usuario_dia = lambda g, a, b, f=fich: {k: dict(v) for k, v in f.items()}
        r = AU.horas_pagadas_grupo(G, L, L + dt.timedelta(days=6)).get("u1", {})
        real = {"horas": r.get("horas"), "dias": r.get("dias"),
                "por_tipo": r.get("por_tipo"), "recortes": len(r.get("recortados") or [])}
        ck(nombre, real, esp)
        # ⚠️ Y el detalle por día tiene que SUMAR el agregado, o las dos vistas
        # estarían contando cosas distintas.
        det = AU.horas_pagadas_dia(G, L, L + dt.timedelta(days=6)).get("u1", {})
        _s = round(sum(h for p in (det.get("dias") or {}).values() for h in p.values()), 2)
        ck(f"   ...y el detalle suma el agregado ({nombre[:28]})", _s, esp["horas"])
    for nombre, filas in FUERA:
        AU._records = lambda f=filas: list(f)
        TC.horas_por_usuario_dia = lambda g, a, b: {}
        ck(f"queda fuera: {nombre}",
           AU.horas_pagadas_grupo(G, L, L + dt.timedelta(days=6)), {})

    # ⚠️ La rama del `except`: si no se pueden leer los fichajes NO se paga a ciegas.
    def _revienta(*a, **kw):
        raise RuntimeError("boom")
    AU._records = lambda: [_fila("u1", AU.VACACIONES, L, L)]
    TC.horas_por_usuario_dia = _revienta
    ck("con los fichajes reventando paga la jornada entera y no revienta",
       AU.horas_pagadas_grupo(G, L, L)["u1"]["horas"], 8.0)
finally:
    AU._records, TC.horas_por_usuario_dia = _rec, _tc

# ═════ 3 · los conceptos se DERIVAN ═════════════════════════════════════════
print("\n[3] conceptos (earnings rates)")
# ⚠️ Es una FUNCIÓN y no una constante de módulo: una constante se evalúa al importar
# y se queda congelada (la familia del `t()` congelado, v445).
ck("`conceptos` es una función", callable(getattr(contable, "conceptos", None)), True)
_c = contable.conceptos()
ck("ordinarias va primera", _c[0], contable.ORDINARIAS)
ck("se derivan de ausencias.TIPOS y solo los PAGADOS", sorted(_c[1:]),
   sorted(k for k, v in AU.TIPOS.items() if v.get("pagado")))
ck("el día libre (no pagado) queda fuera", AU.LIBRE in _c, False)
_m = contable.mapa(G)
ck("hay nombre para cada concepto",
   [k for k in _c if not str(_m["conceptos"].get(k, "")).strip()], [])

_old = auth.group_text_setting
try:
    auth.group_text_setting = (lambda g, f, d="": '{"conceptos": {"vacaciones": "ZZZ"}}'
                               if f == "AccountingJSON" else d)
    _m2 = contable.mapa(G)
    ck("lo guardado sobrescribe el tocado", _m2["conceptos"]["vacaciones"], "ZZZ")
    ck("...y CONSERVA los demás", _m2["conceptos"][contable.ORDINARIAS], "Ordinary Hours")
    ck("...y no toca el mapa de cuentas", _m2["cuentas"]["xero"][contable.VENTAS], "200")
finally:
    auth.group_text_setting = _old

# ═════ 4 · el parte: fuente, forma y orden ══════════════════════════════════
print("\n[4] el parte de horas")
_jd, _au, _lu = TC.horas_por_usuario_dia, AU.horas_pagadas_dia, auth.list_users
try:
    TC.horas_por_usuario_dia = lambda g, a, b: {
        "u1": {L: 8.0, L + dt.timedelta(days=1): 4.68},
        "u2": {L: 8.0}, "fantasma": {L: 6.0},
        # ⚠️ u3 TIENE horas, nombre ÚNICO y NINGÚN código de nómina: sin este caso el
        # chequeo de «no avises de quien está bien» no se ejercita — sin horas no entra
        # en el parte, así que la rotura que hacía saltar el aviso siempre se ESCAPÓ.
        "u3": {L: 8.0}}
    AU.horas_pagadas_dia = lambda g, a, b: {
        "u1": {"nombre": "Mei Chen",
               "dias": {L + dt.timedelta(days=1): {"vacaciones": 3.32}},
               "por_tipo": {"vacaciones": 1}, "dias_contados": 1.0,
               "recortados": [{"fecha": L + dt.timedelta(days=1), "fichadas": 4.68,
                               "pagadas": 3.32, "tipo": "vacaciones"}]}}
    auth.list_users = lambda grupo=None: [
        {"User": "u1", "Name": "Mei Chen", "PayrollID": "EMP-001", "Group": G},
        {"User": "u2", "Name": "Mei Chen", "PayrollID": "", "Group": G},
        {"User": "u3", "Name": "Solo Uno", "PayrollID": "", "Group": G}]

    r = contable.partes(G, L, L + dt.timedelta(days=11))
    ck("los días del periodo, en orden", r["dias"][0], L)
    ck("...y son 12", len(r["dias"]), 12)
    _ord = [f for f in r["filas"] if f["usuario"] == "u1"
            and f["concepto"] == contable.ORDINARIAS][0]
    # ⚠️ 8.0 + 4.68 = la JORNADA. Si cogiera las horas de obra saldría otro número.
    ck("las ordinarias son la JORNADA fichada", _ord["total"], 12.68)
    _vac = [f for f in r["filas"] if f["concepto"] == "vacaciones"][0]
    ck("la ausencia trae el recorte de v432 (3.32, no 8)", _vac["total"], 3.32)
    ck("y su etiqueta es el earnings rate configurado", _vac["etiqueta"], "Annual Leave")
    # ⚠️ El mismo día no puede pagar más de una jornada: 4.68 + 3.32 = 8.
    _dia = L + dt.timedelta(days=1)
    ck("un día con ausencia Y fichaje paga UNA jornada",
       round(_ord["horas"][_dia] + _vac["horas"][_dia], 2), 8.0)

    _txt = " | ".join(r["avisos"])
    ck("avisa de quien tiene horas y NO está en Login", "fantasma" in _txt, True)
    ck("avisa del homónimo SIN código de nómina", "Mei Chen" in _txt, True)
    # ⚠️ Y NO del que tiene nombre único: un aviso que grita sobre lo que está bien
    # acaba ignorándose entero (v450).
    ck("y NO de quien tiene el nombre único", "Solo Uno" in _txt, False)
    ck("avisa del recorte", "3.32" in _txt, True)

    cv = contable.csv_partes(G, L, L + dt.timedelta(days=11))
    _l = cv["csv"].splitlines()
    cab = next(_csv.reader([_l[0]]))
    ck("cabecera = 3 + un día por columna + total", len(cab), 3 + 12 + 1)
    ck("y las columnas van en ORDEN (= el array de la API)",
       cab[3:6], ["07/09/2026", "08/09/2026", "09/09/2026"])
    _filas = list(_csv.reader(_l[1:]))
    ck("toda fila tiene el ancho de la cabecera",
       sorted({len(x) for x in _filas}), [len(cab)])
    _f1 = next(x for x in _filas if x[1] == "EMP-001" and x[2] == "Ordinary Hours")
    # ⚠️ VACÍO y no 0: un 0 afirma «ese día trabajó cero horas».
    ck("un día sin horas va VACÍO", _f1[5], "")
    ck("el día con jornada recortada lleva la jornada", _f1[4], "4.68")
finally:
    TC.horas_por_usuario_dia, AU.horas_pagadas_dia, auth.list_users = _jd, _au, _lu

print("\n[5] bordes")
ck("fechas ilegibles no revientan", contable.partes(G, "x", "y")["filas"], [])
ck("hasta < desde no revienta",
   contable.partes(G, L + dt.timedelta(days=5), L)["filas"], [])
_lg = contable.partes(G, L, L + dt.timedelta(days=400))
ck("el periodo se topa", len(_lg["dias"]), contable._MAX_DIAS)
ck("...y lo dice", any(str(contable._MAX_DIAS) in a for a in _lg["avisos"]), True)

# ═════ 6 · PayrollID ════════════════════════════════════════════════════════
print("\n[6] el identificador de nómina")
ck("la columna es la ÚLTIMA (migra sola)", auth.LOGIN_HEADERS[-1], "PayrollID")
# ⚠️ Y lo que de verdad protege la regla: que NADA se cuele antes de las históricas.
# Comprobar solo el último elemento dejaba pasar una columna insertada en medio, que
# es justo el fallo de v363 — las filas se escriben por POSICIÓN.
_HIST = ["User", "Password", "Role", "Name", "Active", "Group", "SessionToken",
         "SessionTime", "Email", "TelegramChatID", "HourlyRate", "StartedOn"]
ck("las columnas históricas siguen en su orden y al principio",
   auth.LOGIN_HEADERS[:len(_HIST)], _HIST)
ck("...y lo nuevo va DESPUÉS", auth.LOGIN_HEADERS[len(_HIST):], ["PayrollID"])
ck("sin duplicados en la cabecera",
   len(auth.LOGIN_HEADERS), len(set(auth.LOGIN_HEADERS)))
# ⚠️ `_COL` se DERIVA desde v433: si volviera a escribirse a mano, la escritura
# moriría con KeyError la primera vez que alguien guarde.
ck("`_COL` la conoce (derivado)", bool(auth._COL.get("PayrollID")), True)
ck("`list_users` la devuelve (proyección derivada, v434)",
   "PayrollID" in (auth.list_users(G) or [{}])[0], True)
# ⚠️ Decide a QUIÉN le paga el proveedor: si un campo mueve dinero, deja rastro.
ck("está en CAMPOS_CLAVE", "PayrollID" in auditoria.CAMPOS_CLAVE, True)
# ⚠️ Y que se pueda PONER: una columna que existe y no tiene dónde escribirse es el
# «pendiente que nadie puede cerrar» de v325/v340 — el parte avisaría del homónimo
# ambiguo sin ofrecer forma de resolverlo. Por AST, la ficha tiene su editor.
_fu = _func("core/auth_ui.py", "_ficha_usuario")
_esc = [n for n in ast.walk(_fu) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "set_login_setting"
        and any(isinstance(a, ast.Constant) and a.value == "PayrollID" for a in n.args)]
ck("la ficha de usuario puede guardar el PayrollID", len(_esc), 1)
_lee = [n for n in ast.walk(_fu) if isinstance(n, ast.Call)
        and getattr(n.func, "attr", "") == "get"
        and any(isinstance(a, ast.Constant) and a.value == "PayrollID" for a in n.args)]
ck("...y lo lee para precargarlo", len(_lee) >= 1, True)

# Las dos guardas, EJECUTADAS: importar no ejecuta (v378).
ck("el setter genérico rechaza un campo SECRETO",
   auth.set_login_setting("admin1", "Password", "x")[0], False)
ck("...y una columna que no existe",
   auth.set_login_setting("admin1", "NoExiste", "x")[0], False)

# ═════ 7 · la pantalla ══════════════════════════════════════════════════════
print("\n[7] la pantalla")
_src = _fuente("core/contable_ui.py")
_rc = _func("core/contable_ui.py", "render_contable")
_llamadas = [getattr(n.func, "id", "") for n in ast.walk(_rc) if isinstance(n, ast.Call)]
ck("render_contable llama a la sección del parte",
   "_partes_section" in _llamadas, True)
# ⚠️ El parte tiene su PROPIO periodo: una nómina va por periodo de pago, no por el
# mes natural del resumen contable.
_ps = _func("core/contable_ui.py", "_partes_section")
_di = [n for n in ast.walk(_ps) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "date_input"]
ck("y su propio selector de fechas", len(_di), 2)
# ⚠️ Y NO cuelga del selector de formato contable: es de nómina, otro destino.
ck("no depende del perfil contable", "perfil" in ast.unparse(_ps), False)
# ⚠️ `kpi_row` PINTA; `_kpi_card` DEVUELVE y como sentencia suelta se tira (v424).
_sueltas = [ast.unparse(n)[:40] for n in ast.walk(ast.parse(_src))
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and getattr(n.value.func, "attr", "") == "_kpi_card"]
ck("ninguna llamada a _kpi_card tirando su valor", _sueltas, [])
# ⚠️ `t()` formatea Y protege un placeholder mal escrito; por fuera se salta la guarda.
for f in ("core/contable.py", "core/contable_ui.py", "core/ausencias.py", "core/auth.py"):
    _mal = [ast.unparse(n)[:50] for n in ast.walk(ast.parse(_fuente(f)))
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "format"
            and isinstance(n.func.value, ast.Call)
            and getattr(n.func.value.func, "id", "") in ("t", "d")]
    ck(f"{f}: las variables van dentro de t()", _mal, [])

# ── y EJECUTADA, que es lo único que ve un nombre sin importar ──
_pintado = {"kpi": 0, "dl": 0, "sec": 0}


class _Col:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getattr__(self, n):
        return _st(n)


def _st(nombre):
    def _f(*a, **kw):
        if nombre == "date_input":
            return kw.get("value") or dt.date.today()
        if nombre == "data_editor":
            return a[0] if a and isinstance(a[0], pd.DataFrame) else pd.DataFrame()
        if nombre == "download_button":
            _pintado["dl"] += 1
            return False
        if nombre == "columns":
            n = a[0] if a else 2
            return [_Col() for _ in range(n if isinstance(n, int) else len(n))]
        if nombre == "expander":
            return _Col()
        if nombre == "radio":
            return (a[1][0] if len(a) > 1 and a[1] else None)
        if nombre in ("checkbox",):
            return kw.get("value", False)
        if nombre in ("text_input",):
            return kw.get("value", "")
        if nombre in ("button",):
            return False
        return None
    return _f


_g = {}
for n in ("date_input", "data_editor", "download_button", "dataframe", "warning",
          "caption", "expander", "radio", "button", "checkbox", "text_input",
          "markdown", "code", "columns", "error"):
    _g[n] = getattr(st, n)
    setattr(st, n, _st(n))
_sec, _kpi = T.section, T.kpi_row
T.section = lambda *a, **kw: _pintado.__setitem__("sec", _pintado["sec"] + 1)


def _kpi_espia(items):
    _pintado["kpi"] += 1
    for it in items:
        if it[1] is None:
            fallo("una tarjeta KPI con valor None")
    return _kpi(items)


T.kpi_row = _kpi_espia
try:
    contable_ui.render_contable(G)
    ok("la pantalla entera se EJECUTA sin excepción")
    ck("pinta la sección del parte", _pintado["sec"] >= 1, True)
    ck("y los tres ficheros (facturas, gastos, parte)", _pintado["dl"], 3)
except Exception as e:
    fallo("render_contable revienta", f"{type(e).__name__}: {e}")
finally:
    for n, f in _g.items():
        setattr(st, n, f)
    T.section, T.kpi_row = _sec, _kpi

print("\n" + "=" * 74)
print(f"{n_ok} comprobaciones OK · {len(fallos)} fallos")
if fallos:
    for f in fallos:
        print("   -", f)
sys.exit(1 if fallos else 0)
