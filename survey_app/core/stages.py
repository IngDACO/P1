# -*- coding: utf-8 -*-
"""Catálogo de etapas y actividades de instalación de ascensores (v512).

## Qué es

El **menú ponderado** de todo lo que se puede hacer en una obra: 14 etapas de
instalación que suman 100%, 4 de desmontaje que suman otro 100%, y ~170 actividades
con su peso dentro de su etapa. Sale del trabajo de campo de COPEX
(`Lift_Install_Stage_Activity_Draft_v1.md`), no de ninguna suposición mía.

    avance de una actividad en el total = peso de la etapa × peso de la actividad / 100

## ⚠️ Por qué es order-independent, y por qué importa

Una obra real **salta de un lado a otro**: se cablea antes de terminar de montar, se
vuelve a una etapa ya tocada, se hace la mitad de una cosa y se sigue otro día. El
modelo anterior (`schedule.PHASES`) describía una secuencia ideal de 11 fases, y
medir contra una secuencia que nadie sigue obliga a estimar «¿cuánto va de esta fase?»
a ojo.

Esto es lo contrario: un menú fijo donde cada cosa hecha **suma su peso**, la haya
hecho en el orden que sea. El cronograma sigue existiendo —las ETAPAS son las
actividades del cronograma, con sus duraciones y predecesoras— pero el avance de cada
etapa ya no se teclea: se calcula desde abajo.

## ⚠️ Los condicionales NO entran en el denominador

Muchas actividades solo aplican a algunas obras: el espejo, el falso coche (sky
climber / sky lock), el ascensor de obra, y sobre todo el par **tracción / hidráulico**
del desmontaje, que son excluyentes entre sí — una obra es de una clase o de la otra,
nunca de las dos.

Si las no aplicables se quedaran en el denominador, **ninguna obra podría llegar al
100%**: un desmontaje de tracción se quedaría clavado en el 85% de su R3 para siempre.
Por eso al dar de alta la obra solo se crean las actividades que aplican, y
`projects.compute_avance` —que es Σ(peso·avance)/Σpeso, escala-invariante— hace el
resto sin un solo cambio.

## ⚠️ Los pesos son PROVISIONALES y por eso van versionados

El documento de origen lo dice cuatro veces: *«all weights above are temporary
placeholders»*, *«NOT field-verified yet»*. Van a cambiar.

Y cambiarlos **mueve el avance de toda obra en curso**, que es lo que se reclama en
dinero (v507/v510). Una reclamación ya emitida está a salvo porque congela sus números,
pero la siguiente saldría distinta sin que nadie haya tocado nada en terreno. Por eso
cada juego lleva `VERSION` y la obra guarda con cuál nació: recalibrar crea un juego
nuevo y las obras existentes conservan el suyo hasta que alguien las migre a propósito.

## Módulo HOJA

No importa nada de `core`. Es un catálogo con aritmética pura, así que se puede
ejercitar entero sin Sheets ni Streamlit — la lección de `quote_from_plan` (v509).
"""

VERSION = "2026-09-22"          # juego de pesos; ver el aviso de arriba

PISTA_INSTALL = "install"
PISTA_RIPOUT = "ripout"
PISTAS = (PISTA_RIPOUT, PISTA_INSTALL)

# ⚠️ Cuánto del trabajo de una obra «Ripout + Installation» es el desmontaje.
# El documento de origen trata las dos pistas como 100% SEPARADOS y no da este número;
# hace falta porque el usuario decidió (22/09/2026) que el tipo combinado es UNA obra
# con todas las actividades juntas, o sea un solo 100%.
# 14.0 es lo que la app venía diciendo sin decirlo: `schedule.FASE_RIPOUT` pesaba 15
# contra 93 del resto de fases = 13,9%. Es un ARRANQUE, no un dato de campo.
PCT_RIPOUT_DEFECTO = 14.0

