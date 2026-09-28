# -*- coding: utf-8 -*-
"""v522 · EL VOCABULARIO CONTRA 1070 PARTES REALES: proponer, no asumir.

El usuario compartió los partes de Simpro de 11 obras (28/09/2026). Con ellos, el
vocabulario de v517-v519 acertaba del todo 2 de cada 3 propuestas, y los errores tenían
forma: quitar leído como montar, «rope» como belting, «light» como iluminación, lo
PENDIENTE como hecho, y las frases de etapa sin nada. La regla del usuario: la app NO
asume — propone y el usuario confirma. Y dos decisiones: una frase de etapa propone la
etapa entera; varios ascensores en una nota proponen separarla.

Lo que protege (cada caso es una frase de los partes reales, sin nombres):
  (a) «roping» es belting (decisión v519) y «rope» NO lo es;
  (b) un verbo de QUITAR nunca acredita MONTAR — se convierte en su retirada, en el
      desmontaje, o se pregunta; «rip-out kit» NO es un verbo (fallo cazado al hacerlo);
  (c) lo pendiente se aparta, lo que se lleva no se monta — sin perder las entregas;
  (d) la etapa se propone ENTERA solo donde ninguna actividad reclamó la frase;
  (e) «light» se pregunta; la cortina de la puerta y el «make it light» van a lo suyo;
  (f) lo que el parte da por empezado o por otro día sale con su aviso;
  (g) varios ascensores → proponer separar; «L3» se pregunta (puede ser NIVEL);
  (h) ⚠️ el corpus REAL como suelo: 0 propuestas desde «Issues/Pendings», 0 verbos de
      quitar que acrediten montar en la misma oración, y las 30 notas reservadas no bajan.
Todo EJECUTANDO `buscar` (v378).
"""
import importlib.util
import io
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s %s" % (q, ("-> %s" % (det,)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("")
    print(x)


from core import stages as S                                      # noqa: E402
from core import vocabulario as V                                 # noqa: E402

TRAC = S.EXCLUYENTES["demolicion"]["opciones"][0]
INST = S.plan_de("Installation", ())
RIP = S.plan_de("Ripout", (TRAC,))
COMB = S.plan_de("Ripout + Installation", (TRAC,))
CAT = ({a[0] for _v in S.ACTIVIDADES.values() for a in _v}
       | {n for _v in S.INFORMATIVAS.values() for n in _v})
BELTS = "Install belts (motor, CW, cabin)"


def acts(texto, plan):
    return [c["actividad"] for c in V.buscar(texto, plan)["candidatos"]]


# ═════════════════════════════════════════════════════════════════
sec("1. «roping» es belting; «rope» no")
chk("«roping» NO cae en la raíz de «rope»", V._raiz("roping") != V._raiz("rope"),
    (V._raiz("roping"), V._raiz("rope")))
chk("...y «rope»/«ropes» siguen siendo la misma palabra", V._raiz("rope") == V._raiz("ropes"))
chk("«Finished roping lift 5» → belting (decisión del usuario)",
    BELTS in acts("Finished roping lift 5", INST), acts("Finished roping lift 5", INST))
for _f in ("Lubricating the ropes of the lift", "run govenor rope",
           "Setting rope tensions with the tuner"):
    chk("«%s» NO es belting" % _f, BELTS not in acts(_f, INST), acts(_f, INST))
_r = V.buscar("run govenor rope", INST)
chk("«govenor rope» (errata incluida) se PREGUNTA: cabina o foso",
    any(a["termino"] == "governor rope" for a in _r["ambiguos"]), [a["termino"] for a in _r["ambiguos"]])
chk("«Cutting the rest of ropes» en un desmontaje → desmontaje, no belting",
    "Rip out mechanical components - traction" in acts("Cutting the rest of ropes", COMB)
    and BELTS not in acts("Cutting the rest of ropes", COMB), acts("Cutting the rest of ropes", COMB))

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ Quitar nunca acredita montar")
for _f in ("taking off the Tirak", "tirak out"):
    _a = acts(_f, COMB)
    chk("«%s» → Remove tirak gear, y NO Mount tirak" % _f,
        "Remove tirak gear" in _a and "Mount tirak" not in _a, _a)
_a = acts("Remove all cable trays and components shaft", COMB)
chk("«Remove all cable trays…» → desmontaje eléctrico, NO Install cable tray",
    "Rip out electrical components" in _a and "Install cable tray" not in _a, _a)
