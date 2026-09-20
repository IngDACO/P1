# -*- coding: utf-8 -*-
"""Guardián de v445 — F5a: los mensajes de BACKEND de `auth` y `timeclock`.

Son los dos módulos cuyos mensajes se ven más veces al día: cada login pasa por
`auth.verify_login` y cada jornada por `clock_in`/`clock_out`. Aquí el criterio NO
es la posición (no hay llamadas a `st.*`): es el DESTINO de la cadena.

  se traduce   lo que la función DEVUELVE, porque la UI lo pinta con `flash`
  NO se toca   los mensajes de `logger` (nadie los ve) y los **nombres de columna**
               que viajan en el mismo `return` (`"Usuario"`, `"Nombre"`, `"Estado"`):
               son el DATO del libro, y traducirlos rompe la lectura en silencio

⚠️ Y el orden: la local `t` de `auth._session_active` se renombró ANTES de traducir
(pre_i18n). Hacerlo después es como se rompieron v437, v439 y v440.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


AU = (RAIZ / "core/auth.py").read_text(encoding="utf-8")
TC = (RAIZ / "core/timeclock.py").read_text(encoding="utf-8")

# ── 1 ────────────────────────────────────────────────────────────
sec("1. Los mensajes se EJECUTAN y salen en inglés (importar no ejecuta, v378)")
from core import auth, timeclock                                   # noqa: E402

_r = auth.verify_login("no-existe-zzz-v445", "x")
chk("auth.verify_login se ejecuta y devuelve dict", isinstance(_r, dict))
chk("...con el mensaje en inglés", "User not found" in str(_r.get("error")),
    str(_r.get("error")))
_o, _m = auth.add_user("zzz-v445", "x", "rol-inexistente", "n", "cliente1")
chk("auth.add_user (rol inválido) en inglés", "Invalid role" in str(_m), str(_m))
_o, _m = auth.add_group("")
chk("auth.add_group (sin nombre) en inglés", "required" in str(_m).lower(), str(_m))
_o, _m = timeclock.clock_out("nadie-zzz-v445", "cliente1")
chk("timeclock.clock_out (sin fichaje) en inglés",
    "no open clock in" in str(_m).lower(), str(_m))

# ⚠️ La función donde vivía la variable `t`: si el renombrado hubiera roto algo,
# revienta AQUÍ, no al compilar.
import time as _time                                               # noqa: E402
chk("auth._session_active sigue funcionando tras renombrar su local",
    auth._session_active({"SessionToken": "x", "SessionTime": "0"}) is False
    and auth._session_active({"SessionToken": "x",
                              "SessionTime": str(int(_time.time()))}) is True)

# ── 2 ────────────────────────────────────────────────────────────
sec("2. El DATO no se tocó")
# ⚠️ Los nombres de columna se comprueban contra la CONSTANTE, no por subcadena:
# `"Usuario"` aparece en medio módulo, así que traducir la cabecera real seguía
# pasando el chequeo. Lo destapó la rotura, no leerlo (es la lección de v439:
# comprobar PRESENCIA deja pasar una traducción parcial).
from core.auth import LOGIN_HEADERS, GROUPS_HEADERS                # noqa: E402
chk("auth: LOGIN_HEADERS es el DATO del libro (v468: en ingles, con respaldo)",
    LOGIN_HEADERS[:6] == ["User", "Password", "Role", "Name", "Active", "Group"],
    str(LOGIN_HEADERS[:6]))
chk("auth: GROUPS_HEADERS es el DATO del libro (v468: en ingles, con respaldo)",
    GROUPS_HEADERS[:3] == ["Group", "Description", "Active"], str(GROUPS_HEADERS[:3]))
chk("auth: la fecha de alta y el token siguen en la cabecera",
    "StartedOn" in LOGIN_HEADERS and "SessionToken" in LOGIN_HEADERS)
# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto
# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y
# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la
# afirmacion cambia de objeto pero NO de principio.
# ⚠️ Y AQUI ESTA EL CHEQUEO QUE FALTABA. v469 migro `TIPO_PROYECTO` a "project" y
# dejo `("Sheet1", "Type")` FUERA de la lista blanca de `valores.COLUMNAS`, asi que las
# ~500 filas del historico seguian diciendo `proyecto`, se leian sin canonizar y
# `_tipo_of(r) == TIPO_PROYECTO` era FALSO para todas: ni una hora imputada a una obra
# contaba como tal — nomina, costo de obra, conciliacion y reparto por proyecto, todo a
# cero, en lo que mas se usa de la app. Y no daba ningun error. El barrido que lo busco
# tampoco lo vio, porque solo miraba constantes que son LISTA y estas son sueltas.
# Se comprueba EJECUTANDO la funcion real sobre una fila vieja y una nueva.
from core import timeclock as _TCM, valores as _VAL             # noqa: E402
chk("timeclock: el tipo que se GUARDA es el canonico",
    _TCM.TIPO_PROYECTO == "project" and _TCM.TIPO_GENERAL == "general",
    "%r / %r" % (_TCM.TIPO_PROYECTO, _TCM.TIPO_GENERAL))
chk("...y `Sheet1.Type` esta en la lista blanca (si no, el historico no casa)",
    ("Sheet1", "Type") in _VAL.COLUMNAS)
_casos = {"proyecto": True, "project": True, "": True, "general": False}
_mal = [v for v, esp in _casos.items()
        if (_TCM._tipo_of(_VAL.canonizar([{"Type": v}], "Sheet1")[0])
            == _TCM.TIPO_PROYECTO) != esp]
chk("...y una fila SIN migrar sigue contando como segmento de proyecto",
    not _mal, "fallan: %s" % _mal)
chk("...y las cabeceras de la hoja tampoco",
    '"Clock In"' in TC and '"Clock Out"' in TC and '"Project"' in TC)

# ── 3 ────────────────────────────────────────────────────────────
sec("3. El motor está a mano y nadie lo tapa")
_tr = ast.parse(AU)
chk("auth importa `t` a nivel de MÓDULO (no dentro de un def)",
    any(isinstance(x, ast.ImportFrom) and (x.module or "").endswith("i18n")
        and any(a.name == "t" for a in x.names) for x in _tr.body))
_tr2 = ast.parse(TC)
chk("timeclock importa `t` a nivel de módulo",
    any(isinstance(x, ast.ImportFrom) and (x.module or "").endswith("i18n")
        and any(a.name == "t" for a in x.names) for x in _tr2.body))
chk("...y solo UNA vez (correr el parche dos veces lo duplicó)",
    TC.count("from core.i18n import t") == 1, str(TC.count("from core.i18n import t")))

# ⚠️ Nadie puede usar `t` como variable en estos dos módulos: taparía la función en
# TODO el ámbito de esa función y solo se vería al ejecutar la pantalla.
for nombre, src in (("auth", AU), ("timeclock", TC)):
    tr = ast.parse(src)
    malas = []
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
               and x.id == "t" and id(x) not in comp for x in cuerpo):
            malas.append(f"{fn.name}:{fn.lineno}")
    chk(f"{nombre}: ninguna función usa `t` como variable", not malas, str(malas))

# ── 3b ───────────────────────────────────────────────────────────
sec("3b. Ningún `t()` se CONGELA al importar")
# ⚠️ Una llamada a `t()` a nivel de módulo se ejecuta UNA vez, al importar, cuando no
# hay sesión ni idioma: la cadena queda congelada. En `auth.SESION_OCUPADA` eso era
# peor que un texto en el idioma equivocado — esa constante SE COMPARA
# (`tok == auth.SESION_OCUPADA`), así que traducir un lado y no el otro haría
# desaparecer el botón «cerrar la otra sesión» sin dar ningún error.
# ⚠️ `d()` sí puede ir a nivel de módulo: devuelve SIEMPRE el idioma base (v436).
# ⚠️ Y `app.py` queda fuera: no es un módulo importado, es el script que Streamlit
# re-ejecuta entero en cada rerun, así que ahí nada se congela (daba 8 falsos).
from barre_t_modulo import congelados, EXCL                        # noqa: E402
_frios = []
for f in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    if f.name in EXCL:
        continue
    _frios += [f"{f.name}:{ln} ({donde})" for ln, donde in sorted(set(congelados(f)))]
chk("0 llamadas a `t()` congeladas al importar", not _frios, str(_frios))
chk("`SESION_OCUPADA` es un CENTINELA, no un texto traducido",
    "SESION_OCUPADA = \"" in AU and "SESION_OCUPADA = t(" not in AU)
chk("...y la traducción va donde se PINTA",
    "st.error(f\":material/lock: {t(tok)}\")"
    in (RAIZ / "core/auth_ui.py").read_text(encoding="utf-8"))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. No queda ningún mensaje en español")
import medir_f5 as M                                               # noqa: E402


def _es_msg(s):
    return len(s.split()) >= 3 or s.rstrip().endswith((".", ":", "…"))


for mod in ("auth.py", "timeclock.py"):
    c = M.clasifica(RAIZ / "core" / mod)
    resto = sorted({s for _, s in c["RETORNO"] + c["OTRO"] if _es_msg(s)})
    chk(f"{mod}: 0 mensajes en español", not resto, f"{len(resto)}: {resto[:3]}")
# ⚠️ Un «0» no vale si la red no ve el caso malo: se comprueba con uno construido.
_p = AQUI / "_probe_v445.py"
_p.write_text('def f():\n    return False, "No se pudo abrir la hoja."\n',
              encoding="utf-8")
try:
    _c = M.clasifica(_p)
    chk("...y la red SABE ver un mensaje español devuelto",
        any(_es_msg(s) for _, s in _c["RETORNO"]), str(_c))
finally:
    _p.unlink(missing_ok=True)

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
