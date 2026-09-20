"""v452 — la DUODÉCIMA red: el valor de negocio CRUDO dentro de una celda.

## El hueco

v442 enrutó `i18n.etiqueta()` por los puntos donde se PINTA un estado… pero la
celda de un `st.dataframe` no es una llamada a `st.*`: es un valor dentro de un
dict que alimenta un `pd.DataFrame`. Ninguna de las once redes anteriores mira
ahí, así que la columna «Status» de Facturas seguía mostrando `parcial ·
cobrada · vencida · pendiente` en español — a dos centímetros de un KPI que ya
decía OUTSTANDING y OVERDUE.

## ⚠️ Y por qué la red tiene que mirar el DESTINO del dict

Mi primer barrido buscó «clave "Estado" en un dict» y marcó CINCO sitios. Dos de
ellos **no eran filas de tabla: eran el dict que se ESCRIBE en la hoja**
(`update_project`). Traducirlos habría guardado el estado en INGLÉS en Google
Sheets — el peor fallo posible de esta migración, porque un DATO traducido deja
de casar **sin dar ningún error** (v442, la rama muerta del corte de rieles).

Llegué a aplicarlo y **compilaba**. Lo que lo destapó fue mirar el dict entero
antes de dar el cambio por bueno, no el compilador.

→ La red solo mira los dicts que están DENTRO de un `pd.DataFrame(...)`, que es
lo que significa «fila de tabla». Es la lección de v444 (clasificar por lo que
la cadena HACE, no por cómo se ve) aplicada a los valores.
"""
import ast
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


# Funciones que DEVUELVEN un valor de negocio en español (el dato de la hoja).
DEVUELVEN_DATO = {"estado_cobro", "derive_estado", "status", "estado_de"}


def _dicts_de_tabla(arb):
    """Dicts que alimentan un `pd.DataFrame` — o sea, FILAS de tabla."""
    out = []
    for n in ast.walk(arb):
        if not isinstance(n, ast.Call):
            continue
        _f = n.func
        if not (getattr(_f, "attr", None) == "DataFrame"
                or getattr(_f, "id", None) == "DataFrame"):
            continue
        for sub in ast.walk(n):
            if isinstance(sub, ast.Dict):
                out.append(sub)
    return out


