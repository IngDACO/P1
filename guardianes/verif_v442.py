"""Guardián de v442 — la TERCERA red del i18n y los VALORES que se muestran.

v441 dejó dos cosas medidas y sin cerrar, y ésta las cierra:

 1. **Etiquetas CORTAS** (2 palabras) dentro de listas de tuplas y f-strings: ni el
    invariante de posición (mira el argumento de `st.*`) ni la red de FRASES (pide 3+
    palabras) las alcanzaban. Eran ~209.
 2. **`i18n.etiqueta()` existía desde v436 y la interfaz NO la usaba**: los estados,
    tipos, roles y categorías se pintaban en español crudo. Es el patrón «se escribe y
    nadie lo lee» de v131/v148.

⚠️ Y la lección más cara de esta tanda: traducir la OPCIÓN de un radio sin traducir la
comparación deja la rama MUERTA sin dar ningún error (pasó con el Caso 1 de rieles). Eso
lo vigila `verif_ramas_muertas.py`, que corre aparte.
"""
import ast
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


UI = sorted(p.stem for p in (RAIZ / "core").glob("*_ui.py"))

# ── 1 ────────────────────────────────────────────────────────────
sec("1. TERCERA RED: etiquetas CORTAS sin envolver")
from barre_frases import frases                                   # noqa: E402
from barre_cortas import ES, _sin                                 # noqa: E402

# Exclusiones DELIBERADAS, cada una con su razón. No son «lo que no dio tiempo».
EXCL = {
    "🗺 Ruta del día", "📊 Su trabajo",      # IDs de sub-pestaña (v232): los compara `sub ==`
    "En progreso", "En pausa", "⏸ En pausa",  # estados GUARDADOS en la hoja
    "por vencer",                            # lo devuelve `credentials.status()`
}


def _cortas_es(mod):
    rel = "app.py" if mod == "app" else f"core/{mod}.py"
    out = []
    for ln, s in sorted(set(frases(RAIZ / rel, minimo=2))):
        if (s in EXCL or s.lstrip().startswith("<style>") or "/*" in s
                or "function f(s)" in s):
            continue
        # ⚠️ `Login`, `Grupos`, `Rieles` son NOMBRES DE HOJA citados en un texto inglés:
        # no son español que quede por traducir.
        if re.search(r"`(Login|Grupos|Rieles)`", s):
            continue
        # ⚠️ En un fragmento HTML, `background:#eaf3de` aporta la «palabra» «de» y la
        # da por española: un falso positivo del propio chequeo. Se quitan los colores
        # hexadecimales y los nombres de propiedad CSS antes de mirar.
        _limpio = re.sub(r"#[0-9a-fA-F]{3,8}", " ", s)
        _limpio = re.sub(r"<[^>]*>", " ", _limpio)
        if set(re.findall(r"[a-záéíóúñü]+", _sin(_limpio))) & ES:
            out.append(f"{mod}:{ln} {s[:44]!r}")
    return out


_sos = []
for m in UI + ["app"]:
    _sos += _cortas_es(m)
chk(f"0 etiquetas cortas en español en los {len(UI) + 1} módulos", not _sos,
    f"{len(_sos)}: " + str(_sos[:5]))
# ⚠️ Un «0» no vale si la red no sabe ver el caso malo: se comprueba con uno construido.
_prueba = {"Mano de obra (estructura)", "— elige el proyecto —", "sin asignar"}
chk("...y la red SABE ver una etiqueta corta española",
    all(set(re.findall(r"[a-záéíóúñü]+", _sin(p))) & ES for p in _prueba))

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Los VALORES de dato se MUESTRAN traducidos (i18n.etiqueta)")
from core import i18n                                             # noqa: E402
chk("etiqueta() traduce un estado", i18n.etiqueta("En progreso") == "In progress")
chk("...y deja pasar lo que no conoce (no inventa)",
    i18n.etiqueta("PRJ-0007") == "PRJ-0007")

# los módulos que pintan un valor tienen que tener la FUNCIÓN a mano
import importlib                                                  # noqa: E402
CON_ETQ = ["projects_ui", "home_ui", "auth_ui", "payroll_ui", "catalogo_ui",
           "inventory_ui"]
for m in CON_ETQ:
    tr = ast.parse((RAIZ / f"core/{m}.py").read_text(encoding="utf-8"))
    imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
              and any(a.name == "etiqueta" for a in x.names) for x in tr.body)
    chk(f"{m:14} importa `etiqueta` a nivel de módulo", imp)

