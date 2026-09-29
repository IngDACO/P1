# -*- coding: utf-8 -*-
"""v528 · GUARDAR MÁS RÁPIDO: menos llamadas, heartbeat en segundo plano y «Saving…».

Medido en producción (v527): guardar una etapa tardaba ~9,5 s, 7-8 de ellos en ~9 llamadas a
Google de ~1 s cada una desde el Cloud; y cada 50 s el heartbeat paraba un clic ~1,9 s.

Lo que protege:
  (a) ⚠️ `hojas.frescas` lee VARIAS hojas en UNA llamada y da lo MISMO que
      `get_all_records` —el registro `i` es la fila `i + 2`—: si no, se escribiría en la
      fila de otro. Oráculo: las funciones de gspread que usa `get_all_records`;
  (b) `hojas.escribir` escribe VARIAS hojas en UNA llamada, siempre RAW (v42);
  (c) ⚠️ guardar una etapa = 1 lectura + ≤ 1 append + 1 escritura (antes ~9), y el
      resultado en las tres hojas es el que daba el camino viejo: el avance de la obra es
      el que `compute_avance` saca de `Activities` DESPUÉS de escribir;
  (d) ⚠️ se decide con la lectura FRESCA, no con la caché de la pantalla: con dos
      personas en la misma obra, la caché haría bajar el % de una etapa;
  (e) ⚠️ si no se puede, no se escribe NADA (obra que no está, lectura fallida), y el
      mensaje dice lo que quedó guardado;
  (f) el rastro de cambios sigue (decisión: no se quita sin un sí), con el «antes» FRESCO;
  (g) ⚠️ el heartbeat NO bloquea la página, un fallo de Google no expulsa a nadie y un
      token desplazado sí; su hilo no toca Streamlit;
  (h) app.py mira el resultado en CADA pasada y lanza el heartbeat cada 50 s;
  (i) «Saving…» alrededor de cada guardado del campo — y la pantalla, EJECUTADA.
"""
import ast
import io
import os
import sys
import threading
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "field", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


import fixture_guardado as FG                                     # noqa: E402
from gspread.utils import fill_gaps, to_records                   # noqa: E402

from core import auditoria                                        # noqa: E402
from core import auth as A                                        # noqa: E402
from core import columnas, valores                                # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-09-29 10:00" if "%H" in f else "2026-09-29"

    def now(self, g=None):
        return self._T()


# ═════════════════════════════════════════════════════════════════
sec("1. `hojas.frescas`: varias hojas, UNA llamada, lo mismo que `get_all_records`")


class _LibroCrudo:
    def __init__(self, grids, id_="L1"):
        self.id, self.grids, self.pedidos = id_, grids, []

    def values_batch_get(self, rangos, params=None):
        self.pedidos.append(list(rangos))
        return {"valueRanges": [{"range": r + "!A1:Z9",
                                 "values": self.grids[r.strip("'").replace("''", "'")]}
                                for r in rangos]}

    def values_batch_update(self, body):
        self.pedidos.append(body)


class _Hoja:
    def __init__(self, libro, titulo):
        self.spreadsheet, self.title, self.lotes = libro, titulo, []

    def get_all_records(self, numericise_ignore=None):
        g = fill_gaps(self.spreadsheet.grids[self.title])
        return to_records(g[0], g[1:])

    def batch_update(self, lote, value_input_option=None):
        self.lotes.append((lote, value_input_option))


_viejo, _nuevo = next((k, v) for k, v in columnas.LEGADO.items() if k != v)
_vv, _vn = next((k, v) for k, v in valores.LEGADO.items()
                if ("Projects", "Status") in valores.COLUMNAS and k != v)
