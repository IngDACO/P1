# -*- coding: utf-8 -*-
"""El vocabulario contra frases REALES de instaladores, con la respuesta que da el usuario.

⚠️ Por qué esto y no frases mías: una frase inventada por quien escribe el buscador
acierta siempre — la escribo pensando en cómo la va a leer. Eso no es una medida, es un
espejo (trampa nº1 en su forma más cara).

Aquí las frases salen de `docs/`, donde el usuario las CITA literalmente de los partes
para explicar cada corrección («Cleaned 4 car rails», «Installed 2 door blades — Lift 3»,
«yemny wheel»…). Y la respuesta correcta tampoco la pongo yo: es la que da el documento en
esa misma línea, y va citada al lado de cada caso.

⚠️ LO QUE ESTO NO MIDE, y hay que decirlo antes de leer el número: el vocabulario se
construyó desde los MISMOS documentos, así que un acierto aquí dice «transcribí bien el
conocimiento y el buscador lo encuentra en prosa», NO «generaliza a partes que nunca vio».
Para eso hacen falta los partes en bruto. Este número es un techo, no una estimación.

Clases de resultado:
  ACIERTO  propone al menos una de las esperadas y ninguna que el documento descarte
  ERROR    propone algo que el documento dice expresamente que NO es — el peor caso
  FALLO    no propone nada de lo esperado (y nada equivocado)
"""
import os
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "owner", "grupo": "cliente1"}

from core import stages as S                                      # noqa: E402
from core import vocabulario as V                                 # noqa: E402

INST = S.plan_de("Installation", ())
RIP = S.plan_de("Ripout", (S.EXCLUYENTES["demolicion"]["opciones"][0],))

