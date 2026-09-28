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

## v522 · Lo que enseñaron 1070 partes REALES (Simpro, 11 obras)

Hasta aquí el vocabulario solo se había medido contra frases que CITA el documento del
usuario — un techo, no una estimación. Con los partes de verdad acertaba del todo en 2 de
cada 3 propuestas, y los errores tenían forma: quitar leído como instalar («taking off the
Tirak» → *Mount tirak*), «rope» leído como belting, «light» como iluminación (era la
cortina de la puerta), lo PENDIENTE acreditado como hecho, y frases de etapa («shaft
wiring») sin nada que proponer.

⚠️ **La regla del usuario (28/09/2026): la app no asume nada.** Propone y el usuario
confirma; más autonomía, cuando la interpretación la gane. Por eso lo nuevo no «decide
mejor»: PREGUNTA donde antes acertaba o fallaba en silencio.
  · el contexto de cada ORACIÓN manda: lo que va bajo «Issues/Pendings» o dice «still
    needs…» va a `pendientes`; lo que es llevar material, a `no_avance`; un verbo de
    QUITAR nunca acredita una actividad de instalar (se convierte en su contrapartida o
    en el desmontaje, o se pregunta en `retiradas`);
  · una frase de ETAPA sin actividad concreta propone la etapa entera en `etapas`, para
    que el de campo marque lo que hizo (decisión del usuario);
  · varios ascensores en una nota se DETECTAN (`ascensores`) para proponer separarla —
    «L3» puede ser ascensor o NIVEL, así que eso se pregunta, no se decide.

⚠️ Los verbos IRREGULARES que sí aparecen en los partes («hung», «built») y las erratas
que se repiten («govenor», «tunned») entran como ALIAS — lista corta y con evidencia del
corpus, no un diccionario. El resto sigue siendo trabajo de la mitad con modelo.
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
    # ── v519 · decisiones del usuario del 27/09/2026 ──────────────────
    # «Roping» = BELTING ese día (su opción A). El documento decía dos cosas y estuvo
    # marcado sin acreditar hasta que el usuario eligió; ahora la contradicción no existe.
    "roping": ["Install belts (motor, CW, cabin)"],
    # Las que estaban «sin actividad» ya tienen casa: entran como INFORMATIVAS
    # (`stages.INFORMATIVAS`) — se reconocen y se pueden marcar, no cuentan.
    "lighten cabin": ["Lighten cabin if too heavy for intended tirak ratio"],
    "make lift as light as possible": ["Lighten cabin if too heavy for intended tirak ratio"],
    "bridging": ["Bridge landing door circuit (temporary)"],
    "bridge landing door": ["Bridge landing door circuit (temporary)"],
    "chaser job": ["Cut/expand concrete door openings (chaser job)"],
    "programming": ["Program controller parameters"],     # «programming with [name]»
    "program controller": ["Program controller parameters"],
    # ── v522 · lo que los partes REALES escriben y no estaba ──────────────────
    # ⚠️ Cada uno sale de la muestra de DISEÑO o de las frecuencias del corpus entero,
    # nunca de las 30 notas reservadas para medir: añadir un término porque falla una
    # frase de la prueba sería corregir el examen con sus respuestas (regla de v518).
    "belting": ["Install belts (motor, CW, cabin)"],      # «Belting», «Start belting»
    "shaft light": ["Lights"],                            # «Start shaft lighting»
    "kill lift": ["Fully kill lift electrically / route mains power to tirak"],  # «Kill the lift»
    "lifting beam": ["Install top-of-shaft beam/hook point"],   # «Lifting beam installed»
    "set beam": ["Install top-of-shaft beam/hook point"],       # desmontaje: «Set beam»
    # ⚠️ El peso del regulador está en el FOSO (su tensor), no en la bancada del regulador:
    # «Install pit Speed governor weight» salía como *Install single bedplate* porque la
    # tarea «install speed governor» (3 palabras) casaba primero. Cuatro palabras la tapan.
    "install pit speed governor": ["Install governor tension device"],
    "install speed governor weight": ["Install governor tension device"],
    "governor weight": ["Install governor tension device"],
    "call button": ["Call button wiring"],                # «L3 call button» (×7 en el corpus)
    "filler weights": ["Throw fillerweights"],            # «filler weights in» (×10)
    "first ring": ["Install first 2 rings"],
    "first two rings": ["Install first 2 rings"],
    "last ring": ["Install rings to top"],                # «Installed last ring»
    "install last ring": ["Install rings to top"],        # tapa a «install ring» (ambiguo)
    "final rings": ["Install rings to top"],              # «bed plates final rings»
    "kickplates": ["Install cabin interior handrails/kickplates/bumpers"],   # «kickplates in car»
    "kick plates": ["Install cabin interior handrails/kickplates/bumpers"],
    "builders lift": ["Builders lift protection & handover"],   # «Install builders lifts…» (×7)
    "set template": ["Set plumb template"],               # «dropped lines, set template»
    "dropped lines": ["Throw plumblines, attach weights, let settle"],
    "make light": ["Lighten cabin if too heavy for intended tirak ratio"],  # «…to make it light»
    # ── v522 · las RETIRADAS con nombre propio en el catálogo ────────────────
    # ⚠️ Van como término, y largo, para que ganen a su contrapartida: sin esto «Remove
    # stopblock» casaba igual, pero «remove tirak» o «remove template» no tenían a dónde ir
    # y el verbo de quitar acababa acreditando lo contrario (lo peor que puede pasar).
    "remove tirak": ["Remove tirak gear"],                # «taking off the Tirak», «tirak out»
    "take off tirak": ["Remove tirak gear"],
    "remove inex": ["Remove Inex kit components"],        # «Remove inex gear (not all yet)»
    "remove template": ["Remove plumb template/frame"],   # «Remove plumbline template»
    "remove rubbish": ["Final clear-out / site prepared for new install"],   # desmontaje
}