_a = acts("Remove hoardings", INST)
chk("«Remove hoardings» en una instalación → Pack up (el documento: se recogen al cerrar)",
    "Pack up" in _a and "Compound/Hoardings" not in _a, _a)
chk("«Removed tank» en un desmontaje → la parte mecánica (la pieza lo dice)",
    "Rip out mechanical components - traction" in acts("Removed tank", COMB), acts("Removed tank", COMB))
_r = V.buscar("Removed tank", INST)
chk("...y en una instalación SIN desmontaje no se inventa nada: se PREGUNTA",
    not _r["candidatos"] and _r["retiradas"], (_r["candidatos"], _r["retiradas"]))
# ⚠️ El fallo que salió al hacerlo: «rip-out» es el nombre del kit, no un verbo.
_a = acts("Picked up rip-out kit", RIP)
chk("«Picked up rip-out kit» sigue siendo la entrega del kit (no un desmontaje)",
    _a == ["Rip-out kit delivery"], _a)
_c = V._clausulas("so the driver could take off and then proceeded to take them up")
chk("«could take off and then…» es IRSE, no quitar",
    not any("retirada" in c["contexto"] for c in _c), [sorted(c["contexto"]) for c in _c])
# ⚠️ ESCAPE CAZADO POR LA BATERÍA: «Picked up rip-out kit» pasaba aunque «rip-out» volviera
# a ser verbo, porque las entregas NUNCA se convierten (segunda red). Aquí se prueba la
# primera por sí sola: «rip out» a secas es la FASE; «ripped out», el verbo.
chk("«Start rip out» (la fase) NO es una oración de quitar",
    not any("retirada" in c["contexto"] for c in V._clausulas("Start rip out")))
chk("...y «Car ripped out» SÍ lo es (la sonda ve el caso bueno)",
    any("retirada" in c["contexto"] for c in V._clausulas("Car ripped out")))
_a = acts("Remove and dismantle plumb jig", COMB)
chk("«Remove and dismantle plumb jig» → retirar la plantilla, SIN desmontaje de propina",
    "Remove plumb template/frame" in _a and not any(a.startswith("Rip out") for a in _a), _a)
chk("«reverse rotation» NO son las paredes («reverses») de la cabina",
    "Build cabin (walls)" not in acts("helped the tuner reverse rotation on the lift", INST))

# ═════════════════════════════════════════════════════════════════
sec("3. Lo pendiente se aparta; lo que se lleva no se monta")
_r = V.buscar("Install day 12\nInstalled header\nPendings lifts to do:\n"
              "We had a go at the chaser job to trim the walls for 3 hours.", INST)
chk("lo de ANTES de «Pendings» se propone", "Install headers" in [c["actividad"] for c in _r["candidatos"]])
chk("...lo de DEBAJO no: va a `pendientes`",
    not any("chaser" in c["actividad"] for c in _r["candidatos"])
    and any("chaser" in " ".join(p["actividades"]) for p in _r["pendientes"]),
    ([c["actividad"] for c in _r["candidatos"]], _r["pendientes"]))
_r = V.buscar("cube also needs to be installed", INST)
chk("«cube also needs to be installed» NO acredita la caja", not _r["candidatos"] and _r["pendientes"])
_r = V.buscar("Installed all sills\nPendings lifts to do: Nothing today", INST)
chk("«Pendings…: Nothing today» no aparta nada", "Install sills" in [c["actividad"] for c in _r["candidatos"]]
    and not _r["pendientes"])
_r = V.buscar("Loaded 3 sets of hoardings onto the hilux", INST)
chk("«Loaded … hoardings onto the hilux» es logística, no montar", not _r["candidatos"] and _r["no_avance"])
chk("...pero una ENTREGA sigue siendo su actividad («Picked up delivery»)",
    "Receive lift delivery" in acts("Picked up delivery from the office", INST))

# ═════════════════════════════════════════════════════════════════
sec("4. La etapa ENTERA, solo donde ninguna actividad reclamó la frase")
_r = V.buscar("Shaft wiring done", INST)
_e = [e for e in _r["etapas"] if (e["pista"], e["numero"]) == ("install", 11)]
chk("«Shaft wiring done» propone la etapa 11", bool(_e), _r["etapas"])
_esp = [a["nombre"] for e in INST if (e["pista"], e["numero"]) == ("install", 11)
        for a in e["actividades"]]
