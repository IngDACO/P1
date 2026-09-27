# -*- coding: utf-8 -*-
"""El vocabulario de obra: qué palabras del parte apuntan a qué actividad (v517).

## Qué es

La mitad **determinista** de la interpretación del parte diario. Aquí no hay modelo ni
llamada a ninguna API: es una tabla de términos y una función que busca.

Sale de `docs/Process_Knowledge_Reference.md` y `docs/Lift_Install_Task_Breakdown.md`,
que son el poso corregido de pasar un intérprete sobre partes REALES de instaladores —
las 58 anotaciones «(Danilo, Sep 2026)» de esos documentos no explican diseño, corrigen
respuestas concretas. Eso no se reconstruye leyendo el catálogo.

## ⚠️ Para qué sirve si de todos modos va a haber un modelo detrás

Por tres cosas, y la tercera es la que importa:

1. **Barandilla.** Un modelo puede devolver «Landing Door Install», que suena bien y no
   existe. Aquí solo se puede proponer una actividad que esté en el plan SELLADO de esa
   obra. Es la regla de v509: nunca un «1» inventado.
2. **Suelo medible.** Da una línea base sin coste ni API contra la que comparar lo que
   aporta el modelo. Sin ella, «el agente acierta un 80%» no se puede leer.
3. **Es lo único que se puede verificar de verdad.** Una tabla se prueba con un test; una
   interpretación solo se puede juzgar contra partes reales, y de esos todavía no hay.

## ⚠️ Lo que este módulo NO hace, a propósito

**No decide.** Devuelve candidatos con el término que los disparó. Ni escribe, ni
acredita, ni ordena por probabilidad.

**No adivina lo ambiguo.** El documento es explícito: hay frases que no se pueden
resolver con vocabulario porque dependen de POR DÓNDE VA LA OBRA — «under the cabin work»
es mecánico si los rieles no han subido y eléctrico si ya subieron. Esas salen por su
lado, marcadas, con sus alternativas y la regla escrita. Elegir una sería inventar.

**No confunde «no lo entiendo» con «no cuenta».** La inducción y el pre-start son
entradas casi universales en los partes y NO son avance. Se reconocen y se dicen como
tales, que es información; tratarlas como texto no entendido sería perder una señal.

## ⚠️ Lo que NO alcanza, y por qué se deja así

**Verbos irregulares.** La raíz lleva «hanging» a «hang», pero no «hung». Cubrirlos sería
una lista de excepciones a mano que nadie mantiene, y es exactamente el tipo de cosa que
la mitad con modelo sí sabe hacer. Salió probando: una frase de prueba con «hung» puso el
guardián rojo acusando a código sano.

**El sentido.** «No pude hacer las puertas porque no llegaron los marcos» menciona las
puertas y aquí sale como candidato. Una tabla no distingue lo hecho de lo impedido — para
eso hace falta leer la frase, no buscar en ella.

Las dos son la razón de que esto sea la MITAD determinista y no la solución. Lo que se
gana igualmente: nada de lo que se proponga podrá ser una actividad inventada.
"""
import re
import unicodedata