# ⚠️ Términos que el documento reconoce como REALES pero que NO tienen actividad en el
# catálogo. No se mapean a la actividad más parecida: eso sería inventar trabajo donde no
# lo hay, y con peso ajeno. Se reconocen y se dicen, para que el usuario decida.
# ⚠️ VACÍO desde v519, y a propósito: las tres que había (lighten cabin, bridging,
# chaser job) el usuario decidió que ENTRAN como informativas, así que ya tienen casa en
# `stages.INFORMATIVAS` y se mapean arriba como sinónimos. El mecanismo se queda: el
# desglose de tareas «se irá haciendo más granular», dice su propia cabecera, y lo
# próximo que no case tiene que tener dónde declararse en vez de colgarse de otra cosa.
# ⚠️ En INGLÉS, como todo lo que puede llegar a pantalla (v441-v452).
SIN_ACTIVIDAD = {}

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
    # (v518 tuvo aquí «roping», marcado por contradicción del documento. El 27/09/2026 el
    # usuario eligió «belting ese día»: ahora está en SINONIMOS y no es ambiguo.)
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
    # ── v522 · lo que en los partes REALES se leía mal por ir a una sola actividad ──
    # ⚠️ «light» iba directo a *Lights* (Shaft Wiring). En los partes era la cortina de la
    # puerta («3d light ray»), quitar peso («make it light») o la luz temporal. El documento
    # pone luces en CINCO sitios: se pregunta, igual que «contacts».
    "lights": {
        "alternativas": ["Lights", "Hang temporary work lighting", "Top-of-car emergency light",
                         "Ceiling decoration wiring (inside cabin)", "Switch light"],
        "regla": "Lights show up in five places: temporary work lighting (Set Up), the shaft "
                 "lights (Shaft Wiring), the ceiling decoration and the top-of-car emergency "
                 "light (Cabin Wiring) and the pit switch light. With no place named, ask.",
    },
    # ⚠️ «rope» NO es belting: «Roping» sí, por decisión del usuario, pero el documento
    # dice que hay varios aparatos con cuerda. «run govenor rope» acreditaba *Install belts*.
    "governor rope": {
        "alternativas": ["Attach speed governor rope to cabin", "Install governor tension device"],
        "regla": "The speed governor rope is attached to the cabin (Stage 4) and runs down to "
                 "the tension device pinned to the rail in the pit (Stage 8).",
    },
    # Los anillos y los rieles: los dos primeros van con el montaje (4/5); el resto, con la
    # subida del hueco (6). ⚠️ Solo con el verbo delante: «Cleaned 4 car rails» es *Clean
    # rails* y, sin verbo, «car rails» empataba en longitud y le robaba la frase.
    "install ring": {
        "alternativas": ["Install first 2 rings", "Install rings to top"],
        "regla": "The first two rings go in with Car Assembly (Stage 4); after that the "
                 "ring/rail pattern repeats up the shaft (Stage 6).",
    },
    "install rails": {
        "alternativas": ["Install first 2 car rails", "Install car rails to top",
                         "Install first 2 CW rails", "Install CW rails to top"],
        "regla": "Which side (car or counterweight) and which phase: the first two go with "
                 "the car/CW assembly, the rest with the shaft climb (Stage 6).",
    },
    "install car rails": {
        "alternativas": ["Install first 2 car rails", "Install car rails to top"],
        "regla": "The first two car rails go with Car Assembly (Stage 4); the rest with the "
                 "shaft climb (Stage 6).",
    },
    "install cw rails": {
        "alternativas": ["Install first 2 CW rails", "Install CW rails to top"],
        "regla": "The first two CW rails go with CW Assembly (Stage 5); the rest with the "
                 "shaft climb (Stage 6).",
    },
    "set rails": {
        "alternativas": ["Install first 2 car rails", "Install car rails to top",
                         "Install first 2 CW rails", "Install CW rails to top"],
        "regla": "Setting rails is the rail install itself: which side and which phase decide "
                 "the activity.",
    },
    "top rail": {
        "alternativas": ["Install car rails to top", "Install CW rails to top"],
        "regla": "Top rails are the shaft climb (Stage 6): car side or counterweight side.",
    },
    # ⚠️ El documento: «Governor bedplate… distinct component from the motor bedplate — not
    # the same plate, don't merge these».
    "bedplate": {
        "alternativas": ["Install motor bedplate", "Install single bedplate"],
        "regla": "Two distinct plates: the motor bedplate (omega side, motor and bottles) and "
                 "the single/Z-side bedplate (speed governor, salsis tape). Don't merge them.",
    },
    # ⚠️ «Balustrades … can mean either the cabin interior handrail or the rooftop handrail».
    "handrail": {
        "alternativas": ["Install cabin interior handrails/kickplates/bumpers",
                         "Install rooftop handrail"],
        "regla": "Context-dependent: the cabin interior handrail or the rooftop handrail.",
    },
    # En un desmontaje, limpiar el foso es dejarlo listo; al cerrar una instalación, es la
    # limpieza final del hueco. El plan de la obra reduce las opciones.
    "clean pit": {
        "alternativas": ["Final clear-out / site prepared for new install", "Clean shaft"],
        "regla": "On a rip-out it is the final clear-out; at closeout of an install it is the "
                 "shaft clean.",
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
    # ── v522 · lo más repetido de los partes reales que NO es avance ──────────
    "meeting": "A meeting — site support, not progress.",
    "site visit": "A site visit — site support, not progress.",
    "clock": "A timesheet note (clocking on/off), not progress.",
    "log off": "A timesheet note, not progress.",
    "log out": "A timesheet note, not progress.",
    "hours": "A timesheet note (hours worked), not progress.",
    "rubbish run": "Logistics (tip/rubbish run), not progress.",
    "scrap run": "Logistics (scrap run), not progress.",
    "bunnings": "A hardware-store run — logistics, not progress.",
}