chk("...con sus actividades del PLAN para que el usuario elija", bool(_e) and _e[0]["actividades"] == _esp,
    (_e[0]["actividades"] if _e else None, _esp))
chk("...y no se inventa una actividad concreta", not _r["candidatos"])
_r = V.buscar("Prep all landing doors", INST)
chk("«Prep all landing doors» es Prep doors — la actividad gana a la etapa",
    "Prep doors (panels/blades, frames)" in [c["actividad"] for c in _r["candidatos"]] and not _r["etapas"],
    ([c["actividad"] for c in _r["candidatos"]], _r["etapas"]))
chk("«Installed all landing doors» propone la etapa 7",
    [(e["pista"], e["numero"]) for e in V.buscar("Installed all landing doors", INST)["etapas"]]
    == [("install", 7)])
_r = V.buscar("Shaft wiring done\nFinished shaft wiring", INST)
chk("la misma etapa dos veces → UNA propuesta con las dos líneas",
    len(_r["etapas"]) == 1 and _r["etapas"][0]["lineas"] == [0, 1], _r["etapas"])
chk("una etapa que la obra no tiene no se propone (instalación en un desmontaje)",
    not V.buscar("Shaft wiring done", RIP)["etapas"])
for _f in ("Top of car wiring", "Undercabin wiring"):
    chk("«%s» → etapa 10" % _f,
        [(e["pista"], e["numero"]) for e in V.buscar(_f, INST)["etapas"]] == [("install", 10)])
# ⚠️ El alias se aplica a las DOS puntas, así que «Top of car wiring» casaría igual sin él
# (la frase de etapa también dice «car»). Lo que SÍ depende del alias: el catálogo escribe
# «cabin»/«CW» y los partes «car»/«CWT» — «car doors» sale 11 veces en el corpus.
chk("«Installed car doors» → Install cabin doors (car = cabin)",
    "Install cabin doors" in acts("Installed car doors", INST), acts("Installed car doors", INST))
chk("«installing CWT guide shoes» → Install CW guide shoes (CWT = CW)",
    "Install CW guide shoes" in acts("installing CWT guide shoes", INST),
    acts("installing CWT guide shoes", INST))

# ═════════════════════════════════════════════════════════════════
sec("5. «light» se pregunta")
_a = acts("Looked at 3d light ray", INST)
chk("«3d light ray» es la cortina de la puerta", "Lightrays (top of cabin)" in _a and "Lights" not in _a, _a)
_a = acts("Remove gear under the car to make it light", COMB)
chk("«…to make it light» es aligerar la cabina (informativa), no iluminación",
    "Lighten cabin if too heavy for intended tirak ratio" in _a and "Lights" not in _a, _a)
_r = V.buscar("worked on the lights", INST)
chk("«lights» a secas se PREGUNTA, con sus cinco sitios",
    any(a["termino"] == "lights" and len(a["alternativas"]) >= 4 for a in _r["ambiguos"])
    and "Lights" not in [c["actividad"] for c in _r["candidatos"]], (_r["ambiguos"], _r["candidatos"]))
_c = [c for c in V.buscar("Start shaft lighting", INST)["candidatos"] if c["actividad"] == "Lights"]
chk("«Start shaft lighting» → Lights, avisando que está EMPEZADO",
    bool(_c) and _c[0].get("aviso") == "incompleto", _c)

# ═════════════════════════════════════════════════════════════════
sec("6. Lo empezado o de otro día, con su aviso")
_e = V.buscar("Start pit wiring (not finished yet) Fix flex under cabin", INST)["etapas"]
chk("«Start pit wiring (not finished yet)» → etapa 12 con aviso «incompleto»",
    any(e["numero"] == 12 and e.get("aviso") == "incompleto" for e in _e), _e)
_c = [c for c in V.buscar("Remove inex gear (not all yet)", INST)["candidatos"]
      if c["actividad"] == "Remove Inex kit components"]
chk("«Remove inex gear (not all yet)» → retirar el Inex, con aviso", bool(_c) and _c[0].get("aviso") == "incompleto", _c)
_c = [c for c in V.buscar("we did grout guards for the frame yesterday", INST)["candidatos"]]
chk("«…yesterday» avisa de que es OTRO día", bool(_c) and all(c.get("aviso") == "otro_dia" for c in _c), _c)

