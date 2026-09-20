# -*- coding: utf-8 -*-
"""v470 · tipo de proyecto «Ripout + Installation».

El desmontaje del ascensor viejo entra como la PRIMERA actividad del cronograma
(decisión del usuario), no como una tabla de fases aparte, y su duración escala con
el número de paradas igual que el resto.

⚠️ El cambio de fondo NO es la fase nueva: es que hay TRES sitios que preguntan «¿este
tipo genera cronograma?» —el alta a mano, la edición y aceptar una cotización— y
añadir el tipo a dos de ellos deja el tercero comportándose como «Other» sin decirlo.
Es exactamente el fallo de v454, donde `aceptar_y_crear_proyecto` se quedó sin la regla
de v306 y una obra nació con CERO actividades, clavada en 0% para siempre. Por eso se
crea `projects.genera_cronograma()` como ÚNICA definición y los tres delegan.
"""
import io
import os

RAIZ = r"C:\Users\diego\P1\survey_app"
hechos, fallos = [], []


def parche(rel, viejo, nuevo, etq):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(viejo)
    if n != 1:
        fallos.append("%s · %s: ancla %s (%d)"
                      % (rel, etq, "ausente" if not n else "ambigua", n))
        return
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(viejo, nuevo))
    hechos.append("%s · %s" % (rel, etq))


# ── 1 · schedule.py: la fase de desmontaje ────────────────────────────────────
parche(
    "core/schedule.py",
    '# (nombre, dur_base_dias, dias_por_parada, peso, condicion)\nPHASES = [',
    '''# ⚠️ v470 · El desmontaje del ascensor existente NO es una tabla de fases aparte:
# es UNA actividad, la primera del cronograma (decisión del usuario). Su duración
# escala con las paradas como el resto —más plantas son más puertas de rellano que
# quitar y más riel que desmontar—, y el peso la deja a la altura de «Car and
# counterweight», que es un trabajo comparable.
#
# ⚠️ El nombre se GUARDA en la hoja `Activities`, así que nace en inglés: traducirlo
# después obliga a migrar el histórico, que es lo que costó v453. Y duración y peso
# son solo el punto de partida — la tabla de actividades es editable por proyecto
# desde v83, así que en obra se ajusta sin tocar código.
FASE_RIPOUT = ("Ripout of existing lift", 3, 0.5, 15, None)

# (nombre, dur_base_dias, dias_por_parada, peso, condicion)
PHASES = [''',
    "FASE_RIPOUT")

parche(
    "core/schedule.py",
    '''def build_schedule(ns: int, start_date: date, flags: dict,
                   custom_rows: list = None) -> dict:
    """
    Genera el cronograma. Si `custom_rows` viene (edición del usuario),
    usa sus duraciones/pesos en lugar de los automáticos.
    custom_rows: lista de dicts {nombre, duracion, peso}
    """
    ns = max(1, int(ns or 1))

    if custom_rows:
        base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]
    else:
        base = []
        for nombre, db, dpp, peso, cond in PHASES:''',
    '''def build_schedule(ns: int, start_date: date, flags: dict,
                   custom_rows: list = None, ripout: bool = False) -> dict:
    """
    Genera el cronograma. Si `custom_rows` viene (edición del usuario),
    usa sus duraciones/pesos en lugar de los automáticos.
    custom_rows: lista de dicts {nombre, duracion, peso}

    `ripout=True` antepone la actividad de desmontaje (v470, tipo
    «Ripout + Installation»). ⚠️ NO aplica sobre `custom_rows`: ahí las filas son las
    que el usuario ya editó, y volver a insertarla las duplicaría en cada guardado.
    """
    ns = max(1, int(ns or 1))

    if custom_rows:
        base = [(r["nombre"], float(r["duracion"]), float(r["peso"])) for r in custom_rows]
    else:
        base = []
        for nombre, db, dpp, peso, cond in ([FASE_RIPOUT] + PHASES if ripout else PHASES):''',
    "build_schedule(ripout=)")