# (frase real, plan, tipo, esperado, descartado, por qué — cita del documento)
# tipo: act = actividades · amb = debe marcar ese ambiguo · noav = debe marcar no-avance
#       nada = no debe proponer nada
CASOS = [
    ("Cleaned 4 car rails", INST, "act", {"Clean rails"}, set(),
     "Stage 2 — Clean rails"),
    ("Installed 2 door blades — Lift 3", INST, "act", {"Install door panels"}, set(),
     "«Prep doors — panels/blades»: blades ARE the door panels"),
    ("Surveyed shaft — Lift 1", INST, "act", {"Survey (verify vs. existing shaft)"}, set(),
     "Stage 3 — Survey"),
    ("Installed/levelled MBB", INST, "act", {"Install motor bedplate"}, set(),
     "«MBB — Motor bedplate (confirmed abbreviation)»"),
    ("fire rating installed", INST, "act", {"Groutguarding (fire-rated)"}, set(),
     "«also called fire brackets, fire trims, fire rating»"),
    ("Filled sump hole", INST, "act", {"Seal machine room / shaft penetrations"}, set(),
     "«Sump hole — treated the same as seal machine room / shaft penetrations»"),
    ("Tuned magnet reader", INST, "act", {"Tune magnet reader"},
     {"Magnet reader (top of cabin)"},
     "«tune verb → Stage 14» — the install item is NOT the answer"),
    ("gauge top level", INST, "act", {"Install rings to top"}, set(),
     "«Gauge (e.g. gauge top level/ring) — part of this task»"),
    ("yemny wheel pinned to the rail", INST, "act", {"Install governor tension device"},
     set(), "«the earlier yemny wheel was a mishearing/typo» of Jenny wheel"),
    ("speed governor on cabin", INST, "act", {"Attach speed governor rope to cabin"},
     {"Install single bedplate"},
     "«the same rope gets attached to the cabin (here)» — not the Stage 6 governor"),
    ("fixed ladder contact", INST, "act", {"Ladder contact"}, set(),
     "Stage 12 — Ladder contact"),
    ("salsis contact done", INST, "act", {"Salsis contact"}, {"Install single bedplate"},
     "«salsis contact (pit)» — the tape on the bedplate is a different item"),
    ("photocell fitted on top of car", INST, "act", {"Lightrays (top of cabin)"}, set(),
     "«Lightrays — also called photocell»"),
    ("wired the revision box", INST, "act", {"OKR box (top of cabin)"}, set(),
     "«OKR — also called revision box»"),
    ("loadcell wired", INST, "act", {"Weight sensors (under cabin)"}, set(),
     "«Loadcell — alternate name for the weight sensor»"),
    ("pull test on the hook point", INST, "act",
     {"Snap test (trimmer beam/hook point load test)"}, set(),
     "«Snap test … also called a pull test»"),
    ("chisel pit", INST, "act", {"Chisel pit"}, set(), "Stage 8 — Chisel pit"),
    ("stack gates", INST, "act", {"Pack up"}, set(),
     "«stack gates is a Closeout-phase» — Pack up"),
    ("Remove stopblock", INST, "act", {"Remove stopblock"}, set(), "Stage 13"),
    ("installed belts", INST, "act", {"Install belts (motor, CW, cabin)"}, set(),
     "Stage 13 — Install belts"),
    ("plumb lasers set up in the pit", INST, "act",
     {"Throw plumblines, attach weights, let settle"}, set(),
     "«Logs mentioning plumb laser(s) map to this same stage/activity»"),
    ("Controller wiring", INST, "act", {"Wire all boxes"}, set(),
     "«Controller wiring belongs here (Stage 9) … Wire all boxes»"),
    ("helped level the car", INST, "act", {"Level/adjust car position"}, set(),
     "«If the entry names a specific task (e.g. helped level the car), credit it»"),
    ("test lift 1", INST, "act",
     {"Final functional test/run", "Load test", "Speed test", "Safety systems test"},
     set(), "«Logs from test day are often terse (test lift 1) … valid evidence»"),
    ("rooftop pieces up ready to drop", INST, "act", {"Install cabin ceiling (roof)"},
     set(), "«rooftop pieces … up ready to drop reflects this staged rigging»"),
    ("combo bracket on the first ring", INST, "act", {"Install first 2 rings"}, set(),
     "«Install first 2 rings — 1 omega bracket (also called combo bracket)»"),
    ("Picked up delivery from Schindler office, dropped off at job site", INST, "act",
     {"Other deliveries", "Receive lift delivery"}, set(), "a delivery run"),
    ("Built doors, complete internal hoardings, creating door jambs", INST, "act",
     {"Compound/Hoardings", "Install frames", "Install door panels"}, set(),
     "three actions in one sentence — any one is a hit"),
    ("Pit doors", INST, "act", {"Install door panels"}, set(),
     "«Pit doors (vague) — defaults to mechanical installation (Stage 7)»"),
    # ── ambiguos: tienen que salir MARCADOS ─────────────────────────────────────
    # ⚠️ La expectativa aceptaba solo «flex cable» y el modulo marca «flex»: el
    # comportamiento era el correcto (sale ambiguo, con la regla de las dos zonas) y la
    # que estaba mal era MI expectativa, demasiado estrecha. Corregida la prueba, no el
    # codigo — y dicho, porque ajustar una prueba es justo lo que hay que mirar dos veces.
    ("joined flex with Belden", INST, "amb", {"flex cable", "flex"}, set(),
     "«Flex cable (no zone specified) — treat as both» · Belden is a brand"),
    ("strip landing sills", INST, "amb", {"strip"}, set(),
     "«on an Installation job, strip means prepping»"),
    ("Under the cabin work", INST, "amb", {"under the cabin work"}, set(),
     "«read chronological order»"),
    ("Pit work", INST, "amb", {"pit work"}, set(), "«same logic»"),
    # ── no es avance ───────────────────────────────────────────────────────────
    # ⚠️ Igual: «induction» e «inductions» normalizan a lo mismo y sale la primera.
    ("helped with prep and inductions", INST, "noav", {"induction", "inductions"}, set(),
     "«Induction … don't count as progress»"),
    # ── no debe proponer nada ──────────────────────────────────────────────────
    ("Crane issue on hire truck — delayed unloading 2 hrs", INST, "nada", set(),
     {"Receive lift delivery"},
     "«Note issues separately, don't bury them in a progress line»"),
    ("Wired 3-phase outlet for orange box — machine room", INST, "nada", set(), set(),
     "orange box is RIP-OUT: on an installation it cannot be proposed"),
    # ── NEGATIVOS: el riesgo del hueco, medido en vez de supuesto ─────────────────
    # ⚠️ Tolerar dos palabras metidas en medio arregla «Cleaned 4 car rails» y abre la
    # puerta a juntar palabras que no van juntas. Estas frases salen de la sección de
    # BLOQUEOS reales del documento (Kemset, tornillería, herramienta encerrada…): son
    # las líneas que un parte trae y que NO son avance. Si alguna propone algo, el hueco
    # está cobrando precisión, y hay que verlo en el número, no fiarse.
    ("cleaned the pit, rails arriving tomorrow", INST, "nada", set(), {"Clean rails"},
     "the rails have NOT been cleaned — they have not even arrived"),
    ("waiting on door frames, could not install doors", INST, "nada", set(),
     {"Install frames", "Install door panels"},
     "«Door header/panel mismatches … can cause multi-day delays» — a blocker, not work"),
    ("Kemset drying, 18 hour cure, no progress on brackets", INST, "nada", set(), set(),
     "«Kemset drying time is a genuine bottleneck» — explicitly no progress"),
    ("missing 8mm bolts for the Z brackets, job stalled", INST, "nada", set(), set(),
     "«Bolt/fastener shortages are a recurring bottleneck»"),
    ("bandsaw locked in a colleague's toolbox on another job", INST, "nada", set(),
     {"Receive toolbox"}, "«Tool-access blockers are their own bottleneck category»"),
    # ── desmontaje ─────────────────────────────────────────────────────────────
    ("Wired 3-phase outlet for orange box — machine room", RIP, "act",
     {"Fully kill lift electrically / route mains power to tirak"}, set(),
     "«Orange box — the Inex kit's temporary 3-phase power box»"),
    ("three cages built", RIP, "act", {"Hoardings & protection"}, set(),
     "«Cages … same activity (Rip-Out R0, Hoardings & protection)»"),
    ("ripped out top 3 rings", RIP, "act", {"Rip out mechanical components - traction"},
     set(), "«e.g. top 3 rings being ripped out — folded into the traction line»"),
    ("Picked up rip-out kit", RIP, "act", {"Rip-out kit delivery"}, set(), "R0"),
    # ── v519 · decisiones del usuario del 27/09/2026 ─────────────────────────────
    ("roping all day", INST, "act", {"Install belts (motor, CW, cabin)"}, set(),
     "USER DECISION (option A): «roping means the lift was being belted that day»"),
    ("Chaser job on level 3", INST, "act",
     {"Cut/expand concrete door openings (chaser job)"}, set(),
     "«occasionally an opening is undersized … needs a chaser job» — informative"),
    ("programming with Danilo", INST, "act", {"Program controller parameters"}, set(),
     "«confirmed real-world activity, e.g. programming with [name] in logs»"),
    ("make lift as light as possible", RIP, "act",
     {"Lighten cabin if too heavy for intended tirak ratio"}, set(),
     "«Strip components to reduce weight (make lift as light as possible)»"),
]

