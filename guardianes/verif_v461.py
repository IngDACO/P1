"""Guardián de v461 — correcciones de fichaje con revisión del admin.

⚠️ Se EJECUTA lo que solo se ve ejecutando (v378: importar no ejecuta): la fila
posicional de `registrar`, el recálculo de `Horas` de `corregir_fichaje` y las dos
funciones de la UI. Lo estructural va por AST, nunca por subcadena (trampa nº2).
"""
import ast
import inspect
import os
import sys
from datetime import datetime, timedelta

# ⚠️ Ruta ABSOLUTA y sin chdir: el runner de la suite ya lanza con
# cwd=survey_app, y Streamlit busca `.streamlit/secrets.toml` relativo al CWD —
# lanzarlo desde otro sitio da «No secrets found», un rojo que no existe (v19).
RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
sys.path.insert(0, RAIZ)

fallos = []
oks = 0


def ok(msg):
    global oks
    oks += 1
    print("  OK   " + msg)


def fallo(msg):
    fallos.append(msg)
    print("  FALLO " + msg)


def fuente(mod):
    return open(os.path.join(RAIZ, "core", mod + ".py"), encoding="utf-8").read()


def arbol(mod):
    return ast.parse(fuente(mod))


def func(mod, nombre):
    for n in ast.walk(arbol(mod)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre:
            return n
    return None


# ── 1 · La hoja está en el LOTE (regla v353) ─────────────────────
print("1. La hoja entra en el lote de lectura (v353)")
from core import hojas, correcciones as C

if C.SHEET in hojas.HOJAS_LECTURA:
    ok(C.SHEET + " está en HOJAS_LECTURA")
else:
    # ⚠️ Sin esto el módulo lee VACÍO PARA SIEMPRE y sin ningún error: el lector
    # va sin cabeceras (para no crear la hoja al leer, regla v145) y `registros`
    # devuelve None. Es el fallo que costó una versión entera en v353.
    fallo(C.SHEET + " NO está en HOJAS_LECTURA: leería vacío en silencio")


# ── 2 · La fila posicional casa con HEADERS (regla v363) ─────────
print("2. registrar(): la fila posicional casa con HEADERS (v363)")


class _WSFake:
    def __init__(self):
        self.filas = []
        self.batches = []
        self.valores = [list(C.HEADERS)]

    def append_row(self, fila, **kw):
        self.filas.append(fila)
        self.valores.append([str(x) for x in fila])

    def get_all_values(self):
        return self.valores

    def batch_update(self, ops, **kw):
        self.batches.append(ops)


_ws = _WSFake()
C._ws = lambda: _ws
C._next_id = lambda: "COR-0001"
C.nomina_que_cubre = lambda *a, **k: ""
C._invalidate = lambda: None
_okreg, _msg = C.registrar("g", "u", "N", "proyecto", "PRJ-1", C.CAMPO_IN,
                           "2026-09-04 09:00:00", "2026-09-04 07:00:00", motivo="m")
if _okreg and len(_ws.filas) == 1 and len(_ws.filas[0]) == len(C.HEADERS):
    ok("fila de %d valores para %d columnas" % (len(_ws.filas[0]), len(C.HEADERS)))
else:
    fallo("registrar no escribió una fila alineada: %s / %s" % (_okreg, _msg))

_i = {h: i for i, h in enumerate(C.HEADERS)}
if _ws.filas and _ws.filas[0][_i["Status"]] == C.PENDIENTE:
    ok("nace PENDIENTE, o sea la revisa el admin")
else:
    fallo("la corrección no nace pendiente")


# ── 3 · corregir_fichaje RECALCULA las Horas ─────────────────────
print("3. corregir_fichaje(): recalcula Horas (si no, la corrección no mueve nada)")
from core import timeclock


class _TCFake:
    def __init__(self, ci, co):
        self.reg = [{"Name": "N", "User": "u", "Group": "g", "Type": "proyecto",
                     "Clock In": ci, "Clock Out": co, "Hours": "1.0",
                     "Status": "CERRADO", "Project": "P"}]
        self.batches = []

    def get_all_records(self, **kw):
        return self.reg

    def batch_update(self, ops, **kw):
        self.batches.append(ops)


_tc = _TCFake("2026-09-04 09:00:00", "2026-09-04 17:00:00")
timeclock._get_worksheet = lambda: (_tc, "")
timeclock._invalidate_records = lambda: None
_okc, _msgc = timeclock.corregir_fichaje(
    grupo="g", usuario="u", nombre="N", tipo="proyecto", campo="Clock In",
    valor_actual="2026-09-04 09:00:00", valor_nuevo="2026-09-04 07:00:00")
_rangos = [w["range"] for b in _tc.batches for w in b]
if _okc and any(r.startswith("E") for r in _rangos):
    ok("escribe la hora corregida en su columna")
else:
    fallo("no escribió la hora: %s / %s" % (_okc, _msgc))
if any(r.startswith("G") for r in _rangos):
    _h = [w["values"][0][0] for b in _tc.batches for w in b if w["range"].startswith("G")]
    if _h and abs(float(_h[0]) - 10.0) < 0.01:
        ok("recalcula Horas 8 → 10 (07:00–17:00)")
    else:
        fallo("Horas mal recalculadas: %s" % _h)
else:
    # ⚠️ Sin esto `_row_segmentos` respeta las Horas GUARDADAS para una fila
    # cerrada del mismo día (v164), así que la corrección NO movería la nómina
    # ni el costo de la obra — y nadie lo notaría.
    fallo("NO recalcula Horas: la corrección no movería nómina ni costo")

_tc2 = _TCFake("2026-09-04 09:00:00", "")
timeclock._get_worksheet = lambda: (_tc2, "")
timeclock.corregir_fichaje(grupo="g", usuario="u", nombre="N", tipo="proyecto",
                           campo="Clock In", valor_actual="2026-09-04 09:00:00",
                           valor_nuevo="2026-09-04 07:00:00")
_r2 = [w["range"] for b in _tc2.batches for w in b]
if not any(r.startswith("G") for r in _r2):
    ok("una sesión ABIERTA no recibe un 0 en Horas (v346)")
else:
    fallo("escribe Horas en una sesión abierta")

_tc3 = _TCFake("2026-09-04 09:00:00", "2026-09-04 17:00:00")
timeclock._get_worksheet = lambda: (_tc3, "")
_ok3, _m3 = timeclock.corregir_fichaje(
    grupo="g", usuario="u", nombre="N", tipo="proyecto", campo="Clock Out",
    valor_actual="2026-09-04 17:00:00", valor_nuevo="2026-09-04 08:00:00")
if not _ok3 and not _tc3.batches:
    ok("rechaza una salida ANTERIOR a la entrada, sin escribir")
else:
    fallo("aceptó una salida anterior a la entrada")


# ── 4 · El ORDEN de revertir y ajustar (regla v343) ──────────────
print("4. revertir/ajustar: primero el fichaje, después la marca (v343)")


def _orden(nombre):
    fn = func("correcciones", nombre)
    if fn is None:
        return None, None
    pos_fichaje = pos_marca = None
    for i, n in enumerate(ast.walk(fn)):
        pass
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr == "corregir_fichaje":
                pos_fichaje = n.lineno if pos_fichaje is None else pos_fichaje
            if isinstance(f, ast.Name) and f.id == "_set":
                pos_marca = n.lineno if pos_marca is None else pos_marca
    return pos_fichaje, pos_marca


for _n in ("revertir", "ajustar"):
    _pf, _pm = _orden(_n)
    if _pf and _pm and _pf < _pm:
        ok(_n + ": corrige el fichaje (L%d) antes de marcar (L%d)" % (_pf, _pm))
    else:
        # Al revés, un fallo a mitad deja la corrección marcada como resuelta con
        # el fichaje aún cambiado: la app diciendo que deshizo algo que sigue hecho.
        fallo(_n + ": el orden fichaje/marca no está garantizado (%s/%s)" % (_pf, _pm))

_src_aj = ast.get_source_segment(fuente("correcciones"), func("correcciones", "ajustar"))
# ⚠️ ESTRUCTURAL, no por subcadena: «ValorNuevo» aparece también al LEER
# (`r.get("ValorNuevo")`), así que buscar el literal deja pasar que se borre
# la escritura — se escapó en la primera tanda de roturas (v452/v453).
_claves_set = set()
for n in ast.walk(func("correcciones", "ajustar")):
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_set"):
        for a in n.args:
            if isinstance(a, ast.Dict):
                _claves_set |= {k.value for k in a.keys
                                if isinstance(k, ast.Constant)}
if "NewValue" in _claves_set:
    ok("ajustar ESCRIBE ValorNuevo (el rastro no miente)")
else:
    fallo("ajustar no reescribe ValorNuevo: el histórico diría otra hora que la hoja")
if "base.replace(" in _src_aj and "hour=" in _src_aj:
    ok("ajustar cambia solo la HORA, conserva el DÍA")
else:
    fallo("ajustar podría mover el fichaje de día (y de nómina)")


# ── 5 · La regla del mismo día, y su excepción ───────────────────
print("5. Mismo día en _corregir_horas; la sesión ABIERTA sigue siendo la excepción")
_src_ch = ast.get_source_segment(fuente("timeclock_ui"), func("timeclock_ui", "_corregir_horas"))
if _src_ch and _src_ch.count("clock.today(grupo)") >= 2:
    ok("_corregir_horas compone las horas sobre HOY")
else:
    fallo("_corregir_horas no ata la corrección al día de hoy")
_src_av = ast.get_source_segment(fuente("timeclock_ui"), func("timeclock_ui", "_aviso_olvido"))
if _src_av and "out_ts=fin" in _src_av:
    ok("_aviso_olvido conserva el cierre con hora explícita (v164)")
else:
    fallo("_aviso_olvido perdió el cierre con hora: volverían las horas fantasma")
if _src_av and "correcciones.registrar" in _src_av:
    ok("el cierre de una sesión olvidada queda anotado para el admin")
else:
    fallo("cerrar una sesión olvidada no deja rastro para el admin")


# ── 6 · Imports a nivel de MÓDULO (reglas v342/v423/v425) ────────
print("6. logger / correcciones / clock viven en el ámbito de MÓDULO")
for _mod, _necesita in (("timeclock_ui", ("logging", "correcciones", "clock", "flash")),
                        ("correcciones_ui", ("logging", "theme", "clock", "timeclock"))):
    _tree = arbol(_mod)
    _top = set()
    for n in _tree.body:            # ⚠️ SOLO el cuerpo: descender a los `def`
        if isinstance(n, ast.Import):   # es el autoengaño de v342/v366
            for a in n.names:
                _top.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                _top.add(a.asname or a.name)
    _falta = [x for x in _necesita if x not in _top]
    if not _falta:
        ok(_mod + ": los imports que usa están a nivel de módulo")
    else:
        fallo(_mod + " usaría sin importar: " + ", ".join(_falta))

if "logger = logging.getLogger" in fuente("timeclock_ui"):
    ok("timeclock_ui define logger de módulo")
else:
    fallo("timeclock_ui usa logger sin definirlo (NameError latente, v370)")


# ── 7 · La sub-pestaña existe Y tiene su comparación (v449) ──────
print("7. La bandeja está enrutada: ID definido y comparado (v449)")
_hu = fuente("home_ui")
# ⚠️ _SUBSECCIONES[k] es (clave_estado, [(id, display), ...]): la lista es el [1].
# Leerlo como si fuera la lista daba FALLO con el ID perfectamente definido.
_ids = [t[0] for t in __import__("core.home_ui", fromlist=["x"])._SUBSECCIONES["planificacion"][1]]
_ID = "⏱ Correcciones"
if _ID in _ids:
    ok("el ID está en _SUBSECCIONES['planificacion']")
else:
    fallo("el ID no está definido en la navegación")
_comparados = set()
for n in ast.walk(arbol("home_ui")):
    if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == "sub":
        for c in n.comparators:
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                _comparados.add(c.value)
if _ID in _comparados:
    ok("el despachador lo compara EXACTO (un display navegaría a ninguna parte)")
else:
    fallo("el ID no aparece en ningún `sub == ...`: rama MUERTA")


# ── 8 · El acento del KPI no puede ser None ──────────────────────
print("8. theme.kpi_row: el 4º elemento es el ACENTO, nunca None")
_src_b = ast.get_source_segment(fuente("correcciones_ui"), func("correcciones_ui", "render_bandeja"))
if "theme.AMBAR if pend else theme.AZUL" in _src_b:
    ok("acento resuelto siempre a un color real")
else:
    fallo("el acento podría llegar como None → '--cpx-accent:None' en el CSS")


# ── 9 · El ID se emite sin reciclar ni contar filas (v427/v428) ──
print("9. _next_id: ni cuenta filas ni recicla (v427/v428)")
_src_id = ast.get_source_segment(fuente("correcciones"), func("correcciones", "_next_id"))
if "siguiente_id_libre" in _src_id:
    ok("usa siguiente_id_libre")
else:
    fallo("no salta los IDs ya referenciados")
if "len(" not in _src_id.replace("len(str(", ""):
    ok("no deriva el ID del NÚMERO de filas")
else:
    fallo("deriva el ID de len(hoja): colisionaría al borrar una del medio (v428)")


# ── 10 · Ningún t() congelado al importar (v445) ─────────────────
print("10. Ninguna llamada a t() en el ámbito de módulo (v445)")
_congelados = []
for _mod in ("correcciones", "correcciones_ui"):
    for n in arbol(_mod).body:
        for sub in ast.walk(n):
            if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                    and sub.func.id in ("t", "d")):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    _congelados.append(_mod + ":" + str(sub.lineno))
