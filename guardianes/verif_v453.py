"""v453 — la DECIMOCUARTA red (la CONCATENACIÓN) y la migración del histórico.

## La red 14

`st.info("texto " + var + " más texto")`: el literal NO es el argumento de la llamada,
es un **operando de un `BinOp`**, así que la red de POSICIÓN (v440) no lo ve. Es la
red 4 (la f-string entera) con `+` en vez de interpolación.

⚠️ Y aquí la MEDIDA corrigió mi estimación en las dos direcciones: dije «~80 llamadas»
a ojo y contadas eran **127** — de las que **97 son CSS/HTML** (no hay nada que
traducir), **30 frases ya en inglés** y **0 en español**. Estimar fue peor que no dar
número: inflaba el pendiente y ocultaba que 97 no eran trabajo.

## El arreglo NO es envolver cada trozo

Un trozo no es una frase, y el orden de las palabras cambia entre idiomas. Cada frase
pasa a ser UNA clave con marcadores (`{x}`) y los valores calculados entran por
`.replace()` — el patrón del titular de v452.

⚠️ Eso abre un modo de fallo nuevo y SILENCIOSO: si un marcador de la clave no casa con
su `.replace()`, el `{x}` se **pinta literal** y no salta ningún error. Por eso el
chequeo 2 existe.

## La migración del histórico

Los nombres de actividad se GUARDAN en la hoja `Actividades`, así que traducir solo el
código habría dejado los proyectos viejos en español y los nuevos en inglés **sin forma
de casarlos**. En v453 se migraron las 123 filas (1 batch, verificadas leyendo) y por
eso el guardián de v438 se invirtió: ahora protege que no vuelvan al español.

⚠️ Lo que NO se migró, y es deliberado: el `tipo` de un concepto de nómina
(`aporte`/`deduccion`/`devengo`) y las BANDERAS de `PHASES` (`cortes`, `shaft`). Los dos
se COMPARAN, así que traducirlos deja la rama muerta sin dar ningún error (v442/v447).
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


DISPLAY = {"write", "markdown", "info", "success", "warning", "error", "caption",
           "metric", "button", "subheader", "header", "title", "text"}
CSS = re.compile(r"[<>{};:#]|px|rem|font|color|background|margin|padding|border|flex|grid")


def _trozos(n):
    """Literales que son OPERANDO de una concatenación."""
    out = []
    for x in ast.walk(n):
        if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add):
            for lado in (x.left, x.right):
                if isinstance(lado, ast.Constant) and isinstance(lado.value, str):
                    out.append(lado.value)
    return out


def _env(n):
    return isinstance(n, ast.Call) and (getattr(n.func, "id", None) in ("t", "d", "_d")
                                        or getattr(n.func, "attr", None) in ("t", "d"))


print("== 1. La red 14: frases sueltas en una CONCATENACIÓN ==")
sueltas = []
for f in sorted(CORE.glob("*_ui.py")):
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if not (isinstance(n, ast.Call) and getattr(n.func, "attr", None) in DISPLAY and n.args):
            continue
        for tr in _trozos(n.args[0]):
            if _env(n.args[0]) or len(tr.strip()) < 3 or CSS.search(tr):
                continue
            sueltas.append((f.name, n.lineno, tr.strip()[:60]))
for s in sueltas:
    print(f"     {s[0]}:{s[1]}  {s[2]!r}")
chk(not sueltas, f"ninguna frase de display queda suelta en una concatenación ({len(sueltas)})")

# ⚠️ Validar la red contra un caso construido antes de creerse su cero (trampa nº12).
_sonda = ast.parse('st.info("The job is " + x + " and must be fixed by hand.")')
_v = []
for n in ast.walk(_sonda):
    if isinstance(n, ast.Call) and getattr(n.func, "attr", None) in DISPLAY and n.args:
        _v += [t for t in _trozos(n.args[0]) if len(t.strip()) >= 3 and not CSS.search(t)]
chk(len(_v) == 2, f"la red ve una concatenación construida a propósito ({len(_v)})")


print("\n== 2. Cada marcador {x} tiene su .replace() ==")
# ⚠️ SOLO el nodo MÁS EXTERNO de cada cadena: los intermedios ven un único
# `.replace()` y darían 10 «marcadores sin replace» que no existen — me pasó al
# escribir este chequeo, y sin mirar el código acusado habría «arreglado» código sano.
MARK = re.compile(r"\{([a-z]\w*)\}")
desparejados = []
for f in sorted(CORE.glob("*.py")):
    arb = ast.parse(f.read_text(encoding="utf-8"))
    # ⚠️ Interno = CUALQUIER `.replace()` que cuelgue del subarbol de otro. Mirar solo
    # `func.value` no basta: el `.replace()` que vive DENTRO de una rama de un ternario
    # no es el hijo directo del externo, y se procesaba como cadena suelta — por eso el
    # guardian daba un FALLO con el codigo correcto (verificado ejecutandolo).
    _reps = [n for n in ast.walk(arb)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "replace"]
    internos = {id(h) for n in _reps for h in ast.walk(n)
                if h is not n and isinstance(h, ast.Call)
                and getattr(h.func, "attr", None) == "replace"}
    for n in ast.walk(arb):
        if not (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "replace"):
            continue
        if id(n) in internos:
            continue
        raiz, reps = n, []
        while isinstance(raiz, ast.Call) and getattr(raiz.func, "attr", None) == "replace":
            if raiz.args and isinstance(raiz.args[0], ast.Constant):
                reps.append(str(raiz.args[0].value))
            raiz = raiz.func.value
        # ⚠️ La raiz puede ser un TERNARIO: `(t(A).replace(..) if c else t(B)).replace(..)`.
        # Ahi los marcadores salen de las DOS ramas y los `.replace()` estan repartidos
        # dentro y fuera. Mirar solo la cadena externa daba un FALLO con el codigo
        # CORRECTO (verificado ejecutandolo), que es justo lo que empuja a romper algo sano.
        ramas = ([raiz.body, raiz.orelse] if isinstance(raiz, ast.IfExp) else [raiz])
        base = []
        for rm in ramas:
            while isinstance(rm, ast.Call) and getattr(rm.func, "attr", None) == "replace":
                if rm.args and isinstance(rm.args[0], ast.Constant):
                    reps.append(str(rm.args[0].value))
                rm = rm.func.value
            base.append(rm)
        if not any(isinstance(b_, ast.Call) and getattr(b_.func, "id", None) in ("t", "d", "_d")
                   for b_ in base):
            continue
        lit = "".join(a.value for b_ in base for a in ast.walk(b_)
                      if isinstance(a, ast.Constant) and isinstance(a.value, str))
        falta = set(MARK.findall(lit)) - {r.strip("{}") for r in reps if r.startswith("{")}
        if falta:
            desparejados.append(f"{f.name}:{n.lineno} {sorted(falta)}")
for d in desparejados:
    print(f"     {d}")
chk(not desparejados, f"ningún marcador se quedaría literal en pantalla ({len(desparejados)})")

# ⚠️ El hueco gemelo: una clave CON marcador y SIN ningun `.replace()` no forma cadena,
# asi que el chequeo de arriba ni la mira — y el `{x}` se pinta igual en pantalla.
_solitarias = []
for f in sorted(CORE.glob("*.py")):
    arb = ast.parse(f.read_text(encoding="utf-8"))
    _con_rep = {id(x.func.value) for x in ast.walk(arb)
                if isinstance(x, ast.Call) and getattr(x.func, "attr", None) == "replace"}
    # …y todo `t()` que caiga DENTRO del subarbol de un `.replace()` (el caso ternario).
    _bajo_rep = {id(h) for x in ast.walk(arb)
                 if isinstance(x, ast.Call) and getattr(x.func, "attr", None) == "replace"
                 for h in ast.walk(x)}
    for n in ast.walk(arb):
        if not (isinstance(n, ast.Call) and getattr(n.func, "id", None) in ("t", "d", "_d")):
            continue
        lit = "".join(a.value for a in ast.walk(n)
                      if isinstance(a, ast.Constant) and isinstance(a.value, str))
        # ⚠️ Hay DOS formas legitimas de sustituir, y mirar solo `.replace()` daba 22
        # falsos positivos: (a) `t("… {x} …", x=valor)` — el motor acepta **kwargs y
        # hace el `.format()` el mismo (i18n.py:88), que ademas es la forma NATIVA; y
        # (b) el `.replace()` aplicado al resultado de un TERNARIO, donde el `t()` no
        # es el `func.value` del replace. Un chequeo que grita sobre lo que ya esta
        # bien acaba ignorandose entero (v452).
        _tiene_kw = bool(n.keywords)
        if MARK.findall(lit) and not _tiene_kw and id(n) not in _con_rep and id(n) not in _bajo_rep:
            _solitarias.append(f"{f.name}:{n.lineno} {sorted(set(MARK.findall(lit)))}")
for x in _solitarias:
    print(f"     {x}")
chk(not _solitarias, f"ninguna clave con marcador se queda sin .replace() ({len(_solitarias)})")

def _huerfanos(codigo):
    """Aplica la MISMA logica a un fragmento, para poder validarla."""
    arb = ast.parse(codigo)
    _reps = [n for n in ast.walk(arb)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "replace"]
    internos = {id(h) for n in _reps for h in ast.walk(n)
                if h is not n and isinstance(h, ast.Call)
                and getattr(h.func, "attr", None) == "replace"}
    out = []
    for n in ast.walk(arb):
        if not (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "replace"):
            continue
        if id(n) in internos:
            continue
        raiz, reps = n, []
        while isinstance(raiz, ast.Call) and getattr(raiz.func, "attr", None) == "replace":
            if raiz.args and isinstance(raiz.args[0], ast.Constant):
                reps.append(str(raiz.args[0].value))
            raiz = raiz.func.value
        ramas = ([raiz.body, raiz.orelse] if isinstance(raiz, ast.IfExp) else [raiz])
        base = []
        for rm in ramas:
            while isinstance(rm, ast.Call) and getattr(rm.func, "attr", None) == "replace":
                if rm.args and isinstance(rm.args[0], ast.Constant):
                    reps.append(str(rm.args[0].value))
                rm = rm.func.value
            base.append(rm)
        if not any(isinstance(b_, ast.Call) and getattr(b_.func, "id", None) in ("t", "d", "_d")
                   for b_ in base):
            continue
        lit = "".join(a.value for b_ in base for a in ast.walk(b_)
                      if isinstance(a, ast.Constant) and isinstance(a.value, str))
        out += sorted(set(MARK.findall(lit)) - {r.strip("{}") for r in reps if r.startswith("{")})
    return out

_ok_tern = _huerfanos('x = (t("a {c} {f} {d}").replace("{d}", z) if c else t("a {c} {f}"))'
                      '.replace("{c}", p).replace("{f}", q)')
chk(not _ok_tern, f"un TERNARIO correcto no se marca como fallo ({_ok_tern})")
_roto = _huerfanos('x = t("hola {a} y {b}").replace("{a}", z)')
chk(_roto == ["b"], f"…y un marcador huerfano SI se caza ({_roto})")


print("\n== 3. Los nombres de actividad, migrados en las DOS puntas ==")
from core import schedule as S  # noqa: E402
import datetime as _dt  # noqa: E402
from core import stages as _ST53  # noqa: E402
_nom = [a["nombre"] for a in S.build_schedule(6, _dt.date(2026, 9, 1), {})["activities"]]
chk(len(_nom) >= 8, f"…y el chequeo ve actividades de verdad ({len(_nom)})")
chk(not [x for x in _nom if any(c in x for c in "áéíóúñ")],
    "el CÓDIGO genera los nombres en inglés")
# ⚠️ v515 · EL ACENTO NO BASTA, y lo demostró la batería: «Puertas de rellano» no lleva
# ni uno, así que traducir una etapa se ESCAPABA de este chequeo con las dos puntas
# cambiando a la vez. Es la trampa nº28 (un detector por idioma no ve las palabras sin
# acento) dentro del guardián que existe precisamente para el idioma. Se añade la red de
# palabras funcionales, y se valida contra un caso conocido-malo (nº12).
_ES53 = {"de", "del", "la", "el", "los", "las", "y", "con", "sin", "por", "para",
         "puertas", "rellano", "cabina", "hueco", "montaje", "desmontaje", "guias",
         "instalacion", "ajuste", "pruebas", "entrega", "contrapeso"}


def _es53(n):
    return bool({w for w in re.findall(r"[a-záéíóúñ]+", n.lower())} & _ES53)


chk(not [x for x in _nom if _es53(x)],
    f"…y tampoco en español SIN acento ({[x for x in _nom if _es53(x)][:2]})")
chk(_es53("Puertas de rellano") and not _es53("Shaft Climb & Bedplates"),
    "…y la sonda SÍ caza un nombre traducido sin acento")
# ⚠️ v515 · Los tres nombres esperados eran de `PHASES`, borrada. Se DERIVAN del
# catálogo en vez de teclearse (trampa nº16): así el chequeo sigue siendo positivo —que
# los nombres esperados ESTÉN, no que el español no esté (trampa nº28)— sin caducar cada
# vez que el catálogo cambie. Y se compara la lista ENTERA, no tres muestras.
_esp53 = [e[2] for e in _ST53.etapas(_ST53.PISTA_INSTALL)]
chk(bool(_esp53), f"el catálogo aporta los nombres esperados ({len(_esp53)})")
chk(_nom == _esp53, "el cronograma son EXACTAMENTE las etapas del catálogo")
for esperado in _esp53[:3]:
    chk(esperado in _nom, f"…incluido {esperado!r}")

print("\n== 4. ⚠️ Lo que se ESCRIBE es lo mismo que se COMPARA ==")
# ⚠️ NO vale comprobar que el literal «esté en el fichero»: aparece en VARIOS sitios
# (la constante Y la comparación), así que traducir UNO seguía pasando — tres roturas
# se escaparon por eso. La invariante real es que los valores PRODUCIDOS y los
# COMPARADOS sean el MISMO conjunto: si divergen, la rama queda muerta sin dar error.
# ⚠️ v515 · MISMO INVARIANTE, OTRO PAR. Vigilaba las banderas de `PHASES` contra
# `detect_flags`; las dos se BORRARON. El fallo que describe sigue existiendo, solo que
# ahora entre `ACTIVIDADES` (donde se ESCRIBE el nombre de una condicional) y
# `EXCLUYENTES` (donde se COMPARA para preguntar por ella): `plan_de` casa por nombre
# exacto, así que traducir o renombrar UNO deja la opción sin casar NUNCA — la actividad
# no entra en el plan, nadie puede elegirla y **no salta ningún error**. Es exactamente
# la rama muerta que v453 vino a impedir, y en el sitio que más pesa (el 25% del R3).
_op53 = {o for g in _ST53.EXCLUYENTES.values() for o in g["opciones"]}
_act53 = {a[0] for _v in _ST53.ACTIVIDADES.values() for a in _v}
chk(bool(_op53), f"los grupos excluyentes ofrecen opciones ({sorted(_op53)})")
chk(_op53 <= _act53,
    f"toda opción excluyente existe como actividad (huérfanas: {sorted(_op53 - _act53)})")
# ⚠️ Y en la otra punta: una opción que exista pero NO esté marcada como condicional se
# crearía siempre, así que preguntar por ella no cambiaría nada.
_cond53 = {a[0] for _v in _ST53.ACTIVIDADES.values() for a in _v if a[2]}
chk(_op53 <= _cond53,
    f"…y está marcada como condicional (no lo son: {sorted(_op53 - _cond53)})")

_a_pay = ast.parse((CORE / "payroll.py").read_text(encoding="utf-8"))
_esc = {v.value for n in ast.walk(_a_pay) if isinstance(n, ast.Dict)
        for k, v in zip(n.keys, n.values)
        if isinstance(k, ast.Constant) and k.value == "tipo"
        and isinstance(v, ast.Constant) and isinstance(v.value, str)}
_neto = next((n for n in ast.walk(_a_pay)
              if isinstance(n, ast.FunctionDef) and n.name == "neto"), None)
_cmp = {c.value for cp in ast.walk(_neto) if isinstance(cp, ast.Compare)
        for c in cp.comparators
        if isinstance(c, ast.Constant) and isinstance(c.value, str)} if _neto else set()
chk(bool(_esc), f"payroll escribe tipos de concepto ({sorted(_esc)})")
# ⚠️ La direccion correcta es COMPARADOS ⊆ ESCRITOS, no al reves: `aporte` se escribe
# y `neto()` NO lo compara A PROPOSITO (el superannuation no descuenta del neto, v346),
# asi que exigir escritos⊆comparados daba FALLO con el codigo CORRECTO. Lo que si es un
# fallo es que `neto()` compare un valor que nadie escribe: esa rama esta MUERTA (v442).
chk(_cmp <= _esc,
    f"toda rama de neto() compara un tipo que alguien ESCRIBE (muertas: {sorted(_cmp - _esc)})")

# Y la prueba de que el nombre NO decide el dinero: mismo neto con el concepto en
# español (histórico) y en inglés (migrado).
from core import payroll as PY  # noqa: E402
_es = PY.neto(1000.0, [{"concepto": "Retención de impuesto (PAYG)", "tipo": "deduccion", "monto": 150.0}])
_en = PY.neto(1000.0, [{"concepto": "Income tax withheld (PAYG)", "tipo": "deduccion", "monto": 150.0}])
chk(_es == _en == 850.0, f"el neto no depende del NOMBRE del concepto ({_es} vs {_en})")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