# ═════════════════════════════════════════════════════════════════
# v522 · Frases de ETAPA: se propone la etapa entera y el usuario elige
# ═════════════════════════════════════════════════════════════════
# ⚠️ Decisión del usuario (28/09/2026): cuando el parte nombra solo la etapa («shaft wiring
# done»), se propone la ETAPA con sus actividades y el de campo marca las que hizo. Antes no
# se proponía nada: «shaft wiring» salió 33 veces sin reconocer en los partes reales.
# ⚠️ Van en una pasada APARTE, DESPUÉS de las actividades y solo sobre lo que quedó libre:
# «Prep all landing doors» es *Prep doors* (actividad), y si la etapa compitiera en la misma
# pasada, «landing doors» le quitaría la palabra y la propuesta sería menos precisa.
ETAPAS_TERMINOS = {
    "shaft wiring": [("install", 11)],
    "cabin wiring": [("install", 10)],          # «car wiring»: el alias une car = cabin
    "top of car wiring": [("install", 10)],
    "under cabin wiring": [("install", 10)],    # «undercabin wiring»
    "rooftop wiring": [("install", 10)],
    "pit wiring": [("install", 12)],
    "headroom wiring": [("install", 9)],
    "landing doors": [("install", 7)],
    "car sling": [("install", 4)],
    "build the car": [("install", 4)],
    "car installation": [("install", 4)],
    "plumbing": [("install", 3)],
    "commissioning": [("install", 14)],
    "testing": [("install", 14)],               # «test and items» (×4), «all the testing»
}

# ═════════════════════════════════════════════════════════════════
# v522 · El CONTEXTO de la oración: pendiente, logística, retirada
# ═════════════════════════════════════════════════════════════════
# ⚠️ Con los partes reales, 21 propuestas salieron de líneas bajo «Issues»/«Pendings lifts to
# do» — ahí se cuentan problemas y lo que FALTA, no avance. Y «cube also needs to be
# installed» acreditaba la caja. La regla del usuario: no asumir. Lo pendiente se aparta.
_CABECERA_PENDIENTE = re.compile(
    r"^\W*(?:issues?|problems?|pendings?(?:\s+lifts?)?(?:\s+to\s+do)?|pending\s+items?"
    r"|to\s+do(?:\s+list)?)\s*:?\s*(.*)$", re.I)
_NADA = re.compile(r"^\W*(?:nothing|none|nil|n/?a)(?:\s+today)?\W*$", re.I)
# «Today day 6 rip out», «Install day 12»: una cabecera del día, no trabajo.
_CABECERA_DIA = re.compile(
    r"^\W*(?:today\s+)?(?:(?:install(?:ation)?|rip\s*-?\s*out)\s+)?day\s*\d+\b"
    r"(?:\s+(?:install(?:ation)?|rip\s*-?\s*out))?", re.I)
_PENDIENTE = re.compile(
    r"\b(?:yet\s+to|still\s+(?:needs?|to\s+be|has\s+to|have\s+to)|needs?\s+to\s+be|need\s+to"
    r"|to\s+be\s+(?:done|installed|fitted|fixed|finished|completed)"
    r"|can'?t|cannot|couldn'?t|could\s+not|didn'?t|did\s+not|unable\s+to|wasn'?t\s+able"
    r"|waiting\s+(?:for|on)|missing|tomorrow|next\s+(?:week|day)|will\s+(?:be|need|have|do)"
    r"|arriving)\b", re.I)