# Casos que el documento resuelve de DOS maneras incompatibles. No se puntúan: se
# informan. Elegir una en silencio sería decidir por el usuario.
# ⚠️ VACÍA desde v519: la única que había —«roping»— la resolvió el usuario el
# 27/09/2026 (opción A, belting) y ahora es un caso puntuado más arriba. La lista se
# queda: la próxima contradicción del documento tiene que tener dónde informarse.
CONTRADICCIONES = []


def evalua(frase, plan, tipo, esperado, descartado):
    r = V.buscar(frase, plan)
    props = {c["actividad"] for c in r["candidatos"]}
    if tipo == "act":
        if props & descartado:
            return "ERROR", r, props
        return ("ACIERTO" if props & esperado else "FALLO"), r, props
    if tipo == "amb":
        vistos = {a["termino"] for a in r["ambiguos"]}
        return ("ACIERTO" if vistos & esperado else "FALLO"), r, props
    if tipo == "noav":
        vistos = {n["termino"] for n in r["no_avance"]}
        return ("ACIERTO" if vistos & esperado else "FALLO"), r, props
    if tipo == "nada":
        if props & descartado:
            return "ERROR", r, props
        return ("ACIERTO" if not props else "ERROR"), r, props
    raise ValueError(tipo)


def resultados():
    """`(cuenta, malos, ms)`. IMPORTABLE: `verif_v517` lo llama para que el corpus viva
    en la SUITE. Lo que solo se corre a mano se pudre — es literalmente lo que les pasó a
    las baterías (v515), que no estaban en la suite y acumularon 15 anclas muertas."""
    cuenta = {"ACIERTO": 0, "ERROR": 0, "FALLO": 0}
    malos = []
    t0 = time.perf_counter()
    for frase, plan, tipo, esp, desc, porque in CASOS:
        res, r, props = evalua(frase, plan, tipo, esp, desc)
        cuenta[res] += 1
        if res != "ACIERTO":
            malos.append((res, frase, tipo, esp, props, r, porque))
    return cuenta, malos, (time.perf_counter() - t0) * 1000.0


def _informe():
    cuenta, malos, ms = resultados()
    n = len(CASOS)
    print("CORPUS: %d frases reales citadas en docs/, con la respuesta del documento" % n)
    print("")
    for k in ("ACIERTO", "FALLO", "ERROR"):
        print("  %-8s %3d   %5.1f %%" % (k, cuenta[k], 100.0 * cuenta[k] / n))
    print("")
    print("  (%.1f ms las %d — %.2f ms por parte)" % (ms, n, ms / n))

    for res, frase, tipo, esp, props, r, porque in malos:
        print("")
        print("  %s · «%s»" % (res, frase))
        print("     esperaba (%s): %s" % (tipo, sorted(esp) or "nada"))
        print("     propuso:        %s" % (sorted(props) or "nada"))
        if r["ambiguos"]:
            print("     ambiguos:       %s" % [a["termino"] for a in r["ambiguos"]])
        if r["fuera_del_plan"]:
            print("     fuera del plan: %s"
                  % sorted({c["actividad"] for c in r["fuera_del_plan"]}))
        print("     documento:      %s" % porque)

    if CONTRADICCIONES:
        print("")
        print("SIN PUNTUAR — el documento se contradice:")
    for term, txt in CONTRADICCIONES:
        r = V.buscar(term, INST)
        print("  «%s» -> hoy propone %s"
              % (term, sorted({c["actividad"] for c in r["candidatos"]})))
        print("     %s" % txt)
    # Umbral: ningún ERROR. Un fallo es un hueco; un error es proponer lo contrario de
    # lo que dijo quien estuvo en obra.
    return 1 if cuenta["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(_informe())
