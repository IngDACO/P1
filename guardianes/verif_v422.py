"""v422: una localización interna (oficina/almacén/taller) nunca se cuela en el
dinero de obra — ni desaparece de donde se trabaja.

No todo el mundo trabaja en obra: hay gente de oficina y de almacén que ficha, hace
su pre-start y genera gastos. Se modelan como un proyecto para reusar la fontanería
que ya existe, pero con una diferencia que lo decide todo: **no se le facturan a
nadie**. Su costo es estructura.

El cerrojo es el DEFAULT de `list_projects` (`incluir_internos=False`), que protege
los ~59 call-sites de golpe. Este guardián comprueba las DOS direcciones, porque un
cerrojo que solo se mira por un lado envejece: el default de `incluir_archivados` ha
mordido CINCO veces (v310, v321, v322, v358, v369) siempre por el mismo motivo —
alguien escribió una consulta nueva y el default decidió por él.

  (a) NINGUNA función que hable de dinero de cliente, cronograma o cartera puede
      pedir `incluir_internos=True`;
  (b) las que DEBEN verlas tienen que seguir pidiéndolo — si alguien lo quita, el
      almacén desaparece del fichaje o su celda del tablero se queda muda, sin que
      falle nada;
  (c) `es_interno` es la ÚNICA definición (v323: cinco copias divergentes de un
      helper es lo que produjo los fallos de dinero);
  (d) `derive_estado` recibe el tipo en TODOS sus call-sites, o restaurar una
      localización archivada la devuelve a «Planificado» (regla v340).
"""
import ast
import io
import sys
import tokenize
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


def arbol(p: Path):
    """AST sin comentarios: un `grep` cuenta mis propios comentarios como uso
    (trampa nº2, que ya ha mordido cuatro veces)."""
    src = p.read_text(encoding="utf-8")
    sin = tokenize.untokenize(
        [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
         if t.type != tokenize.COMMENT])
    return ast.parse(sin)


def contenedora(a, ln):
    mejor = None
    for n in ast.walk(a):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.lineno <= ln <= (n.end_lineno or n.lineno) and (
                    mejor is None or n.lineno > mejor.lineno):
                mejor = n
    return mejor.name if mejor else "(módulo)"


# ── Inventario de quién pide internos ───────────────────────────────────────
PIDEN = {}                       # (fichero, función) -> nº de llamadas con True
TODAS = set()                    # (fichero, función) con alguna llamada
for p in sorted(RAIZ.glob("core/*.py")) + [RAIZ / "app.py"]:
    a = arbol(p)
    for n in ast.walk(a):
        if not (isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Attribute)
                 and n.func.attr in ("list_projects", "list_projects_for_field"))
                or (isinstance(n.func, ast.Name)
                    and n.func.id in ("list_projects", "list_projects_for_field")))):
            continue
        clave = (p.name, contenedora(a, n.lineno))
        TODAS.add(clave)
        for k in n.keywords:
            if k.arg == "incluir_internos" and isinstance(k.value, ast.Constant) \
                    and k.value.value is True:
                PIDEN[clave] = PIDEN.get(clave, 0) + 1

print("== (a) nadie que hable de dinero de obra pide las internas ==")

# Todo lo que decide un importe que se le cobra a un cliente, un plazo de obra o
# la cartera. Si una de estas empieza a pedirlas, la oficina sale como una obra.
PROHIBIDO = {
    ("finance.py", "group_profitability"),      # margen 0% + aviso
    ("finance.py", "resultado_por_proyecto"),   # pérdida garantizada en el ranking
    ("finance.py", "sin_facturar"),             # «$X sin facturar» de la oficina
    ("invoices.py", "pendiente_por_proyecto"),  # LA definición del pendiente
    ("invoices_ui.py", "_nueva_factura"),       # no se factura
    ("expenses.py", "over_budget"),             # sin presupuesto (decisión del usuario)
    ("projects.py", "gaps_by_group"),           # no tiene fecha de fin
    ("projects.py", "projections_by_group"),
    ("projects_ui.py", "_kpis"),                # 0% eterno arrastra el avance medio
    ("projects_ui.py", "_panel_proyectos"),     # la cartera es de obras
    ("projects_ui.py", "render_owner_projects"),
    ("admin_digest.py", "_base"),               # el radar del admin
    ("survey_ui.py", "render_survey_tab"),      # una oficina no recibe surveys
}
_viola = sorted(k for k in PROHIBIDO if k in PIDEN)
chk("las funciones de obra NO las piden", _viola, [])
chk("...y todas siguen existiendo (si no, el chequeo pasa en vacío)",
    sorted(k for k in PROHIBIDO if k not in TODAS), [])

print("\n== (b) las que deben verlas siguen pidiéndolas ==")