# ── Etapas: (pista, nº, nombre, peso dentro de su pista) ─────────────────────
ETAPAS = [
    (PISTA_RIPOUT, 0, "Set Up (rip-out)", 10),
    (PISTA_RIPOUT, 1, "Take Possession & Initial Shutdown", 13),
    (PISTA_RIPOUT, 2, "Tirak Installation & Transfer to Temporary Drive", 35),
    (PISTA_RIPOUT, 3, "Full Rip-Out", 42),

    (PISTA_INSTALL, 1, "Set Up", 3),
    (PISTA_INSTALL, 2, "Prepping", 3),
    (PISTA_INSTALL, 3, "Plumbing & Survey", 5),
    (PISTA_INSTALL, 4, "Car Assembly", 11),
    (PISTA_INSTALL, 5, "Counterweight (CW) Assembly", 5),
    (PISTA_INSTALL, 6, "Shaft Climb & Bedplates", 13),
    (PISTA_INSTALL, 7, "Landing Doors", 11),
    (PISTA_INSTALL, 8, "Pit Mechanical", 4),
    (PISTA_INSTALL, 9, "Headroom Wiring", 7),
    (PISTA_INSTALL, 10, "Cabin Wiring", 10),
    (PISTA_INSTALL, 11, "Shaft Wiring", 10),
    (PISTA_INSTALL, 12, "Pit Wiring", 4),
    (PISTA_INSTALL, 13, "Belting & Finishes", 5),
    (PISTA_INSTALL, 14, "Commissioning & Tuning", 9),
]