# ⚠️ Y NADIE puede usar `_etq` como variable: Python marca el nombre local en el ámbito
# ENTERO, así que un `_etq = {...}` convierte la llamada de más abajo en «'dict' object is
# not callable». Es el fallo de v437/v439/v440 y volvió a pasar en `render_nominas`.
malos = []
for f in sorted((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"]:
    tr = ast.parse(f.read_text(encoding="utf-8"))
    for fn in ast.walk(tr):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        cuerpo = []
        for h in fn.body:
            pila = [h]
            while pila:
                x = pila.pop()
                cuerpo.append(x)
                for c in ast.iter_child_nodes(x):
                    if not isinstance(c, (ast.Lambda, ast.FunctionDef,
                                          ast.AsyncFunctionDef, ast.ClassDef)):
                        pila.append(c)
        comp = {id(nn) for x in cuerpo for g in (getattr(x, "generators", []) or [])
                for nn in ast.walk(g.target) if isinstance(nn, ast.Name)}
        if any(isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)
               and x.id == "_etq" and id(x) not in comp for x in cuerpo):
            malos.append(f"{f.name}:{fn.lineno} {fn.name}")
chk("ninguna función usa `_etq` como variable (taparía la función)", not malos,
    str(malos))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. El DATO sigue intacto: lo que se guarda no se tradujo")
_pu = (RAIZ / "core/projects_ui.py").read_text(encoding="utf-8")
from core import projects as P                                    # noqa: E402
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado. Hasta v468 esto exigía que el estado
# siguiera en ESPAÑOL, porque el dato vive en la hoja y traducirlo deja de casar en
# silencio. v469 lo migra a inglés A PROPÓSITO, así que la afirmación cambia de objeto
# pero NO de principio: lo guardado y lo mostrado no pueden divergir. Se exigen ahora
# las TRES piezas que lo garantizan.
from core import valores as VAL                                   # noqa: E402
chk("el estado que se GUARDA es el canónico (inglés)",
    "On hold" in P.ESTADOS_MANUAL and "In progress" == P.derive_estado(50, "", ""),
    f"{P.ESTADOS_MANUAL} · {P.derive_estado(50, '', '')}")
# ⚠️ La capa de compatibilidad es lo que permite desplegar ANTES de migrar la hoja:
# una fila que todavía diga «En pausa» tiene que leerse como «On hold», o el estado
# manual dejaría de encontrarse durante toda la ventana entre el deploy y la migración.
_mal = [(v, VAL.canon(v)) for v in ("En pausa", "Cancelado", "Archivado")
        if VAL.canon(v) not in P.ESTADOS_MANUAL]
chk("...y el valor VIEJO de la hoja sigue casando (canon lo traduce al leer)",
    not _mal and VAL.canon("En progreso") == "In progress", str(_mal))
# ⚠️ El canónico NO tiene que estar en `VALORES`: ese mapa es ahora el LEGADO del
# lado del display (viejo→inglés). Lo que no puede pasar es que `etiqueta()` le cambie
# el texto a un valor que YA es canónico — eso mostraría una cosa y guardaría otra.
_mut = [e for e in P.ESTADOS_MANUAL if e and i18n.etiqueta(e) != e]
chk("...y `etiqueta()` no muta un estado que ya es canónico", not _mut, str(_mut))
# el selectbox que GUARDA el estado enseña la etiqueta con format_func, no la traduce
# ⚠️ REANCLADO en v487: comparaba el TEXTO literal «P.ESTADOS_MANUAL, format_func=_etq,»
# y v487 pasa las opciones por `ui.opciones_con_actual` (para no des-archivar una obra
# en silencio), asi que llegan en `_ems`. Lo que esta regla protege no es la forma: es
# que el desplegable que GUARDA el estado muestre la etiqueta con `format_func` y NO
# traduzca las OPCIONES (guardaria el texto traducido y dejaria la rama muerta, v442).
import ast as _ast442
_sel442 = [n for n in _ast442.walk(_ast442.parse(_pu)) if isinstance(n, _ast442.Call)
           and getattr(n.func, 'attr', '') == 'selectbox' and n.args
           and 'Manual status (override)' in _ast442.unparse(n.args[0])]
_trad442 = ('t', 'd', 'etiqueta', '_etq')
# ⚠️ Las opciones llegan por VARIABLE (`_ems`): mirar solo el nombre dejaba pasar una
# traduccion hecha en su asignacion. Se resuelve (tambien `_ems, _emi = ...`), v471.
_arb442 = _ast442.parse(_pu)


def _valores442(nodo):
    if not isinstance(nodo, _ast442.Name):
        return [nodo]
    out = [nodo]
    for a in _ast442.walk(_arb442):
        if isinstance(a, _ast442.Assign):
            for tg in a.targets:
                nombres = [tg] if isinstance(tg, _ast442.Name) else list(getattr(tg, 'elts', []))
                if any(isinstance(x, _ast442.Name) and x.id == nodo.id for x in nombres):
                    out.append(a.value)
    return out


_ok442 = bool(_sel442) and all(
    any(k.arg == 'format_func' for k in n.keywords) and len(n.args) > 1
    and not any(isinstance(c, _ast442.Call)
                and (getattr(c.func, 'id', None) or getattr(c.func, 'attr', '')) in _trad442
                for v in _valores442(n.args[1]) for c in _ast442.walk(v))
    for n in _sel442)
chk("el selector de estado manual usa format_func (no traduce la opción)", _ok442,
    "selectbox encontrados: %d" % len(_sel442))

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