# Si alguien quita el flag aquí, no falla nada: el almacén simplemente deja de
# poder ficharse, o su celda del tablero se queda sin nombre ni color.
OBLIGADO = {
    ("projects.py", "project_hours_bulk"):  "las horas del almacén se perderían",
    ("roster.py", "trabajos_idx"):          "su celda del tablero saldría muda",
    ("home_ui.py", "_agenda_hoy"):          "la agenda no sabría su nombre",
    ("home_ui.py", "buscar"):               "el buscador no la encontraría",
    ("home_ui.py", "_resumen_proyecto_home"): "resolución por ID",
    ("plan_data.py", "del_proyecto"):       "resolución por ID",
    ("timeclock_ui.py", "_proyectos_para"): "no se podría fichar en ella",
    ("prestart_ui.py", "_projects_for"):    "no se podría hacer su pre-start",
    ("roster_ui.py", "_opciones"):          "no se podría asignar en el tablero",
    ("roster_ui.py", "_asignacion_inteligente"): "no se podría asignar",
    ("inventory_ui.py", "_proyectos"):      "un activo no podría estar en el almacén",
    ("auth_ui.py", "_ficha_usuario"):       "diría «0 proyectos» a quien es de oficina",
    ("expenses.py", "group_expenses"):      "su gasto saldría como huérfano",
    ("projects_ui.py", "_nuevo_proyecto_form"): "no avisaría del nombre duplicado",
    # v423: quien trabaja en la oficina/almacén tiene su sitio asignado ahí y necesita
    # sus avisos, sus recibos y sus archivos. Sin esto, «Mis proyectos» le saldría vacío.
    ("projects_ui.py", "render_field_projects"): "el de oficina no vería su sitio",
}
_faltan = sorted(f"{k[0]}:{k[1]} ({por_que})"
                 for k, por_que in OBLIGADO.items() if k not in PIDEN)
chk("todas piden incluir_internos=True", _faltan, [])

# ⚠️ El fallback del fichaje es el caso que NO se ve en la lista de arriba: la misma
# función pide internos en la rama de asignados y NO debe pedirlos en la de «no tiene
# nada asignado», o la oficina se le regala a cualquiera. Se comprueba por estructura.
_tc = arbol(RAIZ / "core" / "timeclock_ui.py")
_fn = next(n for n in ast.walk(_tc)
           if isinstance(n, ast.FunctionDef) and n.name == "_proyectos_para")
_calls = [n for n in ast.walk(_fn) if isinstance(n, ast.Call)
          and isinstance(n.func, ast.Attribute) and n.func.attr == "list_projects"]
_sin_int = [c for c in _calls
            if not any(k.arg == "incluir_internos" for k in c.keywords)]
chk("el fallback (sin asignaciones) NO ofrece localizaciones", len(_sin_int), 1)

print("\n== (c) `es_interno` es la ÚNICA definición ==")
_defs = []
for p in sorted(RAIZ.glob("core/*.py")) + [RAIZ / "app.py"]:
    for n in ast.walk(arbol(p)):
        if isinstance(n, ast.FunctionDef) and n.name in ("es_interno", "solo_obras",
                                                         "solo_internas"):
            _defs.append(f"{p.name}:{n.name}")
chk("definidas una sola vez, y en projects.py",
    sorted(_defs), ["projects.py:es_interno", "projects.py:solo_internas",
                    "projects.py:solo_obras"])
# nadie re-implementa la regla comparando contra la lista a mano
_copias = []
for p in sorted(RAIZ.glob("core/*.py")):
    if p.name == "projects.py":
        continue
    for n in ast.walk(arbol(p)):
        if isinstance(n, ast.Compare) and any(isinstance(o, ast.In) for o in n.ops):
            for c in n.comparators:
                if isinstance(c, ast.Attribute) and c.attr == "TIPOS_INTERNOS":
                    _copias.append(f"{p.name}:{n.lineno}")
chk("nadie re-implementa la regla con `in TIPOS_INTERNOS`", _copias, [])

print("\n== (d) `derive_estado` recibe el tipo en todos sus call-sites ==")
_mal = []
for p in sorted(RAIZ.glob("core/*.py")) + [RAIZ / "app.py"]:
    a = arbol(p)
    for n in ast.walk(a):
        if (isinstance(n, ast.Call)
                and ((isinstance(n.func, ast.Attribute) and n.func.attr == "derive_estado")
                     or (isinstance(n.func, ast.Name) and n.func.id == "derive_estado"))):
            tiene = len(n.args) >= 3 or any(k.arg == "tipo" for k in n.keywords)
            if not tiene:
                _mal.append(f"{p.name}:{n.lineno} ({contenedora(a, n.lineno)})")
chk("todos pasan el tipo", _mal, [])

# ── Comportamiento ──────────────────────────────────────────────────────────
print("\n== y la regla funciona ==")
import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "x"}
from core import projects as P                                     # noqa: E402

chk("Oficina es interna", P.es_interno({"Type": "Office"}))
chk("Almacén es interna", P.es_interno({"Type": "Warehouse"}))
chk("Instalación NO lo es", P.es_interno({"Type": "Installation"}), False)
chk("sin tipo (proyectos anteriores a v306) NO lo es", P.es_interno({}), False)
chk("una localización nace Abierta, no «Planificado»",
    P.derive_estado(0, "", "Office"), P.INTERNO_ABIERTA)
chk("...y restaurarla la devuelve a Abierta, no a Planificado",
    P.derive_estado(0, "", "Warehouse"), P.INTERNO_ABIERTA)
chk("una obra al 0% sigue Planificada", P.derive_estado(0, "", "Installation"),
    "Planned")
chk("archivar sigue mandando sobre el tipo",
    P.derive_estado(0, "Archived", "Office"), "Archived")
_l = [{"ID": "A", "Type": "Installation"}, {"ID": "B", "Type": "Workshop"}]
chk("solo_obras", [p["ID"] for p in P.solo_obras(_l)], ["A"])
chk("solo_internas", [p["ID"] for p in P.solo_internas(_l)], ["B"])
chk("los tipos de obra y los internos no se solapan",
    sorted(set(P.TIPOS) & set(P.TIPOS_INTERNOS)), [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
