"""Ausencias del equipo: vacaciones, día libre y baja por enfermedad (v430).

## Por qué

Hasta ahora la única forma de que alguien constara ausente era que un administrador
le pusiera `OFF` o `LEAVE` a mano en el tablero. O sea: la persona avisaba por fuera
(mensaje, llamada) y alguien tenía que acordarse de reflejarlo. Sin rastro de quién
pidió qué, ni de si se aprobó, ni de cuántos días le quedan.

## Los tres tipos NO tienen el mismo flujo, y eso es deliberado

⚠️ La **baja por enfermedad no se pide por adelantado**: nadie sabe el lunes que el
jueves estará en cama. Se avisa esa mañana o al volver. Meterla en un flujo de
«solicitar → esperar aprobación» haría que la app estorbe justo el día que alguien
está enfermo, y dejaría el tablero mintiendo hasta que un admin entrara a aprobar.
Por eso la enfermedad **se registra ya** (`aprobacion: False`) y el administrador la
ve y la confirma después. Vacaciones y día libre sí van con aprobación previa.

## El saldo se DERIVA, no se guarda

`saldo()` = asignación anual − días ya aprobados de ese tipo en el año. Un saldo
guardado es un número que se desincroniza en cuanto alguien cancela una solicitud o
un admin corrige un rango — el mismo motivo por el que `invoices.estado_cobro` y
`quotes` derivan su estado en vez de almacenarlo (v353).

## Qué NO hace este módulo

No toca el roster ni la nómina: eso lo hacen quienes saben de eso
(`ausencias_ui` → `roster.guardar_persona`, y `payroll` al generar). Aquí solo vive
la solicitud y su estado, para que haya UNA definición de «quién está ausente».
"""
import logging
from datetime import timedelta

import streamlit as st

from core import clock, timeclock
from core import columnas
from core.num import parse_date as _parse_date

from core.i18n import t
logger = logging.getLogger(__name__)

SHEET = "Absences"
HEADERS = ["ID", "Group", "User", "Name", "Type", "From", "To", "Days",
           "Reason", "Status", "ResolvedBy", "ResolvedDate", "AdminNote",
           "CreatedBy", "Created",
           # ⚠️ `Findes` NO es un detalle: sin ella, un rango pedido «con fines de
           # semana» descuenta 12 días del saldo y la nómina paga 8, porque cada
           # lado recuenta el rango con un criterio distinto. Lo cazó ejercitar la
           # nómina de verdad, no leer el código. Va AL FINAL (migra sola) y su
           # valor se añadió a la fila en el mismo cambio (lección v363: cabecera y
           # fila posicional siempre juntas). Una fila anterior no la trae → "" →
           # días hábiles, que era el comportamiento por defecto.
           "IncludesWeekends"]

_COL = {h: i + 1 for i, h in enumerate(HEADERS)}

# ── Estados de la solicitud ──────────────────────────────────────
PENDIENTE, APROBADA, RECHAZADA, CANCELADA = ("pendiente", "aprobada",
                                             "rechazada", "cancelada")
ESTADOS = (PENDIENTE, APROBADA, RECHAZADA, CANCELADA)
# Las que ocupan el calendario: una rechazada o cancelada no bloquea a nadie.
VIGENTES = (PENDIENTE, APROBADA)

