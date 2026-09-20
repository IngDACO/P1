"""v451 — la OCTAVA red: el argumento de display que es un TERNARIO.

## Por qué hacía falta otra red

La red de POSICIÓN (v440) es el invariante que cierra el i18n: «toda cadena
suelta que llega a una función de display va envuelta en `t()`». Da 0 hoy.

⚠️ Pero mira si el ARGUMENTO es un `Constant`, y un ternario
(`st.info(A if c else B)`) es un `IfExp`. Sus dos ramas pasan por delante sin
que salte nada. Es **literalmente** la trampa nº30 otra vez: *un «0» solo vale
para la forma que esa red sabe ver*, y cada red nueva descubre una bolsa nueva.

Barrido con esta red: **7 ramas** en 3 módulos. Ninguna era español —ya estaban
en inglés—, así que la red de IDIOMA tampoco podía verlas. El daño no es una
fuga visible: es que **no se traducirían nunca** cuando se llene el diccionario
español, y eso no lo detecta nadie hasta que alguien mire la pantalla en el otro
idioma.

## Y la NOVENA forma, del mismo lote

`survey_ui` traducía UNA de las dos ramas del `format_func` de la fase
(`{_FASE_DATOS: "…", _FASE_RES: t("…")}`): un valor de dict dentro de un lambda.
Media traducción es peor que ninguna — la mitad cambiaría de idioma y la otra no.

## Lo que NO se toca

⚠️ Las OPCIONES del radio de fase (`"📝 Survey data"` / `"📊 Resultados e
informes"`) son el DATO: se guardan en `survey_fase` y se comparan en dos sitios.
Traducirlas dejaría las dos ramas MUERTAS (el fallo de v442 con corte de rieles).
Solo cambia el display del `format_func`.

⚠️ Y `_GRUPOS_PARAM` es constante de MÓDULO: `t()` ahí se congela al importar
(seis veces ya). El texto va en BASE y `t()` se aplica al pintar.
"""
import ast
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
CORE = BASE / "core"
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


DISPLAY = {"write", "markdown", "caption", "info", "success", "error", "warning",
           "title", "header", "subheader", "button", "text", "metric", "toast",
           "radio", "selectbox", "checkbox", "text_input", "number_input",
           "expander", "download_button", "form_submit_button", "multiselect",
           "text_area", "date_input", "time_input", "file_uploader", "slider",
           "toggle", "popover", "exito", "aviso"}


def _envuelto(n):
    return isinstance(n, ast.Call) and (
        getattr(n.func, "id", None) in ("t", "d", "_d", "_etq")
        or getattr(n.func, "attr", None) in ("t", "d", "etiqueta"))


def ternarios_sueltos():
    """Ramas literales de un ternario que llega a una función de display."""
    out = []
    for f in sorted(BASE.rglob("*.py")):
        if ".venv" in str(f):
            continue
        try:
            arb = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for n in ast.walk(arb):
            if not isinstance(n, ast.Call):
                continue
            nom = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            if nom not in DISPLAY:
                continue
            rec = getattr(getattr(n.func, "value", None), "id", "")
            if rec not in ("st", "flash", "c1", "c2", "c3", "col", "cols", ""):
                continue
            args = list(n.args) + [k.value for k in n.keywords
                                   if k.arg in ("label", "help", "body", "text")]
            for a in args:
                if isinstance(a, ast.IfExp):
                    for rama in (a.body, a.orelse):
                        if (isinstance(rama, ast.Constant)
                                and isinstance(rama.value, str)
                                and len(rama.value) > 12):
                            out.append((f.name, a.lineno, rama.value[:60]))
    return out


print("== 1. La octava red: ternarios de display ==")
_t = ternarios_sueltos()
for h in _t:
    print(f"     {h[0]}:{h[1]}  {h[2]!r}")
chk(not _t, f"ninguna rama de ternario llega a display sin t() (halladas: {len(_t)})")