# ═════════════════════════════════════════════════════════════════
# Sinónimos: la jerga → la actividad del catálogo
# ═════════════════════════════════════════════════════════════════
# ⚠️ Cada nombre de actividad está LEÍDO del catálogo, no supuesto. Mi primera tanda
# inventó diez que no existían («Install ceiling», «Survey (plumb points, datum)»…), y
# por eso `verif_v517` exige que TODOS existan: un término que apunta a una actividad
# fantasma no falla, simplemente no propone nunca — y eso no se ve.
SINONIMOS = {
    # ── Herramienta temporal y montaje (rip-out) ──────────────────
    "tirak": ["Mount tirak"],
    "orange box": ["Fully kill lift electrically / route mains power to tirak"],
    "inex kit orange box": ["Fully kill lift electrically / route mains power to tirak"],
    "stopblock": ["Attach tirak + stopblock"],
    "blockstop": ["Attach tirak + stopblock"],
    "electric chain block": ["Setup electric chain block"],
    "minifor": ["Setup electric chain block"],
    "working deck": ["Build working deck(s)"],
    "cages": ["Hoardings & protection"],
    "glass shaft protection": ["Hoardings & protection"],
    "snap test": ["Snap test (trimmer beam/hook point load test)"],
    "pull test": ["Snap test (trimmer beam/hook point load test)"],
    "trimmer beam": ["Install top-of-shaft beam/hook point"],
    "hook point": ["Install top-of-shaft beam/hook point"],
    "swl": ["Install top-of-shaft beam/hook point"],
    # ── Falso coche ───────────────────────────────────────────────
    "sky climber": ["Install sky climber"],
    "sky lock": ["Install sky lock"],
    "false car": ["Install sky climber", "Install sky lock"],
    # ── Plomada ───────────────────────────────────────────────────
    "laser plumb": ["Throw plumblines, attach weights, let settle"],
    "plumblines": ["Throw plumblines, attach weights, let settle"],
    # ── Cabina ────────────────────────────────────────────────────
    "cradle": ["Install platform (cradle)"],
    "yoke": ["Install yoke/base, level it"],
    "uprights": ["Install uprights"],
    "top bow": ["Install top bow"],
    "reverses": ["Build cabin (walls)"],
    "fillerweights": ["Throw fillerweights"],
    "loaded the tank": ["Throw fillerweights"],
    "load the tank": ["Throw fillerweights"],
    "u/wing brackets": ["Install U/Wing brackets"],
    "wing brackets": ["Install U/Wing brackets"],
    "cop": ["Install COP (mechanical)"],
    "balustrades": ["Install cabin interior handrails/kickplates/bumpers",
                    "Install rooftop handrail"],
    # ── Contrapeso ────────────────────────────────────────────────
    "cw dumbbell": ["Install CW tank"],
    "belt keepers": ["Install CW tank"],
    "cw tank": ["Install CW tank"],
    # ── Bedplates y subida de hueco ───────────────────────────────
    "mbb": ["Install motor bedplate"],
    "motor bedplate": ["Install motor bedplate"],
    "hilti plates": ["Install motor bedplate"],
    "bottles": ["Install motor bedplate"],
    "millsons kit": ["Install motor bedplate"],
    "governor bedplate": ["Install single bedplate"],
    "z side bedplate": ["Install single bedplate"],
    "single bedplate": ["Install single bedplate"],
    "salsis tape": ["Install single bedplate"],
    "calcius tape": ["Install single bedplate"],
    "kss switches": ["Install single bedplate"],
    "sump hole": ["Seal machine room / shaft penetrations"],
    "finals": ["Install car rails to top"],
    "gauge": ["Install rings to top"],
    "guage": ["Install rings to top"],
    # ── Puertas de rellano ────────────────────────────────────────
    "rots": ["Install rots"],
    "groutguarding": ["Groutguarding (fire-rated)"],
    "grout guarding": ["Groutguarding (fire-rated)"],
    "fire brackets": ["Groutguarding (fire-rated)"],
    "fire trims": ["Groutguarding (fire-rated)"],
    "fire rating": ["Groutguarding (fire-rated)"],
    "fire seal": ["Groutguarding (fire-rated)"],
    "door springs": ["Install door weights"],
    "door weights": ["Install door weights"],
    "toe guards": ["Install skirts", "Install cabin toe guard"],
    "skirts": ["Install skirts"],
    # ── Foso ──────────────────────────────────────────────────────
    "jenny wheel": ["Install governor tension device"],
    "genie wheel": ["Install governor tension device"],
    "tension sheave": ["Install governor tension device"],
    "jockey pulley": ["Install governor tension device"],
    "buffer stands": ["Install/trim buffers (car + CW)"],
    "buffer tops": ["Install/trim buffers (car + CW)"],
    "chisel pit": ["Chisel pit"],
    # ── Eléctrico ─────────────────────────────────────────────────
    "okr": ["OKR box (top of cabin)"],
    "revision box": ["OKR box (top of cabin)"],
    "inspection box": ["OKR box (top of cabin)"],
    "hogan unit": ["Install electrical boxes"],
    "aed": ["Install electrical boxes"],
    "aesd": ["Install electrical boxes"],
    "option box": ["Install electrical boxes"],
    "cube": ["Install electrical boxes"],
    "pixel": ["Install electrical boxes"],
    "can line": ["Install electrical boxes"],
    "loadcell": ["Weight sensors (under cabin)"],
    "lightrays": ["Lightrays (top of cabin)"],
    "photocell": ["Lightrays (top of cabin)"],
    "curtain of light": ["Lightrays (top of cabin)"],
    "magnet reader": ["Magnet reader (top of cabin)"],
    "magnet tape reader": ["Magnet reader (top of cabin)"],
    "pdo": ["Wiring from cabin header/PDO (top of cabin)"],
    "lip": ["LIP/LOP cables"],
    "lop": ["LIP/LOP cables"],
    "cable tray": ["Install cable tray"],
    "fire switch": ["Fire switch, landing-side keyed",
                    "Fire switch, COP-side keyed (inside cabin)"],
    "gpo": ["GPO"],
    "sis": ["Install electrical boxes"],
    # ── Belting y cierre ──────────────────────────────────────────
    "wadges": ["Install belts (motor, CW, cabin)"],
    "anti-twists": ["Install belts (motor, CW, cabin)"],
    "twist plates": ["Install belts (motor, CW, cabin)"],
    "belt twist": ["Install belts (motor, CW, cabin)"],
    "change over mains": ["Change over mains on lift"],
    "compensation chain": ["Install compensation chain"],
    "flap disc": ["File rail joins"],
    "manual filer": ["File rail joins"],
    "stack gates": ["Pack up"],
    # ── Certificación ─────────────────────────────────────────────
    "ccew": ["Certification inspection/paperwork"],
    # ── v517 · lo que el corpus de frases reales encontró sin transcribir ──
    # ⚠️ Cada uno está DICHO en `docs/`, con su cita en `ejercitar_v517_corpus.py`. Lo que
    # NO se hace: añadir un término porque una frase de la prueba falle sin que el
    # documento lo respalde — eso sería ajustar el examen a sus respuestas.
    "yemny wheel": ["Install governor tension device"],   # «was a mishearing/typo»
    "plumb laser": ["Throw plumblines, attach weights, let settle"],   # «plumb laser(s)»
    "controller wiring": ["Wire all boxes"],           # «belongs here (Stage 9)»
    "combo bracket": ["Install first 2 rings"],        # «omega bracket = combo bracket»
    "combination bracket": ["Install first 2 rings"],
    "omega bracket": ["Install first 2 rings"],
    "door blades": ["Install door panels"],            # «panels/blades»
    "rooftop pieces": ["Install cabin ceiling (roof)"],    # «rigged up bit by bit»
    "rip out kit": ["Rip-out kit delivery"],
    "speed governor on cabin": ["Attach speed governor rope to cabin"],
    "test lift": ["Final functional test/run"],        # «test lift 1 … valid evidence»
    "level the car": ["Level/adjust car position"],    # «helped level the car»
    "hoardings": ["Compound/Hoardings", "Hoardings & protection"],   # el plan elige
    # ⚠️ A las DOS: «Other deliveries» solo existe en el desmontaje (R0), así que en una
    # instalación apuntaba fuera del plan y el parte no proponía nada. En instalación el
    # mismo recado es «Receive lift delivery». El plan de la obra elige cuál vale.
    "picked up delivery": ["Other deliveries", "Receive lift delivery"],
    "ripped out rings": ["Rip out mechanical components - traction"],  # «top 3 rings»
}