if not _congelados:
    ok("0 traducciones congeladas al importar")
else:
    fallo("t() a nivel de módulo: " + ", ".join(_congelados))


# ── 11 · Toda etiqueta de display pasa por t() (redes v440/v452) ─
print("11. Las etiquetas de pantalla pasan por t()")
_DISPLAY = {"markdown", "caption", "warning", "error", "success", "info", "button",
            "text_input", "radio", "time_input", "expander", "toast", "metric"}
_sueltas = []
for n in ast.walk(arbol("correcciones_ui")):
    if not isinstance(n, ast.Call):
        continue
    f = n.func
    # ⚠️ Por RECEPTOR, no por atributo: `logger.warning` comparte NOMBRE con
    # `st.warning` y se cuela como si fuera una etiqueta de pantalla — el
    # extractor de v439 los coló 92 veces por esto mismo.
    if not (isinstance(f, ast.Attribute) and f.attr in _DISPLAY
            and getattr(f.value, "id", "") != "logger"):
        continue
    if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
        _txt = n.args[0].value.strip()
        if len(_txt) > 2 and not _txt.startswith(":material/"):
            _sueltas.append("L%d %r" % (n.lineno, _txt[:40]))
if not _sueltas:
    ok("0 etiquetas sueltas sin t()")
else:
    fallo("etiquetas sin t(): " + " · ".join(_sueltas))