# ⚠️ Lo que se LLEVA no es lo que se instala: «Loaded 3 sets of hoardings onto the hilux»
# acreditaba *Hoardings*. Excepción: las actividades que SON logística (recibir, entregar,
# recoger) — sin ella «Picked up delivery» dejaría de proponer la entrega.
_LOGISTICA = re.compile(
    r"\b(?:un)?load(?:ed|ing|s)?\b|\bpick(?:ed|ing|s)?\s+up\b|\bdrop(?:ped|ping|s)?\s+(?:off|at)\b"
    r"|\breturn(?:ed|ing|s)?\b|\bsen[dt]\s+back\b|\b(?:scrap|rubbish|tip)\s+runs?\b"
    r"|\bscrap\s*yard\b|\butes?\b|\bhilux\b|\bdmax\b", re.I)
LOGISTICAS = frozenset((
    "Receive toolbox", "Receive Inex kit", "Receive lift delivery",
    "Count/verify all boxes against delivery manifest", "Check box codes (multi-lift sites)",
    "Toolbox/gear delivery for installer", "Rip-out kit delivery", "Other deliveries", "Pack up",
    "Remove Inex kit components",
))
# ⚠️ Un verbo de QUITAR no puede acreditar lo contrario. Salió 27 veces con los partes reales:
# «taking off the Tirak» → *Mount tirak*, «Remove all cable trays» → *Install cable tray*.
# ⚠️ «strip» NO está: el documento dice que en una instalación es PREPARAR (quitar el
# plástico), y ya es ambiguo con su regla. «drop» tampoco: «Drop plumblines» es instalar.
# ⚠️ «ripPED out» y «ripPING out» sí; «rip-out» a secas NO: es el nombre de la fase o del kit
# («Picked up rip-out kit», «rip out tools»). La primera versión lo leía como verbo y el
# corpus de frases de v517 lo cazó: el kit se convertía en *Rip out mechanical*.
_RETIRADA = re.compile(
    r"\bremov\w*|\bdismantl\w*|\bdemolish\w*|\brip(?:ped|ping)\s*-?\s*out\b"
    # ⚠️ «take off» a secas es IRSE («so [name] could take off and then…»): solo cuenta con
    # algo que se quita detrás o en medio («taking off the Tirak», «Take out CW tank»).
    r"|\b(?:took|take[sn]?|taking)\s+(?:off|out|down|apart)\s+"
    r"(?!(?:and|then|to|at|from|for|so|early|home|work|with)\b)\w+"
    r"|\b(?:took|take[sn]?|taking)\s+(?!(?:me|us|him|her|them|it|off|out|a|an)\b)\w+\s+"
    r"(?:off|out|down|apart)\b"
    r"|\bpull(?:ed|ing|s)?\s+(?:out|off|down)\b|\bcut(?:ting|s)?\s+(?:\w+\s+){0,3}ropes?\b"
    r"|\bempt(?:y|ied|ying)\b|\b(?:tirak|tank|cabin|car|motor)\s+(?:is\s+|was\s+)?out\b", re.I)
# Lo que no está terminado se propone igual —el trabajo existe—, pero con el aviso a la vista.
_INCOMPLETO_SOLO = re.compile(
    r"^\W*(?:not\s+(?:all|finished|done|complete[d]?)(?:\s+yet)?|in\s+progress)\W*$", re.I)
_INCOMPLETO = re.compile(r"\bprogress\b|^\W*start(?:ed|ing|s)?\b", re.I)
_OTRO_DIA = re.compile(r"\byesterday\b", re.I)

# Qué es la contrapartida de retirar algo que se montó (se quita al cerrar la obra).
CONTRAPARTIDA = {
    "Mount tirak": ["Remove tirak gear"],
    "Attach tirak to cabin": ["Remove tirak gear"],
    "Hang tirak on hook point": ["Remove tirak gear"],
    "Attach tirak + stopblock": ["Remove tirak gear", "Remove stopblock"],
    "Install sky climber": ["Remove/dismantle sky climber & sky lock"],
    "Install sky lock": ["Remove/dismantle sky climber & sky lock"],
    "Set plumb template": ["Remove plumb template/frame"],
    "Build frame for template": ["Remove plumb template/frame"],
    "Mount plumbline frame + template": ["Remove plumb template/frame"],
    "Throw plumblines, attach weights, let settle": ["Remove plumb template/frame"],
    "Receive Inex kit": ["Remove Inex kit components"],
    # «Cages … get stacked/packed at Closeout once no longer needed (Stage 13 Pack Up)».
    "Hoardings & protection": ["Pack up"],
    "Compound/Hoardings": ["Pack up"],
}
# Lo que ya ES una retirada: se queda como está aunque lo diga un verbo de quitar.
_ES_RETIRADA = ("Remove", "Rip out", "Release", "Final clear-out", "Lighten", "Pack up",
                "Initial electrical shutdown", "Fully kill lift", "Retain/preserve")