# Una fila vacía EN MEDIO y otra CORTA: es donde un índice de fila se descuadra.
GA = [["ID", "Order", _viejo], ["a1", "1", "x"], [], ["a3"], ["a4", "4", "y"]]
GB = [["ID", "Status"], ["p1", _vv], ["p2", "Planned"]]
GC = [["ID", "Name"], ["c1", "O'Brien"]]
_L = _LibroCrudo({"Activities": GA, "Projects": GB, "Rick's": GC})
_hA, _hB, _hC = _Hoja(_L, "Activities"), _Hoja(_L, "Projects"), _Hoja(_L, "Rick's")
_r = H.frescas({"Activities": _hA, "Projects": _hB, "Rick's": _hC})
chk("⚠️ tres hojas en UNA llamada", len(_L.pedidos) == 1 and len(_L.pedidos[0]) == 3,
    _L.pedidos)
chk("...con el título entre comillas, y la comilla de dentro doblada",
    _L.pedidos and _L.pedidos[0][2] == "'Rick''s'", _L.pedidos)
_g = fill_gaps(GA)
_oraculo = columnas.canonizar(to_records(_g[0], _g[1:]))
chk("⚠️ los registros son los de `get_all_records` (oráculo: sus propias funciones)",
    _r.get("Activities") == _oraculo, (_r.get("Activities"), _oraculo))
chk("...y la fila vacía de en medio CUENTA: «a4» es el registro 3 → fila 5",
    [x.get("ID") for x in _r.get("Activities", [])].index("a4") + 2 == 5,
    _r.get("Activities"))
chk("...con la cabecera vieja canonizada (%s → %s)" % (_viejo, _nuevo),
    _nuevo in (_r.get("Activities") or [{}])[0], (_r.get("Activities") or [{}])[0])
chk("...y los VALORES de negocio de esa hoja también (%s → %s)" % (_vv, _vn),
    (_r.get("Projects") or [{}])[0].get("Status") == _vn, _r.get("Projects"))
chk("el texto llega como TEXTO (nunca numerizado, v42)",
    (_r.get("Activities") or [{}])[0].get("Order") == "1")


class _LibroCorto(_LibroCrudo):
    def values_batch_get(self, rangos, params=None):
        return {"valueRanges": [{"range": rangos[0], "values": GA}]}


_Lc = _LibroCorto({})
try:
    H.frescas({"Activities": _Hoja(_Lc, "Activities"), "Projects": _Hoja(_Lc, "Projects")})
    chk("⚠️ si Google devuelve MENOS hojas de las pedidas, lanza (no se adivina)", False)
except Exception as e:
    chk("⚠️ si Google devuelve MENOS hojas de las pedidas, lanza (no se adivina)", True, e)

_L2 = _LibroCrudo({"Projects": GB}, id_="OTRO")
_mix = H.frescas({"Activities": _hA, "Projects": _Hoja(_L2, "Projects")})
chk("en libros DISTINTOS lee cada una por su lado (más lento, igual de correcto)",
    _mix.get("Activities") == _oraculo and len(_L2.pedidos) == 0
    and (_mix.get("Projects") or [{}])[0].get("Status") == _vn, _mix)

# ═════════════════════════════════════════════════════════════════
sec("2. `hojas.escribir`: varias hojas, UNA llamada, RAW")
_L = _LibroCrudo({})
_hA, _hB, _hC = _Hoja(_L, "Activities"), _Hoja(_L, "Projects"), _Hoja(_L, "Rick's")
H.escribir([(_hA, [{"range": "F5", "values": [["17.0"]]}]), (_hB, []),
            (_hC, [{"range": "B2", "values": [["007"]]}])])
_b = _L.pedidos[0] if _L.pedidos else {}
chk("⚠️ UNA llamada para dos hojas (la vacía no cuenta)",
    len(_L.pedidos) == 1 and len(_b.get("data", [])) == 2, _L.pedidos)
chk("...RAW, que conserva «007» (v42)", _b.get("valueInputOption") == "RAW", _b)
chk("...y cada rango con SU hoja delante",
    [d["range"] for d in _b.get("data", [])] == ["'Activities'!F5", "'Rick''s'!B2"], _b)