# ── Los tipos ────────────────────────────────────────────────────
# `estado_roster` reusa los estados que el tablero YA pinta (`roster.ESTADOS`) en vez
# de inventar otros: el histórico, los colores y `_opciones` siguen funcionando sin
# tocarlos. El tipo concreto viaja en la NOTA del día.
# `dias_anio` y `pagado` son los valores de arranque (AU, jornada completa) y se
# pueden ajustar por grupo — como el margen y el impuesto (v353). ⚠️ Esto NO es un
# motor de convenio: es un registro con saldo, y la app no calcula derechos legales.
# ⚠️ El icono es un EMOJI, no un `:material/…:`. Medido en el Cloud: las OPCIONES de
# un `st.selectbox` se pintan como texto plano —sin nodo de icono y con la fuente del
# cuerpo—, así que el `:material/sick:` salía LITERAL en pantalla. En `st.radio` sí
# se interpreta (v234, verificado en vivo), pero en un selectbox no. Un solo campo, y
# emoji, que se pinta en cualquier sitio.
VACACIONES, ENFERMEDAD, LIBRE = "vacaciones", "enfermedad", "libre"
TIPOS = {
    VACACIONES: {"nombre": "Annual leave", "estado_roster": "LEAVE",
                 "aprobacion": True,  "pagado": True,  "dias_anio": 20,
                 "emoji": "🌴"},
    ENFERMEDAD: {"nombre": "Sick leave", "estado_roster": "LEAVE",
                 # ⚠️ Sin aprobación previa: ver el docstring del módulo.
                 "aprobacion": False, "pagado": True,  "dias_anio": 10,
                 "emoji": "🤒"},
    LIBRE:      {"nombre": "Day off", "estado_roster": "OFF",
                 "aprobacion": True,  "pagado": False, "dias_anio": 0,
                 "emoji": "📅"},
}

def nombre_tipo(tipo) -> str:
    """El nombre visible de un tipo de ausencia, en el idioma de la PANTALLA.

    ⚠️ La traducción va aquí y NO dentro de `TIPOS`: ese dict se construye al
    importar el módulo, cuando no hay sesión, así que un `t()` ahí quedaría
    congelado en el idioma de ese instante (el fallo de `auth.SESION_OCUPADA`,
    v445). `TIPOS` guarda el texto BASE, que es el dato; esto lo traduce al pintarlo.

    ⚠️ En los CORREOS no se usa: un aviso que sale de la empresa va en el idioma
    base, pase lo que pase (regla v436).
    """
    return t(str(TIPOS.get(str(tipo), {}).get("nombre", tipo)))


# Horas que vale un día de ausencia PAGADA en la nómina. Se usa solo para eso.
HORAS_DIA = 8.0


