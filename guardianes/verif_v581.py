"""v581 · «NO DEJES NADA PENDIENTE» (decisión del usuario), lo que quedó tras v580.

  1. ⚠️ OCHO generadores de ID (ALR, CAT, ACT, MOV, FAC, ORD, PS, COT) y las nóminas (NOM)
     seguían con `max + 1` a pelo: borrar la fila del ID más alto lo liberaba y el alta
     siguiente heredaba lo que apuntara al viejo. Visto en cliente1: la auditoría guarda
     COT-0001…0003 de cotizaciones de prueba borradas, y la primera REAL habría sido otra
     vez la COT-0001. → todos por `hojas.siguiente_id_libre` (v427), con su respaldo.
  2. ⚠️ `ids_referenciados` miraba una LISTA de hojas (las del lote + la auditoría) y la
     lista envejeció: `PreStarts` no va en el lote y apunta a obras (PS-0002 → PRJ-0015 en
     cliente1). → TODAS las hojas del libro, por su título real.
  3. ⚠️ El roster en lote (`autopoblar_proyecto`) numeraba por NÚMERO DE FILAS: con dos
     filas borradas el ROS- nuevo caía sobre uno que existe. Y las nóminas, `base + 1, + 2…`
     fila a fila sin comprobar nada. → `siguientes_ids_libres`: N IDs, UNA lectura.
  4. ⚠️ Si la lectura fresca fallaba, facturas, inventario, órdenes, catálogo y
     cotizaciones contaban desde CERO y emitían un ID que existe (FAC-0001 otra vez) → a la
     caché. Y los movimientos de inventario y las nóminas sacaban el máximo de la caché
     (regla v323) → fresco.
  5. StageProgress: `SP-<obra>-<etapa>-<posición en el lote>` se repetía entre dos
     confirmaciones de la misma etapa → sigue al mayor de la obra.
  6. ⚠️ La tarjeta que caía sola a la última fila se estiraba a TODO el ancho (medido en
     producción a 846 px con el menú: Status, Timeclock y Library «3 + 1 de 472 px», Costs
     «4 + 1») → `.cpx-kpis` es una rejilla y los once contenedores propios usan la clase.

Todo con hojas FALSAS y `ids_referenciados` sustituido: ninguna hoja real se lee ni escribe.
"""
import ast
import datetime as dt
import io
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