_L.pedidos.clear()
H.escribir([(_hA, []), (_hB, [])])
chk("sin nada que escribir, CERO llamadas", _L.pedidos == [], _L.pedidos)
_L2 = _LibroCrudo({}, id_="OTRO")
_hX = _Hoja(_L2, "Projects")
H.escribir([(_hA, [{"range": "F5", "values": [["1"]]}]), (_hX, [{"range": "N3",
                                                                    "values": [["2"]]}])])
chk("en libros distintos, una escritura por hoja, también RAW",
    _hA.lotes and _hX.lotes and _hA.lotes[-1][1] == "RAW" and _hX.lotes[-1][1] == "RAW",
    (_hA.lotes, _hX.lotes))

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ Guardar una etapa: cuántas llamadas y qué queda escrito")
PRJ = {"ID": "PRJ-T", "Group": "cliente1", "Type": "Installation", "Name": "t",
       "StagePlanJSON": P.plan_nuevo("Installation", ()), "Progress": "0",
       "Status": "Planned", "ManualStatus": ""}
PLAN = SP.plan_de_obra(PRJ)
O6 = 6
A6 = [a["nombre"] for a in PLAN[O6 - 1]["actividades"]]
INF = next(((i, n) for i, e in enumerate(PLAN, start=1)
            for n in S.informativas(e.get("pista"), e.get("numero"))), None)
_oc, _ocr, _orc = SP.clock, SP.creditos, SP._records
SP.clock = _Reloj()
# La caché de la pantalla, VACÍA: el guardado no debe mirarla (sección 4), y si una rotura
# la mirara, que no acabe leyendo la hoja real.
SP._records = lambda: []


def _final(m):
    """Lo que dice la hoja DESPUÉS: el avance de la obra recalculado desde `Activities`."""
    _acts = [r for r in m.acts.registros() if r.get("ProjectID") == "PRJ-T"]
    _p = next(r for r in m.prjs.registros() if r.get("ID") == "PRJ-T")
    return _acts, _p


m = FG.montar(SP, P, PRJ)
try:
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("se acredita", _ok, _msg)
    chk("⚠️ crédito NUEVO: 1 lectura + 1 append + 1 escritura (antes ~9 llamadas)",
        m.cuenta() == {"leer": 1, "append": 1, "escribir": 1}, m.cuenta())
    _esp = next(e for e in SP._sobre(PLAN, {(O6, A6[0]): 100.0}) if e["orden"] == O6)["pct"]
    _acts, _p = _final(m)
    _a6 = next(a for a in _acts if a.get("Order") == str(O6))
    chk("la etapa queda en Activities con su %% (%.1f)" % _esp,
        abs(float(_a6.get("Progress") or -1) - _esp) < 1e-9, _a6)
    _av = P.compute_avance(_acts)
    chk("⚠️ el avance de la obra es el que `compute_avance` saca de Activities DESPUÉS "
        "(%.1f), como hacía el recálculo que releía" % _av,
        abs(float(_p.get("Progress") or -1) - _av) < 1e-9, _p.get("Progress"))
    chk("...y el estado sale de ahí (%s)" % P.derive_estado(_av, "", "Installation"),
        _p.get("Status") == P.derive_estado(_av, "", "Installation"), _p.get("Status"))
    chk("la fila nueva de StageProgress cuadra con la cabecera",
        len(m.nuevas_sp()) == 1 and len(m.sp.nuevas[0]) == len(SP.HEADERS), m.sp.nuevas)

    m.libro.llamadas.clear()
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 0}], quien="Bobo")
    chk("⚠️ DESHACER (fila que ya existe): 1 lectura + 1 escritura, sin append",
        _ok and m.cuenta() == {"leer": 1, "append": 0, "escribir": 1}, (m.cuenta(), _msg))
    _acts, _p = _final(m)
    _sp = [r for r in m.sp.registros() if r.get("ProjectID") == "PRJ-T"]
    chk("...reescribe la MISMA fila (no nace otra) y la deja a 0",
        len(_sp) == 1 and float(_sp[0].get("Pct")) == 0.0, _sp)
    chk("...y la obra vuelve a 0 y «Planned»",
        float(_p.get("Progress")) == 0.0 and _p.get("Status") == "Planned", _p)
    chk("⚠️ la OTRA obra no se ha tocado en ninguna de las tres hojas",
        next(r for r in m.acts.registros() if r["ProjectID"] == "PRJ-AJENA")["Progress"]
        == "33"
        and next(r for r in m.prjs.registros() if r["ID"] == "PRJ-AJENA")["Status"]
        == "In progress"
        and next(r for r in m.sp.registros() if r["ProjectID"] == "PRJ-AJENA")["Pct"] == "100")

    if INF:
        m.libro.llamadas.clear()
        _n_aud = len(m.auditado)
        _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                                 [{"etapa": INF[0], "actividad": INF[1], "pct": 100}],
                                 quien="Bobo")
        chk("una INFORMATIVA nueva: 1 lectura + 1 append y NADA más (%s)" % INF[1],
            _ok and m.cuenta() == {"leer": 1, "append": 1, "escribir": 0},
            (m.cuenta(), _msg))
        chk("...ni rastro de cambios (el avance no se movió)", len(m.auditado) == _n_aud)
    else:
        fallo("el plan de instalación tiene alguna informativa (para probarla)")