# ── Actividades: (pista, nº de etapa) → [(nombre, peso %, condicional)] ──────
# `condicional` = solo aplica a algunas obras. Ver el aviso del denominador arriba.
ACTIVIDADES = {
    (PISTA_RIPOUT, 0): [
        ("Toolbox/gear delivery for installer", 18, False),
        ("Rip-out kit delivery", 18, False),
        ("Hoardings & protection", 27, False),
        ("Build working deck(s)", 7, True),
        ("General preparation of building/site/compound", 20, False),
        ("Other deliveries", 10, False),
    ],
    (PISTA_RIPOUT, 1): [
        ("Take possession of lift", 20, False),
        ("Initial electrical shutdown/isolation", 30, False),
        ("Install top-of-shaft beam/hook point", 50, False),
    ],
    (PISTA_RIPOUT, 2): [
        ("Position cabin at correct height", 7, False),
        ("Fully kill lift electrically / route mains power to tirak", 11, False),
        ("Mount tirak", 9, False),
        ("Setup electric chain block", 8, False),
        ("Attach tirak to cabin", 9, False),
        ("Hang tirak on hook point", 11, False),
        ("Drive up with tirak, collect cabin on temporary motor", 14, False),
        ("Release pressure from old ropes/belts OR detach piston", 16, False),
        ("Confirm free movement under tirak only, lift fully isolated", 15, False),
    ],
    (PISTA_RIPOUT, 3): [
        # ⚠️ Tracción e hidráulico son EXCLUYENTES: una obra es de una clase o de la
        # otra. Condicionales las dos, o la que no aplique dejaría el R3 sin poder
        # pasar del 85%.
        ("Rip out mechanical components - traction", 25, True),
        ("Rip out mechanical components - hydraulic", 15, True),
        ("Rip out electrical components", 25, False),
        ("Retain/preserve components for reuse", 10, True),
        ("Final clear-out / site prepared for new install", 25, False),
    ],

    (PISTA_INSTALL, 1): [
        ("Receive toolbox", 6, False),
        ("Receive Inex kit", 9, False),
        ("Receive lift delivery", 12, False),
        ("Count/verify all boxes against delivery manifest", 12, False),
        ("Check box codes (multi-lift sites)", 8, False),
        ("Paperwork (hand-over/procedure forms, SWMS sign-off)", 12, False),
        ("Snap test (trimmer beam/hook point load test)", 8, False),
        ("Builders lift protection & handover", 6, True),
        ("Hang temporary work lighting", 4, False),
        ("Compound/Hoardings", 8, False),
        ("Install sky climber", 9, True),
        ("Install sky lock", 6, True),
    ],
    # ⚠️ Stage 2 RECALIBRADA (22/09/2026). Las 14 actividades sumaban **106**, no 100:
    # «Fire services access & assist» se añadió en sep-2026 con un 6% sin rebalancear
    # el resto — sin esa fila las otras trece suman 100 clavadas. Se reescaló
    # proporcionalmente (×100/106) para no inventar criterio de oficio que no tengo.
    # Y el peso de etapa es **3%**, no el 4% del encabezado del documento: con 4% el
    # total de las catorce etapas daría 101; con 3% da exactamente 100.
    (PISTA_INSTALL, 2): [
        ("Clean rails", 9.4, False),
        ("Clean fishplates", 6.6, False),
        ("Install fishplates to rails (male side)", 7.6, False),
        ("Prep doors (panels/blades, frames)", 11.3, False),
        ("Prep cabin walls", 7.5, False),
        ("Prep cabin doors", 5.7, False),
        ("Prep cabin reveals", 5.7, False),
        ("Prep COP", 7.5, False),
        ("Prep sills", 7.5, False),
        ("Prep landing door headers", 7.5, False),
        ("Prep cabin panels", 6.6, False),
        ("Prep cabin header", 5.7, False),
        ("Assist concrete cutting", 5.7, False),
        ("Fire services access & assist", 5.7, False),
    ],
    (PISTA_INSTALL, 3): [
        ("Set plumb template", 9, False),
        ("Build frame for template", 13, False),
        ("Mount plumbline frame + template", 13, False),
        ("Throw plumblines, attach weights, let settle", 13, False),
        ("Record measurements on wall", 9, False),
        ("Install pit plumb brackets", 13, False),
        ("Adjust pit brackets to gravity reference", 9, False),
        ("Survey (verify vs. existing shaft)", 9, False),
        ("Remove plumb template/frame", 12, False),
    ],
    (PISTA_INSTALL, 4): [
        ("Install first 2 rings", 5, False),
        ("Install first 2 car rails", 5, False),
        ("Install car guide shoes", 4, False),
        ("Install U/Wing brackets", 5, False),
        ("Install yoke/base, level it", 5, False),
        ("Install platform (cradle)", 5, False),
        ("Throw fillerweights", 4, False),
        ("Install cabin sill", 4, False),
        ("Build cabin (walls)", 6, False),
        ("Install cabin doors", 5, False),
        ("Install cabin ceiling (roof)", 4, False),
        ("Install uprights", 4, False),
        ("Install top bow", 3, False),
        ("Install cabin header (mechanical)", 4, False),
        ("Install COP (mechanical)", 4, False),
        ("Install cabin interior handrails/kickplates/bumpers", 4, False),
        ("Attach tirak + stopblock", 4, False),
        ("Attach speed governor rope to cabin", 4, False),
        ("Quick-calibrate safety gripper (initial)", 3, False),
        ("Install spear", 4, False),
        ("Install rooftop handrail", 4, False),
        ("Install mirror", 4, True),
        ("Install cabin toe guard", 3, False),
        ("Earth cabin platform", 3, False),
    ],
    (PISTA_INSTALL, 5): [
        ("Install first 2 CW rails", 30, False),
        ("Install CW guide shoes", 15, False),
        ("Install props", 25, False),
        ("Install CW tank", 30, False),
    ],
    (PISTA_INSTALL, 6): [
        ("Install rings to top", 22, False),
        ("Install car rails to top", 18, False),
        ("Install CW rails to top", 18, False),
        ("Install motor bedplate", 17, False),
        ("Install single bedplate", 13, False),
        ("Seal machine room / shaft penetrations", 12, False),
    ],
    (PISTA_INSTALL, 7): [
        ("Install rots", 7, False),
        ("Install sills", 11, False),
        ("Install frames", 13, False),
        ("Install headers", 11, False),
        ("Groutguarding (fire-rated)", 9, False),
        ("Install door panels", 16, False),
        ("Install skirts", 9, False),
        ("Install keepers", 6, False),
        ("Install door weights", 5, False),
        ("Tune doors", 13, False),
    ],
    (PISTA_INSTALL, 8): [
        ("Install ladder", 17, False),
        ("Install/trim buffers (car + CW)", 22, False),
        ("Install governor tension device", 22, False),
        ("Install CW screen", 24, False),
        ("Chisel pit", 15, False),
    ],
    (PISTA_INSTALL, 9): [
        ("Install electrical boxes", 30, False),
        ("Wire all boxes", 40, False),
        ("Bottles contact (belt/rope monitoring)", 10, False),
        ("Spin motor", 20, False),
    ],
    # ⚠️ «Speaker» aparece DOS veces en el documento (bajo cabina y techo de cabina) y
    # son dos altavoces distintos. Con el mismo nombre serían indistinguibles para el
    # mapeo, así que la zona va en el nombre — misma razón por la que el propio
    # documento avisa de los dos «toe guards» y de los dos «fire switch».
    (PISTA_INSTALL, 10): [
        ("Weight sensors (under cabin)", 8, False),
        ("Alarms (under cabin)", 6, False),
        ("Safety gear contacts (under cabin)", 8, False),
        ("Speaker (under cabin)", 5, False),
        ("Traveller/flat/flex cables (under cabin)", 8, False),
        ("COP wiring (inside cabin)", 10, False),
        ("Ceiling decoration wiring (inside cabin)", 6, False),
        ("Fire switch, COP-side keyed (inside cabin)", 4, False),
        ("OKR box (top of cabin)", 7, False),
        ("Salsis reader (top of cabin)", 4, False),
        ("Magnet reader (top of cabin)", 5, False),
        ("Wiring from cabin header/PDO (top of cabin)", 7, False),
        ("Lightrays (top of cabin)", 5, False),
        ("Top-of-car emergency light", 4, False),
        ("Speaker (top of cabin)", 4, False),
        ("Flex cables (top of cabin)", 5, False),
        ("Rooftop handrail contact", 4, True),
    ],
    (PISTA_INSTALL, 11): [
        ("LIP/LOP cables", 20, False),
        ("Door locks", 20, False),
        ("Call button wiring", 14, False),
        ("Fire switch, landing-side keyed", 6, False),
        ("Contact cable run to pit", 10, False),
        ("Power cable for lights", 8, False),
        ("Lights", 8, False),
        ("Install cable tray", 6, False),
        ("Install magnet flags", 8, True),
    ],
    (PISTA_INSTALL, 12): [
        ("Stop button box", 15, False),
        ("Switch light", 10, False),
        ("Pendant", 10, False),
        ("GPO", 10, False),
        ("SG contact", 15, False),
        ("Ladder contact", 15, False),
        ("Salsis contact", 15, False),
        ("Buffer contacts", 10, False),
    ],
    (PISTA_INSTALL, 13): [
        ("Install belts (motor, CW, cabin)", 19, False),
        ("Change over mains on lift", 9, False),
        ("Remove tirak gear", 9, False),
        ("Remove stopblock", 4, False),
        ("Remove Inex kit components", 8, False),
        ("Pack up", 8, False),
        ("Clean shaft", 8, False),
        ("File rail joins", 7, False),
        ("Install oilers", 7, False),
        ("Final finishes/touch-ups", 6, False),
        ("Install compensation chain", 10, False),
        ("Remove/dismantle sky climber & sky lock", 5, True),
    ],
    (PISTA_INSTALL, 14): [
        ("Tune magnet reader", 5, False),
        ("Tune keepers", 5, False),
        ("Tune spear", 5, False),
        ("Tune rollers", 5, False),
        ("Tune/fix contacts (unspecified location)", 5, False),
        ("Level/adjust car position", 6, False),
        ("Adjust door alignment/gaps", 6, False),
        ("Adjust ride comfort/smoothness settings", 6, False),
        ("Fine-tune floor-level stopping accuracy", 7, False),
        ("Load test", 6, False),
        ("Speed test", 6, False),
        ("Safety systems test", 6, False),
        ("Final functional test/run", 7, False),
        ("Certification inspection/paperwork", 8, False),
        ("Client walkthrough/handover", 8, False),
        ("Final documentation/as-built delivery", 9, False),
    ],
}