# En un desmontaje, qué se estaba quitando decide si es mecánico o eléctrico. Raíces ya
# normalizadas, sacadas de los partes de diseño («Removed tank», «Remove All headers»,
# «Remove All shaft ducting and wiring», «Emptied CW filler»…).
_PIEZAS_MECANICAS = frozenset(("rail", "ring", "bracket", "cabin", "cw", "tank", "door", "header",
                               "sill", "frame", "panel", "pit", "buffer", "rop", "governor", "motor",
                               "machin", "sheav", "sling", "platform", "yoke", "filler", "shoe"))
_PIEZAS_ELECTRICAS = frozenset(("wir", "cabl", "flex", "controller", "box", "duct", "tray",
                                "trunk", "button"))
_RIP_MEC = ("Rip out mechanical components - traction", "Rip out mechanical components - hydraulic")
_RIP_ELEC = ("Rip out electrical components",)

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
    if len(p) <= 3 or p in _SIN_RAIZ:
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


# ⚠️ v522 · Palabras que NO se recortan. «roping» daba «rop», igual que «rope» y «ropes», así
# que el sinónimo de la decisión del usuario («roping» = belting) casaba con CUALQUIER cuerda:
# «Lubricating the ropes», «run govenor rope», «Cutting the rest of ropes» salían como
# *Install belts*. El documento lo advierte: hay varios aparatos con cuerda (regulador,
# tirak, minifor). Solo la palabra «roping» significa belting.
# ⚠️ «reverses» (las paredes frontales del hueco de puerta, según el documento) y «reverse»
# (dar la vuelta: «reverse rotation») caían en la misma raíz y un ajuste de giro acreditaba
# *Build cabin (walls)*.
_SIN_RAIZ = frozenset(("roping", "reverses"))

