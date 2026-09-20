"""v455 — se ELIMINA el modelo viejo de ganancia (% sobre el total).

Petición del usuario: *«quiero que elimines del todo el viejo modelo de ganancia sobre el
total del proyecto»*.

## Qué había

Dos formas de contestar «cuánto gano con esta obra», conviviendo desde v360:
  - **viejo** — `ingreso = mo × (1 + MargenMO/100) + materiales`, un % tecleado;
  - **por rubro** — un IMPORTE: `horas × ganancia/hora` de cada persona, más la ganancia
    fija de la obra (v373), más el precio pactado si vino de una cotización (v370).

## Qué queda, en este orden

  1. **cotizada** → el precio que el cliente firmó (es un hecho, no una estimación);
  2. **por rubro** → ganancia/hora + ganancia fija;
  3. **nada de lo anterior** → la obra vale su COSTO, y se AVISA de quién trabajaría sin
     ganancia. No se inventa un margen que nadie ha decidido.

El `%` pasa a ser SIEMPRE una consecuencia, nunca una entrada.

## ⚠️ Lo medido antes de tocar

10 de 19 obras usaban el modelo viejo, pero **solo 4 cambiaban de cifra** (las demás
tienen costo 0, así que el % no se aplicaba sobre nada). Ingreso estimado del grupo:
**118.233,77 → 116.757,97 (−1.475,80)**, y la ejecución posterior dio exactamente ese
número. El usuario decidió no migrar esas 4 («son de prueba»).

## ⚠️ Lo que NO se toca, y por qué

  - **La columna `MargenMO` sigue en `PROJECTS_HEADERS`.** Quitarla desplazaría las 20
    columnas siguientes y, como la fila de `create_project` es POSICIONAL, cada dato
    caería en la de al lado — el fallo que mató esa función 3 versiones en v363. Se
    escribe vacía y no la lee nadie. Su CONTENIDO sí se borró de la hoja.
  - **`Grupos.MargenDefault` se queda**: ya no alimenta la ganancia de ninguna obra, pero
    es el punto de partida del margen de una línea de cotización (`quotes_ui`), que es el
    **precio al cliente** — otra cosa. Vaciarlo haría que cada línea nueva arrancara en 0%.
"""
import ast
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


print("== 1. El modelo viejo no existe en el código ==")
_fin = (CORE / "finance.py").read_text(encoding="utf-8")
_a_fin = ast.parse(_fin)
chk(not any(isinstance(n, ast.FunctionDef) and n.name == "project_margin"
            for n in ast.walk(_a_fin)),
    "`project_margin` ya no existe")

# ⚠️ La comprobación de fondo: NINGUNA parte del repo puede volver a aplicar un % de
# margen sobre la mano de obra. Se busca la FORMA (`mo * (1 + algo/100)`), no un nombre.
_sospechosas = []
for f in sorted(CORE.glob("*.py")):
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult)):
            continue
        txt = ast.unparse(n)
        if "1 + " in txt and "/ 100" in txt and ("mo" in txt or "labor" in txt.lower()):
            _sospechosas.append(f"{f.name}:{n.lineno} {txt[:60]}")
for x in _sospechosas:
    print(f"     {x}")
chk(not _sospechosas, f"nadie aplica ya un % sobre la mano de obra ({len(_sospechosas)})")

# Validar la red contra un caso construido (trampa nº12): si no ve el patrón, su 0 no vale.
_s = ast.parse("x = mo * (1 + m / 100.0)")
_v = [n for n in ast.walk(_s) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult)
      and "1 + " in ast.unparse(n) and "/ 100" in ast.unparse(n)]
chk(len(_v) == 1, f"la red ve la fórmula vieja construida a propósito ({len(_v)})")

chk("LabourMargin" not in (CORE / "projects_ui.py").read_text(encoding="utf-8"),
    "la interfaz no lee ni escribe MargenMO en ningún sitio")
chk("margen_mo" not in ast.unparse(ast.parse((CORE / "projects.py").read_text(encoding="utf-8"))),
    "`create_project` ya no acepta `margen_mo`")


print("\n== 2. …pero la columna sigue en la cabecera (o se desplaza la fila) ==")
_a_p = ast.parse((CORE / "projects.py").read_text(encoding="utf-8"))
_hdr = next(n.value for n in ast.walk(_a_p) if isinstance(n, ast.Assign)
            and any(getattr(t_, "id", "") == "PROJECTS_HEADERS" for t_ in n.targets))
_cols = [e.value for e in _hdr.elts if isinstance(e, ast.Constant)]
chk("LabourMargin" in _cols, "la columna muerta sigue en PROJECTS_HEADERS (columna muerta, a propósito)")
_fn = next(n for n in ast.walk(_a_p) if isinstance(n, ast.FunctionDef)
           and n.name == "create_project")
_row = next(x.value for x in ast.walk(_fn) if isinstance(x, ast.Assign)
            and any(getattr(t_, "id", "") == "row" for t_ in x.targets))
chk(len(_row.elts) == len(_cols),
    f"la fila POSICIONAL sigue casando con la cabecera ({len(_row.elts)} vs {len(_cols)})")


print("\n== 3. Los tres modelos que quedan, EJECUTADOS ==")
# ⚠️ Importar no ejecuta (v378): se llama a la función con las tres formas.
import streamlit as st  # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "rol": "administrator", "grupo": "cliente1"}
from core import projects as P, finance as F  # noqa: E402

