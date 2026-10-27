# -*- coding: utf-8 -*-
"""v611 · LO VISTO VERIFICANDO v610 (decisión del usuario, 27/10/2026: «Dale no dejes nada
pendiente»).

⚠️ Lo que lo destapó: con `AgentMemory` sembrada desde FUERA (un script), producción decía «Nothing
learned yet» con 8 filas en la hoja. El índice de pestañas (`timeclock._libro`) vive en
`@st.cache_resource` y NO caduca; el lote solo pide lo que hay en él, así que una hoja que creó
OTRO proceso no se leía nunca (hasta reiniciar la app).

Lo que protege, SIN red y sin la hoja real (todo sustituido, en memoria):
  (a) un lector sin cabeceras que pide una hoja del lote que no vino → se rehace el índice de ESE
      libro y, si la hoja ya existe, se vuelve a pedir el lote y se lee;
  (b) ...como mucho una vez cada `_REFRESCO_S` por libro (una hoja que de verdad no existe no
      cuesta más que eso), y nada para hojas fuera del lote o leídas con cabeceras;
  (c) `ids_referenciados` (una ruta de ESCRITURA) también con el índice al día;
  (d) la memoria: olvidar anota CUÁNDO; lo olvidado se RECUPERA (los mismos permisos que olvidar)
      y una lección que se volvió a aprender no se duplica;
  (e) el panel: sin «Select all» al olvidar, «Show forgotten lessons» → «Restore these», y el
      formulario de la regla nace vacío tras guardarla.
"""
import ast
import os
import sys
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin1", "nombre": "Admin Test", "rol": "administrator",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import agente_memoria as MEM                            # noqa: E402
from core import hojas as H                                       # noqa: E402
from core import timeclock as TC                                  # noqa: E402
from core.num import col_letter as _cl                            # noqa: E402


