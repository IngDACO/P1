"""Guardián de v435 — el motor de idiomas (F0 de la traducción a inglés).

Lo que protege, por orden de gravedad:

 1. ⚠️ **Un VALOR DE DATO nunca puede pasar por `t()`.** `"En progreso"`, `"aprobada"`
    y `"campo"` viven así en Google Sheets y se comparan por igualdad en 387 sitios;
    traducirlos NO da error — simplemente deja de encontrarse ningún proyecto
    completado. Es el fallo silencioso que todo esto existe para evitar.
 2. ⚠️ **`t()` no puede recibir un f-string.** Se evalúa antes de llegar, así que la
    cadena ya llevaría el número dentro y no casaría con ninguna entrada del
    diccionario: quedaría en inglés para siempre y nadie sabría por qué.
 3. El idioma vive en la SESIÓN, no en un global (un global se comparte por proceso
    y le cambiaría el idioma a otra persona — la lección de v378/v379).
 4. `i18n` es módulo HOJA: sin ciclos.
 5. Un diccionario incompleto —o roto— NO puede dejar la pantalla en blanco.
 6. F0 no cambia NADA de lo que se ve hoy.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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


def arbol(rel):
    return ast.parse((RAIZ / rel).read_text(encoding="utf-8"))


def fn(tree, nom):
    return next((x for x in ast.walk(tree)
                 if isinstance(x, ast.FunctionDef) and x.name == nom), None)


# ── 1 ────────────────────────────────────────────────────────────
sec("1. Un VALOR DE DATO no puede pasar por t() (el fallo silencioso)")
from core import i18n                                            # noqa: E402

_val = set(i18n.VALORES)
malos = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and (
                (isinstance(x.func, ast.Name) and x.func.id == "t")
                or (isinstance(x.func, ast.Attribute) and x.func.attr == "t"))):
            continue
        if x.args and isinstance(x.args[0], ast.Constant) \
                and isinstance(x.args[0].value, str) and x.args[0].value in _val:
            malos.append(f"{f.name}:{x.lineno} → {x.args[0].value!r}")
chk("ninguna llamada a t() lleva un valor de negocio", not malos, str(malos))
chk("el chequeo NO corre en vacío: hay valores que vigilar", len(_val) >= 30,
    f"{len(_val)} valores")

# los valores del mapa son EXACTAMENTE los que el código compara
_comp = set()
for f in sorted((RAIZ / "core").glob("*.py")):
    tr = ast.parse(f.read_text(encoding="utf-8"))
    for x in ast.walk(tr):
        if isinstance(x, ast.Compare):
            for c in x.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    _comp.add(c.value)
_clave = {"Completado", "En progreso", "Planificado", "aprobada", "pendiente",
          "campo", "administrador", "vigente", "vencido", "anulada"}
_faltan = [v for v in _clave if v not in _val]
chk("los estados que el código compara están mapeados", not _faltan, str(_faltan))
# ⚠️ El umbral estaba mal calibrado: pedía 8 comparaciones LITERALES y solo hay 5,
# porque el repo compara contra CONSTANTES (`APROBADA`, `PENDIENTE`) — que es mejor
# práctica. Lo que hay que afirmar es que esos valores siguen siendo el TEXTO
# ALMACENADO, esté en un literal suelto o detrás de una constante.
_lits = set()
for f in sorted((RAIZ / "core").glob("*.py")):
    for x in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            _lits.add(x.value)
_perdidos = [v for v in _clave if v not in _lits]
chk("esos valores SIGUEN escritos en español en el código (no se migró la hoja)",
    not _perdidos, str(_perdidos))
chk("...y al menos algunos se comparan directamente", len(_clave & _comp) >= 3,
    f"{len(_clave & _comp)}")

# ── 2 ────────────────────────────────────────────────────────────
sec("2. t() no puede recibir un f-string ni una concatenación")
fs = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for x in ast.walk(tr):
        if not (isinstance(x, ast.Call) and (
                (isinstance(x.func, ast.Name) and x.func.id == "t")
                or (isinstance(x.func, ast.Attribute) and x.func.attr == "t"))):
            continue
        if x.args and isinstance(x.args[0], (ast.JoinedStr, ast.BinOp)):
            fs.append(f"{f.name}:{x.lineno}")
chk("ningún t() recibe f-string ni suma de cadenas", not fs, str(fs))
chk("...y t() acepta placeholders con nombre",
    i18n.t("Saved {n} rows", n=3) == "Saved 3 rows", i18n.t("Saved {n} rows", n=3))

# ── 3 · 4 ────────────────────────────────────────────────────────
sec("3-4. El idioma vive en la sesión, y el módulo es HOJA")
_i = arbol("core/i18n.py")
_gl = [x for x in ast.walk(fn(_i, "set_idioma")) if isinstance(x, ast.Global)]
chk("`set_idioma` no usa variables globales", not _gl)
chk("el idioma se lee de session_state", "session_state" in ast.unparse(fn(_i, "idioma")))
_imp = set()
for x in _i.body:
    if isinstance(x, (ast.Import, ast.ImportFrom)):
        for a in x.names:
            _imp.add((x.module if isinstance(x, ast.ImportFrom) else a.name).split(".")[0])
chk("i18n solo importa librerías externas (módulo HOJA)",
    not (_imp & {"core"}), str(sorted(_imp)))

# ── 5 ────────────────────────────────────────────────────────────
sec("5. Un diccionario incompleto o roto no rompe la pantalla")
chk("sin traducción devuelve el texto base", i18n.t("Anything at all") == "Anything at all")
chk("texto vacío no revienta", i18n.t("") == "")
_orig = i18n._dic
try:
    i18n._dic = lambda idi: {"Hello {x}": "Hola {y}"}      # placeholder MAL escrito
    i18n.set_idioma("es")
    chk("una traducción con placeholder erróneo NO lanza",
        i18n.t("Hello {x}", x=1) in ("Hola {y}", "Hello {x}"), i18n.t("Hello {x}", x=1))
    i18n._dic = lambda idi: (_ for _ in ()).throw(RuntimeError("boom"))
    chk("un diccionario que revienta al cargarse tampoco",
        i18n.t("Fallback works") == "Fallback works")
finally:
    i18n._dic = _orig
    i18n.set_idioma("en")
chk("...y el idioma vuelve a inglés", i18n.idioma() == "en")

# ── 6 ────────────────────────────────────────────────────────────
sec("6. F0 no cambia NADA de lo que se ve hoy")
chk("en inglés, un estado se MUESTRA traducido",
    i18n.etiqueta("En progreso") == "In progress")
i18n.set_idioma("es")
chk("en español, el dato se muestra tal cual (ya está en español)",
    i18n.etiqueta("En progreso") == "En progreso")
i18n.set_idioma("en")
chk("un valor no mapeado sale tal cual (nombre de obra, nota)",
    i18n.etiqueta("Meriton Zetland — Torre A") == "Meriton Zetland — Torre A")
chk("None / vacío no revienta", i18n.etiqueta(None) == "")
# ⚠️ CADUCADO en v436 y actualizado (regla v385): exigía que NADIE usara el motor —
# cierto en F0, que era solo andamio— y se puso rojo al empezar a traducir en F1, o
# sea **por haber avanzado**. Lo que sigue teniendo sentido proteger es que el motor
# se use SOLO por su interfaz pública: nadie debe tocar `_dic`, `VALORES` ni `_CLAVE`
# desde fuera, porque ahí es donde se pierde el fallback y la separación dato/etiqueta.
_privado = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if f.name == "i18n.py":
        continue
    src = f.read_text(encoding="utf-8")
    for pat in ("i18n._dic", "i18n._CLAVE", "i18n.VALORES["):
        if pat in src:
            _privado.append(f"{f.name} → {pat}")
chk("nadie toca las tripas del motor (solo t/d/etiqueta/set_idioma)",
    not _privado, str(_privado))
from core.lang_es import TEXTOS                                  # noqa: E402
chk("el diccionario español arranca vacío (decisión del usuario)", TEXTOS == {})

# ── 7 ────────────────────────────────────────────────────────────
sec("7. Compila e importa (importar no ejecuta — v378)")
import importlib                                                 # noqa: E402
for m in ("core.i18n", "core.lang_es"):
    try:
        importlib.import_module(m)
        chk(f"importa {m}", True)
    except Exception as e:
        chk(f"importa {m}", False, f"{type(e).__name__}: {e}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