# ⚠️ Términos que el documento reconoce como REALES pero que NO tienen actividad en el
# catálogo, porque están en el desglose de tareas y no en el documento de etapas del que
# salió `stages.py` — los dos documentos han derivado. No se mapean a la actividad más
# parecida: eso sería inventar trabajo donde no lo hay, y con peso ajeno. Se reconocen y
# se dicen, para que el usuario decida si entran al catálogo y cuánto pesan.
# ⚠️ En INGLÉS, como todo lo que puede llegar a pantalla (v441-v452). Nacieron en
# español y `verif_v448` los cazó: son descripciones de trabajo, o sea texto que alguien
# acabará leyendo, no comentarios de código.
SIN_ACTIVIDAD = {
    "lighten cabin": "Lightening the cabin for the tirak ratio (R2 in the breakdown)",
    "bridging": "Temporary bridge on the landing door circuit",
    "chaser job": "Cutting/expanding a door opening that came in too small",
}

# ⚠️ Frases que el documento marca como GENUINAMENTE ambiguas: no se resuelven con
# vocabulario porque dependen de por dónde va la obra. Cada una trae la regla TAL COMO
# la escribió quien corrigió al intérprete, y sus alternativas. Elegir una aquí sería
# exactamente lo que el documento dice que no se haga.
AMBIGUOS = {
    "under the cabin work": {
        "alternativas": ["Install platform (cradle)", "Traveller/flat/flex cables (under cabin)"],
        "regla": "Mechanical if the car rails are not up yet; electrical once the shaft "
                 "climb has progressed.",
    },
    "pit work": {
        "alternativas": ["Install ladder", "Stop button box"],
        "regla": "Mechanical if the pit ladder and buffers are not in yet; electrical "
                 "once they are.",
    },
    "flex cable": {
        "alternativas": ["Traveller/flat/flex cables (under cabin)", "Flex cables (top of cabin)"],
        "regla": "With no zone given, treat BOTH the under-cabin and top-of-cabin flex "
                 "cable tasks as done, not just one.",
    },
    "contacts": {
        "alternativas": ["Tune/fix contacts (unspecified location)"],
        # ⚠️ Con la palabra del documento («defaults to»), no con mi paráfrasis: el
        # guardián exige que una entrada de UNA sola alternativa diga que va por DEFECTO,
        # y mi versión —«goes to»— decía lo mismo sin decirlo. Cazado por el chequeo.
        "regla": "Generic term used all over the lift. With no location named it "
                 "defaults to Commissioning & Tuning rather than being guessed into a "
                 "specific system.",
    },
    "mains": {
        "alternativas": ["Fully kill lift electrically / route mains power to tirak",
                         "Change over mains on lift"],
        "regla": "Context decides: initial power connection, or the Stage 13 permanent "
                 "mains changeover.",
    },
    "strip": {
        "alternativas": ["Prep doors (panels/blades, frames)", "Final finishes/touch-ups"],
        "regla": "On an Installation job «strip» means prepping (peeling protective "
                 "film), not removing an installed part. Only read it as removal on a "
                 "Rip-Out job or when the part was clearly already installed.",
    },
    "pit doors": {
        "alternativas": ["Install door panels"],
        "regla": "Vague, with no further detail: defaults to the mechanical landing-door "
                 "install rather than being left unscoreable.",
    },
    # ⚠️ El DOCUMENTO SE CONTRADICE aquí, y no se resuelve en silencio. El glosario dice
    # «roping specifically means the lift was being belted that day (Stage 13)»; la
    # sección de ambiguos, con confirmación (Danilo, Sep 2026), dice «Roping is a generic
    # verb … Don't default it to one fixed stage». Estaba como sinónimo de Install belts
    # —la primera lectura— y el corpus lo destapó. Mientras el usuario no diga cuál vale,
    # queda MARCADO: no acredita nada, que es lo único que no puede salir mal.
    "roping": {
        "alternativas": ["Install belts (motor, CW, cabin)",
                         "Attach speed governor rope to cabin"],
        "regla": "CONTRADICTORY in the source doc. Glossary: roping means the lift was "
                 "being belted that day (Stage 13). Ambiguous-entries section: roping is "
                 "a generic verb across several rope tasks, don't fix it to one stage. "
                 "Pending the user's call.",
    },
    # «joined flex with Belden»: «flex» a secas es el cable sin zona (Belden es la marca).
    "flex": {
        "alternativas": ["Traveller/flat/flex cables (under cabin)", "Flex cables (top of cabin)"],
        "regla": "Flex on its own is the flex cable with no zone given: treat BOTH the "
                 "under-cabin and top-of-cabin flex cable tasks as done, not just one.",
    },
    "ducting": {
        "alternativas": ["Install cable tray", "Wire all boxes"],
        "regla": "A cover over wiring already being run — not a task of its own. Maps to "
                 "whichever wiring task is active (shaft or headroom).",
    },
}