# ═════════════════════════════════════════════════════════════════
sec("7. Varios ascensores → proponer separar; «L3» se pregunta")
_a = V.ascensores("lift 3 and lift 1 forgot to log out")
chk("«lift 3 and lift 1» → dos ascensores, proponer separar", _a["ascensores"] == ["3", "1"] and _a["separar"], _a)
_a = V.ascensores("landing buttons on level 3 no gyprock can't install yet")
chk("«level 3» NO es un ascensor", not _a["ascensores"] and not _a["separar"], _a)
_a = V.ascensores("Setting rope tensions in L3 and LI")
chk("«L3 and LI» va a DUDOSOS (ascensor o nivel), sin separar",
    {"L3", "LI"} <= set(_a["dudosos"]) and not _a["separar"], _a)
# ⚠️ ESCAPE CAZADO POR LA BATERÍA: con UNA sola «L» nunca se proponía separar, así que
# tratar «L3» como ascensor seguro no se notaba. Con DOS (frase real del corpus) sí.
_a = V.ascensores("Revising car earth wiring in L5 and L4")
chk("«…in L5 and L4» NO propone separar: pueden ser dos NIVELES",
    not _a["separar"] and {"L5", "L4"} <= set(_a["dudosos"]), _a)
_a = V.ascensores("Lift 3\nInstalled headers\nLift 1\nInstalled sills")
chk("una línea «Lift 3» abre sección para las siguientes",
    _a["por_ascensor"].get("3") == ["Installed headers"] and _a["por_ascensor"].get("1") == ["Installed sills"], _a)
chk("«Lift2 finishing items list» es UN ascensor: no hay nada que separar",
    V.ascensores("Lift2 finishing items list")["ascensores"] == ["2"]
    and not V.ascensores("Lift2 finishing items list")["separar"])

# ═════════════════════════════════════════════════════════════════
sec("8. Las tablas nuevas apuntan a cosas que EXISTEN")
_et = {(p, n) for p, n, _nom, _w in S.etapas()}
chk("las etapas de ETAPAS_TERMINOS existen", all(d in _et for v in V.ETAPAS_TERMINOS.values() for d in v))
_mal = sorted({a for k, v in V.CONTRAPARTIDA.items() for a in [k] + v if a not in CAT})
chk("CONTRAPARTIDA solo nombra actividades del catálogo", not _mal, _mal)
chk("LOGISTICAS y los desmontajes existen",
    not (set(V.LOGISTICAS) | set(V._RIP_MEC) | set(V._RIP_ELEC)) - CAT,
    sorted((set(V.LOGISTICAS) | set(V._RIP_MEC) | set(V._RIP_ELEC)) - CAT))

# ═════════════════════════════════════════════════════════════════
sec("9. ⚠️ El corpus REAL como suelo (D:\\CopeX\\Logs_simpro, fuera del repo)")
# ⚠️ Los partes llevan NOMBRES de trabajadores: viven fuera del repo (el despliegue hace
# `git add` de todo) y aquí solo se imprimen CUENTAS. Si no están, esto FALLA — un corpus
# que no se encuentra no puede salir en verde (trampa nº1).
T = r"D:\CopeX\Logs_simpro\_texto"
_pj = os.path.join(T, "partes.json")
if not os.path.isfile(_pj):
    fallo("no está el corpus real en %s" % _pj)
