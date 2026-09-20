"""Guardián de v441 — F4 (las 5 herramientas técnicas) y el invariante GLOBAL de la UI.

⚠️ Este guardián no lista módulos a mano: **descubre** todos los `*_ui.py` del repo más
`app.py`. Un guardián con lista fija deja fuera al módulo que alguien añada mañana, y ese
es justo el que nadie recuerda traducir.

Lo que afirma:
 1. **0 cadenas SUELTAS sin `t()`** en toda la interfaz. Es el invariante que sustituye
    al detector de español, que falló tres veces (v438, v439, v440): «Fichar», «Firma»,
    «Neto a pagar» o «Guardar» no llevan acento ni palabra funcional y pasan por delante.
 2. ⚠️ Las **SIGLAS del dominio** siguen intactas en las herramientas técnicas. Son los
    nombres que el plano Schindler trae impreso (BKS, TKSW, LFKK, HKP, DSTS…): traducirlas
    rompería la correspondencia con el PDF que el técnico tiene delante — y no daría
    ningún error, solo una herramienta que ya nadie sabe leer.
 3. Nadie tapa `t` (v437 · v439 · quotes_ui: tres veces el mismo `UnboundLocalError`).
 4. Los módulos importan el motor arriba y **se ejecutan** al importarse (v378: importar
    no ejecuta, y eso fue lo que dejó pasar los dos crasheos de v439).
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

F4 = ["survey_ui", "plumb_ui", "rail_cut_ui", "buffer_cut_ui", "belting_ui"]
ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def _src(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. INVARIANTE GLOBAL: 0 cadenas sueltas sin t() en TODA la interfaz")
from i18n_tool import piezas                                      # noqa: E402

# ⚠️ Se DESCUBREN, no se listan: una lista fija deja fuera el módulo nuevo.
UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))
chk("se descubrieron los módulos de interfaz", len(UI) >= 18, f"{len(UI)}")
chk(f"...y están las 5 técnicas ({', '.join(F4)})",
    all(m in UI for m in F4), str([m for m in F4 if m not in UI]))

sueltos = []
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    sueltos += [f"{m}:{p['lin']} {p['txt'][:40]!r}"
                for p in piezas(RAIZ / rel) if not p["fstr"]]
chk(f"0 cadenas sueltas sin t() en los {len(UI) + 1} módulos", not sueltos,
    str(sueltos[:6]))

_llam = 0
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    _llam += sum(1 for x in ast.walk(ast.parse(_src(rel)))
                 if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                 and x.func.id == "t")
chk("...y la traducción realmente se aplicó", _llam >= 1400, f"{_llam} llamadas a t()")

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Las SIGLAS del plano y del dominio NO se tradujeron")
# ⚠️ Verbatim y por módulo: son los nombres impresos en el plano Schindler.
SIGLAS = {
    "core/plumb_ui.py": ["BKS", "RAIL", "TKSW", "LengthTemplate", "SF1", "SF2",
                         "BSR", "DBP", "DBPW", "Omega"],
    "core/rail_cut_ui.py": ["LFKK", "LFGK", "RZ, RO, RF, RB", "FFL"],
    "core/buffer_cut_ui.py": ["HKP", "HKPR"],
    "core/belting_ui.py": ["DSTS", "HGPR", "HGP", "HQ", "FFL"],
    "core/survey_ui.py": ["MAX OFF RL", "BC_CALC", "DIF TSW-FS", "CUT OR", "CUT OL",
                          "ANTHROPIC_API_KEY", "SF1+BKS+2·RAIL+SF2"],
}
for rel, sg in SIGLAS.items():
    falta = [x for x in sg if x not in _src(rel)]
    chk(f"{Path(rel).name:18} conserva sus siglas", not falta, str(falta))
chk("...y el chequeo no corre en vacío",
    sum(len(v) for v in SIGLAS.values()) >= 25)

# ── 3 ────────────────────────────────────────────────────────────
sec("3. Nadie tapa `t` en las herramientas técnicas")


def _mismo_ambito(fn):
    """⚠️ Sin descender a lambdas, funciones anidadas ni comprensiones: tienen su propio
    ámbito y contarlas da falsos positivos sobre código correcto (trampa nº3)."""
    out = []
    for h in fn.body:
        pila = [h]
        while pila:
            x = pila.pop()
            out.append(x)
            for c in ast.iter_child_nodes(x):
                if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef)):
                    pila.append(c)
    return out


tapan = []
for m in UI + ["app"]:
    rel = "app.py" if m == "app" else f"core/{m}.py"
    for fn in ast.walk(ast.parse(_src(rel))):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nod = _mismo_ambito(fn)
        comp = {id(nn) for x in nod for g in (getattr(x, "generators", []) or [])
                for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        _st = [x.lineno for x in nod if isinstance(x, ast.Name)
               and isinstance(x.ctx, ast.Store) and x.id == "t" and id(x) not in comp]
        if "t" in {a.arg for a in fn.args.args + fn.args.kwonlyargs}:
            _st.append(fn.lineno)
        if _st and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                       and x.func.id == "t" for x in nod):
            tapan.append(f"{m}:{fn.lineno} {fn.name}")
chk("ninguna función de la interfaz tapa `t`", not tapan, str(tapan[:4]))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Importan el motor arriba y EJECUTAN al importarse (v378)")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}
import importlib                                                  # noqa: E402

for m in F4:
    tr = ast.parse(_src(f"core/{m}.py"))
    imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
              and any(a.name == "t" for a in x.names) for x in tr.body)
    try:
        importlib.import_module("core." + m)
        _ok2, _e = True, ""
    except Exception as e:                                        # noqa: BLE001
        _ok2, _e = False, f"{type(e).__name__}: {e}"
    chk(f"{m:16} importa `t` arriba y carga", imp and _ok2, f"import_t={imp} {_e}")


# ── 5 ────────────────────────────────────────────────────────────
sec("5. LA SEGUNDA RED: frases sin envolver (el hueco de v349)")
# ⚠️ El chequeo 1 mira el ARGUMENTO de la llamada de display. Una cadena armada antes en
# una VARIABLE (`msg = f"..."; st.success(msg)`) o un trozo de f-string pasan por delante
# sin que salte nada — es exactamente el guardián del LaTeX de v309, que tampoco veía las
# variables. Con el chequeo 1 en verde quedaban **230 frases en español** en la interfaz.
#
# ⚠️ Y aquí SÍ vale un detector de idioma, aunque la trampa nº28 diga que no vale en
# general: su ceguera es con etiquetas CORTAS sin acento ni palabra funcional («Fichar»,
# «Firma», «Pendientes») — y ESAS ya las cubre el chequeo 1. Lo que este ve son FRASES de
# 3+ palabras, y una frase en español lleva acento o artículo. Las dos redes juntas
# cubren lo que cada una se deja.
from barre_frases import frases                                   # noqa: E402
from barre_frases_es import PAL, _sin                             # noqa: E402
import re as _re                                                  # noqa: E402

# Exclusiones DELIBERADAS, con su razón — no son «lo que no me dio tiempo».
EXCLUIDO = {
    # el ID de la sub-pestaña: lo compara `sub ==` y lo usan los deep-links (v232).
    # Traducirlo rompe la navegación sin dar ningún error.
    "🗺 Ruta del día",
}


def _frases_es(mod):
    rel = "app.py" if mod == "app" else f"core/{mod}.py"
    out = []
    for ln, s in sorted(set(frases(RAIZ / rel))):
        if s in EXCLUIDO or s.lstrip().startswith("<style>") or "/*" in s:
            continue                       # un bloque CSS es código, no pantalla
        pals = set(_re.findall(r"[a-záéíóúñü]+", _sin(s)))
        if _re.search(r"[áéíóúñ¿¡]", s) or len(pals & PAL) >= 2:
            out.append(f"{mod}:{ln} {s[:46]!r}")
    return out


_sos = []
for m in UI + ["app"]:
    _sos += _frases_es(m)
chk(f"0 frases en español sin envolver en los {len(UI) + 1} módulos", not _sos,
    f"{len(_sos)}: " + str(_sos[:4]))
chk("...y la red no corre en vacío (ve el español cuando lo hay)",
    bool(_frases_es.__doc__) is False and
    len([1 for s in ["La fecha de fin no puede ser anterior a la de inicio."]
         if _re.search(r"[áéíóúñ]", s) or len(set(_re.findall(r"[a-záéíóúñü]+", _sin(s))) & PAL) >= 2]) == 1)

# ── 6 ────────────────────────────────────────────────────────────
sec("6. El PDF de las herramientas (sale a OBRA, no es pantalla)")
# ⚠️ `tool_pdf(...)` no es una función de display, así que ni el chequeo 1 (mira `st.*`)
# ni el 5 (busca frases de 3+ palabras) veían sus etiquetas de 1-3 palabras. Y ese PDF se
# descarga, se archiva en Drive y se lleva a obra: dejarlo en español sería la pantalla en
# inglés y su documento en español — el desajuste de media-unificación de v419.
TOOLS = ["core/plumb_ui.py", "core/rail_cut_ui.py", "core/buffer_cut_ui.py",
         "core/belting_ui.py"]
DEST = {"tool_pdf", "render_guardar"}
# `herramienta=` es la clave de `toolruns.HERRAMIENTAS` y `datos=` va a `DatosJSON`, que
# lee `entradas_de` al reabrir un cálculo (v148): son DATO, no se traducen ni se auditan.
NO_MIRAR = {"herramienta", "datos"}


def _lits_pdf(rel):
    tr = ast.parse(_src(rel))
    out = []
    for c in ast.walk(tr):
        if not isinstance(c, ast.Call):
            continue
        fn = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "")
        if fn not in DEST:
            continue
        args = list(c.args) + [k.value for k in c.keywords if k.arg not in NO_MIRAR]
        for a in args:
            for x in ast.walk(a):
                if isinstance(x, ast.Constant) and isinstance(x.value, str):
                    s = x.value.strip()
                    if s and any(ch.isalpha() for ch in s):
                        out.append((x.lineno, s))
    return out


_pdf_es = []
for rel in TOOLS:
    for ln, s in _lits_pdf(rel):
        pals = set(_re.findall(r"[a-záéíóúñü]+", _sin(s)))
        if _re.search(r"[áéíóúñ]", s) or len(pals & PAL) >= 1:
            _pdf_es.append(f"{Path(rel).name}:{ln} {s[:40]!r}")
chk("0 etiquetas en español en el PDF de las 4 herramientas", not _pdf_es,
    str(_pdf_es[:5]))
chk("...y el chequeo mira algo (no corre en vacío)",
    sum(len(_lits_pdf(r)) for r in TOOLS) >= 40,
    str(sum(len(_lits_pdf(r)) for r in TOOLS)))

# ⚠️ Un documento va en el idioma BASE, no en el de la pantalla de quien lo genera
# (regla v436/v439): las 4 herramientas tienen que importar `d`, y a nivel de MÓDULO —
# un import dentro de otra función engaña al chequeo (v342).
for rel in TOOLS:
    tr = ast.parse(_src(rel))
    imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
              and any(a.name == "d" for a in x.names) for x in tr.body)
    chk(f"{Path(rel).name:18} importa `d` a nivel de módulo", imp)

# ⚠️ Y que NADIE haya tocado el DATO: la clave de la herramienta sigue en español porque
# es la clave de `toolruns.HERRAMIENTAS`, no una etiqueta.
_claves = {"plomada", "rieles", "buffers", "belting"}
_vistas = set()
for rel in TOOLS:
    for c in ast.walk(ast.parse(_src(rel))):
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "render_guardar":
            for k in c.keywords:
                if k.arg == "herramienta" and isinstance(k.value, ast.Constant):
                    _vistas.add(k.value.value)
chk("las claves de `toolruns.HERRAMIENTAS` siguen intactas (son DATO)",
    _vistas == _claves, f"{sorted(_vistas)} vs {sorted(_claves)}")

# ── 7 ────────────────────────────────────────────────────────────
sec("7. El generador del PDF SIGUE generando (importar no ejecuta, v378)")
try:
    from core.tool_pdf import tool_pdf as _tp
    _b = _tp("Plumb setting-out",
             meta={"Project": "X", "Lifts": "2"},
             tablas=[("Cuts per lift", [{"Lift": 1, "Cut (mm)": 12.0}])],
             notas=["Site check: di + DBP + dd = BSR."])
    chk("tool_pdf devuelve un PDF de verdad", bool(_b) and _b[:4] == b"%PDF",
        f"{len(_b or b'')} bytes")
except Exception as e:                                            # noqa: BLE001
    chk("tool_pdf devuelve un PDF de verdad", False, f"{type(e).__name__}: {e}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