def _src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def _func(rel, nombre):
    return next((n for n in ast.walk(ast.parse(_src(rel)))
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


import streamlit as st                                                      # noqa: E402
st.session_state["auth"] = {"usuario": "Admin2", "rol": "administrator", "grupo": "g"}

from core import hojas as H, timeclock as TC                                # noqa: E402
from core import alerts as AL, catalogo as CAT, inventory as INV            # noqa: E402
from core import invoices as INVC, orders as ORD, prestart as PS            # noqa: E402
from core import quotes as Q, payroll as PR, roster as RO                   # noqa: E402
from core import projects as P, stage_progress as SP                        # noqa: E402

_HELPERS = ("siguiente_id_libre", "siguientes_ids_libres")

# ═════════════════════════════════════════════════════════════════
print("1. Barrido: ningún ID numerado sale de `max + 1` fuera del respaldo")
# Un ID numerado es un f-string que EMPIEZA por «PREFIJO-» y sigue con un número con
# ceros (`{…:04d}`). Fuera de `hojas.py` solo puede vivir dentro de un `except` cuyo `try`
# llama al helper: es el respaldo de cuando la comprobación falla, nada más.
_vistos, _malos = 0, []
for _f in sorted(os.listdir(os.path.join(RAIZ, "core"))):
    if not _f.endswith(".py") or _f == "hojas.py":
        continue
    _a = ast.parse(_src("core/" + _f))
    _padre = {h: n for n in ast.walk(_a) for h in ast.iter_child_nodes(n)}
    for n in ast.walk(_a):
        if not (isinstance(n, ast.JoinedStr) and len(n.values) > 1):
            continue
        v0, v1 = n.values[0], n.values[1]
        if not (isinstance(v0, ast.Constant) and isinstance(v0.value, str)
                and re.fullmatch(r"[A-Z]{1,4}-", v0.value)
                and isinstance(v1, ast.FormattedValue) and v1.format_spec is not None):
            continue
        _spec = "".join(c.value for c in v1.format_spec.values if isinstance(c, ast.Constant))
        if not re.fullmatch(r"0\d+d", _spec):
            continue
        _vistos += 1
        x, _bien = n, False
        while x in _padre:
            x = _padre[x]
            if isinstance(x, ast.ExceptHandler):
                _try = _padre.get(x)
                _bien = isinstance(_try, ast.Try) and any(
                    isinstance(c, ast.Call)
                    and getattr(c.func, "attr", getattr(c.func, "id", "")) in _HELPERS
                    for b in _try.body for c in ast.walk(b))
                break
        if not _bien:
            _malos.append("%s:%d %s" % (_f, n.lineno, ast.unparse(n)))
chk("el barrido ve los generadores (>= 18 IDs numerados)", _vistos >= 18, _vistos)
chk("⚠️ TODOS son el respaldo de un `try` que llama al helper", not _malos, _malos)

# ═════════════════════════════════════════════════════════════════
print("\n2. `siguientes_ids_libres`: N IDs, UNA lectura")
_oir = H.ids_referenciados
_lecturas = []


def _refs(conj):
    def f(pref, propia="", sheet_id=""):
        _lecturas.append((pref, propia))
        return {x for x in conj if x.startswith(pref)}
    return f


try:
    H.ids_referenciados = _refs({"NOM-0006", "NOM-0008"})
    _r = H.siguientes_ids_libres("NOM-", 5, 3, propia="Payroll")
    chk("salta los referenciados: 0007, 0009, 0010", _r == ["NOM-0007", "NOM-0009", "NOM-0010"], _r)
    chk("...con UNA sola lectura del libro", len(_lecturas) == 1, _lecturas)
    chk("`siguiente_id_libre` es el primero de la lista",
        H.siguiente_id_libre("NOM-", 5, propia="Payroll") == "NOM-0007")

    def _revienta(*a, **k):
        raise RuntimeError("sin red")
    H.ids_referenciados = _revienta
    chk("si la comprobación falla, los siguientes sin más",
        H.siguientes_ids_libres("ROS-", 4, 2) == ["ROS-0005", "ROS-0006"])
    H.ids_referenciados = lambda *a, **k: {f"G-{n:05d}" for n in range(1, 999)}
    _r = H.siguientes_ids_libres("G-", 1, 2, ancho=5, tope=5)
    chk("con todo ocupado no se cuelga (tope) y respeta el ancho", _r == ["G-00007", "G-00013"], _r)
finally:
    H.ids_referenciados = _oir

# ═════════════════════════════════════════════════════════════════
print("\n3. `ids_referenciados` mira TODAS las hojas, y excluye la propia por su título REAL")


class _Libro:
    DATOS = {"Cotizaciones": [["ID"], ["COT-0001"]],          # la propia, con el nombre VIEJO
             "AuditTrail": [["ID", "EntityID"], ["AUD-1", "COT-0002"]],
             "PreStarts": [["ID", "ProjectID"], ["PS-0001", "PRJ-0015"]],
             "Gastos": [["ID"], ["COT-0003 en una nota"]],    # una hoja vieja suelta
             "Rick's": [["Nota"], ["ver COT-0009"]]}            # un título con apóstrofo

    def values_batch_get(self, rangos):
        # ⚠️ Como Google: `'Rick''s'` es la hoja «Rick's»; una comilla sin doblar tumba el LOTE
        for r in rangos:
            if r.strip("'").replace("''", "").count("'"):
                raise RuntimeError("Unable to parse range: %s" % r)
        return {"valueRanges": [{"range": r + "!A1:Z9",
                                 "values": self.DATOS[r.strip("'").replace("''", "'")]}
                                for r in rangos]}


_o = (H._libro, H._titulos, TC.titulo_real, TC.sheet_id_para)
H._libro = lambda sheet_id="": _Libro()
H._titulos = lambda sheet_id="": list(_Libro.DATOS)
TC.titulo_real = lambda title="", sheet_id="": {"Quotes": "Cotizaciones"}.get(title, title)
TC.sheet_id_para = lambda title="", grupo=None: "libro-falso"
try:
    _r = H.ids_referenciados("COT-", propia="Quotes")
    chk("⚠️ la propia se excluye aunque se llame por su nombre viejo; cuentan la auditoría "
        "y una hoja que no va en el lote", sorted(_r) == ["COT-0002", "COT-0003", "COT-0009"],
        sorted(_r))
    chk("⚠️ ...incluida una pestaña con apóstrofo («Rick's»): sin escapar, el lote entero "
        "fallaba y la comprobación se apagaba", "COT-0009" in _r, sorted(_r))
    chk("⚠️ PreStarts cuenta (PRJ-0015 no se podría reutilizar)",
        H.ids_referenciados("PRJ-", propia="Projects") == {"PRJ-0015"})
finally:
    H._libro, H._titulos, TC.titulo_real, TC.sheet_id_para = _o
_titulos = _func("core/hojas.py", "_titulos")
chk("los títulos salen del índice del libro (0 llamadas)",
    _titulos is not None and "_libro" in ast.unparse(_titulos))

# ═════════════════════════════════════════════════════════════════
print("\n4. Cada generador salta lo referenciado (hojas falsas)")


class _WS:
    """Una hoja con columna ID; lee con `get_all_values`/`get_all_records`/`col_values`."""
    def __init__(self, ids, rompe=False):
        self.vals = [["ID", "Group", "Week", "User", "DataJSON"]] + [[i, "g", "", "", ""] for i in ids]
        self.rompe, self.escritas = rompe, []

    def get_all_values(self):
        if self.rompe:
            raise RuntimeError("429")
        return [list(f) for f in self.vals]

    def get_all_records(self, numericise_ignore=None):
        if self.rompe:
            raise RuntimeError("429")
        return [dict(zip(self.vals[0], f)) for f in self.vals[1:]]

    def col_values(self, n):
        if self.rompe:
            raise RuntimeError("429")
        return [f[n - 1] for f in self.vals]

    def append_row(self, fila, value_input_option=None):
        self.escritas.append(list(fila))

    def append_rows(self, filas, value_input_option=None):
        self.escritas += [list(f) for f in filas]

    def batch_update(self, *a, **k):
        pass


_rest = []


def _poner(mod, nombre, valor):
    _rest.append((mod, nombre, getattr(mod, nombre)))
    setattr(mod, nombre, valor)


H.ids_referenciados = _refs({"ALR-0004", "PS-0003", "CAT-00003", "ORD-00003", "FAC-0003",
                             "ACT-0003", "MOV-0003", "COT-0001", "COT-0002", "COT-0003",
                             "NOM-0005", "ROS-0005"})
try:
    chk("ALR: 0003 viva, 0004 referenciada → ALR-0005",
        AL._next_id([{"ID": "ALR-0003"}]) == "ALR-0005")
    chk("PS: 0002 viva, 0003 referenciada → PS-0004", PS._next_id([{"ID": "PS-0002"}]) == "PS-0004")
    _poner(CAT, "_ws", lambda: _WS(["CAT-00002"]))
    chk("CAT (5 cifras) → CAT-00004", CAT._next_id() == "CAT-00004", CAT._next_id())
    _poner(ORD, "_ws", lambda: _WS(["ORD-00002"]))
    chk("ORD (5 cifras) → ORD-00004", ORD._next_id() == "ORD-00004", ORD._next_id())
    _poner(INVC, "_ws", lambda: (_WS(["FAC-0002"]), None))
    chk("FAC → FAC-0004", INVC._next_id() == "FAC-0004", INVC._next_id())
    _poner(INV, "_ws", lambda title=None: (_WS(["ACT-0002"] if title == INV.ACTIVOS_SHEET
                                               else ["MOV-0002"]), None))
    chk("ACT → ACT-0004", INV._next_id() == "ACT-0004", INV._next_id())
    chk("MOV → MOV-0004", INV._next_mov_id() == "MOV-0004", INV._next_mov_id())

    # ⚠️ El caso de cliente1: hoja de cotizaciones VACÍA y la auditoría con 0001…0003
    _wq = _WS([])
    _poner(Q, "_ws", lambda: _wq)
    _poner(Q, "_invalidate", lambda: None)

    class _QC:
        @staticmethod
        def today(g=None):
            return dt.date(2026, 10, 18)

        @staticmethod
        def now(g=None):
            return dt.datetime(2026, 10, 18, 10, 0)
    _poner(Q, "clock", _QC)
    _ok, _cid = Q.crear("g", "CLI-0001", "Cliente", [{"concepto": "x", "cantidad": 1,
                                                      "costo_unit": 100, "ganancia": 10}],
                        creado_por="t")
    chk("⚠️ COT: hoja vacía y 0001…0003 en la auditoría → COT-0004 (antes COT-0001)",
        _ok and _cid == "COT-0004", (_ok, _cid))
    chk("...y el NÚMERO que ve el cliente empieza en 0001 (no es la identidad)",
        _wq.escritas and _wq.escritas[0][4] == "0001", _wq.escritas[:1])

    # Nóminas: dos personas → dos IDs, saltando NOM-0005
    _wp = _WS(["NOM-0003", "NOM-0004"])
    _poner(PR, "_ws", lambda: (_wp, None))
    _poner(PR, "_invalidate", lambda: None)
    _poner(PR, "clock", _QC)         # sin él, la zona del grupo se leería de la hoja real
    _poner(PR, "list_nominas", lambda g, incluir_anuladas=False: [])
    _poner(PR.timeclock, "horas_por_usuario_rango", lambda g, d, h: {
        "u1": {"nombre": "Ana", "horas": 10.0}, "u2": {"nombre": "Beto", "horas": 8.0}})
    _poner(PR.auth, "rate_map", lambda g: {"u1": 40.0, "u2": 40.0})
    from core import ausencias as AU                                        # noqa: E402
    _poner(AU, "horas_pagadas_grupo", lambda *a, **k: {})
    _r = PR.generar("g", "2026-10-05", "2026-10-11", creado_por="t")
    _ids = [f[0] for f in _wp.escritas]
    chk("⚠️ NOM: 0003-0004 vivas, 0005 referenciada → NOM-0006 y NOM-0007",
        _ids == ["NOM-0006", "NOM-0007"], (_ids, _r))
    _wp2 = _WS(["NOM-0003"], rompe=True)
    PR._ws = lambda: (_wp2, None)
    _poner(PR, "_records", lambda: [{"ID": "NOM-0009"}])
    chk("NOM: si la lectura fresca falla, el máximo sale de la caché (9), no de cero",
        PR._max_num() == 9, PR._max_num())

    # Roster en lote: filas 0003 y 0004 (dos filas) — con `len(vals)` salía ROS-0004, que EXISTE
    _wr = _WS(["ROS-0003", "ROS-0004"])
    _poner(RO, "_ws_roster", lambda: _wr)
    _r = RO.autopoblar_proyecto("g", "PRJ-0001", ["u1", "u2"], "2026-10-19", "2026-10-23")
    _ids = [f[0] for f in _wr.escritas]
    chk("⚠️ ROS en lote: sigue al MAYOR (0004), salta 0005 → ROS-0006 y ROS-0007",
        _ids == ["ROS-0006", "ROS-0007"], (_ids, _r))
finally:
    for mod, nombre, valor in reversed(_rest):
        setattr(mod, nombre, valor)
    _rest.clear()
    H.ids_referenciados = _oir

# ═════════════════════════════════════════════════════════════════
print("\n5. ⚠️ Si la lectura fresca falla: a la CACHÉ, nunca desde cero")
H.ids_referenciados = lambda *a, **k: set()
try:
    _poner(INVC, "_ws", lambda: (_WS([], rompe=True), None))
    _poner(INVC, "_records", lambda: [{"ID": "FAC-0007"}])
    chk("FAC: con 0007 en la caché → FAC-0008 (antes FAC-0001, que existe)",
        INVC._next_id() == "FAC-0008", INVC._next_id())
    _poner(INV, "_ws", lambda title=None: (_WS([], rompe=True), None))
    _poner(INV, "_records", lambda title: [{"ID": "ACT-0005"}] if title == INV.ACTIVOS_SHEET
           else [{"ID": "MOV-0011"}])
    chk("ACT → ACT-0006", INV._next_id() == "ACT-0006", INV._next_id())
    chk("MOV → MOV-0012", INV._next_mov_id() == "MOV-0012", INV._next_mov_id())
    _poner(ORD, "_ws", lambda: _WS([], rompe=True))
    _poner(ORD, "_records", lambda: [{"ID": "ORD-00004"}])
    chk("ORD → ORD-00005", ORD._next_id() == "ORD-00005", ORD._next_id())
    _poner(CAT, "_ws", lambda: _WS([], rompe=True))
    _poner(CAT, "_records", lambda: [{"ID": "CAT-00009"}])
    chk("CAT → CAT-00010", CAT._next_id() == "CAT-00010", CAT._next_id())
    _poner(Q, "_ws", lambda: _WS([], rompe=True))
    _poner(Q, "_records", lambda: [{"ID": "COT-0006", "Number": "0004"}])
    chk("COT: el ID y el número salen de la caché (6 y 4), no de cero",
        Q._ids_frescos() == (6, 4), Q._ids_frescos())
    # ⚠️ El NÚMERO de factura (el impreso y el de Xero) salía de la caché: atrasada, dos
    # facturas con el mismo número. La hoja dice 0005 y la caché aún 0004 → 0006.
    class _WSF(_WS):
        def get_all_records(self, numericise_ignore=None):
            if self.rompe:
                raise RuntimeError("429")
            return [{"ID": "FAC-0001", "Group": "g", "Number": "0004"},
                    {"ID": "FAC-0002", "Group": "g", "Number": "0005"},
                    {"ID": "FAC-0003", "Group": "otro", "Number": "0099"}]
    _poner(INVC, "_ws", lambda: (_WSF([]), None))
    _poner(INVC, "_records", lambda: [{"Group": "g", "Number": "0004"}])
    chk("⚠️ número de factura: FRESCO (la hoja ya tiene la 0005 → 6), no la caché (→ 5)",
        INVC._next_numero("g") == 6, INVC._next_numero("g"))
    INVC._ws = lambda: (_WSF([], rompe=True), None)
    chk("...y si la lectura falla, la caché (5), no desde cero",
        INVC._next_numero("g") == 5, INVC._next_numero("g"))
    _mv = _func("core/inventory.py", "_next_mov_id")
    chk("MOV lee FRESCO (`_ids_frescos`), no la caché de 120 s (v323)",
        "_ids_frescos" in ast.unparse(_mv) and "_records" not in ast.unparse(_mv))
finally:
    for mod, nombre, valor in reversed(_rest):
        setattr(mod, nombre, valor)
    _rest.clear()
    H.ids_referenciados = _oir

# ═════════════════════════════════════════════════════════════════
print("\n6. StageProgress: dos confirmaciones de la misma etapa, dos IDs")
import fixture_guardado as FG                                               # noqa: E402


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-10-18 10:00" if "%H" in f else "2026-10-18"

    def now(self, g=None):
        return self._T()


PRJ = {"ID": "PRJ-T", "Group": "cliente1", "Type": "Installation", "Name": "t",
       "StagePlanJSON": P.plan_nuevo("Installation", ()), "Progress": "0",
       "Status": "Planned", "ManualStatus": ""}
PLAN = SP.plan_de_obra(PRJ)
A6 = [a["nombre"] for a in PLAN[5]["actividades"]]
_oc, _orc = SP.clock, SP._records
SP.clock, SP._records = _Reloj(), (lambda: [])
m = FG.montar(SP, P, PRJ)
try:
    SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": 6, "actividad": A6[0], "pct": 100}], quien="t")
    SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": 6, "actividad": A6[1], "pct": 100}], quien="t")
    _ids = [f[0] for f in m.sp.nuevas]
    chk("⚠️ dos IDs DISTINTOS (antes los dos `SP-PRJ-T-6-0`)",
        _ids == ["SP-PRJ-T-6-0", "SP-PRJ-T-6-1"], _ids)
finally:
    m.restaurar()
m = FG.montar(SP, P, PRJ, creditos=[{"ID": "SP-PRJ-T-3-4", "StageOrder": "3",
                                     "Activity": "vieja", "Pct": "100"}])
try:
    SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": 6, "actividad": A6[0], "pct": 50}], quien="t")
    _ids = [f[0] for f in m.sp.nuevas]
    chk("...y siguen al MAYOR de la obra (había un -4 → -5)", _ids == ["SP-PRJ-T-6-5"], _ids)
finally:
    m.restaurar()
    SP.clock, SP._records = _oc, _orc

# ═════════════════════════════════════════════════════════════════
print("\n7. La rejilla de cifras")
from core import theme as T                                                 # noqa: E402
_css = re.sub(r"/\*.*?\*/", "", T._CSS, flags=re.S)
_k = re.search(r"\.cpx-kpis\s*\{([^}]*)\}", _css)
chk("⚠️ `.cpx-kpis` es una REJILLA (no flex)", _k and "display: grid" in _k.group(1)
    and "flex-wrap" not in _k.group(1), _k.group(1) if _k else None)
chk("...columnas iguales con `auto-fit` y la base en `--cpx-min` (150 por defecto)",
    _k and "repeat(auto-fit, minmax(min(100%, var(--cpx-min, 150px)), 1fr))" in _k.group(1))
_flex = []
for _f in sorted(os.listdir(os.path.join(RAIZ, "core"))):
    if _f.endswith(".py"):
        for i, ln in enumerate(_src("core/" + _f).splitlines(), 1):
            if re.search(r"display:\s*flex;\s*gap:\s*10px;\s*flex-wrap:\s*wrap", ln):
                _flex.append("%s:%d" % (_f, i))
chk("⚠️ ninguna fila de tarjetas con su propio flex (eran once)", not _flex, _flex)
# La base de cada fila propia = la de SUS tarjetas (no su min-width: con 104 px «16/11/2026»
# se partía en dos líneas — medido en producción).
# ⚠️ v592 · Al día con su razón (v385): la plomada ya no tiene fila HTML — sus cinco cifras
# son BOTONES activos (`cpxkpi_plb_*`) en un contenedor con `T.por_fila`, la rejilla del tema.
# El principio (ninguna fila con su propio flex, la base la de sus tarjetas) se mantiene: para
# la plomada se afirma la rejilla del tema.
for _f, _base in (("belting_ui.py", 96), ("buffer_cut_ui.py", 96), ("rail_cut_ui.py", 96),
                  ("prestart_ui.py", 110), ("timeclock_ui.py", 132)):
    _s = _src("core/" + _f)
    chk("%s: la fila es `cpx-kpis` con la base de sus tarjetas (%d px)" % (_f, _base),
        'class="cpx-kpis" style="--cpx-min:%dpx;' % _base in _s
        and "min-width:%dpx" % _base in _s)
_spl = _src("core/plumb_ui.py")
chk("plumb_ui.py: sus cifras son botones en la rejilla del tema (`T.por_fila`), sin flex propio",
    'T.por_fila("cpx_plb_kpis", 5)' in _spl and 'key="cpx_plb_kpis"' in _spl
    and "display:flex" not in _spl)
_pu = _src("core/projects_ui.py")
chk("projects_ui: Status, el plan acordado y el resumen con la base del tema (150)",
    _pu.count('<div class="cpx-kpis" style="margin:') == 3)
chk("projects_ui: Costs con 110 px (v559) y sin su clase propia",
    '<div class="cpx-kpis" style="--cpx-min:110px;margin:0 0 10px">' in _pu
    and "cpx-kpis-cst" not in _pu)
chk("ausencias_ui: la rejilla del tema",
    '<div class="cpx-kpis" style="margin:0 0 8px">' in _src("core/ausencias_ui.py"))

print("\n=== %d ok · %d fallo(s) ===" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