finally:
    m.restaurar()

# ═════════════════════════════════════════════════════════════════
sec("4. ⚠️ Se decide con la lectura FRESCA, no con la caché")
# Otra persona acreditó A6[1] hace un momento; la caché de ESTA pantalla no lo ve.
m = FG.montar(SP, P, PRJ, creditos=[{"StageOrder": str(O6), "Activity": A6[1],
                                     "Pct": "100", "WorkDate": "2026-09-28"}])
try:
    SP.creditos = lambda pid, etapa=None: []          # la caché: vacía, rancia
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    _dos = next(e for e in SP._sobre(PLAN, {(O6, A6[0]): 100.0, (O6, A6[1]): 100.0})
                if e["orden"] == O6)["pct"]
    _uno = next(e for e in SP._sobre(PLAN, {(O6, A6[0]): 100.0}) if e["orden"] == O6)["pct"]
    _w = m.escrituras_avance()
    chk("⚠️ la etapa cuenta lo del OTRO (%.1f%%, no %.1f%%)" % (_dos, _uno),
        _ok and _w and abs(_w[0][0]["avance"] - _dos) < 1e-9, (_w, _msg))
    chk("...y su fecha también: la etapa empieza el 28 (el del otro), no hoy",
        m.actividades_escritas().get(O6, {}).get("ActualStartDate") == "2026-09-28",
        m.actividades_escritas())
finally:
    SP.creditos = _ocr
    m.restaurar()

# ═════════════════════════════════════════════════════════════════
sec("5. ⚠️ Si no se puede, no se escribe NADA")
m = FG.montar(SP, P, PRJ)
try:
    m.prjs.grid = [m.prjs.grid[0], m.prjs.grid[1]]    # solo la obra AJENA
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("⚠️ la obra no está en Projects → no se acredita", not _ok and "not found" in _msg,
        _msg)
    chk("...y no se escribe NADA (hasta v527 quedaban los créditos y la obra sin recalcular)",
        m.cuenta() == {"leer": 1, "append": 0, "escribir": 0}, m.cuenta())
finally:
    m.restaurar()
m = FG.montar(SP, P, PRJ)
try:
    m.libro.falla_lectura = True
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("la lectura falla → «Error saving» y nada escrito",
        not _ok and "Error saving" in _msg and m.cuenta()["append"] == 0
        and m.cuenta()["escribir"] == 0, (_msg, m.cuenta()))
finally:
    m.restaurar()
