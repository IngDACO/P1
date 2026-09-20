# -*- coding: utf-8 -*-
"""La suite puede CORRER: ningún guardián importa algo que no está (20/09/2026).

Por qué existe: al traer la suite al repo se clasificaron los ficheros por su nombre
(`verif_`, `check_`, `romper_`…) y ocho módulos auxiliares —`i18n_tool`, los `barre_*`,
`fixture_survey`, `riesgo_claves`— se fueron a `sueltos/` por no encajar en ese patrón.
Catorce guardianes dejaron de importar y la suite los reportó como **14 rojos**, que es
exactamente lo que parece una regresión grande y no lo era.

Un guardián que no puede ni importarse no dice nada de lo que vigila, y se disfraza de
código roto. Esta red separa las dos cosas antes de que nadie se asuste: el fallo apunta
al módulo que falta, no al código de la app.

⚠️ Mira SOLO lo que es resoluble estáticamente. No importa nada (importar ejecuta, y la
suite ya se encarga de ejecutar cada guardián por su cuenta).
"""
import ast
import importlib.util
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = pathlib.Path(__file__).resolve().parent
APP = pathlib.Path("C:/Users/diego/P1/survey_app")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def importados(src: str) -> set:
    """Los módulos de primer nivel que un fichero importa."""
    out = set()
    try:
        tr = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tr):
        if isinstance(n, ast.Import):
            out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            out.add(n.module.split(".")[0])
    return out


def resoluble(m: str, vecinos: set) -> bool:
    """¿Se puede resolver ese nombre desde la carpeta de la suite?"""
    if m in vecinos:                       # otro fichero de la propia carpeta
        return True
    if m == "core":                        # los módulos de la app (cwd = survey_app)
        return (APP / "core").is_dir()
    if m in sys.builtin_module_names:
        return True
    try:
        return importlib.util.find_spec(m) is not None
    except Exception:
        return False


VECINOS = {p.stem for p in AQUI.glob("*.py")}
GUARDIANES = sorted(p for p in AQUI.glob("*.py")
                    if p.name.startswith(("verif_", "check_")))

print("\n[1] la suite entera se puede importar")
ck("hay guardianes que mirar", len(GUARDIANES) > 100, True)

rotos = {}
for p in GUARDIANES:
    src = p.read_text(encoding="utf-8", errors="replace")
    faltan = sorted(m for m in importados(src) if not resoluble(m, VECINOS))
    if faltan:
        rotos[p.name] = faltan

ck("⚠️ ningún guardián importa algo que no está", rotos, {})
if rotos:
    for g, ms in sorted(rotos.items()):
        print("        %s -> %s" % (g, ", ".join(ms)))

print("\n[2] la red sabe ver el caso conocido-malo")
# ⚠️ Un «0 roto» no vale nada hasta demostrar que la sonda sabe detectar uno (nº12).
ck("detecta un import inexistente",
   sorted(m for m in importados("import modulo_que_no_existe_xyz\n")
          if not resoluble(m, VECINOS)),
   ["modulo_que_no_existe_xyz"])
ck("...y no denuncia a un vecino de la carpeta",
   [m for m in importados("import run_suite\n") if not resoluble(m, VECINOS)], [])
ck("...ni a core, que vive en la app",
   [m for m in importados("from core import projects\n") if not resoluble(m, VECINOS)], [])

print("\n[3] los auxiliares que la suite necesita están con ella")
# Los ocho que el traslado se dejó fuera. Si alguien los vuelve a mover, salta aquí.
for m in ("i18n_tool", "barre_frases", "barre_cortas", "barre_t_modulo",
          "fixture_survey", "riesgo_claves"):
    ck("«%s» está junto a los guardianes" % m, (AQUI / (m + ".py")).is_file(), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
