# -*- coding: utf-8 -*-
"""v663 · Las cifras que el ciclo 1 vio salir mal (dinero y horas).

1. El resumen (P&L) cuenta como ingreso lo facturado SIN impuesto; el GST, aparte.
2. La nómina no paga jornadas aún abiertas, lo dice, y su periodo por defecto acaba AYER.
3. Una entrada de OBRA no puede salirse de su JORNADA (motor) y el campo puede mover las dos.
4. La revisión de una corrección enseña el efecto en horas TRABAJADAS («+0.30 h worked»).
5. Horas con dos decimales en las colillas; Costs no dice «No costs» con coste; guardar sin
   cambios no dice «updated».

Nada sale a la red ni escribe: las funciones reales, con filas de prueba en memoria.
"""
import ast
import io
import os
import sys
from datetime import date, datetime, timedelta

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(rel, nombre):
    """El código fuente de la función `nombre` de `rel` (por AST)."""
    s = src(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return ast.get_source_segment(s, n) or ""
    return ""


# ═════════════════════════════════════════════════════════════════════════════
sec("1. P&L: ingreso sin impuesto")
from core import finance as F                                              # noqa: E402
from core import invoices as INV                                           # noqa: E402
from core import payroll as PR                                             # noqa: E402

_FAC = [
    {"ID": "FAC-1", "Group": "g1", "Date": "2026-11-09", "Status": "emitida", "Subtotal": "3834",
     "Tax": "383.4", "Total": "4217.4", "Collected": "4217.4", "ClientName": "C1"},
    {"ID": "FAC-2", "Group": "g1", "Date": "2026-11-09", "Status": "emitida", "Subtotal": "8946",
     "Tax": "894.6", "Total": "9840.6", "Collected": "9840.6", "ClientName": "C1"},
    # fila vieja SIN Subtotal: total − Tax
    {"ID": "FAC-3", "Group": "g1", "Date": "2026-11-09", "Status": "emitida", "Subtotal": "",
     "Tax": "10", "Total": "110", "Collected": "0", "ClientName": "C2"},
    # y sin Subtotal ni Tax: total / (1 + TaxPct)
    {"ID": "FAC-4", "Group": "g1", "Date": "2026-11-09", "Status": "emitida", "Subtotal": "",
     "Tax": "", "TaxPct": "10", "Total": "220", "Collected": "0", "ClientName": "C2"},
    # anulada: no cuenta
    {"ID": "FAC-5", "Group": "g1", "Date": "2026-11-09", "Status": "anulada", "Subtotal": "1000",
     "Tax": "100", "Total": "1100", "Collected": "0", "ClientName": "C3"},
]
_o = (INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de, F.E._records)
INV.list_facturas = lambda g, *a, **k: [dict(f) for f in _FAC]
INV.estado_cobro = lambda f: "cobrada" if F._num(f.get("Collected")) >= F._num(f.get("Total")) else "pendiente"
PR.list_nominas = lambda g, *a, **k: [{"PeriodTo": "2026-11-08", "Base": "439.45", "Status": "pagada",
                                       "Net": "439.45", "ConceptosJSON": "[]"}]
PR.conceptos_de = lambda n: [{"tipo": "aporte", "monto": 50.54}]
F.E._records = lambda *a, **k: [{"Group": "g1", "Date": "2026-11-09", "Amount": "1910"}]
try:
    p = F.pnl("g1")
    pc = F.pnl_comparado("g1", date(2026, 11, 1), date(2026, 11, 9), None)
finally:
    INV.list_facturas, INV.estado_cobro, PR.list_nominas, PR.conceptos_de, F.E._records = _o
_ing = 3834 + 8946 + 100 + 200
chk("la sonda: hay facturas y costes (lo que se prueba existe)", p["facturado"] > 0 and p["costo_total"] > 0, p)
chk("facturado = Σ Total CON impuesto (sin la anulada)", abs(p["facturado"] - (4217.4 + 9840.6 + 110 + 220)) < 0.01, p["facturado"])
chk("ingresos = Σ Subtotal SIN impuesto (con los dos respaldos de filas viejas)", abs(p["ingresos"] - _ing) < 0.01, p["ingresos"])
chk("impuesto = facturado − ingresos", abs(p["impuesto"] - (p["facturado"] - p["ingresos"])) < 0.01, p.get("impuesto"))
chk("ganancia = INGRESOS − costo total (antes, facturado − costo: +GST)",
    abs(p["ganancia"] - (_ing - p["costo_total"])) < 0.01, (p["ganancia"], _ing, p["costo_total"]))
chk("el caso del ciclo 1: 12.780 de ingreso y 10.271 de beneficio, no 14.058 / 11.549",
    abs(F._sin_impuesto(_FAC[0]) + F._sin_impuesto(_FAC[1]) - 12780) < 0.01)
chk("pnl_comparado compara también los ingresos", "ingresos" in (pc.get("var") or {}), list((pc.get("var") or {}).keys()))
_rp = src("core/projects_ui.py")
# ⚠️ la CIFRA de la tarjeta, no solo que `ingresos` se lea en algún sitio (escapó en la 1ª batería)
chk("Summary: la tarjeta «Income» enseña los ingresos y el margen sale de ellos",
    '("ing", t("Income"), T.dinero(d.get("ingresos", d["facturado"]), 0),' in _rp
    and "_mrg = (100 * d[\"ganancia\"] / _ing)" in _rp)
chk("Summary: el GST cobrado sale aparte («tax collected … not income»)",
    "tax collected {x} (owed to the tax office, not income)" in _rp)
_ct = src("core/chat_tools.py")
chk("el Management assistant recibe income_ex_tax, el impuesto y profit_ex_tax",
    '"income_ex_tax"' in _ct and '"tax_collected_owed_to_tax_office"' in _ct and '"profit_ex_tax"' in _ct)

# ═════════════════════════════════════════════════════════════════════════════
sec("2. Nómina: jornadas abiertas fuera y periodo hasta ayer")
from core import timeclock as TC                                           # noqa: E402

_ahora = datetime(2026, 11, 9, 15, 0, 0)
_ROWS = [
    {"Group": "g1", "User": "ana", "Name": "Ana", "Type": "general", "Status": "CERRADO",
     "Clock In": "2026-11-04 07:00:00", "Clock Out": "2026-11-04 15:00:00", "Hours": "8"},
    {"Group": "g1", "User": "ana", "Name": "Ana", "Type": "general", "Status": "ABIERTO",
     "Clock In": "2026-11-09 14:48:00", "Clock Out": "", "Hours": ""},
    {"Group": "g1", "User": "bob", "Name": "Bob", "Type": "general", "Status": "ABIERTO",
     "Clock In": "2026-11-09 10:42:00", "Clock Out": "", "Hours": ""},
]
_o2 = (TC._cached_records, TC.mapa_nombres, TC.clock.now)
TC._cached_records = lambda: [dict(r) for r in _ROWS]
TC.mapa_nombres = lambda g: {}
TC.clock.now = lambda *a, **k: _ahora
try:
    _todas = TC.horas_por_usuario_rango("g1", date(2026, 11, 3), date(2026, 11, 9))
    _cerr = TC.horas_por_usuario_rango("g1", date(2026, 11, 3), date(2026, 11, 9), solo_cerradas=True)
    _abie = TC.jornadas_abiertas("g1", date(2026, 11, 3), date(2026, 11, 9))
    _abie_antes = TC.jornadas_abiertas("g1", date(2026, 10, 1), date(2026, 11, 8))
finally:
    TC._cached_records, TC.mapa_nombres, TC.clock.now = _o2
chk("la sonda: sin filtro, la jornada abierta SÍ cuenta (lo que se arregla existe)",
    "bob" in _todas and _todas["ana"]["horas"] > 8, _todas)
chk("solo_cerradas: Ana = 8 h (su jornada abierta fuera) y Bob, sin horas", _cerr == {"ana": {"nombre": "Ana", "horas": 8.0}}, _cerr)
chk("jornadas_abiertas nombra a Ana y a Bob", set(_abie) == {"ana", "bob"}, _abie)
chk("…y no las de un periodo que acaba ANTES de que empezaran", _abie_antes == {}, _abie_antes)
_gen = funcion("core/payroll.py", "generar")
chk("payroll.generar paga solo lo cerrado y devuelve «abiertas»",
    "solo_cerradas=True" in _gen and '"abiertas": abiertas' in _gen)
_ui = funcion("core/payroll_ui.py", "_generar")
chk("Generate payroll: el «To» por defecto es AYER", "_h0 = hoy - timedelta(days=1)" in _ui and "value=_h0" in _ui)
chk("…avisa si el periodo llega a hoy, y la vista previa es la misma que pagará",
    "if hasta >= hoy:" in _ui and "solo_cerradas=True" in _ui
    # el aviso, BAJO su condición (no solo el texto: escapó en la 1ª batería)
    and "    if _abiertas:\n        st.warning(t(\":material/schedule: **Workday still open:**" in _ui)
chk("…y el aviso de después de generar nombra a quien se dejó fuera", 'res.get("abiertas")' in _ui)

# ═════════════════════════════════════════════════════════════════════════════
sec("3. Una entrada de obra no se sale de su jornada")
_J = {"Group": "g1", "User": "c0", "Type": "general", "Clock In": "2026-11-09 14:48:00", "Clock Out": ""}
_P = {"Group": "g1", "User": "c0", "Type": "project", "Clock In": "2026-11-09 14:48:00", "Clock Out": "",
      "Project": "C1 L1"}
_JC = {"Group": "g1", "User": "c0", "Type": "general", "Clock In": "2026-11-09 07:00:00",
       "Clock Out": "2026-11-09 15:00:00"}
_PC = {"Group": "g1", "User": "c0", "Type": "project", "Clock In": "2026-11-09 08:00:00",
       "Clock Out": "2026-11-09 14:00:00", "Project": "C1 L2"}
_OTRO = {"Group": "g1", "User": "otro", "Type": "general", "Clock In": "2026-11-09 05:00:00", "Clock Out": ""}
TC.clock.now = lambda *a, **k: _ahora
try:
    f = TC.fuera_de_jornada
    r1 = f([_J, _P], "c0", "", "g1", _P, "2026-11-09 14:30:00", "", excluir=1)
    r2 = f([_J, _P], "c0", "", "g1", _P, "2026-11-09 14:50:00", "", excluir=1)
    r3 = f([_JC, _PC], "c0", "", "g1", _PC, "2026-11-09 08:00:00", "2026-11-09 15:30:00", excluir=1)
    r4 = f([_JC, _PC], "c0", "", "g1", _JC, "2026-11-09 09:00:00", "2026-11-09 15:00:00", excluir=0)
    r5 = f([_JC, _PC], "c0", "", "g1", _JC, "2026-11-09 06:30:00", "2026-11-09 15:00:00", excluir=0)
    r6 = f([_OTRO, _P], "c0", "", "g1", _P, "2026-11-09 05:30:00", "", excluir=1)
finally:
    TC.clock.now = _o2[2]
chk("obra 14:48 → 14:30 con la jornada a las 14:48: NO (el caso del ciclo 1)", "before your workday" in r1, r1)
chk("…y a 14:50 (dentro de la jornada): sí", r2 == "", r2)
chk("obra que acabaría después de una jornada CERRADA: NO", "after your workday" in r3, r3)
chk("jornada que empezaría después de su obra (09:00 con la obra a las 08:00): NO", "would fall outside the workday" in r4, r4)
chk("jornada que empieza antes (06:30): sí, la obra sigue dentro", r5 == "", r5)
chk("la jornada de OTRA persona no cuenta", r6 == "", r6)
# ⚠️ EJECUTANDO corregir_fichaje contra una hoja falsa (mirar el orden de las líneas dejó
# escapar en la 1ª batería un `if _fuera:` anulado)


class _HojaFalsa:
    def __init__(self, filas):
        self.filas, self.escrito = filas, []

    def get_all_records(self, **k):
        return [dict(f) for f in self.filas]

    def batch_update(self, cambios, **k):
        self.escrito.append(cambios)


_HF = _HojaFalsa([dict(_J, Name="c0", Status="ABIERTO", Hours=""), dict(_P, Name="c0", Status="ABIERTO", Hours="")])
_o3 = (TC._get_worksheet, TC.clock.now, TC._invalidate_records)
TC._get_worksheet = lambda *a, **k: (_HF, None)
TC.clock.now = lambda *a, **k: _ahora
TC._invalidate_records = lambda *a, **k: None
try:
    _rc = TC.corregir_fichaje("g1", "c0", "c0", "project", "Clock In", "2026-11-09 14:48:00", "2026-11-09 14:30:00")
    _n_tras_1 = len(_HF.escrito)
    _rc2 = TC.corregir_fichaje("g1", "c0", "c0", "project", "Clock In", "2026-11-09 14:48:00", "2026-11-09 14:52:00")
finally:
    TC._get_worksheet, TC.clock.now, TC._invalidate_records = _o3
chk("corregir_fichaje NIEGA mover la obra a 14:30 y no escribe nada",
    _rc[0] is False and "before your workday" in str(_rc[1]) and _n_tras_1 == 0, (_rc, _n_tras_1))
chk("…y sí deja 14:52 (dentro de la jornada): una sola escritura, la buena",
    _rc2[0] is True and len(_HF.escrito) == 1 and "14:52" in str(_HF.escrito), (_rc2, _HF.escrito))
from core import timeclock_ui as TU                                         # noqa: E402
from core import correcciones as CO                                         # noqa: E402

_hoy = [{"tipo": "general", "entrada": "2026-11-09 14:48:00", "salida": ""},
        {"tipo": "project", "entrada": "2026-11-09 14:48:00", "salida": "", "proyecto": "C1 L1"}]
_g = TU._jornada_que_sale(_hoy, _hoy[1], CO.CAMPO_IN, datetime(2026, 11, 9, 14, 30))
_n = TU._jornada_que_sale(_hoy, _hoy[1], CO.CAMPO_IN, datetime(2026, 11, 9, 14, 55))
_j = TU._jornada_que_sale(_hoy, _hoy[0], CO.CAMPO_IN, datetime(2026, 11, 9, 14, 30))
chk("el campo: mover la obra a 14:30 ofrece mover la JORNADA (la devuelve)", _g is _hoy[0], _g)
chk("…a 14:55 no hace falta, y corregir la propia jornada tampoco lo ofrece", _n is None and _j is None, (_n, _j))
_cu = funcion("core/timeclock_ui.py", "_corregir_horas")
chk("…la casilla nace marcada y se corrige PRIMERO la jornada, luego la obra",
    'key="cor_mover_jornada"' in _cu and "value=True" in _cu
    and _cu.find("tipo=timeclock.TIPO_GENERAL") < _cu.rfind("timeclock.corregir_fichaje("))

# ═════════════════════════════════════════════════════════════════════════════
sec("4. La revisión enseña el efecto en horas trabajadas")
from core import correcciones_ui as CU                                       # noqa: E402

_in = CU._dif_horas({"Field": CO.CAMPO_IN, "OldValue": "2026-11-09 14:48:00", "NewValue": "2026-11-09 14:30:00"})
_out = CU._dif_horas({"Field": CO.CAMPO_OUT, "OldValue": "2026-11-09 15:00:00", "NewValue": "2026-11-09 15:30:00"})
_out2 = CU._dif_horas({"Field": CO.CAMPO_OUT, "OldValue": "2026-11-09 15:00:00", "NewValue": "2026-11-09 14:00:00"})
chk("entrada 14:48 → 14:30 = «+0.30 h worked» (decía −0.30 h)", _in.startswith("+0.30") and "worked" in _in, _in)
chk("salida 15:00 → 15:30 = +0.50, y 15:00 → 14:00 = −1.00", _out.startswith("+0.50") and _out2.startswith("-1.00"), (_out, _out2))

# ═════════════════════════════════════════════════════════════════════════════
sec("5. Decimales, Costs y guardar sin cambios")
_pu = src("core/payroll_ui.py")
chk("las horas de las colillas con 2 decimales (lista, detalle, My payslips, vista previa)",
    _pu.count("round(_num(x.get(\"Hours\")), 2)") == 1 and _pu.count("_num(f.get('Hours')):.2f") == 2
    and 'round(v["horas"], 2)' in _pu and "_num(f.get('Hours')):.1f" not in _pu)
_co = src("core/projects_ui.py")
chk("Costs con gasto y presupuesto pero sin avance: dice lo gastado, no «No costs…»",
    # la RAMA que lo pinta, no solo el texto (escapó en la 1ª batería)
    '    elif cp["total"] > 0:\n        # ⚠️ v663' in _co and "spent of the **{b}** budget so far" in _co)
_au = src("core/auth_ui.py")
chk("«Save rate» inactivo si la tarifa no cambia", "disabled=abs(float(tar) - _tar0) < 0.005" in _au)
chk("«Save start date» inactivo si la fecha no cambia (o está vacía como antes)", "disabled=(_nf or None) == (_fi or None)" in _au)

print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLOS: " + " | ".join(FALLOS)))
sys.exit(1 if FALLOS else 0)