m = FG.montar(SP, P, PRJ)
try:
    m.libro.falla_escritura = True
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("⚠️ con un crédito NUEVO guardado y la etapa sin mover, se DICE",
        not _ok and "could not be updated" in _msg, _msg)
finally:
    m.restaurar()
m = FG.montar(SP, P, PRJ, creditos=[{"StageOrder": str(O6), "Activity": A6[0], "Pct": "100"}])
try:
    m.libro.falla_escritura = True
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 0}], quien="Bobo")
    chk("...y sin filas nuevas, lo que falló era TODO: «Error saving», no «was saved»",
        not _ok and "Error saving" in _msg and "was saved" not in _msg, _msg)
finally:
    m.restaurar()

# ═════════════════════════════════════════════════════════════════
sec("6. El rastro de cambios sigue, con el «antes» FRESCO")
_ogp = P.get_project
m = FG.montar(SP, P, PRJ)
try:
    # La caché dice otra cosa: el «antes» tiene que salir de la hoja, no de aquí.
    P.get_project = lambda pid: {"ID": pid, "Progress": "77", "Status": "On hold",
                                 "Group": "zz"}
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("una línea de rastro por guardado", _ok and len(m.auditado) == 1, m.auditado)
    _a, _k = m.auditado[0] if m.auditado else ((), {})
    _d = _a[2] if len(_a) > 2 else {}
    chk("...de la obra", _a[:2] == ("proyecto", "PRJ-T"), _a[:2])
    chk("⚠️ ...con el «antes» de la hoja (0 · Planned), no el de la caché (77 · On hold)",
        _d.get("Progress", [None])[0] == "0" and _d.get("Status", [None])[0] == "Planned", _d)
    chk("...y el grupo de la fila", _k.get("grupo") == "cliente1", _k)
finally:
    P.get_project = _ogp
    m.restaurar()
m = FG.montar(SP, P, PRJ)
try:
    def _revienta(*a, **k):
        raise RuntimeError("AuditTrail no responde")
    auditoria.registrar = _revienta
    _ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                             [{"etapa": O6, "actividad": A6[0], "pct": 100}], quien="Bobo")
    chk("si el rastro falla, el guardado ya está hecho: no se deshace ni se niega (v342)",
        _ok and m.cuenta()["escribir"] == 1, (_msg, m.cuenta()))
finally:
    m.restaurar()
SP.clock, SP._records = _oc, _orc

# ═════════════════════════════════════════════════════════════════
sec("7. Las reglas de fechas de Activities: UNA sola copia")
_tp = ast.parse(_fuente("core/projects.py"))
_fn = {n.name: n for n in ast.walk(_tp) if isinstance(n, ast.FunctionDef)}
_llama = lambda f, nombre: any(isinstance(n, ast.Call) and (  # noqa: E731
    getattr(n.func, "id", "") == nombre or getattr(n.func, "attr", "") == nombre)
    for n in ast.walk(_fn[f]))
chk("la rejilla vieja (`save_field_progress`) usa `_lote_avance`",
    _llama("save_field_progress", "_lote_avance"))
chk("...y ya no lleva su propia copia de las fechas",
    "ActualStartDate" not in ast.unparse(_fn["save_field_progress"]))
_ts = ast.parse(_fuente("core/stage_progress.py"))
_acr = next(n for n in ast.walk(_ts) if isinstance(n, ast.FunctionDef) and n.name == "acreditar")
chk("el guardado por etapas usa la MISMA (`P._lote_avance`)",
    any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "_lote_avance"
        for n in ast.walk(_acr)))
chk("...y `stage_progress` no escribe fechas de Activities por su cuenta",
    "ActualStartDate" not in _fuente("core/stage_progress.py")
    and "ActualEndDate" not in _fuente("core/stage_progress.py"))
chk("...ni pasa ya por `save_field_progress` (que lee y escribe hoja a hoja)",
    not any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "save_field_progress"
            for n in ast.walk(_acr)))