TOLERANCIA = 0.05      # las sumas se comparan con esta holgura, no con ==


def etapas(pista=None) -> list:
    """Las etapas de una pista, o todas, en orden."""
    return [e for e in ETAPAS if pista is None or e[0] == pista]


def actividades(pista, numero) -> list:
    """Las actividades de esa etapa. Lista vacía si la etapa no existe — no lanza."""
    return list(ACTIVIDADES.get((pista, numero), []))


def pistas_de_tipo(tipo) -> list:
    """Qué pistas lleva un tipo de proyecto (decisión del usuario, 22/09/2026).

    ⚠️ «Ripout + Installation» es **una obra con todas las actividades juntas**, o sea
    un solo 100%, no dos barras en paralelo como proponía el documento de origen.
    """
    t = str(tipo or "").strip().lower()
    if t == "ripout":
        return [PISTA_RIPOUT]
    if t in ("ripout + installation", "ripout+installation"):
        return [PISTA_RIPOUT, PISTA_INSTALL]
    if t == "installation":
        return [PISTA_INSTALL]
    return []


def peso_etapa(tipo, pista, numero, pct_ripout=None) -> float:
    """El peso de esa etapa **dentro de la obra entera**.

    En una obra de una sola pista es su peso tal cual. En la combinada se reparte:
    el desmontaje se lleva `pct_ripout` y la instalación el resto, porque las dos
    pistas suman 100 por separado y en una sola obra no pueden sumar 100 las dos.
    """
    _e = next((e for e in ETAPAS if e[0] == pista and e[1] == numero), None)
    if _e is None:
        return 0.0
    _pistas = pistas_de_tipo(tipo)
    if len(_pistas) < 2:
        return float(_e[3])
    p = PCT_RIPOUT_DEFECTO if pct_ripout is None else float(pct_ripout)
    p = max(0.0, min(100.0, p))
    cuota = p if pista == PISTA_RIPOUT else (100.0 - p)
    return round(float(_e[3]) * cuota / 100.0, 4)