_mods = {}
for p in P.list_projects("cliente1", incluir_archivados=True, incluir_internos=True):
    _mods[str(p.get("ID"))] = F.project_revenue(str(p.get("ID")), "cliente1", p)["modelo"]
_vistos = set(_mods.values())
print(f"     modelos vivos: {sorted(_vistos)}")
chk(not any(m.startswith("margen") for m in _vistos),
    f"ninguna obra usa ya el modelo del % ({sorted(m for m in _vistos if m.startswith('margen'))})")
chk(_vistos <= {"cotizado", "rubro", "rubro+fija", "fija", "a_costo"},
    f"solo quedan los modelos nuevos ({sorted(_vistos)})")
# ⚠️ v456: con la demo vacía no hay obras, así que no hay variedad que ver. El resto
# del guardián (que nadie aplique ya un % y que la fila case con la cabecera) es
# ESTÁTICO y sigue valiendo; solo esta afirmación necesita datos.
# ⚠️ v480: la salvaguarda solo contemplaba el libro VACIO, y con UNA obra exigia ver
# tres modelos distintos — imposible por aritmetica, no por un fallo. Se pide que haya
# con que comprobar, no simplemente que haya algo.
if len(_mods) < 3:
    print(f"     ({len(_mods)} proyecto(s): no hay con que comprobar la variedad)")
else:
    chk(len(_vistos) >= 3, f"…y el chequeo ve variedad real, no un solo caso ({len(_vistos)})")

# Una obra sin ganancia vale su COSTO y lo DICE (patrón v346: nada de ceros silenciosos)
_ac = next((pid for pid, m in _mods.items() if m == "a_costo"), None)
if _ac:
    r = F.project_revenue(_ac, "cliente1")
    chk(abs(r["ingreso"] - (r["costo"] + r.get("ganancia_fija", 0))) < 0.01,
        f"{_ac}: sin ganancia, el ingreso ES el costo ({r['ingreso']} vs {r['costo']})")
    chk(r["margen_pct"] == 0.0, f"{_ac}: y el % es 0, no un default heredado")


print("\n== 4. ⚠️ MargenDefault SIGUE vivo: es de la COTIZACIÓN, no de la obra ==")
from core import auth  # noqa: E402
chk(hasattr(auth, "group_margin_default"),
    "`group_margin_default` existe (lo usa quotes_ui para la línea nueva)")
chk("group_margin_default" in (CORE / "quotes_ui.py").read_text(encoding="utf-8"),
    "…y quotes_ui lo sigue usando como punto de partida")
chk("group_margin_default" not in _fin,
    "…pero finance ya NO lo usa para estimar el ingreso de una obra")

print("\n== 5. Ningún TEXTO visible describe ya el modelo viejo ==")
# El usuario no solo pidió quitar el cálculo: pidió que **no se siga hablando** de un
# margen sobre el total. Eso es texto de pantalla, no aritmética — y había cuatro sitios
# que lo describían como vigente, incluido un botón «Back to the %» que ofrecía VOLVER a
# un modelo que ya no existe.
#
# ⚠️ El patrón busca la FÓRMULA y la idea del % sobre el total, NO la palabra «margin»:
# un primer intento con `margin %` marcó 5 textos correctos —la cabecera de columna y los
# de cotización, que dicen «escribes la ganancia y el % sale solo»— y eso es justo el
# modelo NUEVO. Una red que grita sobre lo que ya está bien acaba ignorándose (v452).
_MALAS = re.compile(r"\(1\s*\+\s*margin\)|labour\s*×\s*\(1|cost\s*×\s*\(1|"
                    r"back to the margin|goes back to the margin|"
                    r"%\s*on the labour|margin on labour|"
                    r"margen sobre la mano de obra|sobre el total del proyecto|"
                    r"basis of the sell rate", re.I)
_PINTA = ("write", "markdown", "info", "success", "warning", "error", "caption",
          "metric", "button", "expander", "number_input")
_textos = []
for _f in sorted(CORE.glob("*.py")):
    for _n in ast.walk(ast.parse(_f.read_text(encoding="utf-8"))):
        if not (isinstance(_n, ast.Call)
                and (getattr(_n.func, "id", None) in ("t", "d", "_d")
                     or str(getattr(_n.func, "attr", "")).startswith(_PINTA))):
            continue
        for _a in ast.walk(_n):
            if isinstance(_a, ast.Constant) and isinstance(_a.value, str) and _MALAS.search(_a.value):
                _textos.append(f"{_f.name}:{_a.lineno} {_a.value[:70]!r}")
for _x in _textos:
    print(f"     {_x}")
chk(not _textos, f"ningún texto de pantalla habla del % sobre el total ({len(_textos)})")

# ⚠️ Validar la red antes de creerse su cero (trampa nº12).
_sonda = ast.parse('st.caption("labour × (1 + margin) + materials")')
_ve = [a for n in ast.walk(_sonda) if isinstance(n, ast.Call) for a in ast.walk(n)
       if isinstance(a, ast.Constant) and isinstance(a.value, str) and _MALAS.search(a.value)]
chk(len(_ve) == 1, f"la red ve la frase vieja construida a propósito ({len(_ve)})")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