# ═════════════════════════════════════════════════════════════════
sec("8. ⚠️ El heartbeat en SEGUNDO PLANO")


class _Login:
    """La hoja Login de mentira: tarda en contestar, como Google desde el Cloud."""

    def __init__(self, espera=1.0, revienta=False):
        self.espera, self.revienta, self.lecturas, self.celdas = espera, revienta, 0, []

    def get_all_records(self, numericise_ignore=None):
        self.lecturas += 1
        time.sleep(self.espera)
        if self.revienta:
            raise RuntimeError("429 de Google")
        return [{"User": "otro", "SessionToken": "X"},
                {"User": "u1", "SessionToken": "TOK", "SessionTime": "1"}]

    def update_cell(self, f, c, v):
        self.celdas.append((f, c, v))


def _espera(u, tok, tope=6.0):
    t0 = time.time()
    while time.time() - t0 < tope:
        with A._HB_LOCK:
            h = (A._HB.get((u, tok)) or {}).get("hilo")
        if h is None:
            break
        time.sleep(0.05)
    return A.heartbeat_resultado(u, tok)


_ogl = A._get_login_ws
try:
    _lw = _Login(espera=1.0)
    A._get_login_ws = lambda: (_lw, None)
    A._HB.clear()
    t0 = time.perf_counter()
    A.heartbeat_en_fondo("u1", "TOK")
    _dt = time.perf_counter() - t0
    chk("⚠️ lanzarlo NO espera a Google (%.2f s con una hoja que tarda 1 s)" % _dt, _dt < 0.3,
        _dt)
    chk("...mientras corre, todavía no hay veredicto (None, no se expulsa)",
        A.heartbeat_resultado("u1", "TOK") is None, A.heartbeat_resultado("u1", "TOK"))
    A.heartbeat_en_fondo("u1", "TOK")
    chk("el token VIGENTE → True", _espera("u1", "TOK") is True, A._HB)
    chk("...marcando vida en Login (una celda)", len(_lw.celdas) == 1, _lw.celdas)
    chk("...y un segundo lanzamiento con el primero en marcha NO abre otro hilo",
        _lw.lecturas == 1, _lw.lecturas)
    A.heartbeat_en_fondo("u1", "TOK-VIEJO")
    chk("⚠️ un token DESPLAZADO → False (expulsar)", _espera("u1", "TOK-VIEJO") is False)
    A.heartbeat_en_fondo("nadie", "TOK")
    chk("una cuenta que no está → False, como `heartbeat`", _espera("nadie", "TOK") is False)
    _lw2 = _Login(espera=0.1, revienta=True)
    A._get_login_ws = lambda: (_lw2, None)
    A.heartbeat_en_fondo("u1", "TOK2")
    chk("⚠️ Google falla → True: un hipo de la API no expulsa a nadie",
        _espera("u1", "TOK2") is True)
    # ⚠️ Lo inesperado DENTRO del hilo (no un error de Google, que `heartbeat` ya trata):
    # tampoco expulsa. Sin esto, la rama `except` de `_hb_hilo` no la ejercitaba nadie.
    _ohc = A._heartbeat_con
    A._heartbeat_con = lambda *a: 1 / 0
    try:
        A._get_login_ws = lambda: (_Login(espera=0.0), None)
        A.heartbeat_en_fondo("u1", "TOK4")
        chk("⚠️ el hilo revienta por algo inesperado → True: tampoco expulsa",
            _espera("u1", "TOK4") is True)
    finally:
        A._heartbeat_con = _ohc
    A._get_login_ws = lambda: (None, "sin hoja")
    A.heartbeat_en_fondo("u1", "TOK3")
    chk("sin hoja no se lanza nada (y nadie queda expulsado)",
        A.heartbeat_resultado("u1", "TOK3") is None)
    A._get_login_ws = lambda: (_Login(espera=0.0), None)
    A.heartbeat_en_fondo("u1", "TOK")
    _espera("u1", "TOK")
    _hilos = [h for h in threading.enumerate() if h.name == "heartbeat"]
    chk("el hilo es de fondo (daemon): no retiene el proceso", all(h.daemon for h in _hilos))
    chk("`heartbeat` síncrono sigue igual (lo usa `verif_auth_guards`)",
        A.heartbeat("u1", "TOK") is True and A.heartbeat("u1", "MAL") is False)
