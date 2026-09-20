# -*- coding: utf-8 -*-
"""Guardián de v443 — la CUARTA red del i18n: la f-string ENTERA.

⚠️ Las tres redes de v441/v442 miran cadenas COMPLETAS, y una f-string no lo es: es
una lista de trozos. Por eso se colaron dos formas que ninguna sabía ver:

  1. **Fragmento de UNA palabra** — `f"{g['alarmas']} alarmas"`. La red de frases pide
     3+ palabras y la de cortas 2, así que un trozo de una sola pasa por delante. Y no
     se puede envolver en `t()`: es un trozo de f-string, no una cadena.
  2. **f-string A MEDIO TRADUCIR** — `f"Collected {x} de {y}"`, `f"Nobody free on {d}
     en {a}–{b}"`, `f"Guardado como **{id}** en {obra}"`. Cada trozo por separado no
     parece nada; el texto solo aparece al CONCATENARLOS.

Es la trampa nº30 otra vez, con su corolario incómodo: cada red nueva descubre una
bolsa nueva, y un «0» solo vale para la forma que esa red sabe ver.

+ el chequeo que faltaba y que habría cazado un NameError en producción: usar `d()`
en un módulo que solo importa `t` (el fallo de v423 con `theme`).
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

from barre_fstr_mixto import mixtas                                # noqa: E402
from barre_cortas import ES, _sin                                  # noqa: E402

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


UI = sorted(list((RAIZ / "core").glob("*_ui.py"))) + [RAIZ / "app.py"]

# ── 1 ────────────────────────────────────────────────────────────
sec("1. CUARTA RED: ninguna f-string de interfaz a medio traducir")

# Exclusiones DELIBERADAS, cada una con su razón. No son «lo que no dio tiempo».
EXCL_FRAG = {
    # ⚠️ `Elevador` es la columna del EDITOR DE ENTRADA, y el `_snapshot` de v148 la
    # guarda con su nombre en `DatosJSON`. En la hoja real, `CAL-0002` ya tiene una
    # con esa columna: renombrarla rompería «reabrir el cálculo». Es DATO.
    "Elevador",
    "%Y%m%d",                       # formato de fecha: la «y» no es española
}


def _excluida(txt):
    if any(x in txt for x in EXCL_FRAG):
        return True
    # bloques CSS/HTML sueltos: no son pantalla
    return txt.lstrip().startswith("<") or "font-family" in txt or "display:flex" in txt


_sos = []
for f in UI:
    for ln, s in sorted(set(mixtas(f))):
        if not _excluida(s):
            _sos.append(f"{f.name}:{ln} {s[:44]!r}")
chk(f"0 f-strings con español en los {len(UI)} módulos de interfaz", not _sos,
    f"{len(_sos)}: " + str(_sos[:5]))

# ⚠️ Un «0» no vale si la red no sabe ver el caso malo (trampa nº12): se comprueba
# con uno CONSTRUIDO, no confiando en que el barrido esté bien apuntado.
_prueba = Path(AQUI / "_probe_v443.py")
_prueba.write_text(
    'x = 1\ny = f"Collected {x} de {x}"\nz = f"{x} alarmas"\n', encoding="utf-8")
try:
    _vistos = {s for _, s in mixtas(_prueba)}
    chk("...y la red SABE ver una f-string a medio traducir",
        any("de" in s for s in _vistos) and any("alarmas" in s for s in _vistos),
        str(_vistos))
finally:
    _prueba.unlink(missing_ok=True)

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Nadie usa `t`/`d`/`_etq` sin tenerlo a mano")
MOTOR = {"t", "d", "_d", "_etq"}


def _disponibles(tr):
    """import de i18n a NIVEL DE MÓDULO + def propio + cualquier import local.

    ⚠️ Las tres formas cuentan: `roster_ui` define su propio `_etq(staff, grupo)`
    (v413) y hace `from datetime import date as _d` dentro de una función. Acusarlos
    me habría llevado a «arreglar» código sano (regla v385).
    ⚠️ Y el import de i18n se busca en `tr.body`, sin descender a los `def`: ahí es
    donde el chequeo se autoengaña (v342/v366).
    """
    out = set()
    for x in tr.body:
        if isinstance(x, ast.ImportFrom) and (x.module or "").endswith("i18n"):
            out |= {a.asname or a.name for a in x.names}
    for x in ast.walk(tr):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name in MOTOR:
            out.add(x.name)
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            out |= {(a.asname or a.name) for a in x.names if (a.asname or a.name) in MOTOR}
    return out


_faltan, _mirados = [], 0
for f in sorted(list((RAIZ / "core").glob("*.py"))) + [RAIZ / "app.py"]:
    tr = ast.parse(f.read_text(encoding="utf-8"))
    usos = {x.func.id: x.lineno for x in ast.walk(tr)
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
            and x.func.id in MOTOR}
    if not usos:
        continue
    _mirados += 1
    disp = _disponibles(tr)
    _faltan += [f"{f.name}:{ln} `{k}`" for k, ln in usos.items() if k not in disp]
chk(f"los {_mirados} módulos que usan el motor lo tienen importado", not _faltan,
    str(_faltan))
chk("...y el chequeo miró algo (un 0 sobre 0 módulos no es un aprobado)",
    _mirados > 20, str(_mirados))

# ── 3 ────────────────────────────────────────────────────────────
sec("3. El DATO sigue intacto: la columna del editor no se tradujo")
_rc = (RAIZ / "core/rail_cut_ui.py").read_text(encoding="utf-8")
_pl = (RAIZ / "core/plumb_ui.py").read_text(encoding="utf-8")
# ⚠️ La que se LEE de vuelta (`in_edit[...]`) y la que se ESCRIBE tienen que ser la
# MISMA: media traducción deja la lectura buscando una columna que ya no existe.
chk("rieles: la matriz de entrada sigue con la columna `Elevador`",
    'in_edit[f"Elevador {i+1}"]' in _rc
    and 'cols_expected = ["Riel"] + [f"Elevador {i+1}"' in _rc)
chk("plomada: el editor de BSR sigue con la columna `Elevador`",
    '"Elevador": [f"Elevador {i+1}"' in _pl and 'disabled=["Elevador"]' in _pl)
# y la tabla de RESULTADO sí se tradujo (esa va al PDF que se lleva a obra)
# ⚠️ Se cuentan las DOS (Caso 1 y Caso 2) y se exige que no quede ninguna en
# español. Comprobar PRESENCIA dejaba pasar romper una sola —la otra seguía
# casando— y una traducción PARCIAL es la peor variante: unos sitios leen la
# clave vieja y otros la nueva (lección de v439). Lo destapó la rotura, no leerlo.
chk("...pero las DOS tablas de RESULTADO van en inglés (viajan al PDF de obra)",
    _rc.count('_filas = [{d("Lift"): i + 1') == 2
    and '_filas = [{"Elevador"' not in _rc,
    f'{_rc.count(chr(95) + "filas = [{d(" + chr(34) + "Lift" + chr(34) + "): i + 1")}')

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Las tres redes anteriores siguen en cero")
from barre_frases import frases                                    # noqa: E402

EXCL_CORTAS = {
    "🗺 Ruta del día", "📊 Su trabajo",       # IDs de sub-pestaña (v232)
    "En progreso", "En pausa", "⏸ En pausa",  # estados GUARDADOS en la hoja
    "por vencer",                            # lo devuelve `credentials.status()`
}
_c = []
for f in UI:
    for ln, s in sorted(set(frases(f, minimo=2))):
        if s in EXCL_CORTAS or s.lstrip().startswith("<style>") or "/*" in s \
           or "function f(s)" in s or re.search(r"`(Login|Grupos|Rieles)`", s):
            continue
        _lim = re.sub(r"#[0-9a-fA-F]{3,8}", " ", s)
        _lim = re.sub(r"<[^>]*>", " ", _lim)
        if set(re.findall(r"[a-záéíóúñü]+", _sin(_lim))) & ES:
            _c.append(f"{f.name}:{ln} {s[:40]!r}")
chk("0 etiquetas cortas en español (red 3, v442)", not _c, f"{len(_c)}: {_c[:4]}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
