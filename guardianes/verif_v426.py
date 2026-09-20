"""v426: una factura ANULADA no cuenta como ingreso en ninguna parte.

Encontrado ejercitando el ciclo de negocio completo: `pnl` sumaba las facturas
anuladas en `facturado` y `cobrado`. El comentario del código decía «excluye
anuladas» y el docstring también — pero `list_facturas` NO filtra por estado (a
diferencia de `list_nominas`, que sí tiene `incluir_anuladas=False`).

⚠️ La asimetría es lo que lo hacía peligroso: los COSTOS anulados sí se excluían (las
nóminas), así que el error solo iba en la dirección de **parecer más rentable**.
Medido en la hoja real: una anulada de $1.100 con $400 cobrados inflaba `facturado`,
`cobrado` y la `ganancia` del grupo.

⚠️ Y NO se arregla cambiando el default de `list_facturas`: la lista de Facturas y el
detalle del cliente NECESITAN mostrarlas — ocultarlas de raíz sería el fallo de v340.

Este guardián es de COMPORTAMIENTO, no de forma: parchea `list_facturas` con un
conjunto conocido que incluye una anulada y comprueba qué cuenta cada función. Así
no reproduce la lógica que audita (el error de v412) ni depende de cómo esté escrita.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


import streamlit as st                                                # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "g"}
from core import invoices as INV, finance as F                        # noqa: E402

# Dos facturas VIVAS de 1.000 (una cobrada entera) y una ANULADA de 500 con 200
# cobrados. Lo correcto: facturado 2.000, cobrado 1.000.
FAKE = [
    {"ID": "F1", "Group": "g", "ClientID": "C1", "Status": "emitida",
     "Date": "2026-08-10", "Total": "1000", "Collected": "1000",
     "ExpiryDate": "2026-12-01",
     "LinesJSON": '[{"concepto":"a","importe":1000,"proyecto_id":"PRJ-1"}]'},
    {"ID": "F2", "Group": "g", "ClientID": "C1", "Status": "emitida",
     "Date": "2026-08-11", "Total": "1000", "Collected": "0",
     "ExpiryDate": "2026-12-01",
     "LinesJSON": '[{"concepto":"b","importe":1000,"proyecto_id":"PRJ-2"}]'},
    {"ID": "F3", "Group": "g", "ClientID": "C1", "Status": "anulada",
     "Date": "2026-08-12", "Total": "500", "Collected": "200",
     "ExpiryDate": "2020-01-01",
     "LinesJSON": '[{"concepto":"c","importe":500,"proyecto_id":"PRJ-1"}]'},
]

_orig = INV.list_facturas
INV.list_facturas = lambda grupo=None, cliente_id=None: [
    f for f in FAKE
    if (grupo is None or f["Group"] == grupo)
    and (cliente_id is None or f["ClientID"] == cliente_id)]
# el P&L también lee nóminas y compras: se neutralizan para aislar las facturas
from core import payroll as _PR, projects as _P, expenses as _E             # noqa: E402
_op, _ol, _oe = _PR.list_nominas, _P.list_projects, _E._records
_PR.list_nominas = lambda *a, **k: []
_P.list_projects = lambda *a, **k: []
_E._records = lambda *a, **k: []

try:
    print("== el P&L (era el que fallaba) ==")
    p = F.pnl("g")
    chk("facturado ignora la anulada", p["facturado"], 2000.0)
    chk("cobrado ignora sus $200", p["cobrado"], 1000.0)
    chk("por_cobrar sale de las vivas", p["por_cobrar"], 1000.0)
    # F3 vence en 2020 y está anulada: no puede contar como vencida
    chk("vencido NO cuenta la anulada", p["vencido"], 0.0)
    chk("la ganancia no se infla", p["ganancia"], 2000.0)

    print("\n== y las que ya lo hacían bien siguen igual ==")
    r = INV.resumen_cliente("g", "C1")
    chk("resumen del cliente: facturado", r["facturado"], 2000.0)
    chk("resumen del cliente: cobrado", r["cobrado"], 1000.0)
    chk("resumen del cliente: cuenta 2 facturas", r["n"], 2)
    fp = INV.facturado_por_proyecto("g")
    chk("por proyecto: PRJ-1 no hereda los $500 anulados", fp.get("PRJ-1"), 1000.0)
    chk("por proyecto: PRJ-2", fp.get("PRJ-2"), 1000.0)

    print("\n== la anulada SIGUE siendo visible (regla v340) ==")
    # ⚠️ Esto NO se puede comprobar llamando a `list_facturas`: está parcheada por el
    # propio guardián, así que romper la función real no cambiaría el resultado — un
    # chequeo que pasa en vacío. Se mira el CÓDIGO REAL: la función no puede tener un
    # filtro por estado, porque la lista de Facturas y el detalle del cliente las
    # muestran, y ocultarlas de raíz sería el fallo de v340.
    import ast
    import inspect as _i
    _src = _i.getsource(_orig)
    _filtra = any(
        isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value.lower() == "anulada" for n in ast.walk(ast.parse(_src.lstrip())))
    chk("`list_facturas` NO filtra por estado (para poder mostrarlas)", _filtra, False)
    chk("y se reconoce como anulada", INV.estado_cobro(FAKE[2]), "anulada")

    print("\n== simetría con los COSTOS ==")
    # `list_nominas` sí tiene el parámetro; `list_facturas` no, y ESO es lo que
    # despistaba: el comentario del P&L afirmaba un filtro que no existía.
    import inspect
    _pn = inspect.signature(_op).parameters
    chk("`list_nominas` excluye anuladas por defecto", "incluir_anuladas" in _pn)
    chk("`list_facturas` NO tiene ese parámetro (por eso hay que filtrar a mano)",
        "incluir_anuladas" in inspect.signature(_orig).parameters, False)
finally:
    INV.list_facturas = _orig
    _PR.list_nominas, _P.list_projects, _E._records = _op, _ol, _oe

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