def _func(fich, nombre):
    tr = ast.parse(open(os.path.join(RAIZ, fich), encoding="utf-8").read())
    return next((n for n in ast.walk(tr) if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Una hoja que creó OTRO proceso se lee (índice sustituido)")


class _Pest:
    def __init__(self, titulo):
        self.title = titulo


class _Libros:
    """El índice `timeclock._libro`: lo que el proceso CREE que hay; `clear(sid)` lo rehace con
    lo que hay DE VERDAD en ese libro (la API)."""
    def __init__(self, real, visto):
        self.real, self.visto, self.limpiados = real, visto, []

    def __call__(self, sid=""):
        return {t.lower(): _Pest(t) for t in self.visto[sid]}, {}

    def clear(self, *a):
        if self.rompe:
            raise RuntimeError("API caída")
        self.limpiados.append(a)
        for sid in (a or tuple(self.real)):
            self.visto[sid] = list(self.real[sid])

    rompe = False


class _Lote:
    """El lote `hojas._lote`: cacheado POR LIBRO hasta que se tira; pide solo lo del índice."""
    def __init__(self, idx, datos):
        self.idx, self.datos, self.cache, self.limpiados, self.pedidos = idx, datos, {}, [], 0

    def __call__(self, sid=""):
        if sid not in self.cache:
            self.pedidos += 1
            _vis = {t.lower() for t in self.idx.visto[sid]}
            self.cache[sid] = {t: v for t, v in self.datos.items() if t.lower() in _vis}
        return self.cache[sid]

    def clear(self, *a):
        self.limpiados.append(a)
        for sid in (a or list(self.cache)):
            self.cache.pop(sid, None)


_MEMD = [["ID", "Phrase", "Activity", "Active"], ["MEM-0001", "isntalled the tank", "Install CW tank", ""]]
_real = {"LIBRO-A": ["Sheet1", "AgentMemory"], "LIBRO-B": ["Sheet1", "AgentMemory"]}
_visto = {"LIBRO-A": ["Sheet1"], "LIBRO-B": ["Sheet1"]}      # el índice, de ANTES de la siembra
_idx = _Libros(_real, _visto)
_lt = _Lote(_idx, {"Sheet1": [["Name"]], "AgentMemory": _MEMD})
_reloj = [1000.0]
_orig = (TC._libro, H._lote, TC.titulo_real, TC.sheet_id_para, H.time, TC.get_sheet)
_libro_de = {"v": "LIBRO-A"}
TC._libro = _idx
H._lote = _lt
TC.titulo_real = lambda title, sheet_id="": title
TC.sheet_id_para = lambda title="", grupo=None: _libro_de["v"]
H.time = types.SimpleNamespace(monotonic=lambda: _reloj[0])
try:
    H._refrescado.clear()
    _r = H.registros("AgentMemory")
    chk("⚠️ la hoja creada fuera SE LEE (antes: None → la memoria vacía para siempre)",
        _r is not None and [x.get("ID") for x in _r] == ["MEM-0001"], _r)
    chk("...rehecho el índice SOLO de ese libro (no el de los demás clientes)",
        _idx.limpiados == [("LIBRO-A",)], _idx.limpiados)
    chk("...y tirado el lote SOLO de ese libro, para volver a pedirlo",
        _lt.limpiados == [("LIBRO-A",)] and _lt.pedidos == 2, (_lt.limpiados, _lt.pedidos))
    _r2 = H.registros("AgentMemory")
    chk("la siguiente lectura sale del lote, sin rehacer nada", _r2 == _r and len(_idx.limpiados) == 1
        and _lt.pedidos == 2, (_idx.limpiados, _lt.pedidos))

    # (b) el tope: una hoja que de verdad NO existe en el libro
    _n0, _l0 = len(_idx.limpiados), len(_lt.limpiados)
    _reloj[0] += 10
    chk("una hoja del lote que no existe: None (y antes de 10 min, sin rehacer el índice)",
        H.registros("Claims") is None and len(_idx.limpiados) == _n0, _idx.limpiados)
    _reloj[0] += H._REFRESCO_S + 1
    chk("...pasados los 10 min, se rehace UNA vez — y sin tirar el lote si sigue sin existir",
        H.registros("Claims") is None and len(_idx.limpiados) == _n0 + 1 and len(_lt.limpiados) == _l0,
        (_idx.limpiados, _lt.limpiados))
    chk("...y la vez siguiente, otra vez nada (el tope vale de verdad)",
        H.registros("Claims") is None and len(_idx.limpiados) == _n0 + 1)
    chk("el tope es de 10 minutos", H._REFRESCO_S == 600, H._REFRESCO_S)

    # cada libro, su tope: el de B no espera al de A
    _libro_de["v"] = "LIBRO-B"
    _rb = H.registros("AgentMemory")
    chk("cada libro con su propio tope (el de otro cliente no espera al de este)",
        _rb is not None and _idx.limpiados[-1] == ("LIBRO-B",), _idx.limpiados[-2:])
    _libro_de["v"] = "LIBRO-A"

    # fuera del lote y con cabeceras: nada de esto
    _real["LIBRO-A"].append("PreStarts")
    _reloj[0] += H._REFRESCO_S + 1
    _n1 = len(_idx.limpiados)
    chk("una hoja que NO va en el lote (`PreStarts`): ni se rehace el índice",
        H.registros("PreStarts") is None and len(_idx.limpiados) == _n1, _idx.limpiados)

    class _WS:
        def get_all_records(self, **k):
            return [{"ID": "X-1"}]
    TC.get_sheet = lambda title, headers, grupo=None: _WS()
    _rc = H.registros("Claims", ("ID",))
    chk("con cabeceras, al camino de siempre (`get_sheet`), sin este refresco",
        [x.get("ID") for x in _rc] == ["X-1"] and len(_idx.limpiados) == _n1, (_rc, _idx.limpiados))

    # ⚠️ un lote SIN `.clear` (lo sustituye así verif_v590): la lectura no puede reventar. Lo cazó
    # la suite de v611 —el respaldo `_lote.clear()` iba sin proteger, `invalidar` sí lo protegía—.
    H._lote = lambda sid="": {}
    _reloj[0] += H._REFRESCO_S + 1
    try:
        _rl = H.registros("AgentMemory")
        chk("⚠️ un lote que no se puede tirar: None y sin excepción (como `invalidar`)", _rl is None, _rl)
    except Exception as e:
        fallo("⚠️ un lote que no se puede tirar: None y sin excepción (como `invalidar`)", e)
    H._lote = _lt

    # si rehacer el índice falla, no revienta
    _idx.rompe = True
    _reloj[0] += H._REFRESCO_S + 1
    try:
        _rr = H.registros("Claims")
        chk("si rehacer el índice falla: None y sin excepción", _rr is None)
    except Exception as e:
        fallo("si rehacer el índice falla: None y sin excepción", e)
    _idx.rompe = False

    # (c) ids_referenciados, una ruta de ESCRITURA
    class _Libro:
        def values_batch_get(self, rangos):
            _d = {"Sheet1": [["Name"], ["x"]], "AgentMemory": [["LogID"], ["LOG-0003"]],
                  "DailyLogs": [["ID"], ["LOG-0001"]]}
            return {"valueRanges": [{"range": r, "values": _d.get(r.strip("'"), [])} for r in rangos]}
    _hl = H._libro
    H._libro = lambda sheet_id="": _Libro()
    _real["LIBRO-A"] = ["Sheet1", "AgentMemory", "DailyLogs"]
    _visto["LIBRO-A"] = ["Sheet1", "DailyLogs"]                  # AgentMemory, creada FUERA
    _reloj[0] += H._REFRESCO_S + 1
    try:
        _ids = H.ids_referenciados("LOG-", propia="DailyLogs", sheet_id="LIBRO-A")
    finally:
        H._libro = _hl
    chk("⚠️ `ids_referenciados` ve la pestaña creada fuera (LOG-0003 no se reutilizaría)",
        _ids == {"LOG-0003"}, _ids)
finally:
    TC._libro, H._lote, TC.titulo_real, TC.sheet_id_para, H.time, TC.get_sheet = _orig
    H._refrescado.clear()

_ir = _func("core/hojas.py", "ids_referenciados")
_src = ast.unparse(_ir) if _ir else ""
chk("...y rehace el índice ANTES de listar las pestañas",
    "_indice_al_dia(sheet_id)" in _src and _src.find("_indice_al_dia(") < _src.find("_titulos("))

# ═════════════════════════════════════════════════════════════════
sec("2. La memoria: olvidar anota cuándo, y lo olvidado se recupera (hoja sustituida)")


class _HojaMem:
    def __init__(self, filas):
        self.filas = [dict({h: "" for h in MEM.HEADERS}, **f) for f in filas]
        self.lotes = []

    def get_all_records(self, **k):
        return [dict(f) for f in self.filas]

    def batch_update(self, lote, value_input_option=None):
        assert value_input_option == "RAW"
        self.lotes.append(lote)


def _celdas(lote, col):
    _c = _cl(MEM.HEADERS.index(col) + 1)
    return {int(d["range"][len(_c):]): d["values"][0][0] for d in lote if d["range"].rstrip("0123456789") == _c}


_hm = _HojaMem([
    {"ID": "MEM-0001", "Phrase": "propia", "Activity": "Install sills", "Group": "cliente1", "Active": "NO",
     "Updated": "2026-10-20 09:00"},
    {"ID": "MEM-0002", "Phrase": "ajena", "Activity": "Install frames", "Group": "otro", "Active": "NO"},
    {"ID": "MEM-0003", "Phrase": "vuelta", "Activity": "Spin motor", "Group": "cliente1", "Active": "NO"},
    {"ID": "MEM-0004", "Phrase": "vuelta", "Activity": "Spin motor", "Group": "cliente1", "Active": ""},
    {"ID": "MEM-0005", "Phrase": "doble", "Activity": "Install CW tank", "Group": "cliente1", "Active": "NO"},
    {"ID": "MEM-0006", "Phrase": "Doble ", "Activity": "Install CW tank", "Group": "cliente1", "Active": "NO"},
    {"ID": "MEM-0007", "Phrase": "regla", "Activity": "Wire all boxes", "Group": "", "Kind": "rule", "Active": "NO"},
])
_om = (MEM._ws, MEM._invalidate, MEM._records)
MEM._ws = lambda: _hm
MEM._invalidate = lambda: None
MEM._records = lambda: _hm.get_all_records()
try:
    chk("lo que un admin puede recuperar: lo olvidado de SU grupo (ni otro grupo ni el propietario)",
        sorted(r["ID"] for r in MEM.olvidadas("cliente1")) == ["MEM-0001", "MEM-0003", "MEM-0005", "MEM-0006"],
        [r["ID"] for r in MEM.olvidadas("cliente1")])
    chk("...el propietario, todo lo olvidado", len(MEM.olvidadas(None)) == 6)
    chk("...y lo activo no sale", "MEM-0004" not in [r["ID"] for r in MEM.olvidadas(None)])

    okA, nA, rA = MEM.restaurar(["MEM-0001", "MEM-0002", "MEM-0007"], "cliente1", False)
    _act = _celdas(_hm.lotes[-1], "Active") if _hm.lotes else {}
    chk("⚠️ un admin recupera SOLO lo de su grupo (ni el de otro grupo ni la regla del propietario)",
        okA and nA == 1 and _act == {2: ""}, (okA, nA, _act))
    chk("...con `Active` vacío (activa, como al crearla) y la hora en `Updated`",
        2 in _celdas(_hm.lotes[-1], "Updated") and _celdas(_hm.lotes[-1], "Updated")[2] != "")
    _hm.lotes = []
    okD, nD, rD = MEM.restaurar(["MEM-0003"], "cliente1", False)
    chk("⚠️ una que se volvió a APRENDER después de olvidarla no se duplica: se cuenta aparte",
        okD and nD == 0 and rD == 1 and not _hm.lotes, (okD, nD, rD, _hm.lotes))
    okE, nE, rE = MEM.restaurar(["MEM-0005", "MEM-0006"], "cliente1", False)
    chk("...ni dos olvidadas iguales a la vez (la frase se compara normalizada): una vuelve, la otra no",
        okE and nE == 1 and rE == 1 and len(_celdas(_hm.lotes[-1], "Active")) == 1, (okE, nE, rE))
    _hm.lotes = []
    okP, nP, rP = MEM.restaurar(["MEM-0002", "MEM-0007"], "cliente1", True)
    chk("el propietario recupera cualquiera", okP and nP == 2, (okP, nP, rP))
    _hm.lotes = []
    chk("sin elegir nada: no escribe", MEM.restaurar([], "cliente1", False) == (True, 0, 0) and not _hm.lotes)
    MEM._ws = lambda: None
    chk("sin hoja: dice que no (y no revienta)", MEM.restaurar(["MEM-0001"], "cliente1", False)[0] is False)
    MEM._ws = lambda: _hm
    _hm.filas[0]["Active"] = ""
    _hm.lotes = []
    okO, nO = MEM.olvidar(["MEM-0001"], "cliente1", False)
    chk("olvidar cuenta FILAS (no celdas) y anota CUÁNDO en `Updated`",
        okO and nO == 1 and _celdas(_hm.lotes[-1], "Active") == {2: "NO"}
        and _celdas(_hm.lotes[-1], "Updated").get(2, "") != "", (nO, _hm.lotes))
finally:
    MEM._ws, MEM._invalidate, MEM._records = _om

# ═════════════════════════════════════════════════════════════════
sec("3. El panel (AppTest)")
APP = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
ss = st.session_state
st.session_state.setdefault("auth", {"usuario": ss.get("_u", "admin1"), "nombre": "X",
                                     "rol": ss.get("_rol", "administrator"), "grupo": "cliente1"})
from core import agente_memoria as MEM, daily_log as DL, daily_log_ui as DLU, flash
for _k, _v in (("_olv", []), ("_rest", []), ("_reglas", [])):
    ss.setdefault(_k, _v)
_ACT = [
    {"ID": "MEM-1", "Phrase": "propia", "Activity": "Install sills", "Kind": "learned", "Confirmed": 2,
     "Rejected": 0, "Group": "cliente1", "Updated": "2026-10-27 10:00"},
    {"ID": "MEM-3", "Phrase": "installed motor", "Activity": "Install motor (machine)", "Kind": "rule",
     "Confirmed": 0, "Rejected": 0, "Group": "", "Updated": ""}]
_OLV = [
    {"ID": "MEM-8", "Phrase": "vieja", "Activity": "Install frames", "Group": "cliente1", "Active": "NO",
     "Updated": "2026-10-26 08:00"},
    {"ID": "MEM-9", "Phrase": "de otro", "Activity": "Install frames", "Group": "otro", "Active": "NO",
     "Updated": "2026-10-25 08:00"}]
MEM.lecciones = lambda grupo=None: [] if ss.get("_sin_activas") else [
    r for r in _ACT if grupo is None or r["Group"] in (grupo, "")]
MEM.olvidadas = lambda grupo=None: [r for r in _OLV if grupo is None or r["Group"] == grupo]
MEM.olvidar = lambda ids, g, dueno: (ss["_olv"].append((list(ids), g, dueno)) or (True, len(ids)))
MEM.restaurar = lambda ids, g, dueno: (ss["_rest"].append((list(ids), g, dueno))
                                       or ss.get("_rest_res", (True, len(ids), 0)))
MEM.poner_regla = lambda f, a, g, u: (ss["_reglas"].append((f, a, g, u))
                                      or ss.get("_regla_res", (True, "Rule saved.")))
DL.partes = lambda pid, autor=None, dia=None: []
flash.mostrar()
DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
'''


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _w(lista, key):
    return next((x for x in lista if x.key == key), None)


def _todo(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption] + \
        [str(x.value) for x in list(at.success) + list(at.warning) + list(at.error) + list(at.info)]


at = AppTest.from_string(APP, default_timeout=90).run()
chk("el panel se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_fo = _w(at.multiselect, "adm_mem_olv")
chk("⚠️ «Forget these» SIN «Select all» (con él, todo se olvidaba en dos clics)",
    _fo is not None and _fo.proto.select_all == 0, _fo and _fo.proto.select_all)
_cv = _w(at.checkbox, "adm_mem_ver_olv")
chk("«Show forgotten lessons (1)»: solo lo de SU grupo", _cv is not None and "(1)" in str(_cv.label),
    _cv and _cv.label)
chk("...y cerrado: no enseña nada hasta que se pide", _w(at.multiselect, "adm_mem_rest") is None)
_cv.check()
at.run()
_mr = _w(at.multiselect, "adm_mem_rest")
chk("abierto: «Restore these» con la frase, la actividad y CUÁNDO se olvidó (DD/MM/YYYY)",
    _mr is not None and list(_mr.options) == ["«vieja» → Install frames · forgotten 26/10/2026"],
    _mr and list(_mr.options))
chk("...también sin «Select all»", _mr is not None and _mr.proto.select_all == 0)
_bt(at, "adm_mem_restaurar").click()
at.run()
chk("«Restore» sin elegir nada: lo dice y no llama",
    not at.session_state["_rest"] and any("remember again first" in x for x in _todo(at)), _todo(at)[-3:])
_w(at.multiselect, "adm_mem_rest").select("MEM-8")
at.run()
_bt(at, "adm_mem_restaurar").click()
at.run()
chk("recuperar: lo pide para SU grupo y como admin", at.session_state["_rest"] == [(["MEM-8"], "cliente1", False)],
    at.session_state["_rest"])
chk("...y lo dice: «Restored: 1.»", any("Restored: 1." in x for x in _todo(at)), _todo(at)[-3:])

at2 = AppTest.from_string(APP, default_timeout=90)
at2.session_state["_rest_res"] = (True, 0, 1)
at2.run()
_w(at2.checkbox, "adm_mem_ver_olv").check()
at2.run()
_w(at2.multiselect, "adm_mem_rest").select("MEM-8")
at2.run()
_bt(at2, "adm_mem_restaurar").click()
at2.run()
chk("una que ya volvió a aprenderse: lo dice (no un «Restored: 0.» mudo)",
    any("already back in the memory" in x for x in _todo(at2)) and not any("Restored: 0" in x for x in _todo(at2)),
    _todo(at2)[-3:])

at3 = AppTest.from_string(APP, default_timeout=90)
at3.session_state["_sin_activas"] = True
at3.run()
chk("todo olvidado: lo dice (no «Nothing learned yet») y deja recuperarlo",
    any("Nothing active" in x for x in _todo(at3)) and not any("Nothing learned yet" in x for x in _todo(at3))
    and _w(at3.checkbox, "adm_mem_ver_olv") is not None, _todo(at3)[:6])

at4 = AppTest.from_string(APP, default_timeout=90)
at4.session_state["_rol"] = "owner"
at4.session_state["_u"] = "duena"
at4.run()
_cv4 = _w(at4.checkbox, "adm_mem_ver_olv")
chk("el propietario ve TODO lo olvidado («(2)»)", _cv4 is not None and "(2)" in str(_cv4.label),
    _cv4 and _cv4.label)

# el formulario de la regla, vacío tras guardar
at5 = AppTest.from_string(APP, default_timeout=90).run()
_w(at5.text_input, "adm_mem_frase").set_value("zz frase")
_w(at5.selectbox, "adm_mem_act").set_value("Spin motor")
at5.run()
_bt(at5, "adm_mem_regla").click()
at5.run()
_ti, _sb = _w(at5.text_input, "adm_mem_frase"), _w(at5.selectbox, "adm_mem_act")
chk("guardada la regla, el formulario nace VACÍO (un 2º clic decía «That rule already exists.»)",
    at5.session_state["_reglas"] == [("zz frase", "Spin motor", "cliente1", "admin1")]
    and _ti.value == "" and _sb.value is None, (at5.session_state["_reglas"], _ti.value, _sb.value))
chk("...ASIGNADO (llega al navegador: trampa 31)", _ti.proto.set_value and _sb.proto.set_value,
    (_ti.proto.set_value, _sb.proto.set_value))
at6 = AppTest.from_string(APP, default_timeout=90)
at6.session_state["_regla_res"] = (False, "That rule already exists.")
at6.run()
_w(at6.text_input, "adm_mem_frase").set_value("zz frase")
_w(at6.selectbox, "adm_mem_act").set_value("Spin motor")
at6.run()
_bt(at6, "adm_mem_regla").click()
at6.run()
chk("...pero si NO se guardó, lo tecleado se queda (para corregirlo)",
    _w(at6.text_input, "adm_mem_frase").value == "zz frase"
    and _w(at6.selectbox, "adm_mem_act").value == "Spin motor"
    and any("That rule already exists." in x for x in _todo(at6)))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