# ⚠️ La red se VALIDA contra un caso construido antes de creerse su cero
# (trampa nº12): un «0» de una sonda que no sabe ver el caso no significa nada.
print("\n== 2. ¿La red sabe ver el caso conocido-bueno? ==")
_sonda = ast.parse('st.info("texto largo de prueba aqui" if x else "otro texto largo aqui")')
_visto = []
for n in ast.walk(_sonda):
    if isinstance(n, ast.Call) and getattr(n.func, "attr", None) in DISPLAY:
        for a in n.args:
            if isinstance(a, ast.IfExp):
                _visto = [a.body, a.orelse]
chk(len(_visto) == 2, "la red detecta un ternario construido a propósito (2 ramas)")

print("\n== 3. El format_func de la fase: las DOS ramas traducidas ==")
_su = (CORE / "survey_ui.py").read_text(encoding="utf-8")
_arb = ast.parse(_su)
_fn = next(n for n in ast.walk(_arb)
           if isinstance(n, ast.FunctionDef) and n.name == "render_survey_tab")
_lam = [n for n in ast.walk(_fn) if isinstance(n, ast.Lambda)]
_dicts = [d for lam in _lam for d in ast.walk(lam) if isinstance(d, ast.Dict)]
_crudas = [v.value[:40] for d in _dicts for v in d.values
           if isinstance(v, ast.Constant) and isinstance(v.value, str) and len(v.value) > 8]
chk(not _crudas, f"ningún valor de dict en un lambda de survey_ui sin t() ({_crudas})")

print("\n== 4. Las OPCIONES de la fase NO se traducen (o la rama queda muerta) ==")
chk('_FASE_DATOS, _FASE_RES = "📝 Survey data", "📊 Resultados e informes"' in _su,
    "las opciones del radio de fase conservan su valor (se comparan en 2 sitios)")
chk(_su.count("_fase == _FASE_DATOS") == 1 and _su.count('"_fase_pending"] = _FASE_RES') == 1,
    "las dos comparaciones siguen casando con las constantes")

print("\n== 5. _GRUPOS_PARAM: texto BASE en la constante, t() al PINTAR ==")
_gp = next(n for n in _arb.body
           if isinstance(n, ast.Assign)
           and getattr(n.targets[0], "id", None) == "_GRUPOS_PARAM")
_tit = [e.elts[0].value for e in _gp.value.elts]
chk(all(":material/" in x for x in _tit), f"los 6 títulos conservan su icono ({len(_tit)})")
# ⚠️ Afirmación POSITIVA (lección v438/v439): que el INGLÉS esperado ESTÉ, en vez
# de que el español no esté — el detector de idioma es ciego a «Hueco», «Cabina»,
# «Frontal», «Laterales» y «Contrapeso», que no llevan acento ni terminación
# marcada. Con la red morfológica de v450 tampoco se veían: por eso van a mano.
for esp in ("Shaft", "Car", "Door / sill", "Front", "Sides", "Counterweight"):
    chk(any(x.endswith(esp) for x in _tit), f"el grupo «{esp}» está en inglés")
chk(not any(isinstance(n, ast.Call) for e in _gp.value.elts
            for n in ast.walk(e.elts[0])),
    "⚠️ la constante NO llama a t() (se congelaría al importar — van seis veces)")
chk('st.markdown(f"**{t(_titulo)}**")' in _su,
    "la traducción se aplica al PINTAR, no al importar")

print("\n== 6. Compila y los nombres se resuelven ==")
for m in ("survey_ui.py", "projects_ui.py", "roster_ui.py"):
    try:
        ast.parse((CORE / m).read_text(encoding="utf-8"))
        chk(True, f"{m} compila")
    except SyntaxError as e:
        chk(False, f"{m} NO compila: {e}")