print("== 1. Valores de negocio crudos en una CELDA de tabla ==")
crudos = []
for f in sorted(CORE.glob("*_ui.py")):
    arb = ast.parse(f.read_text(encoding="utf-8"))
    for dd in _dicts_de_tabla(arb):
        for k, v in zip(dd.keys, dd.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            envuelto = isinstance(v, ast.Call) and (
                getattr(v.func, "id", None) == "_etq"
                or getattr(v.func, "attr", None) == "etiqueta")
            if envuelto:
                continue
            for n in ast.walk(v):
                if isinstance(n, ast.Call):
                    nom = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                    if nom in DEVUELVEN_DATO:
                        crudos.append((f.name, k.lineno, k.value, nom))
for c in crudos:
    print(f"     {c[0]}:{c[1]}  clave={c[2]!r} <- {c[3]}()")
chk(not crudos, f"ninguna celda muestra un valor de negocio en crudo ({len(crudos)})")

# ⚠️ Validar la red contra un caso conocido-bueno antes de creerse su cero (nº12).
print("\n== 2. ¿La red sabe ver el caso? ==")
_sonda = ast.parse('df = pd.DataFrame([{"Status": I.estado_cobro(f)} for f in xs])')
_vistos = []
for dd in _dicts_de_tabla(_sonda):
    for k, v in zip(dd.keys, dd.values):
        for n in ast.walk(v):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", None) in DEVUELVEN_DATO:
                _vistos.append(k.value)
chk(_vistos == ["Status"], f"detecta un caso construido a propósito ({_vistos})")

print("\n== 3. ⚠️ Y NO toca lo que se ESCRIBE en la hoja ==")
_pu = (CORE / "projects_ui.py").read_text(encoding="utf-8")
# Los dos dicts de `update_project` conservan el valor CRUDO: es el dato que va a
# Google Sheets y lo comparan 387 sitios.
chk('"Status": P.derive_estado(avance, est_man,' in _pu,
    "el dict de update_project conserva el estado CRUDO (dato de la hoja)")
chk('"Status": P.derive_estado(0, est, tipo),' in _pu,
    "…y el del alta de localización, también")
chk("_etq(P.derive_estado" not in _pu,
    "⚠️ NINGUNA escritura de estado pasa por etiqueta() (guardaría inglés en Sheets)")

print("\n== 4. Las 3 celdas que SÍ son display, traducidas ==")
for fn, frag in [("invoices_ui.py", "_etq(I.estado_cobro(f))"),
                 ("clientes_ui.py", "_etq(INV.estado_cobro(x))"),
                 ("quotes_ui.py", "_etq(Q.estado_de(c))")]:
    chk(frag in (CORE / fn).read_text(encoding="utf-8"), f"{fn}: {frag}")

print("\n== 5. `_etq` importado donde se usa (ámbito, no presencia) ==")
# ⚠️ Al traducir metí `_etq(...)` en dos módulos que NO lo importaban: NameError
# seguro al abrir esas pantallas, y `compileall` lo daba por bueno (v423/v425/v443).
for f in sorted(CORE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    if "_etq(" not in src:
        continue
    arb = ast.parse(src)
    imp = any(isinstance(n, ast.ImportFrom)
              and any(al.asname == "_etq" for al in n.names)
              for n in arb.body)
    propio = any(isinstance(n, ast.FunctionDef) and n.name == "_etq"
                 for n in ast.walk(arb))
    chk(imp or propio, f"{f.name} usa `_etq` y lo tiene a nivel de módulo")

# ======================================================================
# La OCTAVA red, ENSANCHADA: el ternario ASIMETRICO.
#
# El guardian de v451 solo miraba el ternario cuando era el ARGUMENTO de un `st.*`.
# Pero se cuela igual dentro de una lista que luego se junta, y ahi vivia
# `t(':material/lock: closed') if _cerrada else ':material/check_circle: abierta'`:
# una rama traducida y la otra en espanol, en la cabecera de la ficha de localizacion.
#
# La senal que SI se puede buscar en todo el repo sin falsos positivos es la
# ASIMETRIA: si una rama pasa por t() y la otra es un literal, es traduccion a
# medias, este donde este. Barrido: 3 casos mas (la columna Contacto con `yes` y
# `falta` juntos, la campana y el historial de Pre-Start).
# ======================================================================
print(chr(10) + "== 6. Ternarios ASIMETRICOS (una rama t(), la otra literal) ==")

def _env(n):
    return isinstance(n, ast.Call) and (getattr(n.func, "id", None) in ("t", "d", "_d", "_etq")
                                        or getattr(n.func, "attr", None) in ("t", "d", "etiqueta"))


def _texto_real(v):
    """Lo que queda tras quitar iconos, marcas de color y separadores.

    Una rama cuyo literal es solo `"  ·  :orange[:material/warning:] "` no tiene
    NADA que traducir: marcarla seria ruido, y una red que grita sobre lo que ya
    esta bien acaba ignorandose entera (la leccion del lexico corto de v450).
    """
    v = re.sub(r":material/[a-z_]+:", "", str(v))
    v = re.sub(r":(red|green|orange|blue|gray|grey|violet)\[", "", v)
    return re.sub(r"[\s·|\-—:\]\[]+", "", v)


def _lit(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return len(_texto_real(n.value)) > 2
    if isinstance(n, ast.JoinedStr):
        return any(isinstance(x, ast.Constant) and len(_texto_real(x.value)) > 2
                   for x in n.values)
    return False


_asim = []
for _f in sorted(CORE.glob("*.py")):
    for _n in ast.walk(ast.parse(_f.read_text(encoding="utf-8"))):
        if not isinstance(_n, ast.IfExp):
            continue
        if (_env(_n.body) and _lit(_n.orelse)) or (_env(_n.orelse) and _lit(_n.body)):
            _asim.append((_f.name, _n.lineno))
for _h in _asim:
    print(f"     {_h[0]}:{_h[1]}")
chk(not _asim, f"ningun ternario con una rama traducida y la otra no ({len(_asim)})")

# Validar la red contra un caso construido (trampa n12).
_s2 = ast.parse('x = t("closed") if c else ":material/check: abierta"')
_v2 = [n for n in ast.walk(_s2) if isinstance(n, ast.IfExp)
       and _env(n.body) and _lit(n.orelse)]
chk(len(_v2) == 1, "la red ve un ternario asimetrico construido a proposito")

# ======================================================================
# La DECIMOTERCERA red: la LEYENDA de un chart.
#
# Los nombres de columna del DataFrame que va a `st.line_chart`/`st.bar_chart` SON
# la leyenda que se pinta. Ahi no llega `tabla.cfg()` (que es solo para
# `st.dataframe`) ni ninguna de las doce redes: no es una llamada a `st.*` con un
# literal, es una clave de dict. En el dashboard de agrupacion se leia
# «Planificado / Real» bajo una curva cuyo titulo ya estaba en ingles.
#
# ⚠️ ACOTADO A LA FUNCION. Mi primer barrido atribuia al chart TODOS los `_df` del
# modulo y daba 19 casos; 16 eran de otras funciones y ya pasan por `tabla.cfg()`.
# Es el error de ambito del medidor de v450, repetido: un recuento con el medidor
# mal es peor que no medir.
# ======================================================================
print(chr(10) + "== 7. La decimotercera red: leyendas de chart ==")
CHART = {"line_chart", "bar_chart", "area_chart", "scatter_chart"}
_ley = []
for _f in sorted(CORE.glob("*.py")):
    _a4 = ast.parse(_f.read_text(encoding="utf-8"))
    for _fn in [n for n in ast.walk(_a4)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        _dest = {}
        for _n in ast.walk(_fn):
            if (isinstance(_n, ast.Call)
                    and getattr(_n.func, "attr", None) in CHART and _n.args):
                _v = _n.args[0]
                if isinstance(_v, ast.Name):
                    _dest[_v.id] = _n.lineno
                for _d in ast.walk(_v):
                    if isinstance(_d, ast.Dict):
                        for _k in _d.keys:
                            if isinstance(_k, ast.Constant) and isinstance(_k.value, str):
                                _ley.append((_f.name, _k.lineno, _k.value))
        for _n in ast.walk(_fn):
            if (isinstance(_n, ast.Assign) and len(_n.targets) == 1
                    and getattr(_n.targets[0], "id", None) in _dest):
                for _d in ast.walk(_n.value):
                    if isinstance(_d, ast.Dict):
                        for _k in _d.keys:
                            if isinstance(_k, ast.Constant) and isinstance(_k.value, str):
                                _ley.append((_f.name, _k.lineno, _k.value))
for _h in sorted(set(_ley)):
    print(f"     {_h[0]}:{_h[1]}  {_h[2]!r}")
chk(not _ley, f"ninguna leyenda de chart es un literal suelto ({len(set(_ley))})")

# Y la afirmacion POSITIVA: el ingles esperado tiene que ESTAR (v438/v439).
chk('{t("Planned"): cur["plan"], t("Actual"): cur["real"]}' in _pu,
    "la curva consolidada se rotula Planned/Actual")

# ======================================================================
# Las DOS ramas del mismo if/elif, en el MISMO idioma.
#
# El detalle de cotizacion tenia `t("You are at")` en una rama y «Vas» en la
# de al lado: media traduccion DENTRO DEL MISMO BLOQUE, que es el peor caso
# (v443), porque el usuario ve los dos idiomas a la vez y encima el mismo
# «Vas» ya se habia arreglado en `projects_ui` — o sea que se arreglo una
# copia y no la otra.
#
# ⚠️ Se afirma en POSITIVO —el ingles esperado tiene que ESTAR— y NUNCA por
# ausencia de espanol: un detector de idioma es ciego a las palabras sin
# acento (trampa n28), y ya dejo pasar esto mismo dos veces.
# ======================================================================
print(chr(10) + "== 8. Las dos ramas del titular de cotizacion ==")
_qu = (CORE / "quotes_ui.py").read_text(encoding="utf-8")
# ⚠️ CADUCADO Y ACTUALIZADO en v453: en v452 las dos ramas compartian el trozo
# `t("You are at")` y el resto de la frase iba concatenado y SIN traducir. v453 las
# convirtio en dos claves COMPLETAS con marcadores, asi que ese trozo ya no existe.
# Lo que la regla protege no es el literal, sino que las DOS ramas del mismo
# if/elif esten traducidas ENTERAS — media traduccion es el peor caso (v443).
_n_ramas = _qu.count('You are at **{m}')
chk(_n_ramas == 2, f"las DOS ramas del titular son una frase completa ({_n_ramas}/2)")
chk('" above** what was quoted' not in _qu and '" below** what was quoted' not in _qu,
    "…y ningun trozo de esas frases queda suelto en una concatenacion")

# Y los otros dos literales espanoles del mismo modulo.
chk('t("Open")' in _qu, "el boton de abrir el proyecto de la cotizacion")
chk('t("Project")' in _qu and 't("created from this quote.")' in _qu,
    "el aviso de proyecto creado desde la cotizacion")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