def peso_catalogo(tipo, pista, numero, nombre, pct_ripout=None) -> float:
    """Peso NOMINAL de esa actividad: etapa × actividad, sin mirar qué obra es.

    ⚠️ **No es el peso que lleva en una obra concreta.** Ese sale de `plan_de`, que
    además reparte lo que dejan las condicionales que esa obra no tiene. Los dos
    números son legítimamente distintos y por eso se llaman distinto: llamarlos igual
    es exactamente cómo se acaba enseñando un avance y reclamando otro (v361).

    Este es el ÚNICO sitio donde se multiplica etapa × actividad.
    """
    _a = next((a for a in actividades(pista, numero) if a[0] == nombre), None)
    if _a is None:
        return 0.0
    return round(peso_etapa(tipo, pista, numero, pct_ripout) * float(_a[1]) / 100.0, 4)


def plan_de(tipo, condicionales=(), pct_ripout=None) -> list:
    """El menú de una obra concreta: etapas y actividades que SÍ aplican.

    `condicionales` = los nombres de actividades condicionales que esta obra lleva.
    Las que no estén ahí **no se crean**, y por eso no entran en el denominador: si
    entraran, una obra de tracción nunca podría pasar del 85% de su R3 (ver el aviso
    del módulo).

    ⚠️ **Lo que queda se RENORMALIZA a 100.** Sin esto, una obra sin falso coche ni
    espejo sumaba 97,48% y un desmontaje de tracción 78,30%: `compute_avance` habría
    dado el porcentaje correcto igual —normaliza por Σpeso—, pero los pesos que ve el
    usuario habrían mentido, y son los que explican por qué una reclamación vale lo que
    vale. Renormalizar significa que **el mismo trabajo pesa algo más en una obra que
    lleva menos cosas**, que es justamente lo cierto: es una porción mayor de lo que esa
    obra contiene.

    ⚠️ Y se renormaliza **dentro de cada pista**, no sobre el total. Si se hiciera
    sobre el total, el reparto que fijó el usuario se movería solo: un desmontaje sin
    parte hidráulica tiene menos actividades, así que «30% de desmontaje» salía 28,08%.
    El reparto entre pistas es un juicio declarado, no algo que deba encoger porque una
    obra no lleve un condicional.
    """
    _quiere = {str(c) for c in (condicionales or ())}
    _pistas = pistas_de_tipo(tipo)
    p = PCT_RIPOUT_DEFECTO if pct_ripout is None else float(pct_ripout)
    p = max(0.0, min(100.0, p))

    bruto, total = [], {}
    for pista, num, nombre, peso in etapas():
        if pista not in _pistas:
            continue
        _acts = [a for a in actividades(pista, num) if (not a[2]) or a[0] in _quiere]
        if not _acts:
            continue
        # Peso crudo DENTRO de su pista: etapa × actividad, sin el reparto entre pistas.
        _filas = [(a, float(peso) * float(a[1]) / 100.0) for a in _acts]
        _suma = sum(x for _a, x in _filas)
        total[pista] = total.get(pista, 0.0) + _suma
        bruto.append((pista, num, nombre, _filas, _suma))

    # La cuota de cada pista: todo si va sola, el reparto si la obra es combinada.
    cuota = {pista: (100.0 if len(_pistas) < 2
                     else (p if pista == PISTA_RIPOUT else 100.0 - p))
             for pista in _pistas}
    # ⚠️ Sin dividir por cero: un tipo sin pistas (Delivery, Other) o una pista cuyas
    # actividades quedaron todas fuera salen con factor 0, no con una excepción.
    k = {pista: (cuota[pista] / total[pista] if total.get(pista, 0) > 0 else 0.0)
         for pista in _pistas}

    return [{
        "pista": pista, "numero": num, "nombre": nombre,
        "peso": round(_suma * k[pista], 4),
        "actividades": [
            {"nombre": a[0], "peso_en_etapa": float(a[1]), "condicional": bool(a[2]),
             "peso_en_obra": round(x * k[pista], 4)}
            for a, x in _filas],
    } for pista, num, nombre, _filas, _suma in bruto]