# `t` tiene que estar importado a NIVEL DE MÓDULO en los tres (regla v342/v366:
# ámbito, no presencia — un import dentro de OTRA función da un OK en falso).
for m in ("survey_ui.py", "projects_ui.py", "roster_ui.py"):
    _a = ast.parse((CORE / m).read_text(encoding="utf-8"))
    _imp = any(isinstance(n, ast.ImportFrom) and any(al.name == "t" or al.asname == "t"
                                                     for al in n.names)
               for n in _a.body)
    chk(_imp, f"{m} importa `t` a nivel de módulo")



# ══════════════════════════════════════════════════════════════════════════
# LA DÉCIMA RED — un widget cuyas OPCIONES son literales y NO tiene
# `format_func` pinta esas opciones CRUDAS.
#
# ⚠️ En esta app las opciones de un widget casi nunca son etiquetas: son el
# DATO (el ID con emoji que compara `sub ==`, el valor que se guarda en la
# hoja, la clave que indexa un dict). Traducirlas deja la rama MUERTA (v442).
# Así que la única salida es el `format_func` — y si falta, el usuario ve el
# dato en crudo. Es lo que pasaba en Localizaciones, cuyas 5 sub-secciones se
# pintaban «Equipo · Gastos · Pre-Start · Archivos · Datos» en español.
#
# Ninguna de las nueve redes anteriores lo veía: la de POSICIÓN mira el
# argumento (aquí es una LISTA), y las de idioma no disparan sobre «Datos»,
# «Equipo» o «proyecto», que no llevan acento ni terminación marcada.
# ══════════════════════════════════════════════════════════════════════════
WID = {"radio", "selectbox", "segmented_control", "pills", "multiselect"}
# Exentos, con su razón — no por comodidad:
EXENTOS = {
    ("rail_cut_ui.py", "Above the FFL (subtract)"),   # ya está en inglés
    ("survey_ui.py", "Schindler"),                    # nombre propio de la marca
}