else:
    partes = json.load(io.open(_pj, encoding="utf-8"))
    conds = [c["nombre"] for p in S.PISTAS for c in S.condicionales(p) if "hydraulic" not in c["nombre"]]
    PLAN = S.plan_de("Ripout + Installation", conds)
    PISTA = {a[0]: p for (p, n), v in S.ACTIVIDADES.items() for a in v}
    CAB = re.compile(r"^\W*(issues?|problems?|pendings?( lifts?)?( to do)?|pending items?|to do( list)?)\s*:?", re.I)
    # ⚠️ «Install day 12» es la cabecera del día, no una línea de trabajo: contarla en el
    # denominador bajaba la cobertura a 37,6% con el MISMO resultado (el análisis del
    # corpus la excluye; sin esto la medida del guardián y la del informe no coincidían).
    DIA = re.compile(r"^\W*(today\s+)?((install(ation)?|rip\s*-?\s*out)\s+)?day\s*\d+\W*"
                     r"((install(ation)?|rip\s*-?\s*out)\W*)?$", re.I)
    QUITAR = re.compile(r"\bremov\w*|\bdismantl\w*|\brip(?:ped|ping)\s*-?\s*out\b"
                        r"|\b(?:took|take[sn]?|taking)\s+(?:\w+\s+)?(?:off|out|down|apart)\b"
                        r"|\bcut(?:ting)?\s+(?:\w+\s+){0,3}ropes?\b|\b(?:tirak|tank|car|cabin|motor)\s+out\b", re.I)
    OKR = ("Remove", "Rip out", "Release", "Final clear-out", "Lighten", "Pack up",
           "Initial electrical shutdown", "Fully kill lift", "Retain/preserve")
    lin_bloq = prop_bloq = trab = trab_con = 0
    for p in partes:
        r = V.buscar("\n".join(p["lineas"]), PLAN)
        con = {i for c in r["candidatos"] for i in c["lineas"]} | {i for e in r["etapas"] for i in e["lineas"]}
        bloq = False
        for i, l in enumerate(p["lineas"]):
            if CAB.match(l):
                bloq = True
                continue
            if DIA.match(l):
                continue
            if bloq:
                lin_bloq += 1
                prop_bloq += i in con
            else:
                trab += 1
                trab_con += i in con
    chk("el corpus trae los 1070 partes (%d)" % len(partes), len(partes) >= 1000)
    chk("...y hay líneas bajo «Issues/Pendings» que mirar (%d)" % lin_bloq, lin_bloq > 100)
    chk("NINGUNA propuesta sale de «Issues/Pendings» (%d)" % prop_bloq, prop_bloq == 0)
    n_q = contra = 0
    for p in partes:
        for l in p["lineas"]:
            for c in V._clausulas(l):
                if QUITAR.search(c["texto"]):
                    n_q += 1
                    contra += any(PISTA.get(x["actividad"]) == "install" and not x["actividad"].startswith(OKR)
                                  for x in V.buscar(c["texto"], PLAN)["candidatos"])
    chk("hay oraciones de quitar que mirar (%d)" % n_q, n_q > 100)
    chk("NINGUNA acredita montar en la MISMA oración (%d)" % contra, contra == 0)
    # ⚠️ TRINQUETE: la cobertura puede subir, no bajar por accidente (v522: 39,2%).
    chk("cobertura de líneas de trabajo ≥ 39%% (%.1f%%)" % (100.0 * trab_con / trab), trab_con / trab >= 0.39)

    # Las 30 notas RESERVADAS, etiquetadas ANTES de cambiar el vocabulario.
    _et = os.path.join(T, "analisis", "etiquetas_prueba.py")
    _no = os.path.join(T, "analisis", "prueba_notas.json")
    if not (os.path.isfile(_et) and os.path.isfile(_no)):
        fallo("no están las etiquetas de la muestra reservada")
    else:
        _sp = importlib.util.spec_from_file_location("etq522", _et)
        E = importlib.util.module_from_spec(_sp)
        _sp.loader.exec_module(E)
        ETAPA_DE = {a["nombre"]: "S:%s:%s" % (e["pista"], e["numero"]) for e in PLAN for a in e["actividades"]}
        esperan = aciertos = errores = 0
        for n in json.load(io.open(_no, encoding="utf-8")):
            r = V.buscar("\n".join(n["lineas"]), PLAN)
            por = {}
            for c in r["candidatos"]:
                for i in c["lineas"]:
                    por.setdefault(i, []).append(("act", c["actividad"]))
            for e in r["etapas"]:
                for i in e["lineas"]:
                    por.setdefault(i, []).append(("etapa", "S:%s:%s" % (e["pista"], e["numero"])))
            for i, (tipo, okk, mal) in enumerate(E.ETIQUETAS[(n["carpeta"], n["archivo"])]):
                pv = por.get(i, [])
                bien = [v for k, v in pv if v in okk or ETAPA_DE.get(v) in okk
                        or (k == "etapa" and any(ETAPA_DE.get(a) == v for a in okk))]
                errores += sum(1 for _k, v in pv if v in mal)
                if tipo in ("trabajo", "retirada"):
                    esperan += 1
                    aciertos += bool(bien)
        # ⚠️ Suelos de v522: 22 de 40 con la medida por diferencia de prefijo; esta medida
        # atribuye por `lineas` y se registra lo que da, sin redondear a favor.
        chk("muestra reservada: hay líneas con trabajo esperado (%d)" % esperan, esperan >= 35)
        chk("...aciertos ≥ 22 (%d de %d)" % (aciertos, esperan), aciertos >= 22)
        chk("...errores seguros ≤ 1 (%d)" % errores, errores <= 1)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