# ⚠️ Reconocido y NO es avance. Son de las entradas más frecuentes en un parte, así que
# tratarlas como «no entendido» tiraría una señal buena y ensuciaría cualquier medida de
# acierto. El documento las llama «Logistics & Site Support».
NO_AVANCE = {
    "induction": "Site induction — happens once, does not carry progress.",
    "inductions": "Site induction — happens once, does not carry progress.",
    "pre-start": "Daily pre-start — every day, does not carry progress.",
    "prestart": "Daily pre-start — every day, does not carry progress.",
    "toolbox talk": "Safety talk, not progress.",
    "site evaluation drill": "Periodic safety/evacuation drill, not progress.",
    "tkе": "TKE is another company's lift on a shared site — not our job.",
    "tke": "TKE is another company's lift on a shared site — not our job.",
}

# ── Tareas: el TERCER nivel, sacado de `docs/Lift_Install_Task_Breakdown.md` ──────────
# ⚠️ Son VOCABULARIO, no un nivel que se acredite. El peso vive en la actividad y el
# propio documento dice «no weights at Task level yet»: meter un tercer nivel en la hoja
# sería estructura sin medida. Sirven para RECONOCER de qué actividad habla un parte.
TAREAS = {
    'Attach tirak + stopblock': [
        'Attach tirak',
        'Attach stopblock/blockstop',
    ],
    'Builders lift protection & handover': [
        'Install interior protection',
        'Protect landing door frames at every level',
        'Hand over to builder once construction hoist is replaced',
    ],
    'Compound/Hoardings': [
        'Transport hoarding materials to site',
        'Build hoardings on platform/concourse',
        'Install compound & protection',
    ],
    'Final clear-out / site prepared for new install': [
        'Remove scrap/debris',
        'Sweep/clean shaft, pit, machine room',
    ],
    'Fully kill lift electrically / route mains power to tirak': [
        'Install Inex kit orange box',
        'Connect mains to orange box',
        'Kill lift at main switch',
    ],
    'Hoardings & protection': [
        'Transport hoarding materials to site',
        'Build hoardings on platform/concourse',
        'Install compound & protection',
        'Protect glass shaft panels',
        'Deactivate nearby smoke detector',
    ],
    'Initial electrical shutdown/isolation': [
        'Shut down lift at main switch',
    ],
    'Install CW tank': [
        'Install CW dumbbell',
        'Install CW belt keepers',
    ],
    'Install compensation chain': [
        'Install the chain itself',
        'Install chain guides',
        'Install chain safety rope',
    ],
    'Install electrical boxes': [
        'AED',
        'VAF/drive',
        'Option box',
        'Cube',
        'Switch JH',
    ],
    'Install motor bedplate': [
        'Install Hilti plates',
        'Install motor',
        'Install bottles',
    ],
    'Install single bedplate': [
        'Install speed governor',
        'Install salsis tape',
        'Install bottles',
        'Install KSS switches',
    ],
    'Install sky climber': [
        'Install rope',
        'Connect power',
        'Install pendant',
    ],
    'Install sky lock': [
        'Install rope',
        'Attach directly to safety gear',
    ],
    'Install top-of-shaft beam/hook point': [
        'Drive old cabin in inspection mode to access top of shaft',
        'Install beam/hook point structure',
        'Install SWL (Safe Working Load) rating plate on the beam',
    ],
    'Install/trim buffers (car + CW)': [
        'Install car buffer',
        'Install CW buffer',
        'Trim for precise running clearance',
    ],
    'Pack up': [
        'Stack gates/cages',
        'Break down delivery boxes',
    ],
    'Paperwork (hand-over/procedure forms, SWMS sign-off)': [
        'Hand-over/procedure forms signed',
        'SWMS sign-on',
    ],
    'Receive lift delivery': [
        'Unload delivery',
        'Count/verify boxes against manifest',
        'Check box codes',
    ],
    'Release pressure from old ropes/belts OR detach piston': [
        'Traction lifts: release ropes/belts tension',
        'Hydraulic lifts: detach piston',
    ],
    'Rip out electrical components': [
        'Remove wiring',
        'Remove controller/boxes',
    ],
    'Rip out mechanical components - hydraulic': [
        'Drain/empty oil tank in machine room',
        'Remove hose running through shaft wall, connected to ram',
        'Pump remaining oil out of ram/hose',
        'Remove ram/piston',
        'Remove hydraulic structure',
    ],
    'Rip out mechanical components - traction': [
        'Remove rails & rings',
        'Remove cabin',
        'Remove CW/CW tank',
        'Remove landing doors',
        'Remove pit components',
    ],
    'Take possession of lift': [
        'Formal handover/sign-on to the existing lift',
        'Initial site walk of the lift being ripped out',
    ],
    'Throw plumblines, attach weights, let settle': [
        'Attach weights to plumblines',
        'Let settle under gravity',
    ],
    'Tune doors': [
        'Tune headers',
        'Tune panels',
        'Tune contacts',
    ],
}