# ── 12 · Las dos pantallas EJECUTAN (importar no ejecuta, v378) ──
print("12. Las funciones nuevas se EJECUTAN sin excepción (v378)")
import streamlit as st
from core import correcciones_ui, timeclock_ui

st.session_state.clear()
st.session_state["auth"] = {"usuario": "u", "nombre": "N", "rol": "administrator",
                            "grupo": "cliente1"}
try:
    correcciones_ui.render_bandeja("cliente1")
    ok("render_bandeja corre")
except Exception as e:
    fallo("render_bandeja lanza: %r" % (e,))
# ⚠️ Se CAPTURA el logger: los helpers nuevos llevan `except Exception` (bien:
# un fallo de lectura no puede tumbar el fichaje) y eso esconde un NameError
# recién introducido — la pantalla se vería bien y la lista saldría vacía para
# siempre. Es el fallo real de v437, cazado leyendo el log (v448).
import logging


class _Capta(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs = []

    def emit(self, rec):
        self.msgs.append(rec.getMessage())


_cap = _Capta()
for _lg in (timeclock_ui.logger, correcciones_ui.logger):
    _lg.addHandler(_cap)
try:
    timeclock_ui.render_timeclock_tab()
    ok("render_timeclock_tab corre con el bloque nuevo")
except Exception as e:
    fallo("render_timeclock_tab lanza: %r" % (e,))
if not _cap.msgs:
    ok("ningún except se tragó un error durante el render")
else:
    fallo("el log delata un fallo escondido: " + " · ".join(_cap.msgs[:3]))


# ── 13 · Los ESTADOS se muestran traducidos (v442) ───────────────
print("13. Los estados del historial se MUESTRAN traducidos, y el dato no cambia")
from core import i18n

# ⚠️ Encontrado MIRANDO LA PANTALLA en producción, no por un test: la columna
# Status decía «revertida» en una tabla por lo demás en inglés. `pendiente` y
# `aprobada` ya estaban (los usa `ausencias`); el estado NUEVO no.
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
# El canonico NO tiene que ser CLAVE de `VALORES`: ese mapa es ahora el legado del
# lado del display. Lo que no puede pasar es que `etiqueta()` le cambie el texto a un
# valor que YA es canonico — si lo hiciera, es que la constante sigue sin migrar.
_sin = [e for e in C.ESTADOS if i18n.etiqueta(e) != e]
if not _sin:
    ok("los %d estados son canonicos y `etiqueta()` no los muta" % len(C.ESTADOS))
else:
    fallo("estados que saldrian en espanol: " + ", ".join(_sin))
if C.REVERTIDA == "reverted" and C.APROBADA == "approved":
    ok("el dato que se guarda es el canonico")
else:
    fallo("la constante no es canonica: %r / %r" % (C.REVERTIDA, C.APROBADA))
# ⚠️ …y la fila SIN migrar sigue casando: es lo que permite desplegar ANTES de migrar
# la hoja. Sin esto, toda correccion del historico quedaria sin resolver.
from core import valores as _VAL5                              # noqa: E402
if (_VAL5.canon("revertida") == C.REVERTIDA
        and _VAL5.canonizar([{"Status": "aprobada"}], "TimeCorrections")[0]["Status"]
        == C.APROBADA):
    ok("una correccion SIN migrar sigue casando (canon la traduce al leer)")
else:
    fallo("la fila vieja deja de resolver")
_hist = ast.get_source_segment(fuente("correcciones_ui"),
                               func("correcciones_ui", "render_bandeja"))
if "i18n.etiqueta(str(r.get(\"Status\"" in _hist:
    ok("el historial pinta el estado por etiqueta()")
else:
    fallo("el historial muestra el estado CRUDO")


print("")
if fallos:
    print("FALLOS: %d de %d comprobaciones" % (len(fallos), len(fallos) + oks))
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK - %d comprobaciones" % oks)
