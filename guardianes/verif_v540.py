# -*- coding: utf-8 -*-
"""v540 · OLVIDAR TAMBIÉN EN EL NAVEGADOR (y las tablas de lo medido son de su obra).

⚠️ El fallo, visto EN PRODUCCIÓN con la cuenta del admin (07/10/2026): en Belting, de 88
walker a otra obra (sin plano) sin salir de la herramienta, la pantalla seguía con HQ 14045,
HGP 85 y HGPR 1785, y «Calculate» calculó con ellos bajo el nombre de la otra obra. La
regla de v535 («de X a Y sin salir, se olvida») BORRABA las entradas en el servidor, pero
Streamlit identifica esos widgets solo por su clave y el navegador solo se entera de un
valor cuando el código lo ASIGNA (la trampa de v529): se quedaba con el viejo y lo devolvía
en el clic siguiente. AppTest lee el SERVIDOR, así que los guardianes de v535 lo daban por
bueno. Ahora `olvidar` ASIGNA el valor por defecto de cada entrada (`DEFECTOS`).

Y las tablas de lo medido (HKPR de cada buffer, BSR de cada ascensor, L de cada ascensor, la
matriz del caso 2) no se olvidaban NUNCA. Ahora también son de su obra, y la tabla editable
lleva una clave con generación: Streamlit conserva sus ediciones mientras la forma de los
datos no cambie (`data_editor` con filas fijas), así que ponerla a ceros no bastaría.

Lo que protege, EJECUTANDO las cuatro pantallas reales con el selector del admin y mirando
el `set_value` del proto —el contrato con el navegador—, no solo el valor del servidor; con
la sonda validada contra el `olvidar` de v539 (trampa nº12).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import estado_vivo as EV                                 # noqa: E402

GUION = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
import pandas as pd
from core import estado_vivo, plan_ui, plan_store, plan_data, projects as P
from core import rail_cut_ui as R, buffer_cut_ui as B, belting_ui as BE, plumb_ui as PL
st.session_state["auth"] = {"rol": "administrator", "usuario": "adm", "nombre": "Adm",
                            "grupo": "g"}
PROYS = [{"ID": i, "Name": "Obra " + i[-1], "Group": "g"} for i in ("PRJ-A", "PRJ-B", "PRJ-C")]
_PA = {"lfkk": 1111.0, "lfgk": 911.0, "hkp": 70.0, "hq": 14045.0, "hgp": 85.0,
       "rail_altura": 62.0,
       "params": {"BKS": 1162.0, "TKSW": 1315.0, "SF1": 51.0, "SF2": 52.0, "BS": 1597.0,
                  "SG": 300.0, "TG": 100.0}}
_PB = {"lfkk": 2222.0, "lfgk": 922.0, "hkp": 80.0, "hq": 13250.0, "hgp": 90.0,
       "rail_altura": 70.0,
       "params": {"BKS": 1200.0, "TKSW": 1400.0, "SF1": 60.0, "SF2": 61.0, "BS": 1700.0,
                  "SG": 310.0, "TG": 110.0}}
PLANOS = {"PRJ-A": _PA, "PRJ-B": _PB}              # PRJ-C: obra SIN plano (el caso visto)
P.is_configured = lambda: True
P.list_projects = lambda grupo=None, **k: [dict(p) for p in PROYS]
plan_data.del_proyecto = lambda pid: json.loads(json.dumps(PLANOS.get(pid, {})))
plan_data.resumen = lambda d: "plano"
plan_store.selector = lambda *a, **k: None
for M in (R, B, BE, PL):
    M.render_guardar = lambda **k: None
    M.tool_pdf = lambda *a, **k: b""


def _olvidar_v539(herramienta):
    """La de v539, copiada: BORRA. La sonda tiene que ver el fallo con ella."""
    n = 0
    for k in list(st.session_state.keys()):
        if estado_vivo.de_herramienta(herramienta, k):
            del st.session_state[k]
            n += 1
    return n


# ⚠️ Los guiones comparten proceso: lo que se sustituye se repone SIEMPRE (v534).
if not hasattr(estado_vivo, "_olvidar_real"):
    estado_vivo._olvidar_real = estado_vivo.olvidar
estado_vivo.olvidar = (_olvidar_v539 if st.session_state.get("v539")
                       else estado_vivo._olvidar_real)
estado_vivo.pasada()
_tabla = st.session_state.pop("sembrar_tabla", None)
if _tabla:                       # lo que deja una tabla editada (su contenido vive aquí)
    k, col, vals = _tabla
    st.session_state[k] = pd.DataFrame({col[0]: [col[1] + " %%d" %% (i + 1)
                                                 for i in range(len(vals))],
                                        col[2]: vals})
pg = st.session_state.get("pg", "rieles")
{"rieles": R.render_rail_cut_tab, "buffers": B.render_buffer_cut_tab,
 "belting": BE.render_belting_tab, "plomada": PL.render_plumb_tab}.get(pg, lambda: None)()
''' % RAIZ

NADA = "— no project (load the drawing by hand) —"
_KEY = {"rieles": "rc", "buffers": "bc", "belting": "belt", "plomada": "plb"}


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def elige(at, pg, pid):
    at.selectbox(key="pl_prj_" + _KEY[pg]).set_value(
        ("Obra %s (%s)" % (pid[-1], pid)) if pid else NADA)
    return corre(at)


def widget(at, k):
    """El widget de entrada con esa clave (número o radio), o None si no se pintó."""
    for lst in (at.number_input, at.radio):
        for w in lst:
            if w.key == k:
                return w
    return None


def nuevo(pg, **flags):
    at = AppTest.from_string(GUION, default_timeout=120)
    at.session_state["pg"] = pg
    for k, v in flags.items():
        at.session_state[k] = v
    return corre(at)


# ═════════════════════════════════════════════════════════════════
sec("1. Cada valor por defecto es EL del widget (las cuatro pantallas, recién abiertas)")
_cubiertas = {k for h in ("plb", "rc", "bc", "belt") for k in EV.HERRAMIENTAS[h]["claves"]}
# v541 · `DEFECTOS` lleva también el nº de paradas del Survey (`ns`): lo comprueba verif_v541
# contra `survey_ui.init_state`; aquí se miran las cuatro herramientas de cálculo.
_DEF4 = {k: v for k, v in EV.DEFECTOS.items() if k != "ns"}
chk("toda entrada de la lista cerrada de las cuatro herramientas tiene su valor por defecto "
    "(y el HGPR por prefijo)", _cubiertas == set(_DEF4)
    and EV._defecto("belt_hgpr_7") == 0.0, _cubiertas ^ set(_DEF4))
_vistos, _distintos = set(), {}
for pg, extra in (("rieles", {}), ("rieles", {"rc_caso": "Case 2 — last installed (the top one)"}),
                  ("buffers", {}), ("belting", {}), ("plomada", {})):
    at = nuevo(pg)
    for k, v in extra.items():
        at.radio(key=k).set_value(v)
        corre(at)
    for k, d in _DEF4.items():
        w = widget(at, k)
        if w is None or k in extra:
            continue
        _vistos.add(k)
        if not (type(w.value) is type(d) and w.value == d):
            _distintos[k] = (w.value, d)
    for w in at.number_input:
        if w.key and w.key.startswith("belt_hgpr_"):
            _vistos.add("belt_hgpr_")
            if not (type(w.value) is float and w.value == 0.0):
                _distintos[w.key] = w.value
chk("se pintaron TODAS las entradas con valor por defecto (no es un paso en vacío)",
    _vistos >= set(_DEF4) | {"belt_hgpr_"}, set(_DEF4) - _vistos)
chk("⚠️ cada valor por defecto coincide en VALOR y TIPO con el de su widget (un 1.0 donde va "
    "un 1 cambiaría el tipo del widget; un valor bajo su mínimo lo tumbaría)", not _distintos,
    _distintos)

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ Cambiar de obra SIN salir: el navegador RECIBE el olvido (`set_value`)")
TECLEO = {
    "rieles": {"rc_n": 2, "rc_n2500": 3, "rc_n5000": 1},
    "buffers": {"bc_n": 2},
    "belting": {"belt_ns": 2, "belt_hgpr_0": 1785.0, "belt_hgpr_1": 1547.0},
    "plomada": {"plb_lt": 770.0, "plb_n": 2},
}
DEL_PLANO = {"rieles": ("rc_lfkk", "rc_lfgk"), "buffers": ("bc_hkp",),
             "belting": ("belt_hq", "belt_hgp"),
             "plomada": ("plb_bks", "plb_tksw", "plb_sf1", "plb_sf2", "plb_bs", "plb_sg",
                         "plb_tg", "plb_rail")}


def teclea(at, pg):
    for k, v in TECLEO[pg].items():
        w = widget(at, k)
        if w is None:                         # el HGPR del 2º ascensor sale tras belt_ns=2
            corre(at)
            w = widget(at, k)
        w.set_value(v)
        corre(at)


def cambio(pg, destino="PRJ-C", **flags):
    """Obra A con su plano, todo tecleado; luego `destino` sin salir de la herramienta."""
    at = nuevo(pg, **flags)
    elige(at, pg, "PRJ-A")
    teclea(at, pg)
    if pg == "plomada":
        at.radio(key="plb_omega").set_value("L")
        corre(at)
    elige(at, pg, destino)
    return at


for pg in ("rieles", "buffers", "belting", "plomada"):
    at = cambio(pg)
    claves = list(TECLEO[pg]) + list(DEL_PLANO[pg]) + (["plb_omega"] if pg == "plomada" else [])
    mal = {}
    for k in claves:
        w = widget(at, k)
        d = EV._defecto(k)
        if w is None:
            # El HGPR del 2º ascensor deja de pintarse al volver a 1 ascensor: el navegador
            # lo suelta; lo que importa es que en el servidor no quede el de A.
            if at.session_state[k] != d if k in at.session_state else False:
                mal[k] = ("sin pintar", at.session_state[k], d)
        elif not (w.value == d and w.proto.set_value is True):
            mal[k] = (w.value, d, "set_value=%s" % w.proto.set_value)
    chk("⚠️ %s: de A (con plano) a C (sin plano) — lo tecleado y lo del plano de A vuelven a su "
        "valor por defecto Y el navegador lo recibe (%d entradas)" % (pg, len(claves)),
        not mal, mal)

at = cambio("rieles", destino="PRJ-B")
v = {k: (widget(at, k).value, widget(at, k).proto.set_value) for k in ("rc_lfkk", "rc_n2500")}
chk("de A a B (con plano): manda el plano de B y lo tecleado para A vuelve a 0, las dos cosas "
    "en el navegador", v == {"rc_lfkk": (2222.0, True), "rc_n2500": (0, True)}, v)
at = nuevo("rieles")
elige(at, "rieles", "PRJ-A")
at.radio(key="rc_caso").set_value("Case 2 — last installed (the top one)")
corre(at)
at.radio(key="rc_sub").set_value("Below the FFL (add)")
corre(at)
elige(at, "rieles", "PRJ-C")
_w = widget(at, "rc_caso")
chk("también las opciones (el caso de corte de A no se queda para C), en el navegador",
    _w.value == EV.DEFECTOS["rc_caso"] and _w.proto.set_value is True, (_w.value, _w.proto.set_value))

at = cambio("belting", v539=True)
_sv = {k: widget(at, k).proto.set_value for k in ("belt_hgpr_0", "belt_hq")}
chk("la sonda VE el fallo de producción: con el `olvidar` de v539 el servidor borra pero el "
    "navegador NO recibe nada (set_value False) — trampa nº12",
    widget(at, "belt_hgpr_0").value == 0.0 and _sv == {"belt_hgpr_0": False, "belt_hq": False},
    _sv)

at = nuevo("belting")
elige(at, "belting", "PRJ-A")
teclea(at, "belting")
corre(at)
corre(at)
_v = widget(at, "belt_hgpr_0").value
chk("con la MISMA obra, varias pasadas no olvidan nada", _v == 1785.0, _v)

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ Las tablas de lo medido son de su obra")
TABLAS = {"buffers": ("bc_df", ("Buffer", "Buffer", "HKPR (mm)"), [1500.0]),
          "plomada": ("plb_bsr_df", ("Elevador", "Lift", "BSR (mm)"), [1601.0]),
          "rieles": ("rc_L_df", ("Elevador", "Lift", "L (mm)"), [32000.0])}


def editor(at, col):
    return next(df for df in at.dataframe if col in list(df.value.columns))


for pg, (k, col, vals) in TABLAS.items():
    at = nuevo(pg)
    elige(at, pg, "PRJ-A")
    at.session_state["sembrar_tabla"] = (k, col, vals)
    corre(at)
    e0 = editor(at, col[2])
    antes = (list(e0.value[col[2]]), e0.proto.id)
    at.session_state["pg"] = "otra"
    corre(at)
    at.session_state["pg"] = pg
    corre(at)
    e1 = editor(at, col[2])
    chk("%s: lo medido en la tabla (%s) se queda al salir y volver con la MISMA obra"
        % (pg, vals), list(e1.value[col[2]]) == vals and antes[0] == vals,
        (antes[0], list(e1.value[col[2]])))
    elige(at, pg, "PRJ-C")
    e2 = editor(at, col[2])
    chk("⚠️ %s: cambiar de obra sin salir vacía la tabla Y es una tabla NUEVA para el navegador "
        "(otra identidad: sus ediciones no vuelven)" % pg,
        list(e2.value[col[2]]) == [0.0] and e2.proto.id != antes[1],
        (list(e2.value[col[2]]), e2.proto.id == antes[1]))

at = nuevo("buffers")
elige(at, "buffers", "PRJ-A")
at.session_state["sembrar_tabla"] = TABLAS["buffers"]
corre(at)
at.session_state["pg"] = "otra"
corre(at)
at.session_state["pl_prj_bc"] = "Obra B (PRJ-B)"      # la obra cambia mientras está fuera
at.session_state["pg"] = "buffers"
corre(at)
_t = list(editor(at, "HKPR (mm)").value["HKPR (mm)"])
chk("al VOLVER con otra obra también se vacía (antes de v540 la tabla de A seguía)",
    _t == [0.0] and widget(at, "bc_hkp").value == 80.0, (_t, widget(at, "bc_hkp").value))

# ── Cada tabla que escriben las herramientas está en la lista, y su editor usa la clave
#    con generación ──
_escritas, _editores = {}, {}
for f, h in (("core/rail_cut_ui.py", "rc"), ("core/buffer_cut_ui.py", "bc"),
             ("core/plumb_ui.py", "plb"), ("core/belting_ui.py", "belt")):
    for n in ast.walk(ast.parse(_fuente(f))):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Subscript) \
                and ast.unparse(n.targets[0].value) == "st.session_state" \
                and isinstance(n.targets[0].slice, ast.Constant) \
                and str(n.targets[0].slice.value).endswith("_df"):
            _escritas.setdefault(h, set()).add(n.targets[0].slice.value)
        if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("data_editor"):
            _kw = {k.arg: ast.unparse(k.value) for k in n.keywords}
            _editores.setdefault(h, []).append(_kw.get("key", ""))
chk("se leyeron las tablas de las herramientas (no es un paso en vacío)",
    sum(len(x) for x in _escritas.values()) == 4, _escritas)
chk("toda tabla que escribe una herramienta está en `TABLAS` de esa herramienta",
    all(set(v) == set(EV.TABLAS.get(h, ())) for h, v in _escritas.items()), _escritas)
chk("⚠️ cada tabla editable usa la clave con generación de SU herramienta",
    all(k.startswith("estado_vivo.clave_tabla('%s', " % h) for h, ks in _editores.items()
        for k in ks) and sum(len(x) for x in _editores.values()) == 4, _editores)

# ═════════════════════════════════════════════════════════════════
sec("4. «Download», no «Descargar»")
_tp = ast.parse(_fuente("core/projects_ui.py"))
_doc = {id(n.body[0].value) for n in ast.walk(_tp)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module))
        and n.body and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant)}
_es = [n.lineno for n in ast.walk(_tp) if isinstance(n, ast.Constant)
       and isinstance(n.value, str) and "Descargar" in n.value and id(n) not in _doc]
chk("el botón de descarga de Files ya no dice «Descargar» (fuera de comentarios y docstrings)",
    not _es, _es)
chk("...y va por `t()` con placeholder",
    "t(':material/download: Download {x}', x=e['nombre'] or t('file'))" in ast.unparse(_tp))

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