# ═════════════════════════════════════════════════════════════════
# Búsqueda
# ═════════════════════════════════════════════════════════════════
def _raiz(p) -> str:
    """Quita la terminación para que «prepped», «prepping» y «prep» sean lo mismo.

    ⚠️ Esto NO es cosmético: sin ello el vocabulario solo casa con partes escritos en
    infinitivo, y los partes van en prosa — «prepped the doors» no casaba con «Prep
    doors» y la línea entera se perdía. El documento lo avisa en su segunda frase: los
    logs traen jerga, abreviaturas y orden no lineal.

    ⚠️ Deliberadamente tonto: cuatro terminaciones y la consonante doblada. Un stemmer
    de verdad (Porter) acortaría de más —«rings» y «ringed» acabarían en «ring», pero
    también «ceiling» en «ceil»— y se aplica a las DOS puntas, así que un recorte
    agresivo inventa coincidencias en vez de encontrarlas. Se valida contra casos
    conocidos en `verif_v517`, buenos y malos.
    """
    if len(p) <= 3:
        return p
    for suf in ("ing", "ed", "es", "s"):
        if p.endswith(suf) and len(p) - len(suf) >= 3:
            p = p[:-len(suf)]
            break
    # «prepp» → «prep», «fitt» → «fit»: el inglés dobla la consonante antes de -ed/-ing.
    # ⚠️ SIEMPRE, no «solo si se cortó una terminación». Esa condición la puse yo para que
    # «install» no saliera «instal», y rompió justo el verbo MÁS FRECUENTE de los partes:
    # «install» se quedaba en «install» mientras «installed» e «installing» daban
    # «instal», así que ninguna de las dos formas conjugadas casaba con el infinitivo del
    # catálogo. Lo destapó el corpus de frases reales («installed belts» no encontraba
    # «Install belts»). Y el guardián lo había BLINDADO afirmando la FORMA («install →
    # install») en vez del principio (las formas de un verbo coinciden) — la trampa nº16.
    # Lo que importa no es que la raíz sea bonita: es que sea la MISMA a las dos puntas.
    if len(p) > 3 and p[-1] == p[-2] and p[-1] not in "aeiou":
        p = p[:-1]
    # ⚠️ Y la «e» muda, SIEMPRE: «tune» pierde la e al conjugar, así que «tuned» daba
    # «tun» y «tune» se quedaba en «tune» — las dos formas de la misma palabra no
    # casaban entre sí y «Tune doors» no reconocía «tuned the doors». Se quita en las
    # dos puntas, que es lo que las vuelve a juntar.
    if len(p) > 3 and p.endswith("e"):
        p = p[:-1]
    return p