# ⚠️ v522 · Alias, a las DOS puntas y antes de la raíz. Lista corta y con evidencia de los
# partes reales, no un diccionario: el catálogo dice «cabin» y los partes «car»; el
# catálogo «CW» y los partes «CWT» o «counterweight»; y hay erratas que se repiten.
_ALIAS_FRASES = (
    (re.compile(r"\bcounter\s*-?\s*weights?\b", re.I), " cw "),
    (re.compile(r"\bstop\s*-?\s*blocks?\b", re.I), " stopblock "),
    (re.compile(r"\bblock\s*-?\s*stops?\b", re.I), " blockstop "),
    (re.compile(r"\bbed\s*-?\s*plates?\b", re.I), " bedplate "),
    (re.compile(r"\bguide\s*-?\s*rails?\b", re.I), " rail "),
    (re.compile(r"\blight\s*-?\s*rays?\b|\blight\s+curtains?\b", re.I), " lightrays "),
)
_ALIAS = {
    "cwt": "cw", "car": "cabin", "cars": "cabin",
    "undercar": "under cabin", "undercabin": "under cabin",
    "hung": "hang", "built": "build",                           # irregulares que SÍ salen
    "govenor": "governor", "govener": "governor", "governer": "governor",
    "governonr": "governor", "lnstall": "install", "lnstalled": "installed",
    "lnstalling": "installing", "firsr": "first", "survry": "survey",
    "litghing": "lighting", "tunned": "tuned", "tunne": "tune", "frqmes": "frames",
    "frams": "frames", "bedplare": "bedplate", "groudguards": "groutguards",
    "concrere": "concrete", "concret": "concrete", "rubbush": "rubbish", "innex": "inex",
}

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
    for _rx, _por in _ALIAS_FRASES:
        s = _rx.sub(_por, s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    _w = " ".join(_ALIAS.get(p, p) for p in s.split()).split()
    _p = [_raiz(p) for p in _w if p not in RELLENO]
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
    # 1b. v519 · Las INFORMATIVAS, por su nombre: se reconocen igual que las que pesan.
    # Que no cuenten lo dice el candidato (`cuenta=False`), no el buscador.
    for _v in S.INFORMATIVAS.values():
        for n in _v:
            _pon(n, "nombre", [n])
            _base = re.sub(r"\s*\(.*?\)\s*", " ", n).strip()
            if _base and _base != n:
                _pon(_base, "nombre", [n])
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

    Devuelve `{candidatos, ambiguos, no_avance, sin_actividad, fuera_del_plan}` y, desde
    v522, `etapas` (frase de etapa → la etapa entera, para que el usuario elija),
    `retiradas` (se quitó algo y no hay a qué atarlo: se pregunta) y `pendientes` (lo que
    el parte da como NO hecho: bajo «Issues/Pendings», o «still needs…», «can't…»).
    Cada propuesta lleva `linea` (la línea de la nota de la que sale) y, si toca, `aviso`
    («incompleto», «otro_dia»).
    """
    # ⚠️ `plan_de` devuelve ETAPAS con sus actividades DENTRO —comprobado ejecutándolo,
    # no supuesto (v385)—, así que hay que aplanarlas. Leerlo mal dejaría `en_plan`
    # vacío, y un filtro vacío no filtra: pasaría en verde sin proteger nada (nº1).
    from core import stages as S
    en_plan = None
    if plan:
        en_plan = {str(a.get("nombre") if isinstance(a, dict) else a)
                   for e in plan for a in (e.get("actividades") or [])}
        # ⚠️ v519 · Y las informativas de las etapas QUE ESTA OBRA TIENE: sin esto, un
        # «chaser job» en una instalación salía como «fuera del plan», que es falso — la
        # etapa 7 sí está en el plan; lo que pasa es que esa actividad no pesa.
        en_plan |= {n for e in plan for n in S.informativas(e.get("pista"), e.get("numero"))}
    _info = {n for _v in S.INFORMATIVAS.values() for n in _v}
    _pista = {a[0]: (p, n) for (p, n), _v in S.ACTIVIDADES.items() for a in _v}
    # ¿Hay desmontaje en esta obra? Sin plan (obra anterior a v512) se supone que sí: mejor
    # proponer de más que callar, porque quien acepta lo ve (el criterio de siempre).
    con_desmontaje = en_plan is None or any(a in en_plan for a in _RIP_MEC + _RIP_ELEC)

    claus = _clausulas(texto)
    toks, de = [], []
    for i, c in enumerate(claus):
        if toks:
            toks.append(SEP)
            de.append(None)
        toks.extend(c["toks"])
        de.extend([i] * len(c["toks"]))

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
    etapas, retiradas, pendientes = [], [], []
    vistos, usadas = set(), set()

    _filas = {}

    def _propone(a, term, fuente, c):
        # ⚠️ Una propuesta por actividad y término, pero con TODAS las líneas que la
        # respaldan: si la nota dice «Bolted tirak» después de nombrarla en otra línea, la
        # segunda es prueba, no ruido (la pantalla la enseña como evidencia).
        if (a, term) in vistos:
            _f = _filas.get((a, term))
            if _f is not None and c["linea"] not in _f["lineas"]:
                _f["lineas"].append(c["linea"])
            return
        vistos.add((a, term))
        # ⚠️ `cuenta` dice si mover esta casilla mueve el avance. Lo necesita quien venga
        # detrás (F2b, la pantalla): proponer una informativa como si fuera avance haría
        # creer que un «chaser job» subió la etapa.
        fila = {"actividad": a, "termino": term, "fuente": fuente, "cuenta": a not in _info,
                "linea": c["linea"], "lineas": [c["linea"]]}
        _filas[(a, term)] = fila
        if c["aviso"]:
            fila["aviso"] = c["aviso"]
        (fuera if en_plan is not None and a not in en_plan else dentro).append(fila)

    def _retira(acts):
        """Qué se propone cuando la oración QUITA algo. `(propuestas, sin_casa)`."""
        prop, sin_casa = [], []
        for a in acts:
            if a.startswith(_ES_RETIRADA) or a in _info or a in LOGISTICAS:
                prop.append(a)
            elif a in CONTRAPARTIDA:
                prop.extend(CONTRAPARTIDA[a])
            elif con_desmontaje and a in _pista:
                _p, _n = _pista[a]
                prop.extend(_RIP_ELEC if (_p == "install" and 9 <= _n <= 12) else _RIP_MEC)
            else:
                sin_casa.append(a)
        return list(dict.fromkeys(prop)), sin_casa

    def _anota(clase, dato, c):
        ctx = c["contexto"]
        if clase == "noav":
            nop.append(dict(dato, linea=c["linea"]))
            return
        if clase == "sin":
            sin.append(dict(dato, linea=c["linea"]))
            return
        if clase == "act":
            tipo, acts, term = dato
        else:
            tipo, acts, term = "ambiguo", list(dato["alternativas"]), dato["termino"]
        # ⚠️ El orden importa: lo PENDIENTE gana a todo (no está hecho, se quite o se
        # instale); luego la logística (se movió, no se montó); luego la retirada.
        if "pendiente" in ctx:
            pendientes.append({"termino": term, "actividades": acts, "linea": c["linea"],
                               "texto": c["texto"]})
            return
        if "logistica" in ctx:
            _log = [a for a in acts if a in LOGISTICAS]
            if not _log:
                nop.append({"termino": term, "linea": c["linea"],
                            "motivo": "Logistics — moving gear or material, not progress on "
                                      "the lift."})
                return
            acts = _log
        if "retirada" in ctx:
            usadas.add(id(c))
            prop, sin_casa = _retira(acts)
            if sin_casa and not prop:
                retiradas.append({"termino": term, "actividades": sin_casa, "linea": c["linea"],
                                  "texto": c["texto"],
                                  "motivo": "Something was removed and this job has no rip-out: "
                                            "ask whether it was rework, a transfer or packing up."})
                return
            if clase == "amb" and len(prop) > 1 and not all(p.startswith("Rip out") for p in prop):
                amb.append(dict(dato, alternativas=prop, linea=c["linea"]))
                return
            for a in prop:
                _propone(a, term, "retirada", c)
            return
        if clase == "act":
            for a in acts:
                _propone(a, term, tipo, c)
            return
        amb.append(dict(dato, linea=c["linea"]))
        # ⚠️ Lo que el documento resuelve «por defecto» NO es una bifurcación: dice a
        # dónde va. «Pit doors» —«defaults to mechanical installation rather than being
        # left unscoreable»— quedaba marcado y sin proponer nada, que es justo lo que
        # el documento dice que no se haga. Se propone, con su origen a la vista.
        if len(dato["alternativas"]) == 1 and "default" in dato["regla"].lower():
            _propone(dato["alternativas"][0], dato["termino"], "defecto", c)

    for palabras, clase, dato in pats:
        if not palabras:
            continue
        # ⚠️ TODAS las apariciones, no la primera: desde v522 la oración decide (pendiente,
        # retirada…) y la misma palabra puede estar en una línea hecha y en otra pendiente.
        while True:
            pos = _casa(toks, palabras, tapado)
            if pos is None:
                break
            # ⚠️ Se tapan las palabras DEL TÉRMINO, no las intrusas de en medio: en «cleaned
            # 4 car rails» el «4» y el «car» quedan libres por si otro término los necesita.
            for _j in pos:
                tapado[_j] = True
            _anota(clase, dato, claus[de[pos[0]]])

    # ── v522 · Pasada de ETAPAS, solo sobre lo que ninguna actividad reclamó ──────────
    _nombre = {(p, n): nom for p, n, nom, _w in S.etapas()}
    _et_idx = {}
    for term, dest in sorted(ETAPAS_TERMINOS.items(), key=lambda kv: -len(normaliza(kv[0]).split())):
        palabras = normaliza(term).split()
        while True:
            pos = _casa(toks, palabras, tapado)
            if pos is None:
                break
            for _j in pos:
                tapado[_j] = True
            c = claus[de[pos[0]]]
            for (p, n) in dest:
                acts = [a[0] for a in S.ACTIVIDADES.get((p, n), [])
                        if en_plan is None or a[0] in en_plan]
                if not acts:
                    continue
                if "pendiente" in c["contexto"]:
                    pendientes.append({"termino": term, "actividades": acts, "linea": c["linea"],
                                       "texto": c["texto"]})
                elif "logistica" in c["contexto"]:
                    continue
                elif "retirada" in c["contexto"]:
                    # ⚠️ Una etapa nombrada al QUITAR no es un desmontaje: «Remove and
                    # dismantle plumb jig» es retirar la plantilla. Solo las retiradas propias
                    # de esa etapa (o la contrapartida de lo que montó); si no hay, se pregunta.
                    usadas.add(id(c))
                    _suyas = [a for a in acts if a.startswith(_ES_RETIRADA)]
                    _suyas += [x for a in acts for x in CONTRAPARTIDA.get(a, [])]
                    _suyas = [a for a in dict.fromkeys(_suyas) if en_plan is None or a in en_plan]
                    if _suyas:
                        for a in _suyas:
                            _propone(a, term, "retirada", c)
                    else:
                        retiradas.append({"termino": term, "actividades": acts,
                                          "linea": c["linea"], "texto": c["texto"],
                                          "motivo": "A whole stage was named while removing "
                                                    "something: ask what was removed."})
                elif (p, n) in _et_idx:
                    # La misma etapa, otra vez en la nota: una sola propuesta, más pruebas.
                    _f = etapas[_et_idx[(p, n)]]
                    if c["linea"] not in _f["lineas"]:
                        _f["lineas"].append(c["linea"])
                else:
                    fila = {"pista": p, "numero": n, "etapa": _nombre.get((p, n), ""),
                            "termino": term, "actividades": acts, "linea": c["linea"],
                            "lineas": [c["linea"]]}
                    if c["aviso"]:
                        fila["aviso"] = c["aviso"]
                    _et_idx[(p, n)] = len(etapas)
                    etapas.append(fila)

    # ── v522 · Una oración que QUITA una pieza y no nombró ninguna actividad ─────────
    # «Removed tank», «Car ripped out», «Remove All headers»: en un desmontaje, la pieza
    # dice si es la parte mecánica o la eléctrica. Sin desmontaje en el plan, se pregunta.
    for c in claus:
        if "retirada" not in c["contexto"] or id(c) in usadas or "pendiente" in c["contexto"]:
            continue
        piezas = set(c["toks"])
        props = []
        if piezas & _PIEZAS_MECANICAS:
            props += list(_RIP_MEC)
        if piezas & _PIEZAS_ELECTRICAS:
            props += list(_RIP_ELEC)
        if not props:
            continue
        if con_desmontaje:
            for a in props:
                _propone(a, " ".join(sorted(piezas & (_PIEZAS_MECANICAS | _PIEZAS_ELECTRICAS))),
                         "retirada", c)
        else:
            retiradas.append({"termino": c["texto"], "actividades": [], "linea": c["linea"],
                              "texto": c["texto"],
                              "motivo": "Something was removed and this job has no rip-out: "
                                        "ask whether it was rework, a transfer or packing up."})

    return {"candidatos": dentro, "ambiguos": amb, "no_avance": nop,
            "sin_actividad": sin, "fuera_del_plan": fuera,
            "etapas": etapas, "retiradas": retiradas, "pendientes": pendientes}


def _clausulas(texto) -> list:
    """La nota partida en ORACIONES, cada una con su contexto.

    ⚠️ Línea a línea: las cabeceras «Issues» / «Pendings lifts to do:» abren una sección
    que llega hasta el final de la nota, y todo lo que va debajo es PENDIENTE. La cabecera
    del día («Install day 12») se quita: no es trabajo, y su «install» podía emparejarse
    con la palabra de al lado por el hueco.
    ⚠️ Un paréntesis que solo dice «not finished yet» / «not all yet» marca la oración
    ANTERIOR como incompleta: el trabajo existe, pero el usuario tiene que verlo.
    """
    out = []
    en_pendiente = False
    for n_linea, linea in enumerate(str(texto or "").splitlines()):
        l = linea.strip()
        if not l:
            continue
        m = _CABECERA_PENDIENTE.match(l)
        if m:
            en_pendiente = True
            l = m.group(1).strip()
            if not l or _NADA.match(l):
                continue
        l = _CABECERA_DIA.sub(" ", l)
        prev = None
        for trozo in _LIMITE.split(l):
            t = trozo.strip()
            if not t:
                continue
            if _INCOMPLETO_SOLO.match(t):
                if prev is not None:
                    prev["aviso"] = "incompleto"
                continue
            c = {"texto": t, "toks": normaliza(t).split(), "linea": n_linea,
                 "contexto": set(), "aviso": ""}
            if en_pendiente or _PENDIENTE.search(t):
                c["contexto"].add("pendiente")
            if _LOGISTICA.search(t):
                c["contexto"].add("logistica")
            if _RETIRADA.search(t):
                c["contexto"].add("retirada")
            if _OTRO_DIA.search(t):
                c["aviso"] = "otro_dia"
            elif _INCOMPLETO.search(t):
                c["aviso"] = "incompleto"
            if c["toks"]:
                out.append(c)
                prev = c
    return out


# ═════════════════════════════════════════════════════════════════
# v522 · Varios ascensores en una nota: se DETECTA, para proponer separarla
# ═════════════════════════════════════════════════════════════════
# ⚠️ Decisión del usuario (28/09/2026): «propón separar». El documento: «Multi-lift jobs
# track progress per lift, independently» y «multi-job days need the log entry split … before
# being fed into any one job's tracker». La app es 1 obra = 1 ascensor.
# ⚠️ Solo «lift N» es un ascensor seguro. «L3» es ascensor O NIVEL según la obra («landing
# buttons on level 3» vs «rope tensions in L3 and L1»), y «M2», «SL3» son nombres propios de
# una obra: van a `dudosos`, para preguntar — no se decide por el usuario.
_ASC_EXPLICITO = re.compile(
    r"\blifts?\s*(?:#|no\.?\s*|number\s*)?(\d{1,2})\b"
    r"((?:\s*(?:,|&|and|\+)\s*(?:lifts?\s*)?\d{1,2}\b)*)", re.I)
_ASC_DUDOSO = re.compile(r"\b(?:L|M|SL)\s?\d{1,2}\b|\bL[Il]\b")


def ascensores(texto) -> dict:
    """Qué ascensores nombra la nota y qué líneas van con cada uno.

    `{ascensores, dudosos, por_ascensor, separar}`. `separar` = nombra 2 o más ascensores
    de forma explícita: es una PROPUESTA de partir la nota, no una decisión.
    Una línea que es solo «Lift 3» abre sección: las siguientes van con ese ascensor.
    """
    por, explicitos, dudosos = {}, [], []
    actual = ""
    for linea in str(texto or "").splitlines():
        l = linea.strip()
        if not l:
            continue
        nums = []
        for m in _ASC_EXPLICITO.finditer(l):
            nums += re.findall(r"\d{1,2}", m.group(0))
        nums = list(dict.fromkeys(nums))
        for m in _ASC_DUDOSO.finditer(l):
            if m.group(0) not in dudosos:
                dudosos.append(m.group(0))
        if len(nums) == 1 and not normaliza(_ASC_EXPLICITO.sub(" ", l)).split():
            actual = nums[0]                     # la línea ES la cabecera «Lift 3»
            if actual not in explicitos:
                explicitos.append(actual)
            continue
        for n in nums:
            if n not in explicitos:
                explicitos.append(n)
        for d in (nums or [actual]):
            por.setdefault(d, []).append(l)
    return {"ascensores": explicitos, "dudosos": dudosos, "por_ascensor": por,
            "separar": len(explicitos) >= 2}


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