# ⚠️ Grupos EXCLUYENTES: hay que elegir exactamente una opción, y no elegir no es un
# estado válido. Tracción e hidráulico son el 25% y el 15% del R3: sin decidirlo, la
# demolición entera se queda fuera del plan y la obra mediría sobre un denominador que
# no incluye el trabajo más grande del desmontaje.
EXCLUYENTES = {
    "demolicion": {
        "pista": PISTA_RIPOUT,
        "pregunta": "Is the lift being removed traction or hydraulic?",
        "opciones": ("Rip out mechanical components - traction",
                     "Rip out mechanical components - hydraulic"),
    },
}


def falta_por_decidir(tipo, condicionales=()) -> list:
    """Los grupos excluyentes que esta obra todavía no resolvió.

    ⚠️ Devuelve la lista para que QUIEN LLAMA decida qué hacer, en vez de elegir una
    opción por su cuenta. Suponer «tracción» porque es lo común es exactamente el «1
    inventado» que v509 prohibió: escondería un dato que falta dentro de un número que
    parece calculado. Lista vacía = no queda nada por decidir.
    """
    _quiere = {str(c) for c in (condicionales or ())}
    _pistas = pistas_de_tipo(tipo)
    out = []
    for clave, g in EXCLUYENTES.items():
        if g["pista"] not in _pistas:
            continue
        _elegidas = [o for o in g["opciones"] if o in _quiere]
        if len(_elegidas) != 1:
            out.append({"clave": clave, "pregunta": g["pregunta"],
                        "opciones": list(g["opciones"]),
                        "elegidas": _elegidas})
    return out


def condicionales(pista=None) -> list:
    """Todas las actividades condicionales, para que el alta de obra las pregunte."""
    return [{"pista": p, "etapa": n, "nombre": a[0]}
            for (p, n) in sorted(ACTIVIDADES, key=lambda k: (k[0], k[1]))
            for a in ACTIVIDADES[(p, n)]
            if a[2] and (pista is None or p == pista)]


def validar() -> list:
    """Los problemas de aritmética del catálogo. Lista vacía = cuadra.

    ⚠️ Esto existe porque el documento de origen llegó con DOS fallos de este tipo: la
    Stage 2 sumaba 106% en vez de 100 y su encabezado se contradecía con la tabla de
    pesos. Y no era la primera vez — una nota del propio documento cuenta que los
    sub-grupos de la Stage 14 sumaban 104 y hubo que corregirlos. Un 6% de más se
    traduce en avance inflado, y el avance se cobra: esto tiene que ser un guardián,
    no una revisión a ojo.
    """
    problemas = []
    for pista in PISTAS:
        _s = sum(e[3] for e in etapas(pista))
        if abs(_s - 100.0) > TOLERANCIA:
            problemas.append("track %s adds up to %.2f, not 100" % (pista, _s))
    for (pista, num), acts in sorted(ACTIVIDADES.items(), key=lambda k: (k[0][0], k[0][1])):
        _s = sum(a[1] for a in acts)
        if abs(_s - 100.0) > TOLERANCIA:
            problemas.append("activities of %s/%s add up to %.2f, not 100"
                             % (pista, num, _s))
        _n = [a[0] for a in acts]
        if len(set(_n)) != len(_n):
            _rep = sorted({x for x in _n if _n.count(x) > 1})
            problemas.append("%s/%s has duplicate names: %s" % (pista, num, _rep))
        if any(a[1] <= 0 for a in acts):
            problemas.append("%s/%s has an activity with weight <= 0" % (pista, num))
    _sin = [(p, n) for (p, n, _x, _y) in ETAPAS if not ACTIVIDADES.get((p, n))]
    if _sin:
        problemas.append("stages with no activities: %s" % _sin)
    _sobra = [k for k in ACTIVIDADES if k not in {(e[0], e[1]) for e in ETAPAS}]
    if _sobra:
        problemas.append("activities of stages that do not exist: %s" % _sobra)
    return problemas