# ⚠️ Palabras de relleno que se quitan de las DOS puntas. Un parte va en prosa —«tuned
# THE doors»— y el catálogo en infinitivo —«Tune doors»—, así que sin esto el artículo de
# en medio rompe la coincidencia y la línea entera se pierde. Lista corta a propósito:
# quitar demasiado junta cosas que no van juntas.
RELLENO = frozenset(("the", "a", "an", "of", "to", "and", "on", "in", "at", "for",
                     "with", "some", "today", "all", "then", "we", "i", "it", "this",
                     "that", "my", "our", "was", "were", "is", "are", "been", "have",
                     "has", "had", "did", "done", "doing", "got", "up", "out"))


def normaliza(t) -> str:
    """Minúsculas, sin acentos, puntuación como espacio y cada palabra a su raíz.

    ⚠️ La puntuación se convierte en espacio en vez de quitarse: «OKR/salsis» tiene que
    dar dos palabras y no «okrsalsis», que no casaría con nada. Y los espacios se
    colapsan para que «landing   doors» case igual que «landing doors».
    """
    s = unicodedata.normalize("NFD", str(t or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    _p = [_raiz(p) for p in s.split() if p not in RELLENO]
    return " " + " ".join(_p) + " "


def _terminos() -> dict:
    """`término normalizado -> (tipo, [actividades])`, con los nombres del catálogo.

    ⚠️ Se construye al vuelo desde `stages` y no se guarda en una constante: si el
    catálogo cambia, esto cambia con él. Una copia congelada aquí sería una SEGUNDA
    definición de la lista de actividades, que es el fallo de v361.
    """
    from core import stages as S
    out = {}

    def _pon(txt, tipo, acts):
        k = normaliza(txt).strip()
        if len(k) < 3:
            return
        if k in out:
            # Mismo término por dos vías: se acumulan las actividades sin duplicar.
            _t, _a = out[k]
            out[k] = (_t, _a + [x for x in acts if x not in _a])
        else:
            out[k] = (tipo, list(acts))

    # 1. El nombre de la actividad, tal cual. Es el término más fiable que hay.
    # ⚠️ Y TAMBIÉN sin su paréntesis. Lo destapó el corpus de frases reales: «installed
    # belts» no casaba con «Install belts (motor, CW, cabin)» porque el paréntesis
    # formaba parte de la frase a buscar, y nadie escribe eso en un parte. Igual
    # «Surveyed shaft» contra «Survey (verify vs. existing shaft)». Dos actividades cuya
    # base coincide («Speaker (under cabin)» y «Speaker (top of cabin)») quedan en el
    # MISMO término y se proponen las dos: sin la zona, no hay forma honesta de elegir.
    for _v in S.ACTIVIDADES.values():
        for a in _v:
            _pon(a[0], "nombre", [a[0]])
            _base = re.sub(r"\s*\(.*?\)\s*", " ", a[0]).strip()
            if _base and _base != a[0]:
                _pon(_base, "nombre", [a[0]])
    # 2. Sus tareas.
    for act, tareas in TAREAS.items():
        for t in tareas:
            _pon(t, "tarea", [act])
    # 3. La jerga.
    for term, acts in SINONIMOS.items():
        _pon(term, "sinonimo", acts)
    return out


def buscar(texto, plan=None) -> dict:
    """Qué actividades sugiere este parte. NO decide: propone y explica por qué.

    `plan` = la lista que devuelve `stages.plan_de` para ESA obra. Si viene, todo lo que
    no esté en ella se aparta: proponer una etapa de desmontaje en una instalación no es
    una sugerencia mala, es una imposible.

    Devuelve `{candidatos, ambiguos, no_avance, sin_actividad, fuera_del_plan}`.
    """
    toks = _tokens(texto)
    # ⚠️ `plan_de` devuelve ETAPAS con sus actividades DENTRO —comprobado ejecutándolo,
    # no supuesto (v385)—, así que hay que aplanarlas. Leerlo mal dejaría `en_plan`
    # vacío, y un filtro vacío no filtra: pasaría en verde sin proteger nada (nº1).
    en_plan = None
    if plan:
        en_plan = {str(a.get("nombre") if isinstance(a, dict) else a)
                   for e in plan for a in (e.get("actividades") or [])}

    # ⚠️ UNA sola pasada para los cuatro tipos, del término más largo al más corto, con
    # una sola máscara. Antes los candidatos iban primero y lo ambiguo después, cada uno
    # por su lado, y eso daba dos respuestas equivocadas que el documento contradice:
    #   · «fixed LADDER CONTACT» salía como Ladder contact Y ADEMÁS como «contacts»
    #     ambiguo — y el documento dice que con el sitio nombrado va al sitio;
    #   · «joined FLEX CABLE», sin zona, salía como «Flex cables (top of cabin)» — y el
    #     documento dice que sin zona son LAS DOS, o sea ambiguo.
    # Compitiendo juntos por longitud se resuelven solas: «ladder contact» (2 palabras)
    # tapa a «contact» (1), y «flex cable top cabin» (4) gana a «flex cable» (2) solo
    # cuando la zona SÍ está escrita. En empate gana lo marcado, que es lo que el
    # documento señala expresamente.
    PRIO = {"amb": 0, "noav": 0, "sin": 0, "act": 1}
    pats = []
    for term, (tipo, acts) in _terminos().items():
        pats.append((term.split(), "act", (tipo, acts, term)))
    for k, v in AMBIGUOS.items():
        pats.append((normaliza(k).split(), "amb", {"termino": k, **v}))
    for k, v in NO_AVANCE.items():
        pats.append((normaliza(k).split(), "noav", {"termino": k, "motivo": v}))
    for k, v in SIN_ACTIVIDAD.items():
        pats.append((normaliza(k).split(), "sin", {"termino": k, "que_es": v}))
    pats.sort(key=lambda p: (-len(p[0]), -sum(len(w) for w in p[0]), PRIO[p[1]]))

    tapado = [False] * len(toks)
    dentro, fuera, amb, nop, sin = [], [], [], [], []
    vistos = set()
    for palabras, clase, dato in pats:
        if not palabras:
            continue
        pos = _casa(toks, palabras, tapado)
        if pos is None:
            continue
        # ⚠️ Se tapan las palabras DEL TÉRMINO, no las intrusas de en medio: en «cleaned
        # 4 car rails» el «4» y el «car» quedan libres por si otro término los necesita.
        for _j in pos:
            tapado[_j] = True
        if clase == "act":
            tipo, acts, term = dato
            for a in acts:
                if (a, term) in vistos:
                    continue
                vistos.add((a, term))
                fila = {"actividad": a, "termino": term, "fuente": tipo}
                (fuera if en_plan is not None and a not in en_plan else dentro).append(fila)
        elif clase == "amb":
            amb.append(dato)
            # ⚠️ Lo que el documento resuelve «por defecto» NO es una bifurcación: dice a
            # dónde va. «Pit doors» —«defaults to mechanical installation rather than being
            # left unscoreable»— quedaba marcado y sin proponer nada, que es justo lo que
            # el documento dice que no se haga. Se propone, con su origen a la vista.
            if len(dato["alternativas"]) == 1 and "default" in dato["regla"].lower():
                a = dato["alternativas"][0]
                if (a, dato["termino"]) not in vistos:
                    vistos.add((a, dato["termino"]))
                    fila = {"actividad": a, "termino": dato["termino"], "fuente": "defecto"}
                    (fuera if en_plan is not None and a not in en_plan
                     else dentro).append(fila)
        elif clase == "noav":
            nop.append(dato)
        else:
            sin.append(dato)
    return {"candidatos": dentro, "ambiguos": amb, "no_avance": nop,
            "sin_actividad": sin, "fuera_del_plan": fuera}


# ⚠️ Cuántas palabras se toleran METIDAS entre dos de un término. Los instaladores
# escriben «Cleaned 4 CAR rails», «Installed 2 door blades», «ripped out TOP 3 rings»:
# la cantidad y el sitio van en medio de la frase del catálogo, y con la búsqueda
# contigua de antes todas esas líneas se perdían — lo destapó el corpus de frases reales.
# Dos, y no más: con un hueco grande, «clean the shaft, rail delivery» acabaría
# acreditando «Clean rails». El corpus lleva casos NEGATIVOS para medir ese riesgo.
HUECO = 2

# ⚠️ Y el hueco NO cruza una frontera de oración. El corpus lo midió con un negativo
# sacado de los bloqueos del documento: «cleaned the pit, rails arriving tomorrow»
# acreditaba «Clean rails» — «clean» en una oración, «rails» en la siguiente, y los
# rieles ni siquiera habían llegado. Las palabras de un término viven en UNA oración, así
# que las comas, puntos y rayas cortan la búsqueda. ⚠️ La raya solo cuando va entre
# espacios: «3-phase» o «rip-out» son UNA palabra y no pueden partirse.
SEP = "|"
_LIMITE = re.compile(r"[,.;:!?()\n]|\s[-—–]\s|\s[—–]|[—–]\s")


def _tokens(texto) -> list:
    """Las palabras del parte, ya en raíz, con `SEP` donde acaba una oración."""
    out = []
    for trozo in _LIMITE.split(str(texto or "")):
        t = normaliza(trozo).split()
        if t:
            if out:
                out.append(SEP)
            out.extend(t)
    return out


def _casa(toks, palabras, tapado):
    """Posiciones donde aparecen las `palabras` EN ORDEN, con como mucho `HUECO`
    intrusas entre cada dos, sin pisar ninguna ya tapada ni cruzar un `SEP`.
    `None` si no aparecen."""
    n = len(toks)
    for i0 in range(n):
        if tapado[i0] or toks[i0] != palabras[0]:
            continue
        pos = [i0]
        for w in palabras[1:]:
            j, lim = pos[-1] + 1, min(n, pos[-1] + 2 + HUECO)
            while j < lim:
                if toks[j] == SEP:          # fin de oración: aquí no sigue el término
                    j = lim
                    break
                if not tapado[j] and toks[j] == w:
                    break
                j += 1
            if j >= lim:
                pos = None
                break
            pos.append(j)
        if pos is not None:
            return pos
    return None


def cuantos_terminos() -> int:
    """Cuántos términos distintos conoce el vocabulario. Para poder afirmar que hay
    alguno antes de creerse un «0 encontrados» (trampa nº1)."""
    return len(_terminos())