def _libro_de(_hoja) -> str:
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("ausencias: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras: `registros(t, cabeceras)` cae a `get_sheet`, que CREA la
    hoja (regla v145). La crea la primera ESCRITURA, no una lectura."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    """⚠️ El id del libro va en la CLAVE de caché (v378): sin él, `st.cache_data`
    —compartida por proceso— serviría al segundo cliente lo del primero."""
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas                      # v339: tirar también el LOTE
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception:
        pass


# ── Utilidades de fechas ─────────────────────────────────────────
def dias_del_rango(desde, hasta, incluir_findes: bool = False) -> list:
    """Los días naturales de un rango, de lunes a viernes salvo que se pidan todos.

    ⚠️ Por defecto NO cuenta sábado ni domingo: descontar del saldo un fin de semana
    que nadie iba a trabajar es cobrarle a alguien días que no gasta. El tablero sí
    admite fin de semana desde v390, así que se puede pedir con `incluir_findes`.
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1 or d1 < d0:
        return []
    out, d = [], d0
    while d <= d1:
        if incluir_findes or d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def incluye_findes(r: dict) -> bool:
    """¿Ese rango se pidió contando sábado y domingo? (columna `Findes`).

    Una fila anterior a la columna devuelve False, que es lo que hacía entonces.
    """
    return str(r.get("IncludesWeekends", "")).strip().upper() in ("SI", "SÍ", "TRUE", "1")


def _solapan(a0, a1, b0, b1) -> bool:
    """Intersección de intervalos CERRADOS (el criterio de v364 en las nóminas)."""
    return a0 <= b1 and b0 <= a1


# ── Lecturas ─────────────────────────────────────────────────────
def list_group(grupo, estado=None, usuario=None) -> list:
    out = [r for r in _records() if str(r.get("Group", "")) == str(grupo)]
    if estado:
        out = [r for r in out if str(r.get("Status", "")) == estado]
    if usuario is not None:
        out = [r for r in out if str(r.get("User", "")) == str(usuario)]
    return sorted(out, key=lambda r: str(r.get("From", "")), reverse=True)


def pendientes(grupo) -> list:
    """Lo que espera decisión del administrador."""
    return [r for r in list_group(grupo, estado=PENDIENTE)]


def get(aid: str) -> dict:
    return next((r for r in _records() if str(r.get("ID", "")) == str(aid)), {})


def ausentes_en(grupo, dia=None) -> list:
    """Quién está fuera un día concreto (aprobadas y pendientes de enfermedad).

    ⚠️ Cuenta las PENDIENTES además de las aprobadas: una solicitud sin resolver ya
    es un aviso de que esa persona probablemente no esté, y el admin necesita verlo
    ANTES de asignarle una obra — no después de aprobarla.
    """
    dia = dia or clock.today(grupo)
    out = []
    for r in _records():
        if str(r.get("Group", "")) != str(grupo):
            continue
        if str(r.get("Status", "")) not in VIGENTES:
            continue
        d0, d1 = _parse_date(r.get("From")), _parse_date(r.get("To"))
        if d0 and d1 and d0 <= dia <= d1:
            out.append(r)
    return out


def _mismo_dia_mes(anio, mes, dia):
    """La fecha (anio, mes, dia), retrocediendo si ese día no existe ese año.

    ⚠️ Existe por el **29 de febrero**: quien entró un 29/02 no tiene aniversario en
    los años normales, y `date(2027, 2, 29)` lanza. Se usa el 28.
    """
    from datetime import date as _date
    while dia > 28:
        try:
            return _date(anio, mes, dia)
        except ValueError:
            dia -= 1
    from datetime import date as _d2
    return _d2(anio, mes, dia)


def periodo_saldo(grupo, usuario, ref=None) -> dict:
    """El «año de vacaciones» vigente de esa persona: {desde, hasta, origen}.

    ⚠️ Va por el **ANIVERSARIO de alta** de cada uno (decisión del usuario, v433), que
    es lo habitual en AU: quien entró un 15 de marzo cuenta de 15/03 a 14/03. No por
    año natural — con el año natural, el saldo de todo el equipo se reiniciaba el 1 de
    enero aunque cada uno lleve en la empresa desde un mes distinto.

    ⚠️ Sin `FechaIngreso` NO se inventa un aniversario: se cae al año natural y se
    dice (`origen: "natural"`), para que la pantalla pueda avisar de que ese saldo es
    una estimación. Un saldo que parece exacto y no lo es es peor que uno que avisa
    (la lección de v325 y de «sin tarifa» vs «de baja»).
    """
    from datetime import date as _date
    ref = ref or clock.today(grupo)
    try:
        from core import auth
        fi = auth.fecha_ingreso(usuario)
    except Exception as e:
        logger.warning("ausencias.periodo_saldo: %s", e)
        fi = None
    if fi:
        anio = ref.year if (ref.month, ref.day) >= (fi.month, fi.day) else ref.year - 1
        d0 = _mismo_dia_mes(anio, fi.month, fi.day)
        d1 = _mismo_dia_mes(anio + 1, fi.month, fi.day) - timedelta(days=1)
        return {"desde": d0, "hasta": d1, "origen": "aniversario", "ingreso": fi}
    return {"desde": _date(ref.year, 1, 1), "hasta": _date(ref.year, 12, 31),
            "origen": "natural", "ingreso": None}


def dias_usados(grupo, usuario, tipo, desde=None, hasta=None) -> float:
    """Días APROBADOS de ese tipo DENTRO del periodo [desde, hasta] (base del saldo).

    ⚠️ Cuenta los DÍAS que caen dentro, no las filas cuyo `Desde` cae en el año. Antes
    una ausencia se descontaba ENTERA del año en que empezaba, así que unas vacaciones
    de Navidad (28/12 → 08/01, 10 días hábiles) le quitaban **los 10 a 2026** y **0 a
    2027**, cuando en realidad son 4 y 6. El total salía bien y el reparto por año, no.

    ⚠️ Solo las aprobadas: contar las pendientes haría que el saldo bajara antes de
    que nadie decidiera nada, y una solicitud rechazada devolvería días que nunca se
    gastaron. La enfermedad se registra ya aprobada, así que cuenta desde el aviso.
    """
    if desde is None or hasta is None:
        p = periodo_saldo(grupo, usuario)
        desde, hasta = p["desde"], p["hasta"]
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1:
        return 0.0
    tot = 0
    for r in _records():
        if (str(r.get("Group", "")) != str(grupo)
                or str(r.get("User", "")) != str(usuario)
                or str(r.get("Type", "")) != str(tipo)
                or str(r.get("Status", "")) != APROBADA):
            continue
        # los MISMOS días que se pidieron (con o sin fin de semana), recortados al
        # periodo — la misma regla que usa el pago (`horas_pagadas_grupo`)
        tot += sum(1 for d in dias_del_rango(r.get("From"), r.get("To"),
                                             incluye_findes(r))
                   if d0 <= d <= d1)
    return round(float(tot), 1)


def saldo(grupo, usuario, tipo, ref=None) -> dict:
    """{asignados, usados, restantes, periodo} — DERIVADO, nunca guardado (ver módulo)."""
    cfg = TIPOS.get(tipo, {})
    asignados = float(cfg.get("dias_anio", 0) or 0)
    p = periodo_saldo(grupo, usuario, ref)
    usados = dias_usados(grupo, usuario, tipo, p["desde"], p["hasta"])
    return {"asignados": asignados, "usados": usados,
            "restantes": round(asignados - usados, 1),
            "ilimitado": asignados <= 0, "periodo": p}


def solapadas(grupo, usuario, desde, hasta, excluir=None) -> list:
    """Ausencias VIGENTES de esa persona que pisan el rango pedido.

    ⚠️ Mismo criterio que v364 con las nóminas: comprobar la terna exacta no basta,
    porque el caso que hace daño es el rango que se MONTA sobre otro. Pedir dos veces
    los mismos días descontaría el saldo dos veces.
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1:
        return []
    out = []
    for r in _records():
        if (str(r.get("Group", "")) != str(grupo)
                or str(r.get("User", "")) != str(usuario)
                or str(r.get("Status", "")) not in VIGENTES):
            continue
        if excluir and str(r.get("ID", "")) == str(excluir):
            continue
        e0, e1 = _parse_date(r.get("From")), _parse_date(r.get("To"))
        if e0 and e1 and _solapan(d0, d1, e0, e1):
            out.append(r)
    return out


def horas_pagadas_grupo(grupo, desde, hasta) -> dict:
    """Horas de ausencia PAGADA de TODO el grupo en un periodo, en UNA pasada.

    ⚠️ Esto es lo que evita que aprobar unas vacaciones signifique cobrar $0: la base
    de la nómina sale de las horas FICHADAS (`timeclock.horas_por_usuario_rango`), y
    quien está de vacaciones no ficha. Devuelve `{usuario: {horas, dias, por_tipo,
    nombre, recortados}}`.

    ⚠️ **UN DÍA VALE UNA JORNADA, NUNCA DOS** (decisión del usuario, v432). Si esa
    persona además FICHÓ ese día, la ausencia paga solo lo que FALTA hasta la jornada:
    fichó 3 h → se le añaden 5; fichó 8,75 → no se le añade nada. Sin esto se cobraba
    dos veces el mismo día — medido en la hoja real: 8,75 h trabajadas + 8 h de baja =
    $670 por un día, y ninguna línea de la colilla se veía mal (solo el total del día
    delataba). Es el fallo de v364 con otra forma.
    ⚠️ Lo recortado se DEVUELVE (`recortados`) en vez de aplicarse en silencio: un
    ajuste de dinero que nadie ve es la mitad del problema que se viene a arreglar.

    ⚠️ Solo cuenta los días que caen DENTRO del periodo pedido: una ausencia a caballo
    de dos nóminas se reparte, no se paga entera en la primera.

    ⚠️ Es de GRUPO y no por persona a propósito: `payroll.generar` la necesita para
    todo el equipo, y llamarla en el bucle recorrería la lista una vez por trabajador.
    `horas_pagadas` (una persona) sale de aquí, para que haya UNA definición de qué
    día de ausencia se paga (la lección de los cinco `_num` divergentes de v323).
    """
    d0, d1 = _parse_date(desde), _parse_date(hasta)
    if not d0 or not d1:
        return {}
    # jornada ya fichada, día a día, para no pagar dos veces el mismo día
    try:
        fichadas = timeclock.horas_por_usuario_dia(grupo, d0, d1)
    except Exception as e:
        # ⚠️ Si esto falla NO se paga a ciegas la jornada completa: se deja el día sin
        # recorte y se dice en `recortados`, para que el aviso de la nómina lo saque.
        logger.warning("ausencias: no se pudieron leer las horas fichadas: %s", e)
        fichadas = {}
    out = {}
    for r in _records():
        if (str(r.get("Group", "")) != str(grupo)
                or str(r.get("Status", "")) != APROBADA):
            continue
        tipo = str(r.get("Type", ""))
        if not TIPOS.get(tipo, {}).get("pagado"):
            continue
        # ⚠️ Los MISMOS días que se descontaron del saldo, no un recuento propio:
        # si el rango se pidió con fin de semana, `Dias` los cuenta y la paga
        # también. Lo contrario le quitaba 12 días de saldo pagándole 8.
        _d = [d for d in dias_del_rango(r.get("From"), r.get("To"),
                                        incluye_findes(r))
              if d0 <= d <= d1]
        if not _d:
            continue
        clave = str(r.get("User", ""))
        e = out.setdefault(clave, {"horas": 0.0, "dias": 0.0, "por_tipo": {},
                                   "nombre": str(r.get("Name") or clave),
                                   "recortados": []})
        _suyas = fichadas.get(clave, {})
        for d in _d:
            _ya = float(_suyas.get(d, 0.0) or 0.0)
            _pag = max(0.0, HORAS_DIA - _ya)
            e["horas"] = round(e["horas"] + _pag, 2)
            if _ya > 0:
                e["recortados"].append({"fecha": d, "fichadas": round(_ya, 2),
                                        "pagadas": round(_pag, 2), "tipo": tipo})
        e["por_tipo"][tipo] = e["por_tipo"].get(tipo, 0) + len(_d)
        e["dias"] += len(_d)
    return out


def horas_pagadas(grupo, usuario, desde, hasta) -> dict:
    """Lo mismo, para UNA persona. Delega para no duplicar el criterio."""
    return (horas_pagadas_grupo(grupo, desde, hasta).get(str(usuario))
            or {"horas": 0.0, "dias": 0.0, "por_tipo": {},
                "nombre": str(usuario), "recortados": []})


def etiqueta_ausencias(por_tipo: dict) -> str:
    """«Annual leave (5 d) · Sick leave (2 d)» — el concepto de la COLILLA.

    ⚠️ Va en el idioma BASE a propósito, y por eso lee `TIPOS[...]["nombre"]` crudo
    en vez de `nombre_tipo()`: esto se imprime en la colilla y se guarda como
    concepto de la nómina, o sea un DOCUMENTO — su idioma no puede depender de cómo
    tenga la pantalla quien pulsa «generar» (regla v436).

    ⚠️ La variable del generador se llama `_tp` y no `t`: aquí no tapa nada (una
    comprensión tiene su propio ámbito, trampa nº3), pero el día que alguien meta un
    `t(...)` dentro de este generador se encontraría con el tipo de ausencia en vez
    de la función, y eso no lo ve ni `compileall` ni el import.
    """
    return " · ".join(
        f"{TIPOS.get(_tp, {}).get('nombre', _tp)} ({int(n)} d)"
        for _tp, n in sorted((por_tipo or {}).items()))


# ── Enganche con el PLANIFICADOR ─────────────────────────────────
def choques(grupo, usuario, desde, hasta) -> list:
    """Obras a las que esa persona YA está asignada dentro del rango.

    ⚠️ Esto es «todo lo que implica» aprobar: si alguien pide una semana en la que ya
    tiene tres obras, aprobar sin mirar deja esas obras sin nadie **y nadie se entera**
    hasta el lunes. Se le enseña al administrador ANTES de decidir.

    Devuelve `[{fecha, dia, asig, etiqueta, proyecto_id}]`, solo lo que es TRABAJO:
    un `OFF` o un `LEAVE` que ya estuviera puesto no es un choque, es lo mismo que se
    está pidiendo.
    """
    from core import roster as R
    out = []
    dias = dias_del_rango(desde, hasta, incluir_findes=True)
    if not dias:
        return out
    # Una lectura por SEMANA, no por día (con 15 días serían 15 lecturas).
    for lunes in sorted({R.lunes_de(d) for d in dias}):
        try:
            sem = R.get_semana(grupo, lunes)
        except Exception as e:
            logger.warning("ausencias.choques: %s", e)
            continue
        celdas = (sem.get(str(usuario), {}) or {})
        tidx = None
        for d in dias:
            if R.lunes_de(d) != lunes:
                continue
            dia = R.DIAS_TODOS[d.weekday()]
            raw = R._norm_cell(celdas.get(dia, {}))
            for it in raw.get("items", []):
                asig = str(it.get("asig", "") or "")
                if not asig or asig in R.ESTADOS:      # OFF/LEAVE no es un choque
                    continue
                if tidx is None:
                    tidx = R.trabajos_idx(grupo)
                out.append({"fecha": d, "dia": dia, "asig": asig,
                            "etiqueta": R.etiqueta_de(asig, tidx),
                            "proyecto_id": R.proyecto_de(asig, tidx)})
    return out


def aplicar_al_roster(a: dict, quitar: bool = False) -> tuple:
    """Escribe (o retira) la ausencia en el planificador. Devuelve (ok, n_dias|error).

    ⚠️ **PISA lo que hubiera** en esos días, a propósito: si la ausencia está aprobada,
    esa persona no está, y dejar la obra asignada haría que el tablero, la ruta del día
    y «plan vs real» siguieran contando con ella. Lo que se pisó se le enseña antes al
    administrador (`choques`), para que decida el sustituto con la información delante
    en vez de descubrirlo el lunes.

    ⚠️ `quitar=True` NO devuelve la asignación anterior: se limpia el día. Restaurar
    una obra que quizá ya se reasignó a otra persona sería peor que dejar el hueco —
    un hueco se ve en la cobertura del día; un doble asignado, no.

    Una escritura por SEMANA (`guardar_persona` escribe la fila entera), no por día.
    """
    from core import roster as R
    tipo = str(a.get("Type", ""))
    cfg = TIPOS.get(tipo, {})
    estado = cfg.get("estado_roster", "OFF")
    usuario = str(a.get("User", ""))
    grupo = str(a.get("Group", ""))
    # Se marcan TODOS los días del rango, fin de semana incluido: si la persona no
    # está, no está — y el tablero ya admite sábado y domingo desde v390.
    dias = dias_del_rango(a.get("From"), a.get("To"), incluir_findes=True)
    if not dias:
        return False, t("The range has no days.")
    nota = f"{cfg.get('nombre', tipo)} · {a.get('ID', '')}"
    n = 0
    for lunes in sorted({R.lunes_de(d) for d in dias}):
        try:
            sem = R.get_semana(grupo, lunes)
            celdas = dict(sem.get(usuario, {}) or {})
            for d in dias:
                if R.lunes_de(d) != lunes:
                    continue
                dia = R.DIAS_TODOS[d.weekday()]
                if quitar:
                    # solo se retira lo que puso ESTA ausencia (por su ID en la nota)
                    _c = R._norm_cell(celdas.get(dia, {}))
                    if str(a.get("ID", "")) in str(_c.get("nota", "")):
                        celdas.pop(dia, None)
                        n += 1
                else:
                    celdas[dia] = {"asig": estado, "nota": nota}
                    n += 1
            ok, msg = R.guardar_persona(grupo, lunes, usuario, celdas)
            if not ok:
                return False, msg
        except Exception as e:
            logger.warning("ausencias.aplicar_al_roster: %s", e)
            return False, str(e)
    return True, n


def sustitutos(grupo, fecha, proyecto_id=None, excluir=None) -> list:
    """Quién podría cubrir ese día: libre, sin ausencia y con los certificados.

    Reusa lo que ya sabe la app en vez de inventar un criterio nuevo: `roster` dice
    quién tiene el día ocupado y `credentials.compliance` si cumple lo que la obra
    exige (v219). Devuelve `[{usuario, nombre, cumple, faltan}]`.
    """
    from core import roster as R, auth
    fuera = {str(x.get("User", "")) for x in ausentes_en(grupo, fecha)}
    try:
        gente = [u for u in auth.list_users(grupo)
                 if str(u.get("Role", "")) == "campo"
                 and str(u.get("Active", "SI")).upper() != "NO"]
    except Exception:
        return []
    try:
        sem = R.get_semana(grupo, R.lunes_de(fecha))
    except Exception:
        sem = {}
    dia = R.DIAS_TODOS[fecha.weekday()]
    _req = []
    if proyecto_id:
        try:
            from core import projects as P
            _p = P.get_project(proyecto_id) or {}
            _req = [x.strip() for x in str(_p.get("RequiredCerts", "")).split(";") if x.strip()]
        except Exception:
            _req = []
    out = []
    for u in gente:
        us = str(u.get("User", ""))
        if us == str(excluir) or us in fuera:
            continue
        if R._norm_cell((sem.get(us, {}) or {}).get(dia, {})).get("items"):
            continue                                   # ese día ya tiene algo
        cumple, faltan = True, []
        if _req:
            try:
                from core import credentials as C
                _c = C.compliance(us, _req)
                cumple = bool(_c.get("cumple"))
                faltan = [t for t, e in (_c.get("por_tipo") or {}).items()
                          if e in ("falta", "vencido")]
            except Exception:
                pass
        out.append({"usuario": us, "nombre": str(u.get("Name") or us),
                    "cumple": cumple, "faltan": faltan})
    # los que cumplen primero: el admin ve antes a quien puede ir de verdad
    return sorted(out, key=lambda x: (not x["cumple"], x["nombre"]))


# ── Escrituras ───────────────────────────────────────────────────
def _next_id(recs) -> str:
    """AUS-#### sin reciclar (v427/v428): el ID de una ausencia se referencia desde el
    roster (en la nota del día), así que reutilizarlo mezclaría dos historiales."""
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("AUS-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    try:
        from core import hojas
        return hojas.siguiente_id_libre("AUS-", mx, propia=SHEET)
    except Exception as e:
        logger.warning("ausencias: no se pudo comprobar IDs referenciados: %s", e)
        return f"AUS-{mx + 1:04d}"


def solicitar(grupo, usuario, nombre, tipo, desde, hasta, motivo="",
              incluir_findes=False) -> tuple:
    """Crea la solicitud. Devuelve (ok, id|error).

    ⚠️ La enfermedad nace **aprobada**: no se pide permiso para estar enfermo (ver el
    docstring del módulo). El administrador la ve igual y puede rechazarla después si
    hace falta, pero mientras tanto el tablero YA dice la verdad.
    """
    if tipo not in TIPOS:
        return False, f"{t('Unknown absence type')}: {tipo}"
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    # ⚠️ Dos motivos DISTINTOS para no tener días, y decirlos como si fueran el mismo
    # manda a corregir lo que no está mal. Lo cazó el ejercicio: hoy era sábado, así
    # que una baja por enfermedad de HOY a HOY salía «la fecha de fin no puede ser
    # anterior a la de inicio» — con las fechas perfectamente bien. Quien se pone malo
    # un fin de semana no podía registrarlo, y encima el mensaje mentía.
    _d0, _d1 = _parse_date(desde), _parse_date(hasta)
    if not _d0 or not _d1:
        return False, t("The dates could not be read.")
    if _d1 < _d0:
        return False, t("The end date cannot be earlier than the start date.")
    dias = dias_del_rango(desde, hasta, incluir_findes)
    if not dias:
        return False, t("That range only covers the weekend. If those days are "
                        "worked, tick «include weekends».")
    _sol = solapadas(grupo, usuario, desde, hasta)
    if _sol:
        _r = _sol[0]
        return False, (f"{t('There is already an absence overlapping those dates')}: "
                       f"{_r.get('ID')} ({TIPOS.get(str(_r.get('Type')), {}).get('nombre', _r.get('Type'))}, "
                       f"{_r.get('From')} → {_r.get('To')}, {_r.get('Status')}).")

    cfg = TIPOS[tipo]
    estado = PENDIENTE if cfg["aprobacion"] else APROBADA
    hoy = clock.now(grupo).strftime("%Y-%m-%d %H:%M")
    fila = [_next_id(columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))),
            str(grupo), str(usuario), str(nombre or usuario), str(tipo),
            _d0.strftime("%Y-%m-%d"), _d1.strftime("%Y-%m-%d"), str(len(dias)),
            str(motivo or ""), estado,
            # una que nace aprobada la «resuelve» el propio sistema, y se dice
            (t("(automatic)") if estado == APROBADA else ""),
            (hoy if estado == APROBADA else ""), "",
            str(usuario), hoy,
            ("SI" if incluir_findes else "NO")]
    if len(fila) != len(HEADERS):
        return False, (f"{t('Internal error: the row has')} {len(fila)} "
                       f"{t('values and the header has')} "
                       f"{len(HEADERS)} {t('columns.')}")
    try:
        w.append_row(fila, value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, fila[0]


def resolver(aid, aprobar: bool, quien, nota="") -> tuple:
    """Aprueba o rechaza una solicitud PENDIENTE. Devuelve (ok, mensaje).

    ⚠️ Solo actúa sobre lo pendiente. Mi primera versión aceptaba cualquier estado
    «vigente», y como una APROBADA lo es, se podía **rechazar unas vacaciones ya
    concedidas** —con los días puestos en el tablero y la persona con los billetes
    comprados— desde el mismo botón, sin más aviso. Para deshacer una aprobada está
    `cancelar`, que es explícito y conserva el histórico.
    """
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    try:
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))   # FRESCO: es escritura
    except Exception as e:
        return False, f"Error leyendo: {e}"
    fila = next((i + 2 for i, r in enumerate(recs)
                 if str(r.get("ID", "")) == str(aid)), None)
    if fila is None:
        return False, t("Request not found.")
    actual = str(recs[fila - 2].get("Status", ""))
    if actual != PENDIENTE:
        return False, (f"{t('That request is already')} **{actual}**; "
                       + t("it cannot be resolved again. To undo an approved "
                           "absence, cancel it."))
    nuevo = APROBADA if aprobar else RECHAZADA
    from core.num import col_letter as _cl
    try:
        w.batch_update([
            {"range": f"{_cl(_COL['Status'])}{fila}", "values": [[nuevo]]},
            {"range": f"{_cl(_COL['ResolvedBy'])}{fila}", "values": [[str(quien)]]},
            {"range": f"{_cl(_COL['ResolvedDate'])}{fila}",
             "values": [[clock.now().strftime("%Y-%m-%d %H:%M")]]},
            {"range": f"{_cl(_COL['AdminNote'])}{fila}", "values": [[str(nota or "")]]},
        ], value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, (t("Absence approved.") if aprobar else t("Request rejected."))


def cancelar(aid, quien) -> tuple:
    """Cancela una solicitud propia (o ya aprobada: los planes cambian).

    ⚠️ Cancelar NO borra la fila: se marca. Así el histórico se conserva y el saldo
    vuelve a subir solo, porque `dias_usados` cuenta únicamente las aprobadas.
    """
    w = _ws()
    if w is None:
        return False, t("Google Sheets is not configured.")
    try:
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        return False, f"Error leyendo: {e}"
    fila = next((i + 2 for i, r in enumerate(recs)
                 if str(r.get("ID", "")) == str(aid)), None)
    if fila is None:
        return False, t("Request not found.")
    if str(recs[fila - 2].get("Status", "")) not in VIGENTES:
        return False, t("That request is no longer active.")
    from core.num import col_letter as _cl
    try:
        w.batch_update([
            {"range": f"{_cl(_COL['Status'])}{fila}", "values": [[CANCELADA]]},
            {"range": f"{_cl(_COL['ResolvedBy'])}{fila}", "values": [[str(quien)]]},
            {"range": f"{_cl(_COL['ResolvedDate'])}{fila}",
             "values": [[clock.now().strftime("%Y-%m-%d %H:%M")]]},
        ], value_input_option="RAW")
    except Exception as e:
        return False, f"{t('Error saving')}: {e}"
    _invalidate()
    return True, t("Absence cancelled.")