print("\n== 7. La décima red: opciones crudas por falta de format_func ==")
_crudos = []
for f in sorted(CORE.glob("*.py")):
    _a = ast.parse(f.read_text(encoding="utf-8"))
    for c in ast.walk(_a):
        if not isinstance(c, ast.Call) or getattr(c.func, "attr", None) not in WID:
            continue
        if any(k.arg == "format_func" for k in c.keywords):
            continue
        ops = None
        for a in list(c.args)[1:2]:
            if isinstance(a, ast.List):
                ops = [e.value for e in a.elts
                       if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if ops and any(len(o) > 2 for o in ops):
            if (f.name, ops[0]) in EXENTOS:
                continue
            _crudos.append((f.name, c.lineno, ops[:5]))
for h in _crudos:
    print(f"     {h[0]}:{h[1]}  {h[2]}")
chk(not _crudos, f"ningún widget pinta sus opciones crudas ({len(_crudos)})")

print("\n== 8. Las opciones de esos widgets NO se tocaron ==")
_pu = (CORE / "projects_ui.py").read_text(encoding="utf-8")
chk('["📊 Estado", "✏️ Datos", "💰 Costos", "📎 Archivos"]' in _pu,
    "las 4 sub-secciones del detalle conservan su ID (deep-links + matching)")
chk('["👥 Equipo", "💰 Gastos", "🦺 Pre-Start", "📎 Archivos", "✏️ Datos"]' in _pu,
    "las 5 de Localizaciones conservan su ID")
chk('_sec == "👥 Equipo"' in _pu and '_sec == "✏️ Datos"' in _pu,
    "las comparaciones siguen casando (si no, la rama queda MUERTA)")
_qu = (CORE / "quotes_ui.py").read_text(encoding="utf-8")
chk('["Instalación", "Delivery", "Ripout", "Otro"]' in _qu,
    "⚠️ el tipo de proyecto NO se traduce: se GUARDA en `Proyectos.Tipo`")
chk("format_func=_etq" in _qu,
    "…y se muestra con `etiqueta()`, que es quien sabe traducir un valor de negocio")

print("\n== 9. El detalle de proyecto, sin español a medias ==")
_ff_crudos = []
for _f in sorted(CORE.glob("*_ui.py")):
    _a2 = ast.parse(_f.read_text(encoding="utf-8"))
    for _c in ast.walk(_a2):
        if not isinstance(_c, ast.Call):
            continue
        for _k in _c.keywords:
            if _k.arg != "format_func" or not isinstance(_k.value, ast.Lambda):
                continue
            # ⚠️ El patron `t({...}.get(o, o))` es CORRECTO: el dict lleva literales
            # pero su RESULTADO pasa por t(). Marcarlo seria un falso positivo, y un
            # chequeo que grita sobre lo ya traducido acaba ignorandose entero (v450).
            _envueltos = set()
            for _n2 in ast.walk(_k.value):
                if (isinstance(_n2, ast.Call)
                        and getattr(_n2.func, "id", None) in ("t", "d", "_d", "_etq")):
                    for _sub in ast.walk(_n2):
                        if isinstance(_sub, ast.Dict):
                            _envueltos.add(id(_sub))
            for _dd in ast.walk(_k.value):
                if not isinstance(_dd, ast.Dict) or id(_dd) in _envueltos:
                    continue
                for _v in _dd.values:
                    # ⚠️ Un valor que es SOLO un icono Material no tiene texto que
                    # traducir: contarlo seria ruido, y una red que grita sin motivo
                    # acaba ignorandose (la leccion del lexico corto en v450).
                    _limpio = re.sub(r":material/[a-z_]+:", "", str(getattr(_v, "value", ""))).strip()
                    if (isinstance(_v, ast.Constant) and isinstance(_v.value, str)
                            and len(_limpio) > 2):
                        _ff_crudos.append((_f.name, _c.lineno, _v.value[:45]))
for _h in _ff_crudos:
    print(f"     {_h[0]}:{_h[1]}  {_h[2]!r}")
chk(not _ff_crudos,
    f"ningún valor de dict de un format_func es un literal suelto ({len(_ff_crudos)})")
chk("t('progress')" in _pu, "«avance» pasa a `t('progress')`")
chk('f"Vas' not in _pu, "el titular ya no empieza por «Vas» (iba mezclado con «You are»)")



# ══════════════════════════════════════════════════════════════════════════
# LA UNDÉCIMA red — cabeceras de tabla escritas A MANO en HTML.
#
# `tabla.cfg()` (v450) solo alcanza a `st.dataframe`/`st.data_editor`. Las
# tablas que esta app dibuja como HTML —el tablero del roster y la vista de
# disponibilidad, que son HTML porque hay que colorear la celda por valor y
# `st.dataframe` no sabe— llevan su `<th>` escrito a mano, y ahí no llega
# ninguna de las diez redes: el literal vive dentro de una f-string de HTML.
# Se veía «Persona» en la cabecera de la tabla de Libres.
# ══════════════════════════════════════════════════════════════════════════
print(chr(10) + "== 10. La undécima red: cabeceras <th> escritas a mano ==")
_TH = re.compile(r"<th[^>]*>([^<{]{2,40})</th>")
_ths = []
for _f in sorted(CORE.glob("*.py")):
    _a3 = ast.parse(_f.read_text(encoding="utf-8"))
    for _n3 in ast.walk(_a3):
        if isinstance(_n3, ast.Constant) and isinstance(_n3.value, str):
            for _m in _TH.finditer(_n3.value):
                if _m.group(1).strip():
                    _ths.append((_f.name, _n3.lineno, _m.group(1).strip()))
for _h in _ths:
    print(f"     {_h[0]}:{_h[1]}  {_h[2]!r}")
chk(not _ths, f"ninguna cabecera <th> con texto literal ({len(_ths)})")
# Afirmación POSITIVA: el inglés esperado tiene que ESTAR (lección v438/v439).
_ru = (CORE / "roster_ui.py").read_text(encoding="utf-8")
chk(_ru.count("t('Person') + '</th>'") == 2,
    "las 2 cabeceras del roster se traducen al PINTAR")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
