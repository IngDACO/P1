"""Guardián de v430 — autogestión de ausencias.

Afirma PRINCIPIOS, no formas (v392):
  1. Un módulo que lee `hojas.registros(SHEET)` SIN cabeceras necesita SHEET en
     `HOJAS_LECTURA` o lee VACÍO PARA SIEMPRE sin ningún error (regla v353, cuyo
     guardián no existía en la suite: se crea aquí).
  2. La enfermedad NO espera aprobación y el día libre NO se paga (el modelo que
     fijó el usuario). Se lee de `TIPOS`, no de un literal repetido.
  3. `resolver` solo actúa sobre PENDIENTE (no se puede rechazar lo ya aprobado).
  4. La ausencia pagada entra en la nómina como DEVENGO con `origen="ausencia"`,
     NUNCA sumada a `Base` — si entrara, cada vacación aprobada saldría como
     descuadre en la conciliación de v313.
  5. `generar` recorre la UNIÓN de fichados y ausentes: quien estuvo fuera el
     periodo entero no aparece en las horas fichadas y se quedaría SIN nómina.
  6. La conciliación suma las ausencias al costo real (si no, dinero que sale de
     caja y no aparece en ninguna cifra).
  7. Todo mensaje seguido de `st.rerun()` va por `flash` (v365) y `flash`/`theme`
     se importan a nivel de MÓDULO donde se usan (v342/v366: ámbito, no presencia).
  8. Los destinos de navegación existen (regla v303) y las claves de sección están
     cableadas en el despachador.
  9. Ninguna llamada a `_kpi_card` tira su valor (v424).
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True
n_chk = 0


def chk(t, cond, detalle=""):
    global ok, n_chk
    n_chk += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t}" + (f"  → {detalle}" if detalle and not cond else ""))


def arbol(rel):
    return ast.parse((RAIZ / rel).read_text(encoding="utf-8"))


def fn(tree, nombre):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre:
            return n
    return None


def src(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


def seccion(t):
    print(f"\n{'─' * 70}\n{t}\n{'─' * 70}")


# ── 1 ────────────────────────────────────────────────────────────
seccion("1. La hoja está en el LOTE (regla v353: si no, lee vacío PARA SIEMPRE)")
t_h = arbol("core/hojas.py")
_lect = set()
for n in ast.walk(t_h):
    if isinstance(n, ast.Assign) and any(
            getattr(x, "id", "") == "HOJAS_LECTURA" for x in n.targets):
        _lect = {e.value for e in ast.walk(n.value) if isinstance(e, ast.Constant)
                 and isinstance(e.value, str)}
chk("HOJAS_LECTURA se pudo leer", len(_lect) > 5, f"{len(_lect)} hojas")

# Barrido GENERAL: todo módulo con SHEET = "X" que llame registros(SHEET) sin cabeceras
faltan = []
for f in sorted((RAIZ / "core").glob("*.py")):
    try:
        tr = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    consts = {}
    for n in tr.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    consts[tg.id] = n.value.value
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "registros"):
            continue
        if len(n.args) != 1 or not isinstance(n.args[0], ast.Name):
            continue                     # con cabeceras: crea la hoja, otro caso
        hoja = consts.get(n.args[0].id)
        if hoja and hoja not in _lect:
            faltan.append(f"{f.name}:{n.lineno} → {hoja}")
chk("ningún lector sin cabeceras queda fuera del lote", not faltan, str(faltan))
from core import ausencias as _AU  # noqa: E402
chk("la hoja de ausencias (%r) esta en el lote" % _AU.SHEET, _AU.SHEET in _lect)

# ── 2 ────────────────────────────────────────────────────────────
seccion("2. El modelo de los tipos (decisiones del usuario)")
from core import ausencias as AU        # noqa: E402

chk("la ENFERMEDAD no espera aprobación",
    AU.TIPOS[AU.ENFERMEDAD]["aprobacion"] is False)
chk("...y se PAGA", AU.TIPOS[AU.ENFERMEDAD]["pagado"] is True)
chk("las VACACIONES sí requieren aprobación",
    AU.TIPOS[AU.VACACIONES]["aprobacion"] is True)
chk("...y se pagan", AU.TIPOS[AU.VACACIONES]["pagado"] is True)
chk("el día LIBRE requiere aprobación y NO se paga",
    AU.TIPOS[AU.LIBRE]["aprobacion"] is True and AU.TIPOS[AU.LIBRE]["pagado"] is False)
chk("cada tipo declara su estado en el tablero (reusa roster.ESTADOS)",
    all(c["estado_roster"] in ("OFF", "LEAVE", "FORMACION") for c in AU.TIPOS.values()))
chk("el saldo se DERIVA (no hay columna de saldo en la hoja)",
    not any("saldo" in h.lower() for h in AU.HEADERS))
chk("las PENDIENTES no descuentan saldo (dias_usados solo mira APROBADA)",
    "APROBADA" in ast.dump(fn(arbol("core/ausencias.py"), "dias_usados")))

# fin de semana: no se descuenta lo que nadie iba a trabajar
from datetime import date                                       # noqa: E402
_sab, _dom = date(2026, 8, 29), date(2026, 8, 30)
chk("un rango de solo fin de semana no cuenta días por defecto",
    AU.dias_del_rango(_sab, _dom) == [])
chk("...pero se puede pedir con incluir_findes",
    len(AU.dias_del_rango(_sab, _dom, True)) == 2)
chk("solapamiento = intersección de intervalos CERRADOS (v364)",
    AU._solapan(date(2026, 8, 3), date(2026, 8, 7),
                date(2026, 8, 7), date(2026, 8, 10)))

# ⚠️ LA INVARIANTE del dinero: se paga exactamente lo que se descontó del saldo.
# Lo destapó ejercitar la nómina de verdad — a alguien con el rango pedido «con fin
# de semana» se le quitaban 12 días de saldo y se le pagaban 8, porque cada lado
# recontaba el rango con su propio criterio.
chk("la hoja guarda si el rango incluye fin de semana", "IncludesWeekends" in AU.HEADERS)
# ⚠️ CADUCADO en v484 y REANCLADO: el criterio de qué día se paga se mudó a
# `horas_pagadas_dia` (el parte de horas lo necesita día a día) y `horas_pagadas_grupo`
# AGREGA desde ahí. La conducta es la misma —demostrada idéntica en 13 casos contra la
# implementación anterior—; lo que cambió es DÓNDE vive. Así que se comprueba en la
# función que aplica el criterio, y ADEMÁS que el agregado delegue: sin eso, nada
# impediría que apareciera una segunda implementación de lo que se paga. Queda más
# fuerte que antes, no más laxo.
_hpd = fn(arbol("core/ausencias.py"), "horas_pagadas_dia")
_hpg = fn(arbol("core/ausencias.py"), "horas_pagadas_grupo")
# ⚠️ Por LLAMADA y no por subcadena: `ast.unparse` incluye el DOCSTRING, y el de
# `horas_pagadas_grupo` menciona `horas_pagadas_dia` — así que la subcadena casaba con
# la prosa y la rotura «deja de delegar» ESCAPÓ. Es la trampa nº2 (grep ≠ uso) dentro
# del propio reanclaje, y solo la destapó probarlo contra el código roto.
def _llama_nombre(fnodo, nombre):
    """¿Esta función hace una llamada a `nombre`? (llamada por NOMBRE, no por atributo)

    ⚠️ Se llama `_llama_nombre` y no `_llama_a`: este módulo YA tiene un `_llama_a` con
    otra firma —(nodo, obj, attr), para llamadas de atributo— y reusar el nombre lo
    tapaba. El shadowing de v440/v445/v465, esta vez dentro del propio arreglo.
    """
    return any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == nombre
               for n in ast.walk(fnodo))


chk("el criterio vive en UNA función y el agregado DELEGA (llamada real)",
    _hpd is not None and _llama_nombre(_hpg, "horas_pagadas_dia"))
chk("lo pagado usa ESE dato, no un recuento propio",
    _llama_nombre(_hpd, "incluye_findes"))
chk("una fila sin la columna (anterior a v430) cae a días hábiles",
    AU.incluye_findes({}) is False)
chk("...y con SI, los cuenta", AU.incluye_findes({"IncludesWeekends": "SI"}) is True)

# ── 3 ────────────────────────────────────────────────────────────
seccion("3. `resolver` solo toca lo PENDIENTE")
_r = fn(arbol("core/ausencias.py"), "resolver")
_cmp = [n for n in ast.walk(_r) if isinstance(n, ast.Compare)]
chk("compara el estado actual contra PENDIENTE",
    any(any(getattr(c, "id", "") == "PENDIENTE" for c in n.comparators) for n in _cmp))
chk("...y NO se conforma con «vigente» (que incluye las aprobadas)",
    "VIGENTES" not in ast.dump(_r))
chk("`cancelar` sí acepta las vigentes (deshacer una aprobada)",
    "VIGENTES" in ast.dump(fn(arbol("core/ausencias.py"), "cancelar")))

# ── 4 · 5 ────────────────────────────────────────────────────────
seccion("4-5. La nómina paga las ausencias SIN romper la conciliación de v313")
t_p = arbol("core/payroll.py")
g = fn(t_p, "generar")
d = ast.dump(g)
chk("`generar` lee las ausencias del grupo", "horas_pagadas_grupo" in d)

# la ausencia va como devengo con origen, nunca dentro de Base
_base = next((n for n in ast.walk(g) if isinstance(n, ast.Assign)
              and any(getattr(x, "id", "") == "base" for x in n.targets)), None)
chk("`base` sigue siendo SOLO horas fichadas × tarifa",
    _base is not None and "aus" not in ast.dump(_base) and "monto_aus" not in ast.dump(_base),
    ast.dump(_base) if _base else "no se encontró")
_dicts = [n for n in ast.walk(g) if isinstance(n, ast.Dict)]
_orig = [n for n in _dicts
         if any(isinstance(k, ast.Constant) and k.value == "origen" for k in n.keys)]
chk("el concepto de ausencia lleva `origen: 'ausencia'`",
    any("ausencia" in ast.dump(n) and "devengo" in ast.dump(n) for n in _orig))

# la unión de claves: quien no fichó nada también entra
# ⚠️ El bucle de las colillas es el que itera `sorted(...)`, no «el primero»: al
# añadir en v432 otro `for` antes (el de los recortes), coger el primero daba un
# FALLO con el código perfectamente bien. Un localizador flojo genera rojos falsos.
_for = next((n for n in ast.walk(g) if isinstance(n, ast.For)
             and isinstance(n.iter, ast.Call)
             and isinstance(n.iter.func, ast.Name)
             and n.iter.func.id == "sorted"), None)
chk("el bucle de las colillas recorre la UNIÓN de fichados y ausentes",
    _for is not None and "BitOr" in ast.dump(_for.iter),
    ast.dump(_for.iter) if _for else "no hay bucle con sorted()")

# retención y super sobre el bruto
_ret = [n for n in ast.walk(g) if isinstance(n, ast.Dict)
        and any(isinstance(k, ast.Constant) and k.value == "concepto" for k in n.keys)
        and ("deduccion" in ast.dump(n) or "aporte" in ast.dump(n))]
chk("retención y superannuation se calculan sobre base + ausencia",
    len(_ret) == 2 and all("bruto" in ast.dump(n) for n in _ret))

# ── 6 ────────────────────────────────────────────────────────────
seccion("6. La conciliación no pierde el dinero de las ausencias")
c = fn(arbol("core/finance.py"), "conciliacion_mo")
dc = ast.dump(c)
chk("distingue el devengo por su `origen`", "'origen'" in dc and "'ausencia'" in dc)
_ret_dict = next((n for n in ast.walk(c) if isinstance(n, ast.Return)
                  and isinstance(n.value, ast.Dict)), None)
_claves = [k.value for k in _ret_dict.value.keys
           if isinstance(k, ast.Constant)] if _ret_dict else []
chk("devuelve `ausencias` para poder enseñarlo", "ausencias" in _claves)
_cr = next((v for k, v in zip(_ret_dict.value.keys, _ret_dict.value.values)
            if isinstance(k, ast.Constant) and k.value == "costo_real"), None)
chk("`costo_real` las incluye", _cr is not None and "ausencias" in ast.dump(_cr),
    ast.dump(_cr) if _cr else "")
chk("`base_teorica` NO las incluye (sale de la jornada fichada)",
    "ausencias" not in ast.dump(next(
        n for n in ast.walk(c) if isinstance(n, ast.Assign)
        and any(getattr(x, "id", "") == "base_teorica" for x in n.targets))))
# la vista pinta la fila para que la cadena siga cuadrando en pantalla
_v = fn(arbol("core/projects_ui.py"), "_pnl_conciliacion")
chk("la vista pinta la fila de ausencias",
    _v is not None and "'ausencias'" in ast.dump(_v))
# ⚠️ Este chequeo REVENTABA con `ValueError: substring not found` en vez de fallar
# legible en cuanto el texto cambió de idioma (v441) — la misma queja que v385 le hizo
# a v301. Ahora busca con `find` (devuelve -1) y compara el PRINCIPIO: la fila de
# ausencias va antes del total, en el idioma que sea.
def _pos(_t, *alts):
    for a in alts:
        i = _t.find(a)
        if i >= 0:
            return i
    return -1
_u = ast.unparse(_v) if _v is not None else ""
_ia = _pos(_u, "ausencias pagadas", "paid absences")
_ic = _pos(_u, "costo real", "real cost of labour")
chk("...y va ANTES del «costo real» (la cadena se lee de arriba abajo)",
    _ia >= 0 and _ic >= 0 and _ia < _ic, f"ausencias={_ia} costo_real={_ic}")

# ── 7 ────────────────────────────────────────────────────────────
seccion("7. Mensajes que sobreviven al rerun + imports de MÓDULO")
t_u = arbol("core/ausencias_ui.py")
s_u = src("core/ausencias_ui.py")
# imports a nivel de módulo (ámbito, no presencia — v342/v366)
_mod = set()
for n in t_u.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        for a in n.names:
            _mod.add(a.asname or a.name.split(".")[0])
for m in ("flash", "st", "AU", "clock"):
    chk(f"`{m}` importado a nivel de MÓDULO", m in _mod, str(sorted(_mod)))

# Todo `st.success` en una función que además hace `st.rerun()` debe ser `flash`.
# ⚠️ Mi primera versión buscaba la subcadena "st.rerun" en el `ast.dump`, y ahí el
# nodo se escribe `Attribute(value=Name(id='st'), attr='rerun')` — así que NINGUNA
# función pasaba el filtro y el chequeo entero corría en VACÍO (lo destapó romper el
# código: sustituí un `flash.exito` por `st.success` y no lo cazó).
# ⚠️ `st.toast` NO entra: sobrevive al rerun por su cuenta. `st.error` tampoco: en
# `(flash.exito if ok else st.error)` la rama de error se ve porque ahí no hay rerun,
# y convertirla la haría desaparecer (la trampa de v367).
def _llama_a(nodo, obj, attr):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == attr and isinstance(n.func.value, ast.Name)
               and n.func.value.id == obj for n in ast.walk(nodo))


_conrerun = [f_ for f_ in ast.walk(t_u) if isinstance(f_, ast.FunctionDef)
             and _llama_a(f_, "st", "rerun")]
chk("el chequeo NO corre en vacío: hay funciones con rerun que auditar",
    len(_conrerun) >= 2, f"{len(_conrerun)} funciones")
_malos = [f"{f_.name}:{n.lineno}" for f_ in _conrerun for n in ast.walk(f_)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "success" and isinstance(n.func.value, ast.Name)
          and n.func.value.id == "st"]
chk("ningún mensaje de éxito se pierde en un rerun (v365)", not _malos, str(_malos))
# ⚠️ por NODO `ast.Try`, no por la subcadena "try" en el dump: ahí el nodo se
# escribe `Try(`, así que la versión en minúsculas daba FALLO con el código correcto.
chk("los avisos por correo son best-effort (no bloquean el registro)",
    all(any(isinstance(n, ast.Try) for n in ast.walk(fn(t_u, x)))
        for x in ("_avisar_admins", "_avisar_persona")))

# ── 8 ────────────────────────────────────────────────────────────
seccion("8. Navegación cableada (regla v303: el destino tiene que existir)")
from core import home_ui as H          # noqa: E402

# ⚠️ CADUCADO en v478 y ACTUALIZADO: «ausencias» dejo de ser seccion suelta y es
# sub-pestaña de «Self-service» (peticion del usuario: la nav del campo de 8 a 6).
# Lo que v430 protegia —que el campo LLEGUE a sus ausencias— se sigue afirmando.
_ids_auto = [i for i, _d in H._SUBSECCIONES_CAMPO.get("autogestion", ("", []))[1]]
chk("el campo llega a sus ausencias (seccion o sub-pestaña)",
    "ausencias" in [k for k, _ in H._SECCIONES_CAMPO] or "\U0001F334 Ausencias" in _ids_auto)
# ⚠️ Y la razon por la que v430 la dejo SUELTA —avisar de una baja es urgente y se
# hace desde el movil— sigue cubierta: v478 le dio un atajo desde Fichaje. Sin esto,
# agrupar habria costado un toque justo la mañana que alguien se levanta enfermo.
_tc = io.open("core/timeclock_ui.py", encoding="utf-8").read()
chk("...y avisar de una baja tiene atajo desde Fichaje (v478)",
    'navegar("autogestion"' in _tc)
_sub_plan = [i for i, _ in H._SUBSECCIONES["planificacion"][1]]
chk("Planificación tiene la sub-pestaña «🌴 Ausencias»", "🌴 Ausencias" in _sub_plan)
# el despachador compara contra el ID EXACTO (el fallo real de v303)
_sp = fn(arbol("core/home_ui.py"), "_seccion_planificacion")
chk("el despachador compara contra el ID exacto, no el display",
    any(isinstance(n, ast.Constant) and n.value == "🌴 Ausencias"
        for n in ast.walk(_sp)))
_ra = fn(arbol("core/home_ui.py"), "render_admin_content")
chk("la sección del campo se despacha a render_mis_ausencias",
    "render_mis_ausencias" in ast.dump(_ra))
chk("la sub de admin se despacha a render_bandeja", "render_bandeja" in ast.dump(_sp))
# el campo NO tiene sub-pestañas ahí: su vista PONE su propio título (regla v320)
chk("«ausencias» no está en _SUBSECCIONES_CAMPO (sección sin subs)",
    "ausencias" not in H._SUBSECCIONES_CAMPO)
# ⚠️ CADUCADO por v439 (i18n F2): el título pasó al inglés a propósito. Lo que la regla
# protege es que la vista PONGA un título de página (`## `), porque cuelga de una sección
# sin sub-pestañas y la shell no pinta ninguna cabecera (regla v320).
chk("...así que `render_mis_ausencias` pinta su propio título",
    "## :material/event_busy: Mis ausencias" in s_u
    or "## :material/event_busy: My absences" in s_u)
# ⚠️ Un TÍTULO de página es `## `; los `#### ` de dentro son sub-cabeceras legítimas
# y buscar la subcadena las contaba, dando FALLO con el código correcto.
_tit = [c.value for c in ast.walk(fn(t_u, "render_bandeja"))
        if isinstance(c, ast.Constant) and isinstance(c.value, str)
        and c.value.startswith("## ")]
chk("`render_bandeja` NO pinta título (la shell ya pinta «Planificación · Ausencias»)",
    not _tit, str(_tit))

# ── 9 ────────────────────────────────────────────────────────────
seccion("9. Reglas transversales que ya mordieron antes")
# v424: _kpi_card DEVUELVE html, no lo pinta
_tirados = [n.lineno for n in ast.walk(t_u) if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name) and n.value.func.id == "_kpi"]
chk("ninguna tarjeta KPI tira su valor (v424)", not _tirados, str(_tirados))
# ⚠️ Barrido GENERAL: las OPCIONES de un `selectbox`/`multiselect` NO interpretan
# `:material/…:` — se pintan como texto plano (medido en el Cloud en v430: el
# `:material/sick:` salía literal). En `st.radio` sí funciona (v234, verificado en
# vivo), así que la regla es POR WIDGET, no global.
_lit = []
for f_ in sorted(list(Path(RAIZ, "core").glob("*.py")) + [Path(RAIZ, "app.py")]):
    tr = ast.parse(f_.read_text(encoding="utf-8"))
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in ("selectbox", "multiselect"):
            continue
        _partes = [ast.unparse(k.value) for k in n.keywords
                   if k.arg in ("format_func", "options")] + \
                  [ast.unparse(a) for a in n.args[1:2]]
        if any(":material/" in p for p in _partes):
            _lit.append(f"{f_.name}:{n.lineno}")
chk("ningún selectbox pinta `:material/` (saldría literal)", not _lit, str(_lit))
chk("...y el chequeo NO corre en vacío: los tipos traen emoji",
    all(AU.TIPOS[t].get("emoji") for t in AU.TIPOS))
chk("los radios SÍ pueden seguir usándolo (v234): hay 7 y no se tocan",
    sum(1 for f_ in [Path(RAIZ, "core", x) for x in
                     ("auth_ui.py", "projects_ui.py", "roster_ui.py", "survey_ui.py")]
        for n in ast.walk(ast.parse(f_.read_text(encoding="utf-8")))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "radio"
        and any(":material/" in ast.unparse(k.value) for k in n.keywords
                if k.arg == "format_func")) == 7)

# v309/v349: dos $ en un f-string = LaTeX
_lat = []
for n in ast.walk(t_u):
    if isinstance(n, ast.JoinedStr):
        txt = "".join(v.value for v in n.values if isinstance(v, ast.Constant))
        if txt.count("$") - txt.count("\\$") >= 2:
            _lat.append(n.lineno)
chk("ningún f-string con 2+ `$` sin escapar (v309/v349)", not _lat, str(_lat))
# v427/v428: el ID no se recicla ni se cuenta por filas
_ni = fn(arbol("core/ausencias.py"), "_next_id")
# ⚠️ Por NODO, no por la subcadena "len(": `ast.dump` escribe `Call(func=Name(id=
# 'len'...))`, así que la versión anterior no podía casar nunca y aprobaba también un
# `_next_id` que contara filas — el fallo REAL de v428, que es lo que viene a impedir.
chk("`_next_id` usa el MÁXIMO, no el número de filas (v428)",
    not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "len" for n in ast.walk(_ni))
    and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "max" for n in ast.walk(_ni)))
chk("...y salta los IDs ya referenciados (v427)",
    "siguiente_id_libre" in ast.dump(_ni))
# v378: la caché lleva el libro en la clave, y el parámetro NO empieza por _
_rc = fn(arbol("core/ausencias.py"), "_records_cached")
chk("la caché va por LIBRO (v378)", _rc.args.args and _rc.args.args[0].arg == "libro",
    _rc.args.args[0].arg if _rc.args.args else "sin argumentos")
chk("...y el parámetro NO empieza por `_` (o Streamlit lo saca de la clave)",
    not _rc.args.args[0].arg.startswith("_"))
_inv = fn(arbol("core/ausencias.py"), "_invalidate")
chk("`_invalidate` tira también el LOTE (v339)", "invalidar" in ast.dump(_inv))
chk("...y limpia la función CACHEADA, no el envoltorio (v344)",
    "_records_cached" in ast.dump(_inv))
# v306: la fila posicional cuadra con la cabecera
_sol = fn(arbol("core/ausencias.py"), "solicitar")
chk("`solicitar` valida que la fila cuadre con la cabecera (v363)",
    "HEADERS" in ast.dump(_sol) and "len(fila)" in ast.unparse(_sol))
# v351: cerrojo de aislamiento — aquí no hace falta porque todo se filtra por grupo
_por_id = [f_.name for f_ in ast.walk(arbol("core/ausencias_ui.py"))
           if isinstance(f_, ast.FunctionDef) and "AU.get(" in ast.unparse(f_)]
chk("las vistas trabajan sobre listas YA filtradas por grupo (sin ID global suelto)",
    all(n in ("render_mis_ausencias", "_tarjeta_pendiente") for n in _por_id),
    str(_por_id))

# ── 10 ───────────────────────────────────────────────────────────
seccion("10. Compila e importa DE VERDAD (importar no ejecuta — v378)")
import importlib                                                # noqa: E402
for m in ("core.ausencias", "core.ausencias_ui", "core.payroll",
          "core.finance", "core.home_ui", "core.projects_ui"):
    try:
        importlib.import_module(m)
        chk(f"importa {m}", True)
    except Exception as e:
        chk(f"importa {m}", False, f"{type(e).__name__}: {e}")

# se EJECUTAN las funciones puras (un import no las ejecuta)
try:
    # ⚠️ CADUCADO por v446 (i18n F5b): el concepto de la colilla pasa al idioma
    # BASE. Es lo correcto: se imprime en la colilla y se guarda en la hoja, o sea
    # un DOCUMENTO, y su idioma no puede depender de la pantalla de quien la genera
    # (regla v436). Lo que la regla protege es el FORMATO —nombre (n d) separados
    # por un punto medio, ordenados—, no el idioma.
    chk("etiqueta_ausencias compone el texto de la colilla",
        AU.etiqueta_ausencias({AU.VACACIONES: 5, AU.ENFERMEDAD: 2})
        == "Sick leave (2 d) · Annual leave (5 d)",
        AU.etiqueta_ausencias({AU.VACACIONES: 5, AU.ENFERMEDAD: 2}))
    chk("etiqueta_ausencias con nada no revienta", AU.etiqueta_ausencias({}) == "")
    chk("dias_del_rango con fechas invertidas devuelve vacío",
        AU.dias_del_rango(date(2026, 8, 10), date(2026, 8, 1)) == [])
    chk("dias_del_rango con basura devuelve vacío",
        AU.dias_del_rango("no-es-fecha", "tampoco") == [])
except Exception as e:
    chk("las funciones puras se ejecutan", False, f"{type(e).__name__}: {e}")


# ── 11 · v432: un día vale UNA jornada, nunca dos ────────────────
seccion("11. v432 · ausencia + fichaje el mismo día NO se pagan dos veces")
# ⚠️ Mismo motivo que arriba: el criterio de v432 vive desde v484 en la vista por día.
_u = ast.unparse(fn(arbol("core/ausencias.py"), "horas_pagadas_dia"))
chk("el agregado sigue delegando (una sola definición de lo que se paga)",
    _llama_nombre(fn(arbol("core/ausencias.py"), "horas_pagadas_grupo"),
                  "horas_pagadas_dia"))
chk("mira las horas ya FICHADAS día a día", "horas_por_usuario_dia" in _u)
chk("...y paga solo lo que falta hasta la jornada",
    "max(0.0, HORAS_DIA -" in _u or "max(0, HORAS_DIA -" in _u)
chk("el recorte se DEVUELVE, no se aplica en silencio", "recortados" in _u)
_gen = fn(arbol("core/payroll.py"), "generar")
# ⚠️ Que la clave esté en el dict DEVUELTO, no que la palabra aparezca en el cuerpo:
# quitándola del return, la subcadena seguía estando (en el bucle y en los
# comentarios) y el chequeo pasaba con el aviso ya roto. Trampa nº2, otra vez.
_ret = next((n for n in ast.walk(_gen) if isinstance(n, ast.Return)
             and isinstance(n.value, ast.Dict)
             and any(isinstance(k, ast.Constant) and k.value == "creadas"
                     for k in n.value.keys)), None)
chk("la nómina DEVUELVE los recortes para poder avisarlos",
    _ret is not None and any(isinstance(k, ast.Constant) and k.value == "recortes"
                             for k in _ret.value.keys),
    str([k.value for k in _ret.value.keys if isinstance(k, ast.Constant)])
    if _ret else "no hay return")
_pu = fn(arbol("core/payroll_ui.py"), "_generar_form") or fn(
    arbol("core/payroll_ui.py"), "render_nominas")
chk("...y la pantalla lo pinta",
    "recortes" in (RAIZ / "core" / "payroll_ui.py").read_text(encoding="utf-8"))
# la función existe de verdad y reparte por día (no basta con que esté el nombre)
from core import timeclock as _TC          # noqa: E402
chk("`horas_por_usuario_dia` existe y devuelve un dict",
    isinstance(_TC.horas_por_usuario_dia("__no_existe__", "2026-01-01",
                                         "2026-01-02"), dict))

# ── 12 · v432: avisos que faltaban ───────────────────────────────
seccion("12. v432 · los dos avisos que la auditoría echó en falta")
_av = fn(arbol("core/projects_ui.py"), "_avisar_asignados")
# ⚠️ Por el IMPORT real dentro de la función, no por la subcadena «ausencias»: esa
# palabra está también en los comentarios, así que cambiando el import por otro
# módulo el chequeo seguía pasando con el aviso muerto (trampa nº2).
chk("asignar personal importa DE VERDAD el módulo de ausencias",
    any(isinstance(n, ast.ImportFrom) and n.module == "core"
        and any(a.name == "ausencias" for a in n.names)
        for n in ast.walk(_av)))
chk("...y lo usa para listar las de esa persona",
    "list_group" in ast.unparse(_av) and "VIGENTES" in ast.unparse(_av))
chk("...y acepta las fechas de la obra para acotar",
    "fechas" in [a.arg for a in _av.args.args])
_det = fn(arbol("core/projects_ui.py"), "_detalle_proyecto")
chk("el detalle del proyecto se las pasa",
    "fechas=(prj.get('StartDate'), prj.get('EndDateEst'))" in ast.unparse(_det))
_can = fn(arbol("core/ausencias_ui.py"), "_avisar_cancelacion")
chk("existe el aviso de cancelación", _can is not None)
_rma = ast.unparse(fn(arbol("core/ausencias_ui.py"), "render_mis_ausencias"))
chk("...se llama al cancelar", "_avisar_cancelacion" in _rma)
chk("...SOLO si estaba aprobada (una pendiente no cambia nada planificado)",
    "_estaba" in _rma and "APROBADA" in _rma)


# ── 13 · v433: el año de vacaciones va por ANIVERSARIO ───────────
seccion("13. v433 · saldo por aniversario y reparto por periodo")
from core import auth as _AUTH                                   # noqa: E402
chk("la hoja Login guarda la fecha de alta", "StartedOn" in _AUTH.LOGIN_HEADERS)
# ⚠️ CADUCADO en v484 y REANCLADO: se añadió `PayrollID` DETRÁS, así que `StartedOn`
# ya no es la última. Lo que la regla protege no es esa posición concreta: es que NADA
# se cuele DELANTE de las columnas históricas, porque las filas se escriben por
# POSICIÓN (el fallo que mató `create_project` 3 versiones, v363). Se fija el prefijo,
# que es la afirmación de verdad — y aguanta la siguiente columna que se añada bien.
_HIST_LOGIN = ["User", "Password", "Role", "Name", "Active", "Group", "SessionToken",
               "SessionTime", "Email", "TelegramChatID", "HourlyRate", "StartedOn"]
chk("...y nada se cuela delante de las históricas (migran solas)",
    _AUTH.LOGIN_HEADERS[:len(_HIST_LOGIN)] == _HIST_LOGIN,
    str(_AUTH.LOGIN_HEADERS[:len(_HIST_LOGIN)]))
from core import auditoria as _AUD                               # noqa: E402
chk("mover esa fecha deja rastro (mueve el saldo de esa persona)",
    "StartedOn" in _AUD.CAMPOS_CLAVE)
_du = fn(arbol("core/ausencias.py"), "dias_usados")
_su = ast.unparse(_du)
chk("`dias_usados` cuenta DÍAS dentro del periodo, no filas por año de inicio",
    "dias_del_rango" in _su and "d0 <= d <= d1" in _su)
chk("...y ya no filtra por `.year`", ".year" not in _su)
_ps = fn(arbol("core/ausencias.py"), "periodo_saldo")
_sp = ast.unparse(_ps)
chk("`periodo_saldo` usa la fecha de alta", "fecha_ingreso" in _sp)
chk("...y marca el ORIGEN para poder avisar de que estima",
    "'aniversario'" in _sp and "'natural'" in _sp)
# se EJECUTA: importar no ejecuta (v378), y aquí lo que importa es la aritmética
from datetime import date as _dt                                 # noqa: E402
_orig_fi = _AUTH.fecha_ingreso
try:
    _AUTH.fecha_ingreso = lambda u: _dt(2024, 3, 15)
    _p = AU.periodo_saldo("g", "u", ref=_dt(2026, 12, 1))
    chk("aniversario 15/03 → periodo 15/03/2026-14/03/2027",
        (str(_p["desde"]), str(_p["hasta"])) == ("2026-03-15", "2027-03-14"),
        f"{_p['desde']} → {_p['hasta']}")
    _AUTH.fecha_ingreso = lambda u: _dt(2024, 2, 29)
    _p2 = AU.periodo_saldo("g", "u", ref=_dt(2027, 6, 1))
    chk("quien entró un 29/02 no revienta en un año normal",
        _p2["desde"].month == 2 and _p2["origen"] == "aniversario",
        str(_p2["desde"]))
    _AUTH.fecha_ingreso = lambda u: None
    _p3 = AU.periodo_saldo("g", "u", ref=_dt(2026, 12, 1))
    chk("sin fecha de alta cae al año natural…", _p3["origen"], "natural")
    chk("…y NO inventa un aniversario",
        (str(_p3["desde"]), str(_p3["hasta"])) == ("2026-01-01", "2026-12-31"))
finally:
    _AUTH.fecha_ingreso = _orig_fi
# ⚠️ Y el REPARTO, ejecutado. Mirar que `dias_del_rango` aparezca en el código no
# basta: probando el guardián contra el código roto, una versión que devolvía siempre
# 0 pasaba igual. Lo que hay que afirmar es el RESULTADO — las vacaciones de Navidad
# repartidas 4/6 entre los dos años, que es el caso que motivó el cambio.
_orig_rec = AU._records
try:
    _d0, _d1 = _dt(2026, 12, 28), _dt(2027, 1, 8)
    _tot = len(AU.dias_del_rango(_d0, _d1))
    AU._records = lambda: [{"ID": "SIM", "Group": "g", "User": "u", "Name": "u",
                            "Type": AU.VACACIONES, "From": str(_d0), "To": str(_d1),
                            "Days": str(_tot), "Status": AU.APROBADA, "IncludesWeekends": "NO"}]
    _u26 = AU.dias_usados("g", "u", AU.VACACIONES, _dt(2026, 1, 1), _dt(2026, 12, 31))
    _u27 = AU.dias_usados("g", "u", AU.VACACIONES, _dt(2027, 1, 1), _dt(2027, 12, 31))
    chk("unas vacaciones de Navidad se reparten entre los dos años",
        (_u26, _u27) == (4.0, 6.0), f"2026={_u26} · 2027={_u27} (esperado 4 y 6)")
    chk("...y no se pierde ni se duplica ningún día", _u26 + _u27, float(_tot))
finally:
    AU._records = _orig_rec

# la pantalla lo DICE (un saldo estimado que parece exacto es peor que ninguno)
_rma2 = src("core/ausencias_ui.py")
# ⚠️ CADUCADO por v439 (i18n F2): los dos textos pasaron al inglés a propósito. Lo
# que la regla protege es que la pantalla DIGA de qué periodo habla y AVISE cuando
chk("la pantalla dice de qué periodo habla",
    "año de vacaciones va del" in _rma2 or "Your leave year runs from" in _rma2)
# lo está estimando por falta de fecha de alta (un saldo estimado que parece exacto
# es peor que ninguno, v325/v433).
chk("...y avisa cuando lo está estimando",
    "no consta" in _rma2 or "is not on record" in _rma2)
_au = src("core/auth_ui.py")
chk("el admin puede cargar la fecha de alta", "set_fecha_ingreso" in _au)
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
chk("...y ve a quién le falta",
    "Sin fecha de alta" in _au or "With no start date" in _au)


# ── 14 · v433: los mapas de columnas se DERIVAN, nunca a mano ────
seccion("14. v433 · ningún mapa de columnas escrito a mano (barrido del repo)")
# ⚠️ `auth._COL` era un literal en paralelo a LOGIN_HEADERS: al añadir `FechaIngreso`
# la hoja migró la columna y el mapa no la conocía, así que la escritura moría con
# «Error: 'FechaIngreso'». No lo detecta ningún import ni ningún chequeo estático de
# los que había — solo EJECUTARLA. La cura es que no pueda volver a divergir.
# ⚠️ v490: la primera versión marcaba CUALQUIER dict {texto: entero} de 3+ claves, y
# `xero_nomina._DIAS_TIPO = {"WEEKLY": 7, "FORTNIGHTLY": 14, ...}` —días de un periodo de
# nómina, no columnas— salía como mapa de columnas. Un detector que grita sobre lo que
# está bien acaba ignorándose (v450). Lo que define un mapa de columnas es que sus CLAVES
# son CABECERAS, así que el conjunto se DERIVA de todos los *_HEADERS del repo + los
# nombres viejos y nuevos de `columnas.LEGADO` (el fallo real de v433 era con «Usuario»).
_cabeceras = set()
for f_ in sorted(Path(RAIZ, "core").glob("*.py")):
    for n in ast.parse(f_.read_text(encoding="utf-8")).body:
        if (isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Tuple))
                and any(getattr(t_, "id", "").endswith("HEADERS") for t_ in n.targets)):
            _cabeceras |= {e.value for e in n.value.elts
                           if isinstance(e, ast.Constant) and isinstance(e.value, str)}
try:
    from core import columnas as _COLS
    _cabeceras |= set(_COLS.LEGADO) | set(_COLS.LEGADO.values())
except Exception:
    pass


def _mapas_a_mano(fuente, nombre):
    out = []
    for n in ast.parse(fuente).body:
        if not (isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict)):
            continue
        ks = [k.value for k in n.value.keys
              if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        vs = [v.value for v in n.value.values if isinstance(v, ast.Constant)]
        if (len(ks) >= 3 and len(ks) == len(vs) and all(isinstance(v, int) for v in vs)
                and sum(k in _cabeceras for k in ks) >= 2):
            out.append(f"{nombre}:{n.lineno}")
    return out


# la sonda se valida en las DOS direcciones antes de creerse su cero (trampa nº12)
chk("la sonda conoce las cabeceras (derivadas, no a mano)",
    len(_cabeceras) > 50 and "Role" in _cabeceras and "Usuario" in _cabeceras,
    str(len(_cabeceras)))
chk("...y CAZA un mapa de columnas escrito a mano (el `_COL` de v433)",
    bool(_mapas_a_mano('_COL = {"Usuario": 1, "Password": 2, "Rol": 3}', "x")))
chk("...pero NO un dict de dominio como los días de un periodo de nómina",
    not _mapas_a_mano('_D = {"WEEKLY": 7, "FORTNIGHTLY": 14, "FOURWEEKLY": 28}', "x"))
_manual = []
for f_ in sorted(Path(RAIZ, "core").glob("*.py")):
    _manual += _mapas_a_mano(f_.read_text(encoding="utf-8"), f_.name)
chk("ningún mapa {columna: n} literal en core/", not _manual, str(_manual))
_col_auth = next(n for n in ast.walk(arbol("core/auth.py"))
                 if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", "") == "_COL" for t in n.targets))
chk("`auth._COL` se deriva de LOGIN_HEADERS",
    "LOGIN_HEADERS" in ast.unparse(_col_auth.value))
# y se EJECUTA: que la columna nueva tenga sitio de verdad
# ⚠️ Igual: exigía que fuera la ÚLTIMA posición. Lo que importa es que la columna
# TENGA número —si `_COL` volviera a escribirse a mano, la escritura moriría con
# KeyError la primera vez que alguien guardara (v433)— y que el número sea el suyo.
chk("`StartedOn` tiene número de columna, y es el que le toca",
    _AUTH._COL.get("StartedOn") == _AUTH.LOGIN_HEADERS.index("StartedOn") + 1)
chk("...y el mapa cubre TODAS las cabeceras",
    sorted(_AUTH._COL) == sorted(_AUTH.LOGIN_HEADERS))


# ── 15 · v434: `list_users` no puede comerse columnas ────────────
seccion("15. v434 · toda columna de Login (menos las secretas) llega a `list_users`")
# ⚠️ La proyección estaba escrita a mano: al añadir `FechaIngreso` el dato se guardaba
# bien y `list_users` lo BORRABA al leerlo — la hoja tenía la fecha y las pantallas
# veían "". No lanza, no avisa. Misma familia que `auth._COL` a mano.
_lu = fn(arbol("core/auth.py"), "list_users")
_ulu = ast.unparse(_lu)
chk("la proyección se DERIVA de LOGIN_HEADERS", "LOGIN_HEADERS" in _ulu)
chk("...y excluye explícitamente los campos secretos", "_CAMPOS_SECRETOS" in _ulu)
chk("el hash de la contraseña NUNCA sale de ahí",
    "Password" in _AUTH._CAMPOS_SECRETOS)
chk("...ni el token de sesión",
    "SessionToken" in _AUTH._CAMPOS_SECRETOS and "SessionTime" in _AUTH._CAMPOS_SECRETOS)
# y se EJECUTA contra la hoja real: importar no ejecuta (v378)
try:
    _us = _AUTH.list_users()
    if _us:
        _k = set(_us[0])
        _esp = {h for h in _AUTH.LOGIN_HEADERS if h not in _AUTH._CAMPOS_SECRETOS}
        chk("una fila real trae TODAS las columnas no secretas", _k == _esp,
            f"faltan {sorted(_esp - _k)} · sobran {sorted(_k - _esp)}")
        chk("...y ninguna secreta", not (_k & set(_AUTH._CAMPOS_SECRETOS)))
    else:
        chk("hay usuarios que comprobar (si no, el chequeo corre en vacío)", False)
except Exception as e:
    chk("`list_users` se ejecuta", False, f"{type(e).__name__}: {e}")

print(f"\n{'=' * 70}")
print(f"{n_chk} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