finally:
    A._get_login_ws = _ogl
    A._HB.clear()
_ta = ast.parse(_fuente("core/auth.py"))
_fa = {n.name: n for n in ast.walk(_ta) if isinstance(n, ast.FunctionDef)}
_nombres = lambda f: {getattr(n, "id", None) for n in ast.walk(_fa[f])} | {  # noqa: E731
    getattr(n, "attr", None) for n in ast.walk(_fa[f])}
chk("⚠️ lo que corre en el hilo NO toca Streamlit (ni `st` ni la sesión)",
    "st" not in _nombres("_hb_hilo") and "st" not in _nombres("_heartbeat_con")
    and "session_state" not in _nombres("_heartbeat_con"))
chk("...ni resuelve la hoja ahí dentro (se le pasa ya abierta)",
    "_get_login_ws" not in _nombres("_heartbeat_con") and "_get_login_ws" in _nombres("heartbeat"))
chk("la sonda de arriba SÍ ve `st` en las funciones de auth que lo usan (trampa nº12)",
    sum(1 for f in _fa if "st" in _nombres(f)) >= 1, [f for f in _fa if "st" in _nombres(f)][:5])

# ═════════════════════════════════════════════════════════════════
sec("9. app.py: el veredicto en CADA pasada, el heartbeat cada 50 s")
_app = _fuente("app.py")
_tapp = ast.parse(_app)
_ifs = [n for n in _tapp.body if isinstance(n, ast.If)]
_veredicto = [n for n in _ifs if "heartbeat_resultado" in ast.unparse(n.test)]
_throttle = [n for n in _ifs if "_hb_last" in ast.unparse(n.test)]
chk("⚠️ el veredicto se mira a nivel de módulo, FUERA del throttle (en cada pasada)",
    len(_veredicto) == 1 and len(_throttle) == 1
    and "heartbeat_resultado" not in ast.unparse(_throttle[0]), (len(_veredicto), len(_throttle)))
chk("...y va ANTES del throttle",
    _veredicto and _throttle and _veredicto[0].lineno < _throttle[0].lineno)
_v = ast.unparse(_veredicto[0]) if _veredicto else ""
chk("...expulsa solo con un False explícito (None = aún no se sabe)", " is False" in _v, _v)
chk("...y expulsa de verdad: quita la sesión y corta la pasada",
    "session_state.pop('auth'" in _v and "st.stop()" in _v, _v)
_t = ast.unparse(_throttle[0]) if _throttle else ""
chk("el throttle de 50 s LANZA el de fondo", "heartbeat_en_fondo(" in _t and "> 50" in _t, _t)
chk("⚠️ y en app.py no queda ningún heartbeat SÍNCRONO",
    not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "heartbeat"
            for n in ast.walk(_tapp)))

# ═════════════════════════════════════════════════════════════════
sec("10. «Saving…» alrededor de cada guardado del campo")


def _en_spinner(fuente, attr):
    """Por cada llamada `X.attr(...)`: ¿está dentro de un `with st.spinner(...)`?"""
    arbol = ast.parse(fuente)
    padres = {}
    for n in ast.walk(arbol):
        for h in ast.iter_child_nodes(n):
            padres[h] = n
    out = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == attr:
            p, dentro = padres.get(n), False
            while p is not None:
                if isinstance(p, ast.With) and any(
                        getattr(getattr(i.context_expr, "func", None), "attr", "") == "spinner"
                        for i in p.items):
                    dentro = True
                    break
                p = padres.get(p)
            out.append(dentro)
    return out


