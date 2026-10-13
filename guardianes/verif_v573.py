# -*- coding: utf-8 -*-
"""v573 · LA SUITE NO TOCA EL CÓDIGO DE LA APP.

Tres guardianes de la suite escribían en `survey_app/core/` para validar sus sondas:
verif_v471 y verif_v463 rompían un módulo EN DISCO y lo restauraban, y verif_v498 creaba
un fichero dentro de `core/`. El contenido volvía igual, pero `quotes_ui.py` salía
«modificado» (CRLF→LF) tras cada suite, y la regla «la suite no toca el árbol; las
baterías sí» era falsa. Ahora validan EN MEMORIA.

Dos redes, con huecos distintos:
  1. ESTÁTICA (esta): ningún guardián de la suite contiene una escritura dirigida al
     árbol de la app.
  2. EN EJECUCIÓN (`run_suite.py`): la huella del código de la app antes y después de
     CADA guardián; si cambia un byte, ese guardián sale en ROJO (validada con un
     guardián falso que reescribía quotes_ui.py: «TOCÓ el código de la app»).
"""
import ast
import glob
import io
import os
import re
import sys

GUAR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("  ok   " + q)
    else:
        fallos.append(q)
        print("  FALLO " + q + (("  -> " + str(det)) if det != "" else ""))


# Lo que apunta al árbol de la app: `core`, `survey_app`, `app.py` o las constantes con
# que los guardianes nombran su raíz.
_APP = re.compile(r"""['"/\\]core['"/\\]|core/|survey_app|app\.py|\bRAIZ\b|\bCORE\b""")
_ESCRIBE_OS = {"remove", "unlink", "replace", "rename", "copy", "copy2", "copyfile", "move"}


def _escrituras(src):
    """[(línea, texto de la ruta)] de las escrituras cuya ruta apunta a la app."""
    t = ast.parse(src)
    asig = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                for nm in [x.id for x in ast.walk(tg) if isinstance(x, ast.Name)]:
                    asig.setdefault(nm, []).append(ast.unparse(n.value))
        # ⚠️ Y las variables de BUCLE: en verif_v471 la ruta era `fich`, de
        # `for etq, fich, … in PRUEBAS`, y la 1ª red no la resolvía (validada contra la
        # versión vieja de v471: no la veía).
        elif isinstance(n, ast.For):
            for nm in [x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)]:
                asig.setdefault(nm, []).append(ast.unparse(n.iter))

    def ruta(e):
        """El texto de la ruta y lo que valen sus nombres, hasta 3 niveles."""
        tx, vistos = ast.unparse(e), set()
        pend = {x.id for x in ast.walk(e) if isinstance(x, ast.Name)}
        for _ in range(3):
            nuevos = set()
            for nm in pend - vistos:
                vistos.add(nm)
                for v in asig.get(nm, []):
                    tx += " " + v
                    nuevos |= set(re.findall(r"[A-Za-z_]\w*", v))
            pend = nuevos
        return tx
    out = []
    for c in ast.walk(t):
        if not isinstance(c, ast.Call):
            continue
        f = c.func
        nombre = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        objetivo = None
        if nombre == "open" and c.args:
            modo = c.args[1] if len(c.args) > 1 else next(
                (k.value for k in c.keywords if k.arg == "mode"), None)
            if isinstance(modo, ast.Constant) and re.search(r"[wax]", str(modo.value)):
                objetivo = c.args[0]
        elif nombre in ("write_text", "write_bytes") and isinstance(f, ast.Attribute):
            objetivo = f.value
        elif nombre in _ESCRIBE_OS and isinstance(f, ast.Attribute) \
                and getattr(f.value, "id", "") in ("os", "shutil") and c.args:
            objetivo = c.args[-1] if f.value.id == "shutil" else c.args[0]
        if objetivo is not None:
            tx = ruta(objetivo)
            if _APP.search(tx):
                out.append((c.lineno, tx[:80]))
    return out


# ⚠️ Trampa 12: la red tiene que VER las tres formas que había (y no ver las buenas)
_MALOS = {
    "rompe y restaura (v471)": 'import io\nf = "core/quotes_ui.py"\n'
                               'io.open(f, "w", encoding="utf-8", newline="").write("x")\n',
    "con RAIZ (v498)": 'import io, os\n_tmp = os.path.join(RAIZ, "core", "_zz.py")\n'
                       'io.open(_tmp, "w", encoding="utf-8").write("x")\nos.remove(_tmp)\n',
    "Path.write_text en core": 'from pathlib import Path\nCORE = Path("x")\n(CORE / "a.py").write_text("x")\n',
    "variable de bucle (v471 de verdad)": 'import io\nPRUEBAS = [("l", "core/quotes_ui.py", "a", "b")]\n'
                                          'for etq, fich, viejo, nuevo in PRUEBAS:\n'
                                          '    io.open(fich, "w", encoding="utf-8").write(nuevo)\n',
}
_BUENOS = {
    "lee core (solo lectura)": 'import io\nio.open("core/quotes_ui.py", encoding="utf-8").read()\n',
    "escribe en guardianes": 'from pathlib import Path\nAQUI = Path(__file__).parent\n'
                             '(AQUI / "_probe.py").write_text("x")\n',
}
chk("la red VE las cuatro formas malas",
    all(_escrituras(s) for s in _MALOS.values()), {k: _escrituras(s) for k, s in _MALOS.items()})
chk("…y no ve las buenas (leer core, escribir en guardianes)",
    not any(_escrituras(s) for s in _BUENOS.values()), {k: _escrituras(s) for k, s in _BUENOS.items()})

_suite = sorted(p for p in glob.glob(os.path.join(GUAR, "*.py"))
                if os.path.basename(p).startswith(("verif_", "check_")))
_mal = {}
for p in _suite:
    if os.path.basename(p) == "verif_v573.py":          # sus casos malos son TEXTO
        continue
    try:
        _e = _escrituras(io.open(p, encoding="utf-8").read())
    except SyntaxError:
        continue
    if _e:
        _mal[os.path.basename(p)] = _e
chk("⚠️ ningún guardián de la suite escribe en el árbol de la app (%d mirados)" % len(_suite),
    len(_suite) > 150 and not _mal, _mal)

# La red en ejecución sigue puesta en el runner
_rs = ast.parse(io.open(os.path.join(GUAR, "run_suite.py"), encoding="utf-8").read())
_hu = [n for n in ast.walk(_rs) if isinstance(n, ast.FunctionDef) and n.name == "_huella"]
_bucle = [n for n in _rs.body if isinstance(n, ast.For)]
_llam = [c for b in _bucle for c in ast.walk(b) if isinstance(c, ast.Call)
         and getattr(c.func, "id", "") == "_huella"]
chk("run_suite.py toma la huella del código de la app ANTES y DESPUÉS de cada guardián",
    bool(_hu) and len(_llam) == 2, (len(_hu), len(_llam)))

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