# ── 2 · projects.py: el tipo, su icono y la ÚNICA definición ──────────────────
parche(
    "core/projects.py",
    'TIPO_INSTALACION = "Installation"\nTIPOS = [TIPO_INSTALACION, "Delivery", "Ripout", "Other"]',
    '''TIPO_INSTALACION = "Installation"
# v470 · sustituir un ascensor: primero se desmonta el viejo y luego se instala el
# nuevo. Genera el MISMO cronograma que una instalación con la actividad de
# desmontaje delante (`schedule.FASE_RIPOUT`).
TIPO_RIPOUT_INST = "Ripout + Installation"
TIPOS = [TIPO_INSTALACION, TIPO_RIPOUT_INST, "Delivery", "Ripout", "Other"]


def genera_cronograma(tipo) -> bool:
    """¿Este tipo nace con el cronograma estándar de obra?

    ⚠️ ÚNICA definición, y no es ceremonia: hasta v470 la pregunta se hacía en TRES
    sitios —el alta a mano, la edición y `quotes.aceptar_y_crear_proyecto`— y uno de
    ellos comparaba contra el LITERAL `"Installation"` en vez de la constante. Añadir
    un tipo a dos de los tres lo deja comportándose como «Other» **sin dar ningún
    error**: es el fallo de v454, donde una obra creada desde cotización nació con
    CERO actividades y se quedó clavada en 0% para siempre, porque el avance es
    Σ(peso·avance)/Σpeso sobre las actividades.
    """
    return str(tipo) in (TIPO_INSTALACION, TIPO_RIPOUT_INST)


def con_ripout(tipo) -> bool:
    """¿Lleva por delante la actividad de desmontaje?"""
    return str(tipo) == TIPO_RIPOUT_INST''',
    "TIPO_RIPOUT_INST + genera_cronograma")

parche(
    "core/projects.py",
    'TIPO_ICONO = {TIPO_INSTALACION: ":material/construction:", "Delivery": ":material/local_shipping:",',
    'TIPO_ICONO = {TIPO_INSTALACION: ":material/construction:",\n'
    '              TIPO_RIPOUT_INST: ":material/autorenew:",\n'
    '              "Delivery": ":material/local_shipping:",',
    "TIPO_ICONO")

# ── 3 · projects_ui.py: el alta ───────────────────────────────────────────────
parche(
    "core/projects_ui.py",
    '        _es_inst = (_tipo == P.TIPO_INSTALACION)',
    '        # ⚠️ Por el helper, NUNCA comparando el tipo aquí: los tres caminos que\n'
    '        # generan cronograma tienen que decidir con la MISMA regla (v470).\n'
    '        _es_inst = P.genera_cronograma(_tipo)',
    "alta: _es_inst por el helper")

parche(
    "core/projects_ui.py",
    '                    _sch_prev = build_schedule(int(ns), f_ini, {})',
    '                    _sch_prev = build_schedule(int(ns), f_ini, {},\n'
    '                                              ripout=P.con_ripout(_tipo))',
    "alta: vista previa con ripout")

parche(
    "core/projects_ui.py",
    '                sched = build_schedule(int(ns), f_ini, {})',
    '                sched = build_schedule(int(ns), f_ini, {},\n'
    '                                       ripout=P.con_ripout(_tipo))',
    "alta: cronograma con ripout")

# ── 4 · quotes.py: el literal pasa a la constante, y delega ───────────────────
parche(
    "core/quotes.py",
    '''    if str(tipo) == "Installation" and _num(ns) > 0:
        sch = S.build_schedule(int(_num(ns)), ini, {})''',
    '''    # ⚠️ Antes comparaba el LITERAL "Installation" en vez de la constante: dos
    # definiciones de la misma regla, y por ahí es por donde v454 se quedó sin
    # cronograma. Ahora delega en `projects.genera_cronograma`, igual que el alta.
    if P.genera_cronograma(tipo) and _num(ns) > 0:
        sch = S.build_schedule(int(_num(ns)), ini, {}, ripout=P.con_ripout(tipo))''',
    "quotes: delega en el helper")

print("APLICADO:")
for h in hechos:
    print("   ok  " + h)
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   !!  " + f)
    raise SystemExit(1)