_spu = _fuente("core/stage_progress_ui.py")
_dlu = _fuente("core/daily_log_ui.py")
_x = _en_spinner(_spu, "acreditar")
chk("guardar una etapa", _x and all(_x), _x)
_x = _en_spinner(_dlu, "acreditar")
chk("confirmar lo propuesto en un parte", _x and all(_x), _x)
_x = _en_spinner(_dlu, "marcar_revisado")
chk("«Nothing to credit» y marcar el parte revisado", len(_x) == 2 and all(_x), _x)
_x = _en_spinner(_dlu, "crear")
chk("guardar el parte diario", _x and all(_x), _x)
_x = _en_spinner(_spu, "detalle")
chk("la sonda SÍ ve una llamada FUERA (leer el detalle no lleva spinner, trampa nº12)",
    _x and not any(_x), _x)

# ═════════════════════════════════════════════════════════════════
sec("11. ⚠️ La pantalla EJECUTADA: marcar, guardar (con el spinner) y ver el resultado")
from streamlit.testing.v1 import AppTest                          # noqa: E402

_GUION = r'''
import sys
sys.path.insert(0, r"%s")
sys.path.insert(0, r"%s")
import streamlit as st
import fixture_guardado as FG
from core import projects as P, stage_progress as SP, stage_progress_ui as SPU


class _R:
    class _T:
        def strftime(self, f):
            return "2026-09-29 10:00" if "%%H" in f else "2026-09-29"

    def now(self, g=None):
        return self._T()


st.session_state.setdefault("auth", {"usuario": "Bobo", "rol": "field", "grupo": "cliente1"})
PRJ = {"ID": "PRJ-T", "Group": "cliente1", "Type": "Installation", "Name": "t",
       "StagePlanJSON": P.plan_nuevo("Installation", ()), "Progress": "0",
       "Status": "Planned", "ManualStatus": ""}
if getattr(FG, "M_APP", None) is None:
    SP.clock = _R()
    SP.is_configured = lambda: True
    FG.M_APP = FG.montar(SP, P, PRJ)
    SP._records = lambda: FG.M_APP.sp.registros()
SPU.render("PRJ-T", "cliente1", PRJ, key_prefix="t")
''' % (RAIZ, AQUI)
_o = {k: getattr(SP, k) for k in ("clock", "is_configured", "_records")}
FG.M_APP = None
try:
    at = AppTest.from_string(_GUION, default_timeout=120)
    at.run()
    chk("la pantalla pinta sin errores", not at.exception, [e.value for e in at.exception][:1])
    _k = next((c.key for c in at.checkbox if A6[0] in str(c.proto.label)), None)
    chk("...con la casilla de «%s»" % A6[0], _k is not None)
    if _k:
        next(c for c in at.checkbox if c.key == _k).check()
        at.run()
        _b = next((b for b in at.button if ("Save stage %d" % O6) in str(b.proto.label)), None)
        chk("...y el botón de guardar su etapa", _b is not None)
        if _b is not None:
            _b.click()
            at.run()
            _m = FG.M_APP
            chk("⚠️ guardar desde la pantalla: sin excepción", not at.exception,
                [e.value for e in at.exception][:1])
            chk("...y en el libro: 1 lectura + 1 append + 1 escritura",
                _m.cuenta() == {"leer": 1, "append": 1, "escribir": 1}, _m.cuenta())
            # ⚠️ No la casilla: esa sale marcada igual, porque la marcó el clic. El contador
            # de arriba sí sale de lo que hay ESCRITO en el libro.
            _cab = [x.value for x in at.markdown if "What has been done" in x.value]
            chk("...y al repintar, el contador sale de lo escrito: «1 of …»",
                bool(_cab) and "— 1 of " in _cab[0], _cab)
finally:
    if getattr(FG, "M_APP", None) is not None:
        FG.M_APP.restaurar()
    FG.M_APP = None
    for k, v in _o.items():
        setattr(SP, k, v)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
