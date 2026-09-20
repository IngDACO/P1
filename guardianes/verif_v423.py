"""v423: las localizaciones internas tienen su propia sección — y NO heredan las
piezas de obra que no significan nada para ellas.

v422 puso el cerrojo de datos: `list_projects` las oculta por defecto. Eso, solo,
las dejaría **inalcanzables** — se podrían crear y no habría forma de verlas, que es
media aplicación de la regla v340 (lo que se puede ocultar tiene que poder verse).
Esta versión es su cara visible.

Lo que se protege:
  (a) la sub-pestaña existe y su destino se despacha de verdad (guardián v303: un
      `_ir_a` a una sub que no existe navega a ninguna parte);
  (b) ⚠️ la pantalla NO tiene cronograma, avance, presupuesto, margen, cliente ni
      facturación — ponerle esas piezas sería devolverla al mundo de la obra por la
      puerta de atrás, justo lo que v422 vino a impedir;
  (c) el cerrojo de aislamiento (v351) está puesto: esta vista trae el objeto por ID
      GLOBAL, igual que proyecto/factura/nómina/activo, así que sin él editar la URL
      abriría la oficina de otra empresa cliente;
  (d) el alta NO puede crear una obra por descuido (tipo de `TIPOS_INTERNOS`) ni
      generar actividades;
  (e) al CAMPO se le quita «Avance» solo para las internas, y se le siguen dando
      avisos, recibos y archivos.
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
    src = p.read_text(encoding="utf-8")
    sin = tokenize.untokenize(
        [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
         if t.type != tokenize.COMMENT])
    return ast.parse(sin)


PU = arbol(RAIZ / "core" / "projects_ui.py")
HU = arbol(RAIZ / "core" / "home_ui.py")


def fn(a, nombre):
    return next((n for n in ast.walk(a)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ── (a) La sección existe y se despacha ─────────────────────────────────────
print("== a) la sección existe y llega a su pantalla ==")
import streamlit as st                                              # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "x"}
from core import home_ui, projects_ui as _PU                        # noqa: E402

_ids = [i for i, _ in home_ui._SUBSECCIONES["proyectos"][1]]
chk("la sub-pestaña está registrada", "🏢 Localizaciones" in _ids)
chk("...y no se perdió ninguna de las de antes",
    [i for i in ("📊 Proyectos", "🗂 Agrupaciones") if i not in _ids], [])
chk("existe la función que la pinta", hasattr(_PU, "render_localizaciones"))

# El despachador tiene que comparar contra el MISMO literal que el registro. Un
# emoji distinto (o un display en vez del ID) navega a ninguna parte — el fallo real
# que v303 encontró en 7 de los 9 indicadores del resumen.
_disp = fn(HU, "_seccion_proyectos")
_lits = {c.value for c in ast.walk(_disp)
         if isinstance(c, ast.Constant) and isinstance(c.value, str)}
chk("el despachador compara contra el ID exacto", "🏢 Localizaciones" in _lits)
_llama = {n.func.attr for n in ast.walk(_disp)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
chk("...y llama a render_localizaciones", "render_localizaciones" in _llama)

# ── (b) Sin las piezas de obra ──────────────────────────────────────────────
print("\n== b) la pantalla NO hereda lo que no le corresponde ==")
NUEVAS = ("render_localizaciones", "_detalle_localizacion", "_cartera_localizaciones",
          "_nueva_localizacion_form", "_editar_localizacion", "_loc_equipo",
          "_loc_prestarts", "_loc_datos")
_fns = [fn(PU, n) for n in NUEVAS]
chk("las 8 funciones existen", sum(1 for f in _fns if f), len(NUEVAS))

# Nada de cronograma / SPI / facturación / presupuesto / margen.
PROHIBIDAS = {"build_schedule", "project_schedule", "schedule_svg", "real_scurve",
              "schedule_projection", "_ir_a_facturar", "pendiente_de_facturar",
              "project_revenue", "cost_projection", "add_activity", "save_activities",
              "_field_activities", "_ganancia_section"}
_usa = set()
for f in _fns:
    if not f:
        continue
    for n in ast.walk(f):
        if isinstance(n, ast.Call):
            _nm = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if _nm in PROHIBIDAS:
                _usa.add(f"{f.name} -> {_nm}")
chk("no usa cronograma, SPI, margen ni facturación", sorted(_usa), [])

# Ni pide los campos de obra en el alta/edición.
CAMPOS_OBRA = {"Budget", "LabourMargin", "ClientID", "NS", "EndDateEst",
               "FixedProfit", "HourlyProfitJSON", "RequiredCerts"}
_pide = set()
for nombre in ("_nueva_localizacion_form", "_editar_localizacion"):
    f = fn(PU, nombre)
    for n in ast.walk(f or ast.Module(body=[], type_ignores=[])):
        if isinstance(n, ast.Constant) and n.value in CAMPOS_OBRA:
            _pide.add(f"{nombre} -> {n.value}")
chk("el alta/edición no escribe campos de obra", sorted(_pide), [])

# ── (c) Cerrojo de aislamiento ──────────────────────────────────────────────
print("\n== c) el cerrojo de aislamiento (v351) ==")
_det = fn(PU, "_detalle_localizacion")
_calls = [n for n in ast.walk(_det) if isinstance(n, ast.Call)]
_l_get = min([n.lineno for n in _calls
              if getattr(n.func, "attr", "") == "get_project"] or [10 ** 9])
_l_exi = min([n.lineno for n in _calls
              if getattr(n.func, "attr", "") == "exigir"] or [10 ** 9])
_l_pinta = min([n.lineno for n in _calls
                if getattr(n.func, "attr", "") in ("segmented_control", "container")]
               or [10 ** 9])
chk("llama a tenant.exigir", _l_exi < 10 ** 9)
chk("...DESPUÉS de traer el objeto", _l_get < _l_exi)
chk("...y ANTES de pintar nada", _l_exi < _l_pinta)
# y comprueba que el ID es de verdad interno: abrir una OBRA por esta vista la
# mostraría sin su cronograma ni su facturación, que es peor que no abrirla.
_esint = [n for n in ast.walk(_det) if isinstance(n, ast.Call)
          and getattr(n.func, "attr", "") == "es_interno"]
chk("verifica que el ID es una localización", len(_esint) >= 1)

# ── (d) El alta no puede crear una obra ─────────────────────────────────────
print("\n== d) el alta crea una localización, no una obra ==")
_alta = fn(PU, "_nueva_localizacion_form")
_cp = [n for n in ast.walk(_alta) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "create_project"]
chk("hay UNA sola llamada a create_project", len(_cp), 1)
_kw = {k.arg for k in _cp[0].keywords} if _cp else set()
chk("pasa `tipo`", "tipo" in _kw)
chk("NO pasa `activities` (nace sin cronograma)", "activities" not in _kw)
chk("NO pasa presupuesto ni margen",
    sorted(_kw & {"presupuesto", "margen_mo", "cliente_id", "ns", "fecha_fin_est"}), [])
# el selector de tipo se alimenta de TIPOS_INTERNOS, no de TIPOS
# ⚠️ Los atributos son nombres EXACTOS: `TIPOS_INTERNOS` no contiene a `TIPOS` como
# elemento del conjunto. Mi primera versión pedía «TIPOS in _attrs and … not …», que
# fallaba JUSTO porque el código está bien — el test fallando por su propia aritmética
# (v363/v372). Se comprueba lo que se quiere decir, y nada más.
_attrs = {n.attr for n in ast.walk(_alta) if isinstance(n, ast.Attribute)}
chk("el tipo sale de TIPOS_INTERNOS", "TIPOS_INTERNOS" in _attrs)
chk("...y NO de TIPOS (los de obra)", "TIPOS" in _attrs, False)

# ── (e) La vista del campo ──────────────────────────────────────────────────
print("\n== e) el campo: sin «Avance», con lo demás ==")
_rf = fn(PU, "render_field_projects")
_esint_rf = [n for n in ast.walk(_rf) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "es_interno"]
chk("distingue las internas", len(_esint_rf) >= 1)

# ⚠️ Que `es_interno` APAREZCA no basta: la función lo usa también para las tarjetas
# de cabecera, así que borrar el recorte del menú seguía pasando el chequeo. Se
# comprueba la ESTRUCTURA: (1) las opciones del radio salen de una variable —una
# lista literal no se puede recortar—, y (2) hay un `if es_interno(...)` que la
# reasigna. Lo destapó probar el guardián contra el código roto, no leerlo.
_radio = next((n for n in ast.walk(_rf) if isinstance(n, ast.Call)
               and getattr(n.func, "attr", "") == "radio"), None)
chk("las opciones del menú salen de una variable",
    bool(_radio) and len(_radio.args) >= 2 and isinstance(_radio.args[1], ast.Name))
_var = _radio.args[1].id if _radio and isinstance(_radio.args[1], ast.Name) else None
_recorta = []
for n in ast.walk(_rf):
    if not isinstance(n, ast.If):
        continue
    if not any(isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "es_interno"
               for c in ast.walk(n.test)):
        continue
    for s in n.body:
        for t in ast.walk(s):
            if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store) and t.id == _var:
                _recorta.append(n.lineno)
chk(f"...y un `if es_interno(...)` reasigna `{_var}` (quita «Avance»)",
    bool(_recorta))
_txt = {c.value for c in ast.walk(_rf)
        if isinstance(c, ast.Constant) and isinstance(c.value, str)}
for _s in ("🚨 Avisos", "💰 Recibos", "📎 Archivos"):
    chk(f"conserva {_s}", _s in _txt)
chk("«Avance» sigue existiendo (para las OBRAS)", "🏗 Avance" in _txt)

# ── Costos: sin las piezas de OBRA ──────────────────────────────────────────
# ⚠️ v429: una localización no termina, no lleva presupuesto (v423) y su costo no se
# compara con nada. «Costará al terminar» salía «—» fijo, «Presupuesto» también, y el
# titular decía «no tiene presupuesto asignado… se define en Datos» — donde ese campo
# NO existe para una localización, o sea que mandaba a buscar algo que no está.
print("")
print("== la pantalla de Costos no habla de lo que no aplica ==")
# ⚠️ CADUCADO por v481 y REAPUNTADO: el bloque de costos se extrajo de
# `render_expenses` a `_costos_section` para que el CAMPO no lo vea. El código es el
# mismo y el comportamiento también; solo cambió de función.
_re = fn(PU, "_costos_section")
_esint_re = [n for n in ast.walk(_re) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "es_interno"]
chk("el bloque de costos distingue las internas", len(_esint_re) >= 1)
# ⚠️ Y lo que v423 no podía comprobar hasta ahora: que ese bloque sea justo el que el
# campo NO ve. Así la protección de v423 queda atada a la de v481 — si alguien devuelve
# el bloque a `render_expenses` sin guarda, salta aquí y no dentro de tres versiones.
_rx = fn(PU, "render_expenses")
_guardas = [ast.unparse(n.test) for n in ast.walk(_rx)
            if isinstance(n, ast.If) and "_costos_section" in ast.unparse(n)]
chk("...y ese bloque cuelga de `ver_costos` (v481)", _guardas == ["ver_costos"])


def _bajo_if_interno(f, marca):
    """¿`marca` aparece dentro de un `if` que consulta si es interna (o su else)?"""
    for n in ast.walk(f):
        if not isinstance(n, ast.If):
            continue
        _t = ast.dump(n.test)
        if "_loc" not in _t and "es_interno" not in _t:
            continue
        for rama in (n.body, n.orelse):
            for s_ in rama:
                for c in ast.walk(s_):
                    if (isinstance(c, ast.Constant) and isinstance(c.value, str)
                            and marca in c.value):
                        return True
    return False


# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
chk("«Costará al terminar» cuelga de si es interna",
    _bajo_if_interno(_re, "Costará al terminar")
    or _bajo_if_interno(_re, "Cost at completion"))
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
chk("«Presupuesto» también",
    _bajo_if_interno(_re, "Budget") or _bajo_if_interno(_re, "Budget"))
# ⚠️ CADUCADO por el i18n (v440/v441): el titular pasó al inglés y sale con mayúscula
# («**Overhead** spend»), así que la búsqueda en minúsculas ya no casaba. No es una
# regresión: la rama sigue colgando de `es_interno`. Se compara sin distinguir caja.
chk("y el titular tiene su propia rama para estructura",
    _bajo_if_interno(_re, "estructura") or _bajo_if_interno(_re, "overhead")
    or _bajo_if_interno(_re, "Overhead"))

# ── Tarjetas KPI que se pintan de verdad ────────────────────────────────────
print("\n== las tarjetas KPI se PINTAN (no se descartan) ==")
# ⚠️ `_kpi_card` DEVUELVE HTML, no lo pinta. Llamarla como sentencia suelta
# (`with col: _kpi_card(...)`) es código VÁLIDO que no lanza y deja la tarjeta
# INVISIBLE — pasó en `render_localizaciones` y no lo vio ningún guardián: lo cazó
# mirar la pantalla en producción. Se comprueba en TODO el repo, no solo aquí.
_perdidas = []
for _p in sorted(RAIZ.glob("core/*.py")) + [RAIZ / "app.py"]:
    _a = arbol(_p)
    for _n in ast.walk(_a):
        if (isinstance(_n, ast.Expr) and isinstance(_n.value, ast.Call)
                and getattr(_n.value.func, "id",
                            getattr(_n.value.func, "attr", "")) == "_kpi_card"):
            _perdidas.append(f"{_p.name}:{_n.lineno}")
chk("ninguna llamada a `_kpi_card` descarta su HTML", _perdidas, [])

# ── Comportamiento ──────────────────────────────────────────────────────────
print("\n== y la regla funciona ==")
from core import projects as P                                      # noqa: E402
chk("los tipos del alta son todos internos",
    all(P.es_interno(t) for t in P.TIPOS_INTERNOS))
chk("ninguno es de obra", [t for t in P.TIPOS_INTERNOS if t in P.TIPOS], [])
chk("una localización cerrada sale de la lista por defecto",
    P.derive_estado(0, P.INTERNO_CERRADA, "Office"), P.INTERNO_CERRADA)
chk("`_loc_personas` parte por ';' y limpia",
    _PU._loc_personas({"FieldAssigned": "ana; ; luis ;"}), ["ana", "luis"])
chk("...y con la columna vacía no inventa a nadie",
    _PU._loc_personas({}), [])

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
